"""JANE 173: signed claims do not establish independent acquisition truth.

All identities/keys are synthetic fixtures. An external acquisition voucher is an
independently signed claim in this model, NOT proof of a physical measurement.
"""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

DOMAIN='JANE173/acquisition/v1'
def canonical(d): return json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def sha(d): return hashlib.sha256(canonical(d)).hexdigest()
def seed(n): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane173-fixture-'+n).encode()).digest())
def pubhex(k):
 from cryptography.hazmat.primitives import serialization
 return k.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw).hex()
def signed(kind, issuer, payload, key):
 body={'domain':DOMAIN,'kind':kind,'issuer':issuer,'payload':payload}
 return {'body':body,'signature':key.sign(canonical(body)).hex()}
def verify(receipt, keyhex, kind):
 try:
  body=receipt['body']; assert body['domain']==DOMAIN and body['kind']==kind
  assert isinstance(receipt['signature'],str)
  Ed25519PublicKey.from_public_bytes(bytes.fromhex(keyhex)).verify(bytes.fromhex(receipt['signature']),canonical(body))
  return True
 except (InvalidSignature,AssertionError,ValueError,KeyError,TypeError):return False

@dataclass(frozen=True)
class Authority:
 name:str
 admin:str
 ancestry:str
 key:str

class Ledger:
 def __init__(self,path=':memory:'):
  self.db=sqlite3.connect(path)
  self.db.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,body TEXT NOT NULL,prev TEXT NOT NULL,head TEXT NOT NULL)')
  self.db.execute('CREATE TABLE IF NOT EXISTS nonces(scope TEXT NOT NULL,nonce TEXT NOT NULL,PRIMARY KEY(scope,nonce))')
  self.db.commit()
 def append(self,kind,data):
  previous=self.db.execute('SELECT head FROM events ORDER BY id DESC LIMIT 1').fetchone()
  prev=previous[0] if previous else '0'*64
  obj={'kind':kind,'data':data,'prev':prev}
  head=sha(obj)
  self.db.execute('INSERT INTO events(kind,body,prev,head) VALUES (?,?,?,?)',(kind,canonical(data).decode(),prev,head))
  self.db.commit();return head
 def audit(self,external_head=None):
  prev='0'*64
  for kind,body,stored_prev,head in self.db.execute('SELECT kind,body,prev,head FROM events ORDER BY id'):
   if stored_prev!=prev or sha({'kind':kind,'data':json.loads(body),'prev':prev})!=head:return 'TAMPERED'
   prev=head
  return 'EXTERNAL_HEAD_MISMATCH' if external_head is not None and external_head!=prev else 'VALID_LOCAL_CHAIN'
 def seen(self,scope,nonce):
  return self.db.execute('SELECT 1 FROM nonces WHERE scope=? AND nonce=?',(scope,nonce)).fetchone() is not None
 def record(self,scope,nonce):
  try:
   self.db.execute('INSERT INTO nonces(scope,nonce) VALUES (?,?)',(scope,nonce));self.db.commit();return True
  except sqlite3.IntegrityError:return False
 def head(self):
  row=self.db.execute('SELECT head FROM events ORDER BY id DESC LIMIT 1').fetchone()
  return row[0] if row else '0'*64

