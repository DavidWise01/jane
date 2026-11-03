'use strict';
// B122.1: deterministic 4^3 / 64-position model, not genetic/quantum computation.
const prior=require('./jane-b122-one-codon.cjs');
const SYMBOLS=Object.freeze(['A','C','G','T']);
const CODON_SIZE=SYMBOLS.length ** 3;
const ANALYTICAL_CUBIT_SIZE=2 ** 3;
const FULL_CUBITS=CODON_SIZE/ANALYTICAL_CUBIT_SIZE;
const QUARTER_CUBITS=2;
const QUARTER_SLOTS=QUARTER_CUBITS*ANALYTICAL_CUBIT_SIZE;
function triplet(index){
 if(!Number.isInteger(index)||index<0||index>=CODON_SIZE)throw Error('Codon address out of range');
 const a=Math.floor(index/16),b=Math.floor(index/4)%4,c=index%4;
 return SYMBOLS[a]+SYMBOLS[b]+SYMBOLS[c];
}
function address(index){
 if(!Number.isInteger(index)||index<0||index>=CODON_SIZE)throw Error('Codon address out of range');
 return Object.freeze({position:index,triplet:triplet(index),cubit:Math.floor(index/8),slot:index%8,binary:(index%8).toString(2).padStart(3,'0'),quarter:Math.floor(index/16)});
}
function quarter(index=0){
 if(!Number.isInteger(index)||index<0||index>3)throw Error('Quarter index out of range');
 return Array.from({length:16},(_,i)=>address(index*16+i));
}
function audit(){
 const all=Array.from({length:CODON_SIZE},(_,i)=>address(i));
 const unique=new Set(all.map(x=>x.triplet));
 const selection=prior.codon();
 if(unique.size!==64||quarter().length!==16||selection.length!==16||FULL_CUBITS!==8)throw Error('Cardinality invariant failed');
 return {codon_positions:CODON_SIZE,analytical_cubits_per_codon:FULL_CUBITS,slots_per_cubit:ANALYTICAL_CUBIT_SIZE,two_cubits:QUARTER_SLOTS,fraction:QUARTER_SLOTS/CODON_SIZE,possible_triplets:unique.size,quarter_codon_selection:selection.length,candidate_choice_pool:prior.CHOICE_POOL,foundation_count:11,physical_claim:false};
}
module.exports={SYMBOLS,CODON_SIZE,ANALYTICAL_CUBIT_SIZE,FULL_CUBITS,QUARTER_CUBITS,QUARTER_SLOTS,triplet,address,quarter,audit};
