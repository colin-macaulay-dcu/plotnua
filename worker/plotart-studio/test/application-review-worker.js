// LOCAL TEST ENTRY POINT ONLY: never deployed.
import * as R from '../src/gallery-application-review.js';
export default {async fetch(req,env){try{const b=await req.json();const v=b.op==='get'?await R.getReview(env,b.ref):b.op==='retry'?await R.retryReview(env,b.ref,b.id):await R.saveReview(env,b.ref,b.body,'founder@plotnua.invalid');return Response.json({ok:true,value:v});}catch(e){return Response.json({ok:false,error:e.message},{status:e.status||500});}}};
