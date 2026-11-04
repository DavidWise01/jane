'use strict';
const STATES=Object.freeze(['sag a','nib sun','nib','earth','earth sun']);
function pair(primary=1,shadowToken=1){
 if(primary!==1||shadowToken!==1)throw Error('EXPECTED_TWO_POSITIVE_DISPLAY_TOKENS');
 return Object.freeze({display:'+1+1',primary:{token:'+1',role:'primary',effective:1},shadow:{token:'+1',role:'shadow',effective:-1},projected:0});
}
function validate(model){
 const problems=[];
 if(model?.schema!=='JANE-B147.1-BASE11-SHADOW-v1')problems.push('SCHEMA');
 if(model?.notation?.base!==11||model?.notation?.alternative!=='-+5')problems.push('BASE_NOTATION');
 if(JSON.stringify(model?.positions)!==JSON.stringify(STATES))problems.push('FIVE_POSITIONS');
 if(model?.notation?.written!=='+1+1'||model?.notation?.primaryEffective!==1||model?.notation?.shadowEffective!==-1||model?.notation?.projected!==0)problems.push('SHADOW_SEMANTICS');
 if(model?.scope!=='USER_DEFINED_ENCODING'||model?.physicalClaim!=='UNVERIFIED')problems.push('PHYSICAL_STATUS');
 return {status:problems.length?'HOLD':'SYMBOLIC_PASS',problems};
}
module.exports={STATES,pair,validate};
