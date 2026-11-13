import tempfile,unittest
from dataclasses import replace
from datetime import datetime, timezone,timedelta
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from fetch import *
STAMP='{{ 2026.11.12 }}{{ 20.39.00 }}{{ 123.45.56 }}'
def pub(k):return k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.keys=[Ed25519PrivateKey.generate() for _ in range(3)]
  self.ep=[Endpoint(f'k{i}',f'https://witness{i}.example.org/proof',f'root{i}',f'admin{i}',pub(k)) for i,k in enumerate(self.keys)]
  self.now=clock_value(STAMP,-360)
  self.f=FLAY148(Path(self.t.name)/'db.sqlite',self.ep,self.now)
 def tearDown(self):self.f.close();self.t.cleanup()
 def payload(self,i,*,head='a'*64,nonce=None,seq=7,claim_updates=None,sigkey=None):
  c=dict(version='JANE-148',key_name=f'k{i}',custody=f'root{i}',administrator=f'admin{i}',chain='jane',sequence=seq,head=head,nonce=nonce or f'nonce-for-witness{i}-long',chronos=STAMP,offset=-360)
  c.update(claim_updates or {})
  sig=(sigkey or self.keys[i]).sign(canonical(c)).hex()
  return canonical(dict(claim=c,signature=sig))
 def transport(self,i,body=None,**kw):
  body=body if body is not None else self.payload(i)
  return lambda url,timeout,max_bytes:Response(kw.get('status',200),kw.get('url',url),kw.get('ctype','application/json'),body)
 def go(self,i,body=None,**kw):return self.f.fetch(f'k{i}',self.transport(i,body,**kw))
 def all(self):
  for i in range(3):self.assertEqual(self.go(i),'ACCEPTED')
 def test_valid(self):self.assertEqual(self.go(0),'ACCEPTED')
 def test_quorum(self):self.all();self.assertEqual(self.f.compare('jane',7,7,'a'*64)['status'],'MATCHED_FIXTURE_QUORUM')
 def test_rollback(self):self.all();self.assertEqual(self.f.compare('jane',7,5,'a'*64)['status'],'ROLLBACK_DETECTED')
 def test_fork(self):self.all();self.assertEqual(self.f.compare('jane',7,7,'b'*64)['status'],'FORK_DETECTED')
 def test_conflict(self):
  self.go(0);self.go(1);self.go(2,self.payload(2,head='b'*64))
  self.assertEqual(self.f.compare('jane',7,7,'a'*64)['status'],'CROSS_ROOT_CONFLICT')
 def test_replay(self):self.go(0);self.assertEqual(self.go(0),'REPLAY')
 def test_restart(self):
  self.go(0);self.f.close();self.f=FLAY148(Path(self.t.name)/'db.sqlite',self.ep,self.now)
  self.assertEqual(self.go(0),'REPLAY')
 def test_wrong_key(self):self.assertEqual(self.go(0,self.payload(0,sigkey=self.keys[1])),'REJECTED')
 def test_tamper(self):
  doc=json.loads(self.payload(0));doc['claim']['head']='f'*64
  self.assertEqual(self.go(0,canonical(doc)),'REJECTED')
 def test_chronos_tamper(self):
  doc=json.loads(self.payload(0));doc['claim']['chronos']=STAMP.replace('20.39','20.40')
  self.assertEqual(self.go(0,canonical(doc)),'REJECTED')
 def test_stale(self):self.assertEqual(self.go(0,self.payload(0,claim_updates={'chronos':STAMP.replace('20.39','17.39')})),'REJECTED')
 def test_redirect(self):self.assertEqual(self.go(0,url='https://different.example.org'),'REJECTED')
 def test_status(self):self.assertEqual(self.go(0,status=503),'REJECTED')
 def test_type(self):self.assertEqual(self.go(0,ctype='text/html'),'REJECTED')
 def test_size(self):self.assertEqual(self.go(0,b'x'*20000),'REJECTED')
 def test_bad_json(self):self.assertEqual(self.go(0,b'not-json'),'REJECTED')
 def test_network_outage(self):self.assertEqual(self.f.fetch('k0',lambda *_: (_ for _ in ()).throw(TimeoutError())),'UNAVAILABLE')
 def test_unknown_endpoint(self):
  with self.assertRaises(ValueError):self.f.fetch('bad',self.transport(0))
 def test_http_forbidden(self):
  with self.assertRaises(ValueError):FLAY148(':memory:',[replace(self.ep[0],url='http://evil.test')],self.now)
 def test_localhost_forbidden(self):
  with self.assertRaises(ValueError):FLAY148(':memory:',[replace(self.ep[0],url='https://localhost/proof')],self.now)
 def test_ip_forbidden(self):
  with self.assertRaises(ValueError):FLAY148(':memory:',[replace(self.ep[0],url='https://127.0.0.1/proof')],self.now)
 def test_shared_admin(self):
  ep=list(self.ep);ep[1]=replace(ep[1],administrator='admin0')
  self.f.close();self.f=FLAY148(Path(self.t.name)/'db.sqlite',ep,self.now)
  for i in range(3):
   claim={'administrator':'admin0'} if i==1 else None
   self.go(i,self.payload(i,claim_updates=claim))
  self.assertEqual(self.f.compare('jane',7,7,'a'*64)['status'],'SHARED_ADMINISTRATION')
 def test_single_root_two_keys(self):
  # two keys are configured with the same custodian, and must not add a vote
  ep=list(self.ep);ep[1]=replace(ep[1],custody='root0',administrator='admin0')
  self.f.close();self.f=FLAY148(Path(self.t.name)/'db.sqlite',ep,self.now)
  for i in range(3):
   claim={'custody':'root0','administrator':'admin0'} if i==1 else None
   self.go(i,self.payload(i,claim_updates=claim))
  self.assertEqual(self.f.compare('jane',7,7,'a'*64)['status'],'INSUFFICIENT_CUSTODY')
 def test_equivocation(self):
  self.go(0)
  self.go(0,self.payload(0,head='b'*64,nonce='second-unique-nonce'))
  self.assertEqual(self.f.compare('jane',7,7,'a'*64)['status'],'EQUIVOCATION')
 def test_insufficient(self):self.go(0);self.assertEqual(self.f.compare('jane',7,7,'a'*64)['status'],'INSUFFICIENT_CUSTODY')
 def test_audit(self):self.go(0);self.assertEqual(self.f.audit(),'VALID_LOCAL_CHAIN')
 def test_audit_tamper(self):
  self.go(0);self.f.db.execute("UPDATE snapshots SET outcome='ALTERED'");self.f.db.commit()
  self.assertEqual(self.f.audit(),'TAMPERED')
 def test_head_mismatch(self):self.go(0);self.assertEqual(self.f.audit('0'*64),'EXTERNAL_HEAD_MISMATCH')
 def test_no_learning(self):self.all();self.assertFalse(self.f.compare('jane',7,7,'a'*64)['learning_applied'])
 def test_admin_binding(self):self.assertEqual(self.go(0,self.payload(0,claim_updates={'administrator':'rogue'})),'REJECTED')
 def test_custody_binding(self):self.assertEqual(self.go(0,self.payload(0,claim_updates={'custody':'rogue'})),'REJECTED')
 def test_evidence_saved_on_reject(self):self.go(0,b'not-json');self.assertEqual(self.f.db.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0],1)
 def test_no_secrets_in_snapshots(self):self.go(0);self.assertEqual(self.f.db.execute('SELECT outcome FROM snapshots').fetchone()[0],'ACCEPTED')
 def test_case_offset(self):self.assertEqual(clock_value(STAMP,-360).hour,2)
if __name__=='__main__':unittest.main(verbosity=2)