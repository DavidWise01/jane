"""JANE 121 — paired holdout comparison; offline, no automatic learning."""
from dataclasses import dataclass
from hashlib import sha256
import json
@dataclass(frozen=True)
class Case:
    case_id: str
    urls: tuple
    roots: tuple
    independent: bool
    group: str
    split: str = 'holdout'

def old_rule(c): return len(set(c.urls))>=2
def revised_rule(c):
    if any(x is None for x in c.roots): return None
    return len(set(c.roots))>=2

def evaluate(cases,min_groups=2):
    cases=tuple(cases)
    if len(cases)>128 or not cases or len({c.case_id for c in cases})!=len(cases): raise ValueError('case budget or duplicate IDs')
    if any(c.split!='holdout' or not c.group or not c.urls or len(c.urls)!=len(c.roots) for c in cases): raise ValueError('invalid holdout')
    records=[]; old_hits=new_hits=regressions=abstentions=0
    for c in cases:
        old=old_rule(c); new=revised_rule(c)
        a=old==c.independent; b=(new==c.independent if new is not None else False)
        old_hits+=a;new_hits+=b;regressions+=int(a and not b);abstentions+=new is None
        records.append({'case_id':c.case_id,'group':c.group,'old_correct':a,'new_correct':b,'abstained':new is None})
    gain=new_hits-old_hits
    status='JANE_REVIEW_CANDIDATE' if gain>0 and regressions==0 and abstentions==0 and len({c.group for c in cases})>=min_groups else 'FLAY_MORE_EVIDENCE'
    result={'version':'JANE-121','baseline_correct':old_hits,'revised_correct':new_hits,'paired_gain':gain,'regressions':regressions,'abstentions':abstentions,'groups':len({c.group for c in cases}), 'status':status,'cases':records,'jane_decision':'UNDECIDED','learning_applied':False,'limitation':'Synthetic paired accuracy does not establish causal improvement on real novel examples.'}
    result['digest']=sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return result

def demonstration():
    return evaluate([Case('owned_mirror',('github','0root.ai'),('owned','owned'),False,'owned'), Case('syndicated',('news-a','news-b'),('wire','wire'),False,'wire'),Case('independent',('lab-a','lab-b'),('lab-a','lab-b'),True,'labs'),Case('multi_copy',('a','b','c'),('root','root','root'),False,'archive')])
if __name__=='__main__':print(json.dumps(demonstration(),indent=2))
