import unittest,tempfile,os,sqlite3
from provenance import FLAY220,fixture,sha,sign,pub,verify

class AuditTests(unittest.TestCase):
    def run_kind(self,k):
        f=FLAY220()
        try:return f.audit(*fixture(k,nonce=f'jane220-{k}-test-nonce'))['verdict']
        finally:f.close()
    def test_valid(self):self.assertEqual(self.run_kind('valid'),'DECLARED_SUPPLY_CHAIN_CONSISTENT_FIXTURE')
    def test_impostor(self):self.assertEqual(self.run_kind('impostor'),'MANUFACTURING_ENROLLMENT_MISMATCH')
    def test_broken(self):self.assertEqual(self.run_kind('broken'),'BROKEN_CUSTODY_CHAIN')
    def test_shared(self):self.assertEqual(self.run_kind('shared'),'SHARED_PROVENANCE_OR_CAPTURE')
    def test_expired(self):self.assertEqual(self.run_kind('expired'),'ENROLLMENT_EXPIRED')
    def test_late(self):self.assertEqual(self.run_kind('late'),'CAPTURE_OUTSIDE_WINDOW')
    def test_mismatch(self):self.assertEqual(self.run_kind('mismatch'),'RESPONSE_MISMATCH')
    def test_revoked(self):self.assertEqual(self.run_kind('revoked'),'REVOKED_DEVICE')
    def test_missing(self):self.assertEqual(self.run_kind('missing'),'MISSING_CUSTODY_CHAIN')
    def test_self_signed(self):self.assertEqual(self.run_kind('self-signed'),'SELF_DECLARED_DEVICE')
    def test_false_maker(self):self.assertEqual(self.run_kind('false-maker'),'UNTRUSTED_MANUFACTURER_CLAIM')
    def test_physical_false(self):
        f=FLAY220();r=f.audit(*fixture());f.close();self.assertFalse(r['physical_origin_proven'])
    def test_bad_signature(self):
        items=list(fixture());items[0]['signature']='00'; f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'INVALID_CHALLENGE_SIGNATURE');f.close()
    def test_repeat_same_instance(self):
        f=FLAY220();items=fixture();self.assertEqual(f.audit(*items)['verdict'],'DECLARED_SUPPLY_CHAIN_CONSISTENT_FIXTURE');self.assertEqual(f.audit(*items)['verdict'],'REPLAY_CHALLENGE');f.close()
    def test_repeat_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path=os.path.join(td,'test.db');items=fixture()
            a=FLAY220(path);a.audit(*items);a.close()
            b=FLAY220(path);self.assertEqual(b.audit(*items)['verdict'],'REPLAY_CHALLENGE');b.close()
    def test_tamper_chain(self):
        f=FLAY220();f.audit(*fixture());f.db.execute("UPDATE events SET verdict='altered'");f.db.commit();self.assertFalse(f.log_ok());self.assertEqual(f.audit(*fixture(nonce='jane220-tamper-nonce'))['verdict'],'CORRUPT_LOG');f.close()
    def test_bad_nonce(self):
        items=list(fixture());items[0]=sign({**items[0]['body'],'nonce':'x'},'challenger');f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'INVALID_NONCE');f.close()
    def test_invalid_revocation(self):
        items=list(fixture());items[5]=[sign({'issuer':'revocation-authority','device':'device-0'},'attacker')];f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'INVALID_REVOCATION');f.close()
    def test_enrollment_issuer(self):
        items=list(fixture());items[3][1]=sign(items[3][1]['body'],'attacker');f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'INVALID_ENROLLMENT_ISSUER');f.close()
    def test_device_signature(self):
        items=list(fixture());items[4][1]=sign(items[4][1]['body'],'attacker');f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'DEVICE_SIGNATURE_INVALID');f.close()
    def test_insufficient(self):
        items=list(fixture());items[4]=items[4][:1];f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'INSUFFICIENT_DEVICES');f.close()
    def test_transfer_tamper(self):
        items=list(fixture());items[2][0]['body']['to']='attacker';f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'INVALID_CUSTODY_TRANSFER');f.close()
    def test_duplicate_manufacturing(self):
        items=list(fixture());items[1].append(items[1][0]);f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'DUPLICATE_DEVICE');f.close()
    def test_duplicate_enrollment(self):
        items=list(fixture());items[3].append(items[3][0]);f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'DUPLICATE_ENROLLMENT');f.close()
    def test_duplicate_revocation(self):
        items=list(fixture());r=sign({'issuer':'revocation-authority','device':'device-0'},'revocation-authority');items[5]=[r,r];f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'DUPLICATE_REVOCATION');f.close()
    def test_unknown_revocation_is_not_physical_proof(self):
        items=list(fixture());items[5]=[sign({'issuer':'revocation-authority','device':'other-device'},'revocation-authority')];f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'DECLARED_SUPPLY_CHAIN_CONSISTENT_FIXTURE');f.close()
    def test_canonical_hash(self):self.assertEqual(sha({'a':1,'b':2}),sha({'b':2,'a':1}))
    def test_signature_roundtrip(self):self.assertTrue(verify(sign({'x':5},'manufacturer'),pub('manufacturer')))
    def test_wrong_key(self):self.assertFalse(verify(sign({'x':5},'manufacturer'),pub('attacker')))
    def test_timing_invalid(self):
        items=list(fixture());cb=items[0]['body'];items[0]=sign({**cb,'deadline':100},'challenger');f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'INVALID_CHRONOLOGY');f.close()
    def test_missing_manufacturer(self):
        items=list(fixture());items[1]=items[1][:1];f=FLAY220();self.assertEqual(f.audit(*items)['verdict'],'MISSING_MANUFACTURING_CLAIM');f.close()
    def test_bad_data(self):
        f=FLAY220();self.assertEqual(f.audit({'body':{'nonce':'jane220-bad-001'}},[],[],[],[])['verdict'],'INVALID_CHALLENGE_SIGNATURE');f.close()

if __name__=='__main__':unittest.main()