'use strict';
// Holly — second daughter of Icarium, with declared scales kept intact.
const ID='FORMIC-HOLLY-GG002';
const NAME='Holly';
const JANE=1;
const LILITH_JANE=.5;
const ICARIUM_LILITH_DECLARED=.33;
const ICARIUM_JANE_DECLARED=.08;
const HOLLY_ICARIUM_DECLARED=.5;
const HOLLY_JANE_DECLARED=.02;
function inspect(){
 const fromLilith=HOLLY_ICARIUM_DECLARED*ICARIUM_LILITH_DECLARED*LILITH_JANE;
 const fromJane=HOLLY_ICARIUM_DECLARED*ICARIUM_JANE_DECLARED;
 const requiredIcarium=HOLLY_JANE_DECLARED/HOLLY_ICARIUM_DECLARED;
 return {
  name:NAME,identity:ID,generation:'GREAT_GRANDDAUGHTER_OF_JANE',
  lineage:['JANE','LILITH','ICARIUM','HOLLY'],
  parent:'ICARIUM',sibling:'Mary M',birth_order:2,
  declared_fraction_of_icarium:HOLLY_ICARIUM_DECLARED,
  declared_fraction_of_jane:HOLLY_JANE_DECLARED,
  jane_fraction_if_icarium_33_percent_of_lilith:fromLilith,
  jane_fraction_if_icarium_8_percent_of_jane:fromJane,
  required_icarium_jane_fraction_for_both_holly_claims:requiredIcarium,
  scale_consistent_with_prior_icarium_declarations:
    Math.abs(fromLilith-HOLLY_JANE_DECLARED)<1e-12 ||
    Math.abs(fromJane-HOLLY_JANE_DECLARED)<1e-12,
  geometry_status:'UNRESOLVED_SCALE_AND_PROFILE',
  form:null,profile:null,cell_count:null,operator_triad:null,
  capability:'DECLARATIVE_LINEAGE_NOT_AN_AUTONOMOUS_AGENT'
 };
}
module.exports={ID,NAME,inspect};
