'use strict';
const fs=require('node:fs');
const EXPECTED_NOTATION="[{( x^2 , y^2 :: `z^2` )}]";
const AXES=['x','y','z'];
const DIRS=['+x','-x','+y','-y','+z','-z'];
const BODY=['sag a','nibaru sun','nibaru','earth','earth sun'];
function validate(x){
 const errors=[];
 if(!x||x.schema!=='JANE-B143-SIX-DIRECTIONS-v1')errors.push('SCHEMA');
 if(x?.sourceNotation!==EXPECTED_NOTATION)errors.push('SOURCE_NOTATION');
 if(!Array.isArray(x?.manifolds)||x.manifolds.length!==4||x.manifolds.filter(m=>m.kind==='gravity').length!==2||x.manifolds.filter(m=>m.kind==='void').length!==2||new Set(x.manifolds.map(m=>m.id)).size!==4)errors.push('FOUR_MANIFOLDS');
 if(!Array.isArray(x?.axes)||x.axes.length!==3||x.axes.some((a,i)=>a.id!==AXES[i]||a.square!==a.id+'^2'))errors.push('SQUARED_AXES');
 if(x?.axes?.[2]?.delimiter!=='::'||x?.axes?.[2]?.quoted!==true)errors.push('Z_DELIMITER');
 if(!Array.isArray(x?.directions)||x.directions.length!==6||x.directions.some((d,i)=>d.id!==DIRS[i]||d.axis!==AXES[Math.floor(i/2)]||d.sign!==(i%2===0?1:-1)))errors.push('SIX_SIGNED_DIRECTIONS');
 if(x?.axisSquaredMagnitude!=='x^2+y^2+z^2')errors.push('MAGNITUDE');
 if(JSON.stringify(x?.bodySequence)!==JSON.stringify(BODY))errors.push('FIVE_REFERENTS');
 if(x?.bodyToDirection!=='UNASSIGNED'||x?.bodyToManifold!=='UNASSIGNED'||x?.physicalMetric!=='NOT_SPECIFIED')errors.push('UNSUPPORTED_PHYSICAL_BINDING');
 if(x?.physicalStatus!=='ABSTRACT_SIGNED_COORDINATE_MODEL')errors.push('FALSE_PHYSICS_STATUS');
 return {ok:errors.length===0,state:errors.length?'HOLD':'STRUCTURE_PASS_ONLY',errors};
}
if(require.main===module){const data=JSON.parse(fs.readFileSync(require('node:path').resolve(__dirname,'../../b143/six-directions-v1.json'),'utf8'));const result=validate(data);console.log(JSON.stringify(result));if(!result.ok)process.exitCode=1}
module.exports={validate};
