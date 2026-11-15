"""JANE 226: bounded runtime observation; local process receipt, not hardware attestation.

An execution wrapper can bind an allowed program's source, stdin, stdout,
process status, and nonce to a reproducible receipt. It cannot independently
prove the runner was uncompromised, the code was genuinely executed on a remote
machine, or the generated choice belonged to a conscious collective.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

SCHEMA = 'jane.runtime-receipt/1'
WORKER_SCHEMA = 'jane.runtime-worker-output/1'
QUESTION = 'If no next task is assigned, what should the collective investigate next?'
MAX_OUTPUT = 12000


def enc(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(file):
    return digest(Path(file).read_bytes())


def valid_hex(x, count):
    return isinstance(x, str) and len(x) == count and all(y in '0123456789abcdef' for y in x)


def challenge(agent, nonce, source_sha, question=QUESTION):
    return {'schema': 'jane.runtime-challenge/1', 'agent_id': agent,
            'nonce': nonce, 'source_sha256': source_sha, 'question_sha256': digest(question.encode())}


def checked_challenge(req, agent, source_sha):
    if not isinstance(req, dict) or set(req) != {'schema','agent_id','nonce','source_sha256','question_sha256'}:
        raise ValueError('INVALID_CHALLENGE_SCHEMA')
    if req['schema'] != 'jane.runtime-challenge/1' or req['agent_id'] != agent:
        raise ValueError('BAD_AGENT_BINDING')
    if not isinstance(req['nonce'], str) or len(req['nonce']) < 32:
        raise ValueError('WEAK_NONCE')
    if req['source_sha256'] != source_sha or not valid_hex(source_sha, 64):
        raise ValueError('SOURCE_DIGEST_MISMATCH')
    if req['question_sha256'] != digest(QUESTION.encode()):
        raise ValueError('QUESTION_MISMATCH')


class Audit:
    def __init__(self, path):
        self.db = sqlite3.connect(str(path))
        self.db.execute('CREATE TABLE IF NOT EXISTS observations (agent_id TEXT, nonce TEXT, receipt_sha TEXT, PRIMARY KEY(agent_id,nonce))')
    def claim(self, agent, nonce, h):
        try:
            with self.db:
                self.db.execute('INSERT INTO observations VALUES (?,?,?)', (agent, nonce, h))
            return True
        except sqlite3.IntegrityError:
            return False
    def close(self):
        self.db.close()


def verify_worker_output(data, req):
    if not isinstance(data, dict) or set(data) != {'schema','agent_id','nonce','decision','proposal','reason','source_sha256'}:
        raise ValueError('WORKER_SCHEMA_MISMATCH')
    if data['schema'] != WORKER_SCHEMA:
        raise ValueError('WORKER_SCHEMA_MISMATCH')
    if data['agent_id'] != req['agent_id'] or data['nonce'] != req['nonce']:
        raise ValueError('WORKER_BINDING_MISMATCH')
    if data['source_sha256'] != req['source_sha256']:
        raise ValueError('WORKER_SOURCE_MISMATCH')
    if data['decision'] not in ('propose','abstain'):
        raise ValueError('INVALID_DECISION')
    if not isinstance(data['proposal'],str) or not isinstance(data['reason'],str):
        raise ValueError('INVALID_TEXT')
    if len(data['proposal']) > 2000 or len(data['reason']) > 3000:
        raise ValueError('OVERSIZE_TEXT')
    if data['decision'] == 'propose' and not data['proposal'].strip():
        raise ValueError('EMPTY_PROPOSAL')
    if data['decision'] == 'abstain' and data['proposal']:
        raise ValueError('ABSTENTION_CONFLICT')
    return data


def execute(req, worker_path, expected_worker_sha, audit_path, *, agent='jane-component-demo', timeout=5, cwd=None, context=None):
    """Run a fixed Python script without shell, bound input, and fail-closed receipt."""
    context = context or {}
    result = {'schema': SCHEMA, 'agent_id': agent, 'nonce': req.get('nonce') if isinstance(req,dict) else None,
              'verdict':'WITHHELD', 'collective_decision':'UNRESOLVED','action_executed':False,
              'provenance_level':'LOCAL_PROCESS_OBSERVATION_NOT_INDEPENDENT_ATTESTATION'}
    audit = None
    try:
        if not valid_hex(expected_worker_sha,64): raise ValueError('BAD_PIN')
        actual = sha_file(worker_path)
        if actual != expected_worker_sha: raise ValueError('EXECUTABLE_HASH_MISMATCH')
        checked_challenge(req,agent,expected_worker_sha)
        if not 0 < timeout <= 15: raise ValueError('BAD_TIMEOUT')
        if any(x not in {'github_repository','github_sha','github_run_id','github_workflow_ref'} for x in context):
            raise ValueError('UNKNOWN_CONTEXT_FIELD')
        # Do not inherit secrets/environment through the subprocess.
        safe_env = {'PATH':os.environ.get('PATH',''), 'PYTHONDONTWRITEBYTECODE':'1', 'PYTHONIOENCODING':'utf-8'}
        started = datetime.now(timezone.utc).isoformat()
        run = subprocess.run([sys.executable, '-I', str(Path(worker_path).resolve())],
                             input=enc(req), capture_output=True, timeout=timeout, cwd=cwd,
                             env=safe_env, shell=False)
        finished = datetime.now(timezone.utc).isoformat()
        if run.returncode != 0: raise ValueError('WORKER_EXIT_NONZERO')
        if len(run.stdout) > MAX_OUTPUT or run.stderr: raise ValueError('WORKER_OUTPUT_UNSAFE')
        try: data = json.loads(run.stdout)
        except (UnicodeError,json.JSONDecodeError): raise ValueError('WORKER_OUTPUT_NOT_JSON')
        verify_worker_output(data,req)
        body = {'schema':SCHEMA, 'agent_id':agent,'nonce':req['nonce'],
                'challenge_sha256':digest(enc(req)), 'source_sha256':actual,
                'output_sha256':digest(run.stdout), 'observed_output':data,
                'exit_code':run.returncode,'started_utc':started,'finished_utc':finished,
                'runner_claims':context,'collective_decision':'UNRESOLVED',
                'action_executed':False,'provenance_level':'LOCAL_PROCESS_OBSERVATION_NOT_INDEPENDENT_ATTESTATION'}
        h=digest(enc(body))
        audit=Audit(audit_path)
        if not audit.claim(agent,req['nonce'],h): raise ValueError('REPLAY')
        result = dict(body,receipt_sha256=h,verdict='OBSERVED_ALLOWLISTED_PROCESS_RUN')
    except subprocess.TimeoutExpired:
        result['verdict']='WORKER_TIMEOUT'
    except (OSError, ValueError, TypeError, KeyError) as e:
        result['verdict'] = str(e) if isinstance(e,ValueError) else 'MALFORMED_OR_IO_ERROR'
    finally:
        if audit: audit.close()
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--worker',default='bounded_worker.py')
    ap.add_argument('--audit',default='runtime-audit.sqlite')
    ap.add_argument('--out',default='execution-receipt.json')
    ap.add_argument('--nonce',required=True)
    ap.add_argument('--agent',default='jane-component-demo')
    args=ap.parse_args()
    sha=sha_file(args.worker)
    req=challenge(args.agent,args.nonce,sha)
    context={k:v for k,v in {'github_repository':os.environ.get('GITHUB_REPOSITORY'),
      'github_sha':os.environ.get('GITHUB_SHA'), 'github_run_id':os.environ.get('GITHUB_RUN_ID'),
      'github_workflow_ref':os.environ.get('GITHUB_WORKFLOW_REF')}.items() if v}
    receipt=execute(req,args.worker,sha,args.audit,agent=args.agent,context=context)
    Path(args.out).write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'verdict':receipt['verdict'],'collective_decision':receipt['collective_decision']}))
    return 0 if receipt['verdict']=='OBSERVED_ALLOWLISTED_PROCESS_RUN' else 1

if __name__=='__main__': raise SystemExit(main())
