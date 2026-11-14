import unittest,tempfile,os,copy
from pathlib import Path
from delivery import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.path=str(Path(self.temp.name)/'db.sqlite');self.s=key('sender');self.r=key('receiver')
  self.m=manifest([b'alpha',b'beta',b'gamma']);self.S=sign(self.m,self.s,'sender')
  self.acks=[sign(ack(e['seq'],e['payload_hash'],'ack-'+str(e['seq']),1050),self.r,'receiver') for e in self.m['entries']]
  self.f=FLAY(self.path,self.s.public_key(),self.r.public_key())
 def run_case(self,acks=None,now=1500,signed=None):return self.f.receive(signed or self.S,self.acks if acks is None else acks,now)
 def test_complete(self):self.assertEqual(self.run_case()['status'],'DELIVERY_COMPLETE_FIXTURE')
 def test_omission(self):self.assertEqual(self.run_case([self.acks[0],self.acks[2]])['missing'],[2])
 def test_overdue(self):self.assertEqual(self.run_case([self.acks[0],self.acks[2]])['status'],'SELECTIVE_SUPPRESSION')
 def test_pending(self):self.assertEqual(self.run_case([self.acks[0]],1200)['status'],'DELIVERY_PENDING')
 def test_no_receipts(self):self.assertEqual(self.run_case([])['overdue'],[1,2,3])
 def test_replay(self):self.run_case();self.assertEqual(self.run_case()['status'],'REPLAY')
 def test_replay_restart(self):self.run_case();g=FLAY(self.path,self.s.public_key(),self.r.public_key());self.assertEqual(g.receive(self.S,self.acks,1500)['status'],'REPLAY')
 def test_sender_forgery(self):
  x=copy.deepcopy(self.S);x['body']['root']='0'*64;self.assertEqual(self.run_case(signed=x)['status'],'BAD_SENDER_SIGNATURE')
 def test_receiver_forgery(self):
  x=copy.deepcopy(self.acks);x[0]['body']['seq']=2;self.assertEqual(self.run_case(x)['status'],'BAD_RECEIVER_SIGNATURE')
 def test_bad_receiver_signer(self):
  x=[sign(self.acks[0]['body'],self.s,'sender')];self.assertEqual(self.run_case(x)['status'],'BAD_RECEIVER_SIGNATURE')
 def test_ack_wrong_hash(self):
  x=[sign(ack(1,'0'*64,'newnonce',1050),self.r,'receiver')];self.assertEqual(self.run_case(x)['status'],'ACK_PAYLOAD_CONFLICT')
 def test_unexpected_ack(self):
  x=[sign(ack(4,'0'*64,'newnonce',1050),self.r,'receiver')];self.assertEqual(self.run_case(x)['status'],'UNEXPECTED_ACK')
 def test_duplicate_ack(self):self.assertEqual(self.run_case([self.acks[0],self.acks[0]])['status'],'DUPLICATE_ACK')
 def test_conflicting_ack(self):
  x=sign(ack(1,self.m['entries'][0]['payload_hash'],'other',1051),self.r,'receiver');self.assertEqual(self.run_case([self.acks[0],x])['status'],'CONFLICTING_ACK')
 def test_duplicate_nonce(self):
  x=sign(ack(2,self.m['entries'][1]['payload_hash'],'ack-1',1050),self.r,'receiver');self.assertEqual(self.run_case([self.acks[0],x])['status'],'DUPLICATE_NONCE')
 def test_future_ack(self):
  x=sign(ack(1,self.m['entries'][0]['payload_hash'],'x',1800),self.r,'receiver');self.assertEqual(self.run_case([x])['status'],'BAD_ACK')
 def test_ancient_ack(self):
  x=sign(ack(1,self.m['entries'][0]['payload_hash'],'x',900),self.r,'receiver');self.assertEqual(self.run_case([x])['status'],'BAD_ACK')
 def test_bad_chronos(self):self.assertEqual(self.run_case(now=999)['status'],'BAD_CHRONOS')
 def test_bad_manifest_size(self):
  m=copy.deepcopy(self.m);m['size']=4;self.assertEqual(self.run_case(signed=sign(m,self.s,'sender'))['status'],'BAD_MANIFEST')
 def test_bad_manifest_root(self):
  m=copy.deepcopy(self.m);m['root']='0'*64;self.assertEqual(self.run_case(signed=sign(m,self.s,'sender'))['status'],'BAD_MANIFEST')
 def test_bad_manifest_order(self):
  m=copy.deepcopy(self.m);m['entries'][0]['seq']=3;m['root']=sha(m['entries']);self.assertEqual(self.run_case(signed=sign(m,self.s,'sender'))['status'],'BAD_MANIFEST')
 def test_fork(self):
  self.run_case([]);m=copy.deepcopy(self.m);m['nonce']='new';m['entries'][0]['payload_hash']='0'*64;m['root']=sha(m['entries']);self.assertEqual(self.run_case([],signed=sign(m,self.s,'sender'))['status'],'SIGNED_OUTBOX_FORK')
 def test_local_ledger(self):self.run_case();self.assertEqual(self.f.audit(),'VALID_LOCAL_CHAIN')
 def test_ledger_tamper(self):
  self.run_case()
  with self.f.db() as c:c.execute("UPDATE observations SET code='FAKE' WHERE id=0")
  self.assertEqual(self.f.audit(),'TAMPERED')
 def test_frozen(self):self.assertEqual(self.run_case()['active_parent'],'frozen_parent')
 def test_no_learning(self):self.assertFalse(self.run_case()['learning_applied'])
 def test_no_physical_custody(self):self.assertFalse(self.run_case()['independent_custody_verified'])
 def test_outbox_bound(self):
  with self.assertRaises(ValueError):manifest([b'a']*129)
 def test_empty_outbox(self):
  with self.assertRaises(ValueError):manifest([])
 def test_ack_set_limit(self):self.assertEqual(self.run_case(self.acks*43)['status'],'BAD_ACK_SET')
 def test_digest_determinism(self):self.assertEqual(manifest([b'a']),manifest([b'a']))
 def test_payload_different(self):self.assertNotEqual(manifest([b'a'])['root'],manifest([b'b'])['root'])
 def test_outbox_nonempty(self):self.assertEqual(self.m['size'],3)
 def test_no_relay_trust(self):self.assertEqual(self.run_case([self.acks[0]])['missing'],[2,3])
 def test_early_missing_not_suppressed(self):self.assertEqual(self.run_case([],1200)['status'],'DELIVERY_PENDING')
 def test_exact_deadline(self):self.assertEqual(self.run_case([],1300)['status'],'DELIVERY_PENDING')
 def test_deadline_plus_one(self):self.assertEqual(self.run_case([],1301)['status'],'SELECTIVE_SUPPRESSION')
 def test_forged_manifest_signer(self):self.assertEqual(self.run_case(signed=sign(self.m,self.r,'receiver'))['status'],'BAD_SENDER_SIGNATURE')
 def test_ack_nonce_restart(self):
  self.run_case();m=manifest([b'alpha',b'beta',b'gamma'],2,'outbox-002');g=FLAY(self.path,self.s.public_key(),self.r.public_key());self.assertEqual(g.receive(sign(m,self.s,'sender'),self.acks,1500)['status'],'REPLAY')
 def test_valid_new_epoch(self):
  self.run_case();m=manifest([b'alpha',b'beta',b'gamma'],2,'outbox-002');a=[sign(ack(e['seq'],e['payload_hash'],'next-'+str(e['seq']),1100),self.r,'receiver') for e in m['entries']];self.assertEqual(self.f.receive(sign(m,self.s,'sender'),a,1500)['status'],'DELIVERY_COMPLETE_FIXTURE')
 def test_state_proof(self):self.assertEqual(self.run_case()['outbox_size'],3)
 def test_ack_hash(self):self.assertEqual(self.acks[0]['body']['payload_hash'],self.m['entries'][0]['payload_hash'])
 def test_ledger_persists(self):
  self.run_case();g=FLAY(self.path,self.s.public_key(),self.r.public_key());self.assertEqual(g.audit(),'VALID_LOCAL_CHAIN')
 def test_missing_order(self):self.assertEqual(self.run_case([self.acks[2]])['missing'],[1,2])
 def test_opaque_bytes(self):self.assertNotEqual(manifest([b'\x00'])['root'],manifest([b'\x01'])['root'])
 def test_fixture(self):
  f,_,_,r=fixture();self.assertEqual(r['status'],'SELECTIVE_SUPPRESSION');self.assertEqual(f.audit(),'VALID_LOCAL_CHAIN')
if __name__=='__main__':unittest.main(verbosity=2)