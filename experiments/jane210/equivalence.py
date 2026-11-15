"""JANE 210 — subgroup uncertainty and equivalence gate.

Illustrative independent-binomial Wilson score intervals, combined by
Bonferroni-adjusted Wilson interval subtraction. Never equate non-significance to equivalence.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json, math
from typing import Mapping

Z = 2.241402727604947


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return sha256(canonical(value).encode()).hexdigest()


def wilson(successes: int, total: int, z: float=Z):
    if type(total) is not int or type(successes) is not int or total <= 0 or not (0 <= successes <= total):
        raise ValueError('invalid binomial counts')
    p=successes/total
    d=1+z*z/total
    mid=(p+z*z/(2*total))/d
    half=z*math.sqrt((p*(1-p)+z*z/(4*total))/total)/d
    return (max(0., mid-half), min(1., mid+half))


@dataclass(frozen=True)
class Counts:
    success: int
    total: int
    def __post_init__(self):
        wilson(self.success,self.total)


@dataclass(frozen=True)
class Group:
    name: str
    before: Counts
    after: Counts
    before_root: str
    after_root: str


def analyze(groups, *, margin=.10, min_n=30, z=Z, expected_groups=None, max_absolute_shift=None):
    if not math.isfinite(margin) or not 0 < margin < 1:
        raise ValueError('margin must be in (0,1)')
    if type(min_n) is not int or min_n < 1:
        raise ValueError('min_n must be positive')
    if not math.isfinite(z) or z <= 0:
        raise ValueError('z must be positive finite')
    if max_absolute_shift is not None and (not math.isfinite(max_absolute_shift) or max_absolute_shift < 0):
        raise ValueError('invalid monitoring shift')
    gs=list(groups)
    if not gs:
        raise ValueError('empty groups')
    names=[g.name for g in gs]
    if any(not isinstance(n,str) or not n.strip() for n in names) or len(set(names))!=len(names):
        raise ValueError('invalid/duplicate group name')
    if expected_groups is not None and set(names)!=set(expected_groups):
        return {'verdict':'MISSING_OR_EXTRA_GROUP','details':[], 'frozen_digest':digest({'groups':sorted(names)}), 'margin':margin}
    outcomes=[]
    for g in sorted(gs,key=lambda x:x.name):
        if not g.before_root or not g.after_root:
            raise ValueError('missing declared provenance')
        before=wilson(g.before.success,g.before.total,z)
        after=wilson(g.after.success,g.after.total,z)
        diff=(after[0]-before[1],after[1]-before[0])
        estimate=g.after.success/g.after.total-g.before.success/g.before.total
        adequate=(min(g.before.total,g.after.total)>=min_n)
        # Two nominal 97.5% Wilson intervals use Bonferroni adjustment
        # for a nominal simultaneous 95% comparison; Wilson coverage is approximate.
        if not adequate:
            verdict='INSUFFICIENT_SUBGROUP_SAMPLE'
        elif diff[0] > -margin and diff[1] < margin:
            verdict='EQUIVALENCE_SUPPORTED_CONDITIONAL'
        elif diff[0] > margin or diff[1] < -margin:
            verdict='MATERIAL_DRIFT_SUPPORTED_CONDITIONAL'
        else:
            verdict='STABILITY_NOT_ESTABLISHED'
        if g.before_root==g.after_root and verdict=='EQUIVALENCE_SUPPORTED_CONDITIONAL':
            verdict='SHARED_ANCESTRY_UNVERIFIED'
        outcomes.append({'name':g.name,'before':[g.before.success,g.before.total],
                         'after':[g.after.success,g.after.total], 'difference_estimate':estimate,
                         'before_interval':list(before),'after_interval':list(after),
                         'difference_interval':list(diff),'result':verdict,
                         'declared_roots':[g.before_root,g.after_root]})
    priority=['MATERIAL_DRIFT_SUPPORTED_CONDITIONAL','SHARED_ANCESTRY_UNVERIFIED',
              'INSUFFICIENT_SUBGROUP_SAMPLE','STABILITY_NOT_ESTABLISHED']
    allresults={x['result'] for x in outcomes}
    verdict=next((x for x in priority if x in allresults),'EQUIVALENCE_SUPPORTED_CONDITIONAL')
    data={'groups':[{'name':g.name,'before':[g.before.success,g.before.total],
                     'after':[g.after.success,g.after.total], 'roots':[g.before_root,g.after_root]}
                    for g in sorted(gs,key=lambda x:x.name)],
          'margin':margin,'min_n':min_n,'z':z,'max_absolute_shift':max_absolute_shift}
    return {'verdict':verdict,'details':outcomes,'frozen_digest':digest(data),
            'margin':margin,'min_n':min_n,
            'notice':'Signed or independent custody not established. Nominal Bonferroni-adjusted Wilson 95% difference interval; finite-sample Wilson coverage is approximate, not a guaranteed simultaneous bound.'}


def demo():
    def G(name,bn,bd,an,ad):
        return Group(name,Counts(bn,bd),Counts(an,ad),name+'-baseline',name+'-current')
    cases={
       'small_equal': [G('tiny',2,4,2,4)],
       'large_equal':[G('large',500,1000,500,1000)],
       'large_drift':[G('large',900,1000,500,1000)],
       'moderate_equal':[G('moderate',15,30,15,30)],
       'mixed':[G('large',500,1000,500,1000),G('tiny',2,4,2,4)],
    }
    return {name:analyze(value) for name,value in cases.items()}

if __name__=='__main__':
    print(json.dumps(demo(),indent=2,sort_keys=True))