"""JANE 186: bounded, uncertainty-aware late ACK reconciliation.

Signatures authenticate fixture reports, not actual network delivery.
All times are integer milliseconds in a shared *declared* reference frame.
"""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

def canon(x): return json.dumps(x, sort_keys=True, separators=(',', ':')).encode()
def sha(x): return hashlib.sha256(canon(x)).hexdigest()

@dataclass(frozen=True)
class ClockWindow:
    low: int
    high: int
    def __post_init__(self):
        if type(self.low) is not int or type(self.high) is not int or self.low > self.high: raise ValueError('invalid clock bounds')

@dataclass(frozen=True)
class Receipt:
    signer: str
    kind: str
    nonce: str
    body: dict
    signature: str

def sign(private, signer, kind, nonce, body):
    payload = {'signer':signer,'kind':kind,'nonce':nonce,'body':body}
    return Receipt(signer,kind,nonce,body,private.sign(canon(payload)).hex())

def verify(receipt, keys):
    if receipt.signer not in keys: return False
    try:
        keys[receipt.signer].verify(bytes.fromhex(receipt.signature),canon({'signer':receipt.signer,'kind':receipt.kind,'nonce':receipt.nonce,'body':receipt.body}))
        return True
    except (InvalidSignature, ValueError, TypeError):return False

def window(value):
    if not isinstance(value,dict) or set(value)!= {'low','high'}:raise ValueError('clock window')
    return ClockWindow(value['low'],value['high'])

def w(low,high):return {'low':low,'high':high}

