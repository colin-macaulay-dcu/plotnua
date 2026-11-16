/* Separate public Worker: no Cloudflare Access session or Studio account required.
   Token is carried in the URL fragment and Authorization header, never in query strings. */
import * as R from './gallery-application-review.js';
import { checkImage } from './lib.js';
import { EDIT_HTML } from './application-revision-ui.js';
const SEC={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow','Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"};
function json(data,status=200){return new Response(JSON.stringify(data),{status,headers:{...SEC,'Content-Type':'application/json'}});}
export default {async fetch(req,env){
 try {
  const url=new URL(req.url),p=url.pathname;
  if(p==='/application/edit'&&req.method==='GET')return new Response(EDIT_HTML,{headers:{...SEC,'Content-Type':'text/html; charset=utf-8'}});
  if(p==='/application/edit.js'&&req.method==='GET')return new Response(EDIT_JS,{headers:{...SEC,'Content-Type':'application/javascript'}});
  const m=p.match(/^\/v1\/application-revision\/(PA-AP-\d{6}-[0-9A-F]{6})(?:\/(image|submit))?$/);
  if(!m)return json({ok:false,error:'Not found'},404);
  const ref=m[1],token=(req.headers.get('Authorization')||'').replace(/^Bearer /,'');
  if(req.headers.get('Origin')&&req.headers.get('Origin')!==url.origin)return json({ok:false},403);
  if(req.method==='GET'&&!m[2])return json({ok:true,...await R.revisionView(env,ref,token)});
  if(req.method==='GET'&&m[2]==='image'){
   const {a,s}=await R.authoriseRevision(env,ref,token);const file=url.searchParams.get('file')||'';
   if(!/^(?:[1-5]|review\/uploads\/[0-9a-f-]{36})\.(jpg|png|webp)$/.test(file))return json({ok:false},404);
   const o=await env.APPLICATIONS.get(`applications/${ref}/${file}`);
   if(!o||(!(a.images||[]).some(i=>i.file===file)&&o.customMetadata?.revision!==String(s.revision)))return json({ok:false},404);
   return new Response(o.body,{headers:{...SEC,'Content-Type':o.httpMetadata.contentType}});
  }
  if(req.method==='POST'&&m[2]==='submit'){
   const raw=await req.text();if(raw.length>20000)return json({ok:false,error:'Submission too large'},413);
   return json(await R.submitRevision(env,ref,token,JSON.parse(raw)));
  }
  if(req.method==='POST'&&m[2]==='image'){
   const {s}=await R.authoriseRevision(env,ref,token);
   if(Number(req.headers.get('Content-Length'))>8*1024*1024)return json({ok:false,error:'Photograph exceeds 8 MB'},413);
   const reader=req.body?.getReader();if(!reader)return json({ok:false,error:'No photograph supplied'},400);
   const chunks=[];let size=0;
   while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>8*1024*1024){await reader.cancel();return json({ok:false,error:'Photograph exceeds 8 MB'},413);}chunks.push(value);}
   const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}
   const checked=checkImage(bytes,{minLong:600});if(checked.blocks.length)return json({ok:false,error:checked.blocks.join(' ')},400);
   const held=await env.APPLICATIONS.list({prefix:`applications/${ref}/review/uploads/`,limit:1000});
   if(held.objects.length>=30)return json({ok:false,error:'Upload limit reached. Contact hello@plotnua.ie for assistance.'},429);
   const fmt=checked.fmt==='jpeg'?'jpg':checked.fmt;
   const file=`review/uploads/${crypto.randomUUID()}.${fmt}`;
   await env.APPLICATIONS.put(`applications/${ref}/${file}`,bytes,{httpMetadata:{contentType:`image/${fmt==='jpg'?'jpeg':fmt}`},customMetadata:{revision:String(s.revision)}});
   return json({ok:true,image:{file,w:checked.dims.w,h:checked.dims.h}});
  }
  return json({ok:false,error:'Method not allowed'},405);
 }catch(e){return json({ok:false,error:e.status?e.message:'The application could not be updated. Please try again or contact hello@plotnua.ie.'},e.status||500);}
}};
import { EDIT_JS } from './application-revision-ui.js';
