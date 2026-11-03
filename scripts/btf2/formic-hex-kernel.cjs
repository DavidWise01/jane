'use strict';
// FORMIC B112: exact axial lattice only. No photon, optics or coverage models.
const crypto=require('node:crypto');
const DIRS=Object.freeze([[1,0],[1,-1],[0,-1],[-1,0],[-1,1],[0,1]]);
const mod=(a,m)=>((a%m)+m)%m;
const key=(q,r)=>q+','+r;
const distance=(a,b={q:0,r:0})=>(Math.abs(a.q-b.q)+Math.abs(a.q+a.r-b.q-b.r)+Math.abs(a.r-b.r))/2;
const color=(q,r)=>mod(q-r,3);
const identity=repo=>'FORMIC-'+crypto.createHash('sha256').update(repo.toLowerCase()).digest('hex').slice(0,16);
function* cells(){yield {q:0,r:0};for(let R=1;;R++){let q=-R,r=R;for(const [dq,dr] of DIRS){for(let i=0;i<R;i++){yield {q,r};q+=dq;r+=dr}}}}
function ringCount(R){if(!Number.isSafeInteger(R)||R<0)throw Error('radius must be a nonnegative safe integer');return R?6*R:1}
function diskCount(R){if(!Number.isSafeInteger(R)||R<0)throw Error('radius must be a nonnegative safe integer');return 1+3*R*(R+1)}
function neighbors(q,r){return DIRS.map(([a,b])=>({q:q+a,r:r+b}))}
function allocate(repos,old=[]){const prev=new Map(old.map(x=>[x.repo.toLowerCase(),x]));const used=new Set(old.map(x=>key(x.q,x.r)));const gen=cells();let cursor=gen.next();const take=()=>{while(!cursor.done&&used.has(key(cursor.value.q,cursor.value.r)))cursor=gen.next();if(cursor.done)throw Error('lattice exhausted');const p=cursor.value;used.add(key(p.q,p.r));cursor=gen.next();return p};
const out=[];for(const repo of [...new Set(repos.map(x=>String(x).trim()).filter(Boolean))].sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()))){const p=prev.get(repo.toLowerCase())||take();out.push({repo,formic:identity(repo),channel:'btf2:'+repo.toLowerCase(),q:p.q,r:p.r,sector:color(p.q,p.r),ring:distance(p),presence:'RESERVED'})}
return out}
module.exports={DIRS,mod,key,distance,color,identity,cells,ringCount,diskCount,neighbors,allocate};
