'use strict';
// B127: explicit observed nuclear reactions versus catalogue traversal.
// Reaction participants carry (A,Z,Q,L) for baryon number, atomic/nuclear
// charge, electric charge and electron-family lepton number.
const PARTICLES=Object.freeze({
 H2:{A:2,Z:1,Q:1,L:0,label:'Deuterium-2',stable:true},
 H3:{A:3,Z:1,Q:1,L:0,label:'Tritium-3',stable:false},
 He3:{A:3,Z:2,Q:2,L:0,label:'Helium-3',stable:true},
 He4:{A:4,Z:2,Q:2,L:0,label:'Helium-4',stable:true},
 Be7:{A:7,Z:4,Q:4,L:0,label:'Beryllium-7',stable:false},
 Be9:{A:9,Z:4,Q:4,L:0,label:'Beryllium-9',stable:true},
 Li7:{A:7,Z:3,Q:3,L:0,label:'Lithium-7',stable:true},
 n:{A:1,Z:0,Q:0,L:0,label:'Neutron',stable:false},
 electron:{A:0,Z:null,Q:-1,L:1,label:'Electron'},
 antineutrino:{A:0,Z:null,Q:0,L:-1,label:'Electron antineutrino'},
 neutrino:{A:0,Z:null,Q:0,L:1,label:'Electron neutrino'},
 gamma:{A:0,Z:null,Q:0,L:0,label:'Gamma photon'}
});
const REFERENCES=Object.freeze([
 Object.freeze({Z:1,element:'Hydrogen',stable:Object.freeze(['H1','H2'])}),
 Object.freeze({Z:2,element:'Helium',stable:Object.freeze(['He3','He4'])}),
 Object.freeze({Z:3,element:'Lithium',stable:Object.freeze(['Li6','Li7'])}),
 Object.freeze({Z:4,element:'Beryllium',stable:Object.freeze(['Be9'])})
]);
const REACTIONS=Object.freeze([
 Object.freeze({id:'H3-BETA',type:'beta_minus',reactants:['H3'],products:['He3','electron','antineutrino'],promote:'Helium',evidence:'https://www.energy.gov/documents/doe-hdbk-1129-2008pdf',condition:'spontaneous tritium decay; half-life ~12.32 years'}),
 Object.freeze({id:'DT-FUSION',type:'fusion',reactants:['H2','H3'],products:['He4','n'],promote:'Helium',evidence:'https://www.fusionenergynews.com/kb/deuterium-tritium.html',condition:'fusion plasma; energy released ~17.6 MeV'}),
 Object.freeze({id:'HE3-HE4-CAPTURE',type:'fusion_capture',reactants:['He3','He4'],products:['Be7','gamma'],promote:null,evidence:'https://marvin.byu.edu/beryllium7/references/Solar/RepProgPhys-71-106201.pdf',condition:'proton-proton stellar chain, produces unstable Be-7; do not promote Be grandmother'}),
 Object.freeze({id:'BE7-E-CAPTURE',type:'electron_capture',reactants:['Be7','electron'],products:['Li7','neutrino'],promote:'Lithium',evidence:'https://marvin.byu.edu/beryllium7/references/Solar/RepProgPhys-71-106201.pdf',condition:'Be-7 electron capture produces stable Li-7'})
]);
function totals(parts){return parts.reduce((v,key)=>{const p=PARTICLES[key];if(!p)throw Error('Unknown particle '+key);v.A+=p.A;v.Q+=p.Q;v.L+=p.L;return v},{A:0,Q:0,L:0})}
function evaluate(reaction){
 const r=totals(reaction.reactants),p=totals(reaction.products);
 const balanced=r.A===p.A&&r.Q===p.Q&&r.L===p.L;
 const products=reaction.products.filter(x=>PARTICLES[x].Z!==null&&PARTICLES[x].Z>0);
 const targetProducts=products.map(x=>PARTICLES[x]);
 const validPromote=!reaction.promote||targetProducts.some(n=>n.stable&&REFERENCES.some(ref=>ref.element===reaction.promote&&ref.Z===n.Z));
 return {id:reaction.id,balanced,validPromote,reactants:r,products:p,handoff:reaction.promote||'NO_STABLE_GRANDMA_HANDOFF',documented:!!reaction.evidence};
}
function isotopeRecord(Z,A,status,evidence){if(!Number.isInteger(Z)||!Number.isInteger(A)||A<Z||Z<1)throw Error('Invalid nuclear address');return {Z,A,N:A-Z,status,evidence}}
function audit(){
 const checks=REACTIONS.map(evaluate);
 if(checks.some(x=>!x.balanced||!x.validPromote||!x.documented))throw Error('Reaction verification failure');
 if(REACTIONS[2].promote!==null)throw Error('Unstable Be7 cannot become stable Grandma');
 return {verified_records:checks.length,balanced:checks.every(c=>c.balanced),grandma_handoffs:['Helium','Lithium'],be7_unstable_intermediate:true,catalogue_edges_are_not_reactions:true,details:checks};
}
module.exports={PARTICLES,REFERENCES,REACTIONS,totals,evaluate,isotopeRecord,audit};
