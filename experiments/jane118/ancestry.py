"""JANE 118: bounded ancestry graph, offline and read-only."""
from dataclasses import dataclass
from hashlib import sha256
import json
MAX_DEPTH=12
MAX_NODES=128
@dataclass(frozen=True)
class Source:
    id: str
    parents: tuple[str,...]=()
    complete: bool=True
class GraphError(ValueError): pass
class AncestryGraph:
    def __init__(self,sources):
        sources=list(sources)
        if len(sources)>MAX_NODES or len({s.id for s in sources})!=len(sources):
            raise GraphError("size or duplicate identifiers")
        self.sources={s.id:s for s in sources}
    def trace(self,start,max_depth=MAX_DEPTH):
        if not 0<=max_depth<=MAX_DEPTH: raise GraphError("depth bound")
        roots,unknown,cycles,exhausted=set(),set(),set(),set()
        visited=set()
        def walk(node,depth,stack):
            if node in stack: cycles.add(node); return
            if node not in self.sources: unknown.add(node); return
            if depth>max_depth: exhausted.add(node); return
            if node in visited:return
            visited.add(node)
            s=self.sources[node]
            if not s.complete:unknown.add(node)
            if not s.parents:
                if s.complete:roots.add(node)
                return
            for p in sorted(s.parents):walk(p,depth+1,stack|{node})
        walk(start,0,set())
        return dict(start=start,roots=sorted(roots),unknown=sorted(unknown),
                    cycles=sorted(cycles),exhausted=sorted(exhausted),
                    status="UNRESOLVED" if unknown or cycles or exhausted else "RESOLVED",
                    visited=len(visited))
    def compare(self,left,right,max_depth=MAX_DEPTH):
        a,b=self.trace(left,max_depth),self.trace(right,max_depth)
        shared=sorted(set(a["roots"])&set(b["roots"]))
        verdict=("SHARED_ANCESTRY" if shared else "UNKNOWN" if
                 a["status"]!="RESOLVED" or b["status"]!="RESOLVED" else
                 "SEPARATE_RECORDED_ROOTS")
        return dict(left=a,right=b,shared_roots=shared,verdict=verdict,
                    learning_applied=False,jane_decision="UNDECIDED")
    def evidence_packet(self,left,right,max_depth=MAX_DEPTH):
        result=self.compare(left,right,max_depth)
        p=dict(version="JANE-118",question="Do sources share a root of roots?",
               evaluation=result,caveat="Separate recorded roots do not prove real-world independence.",
               next_action="FLAY_REQUEST_LINEAGE" if result["verdict"]=="UNKNOWN" else "JANE_REVIEW")
        p["digest"]=sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
        return p
