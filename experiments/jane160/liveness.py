"""JANE 160 — finite-state fairness and liveness, observational only.

The analyzer models a transition system as a finite total directed graph; every
infinite execution eventually remains in an SCC. Fairness is evaluated on
repeatable closed walks (lassos), not presumed from enabledness.
"""
from dataclasses import dataclass
from collections import deque
from hashlib import sha256
import json


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def hash_obj(obj):
    return sha256(canonical(obj).encode()).hexdigest()


@dataclass(frozen=True)
class Edge:
    source: str
    action: str
    target: str


class System:
    def __init__(self, states, edges, initial, goal, budget=10000):
        self.states = frozenset(states)
        self.edges = tuple(edges)
        self.initial = initial
        self.goal = frozenset(goal)
        self.budget = budget
        if not self.states or initial not in self.states or not self.goal <= self.states:
            raise ValueError('invalid states, initial or goal')
        if len(self.states) > 32 or len(self.edges) > 128 or not (1 <= budget <= 100000):
            raise ValueError('bound exceeded')
        if len({(e.source,e.action,e.target) for e in self.edges}) != len(self.edges):
            raise ValueError('duplicate edge')
        if any(e.source not in self.states or e.target not in self.states or not e.action for e in self.edges):
            raise ValueError('invalid edge')
        self.out = {s: sorted((e for e in self.edges if e.source==s), key=lambda e:(e.action,e.target)) for s in self.states}
        if any(not es for es in self.out.values()):
            raise ValueError('deadlock: supply an explicit stutter edge')

    def shortest(self, goal):
        queue=deque([(self.initial, [])]); seen={self.initial}; count=0
        while queue:
            s,path=queue.popleft(); count+=1
            if count>self.budget: return None, True
            if goal(s): return path,False
            for e in self.out[s]:
                if e.target not in seen:
                    seen.add(e.target); queue.append((e.target,path+[e]))
        return None,False

    def reachable(self):
        q=deque([self.initial]); seen={self.initial}
        while q:
            s=q.popleft()
            for e in self.out[s]:
                if e.target not in seen:
                    seen.add(e.target);q.append(e.target)
        return seen

    def enabled(self,s,action):
        return any(e.action==action for e in self.out[s])

    def find_lasso(self, fairness='none'):
        if fairness not in ('none','weak','strong'): raise ValueError('fairness')
        # Enumerate repeatable closed walks in non-goal states, bounding search.
        # A fair lasso's cycle may revisit vertices. For a finite graph, a fair
        # witness can be found by traversing all selected cyclic SCC edges.
        reachable=self.reachable(); candidates=sorted(reachable-self.goal)
        visits=0
        for origin in candidates:
            prefix,exhausted=self.shortest(lambda s:s==origin)
            if exhausted:return None,True
            # enumerate a walk that can return to origin, recording edges and visited vertices.
            queue=deque([(origin,[],frozenset([origin]))])
            visited=set()
            while queue:
                state,path,vertices=queue.popleft();visits+=1
                if visits>self.budget:return None,True
                # Canonicalize by edge subset, which captures enabled and taken actions
                key=(state,frozenset((e.source,e.action,e.target) for e in path))
                if key in visited:continue
                visited.add(key)
                for e in self.out[state]:
                    if e.target in self.goal:continue
                    cycle=path+[e]
                    if e.target==origin and self.fair_cycle(cycle,fairness):
                        return {'prefix':[x.__dict__ for x in prefix], 'cycle':[x.__dict__ for x in cycle],
                                'states':sorted({x.source for x in cycle}|{origin}), 'fairness':fairness},False
                    # Edge-set bound: no need to repeat an edge on a lasso candidate.
                    if (e.source,e.action,e.target) not in key[1]:
                        queue.append((e.target,cycle,vertices|{e.target}))
        return None,False

    def fair_cycle(self,cycle,fairness):
        if fairness=='none':return True
        states={e.source for e in cycle};taken={e.action for e in cycle}
        actions={e.action for s in states for e in self.out[s]}
        # weak: if action enabled in *every* state of repeating cycle it must occur
        # strong: if action enabled in *any* recurring state, it must occur
        for action in actions:
            required=(all(self.enabled(s,action) for s in states) if fairness=='weak'
                      else any(self.enabled(s,action) for s in states))
            if required and action not in taken:return False
        return True

    def analyze(self,fairness='none'):
        path,timeout=self.shortest(lambda s:s in self.goal)
        if timeout:return self.packet('INCONCLUSIVE_BUDGET',None,None,fairness)
        lasso,timeout=self.find_lasso(fairness)
        if timeout:return self.packet('INCONCLUSIVE_BUDGET',path,lasso,fairness)
        if path is None: status='GOAL_UNREACHABLE'
        elif lasso is None:status=('GUARANTEED_PROGRESS' if fairness=='none' else 'PROGRESS_UNDER_'+fairness.upper()+'_FAIRNESS')
        else:status='POSSIBLE_NOT_INEVITABLE'
        return self.packet(status,path,lasso,fairness)

    def packet(self,status,path,lasso,fairness):
        p=dict(experiment='JANE-160',status=status,fairness=fairness,
               progress_path=[e.__dict__ for e in path] if path is not None else None,
               nonprogress_lasso=lasso,initial=self.initial,goal=sorted(self.goal),
               states=sorted(self.states),edges=[e.__dict__ for e in self.edges],
               scope='finite explicit transition graph and specified fairness only',
               active='frozen_parent',learning_applied=False,independent_witness_increment=0)
        p['digest']=hash_obj(p)
        return p


def fixture():
    # A state with progress or infinite stutter; weak fairness disallows stutter forever.
    return System(['s0','goal'],[Edge('s0','stutter','s0'),Edge('s0','advance','goal'),Edge('goal','rest','goal')],'s0',['goal'])


def intermittent_fixture():
    # Advance is enabled at s0 but not s1, so weak fairness permits forever
    # switching s0/s1; strong fairness requires advance eventually.
    return System(['s0','s1','goal'],[
        Edge('s0','switch','s1'),Edge('s1','switch','s0'),Edge('s0','advance','goal'),
        Edge('goal','rest','goal')],'s0',['goal'])


def demo():
    f=fixture();i=intermittent_fixture()
    return dict(always_enabled={m:f.analyze(m) for m in ['none','weak','strong']},
                intermittently_enabled={m:i.analyze(m) for m in ['none','weak','strong']})

if __name__=='__main__':print(json.dumps(demo(),indent=2))