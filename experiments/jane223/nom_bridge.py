"""JANE 223 — bounded, read-only observation of NOM's actual citation ledger.

This adapter never calls NOM an LLM, never attributes desire, and does not
execute remote-supplied instructions. It records evidence only, not a vote.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = 'jane.component-observation/1'
MAX_BYTES = 2_000_000
MAX_LINES = 10000
REQUIRED = {'wiki','wiki_rev','arxiv','arxiv_title','arxiv_pub','verdict','read'}
SHA = re.compile(r'^[a-f0-9]{40}$')


def date(s):
    if not isinstance(s, str):
        raise ValueError('timestamp must be text')
    out = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if out.tzinfo is None:
        raise ValueError('timestamp must be timezone-aware')
    return out.astimezone(timezone.utc)


def audit(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError('bounded raw ledger required')
    if raw and not raw.endswith(b'\n'):
        raise ValueError('truncated ledger')
    rows = raw.splitlines()
    if len(rows) > MAX_LINES:
        raise ValueError('too many ledger rows')
    found = []
    for i, line in enumerate(rows, 1):
        if not line or len(line) > 12000:
            raise ValueError(f'bad line {i}')
        try:
            item = json.loads(line)
        except (ValueError, UnicodeError) as exc:
            raise ValueError(f'invalid JSON line {i}') from exc
        if not isinstance(item, dict) or not REQUIRED.issubset(item):
            raise ValueError(f'missing schema at line {i}')
        for k in REQUIRED:
            if not isinstance(item[k], str):
                raise ValueError(f'non-string field {k} at line {i}')
        a = urlsplit(item['arxiv']); w = urlsplit(item['wiki'])
        if (a.scheme, a.hostname) != ('https','arxiv.org') or (w.scheme,w.hostname) != ('https','en.wikipedia.org'):
            raise ValueError(f'unapproved source host line {i}')
        if a.username or w.username or a.port or w.port or not a.path.startswith('/abs/') or not w.path.startswith('/wiki/'):
            raise ValueError(f'invalid source path line {i}')
        if item['verdict'] != 'NEW' or date(item['arxiv_pub']) <= date(item['wiki_rev']):
            raise ValueError(f'invalid timestamp comparison line {i}')
        date(item['read'])
        found.append(item)
    return {'count':len(found),'last_read':found[-1]['read'] if found else None,
            'ledger_sha256':hashlib.sha256(raw).hexdigest()}


def observe(raw, *, commit, registry=None):
    if not isinstance(commit,str) or not SHA.fullmatch(commit):
        raise ValueError('complete 40-char source commit required')
    if registry is not None:
        if not isinstance(registry,dict) or not isinstance(registry.get('agents'),list) or not any(
            isinstance(x,dict) and x.get('name')=='nom' for x in registry['agents']):
            raise ValueError('NOM is not registered')
    info = audit(raw)
    return {'schema':SCHEMA,'agent':'nom','source_repository':'DavidWise01/nom',
            'source_commit':commit,'capability':'deterministic_citation_ledger_audit',
            'execution':'local_read_only_audit_of_git_content',
            'evidence':info,'observation_status':'AUDITED_SOURCE_RECORDS',
            'independent_runtime_attestation':False,'agent_proposal':None,
            'collective_choice':None,'action_executed':False,
            'limitations':'Passing an offline audit does not show NOM executed recently, independently sent a message, or expressed a preference.'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ledger',required=True)
    ap.add_argument('--nom-commit',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--registry')
    args=ap.parse_args()
    raw=Path(args.ledger).read_bytes()
    if len(raw)>MAX_BYTES: raise SystemExit('Ledger size exceeds bound')
    reg=json.loads(Path(args.registry).read_text()) if args.registry else None
    result=observe(raw,commit=args.nom_commit,registry=reg)
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,sort_keys=True); f.write('\n')
    print(f"{result['observation_status']}: {result['evidence']['count']} rows; collective choice remains unknown")


if __name__=='__main__': main()
