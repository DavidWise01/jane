"""JANE 116: bounded read-only evidence scout. Input is externally retrieved PUBLIC text.
No network calls, model training, or automatic learning decisions occur here.
"""
from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import urlsplit
from ipaddress import ip_address

MAX_ITEMS=8
MAX_BYTES=32768
MAX_TEXT=4096

@dataclass(frozen=True)
class Observation:
    url: str
    title: str
    excerpt: str
    declared_origin: str | None=None
    visibility: str="public"

def public_url(url):
    try:
        p=urlsplit(url)
        if p.scheme!="https" or not p.hostname or p.username or p.password or p.port not in (None,443):
            return False
        host=p.hostname.lower().rstrip(".")
        if host in {"localhost","0root.ai","github.com"} or host.endswith(".local"):
            return False
        try:
            ip_address(host)
            return False
        except ValueError:
            return "." in host and all(host.split("."))
    except ValueError:
        return False

def make_packet(question,observations,existing_rule,new_distinction):
    if len(observations)>MAX_ITEMS:raise ValueError("item budget exceeded")
    evidence=[]
    seen=set()
    for o in observations:
        if o.visibility!="public" or not public_url(o.url):
            raise ValueError("nonpublic or nonexternal evidence rejected")
        if len(o.excerpt.encode("utf-8"))>MAX_BYTES or len(o.excerpt)>MAX_TEXT:
            raise ValueError("text budget exceeded")
        digest=sha256(o.excerpt.encode("utf-8")).hexdigest()
        if digest in seen:continue
        seen.add(digest)
        evidence.append({"url":o.url,"title":o.title[:180],"excerpt":o.excerpt,
                         "sha256":digest,"origin":o.declared_origin,"trust":"untrusted_web_data"})
    if not evidence:raise ValueError("no public evidence")
    unknown=[e["url"] for e in evidence if not e["origin"]]
    origins=sorted({e["origin"] for e in evidence if e["origin"]})
    return {"version":"JANE-116","question":question,"existing_rule":existing_rule,
            "proposed_distinction":new_distinction,"evidence":evidence,
            "origins":origins,"unknown_ancestry":unknown,
            "status":"ANCESTRY_REVIEW" if unknown else "JANE_REVIEW_REQUIRED",
            "decision":"UNDECIDED","learning_applied":False,
            "constraints":{"max_items":MAX_ITEMS,"max_bytes_each":MAX_BYTES}}

def flay(packet):
    missing=[]
    if packet["unknown_ancestry"]:missing.append("source ancestry")
    if len(packet["origins"])<2:missing.append("independent corroboration")
    missing.append("Jane's evaluation of whether distinction improves novel-case accuracy")
    return {"candidate":packet["proposed_distinction"],"missing":missing,
            "action":"REQUEST_EVIDENCE_OR_JANE_REVIEW","auto_learn":False}
