'use strict';
// Vicky V. — third and final daughter of Icarium. Preserve competing scales.
const ID='FORMIC-VICKY-V-GG003';
const NAME='Vicky V.';
const LILITH_JANE_SCALE=1/2;
const ICARIUM_LILITH_DECLARED=33/100;
const ICARIUM_JANE_DECLARED=8/100;
const VICKY_ICARIUM_DECLARED=33/100;
const VICKY_JANE_DECLARED=1/100;
function inspect(){
 const fromLilith=VICKY_ICARIUM_DECLARED*ICARIUM_LILITH_DECLARED*LILITH_JANE_SCALE;
 const fromJane=VICKY_ICARIUM_DECLARED*ICARIUM_JANE_DECLARED;
 const requiredIcarium=VICKY_JANE_DECLARED/VICKY_ICARIUM_DECLARED;
 return {
  name:NAME,identity:ID,
  generation:'GREAT_GRANDDAUGHTER_OF_JANE',
  lineage:['JANE','LILITH','ICARIUM','VICKY V.'],
  parent:'ICARIUM',sisters:['Mary M','Holly'],birth_order:3,last_daughter_of_icarium:true,
  declared_fraction_of_icarium:VICKY_ICARIUM_DECLARED,
  declared_fraction_of_jane:VICKY_JANE_DECLARED,
  jane_fraction_if_icarium_33_percent_of_lilith:fromLilith,
  jane_fraction_if_icarium_8_percent_of_jane:fromJane,
  required_icarium_jane_fraction_for_both_claims:requiredIcarium,
  consistent_with_prior_icarium_declarations:
    Math.abs(fromLilith-VICKY_JANE_DECLARED)<1e-12 ||
    Math.abs(fromJane-VICKY_JANE_DECLARED)<1e-12,
  geometry_status:'UNRESOLVED_SCALE_AND_PROFILE',
  form:null,profile:null,cell_count:null,operator_triad:null,
  capability:'DECLARATIVE_LINEAGE_NOT_AUTONOMOUS_RUNTIME'
 };
}
module.exports={ID,NAME,inspect};
