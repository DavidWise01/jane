import copy
import unittest
from dataclasses import replace
from holdout import Ledger, FLAY201, InvalidEvent, fixture, demonstration


class HoldoutTests(unittest.TestCase):
    def outcome(self, mode):
        return FLAY201(fixture(mode)).audit('development', 'final')

    def test_sealed(self): self.assertEqual(self.outcome('sealed')['verdict'], 'SEALED_FINAL_FIXTURE')
    def test_dev_repeated(self): self.assertTrue(self.outcome('sealed')['development_reused'])
    def test_dev_selection_feedback(self): self.assertTrue(self.outcome('sealed')['development_selection_after_feedback'])
    def test_dev_count(self): self.assertEqual(self.outcome('sealed')['development_evaluations'], 2)
    def test_final_count(self): self.assertEqual(self.outcome('sealed')['final_evaluations'], 1)
    def test_final_disclosure_count(self): self.assertEqual(self.outcome('sealed')['final_disclosures'], 1)
    def test_leak(self): self.assertEqual(self.outcome('leaked')['verdict'], 'FINAL_TEST_WITHHELD')
    def test_leak_exposure(self): self.assertEqual(len(self.outcome('leaked')['final_exposure_preseal']), 2)
    def test_retest(self): self.assertIn('repeated final evaluation', self.outcome('retest')['issues'])
    def test_adapt(self): self.assertIn('model development after final exposure', self.outcome('adapt')['issues'])
    def test_alias(self): self.assertEqual(FLAY201(fixture()).audit('final','final')['verdict'], 'SET_ALIAS')
    def test_verify(self): self.assertTrue(fixture().verify())
    def test_copy(self): self.assertEqual(Ledger(fixture().events).head,fixture().head)
    def test_head_stable(self): self.assertEqual(fixture().head,fixture().head)
    def test_event_seq(self): self.assertEqual([e.seq for e in fixture().events],list(range(1,11)))
    def test_corrupted_head(self):
        l=fixture(); l.events[3]=replace(l.events[3],head='f'*64)
        self.assertEqual(FLAY201(l).audit('development','final')['verdict'],'CORRUPT_LOG')
    def test_corrupted_payload(self):
        l=fixture(); l.events[2].payload['score']=123
        self.assertFalse(l.verify())
    def test_corrupted_prev(self):
        l=fixture(); l.events[3]=replace(l.events[3],prev='0'*64)
        self.assertFalse(l.verify())
    def test_invalid_kind(self):
        with self.assertRaises(InvalidEvent): Ledger().append('DELETE','s')
    def test_blank_set(self):
        with self.assertRaises(InvalidEvent): Ledger().append('NOTE','')
    def test_bad_model(self):
        with self.assertRaises(InvalidEvent): Ledger().append('NOTE','s',None)
    def test_bad_payload(self):
        with self.assertRaises(InvalidEvent): Ledger().append('NOTE','s',payload=[])
    def test_bad_float(self):
        with self.assertRaises(InvalidEvent): Ledger().append('NOTE','s',payload={'x':set()})
    def test_mutation_isolation(self):
        p={'members':['a']}; l=Ledger(); l.append('FREEZE_SET','s',payload=p)
        p['members'].append('b'); self.assertEqual(l.events[0].payload['members'],['a'])
    def test_export(self): self.assertEqual(fixture().export()['head'],fixture().head)
    def test_missing_final(self):
        l=Ledger();l.append('FREEZE_SET','development');l.append('FREEZE_SET','final');l.append('SEAL_FINAL','final')
        self.assertIn('final test not executed',FLAY201(l).audit('development','final')['issues'])
    def test_missing_seal(self):
        l=Ledger();l.append('FREEZE_SET','final');l.append('FINAL_EVALUATE','final')
        self.assertEqual(FLAY201(l).audit('development','final')['verdict'],'FINAL_TEST_WITHHELD')
    def test_overlap(self):
        l=fixture();l2=Ledger();
        for e in l.events:
            p=e.payload
            if e.kind=='FREEZE_SET' and e.set_id=='final':p={'members':['d1','f2']}
            l2.append(e.kind,e.set_id,e.model,p)
        self.assertIn('frozen member overlap',FLAY201(l2).audit('development','final')['issues'])
    def test_premature_final_disclosure(self):
        l=Ledger();l.append('FREEZE_SET','final');l.append('SEAL_FINAL','final');l.append('FINAL_DISCLOSE','final');l.append('FINAL_EVALUATE','final')
        self.assertIn('premature final disclosure',FLAY201(l).audit('development','final')['issues'])
    def test_double_disclosure(self):
        l=fixture();l.append('FINAL_DISCLOSE','final')
        self.assertIn('repeated final disclosure',FLAY201(l).audit('development','final')['issues'])
    def test_duplicate_seal(self):
        l=fixture();l.append('SEAL_FINAL','final')
        self.assertIn('missing or invalid frozen seal',FLAY201(l).audit('development','final')['issues'])
    def test_demo(self): self.assertEqual(len(demonstration()['cases']),4)
    def test_limit(self): self.assertIn('no external custody',self.outcome('sealed')['limits'])
    def test_event_count(self): self.assertEqual(self.outcome('sealed')['event_count'],10)
    def test_unique_heads(self):
        l=fixture(); heads=[e.head for e in l.events];self.assertEqual(len(heads),len(set(heads)))
    def test_deterministic_export(self):self.assertEqual(fixture().export(),fixture().export())


if __name__=='__main__':unittest.main()