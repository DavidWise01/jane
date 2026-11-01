#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const source=path.join(root,'btf2','formic-observers.json');if(!fs.existsSync(source))throw Error('Run B86 observer first');
const report=JSON.parse(fs.readFileSync(source,'utf8'));if(!Array.isArray(report.agents))throw Error('Invalid B86 report');
const id=(process.env.GITHUB_RUN_ID||'local')+'-'+(process.env.GITHUB_RUN_ATTEMPT||'1')+'-'+new Date().toISOString().replace(/[:.]/g,'-');
const dir=path.join(root,'btf2','memory','runs'),filename=id+'.jsonl',dest=path.join(dir,filename);
fs.mkdirSync(dir,{recursive:true});if(fs.existsSync(dest))throw Error('Refuse overwrite existing run '+id);
const rows=report.agents.map(a=>{const repo=String(a.scope||'');const stable=crypto.createHash('sha256').update(repo.toLowerCase()).digest('hex').slice(0,16);return{schema:'B87_EVENT_V1',run_id:id,observer_id:'FORMIC-'+stable,repository:repo,pin:'BTF2',recorded_at:new Date().toISOString(),status:a.status||'UNKNOWN',source:'B86_PUBLIC_GITHUB_API',capability:'READ_ONLY',signals:a.signals||null,error:a.error||null}});
fs.writeFileSync(dest,rows.map(r=>JSON.stringify(r)).join('\n')+'\n',{flag:'wx'});
const indexPath=path.join(root,'btf2','memory','index.json');const previous=fs.existsSync(indexPath)?JSON.parse(fs.readFileSync(indexPath,'utf8')):{schema:'B87_INDEX_V1',runs:[]};if(!Array.isArray(previous.runs))throw Error('Invalid index');
previous.runs.push({run_id:id,file:'runs/'+filename,at:new Date().toISOString(),count:rows.length,sha256:crypto.createHash('sha256').update(fs.readFileSync(dest)).digest('hex')});
fs.writeFileSync(indexPath,JSON.stringify(previous,null,2)+'\n');
console.log('B87 appended',rows.length,'observer events; run',id);
