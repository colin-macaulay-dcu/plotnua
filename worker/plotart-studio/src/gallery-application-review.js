/* Private Gallery Artist review workflow. D1 serialises each application across isolates;
 * R2 retains snapshots inside the application's existing erasure boundary. */
import { send } from './mailer.js';
const REF = /^PA-AP-\d{6}-[0-9A-F]{6}$/;
const PROTECTED = 'PA-AP-261116-7C1EB4';
const FINAL = new Set(['accepted','declined','withdrawn']);
const STATES = new Set(['received','under_review','info_requested',...FINAL]);
const BASE = 'appS4gWOxuZqJyWvU', TABLE = 'tblEQ8CiXFWMlWqsE';
const stamp = () => new Date().toISOString();
const fail = (message,status=409) => Object.assign(new Error(message),{status});
const sql = (env,q,...args) => env.DB.prepare(q).bind(...args);
const one = (env,q,...args) => sql(env,q,...args).first();
const root = ref => `applications/${ref}/`;
export async function digest(value) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value))),x=>x.toString(16).padStart(2,'0')).join('');
}
function check(ref,write=false) {
  if (!REF.test(ref)) throw fail('Invalid application reference',400);
  if (write && ref===PROTECTED) throw fail('This existing application is protected');
}
export function reviewConfigured(env) { return !!((env.PLOTART_REVIEW_AIRTABLE_TOKEN || env.APPLICATION_REGISTER) && env.DB && env.APPLICATIONS); }
async function register(env,path='',options={}) {
  if (!reviewConfigured(env)) throw fail('Application review is not configured',503);
  const init={...options,headers:{'Content-Type':'application/json'},signal:AbortSignal.timeout(10000)};
  const r=env.APPLICATION_REGISTER
    ? await env.APPLICATION_REGISTER.fetch(new Request('https://application-register.internal'+(path||'/'),init))
    : await fetch(`https://api.airtable.com/v0/${BASE}/${TABLE}${path}`,{...init,headers:{...init.headers,Authorization:`Bearer ${env.PLOTART_REVIEW_AIRTABLE_TOKEN}`}});
  if(!r.ok)throw fail(`Application register unavailable (${r.status})`,502);
  return r.json();
}
async function stored(env,ref) {
  const o=await env.APPLICATIONS.get(root(ref)+'application.json');
  if(!o)throw fail('Application review copy unavailable',404);
  const a=JSON.parse(await o.text());
  if(a.application_ref!==ref || !/^rec[A-Za-z0-9]{14}$/.test(a.airtable_record||''))throw fail('Application identity mismatch');
  return a;
}
async function record(env,ref) {
  check(ref);
  const a=await stored(env,ref), row=await register(env,'/'+a.airtable_record);
  if(row.fields?.application_ref!==ref || !STATES.has(row.fields.status))throw fail('Application register identity or status mismatch');
  return {a,row};
}
async function state(env,ref) {
  await sql(env,'INSERT OR IGNORE INTO application_review(ref) VALUES (?)',ref).run();
  return one(env,'SELECT * FROM application_review WHERE ref=?',ref);
}
export async function getReview(env,ref) {
  const {row}=await record(env,ref);
  const s=await one(env,'SELECT * FROM application_review WHERE ref=?',ref);
  const history=await sql(env,'SELECT id,kind,actor,phase,created_at,sent_at,completed_at,error,payload FROM application_review_actions WHERE ref=? ORDER BY created_at',ref).all();
  return {...row.fields,ref,id:undefined,protected:ref===PROTECTED,revision:s?.revision||0,revised_at:s?.revised_at||null,snapshots:Array.from({length:(s?.revision||0)+1},(_,i)=>i),
    pending_action:s?.active_action||null,history:history.results.map(({payload,...h})=>{const p=JSON.parse(payload);return {...h,message:p.message||'',notes:p.notes||'',reason:p.reason||''};})};
}
function text(v,max,label,required=false) {
  if(typeof v!=='string'||v.length>max||(required&&!v.trim()))throw fail('Invalid '+label,400);
  return v.trim();
}
function mailReady(env) {
  if(!((env.MAILER==='resend'&&env.RESEND_API_KEY&&env.MAIL_FROM)||(env.MAILER==='capture'&&env.ENVIRONMENT==='local')))throw fail('Email delivery is not configured; no decision has been recorded',503);
}
async function lock(env,ref,id) {
  const r=await sql(env,'UPDATE application_review SET active_action=?,active_since=? WHERE ref=? AND active_action IS NULL',id,stamp(),ref).run();
  if(!r.meta.changes)throw fail('Another change is pending. Retry that change before continuing.');
}
async function snapshot(env,ref,a,version) {
  const key=root(ref)+`review/history/${version}.json`;
  const existing=await env.APPLICATIONS.get(key);
  if(!existing)await env.APPLICATIONS.put(key,JSON.stringify(a),{httpMetadata:{contentType:'application/json'}});
}
export async function saveReview(env,ref,b,actor) {
  check(ref,true);
  if(!['under_review','info_requested','accepted','declined'].includes(b.status))throw fail('Invalid review action',400);
  if(!/^[0-9a-f-]{36}$/.test(b.action_id||''))throw fail('Invalid action identifier',400);
  const message=text(b.message||'',6000,'message',b.status!=='under_review');
  const notes=text(b.notes||'',4000,'notes'),reason=text(b.reason||'',2000,'reason');
  const old=await one(env,'SELECT * FROM application_review_actions WHERE id=?',b.action_id);
  if(old) {
    const p=JSON.parse(old.payload);
    if(old.ref!==ref||p.status!==b.status||p.message!==message||p.notes!==notes||p.reason!==reason)throw fail('Action identifier already used');
    return finish(env,old);
  }
  const {a,row}=await record(env,ref),s=await state(env,ref);
  if(FINAL.has(row.fields.status))throw fail('Finalised applications cannot be changed');
  if(row.fields.status!==b.expected_status || s.revision!==b.expected_revision)throw fail('Application changed; reload before deciding');
  if(message)mailReady(env);
  let token=null;
  if(b.status==='info_requested') {
    if(!/^https:\/\/[a-z0-9.-]+(?::\d+)?$/.test(env.APPLICATION_REVIEW_PUBLIC_URL||''))throw fail('Secure editing endpoint is not configured',503);
    token=Array.from(crypto.getRandomValues(new Uint8Array(32)),x=>x.toString(16).padStart(2,'0')).join('');
  }
  await lock(env,ref,b.action_id);
  // Re-read under the D1 lock; no external state is changed until the durable action exists.
  try {
    const latest=await record(env,ref);
    if(latest.row.fields.status!==b.expected_status)throw fail('Application changed; reload before deciding');
    await snapshot(env,ref,a,s.revision);
    const payload={status:b.status,message,notes,reason,expected_status:b.expected_status,revision:s.revision,email:row.fields.email,token,
      token_expires:token?new Date(Date.now()+7*86400000).toISOString():null};
    await sql(env,'INSERT INTO application_review_actions(id,ref,kind,actor,payload,created_at) VALUES (?,?,?,?,?,?)',b.action_id,ref,'decision',actor,JSON.stringify(payload),stamp()).run();
  }catch(e){await sql(env,'UPDATE application_review SET active_action=NULL WHERE ref=? AND active_action=?',ref,b.action_id).run();throw e;}
  return finish(env,await one(env,'SELECT * FROM application_review_actions WHERE id=?',b.action_id));
}
async function deliver(env,action,to,subject,body,suffix='artist') {
  // Resend's idempotency window is 24 hours. A later retry needs reconciliation, never an unguarded resend.
  if(Date.now()-Date.parse(action.created_at)>23*3600000)throw fail('Delivery needs reconciliation before retrying; no automatic resend was attempted');
  const result=await send(env,{to,replyTo:'hello@plotnua.ie',subject,text:body,idempotencyKey:`application-${action.id}-${suffix}`});
  if(!result.sent)throw fail('Email was not sent. The change remains pending; retry it here.',502);
}
async function finish(env,action) {
  if(action.phase==='complete')return {ref:action.ref,status:JSON.parse(action.payload).status,complete:true};
  const active=await one(env,'SELECT active_action FROM application_review WHERE ref=?',action.ref);
  if(active?.active_action!==action.id)throw fail('This action is no longer active');
  const p=JSON.parse(action.payload),ref=action.ref;
  // Claim execution in D1 to prevent parallel retry clicks sending or applying an action twice.
  const claimed=await sql(env,"UPDATE application_review_actions SET phase='running',running_at=?,error=NULL WHERE id=? AND (phase IN ('prepared','failed','sent','sync_failed') OR (phase='running' AND running_at<?))",stamp(),action.id,new Date(Date.now()-600000).toISOString()).run();
  if(!claimed.meta.changes)throw fail('This change is already processing. Reload shortly.');
  let sent=!!action.sent_at;
  try {
    const {row}=await record(env,ref);
    if(row.fields.status!==p.expected_status && row.fields.status!==p.status)throw fail('Register changed outside the Review Desk; reconciliation required');
    if(p.message&&!sent) {
      const link=p.token?`\n\nUpdate your application (valid for seven days):\n${env.APPLICATION_REVIEW_PUBLIC_URL}/application/edit#${ref}/${p.token}`:'';
      await deliver(env,action,p.email,`PlotArt application ${ref}`,`Dear ${row.fields.artist_name},\n\n${p.message}${link}\n\nBest wishes,\nColin\nPlotArt\nhello@plotnua.ie`);
      sent=true;
      await sql(env,"UPDATE application_review_actions SET sent_at=? WHERE id=?",stamp(),action.id).run();
    }
    const now=stamp(),fields={status:p.status,review_notes:p.notes,status_changed_at:now};
    if(FINAL.has(p.status)){fields.decided_at=now;fields.decision_reason=p.reason;}
    if(sent&&FINAL.has(p.status))fields.decision_emailed_at=action.sent_at||now;
    await register(env,'/'+row.id,{method:'PATCH',body:JSON.stringify({fields})});
    await env.DB.batch([
      sql(env,'UPDATE application_review SET token_hash=?,token_expires=?,requested_message=?,active_action=NULL WHERE ref=? AND active_action=?',p.token?await digest(p.token):null,p.token_expires,p.message,ref,action.id),
      sql(env,"UPDATE application_review_actions SET phase='complete',completed_at=?,error=NULL,payload=? WHERE id=?",now,JSON.stringify({...p,token:undefined}),action.id)
    ]);
    return {ref,status:p.status,complete:true};
  }catch(e){await sql(env,"UPDATE application_review_actions SET phase=?,error=? WHERE id=?",sent?'sync_failed':'failed',String(e.message).slice(0,400),action.id).run();throw e;}
}
export async function retryReview(env,ref,id) {
  check(ref,true);
  const action=await one(env,'SELECT * FROM application_review_actions WHERE ref=? AND id=?',ref,id);
  if(!action){const s=await one(env,'SELECT * FROM application_review WHERE ref=?',ref);if(s?.active_action===id && s.active_since<new Date(Date.now()-600000).toISOString()){await sql(env,'UPDATE application_review SET active_action=NULL WHERE ref=? AND active_action=?',ref,id).run();return {ref,recovered:true};}throw fail('The pending change is still preparing. Retry after ten minutes if it does not finish.',409);}
  return action.kind==='revision'?finishRevision(env,action):finish(env,action);
}
export async function authoriseRevision(env,ref,token) {
  check(ref,true);
  if(!/^[0-9a-f]{64}$/.test(token||''))throw fail('This editing link is invalid or expired',403);
  const s=await one(env,'SELECT * FROM application_review WHERE ref=?',ref);
  if(!s||!s.token_hash||s.token_hash!==await digest(token)||s.token_expires<stamp()||s.active_action)throw fail('This editing link is invalid, expired or temporarily busy',403);
  const {a,row}=await record(env,ref);
  if(row.fields.status!=='info_requested')throw fail('This application is no longer awaiting changes',403);
  return {s,a,row};
}
export async function revisionView(env,ref,token) {
  const {s,a}=await authoriseRevision(env,ref,token);
  const keys=['artist_name','bio','additional_info','medium','region','portfolio','website','social_link'];
  return {ref,revision:s.revision,message:s.requested_message,application:Object.fromEntries(keys.map(k=>[k,a[k]||''])),images:a.images||[]};
}
export async function submitRevision(env,ref,token,b) {
  const {s,a,row}=await authoriseRevision(env,ref,token);
  if(b.revision!==s.revision)throw fail('Application changed; reload the editing page');
  const values={};
  const limits={artist_name:120,bio:6000,additional_info:4000,portfolio:1000,website:1000,social_link:1000};
  for(const [k,max] of Object.entries(limits))values[k]=text(b[k]??a[k]??'',max,k,['artist_name','bio'].includes(k));
  for(const k of ['portfolio','website'])if(values[k]&&!/^https?:\/\/[^\s]+$/i.test(values[k]))throw fail('Invalid '+k,400);
  if(values.social_link&&!/^(@[a-zA-Z0-9_.]+|https?:\/\/[^\s]+)$/.test(values.social_link))throw fail('Invalid social link',400);
  const id=crypto.randomUUID();
  await lock(env,ref,id);
  try {
    await snapshot(env,ref,a,s.revision);
    const images=b.images===undefined?a.images:b.images;
    if(!Array.isArray(images)||images.length>5)throw fail('Invalid photographs',400);
    const clean=[];
    for(const im of images){
      const existing=(a.images||[]).find(x=>x.file===im.file);
      if(existing){clean.push(existing);continue;}
      if(!/^review\/uploads\/[0-9a-f-]{36}\.(jpg|png|webp)$/.test(im.file||''))throw fail('Invalid photograph',400);
      const o=await env.APPLICATIONS.get(root(ref)+im.file);
      if(!o||o.customMetadata?.revision!==String(s.revision))throw fail('Photograph unavailable',400);
      clean.push({file:im.file,type:o.httpMetadata.contentType,bytes:o.size});
    }
    if(!values.portfolio&&clean.length<3)throw fail('Provide a portfolio link or at least three photographs',400);
    const revised={...a,...values,images:clean,revised_at:stamp()};
    // Write a recoverable revision artifact BEFORE changing either authoritative view.
    await env.APPLICATIONS.put(root(ref)+`review/history/${s.revision+1}.json`,JSON.stringify(revised));
    const payload={...values,status:'under_review',revision:s.revision+1};
    await sql(env,'INSERT INTO application_review_actions(id,ref,kind,actor,payload,created_at) VALUES (?,?,?,?,?,?)',id,ref,'revision','applicant',JSON.stringify(payload),stamp()).run();
    return finishRevision(env,await one(env,'SELECT * FROM application_review_actions WHERE id=?',id));
  }catch(e){
    const action=await one(env,'SELECT id FROM application_review_actions WHERE id=?',id);
    if(!action)await sql(env,'UPDATE application_review SET active_action=NULL WHERE ref=? AND active_action=?',ref,id).run();
    else await sql(env,"UPDATE application_review_actions SET phase='sync_failed',error=? WHERE id=?",'Revision reconciliation required: '+e.message,id).run();
    throw e;
  }
}
export async function eraseReview(env,ref) {
  await env.DB.batch([sql(env,'DELETE FROM application_review_actions WHERE ref=?',ref),sql(env,'DELETE FROM application_review WHERE ref=?',ref)]);
}

