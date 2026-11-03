'use strict';
const crypto=require('node:crypto');
function stableId(repo){return crypto.createHash('sha256').update(repo.toLowerCase()).digest('hex').slice(0,16)}
function dayOf(t){if(typeof t!=='string'||!/^\d{4}-\d\d-\d\dT/.test(t)||!Number.isFinite(Date.parse(t)))return null;return new Date(t).toISOString().slice(0,10)}
function cohort(firstSeen){const d=dayOf(firstSeen);return d?'ARRIVAL_'+d:'UNKNOWN'}
function normalize(input,history={},now=new Date().toISOString()){
 const out=[],emitted=[];
 for(const child of input){if(!child?.repo||!/^[\w.-]+\/[\w.-]+$/.test(child.repo))continue;
 const repo=child.repo,key=repo.toLowerCase(),old=history[key]||null;
 const firstSeen=old?.first_seen||child.first_seen||null;
 const generation=old?.generation||cohort(firstSeen);
 const datum={repo,formic:child.formic||child.observer||'FORMIC-'+stableId(repo),channel:child.channel||'btf2:'+key,presence:child.presence||'RESERVED',
 hex: Number.isSafeInteger(child.q)&&Number.isSafeInteger(child.r)?{q:child.q,r:child.r,sector:child.sector}:null,
 first_seen:firstSeen,generation,lineage:{parent_repo:null,parentage:'UNKNOWN'},status:'OBSERVED_LOGICAL_IDENTITY'};
 if(old){datum.generation=old.generation;datum.first_seen=old.first_seen;datum.lineage=old.lineage||datum.lineage}
 else emitted.push({event:'GENERATION_REGISTERED',repo,formic:datum.formic,generation:datum.generation,first_seen:datum.first_seen,at:now});
 out.push(datum);
 }
 return {members:out,events:emitted};
}
module.exports={cohort,dayOf,normalize};
