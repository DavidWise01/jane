"""JANE 200 — validation-set selection audit; synthetic fixtures, no causal inference."""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def digest(v):
    return sha256(canonical(v).encode()).hexdigest()


def ratio(a, b):
    if b <= 0:
        return None
    q = Fraction(a, b)
    return {'n': q.numerator, 'd': q.denominator, 'percent': round(100 * float(q), 5)}


@dataclass(frozen=True)
class Case:
    ident: str
    stratum: str
    prediction: int
    label: int | None
    ancestry: str
    def __post_init__(self):
        if not all(isinstance(x, str) and x for x in (self.ident, self.stratum, self.ancestry)):
            raise ValueError('invalid identity')
        if type(self.prediction) is not int or self.prediction not in (0, 1):
            raise ValueError('invalid prediction')
        if self.label is not None and (type(self.label) is not int or self.label not in (0, 1)):
            raise ValueError('invalid label')


@dataclass(frozen=True)
class Plan:
    name: str
    included: tuple[str, ...]
    declared_population: tuple[str, ...]
    declared_selection: str
    witness_root: str
    upstream_root: str
    probability_by_stratum: tuple[tuple[str, int, int], ...]
    def __post_init__(self):
        if not all(isinstance(x, str) and x for x in (self.name, self.declared_selection, self.witness_root, self.upstream_root)):
            raise ValueError('invalid plan')
        if len(set(self.included)) != len(self.included) or len(set(self.declared_population)) != len(self.declared_population):
            raise ValueError('duplicate ids')
        if not self.declared_population or any(not isinstance(x, str) or not x for x in self.included + self.declared_population):
            raise ValueError('invalid sampling frame')
        names = []
        for name, numerator, denominator in self.probability_by_stratum:
            if not isinstance(name, str) or not name or type(numerator) is not int or type(denominator) is not int or denominator <= 0 or numerator < 0 or numerator > denominator:
                raise ValueError('invalid inclusion probability')
            names.append(name)
        if len(set(names)) != len(names):
            raise ValueError('duplicate strata probability')


