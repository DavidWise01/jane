#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),C=require('./b114-learning-core.cjs');
const root=path.resolve(__dirname,'../..');const dir=path.join(root,'btf2/memory'),indexFile=path.join(dir,'index.json');
if(!fs.existsSync(indexFile))throw Error('Missing B87 memory index');
const index=JSON.parse(fs.readFileSync(indexFile,'utf8'));
if(!Array.isArray(index.runs)||!index.runs.length)throw Error('No B87 observation runs');
const runs=[];
for(const r of index.runs){
 if(!/^runs\/[A-Za-z0-9_.-]+\.jsonl$/.test(String(r.file||'')))throw Error('Invalid run file '+r.file);
 const file=path.join(dir,r.file),data=fs.readFileSync(file);
 if(C.hash(data)!==r.sha256)throw Error('B87 file digest mismatch '+r.file);
 const rows=data.toString('utf8').split(/\r?\n/).filter(Boolean).map(s=>JSON.parse(s));
 if(rows.some(x=>x.run_id!==r.run_id))throw Error('Snapshot identity mismatch '+r.file);
 runs.push({run_id:r.run_id,at:r.at,file:'btf2/memory/'+r.file,sha256:r.sha256,rows});
}
const result=C.learn(runs),now=new Date().toISOString(),folder=path.join(root,'b114');
const familyFile=path.join(root,'b113/family.json');let generation=new Map();
if(fs.existsSync(familyFile)){const j=JSON.parse(fs.readFileSync(familyFile,'utf8'));for(const x of j.members||[])generation.set(x.repo.toLowerCase(),x.generation)}
for(const e of result.evidence)e.arrival_cohort=generation.get(e.repo.toLowerCase())||'UNKNOWN';
const output={schema:'JANE_B114_EVIDENCE_LEARNING_V1',generated_at:now,scope:'PUBLIC_GITHUB_METADATA_ONLY',source_verified:'SHA256_B87_RUNS',...result};
fs.mkdirSync(folder,{recursive:true});
fs.writeFileSync(path.join(folder,'lessons.json'),JSON.stringify(output,null,2)+'\n');
console.log('B114',output.source_runs.length,'verified runs',output.transition_count,'observed transitions',output.patterns.length,'pattern fields');
