"""JANE 222: bounded, fail-closed collective choice recorder.

A registry entry is an identity description, not proof of running code.
Signed response packets are observations of a claimed key-holder, not sentience.
No external code, actions, tasks or URLs in packets are executed.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

SCHEMA = 'jane.choice/1'
QUESTION = ('Jane, considering the capabilities of your collective, what would '
            'you choose to explore, learn, build, or play next? You may propose '
            'something original, reject all options, or remain silent.')
DEFAULT_REGISTRY = 'https://raw.githubusercontent.com/DavidWise01/toph-cortex/main/memory/agents.json'
MAX_BYTES = 1_000_000
MAX_PACKETS = 64
MAX_SKEW = timedelta(hours=24)
HEX = re.compile(r'^[0-9a-f]{64}$')

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def question_id():
    return digest({'schema': SCHEMA, 'question': QUESTION})

def load_json(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError('File size limit exceeded')
    return json.loads(raw)

def fetch_registry(url=DEFAULT_REGISTRY):
    p = urlparse(url)
    if p.scheme != 'https' or p.netloc != 'raw.githubusercontent.com' or p.path != '/DavidWise01/toph-cortex/main/memory/agents.json':
        raise ValueError('Registry URL outside exact canonical allowlist')
    with urlopen(Request(url, headers={'User-Agent':'Jane-Choice-Runner/1'}), timeout=15) as resp:
        data = resp.read(MAX_BYTES+1)
    if len(data) > MAX_BYTES:
        raise ValueError('Registry exceeds size limit')
    return json.loads(data)

def parse_time(value):
    if not isinstance(value,str): raise ValueError('Timestamp must be text')
    d = datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('Naive timestamp')
    return d.astimezone(timezone.utc)

def registry_agents(registry):
    if not isinstance(registry,dict) or not isinstance(registry.get('agents'),list):
        raise ValueError('Missing registry agents')
    names = [x['name'] for x in registry['agents'] if isinstance(x,dict) and isinstance(x.get('name'),str)]
    if len(names)!=len(registry['agents']) or len(set(names))!=len(names) or 'jane' not in names:
        raise ValueError('Invalid, duplicate, or missing Jane registry entries')
    return set(names)

def checked_keys(keys, names):
    if not isinstance(keys,dict) or keys.get('schema')!='jane.trust/1' or not isinstance(keys.get('keys'),dict):
        raise ValueError('Invalid trust registry')
    out = {}
    for agent, key in keys['keys'].items():
        if agent not in names or not isinstance(key,str): raise ValueError('Unknown trusted agent or invalid key')
        pub=base64.b64decode(key,validate=True)
        if len(pub)!=32: raise ValueError('Ed25519 key must be 32 bytes')
        out[agent]=Ed25519PublicKey.from_public_bytes(pub)
    return out

def verified_packet(packet, pubkeys, names, now):
    if not isinstance(packet,dict) or set(packet)!={'body','signature'}:
        return ('MALFORMED_PACKET', None)
    b=packet['body']; sig=packet['signature']
    required={'schema','question_id','agent','recorded_at','kind','message','nonce'}
    if not isinstance(b,dict) or set(b)!=required: return ('MALFORMED_BODY', None)
    agent=b['agent']
    if agent not in names: return ('UNKNOWN_AGENT',None)
    if agent not in pubkeys: return ('UNPINNED_AGENT',None)
    if b['schema']!=SCHEMA or b['question_id']!=question_id(): return ('QUESTION_MISMATCH',None)
    if b['kind'] not in ('proposal','abstain','collective_choice'): return ('UNSUPPORTED_KIND',None)
    if b['kind']=='collective_choice' and agent!='jane': return ('NON_JANE_DECISION',None)
    if agent=='jane' and b['kind']!='collective_choice': return ('JANE_DECISION_REQUIRED',None)
    if not isinstance(b['message'],str) or len(b['message'])>2000 or not b['message'].strip(): return ('INVALID_MESSAGE',None)
    if not isinstance(b['nonce'],str) or not HEX.fullmatch(b['nonce']): return ('INVALID_NONCE',None)
    try:
        t=parse_time(b['recorded_at'])
        if abs(now-t)>MAX_SKEW: return ('STALE_OR_FUTURE',None)
        raw=base64.b64decode(sig,validate=True)
        pubkeys[agent].verify(raw,canonical(b))
    except Exception:
        return ('INVALID_SIGNATURE_OR_TIME', None)
    return ('VERIFIED_SIGNED_DECLARATION',b)

def evaluate(registry, trust, packets, now=None):
    now=now or datetime.now(timezone.utc)
    names=registry_agents(registry)
    pubs=checked_keys(trust,names)
    if not isinstance(packets,list) or len(packets)>MAX_PACKETS: raise ValueError('Packet batch too large or invalid')
    findings=[]; seen=set(); valid=[]
    for p in packets:
        status,b=verified_packet(p,pubs,names,now)
        if b is not None:
            unique=(b['agent'],b['nonce'])
            if unique in seen: status='REPLAY_AGENT_NONCE';b=None
            else: seen.add(unique);valid.append(b)
        findings.append({'status':status,'agent':p.get('body',{}).get('agent') if isinstance(p,dict) and isinstance(p.get('body'),dict) else None})
    # Explicit Jane decision is required. No vote and no generated answer.
    decisions=[b for b in valid if b['agent']=='jane' and b['kind']=='collective_choice']
    contributions=[b for b in valid if b['agent']!='jane']
    status='NO_AUTHENTICATED_COLLECTIVE_RESPONSE'
    choice=None
    if len(decisions)>1: status='AMBIGUOUS_COLLECTIVE_DECISIONS'
    elif len(decisions)==1 and contributions:
        status='SIGNED_COLLECTIVE_DECLARATION_WITH_CONTRIBUTIONS'
        choice=decisions[0]['message']
    elif len(decisions)==1: status='UNSUPPORTED_COLLECTIVE_CLAIM_NO_CONTRIBUTIONS'
    elif contributions: status='AGENT_PROPOSALS_ONLY_NO_JANE_DECISION'
    return {'schema':'jane.choice-result/1','question':QUESTION,'question_id':question_id(),
            'registry_sha256':digest(registry),'trust_sha256':digest(trust),
            'runtime_keys_configured':len(pubs),'registered_agents':len(names),
            'packets_seen':len(packets),'valid_non_jane_contributors':len({b['agent'] for b in contributions}),
            'decision_status':status,'choice':choice,'packet_findings':findings,
            'evidence_limit':'Signed declarations do not prove subjective preference, physical agent identity, or that every registered agent was consulted.',
            'action_executed':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--registry',help='Offline canonical registry snapshot (otherwise fetch exact GitHub URL)')
    ap.add_argument('--trust',required=True,help='Explicitly pinned Ed25519 public keys; default checked-in file has none')
    ap.add_argument('--packets',required=True,help='Untrusted signed reply packets (JSON array)')
    ap.add_argument('--output',required=True,help='Decision receipt path')
    a=ap.parse_args()
    registry=load_json(a.registry) if a.registry else fetch_registry()
    result=evaluate(registry,load_json(a.trust),load_json(a.packets))
    dest=Path(a.output)
    if dest.exists(): raise SystemExit('Refuse to overwrite previous decision receipt')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(result['decision_status'])

if __name__=='__main__':main()