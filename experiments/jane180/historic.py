"""JANE 180: historic decisions amid signing-key compromise.

No external custody or physical independence is proven by these fixtures.
Signed timestamps are assertions; anchor custody is independently keyed but simulated.
"""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def canonical(obj): return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
def sha(obj): return hashlib.sha256(canonical(obj)).hexdigest()
def pub(key): return key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()
def sign(key, record): return key.sign(canonical(record)).hex()
def valid(public_hex, record, signature):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(bytes.fromhex(signature),canonical(record))
        return True
    except (ValueError, TypeError, Exception): return False

def receipt(issuer, key, payload): return {'issuer':issuer,'payload':payload,'signature':sign(key,payload)}

def deterministic_key(tag):
    return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('JANE180-FIXTURE:'+tag).encode()).digest())

@dataclass(frozen=True)
class Policy:
    required_custodians: int=2
    max_depth: int=128
    def __post_init__(self):
        if not 2<=self.required_custodians<=8 or not 1<=self.max_depth<=10000: raise ValueError('policy limits')

class HistoricAudit:
    def __init__(self, decision_public, custodian_registry, *, db=':memory:',policy=Policy()):
        self.decision_public=decision_public
        self.custodians=custodian_registry # name -> {public,admin,root}; fixture claims only
        self.policy=policy
        self.conn=sqlite3.connect(db)
        self.conn.execute('create table if not exists audits (seq integer primary key, previous text not null, body text not null, head text not null)')
        self.conn.commit()
    def close(self): self.conn.close()
    def _append(self, body):
        seq,previous=self._head()
        record={'seq':seq,'previous':previous,'body':body}
        head=sha(record)
        self.conn.execute('insert into audits values (?,?,?,?)',(seq,previous,canonical(body).decode(),head));self.conn.commit()
        return head
    def _head(self):
        row=self.conn.execute('select seq,head from audits order by seq desc limit 1').fetchone()
        return (row[0]+1,row[1]) if row else (0,'0'*64)
    def audit_chain(self,external_head=None):
        previous='0'*64
        for seq,p,b,head in self.conn.execute('select seq,previous,body,head from audits order by seq'):
            if p!=previous or head!=sha({'seq':seq,'previous':p,'body':json.loads(b)}):return 'TAMPERED'
            previous=head
        return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and previous!=external_head else 'VALID_LOCAL_CHAIN'
    def evaluate(self, decision, anchors, compromised, *, expected_checkpoint=None):
        # decision: signed record {issuer,payload:{id,seq,head,claimed_time,epoch},signature}
        # anchor: signed payload {decision_id,seq,head,retained_at,recorded_before,nonce,chain_root}
        verdict='UNCERTAIN_OR_UNANCHORED'; findings=[]; admins=set();roots=set();accepted=[]
        d=decision.get('payload',{}) if isinstance(decision,dict) else {}
        issuer=decision.get('issuer') if isinstance(decision,dict) else None
        if issuer not in self.decision_public or not valid(self.decision_public[issuer],d,decision.get('signature','')):
            verdict='INVALID_DECISION_SIGNATURE';findings.append(verdict)
        elif not all(isinstance(d.get(k),int) and not isinstance(d.get(k),bool) for k in ('seq','claimed_time','epoch')) or not isinstance(d.get('id'),str) or not isinstance(d.get('head'),str) or len(d['head'])!=64:
            verdict='MALFORMED_DECISION';findings.append(verdict)
        elif not isinstance(compromised,tuple) or len(compromised)!=2 or any(type(x)!=int for x in compromised) or compromised[0]>compromised[1]:
            verdict='INVALID_COMPROMISE_INTERVAL';findings.append(verdict)
        else:
            seen_issuers=set();seen_nonces=set();source_conflict=False
            for a in anchors[:self.policy.max_depth]:
                signer=a.get('issuer') if isinstance(a,dict) else None
                payload=a.get('payload',{}) if isinstance(a,dict) else {}
                meta=self.custodians.get(signer)
                if meta is None or not valid(meta['public'],payload,a.get('signature','')):
                    findings.append('INVALID_ANCHOR_SIGNATURE');continue
                if signer in seen_issuers or (signer,payload.get('nonce')) in seen_nonces:
                    findings.append('DUPLICATE_ANCHOR');continue
                seen_issuers.add(signer);seen_nonces.add((signer,payload.get('nonce')))
                if payload.get('decision_id')!=d['id'] or payload.get('seq')!=d['seq'] or payload.get('head')!=d['head']:
                    findings.append('ANCHOR_HEAD_CONFLICT');source_conflict=True;continue
                if type(payload.get('retained_at'))!=int or type(payload.get('recorded_before'))!=int or not isinstance(payload.get('nonce'),str):
                    findings.append('BAD_ANCHOR_METADATA');continue
                if payload['retained_at']>payload['recorded_before']:
                    findings.append('IMPOSSIBLE_ANCHOR_TIME');continue
                # External retention during an uncertain interval does not certify authorship.
                if payload['recorded_before']>=compromised[0]:
                    findings.append('ANCHOR_NOT_PREDATING_RISK');continue
                if meta['admin'] in admins or meta['root'] in roots:
                    findings.append('SHARED_CUSTODY_ANCESTRY');continue
                admins.add(meta['admin']);roots.add(meta['root']);accepted.append(signer)
            if len(anchors)>self.policy.max_depth:findings.append('ANCHOR_BUDGET_EXCEEDED')
            if source_conflict:verdict='CONFLICTING_ANCHORS'
            elif expected_checkpoint is not None and d['head']!=expected_checkpoint:verdict='CHECKPOINT_MISMATCH'
            elif len(accepted)>=self.policy.required_custodians and d['claimed_time']<compromised[0]:
                verdict='PRE_RISK_ANCHORED_FIXTURE'
            elif compromised[0]<=d['claimed_time']<=compromised[1]:verdict='POTENTIALLY_ATTACKER_AUTHORED'
            elif d['claimed_time']>compromised[1]:verdict='POST_RISK_OLD_KEY_UNTRUSTED'
            else:verdict='HISTORIC_SIGNATURE_UNCORROBORATED'
        output={'version':'JANE-180','decision_id':d.get('id'),'verdict':verdict,'accepted_fixture_roots':len(accepted),'accepted_custodians':sorted(accepted),'findings':sorted(set(findings)), 'compromise_interval':list(compromised) if isinstance(compromised,tuple) else None,'decision_claimed_time':d.get('claimed_time'),'active_parent':'FROZEN','learning_applied':False,'independence_verified':False,'scope':'synthetic signed fixture claims; no physical execution proof'}
        output['digest']=sha(output)
        self._append({'result_digest':output['digest'],'verdict':verdict,'decision_id':d.get('id'),'findings':output['findings']})
        return output

