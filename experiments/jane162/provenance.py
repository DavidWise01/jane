"""JANE 162 — authenticatable scheduler receipts, with a deliberately untrusted observer.

Trust limits: signature proves possession of the configured scheduler key, not that
hardware executed the asserted event. External anti-truncation anchoring is needed.
"""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

GENESIS = '0' * 64

def canonical(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
def sha(v): return hashlib.sha256(canonical(v)).hexdigest()

@dataclass(frozen=True)
class Decision:
    scheduler: str
    epoch: str
    seq: int
    tick: int
    enabled: tuple[str, ...]
    selected: str | None
    prev: str
    def asdict(self):
        return {'scheduler':self.scheduler,'epoch':self.epoch,'seq':self.seq,'tick':self.tick,
                'enabled':list(self.enabled),'selected':self.selected,'prev':self.prev}

class SchedulerSigner:
    def __init__(self, key=None, scheduler='hive-a', epoch='epoch-1'):
        self.key=key or Ed25519PrivateKey.generate()
        self.scheduler=scheduler;self.epoch=epoch;self.seq=0;self.prev=GENESIS
    def public_key(self): return self.key.public_key()
    def issue(self,tick,enabled,selected):
        enabled=tuple(sorted(set(enabled)))
        if any(type(x)!=str or not x for x in enabled): raise ValueError('invalid enabled set')
        if selected is not None and selected not in enabled: raise ValueError('selected not enabled')
        if type(tick)!=int or tick<0: raise ValueError('bad tick')
        d=Decision(self.scheduler,self.epoch,self.seq,tick,enabled,selected,self.prev)
        body=d.asdict();signature=self.key.sign(canonical(body)).hex()
        receipt={'decision':body,'signature':signature}
        self.prev=sha(receipt);self.seq+=1
        return receipt

def verify_receipt(receipt,key:Ed25519PublicKey,scheduler,epoch):
    if not isinstance(receipt,dict) or set(receipt)!={'decision','signature'}:return 'MALFORMED'
    d=receipt['decision']; sig=receipt['signature']
    if not isinstance(d,dict) or set(d)!={'scheduler','epoch','seq','tick','enabled','selected','prev'}:return 'MALFORMED'
    if d['scheduler']!=scheduler or d['epoch']!=epoch:return 'FOREIGN_IDENTITY'
    if type(d['seq'])!=int or d['seq']<0 or type(d['tick'])!=int or d['tick']<0:return 'MALFORMED'
    if not isinstance(d['enabled'],list) or not all(type(x)==str and bool(x) for x in d['enabled']) or d['enabled']!=sorted(set(d['enabled'])):return 'MALFORMED'
    if d['selected'] is not None and d['selected'] not in d['enabled']:return 'MALFORMED'
    if type(d['prev'])!=str or len(d['prev'])!=64:return 'MALFORMED'
    try:
        raw=bytes.fromhex(sig)
        key.verify(raw,canonical(d))
    except (ValueError,TypeError,InvalidSignature):return 'BAD_SIGNATURE'
    return 'VALID_SIGNATURE'

class FLAYObserverAudit:
    """SQLite audit: append-only observations, with explicit report comparison.
    No arbitrary reset/promotion; signed anchor supplied by caller (not produced here).
    """
    def __init__(self,path,key,scheduler='hive-a',epoch='epoch-1',expected_head=None):
        self.path=str(path);self.key=key;self.scheduler=scheduler;self.epoch=epoch
        self.db=sqlite3.connect(self.path)
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, payload TEXT NOT NULL, prev TEXT NOT NULL, head TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS signed_receipts (seq INTEGER PRIMARY KEY, digest TEXT NOT NULL, tick INTEGER NOT NULL, prev TEXT NOT NULL, body TEXT NOT NULL)')
        self.db.commit()
        self.external_anchor_status='NOT_PROVIDED' if expected_head is None else ('MATCH' if self.head()==expected_head else 'HEAD_MISMATCH')
    def head(self):
        row=self.db.execute('SELECT head FROM events ORDER BY id DESC LIMIT 1').fetchone()
        return row[0] if row else GENESIS
    def append(self,kind,payload):
        prior=self.head();data={'kind':kind,'payload':payload,'prev':prior};h=sha(data)
        self.db.execute('INSERT INTO events (kind,payload,prev,head) VALUES (?,?,?,?)',(kind,canonical(payload).decode(),prior,h));self.db.commit()
        return h
    def check_ledger(self,expected_head=None):
        prev=GENESIS
        for kind,body,old,head in self.db.execute('SELECT kind,payload,prev,head FROM events ORDER BY id'):
            if old!=prev or sha({'kind':kind,'payload':json.loads(body),'prev':old})!=head:return 'TAMPERED_LEDGER'
            prev=head
        return 'HEAD_MISMATCH' if expected_head is not None and expected_head!=prev else 'VALID_LOCAL_CHAIN'
    def capture(self,receipt,observer_report=None):
        verification=verify_receipt(receipt,self.key,self.scheduler,self.epoch)
        if verification!='VALID_SIGNATURE':
            self.append('REJECTED',{'reason':verification,'receipt_hash':sha(receipt)})
            return verification
        d=receipt['decision'];i=d['seq'];rh=sha(receipt)
        prior=self.db.execute('SELECT digest FROM signed_receipts WHERE seq=?',(i,)).fetchone()
        if prior:
            outcome='REPLAY' if prior[0]==rh else 'SIGNED_EQUIVOCATION'
        else:
            latest=self.db.execute('SELECT seq,digest,tick FROM signed_receipts ORDER BY seq DESC LIMIT 1').fetchone()
            if latest is None:
                outcome='ACCEPTED' if i==0 and d['prev']==GENESIS else 'MISSING_PREFIX'
            elif i!=latest[0]+1:
                outcome='MISSING_SEQUENCE' if i>latest[0]+1 else 'OUT_OF_ORDER'
            elif d['prev']!=latest[1]:outcome='BROKEN_SIGNED_CHAIN'
            elif d['tick']<=latest[2]:outcome='NONMONOTONIC_TICK'
            else:outcome='ACCEPTED'
            if outcome=='ACCEPTED':
                self.db.execute('INSERT INTO signed_receipts VALUES(?,?,?,?,?)',(i,rh,d['tick'],d['prev'],canonical(d).decode()))
                self.db.commit()
        report_result='NOT_REPORTED'
        if observer_report is not None:
            if not isinstance(observer_report,dict):report_result='INVALID_REPORT'
            elif observer_report.get('seq')!=i or observer_report.get('selected')!=d['selected'] or observer_report.get('enabled')!=d['enabled'] or observer_report.get('tick')!=d['tick']:
                report_result='OBSERVER_CONTRADICTION'
            else:report_result='REPORT_MATCH'
        self.append('CAPTURE',{'seq':i,'receipt_hash':rh,'decision':outcome,'observer':report_result})
        return outcome if outcome!='ACCEPTED' else (report_result if report_result in ('INVALID_REPORT','OBSERVER_CONTRADICTION') else 'ACCEPTED')
    def reconcile_observer_window(self,reports,first_seq,last_seq):
        """Require an observer report for every verified decision in a contiguous window.
        If the signed source itself is missing a decision, report missing source first.
        """
        if type(first_seq)!=int or type(last_seq)!=int or first_seq<0 or last_seq<first_seq or last_seq-first_seq>10000:
            raise ValueError('invalid window')
        source={r[0]:json.loads(r[1]) for r in self.db.execute('SELECT seq,body FROM signed_receipts WHERE seq BETWEEN ? AND ?',(first_seq,last_seq))}
        obs={};duplicate=[]
        for r in reports:
            if not isinstance(r,dict) or type(r.get('seq'))!=int:raise ValueError('invalid report')
            if r['seq'] in obs:duplicate.append(r['seq'])
            obs[r['seq']]=r
        missing_source=[i for i in range(first_seq,last_seq+1) if i not in source]
        missing_observer=[i for i in range(first_seq,last_seq+1) if i in source and i not in obs]
        contradictions=[i for i in range(first_seq,last_seq+1) if i in source and i in obs and
                        any(obs[i].get(k)!=source[i][k] for k in ('tick','enabled','selected'))]
        result={'status':('MISSING_SIGNED_SOURCE' if missing_source else 'OBSERVER_DUPLICATES' if duplicate else 'OBSERVER_OMISSION' if missing_observer else 'OBSERVER_CONTRADICTION' if contradictions else 'MATCHED_WINDOW'),
                'missing_source':missing_source,'missing_observer':missing_observer,'contradictions':contradictions,'duplicates':duplicate,
                'window':[first_seq,last_seq],'external_anchor':self.external_anchor_status,
                'independence_verified':False,'physical_execution_verified':False,'active_parent':'FROZEN','jane_approval':False}
        self.append('RECONCILE',result)
        return result
    def close(self):self.db.close()

def demo():
    key=Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    signer=SchedulerSigner(key)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        audit=FLAYObserverAudit(Path(tmp)/'ledger.db',signer.public_key())
        receipts=[signer.issue(i,['A','B'],'A' if i<3 else 'B') for i in range(4)]
        captures=[audit.capture(r) for r in receipts]
        reports=[{'seq':i,'tick':i,'enabled':['A','B'],'selected':('A' if i<3 else 'B')} for i in (0,1,3)]
        outcome=audit.reconcile_observer_window(reports,0,3)
        evidence={'version':'JANE-162','captures':captures,'reconciliation':outcome,
                  'ledger_audit':audit.check_ledger(), 'ledger_head':audit.head(),
                  'scope':'locally signed synthetic scheduler receipts; not proof of real execution',
                  'independent_witness_increment':0}
        audit.close();return evidence
if __name__=='__main__':print(json.dumps(demo(),indent=2))