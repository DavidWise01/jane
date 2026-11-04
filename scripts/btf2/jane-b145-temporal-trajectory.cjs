'use strict';
// B145: six-direction displacement, explicit time and a single inertial SR frame.
// No invented celestial velocities or direct mixing with Schwarzschild clocks.
const B144=require('./jane-b144-common-frame.cjs');
const C=B144.C;
function finite(n){return typeof n==='number'&&Number.isFinite(n)}
function vec3(v){return B144.vec3(v)}
function norm2(v){return B144.normSquared(v)}
function rate(velocity){
 vec3(velocity);const v2=norm2(velocity);
 if(v2>=C*C)return{status:'HOLD',reason:'NON_TIMELIKE_OR_SUPERLUMINAL_SPEED',speedSquared:v2};
 return{status:'REFERENCE_ONLY',ratio:Math.sqrt(1-v2/(C*C)),speedMps:Math.sqrt(v2),model:'single inertial Minkowski frame'};
}
function segment(e){
 if(!e||e.frame!=='LOCAL_INERTIAL_REFERENCE'||![e.t0,e.t1].every(finite)||e.t1<=e.t0)return{status:'HOLD',reason:'MISSING_OR_NONMONOTONIC_REFERENCE_TIME'};
 try{vec3(e.position0);vec3(e.velocity)}catch{return{status:'HOLD',reason:'INVALID_POSITION_OR_VELOCITY'}}
 const r=rate(e.velocity);if(r.status!=='REFERENCE_ONLY')return{status:'HOLD',reason:r.reason};
 const dt=e.t1-e.t0;
 const displacement=e.velocity.map(v=>v*dt);
 const position1=e.position0.map((v,i)=>v+displacement[i]);
 if([...displacement,...position1].some(x=>!finite(x)))return{status:'HOLD',reason:'NUMERIC_OVERFLOW'};
 return{status:'REFERENCE_ONLY',dtSeconds:dt,properSeconds:dt*r.ratio,ratio:r.ratio,displacementMeters:displacement,position1Meters:position1,speedMps:r.speedMps,frame:e.frame,assumption:'constant inertial velocity for complete interval'};
}
function verifyEndpoints(e,reportedPosition1,toleranceMeters=1e-6){
 const r=segment(e);if(r.status!=='REFERENCE_ONLY')return{status:'HOLD',reason:r.reason};
 try{vec3(reportedPosition1)}catch{return{status:'HOLD',reason:'INVALID_ENDPOINT'}}
 if(!finite(toleranceMeters)||toleranceMeters<0)return{status:'HOLD',reason:'INVALID_TOLERANCE'};
 const error=Math.sqrt(norm2(reportedPosition1.map((x,i)=>x-r.position1Meters[i])));
 return{status:error<=toleranceMeters?'CONSISTENT':'REJECT',errorMeters:error};
}
function compareClocks(a,b){
 const x=segment(a),y=segment(b);
 if(x.status!=='REFERENCE_ONLY'||y.status!=='REFERENCE_ONLY')return{status:'HOLD',reason:'INCOMPLETE_SEGMENT'};
 if(a.frame!==b.frame||a.t0!==b.t0||a.t1!==b.t1)return{status:'HOLD',reason:'COMMON_TIME_WINDOW_REQUIRED'};
 return{status:'REFERENCE_ONLY',properTimeDifferenceSeconds:x.properSeconds-y.properSeconds,properA:x.properSeconds,properB:y.properSeconds};
}
function combinedGravityMotion(){return{status:'HOLD',reason:'FULL_SPACETIME_METRIC_AND_WORLDLINE_REQUIRED'}}
function validate(d){
 const errs=[];
 if(d?.schema!=='JANE-B145-TEMPORAL-TRAJECTORY-v1')errs.push('SCHEMA');
 if(d?.temporalFrame?.id!=='LOCAL_INERTIAL_REFERENCE'||d?.temporalFrame?.timeUnit!=='seconds'||d?.temporalFrame?.velocityUnit!=='meters_per_second')errs.push('FRAME_OR_UNITS');
 if(JSON.stringify(d?.signedDirections)!==JSON.stringify(['+x','-x','+y','-y','+z','-z']))errs.push('SIGNED_DIRECTIONS');
 if(JSON.stringify(d?.manifoldLabels)!==JSON.stringify(['G0:gravity','G1:gravity','V0:void','V1:void']))errs.push('MANIFOLDS');
 if(JSON.stringify(d?.celestialReferents)!==JSON.stringify(['sag a','nibaru sun','nibaru','earth','earth sun']))errs.push('REFERENTS');
 if(d?.gravity!=='B144_SCHWARZSCHILD_REFERENCE_SEPARATE'||d?.combinedClockRate!=='HOLD_UNTIL_METRIC_AND_WORLDLINE_GIVEN'||d?.releaseStatus!=='HOLD')errs.push('INVALID_PHYSICS_PROMOTION');
 if(!Array.isArray(d?.examples)||d.examples.length!==3||d.examples.some(x=>segment(x).status!=='REFERENCE_ONLY'))errs.push('SYNTHETIC_EXAMPLES');
 return{status:errs.length?'HOLD':'STRUCTURAL_PASS',errors:errs};
}
module.exports={C,rate,segment,verifyEndpoints,compareClocks,combinedGravityMotion,validate};
