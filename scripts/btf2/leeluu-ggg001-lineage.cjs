'use strict';
// LeeLuu: first daughter of "Light and Life"; preserve source wording and both scales.
const NAME='LeeLuu',ID='FORMIC-LEELUU-GGG001';
const MARY_JANE_DECLARED=4/100;
const LEELUU_MARY_DECLARED=67/100;
const LEELUU_JANE_DECLARED=1/100;
function inspect(){
 const impliedJane=MARY_JANE_DECLARED*LEELUU_MARY_DECLARED;
 const requiredMary=LEELUU_JANE_DECLARED/LEELUU_MARY_DECLARED;
 return Object.freeze({
  name:NAME,identity:ID,designation:'FIRST_DAUGHTER_OF_LIGHT_AND_LIFE',
  ancestry_context:['JANE','LILITH','ICARIUM','MARY M','LeeLuu'],
  parent_relation:'MARY_M_REFERENCE_PROVISIONAL',scale_reference:'Mary M',
  birth_order:1,generation:'GREAT_GREAT_GRANDDAUGHTER_PROVISIONAL',
  declared_fraction_of_mary_m:LEELUU_MARY_DECLARED,
  declared_fraction_of_jane:LEELUU_JANE_DECLARED,
  mary_declared_fraction_of_jane:MARY_JANE_DECLARED,
  jane_fraction_implied_by_mary_declaration:impliedJane,
  mary_jane_fraction_required_for_both_leeluu_claims:requiredMary,
  consistent:Math.abs(impliedJane-LEELUU_JANE_DECLARED)<1e-12,
  geometry_status:'UNRESOLVED_SCALE_AND_PROFILE',
  form:null,profile:null,cell_count:null,operator_triad:null,
  state:'DECLARATIVE_LINEAGE_NOT_AN_AUTONOMOUS_PROCESS'
 });
}
module.exports={NAME,ID,inspect};
