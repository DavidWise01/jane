import unittest
from dataclasses import replace
from risk import Budget, Case, Flay141, fixture, digest


def sample(i=1, cohort='a', parent=False, child=True, severity=2, reversibility=1):
    return Case(str(i), cohort, 'external:a', True, parent, child, severity, reversibility, f'{i+100:064x}')


def policy(**kw):
    return Budget(**dict(overall_max_cost=20, cohort_max_cost=(('a', 20),),
                         max_new_severe_errors=0, severe_threshold=8, min_cases_per_cohort=2, **kw))


class RiskTests(unittest.TestCase):
    def test_demo_status(self): self.assertEqual(fixture()[1]['status'], 'BLOCK_NEW_SEVERE_ERRORS')
    def test_parent_cost(self): self.assertEqual(fixture()[1]['parent_cost'], 12)
    def test_child_cost(self): self.assertEqual(fixture()[1]['child_cost'], 100)
    def test_new_severe(self): self.assertEqual(fixture()[1]['new_severe_errors'], 2)
    def test_critical_budget(self): self.assertEqual(fixture()[1]['cohorts'][0]['budget'], 0)
    def test_routine_gain(self): self.assertEqual(fixture()[1]['cohorts'][1]['net_cost_improvement'], 12)
    def test_no_activation(self): self.assertEqual(fixture()[1]['active'], 'frozen_parent')
    def test_no_learning(self): self.assertFalse(fixture()[1]['learning_applied'])
    def test_immutable_budget(self):
        with self.assertRaises(Exception): fixture()[0].budget.overall_max_cost = 999
    def test_chain(self): self.assertEqual(fixture()[0].audit(), 'VALID_LOCAL_CHAIN')
    def test_digest(self): self.assertEqual(len(fixture()[1]['digest']), 64)
    def test_determinism(self): self.assertEqual(fixture()[1], fixture()[1])
    def test_tamper(self):
        obj, _ = fixture(); obj.events[-1]['kind'] = 'FRAUD'
        self.assertEqual(obj.audit(), 'TAMPERED')
    def test_external_anchor(self): self.assertEqual(fixture()[0].audit('0'*64), 'EXTERNAL_HEAD_MISMATCH')
    def test_clean_improvement(self):
        obj = Flay141(policy())
        self.assertEqual(obj.evaluate([sample(1), sample(2)])['status'], 'JANE_REVIEW_CANDIDATE')
    def test_no_improvement(self):
        obj = Flay141(policy())
        self.assertEqual(obj.evaluate([sample(1, parent=True), sample(2, parent=True)])['status'], 'NO_RISK_IMPROVEMENT')
    def test_cohort_budget(self):
        b = Budget(30, (('a', 0),), 2, 8, 2); obj = Flay141(b)
        self.assertEqual(obj.evaluate([sample(1, parent=True, child=False), sample(2, parent=True, child=False)])['status'], 'BLOCK_COHORT_RISK')
    def test_total_budget(self):
        b = Budget(1, (('a', 100),), 2, 8, 2); obj = Flay141(b)
        self.assertEqual(obj.evaluate([sample(1, parent=True, child=False), sample(2, parent=True, child=False)])['status'], 'BLOCK_OVERALL_RISK')
    def test_low_severity_new_error(self):
        b = Budget(20, (('a', 20),), 0, 8, 2); obj = Flay141(b)
        self.assertEqual(obj.evaluate([sample(1, parent=True, child=False), sample(2, parent=True, child=False)])['status'], 'NO_RISK_IMPROVEMENT')
    def test_abstention(self):
        obj = Flay141(policy())
        self.assertEqual(obj.evaluate([sample(1, child=None), sample(2)])['status'], 'ABSTENTION_REVIEW')
    def test_min_cohort(self):
        obj = Flay141(policy())
        self.assertEqual(obj.evaluate([sample(1)])['status'], 'INSUFFICIENT_COHORT_COVERAGE')
    def test_missing_cohort_policy(self):
        obj = Flay141(policy())
        self.assertEqual(obj.evaluate([sample(1), sample(2, cohort='b')])['status'], 'INCOMPLETE_COHORT_POLICY')
    def test_leakage(self):
        obj = Flay141(policy()); s = sample()
        self.assertEqual(obj.evaluate([s, sample(2)], [s.evidence_hash])['status'], 'HOLDOUT_LEAKAGE')
    def test_duplicate_id(self):
        with self.assertRaises(ValueError): Flay141(policy()).evaluate([sample(1), sample(1)])
    def test_empty(self):
        with self.assertRaises(ValueError): Flay141(policy()).evaluate([])
    def test_bad_split(self):
        with self.assertRaises(ValueError): Flay141(policy()).evaluate([replace(sample(), split='train')])
    def test_bad_severity(self):
        with self.assertRaises(ValueError): Flay141(policy()).evaluate([sample(1, severity=11)])
    def test_bad_reversibility(self):
        with self.assertRaises(ValueError): Flay141(policy()).evaluate([sample(1, reversibility=0)])
    def test_bad_digest(self):
        with self.assertRaises(ValueError): Flay141(policy()).evaluate([replace(sample(), evidence_hash='oops')])
    def test_budget_invalid(self):
        with self.assertRaises(ValueError): Budget(-1, (('a', 1),), 0)
    def test_budget_duplicate_cohort(self):
        with self.assertRaises(ValueError): Budget(10, (('a', 1), ('a', 2)), 0)
    def test_budget_negative_cohort(self):
        with self.assertRaises(ValueError): Budget(10, (('a', -1),), 0)
    def test_budget_bad_threshold(self):
        with self.assertRaises(ValueError): Budget(10, (('a', 1),), 0, severe_threshold=101)
    def test_over_max_cases(self):
        with self.assertRaises(ValueError): Flay141(policy()).evaluate([sample(i) for i in range(257)])
    def test_predeclared_budget_event(self): self.assertEqual(fixture()[0].events[0]['kind'], 'DECLARE_BUDGET')
    def test_risk_multiplier(self): self.assertEqual(10*5, 50)
    def test_payload_hash_changes(self):
        p1 = fixture()[1]; p2 = fixture()[1].copy();p2['status']='FAKE'
        self.assertNotEqual(digest(p1), digest(p2))


if __name__ == '__main__': unittest.main(verbosity=2)
