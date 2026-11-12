"""JANE 145 independent-custody evidence gate (offline fixture; not proof of real operators).

Signed receipts prove possession of configured Ed25519 keys. Administrator separation is
an input claim, NOT a cryptographically demonstrated real-world independence fact.
"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json, re
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

STAMP = '{{ 2026.11.12 }}{{ 14.30.00 }}{{ 123.45.56 }}'
PAT = re.compile(r'^\{\{ (\d{4})\.(\d{2})\.(\d{2}) \}\}\{\{ (\d{2})\.(\d{2})\.(\d{2}) \}\}\{\{ ([+-]?\d{1,3})\.(\d{2})\.(\d{2}) \}\}$')

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()

def sha(obj):
    return sha256(canonical(obj)).hexdigest()

def chronos_utc(stamp, offset):
    m = PAT.fullmatch(stamp)
    if not m or type(offset) is not int or not -840 <= offset <= 840:
        raise ValueError('bad Chronos')
    parts = m.groups()
    degree, arcmin, arcsec = map(int, parts[6:])
    if abs(degree)>360 or arcmin>=60 or arcsec>=60 or (abs(degree)==360 and (arcmin or arcsec)):
        raise ValueError('bad angle')
    return datetime(*map(int,parts[:6]),tzinfo=timezone(timedelta(minutes=offset))).astimezone(timezone.utc)

@dataclass(frozen=True)
class Identity:
    key_id: str
    public_key: bytes
    root: str
    administrator: str
    generation: int = 0
    enabled: bool = True
    # This is a local registry annotation, not independently proven custody.
    assertion: str = 'fixture'

@dataclass(frozen=True)
class Receipt:
    payload: dict
    signature: bytes

RECEIPT_KEYS = frozenset(('protocol','key_id','root','sequence','head','nonce','chronos','utc_offset'))

class Gate:
    def __init__(self, identities, expected_anchors, now, max_skew=300):
        self.identities = dict(identities)
        self.expected_anchors = dict(expected_anchors)
        self.now = now
        self.max_skew = max_skew
        self.used = set()
        self.receipts = []
        self.events = []
        if not 0 <= max_skew <= 86400 or now.tzinfo is None:
            raise ValueError('time')

    def _event(self, kind, detail):
        data = dict(seq=len(self.events), kind=kind, detail=detail,
                    prev=self.events[-1]['hash'] if self.events else '0'*64)
        data['hash'] = sha(data)
        self.events.append(data)

    def receive(self, receipt):
        p = receipt.payload
        status = 'BAD_SCHEMA'
        if isinstance(p, dict) and frozenset(p)==RECEIPT_KEYS and p.get('protocol')=='JANE-145':
            ident = self.identities.get(p['key_id'])
            if not ident or not ident.enabled:
                status='UNKNOWN_KEY'
            else:
                try:
                    Ed25519PublicKey.from_public_bytes(ident.public_key).verify(receipt.signature,canonical(p))
                    status='SIGNED'
                except (InvalidSignature,ValueError,TypeError):
                    status='BAD_SIGNATURE'
                if status=='SIGNED':
                    try:
                        t=chronos_utc(p['chronos'],p['utc_offset'])
                        if abs((self.now-t).total_seconds())>self.max_skew:
                            status='STALE'
                        elif (p['root']!=ident.root or not ident.root or not ident.administrator
                              or type(p['sequence']) is not int or p['sequence']<0
                              or not isinstance(p['head'],str) or not re.fullmatch('[0-9a-f]{64}',p['head'])
                              or not isinstance(p['nonce'],str) or len(p['nonce'])<12):
                            status='BAD_CLAIM'
                        elif (ident.root,p['nonce']) in self.used:
                            status='REPLAY'
                        else:
                            status='ACCEPTED'
                    except (ValueError,TypeError,OverflowError):
                        status='BAD_CLAIM'
                if status=='ACCEPTED':
                    self.used.add((ident.root,p['nonce']))
                    self.receipts.append((ident.root,ident.administrator,p['sequence'],p['head'],ident.assertion))
        self._event('ACCEPT' if status=='ACCEPTED' else 'REJECT',dict(status=status,receipt_sha=sha(p) if isinstance(p,dict) else 'invalid'))
        return status

    def assess(self, local_sequence, local_head, required=3):
        if type(local_sequence) is not int or local_sequence < -1 or not isinstance(local_head,str) or not re.fullmatch('[0-9a-f]{64}',local_head) or not 1<=required<=8:
            raise ValueError('local checkpoint')
        # One root might sign two different heads, including through key rotation.
        byroot={}
        for root,admin,seq,head,assertion in self.receipts:
            byroot.setdefault((root,seq),set()).add(head)
        equivocations=sorted([dict(root=r,sequence=s,heads=sorted(heads)) for (r,s),heads in byroot.items() if len(heads)>1],key=lambda x:(x['root'],x['sequence']))
        root_admins={}
        for root,admin,seq,head,assertion in self.receipts:
            root_admins.setdefault(root,set()).add(admin)
        ambiguous_roots=sorted(root for root,admins in root_admins.items() if len(admins)>1)
        if equivocations or ambiguous_roots:
            status='EQUIVOCATION_QUARANTINE' if equivocations else 'CUSTODY_IDENTITY_CONFLICT'
            best=None;votes=0
        else:
            bypoint={}
            for root,admin,seq,head,assertion in self.receipts:
                # One admin's many roots count at most once. One root's many keys count at most once.
                bypoint.setdefault((seq,head),set()).add((root,admin))
            candidate=[]
            for (seq,head),voteset in bypoint.items():
                # Count unique administrator names, with one vote per administrator.
                n=len({admin for root,admin in voteset})
                candidate.append((n,seq,head))
            candidate.sort(key=lambda v:(-v[0],-v[1],v[2]))
            best=candidate[0][1:] if candidate else None
            votes=candidate[0][0] if candidate else 0
            # Distinct receipts disagree about one sequence, no checkpoint consensus.
            conflicts=any(len({h for r,a,s,h,q in self.receipts if s==seq})>1 for seq in {s for r,a,s,h,q in self.receipts})
            if conflicts:
                status='CROSS_ROOT_CONFLICT'
            elif votes<required:
                status='INSUFFICIENT_CUSTODY'
            elif best[0]>local_sequence:
                status='ROLLBACK_DETECTED'
            elif best[0]==local_sequence and best[1]!=local_head:
                status='FORK_DETECTED'
            elif best==(local_sequence,local_head):
                status='MATCHED_FIXTURE_QUORUM'
            else:
                status='LOCAL_AHEAD'
        result=dict(version='JANE-145',status=status,matching_administrators=votes,
                    checkpoint=list(best) if best else None,local=[local_sequence,local_head],
                    equivocations=equivocations,ambiguous_roots=ambiguous_roots,all_custody_claims_are_fixtures=True,
                    independent_operators_verified=False,learning_applied=False,
                    jane_decision='UNDECIDED')
        result['digest']=sha(result)
        self._event('ASSESS',dict(status=status,digest=result['digest']))
        return result

    def audit(self, trusted_external_head=None):
        prev='0'*64
        for i,e in enumerate(self.events):
            if e['seq']!=i or e['prev']!=prev or e['hash']!=sha({k:v for k,v in e.items() if k!='hash'}):
                return 'TAMPERED'
            prev=e['hash']
        return 'EXTERNAL_HEAD_MISMATCH' if trusted_external_head is not None and prev!=trusted_external_head else 'VALID_LOCAL_CHAIN'


def demo():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    now=chronos_utc(STAMP,-360)
    priv=[Ed25519PrivateKey.generate() for _ in range(3)]
    roots=['owned:canonical','external:A','external:B'];admins=['operator:owned','operator:A','operator:B']
    keys={str(i):Identity(str(i),k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw),roots[i],admins[i]) for i,k in enumerate(priv)}
    head=sha256(b'fixture-checkpoint-7').hexdigest()
    g=Gate(keys,{},now)
    for i,k in enumerate(priv):
        p=dict(protocol='JANE-145',key_id=str(i),root=roots[i],sequence=7,head=head,
               nonce=f'fixture-nonce-{i}-unique',chronos=STAMP,utc_offset=-360)
        assert g.receive(Receipt(p,k.sign(canonical(p))))=='ACCEPTED'
    return g,g.assess(5,sha256(b'older-checkpoint').hexdigest())

if __name__=='__main__':
    print(json.dumps(demo()[1],indent=2))