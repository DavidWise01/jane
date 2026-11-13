"""JANE 147 — portable custody proof, offline fixture protocol.

Portable artifacts carry an operator-signed statement and two independently pinned
*fixture attestor* signatures. The verifier's pinned trust map and a separately
retained checkpoint are inputs, not self-supplied authority. This code does not
prove real-world organizational independence or fetch external URLs.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import base64
import json
import re
import sqlite3

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

DOMAIN = "JANE-147-PORTABLE-V1"
TIME = "{{ 2026.11.12 }}{{ 19.32.00 }}{{ 123.45.56 }}"
CHRONOS = re.compile(r"^\{\{ (\d{4})\.(\d{2})\.(\d{2}) \}\}\{\{ (\d{2})\.(\d{2})\.(\d{2}) \}\}\{\{ ([+-]?\d{1,3})\.(\d{2})\.(\d{2}) \}\}$")
HEX = re.compile(r"^[0-9a-f]{64}$")

def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def hexdigest(data):
    return sha256(canon(data)).hexdigest()

def b64(b):
    return base64.b64encode(b).decode("ascii")

def unb64(s):
    return base64.b64decode(s, validate=True)

def pub(key):
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)

def parse_chronos(value, offset):
    m = CHRONOS.fullmatch(value) if isinstance(value, str) else None
    if not m or type(offset) is not int or not -840 <= offset <= 840:
        raise ValueError("Chronos syntax/offset")
    v = list(map(int, m.groups()))
    if abs(v[6]) > 360 or v[7] >= 60 or v[8] >= 60 or (abs(v[6]) == 360 and (v[7] or v[8])):
        raise ValueError("Angle out of bounds")
    return datetime(*v[:6], tzinfo=timezone(timedelta(minutes=offset))).astimezone(timezone.utc)

@dataclass(frozen=True)
class Trust:
    # Key ID -> (pinned public key, administrative control root)
    attestors: dict
    # Operator ID -> (pinned public key, custody root, canonical endpoint)
    operators: dict


def make_bundle(operator_key, operator_id, custody_root, endpoint, sequence, head,
                challenge, chronos=TIME, offset=-360, attestors=()):
    """Exporter signs payload. Two independent approvers must sign the same payload.

    The exporter may include attestor signatures but cannot invent *trusted*
    public keys: those are pinned at verifier initialization.
    """
    statement = dict(domain=DOMAIN, operator_id=operator_id, custody_root=custody_root,
                     endpoint=endpoint, checkpoint_sequence=sequence,
                     checkpoint_head=head, challenge=challenge,
                     chronos=chronos, utc_offset=offset,
                     operator_key_sha256=sha256(pub(operator_key)).hexdigest())
    sigs = [{"attestor_id": i, "signature": b64(k.sign(canon(statement)))} for i, k in attestors]
    return {"statement": statement,
            "operator_signature": b64(operator_key.sign(canon(statement))),
            "attestations": sigs}


class Verifier:
    def __init__(self, db_path, trust: Trust, retained_anchors, now, *, max_skew=300, required_attestors=2):
        if not 0 <= max_skew <= 86400 or not 1 <= required_attestors <= 5:
            raise ValueError("policy")
        self.db = sqlite3.connect(db_path)
        self.db.execute("CREATE TABLE IF NOT EXISTS seen (operator TEXT, challenge TEXT, PRIMARY KEY(operator,challenge))")
        self.db.execute("CREATE TABLE IF NOT EXISTS checked (root TEXT, seq INTEGER, head TEXT, PRIMARY KEY(root,seq,head))")
        self.db.commit()
        self.trust = trust
        self.anchors = retained_anchors
        self.now = now.astimezone(timezone.utc)
        self.max_skew = max_skew
        self.required = required_attestors
        self.events = []

    def _log(self, kind, status, statement):
        e = {"seq": len(self.events), "kind": kind, "status": status,
             "statement_hash": hexdigest(statement) if isinstance(statement, dict) else None,
             "prev": self.events[-1]["head"] if self.events else "0" * 64}
        e["head"] = hexdigest(e)
        self.events.append(e)
        return status

    def verify(self, bundle, expected_endpoint, expected_challenge):
        try:
            s = bundle["statement"]
            if not isinstance(s, dict) or set(s) != {
                "domain", "operator_id", "custody_root", "endpoint", "checkpoint_sequence",
                "checkpoint_head", "challenge", "chronos", "utc_offset", "operator_key_sha256"
            } or s["domain"] != DOMAIN:
                return self._log("REJECT", "INVALID_SCHEMA", s)
            if not isinstance(s["operator_id"], str) or not isinstance(s["custody_root"], str):
                return self._log("REJECT", "INVALID_SCHEMA", s)
            if type(s["checkpoint_sequence"]) is not int or s["checkpoint_sequence"] < 0 or \
                not isinstance(s["checkpoint_head"], str) or not HEX.fullmatch(s["checkpoint_head"]) or \
                not isinstance(s["operator_key_sha256"], str) or not HEX.fullmatch(s["operator_key_sha256"]):
                return self._log("REJECT", "INVALID_SCHEMA", s)
            if s["endpoint"] != expected_endpoint or s["challenge"] != expected_challenge or \
                not isinstance(expected_challenge, str) or len(expected_challenge) < 16:
                return self._log("REJECT", "BINDING_MISMATCH", s)
            identity = self.trust.operators.get(s["operator_id"])
            if identity is None:
                return self._log("REJECT", "UNKNOWN_OPERATOR", s)
            key, root, pinned_endpoint = identity
            if root != s["custody_root"] or pinned_endpoint != s["endpoint"] or \
                sha256(key).hexdigest() != s["operator_key_sha256"]:
                return self._log("REJECT", "IDENTITY_MISMATCH", s)
            Ed25519PublicKey.from_public_bytes(key).verify(unb64(bundle["operator_signature"]), canon(s))
            timestamp = parse_chronos(s["chronos"], s["utc_offset"])
            if abs((self.now - timestamp).total_seconds()) > self.max_skew:
                return self._log("REJECT", "STALE_CHRONOS", s)
            eligible = set()
            for att in bundle["attestations"]:
                pinned = self.trust.attestors.get(att["attestor_id"])
                if pinned is None:
                    continue
                attkey, admin = pinned
                Ed25519PublicKey.from_public_bytes(attkey).verify(unb64(att["signature"]), canon(s))
                if admin != root:
                    eligible.add(admin)
            if len(eligible) < self.required:
                return self._log("REJECT", "ATTESTATION_INSUFFICIENT", s)
            anchor = self.anchors.get(root)
            if anchor is None:
                return self._log("REJECT", "ANCHOR_UNAVAILABLE", s)
            if s["checkpoint_sequence"] < anchor[0]:
                return self._log("REJECT", "CHECKPOINT_ROLLBACK", s)
            if s["checkpoint_sequence"] == anchor[0] and s["checkpoint_head"] != anchor[1]:
                return self._log("REJECT", "CHECKPOINT_FORK", s)
            existing = self.db.execute("SELECT head FROM checked WHERE root=? AND seq=?",
                                       (root, s["checkpoint_sequence"])).fetchall()
            if any(head != s["checkpoint_head"] for (head,) in existing):
                return self._log("REJECT", "EQUIVOCATION", s)
            try:
                with self.db:
                    self.db.execute("INSERT INTO seen VALUES(?,?)", (s["operator_id"], s["challenge"]))
                    self.db.execute("INSERT OR IGNORE INTO checked VALUES(?,?,?)",
                                    (root, s["checkpoint_sequence"], s["checkpoint_head"]))
            except sqlite3.IntegrityError:
                return self._log("REJECT", "REPLAY", s)
            return self._log("ACCEPT", "VERIFIED_PORTABLE_FIXTURE", s)
        except (KeyError, ValueError, TypeError, InvalidSignature, OverflowError, AttributeError, IndexError, sqlite3.Error):
            return self._log("REJECT", "INVALID_PROOF", bundle.get("statement") if isinstance(bundle, dict) else None)

    def audit(self):
        prev = "0" * 64
        for n, e in enumerate(self.events):
            if e["seq"] != n or e["prev"] != prev or e["head"] != hexdigest({k:v for k,v in e.items() if k != "head"}):
                return "TAMPERED"
            prev = e["head"]
        return "VALID_LOCAL_EVENT_CHAIN"


def fixture():
    op = Ed25519PrivateKey.generate()
    ats = [Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()]
    endpoint = "https://witness.example.invalid/.well-known/jane-custody.json"
    root = "fixture:operator-A"
    keys = Trust({f"att-{i}":(pub(k),f"fixture:attestor-{i}") for i,k in enumerate(ats)},
                 {"operator-A":(pub(op),root,endpoint)})
    anchor = sha256(b"checkpoint 8").hexdigest()
    ch = "verifier-challenge-00001"
    bundle = make_bundle(op,"operator-A",root,endpoint,8,anchor,ch,attestors=tuple((f"att-{i}",k) for i,k in enumerate(ats)))
    return keys, {root:(8,anchor)}, bundle, endpoint, ch, parse_chronos(TIME,-360)


def demo(db_path=":memory:"):
    trust, anchors, bundle, endpoint, ch, now = fixture()
    v = Verifier(db_path,trust,anchors,now)
    first = v.verify(bundle,endpoint,ch)
    second = v.verify(bundle,endpoint,ch)
    return {"version":"JANE-147","first":first,"replay":second,
            "audit":v.audit(),"registered_operator_roots":1,
            "independent_witness_service_deployed":False,
            "learning_applied":False,"jane_decision":"UNDECIDED"}

if __name__ == "__main__":
    print(json.dumps(demo(),indent=2))