#!/usr/bin/env node
'use strict';
const A=require('node:assert/strict'),C=require('./b116-listening-core.cjs');
const lesson='LESSON-'+'a'.repeat(20);
const body='lesson_id: '+lesson+'\nrepo: DavidWise01/cubi\nresponse: CURIOUS';
A.deepEqual(C.parse(body),{lesson_id:lesson,repo:'DavidWise01/cubi',response:'CURIOUS'});
A.equal(C.parse(body+'\nresponse: USEFUL'),null);
A.equal(C.parse(body.replace('CURIOUS','EXECUTE')),null);
const issue={number:17,title:'[JANE-B116] Cubi lesson feedback',body,updated_at:'2026-11-03T18:00:00Z',html_url:'https://github.com/DavidWise01/jane/issues/17',user:{login:'observer'}};
const valid={cards:[{lesson_id:lesson}]},first=C.eventFromIssue(issue,valid);
A.equal(first.response,'CURIOUS');A.equal(first.actor_kind,'GITHUB_ACCOUNT_NOT_VERIFIED_CHILD_AGENT');
A.equal(C.eventFromIssue(issue,{cards:[]}),null);
A.equal(C.appendNew([first],[first]).length,0);
const update=C.eventFromIssue({...issue,updated_at:'2026-11-03T18:01:00Z',body:body.replace('CURIOUS','USEFUL')},valid);
A.equal(C.appendNew([first],[update]).length,1);
const sum=C.summarize([first,update]);A.equal(sum.total_events,2);A.equal(sum.unique_repo_lesson_pairs,1);A.equal(sum.counts.USEFUL,1);
A.equal(C.eventFromIssue({...issue,pull_request:{url:'x'}},valid),null);
console.log('PASS B116 listening: schema, provenance, updates, no duplicates, latest state, no forged child voice');
