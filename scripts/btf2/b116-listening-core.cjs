'use strict';
const crypto=require('node:crypto');
const RESPONSES=new Set(['CURIOUS','USEFUL','IRRELEVANT','QUIET']);
const canonical=s=>String(s||'').trim();
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
function parse(body){
 if(typeof body!=='string'||body.length>16000)return null;
 const lines=body.split(/\r?\n/);
 const values={};
 for(const line of lines){
  const m=/^(lesson_id|repo|response):\s*(.*?)\s*$/i.exec(line.trim());
  if(m){const k=m[1].toLowerCase();if(values[k]!==undefined)return null;values[k]=m[2]}
 }
 if(!/^LESSON-[a-f0-9]{20}$/.test(values.lesson_id||''))return null;
 if(!/^DavidWise01\/[\w.-]+$/i.test(values.repo||''))return null;
 if(!RESPONSES.has(values.response||''))return null;
 return {lesson_id:values.lesson_id,repo:values.repo,response:values.response};
}
function eventFromIssue(issue,lessons){
 if(!issue||issue.pull_request||!/^\[JANE-B116\]/.test(String(issue.title||'')))return null;
 const parsed=parse(issue.body);if(!parsed)return null;
 const known=new Set((lessons?.cards||[]).map(c=>c.lesson_id));
 if(!known.has(parsed.lesson_id))return null;
 const number=Number(issue.number);
 if(!Number.isSafeInteger(number)||number<=0||typeof issue.updated_at!=='string')return null;
 const author=canonical(issue.user?.login);if(!/^[\w-]+$/.test(author))return null;
 const key=hash(JSON.stringify([number,issue.updated_at,parsed,author])).slice(0,32);
 return {schema:'JANE_B116_LISTENING_EVENT_V1',event_id:key,event:'LESSON_RESPONSE_OBSERVED',
 source:'PUBLIC_GITHUB_ISSUE',issue_number:number,url:String(issue.html_url||''),at:issue.updated_at,
 actor:author,actor_kind:'GITHUB_ACCOUNT_NOT_VERIFIED_CHILD_AGENT',
 lesson_id:parsed.lesson_id,repo:parsed.repo,response:parsed.response,
 interpretation:'Human-authored response; not an autonomous child acknowledgement.'};
}
function appendNew(previous,received){
 const seen=new Set(previous.map(e=>e.event_id));const additions=[];
 for(const e of received){if(e&&!seen.has(e.event_id)){seen.add(e.event_id);additions.push(e)}}
 return additions;
}
function summarize(events){
 const last=new Map();for(const e of events){const key=e.lesson_id+'|'+e.repo.toLowerCase();const prior=last.get(key);if(!prior||e.at>=prior.at)last.set(key,e)}
 const totals={CURIOUS:0,USEFUL:0,IRRELEVANT:0,QUIET:0};
 for(const e of last.values())if(totals[e.response]!==undefined)totals[e.response]++;
 return {total_events:events.length,unique_repo_lesson_pairs:last.size,latest_responses:[...last.values()].sort((a,b)=>b.at.localeCompare(a.at)),counts:totals};
}
module.exports={parse,eventFromIssue,appendNew,summarize};
