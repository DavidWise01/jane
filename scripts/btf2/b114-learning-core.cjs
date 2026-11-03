'use strict';
const crypto=require('node:crypto');
const FIELDS=Object.freeze(['archived','fork','updated_at','default_branch','pushed_at','open_issues_count','license_spdx','has_pages']);
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const ident=x=>String(x||'').toLowerCase();
function learn(runs){
 const sequence=[...runs].sort((a,b)=>String(a.at).localeCompare(String(b.at)));
 const evidence=[],history=new Map(),transitions=new Map();
 for(const run of sequence){
  const rows=new Map();
  for(const e of run.rows||[]){
   const repo=String(e.repository||'');
   if(!/^DavidWise01\/[\w.-]+$/i.test(repo))continue;
   if(rows.has(ident(repo)))throw Error('Duplicate repo in snapshot: '+repo);
   rows.set(ident(repo),e);
  }
  for(const [k,cur] of rows){
   if(!history.has(k))history.set(k,[]);
   const observations=history.get(k);const prev=observations.at(-1)||null;
   if(prev?.record?.status==='OBSERVED'&&cur.status==='OBSERVED'){
    for(const f of FIELDS){
     const a=prev.record.signals?.[f],b=cur.signals?.[f];
     if(a==null||b==null||a===undefined||b===undefined||a===b)continue;
     const id=hash(JSON.stringify([k,f,prev.run_id,run.run_id,a,b])).slice(0,24);
     const change={id,repo:cur.repository,field:f,previous:a,current:b,previous_run:prev.run_id,current_run:run.run_id,observed_at:run.at,confidence:'METADATA_TRANSITION_ONLY',evidence:[{run:prev.run_id,file:prev.file,sha256:prev.sha256},{run:run.run_id,file:run.file,sha256:run.sha256}]};
     evidence.push(change);
     if(!transitions.has(f))transitions.set(f,{field:f,count:0,repositories:new Set(),examples:[]});
     const t=transitions.get(f);t.count++;t.repositories.add(k);if(t.examples.length<12)t.examples.push(id);
    }
   }
   observations.push({run_id:run.run_id,at:run.at,file:run.file,sha256:run.sha256,record:cur});
  }
 }
 const patterns=[...transitions.values()].map(t=>({field:t.field,observed_transitions:t.count,distinct_repositories:t.repositories.size,evidence_ids:t.examples,classification:t.repositories.size>=2?'CROSS_CHILD_OBSERVATION':'SINGLE_CHILD_OBSERVATION',hypothesis:'Public GitHub metadata field '+t.field+' changed between verified observation snapshots; reason unknown.'})).sort((a,b)=>b.observed_transitions-a.observed_transitions||a.field.localeCompare(b.field));
 return {source_runs:sequence.map(r=>({run_id:r.run_id,at:r.at,file:r.file,sha256:r.sha256})),observed_repositories:history.size,transition_count:evidence.length,patterns,evidence,notes:'No causal claims, model training, child autonomy, or actual ancestry inferred.'};
}
module.exports={learn,FIELDS,hash};
