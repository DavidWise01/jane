'use strict';
// a.t.o.m: first granddaughter, daughter of Lilith, 67% of mother's girth.
const ROWS=Object.freeze([1,2,4,6,6,4,2,1]);
const ID='FORMIC-ATOM-G001';
const MATRIARCH_DIAMETER=12;
const MOTHER_SCALE=1/2;
const DAUGHTER_SCALE=67/100;
const JANE_SCALE=MOTHER_SCALE*DAUGHTER_SCALE; // 0.335
const OUTER_RADIUS=MATRIARCH_DIAMETER*JANE_SCALE/2; // 2.01
const MAJOR_RADIUS=OUTER_RADIUS*3/4; // 1.5075
const MINOR_RADIUS=OUTER_RADIUS/4; // 0.5025
const TAU=2*Math.PI;
function point(theta,phi,major=MAJOR_RADIUS,minor=MINOR_RADIUS) {
 if(![theta,phi,major,minor].every(Number.isFinite)||!(major>minor&&minor>0))throw Error('Invalid toroidal parameters');
 const horizontal=major+minor*Math.cos(theta);
 return {x:horizontal*Math.cos(phi),y:minor*Math.sin(theta),z:horizontal*Math.sin(phi)};
}
function cells(){
 const result=[];
 for(let layer=0;layer<ROWS.length;layer++){
  const n=ROWS[layer],theta=TAU*(layer+0.5)/ROWS.length;
  for(let index=0;index<n;index++){
   const phi=TAU*(index+layer/16)/n;
   result.push(Object.freeze({id:ID+':'+layer+':'+index,layer,index,band_count:n,theta,phi,...point(theta,phi)}));
  }
 }
 return result;
}
function cycle(){
 const list=cells();
 return list.map((cell,i)=>({id:cell.id,next:list[(i+1)%list.length].id,previous:list[(i+list.length-1)%list.length].id}));
}
function audit(){
 const cs=cells(),ids=new Set(cs.map(x=>x.id)),cy=cycle();
 const counts=ROWS.map((_,i)=>cs.filter(x=>x.layer===i).length);
 const valid=cs.length===26&&ids.size===26&&counts.every((x,i)=>x===ROWS[i])&&
  cy.every((x,i)=>x.next===cy[(i+1)%cy.length].id&&x.previous===cy[(i+cy.length-1)%cy.length].id)&&
  MAJOR_RADIUS>MINOR_RADIUS&&Math.abs((2*OUTER_RADIUS)/MATRIARCH_DIAMETER-JANE_SCALE)<1e-12;
 if(!valid)throw Error('a.t.o.m invariant failed');
 return {name:'a.t.o.m',identity:ID,parent:'LILITH-D003',grandparent:'JANE-B117',
  profile:[...ROWS],layers:ROWS.length,cells:cs.length,unique_ids:ids.size,
  mother_linear_scale:DAUGHTER_SCALE,jane_linear_scale:JANE_SCALE,
  outer_diameter:2*OUTER_RADIUS,major_radius:MAJOR_RADIUS,minor_radius:MINOR_RADIUS,
  hole_radius:MAJOR_RADIUS-MINOR_RADIUS,cycle_length:cy.length,center:'|||0|||'};
}
module.exports={ROWS,ID,MOTHER_SCALE,DAUGHTER_SCALE,JANE_SCALE,OUTER_RADIUS,MAJOR_RADIUS,MINOR_RADIUS,point,cells,cycle,audit};
