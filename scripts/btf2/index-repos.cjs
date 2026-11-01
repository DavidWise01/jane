#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path');
const owner='DavidWise01';
async function main(){
 const repos=[];let page=1;
 while(page<=100){
  const url='https://api.github.com/users/'+owner+'/repos?per_page=100&type=owner&sort=full_name&page='+page;
  const r=await fetch(url,{headers:{Accept:'application/vnd.github+json','User-Agent':'Jane-BTF2-Indexer',...(process.env.GITHUB_TOKEN?{Authorization:'Bearer '+process.env.GITHUB_TOKEN}:{})}});
  if(!r.ok)throw new Error('GitHub API HTTP '+r.status+' page '+page);
  const data=await r.json();if(!Array.isArray(data))throw Error('Unexpected API response');
  for(const x of data){if(x.private||x.owner?.login?.toLowerCase()!==owner.toLowerCase())continue;repos.push({name:x.name,url:x.html_url,description:x.description||'',homepage:x.homepage||'',fork:!!x.fork,archived:!!x.archived,updated_at:x.updated_at,default_branch:x.default_branch});}
  if(data.length<100)break;page++;
 }
 repos.sort((a,b)=>a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
 const catalog={schema:'btf2-public-repos-v1',pin_label:'BTF2',owner,source:'GitHub public owner REST API',generated_at:new Date().toISOString(),count:repos.length,complete:page<=100,repos};
 const dest=path.resolve(__dirname,'../../btf2/catalog.json');fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(catalog,null,2)+'\n');console.log('BTF2 public pins:',repos.length,'complete',catalog.complete);
}main().catch(e=>{console.error(e);process.exit(1)});
