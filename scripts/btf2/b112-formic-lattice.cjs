#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),K=require('./formic-hex-kernel.cjs');
const root=path.resolve(__dirname,'../..'),input=path.join(root,'btf2/catalog.json'),outDir=path.join(root,'b112'),output=path.join(outDir,'registry.json');
const cat=JSON.parse(fs.readFileSync(input,'utf8'));
if(cat.owner!=='DavidWise01'||!Array.isArray(cat.repos)||cat.complete!==true)throw Error('Require complete public DavidWise01 repository catalog');
const last=fs.existsSync(output)?JSON.parse(fs.readFileSync(output,'utf8')):null;
const prior=last?[...(last.members||[]),...(last.reserved_positions||[])]:[];
const repos=cat.repos.filter(x=>x&&typeof x.name==='string'&&/^[\w.-]+$/.test(x.name)).map(x=>'DavidWise01/'+x.name);
const members=K.allocate(repos,prior);const byPos=new Map(members.map(x=>[K.key(x.q,x.r),x]));
if(byPos.size!==members.length)throw Error('Coordinate collision');
const missing=members.filter(x=>!prior.some(y=>y.repo.toLowerCase()===x.repo.toLowerCase()));
const active=new Set(members.map(x=>x.repo.toLowerCase()));
const reserved_positions=prior.filter(x=>!active.has(x.repo.toLowerCase()));
const result={schema:'JANE_B112_FORMIC_HEX_V1',generated_at:new Date().toISOString(),source:'btf2/catalog.json',source_count:cat.count,member_count:members.length,new_assignments:missing.length,radius_bound:Math.max(0,...members.map(x=>x.ring)),sector_counts:[0,1,2].map(i=>members.filter(x=>x.sector===i).length),reserved_positions,rules:{neighbors:6,sector:'(q-r) mod 3',disk_cells:'1+3R(R+1)',namespace:'PUBLIC_OWNER_REPOS',claim:'logical routing addresses only'},members};
fs.mkdirSync(outDir,{recursive:true});fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
const log=path.join(outDir,'assignments.jsonl');if(missing.length)fs.appendFileSync(log,missing.map(x=>JSON.stringify({event:'CELL_ASSIGNED',repo:x.repo,q:x.q,r:x.r,formic:x.formic,at:result.generated_at})).join('\n')+'\n');
console.log('B112 FORMIC hex',members.length,'children',result.radius_bound,'rings',missing.length,'new');
