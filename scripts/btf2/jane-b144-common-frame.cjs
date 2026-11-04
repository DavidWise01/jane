'use strict';
/* B144: A shared axis frame with separate, limited Schwarzschild reference.
   A model with four *labels* and six signed spatial directions is not a
   four-manifold solution of the Einstein field equations. */
const fs=require('node:fs'),path=require('node:path');
const C=299792458,G=6.67430e-11;
const signed=Object.freeze({ 'x+':[1,0,0],'x-':[-1,0,0],'y+':[0,1,0],'y-':[0,-1,0],'z+':[0,0,1],'z-':[0,0,-1] });
function vec3(v){if(!Array.isArray(v)||v.length!==3||v.some(n=>!Number.isFinite(n)))throw Error('FINITE_VECTOR3_REQUIRED');return v;}
function step(position,code,magnitude=1){
 vec3(position);
 if(!Object.hasOwn(signed,code)||!Number.isFinite(magnitude)||magnitude<0)throw Error('SIGNED_DIRECTION_OR_MAGNITUDE_INVALID');
 const delta=signed[code];return position.map((x,i)=>x+delta[i]*magnitude);
}
function normSquared(position){return vec3(position).reduce((s,v)=>s+v*v,0)}
function translate(position,origin=[0,0,0]){vec3(origin);return vec3(position).map((x,i)=>x-origin[i])}
function roundTrip(position,axis,magnitude){const p=step(position,axis+'+',magnitude);return step(p,axis+'-',magnitude)}
function schwarzschildStationaryRate({massKg,radiusM}={}){
 if(!Number.isFinite(massKg)||massKg<=0||!Number.isFinite(radiusM)||radiusM<=0)return{status:'HOLD',reason:'MASS_RADIUS_REQUIRED'};
 const rs=2*G*massKg/(C*C),q=1-rs/radiusM;
 if(!(q>0))return{status:'HOLD',reason:'OUTSIDE_EXTERIOR_STATIC_CLOCK_DOMAIN',schwarzschildRadiusM:rs};
 return{status:'REFERENCE_ONLY',ratio:Math.sqrt(q),schwarzschildRadiusM:rs,model:'stationary Schwarzschild exterior, isolated nonrotating spherical mass'};
}
function validate(spec){
 const errors=[];
 if(spec?.schema!=='JANE-B144-COMMON-FRAME-v1')errors.push('SCHEMA');
 const frame=spec?.coordinateFrame;
 if(!frame||JSON.stringify(frame.origin)!=='[0,0,0]'||JSON.stringify(frame.axes)!=='["x","y","z"]')errors.push('FRAME');
 if(!frame?.directions||Object.keys(frame.directions).length!==6||Object.keys(signed).some(k=>JSON.stringify(frame.directions[k])!==JSON.stringify(signed[k])))errors.push('DIRECTIONS');
 if(!Array.isArray(spec?.manifoldLabels)||spec.manifoldLabels.length!==4||spec.manifoldLabels.filter(x=>x.kind==='gravity').length!==2||spec.manifoldLabels.filter(x=>x.kind==='void').length!==2)errors.push('MANIFOLD_COUNTS');
 if(JSON.stringify(spec?.referents)!==JSON.stringify(['sag a','nibaru sun','nibaru','earth','earth sun']))errors.push('REFERENT_ORDER');
 if(!spec?.mappings||Object.values(spec.mappings).some(v=>!['UNASSIGNED','UNSPECIFIED'].includes(v)))errors.push('UNVERIFIED_MAPPING');
 if(spec?.clockReference?.model!=='SCHWARZSCHILD_STATIONARY_EXTERIOR'||spec?.releaseStatus!=='HOLD')errors.push('PHYSICS_OR_RELEASE_OVERCLAIM');
 return{status:errors.length?'HOLD':'STRUCTURAL_PASS',errors};
}
if(require.main===module){
 const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b144/coordinate-frame-v1.json'),'utf8'));
 const v=validate(d);console.log(v);if(v.status!=='STRUCTURAL_PASS')process.exitCode=1;
}
module.exports={C,G,signed,vec3,step,normSquared,translate,roundTrip,schwarzschildStationaryRate,validate};
