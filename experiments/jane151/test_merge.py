import unittest
from dataclasses import replace
from merge import *

class MergeTests(unittest.TestCase):
    def setUp(self):
        self.m,self.r,self.a,self.b=demo()
    def test_proposal(self):self.assertEqual(self.r['status'],'TWO_PARENT_REVIEW_PROPOSAL')
    def test_ancestor_sequence(self):self.assertEqual(self.r['ancestor_sequence'],3)
    def test_shared_count(self):self.assertEqual(self.r['shared_events'],4)
    def test_ancestor_head(self):self.assertEqual(self.r['ancestor_head'],self.a.events[3].head)
    def test_divergence(self):self.assertNotEqual(self.a.events[4].head,self.b.events[4].head)
    def test_both_parents(self):self.assertEqual({x['branch'] for x in self.r['parents']},{'MESH-A','MESH-B'})
    def test_tail_A(self):self.assertEqual(len(self.r['parents'][0]['tail_heads']),2)
    def test_tail_B(self):self.assertEqual(len(self.r['parents'][1]['tail_heads']),2)
    def test_refs(self):self.assertEqual(self.r['preserved_event_references'],8)
    def test_no_auto_merge(self):self.assertEqual(self.r['active'],'frozen_parent')
    def test_no_learning(self):self.assertFalse(self.r['learning_applied'])
    def test_no_authenticated_claim(self):self.assertFalse(self.r['evidence_authenticated'])
    def test_no_independent_claim(self):self.assertEqual(self.r['independent_witnesses_verified'],0)
    def test_auditable(self):self.assertEqual(self.m.audit(),'VALID_LOCAL_CHAIN')
    def test_deterministic(self):self.assertEqual(demo()[1],demo()[1])
    def test_declared_roots(self):self.assertEqual(len(self.r['parents'][0]['declared_roots']),3)
    def test_false_ancestor(self):self.assertEqual(Merger().propose(self.a,self.b,'f'*64)['status'],'FALSE_COMMON_ANCESTOR')
    def test_same_branch(self):self.assertEqual(Merger().propose(self.a,self.a)['status'],'INVALID_OR_SAME_BRANCH')
    def test_same_id(self):self.assertEqual(Merger().propose(self.a,replace(self.b,branch_id=self.a.branch_id))['status'],'INVALID_OR_SAME_BRANCH')
    def test_tamper(self):
        bad=list(self.a.events);bad[2]=replace(bad[2],payload='altered')
        self.assertEqual(Merger().propose(replace(self.a,events=tuple(bad)),self.b)['status'],'INVALID_OR_SAME_BRANCH')
    def test_missing_link(self):
        bad=tuple(x for i,x in enumerate(self.a.events) if i!=4)
        self.assertEqual(Merger().propose(replace(self.a,events=bad),self.b)['status'],'INVALID_OR_SAME_BRANCH')
    def test_no_common(self):
        a=build_branch('a',['A','B']);b=build_branch('b',['X','Y'])
        self.assertEqual(Merger().propose(a,b)['status'],'NO_SHARED_EVENT_ANCESTOR')
    def test_prefix(self):
        b=build_branch('B',['A','B','C']);a=build_branch('A',['A','B'])
        self.assertEqual(Merger().propose(a,b)['status'],'PREFIX_RELATION_NOT_FORK')
    def test_empty_root(self):
        a=build_branch('A',[]);b=build_branch('B',['something'])
        self.assertEqual(Merger().propose(a,b)['status'],'NO_SHARED_EVENT_ANCESTOR')
    def test_distinct_proposals_order_invariant(self):
        r=Merger().propose(self.b,self.a)
        self.assertEqual(r['proposal_digest'],self.r['proposal_digest'])
    def test_idempotence(self):
        self.assertEqual(self.m.propose(self.a,self.b)['proposal_digest'],self.r['proposal_digest'])
        self.assertEqual(len(self.m.events),1)
    def test_audit_mutated_event(self):
        self.m.events[0]['kind']='ALTERED';self.assertEqual(self.m.audit(),'TAMPERED')
    def test_audit_external_head(self):self.assertEqual(self.m.audit('f'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_audit_proposal_mutation(self):
        h=self.r['proposal_digest'];self.m.proposals[h]['shared_events']=100
        self.assertEqual(self.m.audit(),'PROPOSAL_TAMPERED')
    def test_event_length_budget(self):
        a=build_branch('A',[f'event {i}' for i in range(257)])
        self.assertEqual(Merger().propose(a,self.b)['status'],'INVALID_OR_SAME_BRANCH')
    def test_missing_branch(self):
        with self.assertRaises(ValueError):Merger().propose('a',self.b)
    def test_append_only_event(self):self.assertEqual(self.m.events[0]['kind'],'PROPOSE')
    def test_no_new_history_event(self):self.assertEqual(len(self.a.events),6)
    def test_no_change_parent(self):self.assertEqual(self.a.head,self.a.events[-1].head)
    def test_no_change_other(self):self.assertEqual(self.b.head,self.b.events[-1].head)
    def test_genesis(self):self.assertTrue(self.a.verified())
    def test_invalid_predecessor(self):
        x=list(self.b.events);x[1]=replace(x[1],predecessor=ZERO)
        self.assertFalse(replace(self.b,events=tuple(x)).verified())
    def test_invalid_head(self):
        x=list(self.a.events);x[-1]=replace(x[-1],head='f'*64)
        self.assertFalse(replace(self.a,events=tuple(x)).verified())
    def test_false_ancestor_audited(self):
        m=Merger();m.propose(self.a,self.b,'f'*64)
        self.assertEqual(m.audit(),'VALID_LOCAL_CHAIN')
    def test_chronos(self):self.assertTrue(CHRONOS.startswith('{{ 2026.11.13 }}'))
    def test_root_mirror_not_independent(self):
        self.assertEqual(self.r['independent_witnesses_verified'],0)
    def test_encoded_digest(self):self.assertEqual(len(self.r['proposal_digest']),64)

if __name__=='__main__': unittest.main(verbosity=2)