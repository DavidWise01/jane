"""JANE 192: future-beacon proof gate. All keys/times are controlled fixtures.

A valid signature proves key control; signed timestamps do not establish external chronology.
"""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def sha(obj):
    return hashlib.sha256(obj if isinstance(obj, bytes) else canonical(obj)).hexdigest()


def key(name):
    """DETERMINISTIC TEST FIXTURE KEYS. Never deploy these keys."""
    return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('JANE192-FIXTURE-'+name).encode()).digest())


def sign(private, body):
    return {'body': body, 'signature': private.sign(canonical(body)).hex()}


def verify(public, doc):
    try:
        public.verify(bytes.fromhex(doc['signature']), canonical(doc['body']))
        return True
    except (InvalidSignature, ValueError, KeyError, TypeError, AttributeError):
        return False


def is_digest(v):
    return type(v) is str and len(v) == 64 and all(c in '0123456789abcdef' for c in v)


def derive(task_hash, beacon_id, round_number, randomness):
    if not is_digest(task_hash) or not is_digest(randomness) or type(round_number) is not int or round_number < 1:
        raise ValueError('invalid challenge input')
    return sha({'domain':'jane192.challenge.v1','task':task_hash,'beacon':beacon_id,
                'round':round_number,'randomness':randomness})


@dataclass(frozen=True)
class Trust:
    task_key: object
    beacon_keys: dict
    # anchor key -> (public key, declared administration/ancestry)
    anchor_keys: dict
    anchor_quorum: int = 2
    max_age: int = 300
    future_skew: int = 15


