#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),base=path.join(root,'btf2','memory');
const idx=JSON.parse(fs.readFileSync(path.join(base,'index.json'),'utf8'));
const entries=idx.runs;if(!Array.isArray(entries)||!entries.length)throw Error('No B87 memory runs');
function load(ref){const file=path.resolve(base,ref.file);if(!file.startsWith(path.resolve(base,'runs')+path.sep))throw Error('unsafe snapshot path');return fs.readFileSync(file,'utf8').trim().split('\n').filter(Boolean).map(s=>JSON.parse(s))}
const latest=entries.at(-1),prior=entries.length>1?entries.at(-2):null,now=load(latest),before=prior?load(prior):[];
const previous=new Map(before.map(x=>[String(x.repository).toLowerCase(),x]));
const fields=['archived','fork','updated_at','default_branch','pushed_at','open_issues_count','license_spdx','has_pages'];
let changed=0,unknown=0,baseline=0,stable=0;const events=[];
for(const cur of now){const old=previous.get(String(cur.repository).toLowerCase());
let classification='UNKNOWN',deltas=[];
if(cur.status!=='OBSERVED'||(old&&old.status!=='OBSERVED')){classification='UNKNOWN';unknown++}
else if(!old){classification='BASELINE_NEW';baseline++}
else{for(const field of fields){const a=old.signals?.[field],b=cur.signals?.[field];if(a===undefined||b===undefined||a===null||b===null)continue;if(a!==b)deltas.push({field,previous:a,current:b})}classification=deltas.length?'CHANGED':'UNCHANGED';if(deltas.length)changed++;else stable++}
events.push({repo:cur.repository,pin:'BTF2',observer_id:cur.observer_id,previous_run:prior?.run_id||null,current_run:latest.run_id,status:classification,changes:deltas,source:'PUBLIC_GITHUB_METADATA',confidence:'OBSERVATION_NOT_CAUSATION'})}
const report={schema:'B88_COLLATION_V1',generated_at:new Date().toISOString(),latest_run:latest.run_id,previous_run:prior?.run_id||null,scope:'Public DavidWise01 repos',metrics:{total:events.length,changed,stable,baseline,unknown},events};
const dest=path.join(root,'b88','collation.json');fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
console.log('B88 collated:',JSON.stringify(report.metrics));
