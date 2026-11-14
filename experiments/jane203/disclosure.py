"""JANE 203: conservative, append-only fixture accounting for adaptive holdout queries.
Policy credits are illustrative, NOT differential-privacy epsilon or information bounds.
"""
from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from pathlib import Path


def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()

class Rejected(ValueError): pass

@dataclass(frozen=True)
class Policy:
    holdout: tuple[str,...]
    budget: int = 12
    base_cost: int = 2
    overlap_cost: int = 1
    repeat_cost: int = 2
    def __post_init__(self):
        if not self.holdout or len(set(self.holdout))!=len(self.holdout) or any(not isinstance(x,str) or not x for x in self.holdout): raise Rejected('invalid holdout')
        if self.budget<0 or self.base_cost<=0 or self.overlap_cost<0 or self.repeat_cost<0: raise Rejected('invalid costs')

class FLAY203:
    def __init__(self,path,policy:Policy):
        self.policy=policy
        self.db=sqlite3.connect(str(path), isolation_level=None)
        self.db.execute('PRAGMA busy_timeout=3000')
        self.db.execute('CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY,v TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (n INTEGER PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL)')
        p=digest({'holdout':policy.holdout,'budget':policy.budget,'base':policy.base_cost,'overlap':policy.overlap_cost,'repeat':policy.repeat_cost})
        existing=self.db.execute("SELECT v FROM meta WHERE k='policy'").fetchone()
        if existing and existing[0]!=p:
            self.db.close()
            raise Rejected('POLICY_CHANGED')
        self.db.execute("INSERT OR IGNORE INTO meta VALUES('policy',?)",(p,))
    def close(self): self.db.close()
    def events(self):
        rows=self.db.execute('SELECT n,kind,body,previous,hash FROM events ORDER BY n').fetchall()
        prior='0'*64; result=[]
        for expect,(n,kind,body,previous,hash_) in enumerate(rows,1):
            try: parsed=json.loads(body)
            except (ValueError,TypeError): raise Rejected('CORRUPT_LOG') from None
            if n!=expect or previous!=prior or hash_!=digest({'n':n,'kind':kind,'body':parsed,'previous':prior}):raise Rejected('CORRUPT_LOG')
            result.append({'n':n,'kind':kind,'body':parsed,'hash':hash_}); prior=hash_
        return result
    def _insert(self,kind,body,history):
        n=len(history)+1; previous=history[-1]['hash'] if history else '0'*64
        hash_=digest({'n':n,'kind':kind,'body':body,'previous':previous})
        self.db.execute('INSERT INTO events VALUES(?,?,?,?,?)',(n,kind,canonical(body),previous,hash_))
        return {'n':n,'kind':kind,'body':body,'hash':hash_}
    def record(self,kind,**kwargs):
        if kind not in ('query','adapt','seal'): raise Rejected('UNKNOWN_EVENT')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            history=self.events(); queries=[e for e in history if e['kind']=='query']; cost_used=sum(e['body']['cost'] for e in queries)
            sealed=any(e['kind']=='seal' for e in history)
            if sealed: raise Rejected('SEALED_FINAL')
            if kind=='query':
                qid=kwargs.get('id'); model=kwargs.get('model'); items=kwargs.get('subset'); answer=kwargs.get('answer')
                if not isinstance(qid,str) or not qid or not isinstance(model,str) or not model: raise Rejected('INVALID_QUERY')
                if any(e['body']['id']==qid for e in queries): raise Rejected('DUPLICATE_QUERY')
                if not isinstance(items,(tuple,list)) or not items or len(set(items))!=len(items) or any(x not in self.policy.holdout for x in items): raise Rejected('INVALID_SUBSET')
                if not isinstance(answer,(int,float)) or isinstance(answer,bool) or not (0<=answer<=1):raise Rejected('INVALID_ANSWER')
                subset=sorted(items)
                overlap=max((len(set(subset)&set(e['body']['subset'])) for e in queries),default=0)
                repeated=any(subset==e['body']['subset'] for e in queries)
                cost=self.policy.base_cost+self.policy.overlap_cost*overlap+self.policy.repeat_cost*int(repeated)
                if cost_used+cost>self.policy.budget:raise Rejected('CUMULATIVE_BUDGET_EXCEEDED')
                body={'id':qid,'model':model,'subset':subset,'answer':float(answer),'cost':cost,'overlap':overlap,'repeated':repeated}
            elif kind=='adapt':
                model=kwargs.get('model'); based=kwargs.get('based_on')
                if not isinstance(model,str) or not model or not isinstance(based,(tuple,list)) or not based:raise Rejected('INVALID_ADAPTATION')
                known={e['body']['id'] for e in queries}
                if len(set(based))!=len(based) or not set(based)<=known:raise Rejected('UNKNOWN_FEEDBACK')
                body={'model':model,'based_on':sorted(based)}
            else:
                body={'final_model':kwargs.get('model')}
                if not isinstance(body['final_model'],str) or not body['final_model']:raise Rejected('INVALID_SEAL')
            entry=self._insert(kind,body,history)
            self.db.execute('COMMIT')
            return entry
        except BaseException:
            self.db.execute('ROLLBACK');raise
    def report(self):
        history=self.events(); queries=[e for e in history if e['kind']=='query']; adaptations=[e for e in history if e['kind']=='adapt']
        spent=sum(e['body']['cost'] for e in queries)
        seen=set().union(*(set(e['body']['subset']) for e in queries)) if queries else set()
        repeat=sum(e['body']['repeated'] for e in queries)
        return {'verdict':'ADAPTIVE_DISCLOSURE_RECORDED' if adaptations else 'DISCLOSURES_RECORDED','used':spent,'remaining':self.policy.budget-spent,'total_queries':len(queries),'reused_subsets':repeat,'adaptations':len(adaptations),'covered_cases':len(seen),'holdout_cases':len(self.policy.holdout),'sealed':any(e['kind']=='seal' for e in history),'root':history[-1]['hash'] if history else '0'*64,'limits':'Policy credits are illustrative only; no formal privacy, secrecy, or physical provenance guarantee.'}

def fixture(path=':memory:'):
    f=FLAY203(path,Policy(tuple(f'r{i:02}' for i in range(8))))
    traces=[]
    for q in [dict(id='q1',model='A',subset=['r00','r01','r02','r03'],answer=.75),dict(id='q2',model='B',subset=['r02','r03','r04'],answer=.67)]:
        traces.append(f.record('query',**q))
    traces.append(f.record('adapt',model='C',based_on=['q1','q2']))
    try: f.record('query',id='q3',model='C',subset=['r02','r03','r04'],answer=1)
    except Rejected as e: denied=str(e)
    summary=f.report();summary.update({'denied':denied,'events':traces});f.close()
    return summary

if __name__=='__main__': print(json.dumps(fixture(),indent=2))