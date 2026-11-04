'use strict';
const fs=require('node:fs'),path=require('node:path');
const bodies=['SAG A*','NIB SUN','NIBURU','EARTH SUN','EARTH'];
const edgeLabels=['x²','y²','z²','x²::y²','y²::z²','z²::x²'];
const key=(a,b)=>[a,b].sort().join('|');
function audit(d){
 const errors=[];
 if(d?.schema!=='JANE-B146-DISTANCE-GRAVITY-SOURCE-v1')errors.push('SCHEMA');
 if(d?.source?.sha256!=='b03110e432cd637314e9cfc7d16bdf6703dd8ca6ff46f2510ef3bf26fb6f6d50')errors.push('SOURCE_HASH');
 if(JSON.stringify(d?.bodyOrder)!==JSON.stringify(bodies))errors.push('BODY_ORDER');
 if(d?.origin!=='SAG A*'||JSON.stringify(d?.vertices)!==JSON.stringify(bodies.slice(0,4)))errors.push('VERTICES');
 if(d?.fields?.length!==4||d.fields.filter(f=>f.kind==='gravity').length!==2||d.fields.filter(f=>f.kind==='void').length!==2)errors.push('FIELDS');
 if(d?.userEdges?.length!==6||d.userEdges.some((e,i)=>e.notation!==edgeLabels[i]||!e.nonzeroGap))errors.push('SOURCE_EDGES');
 const found=new Set((d?.userEdges||[]).filter(e=>d.vertices?.includes(e.from)&&d.vertices?.includes(e.to)).map(e=>key(e.from,e.to)));
 const all=[];for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)all.push(key(d.vertices[i],d.vertices[j]));
 const missing=all.filter(p=>!found.has(p));
 if(found.size!==5||missing.length!==1||missing[0]!==key('NIB SUN','EARTH SUN'))errors.push('SOURCE_TOPOLOGY_DISCREPANCY_CHANGED');
 if(d?.measuredSeparationMeters!==null||d?.physicalMetric!==null||d?.physicalClockRate!==null)errors.push('UNVERIFIED_PHYSICS');
 if(d?.status!=='HOLD_TOPOLOGY_AND_PHYSICAL_MEASUREMENT')errors.push('UNWARRANTED_PROMOTION');
 return {status:errors.length?'HOLD':'SOURCE_STRUCTURE_PASS_WITH_CONFLICT',errors,sourceEdges:d?.userEdges?.length,vertexEdges:found.size,missingTetrahedronEdge:missing,physicalClockRate:'HOLD'};
}
if(require.main===module){const d=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../b146/distance-gravity-source-v1.json'),'utf8'));const report=audit(d);console.log(report);if(report.status==='HOLD')process.exitCode=1;}
module.exports={audit,key};
