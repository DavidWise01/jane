"""JANE 225: signed, bounded component-reply verifier. No network or autonomous calls.

An actor-specific signed declaration is evidence of that signing key's output,
NOT evidence of independent agency, desire, physical identity, or collective consent.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

SCHEMA = 'jane.agent-reply/1'
ALLOWED = {'propose', 'abstain'}

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def b64(data):
    return base64.b64encode(data).decode('ascii')

def unb64(value):
    return base64.b64decode(value, validate=True)

def fingerprint(pk):
    return hashlib.sha256(unb64(pk)).hexdigest()

def challenge(agent_id, nonce, issued_at, expires_at, question_hash):
    return {'schema': 'jane.agent-challenge/1', 'agent_id': agent_id, 'nonce': nonce,
            'issued_at': issued_at, 'expires_at': expires_at, 'question_sha256': question_hash}

def signed_response(private, req, decision, proposal='', reason=''):
    if decision not in ALLOWED: raise ValueError('invalid decision')
    if decision == 'abstain' and proposal: raise ValueError('abstention cannot propose')
    if decision == 'propose' and not proposal.strip(): raise ValueError('empty proposal')
    payload = {'schema': SCHEMA, 'agent_id': req['agent_id'], 'request_sha256': hashlib.sha256(canonical(req)).hexdigest(),
               'nonce': req['nonce'], 'decision': decision, 'proposal': proposal, 'reason': reason}
    return {'payload': payload, 'signature': b64(private.sign(canonical(payload)))}

def iso(s):
    t = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if t.tzinfo is None: raise ValueError('timezone required')
    return t.astimezone(timezone.utc)

class ReplayStore:
    def __init__(self, path):
        self.conn = sqlite3.connect(str(path))
        self.conn.execute('CREATE TABLE IF NOT EXISTS accepted (agent_id TEXT NOT NULL, nonce TEXT NOT NULL, request_hash TEXT NOT NULL, reply_hash TEXT NOT NULL, PRIMARY KEY(agent_id, nonce))')
    def reserve(self, agent, nonce, request_hash, reply_hash):
        try:
            with self.conn:
                self.conn.execute('INSERT INTO accepted VALUES (?,?,?,?)', (agent, nonce, request_hash, reply_hash))
        except sqlite3.IntegrityError:
            return False
        return True
    def close(self): self.conn.close()

def verify(packet, req, trust, store, now=None):
    """Validate without changing state on any rejection. Only accepted replies consume nonce."""
    try:
        p, sig = packet['payload'], unb64(packet['signature'])
        if set(packet) != {'payload', 'signature'}: return {'verdict':'EXTRA_PACKET_FIELDS'}
        if set(p) != {'schema','agent_id','request_sha256','nonce','decision','proposal','reason'}: return {'verdict':'MALFORMED_RESPONSE'}
        if set(req) != {'schema','agent_id','nonce','issued_at','expires_at','question_sha256'}: return {'verdict':'MALFORMED_CHALLENGE'}
        if req['schema'] != 'jane.agent-challenge/1' or p['schema'] != SCHEMA: return {'verdict':'BAD_SCHEMA'}
        if not isinstance(req['nonce'],str) or len(req['nonce']) < 24: return {'verdict':'WEAK_CHALLENGE_NONCE'}
        if not isinstance(req['question_sha256'], str) or len(req['question_sha256']) != 64 or any(x not in '0123456789abcdef' for x in req['question_sha256']): return {'verdict':'BAD_QUESTION_HASH'}
        if p['agent_id'] != req['agent_id'] or p['nonce'] != req['nonce'] or p['request_sha256'] != hashlib.sha256(canonical(req)).hexdigest(): return {'verdict':'CHALLENGE_MISMATCH'}
        if not all(isinstance(p[k],str) for k in ('agent_id','decision','proposal','reason')): return {'verdict':'MALFORMED_RESPONSE'}
        if p['decision'] not in ALLOWED: return {'verdict':'INVALID_DECISION'}
        if p['decision'] == 'abstain' and p['proposal']: return {'verdict':'ABSTENTION_CONFLICT'}
        if p['decision'] == 'propose' and not p['proposal'].strip(): return {'verdict':'EMPTY_PROPOSAL'}
        if len(p['proposal']) > 2000 or len(p['reason']) > 4000: return {'verdict':'OVERSIZE_RESPONSE'}
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None: return {'verdict':'BAD_CLOCK'}
        start, end = iso(req['issued_at']), iso(req['expires_at'])
        if not start < end or (end - start).total_seconds() > 3600: return {'verdict':'BAD_CHALLENGE_WINDOW'}
        if not start <= now.astimezone(timezone.utc) <= end: return {'verdict':'STALE_OR_FUTURE_CHALLENGE'}
        key = trust.get(p['agent_id'])
        if not isinstance(key, dict) or not key.get('enabled') or not key.get('public_key_b64'): return {'verdict':'UNTRUSTED_RUNTIME'}
        Ed25519PublicKey.from_public_bytes(unb64(key['public_key_b64'])).verify(sig, canonical(p))
        h = hashlib.sha256(canonical(packet)).hexdigest()
        if not store.reserve(p['agent_id'],p['nonce'],p['request_sha256'],h): return {'verdict':'REPLAY'}
        return {'verdict':'AUTHENTICATED_COMPONENT_RESPONSE', 'agent_id':p['agent_id'],
                'decision':p['decision'], 'proposal':p['proposal'], 'reason':p['reason'],
                'reply_sha256':h,'runtime_key_fingerprint':fingerprint(key['public_key_b64']),
                'collective_decision':'UNRESOLVED', 'action_executed':False}
    except Exception as e:
        if isinstance(e, (ValueError,TypeError,KeyError,AttributeError,OverflowError)): return {'verdict':'MALFORMED_INPUT'}
        return {'verdict':'INVALID_SIGNATURE_OR_KEY'}

def aggregate(results):
    # No voting, no implicit authority escalation.
    return {'schema':'jane.collective-observation/1','components':results,
            'collective_decision':'UNRESOLVED', 'action_executed':False,
            'note':'Component declarations are not a collective authorization or demonstrated desire.'}

def run_cli(args):
    req=json.loads(Path(args.challenge).read_text())
    trust=json.loads(Path(args.trust).read_text())
    packets=json.loads(Path(args.responses).read_text())
    if not isinstance(packets,list): raise ValueError('responses must be array')
    if len(packets)>32: raise ValueError('bounded maximum 32 packets')
    with_store=ReplayStore(args.audit)
    try: out=aggregate([verify(x,req,trust,with_store) for x in packets])
    finally: with_store.close()
    Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'responses':len(out['components']),'verdicts':[x['verdict'] for x in out['components']], 'collective_decision':out['collective_decision']}))

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for item in ('challenge','trust','responses','audit','output'): a.add_argument('--'+item,required=True)
    run_cli(a.parse_args())