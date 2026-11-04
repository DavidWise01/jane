'use strict';
const fs=require('node:fs');
const CANON='[{( -+ 4 manifolds, 2 gravity , 2 void, planets are sag a , nibaru sun , nibaru , earth , earth sun +- )}]';
const LABELS=['sag a','nibaru sun','nibaru','earth','earth sun'];
function validate(d){
 const errors=[];
 if(!d||d.schema!=='JANE-B142-FOUR-MANIFOLD-BOUNDARY-v1')errors.push('SCHEMA_MISMATCH');
 if(d?.notation!==CANON)errors.push('SOURCE_NOTATION_CHANGED');
 if(!Array.isArray(d?.container?.manifolds)||d.container.manifolds.length!==4)errors.push('FOUR_MANIFOLDS_REQUIRED');
 else{
  const m=d.container.manifolds;
  if(m.filter(x=>x.kind==='gravity').length!==2||m.filter(x=>x.kind==='void').length!==2)errors.push('TWO_GRAVITY_TWO_VOID_REQUIRED');
  if(new Set(m.map(x=>x.id)).size!==4)errors.push('DUPLICATE_MANIFOLD');
 }
 if(!Array.isArray(d?.container?.polarity)||d.container.polarity.join('')!=='-+')errors.push('SIGN_INVARIANT');
 if(!Array.isArray(d?.bodySequence)||d.bodySequence.length!==5||d.bodySequence.some((x,i)=>x.label!==LABELS[i]))errors.push('BODY_SEQUENCE_CHANGED');
 if(d?.bodyToManifold!=='UNASSIGNED')errors.push('UNSUPPORTED_BODY_MANIFOLD_ASSIGNMENT');
 if(d?.gravitationalGeometry!=='MODEL_HYPOTHESIS_UNVALIDATED')errors.push('UNSUPPORTED_PHYSICS_CLAIM');
 return {ok:errors.length===0,status:errors.length?'HOLD':'STRUCTURAL_PASS_ONLY',errors};
}
if(require.main===module){
 const document=JSON.parse(fs.readFileSync(require('node:path').resolve(__dirname,'../../b142/four-manifold-boundary-v1.json'),'utf8'));
 const r=validate(document);console.log(r);if(!r.ok)process.exitCode=1;
}
module.exports={validate,CANON,LABELS};
