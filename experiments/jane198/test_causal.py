import unittest
from dataclasses import replace
from fractions import Fraction
from causal import Observation,CausalCandidate,FLAY198,demo,digest

class Validation(unittest.TestCase):
    def test_no_empty(self):
        with self.assertRaises(ValueError):FLAY198([])
    def test_duplicate_round(self):
        with self.assertRaises(ValueError):FLAY198([Observation(1,'a',False,None)]*2)
    def test_negative_round(self):
        with self.assertRaises(ValueError):Observation(-1,'a',False,None)
    def test_missing_stratum(self):
        with self.assertRaises(ValueError):Observation(1,'',False,None)
    def test_nonbool_selection(self):
        with self.assertRaises(ValueError):Observation(1,'a',1,1)
    def test_missing_cannot_have_outcome(self):
        with self.assertRaises(ValueError):Observation(1,'a',False,1)
    def test_selected_needs_outcome(self):
        with self.assertRaises(ValueError):Observation(1,'a',True,None)
    def test_binary_outcome(self):
        with self.assertRaises(ValueError):Observation(1,'a',True,2)
    def test_invalid_latent(self):
        with self.assertRaises(ValueError):CausalCandidate('c',(2,),(1,),'x')
    def test_invalid_gate(self):
        with self.assertRaises(ValueError):CausalCandidate('c',(1,),(2,),'x')
    def test_candidate_lengths(self):
        with self.assertRaises(ValueError):CausalCandidate('c',(1,),(1,0),'x')
    def test_candidate_name(self):
        with self.assertRaises(ValueError):CausalCandidate('',(1,),(1,),'x')
    def test_projection_length(self):
        with self.assertRaises(ValueError):CausalCandidate('c',(1,),(1,),'x').projection([])
    def test_empty_candidates(self):
        with self.assertRaises(ValueError):demo()[0].compare([])
    def test_duplicate_candidate_name(self):
        c=CausalCandidate('same',(1,)*16,(0,)*16,'x')
        with self.assertRaises(ValueError):demo()[0].compare([c,c])

class Evidence(unittest.TestCase):
    def test_two_models_compatible(self):
        _,r=demo();self.assertEqual(r['compatible_count'],2)
    def test_nonidentifiable(self):
        _,r=demo();self.assertEqual(r['verdict'],'NONIDENTIFIABLE_COMPETING_MODELS')
    def test_identical_projection(self):
        _,r=demo();self.assertEqual(r['candidates'][0]['projected_digest'],r['candidates'][1]['projected_digest'])
    def test_projection_equals_frozen(self):
        _,r=demo();self.assertEqual(r['candidates'][0]['projected_digest'],r['frozen_observation_digest'])
    def test_different_population_rates(self):
        _,r=demo();self.assertNotEqual(r['candidates'][0]['population_rate'],r['candidates'][1]['population_rate'])
    def test_lower_rate(self):
        _,r=demo();self.assertEqual(r['candidates'][0]['population_rate']['percentage'],31.25)
    def test_upper_rate(self):
        _,r=demo();self.assertEqual(r['candidates'][1]['population_rate']['percentage'],81.25)
    def test_bounds(self):
        _,r=demo();self.assertEqual(r['bounds']['lower']['percentage'],31.25);self.assertEqual(r['bounds']['upper']['percentage'],81.25)
    def test_missing_count(self):
        _,r=demo();self.assertEqual(r['bounds']['unknown_outcomes'],8)
    def test_observed_count(self):
        _,r=demo();self.assertEqual(r['bounds']['observed_successes'],5)
    def test_order_independent_evidence(self):
        a,_=demo();b=FLAY198(reversed(a.rows));self.assertEqual(a.frozen,b.frozen)
    def test_audit_valid(self):
        a,_=demo();self.assertEqual(a.audit(),'VALID_LOCAL_CHAIN')
    def test_audit_tamper(self):
        a,_=demo();a.events[-1]['data']['verdict']='CHANGED';self.assertEqual(a.audit(),'TAMPERED')
    def test_active_frozen(self):
        _,r=demo();self.assertFalse(r['learning_applied']);self.assertEqual(r['active_parent'],'frozen')
    def test_no_physical_independence_claim(self):
        _,r=demo();self.assertFalse(r['observer_roots_are_independent']);self.assertFalse(r['causal_identification'])
    def test_invalid_candidate_model(self):
        a,_=demo();self.assertRaises(ValueError,a.compare,['fake'])
    def test_no_compatible_model(self):
        a,_=demo();c=CausalCandidate('broken',(1,)*16,(1,)*16,'x');self.assertEqual(a.compare([c])['verdict'],'NO_COMPATIBLE_MODEL')
    def test_one_compatible_model(self):
        a,_=demo();latent=tuple(r.outcome if r.selected else 0 for r in a.rows);gate=tuple(latent[i] if r.selected else 1-latent[i] for i,r in enumerate(a.rows));c=CausalCandidate('one',latent,gate,'x');self.assertEqual(a.compare([c])['verdict'],'SINGLE_COMPATIBLE_MODEL')
    def test_same_rate_models(self):
        a,_=demo();latent=tuple(r.outcome if r.selected else 0 for r in a.rows);gate=tuple(latent[i] if r.selected else 1-latent[i] for i,r in enumerate(a.rows));c=CausalCandidate('one',latent,gate,'x');d=CausalCandidate('two',latent,gate,'x');self.assertEqual(a.compare([c,d])['verdict'],'MULTIPLE_COMPATIBLE_SAME_RATE')
    def test_candidate_digest_changes(self):
        _,r=demo();self.assertNotEqual(r['candidates'][0]['candidate_digest'],r['candidates'][1]['candidate_digest'])
    def test_result_digest_consistent(self):
        _,r=demo();self.assertEqual(r['digest'],digest({k:v for k,v in r.items() if k!='digest'}))
    def test_consistent_replay_computation(self):
        self.assertEqual(demo()[1],demo()[1])

if __name__=='__main__':unittest.main()