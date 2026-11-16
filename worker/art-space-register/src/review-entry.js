/* The default public intake handler is unchanged. This named entrypoint is only available
 * to explicitly configured Cloudflare service bindings; it has no public URL. */
import { WorkerEntrypoint } from 'cloudflare:workers';
export { default } from './index.js';
const BASE='appS4gWOxuZqJyWvU',TABLE='tblEQ8CiXFWMlWqsE';
const FIELDS=new Set(['status','review_notes','status_changed_at','decided_at','decision_reason','decision_emailed_at','artist_name','bio','additional_info','portfolio','website','social_link','artwork_images']);
export class GalleryApplicationRegister extends WorkerEntrypoint {
 async fetch(req){
  const path=new URL(req.url).pathname;
  if(!/^\/rec[A-Za-z0-9]{14}$/.test(path)||!['GET','PATCH'].includes(req.method))return Response.json({ok:false},{status:404});
  if(this.env.AIRTABLE_BASE!==BASE||!this.env.AIRTABLE_TOKEN)return Response.json({ok:false},{status:503});
  const headers={Authorization:'Bearer '+this.env.AIRTABLE_TOKEN,'Content-Type':'application/json'};
  // Fiona remains read-only even through this private service.
  const original=await fetch(`https://api.airtable.com/v0/${BASE}/${TABLE}${path}`,{headers,signal:AbortSignal.timeout(10000)});
  if(!original.ok)return new Response(null,{status:original.status});
  const row=await original.json();
  if(!/^PA-AP-\d{6}-[0-9A-F]{6}$/.test(row.fields?.application_ref||''))return new Response(null,{status:409});
  if(req.method==='GET')return Response.json(row);
  if(row.fields.application_ref==='PA-AP-261116-7C1EB4')return new Response(null,{status:409});
  const raw=await req.text();if(raw.length>20000)return new Response(null,{status:413});
  let b;try{b=JSON.parse(raw);}catch{return new Response(null,{status:400});}
  if(!b?.fields||Object.keys(b).some(k=>k!=='fields')||Object.keys(b.fields).some(k=>!FIELDS.has(k)))return new Response(null,{status:400});
  return fetch(`https://api.airtable.com/v0/${BASE}/${TABLE}${path}`,{method:'PATCH',headers,body:JSON.stringify({fields:b.fields,typecast:false}),signal:AbortSignal.timeout(10000)});
 }
}
