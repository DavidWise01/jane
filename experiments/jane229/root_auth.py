"""JANE 229: pin-anchored signers and conservative independent-root classification.

Cryptographic identities here are test-fixture keys. Trust-root names alone are not evidence
of different control domains, and even verified signatures cannot prove physical separation.
"""
import argparse, base64, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

SHA=re.compile(r'^[0-9a-f]{64}$')
ID=re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$')
SCHEMA='jane229.root-auth/1'
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',', ':'),ensure_ascii=False).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def outcome(code, accepted=(), clusters=(), reasons=()):
    o={'schema':SCHEMA,'verdict':code,'authenticated_signers':list(accepted),
       'declared_dependency_clusters':list(clusters),'reasons':list(reasons),
       'independent_physical_roots_proven':False,'collective_decision':'UNRESOLVED',
       'action_executed':False}
    o['receipt_sha256']=digest(o);return o

def valid_time(value):
    if not isinstance(value,str) or not value.endswith('Z'):raise ValueError('timestamp must use UTC Z')
    v=datetime.fromisoformat(value.replace('Z','+00:00'))
    if v.utcoffset().total_seconds()!=0:raise ValueError('not UTC')
    return v

def verify(bundle, expected_challenge, expected_claim, now, max_age_seconds=300):
    if not isinstance(bundle,dict) or set(bundle)!={'pins','statements'}:return outcome('INVALID_BUNDLE')
    pins=bundle['pins']; rows=bundle['statements']
    if not isinstance(pins,list) or not isinstance(rows,list) or len(pins)>20 or len(rows)>20:
        return outcome('INVALID_BUNDLE_SIZE')
    if not (isinstance(expected_claim,str) and SHA.fullmatch(expected_claim) and isinstance(expected_challenge,str) and len(expected_challenge)>=16):
        return outcome('INVALID_EXPECTATION')
    try:t=valid_time(now)
    except (TypeError,ValueError):return outcome('INVALID_CLOCK')
    lookup={}
    for p in pins:
        if not isinstance(p,dict) or set(p)!={'id','public_key','controller','platform','source_ancestry','status'}:
            return outcome('INVALID_PIN')
        if not all(isinstance(p[k],str) and ID.fullmatch(p[k]) for k in ('id','controller','platform','source_ancestry')):
            return outcome('INVALID_PIN')
        if p['id'] in lookup:return outcome('DUPLICATE_PIN')
        if p['status'] not in ('active','revoked'):return outcome('INVALID_PIN')
        try:
            raw=base64.b64decode(p['public_key'],validate=True)
            if len(raw)!=32:raise ValueError('wrong key size')
            Ed25519PublicKey.from_public_bytes(raw)
        except (ValueError,TypeError):return outcome('INVALID_PUBLIC_KEY')
        lookup[p['id']]=p
    if not rows:return outcome('NO_SIGNED_RESPONSES')
    seen=set();ok=[]
    for i,entry in enumerate(rows):
        if not isinstance(entry,dict) or set(entry)!={'body','signature'}:return outcome('MALFORMED_RESPONSE',reasons=[i])
        b=entry['body'];sig=entry['signature']
        if not isinstance(b,dict) or set(b)!={'signer','challenge','claim_sha256','observed_at','choice'}:
            return outcome('MALFORMED_RESPONSE',reasons=[i])
        sid=b['signer']
        if not isinstance(sid,str) or sid not in lookup:return outcome('UNPINNED_SIGNER',reasons=[i])
        if sid in seen:return outcome('DUPLICATED_SIGNER',reasons=[sid])
        seen.add(sid)
        if lookup[sid]['status']!='active':return outcome('REVOKED_SIGNER',reasons=[sid])
        try:
            pk=Ed25519PublicKey.from_public_bytes(base64.b64decode(lookup[sid]['public_key'],validate=True))
            pk.verify(base64.b64decode(sig,validate=True),canonical(b))
        except (ValueError,TypeError,Exception) as exc:
            return outcome('INVALID_SIGNATURE',reasons=[sid])
        if b['challenge']!=expected_challenge:return outcome('WRONG_CHALLENGE',reasons=[sid])
        if b['claim_sha256']!=expected_claim:return outcome('WRONG_CLAIM',reasons=[sid])
        if b['choice'] not in ('observe','abstain'):return outcome('INVALID_CHOICE',reasons=[sid])
        try:dt=valid_time(b['observed_at'])
        except (TypeError,ValueError):return outcome('INVALID_OBSERVATION_TIME',reasons=[sid])
        age=(t-dt).total_seconds()
        if age<0 or age>max_age_seconds:return outcome('STALE_OR_FUTURE_RESPONSE',reasons=[sid])
        ok.append(sid)
    # Even separate signer keys may be controlled by the same party or cloud account.
    groups=[]
    for field in ('public_key','controller','platform','source_ancestry'):
        rev={}
        for sid in ok:rev.setdefault(lookup[sid][field],[]).append(sid)
        for value,members in rev.items():
            if len(members)>1:groups.append({'field':field,'value':value,'signers':sorted(members)})
    if groups:return outcome('SHARED_AUTHENTICATION_ANCESTRY',ok,groups)
    if len(ok)<3:return outcome('INSUFFICIENT_AUTHENTICATED_SIGNERS',ok,reasons=['requires 3 distinct registered signers'])
    return outcome('DISTINCT_PINNED_SIGNERS_FIXTURE',ok,reasons=[
        'Independent physical or operational control was NOT established.',
        'Pinned keys and declared roots have not been independently audited.'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--challenge',required=True)
    p.add_argument('--claim',required=True);p.add_argument('--now',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();result=verify(json.loads(Path(a.bundle).read_text()),a.challenge,a.claim,a.now)
    Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(result['verdict'])
if __name__=='__main__':main()
