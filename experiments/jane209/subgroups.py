"""JANE 209: deterministic subgroup calibration audit (synthetic evidence only)."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def digest(x):
    return sha256(canonical(x).encode()).hexdigest()


@dataclass(frozen=True)
class Group:
    name: str
    n: int
    successes: int
    root: str

    def as_dict(self):
        return {'name': self.name, 'n': self.n, 'successes': self.successes, 'root': self.root}


@dataclass(frozen=True)
class Window:
    label: str
    start: int
    end: int
    population: str
    instrument: str
    groups: tuple[Group, ...]

    def as_dict(self):
        return {'label': self.label, 'start': self.start, 'end': self.end,
                'population': self.population, 'instrument': self.instrument,
                'groups': [g.as_dict() for g in self.groups]}


def checked(w: Window):
    if not isinstance(w, Window) or not isinstance(w.label, str) or not w.label.strip():
        raise ValueError('INVALID_WINDOW')
    if type(w.start) is not int or type(w.end) is not int or w.start > w.end:
        raise ValueError('INVALID_TIME')
    if not isinstance(w.population, str) or not w.population.strip():
        raise ValueError('INVALID_POPULATION')
    if not isinstance(w.instrument, str) or not w.instrument.strip():
        raise ValueError('INVALID_INSTRUMENT')
    if not isinstance(w.groups, tuple) or not w.groups:
        raise ValueError('EMPTY_GROUPS')
    names = set()
    for g in w.groups:
        if not isinstance(g, Group) or not isinstance(g.name, str) or not g.name.strip():
            raise ValueError('INVALID_GROUP')
        if g.name in names:
            raise ValueError('DUPLICATE_GROUP')
        names.add(g.name)
        if type(g.n) is not int or type(g.successes) is not int or g.n < 0 or not 0 <= g.successes <= g.n:
            raise ValueError('INVALID_COUNTS')
        if not isinstance(g.root, str) or not g.root.strip():
            raise ValueError('INVALID_ROOT')
    return {g.name: g for g in w.groups}


def ratio(x: Fraction | None):
    if x is None:
        return None
    return {'numerator': x.numerator, 'denominator': x.denominator, 'decimal': round(float(x), 6)}


class FLAY209:
    """Pure auditable comparison; never modifies the supplied windows."""
    def __init__(self, tolerance=Fraction(1, 10), min_n=5, max_age=30):
        if not isinstance(tolerance, Fraction) or not 0 <= tolerance <= 1:
            raise ValueError('INVALID_TOLERANCE')
        if type(min_n) is not int or min_n < 1:
            raise ValueError('INVALID_SAMPLE_FLOOR')
        if type(max_age) is not int or max_age < 0:
            raise ValueError('INVALID_MAX_AGE')
        self.tolerance, self.min_n, self.max_age = tolerance, min_n, max_age

    def audit(self, baseline: Window, current: Window):
        b, c = checked(baseline), checked(current)
        before = (digest(baseline.as_dict()), digest(current.as_dict()))
        reasons = []
        if baseline.end > current.start:
            reasons.append('WINDOW_OVERLAP_OR_BACKDATED')
        if current.start - baseline.end > self.max_age:
            reasons.append('STALE_BASELINE')
        if baseline.population != current.population:
            reasons.append('POPULATION_MISMATCH')
        if baseline.instrument != current.instrument:
            reasons.append('INSTRUMENT_MISMATCH')
        if set(b) != set(c):
            reasons.append('SUBGROUP_COVERAGE_MISMATCH')
        names = sorted(set(b) | set(c))
        all_b = sum(g.n for g in b.values())
        all_c = sum(g.n for g in c.values())
        pool_b = Fraction(sum(g.successes for g in b.values()), all_b) if all_b else None
        pool_c = Fraction(sum(g.successes for g in c.values()), all_c) if all_c else None
        rows = []
        rate_drift = False
        composition_drift = False
        roots_b = [g.root for g in b.values()]
        roots_c = [g.root for g in c.values()]
        if len(set(roots_b)) < len(roots_b) or len(set(roots_c)) < len(roots_c):
            reasons.append('SHARED_DECLARED_ANCESTRY')
        if all_b == 0 or all_c == 0:
            reasons.append('EMPTY_WINDOW')
        for name in names:
            x, y = b.get(name), c.get(name)
            rb = Fraction(x.successes, x.n) if x and x.n else None
            rc = Fraction(y.successes, y.n) if y and y.n else None
            wb = Fraction(x.n, all_b) if x and all_b else None
            wc = Fraction(y.n, all_c) if y and all_c else None
            delta = rc-rb if rb is not None and rc is not None else None
            if x is None or y is None or x.n < self.min_n or y.n < self.min_n:
                reasons.append('INSUFFICIENT_SUBGROUP_SUPPORT')
            if delta is not None and abs(delta) > self.tolerance:
                rate_drift = True
            if wb is not None and wc is not None and abs(wb-wc) > self.tolerance:
                composition_drift = True
            rows.append({'group': name, 'baseline_n': x.n if x else None,
                         'current_n': y.n if y else None, 'baseline_rate': ratio(rb),
                         'current_rate': ratio(rc), 'rate_delta': ratio(delta),
                         'baseline_weight': ratio(wb), 'current_weight': ratio(wc),
                         'baseline_root': x.root if x else None,
                         'current_root': y.root if y else None})
        standard_b, standard_c = None, None
        if all_b and all(name in c and c[name].n for name in b):
            standard_b = sum((Fraction(g.successes, all_b) for g in b.values()), Fraction(0))
            standard_c = sum((Fraction(b[name].n, all_b) * Fraction(c[name].successes, c[name].n)
                              for name in b), Fraction(0))
        if rate_drift:
            reasons.append('SUBGROUP_RATE_DRIFT')
        if composition_drift:
            reasons.append('COMPOSITION_SHIFT')
        if pool_b is not None and pool_c is not None and abs(pool_b-pool_c) <= self.tolerance and rate_drift:
            reasons.append('AGGREGATE_MASKED_SUBGROUP_DRIFT')
        blockers = {'WINDOW_OVERLAP_OR_BACKDATED', 'STALE_BASELINE', 'POPULATION_MISMATCH',
                    'INSTRUMENT_MISMATCH', 'SUBGROUP_COVERAGE_MISMATCH',
                    'SHARED_DECLARED_ANCESTRY', 'EMPTY_WINDOW', 'INSUFFICIENT_SUBGROUP_SUPPORT',
                    'SUBGROUP_RATE_DRIFT', 'COMPOSITION_SHIFT'}
        verdict = ('TRANSFER_WITHHELD' if blockers.intersection(reasons)
                   else 'CONDITIONAL_SUBGROUP_STABILITY_FIXTURE')
        result = {'experiment': 'JANE 209', 'verdict': verdict,
                  'reasons': sorted(set(reasons)), 'baseline_digest': before[0],
                  'current_digest': before[1], 'baseline_overall': ratio(pool_b),
                  'current_overall': ratio(pool_c), 'standardized_baseline': ratio(standard_b),
                  'standardized_current': ratio(standard_c), 'groups': rows,
                  'policy': {'tolerance': ratio(self.tolerance), 'minimum_per_group': self.min_n,
                             'maximum_baseline_age': self.max_age},
                  'claim_limit': 'Fixture rates and declared ancestry only; no measured real-world calibration.'}
        assert before == (digest(baseline.as_dict()), digest(current.as_dict()))
        result['audit_digest'] = digest(result)
        return result


def make_window(label, start, end, pairs, population='beacon-fixture', instrument='proxy-v1'):
    return Window(label, start, end, population, instrument,
                  tuple(Group(name, n, hit, f'root-{name}') for name, n, hit in pairs))


def fixture(scenario='masked'):
    b = make_window('baseline', 80, 100, [('A', 10, 9), ('B', 10, 1)])
    c = make_window('current', 110, 120, [('A', 10, 6), ('B', 10, 4)])
    if scenario == 'stable':
        c = make_window('current', 110, 120, [('A', 10, 9), ('B', 10, 1)])
    elif scenario == 'composition':
        b = make_window('baseline', 80, 100, [('A', 40, 32), ('B', 10, 2)])
        c = make_window('current', 110, 120, [('A', 10, 8), ('B', 40, 8)])
    elif scenario == 'missing_group':
        c = make_window('current', 110, 120, [('A', 10, 6)])
    elif scenario == 'underpowered':
        c = make_window('current', 110, 120, [('A', 19, 17), ('B', 1, 0)])
    elif scenario == 'shared_root':
        c = Window(c.label, c.start, c.end, c.population, c.instrument,
                   (Group('A', 10, 9, 'shared'), Group('B', 10, 1, 'shared')))
    elif scenario == 'stale':
        c = make_window('current', 150, 160, [('A', 10, 9), ('B', 10, 1)])
    elif scenario != 'masked':
        raise ValueError('UNKNOWN_SCENARIO')
    return b,c


def demonstration():
    return {s: FLAY209().audit(*fixture(s)) for s in
            ('masked', 'stable', 'composition', 'missing_group', 'underpowered', 'shared_root', 'stale')}


if __name__ == '__main__':
    print(json.dumps(demonstration(), indent=2, sort_keys=True))
