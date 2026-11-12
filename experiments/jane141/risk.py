"""JANE 141: severity-aware, cohort-limited branch assessment.

Synthetic fixtures only. Budget declared before evaluate; immutable data classes;
no learning or activation. Checks risk, cohort shifts and ancestor leakage.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json

CHRONOS = '{{ 2026.11.12 }}{{ 09.00.00 }}{{ 123.45.56 }}'


def digest(obj):
    return sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class Case:
    case_id: str
    cohort: str
    root: str
    truth: bool
    parent: bool | None
    child: bool | None
    severity: int
    reversibility: int
    evidence_hash: str
    split: str = 'holdout'


@dataclass(frozen=True)
class Budget:
    overall_max_cost: int
    cohort_max_cost: tuple[tuple[str, int], ...]
    max_new_severe_errors: int
    severe_threshold: int = 8
    min_cases_per_cohort: int = 2

    def __post_init__(self):
        if self.overall_max_cost < 0 or self.max_new_severe_errors < 0 or not 1 <= self.severe_threshold <= 100:
            raise ValueError('invalid budget')
        if self.min_cases_per_cohort < 1 or len(set(k for k, _ in self.cohort_max_cost)) != len(self.cohort_max_cost):
            raise ValueError('invalid cohort budget')
        if any(not k or value < 0 for k, value in self.cohort_max_cost):
            raise ValueError('invalid cohort limit')


class Flay141:
    def __init__(self, budget: Budget, parent_hash: str = 'f' * 64, chronos: str = CHRONOS):
        if len(parent_hash) != 64 or not chronos:
            raise ValueError('frozen parent required')
        self.budget = budget
        self.parent_hash = parent_hash
        self.chronos = chronos
        self.active = 'frozen_parent'
        self.events = []
        self._append('DECLARE_BUDGET', {'budget': self._budget_json()})

    def _budget_json(self):
        return dict(overall_max_cost=self.budget.overall_max_cost,
                    cohort_max_cost=list(self.budget.cohort_max_cost),
                    max_new_severe_errors=self.budget.max_new_severe_errors,
                    severe_threshold=self.budget.severe_threshold,
                    min_cases_per_cohort=self.budget.min_cases_per_cohort)

    def _append(self, kind, data):
        event = {'seq': len(self.events), 'kind': kind, 'data': data,
                 'prev': self.events[-1]['head'] if self.events else '0'*64}
        event['head'] = digest(event)
        self.events.append(event)

    def evaluate(self, cases, known_training_hashes=()):
        cases = tuple(cases)
        if not 1 <= len(cases) <= 256 or len({c.case_id for c in cases}) != len(cases):
            raise ValueError('empty, duplicate or oversized case set')
        if any(not c.case_id or not c.cohort or not c.root or c.split != 'holdout' or
               not isinstance(c.truth, bool) or
               (c.parent is not None and not isinstance(c.parent, bool)) or
               (c.child is not None and not isinstance(c.child, bool)) or
               not 1 <= c.severity <= 10 or not 1 <= c.reversibility <= 5 or
               len(c.evidence_hash) != 64 or any(x not in '0123456789abcdef' for x in c.evidence_hash)
               for c in cases):
            raise ValueError('invalid case')
        if any(c.evidence_hash in known_training_hashes for c in cases):
            self._append('QUARANTINE', {'reason': 'HOLDOUT_LEAKAGE', 'n': len(cases)})
            return {'status': 'HOLDOUT_LEAKAGE', 'learning_applied': False, 'jane_decision': 'UNDECIDED'}

        limits = dict(self.budget.cohort_max_cost)
        names = {c.cohort for c in cases}
        if names != set(limits):
            return self._short_circuit('INCOMPLETE_COHORT_POLICY', len(cases))
        if any(sum(c.cohort == name for c in cases) < self.budget.min_cases_per_cohort for name in names):
            return self._short_circuit('INSUFFICIENT_COHORT_COVERAGE', len(cases))
        if any(c.parent is None or c.child is None for c in cases):
            return self._short_circuit('ABSTENTION_REVIEW', len(cases))

        summaries = []
        parent_cost = child_cost = new_severe = 0
        for cohort in sorted(names):
            cc = [c for c in cases if c.cohort == cohort]
            p = sum((c.severity*c.reversibility) for c in cc if c.parent != c.truth)
            n = sum((c.severity*c.reversibility) for c in cc if c.child != c.truth)
            new = sum(1 for c in cc if c.parent == c.truth and c.child != c.truth and
                      c.severity >= self.budget.severe_threshold)
            parent_cost += p
            child_cost += n
            new_severe += new
            summaries.append({'cohort': cohort, 'cases': len(cc), 'parent_cost': p,
                              'child_cost': n, 'new_severe_errors': new,
                              'budget': limits[cohort], 'within_budget': n <= limits[cohort],
                              'net_cost_improvement': p-n})
        if new_severe > self.budget.max_new_severe_errors:
            status = 'BLOCK_NEW_SEVERE_ERRORS'
        elif child_cost > self.budget.overall_max_cost:
            status = 'BLOCK_OVERALL_RISK'
        elif any(not s['within_budget'] for s in summaries):
            status = 'BLOCK_COHORT_RISK'
        elif child_cost < parent_cost:
            status = 'JANE_REVIEW_CANDIDATE'
        else:
            status = 'NO_RISK_IMPROVEMENT'
        result = {'version': 'JANE-141', 'chronos': self.chronos, 'parent_hash': self.parent_hash,
                  'budget_digest': digest(self._budget_json()), 'n': len(cases),
                  'parent_cost': parent_cost, 'child_cost': child_cost,
                  'new_severe_errors': new_severe, 'cohorts': summaries, 'status': status,
                  'active': self.active, 'learning_applied': False, 'jane_decision': 'UNDECIDED',
                  'caveat': 'Synthetic impact weights, not calibrated real-world harm or causal estimates.'}
        result['digest'] = digest(result)
        self._append('COMPARE', {'result_digest': result['digest'], 'status': status})
        return result

    def _short_circuit(self, status, n):
        self._append('ABSTAIN', {'status': status, 'n': n})
        return {'status': status, 'learning_applied': False, 'jane_decision': 'UNDECIDED'}

    def audit(self, retained_head=None):
        prev = '0'*64
        for i, event in enumerate(self.events):
            if event['seq'] != i or event['prev'] != prev or digest({k: v for k, v in event.items() if k != 'head'}) != event['head']:
                return 'TAMPERED'
            prev = event['head']
        return 'EXTERNAL_HEAD_MISMATCH' if retained_head is not None and retained_head != prev else 'VALID_LOCAL_CHAIN'


def fixture():
    policy = Budget(overall_max_cost=12, cohort_max_cost=(('routine', 12), ('critical', 0)),
                    max_new_severe_errors=0, severe_threshold=8)
    cases = [Case('R'+str(i), 'routine', 'external:r', True, False, True, 2, 1, f'{i+1:064x}') for i in range(6)]
    cases.extend(Case('C'+str(i), 'critical', 'external:c', True, True, False, 10, 5, f'{i+50:064x}') for i in range(2))
    flay = Flay141(policy)
    return flay, flay.evaluate(cases)

if __name__ == '__main__':
    obj, result = fixture()
    print(json.dumps({'result': result, 'audit': obj.audit()}, indent=2))
