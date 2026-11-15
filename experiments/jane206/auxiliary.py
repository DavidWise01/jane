"""JANE 206: exact binary reconstruction with adversarial auxiliary knowledge.

Fixture-only exhaustive verifier; not a privacy guarantee for real deployments.
"""
from __future__ import annotations
import hashlib
import itertools
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


def canon(o):
    return json.dumps(o,sort_keys=True,separators=(',',':')).encode()


def digest(o):
    return hashlib.sha256(canon(o)).hexdigest()


@dataclass(frozen=True)
class Query:
    mask: tuple[int,...]
    total: int

    def __post_init__(self):
        if not self.mask or any(type(x) is not int or x not in (0,1) for x in self.mask):
            raise ValueError('invalid mask')
        if type(self.total) is not int or not 0 <= self.total <= sum(self.mask):
            raise ValueError('invalid sum')

    def matches(self, bits):
        return sum(a*b for a,b in zip(self.mask,bits)) == self.total


@dataclass(frozen=True)
class Fact:
    index: int
    value: int
    root: str
    source: str

    def __post_init__(self):
        if type(self.index) is not int or self.index < 0 or type(self.value) is not int or self.value not in (0,1):
            raise ValueError('invalid auxiliary fact')
        if not self.root or not self.source:
            raise ValueError('missing fact provenance')


class FLAY206:
    def __init__(self,n:int,db:str=':memory:',max_n:int=18):
        if type(n) is not int or not 1 <= n <= max_n:
            raise ValueError('unsupported binary dimension')
        self.n=n
        self.db=sqlite3.connect(db)
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, prev TEXT NOT NULL, event TEXT NOT NULL, hash TEXT NOT NULL)')
        self.db.commit()
        self.queries=[]
        self.facts=[]

    def close(self):
        self.db.close()

    def _append(self,event):
        last=self.db.execute('SELECT hash FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
        prev=last[0] if last else '0'*64
        serialized=canon(event).decode()
        head=digest({'prev':prev,'event':event})
        self.db.execute('INSERT INTO audit(prev,event,hash) VALUES(?,?,?)',(prev,serialized,head))
        self.db.commit()
        return head

    def verify_chain(self):
        previous='0'*64
        for prev,raw,head in self.db.execute('SELECT prev,event,hash FROM audit ORDER BY seq'):
            if prev!=previous or digest({'prev':prev,'event':json.loads(raw)})!=head:
                return False
            previous=head
        return True

    def _validate_query(self,q):
        if not isinstance(q,Query) or len(q.mask)!=self.n:
            raise ValueError('query length mismatch')

    def _validate_fact(self,f):
        if not isinstance(f,Fact) or f.index>=self.n:
            raise ValueError('auxiliary index mismatch')

    def candidates(self,queries=None,facts=None):
        qs=self.queries if queries is None else queries
        fs=self.facts if facts is None else facts
        for q in qs: self._validate_query(q)
        for f in fs: self._validate_fact(f)
        return [b for b in itertools.product((0,1),repeat=self.n) if all(q.matches(b) for q in qs) and all(b[f.index]==f.value for f in fs)]

    def _report(self,before,after,action):
        fixed=[i for i in range(self.n) if after and len({x[i] for x in after})==1]
        return {'action':action,'before':len(before),'after':len(after),'fixed_indices':fixed,
                'fully_reconstructed':len(after)==1,'inconsistent':len(after)==0,
                'candidate_digest':digest(after),'ancestry_roots':sorted({f.root for f in self.facts}),
                'limitations':'Enumerated binary fixture only; external knowledge and custody are declared, not independently verified.'}

    def add_query(self,q,allow_reconstruction=False):
        self._validate_query(q)
        before=self.candidates()
        after=self.candidates(self.queries+[q],self.facts)
        if not after:
            return self._report(before,after,'REJECT_CONTRADICTORY_QUERY')
        if len(after)==1 and len(before)>1 and not allow_reconstruction:
            return self._report(before,after,'BLOCK_RECONSTRUCTING_QUERY')
        if len(after)<len(before) and any(len({b[i] for b in before})>1 and len({b[i] for b in after})==1 for i in range(self.n)) and not allow_reconstruction:
            return self._report(before,after,'BLOCK_INDIVIDUAL_DISCLOSURE')
        self.queries.append(q)
        self._append({'kind':'query','mask':q.mask,'total':q.total})
        return self._report(before,after,'QUERY_RETAINED')

    def analyze_auxiliary(self,f:Fact,allow_risk=False):
        self._validate_fact(f)
        before=self.candidates()
        after=self.candidates(self.queries,self.facts+[f])
        if not after: return self._report(before,after,'AUXILIARY_CONTRADICTS_OBSERVATIONS')
        already={x.index:x.value for x in self.facts}
        if f.index in already and already[f.index]!=f.value:
            return self._report(before,after,'AUXILIARY_CONFLICT')
        if f in self.facts: return self._report(before,after,'AUXILIARY_DUPLICATE')
        newly_fixed=[i for i in range(self.n) if len({b[i] for b in before})>1 and len({b[i] for b in after})==1]
        if len(after)==1 and len(before)>1:
            verdict='AUXILIARY_COMPLETES_RECONSTRUCTION'
        elif len(newly_fixed)>1:
            verdict='AUXILIARY_EXPOSES_ADDITIONAL_COORDINATES'
        else:
            verdict='AUXILIARY_CONSTRAINS_CANDIDATES'
        report=self._report(before,after,verdict)
        report['newly_fixed']=newly_fixed
        report['fact_provenance']={'root':f.root,'source':f.source}
        if allow_risk or verdict=='AUXILIARY_CONSTRAINS_CANDIDATES':
            self.facts.append(f)
            self._append({'kind':'auxiliary','index':f.index,'value':f.value,'root':f.root,'source':f.source,'verdict':verdict})
            report['retained']=True
        else:
            report['retained']=False
        return report


def fixture():
    f=FLAY206(4)
    for mask in ((1,1,0,0),(0,1,1,0),(0,0,1,1)):
        assert f.add_query(Query(mask,1))['action']=='QUERY_RETAINED'
    before=f.candidates()
    result=f.analyze_auxiliary(Fact(0,1,'external-root','public-register'))
    out={'name':'JANE 206','invariant':'Multiple compatible records != privacy against auxiliary knowledge',
         'before_candidates':[list(x) for x in before], 'auxiliary_result':result,
         'retained_count':len(f.candidates()),'audit_integrity':f.verify_chain(),
         'parent_activated':False}
    f.close()
    return out

if __name__=='__main__':
    print(json.dumps(fixture(),indent=2,sort_keys=True))