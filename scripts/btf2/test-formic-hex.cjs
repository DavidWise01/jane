#!/usr/bin/env node
'use strict';
const A=require('node:assert/strict'),K=require('./formic-hex-kernel.cjs');
const it=K.cells();for(let r=0;r<=20;r++){let seen=new Set();for(let i=0;i<K.ringCount(r);i++){let p=it.next().value;A.equal(K.distance(p),r);A.equal(seen.has(K.key(p.q,p.r)),false);seen.add(K.key(p.q,p.r));A.ok([0,1,2].includes(K.color(p.q,p.r)));for(let n of K.neighbors(p.q,p.r)){A.equal(K.distance(p,n),1);A.notEqual(K.color(p.q,p.r),K.color(n.q,n.r))}}A.equal(seen.size,K.ringCount(r));A.equal(K.diskCount(r),1+3*r*(r+1))}
const names=Array.from({length:2147},(_,i)=>'DavidWise01/test-'+i);const first=K.allocate(names);
A.equal(new Set(first.map(p=>K.key(p.q,p.r))).size,2147);
A.equal(new Set(first.map(p=>p.formic)).size,2147);
const second=K.allocate([...names,'DavidWise01/new-child'],first);
for(const x of first){const y=second.find(p=>p.repo===x.repo);A.equal(K.key(x.q,x.r),K.key(y.q,y.r))}
A.equal(second.length,2148);
console.log('PASS: radius 0–20; neighbor colors; 2147+1 family continuity');
