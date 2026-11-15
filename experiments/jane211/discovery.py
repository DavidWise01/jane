"""JANE 211 — exact-binomial subgroup search and post-selection audit.

Synthetic fixture; binomial tests assume fixed independent Bernoulli observations
under a declared 1/2 null. Holm controls family-wise error under valid p values.
"""
from __future__ import annotations
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Sequence


class InvalidPlan(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True)
class Subgroup:
    group: str
    successes: int
    trials: int
    ancestry: str


@dataclass(frozen=True)
class Plan:
    family: tuple[str, ...]
    population: str
    alpha: float = 0.05
    null_probability: float = 0.5
    frozen: bool = True
    validation_id: str = 'sealed-final'


def exact_pvalue(successes: int, trials: int) -> float:
    """Two-sided exact binomial p-value with null probability 1/2."""
    if isinstance(successes, bool) or isinstance(trials, bool) or not isinstance(successes, int) or not isinstance(trials, int):
        raise InvalidPlan('integer counts required')
    if trials <= 0 or not (0 <= successes <= trials):
        raise InvalidPlan('invalid counts')
    k = min(successes, trials - successes)
    return min(1.0, 2 * sum(math.comb(trials, i) for i in range(k + 1)) / (2 ** trials))


def audit(plan: Plan, samples: Sequence[Subgroup], selected: str, *, validation=None):
    if not isinstance(plan, Plan) or not plan.frozen or not plan.population or not plan.validation_id:
        raise InvalidPlan('frozen plan required')
    if plan.null_probability != 0.5:
        raise InvalidPlan('this exact test requires null_probability=0.5')
    if not (0 < plan.alpha < 1) or not math.isfinite(plan.alpha):
        raise InvalidPlan('invalid alpha')
    if not plan.family or len(set(plan.family)) != len(plan.family) or any(not x for x in plan.family):
        raise InvalidPlan('family must have distinct named subgroups')
    if len(samples) != len(plan.family) or {x.group for x in samples} != set(plan.family):
        raise InvalidPlan('all prespecified subgroup tests must be reported')
    if len({x.group for x in samples}) != len(samples):
        raise InvalidPlan('duplicate subgroup')
    if selected not in plan.family:
        raise InvalidPlan('selected group outside family')
    if any(not isinstance(x.ancestry, str) or not x.ancestry for x in samples):
        raise InvalidPlan('declared ancestry required')
    raw = {x.group: exact_pvalue(x.successes, x.trials) for x in samples}
    ordered = sorted(raw, key=lambda name: (raw[name], name))
    m = len(ordered)
    adjusted = {}
    running = 0.0
    for index, name in enumerate(ordered):
        running = max(running, min(1., (m-index) * raw[name]))
        adjusted[name] = running
    rows = [{'group': g, 'successes': next(x.successes for x in samples if x.group == g),
             'trials': next(x.trials for x in samples if x.group == g),
             'raw_p': raw[g], 'holm_p': adjusted[g],
             'ancestry': next(x.ancestry for x in samples if x.group == g)} for g in plan.family]
    selected_row = next(row for row in rows if row['group'] == selected)
    verdict = 'EXPLORATORY_NOT_VALIDATED'
    final = None
    if validation is not None:
        if set(validation) != {'group', 'successes', 'trials', 'dataset_id', 'previously_exposed', 'selection_influenced'}:
            raise InvalidPlan('explicit validation schema required')
        if validation['group'] != selected or validation['dataset_id'] != plan.validation_id:
            raise InvalidPlan('validation not bound to selected group and sealed dataset')
        p = exact_pvalue(validation['successes'], validation['trials'])
        final = {'group': selected, 'p': p, 'successes': validation['successes'], 'trials': validation['trials']}
        if validation['previously_exposed'] or validation['selection_influenced']:
            verdict = 'VALIDATION_CONTAMINATED'
        elif p <= plan.alpha:
            verdict = 'INDEPENDENT_VALIDATION_CONDITIONAL'
        else:
            verdict = 'INDEPENDENT_VALIDATION_NOT_CONFIRMED'
    output = {'experiment': 211, 'plan_digest': digest(plan.__dict__), 'family_size': m,
              'selected': selected, 'selected_raw_p': selected_row['raw_p'],
              'selected_holm_p': selected_row['holm_p'], 'rows': rows,
              'selection_adjusted_discovery': selected_row['holm_p'] <= plan.alpha,
              'validation': final, 'verdict': verdict, 'frozen_parent': True,
              'limitations': 'Synthetic, fixed-hypothesis independent Bernoulli model; declared final-test separation is not externally verified.'}
    output['evidence_digest'] = digest(output)
    return output


def fixture():
    plan = Plan(family=tuple(f'G{i:02d}' for i in range(1, 21)), population='synthetic-20-group-population')
    samples = [Subgroup(g, 16 if i == 7 else (8 + (i % 3)), 16, f'scout-{i}') for i, g in enumerate(plan.family)]
    return plan, samples


def demo():
    p, s = fixture()
    result = {
      'exploratory': audit(p,s,'G08'),
      'validation_failed': audit(p,s,'G08',validation={'group':'G08','successes':8,'trials':16,'dataset_id':p.validation_id,'previously_exposed':False,'selection_influenced':False}),
      'validation_passed_fixture': audit(p,s,'G08',validation={'group':'G08','successes':16,'trials':16,'dataset_id':p.validation_id,'previously_exposed':False,'selection_influenced':False}),
      'validation_leaked': audit(p,s,'G08',validation={'group':'G08','successes':16,'trials':16,'dataset_id':p.validation_id,'previously_exposed':True,'selection_influenced':False}),
    }
    return result


if __name__ == '__main__':
    print(json.dumps(demo(), indent=2, sort_keys=True))