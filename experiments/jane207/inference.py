"""JANE 207: exact-rational, ancestry-aware probabilistic auxiliary evidence.

Illustrative probability models; calibration metadata is not independently certified.
"""
from __future__ import annotations
from fractions import Fraction
import hashlib
import json
import re

CANDIDATES = ('0101', '1010')
MAX_EVIDENCE = 32


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Fraction)):
        raise ValueError('rational required')
    try:
        out = Fraction(value)
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise ValueError('invalid rational') from exc
    if out < 0 or out > 1:
        raise ValueError('probability outside [0,1]')
    return out


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def validate_prior(prior):
    if not isinstance(prior, dict) or set(prior) != set(CANDIDATES):
        raise ValueError('prior must cover exactly both candidates')
    out = {key: rational(prior[key]) for key in CANDIDATES}
    if sum(out.values(), Fraction(0)) != 1:
        raise ValueError('prior must sum to one')
    return out


def validate_evidence(event):
    if not isinstance(event, dict):
        raise ValueError('evidence must be an object')
    required = {'id', 'root', 'proxy', 'calibration_n', 'likelihood'}
    if not required <= set(event):
        raise ValueError('incomplete evidence')
    for field in ('id', 'root', 'proxy'):
        val = event[field]
        if not isinstance(val, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,72}', val):
            raise ValueError('invalid ' + field)
    n = event['calibration_n']
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError('invalid calibration_n')
    if not isinstance(event['likelihood'], dict) or set(event['likelihood']) != set(CANDIDATES):
        raise ValueError('likelihood must cover both candidates')
    return {candidate: rational(event['likelihood'][candidate]) for candidate in CANDIDATES}


def audit(prior, evidence, *, min_calibration_n=20, threshold=Fraction(4, 5)):
    """Audit an illustrative two-candidate posterior, rejecting uncertain provenance.

    Evidence is accepted only if all declared roots are distinct and every
    calibration sample meets the declared minimum. These are policy checks,
    NOT verification of real independence or calibrated probability claims.
    """
    weights = validate_prior(prior)
    if isinstance(min_calibration_n, bool) or not isinstance(min_calibration_n, int) or min_calibration_n < 1:
        raise ValueError('invalid calibration minimum')
    threshold = rational(threshold)
    if not isinstance(evidence, list) or len(evidence) > MAX_EVIDENCE:
        raise ValueError('evidence must be bounded list')
    roots = set()
    ids = set()
    compiled = []
    for event in evidence:
        likelihoods = validate_evidence(event)
        if event['id'] in ids:
            raise ValueError('duplicate event ID')
        ids.add(event['id'])
        if event['root'] in roots:
            return _withhold('SHARED_ANCESTRY_WITHHELD', weights, evidence, 'A declared source root appears more than once')
        roots.add(event['root'])
        if event['calibration_n'] < min_calibration_n:
            return _withhold('INSUFFICIENT_CALIBRATION', weights, evidence, 'A declared calibration sample is below the policy minimum')
        compiled.append(likelihoods)
    weighted = dict(weights)
    for likelihoods in compiled:
        for candidate in CANDIDATES:
            weighted[candidate] *= likelihoods[candidate]
    total = sum(weighted.values(), Fraction(0))
    if total == 0:
        return _withhold('ZERO_LIKELIHOOD_CONFLICT', weights, evidence, 'No candidate has nonzero likelihood under the stated model')
    posterior = {candidate: weighted[candidate] / total for candidate in CANDIDATES}
    peak = max(posterior.values())
    if len([x for x in posterior.values() if x > 0]) == 1:
        verdict = 'MODEL_CONDITIONAL_POINT_MASS'
    elif peak >= threshold and peak > Fraction(1, 2):
        verdict = 'HIGH_CONFIDENCE_UNVERIFIED'
    elif posterior == weights:
        verdict = 'NO_UPDATE_FROM_DECLARED_EVIDENCE'
    else:
        verdict = 'PROBABILISTIC_INFERENCE_ONLY'
    return {
        'experiment': 207,
        'verdict': verdict,
        'posterior': {key: str(posterior[key]) for key in CANDIDATES},
        'maximum_probability': str(peak),
        'leading_candidates': [key for key in CANDIDATES if posterior[key] == peak],
        'evidence_count': len(evidence),
        'distinct_declared_roots': len(roots),
        'evidence_digest': digest({'prior': prior, 'evidence': evidence}),
        'limitations': ['Probabilities and calibration are supplied assumptions, not verified facts',
                        'Distinct root labels do not prove independent collection',
                        'Conditional point mass is not proof of true identity',
                        'This toy model contains exactly two candidate records']
    }


def _withhold(verdict, prior, evidence, reason):
    return {'experiment': 207, 'verdict': verdict, 'posterior': None,
            'maximum_probability': None, 'leading_candidates': [],
            'evidence_count': len(evidence), 'distinct_declared_roots': len({e.get('root') for e in evidence if isinstance(e, dict)}),
            'evidence_digest': digest({'prior': {k: str(v) for k,v in prior.items()}, 'evidence': evidence}),
            'reason': reason}


def fixture(mode='noisy'):
    prior = {'0101': '1/2', '1010': '1/2'}
    observation = {'id': 'proxy-1', 'root': 'sensor-fam-A', 'proxy': 'noisy-x0-reads-1',
                   'calibration_n': 100, 'likelihood': {'0101': '1/5', '1010': '9/10'}}
    second = {'id': 'proxy-2', 'root': 'sensor-fam-B', 'proxy': 'independent-proxy',
              'calibration_n': 80, 'likelihood': {'0101': '1/4', '1010': '3/4'}}
    if mode == 'noisy':
        return prior, [observation]
    if mode == 'additional':
        return prior, [observation, second]
    if mode == 'shared-root':
        second['root'] = observation['root']
        return prior, [observation, second]
    if mode == 'poor-calibration':
        observation['calibration_n'] = 3
        return prior, [observation]
    if mode == 'non-discriminating':
        observation['likelihood'] = {'0101': '1/2', '1010': '1/2'}
        return prior, [observation]
    if mode == 'point-mass':
        observation['likelihood'] = {'0101': '0', '1010': '1'}
        return prior, [observation]
    if mode == 'conflict':
        observation['likelihood'] = {'0101': '0', '1010': '0'}
        return prior, [observation]
    raise ValueError('unknown fixture mode')


if __name__ == '__main__':
    import sys
    modes = ['noisy', 'additional', 'shared-root', 'poor-calibration', 'non-discriminating', 'point-mass', 'conflict']
    print(json.dumps({'experiment': 207, 'cases': {mode: audit(*fixture(mode)) for mode in modes},
                      'frozen_parent': True, 'physical_measurements': False}, indent=2, sort_keys=True))