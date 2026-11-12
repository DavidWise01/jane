"""JANE 140 — cohort-preserving branch evaluation. Synthetic offline evidence only."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from collections import defaultdict
from fractions import Fraction
import json

CHRONOS = '{{ 2026.11.12 }}{{ 09.00.00 }}{{ 123.45.56 }}'
ANCHORS = ('upperleftrear','centerrear','lowerleftrear','centerupper','center','centerlower','upperrightfront','rightcenter','lowerrightfront')

def digest(obj):
    return sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def root_of(surface, root):
    return 'owned:canonical' if surface in ('github','0root.ai') else root


@dataclass(frozen=True)
class Case:
    case_id: str
    cohort: str
    ancestry: str
    truth: bool
    baseline: bool | None
    candidate: bool | None
    split: str = 'holdout'
    surface: str = 'internet'
    content_hash: str = 'a'*64


class Flay140:
    def __init__(self, parent_hash='f'*64, chronos=CHRONOS):
        if len(parent_hash) != 64 or not chronos:
            raise ValueError('frozen parent required')
        self.parent_hash = parent_hash
        self.chronos = chronos
        self.active = 'frozen_parent'
        self.events = []

    def _record(self, kind, data):
        event = {'seq':len(self.events), 'kind':kind, 'data':data,
                 'prev':self.events[-1]['head'] if self.events else '0'*64}
        event['head'] = digest(event)
        self.events.append(event)

    def evaluate(self, cases, known_training_hashes=(), min_cohort=2):
        cases = tuple(cases)
        if not 1 <= len(cases) <= 256 or not 1 <= min_cohort <= 64:
            raise ValueError('bounded evaluation required')
        if len({c.case_id for c in cases}) != len(cases):
            raise ValueError('duplicate case ids')
        if any(not c.case_id or not c.cohort or not c.ancestry or c.split!='holdout' or
               not isinstance(c.truth,bool) or c.baseline is not None and not isinstance(c.baseline,bool) or
               c.candidate is not None and not isinstance(c.candidate,bool) or
               len(c.content_hash)!=64 for c in cases):
            raise ValueError('invalid case')
        if any(c.content_hash in known_training_hashes for c in cases):
            self._record('QUARANTINE', {'reason':'HOLDOUT_LEAKAGE', 'cases':len(cases)})
            return {'status':'HOLDOUT_LEAKAGE', 'learning_applied':False, 'jane_decision':'UNDECIDED'}
        rows = defaultdict(list)
        for c in cases:
            rows[c.cohort].append(c)
        report=[]
        total_b = total_n = gain = regression = abstentions = 0
        for name, group in sorted(rows.items()):
            b_correct = sum(c.baseline is not None and c.baseline==c.truth for c in group)
            n_correct = sum(c.candidate is not None and c.candidate==c.truth for c in group)
            g = sum(c.baseline != c.truth and c.candidate == c.truth for c in group if c.baseline is not None and c.candidate is not None)
            r = sum(c.baseline == c.truth and c.candidate != c.truth for c in group if c.baseline is not None and c.candidate is not None)
            abstain = sum(c.candidate is None for c in group)
            distinct_roots = len({root_of(c.surface,c.ancestry) for c in group})
            report.append({'cohort':name,'n':len(group),'baseline_correct':b_correct,'candidate_correct':n_correct,
                           'gain':g,'regression':r,'abstentions':abstain,'distinct_roots':distinct_roots,
                           'status':'UNDERPOWERED' if len(group)<min_cohort else 'REGRESSION' if r else 'ABSTENTION' if abstain else 'NO_REGRESSION'})
            total_b += b_correct; total_n += n_correct;gain+=g;regression+=r;abstentions+=abstain
        flags = {'cohort_regression':any(s['regression']>0 for s in report),
                 'abstention_gap':abstentions>0,'insufficient_cohort':any(s['n']<min_cohort for s in report)}
        status = ('BLOCK_SUBGROUP_REGRESSION' if flags['cohort_regression'] else
                  'ABSTAIN_INCOMPLETE_COVERAGE' if flags['abstention_gap'] else
                  'ABSTAIN_SMALL_COHORT' if flags['insufficient_cohort'] else
                  'JANE_REVIEW_CANDIDATE' if total_n>total_b else 'NO_IMPROVEMENT')
        result={'version':'JANE-140','chronos':self.chronos,'parent_hash':self.parent_hash,
                'n':len(cases),'baseline_correct':total_b,'candidate_correct':total_n,
                'gross_gain':gain,'gross_regression':regression,'cohorts':report,
                'flags':flags,'status':status,'active':self.active,
                'learning_applied':False,'jane_decision':'UNDECIDED',
                'caveat':'Synthetic held-out labels; no live sourcing, no statistical power claim.'}
        result['digest']=digest(result)
        self._record('COMPARE',{'digest':result['digest'],'status':status})
        return result

    def audit(self):
        prev='0'*64
        for i,e in enumerate(self.events):
            if e['seq']!=i or e['prev']!=prev or digest({k:v for k,v in e.items() if k!='head'})!=e['head']:
                return 'TAMPERED'
            prev=e['head']
        return 'VALID_LOCAL_CHAIN'


def demo():
    """8 test cases: six wins in A, two regressions in B. Aggregate +4, veto."""
    cases=[]
    for i in range(6):
        cases.append(Case(f'A{i}','A','external:A',True,False,True, content_hash=f'{i+1:064x}'))
    for i in range(2):
        cases.append(Case(f'B{i}','B','external:B',True,True,False, content_hash=f'{i+50:064x}'))
    flay=Flay140()
    return flay, flay.evaluate(cases)

if __name__=='__main__':
    flay,result=demo()
    print(json.dumps({'result':result,'ledger_audit':flay.audit()},indent=2))
