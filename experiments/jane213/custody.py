"""JANE 213: declared observation ancestry vs physical custody (fixture only)."""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

def canon(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(value:Any)->str:
    return hashlib.sha256(canon(value)).hexdigest()
def signed(body:dict, secret:Ed25519PrivateKey)->dict:
    return {'body':body,'signature':secret.sign(canon(body)).hex()}
def verify(packet:dict, key:Ed25519PublicKey)->bool:
    try:
        key.verify(bytes.fromhex(packet['signature']),canon(packet['body']))
        return True
    except (ValueError,KeyError,TypeError):
        return False
    except Exception:
        return False

@dataclass(frozen=True)
class Policy:
    required_roots:int=3
    required_independent_sensors:int=2

class Ledger:
    def __init__(self,path: str=':memory:'):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS uses (nonce TEXT PRIMARY KEY, verdict TEXT NOT NULL, evidence_hash TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, prev TEXT NOT NULL, digest TEXT NOT NULL, event TEXT NOT NULL)')
        self.db.commit()
    def close(self): self.db.close()
    def seen(self,nonce:str)->bool:
        return self.db.execute('SELECT 1 FROM uses WHERE nonce=?',(nonce,)).fetchone() is not None
    def record(self,nonce:str,verdict:str,evidence_hash:str)->None:
        event={'nonce':nonce,'verdict':verdict,'evidence_hash':evidence_hash}
        row=self.db.execute('SELECT seq,digest FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        seq=row[0]+1 if row else 1
        prev=row[1] if row else '0'*64
        d=digest({'prev':prev,'event':event,'seq':seq})
        with self.db:
            self.db.execute('INSERT INTO uses VALUES (?,?,?)',(nonce,verdict,evidence_hash))
            self.db.execute('INSERT INTO audit VALUES (?,?,?,?)',(seq,prev,d,canon(event).decode()))
    def audit_ok(self)->bool:
        prev='0'*64
        for seq,old,h,event_json in self.db.execute('SELECT seq,prev,digest,event FROM audit ORDER BY seq'):
            if old!=prev or h!=digest({'prev':prev,'event':json.loads(event_json),'seq':seq}):return False
            prev=h
        return True

class FLAY213:
    def __init__(self,keys:dict[str,Ed25519PublicKey],ledger:Ledger,policy:Policy=Policy()):
        self.keys=keys;self.ledger=ledger;self.policy=policy
    def inspect(self,packet:dict)->dict:
        if not self.ledger.audit_ok(): return {'verdict':'CORRUPT_AUDIT'}
        try:
            counter=packet['counter']; witnesses=packet['witnesses']; nonce=counter['body']['nonce']
            if not isinstance(nonce,str) or len(nonce)<12: return {'verdict':'INVALID_NONCE'}
            if self.ledger.seen(nonce):return {'verdict':'REPLAY'}
            evidence=digest(packet)
            if not isinstance(witnesses,list) or not witnesses:return {'verdict':'MISSING_WITNESSES'}
            all_packets=[counter,*witnesses]
            if any(not isinstance(p,dict) or not isinstance(p.get('body'),dict) for p in all_packets):return {'verdict':'INVALID_PACKET'}
            identities=[p['body'].get('id') for p in all_packets]
            if len(set(identities))!=len(identities):return {'verdict':'DUPLICATE_IDENTITY'}
            for p in all_packets:
                ident=p['body']['id']; key=self.keys.get(ident)
                if not key or not verify(p,key):return {'verdict':'SIGNATURE_INVALID'}
            task=counter['body']['task']; head=counter['body']['head']; seq=counter['body']['sequence']; clock=counter['body']['tick']
            if not isinstance(seq,int) or isinstance(seq,bool) or seq<1:return {'verdict':'INVALID_SEQUENCE'}
            if not isinstance(clock,int) or isinstance(clock,bool) or clock<0:return {'verdict':'INVALID_CHRONOLOGY'}
            if not isinstance(head,str) or len(head)!=64:return {'verdict':'INVALID_HEAD'}
            for w in witnesses:
                b=w['body']
                if b.get('nonce')!=nonce or b.get('task')!=task or b.get('head')!=head or b.get('sequence')!=seq:return {'verdict':'CHECKPOINT_DISAGREEMENT'}
                if not isinstance(b.get('tick'),int) or b['tick']<clock:return {'verdict':'INVALID_CHRONOLOGY'}
            # Ancestry, operator, and sensor are separate fields; identity/signature counts do not equal roots.
            bodies=[p['body'] for p in all_packets]
            for b in bodies:
                if not all(isinstance(b.get(k),str) and b[k] for k in ('root','operator','sensor')):
                    return {'verdict':'MISSING_CUSTODY_DECLARATION'}
            roots={b['root'] for b in bodies}
            operators={b['operator'] for b in bodies}
            sensors={b['sensor'] for b in bodies}
            # Count witness-independent sensor origins, excluding executor's sensor.
            independent_sensors={w['body']['sensor'] for w in witnesses if w['body']['sensor']!=counter['body']['sensor']}
            common_log={b.get('logging_service','') for b in bodies}
            shared_service=len(common_log)==1 and '' not in common_log
            if len(roots)<self.policy.required_roots or len(operators)<self.policy.required_roots or shared_service:
                verdict='SHARED_ANCESTRY_WITHHELD'
            elif len(independent_sensors)<self.policy.required_independent_sensors:
                verdict='INSUFFICIENT_INDEPENDENT_OBSERVATION'
            else:
                verdict='DECLARED_CUSTODY_CONSISTENT_FIXTURE'
            self.ledger.record(nonce,verdict,evidence)
            return {'verdict':verdict,'declared_roots':len(roots),'declared_operators':len(operators),'declared_sensors':len(sensors),'independent_observer_sensors':len(independent_sensors),'shared_logging_service':shared_service,'evidence_hash':evidence,'caveat':'Declared custody and signed agreement do not prove physical independence or complete execution.'}
        except (KeyError,TypeError,ValueError,IndexError):
            return {'verdict':'INVALID_PACKET'}

def fixture(variant='independent',nonce='jane213-nonce-000001'):
    ids=('executor','witnessA','witnessB')
    keys={name:Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('JANE213/'+name).encode()).digest()) for name in ids}
    body={'id':'executor','nonce':nonce,'task':'frozen-task-212','head':digest({'events':[1,2,3]}),'sequence':3,'tick':100,'root':'R0','operator':'OP0','sensor':'S0','logging_service':'log0'}
    ws=[]
    for i,name in enumerate(ids[1:],1):
        b={**body,'id':name,'tick':100+i,'root':f'R{i}','operator':f'OP{i}','sensor':f'S{i}','logging_service':f'log{i}'}
        if variant=='shared_root':b['root']='R0'
        if variant=='shared_operator':b['operator']='OP0'
        if variant=='shared_sensor':b['sensor']='S0'
        if variant=='shared_logger':b['logging_service']='log0'
        if variant=='shared_logger' and i==1:pass
        if variant=='conflict' and i==2:b['head']='f'*64
        if variant=='bad_clock' and i==1:b['tick']=99
        ws.append(signed(b,keys[name]))
    if variant=='shared_logger':
        # executor and both witnesses use same logging service
        pass
    return {'counter':signed(body,keys['executor']),'witnesses':ws}, {n:k.public_key() for n,k in keys.items()},keys

def demo()->dict:
    scenarios={}
    for name in ('independent','shared_root','shared_operator','shared_sensor','shared_logger','conflict','bad_clock'):
        p,keys,_=fixture(name,nonce='jane213-'+name+'-0001')
        ledger=Ledger()
        scenarios[name]=FLAY213(keys,ledger).inspect(p)
        ledger.close()
    return {'experiment':'JANE 213','invariant':'Multiple signed witnesses != independent execution evidence','scenarios':scenarios,'parent':'FROZEN','fixture_only':True}
if __name__=='__main__':print(json.dumps(demo(),indent=2,sort_keys=True))