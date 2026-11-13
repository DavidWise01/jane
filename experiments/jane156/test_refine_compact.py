import unittest
from refine_compact import Interval,Affine,verify,experiment,digest

class JANE156RepositoryTests(unittest.TestCase):
    def test_original_fails(self):
        self.assertEqual(verify(Interval(0),Affine(-1,20),0)['status'],'INDUCTIVE_FAILURE')
    def test_smallest_witness(self):
        self.assertEqual(verify(Interval(0),Affine(-1,20),0)['witness'],21)
    def test_negative_image(self):
        self.assertEqual(verify(Interval(0),Affine(-1,20),0)['next'],-1)
    def test_proposed_proven(self):
        self.assertEqual(verify(Interval(0,20),Affine(-1,20),0)['status'],'INDUCTIVE_PROVEN')
    def test_smaller_rejected(self):
        self.assertEqual(verify(Interval(0,19),Affine(-1,20),0)['status'],'INDUCTIVE_FAILURE')
    def test_endpoint_swap(self):
        self.assertEqual((Affine(-1,20).apply(0),Affine(-1,20).apply(20)),(20,0))
    def test_initial_gate(self):
        self.assertEqual(verify(Interval(1,20),Affine(-1,20),0)['status'],'INITIAL_OUTSIDE')
    def test_original_preserved(self):
        self.assertEqual([x['kind'] for x in experiment()['events']][1],'PRESERVE_FAILURE')
    def test_digest(self):
        r=experiment();self.assertEqual(r['digest'],digest({k:v for k,v in r.items() if k!='digest'}))
    def test_parent_frozen(self):
        self.assertEqual(experiment()['parent'],'FROZEN')
    def test_no_activation(self):
        self.assertFalse(experiment()['learning_applied'])
    def test_deterministic(self):
        self.assertEqual(experiment(),experiment())
if __name__=='__main__':unittest.main()