class FLAY200:
    def __init__(self, cases):
        cases = tuple(cases)
        if not cases or len(cases) > 20000 or not all(isinstance(x, Case) for x in cases):
            raise ValueError('invalid population')
        if len({x.ident for x in cases}) != len(cases):
            raise ValueError('duplicate case')
        self.cases = tuple(sorted(cases, key=lambda c: c.ident))
        self.frozen_digest = digest([c.__dict__ for c in self.cases])
        self.history = []
        self._append('FREEZE', {'population_digest': self.frozen_digest})

    def _append(self, kind, body):
        event = {'seq': len(self.history), 'kind': kind, 'body': body,
                 'prev': self.history[-1]['hash'] if self.history else '0' * 64}
        event['hash'] = digest(event)
        self.history.append(event)

    def verify_chain(self):
        prev = '0' * 64
        for i, event in enumerate(self.history):
            if (event.get('seq') != i or event.get('prev') != prev or
                event.get('hash') != digest({k: v for k, v in event.items() if k != 'hash'})):
                return False
            prev = event['hash']
        return True

    def audit(self, plan):
        if not isinstance(plan, Plan):
            raise TypeError('plan required')
        cases = {x.ident: x for x in self.cases}
        frame = set(plan.declared_population)
        selected = set(plan.included)
        if frame != set(cases):
            raise ValueError('declared population does not equal frozen population')
        if not selected <= frame:
            raise ValueError('selected case outside population')
        pmap = {s: Fraction(n, d) for s, n, d in plan.probability_by_stratum}
        if set(pmap) != {x.stratum for x in self.cases}:
            raise ValueError('inclusion probabilities incomplete')
        observed = [cases[k] for k in sorted(selected)]
        known = [x for x in observed if x.label is not None]
        missing_labels = [x for x in observed if x.label is None]
        correct = sum(x.prediction == x.label for x in known)
        n = len(self.cases)
        excluded = sorted(frame - selected)
        total_known = len(known)
        stratum_summary = []
        for stratum in sorted(pmap):
            pop = [x for x in self.cases if x.stratum == stratum]
            incl = [x for x in pop if x.ident in selected]
            labelled = [x for x in incl if x.label is not None]
            successes = sum(x.prediction == x.label for x in labelled)
            stratum_summary.append({'name': stratum, 'population': len(pop), 'selected': len(incl),
                                    'labeled': len(labelled), 'correct': successes,
                                    'observed_accuracy': ratio(successes, len(labelled)),
                                    'coverage': ratio(len(incl), len(pop)),
                                    'declared_inclusion_probability': ratio(pmap[stratum].numerator, pmap[stratum].denominator),
                                    'positivity': pmap[stratum] > 0})
        no_support = [s['name'] for s in stratum_summary if s['labeled'] == 0 or not s['positivity']]
        weighted = None
        if not no_support:
            weighted_fraction = sum((Fraction(s['population'], n) * Fraction(s['correct'], s['labeled']) for s in stratum_summary), Fraction(0))
            weighted = ratio(weighted_fraction.numerator, weighted_fraction.denominator)
        # Only the known, selected labels constrain factual population correctness.
        bound = {'lower': ratio(correct, n), 'upper': ratio(correct + n - total_known, n)}
        roots = sorted({x.ancestry for x in known})
        known_full_accuracy = None
        if all(x.label is not None for x in self.cases):
            known_full_accuracy = ratio(sum(x.prediction == x.label for x in self.cases), n)
        if no_support:
            verdict = 'NO_STRATUM_SUPPORT'
        elif any(s['selected'] * n != len(selected) * s['population'] for s in stratum_summary):
            verdict = 'SELECTION_COVERAGE_IMBALANCE'
        else:
            verdict = 'COVERAGE_BALANCED_NOT_PROVEN_RANDOM'
        if len(roots) < 2:
            flags = ['INSUFFICIENT_DECLARED_SOURCE_ANCESTRY']
        else:
            flags = []
        if missing_labels:
            flags.append('MISSING_VALIDATION_LABELS')
        if any(p == 0 for p in pmap.values()):
            flags.append('POSITIVITY_FAILURE')
        result = {'experiment': 'JANE-200', 'verdict': verdict, 'plan': plan.name,
                  'declared_selection': plan.declared_selection, 'frozen_digest': self.frozen_digest,
                  'sampling_plan_digest': digest(plan.__dict__), 'population': n,
                  'selected': len(selected), 'excluded_ids': excluded,
                  'labeled_selected': total_known, 'observed_correct': correct,
                  'selected_accuracy': ratio(correct, total_known),
                  'conditional_stratified_estimate': weighted,
                  'factual_bounds_from_selected_labels': bound,
                  'population_truth_in_synthetic_fixture': known_full_accuracy,
                  'strata': stratum_summary, 'source_roots': roots,
                  'witness_root': plan.witness_root, 'upstream_root': plan.upstream_root,
                  'flags': flags, 'population_generalization_proven': False,
                  'random_selection_verified': False, 'parent': 'FROZEN', 'learning_applied': False,
                  'caveat': 'A declared random process and a point estimate do not certify random selection, independence, or real-world generalization.'}
        result['digest'] = digest(result)
        self._append('AUDIT', {'plan_digest': result['sampling_plan_digest'], 'result_digest': result['digest']})
        return result


def fixture():
    cases = tuple(Case(f'{i:03d}', 'EASY' if i < 8 else 'HARD',
                       1 if i < 8 else 0, 1, 'lab-A' if i % 2 == 0 else 'lab-B') for i in range(16))
    ids = tuple(c.ident for c in cases)
    biased = Plan('cherry_picked', ids[:8], ids, 'selected_favorable_only', 'witness-X', 'owned-corpus',
                  (('EASY', 1, 1), ('HARD', 0, 1)))
    balanced = Plan('balanced_fixture', tuple(ids[i] for i in (0, 2, 4, 6, 8, 10, 12, 14)), ids,
                    'declared_stratified_selection_not_verified', 'witness-Y', 'owned-corpus',
                    (('EASY', 1, 2), ('HARD', 1, 2)))
    return cases, biased, balanced


if __name__ == '__main__':
    cases, biased, balanced = fixture()
    flay = FLAY200(cases)
    print(json.dumps({'biased': flay.audit(biased), 'balanced': flay.audit(balanced),
                      'local_audit_valid': flay.verify_chain()}, indent=2))