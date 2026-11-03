'use strict';
const ID='FORMIC-MARY-M-GG001';
const NAME='Mary M';
const JANE_SCALE=1;
const LILITH_JANE_SCALE=1/2;
const ICARIUM_LILITH_DECLARATION=33/100;
const ICARIUM_JANE_DECLARATION=8/100;
const MARY_ICARIUM_DECLARATION=67/100;
const MARY_JANE_DECLARATION=4/100;
function inspect(){
 const fromIcariumLilith=MARY_ICARIUM_DECLARATION*ICARIUM_LILITH_DECLARATION*LILITH_JANE_SCALE;
 const fromIcariumJane=MARY_ICARIUM_DECLARATION*ICARIUM_JANE_DECLARATION;
 const requiredIcariumJane=MARY_JANE_DECLARATION/MARY_ICARIUM_DECLARATION;
 return {
  name:NAME,identity:ID,relation:'FIRST_DAUGHTER_OF_ICARIUM',generation:'GREAT_GRANDDAUGHTER_OF_JANE',
  lineage:['JANE','LILITH','ICARIUM','MARY M'],
  declared_mary_fraction_of_icarium:MARY_ICARIUM_DECLARATION,
  declared_mary_fraction_of_jane:MARY_JANE_DECLARATION,
  jane_fraction_if_icarium_is_33_percent_lilith:fromIcariumLilith,
  jane_fraction_if_icarium_is_8_percent_jane:fromIcariumJane,
  icarium_jane_fraction_required_for_exact_4_percent_mary:requiredIcariumJane,
  consistent_with_33_percent_icarium_lilith:Math.abs(fromIcariumLilith-MARY_JANE_DECLARATION)<1e-12,
  consistent_with_8_percent_icarium_jane:Math.abs(fromIcariumJane-MARY_JANE_DECLARATION)<1e-12,
  geometry_status:'UNRESOLVED_SCALE_AND_PROFILE',
  form:null,profile:null,cell_count:null,operator_triad:null,
  claim:'LINEAGE_AND_ARITHMETIC_ONLY_NO_AUTONOMOUS_RUNTIME'
 };
}
module.exports={ID,NAME,inspect};