class FLAY:
    def __init__(self, db, keys, *, deadline_ms=300, now=1000):
        if type(deadline_ms) is not int or deadline_ms<=0:raise ValueError('deadline')
        self.keys=keys;self.deadline=deadline_ms;self.now=now
        self.db=sqlite3.connect(db)
        self.db.execute('CREATE TABLE IF NOT EXISTS receipts (signer TEXT, nonce TEXT, digest TEXT, PRIMARY KEY(signer,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, prev TEXT, event TEXT, head TEXT)')
        self.db.commit()
    def close(self):self.db.close()
    def audit(self,event):
        row=self.db.execute('SELECT head FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        prev=row[0] if row else '0'*64
        packed=canon(event).decode(); head=hashlib.sha256((prev+packed).encode()).hexdigest()
        self.db.execute('INSERT INTO audit(prev,event,head) VALUES (?,?,?)',(prev,packed,head));self.db.commit()
    def check_chain(self):
        prev='0'*64
        for _,p,e,h in self.db.execute('SELECT seq,prev,event,head FROM audit ORDER BY seq'):
            if p!=prev or hashlib.sha256((p+e).encode()).hexdigest()!=h:return False
            prev=h
        return True
    def receive(self,r):
        if not isinstance(r,Receipt) or r.kind not in ('outbox','ack','watermark','outage') or not verify(r,self.keys):
            self.audit({'status':'BAD_SIGNATURE_OR_KIND','signer':getattr(r,'signer',None)})
            return 'BAD_SIGNATURE_OR_KIND'
        try:
            b=r.body
            if r.kind=='outbox':
                if type(b['seq']) is not int or b['seq']<1 or not isinstance(b['payload_hash'],str) or len(b['payload_hash'])!=64:raise ValueError()
                window(b['sent'])
            elif r.kind=='ack':
                if type(b['seq']) is not int or b['seq']<1 or not isinstance(b['payload_hash'],str) or len(b['payload_hash'])!=64:raise ValueError()
                window(b['received'])
            elif r.kind=='watermark':
                if type(b['through']) is not int or b['through']<0:raise ValueError()
                window(b['observed'])
            else:
                window(b['start']);window(b['end'])
        except (ValueError,KeyError,TypeError):
            self.audit({'status':'INVALID_BODY','kind':r.kind});return 'INVALID_BODY'
        current=self.db.execute('SELECT digest FROM receipts WHERE signer=? AND nonce=?',(r.signer,r.nonce)).fetchone()
        if current:
            status='REPLAY' if current[0]==sha(r.__dict__) else 'NONCE_EQUIVOCATION'
            self.audit({'status':status,'nonce':r.nonce});return status
        self.db.execute('INSERT INTO receipts VALUES(?,?,?)',(r.signer,r.nonce,sha(r.__dict__)))
        self.db.commit()
        self.audit({'status':'ACCEPTED_RECEIPT','kind':r.kind,'digest':sha(r.__dict__)})
        return 'ACCEPTED_RECEIPT'

def reconcile(outbox,acks,receiver_watermark=None,outages=(),*,deadline_ms=300,now=1000):
    """Uses pre-verified signed receipts. Only reports evidence status, not relay culpability.

    Watermark semantics: receiver certifies it has accounted for *every* sequence
    <= through at observation time (including explicit missing classifications).
    A watermark without an ACK is an evidence gap, not proof of packet loss.
    """
    if not outbox:return {'status':'NO_OUTBOX','items':[]}
    ordered=sorted(outbox,key=lambda r:r.body['seq'])
    seqs=[r.body['seq'] for r in ordered]
    if seqs!=list(range(1,max(seqs)+1)):return {'status':'OUTBOX_GAP','items':[]}
    for r in ordered:
        if r.kind!='outbox':raise ValueError('outbox kind')
    if any(r.kind!='ack' for r in acks):raise ValueError('ack kind')
    ack_map={}
    for a in acks:
        seq=a.body['seq']
        if seq in ack_map and (a.body['payload_hash']!=ack_map[seq].body['payload_hash'] or a.body['received']!=ack_map[seq].body['received']):
            return {'status':'ACK_CONFLICT','items':[]}
        ack_map[seq]=a
    if any(a.body['seq'] not in seqs for a in acks):return {'status':'UNKNOWN_ACK','items':[]}
    if receiver_watermark and receiver_watermark.kind!='watermark':raise ValueError('watermark kind')
    for o in outages:
        if o.kind!='outage':raise ValueError('outage kind')
    items=[]
    for sent in ordered:
        b=sent.body; seq=b['seq']; sw=window(b['sent']);deadline=ClockWindow(sw.low+deadline_ms,sw.high+deadline_ms)
        a=ack_map.get(seq)
        if a:
            if a.body['payload_hash']!=b['payload_hash']:status='ACK_PAYLOAD_CONFLICT'
            else:
                aw=window(a.body['received'])
                status='DELIVERED_ON_TIME' if aw.high<=deadline.low else ('DELIVERED_LATE' if aw.low>deadline.high else 'DELIVERED_TIME_UNCERTAIN')
        elif any(window(o.body['start']).low <= deadline.high and window(o.body['end']).high >= sw.low for o in outages):
            status='OUTAGE_OBSCURES_DELIVERY'
        elif receiver_watermark and receiver_watermark.body['through']>=seq and window(receiver_watermark.body['observed']).low>deadline.high:
            status='ACK_EVIDENCE_GAP'
        elif now>deadline.high:
            status='OVERDUE_UNOBSERVED'
        elif now<=deadline.low:
            status='AWAITING_DEADLINE'
        else:status='DEADLINE_UNCERTAIN'
        items.append({'seq':seq,'status':status,'deadline':[deadline.low,deadline.high]})
    statuses=[i['status'] for i in items]
    if any(x=='ACK_PAYLOAD_CONFLICT' for x in statuses):overall='ACK_PAYLOAD_CONFLICT'
    elif any(x=='ACK_EVIDENCE_GAP' for x in statuses):overall='ACK_EVIDENCE_GAP'
    elif any(x=='OUTAGE_OBSCURES_DELIVERY' for x in statuses):overall='OUTAGE_OBSCURES_DELIVERY'
    elif any(x=='OVERDUE_UNOBSERVED' for x in statuses):overall='OVERDUE_UNOBSERVED'
    elif any(x=='DELIVERED_LATE' for x in statuses):overall='LATE_DELIVERY_CONFIRMED_FIXTURE'
    elif any(x=='DELIVERED_TIME_UNCERTAIN' for x in statuses):overall='TIMING_UNCERTAIN'
    elif all(x=='DELIVERED_ON_TIME' for x in statuses):overall='FULLY_ACKNOWLEDGED_FIXTURE'
    else:overall='PENDING'
    return {'status':overall,'items':items,'active':'frozen_parent','learning_applied':False,'cause':'NOT_ESTABLISHED'}

def demo():
    priv={n:Ed25519PrivateKey.from_private_bytes(bytes([i])*32) for i,n in enumerate(['sender','receiver'],start=1)}
    h=lambda i:hashlib.sha256(f'payload-{i}'.encode()).hexdigest()
    sent=[sign(priv['sender'],'sender','outbox',f's{i}',{'seq':i,'payload_hash':h(i),'sent':w(100,110)}) for i in range(1,4)]
    ack=[sign(priv['receiver'],'receiver','ack',f'a{i}',{'seq':i,'payload_hash':h(i),'received':w(210,220)}) for i in (1,3)]
    wm=sign(priv['receiver'],'receiver','watermark','w1',{'through':3,'observed':w(700,710)})
    f=FLAY(':memory:',{n:pk.public_key() for n,pk in priv.items()},now=800)
    for r in sent+ack+[wm]:assert f.receive(r)=='ACCEPTED_RECEIPT'
    r=reconcile(sent,ack,wm,now=800)
    f.audit({'type':'reconcile','result':r});r['audit_valid']=f.check_chain();f.close()
    return r
if __name__=='__main__':print(json.dumps(demo(),indent=2))