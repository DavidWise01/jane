"""JANE 131: bounded additive-bias sensitivity experiment; offline only."""
from fractions import Fraction as F
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json,re
PAT=re.compile(r'^\{\{ - (\d{4}):(\d{2}):(\d{2}) \|\| (\d{2}):(\d{2}):(\d{2}) \|\| ([+-])(\d{1,3})\.(\d{2})\.(\d{2}) \|\| \}\}$')
def sweep(observed,bounds,chronos,offset,roots):
 o=F(observed);bs=tuple(bounds)
 m=PAT.fullmatch(chronos)
 if not m or not -840<=offset<=840:raise ValueError("chronos")
 v=m.groups()
 y,mo,d,h,mi,s=map(int,v[:6]);degree,arcmin,arcsec=map(int,v[7:])
 if degree>360 or arcmin>=60 or arcsec>=60 or degree==360 and (arcmin or arcsec):raise ValueError("angle")
 utc=datetime(y,mo,d,h,mi,s,tzinfo=timezone(timedelta(minutes=offset))).astimezone(timezone.utc).isoformat()
 if not -1<=o<=1 or not 1<=len(bs)<=64 or not roots:raise ValueError("budget")
 records=[]
 for name,bias in sorted(bs):
  b=F(bias)
  if not name or not 0<=b<=1:raise ValueError("bias")
  lo=max(F(-1),o-b);hi=min(F(1),o+b)
  status="POSITIVE_WITHIN_ASSUMPTION" if lo>0 else "NEGATIVE_WITHIN_ASSUMPTION" if hi<0 else "SIGN_UNRESOLVED"
  records.append(dict(assumption=name,bias_bound=str(b),lower=str(lo),upper=str(hi),verdict=status))
 result=dict(version="JANE-131",chronos=chronos,instant_utc=utc,observed_difference=str(o),threshold=str(abs(o)),models=records,roots=sorted(set(roots)),jane_decision="UNDECIDED",learning_applied=False,caveat="Assumed absolute additive bias, not inferred causation.")
 result["sha256"]=sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
 return result
def demo():
 return sweep(F(-1,10),[("small",F(1,20)),("threshold",F(1,10)),("large",F(1,5))],"{{ - 2026:11:11 || 17:31:00 || +123.45.56 || }}",-360,["owned:canonical"])
if __name__=="__main__":print(json.dumps(demo(),indent=2))
