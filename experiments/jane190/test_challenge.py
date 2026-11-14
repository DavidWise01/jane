import unittest,tempfile,os,copy
from challenge import *

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=os.path.join(self.tmp.name,'state.db');self.keys,self.pack=fixture();self.a=Audit(self.path,self.keys)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def submit(self,p=None,now=150):return self.a.accept(*(p or self.pack),now=now)
 def resign(self,p,idx,role):
  sk=Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane190:'+role).encode()).digest())
  p[idx]=signed(role,p[idx]['body'],sk)
 def test_valid(self):self.assertEqual(self.submit(),'CHRONOLOGY_CONSISTENT_FIXTURE')
 def test_replay(self):self.submit();self.assertEqual(self.submit(),'REPLAY')
 def test_restart_replay(self):
  self.submit();self.a.close();self.a=Audit(self.path,self.keys);self.assertEqual(self.submit(),'REPLAY')
 def test_leak(self):self.assertEqual(self.submit(fixture(leaked_at=115)[1]),'PREMATURE_DISCLOSURE_REPORTED')
 def test_backdated_disclosure(self):
  p=copy.deepcopy(self.pack);p[2]['body']['at']=108;self.resign(p,2,'challenger');self.assertEqual(self.submit(p),'CAUSAL_ORDER_VIOLATION')
 def test_execution_before_disclosure(self):
  p=copy.deepcopy(self.pack);p[3]['body']['at']=118;self.resign(p,3,'executor');self.assertEqual(self.submit(p),'CAUSAL_ORDER_VIOLATION')
 def test_task_freeze_after_challenge(self):
  p=copy.deepcopy(self.pack);p[0]['body']['at']=115;self.resign(p,0,'task');self.assertEqual(self.submit(p),'CAUSAL_ORDER_VIOLATION')
 def test_task_mutation(self):
  p=copy.deepcopy(self.pack);p[0]['body']['task']['input']=99;self.resign(p,0,'task');self.assertEqual(self.submit(p),'TASK_BINDING_CONFLICT')
 def test_effect_wrong_nonce(self):
  p=copy.deepcopy(self.pack);p[4][0]['body']['nonce']='f'*32;p[4][0]=signed('observer',p[4][0]['body'],Ed25519PrivateKey.from_private_bytes(hashlib.sha256(b'jane190:observer').digest()));self.assertEqual(self.submit(p),'EFFECT_CONFLICT')
 def test_effect_wrong_output(self):
  p=copy.deepcopy(self.pack);p[4][0]['body']['output_hash']='a'*64;p[4][0]=signed('observer',p[4][0]['body'],Ed25519PrivateKey.from_private_bytes(hashlib.sha256(b'jane190:observer').digest()));self.assertEqual(self.submit(p),'EFFECT_CONFLICT')
 def test_forgery(self):
  p=copy.deepcopy(self.pack);p[3]['body']['at']=140;self.assertEqual(self.submit(p),'BAD_SIGNATURE_OR_ROLE')
 def test_wrong_role(self):
  p=copy.deepcopy(self.pack);p[3]['role']='observer';self.assertEqual(self.submit(p),'BAD_SIGNATURE_OR_ROLE')
 def test_future(self):self.assertEqual(self.submit(now=120),'STALE_OR_FUTURE_EXECUTION')
 def test_stale(self):self.assertEqual(self.submit(now=1000),'STALE_OR_FUTURE_EXECUTION')
 def test_no_effects(self):
  p=copy.deepcopy(self.pack);p[4]=[];self.assertEqual(self.submit(p),'UNCORROBORATED_EXECUTION')
 def test_one_effect(self):
  p=copy.deepcopy(self.pack);p[4]=p[4][:1];self.assertEqual(self.submit(p),'INSUFFICIENT_OBSERVERS')
 def test_shared_source(self):
  p=copy.deepcopy(self.pack);p[4][1]['body']['source_root']='source-0';p[4][1]=signed('observer',p[4][1]['body'],Ed25519PrivateKey.from_private_bytes(hashlib.sha256(b'jane190:observer').digest()));self.assertEqual(self.submit(p),'SHARED_OBSERVER_ANCESTRY')
 def test_bad_nonce(self):
  p=copy.deepcopy(self.pack);p[1]['body']['nonce']='oops';self.resign(p,1,'challenger');self.assertEqual(self.submit(p),'BAD_NONCE')
 def test_challenge_mismatch(self):
  p=copy.deepcopy(self.pack);p[2]['body']['nonce']='f'*32;self.resign(p,2,'challenger');self.assertEqual(self.submit(p),'CHALLENGE_BINDING_CONFLICT')
 def test_expired_window(self):
  p=copy.deepcopy(self.pack);p[3]['body']['at']=250;self.resign(p,3,'executor');self.assertEqual(self.submit(p,now=260),'EXECUTION_WINDOW_EXCEEDED')
 def test_ledger(self):self.submit();self.assertEqual(self.a.audit_chain(),'VALID_LOCAL_CHAIN')
 def test_external_head(self):self.submit();self.assertEqual(self.a.audit_chain('a'*64),'EXTERNAL_HEAD_MISMATCH')
 def test_tampered_ledger(self):
  self.submit();self.a.db.execute("update events set kind='FORGED' where id=1");self.a.db.commit();self.assertEqual(self.a.audit_chain(),'TAMPERED')
 def test_parent_frozen(self):self.submit();self.assertEqual(self.a.active,'frozen_parent')
 def test_fixture_deterministic(self):self.assertEqual(fixture()[1],fixture()[1])
 def test_demo(self):self.assertEqual(demo()['valid'],'CHRONOLOGY_CONSISTENT_FIXTURE')
 def test_demo_leak(self):self.assertEqual(demo()['reported_leak'],'PREMATURE_DISCLOSURE_REPORTED')
 def test_invalid_policy(self):
  with self.assertRaises(ValueError):Policy(max_lag=0)
 def test_empty_keys(self):
  self.a.close();self.a=Audit(self.path,{});self.assertEqual(self.submit(),'BAD_SIGNATURE_OR_ROLE')
 def test_chronos_not_integer(self):
  p=copy.deepcopy(self.pack);p[1]['body']['at']='110';self.resign(p,1,'challenger');self.assertEqual(self.submit(p),'BAD_CHRONOS')
if __name__=='__main__':unittest.main(verbosity=2)