'use strict';
const crypto=require('node:crypto');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const repoKey=s=>String(s||'').toLowerCase();
function build(lessons,registry=null,prior={}){
 if(!Array.isArray(lessons?.patterns)||!Array.isArray(lessons?.evidence))throw Error('Requires B114 patterns and evidence');
 const evidenceById=new Map(lessons.evidence.map(e=>[e.id,e]));
 const cards=[],newEvents=[];
 const old=new Map((prior.cards||[]).map(c=>[c.lesson_id,c]));
 for(const p of lessons.patterns){
  if(!p.field||!Number.isSafeInteger(p.observed_transitions)||p.observed_transitions<1)continue;
  const all=lessons.evidence.filter(e=>e.field===p.field);
  if(!all.length)continue;
  // A stable identity per evidence set, so additional evidence creates a new revision rather than editing history.
  const evidence_ids=[...new Set(all.map(e=>e.id))].sort();
  const lesson_id='LESSON-'+sha(JSON.stringify({field:p.field,evidence_ids})).slice(0,20);
  const level=p.distinct_repositories>=2?'RECURRING_METADATA_OBSERVATION':'SINGLE_REPOSITORY_OBSERVATION';
  const earlier=old.get(lesson_id);
  const card={lesson_id,field:p.field,level,observed_transitions:all.length,distinct_repositories:new Set(all.map(e=>repoKey(e.repo))).size,
   source_run_ids:[...new Set(all.flatMap(e=>[e.previous_run,e.current_run]))].filter(Boolean).sort(),
   evidence_ids,statement:'Public GitHub metadata value for '+p.field+' changed in one or more recorded comparisons. No cause or prescription established.',
   instructional_use:'When this field is encountered, compare prior and current snapshots before drawing conclusions.',
   certainty:'OBSERVED_METADATA_ONLY', status:'AVAILABLE_FOR_OPTIONAL_REVIEW',version:1};
  cards.push(card);
  if(!earlier)newEvents.push({event:'LESSON_CATALOGUED',lesson_id,field:p.field,evidence_ids});
 }
 // Only suggest cards to children where matching metadata was actually observed; no mass commands.
 const members=Array.isArray(registry?.members)?registry.members:[];
 const observedByRepo=new Map();
 for(const e of lessons.evidence){const k=repoKey(e.repo);if(!observedByRepo.has(k))observedByRepo.set(k,new Set());observedByRepo.get(k).add(e.field)}
 const suggestions=[];
 for(const child of members){
  if(!child.repo)continue;
  const seen=observedByRepo.get(repoKey(child.repo));
  if(!seen)continue;
  for(const c of cards){
   if(!seen.has(c.field))continue;
   suggestions.push({repo:child.repo,channel:child.channel||'btf2:'+repoKey(child.repo),generation:child.generation||'UNKNOWN',lesson_id:c.lesson_id,reason:'MATCHING_PRIOR_OBSERVED_FIELD',mode:'AVAILABLE_NOT_SENT'});
  }
 }
 return {cards:cards.sort((a,b)=>a.field.localeCompare(b.field)),suggestions,newEvents};
}
module.exports={build,sha};
