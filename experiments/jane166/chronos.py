"""JANE 166: signed clock uncertainty intervals and partial causal order.

All authorities are local fixtures. Cryptographic authenticity does not establish accurate clocks.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import sqlite3
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def hashof(v):
    return sha256(canonical(v)).hexdigest()


@dataclass(frozen=True)
class ClockClaim:
    root: str
    admin: str
    clock_source: str
    observation: str
    nominal_ms: int
    uncertainty_ms: int
    nonce: str
    key_id: str
    signature: str
    def body(self):
        return {k: getattr(self, k) for k in ('root','admin','clock_source','observation','nominal_ms','uncertainty_ms','nonce','key_id')}
    def interval(self):
        return [self.nominal_ms-self.uncertainty_ms, self.nominal_ms+self.uncertainty_ms]
    def asdict(self):
        return dict(self.body(), signature=self.signature)


def signed_claim(key, root, admin, source, observation, nominal_ms, uncertainty_ms, nonce, key_id):
    data = dict(root=root,admin=admin,clock_source=source,observation=observation,
                nominal_ms=nominal_ms,uncertainty_ms=uncertainty_ms,nonce=nonce,key_id=key_id)
    return ClockClaim(**data, signature=key.sign(canonical(data)).hex())


class Chronos:
    def __init__(self, authorities, database=':memory:', max_uncertainty=10_000, quorum=3):
        """authorities: key_id -> (public_key_bytes, expected_root, expected_admin).

        This declared administrative identity is only a configured fixture label.
        """
        self.authorities = authorities
        self.max_uncertainty=max_uncertainty
        self.quorum=quorum
        self.db=sqlite3.connect(database)
        self.db.execute('CREATE TABLE IF NOT EXISTS receipts (nonce TEXT PRIMARY KEY, digest TEXT NOT NULL, observation TEXT NOT NULL, root TEXT NOT NULL, lo INTEGER NOT NULL, hi INTEGER NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, prior TEXT NOT NULL, event TEXT NOT NULL, head TEXT NOT NULL)')
        self.db.commit()
    def close(self): self.db.close()
    def _audit(self, event):
        prev=self.db.execute('SELECT head FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        prior=prev[0] if prev else '0'*64
        head=hashof(dict(prior=prior,event=event))
        self.db.execute('INSERT INTO audit(prior,event,head) VALUES(?,?,?)',(prior,json.dumps(event,sort_keys=True),head))
    def audit_chain(self, retained_head=None):
        prior='0'*64
        for stored_prior,text,head in self.db.execute('SELECT prior,event,head FROM audit ORDER BY seq'):
            if stored_prior != prior or hashof(dict(prior=prior,event=json.loads(text)))!=head:
                return 'TAMPERED_LOCAL_AUDIT'
            prior=head
        return 'EXTERNAL_HEAD_MISMATCH' if retained_head is not None and retained_head!=prior else 'VALID_LOCAL_AUDIT'
    def audit_head(self):
        row=self.db.execute('SELECT head FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        return row[0] if row else '0'*64
    def ingest(self, claim):
        if not isinstance(claim,ClockClaim): return 'MALFORMED'
        body=claim.body()
        if any(not isinstance(body[k],str) or not body[k] for k in ('root','admin','clock_source','observation','nonce','key_id')):
            return 'MALFORMED'
        if type(claim.nominal_ms) is not int or type(claim.uncertainty_ms) is not int or claim.uncertainty_ms < 0 or claim.uncertainty_ms > self.max_uncertainty:
            return 'BAD_UNCERTAINTY'
        registry=self.authorities.get(claim.key_id)
        if registry is None: return 'UNKNOWN_KEY'
        pub,root,admin=registry
        if (claim.root,claim.admin)!=(root,admin): return 'IDENTITY_MISMATCH'
        try:
            Ed25519PublicKey.from_public_bytes(pub).verify(bytes.fromhex(claim.signature),canonical(body))
        except (InvalidSignature,ValueError,TypeError):return 'BAD_SIGNATURE'
        if self.db.execute('SELECT 1 FROM receipts WHERE nonce=?',(claim.nonce,)).fetchone():return 'REPLAY'
        lo,hi=claim.interval()
        with self.db:
            self.db.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?)',(claim.nonce,hashof(claim.asdict()),claim.observation,claim.root,lo,hi))
            self._audit(dict(action='ACCEPT',digest=hashof(claim.asdict()),root=claim.root,observation=claim.observation,interval=[lo,hi]))
        return 'ACCEPTED'
    def compare(self, claims, observation=None):
        """Verify already-ingested claims as source of truth; no new votes from duplicate root/admin.

        Returns intersection if all admitted custody roots agree, or preserves conflicting
        groups. Disjoint claims are not averaged into invented time.
        """
        if not claims: return dict(status='NO_EVIDENCE',intersection=None,independent_operators_verified=False)
        accepted=[]; seen_roots=set();seen_admins=set();failures=[]
        for c in claims:
            if not isinstance(c,ClockClaim): failures.append('MALFORMED'); continue
            if observation is not None and c.observation!=observation:
                failures.append('OBSERVATION_MISMATCH');continue
            if not self.db.execute('SELECT 1 FROM receipts WHERE nonce=? AND digest=?',(c.nonce,hashof(c.asdict()))).fetchone():
                failures.append('NOT_INGESTED');continue
            if c.root in seen_roots or c.admin in seen_admins:
                failures.append('SHARED_CUSTODY');continue
            seen_roots.add(c.root);seen_admins.add(c.admin);accepted.append(c)
        intervals=[c.interval() for c in accepted]
        if not intervals: return dict(status='NO_ADMISSIBLE_CLAIMS',failures=failures,independent_operators_verified=False)
        lo=max(v[0] for v in intervals);hi=min(v[1] for v in intervals)
        agreed=lo<=hi
        status='CLOCK_CONFLICT' if not agreed else ('MATCHED_FIXTURE_INTERVAL' if len(accepted)>=self.quorum and not failures else 'INSUFFICIENT_OR_DISPUTED_CUSTODY')
        return dict(status=status,intersection=[lo,hi] if agreed else None,
                    interval_claims=[dict(root=c.root,source=c.clock_source,interval=c.interval()) for c in accepted],
                    roots=len(accepted),quorum=self.quorum,failures=failures,
                    independent_operators_verified=False,
                    temporal_scope='configured signed uncertainty intervals; accuracy not independently validated')


def temporal_relation(interval_a,interval_b):
    a,b=interval_a,interval_b
    if a[1]<b[0]:return 'DEFINITELY_BEFORE'
    if b[1]<a[0]:return 'DEFINITELY_AFTER'
    return 'OVERLAP_UNORDERED'


def causal_audit(parent_interval,child_interval,edge_claimed=True):
    relation=temporal_relation(parent_interval,child_interval)
    if not edge_claimed: return dict(status='NO_CAUSAL_EDGE',temporal_relation=relation)
    if relation=='DEFINITELY_AFTER':return dict(status='CLOCK_CAUSAL_CONTRADICTION',temporal_relation=relation)
    return dict(status='TEMPORAL_CONSISTENT' if relation=='DEFINITELY_BEFORE' else 'TEMPORAL_AMBIGUOUS',temporal_relation=relation)


def fixture():
    keys=[Ed25519PrivateKey.from_private_bytes(bytes([i])*32) for i in (11,12,13)]
    auth={f'key{i}':(keys[i].public_key().public_bytes_raw(),f'root{i}',f'admin{i}') for i in range(3)}
    claims=[signed_claim(keys[i],f'root{i}',f'admin{i}',f'local-clock-{i}','checkpoint-006',100000+(i-1)*6,20,f'nonce-{i}',f'key{i}') for i in range(3)]
    f=Chronos(auth)
    receipts=[f.ingest(c) for c in claims]
    matching=f.compare(claims,'checkpoint-006')
    conflict=signed_claim(keys[2],'root2','admin2','local-clock-2','checkpoint-007',101000,3,'nonce-conflict','key2')
    f.ingest(conflict)
    disagreement=f.compare([claims[0],claims[1],conflict],observation=None)
    output=dict(version='JANE-166',matching=matching,disagreement=disagreement,
                ingestion=receipts,ordered=temporal_relation([0,10],[11,20]),
                ambiguous=temporal_relation([0,10],[10,20]),audit=f.audit_chain(),
                audit_head=f.audit_head(),active='frozen_parent',learning_applied=False)
    f.close();return output

if __name__=='__main__':print(json.dumps(fixture(),indent=2))
