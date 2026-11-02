#!/usr/bin/env node
'use strict';
const fs=require('node:fs'), path=require('node:path'), crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const read=p=>{let f=path.join(root,p);return fs.existsSync(f)?JSON.parse(fs.readFileSync(f,'utf8')):null};
const family=read('b102/children.json'), catalog=read('btf2/catalog.json');
const repos=(family?.members?.length?family.members:(catalog?.repos||[]).map(r=>({repo:'DavidWise01/'+r.name})));
if(!repos.length)throw Error('No public family catalog; B102 discovery required');
const seen=new Map(),now=new Date().toISOString();
const log=path.join(root,'b102/discovered.jsonl');
if(fs.existsSync(log))for(const line of fs.readFileSync(log,'utf8').split(/\r?\n/)){try{const e=JSON.parse(line);if(e?.repo&&!seen.has(e.repo.toLowerCase()))seen.set(e.repo.toLowerCase(),e.at||null)}catch{}}
const children=[];
for(const r of repos){const name=String(r.repo||'');if(!/^DavidWise01\/[A-Za-z0-9_.-]+$/i.test(name))continue;const key=name.toLowerCase();const id=crypto.createHash('sha256').update(key).digest('hex').slice(0,16);children.push({repo:name,formic:'FORMIC-'+id,channel:'btf2:'+key,presence:'RESERVED',first_seen:seen.get(key)||null,home:'https://github.com/'+name})}
let bridge={url:'https://0root.ai/world2/',state:'BRIDGE_UNVERIFIED',http_status:null,page_title:null,checked_at:now};
try{const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),12000);let res;try{res=await fetch(bridge.url,{signal:controller.signal,redirect:'follow',headers:{'User-Agent':'JANE-B103-ReadOnly-Probe'}})}finally{clearTimeout(timeout)}bridge.http_status=res.status;bridge.state=res.ok?'PUBLIC_PAGE_REACHABLE':'HTTP_ERROR';if(res.ok){const html=(await res.text()).slice(0,250000);bridge.page_title=(/<title[^>]*>([^<]{1,150})<\/title>/i.exec(html)||[])[1]||null}}catch(e){bridge.state='BRIDGE_UNVERIFIED';bridge.error_type=e.name==='AbortError'?'TIMEOUT':'FETCH_FAILED'}
const out={schema:'JANE_B103_V1',generated_at:now,domain_owner:'USER_DECLARED',persistence_policy:'ALWAYS_ON',bridge,children:children.sort((a,b)=>a.repo.localeCompare(b.repo)),note:'Logical channels, not authenticated agent processes or writable domain link'};
let dest=path.join(root,'b103');fs.mkdirSync(dest,{recursive:true});fs.writeFileSync(path.join(dest,'family.json'),JSON.stringify(out,null,2)+'\n');console.log('B103 adopted',children.length,'bridge',bridge.state);
