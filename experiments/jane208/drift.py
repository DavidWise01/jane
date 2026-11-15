"""JANE 208 — temporal and population calibration transfer audit.

Synthetic metadata is treated as a claim, never independent proof of calibration.
All probabilities are exact rational values. A withheld update returns no posterior.
"""
from __future__ import annotations
from fractions import Fraction
import hashlib
import json
import re

CANDIDATES = ('0101', '1010')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def probability(value):
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise ValueError('probability requires rational')
    try:
        v = Fraction(value)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError('bad probability') from exc
    if not 0 <= v <= 1:
        raise ValueError('probability outside [0,1]')
    return v


def natural(value, *, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('invalid nonnegative integer')
    return value


def token(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}', value):
        raise ValueError('invalid identifier')
    return value


def audit(prior, calibration, deployment, *, max_age=30, min_n=20, max_rate_gap=Fraction(1, 10)):
    """Validate transfer under declared policy; NEVER certify actual causal or calibration validity.

    calibration: id, root, population, from_day, to_day, n, rates,
                 likelihoods, snapshot_digest
    deployment:  day, population, observed_rates, calibration_id, artifact_digest
    Days are integer indices from a common frozen epoch, not trusted wall-clock proofs.
    Observed rates are an explicitly reported monitoring sample, not ground truth.
    """
    if not isinstance(prior, dict) or set(prior) != set(CANDIDATES):
        raise ValueError('prior keys')
    p = {k: probability(prior[k]) for k in CANDIDATES}
    if sum(p.values(), Fraction()) != 1:
        raise ValueError('prior sum')
    natural(max_age)
    natural(min_n, minimum=1)
    gap_cap = probability(max_rate_gap)
    if not isinstance(calibration, dict) or not isinstance(deployment, dict):
        raise ValueError('record type')
    creq = {'id','root','population','from_day','to_day','n','rates','likelihoods','snapshot_digest'}
    dreq = {'day','population','observed_rates','calibration_id','artifact_digest'}
    if not creq <= calibration.keys() or not dreq <= deployment.keys():
        raise ValueError('incomplete record')
    for key in ('id','root','population','snapshot_digest'):
        token(calibration[key])
    for key in ('population','calibration_id','artifact_digest'):
        token(deployment[key])
    start = natural(calibration['from_day'])
    end = natural(calibration['to_day'])
    day = natural(deployment['day'])
    n = natural(calibration['n'])
    if start > end:
        raise ValueError('reversed calibration window')
    if not isinstance(calibration['likelihoods'],dict) or set(calibration['likelihoods']) != set(CANDIDATES):
        raise ValueError('likelihood keys')
    likelihood = {k:probability(calibration['likelihoods'][k]) for k in CANDIDATES}
    if not isinstance(calibration['rates'],dict) or not isinstance(deployment['observed_rates'],dict):
        raise ValueError('rate objects required')
    if set(calibration['rates']) != {'positive'} or set(deployment['observed_rates']) != {'positive'}:
        raise ValueError('rate keys')
    base_rate = probability(calibration['rates']['positive'])
    observed_rate = probability(deployment['observed_rates']['positive'])
    frozen = digest({'prior': {k: str(p[k]) for k in CANDIDATES}, 'calibration':calibration, 'deployment':deployment,
                     'policy':{'max_age':max_age,'min_n':min_n,'max_rate_gap':str(gap_cap)}})
    age = day-end if day>=end else None
    rate_gap = abs(base_rate-observed_rate)
    common = dict(experiment=208, evidence_digest=frozen, calibration_window=[start,end], deployment_day=day,
                  calibration_n=n, population_from=calibration['population'], population_to=deployment['population'],
                  declared_rate_gap=str(rate_gap), age_days=age,
                  caveat='All measurements, dates, and provenance are self-reported fixture metadata; not authenticated externally')
    def withheld(code):
        return {**common, 'verdict':code, 'posterior':None, 'calibration_transfer_supported':False}
    if deployment['calibration_id'] != calibration['id']:
        return withheld('CALIBRATION_ID_MISMATCH')
    if deployment['artifact_digest'] != calibration['snapshot_digest']:
        return withheld('ARTIFACT_VERSION_MISMATCH')
    if day < end:
        return withheld('CALIBRATION_FROM_FUTURE')
    if n < min_n:
        return withheld('INSUFFICIENT_CALIBRATION')
    if age > max_age:
        return withheld('STALE_CALIBRATION')
    if deployment['population'] != calibration['population']:
        return withheld('POPULATION_TRANSFER_UNVERIFIED')
    if rate_gap > gap_cap:
        return withheld('MONITORING_SHIFT_DETECTED')
    weighted = {k:p[k]*likelihood[k] for k in CANDIDATES}
    denominator = sum(weighted.values(), Fraction())
    if denominator == 0:
        return withheld('ZERO_LIKELIHOOD_CONFLICT')
    posterior = {k:str(weighted[k]/denominator) for k in CANDIDATES}
    return {**common,'verdict':'CONDITIONAL_TRANSFER_FIXTURE','posterior':posterior,
            'calibration_transfer_supported':True,
            'limitations':['Matching metadata does not establish distributional equivalence',
                           'Single summary rate cannot rule out calibration drift or concept shift',
                           'Posterior is conditional on unverified likelihoods and prior']}


def fixture(scenario='current'):
    prior={'0101':'1/2','1010':'1/2'}
    cal={'id':'cal-A','root':'instrument-family-A','population':'lab-A','from_day':80,'to_day':100,'n':120,
         'rates':{'positive':'1/2'},'likelihoods':{'0101':'1/5','1010':'9/10'},'snapshot_digest':'sha256fixtureA'}
    dep={'day':110,'population':'lab-A','observed_rates':{'positive':'11/20'},
         'calibration_id':'cal-A','artifact_digest':'sha256fixtureA'}
    if scenario=='stale':dep['day']=180
    elif scenario=='population':dep['population']='lab-B'
    elif scenario=='monitoring-shift':dep['observed_rates']['positive']='9/10'
    elif scenario=='future':dep['day']=99
    elif scenario=='small':cal['n']=3
    elif scenario=='artifact':dep['artifact_digest']='sha256fixtureB'
    elif scenario=='identity':dep['calibration_id']='cal-B'
    elif scenario=='zero':cal['likelihoods']={'0101':'0','1010':'0'}
    elif scenario=='boundary':dep['day']=130;dep['observed_rates']['positive']='3/5'
    elif scenario!='current':raise ValueError('unknown fixture')
    return prior,cal,dep


def demo():
    result={}
    for mode in ('current','stale','population','monitoring-shift','future','small','artifact','identity','zero','boundary'):
        result[mode]=audit(*fixture(mode))
    return {'experiment':208,'invariant':'Past Calibration != Present Accuracy','fixtures':result,
            'frozen_parent':True, 'simulated_only':True}

if __name__=='__main__':
    print(json.dumps(demo(),indent=2,sort_keys=True))