async function finishRevision(env,action) {
  if(action.phase==='complete')return {ok:true};
  const claimed=await sql(env,"UPDATE application_review_actions SET phase='running',running_at=?,error=NULL WHERE id=? AND (phase IN ('prepared','sync_failed') OR (phase='running' AND running_at<?))",stamp(),action.id,new Date(Date.now()-600000).toISOString()).run();
  if(!claimed.meta.changes)throw fail('Revision already processing');
  const p=JSON.parse(action.payload),ref=action.ref;
  try {
    const {row}=await record(env,ref);
    if(!['info_requested','under_review'].includes(row.fields.status))throw fail('Application status changed; reconciliation required');
    const o=await env.APPLICATIONS.get(root(ref)+`review/history/${p.revision}.json`);
    if(!o)throw fail('Revision snapshot missing');
    const revised=JSON.parse(await o.text());
    const {revision,...fields}=p;
    await register(env,'/'+row.id,{method:'PATCH',body:JSON.stringify({fields:{...fields,status_changed_at:stamp()}})});
    await env.APPLICATIONS.put(root(ref)+'application.json',JSON.stringify(revised),{httpMetadata:{contentType:'application/json'}});
    await env.DB.batch([
      sql(env,'UPDATE application_review SET revision=?,revised_at=?,token_hash=NULL,token_expires=NULL,active_action=NULL WHERE ref=? AND active_action=?',p.revision,stamp(),ref,action.id),
      sql(env,"UPDATE application_review_actions SET phase='complete',completed_at=? WHERE id=?",stamp(),action.id)
    ]);
    try {await deliver(env,action,'hello@plotnua.ie',`Revised PlotArt application ${ref}`,`${p.artist_name} has resubmitted application ${ref}. Review it in the PlotArt Review Desk.`,'founder');}
    catch(e){await sql(env,'UPDATE application_review_actions SET error=? WHERE id=?','Founder notification failed: '+e.message,action.id).run();}
    return {ok:true};
  }catch(e){await sql(env,"UPDATE application_review_actions SET phase='sync_failed',error=? WHERE id=?",e.message,action.id).run();throw e;}
}
export async function reviewSnapshot(env,ref,version) {
  check(ref);await record(env,ref);
  if(!/^\d+$/.test(version))throw fail('Invalid revision',400);
  const o=await env.APPLICATIONS.get(root(ref)+`review/history/${version}.json`);
  if(!o)throw fail('Revision not found',404);
  return JSON.parse(await o.text());
}
