"""JANE 148: allowlisted proof fetch, signed verification, immutable local snapshots.
Local HTTP fixtures only in tests. This does not establish external operator independence.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import ipaddress, json, re, sqlite3, urllib.request, urllib.error
from urllib.parse import urlsplit
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

CHRONOS = re.compile(r'^\{\{ (\d{4})\.(\d{2})\.(\d{2}) \}\}\{\{ (\d{2})\.(\d{2})\.(\d{2}) \}\}\{\{ ([+-]?\d{1,3})\.(\d{2})\.(\d{2}) \}\}$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()

def digest(data):
    return sha256(data).hexdigest()

def clock_value(coord, utc_offset):
    matched = CHRONOS.fullmatch(coord)
    if not matched or not isinstance(utc_offset, int) or not -840 <= utc_offset <= 840:
        raise ValueError('Chronos syntax/offset')
    vals = list(map(int, matched.groups()))
    degree, amin, asec = vals[6:]
    if abs(degree) > 360 or amin >= 60 or asec >= 60 or (abs(degree) == 360 and (amin or asec)):
        raise ValueError('angle')
    return datetime(*vals[:6], tzinfo=timezone(timedelta(minutes=utc_offset))).astimezone(timezone.utc)

@dataclass(frozen=True)
class Endpoint:
    name: str
    url: str
    custody: str
    administrator: str
    public_key: bytes

@dataclass(frozen=True)
class Response:
    status: int
    final_url: str
    content_type: str
    body: bytes

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('redirect prohibited')

def network_fetch(url, timeout, max_bytes):
    """Production transport boundary. Only call with preconfigured exact-match URLs."""
    req = urllib.request.Request(url, headers={'Accept':'application/json', 'User-Agent':'JANE148-FLAY/1.0'})
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(req, timeout=timeout) as r:
        return Response(r.status, r.geturl(), r.headers.get('Content-Type',''), r.read(max_bytes + 1))

class FLAY148:
    def __init__(self, path, endpoints, now, *, max_bytes=16384, timeout=4, max_age=300):
        endpoints = tuple(endpoints)
        if not 1 <= len(endpoints) <= 16 or len({e.name for e in endpoints}) != len(endpoints):
            raise ValueError('endpoint count/name')
        if not 256 <= max_bytes <= 1048576 or not 0 < timeout <= 10 or not 1 <= max_age <= 3600:
            raise ValueError('limits')
        for e in endpoints:
            parts = urlsplit(e.url)
            if (not e.name or not e.custody or not e.administrator or len(e.public_key) != 32 or
                parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or
                parts.fragment or parts.port not in (None, 443) or parts.hostname in ('localhost',) or
                parts.hostname.endswith('.local') or (parts.path and not parts.path.startswith('/'))):
                raise ValueError('endpoint config')
            try:
                ipaddress.ip_address(parts.hostname)
                raise ValueError('IP literal denied')
            except ValueError as ex:
                if str(ex) == 'IP literal denied':
                    raise
        self.endpoints = {e.name:e for e in endpoints}
        self.now = now.astimezone(timezone.utc)
        self.max_bytes = max_bytes
        self.timeout = timeout
        self.max_age = max_age
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS snapshots (seq INTEGER PRIMARY KEY, endpoint TEXT, outcome TEXT, rawhash TEXT, raw BLOB, previous TEXT, head TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS nonces (custody TEXT, nonce TEXT, PRIMARY KEY(custody,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS accepted (custody TEXT, administrator TEXT, chain TEXT, sequence INT, head TEXT, nonce TEXT, PRIMARY KEY(custody,nonce))')
        self.db.commit()

    def _append(self, endpoint, outcome, raw):
        row = self.db.execute('SELECT seq,head FROM snapshots ORDER BY seq DESC LIMIT 1').fetchone()
        seq, prev = (row[0] + 1, row[1]) if row else (0, '0'*64)
        rawhash = digest(raw)
        body = {'seq':seq,'endpoint':endpoint,'outcome':outcome,'rawhash':rawhash,'previous':prev}
        head = digest(canonical(body))
        self.db.execute('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?)',(seq,endpoint,outcome,rawhash,raw,prev,head))

    def fetch(self, name, transport=network_fetch):
        if name not in self.endpoints:
            raise ValueError('endpoint not allowlisted')
        e = self.endpoints[name]
        raw = b''
        try:
            response = transport(e.url, self.timeout, self.max_bytes)
            if not isinstance(response, Response):
                raise ValueError('transport schema')
            raw = response.body
            if not isinstance(raw, bytes) or len(raw) > self.max_bytes:
                raise ValueError('response oversized')
            if response.status != 200 or response.final_url != e.url:
                raise ValueError('HTTP status/redirect')
            if response.content_type.split(';')[0].lower().strip() != 'application/json':
                raise ValueError('content-type')
            doc = json.loads(raw)
            if not isinstance(doc, dict) or set(doc) != {'claim','signature'} or not isinstance(doc['claim'], dict):
                raise ValueError('JSON structure')
            claim = doc['claim']
            expected = {'version','key_name','custody','administrator','chain','sequence','head','nonce','chronos','offset'}
            if set(claim) != expected or claim['version'] != 'JANE-148' or claim['key_name'] != name or claim['custody'] != e.custody or claim['administrator'] != e.administrator:
                raise ValueError('claim binding')
            if not isinstance(doc['signature'], str) or len(doc['signature']) != 128 or not re.fullmatch('[0-9a-f]{128}',doc['signature']):
                raise ValueError('signature encoding')
            try:
                Ed25519PublicKey.from_public_bytes(e.public_key).verify(bytes.fromhex(doc['signature']), canonical(claim))
            except (ValueError, InvalidSignature, TypeError) as ex:
                raise ValueError('bad signature') from ex
            if (type(claim['sequence']) is not int or claim['sequence'] < 0 or not isinstance(claim['chain'], str) or not claim['chain'] or
                not isinstance(claim['nonce'], str) or len(claim['nonce']) < 12 or not isinstance(claim['head'], str) or not HEX64.fullmatch(claim['head'])):
                raise ValueError('claim fields')
            if abs((self.now - clock_value(claim['chronos'],claim['offset'])).total_seconds()) > self.max_age:
                raise ValueError('stale Chronos')
            with self.db:
                self.db.execute('INSERT INTO nonces VALUES(?,?)',(e.custody,claim['nonce']))
                self.db.execute('INSERT INTO accepted VALUES(?,?,?,?,?,?)',(e.custody,e.administrator,claim['chain'],claim['sequence'],claim['head'],claim['nonce']))
                self._append(name,'ACCEPTED',raw)
            return 'ACCEPTED'
        except sqlite3.IntegrityError:
            with self.db:
                self._append(name,'REPLAY',raw)
            return 'REPLAY'
        except (ValueError,TypeError,KeyError,UnicodeError,json.JSONDecodeError,urllib.error.URLError,TimeoutError,OSError) as ex:
            category = 'UNAVAILABLE' if isinstance(ex,(urllib.error.URLError,TimeoutError,OSError)) else 'REJECTED'
            with self.db:
                self._append(name,category,raw if isinstance(raw,bytes) else b'')
            return category

    def compare(self, chain, sequence, local_sequence, local_head, quorum=3):
        if not isinstance(chain,str) or not chain or not 1 <= quorum <= 16 or not isinstance(sequence,int):
            raise ValueError('comparison parameters')
        entries=self.db.execute('SELECT custody,administrator,head FROM accepted WHERE chain=? AND sequence=?',(chain,sequence)).fetchall()
        by_root={}
        for custody,admin,head in entries:
            by_root.setdefault(custody,set()).add((admin,head))
        if any(len(v)>1 for v in by_root.values()):status='EQUIVOCATION'
        else:
            tuples=[next(iter(v)) for v in by_root.values()]
            by_admin={}
            for (root, v) in by_root.items():
                admin, head=next(iter(v));by_admin.setdefault(admin,set()).add(root)
            if any(len(roots)>1 for roots in by_admin.values()):status='SHARED_ADMINISTRATION'
            elif len(by_root)<quorum:status='INSUFFICIENT_CUSTODY'
            elif len({head for _,head in tuples})>1:status='CROSS_ROOT_CONFLICT'
            else:
                anchored=tuples[0][1]
                status=('ROLLBACK_DETECTED' if sequence>local_sequence else
                        'FORK_DETECTED' if sequence==local_sequence and anchored!=local_head else
                        'MATCHED_FIXTURE_QUORUM' if sequence==local_sequence else 'LOCAL_AHEAD')
        return {'status':status,'custody_roots':len(by_root),'active':'frozen_parent','jane_decision':'UNDECIDED','learning_applied':False,
                'caveat':'Configured endpoint identities and administrator claims are fixtures, not verified independent external operators.'}

    def audit(self, expected_head=None):
        prev='0'*64
        for i,(seq,endpoint,outcome,rawhash,raw,previous,head) in enumerate(self.db.execute('SELECT * FROM snapshots ORDER BY seq')):
            if seq!=i or previous!=prev or digest(raw)!=rawhash or digest(canonical({'seq':seq,'endpoint':endpoint,'outcome':outcome,'rawhash':rawhash,'previous':previous}))!=head:
                return 'TAMPERED'
            prev=head
        return 'EXTERNAL_HEAD_MISMATCH' if expected_head is not None and expected_head!=prev else 'VALID_LOCAL_CHAIN'

    def close(self):self.db.close()