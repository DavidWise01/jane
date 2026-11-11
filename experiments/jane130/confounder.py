"""JANE 130: synthetic stratified confounder check; no learning or live retrieval."""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json

CHRONOS="{{ - year:month:day || hour:minute:second || degree.arcminute.arcsecond || }}"
@dataclass(frozen=True)
class Observation:
    id:str
    a:bool
    b:bool
    c:str|None
    chronos:str
    root:str|None
    custody:str|None

def _difference(rows):
    yes=[r for r in rows if r.a]
    no=[r for r in rows if not r.a]
    if not yes or not no:return None
    return Fraction(sum(r.b for r in yes),len(yes))-Fraction(sum(r.b for r in no),len(no))

def evaluate(observations,min_per_cell=1):
    rows=tuple(observations)
    if not 1<=len(rows)<=512 or not 1<=min_per_cell<=128:raise ValueError("budget")
    if len({r.id for r in rows})!=len(rows):raise ValueError("duplicate")
    if any(not r.id or not isinstance(r.a,bool) or not isinstance(r.b,bool) or not r.chronos for r in rows):raise ValueError("invalid row")
    if any(not r.c or not r.root or not r.custody for r in rows):
        return dict(status="EVIDENCE_INCOMPLETE",learning_applied=False,jane_decision="UNDECIDED")
    raw=_difference(rows)
    if raw is None:return dict(status="NO_COMPARISON",learning_applied=False,jane_decision="UNDECIDED")
    details=[];adjusted=Fraction(0);gaps=[]
    for group in sorted(set(r.c for r in rows)):
        subset=[r for r in rows if r.c==group]
        on=sum(r.a for r in subset);off=len(subset)-on
        difference=_difference(subset)
        if on<min_per_cell or off<min_per_cell:gaps.append(group)
        else:adjusted+=Fraction(len(subset),len(rows))*difference
        details.append(dict(group=group,on=on,off=off,difference=str(difference) if difference is not None else None))
    status=("POSITIVITY_GAP" if gaps else "SIMPSON_REVERSAL" if raw*adjusted<0 else
            "CONFOUNDER_EXPLAINS_ASSOCIATION" if raw!=0 and adjusted==0 else
            "ASSOCIATION_REMAINS_AFTER_ADJUSTMENT")
    result=dict(version="JANE-130",status=status,n=len(rows),raw_difference=str(raw),
                adjusted_difference=None if gaps else str(adjusted),strata=details,
                missing_strata=gaps,learning_applied=False,jane_decision="UNDECIDED",
                caveat="Synthetic observational association; not an identified causal effect")
    result["sha256"]=sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return result

def demo():
    rows=[]
    def add(c,a,b,n):
        for _ in range(n):
            i=len(rows)
            rows.append(Observation(str(i),a,b,c,
                "{{ - 2026:11:11 || 15:18:00 || +123.45.56 || }}",
                "synthetic:owned","test-custody"))
    add("high",True,True,72);add("high",True,False,18)
    add("high",False,True,9);add("high",False,False,1)
    add("low",True,True,1);add("low",True,False,9)
    add("low",False,True,18);add("low",False,False,72)
    return evaluate(rows)

if __name__=="__main__":print(json.dumps(demo(),indent=2))
