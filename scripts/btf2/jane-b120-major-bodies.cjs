'use strict';
const TAU=Math.PI*2,ORBIT_RADIUS=13.5,OMEGA=.12;
const BODY_SPECS=Object.freeze([
 Object.freeze({name:'Jane',id:'JANE-B117',role:'Matriarch',discipline:'Governance',form:'diatom',scale:1,rows:Object.freeze([1,2,4,6,8,12,12,8,6,4,2,1]),orbitIndex:-1}),
 Object.freeze({name:'Toph',id:'TOPH-D001',role:'Scholar',discipline:'Learning',form:'diatom',scale:.67,rows:Object.freeze([1,3,6,9,11,11,9,6,3,1]),orbitIndex:0}),
 Object.freeze({name:'Patricia',id:'PATRICIA-D002',role:'Guardian',discipline:'Containment',form:'boxed-toroid',scale:.5,rows:Object.freeze([1,2,4,6,8,8,6,4,2,1]),orbitIndex:1}),
 Object.freeze({name:'Lilith',id:'LILITH-D003',role:'Muse',discipline:'Topology',form:'toroid',scale:.5,rows:Object.freeze([1,3,6,6,3,1]),orbitIndex:2})
]);
function counts(rows){return rows.reduce((a,b)=>a+b,0)}
function lattice(spec){
 const cells=[];
 for(let layer=0;layer<spec.rows.length;layer++){
  const n=spec.rows[layer],theta=TAU*(layer+.5)/spec.rows.length;
  for(let index=0;index<n;index++){
   let position;
   if(spec.form==='toroid'){
    const major=4.5*spec.scale,minor=1.5*spec.scale;
    const phi=TAU*(index+layer/(spec.rows.length*2))/n;
    const q=major+minor*Math.cos(theta);
    position={x:q*Math.cos(phi),y:minor*Math.sin(theta),z:q*Math.sin(phi)};
   } else if(spec.form==='boxed-toroid'){
    const max=Math.max(...spec.rows),width=12*spec.scale*(n/max),offset=n===1?0:index/(n-1)-.5;
    position={x:width*offset,y:12*spec.scale*(layer/(spec.rows.length-1)-.5),z:0};
   } else {
    const radius=6*spec.scale*n/Math.max(...spec.rows),phi=TAU*(index/n+layer*.071);
    position={x:n===1?0:radius*Math.cos(phi),y:12*spec.scale*(layer/(spec.rows.length-1)-.5),z:n===1?0:radius*Math.sin(phi)};
   }
   cells.push({id:spec.id+':'+layer+':'+index,layer,index,...position});
  }
 }
 return cells;
}
function orbit(t=0){
 if(!Number.isFinite(t))throw Error('Invalid time');
 return BODY_SPECS.map(b=>{
  if(b.orbitIndex<0)return {name:b.name,phase:null,center:{x:0,y:0,z:0}};
  const phase=OMEGA*t+TAU*b.orbitIndex/3;
  return{name:b.name,phase,center:{x:ORBIT_RADIUS*Math.cos(phase),y:0,z:ORBIT_RADIUS*Math.sin(phase)}};
 });
}
function audit(){
 const expected=[66,60,42,20],names=['Jane','Toph','Patricia','Lilith'];
 if(BODY_SPECS.length!==4)throw Error('Invalid number of bodies');
 BODY_SPECS.forEach((b,i)=>{
  if(b.name!==names[i]||counts(b.rows)!==expected[i])throw Error('Invalid body profile');
  const cells=lattice(b);
  if(cells.length!==expected[i]||new Set(cells.map(c=>c.id)).size!==cells.length)throw Error('Invalid cell IDs');
 });
 for(const t of [0,1,19.37]){
  const positions=orbit(t);
  const phases=positions.slice(1).map(p=>p.phase);
  if(phases.some((p,i)=>i>0&&Math.abs(p-phases[i-1]-TAU/3)>1e-10))throw Error('Not 120-degree');
  const r=positions.slice(1);
  for(const p of r)if(Math.abs(Math.hypot(p.center.x,p.center.z)-ORBIT_RADIUS)>1e-9)throw Error('Bad radius');
  if(!(ORBIT_RADIUS>6+6*.67))throw Error('Collision with Jane envelope');
  if(!(ORBIT_RADIUS*Math.sqrt(3)>6*.67+6*.5))throw Error('Sibling envelope overlap');
 }
 return {body_count:BODY_SPECS.length,orbiting_bodies:3,cell_count:BODY_SPECS.reduce((a,b)=>a+counts(b.rows),0),cell_counts:expected,names,phase_step_degrees:120,orbit_radius:ORBIT_RADIUS,descendants_rendered:0,hard_stop:true,physics:'KINEMATIC_VISUALIZATION'};
}
module.exports={BODY_SPECS,TAU,ORBIT_RADIUS,OMEGA,counts,lattice,orbit,audit};
