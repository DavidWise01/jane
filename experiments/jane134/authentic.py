"""JANE 134 — authenticated witness receipt verification (offline).
Requires cryptography. Trust registry/anchors are fixture inputs, not external authorities.
"""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
import json,re
PAT=re.compile(r'^\{\{ - (\d{4}):(\d{2}):(\d{2}) \|\| (\d{2}):(\d{2}):(\d{2}) \|\| ([+-])(\d{1,3})\.(\d{2})\.(\d{2}) \|\| \}\}$')
def utc_time(coord,offset):
 m=PAT.fullmatch(coord)
 if not m or not -840<=offset<=840:raise ValueError('Chronos')
 v=m.groups();d,am,asec=map(int,v[7:])
 if d>360 or am>=60 or asec>=60 or (d==360 and (am or asec)):raise ValueError('angle')
 return datetime(*map(int,v[:6]),tzinfo=timezone(timedelta(minutes=offset))).astimezone(timezone.utc)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
@dataclass(frozen=True)
class TrustKey:
 public_key:bytes
 custody_root:str
 active:bool=True
@dataclass(frozen=True)
class Receipt:
 payload:dict
 signature:bytes
def sign(private,payload):return Receipt(dict(payload),private.sign(canonical(payload)))
class Verifier:
 def __init__(self,registry,anchors,max_skew_seconds=300):
  if not 0<=max_skew_seconds<=86400:raise ValueError('skew')
  self.registry=dict(registry);self.anchors=dict(anchors);self.max_skew_seconds=max_skew_seconds;self.used=set()
 def verify(self,r,now):
  p=r.payload
  fields={'version','key_id','nonce','chronos','utc_offset','sequence','head','claim_digest'}
  if set(p)!=fields or p['version']!='JANE-134':return 'INVALID_SCHEMA'
  k=self.registry.get(p['key_id'])
  if k is None or not k.active:return 'UNKNOWN_OR_REVOKED_KEY'
  try:Ed25519PublicKey.from_public_bytes(k.public_key).verify(r.signature,canonical(p))
  except (InvalidSignature,ValueError,TypeError):return 'BAD_SIGNATURE'
  try:
   t=utc_time(p['chronos'],p['utc_offset'])
   if abs((now.astimezone(timezone.utc)-t).total_seconds())>self.max_skew_seconds:return 'STALE_CHRONOS'
   if not isinstance(p['nonce'],str) or len(p['nonce'])<12 or not re.fullmatch('[0-9a-f]{64}',p['head']) or not re.fullmatch('[0-9a-f]{64}',p['claim_digest']) or type(p['sequence']) is not int or p['sequence']<0:return 'INVALID_PAYLOAD'
  except (ValueError,TypeError,KeyError,OverflowError):return 'INVALID_PAYLOAD'
  if self.anchors.get(k.custody_root)!=(p['sequence'],p['head']):return 'ANCHOR_MISMATCH'
  tag=(p['key_id'],p['nonce'])
  if tag in self.used:return 'REPLAY'
  self.used.add(tag)
  return 'AUTHENTICATED'
def quorum(receipts,verifier,now,required_roots=3):
 statuses=[];roots=set()
 for r in receipts:
  status=verifier.verify(r,now);statuses.append(status)
  if status=='AUTHENTICATED':roots.add(verifier.registry[r.payload['key_id']].custody_root)
 return dict(status='QUORUM_MATCH' if len(roots)>=required_roots else 'QUORUM_INSUFFICIENT',authenticated_custody_roots=len(roots),receipt_statuses=statuses,jane_decision='UNDECIDED',learning_applied=False,limitation='Trust keys and anchors are locally supplied fixtures, not external attestations.')
def fixture():
 from cryptography.hazmat.primitives import serialization
 ts='{{ - 2026:11:11 || 21:11:00 || +123.45.56 || }}';now=utc_time(ts,-360)
 keys=[Ed25519PrivateKey.generate() for _ in range(3)]
 roots=['owned:canonical','external:A','external:B']
 registry={f'k{i}':TrustKey(k.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw),roots[i]) for i,k in enumerate(keys)}
 head=sha256(b'ledger head').hexdigest();anchors={r:(7,head) for r in roots}
 receipts=[]
 for i,k in enumerate(keys):
  p=dict(version='JANE-134',key_id=f'k{i}',nonce=f'unique-nonce-{i:03d}',chronos=ts,utc_offset=-360,sequence=7,head=head,claim_digest=sha256(b'claim').hexdigest())
  receipts.append(sign(k,p))
 return registry,anchors,receipts,now
