import unittest
from fractions import Fraction
from dataclasses import replace
from protocol import *

class TestProtocol(unittest.TestCase):
    def setUp(self):
        self.a=fixture(); self.b=fixture(source_root='acquisition-root-B',raw_commitment='b'*64)
        self.roots={'acquisition-root-A','acquisition-root-B'}
    def call(self,a=None,b=None,v=1000,w=1000,roots=None,**k):
        return compare(a or self.a,b or self.b,v,w,Fraction(2),self.roots if roots is None else roots,**k)[0]
    def test_matching(self):self.assertEqual(self.call()['status'],'DECLARED_FIXTURE_REPRODUCTION')
    def test_matching_numbers_not_enough(self):self.assertEqual(self.call(b=replace(self.b,question='battery life'))['status'],'PROTOCOL_DRIFT')
    def test_estimand(self):self.assertEqual(self.call(b=replace(self.b,estimand='median offset'))['differences'][0]['field'],'estimand')
    def test_unit(self):self.assertEqual(self.call(b=replace(self.b,unit='seconds'))['status'],'PROTOCOL_DRIFT')
    def test_population(self):self.assertEqual(self.call(b=replace(self.b,population='generation 2'))['status'],'PROTOCOL_DRIFT')
    def test_frame(self):self.assertEqual(self.call(b=replace(self.b,sampling_frame='volunteers'))['status'],'PROTOCOL_DRIFT')
    def test_inclusion(self):self.assertEqual(self.call(b=replace(self.b,inclusion='healthy only'))['status'],'PROTOCOL_DRIFT')
    def test_exclusion(self):self.assertEqual(self.call(b=replace(self.b,exclusion='high variance'))['status'],'PROTOCOL_DRIFT')
    def test_selection(self):self.assertEqual(self.call(b=replace(self.b,selection_rule='cherry pick'))['status'],'PROTOCOL_DRIFT')
    def test_assignment(self):self.assertEqual(self.call(b=replace(self.b,assignment='no seed'))['status'],'PROTOCOL_DRIFT')
    def test_instrument(self):self.assertEqual(self.call(b=replace(self.b,instrument='sensor-Z'))['status'],'PROTOCOL_DRIFT')
    def test_condition(self):self.assertEqual(self.call(b=replace(self.b,condition='80 C'))['status'],'PROTOCOL_DRIFT')
    def test_calibration(self):self.assertEqual(self.call(b=replace(self.b,calibration='unknown'))['status'],'PROTOCOL_DRIFT')
    def test_processing(self):self.assertEqual(self.call(b=replace(self.b,processing='round values'))['status'],'PROTOCOL_DRIFT')
    def test_aggregation(self):self.assertEqual(self.call(b=replace(self.b,aggregation='median'))['status'],'PROTOCOL_DRIFT')
    def test_time(self):self.assertEqual(self.call(b=replace(self.b,time_window='UTC 2027'))['status'],'PROTOCOL_DRIFT')
    def test_difference_preserved(self):
        x=self.call(b=replace(self.b,selection_rule='biased',condition='hot'))
        self.assertEqual(len(x['differences']),2)
    def test_measurement_disagreement(self):self.assertEqual(self.call(w=1003)['status'],'RESULT_DISAGREEMENT')
    def test_tolerance_boundary(self):self.assertTrue(self.call(w=1002)['matching_numbers'])
    def test_fraction(self):self.assertTrue(self.call(v=Fraction(1,3),w=Fraction(1,2))['matching_numbers'])
    def test_bad_tolerance(self):
        with self.assertRaises(ValueError):compare(self.a,self.b,1,1,-1)
    def test_float_disallowed(self):
        with self.assertRaises(TypeError):compare(self.a,self.b,1.0,1,0)
    def test_shared_source(self):self.assertEqual(self.call(b=fixture(raw_commitment='b'*64))['status'],'SHARED_ACQUISITION_ANCESTRY')
    def test_unknown_independence(self):self.assertEqual(compare(self.a,self.b,1000,1000,Fraction(2))[0]['status'],'INDEPENDENCE_UNESTABLISHED')
    def test_no_physical_proof(self):self.assertFalse(self.call()['physical_independence_verified'])
    def test_no_activation(self):self.assertFalse(self.call()['jane_activation'])
    def test_frozen(self):self.assertEqual(self.call()['active_parent'],'FROZEN')
    def test_distinct_raw(self):self.assertFalse(self.call()['raw_commitments_match'])
    def test_raw_copy_detected(self):self.assertTrue(self.call(b=replace(self.b,raw_commitment=self.a.raw_commitment))['raw_commitments_match'])
    def test_configured_instrument_equivalence(self):
        r=self.call(b=replace(self.b,instrument='sensor-B'),allowed_instrument_pairs={('sensor-A','sensor-B')})
        self.assertEqual(r['status'],'DECLARED_FIXTURE_REPRODUCTION')
        self.assertEqual(len(r['explicit_equivalences']),1)
    def test_not_bidirectional_unless_configured(self):
        r=self.call(b=replace(self.b,instrument='sensor-B'),allowed_instrument_pairs={('sensor-B','sensor-A')})
        self.assertEqual(r['status'],'PROTOCOL_DRIFT')
    def test_invalid_roots(self):
        with self.assertRaises(ValueError):self.call(roots={'acquisition-root-A'})
    def test_invalid_commitment(self):
        with self.assertRaises(ValueError):fixture(raw_commitment='garbage')
    def test_empty_field(self):
        with self.assertRaises(ValueError):fixture(question='')
    def test_ledger(self):self.assertEqual(compare(self.a,self.b,1,1)[1].audit(),'VALID_LOCAL_CHAIN')
    def test_ledger_tamper(self):
        _,l=compare(self.a,self.b,1,1);l.events[0]['kind']='forged';self.assertEqual(l.audit(),'TAMPERED')
    def test_external_head(self):self.assertEqual(compare(self.a,self.b,1,1)[1].audit('f'*64),'EXTERNAL_HEAD_MISMATCH')
    def test_ledger_three_events(self):self.assertEqual(len(compare(self.a,self.b,1,1)[1].events),3)
    def test_deterministic(self):self.assertEqual(self.call(),self.call())
    def test_sha64(self):self.assertEqual(len(self.call()['digest']),64)
    def test_original_unchanged(self):
        self.call(b=replace(self.b,condition='hot'))
        self.assertEqual(self.a.condition,'20 C')
    def test_demo(self):self.assertEqual(demo()['cases']['matching_but_biased']['status'],'PROTOCOL_DRIFT')
    def test_false_positive_blocked(self):self.assertFalse(self.call(b=replace(self.b,selection_rule='biased'))['protocol_equivalent_under_declared_policy'])
    def test_source_root_not_in_dimensions(self):self.assertNotIn('source_root',sum(DIMENSIONS.values(),[]))
    def test_raw_commit_not_in_dimensions(self):self.assertNotIn('raw_commitment',sum(DIMENSIONS.values(),[]))

if __name__=='__main__':unittest.main(verbosity=2)
