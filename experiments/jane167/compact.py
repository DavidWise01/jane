"""JANE 167 — portable compact calibration checker. Offline synthetic fixtures.

Signed agreement is not physical calibration or proof of custody independence.
For the full 46-test experiment, use jane167-tested.zip.
"""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
@dataclass(frozen=True)
class Claim:
    issuer:str
    ancestry:str
    admin:str
    low:int
    high:int
    tick:int
    nonce:str

def sign(claim,key):
    p=asdict(claim)
    return {'payload':p,'signature':key.sign(canonical(p)).hex()}

def check(packet,key):
    try:
        p=Claim(**packet['payload'])
        key.verify(bytes.fromhex(packet['signature']),canonical(asdict(p)))
        if type(p.low)!=int or type(p.high)!=int or type(p.tick)!=int or p.low>p.high or not p.ancestry or not p.admin or not p.nonce:
            raise ValueError('BAD_FIELDS')
        return p
    except (InvalidSignature,ValueError,KeyError,TypeError) as exc:
        raise ValueError('INVALID_SIGNATURE_OR_FIELDS') from exc

def evaluate(target, references, keyring, now=110, max_age=300, min_roots=3):
    errors=[]; accepted=[]
    try:
        t=check(target,keyring[target['payload']['issuer']])
        if not 0<=now-t.tick<=max_age: raise ValueError('STALE_TARGET')
    except (ValueError,KeyError,TypeError):
        t=None;errors.append('TARGET_INVALID')
    ancestry=set();admins=set();nonces=set()
    for packet in references:
        try:
            r=check(packet,keyring[packet['payload']['issuer']])
            if not 0<=now-r.tick<=max_age: raise ValueError('STALE_REFERENCE')
            if (r.issuer,r.nonce) in nonces: raise ValueError('REPLAY')
            nonces.add((r.issuer,r.nonce))
            if r.ancestry in ancestry or r.admin in admins:
                errors.append('SHARED_ANCESTRY_OR_ADMIN');continue
            accepted.append(r);ancestry.add(r.ancestry);admins.add(r.admin)
        except (ValueError,KeyError,TypeError):errors.append('INVALID_REFERENCE')
    lo=max((r.low for r in accepted),default=None)
    hi=min((r.high for r in accepted),default=None)
    overlap=[lo,hi] if lo is not None and lo<=hi else None
    if t is None:status='UNTRUSTED_CLOCK_CLAIM'
    elif len(accepted)<min_roots:status='INSUFFICIENT_DISTINCT_REFERENCES'
    elif overlap is None:status='REFERENCE_CONFLICT'
    elif overlap[1]<t.low or overlap[0]>t.high:status='UNDERSTATED_UNCERTAINTY'
    elif any(e!='SHARED_ANCESTRY_OR_ADMIN' for e in errors):status='EVIDENCE_INCOMPLETE'
    else:status='CALIBRATION_CONSISTENT_FIXTURE'
    result={'version':'JANE-167-COMPACT','status':status,'overlap':overlap,'roots':len(accepted),
            'errors':errors,'uncertainty_tightened':False,'independence_verified':False,
            'physical_time_verified':False,'jane_activated':False,'active_parent':'FROZEN'}
    result['digest']=sha256(canonical(result)).hexdigest()
    return result

def fixture():
    ids=('clock','A','B','C')
    keys={x:Ed25519PrivateKey.from_private_bytes(sha256(x.encode()).digest()) for x in ids}
    pubs={x:k.public_key() for x,k in keys.items()}
    target=sign(Claim('clock','clock-root','clock-admin',950,1050,100,'clk-1'),keys['clock'])
    refs=[sign(Claim(x,'root-'+x,'admin-'+x,lo,hi,100,x+'-1'),keys[x])
          for x,lo,hi in [('A',990,1010),('B',995,1015),('C',992,1008)]]
    return keys,pubs,target,refs

if __name__=='__main__':
    _,pubs,t,refs=fixture()
    print(json.dumps(evaluate(t,refs,pubs),indent=2))
