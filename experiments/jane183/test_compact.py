import copy,random,unittest
from compact import *
class CompactTests(unittest.TestCase):
    def setUp(self):
        self.xs=[leaf({'i':i}) for i in range(12)]
        self.keys=[signer('k'+str(i),'a'+str(i)) for i in range(3)]
    def test_demo(self):self.assertEqual(demo()['status'],'CONSISTENT_COMPACT_FIXTURE')
    def test_audit(self):
        f=FLAY(self.keys);f.reconcile(signed_checkpoint(self.xs[:6],self.keys,1,'a'),signed_checkpoint(self.xs,self.keys,2,'b'),make_proof(self.xs,6));self.assertEqual(f.audit(),'VALID_LOCAL_CHAIN')
    def test_all_prefix_sizes(self):
        for n in range(1,70):
            xs=[leaf(i) for i in range(n)]
            for m in range(1,n+1):
                p=make_proof(xs,m)
                self.assertTrue(verify(p,commit(xs[:m]),commit(xs)),(m,n))
    def test_random_differential(self):
        rng=random.Random(183)
        for _ in range(1000):
            n=rng.randint(1,128);m=rng.randint(1,n)
            xs=[leaf(rng.getrandbits(64)) for _ in range(n)]
            p=make_proof(xs,m)
            self.assertEqual(verify(p,commit(xs[:m]),commit(xs)),xs[:m]==xs[:m])
            other=xs[:];pos=rng.randrange(m);other[pos]=leaf(('edited',pos))
            self.assertFalse(verify(p,commit(xs[:m]),commit(other)))
    def test_jane182_reference_differential(self):
        import sys
        sys.path.insert(0,'/mnt/data/jane182')
        from consistency import make_proof as explicit, verify_path as path_check, root as ref_root, path as ref_path
        rng=random.Random(182183)
        for _ in range(300):
            n=rng.randint(1,72);m=rng.randint(1,n)
            values=[{'sequence':i,'salt':rng.getrandbits(48)} for i in range(n)]
            xs=[leaf(x) for x in values]
            old=xs[:m]
            self.assertEqual(commit(old),ref_root([x.hex() for x in old]))
            self.assertEqual(commit(xs),ref_root([x.hex() for x in xs]))
            old_hex=[x.hex() for x in old];new_hex=[x.hex() for x in xs]
            evidence=explicit(old_hex,new_hex)
            reference=(ref_root(evidence['prefix'])==ref_root(old_hex) and all(path_check(v,i,n,p,ref_root(new_hex)) for i,(v,p) in enumerate(zip(evidence['prefix'],evidence['paths']))))
            compact=verify(make_proof(xs,m),commit(old),commit(xs))
            self.assertEqual(reference,compact)
            edited=xs[:];edited[rng.randrange(m)]=leaf({'modified':rng.getrandbits(32)})
            self.assertFalse(verify(make_proof(xs,m),commit(old),commit(edited)))
    def test_no_leaf_material_in_proof(self):self.assertLessEqual(len(make_proof(self.xs,6)['nodes']),2*len(self.xs).bit_length())
    def test_rewritten_prefix(self):
        changed=self.xs[:];changed[2]=leaf('rewrite');self.assertFalse(verify(make_proof(changed,6),commit(self.xs[:6]),commit(changed)))
    def test_reordered_prefix(self):
        changed=self.xs[:];changed[2],changed[3]=changed[3],changed[2];self.assertFalse(verify(make_proof(changed,6),commit(self.xs[:6]),commit(changed)))
    def test_removed_prefix(self):
        changed=self.xs[:2]+self.xs[3:];self.assertFalse(verify(make_proof(changed,6),commit(self.xs[:6]),commit(changed)))
    def test_claimed_tree_size(self):
        p=make_proof(self.xs,6);p['new_size']+=1;self.assertFalse(verify(p,commit(self.xs[:6]),commit(self.xs)))
    def test_claimed_old_size(self):
        p=make_proof(self.xs,6);p['old_size']+=1;self.assertFalse(verify(p,commit(self.xs[:6]),commit(self.xs)))
    def test_missing_node(self):
        p=make_proof(self.xs,6);p['nodes'].pop();self.assertFalse(verify(p,commit(self.xs[:6]),commit(self.xs)))
    def test_extra_node(self):
        p=make_proof(self.xs,6);p['nodes'].append('0'*64);self.assertFalse(verify(p,commit(self.xs[:6]),commit(self.xs)))
    def test_modified_node(self):
        p=make_proof(self.xs,6);p['nodes'][0]='0'*64;self.assertFalse(verify(p,commit(self.xs[:6]),commit(self.xs)))
    def test_old_root_opening(self):
        p=make_proof(self.xs,6);p['old_internal']='0'*64;self.assertFalse(verify(p,commit(self.xs[:6]),commit(self.xs)))
    def test_old_root_modified(self):self.assertFalse(verify(make_proof(self.xs,6),'0'*64,commit(self.xs)))
    def test_new_root_modified(self):self.assertFalse(verify(make_proof(self.xs,6),commit(self.xs[:6]),'0'*64))
    def test_forged_signature(self):
        a=signed_checkpoint(self.xs[:6],self.keys,1,'a');a[0]['signature']='00'*64
        f=FLAY(self.keys);self.assertEqual(f.reconcile(a,signed_checkpoint(self.xs,self.keys,2,'b'),make_proof(self.xs,6)),'BAD_SIGNATURE')
    def test_shared_admin(self):
        keys=[signer(str(i),'shared') for i in range(3)]
        f=FLAY(keys);self.assertEqual(f.reconcile(signed_checkpoint(self.xs[:6],keys,1,'a'),signed_checkpoint(self.xs,keys,2,'b'),make_proof(self.xs,6)),'SHARED_OR_INSUFFICIENT_CUSTODY')
    def test_replay(self):
        a=signed_checkpoint(self.xs[:6],self.keys,1,'a');b=signed_checkpoint(self.xs,self.keys,2,'b');f=FLAY(self.keys);self.assertEqual(f.reconcile(a,b,make_proof(self.xs,6)),'CONSISTENT_COMPACT_FIXTURE');self.assertEqual(f.reconcile(a,b,make_proof(self.xs,6)),'REPLAY')
    def test_rollback(self):
        f=FLAY(self.keys);self.assertEqual(f.reconcile(signed_checkpoint(self.xs,self.keys,2,'a'),signed_checkpoint(self.xs[:6],self.keys,3,'b'),make_proof(self.xs,6)),'ROLLBACK_OR_REPLAY')
    def test_no_auto_learning(self):self.assertFalse(demo()['active_parent_changed'])
    def test_tampered_ledger(self):
        f=FLAY(self.keys);f.append('test','payload');f.events[0]['status']='altered';self.assertEqual(f.audit(),'TAMPERED')
    def test_non_integer_size(self):
        p=make_proof(self.xs,6);p['old_size']=6.0;self.assertFalse(verify(p,commit(self.xs[:6]),commit(self.xs)))
    def test_empty_proof_rejected(self):
        with self.assertRaises(ValueError):make_proof(self.xs,0)
    def test_size_limit(self):self.assertFalse(verify(make_proof(self.xs,6),commit(self.xs[:6]),commit(self.xs),max_size=6))
if __name__=='__main__':unittest.main(verbosity=2)