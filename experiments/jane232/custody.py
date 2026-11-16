"""JANE 232: bounded offline signed custody-event audit; never proves private-key secrecy."""
import argparse
import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

SCHEMA = 'jane232.custody/1'
HEX64 = re.compile(r'^[0-9a-f]{64}$')
VALID_EVENTS = {'ENROLLED', 'CUSTODY_ATTESTED', 'EXPOSURE_SUSPECTED', 'EXPOSURE_CONFIRMED', 'REVOKED', 'ROTATED'}
ALLOWED_ROLES = {'registrar', 'custody_auditor', 'security_operator'}

def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def digest(v):
    return hashlib.sha256(canonical(v)).hexdigest()

def parse_time(value):
    if not isinstance(value, str):
        raise ValueError('timestamp_not_string')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timestamp_without_zone')
    return dt.astimezone(timezone.utc)

def verify(pubkey, body, sig):
    try:
        p = base64.b64decode(pubkey, validate=True)
        s = base64.b64decode(sig, validate=True)
        if len(p) != 32 or len(s) != 64:
            return False
        Ed25519PublicKey.from_public_bytes(p).verify(s, canonical(body))
        return True
    except (ValueError, TypeError, KeyError, Exception):
        return False

def verdict(name, events=0, errors=(), authenticated=0, custody='UNKNOWN', key=None):
    return {'schema': SCHEMA, 'verdict': name, 'event_count': events,
            'authenticated_events': authenticated, 'custody_state': custody,
            'active_key': key, 'errors': list(errors),
            'exclusive_custody_proven': False,
            'jane_collective_choice': 'UNRESOLVED', 'actions_executed': 0}

