'use strict';
const fs=require('node:fs'),path=require('node:path');
const names=['IONOSPHERE','PLASMASPHERE','MAGNETOSPHERE','HELIOSPHERE','ASTROSPHERE'];
function validate(d){
 const errors=[];
 if(d?.schema!=='JANE-B148-FIVE-SPHERE-BOUNDARY-v1')errors.push('SCHEMA');
 if(JSON.stringify(d?.primaryShadow?.input)!=='[-1,1]'||d.primaryShadow.sum!==0||d.primaryShadow.foldedPositions!==1||d.primaryShadow.onlyShadowPair!==true)errors.push('ONE_SHADOW_FOLD');
 if(!Array.isArray(d?.signedSphereSlots)||d.signedSphereSlots.length!==5)errors.push('FIVE_SLOTS');
 else d.signedSphereSlots.forEach((s,i)=>{
  if(s.id!=='S'+(i+1)||s.minus!=='UNASSIGNED'||s.plus!=='UNASSIGNED'||s.physicalRegionId!==null||s.center!==null||s.innerBoundary!==null||s.outerBoundary!==null||s.distanceUnit!==null||s.transitionRule!=='UNSPECIFIED')errors.push('UNSUPPORTED_SLOT_BINDING_'+(i+1));
 });
 if(!Array.isArray(d?.physicalExamples)||d.physicalExamples.length!==5||d.physicalExamples.some((e,i)=>e.id!==names[i]||!e.center||!e.boundary||!e.extentKind||!/^https:\/\//.test(e.source)))errors.push('SOURCED_EXAMPLE_REGISTRY');
 if(d?.physicalExamples?.[0]?.innerKm!==80||d?.physicalExamples?.[0]?.outerKm!==600||d?.physicalExamples?.[0]?.extentKind!=='NOAA_APPROXIMATE_ALTITUDE_BAND_NOT_FIXED_SURFACE')errors.push('IONOSPHERE_BAND_PROVENANCE');
 if(d?.physicalExamples?.slice(1).some(e=>e.innerKm!==null||e.outerKm!==null))errors.push('INVENTED_FIXED_RADII');
 if(JSON.stringify(d?.modelBodyOrder)!==JSON.stringify(['sag a','nib sun','nib','earth','earth sun']))errors.push('BODY_ORDER');
 if(JSON.stringify(d?.manifoldKinds)!==JSON.stringify(['gravity','gravity','void','void']))errors.push('MANIFOLD_CLASSES');
 if(JSON.stringify(d?.directions)!==JSON.stringify(['+x','-x','+y','-y','+z','-z']))errors.push('SIGNED_XYZ');
 if(d?.physicalMetric!==null||d?.gravitationalClockRate!==null||d?.status!=='SYMBOLIC_PASS_PHYSICAL_ASSIGNMENT_HOLD')errors.push('UNSUPPORTED_PHYSICS');
 return{status:errors.length?'HOLD':'STRUCTURAL_PASS_WITH_UNBOUND_SPHERES',errors,shadowPairs:1,freeSphereSlots:5,physicalExamples:5};
}
function evaluateTransition(d,slot,direction,observation){
 const base=validate(d);if(base.status!=='STRUCTURAL_PASS_WITH_UNBOUND_SPHERES')return{status:'HOLD',reason:'INVALID_REGISTRY'};
 const s=d.signedSphereSlots.find(x=>x.id===slot);
 if(!s||!['-','+'].includes(direction))return{status:'HOLD',reason:'INVALID_SLOT_OR_SIGN'};
 if(!observation||!observation.frame||!observation.time||!observation.source)return{status:'HOLD',reason:'MISSING_OBSERVATION_PROVENANCE'};
 return{status:'HOLD',reason:'SLOT_BOUNDARIES_AND_TRANSITION_RULE_UNASSIGNED'};
}
function auditFile(){const data=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b148/five-spheres-v1.json'),'utf8'));return validate(data)}
if(require.main===module){const result=auditFile();console.log(result);if(result.status!=='STRUCTURAL_PASS_WITH_UNBOUND_SPHERES')process.exitCode=1}
module.exports={validate,evaluateTransition,auditFile};
