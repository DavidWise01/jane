import copy
import unittest
from fractions import Fraction
from subgroups import Group, Window, FLAY209, fixture, make_window, checked, digest, demonstration


class JANE209Tests(unittest.TestCase):
    def setUp(self):
        self.engine = FLAY209()

    def check(self, scenario, marker, verdict='TRANSFER_WITHHELD'):
        result = self.engine.audit(*fixture(scenario))
        self.assertEqual(result['verdict'], verdict)
        self.assertIn(marker, result['reasons'])
        return result

    def test_masked_rate(self):
        r = self.check('masked', 'AGGREGATE_MASKED_SUBGROUP_DRIFT')
        self.assertEqual(r['baseline_overall']['decimal'], .5)
        self.assertEqual(r['current_overall']['decimal'], .5)
        self.assertEqual(r['standardized_current']['decimal'], .5)
        self.assertIn('SUBGROUP_RATE_DRIFT', r['reasons'])

    def test_stable(self):
        r = self.engine.audit(*fixture('stable'))
        self.assertEqual(r['verdict'], 'CONDITIONAL_SUBGROUP_STABILITY_FIXTURE')
        self.assertEqual(r['reasons'], [])

    def test_composition(self):
        r = self.check('composition', 'COMPOSITION_SHIFT')
        self.assertEqual(r['baseline_overall']['decimal'], .68)
        self.assertEqual(r['current_overall']['decimal'], .32)
        self.assertEqual(r['standardized_current']['decimal'], .68)

    def test_missing(self): self.check('missing_group', 'SUBGROUP_COVERAGE_MISMATCH')
    def test_min_support(self): self.check('underpowered', 'INSUFFICIENT_SUBGROUP_SUPPORT')
    def test_shared(self): self.check('shared_root', 'SHARED_DECLARED_ANCESTRY')
    def test_stale(self): self.check('stale', 'STALE_BASELINE')
    def test_order_independent(self):
        b,c=fixture('masked')
        br=Window(b.label,b.start,b.end,b.population,b.instrument,tuple(reversed(b.groups)))
        cr=Window(c.label,c.start,c.end,c.population,c.instrument,tuple(reversed(c.groups)))
        a=self.engine.audit(b,c);z=self.engine.audit(br,cr)
        self.assertEqual(a['groups'], z['groups'])
        self.assertEqual(a['verdict'], z['verdict'])

    def test_immutable(self):
        b,c=fixture('masked'); before=copy.deepcopy((b,c));self.engine.audit(b,c)
        self.assertEqual((b,c), before)

    def test_deterministic(self):
        b,c=fixture('masked'); self.assertEqual(self.engine.audit(b,c),self.engine.audit(b,c))

    def test_digest_tamper(self):
        r=self.engine.audit(*fixture('masked'));original=r['audit_digest'];r['groups'][0]['current_n']=99
        self.assertNotEqual(original,digest({k:v for k,v in r.items() if k!='audit_digest'}))

    def test_future(self):
        b,c=fixture('stable')
        b=Window(b.label,125,130,b.population,b.instrument,b.groups)
        self.assertIn('WINDOW_OVERLAP_OR_BACKDATED',self.engine.audit(b,c)['reasons'])

    def test_population(self):
        b,c=fixture('stable');c=Window(c.label,c.start,c.end,'other',c.instrument,c.groups)
        self.assertIn('POPULATION_MISMATCH',self.engine.audit(b,c)['reasons'])

    def test_instrument(self):
        b,c=fixture('stable');c=Window(c.label,c.start,c.end,c.population,'other',c.groups)
        self.assertIn('INSTRUMENT_MISMATCH',self.engine.audit(b,c)['reasons'])

    def test_zero_group(self):
        b,c=fixture('stable')
        c=Window(c.label,c.start,c.end,c.population,c.instrument,(Group('A',10,9,'ra'),Group('B',0,0,'rb')))
        r=self.engine.audit(b,c)
        self.assertIn('INSUFFICIENT_SUBGROUP_SUPPORT',r['reasons'])
        self.assertIsNone(r['standardized_current'])

    def test_empty_window(self):
        b,c=fixture('stable'); c=Window(c.label,c.start,c.end,c.population,c.instrument,
                                        (Group('A',0,0,'ra'),Group('B',0,0,'rb')))
        self.assertIn('EMPTY_WINDOW',self.engine.audit(b,c)['reasons'])

    def test_at_tolerance(self):
        b=make_window('b',0,10,[('A',10,5),('B',10,5)])
        c=make_window('c',11,20,[('A',10,6),('B',10,4)])
        self.assertEqual(self.engine.audit(b,c)['verdict'],'CONDITIONAL_SUBGROUP_STABILITY_FIXTURE')

    def test_beyond_tolerance(self):
        b=make_window('b',0,10,[('A',10,5),('B',10,5)])
        c=make_window('c',11,20,[('A',10,7),('B',10,3)])
        self.assertIn('SUBGROUP_RATE_DRIFT',self.engine.audit(b,c)['reasons'])

    def test_missing_order_not_masked(self):
        r=self.engine.audit(*fixture('missing_group'))
        self.assertIsNone(r['standardized_current'])

    def test_names_sorted(self):
        r=self.engine.audit(*fixture('stable'))
        self.assertEqual([g['group'] for g in r['groups']],['A','B'])

    def test_policy_recorded(self):
        self.assertEqual(self.engine.audit(*fixture('stable'))['policy']['minimum_per_group'],5)

    def test_two_digest(self):
        b,c=fixture('masked');r=self.engine.audit(b,c)
        self.assertEqual(r['baseline_digest'],digest(b.as_dict()))
        self.assertEqual(r['current_digest'],digest(c.as_dict()))

    def test_demonstration(self):
        d=demonstration();self.assertEqual(len(d),7)
        self.assertEqual(d['stable']['verdict'],'CONDITIONAL_SUBGROUP_STABILITY_FIXTURE')

    def test_bad_tolerance_type(self):
        with self.assertRaises(ValueError): FLAY209(.1)

    def test_bad_tolerance_range(self):
        with self.assertRaises(ValueError): FLAY209(Fraction(11,10))

    def test_bad_sample_floor(self):
        with self.assertRaises(ValueError): FLAY209(min_n=0)

    def test_bad_age(self):
        with self.assertRaises(ValueError): FLAY209(max_age=-1)

    def test_duplicate_group(self):
        b,c=fixture('stable'); b=Window(b.label,b.start,b.end,b.population,b.instrument,(b.groups[0],b.groups[0]))
        with self.assertRaisesRegex(ValueError,'DUPLICATE_GROUP'): self.engine.audit(b,c)

    def test_bad_counts(self):
        b,c=fixture('stable'); b=Window(b.label,b.start,b.end,b.population,b.instrument,(Group('A',10,11,'r'),b.groups[1]))
        with self.assertRaisesRegex(ValueError,'INVALID_COUNTS'): self.engine.audit(b,c)

    def test_negative_counts(self):
        b,c=fixture('stable'); b=Window(b.label,b.start,b.end,b.population,b.instrument,(Group('A',-1,0,'r'),b.groups[1]))
        with self.assertRaisesRegex(ValueError,'INVALID_COUNTS'): self.engine.audit(b,c)

    def test_bool_count(self):
        b,c=fixture('stable'); b=Window(b.label,b.start,b.end,b.population,b.instrument,(Group('A',True,1,'r'),b.groups[1]))
        with self.assertRaisesRegex(ValueError,'INVALID_COUNTS'): self.engine.audit(b,c)

    def test_bad_name(self):
        b,c=fixture('stable');b=Window(b.label,b.start,b.end,b.population,b.instrument,(Group('',10,5,'r'),b.groups[1]))
        with self.assertRaisesRegex(ValueError,'INVALID_GROUP'):self.engine.audit(b,c)

    def test_bad_root(self):
        b,c=fixture('stable');b=Window(b.label,b.start,b.end,b.population,b.instrument,(Group('A',10,5,''),b.groups[1]))
        with self.assertRaisesRegex(ValueError,'INVALID_ROOT'):self.engine.audit(b,c)

    def test_bad_time(self):
        b,c=fixture('stable'); b=Window(b.label,101,100,b.population,b.instrument,b.groups)
        with self.assertRaisesRegex(ValueError,'INVALID_TIME'): self.engine.audit(b,c)

    def test_invalid_population(self):
        b,c=fixture('stable'); b=Window(b.label,b.start,b.end,' ',b.instrument,b.groups)
        with self.assertRaisesRegex(ValueError,'INVALID_POPULATION'): self.engine.audit(b,c)

    def test_invalid_instrument(self):
        b,c=fixture('stable'); b=Window(b.label,b.start,b.end,b.population,'',b.groups)
        with self.assertRaisesRegex(ValueError,'INVALID_INSTRUMENT'): self.engine.audit(b,c)

    def test_empty_groups(self):
        b,c=fixture('stable'); b=Window(b.label,b.start,b.end,b.population,b.instrument,())
        with self.assertRaisesRegex(ValueError,'EMPTY_GROUPS'): self.engine.audit(b,c)

    def test_invalid_window(self):
        with self.assertRaisesRegex(ValueError,'INVALID_WINDOW'): checked(None)

    def test_no_unknown_scenario(self):
        with self.assertRaisesRegex(ValueError,'UNKNOWN_SCENARIO'):fixture('bogus')

    def test_decimal_exact(self):
        r=self.engine.audit(*fixture('masked'))
        self.assertEqual(r['groups'][0]['rate_delta']['numerator'],-3)
        self.assertEqual(r['groups'][0]['rate_delta']['denominator'],10)

    def test_scope_not_global_causality(self):
        r=self.engine.audit(*fixture('stable'))
        self.assertIn('Fixture',r['claim_limit'])


if __name__ == '__main__': unittest.main()