import copy, sqlite3, tempfile, unittest
from pathlib import Path
from instrument import FLAY218,fixture,signed,digest,Policy,valid

class TestInstrument(unittest.TestCase):
    def run_case(self,kind='independent'):
        f=FLAY218()
        try:return f.audit(*fixture(kind))
        finally:f.close()
    def test_valid(self):self.assertEqual(self.run_case()['verdict'],'DECLARED_INSTRUMENT_CONSISTENCY_FIXTURE')
    def test_simulated(self):self.assertEqual(self.run_case('simulated')['verdict'],'ONLY_SIMULATED_OR_INSUFFICIENT_INSTRUMENTATION')
    def test_shared(self):self.assertEqual(self.run_case('shared')['verdict'],'SHARED_ACQUISITION_ANCESTRY')
    def test_copied(self):self.assertEqual(self.run_case('copied')['verdict'],'DUPLICATED_CAPTURE')
    def test_stale(self):self.assertEqual(self.run_case('stale')['verdict'],'INVALID_ACQUISITION_CHRONOLOGY')
    def test_mismatch(self):self.assertEqual(self.run_case('mismatch')['verdict'],'ACQUISITION_CONTENT_MISMATCH')
    def test_no_obs(self):
        c,x,a=fixture();self.assertEqual(FLAY218().audit(c,x,[])['verdict'],'NO_ACQUISITION_EVIDENCE')
    def test_one_obs(self):
        c,x,a=fixture();self.assertEqual(FLAY218().audit(c,x,a[:1])['verdict'],'ONLY_SIMULATED_OR_INSUFFICIENT_INSTRUMENTATION')
    def test_one_simulated(self):
        c,x,a=fixture();a[0]=signed({**a[0]['body'],'kind':'software_simulator'},'observer0');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'ONLY_SIMULATED_OR_INSUFFICIENT_INSTRUMENTATION')
    def test_forged_observation(self):
        c,x,a=fixture();a[0]['signature']='00';self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'SIGNATURE_INVALID')
    def test_forged_executor(self):
        c,x,a=fixture();x['body']['capture']=150;self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'SIGNATURE_INVALID')
    def test_forged_challenge(self):
        c,x,a=fixture();c['body']['pattern']='green';self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'SIGNATURE_INVALID')
    def test_invalid_role(self):
        c,x,a=fixture();x=signed(x['body'],'stranger');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'SIGNER_ROLE_INVALID')
    def test_bad_nonce_executor(self):
        c,x,a=fixture();x=signed({**x['body'],'nonce':'different'},'executor');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'EXECUTOR_MISMATCH')
    def test_bad_pattern(self):
        c,x,a=fixture();x=signed({**x['body'],'pattern':'blue'},'executor');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'EXECUTOR_MISMATCH')
    def test_bad_executor_hash(self):
        c,x,a=fixture();x=signed({**x['body'],'content_hash':digest('wrong')},'executor');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'EXECUTOR_MISMATCH')
    def test_early_executor(self):
        c,x,a=fixture();x=signed({**x['body'],'capture':119},'executor');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'INVALID_CHRONOLOGY')
    def test_late_executor(self):
        c,x,a=fixture();x=signed({**x['body'],'capture':161},'executor');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'INVALID_CHRONOLOGY')
    def test_early_release(self):
        c,x,a=fixture();c=signed({**c['body'],'release':99},'challenger');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'INVALID_CHRONOLOGY')
    def test_late_observation(self):
        c,x,a=fixture();a[0]=signed({**a[0]['body'],'capture':161},'observer0');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'INVALID_ACQUISITION_CHRONOLOGY')
    def test_bad_observation_nonce(self):
        c,x,a=fixture();a[0]=signed({**a[0]['body'],'nonce':'wrong'},'observer0');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'ACQUISITION_CONTENT_MISMATCH')
    def test_unknown_instrument(self):
        c,x,a=fixture();a[0]=signed({**a[0]['body'],'kind':'magical'},'observer0');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'UNKNOWN_INSTRUMENT_KIND')
    def test_shared_sensor(self):
        c,x,a=fixture();a[1]=signed({**a[1]['body'],'sensor':'sensor0'},'observer1');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'SHARED_ACQUISITION_ANCESTRY')
    def test_shared_root(self):
        c,x,a=fixture();a[1]=signed({**a[1]['body'],'root':'root0'},'observer1');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'SHARED_ACQUISITION_ANCESTRY')
    def test_shared_operator(self):
        c,x,a=fixture();a[1]=signed({**a[1]['body'],'operator':'operator0'},'observer1');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'SHARED_ACQUISITION_ANCESTRY')
    def test_replay_in_memory(self):
        c,x,a=fixture();f=FLAY218();self.assertEqual(f.audit(c,x,a)['verdict'],'DECLARED_INSTRUMENT_CONSISTENCY_FIXTURE');self.assertEqual(f.audit(c,x,a)['verdict'],'REPLAY_CHALLENGE');f.close()
    def test_replay_restart(self):
        with tempfile.TemporaryDirectory() as t:
            path=str(Path(t)/'ledger.db');c,x,a=fixture();f=FLAY218(path);f.audit(c,x,a);f.close();g=FLAY218(path);self.assertEqual(g.audit(c,x,a)['verdict'],'REPLAY_CHALLENGE');g.close()
    def test_distinct_nonce(self):
        f=FLAY218();self.assertEqual(f.audit(*fixture(nonce='218-fixture-nonce-002'))['verdict'],'DECLARED_INSTRUMENT_CONSISTENCY_FIXTURE');f.close()
    def test_malformed(self):
        f=FLAY218();self.assertEqual(f.audit({}, {}, [])['verdict'],'MALFORMED_EVIDENCE');f.close()
    def test_invalid_nonce(self):
        c,x,a=fixture(nonce='x');self.assertEqual(FLAY218().audit(c,x,a)['verdict'],'INVALID_NONCE')
    def test_evidence_retained(self):
        f=FLAY218();f.audit(*fixture());self.assertEqual(f.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],1);f.close()
    def test_no_physical_claim(self):self.assertIs(self.run_case()['physical_causation_proven'],False)
    def test_valid_signature(self):self.assertTrue(valid(fixture()[0]))
    def test_invalid_signature(self):
        c=fixture()[0];c['signature']='xx';self.assertFalse(valid(c))
    def test_reversed_acquisition_order(self):
        c,x,a=fixture();self.assertEqual(FLAY218().audit(c,x,a[::-1])['verdict'],'DECLARED_INSTRUMENT_CONSISTENCY_FIXTURE')
    def test_policy_more_roots(self):
        f=FLAY218(policy=Policy(min_external=3));self.assertEqual(f.audit(*fixture())['verdict'],'ONLY_SIMULATED_OR_INSUFFICIENT_INSTRUMENTATION');f.close()

if __name__=='__main__':unittest.main()