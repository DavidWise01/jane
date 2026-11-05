'use strict';
/* B169 autonomous read-only scan of committed proof envelopes, no synthetic proofs. */
const fs=require('node:fs'),path=require('node:path');
const {inspect,report}=require('./jane-b169-drift-and-ci.cjs');
const {audit}=require('./jane-b168-proof-proposal.cjs');
const DIR='ecosystem/proposals',MAX=8;
function candidates(dir=DIR){
 if(!fs.existsSync(dir))return{status:'HOLD_NO_PROPOSALS',files:[]};
 const entries=fs.readdirSync(dir,{withFileTypes:true});
 const json=entries.filter(e=>e.isFile()&&/^[A-Za-z0-9_.-]+[.]json$/.test(e.name)).map(e=>path.join(dir,e.name)).sort();
 if(json.length>MAX)return{status:'HOLD_TOO_MANY_PROPOSALS',files:[]};
 return{status:json.length?'CANDIDATES_PRESENT':'HOLD_NO_PROPOSALS',files:json};
}
async function run({dir=DIR,token='',inspectFn=inspect}={}){
 const found=candidates(dir),rows=[];
 if(found.status==='HOLD_TOO_MANY_PROPOSALS')return{...report([]),status:found.status};
 for(const name of found.files){
  try{
   const data=JSON.parse(fs.readFileSync(name,'utf8'));
   if(audit(data).status!=='PASS'){
    rows.push({repository:data?.envelope?.repository||null,status:'HOLD',reasons:['INVALID_PROOF'],mayCreatePR:false});
   }else rows.push(await inspectFn(data,token));
  }catch{rows.push({repository:null,status:'HOLD',reasons:['PROPOSAL_READ_ERROR'],mayCreatePR:false})}
 }
 const result=report(rows);result.status=found.status;return result;
}
async function main(){
 const args=process.argv.slice(2),i=args.indexOf('--output'),dest=i>=0?args[i+1]:'ecosystem/reports/b169-latest.json';
 if(!dest)throw Error('OUTPUT_REQUIRED');
 const result=await run({token:process.env.GITHUB_TOKEN||''});
 fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,counts:result.counts,automaticWrites:false}));
}
if(require.main===module)main().catch(e=>{console.error('HOLD '+e.message);process.exitCode=1});
module.exports={candidates,run};
