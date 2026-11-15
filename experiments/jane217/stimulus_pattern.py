"""JANE 217: signed commit/reveal pattern and sensor response; synthetic evidence only."""
import hashlib
import json
import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(obj):
    return hashlib.sha256(canon(obj)).hexdigest()


def keypair(seed_byte):
    sk = Ed25519PrivateKey.from_private_bytes(bytes([seed_byte]) * 32)
    return sk, sk.public_key()


def signed(sk, body):
    return {'body': body, 'signature': sk.sign(canon(body)).hex()}


def verify(pk, packet):
    try:
        pk.verify(bytes.fromhex(packet['signature']), canon(packet['body']))
        return True
    except (InvalidSignature, ValueError, KeyError, TypeError):
        return False


class GateError(ValueError):
    pass


@dataclass(frozen=True)
class Verdict:
    status: str
    details: dict


class FLAY217:
    def __init__(self, db=':memory:'):
        self.connection = sqlite3.connect(str(db))
        self.connection.execute('CREATE TABLE IF NOT EXISTS used (challenge TEXT PRIMARY KEY, capture TEXT UNIQUE)')
        self.connection.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, previous TEXT, body TEXT, hash TEXT)')
        self.connection.commit()

    def close(self):
        self.connection.close()

    def audit_ok(self):
        previous = '0' * 64
        for seq, prev, body, head in self.connection.execute('SELECT seq,previous,body,hash FROM audit ORDER BY seq'):
            if prev != previous or hashlib.sha256((prev+body).encode()).hexdigest() != head:
                return False
            previous = head
        return True

    def audit(self, status, challenge):
        last = self.connection.execute('SELECT hash FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        prev = last[0] if last else '0' * 64
        body = canon({'status':status,'challenge':challenge}).decode()
        head = hashlib.sha256((prev+body).encode()).hexdigest()
        self.connection.execute('INSERT INTO audit(previous,body,hash) VALUES(?,?,?)',(prev,body,head))

    def evaluate(self, plan, commitment, reveal, response, witnesses, keys):
        if not self.audit_ok():
            return Verdict('CORRUPT_LOG', {})
        for name, value in [('plan',plan),('commitment',commitment),('reveal',reveal),('response',response)]:
            if not verify(keys[name],value):
                return Verdict('SIGNATURE_INVALID', {'record':name})
        if len(witnesses) != 2 or any(not verify(keys['witnesses'][i],w) for i,w in enumerate(witnesses)):
            return Verdict('SIGNATURE_INVALID', {'record':'witness'})
        p,c,r,s = [x['body'] for x in (plan,commitment,reveal,response)]
        try:
            challenge = str(p['challenge'])
            if len(challenge)<8 or any(x['challenge']!=challenge for x in (c,r,s)):
                return Verdict('CHALLENGE_MISMATCH', {})
            times=[int(p['freeze_time']),int(c['commit_time']),int(r['release_time']),int(s['capture_time'])]
            if times!=sorted(times) or len(set(times))!=4 or int(s['capture_time'])>int(p['deadline']):
                return Verdict('INVALID_CHRONOLOGY', {})
            if c['task_hash']!=p['task_hash'] or c['plan_hash']!=digest(p):
                return Verdict('PLAN_COMMITMENT_MISMATCH', {})
            if r['seed'] != r['seed'].lower() or len(bytes.fromhex(r['seed'])) != 32:
                return Verdict('INVALID_SEED', {})
            expected_commit=digest({'domain':'jane217.pattern.commit.v1','seed':r['seed'],'challenge':challenge,'task':p['task_hash']})
            if expected_commit!=c['seed_commitment']:
                return Verdict('SEED_COMMITMENT_MISMATCH', {})
            if r['seed_commitment']!=c['seed_commitment'] or r['commit_hash']!=digest(c):
                return Verdict('REVEAL_COMMITMENT_MISMATCH', {})
            pattern=hashlib.shake_256(b'jane217.pattern.v1'+bytes.fromhex(r['seed'])+canon({'challenge':challenge,'task':p['task_hash']})).digest(16).hex()
            if r['pattern']!=pattern:
                return Verdict('PATTERN_MISMATCH', {})
            if p.get('early_disclosure') is True or c.get('early_disclosure') is True or r.get('early_disclosure') is True:
                return Verdict('PREMATURE_DISCLOSURE_REPORTED', {})
            if s['pattern']!=pattern:
                return Verdict('RESPONSE_PATTERN_MISMATCH', {})
            if int(s['capture_time']) < int(r['release_time']):
                return Verdict('PRECOMPUTED_RESPONSE', {})
            if s['task_hash']!=p['task_hash'] or s['release_hash']!=digest(r):
                return Verdict('RESPONSE_BINDING_MISMATCH', {})
            observations=[w['body'] for w in witnesses]
            if any(w['challenge']!=challenge or w['response_hash']!=digest(s) or w['capture_hash']!=s['capture_hash'] for w in observations):
                return Verdict('WITNESS_RESPONSE_MISMATCH', {})
            if any(int(w['observed_time'])<int(s['capture_time']) or int(w['observed_time'])>int(p['deadline']) for w in observations):
                return Verdict('WITNESS_CHRONOLOGY_INVALID', {})
            if len({w['root'] for w in observations})!=2 or len({w['sensor'] for w in observations})!=2:
                return Verdict('SHARED_OBSERVATION_ROOT', {})
            if p.get('early_disclosure') is True or c.get('early_disclosure') is True or r.get('early_disclosure') is True:
                return Verdict('PREMATURE_DISCLOSURE_REPORTED', {})
            capture=str(s['capture_id'])
            if self.connection.execute('SELECT 1 FROM used WHERE challenge=? OR capture=?',(challenge,capture)).fetchone():
                return Verdict('REPLAY', {})
            with self.connection:
                self.connection.execute('INSERT INTO used VALUES(?,?)',(challenge,capture))
                self.audit('CHALLENGE_RESPONSE_CONSISTENT_FIXTURE',challenge)
            return Verdict('CHALLENGE_RESPONSE_CONSISTENT_FIXTURE', {'pattern':pattern,'capture':capture,'audit_head':self.connection.execute('SELECT hash FROM audit ORDER BY seq DESC LIMIT 1').fetchone()[0]})
        except (ValueError, KeyError, TypeError, OverflowError, AttributeError):
            return Verdict('MALFORMED_EVIDENCE', {})


def fixture(seed=None):
    seed=seed or secrets.token_bytes(32)
    keys={name:keypair(i+1) for i,name in enumerate(('plan','commitment','reveal','response','w0','w1'))}
    private={k:v[0] for k,v in keys.items()}
    public={k:v[1] for k,v in keys.items()}
    challenge='jane217-042-immutable'
    task=digest({'task':'observe unpredictable orange/teal 128-bit pulse'})
    p={'challenge':challenge,'task_hash':task,'freeze_time':100,'deadline':200}
    c={'challenge':challenge,'task_hash':task,'plan_hash':digest(p),'commit_time':110,'seed_commitment':digest({'domain':'jane217.pattern.commit.v1','seed':seed.hex(),'challenge':challenge,'task':task})}
    pattern=hashlib.shake_256(b'jane217.pattern.v1'+seed+canon({'challenge':challenge,'task':task})).digest(16).hex()
    r={'challenge':challenge,'seed':seed.hex(),'seed_commitment':c['seed_commitment'],'commit_hash':digest(c),'release_time':130,'pattern':pattern}
    s={'challenge':challenge,'task_hash':task,'release_hash':digest(r),'capture_time':140,'capture_id':'cap-042','pattern':pattern,'capture_hash':digest({'frame':'synthetic frame matching pulse'})}
    w=[]
    for idx in range(2):
        w.append({'challenge':challenge,'response_hash':digest(s),'capture_hash':s['capture_hash'],'observed_time':150+idx,'root':f'root-{idx}','sensor':f'sensor-{idx}'})
    return (signed(private['plan'],p),signed(private['commitment'],c),signed(private['reveal'],r),signed(private['response'],s),[signed(private[f'w{i}'],v) for i,v in enumerate(w)],{'plan':public['plan'],'commitment':public['commitment'],'reveal':public['reveal'],'response':public['response'],'witnesses':[public['w0'],public['w1']]},private)


def run_demo():
    import tempfile
    report={}
    with tempfile.TemporaryDirectory() as tmp:
        gate=FLAY217(Path(tmp)/'audit.db')
        p,c,r,s,w,keys,_=fixture(bytes.fromhex('a7'*32))
        report['baseline']=gate.evaluate(p,c,r,s,w,keys).__dict__
        report['replay']=gate.evaluate(p,c,r,s,w,keys).__dict__
        gate.close()
        again=FLAY217(Path(tmp)/'audit.db')
        report['replay_after_restart']=again.evaluate(p,c,r,s,w,keys).__dict__
        again.close()
    return {'experiment':'JANE 217','invariant':'Correct Challenge Response != Physical Sensor Causation','scenarios':report,'limitations':['Synthetic signatures and timestamps','No trusted physical sensor or true nondisclosure guarantee']}


if __name__=='__main__':
    print(json.dumps(run_demo(),sort_keys=True,indent=2))