'use strict';
const fs=require('node:fs'),path=require('node:path');
const ORDER=['sag a','nib sun','nib','earth','earth sun'];
const PAIRS=[[0,1],[1,2],[2,3],[3,4],[0,2],[0,3]];
const NOTATIONS=['x²','y²','z²','x²::y²','y²::z²','z²::x²'];
function pairKey(a,b){return[a,b].sort().join('|')}
function inspect(d){
 const errors=[];
 if(d?.schema!=='JANE-B146.2-NATURAL-POSITIONAL-REMAP-v1'||d.method!=='POSITIONAL_INDEX_PRESERVING')errors.push('SCHEMA_OR_METHOD');
 if(JSON.stringify(d?.canonicalOrder)!==JSON.stringify(ORDER))errors.push('CANONICAL_ORDER');
 if(JSON.stringify(d?.coreVertices)!==JSON.stringify(ORDER.slice(0,4))||d?.terminalReferent!==ORDER[4])errors.push('CORE_OR_TERMINAL');
 if(d?.manifolds?.length!==4||d.manifolds.filter(m=>m.kind==='gravity').length!==2||d.manifolds.filter(m=>m.kind==='void').length!==2)errors.push('MANIFOLDS');
 if(JSON.stringify(d?.directions)!==JSON.stringify(['+x','-x','+y','-y','+z','-z']))errors.push('SIGNED_DIRECTIONS');
 if(!Array.isArray(d?.edges)||d.edges.length!==6)errors.push('EDGE_COUNT');
 else for(let i=0;i<6;i++){
  const e=d.edges[i], p=PAIRS[i];
  if(!e||e.from!==ORDER[p[0]]||e.to!==ORDER[p[1]]||e.notation!==NOTATIONS[i]||e.sourceEdgeId!=='u'+(i+1)||e.sourcePosition!==i+1||e.classification!==(i===3?'TERMINAL_LINK':'CORE_EDGE')||!e.nonzeroGap)errors.push('SLOT_'+(i+1));
 }
 const coreKeys=new Set((d?.edges||[]).filter(e=>e.classification==='CORE_EDGE').map(e=>pairKey(e.from,e.to)));
 const full=[];for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)full.push(pairKey(ORDER[i],ORDER[j]));
 const missing=full.filter(k=>!coreKeys.has(k));
 if(coreKeys.size!==5||missing.length!==1||missing[0]!==pairKey('nib sun','earth'))errors.push('TETRAHEDRON_DISCREPANCY');
 if(d?.tetrahedron?.resolution!=='HOLD_UNSPECIFIED'||d?.tetrahedron?.presentCoreEdges!==5||d?.tetrahedron?.requiredCoreEdges!==6)errors.push('UNSUPPORTED_TETRAHEDRON_FIX');
 if(d?.distanceValuesMeters!==null||d?.physicalMetric!==null||d?.clockPrediction!==null||d?.decision!=='STRUCTURAL_REMAP_ONLY_PHYSICS_HOLD')errors.push('PHYSICS_PROMOTION');
 return{status:errors.length?'HOLD':'REMAP_STRUCTURE_PASS',errors,coreEdges:coreKeys.size,terminalEdges:(d?.edges||[]).filter(e=>e.classification==='TERMINAL_LINK').length,missingCoreEdges:missing};
}
function inspectFiles(){
 const base=path.resolve(__dirname,'../../b146');
 return inspect(JSON.parse(fs.readFileSync(path.join(base,'natural-remap-v1.json'),'utf8')));
}
if(require.main===module){const r=inspectFiles();console.log(JSON.stringify(r));if(r.status!=='REMAP_STRUCTURE_PASS')process.exitCode=1}
module.exports={inspect,inspectFiles,pairKey};
