"""JANE 172: signed measurement-lineage edges, conservative independent-root counting.

All keys and attestations are locally configured fixtures. No physical independence proof.
"""
import hashlib, json
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature


def canonical(obj): return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
def sha(obj): return hashlib.sha256(canonical(obj)).hexdigest()

@dataclass(frozen=True)
class Principal:
    name: str
    role: str  # sensor, broker, source
    admin: str
    public_key: object

class Registry:
    def __init__(self): self.nodes={}; self.private={}
    def add_fixture(self,name,role,admin):
        if name in self.nodes or role not in ('sensor','broker','source'): raise ValueError('principal')
        key=Ed25519PrivateKey.generate()
        self.nodes[name]=Principal(name,role,admin,key.public_key()); self.private[name]=key
    def receipt(self,child,parent,nonce,observed_at=1000,**overrides):
        claim=dict(version='JANE172_EDGE_V1',child=child,parent=parent,nonce=nonce,observed_at=observed_at,relation='derives_measurement_from')
        claim.update(overrides)
        return dict(claim=claim,child_signature=self.private[child].sign(canonical(claim)).hex(),parent_signature=self.private[parent].sign(canonical(claim)).hex())

class LineageAudit:
    def __init__(self,registry,now=1000,max_age=300,max_edges=128):
        self.registry=registry; self.now=now;self.max_age=max_age;self.max_edges=max_edges
        self.ledger=[]; self.last='0'*64
    def append(self,kind,details):
        event=dict(seq=len(self.ledger),kind=kind,details=details,previous=self.last)
        event['head']=sha(event);self.ledger.append(event);self.last=event['head']
    def audit_log(self,anchor=None):
        previous='0'*64
        for i,event in enumerate(self.ledger):
            if event['seq']!=i or event['previous']!=previous or sha({k:v for k,v in event.items() if k!='head'})!=event['head']:return 'TAMPERED'
            previous=event['head']
        return 'ANCHOR_MISMATCH' if anchor is not None and anchor!=previous else 'LOCAL_CHAIN_VALID'
    def verify(self,receipts,reports):
        reasons=[];accepted=[]; seen_nonce=set();edges=set(); parents={}
        if len(receipts)>self.max_edges: reasons.append('EDGE_BUDGET_EXCEEDED')
        else:
            for idx,rec in enumerate(receipts):
                reason=None
                try:
                    c=rec['claim']; child=c['child'];parent=c['parent']; nonce=c['nonce']; time=c['observed_at']
                    if set(c)!= {'version','child','parent','nonce','observed_at','relation'} or c['version']!='JANE172_EDGE_V1' or c['relation']!='derives_measurement_from':reason='INVALID_SCHEMA'
                    elif child not in self.registry.nodes or parent not in self.registry.nodes:reason='UNKNOWN_PRINCIPAL'
                    elif child==parent:reason='SELF_EDGE'
                    elif self.registry.nodes[child].role=='source':reason='SOURCE_HAS_PARENT'
                    elif self.registry.nodes[parent].role=='sensor':reason='INVALID_PARENT_ROLE'
                    elif type(time) is not int or time>self.now or self.now-time>self.max_age:reason='STALE_OR_FUTURE'
                    elif not isinstance(nonce,str) or not nonce or len(nonce)>128 or (child,nonce) in seen_nonce:reason='NONCE_REPLAY'
                    else:
                        try:
                            payload=canonical(c)
                            self.registry.nodes[child].public_key.verify(bytes.fromhex(rec['child_signature']),payload)
                            self.registry.nodes[parent].public_key.verify(bytes.fromhex(rec['parent_signature']),payload)
                        except (InvalidSignature,ValueError,KeyError,TypeError):reason='BAD_EDGE_SIGNATURE'
                    if reason is None:
                        if child in parents and parents[child]!=parent:reason='CONFLICTING_PARENTS'
                        elif (child,parent) in edges:reason='DUPLICATE_EDGE'
                        else:
                            parents[child]=parent;edges.add((child,parent));seen_nonce.add((child,nonce));accepted.append((child,parent))
                except (KeyError,TypeError,ValueError):reason='INVALID_SCHEMA'
                if reason:reasons.append(reason)
                self.append('EDGE_REVIEW',dict(index=idx,status=reason or 'VALID',claim_digest=sha(rec.get('claim',{})) if isinstance(rec,dict) else None))
        roots={}; unresolved=[]
        for reporter in reports:
            if reporter not in self.registry.nodes or self.registry.nodes[reporter].role!='sensor':
                unresolved.append((reporter,'INVALID_REPORTER'));continue
            visited=set(); current=reporter
            while True:
                if current in visited:
                    unresolved.append((reporter,'LINEAGE_CYCLE'));break
                visited.add(current)
                node=self.registry.nodes[current]
                if node.role=='source':
                    roots[reporter]=current;break
                if current not in parents:
                    unresolved.append((reporter,'MISSING_SIGNED_EDGE'));break
                current=parents[current]
        if len(set(reports))!=len(reports):reasons.append('DUPLICATE_REPORT')
        for _,why in unresolved:reasons.append(why)
        # Only a conservative declared-root count. If ANY bad receipt exists, never certify a quorum.
        distinct_roots=set(roots.values());admins={self.registry.nodes[root].admin for root in distinct_roots}
        if len(admins)<len(distinct_roots):reasons.append('SHARED_ROOT_ADMIN')
        status=('UNVERIFIED_LINEAGE' if reasons else 'DECLARED_ROOT_QUORUM' if len(roots)==len(reports) and len(distinct_roots)>=3 else 'SHARED_MEASUREMENT_ANCESTRY')
        result=dict(version='JANE-172',status=status,declared_measurement_roots=sorted(distinct_roots),root_count=len(distinct_roots),report_count=len(reports),valid_edge_count=len(accepted),rejections=sorted(set(reasons)),unresolved=unresolved,independence_verified=False,active_parent='frozen',learning_applied=False,scope='locally configured cryptographic identities and claimed source relationships')
        self.append('DECISION',dict(result_digest=sha(result),status=status))
        return result

def demo():
    r=Registry()
    for i in range(3):r.add_fixture('s'+str(i),'sensor','sensor_admin_'+str(i))
    r.add_fixture('broker','broker','broker_admin')
    r.add_fixture('physical','source','source_admin')
    receipts=[r.receipt('s'+str(i),'broker','n'+str(i)) for i in range(3)]+[r.receipt('broker','physical','n3')]
    a=LineageAudit(r);shared=a.verify(receipts,['s0','s1','s2'])
    for i in range(3):r.add_fixture('physical'+str(i),'source','distinct_admin_'+str(i))
    distinct=[r.receipt('s'+str(i),'physical'+str(i),'independent'+str(i)) for i in range(3)]
    b=LineageAudit(r);separate=b.verify(distinct,['s0','s1','s2'])
    return dict(shared=shared,separate=separate,ledger_head=a.last,local_audit=a.audit_log())

if __name__=='__main__':print(json.dumps(demo(),indent=2))