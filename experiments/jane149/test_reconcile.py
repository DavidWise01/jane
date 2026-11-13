import unittest
from dataclasses import replace
from reconcile import Checkpoint,Link,FLAY,make_link,demo
T='{{ 2026.11.12 }}{{ 22.02.00 }}{{ 123.45.56 }}'
class Tests(unittest.TestCase):
 def setUp(self):
  self.o=Checkpoint(4,'a'*64,'external:A',T);self.f=FLAY({'external:A':self.o});self.f.offline('external:A',T,'outage')
  self.a=make_link(5,self.o.head,'b'*64);self.b=make_link(6,self.a.head,'c'*64)
 def ret(self,seq=6,head=None,links=None):
  return self.f.returned('external:A',Checkpoint(seq,head if head is not None else self.b.head,'external:A',T),[self.a,self.b] if links is None else links,T)['status']
 def test_demo(self):self.assertEqual(demo()[1]['status'],'CATCHUP_ACCEPTED')
 def test_demo_audit(self):self.assertEqual(demo()[0].audit(),'VALID_LOCAL_CHAIN')
 def test_accept(self):self.assertEqual(self.ret(),'CATCHUP_ACCEPTED')
 def test_checkpoint_advance(self):self.ret();self.assertEqual(self.f.checkpoints['external:A'].sequence,6)
 def test_outage_clear(self):self.ret();self.assertNotIn('external:A',self.f.outages)
 def test_stale(self):self.assertEqual(self.ret(seq=3),'STALE_RETURN')
 def test_unchanged(self):self.assertEqual(self.ret(seq=4,head=self.o.head,links=[]),'UNCHANGED')
 def test_fork_same_sequence(self):self.assertEqual(self.ret(seq=4,head='f'*64,links=[]),'FORK')
 def test_missing_link(self):self.assertEqual(self.ret(links=[self.a]),'MISSING_LINKS')
 def test_empty_proof(self):self.assertEqual(self.ret(links=[]),'MISSING_LINKS')
 def test_bad_previous(self):self.assertEqual(self.ret(links=[replace(self.a,previous='f'*64),self.b]),'BROKEN_CONTINUITY')
 def test_bad_head(self):self.assertEqual(self.ret(links=[replace(self.a,head='f'*64),self.b]),'BROKEN_CONTINUITY')
 def test_bad_event(self):self.assertEqual(self.ret(links=[replace(self.a,event_digest='f'*64),self.b]),'BROKEN_CONTINUITY')
 def test_swapped_links(self):self.assertEqual(self.ret(links=[self.b,self.a]),'BROKEN_CONTINUITY')
 def test_fork_at_tip(self):self.assertEqual(self.ret(head='f'*64),'FORK')
 def test_budget(self):
  f=FLAY({'external:A':self.o},max_links=1);f.offline('external:A',T,'outage')
  self.assertEqual(f.returned('external:A',Checkpoint(6,self.b.head,'external:A',T),[self.a,self.b],T)['status'],'PROOF_BUDGET_EXCEEDED')
 def test_preserve_old_on_fork(self):self.ret(head='f'*64);self.assertEqual(self.f.checkpoints['external:A'].sequence,4)
 def test_outage_retained(self):self.ret(head='f'*64);self.assertIn('external:A',self.f.outages)
 def test_no_learning(self):self.assertFalse(demo()[1]['learning_applied'])
 def test_jane_gate(self):self.assertEqual(demo()[1]['jane_decision'],'UNDECIDED')
 def test_tamper(self):self.f.events[0]['kind']='CHANGED';self.assertEqual(self.f.audit(),'TAMPERED')
 def test_external_head(self):self.assertEqual(self.f.audit('f'*64),'EXTERNAL_HEAD_MISMATCH')
 def test_duplicate_outage(self):
  with self.assertRaises(ValueError):self.f.offline('external:A',T,'again')
 def test_unknown_root(self):
  with self.assertRaises(ValueError):self.f.offline('external:B',T,'outage')
 def test_no_outage_return(self):
  self.ret()
  with self.assertRaises(ValueError):self.f.returned('external:A',Checkpoint(7,'f'*64,'external:A',T),[],T)
 def test_bad_link(self):
  with self.assertRaises(ValueError):make_link(-1,'a'*64,'b'*64)
 def test_bad_budget(self):
  with self.assertRaises(ValueError):FLAY({'external:A':self.o},max_links=0)
 def test_wrong_root(self):
  self.assertEqual(self.f.returned('external:A',Checkpoint(6,self.b.head,'external:B',T),[self.a,self.b],T)['status'],'BAD_CLAIM')
 def test_bad_chronos(self):
  self.assertEqual(self.f.returned('external:A',Checkpoint(6,self.b.head,'external:A',''),[self.a,self.b],T)['status'],'BAD_CLAIM')
 def test_deterministic(self):self.assertEqual(demo()[0].events,demo()[0].events)
 def test_link_idempotent(self):self.assertEqual(self.a,make_link(5,self.o.head,'b'*64))
if __name__=='__main__':unittest.main(verbosity=2)
