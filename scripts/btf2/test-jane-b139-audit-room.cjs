#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const h=fs.readFileSync('b139/index.html','utf8');
const required=['const names0=','const names1=','ROYAL PURPLE','active:index===15','canvas.addEventListener(\'click\'','jane-b139-viewer-snapshot.json','offline illustrative audit viewer','const families=','const reactions=','const controls=','wConflict','wMissing','modelSpread'];
for(const token of required)assert.ok(h.includes(token),'Missing B139 feature: '+token);
for(const tab of ['family','reaction','trainer','witness','control'])assert.ok(h.includes('data-tab="'+tab+'"'),'Missing tab '+tab);
assert.ok(h.includes('No auto-spawning of new Grandma'));
assert.ok(h.includes('No viewer interactions recorded.'));
assert.ok(h.includes('CIAAW'));
console.log('PASS B139: 5 audit views, two cubits, active Royal Purple, science warnings, witness controls, JSON export');
