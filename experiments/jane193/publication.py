"""JANE 193 — Beacon publication and withholding observations (fixture model).

All keys, clocks, observers, and roots here are synthetic fixtures. Signatures
validate claims; they do not prove publication, availability or operator intent.
"""
import hashlib, json, sqlite3
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

DOMAIN = 'JANE193_PUBLICATION_V1'
def encode(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
def hashof(x): return hashlib.sha256(encode(x)).hexdigest()
def signed(key, data): return {'data': data, 'sig': key.sign(encode(data)).hex()}
def verify(pub, receipt):
    try: pub.verify(bytes.fromhex(receipt['sig']), encode(receipt['data'])); return True
    except (InvalidSignature, ValueError, KeyError, TypeError): return False

@dataclass(frozen=True)
class Trust:
    keys: dict
    admins: dict
    roots: dict
    def distinct(self, actors):
        return len({self.roots.get(a) for a in actors}) == len(actors) and len({self.admins.get(a) for a in actors}) == len(actors)

class Audit:
    def __init__(self, path=':memory:'):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS used (actor TEXT, nonce TEXT, PRIMARY KEY(actor,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, prev TEXT, head TEXT, payload TEXT)')
        self.db.commit()
    def close(self): self.db.close()
    def append(self, item):
        old=self.db.execute('SELECT head FROM events ORDER BY id DESC LIMIT 1').fetchone()
        prev=old[0] if old else '0'*64
        h=hashof({'prev':prev,'item':item})
        self.db.execute('INSERT INTO events(prev,head,payload) VALUES(?,?,?)',(prev,h,encode(item).decode()))
        self.db.commit()
        return h
    def has(self,actor,nonce):
        return bool(self.db.execute('SELECT 1 FROM used WHERE actor=? AND nonce=?',(actor,nonce)).fetchone())
    def mark(self, pairs):
        self.db.executemany('INSERT INTO used(actor,nonce) VALUES(?,?)',pairs)
        self.db.commit()
    def check(self, expected_head=None):
        prev='0'*64
        for p,h,raw in self.db.execute('SELECT prev,head,payload FROM events ORDER BY id'):
            if p!=prev or hashof({'prev':p,'item':json.loads(raw)})!=h: return 'TAMPERED'
            prev=h
        if expected_head is not None and prev!=expected_head:return 'EXTERNAL_HEAD_MISMATCH'
        return 'VALID_LOCAL_CHAIN'
    def head(self):
        r=self.db.execute('SELECT head FROM events ORDER BY id DESC LIMIT 1').fetchone()
        return r[0] if r else '0'*64

class FLAY:
    def __init__(self, trust, db=':memory:', quorum=2, max_attempts=32):
        self.trust=trust;self.audit=Audit(db);self.quorum=quorum;self.max_attempts=max_attempts
    def close(self):self.audit.close()
    def check(self, task, attempts, observations, beacon=None, now=200, clock_slack=5):
        def finish(status,**details):
            res={'experiment':'JANE-193','status':status,'task_hash':hashof(task),'round':task.get('round'),
                 'deadline':task.get('deadline'),'now':now,'evidence':details,
                 'active':'FROZEN_PARENT','learning_applied':False,'independent_operators_verified':False}
            self.audit.append(res);return res
        if task.get('domain')!=DOMAIN or not isinstance(task.get('round'),int) or task['round']<0 or not isinstance(task.get('deadline'),int):
            return finish('INVALID_FROZEN_TASK')
        if len(attempts)>self.max_attempts or len(observations)>self.max_attempts:return finish('EVIDENCE_BUDGET_EXCEEDED')
        seen=[]; actors=[]; positive=[];negative=[]
        for rec in observations:
            d=rec.get('data',{}); actor=d.get('actor'); pub=self.trust.keys.get(actor)
            if pub is None or not verify(pub,rec):return finish('BAD_OBSERVER_SIGNATURE')
            if d.get('domain')!=DOMAIN or d.get('task_hash')!=hashof(task) or d.get('round')!=task['round']:
                return finish('OBSERVATION_CONTEXT_MISMATCH')
            if d.get('kind') not in ('PUBLISHED','NOT_OBSERVED') or type(d.get('time')) is not int or d['time']>now+clock_slack:
                return finish('INVALID_OBSERVATION')
            if type(d.get('nonce')) is not str or len(d['nonce'])<8:return finish('INVALID_NONCE')
            pair=(actor,d['nonce'])
            if pair in seen or self.audit.has(*pair):return finish('REPLAY')
            seen.append(pair);actors.append(actor)
            (positive if d['kind']=='PUBLISHED' else negative).append(d)
        for a in attempts:
            if a.get('task_hash')!=hashof(task) or a.get('round')!=task['round'] or a.get('result') not in ('SUCCESS','TIMEOUT','ERROR') or type(a.get('time')) is not int:
                return finish('INVALID_FETCH_ATTEMPT')
            if a['time']>now+clock_slack:return finish('INVALID_FETCH_ATTEMPT')
        if beacon is not None:
            d=beacon.get('data',{});actor=d.get('actor');pub=self.trust.keys.get(actor)
            if pub is None or not verify(pub,beacon):return finish('BAD_BEACON_SIGNATURE')
            if d.get('domain')!=DOMAIN or d.get('task_hash')!=hashof(task) or d.get('round')!=task['round'] or d.get('kind')!='BEACON_OUTPUT':
                return finish('BEACON_CONTEXT_MISMATCH')
            if type(d.get('time')) is not int or d['time']<task['deadline']-100 or d['time']>now+clock_slack:return finish('INVALID_BEACON_TIME')
            if not isinstance(d.get('output'),str) or len(d['output'])<16:return finish('INVALID_BEACON_OUTPUT')
        if len(set(actors))!=len(actors):return finish('DUPLICATE_OBSERVER')
        if actors and not self.trust.distinct(actors):return finish('SHARED_DECLARED_ANCESTRY')
        if positive and negative:return finish('AVAILABILITY_CONFLICT',published=len(positive),not_observed=len(negative))
        if beacon is not None and positive:
            if len(positive)<self.quorum:return finish('INSUFFICIENT_PUBLICATION_CUSTODY',observations=len(positive))
            if not all(d.get('output_hash')==hashof(beacon['data']['output']) for d in positive):return finish('BEACON_OUTPUT_CONFLICT')
            status='PUBLISHED_FIXTURE_OBSERVED'
        elif positive and beacon is None:
            status='PUBLICATION_REPORTED_CONTENT_UNAVAILABLE'
        elif now+clock_slack<task['deadline']:
            status='BEFORE_PUBLICATION_DEADLINE'
        elif negative and len(negative)>=self.quorum:
            status='NOT_OBSERVED_BY_FIXTURE_QUORUM'
        elif attempts and all(a['result']!='SUCCESS' for a in attempts):
            status='NETWORK_UNAVAILABLE_OR_WITHHELD'
        else:status='INSUFFICIENT_AVAILABILITY_EVIDENCE'
        if seen:self.audit.mark(seen)
        return finish(status,published=len(positive),not_observed=len(negative),attempts=len(attempts),beacon_present=beacon is not None,
                      intent_established=False,global_completeness_established=False)

def fixture():
    private={k:Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('jane193/'+k).encode()).digest()) for k in ('beacon','a','b','c')}
    tr=Trust({k:p.public_key() for k,p in private.items()},
             {k:'admin_'+k for k in private}, {k:'root_'+k for k in private})
    task={'domain':DOMAIN,'task_id':'frozen:sha256:alpha','round':42,'deadline':150}
    def obs(k,kind,nonce,time=175,output='round42-public-randomness-128'):
        return signed(private[k],{'domain':DOMAIN,'actor':k,'task_hash':hashof(task),'round':42,'time':time,'kind':kind,
                                  'nonce':nonce,'output_hash':hashof(output) if kind=='PUBLISHED' else None})
    beacon=signed(private['beacon'],{'domain':DOMAIN,'actor':'beacon','task_hash':hashof(task),'round':42,'time':160,'kind':'BEACON_OUTPUT','output':'round42-public-randomness-128'})
    def attempt(result='TIMEOUT',time=181):return {'task_hash':hashof(task),'round':42,'time':time,'result':result}
    return private,tr,task,obs,beacon,attempt

def demo():
    private,tr,task,obs,beacon,attempt=fixture()
    flay=FLAY(tr)
    cases={
      'published':flay.check(task,[attempt('SUCCESS')],[obs('a','PUBLISHED','publication-a'),obs('b','PUBLISHED','publication-b')],beacon),
      'missing':flay.check(task,[attempt()],[obs('a','NOT_OBSERVED','missing-a-1'),obs('b','NOT_OBSERVED','missing-b-1')]),
      'outage':flay.check(task,[attempt()],[]),
      'conflict':flay.check(task,[attempt()],[obs('a','PUBLISHED','conflict-a-1'),obs('b','NOT_OBSERVED','conflict-b-1')])}
    r={'experiment':'JANE-193','scenario_statuses':{k:v['status'] for k,v in cases.items()},'tests':'executed separately',
       'audit':flay.audit.check(),'last_head':flay.audit.head(),'scope':'synthetic signed availability claims; absence does not prove deliberate withholding'}
    flay.close();return r
if __name__=='__main__':print(json.dumps(demo(),indent=2,sort_keys=True))