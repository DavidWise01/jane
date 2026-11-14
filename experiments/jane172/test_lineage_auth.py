import unittest, copy
from lineage_auth import Registry,LineageAudit,demo
class TestLineage(unittest.TestCase):
 def setUp(self):
  self.r=Registry()
  for n,role in [('a','sensor'),('b','sensor'),('c','sensor'),('hub','broker'),('root','source'),('root2','source'),('root3','source')]:self.r.add_fixture(n,role,n+'_admin')
  self.recs=[self.r.receipt('a','hub','1'),self.r.receipt('b','hub','2'),self.r.receipt('c','hub','3'),self.r.receipt('hub','root','4')]
 def check(self,recs=None,reports=None,now=1000):return LineageAudit(self.r,now=now).verify(self.recs if recs is None else recs,['a','b','c'] if reports is None else reports)
 def test_shared(self):self.assertEqual(self.check()['root_count'],1)
 def test_shared_status(self):self.assertEqual(self.check()['status'],'SHARED_MEASUREMENT_ANCESTRY')
 def test_independent_fixture(self):
  recs=[self.r.receipt('a','root','5'),self.r.receipt('b','root2','6'),self.r.receipt('c','root3','7')]
  self.assertEqual(self.check(recs)['status'],'DECLARED_ROOT_QUORUM')
 def test_not_verified(self):self.assertFalse(self.check()['independence_verified'])
 def test_no_learning(self):self.assertFalse(self.check()['learning_applied'])
 def test_frozen(self):self.assertEqual(self.check()['active_parent'],'frozen')
 def test_forged_child(self):
  recs=copy.deepcopy(self.recs);recs[0]['child_signature']='00'*64
  self.assertIn('BAD_EDGE_SIGNATURE',self.check(recs)['rejections'])
 def test_forged_parent(self):
  recs=copy.deepcopy(self.recs);recs[0]['parent_signature']='00'*64
  self.assertIn('BAD_EDGE_SIGNATURE',self.check(recs)['rejections'])
 def test_tampered_claim(self):
  recs=copy.deepcopy(self.recs);recs[0]['claim']['parent']='root'
  self.assertIn('BAD_EDGE_SIGNATURE',self.check(recs)['rejections'])
 def test_missing_edge(self):self.assertIn('MISSING_SIGNED_EDGE',self.check(self.recs[1:])['rejections'])
 def test_missing_root_edge(self):self.assertIn('MISSING_SIGNED_EDGE',self.check(self.recs[:3])['rejections'])
 def test_duplicate_edge(self):self.assertIn('DUPLICATE_EDGE',self.check(self.recs+[self.r.receipt('a','hub','new')])['rejections'])
 def test_reused_nonce(self):self.assertIn('NONCE_REPLAY',self.check(self.recs+[self.r.receipt('a','root','1')])['rejections'])
 def test_conflicting_parent(self):self.assertIn('CONFLICTING_PARENTS',self.check(self.recs+[self.r.receipt('a','root','new')])['rejections'])
 def test_cycle(self):
  self.r.add_fixture('hub2','broker','other')
  recs=[self.r.receipt('a','hub','x'),self.r.receipt('hub','hub2','y'),self.r.receipt('hub2','hub','z')]
  self.assertIn('LINEAGE_CYCLE',self.check(recs,['a'])['rejections'])
 def test_self(self):self.assertIn('SELF_EDGE',self.check([self.r.receipt('hub','hub','x')],[])['rejections'])
 def test_source_parent(self):self.assertIn('SOURCE_HAS_PARENT',self.check([self.r.receipt('root','hub','x')],[])['rejections'])
 def test_sensor_parent(self):self.assertIn('INVALID_PARENT_ROLE',self.check([self.r.receipt('b','a','x')],[])['rejections'])
 def test_stale(self):self.assertIn('STALE_OR_FUTURE',self.check(now=2000)['rejections'])
 def test_future(self):self.assertIn('STALE_OR_FUTURE',self.check(now=999)['rejections'])
 def test_bad_schema(self):
  recs=copy.deepcopy(self.recs);recs[0]['claim']['extra']=1
  self.assertIn('INVALID_SCHEMA',self.check(recs)['rejections'])
 def test_unknown(self):
  recs=copy.deepcopy(self.recs);recs[0]['claim']['parent']='unknown'
  self.assertIn('UNKNOWN_PRINCIPAL',self.check(recs)['rejections'])
 def test_duplicate_report(self):self.assertIn('DUPLICATE_REPORT',self.check(reports=['a','a'])['rejections'])
 def test_unknown_report(self):self.assertIn('INVALID_REPORTER',self.check(reports=['unknown'])['rejections'])
 def test_nonsensor_report(self):self.assertIn('INVALID_REPORTER',self.check(reports=['root'])['rejections'])
 def test_edge_budget(self):
  a=LineageAudit(self.r,max_edges=2)
  self.assertIn('EDGE_BUDGET_EXCEEDED',a.verify(self.recs,['a'])['rejections'])
 def test_ledger_valid(self):
  a=LineageAudit(self.r);a.verify(self.recs,['a']);self.assertEqual(a.audit_log(),'LOCAL_CHAIN_VALID')
 def test_ledger_tamper(self):
  a=LineageAudit(self.r);a.verify(self.recs,['a']);a.ledger[0]['kind']='forged';self.assertEqual(a.audit_log(),'TAMPERED')
 def test_external_head(self):
  a=LineageAudit(self.r);a.verify(self.recs,['a']);self.assertEqual(a.audit_log('f'*64),'ANCHOR_MISMATCH')
 def test_external_match(self):
  a=LineageAudit(self.r);a.verify(self.recs,['a']);self.assertEqual(a.audit_log(a.last),'LOCAL_CHAIN_VALID')
 def test_demo(self):self.assertEqual(demo()['separate']['root_count'],3)
 def test_demo_shared(self):self.assertEqual(demo()['shared']['root_count'],1)
 def test_no_independence_even_three(self):self.assertFalse(demo()['separate']['independence_verified'])
 def test_empty_reports(self):self.assertNotEqual(self.check(reports=[])['status'],'DECLARED_ROOT_QUORUM')
 def test_deterministic_roots(self):self.assertEqual(self.check()['declared_measurement_roots'],['root'])
 def test_immutable_declared_roots(self):self.assertEqual(self.check()['valid_edge_count'],4)
 def test_missing_signature(self):
  recs=copy.deepcopy(self.recs);del recs[0]['parent_signature']
  self.assertIn('BAD_EDGE_SIGNATURE',self.check(recs)['rejections'])
 def test_report_scope(self):self.assertIn('claimed',self.check()['scope'])
if __name__=='__main__':unittest.main(verbosity=2)