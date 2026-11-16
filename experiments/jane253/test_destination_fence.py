import tempfile,unittest,threading
from pathlib import Path
from destination_fence import Destination,FenceError,demo

class DestinationFenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.db=str(Path(self.tmp.name)/'destination.sqlite');self.d=Destination(self.db)
    def grant_a(self):self.d.grant('task',1,'a','g1')
    def grant_b(self):self.d.grant('task',2,'b','g2')
    def test_first_grant(self):self.assertEqual(self.d.grant('task',1,'a','g1')['verdict'],'GRANTED')
    def test_identical_grant_idempotent(self):self.grant_a();self.assertEqual(self.d.grant('task',1,'a','g1')['verdict'],'IDEMPOTENT_GRANT')
    def test_same_epoch_other_holder(self):self.grant_a();self.assertRaises(FenceError,self.d.grant,'task',1,'b','new')
    def test_decreasing_epoch(self):self.grant_a();self.grant_b();self.assertRaises(FenceError,self.d.grant,'task',1,'a','other')
    def test_duplicate_grant_across_resources(self):self.grant_a();self.assertRaises(FenceError,self.d.grant,'other',1,'b','g1')
    def test_invalid_epoch_zero(self):self.assertRaises(FenceError,self.d.grant,'task',0,'a','g1')
    def test_invalid_epoch_boolean(self):self.assertRaises(FenceError,self.d.grant,'task',True,'a','g1')
    def test_invalid_resource(self):self.assertRaises(FenceError,self.d.grant,'../escape',1,'a','g1')
    def test_missing_authority(self):self.assertEqual(self.d.commit('task',1,'a','op','p')['committed'],False)
    def test_correct_commit(self):self.grant_a();self.assertTrue(self.d.commit('task',1,'a','op','p')['committed'])
    def test_wrong_holder(self):self.grant_a();self.assertEqual(self.d.commit('task',1,'b','op','p')['verdict'],'UNAUTHORIZED_DESTINATION_WRITE')
    def test_future_epoch(self):self.grant_a();self.assertEqual(self.d.commit('task',3,'a','op','p')['verdict'],'UNAUTHORIZED_DESTINATION_WRITE')
    def test_stale_epoch(self):self.grant_a();self.grant_b();self.assertEqual(self.d.commit('task',1,'a','op','p')['verdict'],'FENCED_STALE_EPOCH')
    def test_precheck_then_grant_then_commit(self):
        self.grant_a();self.assertTrue(self.d.precheck('task',1,'a'));self.grant_b()
        self.assertFalse(self.d.commit('task',1,'a','delayed','p')['committed'])
    def test_current_after_takeover(self):self.grant_a();self.grant_b();self.assertTrue(self.d.commit('task',2,'b','new','p')['committed'])
    def test_replay_idempotent(self):
        self.grant_a();self.d.commit('task',1,'a','op','p');self.assertEqual(self.d.commit('task',1,'a','op','p')['verdict'],'IDEMPOTENT_REPLAY')
    def test_replay_changed_payload(self):
        self.grant_a();self.d.commit('task',1,'a','op','p');self.assertEqual(self.d.commit('task',1,'a','op','changed')['verdict'],'OPERATION_ID_CONFLICT')
    def test_replay_after_takeover_fenced(self):
        self.grant_a();self.d.commit('task',1,'a','op','p');self.grant_b()
        self.assertEqual(self.d.commit('task',1,'a','op','p')['verdict'],'FENCED_STALE_EPOCH')
    def test_op_reuse_between_epochs_conflict(self):
        self.grant_a();self.d.commit('task',1,'a','op','p');self.grant_b()
        self.assertEqual(self.d.commit('task',2,'b','op','p')['verdict'],'OPERATION_ID_CONFLICT')
    def test_distinct_resource_isolation(self):
        self.grant_a();self.d.grant('other',1,'b','other-grant')
        self.assertTrue(self.d.commit('other',1,'b','op','p')['committed'])
    def test_same_op_different_resources(self):
        self.grant_a();self.d.grant('other',1,'b','other-grant')
        self.assertTrue(self.d.commit('task',1,'a','op','p')['committed']);self.assertTrue(self.d.commit('other',1,'b','op','p')['committed'])
    def test_large_payload(self):self.grant_a();self.assertRaises(FenceError,self.d.commit,'task',1,'a','op','x'*8193)
    def test_nonstring_payload(self):self.grant_a();self.assertRaises(FenceError,self.d.commit,'task',1,'a','op',b'bytes')
    def test_invalid_operation_id(self):self.grant_a();self.assertRaises(FenceError,self.d.commit,'task',1,'a','bad id','p')
    def test_invalid_commit_epoch(self):self.grant_a();self.assertRaises(FenceError,self.d.commit,'task',False,'a','op','p')
    def test_attempt_preserved(self):self.grant_a();self.grant_b();self.d.commit('task',1,'a','op','p');self.assertEqual(len(self.d.inspect('task')['attempts']),1)
    def test_effects_not_written_on_failure(self):self.grant_a();self.grant_b();self.d.commit('task',1,'a','op','p');self.assertEqual(len(self.d.inspect('task')['effects']),0)
    def test_three_events(self):
        self.grant_a();self.d.commit('task',1,'a','first','p');self.grant_b();self.d.commit('task',1,'a','old','p');self.d.commit('task',2,'b','new','p')
        r=self.d.inspect('task');self.assertEqual(len(r['attempts']),3);self.assertEqual(len(r['effects']),2)
    def test_reopen_state(self):self.grant_a();self.assertEqual(Destination(self.db).inspect('task')['authority']['epoch'],1)
    def test_concurrent_same_op_one_effect(self):
        self.grant_a();results=[];barrier=threading.Barrier(3)
        def f():barrier.wait();results.append(Destination(self.db).commit('task',1,'a','same','p')['verdict'])
        t1=threading.Thread(target=f);t2=threading.Thread(target=f);t1.start();t2.start();barrier.wait();t1.join();t2.join()
        self.assertEqual(set(results),{'COMMITTED','IDEMPOTENT_REPLAY'});self.assertEqual(len(self.d.inspect('task')['effects']),1)
    def test_demo(self):
        r=demo(str(Path(self.tmp.name)/'demo.sqlite'))
        self.assertEqual(r['a_delayed_attempt']['verdict'],'FENCED_STALE_EPOCH');self.assertEqual(r['b_current_attempt']['verdict'],'COMMITTED')
    def test_no_collective_choice(self):self.assertEqual(self.d.inspect('task')['collective_choice'],'UNRESOLVED')

if __name__=='__main__':unittest.main(verbosity=2)