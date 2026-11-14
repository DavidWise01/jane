import unittest,tempfile,os,copy
from consistency import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.keys=[fixture_key('w'+str(i),'admin'+str(i)) for i in range(3)]
  self.old=[leaf({'i':i}) for i in range(6)]
  self.new=self.old+[leaf({'i':i}) for i in range(6,9)]
  self.audit=Audit(self.keys)
 def tearDown(self):self.audit.close()
 def receipts(self,old=None,new=None,keys=None):
  k=keys or self.keys
  return checkpoint(old if old is not None else self.old,k,6,'old'),checkpoint(new if new is not None else self.new,k,9,'new')
 def run_case(self,proof=None,old=None,new=None,keys=None):
  a,b=self.receipts(old,new,keys)
  return self.audit.reconcile(a,b,proof if proof is not None else make_proof(self.old,self.new))
 def test_success(self):self.assertEqual(self.run_case(),'CONSISTENT_APPEND_ONLY_FIXTURE')
 def test_demo(self):self.assertEqual(demo()['status'],'CONSISTENT_APPEND_ONLY_FIXTURE')
 def test_old_root(self):self.assertNotEqual(root(self.old),root(self.new))
 def test_empty_root(self):self.assertTrue(is_hash(root([])))
 def test_leaf_domain(self):self.assertNotEqual(leaf({'a':1}),h(enc({'a':1})))
 def test_old_root_rebuilt(self):self.assertEqual(root(make_proof(self.old,self.new)['prefix']),root(self.old))
 def test_tampered_old_prefix(self):
  p=make_proof(self.old,self.new);p['prefix'][0]=leaf({'oops':1});self.assertEqual(self.run_case(p),'OLD_ROOT_MISMATCH')
 def test_reordered_new(self):
  change=self.new[:];change[1],change[2]=change[2],change[1]
  a,b=self.receipts(new=change)
  self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,change)),'PREFIX_NOT_PRESERVED')
 def test_rewritten_new(self):
  change=self.new[:];change[3]=leaf({'evil':True})
  a,b=self.receipts(new=change)
  self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,change)),'PREFIX_NOT_PRESERVED')
 def test_missing_old_inclusion(self):
  p=make_proof(self.old,self.new);p['paths'].pop();self.assertEqual(self.run_case(p),'INCOMPLETE_PROOF')
 def test_inclusion_modified(self):
  p=make_proof(self.old,self.new);p['paths'][0][0][1]='f'*64;self.assertEqual(self.run_case(p),'PREFIX_NOT_PRESERVED')
 def test_side_modified(self):
  p=make_proof(self.old,self.new);p['paths'][0][0][0]='L';self.assertEqual(self.run_case(p),'PREFIX_NOT_PRESERVED')
 def test_fake_size(self):
  p=make_proof(self.old,self.new);p['new_size']=10;self.assertEqual(self.run_case(p),'INVALID_PROOF_DOMAIN')
 def test_fake_kind(self):
  p=make_proof(self.old,self.new);p['kind']='claim';self.assertEqual(self.run_case(p),'INVALID_PROOF_DOMAIN')
 def test_short_new(self):
  short=self.old[:4];a,b=self.receipts(new=short)
  self.assertEqual(self.audit.reconcile(a,b,make_proof(short,short)),'ROLLBACK_OR_REPLAY')
 def test_equal_head_new_epoch(self):
  a,b=self.receipts(new=self.old)
  self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,self.old)),'CONSISTENT_APPEND_ONLY_FIXTURE')
 def test_replay(self):
  self.run_case();self.assertEqual(self.run_case(),'REPLAY')
 def test_signature_tamper(self):
  a,b=self.receipts();b[0]['signature']='00'*64
  self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,self.new)),'BAD_SIGNATURE')
 def test_conflicting_checkpoint(self):
  a,b=self.receipts();b[0]['body']=dict(b[0]['body'],root='f'*64)
  self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,self.new)),'BAD_SIGNATURE')
 def test_shared_administration(self):
  keys=[fixture_key('a'+str(i),'same') for i in range(3)]
  a,b=self.receipts(keys=keys)
  self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,self.new)),'BAD_SIGNATURE') # unregistered keys
 def test_duplicate_signer(self):
  a,b=self.receipts();b.append(b[0]);self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,self.new)),'DUPLICATE_SIGNER')
 def test_unsigned_claim(self):
  a,b=self.receipts();b[1]['signature']='zz'
  self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,self.new)),'BAD_SIGNATURE')
 def test_bad_index(self):
  with self.assertRaises(ValueError):path(self.old,999)
 def test_truncated_proof(self):self.assertFalse(verify_path(self.old[0],0,6,[] ,root(self.old)))
 def test_wrong_total(self):self.assertFalse(verify_path(self.old[0],0,7,path(self.old,0),root(self.old)))
 def test_wrong_index(self):self.assertFalse(verify_path(self.old[0],1,6,path(self.old,0),root(self.old)))
 def test_path_roundtrips(self):
  for n in range(1,16):
   l=[leaf(i) for i in range(n)]
   for i in range(n):self.assertTrue(verify_path(l[i],i,n,path(l,i),root(l)))
 def test_ledger(self):
  self.run_case();self.assertEqual(self.audit.audit_chain(),'VALID_LOCAL_CHAIN')
 def test_ledger_mutation(self):
  self.run_case();self.audit.db.execute("UPDATE audit SET entry='bad' WHERE seq=1");self.audit.db.commit()
  self.assertEqual(self.audit.audit_chain(),'TAMPERED')
 def test_persist_nonce(self):
  t=tempfile.NamedTemporaryFile(delete=False);name=t.name;t.close()
  try:
   db=Audit(self.keys,name);a,b=self.receipts();p=make_proof(self.old,self.new)
   self.assertEqual(db.reconcile(a,b,p),'CONSISTENT_APPEND_ONLY_FIXTURE');db.close()
   db=Audit(self.keys,name);self.assertEqual(db.reconcile(a,b,p),'REPLAY');db.close()
  finally:os.unlink(name)
 def test_budget_old(self):
  a=Audit(self.keys,max_old=5)
  try:
   x,y=self.receipts();self.assertEqual(a.reconcile(x,y,make_proof(self.old,self.new)),'INVALID_PROOF_DOMAIN')
  finally:a.close()
 def test_bad_proof_root(self):
  p=make_proof(self.old,self.new);p['prefix'][1]='nonsense'
  self.assertEqual(self.run_case(p),'OLD_ROOT_MISMATCH')
 def test_valid_new_inclusion(self):
  for i,x in enumerate(self.new):self.assertTrue(verify_path(x,i,len(self.new),path(self.new,i),root(self.new)))
 def test_scope(self):self.assertFalse(demo()['independence_verified'])
 def test_parent(self):self.assertFalse(demo()['active_parent_changed'])
 def test_previous_root_link_not_required(self):self.assertNotIn('previous_root',self.receipts()[1][0]['body'])
 def test_false_signed_replacement(self):
  # two independently signed roots alone cannot certify preservation
  other=[leaf({'i':i,'new':True}) for i in range(9)];a,b=self.receipts(new=other)
  self.assertEqual(self.audit.reconcile(a,b,make_proof(self.old,other)),'PREFIX_NOT_PRESERVED')
if __name__=='__main__':unittest.main(verbosity=2)