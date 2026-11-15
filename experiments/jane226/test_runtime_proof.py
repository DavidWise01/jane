import hashlib, json, tempfile, unittest
from pathlib import Path
import runtime_proof as r

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.worker=Path(__file__).with_name('bounded_worker.py')
        self.sha=r.sha_file(self.worker)
        self.req=r.challenge('jane-component-demo','a'*48,self.sha)
        self.db=self.dir/'audit.db'
    def go(self,req=None,worker=None,sha=None,db=None,**kwargs):
        return r.execute(req or self.req,worker or self.worker,sha or self.sha,db or self.db,**kwargs)
    def assert_rejected(self,verdict,**kw):
        self.assertEqual(self.go(**kw)['verdict'],verdict)
    def test_good_run(self):
        o=self.go();self.assertEqual(o['verdict'],'OBSERVED_ALLOWLISTED_PROCESS_RUN')
        self.assertEqual(o['collective_decision'],'UNRESOLVED')
        self.assertFalse(o['action_executed'])
        self.assertEqual(o['observed_output']['decision'],'propose')
    def test_replay(self):
        self.go();self.assert_rejected('REPLAY')
    def test_restart_replay(self):
        self.go();self.assert_rejected('REPLAY')
    def test_source_tampered(self):
        p=self.dir/'worker.py';p.write_bytes(self.worker.read_bytes()+b'\n#tamper')
        self.assert_rejected('EXECUTABLE_HASH_MISMATCH',worker=p)
    def test_bad_pin(self):self.assert_rejected('BAD_PIN',sha='garbage')
    def test_short_nonce(self):
        req=dict(self.req,nonce='tiny');self.assert_rejected('WEAK_NONCE',req=req)
    def test_wrong_question(self):
        req=dict(self.req,question_sha256='b'*64);self.assert_rejected('QUESTION_MISMATCH',req=req)
    def test_wrong_source(self):
        req=dict(self.req,source_sha256='b'*64);self.assert_rejected('SOURCE_DIGEST_MISMATCH',req=req)
    def test_wrong_agent(self):
        req=dict(self.req,agent_id='fake');self.assert_rejected('BAD_AGENT_BINDING',req=req)
    def test_extra_challenge_field(self):
        req=dict(self.req,foo=1);self.assert_rejected('INVALID_CHALLENGE_SCHEMA',req=req)
    def test_timeout_limit(self):self.assert_rejected('BAD_TIMEOUT',timeout=16)
    def test_context_injection(self):self.assert_rejected('UNKNOWN_CONTEXT_FIELD',context={'admin':True})
    def test_empty_context(self):self.assertEqual(self.go(context={})['verdict'],'OBSERVED_ALLOWLISTED_PROCESS_RUN')
    def test_context_claims_not_attestation(self):
        out=self.go(context={'github_sha':'f'*40})
        self.assertEqual(out['runner_claims']['github_sha'],'f'*40)
        self.assertIn('NOT_INDEPENDENT_ATTESTATION',out['provenance_level'])
    def test_worker_bad_json(self):
        p=self.dir/'bad.py';p.write_text('print("hello")\n')
        req=r.challenge('jane-component-demo','a'*48,r.sha_file(p))
        self.assert_rejected('WORKER_OUTPUT_NOT_JSON',req=req,worker=p,sha=r.sha_file(p))
    def test_worker_exit(self):
        p=self.dir/'bad.py';p.write_text('raise SystemExit(3)\n')
        req=r.challenge('jane-component-demo','a'*48,r.sha_file(p))
        self.assert_rejected('WORKER_EXIT_NONZERO',req=req,worker=p,sha=r.sha_file(p))
    def test_worker_stderr(self):
        p=self.dir/'bad.py';p.write_text('import sys\nprint("bad",file=sys.stderr)\nprint("{}")\n')
        req=r.challenge('jane-component-demo','a'*48,r.sha_file(p))
        self.assert_rejected('WORKER_OUTPUT_UNSAFE',req=req,worker=p,sha=r.sha_file(p))
    def test_worker_wrong_nonce(self):
        self.worker_bad_field('nonce','stolen','WORKER_BINDING_MISMATCH')
    def test_worker_wrong_agent(self):
        self.worker_bad_field('agent_id','someone-else','WORKER_BINDING_MISMATCH')
    def test_worker_wrong_source(self):
        self.worker_bad_field('source_sha256','1'*64,'WORKER_SOURCE_MISMATCH')
    def test_worker_bad_decision(self):
        self.worker_bad_field('decision','go-live','INVALID_DECISION')
    def test_worker_abstention_conflict(self):
        self.worker_bad_field('decision','abstain','ABSTENTION_CONFLICT')
    def test_worker_empty_proposal(self):
        self.worker_bad_field('proposal','','EMPTY_PROPOSAL')
    def test_worker_oversize(self):
        self.worker_bad_field('reason','x'*3001,'OVERSIZE_TEXT')
    def test_worker_schema(self):
        self.worker_bad_field('schema','foo','WORKER_SCHEMA_MISMATCH')
    def test_worker_missing_field(self):
        self.worker_bad_field('reason',None,'WORKER_SCHEMA_MISMATCH',delete=True)
    def test_worker_abstain_valid(self):
        body=self.base_output();body['decision']='abstain';body['proposal']=''
        self.assertEqual(self.run_custom(body),'OBSERVED_ALLOWLISTED_PROCESS_RUN')
    def test_worker_output_binding(self):
        out=self.go();self.assertEqual(out['output_sha256'], r.digest(r.enc(out['observed_output'])+b'\n'))
    def test_change_nonce_is_distinct(self):
        self.go();req=dict(self.req,nonce='b'*48)
        self.assertEqual(self.go(req=req)['verdict'],'OBSERVED_ALLOWLISTED_PROCESS_RUN')
    def test_invalid_worker_type(self):
        self.worker_bad_field('proposal',123,'INVALID_TEXT')
    def test_worker_extra_field(self):
        self.worker_bad_field('ignored',True,'WORKER_SCHEMA_MISMATCH')
    def base_output(self):
        return {'schema':r.WORKER_SCHEMA,'agent_id':self.req['agent_id'],
           'nonce':self.req['nonce'],'source_sha256':'PLACEHOLDER',
           'decision':'propose','proposal':'some action','reason':'fixture'}
    def run_custom(self,body):
        p=self.dir/'fixture.py'
        # output source sha dynamically from input so source binding remains valid.
        p.write_text("import json,sys\nr=json.load(sys.stdin)\no="+repr(body)+"\nif o.get('source_sha256')=='PLACEHOLDER':o['source_sha256']=r['source_sha256']\nprint(json.dumps(o))\n")
        sha=r.sha_file(p);req=r.challenge('jane-component-demo','a'*48,sha)
        return self.go(req=req,worker=p,sha=sha)['verdict']
    def worker_bad_field(self,key,val,expected,delete=False):
        b=self.base_output()
        if delete:del b[key]
        else:b[key]=val
        self.assertEqual(self.run_custom(b),expected)

if __name__=='__main__':unittest.main()
