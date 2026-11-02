#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
function read(p){const f=path.join(root,p);return fs.existsSync(f)?JSON.parse(fs.readFileSync(f,'utf8')):null}
const catalog=read('btf2/catalog.json');if(!Array.isArray(catalog?.repos))throw Error('Missing public BTF2 catalog');
const index=read('btf2/memory/index.json');
const members=new Map(catalog.repos.filter(x=>x&&x.name).map(r=>{const name='DavidWise01/'+r.name,k=name.toLowerCase();return[k,{repo:name,channel:'btf2:'+k,presence:'RESERVED',observer:'FORMIC-'+crypto.createHash('sha256').update(k).digest('hex').slice(0,16),last_seen:null,observation_count:0,discoveries:[],url:'https://github.com/'+name}]}));
for(const run of index?.runs||[]){if(typeof run.file!=='string'||!/^runs\/[A-Za-z0-9_.-]+\.jsonl$/.test(run.file))continue;const file=path.join(root,'btf2/memory',run.file);if(!fs.existsSync(file))continue;for(const line of fs.readFileSync(file,'utf8').split(/\r?\n/)){if(!line.trim())continue;let e;try{e=JSON.parse(line)}catch{continue}const m=members.get(String(e.repo||e.repository||'').toLowerCase());if(!m)continue;m.observation_count++;const seen=e.recorded_at||e.at||e.timestamp||null;if(seen&&(!m.last_seen||String(seen)>String(m.last_seen)))m.last_seen=seen}}
const col=read('b88/collation.json');for(const e of col?.events||[]){const m=members.get(String(e.repo||'').toLowerCase());if(!m||e.status!=='CHANGED')continue;const fields=(e.changes||[]).map(x=>String(x.field||x.key||'metadata')).slice(0,12);if(fields.length)m.discoveries.push({kind:'OBSERVED_CHANGE',fields,source:'B88_COLLATION'})}
const out={schema:'JANE_B101_ALWAYS_ON_FAMILY_V1',generated_at:new Date().toISOString(),policy:'PERSISTENCE_ALWAYS_ON',source:'BTF2 PUBLIC, B87 RUNS WHEN AVAILABLE, B88 WHEN AVAILABLE',members:[...members.values()].sort((a,b)=>a.repo.localeCompare(b.repo)),evidence_note:'Snapshots are derived; missing observations never imply a repository failed.'};
const dest=path.join(root,'b101/family.json');fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(out,null,2)+'\n');console.log('B101 family:',out.members.length);