def fixture():
    dk=deterministic_key('scheduler')
    keys={name:deterministic_key(name) for name in ('custodyA','custodyB','custodyC')}
    reg={name:{'public':pub(key),'admin':name,'root':name} for name,key in keys.items()}
    decision=receipt('scheduler',dk,{'id':'decision-004','seq':4,'head':'a'*64,'claimed_time':50,'epoch':0})
    def anchors(record=decision,at=65):
        return [receipt(name,key,{'decision_id':record['payload']['id'],'seq':record['payload']['seq'],'head':record['payload']['head'],'retained_at':at,'recorded_before':at+1,'nonce':name+'-4'}) for name,key in keys.items()]
    return {'decision_key':dk,'keys':keys,'registry':reg,'decision':decision,'anchors':anchors}

def demo():
    f=fixture(); a=HistoricAudit({'scheduler':pub(f['decision_key'])},f['registry'])
    accepted=a.evaluate(f['decision'],f['anchors'](),(100,200),expected_checkpoint='a'*64)
    late=a.evaluate(f['decision'],f['anchors'](at=125),(100,200))
    forged_dec=receipt('scheduler',f['decision_key'],{**f['decision']['payload'],'claimed_time':150})
    ambiguous=a.evaluate(forged_dec,f['anchors'](forged_dec,at=180),(100,200))
    result={'accepted':accepted,'unanchored_due_to_late_custody':late,'ambiguous':ambiguous,'audit':a.audit_chain()}
    a.close();return result
if __name__=='__main__':print(json.dumps(demo(),indent=2))
