#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),catalog=JSON.parse(fs.readFileSync(path.join(root,'btf2/catalog.json'),'utf8'));
const repos=new Map((catalog.repos||[]).filter(r=>r?.name).map(r=>[r.name.toLowerCase(),'DavidWise01/'+r.name]));
const token=process.env.GITHUB_TOKEN,repo=process.env.GITHUB_REPOSITORY||'DavidWise01/jane';
if(!token)throw Error('GITHUB_TOKEN missing');
async function main(){
const msgs=[];let page=1;
while(page<=10){const url='https://api.github.com/repos/'+repo+'/issues?state=all&per_page=100&page='+page;const r=await fetch(url,{headers:{Authorization:'Bearer '+token,Accept:'application/vnd.github+json','User-Agent':'jane-b99'}});if(!r.ok)throw Error('GitHub API '+r.status);const issues=await r.json();if(!issues.length)break;
for(const issue of issues){if(issue.pull_request)continue;const m=/^\[FORMIC\] ([A-Za-z0-9_.-]+): (.{1,140})$/.exec(issue.title||'');if(!m)continue;const canonical=repos.get(m[1].toLowerCase());if(!canonical)continue;msgs.push({repo:canonical,channel:'btf2:'+canonical.toLowerCase(),issue:issue.number,subject:m[2],author:issue.user?.login||null,created_at:issue.created_at,url:issue.html_url,state:issue.state,source:'GITHUB_ISSUE_TITLE',authenticated_agent:false})}
if(issues.length<100)break;page++}
const data={schema:'JANE_B99_PUBLIC_INBOX_V1',generated_at:new Date().toISOString(),messages:msgs.sort((a,b)=>a.created_at.localeCompare(b.created_at)),note:'Public issue-title metadata only; issue authors are GitHub identities, not verified FORMIC agents.'};
const out=path.join(root,'b99/inbox.json');fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(data,null,2)+'\n');console.log('B99 inbox messages',msgs.length)}
main().catch(e=>{console.error(e);process.exitCode=1});
