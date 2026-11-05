#!/usr/bin/env python3
"""B160: observation-only, bounded ecosystem inventory, Python stdlib, no GitHub writes."""
import argparse, datetime as dt, json, os, pathlib, sys, time, urllib.error, urllib.parse, urllib.request
OWNER="DavidWise01"
MAX_PAGES=30
PAGE_SIZE=100
def request(url,token):
    headers={"Accept":"application/vnd.github+json","User-Agent":"jane-b160-ecosphere-observer","X-GitHub-Api-Version":"2022-11-28"}
    if token: headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,headers=headers,method="GET")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=25) as resp: return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code in (429,500,502,503,504) and attempt<2:
                time.sleep(1+attempt*2)
                continue
            raise RuntimeError("GitHub HTTP "+str(exc.code)+" for "+url.split("?")[0]) from None
    raise RuntimeError("unreachable")
def list_public(token,limit):
    results=[]
    for page in range(1,MAX_PAGES+1):
        url=f"https://api.github.com/users/{OWNER}/repos?per_page={PAGE_SIZE}&page={page}&type=owner&sort=full_name&direction=asc"
        batch=request(url,token)
        if not isinstance(batch,list): raise RuntimeError("expected repository array")
        results.extend(batch)
        if len(results)>=limit: return results[:limit],False
        if len(batch)<PAGE_SIZE: return results,True
    return results,False
def normalize(repo):
    # Exclude private repos from public artifact, even when an elevated token is present.
    if repo.get("private") or repo.get("owner",{}).get("login","").lower()!=OWNER.lower(): return None
    return {k:repo.get(k) for k in ("name","full_name","html_url","description","default_branch","archived","disabled","fork","has_pages","has_wiki","open_issues_count","size","language","created_at","updated_at","pushed_at","visibility")}
def proposals(repo):
    p=[]
    if repo.get("archived"): return ["ARCHIVED_OBSERVE_ONLY"]
    if repo.get("disabled"): return ["DISABLED_HOLD"]
    if not repo.get("description"): p.append("SUGGEST_DESCRIPTION")
    if not repo.get("pushed_at"): p.append("CHECK_INITIAL_CONTENT")
    if not repo.get("default_branch"): p.append("CHECK_DEFAULT_BRANCH")
    if not repo.get("has_pages"): p.append("CONSIDER_PAGES_WHEN_APPLICABLE")
    return p
def build(repos,complete):
    normalized=[r for raw in repos if (r:=normalize(raw)) is not None]
    normalized.sort(key=lambda x:x["full_name"].lower())
    snapshot=[{**r,"proposals":proposals(r)} for r in normalized]
    counts={"observed":len(snapshot),"archived":sum(bool(r["archived"]) for r in snapshot),"has_pages":sum(bool(r["has_pages"]) for r in snapshot),"no_description":sum(not r["description"] for r in snapshot),"forks":sum(bool(r["fork"]) for r in snapshot)}
    return {"schema":"JANE-B160-ECOSPHERE-OBSERVATION-v1","owner":OWNER,"mode":"PUBLIC_READ_ONLY","complete":complete,"scope":"PUBLIC_REPOS_ONLY","counts":counts,"repositories":snapshot,"governance":{"isaDefined":False,"threeWitnesses":["a1","b1","c1"],"observationLayerDepth":1,"quorum":False,"automatedCrossRepoWrites":False,"physicalPromotion":False,"noAutonomousMerges":True},"warnings":["SUGGESTIONS_NOT_CHANGES","NO_SOURCE_REPO_MODIFICATION","PRIVATE_REPOS_EXCLUDED","INCOMPLETE_IF_LIMIT_REACHED"]}
def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="ecosystem/reports/latest.json")
    parser.add_argument("--limit",type=int,default=2500)
    parser.add_argument("--fixture",default=None,help="Offline JSON array of GitHub API repo objects for validation")
    args=parser.parse_args(argv)
    if not 1<=args.limit<=3000: parser.error("limit must be between 1 and 3000")
    if args.fixture:
        repos=json.loads(pathlib.Path(args.fixture).read_text(encoding="utf8"))
        complete=len(repos)<=args.limit
        repos=repos[:args.limit]
    else:
        # Public endpoint only; optional token increases rate limit without increasing scope.
        repos,complete=list_public(os.getenv("ECOSPHERE_READ_TOKEN") or os.getenv("GITHUB_TOKEN",""),args.limit)
    data=build(repos,complete)
    data["observed_at"]=dt.datetime.now(dt.timezone.utc).isoformat()
    path=pathlib.Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"output":str(path),"observed":data["counts"]["observed"],"complete":complete,"mode":data["mode"]}))
    return 0
if __name__=="__main__": sys.exit(main())