class Auditor:
    def __init__(self, database, trust):
        self.trust = trust
        self.db = sqlite3.connect(database)
        self.db.execute('CREATE TABLE IF NOT EXISTS accepted (task TEXT PRIMARY KEY, beacon TEXT, round INTEGER, result TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS seen (beacon TEXT, round INTEGER, commitment TEXT, PRIMARY KEY(beacon,round))')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, prev TEXT, record TEXT, head TEXT)')
        self.db.commit()

    def close(self): self.db.close()

    def _log(self, status, details):
        row = self.db.execute('SELECT seq,head FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        seq = 0 if row is None else row[0] + 1
        prev = '0'*64 if row is None else row[1]
        rec = {'status':status,'details':details}
        head = sha({'seq':seq,'prev':prev,'record':rec})
        self.db.execute('INSERT INTO events VALUES (?,?,?,?)',(seq,prev,canonical(rec).decode(),head))
        self.db.commit()
        return {'status':status,'details':details,'log_head':head,'activation':False,
                'scope':'SIGNED_LOCAL_FIXTURE_ONLY','independence_verified':False}

    def audit_log(self):
        prev='0'*64
        for expected, (seq, predecessor, record, head) in enumerate(self.db.execute('SELECT * FROM events ORDER BY seq')):
            if seq != expected or predecessor != prev or sha({'seq':seq,'prev':prev,'record':json.loads(record)}) != head:
                return False
            prev=head
        return True

    def evaluate(self, freeze, round_receipt, anchors, now):
        """Audit one exactly selected future beacon round. No fallback or latest-round substitution."""
        def finish(status, **kw): return self._log(status, kw)
        if type(now) is not int or now < 0: return finish('BAD_EVALUATION_TIME')
        if not verify(self.trust.task_key, freeze): return finish('BAD_FREEZE_SIGNATURE')
        task=freeze['body']
        if (task.get('type')!='task.freeze' or not is_digest(task.get('task_hash')) or
            type(task.get('tick')) is not int or type(task.get('target_round')) is not int or
            task['target_round'] < 1 or type(task.get('not_before')) is not int or
            task['tick'] >= task['not_before'] or not isinstance(task.get('beacon_id'),str) or
            task['beacon_id'] not in self.trust.beacon_keys):
            return finish('BAD_FREEZE_FORMAT')
        identity=task['beacon_id']; number=task['target_round']
        if round_receipt is None: return finish('ROUND_UNAVAILABLE', beacon=identity,round=number)
        if not verify(self.trust.beacon_keys[identity],round_receipt):return finish('BAD_BEACON_SIGNATURE')
        r=round_receipt['body']
        if (r.get('type')!='beacon.round' or r.get('beacon_id')!=identity or r.get('round')!=number):
            return finish('ROUND_SUBSTITUTED')
        if not is_digest(r.get('randomness')) or type(r.get('tick')) is not int or type(r.get('release_tick')) is not int:
            return finish('BAD_ROUND_FORMAT')
        if r['release_tick'] < task['not_before'] or r['tick'] < r['release_tick']:
            return finish('PREMATURE_BEACON_RELEASE_REPORTED')
        if task['tick'] >= r['release_tick']:return finish('FREEZE_NOT_PRIOR_TO_ROUND')
        if r['tick'] > now+self.trust.future_skew:return finish('BEACON_FROM_FUTURE')
        if now-r['tick'] > self.trust.max_age:return finish('STALE_BEACON')
        # Anchors commit to this *exact* signed beacon record, not an alleged public key or round.
        commitment=sha(round_receipt)
        admins=set()
        for anchor in anchors:
            if not isinstance(anchor,dict) or not isinstance(anchor.get('body'),dict):return finish('BAD_ANCHOR_FORMAT')
            a=anchor['body']; wid=a.get('witness')
            entry=self.trust.anchor_keys.get(wid)
            if entry is None or not verify(entry[0],anchor):return finish('BAD_ANCHOR_SIGNATURE')
            if (a.get('type')!='beacon.anchor' or a.get('beacon_id')!=identity or
                a.get('round')!=number or a.get('beacon_commitment')!=commitment or
                type(a.get('observed_tick')) is not int):
                return finish('ANCHOR_MISMATCH')
            if a['observed_tick'] < r['tick']:return finish('ANCHOR_BEFORE_BEACON_REPORTED')
            if a['observed_tick'] > now+self.trust.future_skew:return finish('ANCHOR_FROM_FUTURE')
            admins.add(entry[1])
        if len(admins) < self.trust.anchor_quorum:return finish('INSUFFICIENT_DECLARED_ANCHORS',distinct=len(admins))
        previous=self.db.execute('SELECT commitment FROM seen WHERE beacon=? AND round=?',(identity,number)).fetchone()
        if previous is not None and previous[0]!=commitment:return finish('SIGNED_BEACON_EQUIVOCATION')
        if self.db.execute('SELECT 1 FROM accepted WHERE task=?',(task['task_hash'],)).fetchone():
            return finish('REPLAY_TASK')
        result=derive(task['task_hash'],identity,number,r['randomness'])
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO seen VALUES(?,?,?)',(identity,number,commitment))
            self.db.execute('INSERT INTO accepted VALUES(?,?,?,?)',(task['task_hash'],identity,number,result))
        return finish('FUTURE_BEACON_FIXTURE_VERIFIED',round=number,challenge=result,
                      declared_anchor_roots=len(admins),beacon_commitment=commitment)


def fixture(mode='valid'):
    now=300
    task_hash=sha('frozen-task-192')
    freeze=sign(key('task'),{'type':'task.freeze','task_hash':task_hash,'beacon_id':'fixture-beacon',
                             'target_round':42,'tick':100,'not_before':200})
    rec=sign(key('beacon'),{'type':'beacon.round','beacon_id':'fixture-beacon','round':42,
                            'release_tick':220,'tick':222,'randomness':sha('round-42')})
    if mode=='substitute':rec=sign(key('beacon'),dict(rec['body'],round=43))
    if mode=='stale':rec=sign(key('beacon'),dict(rec['body'],tick=5,release_tick=5))
    if mode=='leaked':rec=sign(key('beacon'),dict(rec['body'],tick=185,release_tick=185))
    if mode=='conflict':rec=sign(key('beacon'),dict(rec['body'],randomness=sha('alternate')))
    anchors=[sign(key('anchor-'+w),{'type':'beacon.anchor','witness':w,'beacon_id':'fixture-beacon',
                 'round':rec['body']['round'],'beacon_commitment':sha(rec),'observed_tick':225})
             for w in ('a','b','c')]
    if mode=='one-root':anchors=anchors[:1]
    if mode=='unavailable':rec=None;anchors=[]
    trust=Trust(key('task').public_key(),{'fixture-beacon':key('beacon').public_key()},
                {w:(key('anchor-'+w).public_key(),w) for w in ('a','b','c')},2)
    return freeze,rec,anchors,trust,now


def demonstration():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        freeze,rec,anchors,trust,now=fixture()
        audit=Auditor(tmp+'/replay.sqlite3',trust)
        first=audit.evaluate(freeze,rec,anchors,now)
        integrity=audit.audit_log()
        audit.close()
        audit=Auditor(tmp+'/replay.sqlite3',trust)
        replay=audit.evaluate(freeze,rec,anchors,now)
        audit.close()
        return {'experiment':'JANE-192','verified':first['status'],'challenge':first['details']['challenge'],
                'replay_after_restart':replay['status'],'audit_valid':integrity,'tests':'run separately',
                'real_world_independence_verified':False,'automatic_activation':False}

if __name__=='__main__':print(json.dumps(demonstration(),indent=2))