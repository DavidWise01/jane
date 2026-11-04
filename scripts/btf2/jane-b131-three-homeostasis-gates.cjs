'use strict';
// B131: three independent boundaries. Sources are published references;
// classifications are manually entered, not measured by this program.
const CASES=Object.freeze([
 {id:'KR84-GAS-ROOM',name:'Krypton-84 gas',Z:36,A:84,nuclear:'stable',chemical:'low_reactivity',environment:'room_temperature_inert_container',persistence:'pass',source:'https://pubchem.ncbi.nlm.nih.gov/element/36'},
 {id:'KR85-GAS-ROOM',name:'Krypton-85 gas',Z:36,A:85,nuclear:'radioactive',chemical:'low_reactivity',environment:'room_temperature_inert_container',persistence:'pass',source:'https://pubchem.ncbi.nlm.nih.gov/element/36'},
 {id:'KRF2-ROOM',name:'Krypton difluoride at room temperature',Z:36,A:84,nuclear:'stable',chemical:'high_oxidizing_reactivity',environment:'room_temperature',persistence:'fail',source:'https://www.acs.org/molecule-of-the-week/archive/k/krypton-difluoride.html'},
 {id:'KRF2-COLD',name:'Krypton difluoride at -78C',Z:36,A:84,nuclear:'stable',chemical:'high_oxidizing_reactivity',environment:'-78_celsius_appropriate_storage',persistence:'pass',source:'https://www.acs.org/molecule-of-the-week/archive/k/krypton-difluoride.html'},
 {id:'RB85-WATER',name:'Rubidium-85 metal in water',Z:37,A:85,nuclear:'stable',chemical:'high_water_reactivity',environment:'liquid_water',persistence:'fail',source:'https://cameochemicals.noaa.gov/report?key=CH1439'},
 {id:'RB85-ISOLATED',name:'Rubidium-85 metal isolated from water/air',Z:37,A:85,nuclear:'stable',chemical:'high_water_reactivity',environment:'protected_inert_storage',persistence:'pass',source:'https://cameochemicals.noaa.gov/report?key=CH1439'}
].map(c=>Object.freeze(c)));
const NUCLEAR_ALLOWED=new Set(['stable','radioactive','uncertain']);
const PERSISTENCE_ALLOWED=new Set(['pass','fail','unknown']);
function inspect(c){
 if(!c||!c.id||!Number.isInteger(c.Z)||!Number.isInteger(c.A)||c.A<c.Z||!NUCLEAR_ALLOWED.has(c.nuclear)||!PERSISTENCE_ALLOWED.has(c.persistence)||!c.chemical||!c.environment||!c.source)throw Error('Invalid sourced candidate');
 const nuclear=c.nuclear==='stable'?'PASS':c.nuclear==='radioactive'?'HOLD':'UNKNOWN';
 const chemical='CONTEXT_REQUIRED'; // reactivity alone never determines safety or persistence
 const environmental=c.persistence==='pass'?'PASS':c.persistence==='fail'?'FAIL':'UNKNOWN';
 const decision=nuclear==='PASS'&&environmental==='PASS'?'ELIGIBLE':environmental==='FAIL'?'NO_PROMOTION':'HOLD';
 return {id:c.id,nuclear,chemical,environmental,decision,Z:c.Z,N:c.A-c.Z,evidence:c.source};
}
function groupByNuclearIdentity(){
 const groups={};for(const c of CASES){const key=c.Z+':'+c.A;(groups[key]??=[]).push(inspect(c));}
 return groups;
}
function audit(){
 const results=CASES.map(inspect);
 if(results.length!==6)throw Error('Incorrect test set');
 if(results.filter(r=>r.decision==='ELIGIBLE').length!==3)throw Error('Eligible count mismatch');
 if(results.filter(r=>r.decision==='NO_PROMOTION').length!==2)throw Error('Failure count mismatch');
 if(results.filter(r=>r.decision==='HOLD').length!==1)throw Error('Hold count mismatch');
 const kr84=results.filter(r=>r.Z===36&&r.N===48);
 if(kr84.length!==3||new Set(kr84.map(x=>x.environmental)).size!==2)throw Error('Environment independent invariant failed');
 return {cases:6,eligible:3,no_promotion:2,hold:1,independent_domains:['nuclear','chemical','environment'],nuclear_charge_changes:0,manual_sources_only:true,outputs:results};
}
module.exports={CASES,inspect,groupByNuclearIdentity,audit};
