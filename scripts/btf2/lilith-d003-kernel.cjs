'use strict';
/** D003 Lilith: 20 cells organized on a 50%-Jane toroidal shell. */
const ROWS=Object.freeze([1,3,6,6,3,1]);
const JANE_MAX_DIAMETER=12;
const SCALE=1/2;
const OUTER_RADIUS=JANE_MAX_DIAMETER*SCALE/2; // 3 Jane-space units
const MAJOR_RADIUS=OUTER_RADIUS*3/4;             // 2.25
const MINOR_RADIUS=OUTER_RADIUS/4;               // 0.75
const TAU=2*Math.PI;
const ADDRESS='FORMIC-LILITH-D003';
function torus(theta,phi,R=MAJOR_RADIUS,r=MINOR_RADIUS){
 if(!(Number.isFinite(theta)&&Number.isFinite(phi)&&Number.isFinite(R)&&Number.isFinite(r)&&R>r&&r>0))throw Error('Invalid torus parameters');
 let a=R+r*Math.cos(theta);
 return {x:a*Math.cos(phi),y:r*Math.sin(theta),z:a*Math.sin(phi)};
}
function cells(){
 let result=[];
 for(let layer=0;layer<ROWS.length;layer++){
  let n=ROWS[layer],theta=TAU*(layer+0.5)/ROWS.length;
  for(let index=0;index<n;index++){
   let phi=TAU*(index+layer/12)/n;
   result.push({id:ADDRESS+':'+layer+':'+index,layer,index,layer_count:n,theta,phi,...torus(theta,phi),role:'TOROID_CELL',center:'|||0|||'});
  }
 }
 return result;
}
function audit(){
 const points=cells(),counts=ROWS.map((_,i)=>points.filter(c=>c.layer===i).length);
 const ids=new Set(points.map(c=>c.id));
 let result={identity:ADDRESS,profile:[...ROWS],layers:ROWS.length,cells:points.length,unique_addresses:ids.size,linear_scale:SCALE,jane_reference_diameter:JANE_MAX_DIAMETER,outer_diameter:2*OUTER_RADIUS,major_radius:MAJOR_RADIUS,minor_radius:MINOR_RADIUS,hole_radius:MAJOR_RADIUS-MINOR_RADIUS,layer_counts:counts};
 if(result.cells!==20||ids.size!==20||counts.some((n,i)=>n!==ROWS[i])||!(MAJOR_RADIUS>MINOR_RADIUS)||result.outer_diameter!==JANE_MAX_DIAMETER*SCALE)throw Error('D003 invariant failed');
 return result;
}
module.exports={ROWS,ADDRESS,SCALE,OUTER_RADIUS,MAJOR_RADIUS,MINOR_RADIUS,torus,cells,audit};
