import copy
import unittest
from inheritance import audit,digest,ROOT_TYPES
NOW='2026-11-15T20:00:00Z'
K1='1'*64; K2='2'*64; K3='3'*64;CH='a'*64
ROOTS={x:x+'-shared' for x in ROOT_TYPES}
FRESH={x:x+'-new' for x in ROOT_TYPES}

def event(kind='ENROLLED',key=K1,replacement=None,roots=None,seq=1):
    return {'id':f'e-{seq}','kind':kind,'key':key,'replacement':replacement,
            'roots':(ROOTS if roots is None else roots).copy(),'time':f'2026-11-15T19:{seq:02d}:00Z',
            'challenge':CH,'prev':'0'*64,'witness':'fixture-not-authenticated'}
def make(*events):
    xs=[];prev='0'*64
    for i,e in enumerate(events,1):
        e=copy.deepcopy(e);e['prev']=prev;prev=digest(e);xs.append(e)
    return {'subject':'jane-fixture','challenge':CH,'events':xs}
def baseline():return make(event())
def compromised(rotation_roots=None):
    return make(event(),event('EXPOSURE',seq=2),event('ROTATED',replacement=K2,roots=rotation_roots,seq=3))
def check(b):return audit(b,NOW)['verdict']
class InheritanceTests(unittest.TestCase):
    def test_empty(self):self.assertEqual(check({'subject':'jane','challenge':CH,'events':[]}), 'NO_RUNTIME_CUSTODY_EVIDENCE')
    def test_valid_fixture(self):self.assertEqual(check(baseline()),'NO_KNOWN_OVERLAP_UNVERIFIED')
    def test_exposure_inherited(self):self.assertEqual(check(compromised()),'INHERITED_COMPROMISE')
    def test_new_roots_claim_not_proof(self):
        r=audit(compromised(FRESH),NOW);self.assertEqual(r['verdict'],'NO_KNOWN_OVERLAP_UNVERIFIED');self.assertFalse(r['clean_environment_proven'])
    def test_copied_admin(self):
        r=FRESH.copy();r['administrator']=ROOTS['administrator'];self.assertEqual(check(compromised(r)),'INHERITED_COMPROMISE')
    def test_copied_credential(self):
        r=FRESH.copy();r['credential']=ROOTS['credential'];self.assertEqual(check(compromised(r)),'INHERITED_COMPROMISE')
    def test_copied_runner(self):
        r=FRESH.copy();r['runner']=ROOTS['runner'];self.assertEqual(check(compromised(r)),'INHERITED_COMPROMISE')
    def test_copied_pipeline(self):
        r=FRESH.copy();r['build_pipeline']=ROOTS['build_pipeline'];self.assertEqual(check(compromised(r)),'INHERITED_COMPROMISE')
    def test_exposure_then_remediation_doesnt_clear(self):
        b=make(event(),event('EXPOSURE',seq=2),event('REMEDIATED',seq=3),event('ROTATED',replacement=K2,seq=4));self.assertEqual(check(b),'INHERITED_COMPROMISE')
    def test_two_rotations_reuse_root(self):
        b=make(event(),event('EXPOSURE',seq=2),event('ROTATED',replacement=K2,roots=FRESH,seq=3),event('ROTATED',key=K2,replacement=K3,seq=4))
        self.assertEqual(check(b),'INHERITED_COMPROMISE')
    def test_chain_tamper(self):
        b=compromised();b['events'][1]['prev']='f'*64;self.assertEqual(check(b),'BROKEN_PROVENANCE_CHAIN')
    def test_challenge_tamper(self):
        b=baseline();b['events'][0]['challenge']='b'*64;self.assertEqual(check(b),'BROKEN_PROVENANCE_CHAIN')
    def test_replay(self):
        b=make(event(),event('EXPOSURE',seq=2));b['events'][1]['id']='e-1';self.assertEqual(check(b),'REPLAYED_EVENT')
    def test_reordered_time(self):
        b=make(event(),event('EXPOSURE',seq=2));b['events'][1]['time']=b['events'][0]['time'];self.assertEqual(check(b),'INVALID_EVENT_TIME')
    def test_future_time(self):
        b=baseline();b['events'][0]['time']='2026-11-16T01:00:00Z';self.assertEqual(check(b),'INVALID_EVENT_TIME')
    def test_timezone_required(self):
        b=baseline();b['events'][0]['time']='2026-11-15T19:00:00';self.assertEqual(check(b),'INVALID_EVENT')
    def test_no_root(self):
        b=baseline();del b['events'][0]['roots']['runner'];self.assertEqual(check(b),'INVALID_ROOTS')
    def test_empty_root(self):
        b=baseline();b['events'][0]['roots']['runner']='';self.assertEqual(check(b),'INVALID_ROOTS')
    def test_unknown_kind(self):
        b=baseline();b['events'][0]['kind']='SAFE';self.assertEqual(check(b),'INVALID_EVENT')
    def test_extra_event_field(self):
        b=baseline();b['events'][0]['safe']=True;self.assertEqual(check(b),'INVALID_EVENT')
    def test_forged_replace_without_active(self):
        b=make(event('ROTATED',replacement=K2));self.assertEqual(check(b),'INVALID_LIFECYCLE')
    def test_duplicate_key(self):
        b=make(event(),event('ROTATED',replacement=K1,seq=2));self.assertEqual(check(b),'INVALID_LIFECYCLE')
    def test_revoked_lifecycle(self):
        b=make(event(),event('REVOKED',seq=2));self.assertEqual(check(b),'NO_ACTIVE_KEY')
    def test_revoke_wrong(self):
        b=make(event(),event('REVOKED',key=K2,seq=2));self.assertEqual(check(b),'INVALID_LIFECYCLE')
    def test_root_history_change(self):
        b=make(event(),event('EXPOSURE',roots=FRESH,seq=2));self.assertEqual(check(b),'ROOT_HISTORY_MUTATED')
    def test_missing_subject(self):
        b=baseline();del b['subject'];self.assertEqual(check(b),'INVALID_BUNDLE')
    def test_missing_challenge(self):
        b=baseline();b['challenge']='z'*64;self.assertEqual(check(b),'INVALID_BUNDLE')
    def test_too_many(self):
        self.assertEqual(audit({'subject':'jane','challenge':CH,'events':[{}]*129},NOW)['verdict'],'INVALID_BUNDLE')
    def test_no_execution(self):
        r=audit(baseline(),NOW);self.assertEqual(r['actions_executed'],0);self.assertEqual(r['jane_collective_choice'],'UNRESOLVED')
    def test_no_live_witnesses(self):self.assertEqual(audit(baseline(),NOW)['authenticated_live_witnesses'],0)
    def test_no_secret_claim(self):self.assertFalse(audit(baseline(),NOW)['exclusive_key_custody_proven'])
    def test_body_not_self_attested(self):self.assertFalse(audit(baseline(),NOW)['clean_environment_proven'])
    def test_invalid_now(self):self.assertEqual(audit(baseline(),'bad')['verdict'],'INVALID_BUNDLE')
    def test_malformed_events(self):self.assertEqual(audit({'subject':'x','challenge':CH,'events':'bad'},NOW)['verdict'],'INVALID_BUNDLE')
    def test_malformed_root_type(self):
        b=baseline();b['events'][0]['roots']['runner']=None;self.assertEqual(check(b),'INVALID_ROOTS')
    def test_no_events_not_evidence(self):self.assertEqual(audit({'subject':'jane','challenge':CH,'events':[]},NOW)['events_checked'],0)
if __name__=='__main__':unittest.main()
