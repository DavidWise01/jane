'use strict';
const fs=require('node:fs');
const path=require('node:path');
function validate(m){
 const problems=[];
 if(m?.schema!=='JANE-B147.2-FIRST-SHADOW-FIVE-SPHERES-v1')problems.push('SCHEMA');
 if(m?.canonicalNotation!=='{ -1, 1 } > 1 ; -+5')problems.push('NOTATION');
 if(m?.firstPair?.tokens?.join(',')!=='-1,1'||m.firstPair.shadowApplied!==true||m.firstPair.effectivePositionCount!==1||m.firstPair.netSignedValue!==0)problems.push('FIRST_PAIR');
 if(m?.remaining?.signedSphereCount!==5||m.remaining.shadowApplied!==false||m.remaining.polarity?.join(',')!=='-,+'||m.remaining.sphereSlots?.join(',')!=='1,2,3,4,5')problems.push('FIVE_NO_SHADOW');
 if(m?.contextualExamples?.some(s=>s.status!=='PHYSICAL_REGION_EXAMPLE_NOT_ASSIGNED_TO_SLOT'))problems.push('UNSUPPORTED_EXAMPLE_BINDING');
 if(m?.bodies?.join('|')!=='sag a|nib sun|nib|earth|earth sun')problems.push('BODY_ORDER');
 if(m?.preserved?.forceEdges!==6||m.preserved.geometricPairs!==6||m.preserved.unboundCorePair?.join('|')!=='nib sun|earth'||m.preserved.manifolds?.gravity!==2||m.preserved.manifolds?.void!==2)problems.push('B147_PRESERVATION');
 if(m?.status!=='SYMBOLIC_STRUCTURE_ONLY')problems.push('PHYSICAL_STATUS');
 return{status:problems.length?'HOLD':'SYMBOLIC_STRUCTURE_PASS',problems,firstShadowPairs:1,otherShadowPairs:0,signedSphereSlots:5};
}
if(require.main===module){const m=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b147/first-shadow-five-spheres-v1.json'),'utf8'));const r=validate(m);console.log(r);if(r.status!=='SYMBOLIC_STRUCTURE_PASS')process.exitCode=1}
module.exports={validate};
