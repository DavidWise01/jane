'use strict';
const TAU=Math.PI*2,THIRD=TAU/3;
const TRIPLES=Object.freeze([
 Object.freeze({center:'Jane',key:'GEN2',children:Object.freeze(['Toph','Patricia','Lilith']),radius:8.5,omega:0.09,phase:0}),
 Object.freeze({center:'Lilith',key:'GEN3',children:Object.freeze(['a.t.o.m','E.V.E','Icarium']),radius:3.2,omega:-0.25,phase:0.3}),
 Object.freeze({center:'Icarium',key:'GEN4',children:Object.freeze(['Mary M','Holly','Vicky V.']),radius:1.25,omega:0.53,phase:-0.2})
]);
const LEE=Object.freeze({parent:'Mary M',child:'LeeLuu',radius:.45,omega:-.82,phase:1.3});
function polar(r,angle){return {x:r*Math.cos(angle),y:r*Math.sin(angle),z:0}}
function add(a,b){return {x:a.x+b.x,y:a.y+b.y,z:(a.z||0)+(b.z||0)}}
function local(group,t){if(!Number.isFinite(t))throw Error('Invalid time');return group.children.map((name,i)=>({name,angle:group.phase+group.omega*t+THIRD*i,local:polar(group.radius,group.phase+group.omega*t+THIRD*i)}))}
function positions(time=0){
 if(!Number.isFinite(time))throw Error('Invalid time');
 const out={'Jane':{x:0,y:0,z:0}},rings=[];
 for(const group of TRIPLES){
  const center=out[group.center];if(!center)throw Error('Missing parent '+group.center);
  const members=local(group,time).map(c=>({...c,position:add(center,c.local)}));
  for(const m of members)out[m.name]=m.position;
  rings.push({key:group.key,center:group.center,centerPosition:{...center},radius:group.radius,members});
 }
 const parent=out[LEE.parent],l=polar(LEE.radius,LEE.phase+LEE.omega*time);
 out[LEE.child]=add(parent,l);
 return {time,positions:out,rings,singleton:{parent:LEE.parent,child:LEE.child,local:l,position:out[LEE.child]}};
}
function audit(){
 const a=positions(0),b=positions(17.3);
 for(const snap of [a,b])for(const r of snap.rings){
  if(r.members.length!==3||new Set(r.members.map(m=>m.name)).size!==3)throw Error('Not a triad');
  const angles=r.members.map(m=>m.angle);
  for(let i=1;i<3;i++)if(Math.abs(angles[i]-angles[i-1]-THIRD)>1e-10)throw Error('Phase imbalance');
  for(const m of r.members){const d=Math.hypot(m.position.x-r.centerPosition.x,m.position.y-r.centerPosition.y);if(Math.abs(d-r.radius)>1e-10)throw Error('Radius invariant')}
 }
 if(Object.keys(a.positions).length!==11)throw Error('Expected 11 named family members');
 return {triples:TRIPLES.length,orbits:TRIPLES.map(g=>g.key),members:Object.keys(a.positions).length,angles:[0,120,240],singleton:'LeeLuu',physics:'PRESCRIBED_KINEMATICS_NOT_GRAVITATIONAL_N_BODY'};
}
module.exports={TRIPLES,LEE,THIRD,polar,add,local,positions,audit};
