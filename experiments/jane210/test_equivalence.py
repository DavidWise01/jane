import unittest
from equivalence import Counts,Group,analyze,wilson,demo

def g(name,bs=5,bn=10,cs=5,cn=10,root=None):
    return Group(name,Counts(bs,bn),Counts(cs,cn),root or name+'-b',name+'-c')

class EquivalenceTests(unittest.TestCase):
    def test_01_small_equal_not_stable(self):
        self.assertEqual(analyze([g('tiny',2,4,2,4)])['verdict'],'INSUFFICIENT_SUBGROUP_SAMPLE')
    def test_02_large_equal_supported(self):
        self.assertEqual(analyze([g('big',500,1000,500,1000)])['verdict'],'EQUIVALENCE_SUPPORTED_CONDITIONAL')
    def test_03_large_drift(self):
        self.assertEqual(analyze([g('big',900,1000,500,1000)])['verdict'],'MATERIAL_DRIFT_SUPPORTED_CONDITIONAL')
    def test_04_non_significant_not_equivalence(self):
        self.assertEqual(analyze([g('moderate',15,30,15,30)])['verdict'],'STABILITY_NOT_ESTABLISHED')
    def test_05_mixed_small_prevents_stability(self):
        self.assertEqual(analyze([g('big',500,1000,500,1000),g('tiny',2,4,2,4)])['verdict'],'INSUFFICIENT_SUBGROUP_SAMPLE')
    def test_06_missing_group(self):
        self.assertEqual(analyze([g('A')],expected_groups=['A','B'])['verdict'],'MISSING_OR_EXTRA_GROUP')
    def test_07_extra_group(self):
        self.assertEqual(analyze([g('A'),g('B')],expected_groups=['A'])['verdict'],'MISSING_OR_EXTRA_GROUP')
    def test_08_duplicate(self):
        with self.assertRaises(ValueError): analyze([g('A'),g('A')])
    def test_09_empty(self):
        with self.assertRaises(ValueError): analyze([])
    def test_10_invalid_margin_zero(self):
        with self.assertRaises(ValueError): analyze([g('A')],margin=0)
    def test_11_invalid_margin_one(self):
        with self.assertRaises(ValueError): analyze([g('A')],margin=1)
    def test_12_invalid_margin_nan(self):
        with self.assertRaises(ValueError): analyze([g('A')],margin=float('nan'))
    def test_13_invalid_n(self):
        with self.assertRaises(ValueError): analyze([g('A')],min_n=0)
    def test_14_bool_n(self):
        with self.assertRaises(ValueError): analyze([g('A')],min_n=True)
    def test_15_invalid_z(self):
        with self.assertRaises(ValueError): analyze([g('A')],z=0)
    def test_16_invalid_z_nan(self):
        with self.assertRaises(ValueError): analyze([g('A')],z=float('nan'))
    def test_17_counts_negative(self):
        with self.assertRaises(ValueError): Counts(-1,10)
    def test_18_counts_excess(self):
        with self.assertRaises(ValueError): Counts(11,10)
    def test_19_counts_zero_total(self):
        with self.assertRaises(ValueError): Counts(0,0)
    def test_20_counts_bool(self):
        with self.assertRaises(ValueError): Counts(True,10)
    def test_21_root_missing(self):
        with self.assertRaises(ValueError): analyze([Group('A',Counts(1,2),Counts(1,2),'','root')])
    def test_22_root_shared(self):
        x=Group('A',Counts(500,1000),Counts(500,1000),'same','same')
        self.assertEqual(analyze([x])['verdict'],'SHARED_ANCESTRY_UNVERIFIED')
    def test_23_interval_bounds(self):
        low,high=wilson(5,10)
        self.assertLess(low,.5);self.assertGreater(high,.5)
    def test_24_zero_interval(self):
        low,high=wilson(0,10)
        self.assertEqual(low,0);self.assertGreater(high,0)
    def test_25_all_interval(self):
        low,high=wilson(10,10)
        self.assertAlmostEqual(high,1);self.assertLess(low,1)
    def test_26_reverse_order_same_digest(self):
        a,b=g('A'),g('B')
        self.assertEqual(analyze([a,b])['frozen_digest'],analyze([b,a])['frozen_digest'])
    def test_27_modified_count_different_digest(self):
        self.assertNotEqual(analyze([g('A')])['frozen_digest'],analyze([g('A',4,10)])['frozen_digest'])
    def test_28_margin_changes_digest(self):
        self.assertNotEqual(analyze([g('A')],margin=.1)['frozen_digest'],analyze([g('A')],margin=.2)['frozen_digest'])
    def test_29_min_n_changes_digest(self):
        self.assertNotEqual(analyze([g('A')],min_n=10)['frozen_digest'],analyze([g('A')],min_n=20)['frozen_digest'])
    def test_30_no_point_from_zero_group(self):
        with self.assertRaises(ValueError): g('A',0,0,1,1)
    def test_31_demo_scenarios(self):
        self.assertEqual(len(demo()),5)
    def test_32_demo_has_no_unqualified_claim(self):
        self.assertTrue(all('CONDITIONAL' in x['verdict'] or x['verdict'] in {'INSUFFICIENT_SUBGROUP_SAMPLE','STABILITY_NOT_ESTABLISHED'} for x in demo().values()))
    def test_33_narrow_margin(self):
        self.assertEqual(analyze([g('big',500,1000,500,1000)],margin=.01)['verdict'],'STABILITY_NOT_ESTABLISHED')
    def test_34_wide_margin(self):
        self.assertEqual(analyze([g('big',500,1000,500,1000)],margin=.2)['verdict'],'EQUIVALENCE_SUPPORTED_CONDITIONAL')
    def test_35_missing_provenance_does_not_prove_independence(self):
        self.assertIn('not established',analyze([g('big',500,1000,500,1000)])['notice'])
    def test_36_invalid_shift(self):
        with self.assertRaises(ValueError):analyze([g('A')],max_absolute_shift=-1)

if __name__=='__main__':unittest.main()