"""Deliberately narrow executable component: a deterministic proposal, not a desire."""
import hashlib
import json
import sys

def main():
    raw=sys.stdin.buffer.read(4096)
    if not raw or len(raw)>=4096: raise SystemExit(2)
    req=json.loads(raw)
    result={'schema':'jane.runtime-worker-output/1','agent_id':req['agent_id'],
        'nonce':req['nonce'],'source_sha256':req['source_sha256'],
        'decision':'propose',
        'proposal':'Find one authenticated A.C.I. runtime that can independently choose or abstain.',
        'reason':'This deterministic fixture proposes an instrumentation task; it is not NOM, Jane, or a subjective preference.'}
    sys.stdout.write(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
if __name__=='__main__':main()