def audit(bundle, now, max_events=256):
    """Public keys are pinned by an OUT-OF-BAND trusted configuration.
    A signed custody claim is evidence of that signer saying it, not proof of actual custody.
    All events must be present, ordered, signed, and cryptographically chained.
    Any reported exposure/revocation stops continued key use, even if a later event says safe.
    """
    try:
        clock = parse_time(now)
        if not isinstance(bundle, dict) or set(bundle) != {'subject', 'anchors', 'events', 'challenge'}:
            return verdict('INVALID_BUNDLE', errors=['bundle_shape'])
        subject, anchors, events, challenge = (bundle[k] for k in ('subject','anchors','events','challenge'))
        if not isinstance(subject, str) or not (1 <= len(subject) <= 120):
            return verdict('INVALID_BUNDLE', errors=['subject'])
        if not isinstance(challenge, str) or not HEX64.fullmatch(challenge):
            return verdict('INVALID_BUNDLE', errors=['challenge'])
        if not isinstance(anchors, dict) or not isinstance(events, list) or len(events) > max_events:
            return verdict('INVALID_BUNDLE', errors=['anchors_events'])
        if not events:
            return verdict('NO_CUSTODY_EVIDENCE')
        trust = {}
        for name, root in anchors.items():
            if not isinstance(name, str) or not isinstance(root, dict) or set(root) != {'public_key', 'trust_root', 'role'}:
                return verdict('INVALID_TRUST_CONFIGURATION', errors=['anchor_shape'])
            if root['role'] not in ALLOWED_ROLES or not isinstance(root['trust_root'], str) or not root['trust_root']:
                return verdict('INVALID_TRUST_CONFIGURATION', errors=['role_or_root'])
            try:
                key = base64.b64decode(root['public_key'], validate=True)
                if len(key) != 32:
                    raise ValueError()
            except (ValueError, TypeError):
                return verdict('INVALID_TRUST_CONFIGURATION', errors=['public_key'])
            trust[name] = root
        if len({r['public_key'] for r in trust.values()}) != len(trust):
            return verdict('SHARED_SIGNING_KEY', errors=['duplicate_anchor_public_key'])
        previous = '0' * 64
        previous_time = None
        active_key = None
        compromised = set()
        revoked = set()
        custody = 'UNKNOWN'
        authenticated = 0
        attestations = []
        seen_ids = set()
        for ix, record in enumerate(events):
            if not isinstance(record, dict) or set(record) != {'body','signer','signature'}:
                return verdict('INVALID_EVENT', len(events), [f'event_{ix}:envelope'], authenticated, custody, active_key)
            body, signer, signature = record['body'], record['signer'], record['signature']
            if not isinstance(body, dict) or set(body) != {'id','subject','event','key_fingerprint','replacement_fingerprint','time','challenge','prev'}:
                return verdict('INVALID_EVENT', len(events), [f'event_{ix}:body'], authenticated, custody, active_key)
            if not isinstance(signer, str) or signer not in trust:
                return verdict('UNKNOWN_SIGNER', len(events), [f'event_{ix}:signer'], authenticated, custody, active_key)
            if not verify(trust[signer]['public_key'], body, signature):
                return verdict('INVALID_SIGNATURE', len(events), [f'event_{ix}:signature'], authenticated, custody, active_key)
            authenticated += 1
            if body['subject'] != subject or body['challenge'] != challenge:
                return verdict('CHALLENGE_OR_SUBJECT_MISMATCH', len(events), [f'event_{ix}:binding'], authenticated, custody, active_key)
            if not isinstance(body['id'], str) or not body['id'] or body['id'] in seen_ids:
                return verdict('REPLAYED_EVENT', len(events), [f'event_{ix}:id'], authenticated, custody, active_key)
            seen_ids.add(body['id'])
            if body['prev'] != previous:
                return verdict('BROKEN_EVENT_CHAIN', len(events), [f'event_{ix}:previous'], authenticated, custody, active_key)
            previous = digest(record)
            kind = body['event']
            if kind not in VALID_EVENTS:
                return verdict('UNKNOWN_EVENT_TYPE', len(events), [f'event_{ix}:event'], authenticated, custody, active_key)
            try:
                when = parse_time(body['time'])
            except (ValueError, TypeError):
                return verdict('INVALID_EVENT_TIME', len(events), [f'event_{ix}:time'], authenticated, custody, active_key)
            if previous_time is not None and when <= previous_time:
                return verdict('NONMONOTONIC_EVENT_TIME', len(events), [f'event_{ix}:ordering'], authenticated, custody, active_key)
            if when > clock or (clock - when).total_seconds() > 86400:
                return verdict('STALE_OR_FUTURE_EVENT', len(events), [f'event_{ix}:window'], authenticated, custody, active_key)
            previous_time = when
            key = body['key_fingerprint']
            replacement = body['replacement_fingerprint']
            if not isinstance(key, str) or not HEX64.fullmatch(key) or (replacement is not None and (not isinstance(replacement,str) or not HEX64.fullmatch(replacement))):
                return verdict('INVALID_KEY_FINGERPRINT', len(events), [f'event_{ix}:key'], authenticated, custody, active_key)
            role = trust[signer]['role']
            allowed = {'ENROLLED': {'registrar'}, 'CUSTODY_ATTESTED': {'custody_auditor'}, 'EXPOSURE_SUSPECTED': {'security_operator','custody_auditor'}, 'EXPOSURE_CONFIRMED': {'security_operator','custody_auditor'}, 'REVOKED': {'registrar'}, 'ROTATED': {'registrar'}}
            if role not in allowed[kind]:
                return verdict('UNAUTHORIZED_EVENT_SIGNER', len(events), [f'event_{ix}:role'], authenticated, custody, active_key)
            if kind == 'ENROLLED':
                if active_key is not None or replacement is not None:
                    return verdict('INVALID_TRANSITION', len(events), [f'event_{ix}:enroll'], authenticated, custody, active_key)
                active_key = key
                custody = 'DECLARED_ENROLLED'
            else:
                if key != active_key:
                    return verdict('KEY_LINEAGE_MISMATCH', len(events), [f'event_{ix}:key'], authenticated, custody, active_key)
                if kind == 'CUSTODY_ATTESTED':
                    if replacement is not None:
                        return verdict('INVALID_TRANSITION', len(events), [f'event_{ix}:replacement'], authenticated, custody, active_key)
                    attestations.append((signer,trust[signer]['trust_root']))
                    if key not in compromised and key not in revoked:
                        custody = 'SIGNED_CUSTODY_CLAIM_ONLY'
                elif kind in {'EXPOSURE_SUSPECTED','EXPOSURE_CONFIRMED'}:
                    if replacement is not None:
                        return verdict('INVALID_TRANSITION', len(events), [f'event_{ix}:replacement'], authenticated, custody, active_key)
                    compromised.add(key)
                    custody = 'EXPOSURE_REPORTED'
                elif kind == 'REVOKED':
                    if replacement is not None:
                        return verdict('INVALID_TRANSITION', len(events), [f'event_{ix}:replacement'], authenticated, custody, active_key)
                    revoked.add(key)
                    custody = 'REVOKED'
                elif kind == 'ROTATED':
                    if not replacement or replacement == key or replacement in compromised or replacement in revoked:
                        return verdict('INVALID_ROTATION', len(events), [f'event_{ix}:replacement'], authenticated, custody, active_key)
                    revoked.add(key)
                    active_key = replacement
                    custody = 'ROTATED_UNATTESTED'
                    attestations = []
        if active_key in compromised:
            return verdict('KEY_EXPOSURE_REPORTED', len(events), authenticated=authenticated, custody=custody, key=active_key)
        if active_key in revoked:
            return verdict('KEY_REVOKED', len(events), authenticated=authenticated, custody=custody, key=active_key)
        if len({root for _,root in attestations}) < 2:
            return verdict('INSUFFICIENT_DISTINCT_ATTESTOR_ROOTS', len(events), authenticated=authenticated, custody=custody, key=active_key)
        return verdict('SIGNED_CUSTODY_CLAIMS_CONSISTENT_NOT_PROVEN', len(events), authenticated=authenticated, custody=custody, key=active_key)
    except (KeyError,TypeError,ValueError) as exc:
        return verdict('INVALID_BUNDLE', errors=[type(exc).__name__])


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--bundle',required=True)
    p.add_argument('--now',required=True)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    path=Path(args.bundle)
    if path.stat().st_size > 1024*1024: raise SystemExit('bundle too large')
    result=audit(json.loads(path.read_text()),args.now)
    Path(args.output).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['verdict'])

if __name__=='__main__': main()
