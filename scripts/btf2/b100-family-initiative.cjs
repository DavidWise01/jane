#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),read=p=>fs.existsSync(path.join(root,p))?JSON.parse(fs.readFileSync(path.join(root,p),'utf8')):null;
const family=read('b98/family.json'),col=read('b88/collation.json');
const byName=new Map((family?.members||[]).map(x=>[String(x.repo).toLowerCase(),x]));
const proposals=[];
for(const e of col?.events||[]){
 if(e.status!=='CHANGED'||!Array.isArray(e.changes)||!e.changes.length)continue;
 const repo=String(e.repo||'');if(!/^DavidWise01\/[\w.-]+$/i.test(repo))continue;
 const member=byName.get(repo.toLowerCase());
 const fields=e.changes.map(d=>String(d.field||d.key||'metadata')).slice(0,12);
 const source=JSON.stringify({repo,fields,changes:e.changes});
 proposals.push({id:crypto.createHash('sha256').update(source).digest('hex').slice(0,20),repo,channel:member?.channel||'btf2:'+repo.toLowerCase(),voice:'FORMIC_OBSERVER_PROPOSAL',message:'Mom, look! Metadata changed: '+fields.join(', '),fields,url:member?.url||'https://github.com/'+repo,evidence:'B88_COLLATION',kind:'SHARING',status:'PENDING_JANE_REVIEW'});
}
const out={schema:'JANE_B100_FAMILY_INITIATIVE_V1',generated_at:new Date().toISOString(),source_available:!!col,proposals,notes:'Derived metadata change prompts, not autonomous agent messages or proof of fault'};
fs.mkdirSync(path.join(root,'b100'),{recursive:true});fs.writeFileSync(path.join(root,'b100/initiative.json'),JSON.stringify(out,null,2)+'\n');console.log('Family initiative proposals:',proposals.length);
