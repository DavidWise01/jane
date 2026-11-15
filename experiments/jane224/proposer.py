"""JANE 224 — bounded proposal emitted by an executable adapter.

Proposal is a deterministic suggestion from observed NOM records, never NOM's wish
and never a collective Jane decision. No network calls, shell commands or writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = 'jane.component-proposal/1'
MAX_FILE = 2_000_000
MAX_ROWS = 10_000
SHA40 = re.compile(r'^[0-9a-f]{40}$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
FIELDS = {'wiki', 'wiki_rev', 'arxiv', 'arxiv_title', 'arxiv_pub', 'verdict', 'read'}


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def as_time(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be text')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timestamp requires zone')
    return parsed.astimezone(timezone.utc)


def host(url):
    if not isinstance(url, str):
        raise ValueError('URL must be text')
    p = urlsplit(url)
    if p.scheme != 'https' or p.username or p.password or p.port or not p.path or p.query or p.fragment:
        raise ValueError('disallowed URL')
    return p.hostname


def read_limited(path):
    with Path(path).open('rb') as f:
        raw = f.read(MAX_FILE+1)
    if len(raw) > MAX_FILE:
        raise ValueError('file too large')
    return raw


def jsonlines(raw, *, ground=False):
    try:
        lines = raw.decode('utf-8').splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError('invalid UTF-8') from exc
    if len(lines) > MAX_ROWS:
        raise ValueError('too many rows')
    rows = []
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'invalid JSON line {i}') from exc
        if not isinstance(row, dict):
            raise ValueError(f'line {i} not object')
        if not ground:
            validate_citation(row)
        else:
            if not isinstance(row.get('wiki'), str) or not isinstance(row.get('arxiv'), str):
                raise ValueError(f'ground row {i} missing pair')
            if host(row['wiki']) != 'en.wikipedia.org' or host(row['arxiv']) != 'arxiv.org':
                raise ValueError(f'ground row {i} source invalid')
        rows.append(row)
    return rows


def validate_citation(row):
    if not FIELDS.issubset(row) or row.get('verdict') != 'NEW':
        raise ValueError('bad citation schema/verdict')
    if host(row['wiki']) != 'en.wikipedia.org' or host(row['arxiv']) != 'arxiv.org':
        raise ValueError('disallowed research source')
    if not isinstance(row['arxiv_title'], str) or len(row['arxiv_title']) > 1000:
        raise ValueError('invalid title')
    if as_time(row['arxiv_pub']) <= as_time(row['wiki_rev']):
        raise ValueError('not newer')
    as_time(row['read'])


def propose(ledger_raw, ground_raw, *, nom_commit, ground_commit=None):
    if not SHA40.fullmatch(nom_commit) or not SHA40.fullmatch(ground_commit or nom_commit):
        raise ValueError('source commit must be full lowercase SHA40')
    ledger = jsonlines(ledger_raw)
    ground = jsonlines(ground_raw, ground=True)
    ledger_pairs = [(row['wiki'], row['arxiv']) for row in ledger]
    if len(set(ledger_pairs)) != len(ledger_pairs):
        raise ValueError('duplicate citation pair')
    ledger_set = set(ledger_pairs)
    grounded = set()
    for row in ground:
        pair = (row['wiki'], row['arxiv'])
        if pair not in ledger_set:
            raise ValueError('ground receipt for nonexistent citation')
        grounded.add(pair)
    unresolved = [(i, row) for i, row in enumerate(ledger) if (row['wiki'], row['arxiv']) not in grounded]
    choice = None
    if unresolved:
        index, row = unresolved[0]
        choice = {'candidate_id':hash_bytes(canonical({'wiki':row['wiki'],'arxiv':row['arxiv']})),
                  'task':'Recheck the earliest ungrounded NOM citation pair against its original two permitted research sources',
                  'ledger_index':index + 1,
                  'wiki':row['wiki'], 'arxiv':row['arxiv'],
                  'origin':'adapter-generated gap selection; not NOM preference',
                  'execution_authorized':False}
    result = {
       'schema':SCHEMA,
       'producer':'jane224-proposer',
       'producer_kind':'deterministic_adapter',
       'origin_agent':'nom',
       'origin_agent_spoke':False,
       'jane_collective_answered':False,
       'collective_choice':None,
       'next_action_authorized':False,
       'source': {'repo':'DavidWise01/nom','commit':nom_commit,
                 'ledger_sha256':hash_bytes(ledger_raw),
                 'ground_sha256':hash_bytes(ground_raw),
                 'ground_commit':ground_commit or nom_commit},
       'counts': {'citations':len(ledger),'ground_receipts':len(ground),
                  'unique_grounded_pairs':len(grounded),'unresolved_pairs':len(unresolved)},
       'status':'CANDIDATE_PROPOSAL_ONLY' if choice else 'NO_UNGROUNDED_CITATION',
       'candidate':choice,
       'evidence_level':'SOURCE_CONSISTENCY_NOT_AGENT_PREFERENCE',
       'limitations': [
         'The adapter chooses a gap by explicit deterministic rule, not NOM or Jane.',
         'Git commit plus SHA-256 identifies data, not independent witness identity.',
         'No live research-source freshness or semantic relevance was verified.',
         'A candidate does not authorize any action or establish subjective desire.'
       ]
    }
    result['receipt_sha256'] = hash_bytes(canonical(result))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ledger',required=True)
    p.add_argument('--ground',required=True)
    p.add_argument('--nom-commit',required=True)
    p.add_argument('--output',required=True)
    a = p.parse_args()
    result=propose(read_limited(a.ledger),read_limited(a.ground),nom_commit=a.nom_commit)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n', encoding='utf-8')
    print(result['status'], 'unresolved=',result['counts']['unresolved_pairs'])

if __name__=='__main__':
    main()