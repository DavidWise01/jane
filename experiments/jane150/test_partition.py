import unittest
from dataclasses import replace
from partition import *

class PartitionTests(unittest.TestCase):
    def setUp(self):
        self.p,self.r=demo()
    def test_fork(self):self.assertEqual(self.r['status'],'PARTITION_FORK')
    def test_ancestor(self):self.assertEqual(self.r['ancestor']['sequence'],3)
    def test_two_branches(self):self.assertEqual(len(self.r['branches']),2)
    def test_same_seq(self):self.assertEqual(self.r['branches']['A']['sequence'],5)
    def test_quorum_A(self):self.assertTrue(self.r['branches']['A']['fixture_quorum'])
    def test_quorum_B_insufficient(self):self.assertFalse(self.r['branches']['B']['fixture_quorum'])
    def test_no_merge(self):self.assertFalse(self.r['automatic_merge'])
    def test_no_learning(self):self.assertFalse(self.r['learning_applied'])
    def test_preserve(self):self.assertTrue(self.r['preserve_both'])
    def test_parent(self):self.assertEqual(self.r['active'],'frozen_parent')
    def test_deterministic(self):self.assertEqual(demo()[1],self.r)
    def test_audit(self):self.assertEqual(self.p.audit(),'VALID_LOCAL_CHAIN')
    def test_external_head(self):self.assertEqual(self.p.audit('f'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_audit_tamper(self):self.p.events[0]['kind']='fake';self.assertEqual(self.p.audit(),'TAMPERED')
    def test_invalid_chain(self):
        chain=extend((),'a');invalid=tuple([replace(chain[0],head='f'*64)])
        self.assertFalse(validate(invalid))
    def test_no_duplicate_mirror(self):
        a=self.p.branches['A'];b=self.p.branches['B']
        cs=[Claim('A','github','one',5,a[-1].head,True),Claim('A','0root.ai','one',5,a[-1].head,True)]
        q=Partition({'A':a,'B':b},cs);self.assertEqual(q.assess()['branches']['A']['eligible_root_count'],1)
    def test_mirror_conflicting_admin(self):
        a=self.p.branches['A'];b=self.p.branches['B']
        cs=[Claim('A','github','one',5,a[-1].head,True),Claim('A','0root.ai','two',5,a[-1].head,True)]
        q=Partition({'A':a,'B':b},cs);self.assertEqual(q.assess()['branches']['A']['eligible_root_count'],0)
    def test_double_signed_conflict(self):
        a=self.p.branches['A'];b=self.p.branches['B']
        cs=[Claim('A','external:x','admin',5,a[-1].head,True),Claim('B','external:x','admin',5,b[-1].head,True)]
        q=Partition({'A':a,'B':b},cs);self.assertIn('external:x',q.assess()['disqualified_roots'])
    def test_unsigned_not_counted(self):
        a=self.p.branches['A'];b=self.p.branches['B']
        q=Partition({'A':a,'B':b},[Claim('A','x','admin',5,a[-1].head,False)])
        self.assertEqual(q.assess()['branches']['A']['eligible_root_count'],0)
    def test_identical_history(self):
        a=self.p.branches['A'];q=Partition({'A':a,'B':a},[])
        self.assertEqual(q.assess()['status'],'SAME_HISTORY')
    def test_prefix(self):
        a=self.p.branches['A'];q=Partition({'A':a[:4],'B':a},[])
        self.assertEqual(q.assess()['status'],'PREFIX_CONTINUATION')
    def test_missing_chain_event(self):
        a=self.p.branches['A'];self.assertFalse(validate(a[:3]+a[4:]))
    def test_max_chain(self):
        a=();
        for i in range(129):a=extend(a,str(i))
        self.assertFalse(validate(a))
    def test_bad_branch_count(self):
        a=self.p.branches['A'];p=Partition({'A':a},[])
        with self.assertRaises(ValueError):p.assess()
    def test_unknown_branch_claim(self):
        a=self.p.branches['A'];b=self.p.branches['B']
        p=Partition({'A':a,'B':b},[Claim('C','external:x','x',5,'a'*64,True)])
        with self.assertRaises(ValueError):p.assess()
    def test_bad_admin(self):
        a=self.p.branches['A'];b=self.p.branches['B']
        p=Partition({'A':a,'B':b},[Claim('A','external:x','',5,a[-1].head,True)])
        with self.assertRaises(ValueError):p.assess()
    def test_empty_chains_same(self):
        self.assertEqual(Partition({'A':(),'B':()},[]).assess()['status'],'SAME_HISTORY')
    def test_separate_paths(self):self.assertNotEqual(self.p.branches['A'][-1].head,self.p.branches['B'][-1].head)
    def test_head_length(self):self.assertEqual(len(self.r['ancestor']['head']),64)
    def test_initial_event(self):self.assertEqual(self.p.events[0]['kind'],'DECLARE')

if __name__=='__main__':unittest.main(verbosity=2)
