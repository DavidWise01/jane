'use strict';
// B128: documented nuclear-reaction branch growth. Logical catalogue, not a reactor.
const NUCLIDES=Object.freeze({
 H1:Object.freeze({Z:1,A:1,stable:true}),
 He4:Object.freeze({Z:2,A:4,stable:true}),
 Li7:Object.freeze({Z:3,A:7,stable:true}),
 Be8:Object.freeze({Z:4,A:8,stable:false}),
 B11:Object.freeze({Z:5,A:11,stable:true}),
 C12:Object.freeze({Z:6,A:12,stable:true}),
 O16:Object.freeze({Z:8,A:16,stable:true}),
 Ne20:Object.freeze({Z:10,A:20,stable:true}),
 gamma:Object.freeze({Z:0,A:0,stable:true})
});
const PATHS=Object.freeze([
 Object.freeze({id:'LI7-ALPHA-B11',inputs:['Li7','He4'],outputs:['B11','gamma'],target:'B11',evidence:'https://www.nndc.bnl.gov/ensdf/getrefs.jsp?dsid=7LI%28A%2CG%29+RES&recid=11005007',mechanism:'radiative alpha capture',context:'measured nuclear reaction; specific rates depend on incident energies'}),
 Object.freeze({id:'B11-P-C12',inputs:['B11','H1'],outputs:['C12','gamma'],target:'C12',evidence:'https://doi.org/10.1103/PhysRevC.109.014619',mechanism:'radiative proton capture',context:'measured reaction channel; competes with other channels'}),
 Object.freeze({id:'C12-ALPHA-O16',inputs:['C12','He4'],outputs:['O16','gamma'],target:'O16',evidence:'https://pubmed.ncbi.nlm.nih.gov/11327941/',mechanism:'radiative alpha capture',context:'important stellar helium-burning reaction'}),
 Object.freeze({id:'O16-ALPHA-NE20',inputs:['O16','He4'],outputs:['Ne20','gamma'],target:'Ne20',evidence:'https://www.sciencedirect.com/science/article/pii/S0924809906800296',mechanism:'radiative alpha capture',context:'stellar alpha-capture chain'}),
 Object.freeze({id:'HE4-HE4-BE8',inputs:['He4','He4'],outputs:['Be8'],target:'Be8',evidence:'https://www.sciencedirect.com/science/article/pii/S0924809906800296',mechanism:'unbound beryllium-8 resonance',context:'unstable triple-alpha intermediate, not stable Grandma'})
]);
function conserved(parts){
 return parts.reduce((acc,id)=>{const p=NUCLIDES[id];if(!p)throw Error('Unknown nuclide '+id);return {A:acc.A+p.A,Z:acc.Z+p.Z}}, {A:0,Z:0});
}
function inspect(path){
 const a=conserved(path.inputs),b=conserved(path.outputs);
 const target=NUCLIDES[path.target];
 if(!target)throw Error('Missing reaction target');
 return Object.freeze({id:path.id,balanced:a.A===b.A&&a.Z===b.Z,stable_target:target.stable,promote:target.stable?'NEW_GRANDMA':'INTERMEDIATE_ONLY',evidence:path.evidence,context:path.context});
}
function audit(){
 const results=PATHS.map(inspect);
 if(results.some(x=>!x.balanced||!x.evidence))throw Error('Reaction accounting failed');
 if(results.filter(x=>x.promote==='NEW_GRANDMA').length!==4||results.filter(x=>x.promote==='INTERMEDIATE_ONLY').length!==1)throw Error('Promotion contract failed');
 return {branch_paths:PATHS.length,new_stable_grandmas:4,unstable_intermediates:1,stable_products:['B11','C12','O16','Ne20'],reaction_edges_are_conditioned:true,conservation:'NUCLEON_AND_NUCLEAR_CHARGE_ONLY',physical_reaction_model:false,results};
}
module.exports={NUCLIDES,PATHS,conserved,inspect,audit};
