import unittest
from dataclasses import replace
from leakage import Event, FLAY202, InvalidEvidence, fixture, digest, canonical

class Tests(unittest.TestCase):
    def test_scenarios(self):
        for scenario in ('summary_leak','embedding_leak','score_leak','declared_release'):
            with self.subTest(scenario=scenario):
                self.assertEqual(fixture(scenario).audit()['verdict'], 'SEALED_INFORMATION_INFLUENCED_SELECTION')
    def test_isolated(self):
        self.assertEqual(fixture('isolated').audit()['verdict'], 'INDIRECT_EXPOSURE_NO_SELECTION_PATH')
    def test_no_access(self):
        self.assertEqual(fixture('no_access').audit()['verdict'], 'INDIRECT_EXPOSURE_NO_SELECTION_PATH')
    def test_affected(self):
        self.assertEqual(fixture().audit()['affected_decisions'][0]['model'],'model-1')
    def test_indirect(self):
        self.assertIn('sealed-dataset-info', fixture().audit()['affected_decisions'][0]['sealed_ancestry'])
    def test_retain_three_transfers(self):
        a=fixture().audit()
        self.assertEqual([x['kind'] for x in a['exposures']],['evaluation','summary','report'])
    def test_declassify_does_not_launder(self):
        self.assertEqual(fixture('declared_release').audit()['verdict'],'SEALED_INFORMATION_INFLUENCED_SELECTION')
    def test_head(self):
        self.assertEqual(len(fixture().head),64)
    def test_determinism(self):
        self.assertEqual(fixture().head, fixture().head)
    def test_distinct_fixture_heads(self):
        self.assertNotEqual(fixture().head,fixture('isolated').head)
    def test_canonical(self):
        self.assertEqual(canonical({'b':1,'a':2}),canonical({'a':2,'b':1}))
    def test_digest(self):
        self.assertEqual(digest({'a':1}),digest({'a':1}))
    def test_no_seal(self):
        self.assertEqual(FLAY202().audit()['verdict'],'NO_SEALED_TEST')
    def test_seal_only(self):
        x=FLAY202();x.append(Event('s','seal','c',dataset='sealed-final'));self.assertEqual(x.audit()['verdict'],'NO_RECORDED_EXPOSURE')
    def test_invalid_kind(self):
        with self.assertRaises(InvalidEvidence): FLAY202().append(Event('a','wrong','x'))
    def test_invalid_type(self):
        with self.assertRaises(InvalidEvidence): FLAY202().append(None)
    def test_empty_id(self):
        with self.assertRaises(InvalidEvidence): FLAY202().append(Event('','seal','x',dataset='sealed-final'))
    def test_duplicate_id(self):
        x=fixture();with_event=Event('sealed','score','x');self.assertRaises(InvalidEvidence,x.append,with_event)
    def test_missing_parent(self):
        self.assertRaises(InvalidEvidence,FLAY202().append,Event('a','score','x',('bad',)))
    def test_future_parent(self):
        self.assertRaises(InvalidEvidence,FLAY202().append,Event('a','score','x',('b',)))
    def test_repeated_parent(self):
        x=fixture();self.assertRaises(InvalidEvidence,x.append,Event('x','report','x',('test','test'),epoch=6))
    def test_empty_actor(self):
        self.assertRaises(InvalidEvidence,FLAY202().append,Event('a','seal','',dataset='sealed-final'))
    def test_wrong_dataset(self):
        self.assertRaises(InvalidEvidence,FLAY202().append,Event('a','seal','x',dataset='wrong'))
    def test_negative_epoch(self):
        self.assertRaises(InvalidEvidence,FLAY202().append,Event('a','seal','x',epoch=-1))
    def test_bool_epoch(self):
        self.assertRaises(InvalidEvidence,FLAY202().append,Event('a','seal','x',epoch=True))
    def test_nonmonotonic_epoch(self):
        x=fixture();self.assertRaises(InvalidEvidence,x.append,Event('x','report','x',epoch=0))
    def test_unbound_declassify(self):
        self.assertRaises(InvalidEvidence,FLAY202().append,Event('a','declassify','x'))
    def test_tamper_event(self):
        x=fixture();x.events[2]['event']['payload']='falsified';self.assertEqual(x.audit()['verdict'],'CORRUPT_LOG')
    def test_tamper_head(self):
        x=fixture();x.head='f'*64;self.assertEqual(x.audit()['verdict'],'CORRUPT_LOG')
    def test_tamper_link(self):
        x=fixture();x.events[1]['prior']='bad';self.assertEqual(x.audit()['verdict'],'CORRUPT_LOG')
    def test_tamper_hash(self):
        x=fixture();x.events[-1]['hash']='bad';self.assertEqual(x.audit()['verdict'],'CORRUPT_LOG')
    def test_tamper_ids(self):
        x=fixture();x._ids.clear();self.assertEqual(x.audit()['verdict'],'CORRUPT_LOG')
    def test_missing_selection_lineage(self):
        x=fixture('isolated');self.assertEqual(x.audit()['affected_decisions'],[])
    def test_model_is_recorded(self):
        self.assertEqual(fixture('score_leak').audit()['affected_decisions'][0]['event'],'select')
    def test_no_raw_access_required(self):
        x=fixture();self.assertFalse(any(z['event']['kind']=='access' for z in x.events))
    def test_chain_intact(self):
        self.assertTrue(fixture().intact())
    def test_no_parent_mutation(self):
        x=fixture();old=x.events[0]['event'].copy();x.audit();self.assertEqual(x.events[0]['event'],old)
    def test_chain_total(self):
        x=fixture();self.assertEqual(x.audit()['events'],5)
    def test_reordered_disclosure_invalid(self):
        x=fixture();x.events[2],x.events[3]=x.events[3],x.events[2];self.assertEqual(x.audit()['verdict'],'CORRUPT_LOG')
    def test_external_signal_requires_path(self):
        x=fixture('isolated');self.assertNotEqual(x.audit()['verdict'],'SEALED_INFORMATION_INFLUENCED_SELECTION')
    def test_ancestry_reaches_seal(self):
        x=fixture();self.assertIn('sealed',x.audit()['affected_decisions'][0]['sealed_ancestry'])

if __name__=='__main__': unittest.main()