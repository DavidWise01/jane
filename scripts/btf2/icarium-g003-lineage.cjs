'use strict';
const ID='FORMIC-ICARIUM-G003';
const OPERATORS=Object.freeze(['i','care','ium']);
const LILITH_JANE_SCALE=1/2;
const CLAIM_MOTHER_SCALE=33/100;
const CLAIM_JANE_SCALE=8/100;
const JANE_FROM_MOTHER=LILITH_JANE_SCALE*CLAIM_MOTHER_SCALE;
const MOTHER_FROM_JANE=CLAIM_JANE_SCALE/LILITH_JANE_SCALE;
function inspect(){
 const consistent=Math.abs(JANE_FROM_MOTHER-CLAIM_JANE_SCALE)<1e-12;
 return Object.freeze({
  name:'ICARIUM',identity:ID,operator:'{{i,care,ium}}',operators:[...OPERATORS],
  lineage:['JANE','LILITH','ICARIUM'],siblings:['a.t.o.m','E.V.E'],
  mother_scale_claim:CLAIM_MOTHER_SCALE,
  jane_scale_claim:CLAIM_JANE_SCALE,
  mother_scale_implied_by_jane_claim:MOTHER_FROM_JANE,
  jane_scale_implied_by_mother_claim:JANE_FROM_MOTHER,
  consistent,
  geometry_status:consistent?'SCALE_CONSISTENT_PROFILE_UNKNOWN':'UNRESOLVED_SCALE_AND_PROFILE',
  profile:null,cell_count:null
 });
}
module.exports={ID,OPERATORS,LILITH_JANE_SCALE,CLAIM_MOTHER_SCALE,CLAIM_JANE_SCALE,inspect};
