"""JANE 233: offline key-rotation inherited-compromise ancestry audit.

This checks declared history only; does not establish a clean physical environment.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 'jane233.inheritance/1'
ROOT_TYPES = ('machine', 'administrator', 'credential', 'signer_service', 'runner', 'source', 'build_pipeline')
EVENT_TYPES = ('ENROLLED', 'EXPOSURE', 'REVOKED', 'ROTATED', 'REMEDIATED')

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()

def time_parse(s):
    if not isinstance(s,str): raise ValueError('invalid_time')
    t=datetime.fromisoformat(s.replace('Z','+00:00'))
    if t.tzinfo is None: raise ValueError('timezone_required')
    return t.astimezone(timezone.utc)

def verdict(code, *, active=None, inherited=(), errors=(), events=0, note=''):
    return {'schema':SCHEMA,'verdict':code,'active_key':active,
            'inherited_compromise_roots':sorted(inherited),'errors':list(errors),
            'events_checked':events,'exclusive_key_custody_proven':False,
            'clean_environment_proven':False,'authenticated_live_witnesses':0,
            'jane_collective_choice':'UNRESOLVED','actions_executed':0,
            'note':note or 'No claim about physical host integrity or exclusive control'}

def audit(bundle, now, max_events=128):
    """Events are observations supplied to this verifier; the bundle cannot attest itself.

    A successful *structural* history check is never an independent attestation.
    A compromised root propagates across rotations until separately evidenced remediation.
    A remediation claim cannot independently clear an exposure without a separately
    identified out-of-band witness and non-overlapping custody roots.
    """
    try:
        current=time_parse(now)
        if not isinstance(bundle,dict) or set(bundle)!={'subject','challenge','events'}:
            return verdict('INVALID_BUNDLE', errors=['shape'])
        if not isinstance(bundle['subject'],str) or not bundle['subject'].strip() or len(bundle['subject'])>120:
            return verdict('INVALID_BUNDLE',errors=['subject'])
        challenge=bundle['challenge']
        if not isinstance(challenge,str) or len(challenge)!=64 or any(c not in '0123456789abcdef' for c in challenge):
            return verdict('INVALID_BUNDLE',errors=['challenge'])
        events=bundle['events']
        if not isinstance(events,list) or len(events)>max_events:
            return verdict('INVALID_BUNDLE',errors=['events'])
        if not events: return verdict('NO_RUNTIME_CUSTODY_EVIDENCE')
        active=None; roots_by_key={}; exposed=set(); retired=set(); previous='0'*64
        seen=set(); prev_time=None; count=0
        for i,e in enumerate(events):
            count+=1
            if not isinstance(e,dict) or set(e)!={'id','kind','key','replacement','roots','time','challenge','prev','witness'}:
                return verdict('INVALID_EVENT',errors=[f'{i}:shape'],events=count)
            if any(not isinstance(e[f],str) for f in ('id','kind','key','time','challenge','prev','witness')):
                return verdict('INVALID_EVENT',errors=[f'{i}:fields'],events=count)
            if e['id'] in seen or not e['id']:
                return verdict('REPLAYED_EVENT',errors=[f'{i}:id'],events=count)
            seen.add(e['id'])
            if e['kind'] not in EVENT_TYPES: return verdict('INVALID_EVENT',errors=[f'{i}:kind'],events=count)
            if e['challenge']!=challenge or e['prev']!=previous:
                return verdict('BROKEN_PROVENANCE_CHAIN',errors=[f'{i}:binding'],events=count)
            try: stamp=time_parse(e['time'])
            except (ValueError,TypeError):return verdict('INVALID_EVENT',errors=[f'{i}:time'],events=count)
            if stamp>current or (prev_time is not None and stamp<=prev_time):
                return verdict('INVALID_EVENT_TIME',errors=[f'{i}:chronology'],events=count)
            prev_time=stamp
            roots=e['roots']
            if not isinstance(roots,dict) or set(roots)!=set(ROOT_TYPES) or any(not isinstance(v,str) or not v.strip() or len(v)>160 for v in roots.values()):
                return verdict('INVALID_ROOTS',errors=[f'{i}:roots'],events=count)
            ekey=e['key']; rep=e['replacement']
            if len(ekey)!=64 or any(c not in '0123456789abcdef' for c in ekey):
                return verdict('INVALID_KEY',errors=[f'{i}:key'],events=count)
            if e['kind']=='ENROLLED':
                if active is not None or rep is not None or ekey in roots_by_key:
                    return verdict('INVALID_LIFECYCLE',errors=[f'{i}:enroll'],events=count)
                active=ekey; roots_by_key[active]=roots.copy()
            elif e['kind']=='EXPOSURE':
                if ekey not in roots_by_key or rep is not None:
                    return verdict('INVALID_LIFECYCLE',errors=[f'{i}:exposure'],events=count)
                if roots!=roots_by_key[ekey]:
                    return verdict('ROOT_HISTORY_MUTATED',errors=[f'{i}:roots'],events=count)
                exposed.update(roots.values())
            elif e['kind']=='ROTATED':
                if ekey!=active or not isinstance(rep,str) or len(rep)!=64 or any(c not in '0123456789abcdef' for c in rep) or rep in roots_by_key or rep==ekey:
                    return verdict('INVALID_LIFECYCLE',errors=[f'{i}:rotate'],events=count)
                retired.add(active); active=rep;roots_by_key[rep]=roots.copy()
            elif e['kind']=='REVOKED':
                if ekey!=active or rep is not None or roots!=roots_by_key[ekey]:
                    return verdict('INVALID_LIFECYCLE',errors=[f'{i}:revoke'],events=count)
                retired.add(active); active=None
            else: # REMEDIATED: never self-clears exposed roots
                if ekey not in roots_by_key or rep is not None or roots!=roots_by_key[ekey]:
                    return verdict('INVALID_LIFECYCLE',errors=[f'{i}:remediate'],events=count)
                # External evidence would need independent witness authentication;
                # this offline audit does not treat a witness label as that proof.
            previous=digest(e)
        if active is None: return verdict('NO_ACTIVE_KEY',events=count)
        overlap=set(roots_by_key[active].values()) & exposed
        if overlap:
            return verdict('INHERITED_COMPROMISE',active=active,inherited=overlap,events=count,
                           note='New key shares roots previously reported exposed; remediation claims cannot self-clear')
        return verdict('NO_KNOWN_OVERLAP_UNVERIFIED',active=active,events=count,
                       note='No declared exposed root overlaps; independence and runtime integrity unverified')
    except (TypeError,ValueError,KeyError,OverflowError) as exc:
        return verdict('INVALID_BUNDLE',errors=[type(exc).__name__])

def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--now',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();result=audit(json.loads(Path(a.bundle).read_text()),a.now)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(result['verdict'])

if __name__=='__main__':main()
