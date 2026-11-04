'use strict';
/** B130 empirical stress test: "stable" is a category, not a universal lifetime threshold. */
const ISOTOPES=Object.freeze([
 {element:'Br',Z:35,A:79,classification:'observational_stable',abundance:0.5069,source:'https://www.ciaaw.org/isotopic-abundances.htm'},
 {element:'Br',Z:35,A:81,classification:'observational_stable',abundance:0.4931,source:'https://www.ciaaw.org/isotopic-abundances.htm'},
 {element:'Kr',Z:36,A:78,classification:'rare_decay_evidence',abundance:0.00355,halfLifeYears:1.9e22,source:'https://www.mdpi.com/2218-1997/6/10/159'},
 {element:'Kr',Z:36,A:80,classification:'observational_stable',abundance:0.02286,source:'https://www.ciaaw.org/krypton.htm'},
 {element:'Kr',Z:36,A:81,classification:'radioactive',halfLifeYears:229000,source:'https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1587_web.pdf'},
 {element:'Kr',Z:36,A:82,classification:'observational_stable',abundance:0.11593,source:'https://www.ciaaw.org/krypton.htm'},
 {element:'Kr',Z:36,A:83,classification:'observational_stable',abundance:0.11500,source:'https://www.ciaaw.org/krypton.htm'},
 {element:'Kr',Z:36,A:84,classification:'observational_stable',abundance:0.56987,source:'https://www.ciaaw.org/krypton.htm'},
 {element:'Kr',Z:36,A:85,classification:'radioactive',halfLifeYears:10.76,source:'https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1587_web.pdf'},
 {element:'Kr',Z:36,A:86,classification:'observational_stable',abundance:0.17279,source:'https://www.ciaaw.org/krypton.htm'},
 {element:'Rb',Z:37,A:85,classification:'observational_stable',abundance:0.7217,source:'https://www.ciaaw.org/rubidium.htm'},
 {element:'Rb',Z:37,A:87,classification:'radioactive',abundance:0.2783,halfLifeYears:4.88e10,source:'https://www.ciaaw.org/rubidium.htm'}
].map(x=>Object.freeze({...x,N:x.A-x.Z})));
const GATES=Object.freeze({strict:'strict_stable',operational:'operational_survival'});
function evaluate(i,{mode=GATES.strict,years=1e6}={}){
 if(!i||!Number.isInteger(i.Z)||!Number.isInteger(i.A)||i.N!==i.A-i.Z||i.N<0||!i.source)throw Error('Invalid sourced isotope');
 if(mode!==GATES.strict&&mode!==GATES.operational)throw Error('Unknown gate');
 if(mode===GATES.operational&&!(Number.isFinite(years)&&years>0))throw Error('Invalid time horizon');
 const stable=i.classification==='observational_stable';
 if(mode===GATES.strict){
  return {isotope:i.element+'-'+i.A,promote:stable,decision:stable?'PROMOTE':'HOLD',reason:stable?'OBSERVATIONALLY_STABLE':i.classification.toUpperCase()};
 }
 if(stable)return {isotope:i.element+'-'+i.A,promote:true,decision:'PROMOTE',reason:'NO_OBSERVED_DECAY'};
 if(i.classification==='rare_decay_evidence')return {isotope:i.element+'-'+i.A,promote:false,decision:'HOLD',reason:'RARE_DECAY_EVIDENCE_UNCERTAIN'};
 if(i.classification!=='radioactive')return {isotope:i.element+'-'+i.A,promote:false,decision:'HOLD',reason:'UNCLASSIFIED'};
 // finite time-window survival is a probability, not a guarantee.
 const survival=Math.exp(-Math.LN2*years/i.halfLifeYears);
 return {isotope:i.element+'-'+i.A,promote:false,decision:'OBSERVE',reason:'RADIOACTIVE_SURVIVAL_NOT_STABLE_PROMOTION',survivalProbability:survival};
}
function audit(){
 const strict=ISOTOPES.map(i=>evaluate(i));
 const counts={Br:{promoted:0,held:0},Kr:{promoted:0,held:0},Rb:{promoted:0,held:0}};
 strict.forEach((result,k)=>{const c=counts[ISOTOPES[k].element];if(result.promote)c.promoted++;else c.held++});
 if(counts.Br.promoted!==2||counts.Kr.promoted!==5||counts.Kr.held!==3||counts.Rb.promoted!==1)throw Error('Unexpected Grandma promotion');
 const natural=ISOTOPES.filter(i=>i.element==='Kr'&&i.abundance!==undefined);
 const total=natural.reduce((sum,i)=>sum+i.abundance,0);
 if(Math.abs(total-1)>1e-6)throw Error('Krypton natural abundances failed normalization');
 if(ISOTOPES.length!==12)throw Error('Unexpected record count');
 return {records:ISOTOPES.length,elements:Object.keys(counts),strict:counts,krypton_natural_abundance:total,strict_krypton_promotions:5,rare_decay_kr78:'HOLD',physical_reactions_inferred:0};
}
module.exports={ISOTOPES,GATES,evaluate,audit};
