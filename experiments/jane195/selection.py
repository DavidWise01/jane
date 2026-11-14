"""JANE 195: deterministic sampling-coverage and selection-bias audit.

Synthetic fixtures; no causal or real-world independent-observer inference.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from hashlib import sha256
from math import comb
import json

def canonical(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
def digest(x): return sha256(canonical(x).encode()).hexdigest()

@dataclass(frozen=True)
class Round:
    index: int
    band: str
    selected: bool
    observer: str
    ancestry: str
    status: str
    def __post_init__(self):
        if type(self.index) is not int or self.index < 0: raise ValueError('index')
        if self.band not in ('day','night'): raise ValueError('band')
        if type(self.selected) is not bool: raise ValueError('selected')
        if not self.observer or not self.ancestry: raise ValueError('identity')
        if self.status not in ('published','not_observed','outage','unselected'): raise ValueError('status')
        if self.selected == (self.status == 'unselected'): raise ValueError('selection and status inconsistent')

def audit(rounds, *, max_rounds=1024):
    rounds=list(rounds)
    if not rounds or len(rounds)>max_rounds: raise ValueError('population size')
    indices=[r.index for r in rounds]
    if len(set(indices))!=len(indices): raise ValueError('duplicate round')
    if sorted(indices)!=list(range(min(indices),max(indices)+1)): raise ValueError('incomplete declared population')
    population=Counter(r.band for r in rounds)
    chosen=Counter(r.band for r in rounds if r.selected)
    observed=Counter(r.band for r in rounds if r.selected and r.status!='outage')
    missing=Counter(r.band for r in rounds if r.selected and r.status=='not_observed')
    outages=Counter(r.band for r in rounds if r.selected and r.status=='outage')
    published=Counter(r.band for r in rounds if r.selected and r.status=='published')
    roots={r.ancestry for r in rounds if r.selected and r.status!='outage'}
    observers={r.observer for r in rounds if r.selected and r.status!='outage'}
    by_band={band:{'population':population[band], 'selected':chosen[band], 'observable':observed[band], 'published':published[band], 'not_observed':missing[band], 'outages':outages[band], 'coverage':(chosen[band]/population[band] if population[band] else None)} for band in ('day','night')}
    uncovered=[band for band in ('day','night') if population[band] and not chosen[band]]
    unequal=(all(population[b] for b in ('day','night')) and chosen['day']*population['night']!=chosen['night']*population['day'])
    shared=len(observers)>len(roots)
    # Published-rate bounds: every unselected or outage round can be either published or not.
    n=len(rounds)
    definite=sum(published.values())
    unknown=sum(not r.selected or r.status=='outage' for r in rounds)
    lower=definite/n
    upper=(definite+unknown)/n
    selected_count=sum(chosen.values())
    status=('UNCOVERED_POPULATION_STRATUM' if uncovered else
            'SELECTION_COVERAGE_IMBALANCE' if unequal else
            'SHARED_OBSERVER_ANCESTRY' if shared else
            'COVERAGE_BALANCED_FIXTURE')
    out={'version':'JANE-195','status':status,'population_rounds':n,'selected_rounds':selected_count,
         'by_band':by_band,'uncovered_bands':uncovered,'unequal_selection_rates':bool(unequal),
         'selected_observers':len(observers),'declared_observation_roots':len(roots),'shared_ancestry':shared,
         'population_published_fraction_bounds':[lower,upper],
         'scope':'finite declared population, synthetic observer declarations',
         'causal_claim':False,'independence_established':False,'active_parent':'frozen',
         'policy_digest':digest({'population':sorted((r.index,r.band) for r in rounds), 'selected':sorted(r.index for r in rounds if r.selected)})}
    out['digest']=digest(out)
    return out

def demo():
    # Equal day/night population, selection concentrated in day.
    rows=[]
    for i in range(16):
        day=i<8
        selected=i in (0,1,2,3,4,5,8,9)
        status=('published' if i in (0,1,2,4,8) else 'not_observed' if i in (3,5,9) else 'unselected') if selected else 'unselected'
        rows.append(Round(i,'day' if day else 'night',selected,'obs-'+str(i%3),'root-'+str(i%2),status))
    return audit(rows)

if __name__=='__main__': print(json.dumps(demo(),indent=2))
