"""JANE 146 — custody enrollment with signed challenges and dual authorization.

Offline reference implementation. A configured authority establishes a *registry claim*,
not verified real-world organizational independence. No network or automatic learning.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

CHRONOS = "{{ 2026.11.12 }}{{ 17.27.00 }}{{ 123.45.56 }}"
_DATE = re.compile(r"^\{\{ (\d{4})\.(\d{2})\.(\d{2}) \}\}\{\{ (\d{2})\.(\d{2})\.(\d{2}) \}\}\{\{ ([+-]?\d{1,3})\.(\d{2})\.(\d{2}) \}\}$")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def utc(stamp, offset):
    m = _DATE.fullmatch(stamp)
    if not m or type(offset) is not int or not -840 <= offset <= 840:
        raise ValueError("Chronos syntax/offset")
    parts = list(map(int, m.groups()))
    if abs(parts[6]) > 360 or parts[7] > 59 or parts[8] > 59 or (abs(parts[6]) == 360 and (parts[7] or parts[8])):
        raise ValueError("Chronos angle")
    return datetime(*parts[:6], tzinfo=timezone(timedelta(minutes=offset))).astimezone(timezone.utc)


def verify(public, message, signature):
    try:
        if not isinstance(public, bytes) or len(public) != 32:
            return False
        Ed25519PublicKey.from_public_bytes(public).verify(signature, canonical(message))
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


@dataclass(frozen=True)
class Authority:
    authority_id: str
    public: bytes
    administrative_root: str


class Enrollment:
    def __init__(self, database, anchor_file, authorities, *, max_skew=300):
        self.db = sqlite3.connect(str(database))
        self.anchor_file = Path(anchor_file)
        self.authorities = dict(authorities)
        self.max_skew = max_skew
        if not 0 <= max_skew <= 86400:
            raise ValueError("skew")
        if not self.authorities or any(k != a.authority_id or not a.administrative_root for k, a in self.authorities.items()):
            raise ValueError("authority registry")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS challenges(nonce TEXT PRIMARY KEY,operator TEXT,root TEXT,pub BLOB,stamp TEXT,offset INTEGER,expires TEXT,spent INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS custody(root TEXT PRIMARY KEY,operator TEXT UNIQUE,key_id TEXT UNIQUE,pub BLOB,generation INTEGER,active INTEGER);
        CREATE TABLE IF NOT EXISTS used(root TEXT,nonce TEXT,PRIMARY KEY(root,nonce));
        CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY,kind TEXT,body TEXT,prev TEXT,head TEXT);
        """)
        self.db.commit()

    def _event(self, kind, body):
        last = self.db.execute("SELECT seq,head FROM history ORDER BY seq DESC LIMIT 1").fetchone()
        seq = last[0]+1 if last else 0
        prev = last[1] if last else "0"*64
        head = sha(dict(seq=seq, kind=kind, body=body, prev=prev))
        self.db.execute("INSERT INTO history VALUES(?,?,?,?,?)", (seq,kind,canonical(body).decode(),prev,head))
        return head

    def challenge(self, nonce, operator, root, public, stamp, offset, now, *, lifetime=300):
        if not isinstance(nonce,str) or len(nonce)<16 or not operator or not root or len(public)!=32 or not 1<=lifetime<=900:
            return "INVALID_CHALLENGE"
        try:
            ts = utc(stamp,offset)
            if abs((now.astimezone(timezone.utc)-ts).total_seconds()) > self.max_skew:
                return "STALE_CHRONOS"
        except (ValueError,TypeError):
            return "INVALID_CHRONOS"
        if self.db.execute("SELECT 1 FROM custody WHERE root=? OR operator=?", (root,operator)).fetchone():
            return "IDENTITY_ALREADY_ENROLLED"
        try:
            with self.db:
                self.db.execute("INSERT INTO challenges VALUES(?,?,?,?,?,?,?,0)",
                    (nonce,operator,root,public,stamp,offset,(now+timedelta(seconds=lifetime)).isoformat()))
                self._event("CHALLENGE",dict(nonce=nonce,operator=operator,root=root,public_digest=hashlib.sha256(public).hexdigest()))
        except sqlite3.IntegrityError:
            return "REPLAY"
        return "CHALLENGE_ISSUED"

    def enroll(self, nonce, key_id, possession_signature, approvals, now):
        row = self.db.execute("SELECT operator,root,pub,stamp,offset,expires,spent FROM challenges WHERE nonce=?",(nonce,)).fetchone()
        if row is None:
            return "UNKNOWN_CHALLENGE"
        operator,root,public,stamp,offset,expires,spent = row
        if spent:
            return "REPLAY"
        if now > datetime.fromisoformat(expires):
            return "EXPIRED_CHALLENGE"
        if not key_id:
            return "INVALID_KEY_ID"
        binding = dict(domain="JANE-146-ENROLL", nonce=nonce,key_id=key_id,operator=operator,root=root,
                       public_sha256=hashlib.sha256(public).hexdigest(),chronos=stamp,utc_offset=offset)
        if not verify(public,binding,possession_signature):
            return "FAILED_KEY_POSSESSION"
        approved_roots=set()
        for authority_id,sig in approvals:
            a=self.authorities.get(authority_id)
            if a and verify(a.public,dict(domain="JANE-146-APPROVE",binding=binding,authority=authority_id),sig):
                approved_roots.add(a.administrative_root)
        if len(approved_roots)<2:
            return "INSUFFICIENT_ATTESTATION"
        try:
            with self.db:
                self.db.execute("INSERT INTO custody VALUES(?,?,?,?,0,1)",(root,operator,key_id,public))
                self.db.execute("UPDATE challenges SET spent=1 WHERE nonce=?",(nonce,))
                self._event("ENROLL",dict(root=root,operator=operator,key_id=key_id,public_sha256=binding["public_sha256"],attestation_count=len(approved_roots)))
        except sqlite3.IntegrityError:
            return "IDENTITY_ALREADY_ENROLLED"
        return "ENROLLED_REGISTRY_CLAIM"

    def rotate(self, root, new_key_id, new_public, nonce, chronos, offset, signature, now):
        row=self.db.execute("SELECT operator,key_id,pub,generation,active FROM custody WHERE root=?",(root,)).fetchone()
        if row is None or not row[4] or not new_key_id or len(new_public)!=32 or len(nonce)<16:
            return "INVALID_ROTATION"
        try:
            if abs((utc(chronos,offset)-now.astimezone(timezone.utc)).total_seconds())>self.max_skew:
                return "STALE_CHRONOS"
        except (ValueError,TypeError):
            return "INVALID_CHRONOS"
        body=dict(domain="JANE-146-ROTATE",root=root,old_key=row[1],new_key=new_key_id,
                  new_public_sha256=hashlib.sha256(new_public).hexdigest(),generation=row[3]+1,
                  nonce=nonce,chronos=chronos,utc_offset=offset)
        if not verify(row[2],body,signature):
            return "FAILED_ROTATION_SIGNATURE"
        try:
            with self.db:
                self.db.execute("INSERT INTO used VALUES(?,?)",(root,nonce))
                self.db.execute("UPDATE custody SET key_id=?,pub=?,generation=? WHERE root=?",(new_key_id,new_public,row[3]+1,root))
                self._event("ROTATE",body)
        except sqlite3.IntegrityError:
            return "REPLAY_OR_COLLISION"
        return "ROTATED_SAME_CUSTODY"

    def custody(self):
        rows=self.db.execute("SELECT root,operator,key_id,generation FROM custody ORDER BY root").fetchall()
        return [dict(root=r,operator=o,key_id=k,generation=g) for r,o,k,g in rows]

    def head(self):
        row=self.db.execute("SELECT head FROM history ORDER BY seq DESC LIMIT 1").fetchone()
        return row[0] if row else "0"*64

    def export_anchor(self):
        packet=dict(head=self.head(),count=self.db.execute("SELECT COUNT(*) FROM history").fetchone()[0])
        self.anchor_file.write_text(json.dumps(packet,sort_keys=True))
        return packet

    def audit(self):
        prev="0"*64
        for i,(seq,kind,body,prior,head) in enumerate(self.db.execute("SELECT * FROM history ORDER BY seq")):
            if seq != i or prior != prev or head != sha(dict(seq=seq,kind=kind,body=json.loads(body),prev=prior)):
                return "TAMPERED"
            prev=head
        if self.anchor_file.exists():
            a=json.loads(self.anchor_file.read_text())
            if a != dict(head=prev,count=self.db.execute("SELECT COUNT(*) FROM history").fetchone()[0]):
                return "ROLLBACK_OR_FORK"
            return "MATCHED_LOCAL_ANCHOR"
        return "VALID_LOCAL_CHAIN_ONLY"

    def report(self):
        return dict(version="JANE-146",registered_custody=self.custody(),audit=self.audit(),
                    root_count=len(self.custody()),operational_independence="UNVERIFIED",
                    active="frozen_parent",learning_applied=False,jane_decision="UNDECIDED")