class FLAY:
 def __init__(self,registry,ledger=None,quorum=2,now=1000,max_age=60):
  if quorum<1 or max_age<0:raise ValueError('policy')
  self.registry=registry;self.ledger=ledger or Ledger();self.quorum=quorum;self.now=now;self.max_age=max_age
  self.active='frozen_parent'
 def _inspect(self,receipt,kind):
  try:
   b=receipt['body'];issuer=b['issuer'];payload=b['payload'];authority=self.registry[issuer]
   if not verify(receipt,authority.key,kind):return 'BAD_SIGNATURE',None
   if type(payload['timestamp']) is not int or payload['timestamp']>self.now or self.now-payload['timestamp']>self.max_age:return 'STALE_OR_FUTURE',None
   if not isinstance(payload['nonce'],str) or not payload['nonce'] or len(payload['nonce'])>128:return 'INVALID_NONCE',None
   if not isinstance(payload['measurement_id'],str) or not payload['measurement_id']:return 'INVALID_MEASUREMENT',None
   if not isinstance(payload['source_id'],str) or not payload['source_id']:return 'INVALID_SOURCE',None
   if kind=='CLAIM' and payload['counterparty'] not in self.registry:return 'UNKNOWN_COUNTERPARTY',None
   return 'VALID',authority
  except (KeyError,TypeError,ValueError):return 'INVALID_RECEIPT',None
 def evaluate(self,claims,vouchers,measurement_id='m-001'):
  # All evidence, even rejected evidence, is immutable audit input.
  inputs=sha({'claims':claims,'vouchers':vouchers,'measurement_id':measurement_id})
  problems=[];valid_claims=[];valid_vouchers=[];nonce_keys=[]
  for kind,receipts,out in [('CLAIM',claims,valid_claims),('ACQUISITION',vouchers,valid_vouchers)]:
   for r in receipts:
    code,auth=self._inspect(r,kind)
    if code!='VALID':problems.append(code);continue
    p=r['body']['payload'];issuer=r['body']['issuer'];nonce=(issuer+':'+kind,p['nonce'])
    if self.ledger.seen(*nonce) or nonce in nonce_keys:problems.append('REPLAY');continue
    nonce_keys.append(nonce)
    if p['measurement_id']!=measurement_id:problems.append('MEASUREMENT_MISMATCH');continue
    out.append((auth,p))
  # Issuer signatures and co-signing are claims, not new physical measurement roots.
  claimed_sources={p['source_id'] for _,p in valid_claims}
  acquired_sources={p['source_id'] for _,p in valid_vouchers}
  valid_claim_admins={a.admin for a,_ in valid_claims}
  voucher_ancestries={a.ancestry for a,_ in valid_vouchers}
  distinct_vouchers=[];used_admins=set();used_ancestries=set()
  for a,p in sorted(valid_vouchers,key=lambda t:t[0].name):
   if a.admin not in used_admins and a.ancestry not in used_ancestries:
    distinct_vouchers.append((a,p));used_admins.add(a.admin);used_ancestries.add(a.ancestry)
  status='UNVERIFIED_ACQUISITION'
  if len(valid_claims)<2 or len(valid_claim_admins)<2:status='CLAIM_AUTHENTICATION_INSUFFICIENT'
  elif len(claimed_sources)>1:status='CONFLICTING_SIGNED_CLAIMS'
  elif acquired_sources and claimed_sources!=acquired_sources:status='PHYSICAL_SOURCE_CLAIM_CONFLICT'
  elif len(voucher_ancestries)<self.quorum:status='SHARED_OR_INSUFFICIENT_ACQUISITION_ANCESTRY'
  elif len(distinct_vouchers)<self.quorum:status='SHARED_OR_INSUFFICIENT_ACQUISITION_ANCESTRY'
  elif len(acquired_sources)!=1:status='CONFLICTING_ACQUISITION_SOURCES'
  elif problems:status='INVALID_OR_REPLAYED_EVIDENCE'
  else:status='CORROBORATED_FIXTURE_CLAIMS'
  result={'version':'JANE-173','status':status,'measurement_id':measurement_id,
          'claim_signers':len(valid_claims),'claim_administrators':len(valid_claim_admins),
          'acquisition_signers':len(valid_vouchers),'distinct_declared_acquisition_roots':len(distinct_vouchers),
          'claimed_sources':sorted(claimed_sources),'acquired_sources':sorted(acquired_sources),
          'problems':sorted(problems),'inputs_sha256':inputs,'active_parent':self.active,
          'learning_applied':False,'independent_physical_sources_verified':False,
          'scope':'authenticated local fixture statements; physical truth not established'}
  result['digest']=sha(result)
  self.ledger.append('FLAY173_ASSESS',result)
  # A replayed receipt cannot be silently treated as new on the next audit.
  for scope,nonce in nonce_keys:self.ledger.record(scope,nonce)
  return result

def fixtures(scenario='agree'):
 names=['sensor-A','sensor-B','acquisition-X','acquisition-Y']
 keys={n:seed(n) for n in names}
 reg={n:Authority(n,('adminA','adminB','adminX','adminY')[i],('claimA','claimB','acqX','acqY')[i],pubhex(keys[n])) for i,n in enumerate(names)}
 def item(kind,issuer,source,nonce):
  payload={'measurement_id':'m-001','source_id':source,'timestamp':990,'nonce':nonce}
  if kind=='CLAIM':payload['counterparty']='sensor-B' if issuer=='sensor-A' else 'sensor-A'
  return signed(kind,issuer,payload,keys[issuer])
 claims=[item('CLAIM','sensor-A','physical-1','cA'),item('CLAIM','sensor-B','physical-1','cB')]
 vouchers=[item('ACQUISITION','acquisition-X','physical-1','vX'),item('ACQUISITION','acquisition-Y','physical-1','vY')]
 if scenario=='collusion':vouchers=[]
 if scenario=='conflict':vouchers[1]=item('ACQUISITION','acquisition-Y','physical-2','vY')
 if scenario=='false_claim':claims[1]=item('CLAIM','sensor-B','physical-2','cB')
 if scenario=='shared':reg['acquisition-Y']=Authority('acquisition-Y','adminX','acqX',pubhex(keys['acquisition-Y']))
 return reg,claims,vouchers

def demo():
 result={}
 for name in ('agree','collusion','conflict','false_claim','shared'):
  reg,c,v=fixtures(name);f=FLAY(reg);r=f.evaluate(c,v)
  result[name]={'status':r['status'],'roots':r['distinct_declared_acquisition_roots'],'audit':f.ledger.audit()}
 return {'experiment':'JANE-173','tests_scope':'local deterministic fixtures','scenarios':result,'jane_activation':False}
if __name__=='__main__':print(json.dumps(demo(),indent=2))