"""JANE 228: conservative ancestry audit for alleged independent run witnesses.

Inputs are declared metadata or separately fetched records. A distinct ID is not a
fresh trust root. GitHub-hosted witnesses share the GitHub platform root even when
repositories and runner IDs differ. This module NEVER proves physical independence.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = 'jane228.execution-ancestry/1'
VALID_TYPES = {'github_actions', 'local_subprocess', 'external_attestor'}
TRUST_FIELDS = ('platform_root', 'credential_root', 'runner_root', 'workflow_root',
                'source_root', 'artifact_root', 'operator_root')
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,159}$')
SHA = re.compile(r'^[0-9a-f]{64}$')

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()

def result(code, nodes=(), collisions=(), unknowns=(), groups=(), notes=()):
    out = dict(schema=SCHEMA, verdict=code, independent_execution_witnesses_established=0,
               verified_physical_or_hardware_independence=False,
               jane_collective_decision='UNRESOLVED', action_executed=False,
               witnesses_examined=len(nodes), collisions=list(collisions), unknowns=list(unknowns),
               components=list(groups), notes=list(notes))
    out['result_sha256']=digest(out)
    return out

def validate(w):
    if not isinstance(w, dict): return 'BAD_RECORD'
    required={'id','kind','repo','run_id','commit','evidence_digest','roots','evidence_origin'}
    if not required <= w.keys(): return 'MISSING_FIELDS'
    if w['kind'] not in VALID_TYPES: return 'BAD_KIND'
    if any(not isinstance(w[k],str) or not ID.fullmatch(w[k]) for k in ('id','repo','run_id','commit')):
        return 'BAD_IDENTIFIER'
    if not isinstance(w['evidence_digest'],str) or not SHA.fullmatch(w['evidence_digest']):
        return 'BAD_EVIDENCE_DIGEST'
    if w['evidence_origin'] not in ('separately_retrieved','self_reported'): return 'BAD_ORIGIN'
    roots=w['roots']
    if not isinstance(roots,dict) or set(roots)!=set(TRUST_FIELDS): return 'BAD_ROOT_SCHEMA'
    for k,v in roots.items():
        if v is not None and (not isinstance(v,str) or not ID.fullmatch(v)):
            return 'BAD_ROOT_VALUE'
    # Immutable GitHub platform provenance cannot honestly be labeled as independent platform.
    if w['kind']=='github_actions' and roots['platform_root']!='github.com/actions':
        return 'FORGED_PLATFORM_ROOT'
    return None

def connected_components(ids, collisions):
    adjacency={i:set() for i in ids}
    for e in collisions:
        a,b=e['a'],e['b']; adjacency[a].add(b);adjacency[b].add(a)
    seen=set(); groups=[]
    for first in sorted(ids):
        if first in seen: continue
        stack=[first];seen.add(first);group=[]
        while stack:
            a=stack.pop();group.append(a)
            for b in sorted(adjacency[a]):
                if b not in seen:seen.add(b);stack.append(b)
        groups.append(sorted(group))
    return groups

def verify(witnesses):
    if not isinstance(witnesses,list) or len(witnesses)>100:
        return result('BAD_WITNESS_SET')
    if not witnesses:return result('NO_EXECUTION_WITNESSES')
    ids=[]
    for i,w in enumerate(witnesses):
        err=validate(w)
        if err:return result(err, witnesses[:i], notes=[f'invalid index {i}'])
        ids.append(w['id'])
    if len(set(ids))!=len(ids):return result('DUPLICATE_WITNESS_ID',witnesses)
    collisions=[];unknowns=[]
    for n,a in enumerate(witnesses):
        for b in witnesses[n+1:]:
            shared=[];unknown=[]
            for f in TRUST_FIELDS:
                av=a['roots'][f];bv=b['roots'][f]
                if av is None or bv is None:unknown.append(f)
                elif av==bv:shared.append(f)
            # A source or run reused by a supposed independent witness is correlated.
            if a['repo']==b['repo'] and a['run_id']==b['run_id']:
                shared.append('same_run')
            if a['evidence_digest']==b['evidence_digest']:
                shared.append('same_evidence_digest')
            if shared:collisions.append(dict(a=a['id'],b=b['id'],shared=sorted(shared)))
            if unknown:unknowns.append(dict(a=a['id'],b=b['id'],unknown=sorted(unknown)))
    groups=connected_components(ids,collisions)
    self_reported=[w['id'] for w in witnesses if w['evidence_origin']=='self_reported']
    notes=['Identity labels and metadata alone are not independent platform attestations.']
    if self_reported:notes.append('Self-reported metadata: '+', '.join(self_reported))
    if collisions:code='SHARED_EXECUTION_ANCESTRY'
    elif unknowns:code='UNKNOWN_EXECUTION_ANCESTRY'
    else:code='DECLARED_DISTINCT_ROOTS_NOT_ATTESTED'
    if len(witnesses)==1:code='SINGLE_EXECUTION_WITNESS'
    return result(code,witnesses,collisions,unknowns,groups,notes)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    witnesses=json.loads(args.input.read_text(encoding='utf8'))
    out=verify(witnesses)
    args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(out['verdict'], 'witnesses=',out['witnesses_examined'])
    return 0
if __name__=='__main__':raise SystemExit(main())
