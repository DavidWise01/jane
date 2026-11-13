"""JANE 153: conditional commutativity in a declared finite domain.

Offline exhaustive bounded exploration. No general proof outside the domain.
"""
from dataclasses import dataclass
from hashlib import sha256
import json

CHRONOS = "{{ 2026.11.13 }}{{ 11.34.00 }}{{ 123.45.56 }}"
def canon(value): return json.dumps(value, sort_keys=True, separators=(",", ":"))
def digest(value): return sha256(canon(value).encode()).hexdigest()
@dataclass(frozen=True)
class Operation:
    kind: str
    argument: int
    def __post_init__(self):
        if self.kind not in ("add", "multiply", "set", "conditional_add"):
            raise ValueError("unsupported operation")
        if type(self.argument) is not int or abs(self.argument)>100:
            raise ValueError("invalid argument")
    def apply(self, value):
        if type(value) is not int or abs(value)>100000:
            raise ValueError("out of arithmetic domain")
        if self.kind=="add": return value+self.argument
        if self.kind=="multiply": return value*self.argument
        if self.kind=="set": return self.argument
        if value<0: raise ValueError("precondition: value >= 0")
        return value+self.argument
@dataclass(frozen=True)
class Domain:
    low: int
    high: int
    def __post_init__(self):
        if type(self.low) is not int or type(self.high) is not int or self.low>self.high or self.high-self.low>256 or abs(self.low)>1000 or abs(self.high)>1000:
            raise ValueError("invalid bounded domain")
    def states(self): return range(self.low, self.high+1)
def replay(state, first, second):
    trace=[state]
    try:
        value=first.apply(state);trace.append(value)
        value=second.apply(value);trace.append(value)
        return dict(valid=True, final=value, trace=trace)
    except ValueError as e:
        return dict(valid=False, final=None, trace=trace, error=str(e))
class FLAY:
    def __init__(self, op_a, op_b, domain, parent_hash="f"*64):
        if len(parent_hash)!=64 or any(c not in "0123456789abcdef" for c in parent_hash):
            raise ValueError("parent")
        self.a=op_a;self.b=op_b;self.domain=domain;self.parent_hash=parent_hash
        self.events=[];self.active="frozen_parent"
        self._append("DECLARE", dict(a=op_a.__dict__, b=op_b.__dict__, domain=domain.__dict__, chronos=CHRONOS, parent=parent_hash))
    def _append(self,kind,data):
        event=dict(seq=len(self.events),kind=kind,data=data,prev=self.events[-1]["head"] if self.events else "0"*64)
        event["head"]=digest(event);self.events.append(event)
    def evaluate(self):
        failures=[]; invalid=0;checked=0
        for state in self.domain.states():
            ab=replay(state,self.a,self.b)
            ba=replay(state,self.b,self.a)
            checked+=1
            if not ab["valid"] or not ba["valid"]: invalid+=1
            if ab["valid"] != ba["valid"] or (ab["valid"] and ba["valid"] and ab["final"]!=ba["final"]):
                failures.append(dict(state=state,AB=ab,BA=ba))
        # Smallest = minimum |s|, then numeric s; deterministic irrespective of scan direction.
        failures.sort(key=lambda item:(abs(item["state"]),item["state"]))
        first=failures[0] if failures else None
        status=("COUNTEREXAMPLE_FOUND" if first else
                "DOMAIN_HAS_INVALID_STATES" if invalid else
                "COMMUTES_ON_DECLARED_DOMAIN")
        result=dict(version="JANE-153",chronos=CHRONOS,status=status,
                    declared_domain=[self.domain.low,self.domain.high],
                    states_checked=checked,invalid_orders=invalid,
                    counterexample_count=len(failures),smallest_counterexample=first,
                    scope="declared finite integer domain only",active=self.active,
                    learning_applied=False,jane_decision="UNDECIDED",
                    independent_witness_increment=0)
        result["digest"]=digest(result)
        self._append("EVALUATE",dict(result_digest=result["digest"],status=status,
                                      smallest_counterexample=first))
        return result
    def audit(self,external_head=None):
        prev="0"*64
        for i,event in enumerate(self.events):
            if event["seq"]!=i or event["prev"]!=prev or event["head"]!=digest({k:v for k,v in event.items() if k!="head"}):return "TAMPERED"
            prev=event["head"]
        return "EXTERNAL_HEAD_MISMATCH" if external_head is not None and external_head!=prev else "VALID_LOCAL_CHAIN"
def demo():
    # Multiplication by 0 and assignment to 0 commute at s=0 only, not elsewhere.
    engine=FLAY(Operation("multiply",0),Operation("set",0),Domain(-3,3))
    return engine,engine.evaluate()
if __name__=="__main__":
    f,r=demo()
    print(json.dumps(dict(result=r,audit=f.audit()),indent=2))
