import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
const require=createRequire(process.env.MINIFLARE_FROM || '/tmp/plotart-review-tools/package.json');
const {Miniflare}=require('miniflare');
const here=new URL('..',import.meta.url).pathname;
const ref='PA-AP-261116-AABBCC',id='rec12345678901234';
const fields={application_ref:ref,artist_name:'Synthetic Artist',email:'synthetic@example.invalid',status:'received',bio:'Original biography',portfolio:'https://example.invalid/portfolio'};
let rejectPatch=false;
const common={modules:true,modulesRoot:here,modulesRules:[{type:'ESModule',include:['**/*.js']}],compatibilityDate:'2026-08-01',d1Databases:{DB:'review-test'},r2Buckets:{APPLICATIONS:'review-test'},bindings:{ENVIRONMENT:'local',MAILER:'capture',PLOTART_REVIEW_AIRTABLE_TOKEN:'test-only',APPLICATION_REVIEW_PUBLIC_URL:'https://review.test'},outboundService:async(req)=>{
 const u=new URL(req.url);assert.equal(u.hostname,'api.airtable.com');
 if(req.method==='PATCH'){if(rejectPatch)return Response.json({}, {status:503});Object.assign(fields,(await req.json()).fields);}
 return Response.json({id,fields});
}};
const serviceBindings={APPLICATION_REGISTER:{name:'register',entrypoint:'GalleryApplicationRegister'}};
const mf=new Miniflare({workers:[
 {name:'register',...common,modulesRoot:new URL('../../',import.meta.url).pathname,scriptPath:here+'../art-space-register/src/review-entry.js',bindings:{AIRTABLE_BASE:'appS4gWOxuZqJyWvU',AIRTABLE_TOKEN:'test-only'}},
 {name:'private',...common,serviceBindings,scriptPath:here+'test/application-review-worker.js'},
 {name:'studio',...common,serviceBindings,scriptPath:here+'src/studio-entry.js'},
 {name:'public',modules:true,modulesRoot:here,modulesRules:common.modulesRules,compatibilityDate:common.compatibilityDate,serviceBindings:{APPLICATION_REVIEW:{name:'studio',entrypoint:'ApplicationRevision'}},scriptPath:here+'src/application-revision-gateway.js'}
]});
const db=await mf.getD1Database('DB','private'),bucket=await mf.getR2Bucket('APPLICATIONS','private');
for(const stmt of readFileSync(here+'migrations/0014_application_review.sql','utf8').split(';').filter(x=>x.trim()))await db.prepare(stmt).run();
await db.prepare('CREATE TABLE mail_capture(id INTEGER PRIMARY KEY,at TEXT,to_addr TEXT,reply_to TEXT,subject TEXT,body TEXT)').run();
await bucket.put(`applications/${ref}/application.json`,JSON.stringify({...fields,airtable_record:id,images:[]}));
const w=await mf.getWorker('private'),pub=await mf.getWorker('public');
const call=async b=>{const r=await w.fetch('https://private.test/',{method:'POST',body:JSON.stringify({...b,ref:b.ref||ref})});return {status:r.status,...await r.json()};};
const publicCall=async(suffix='',token='',body)=>{const r=await pub.fetch('https://review.test/v1/application-revision/'+ref+suffix,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+token},body:body?JSON.stringify(body):undefined});return {status:r.status,...await r.json()};};
let passed=0;const check=(label,value)=>{assert.ok(value,label);console.log('PASS '+label);passed++;};
try{
 check('reference alone cannot edit',(await publicCall()).status===403);
 let r=await call({op:'get'});check('application reads trusted R2 record identity',r.ok&&r.value.status==='received');
 const body={action_id:randomUUID(),status:'info_requested',expected_status:'received',expected_revision:0,message:'Please improve your biography.',notes:'Private notes',reason:''};
 await db.prepare("CREATE TRIGGER fail_mail BEFORE INSERT ON mail_capture BEGIN SELECT RAISE(FAIL, 'synthetic mail failure'); END").run();
 r=await call({body});check('mail failure does not change application status',!r.ok&&fields.status==='received');
 await db.prepare('DROP TRIGGER fail_mail').run();
 r=await call({op:'retry',id:body.action_id});check('request sends mail and updates register',r.ok&&fields.status==='info_requested');
 const mails=await db.prepare('SELECT * FROM mail_capture').all();const token=mails.results[0].body.match(/#PA-AP-[^/]+\/([a-f0-9]{64})/)[1];
 check('editing link opens without Studio account',(await publicCall('',token)).ok);
 check('wrong token is refused',(await publicCall('','a'.repeat(64))).status===403);
 await db.prepare('UPDATE application_review SET token_expires=? WHERE ref=?').bind('2000-01-01T00:00:00.000Z',ref).run();
 check('expired token is refused',(await publicCall('',token)).status===403);
 await db.prepare('UPDATE application_review SET token_expires=? WHERE ref=?').bind('2099-01-01T00:00:00.000Z',ref).run();
 await call({body});check('same action does not duplicate email',(await db.prepare('SELECT COUNT(*) n FROM mail_capture').first()).n===1);
 check('private notes not disclosed',!JSON.stringify(await publicCall('',token)).includes('Private notes'));
 const badImage=await pub.fetch('https://review.test/v1/application-revision/'+ref+'/image',{method:'POST',headers:{Authorization:'Bearer '+token},body:'this is not a photograph'});
 check('invalid image content refused',badImage.status===400);
 const png=readFileSync(new URL('./review-fixture.png',import.meta.url));
 const upload=await pub.fetch('https://review.test/v1/application-revision/'+ref+'/image',{method:'POST',headers:{Authorization:'Bearer '+token},body:png});const uploaded=await upload.json();
 check('replacement photograph uploads privately',uploaded.ok&&uploaded.image.file.startsWith('review/uploads/'));
 const preview=await pub.fetch('https://review.test/v1/application-revision/'+ref+'/image?file='+uploaded.image.file,{headers:{Authorization:'Bearer '+token}});
 check('token permits private image preview',preview.status===200&&preview.headers.get('Content-Type')==='image/png');
 check('image is inaccessible without token',(await pub.fetch('https://review.test/v1/application-revision/'+ref+'/image?file='+uploaded.image.file)).status===403);
 const revisionBody={revision:0,bio:'Revised biography',portfolio:'https://example.invalid/updated',images:[uploaded.image]};
 check('unsafe links refused',!(await publicCall('/submit',token,{...revisionBody,website:'javascript:alert(1)'})).ok);
 rejectPatch=true;r=await publicCall('/submit',token,revisionBody);check('revision write failure remains pending',!r.ok&&!!(await call({op:'get'})).value.pending_action);
 rejectPatch=false;r=await call({op:'retry',id:(await call({op:'get'})).value.pending_action});
 check('resubmission returns to review',r.ok&&fields.status==='under_review'&&fields.bio==='Revised biography');
 check('resubmission revokes token',(await publicCall('',token)).status===403);
 check('original remains available',JSON.parse(await(await bucket.get(`applications/${ref}/review/history/0.json`)).text()).bio==='Original biography');
 r=await call({op:'get'});check('revision and correspondence visible',r.value.revision===1&&r.value.history.length===2);
 const decision={action_id:randomUUID(),status:'accepted',expected_status:'under_review',expected_revision:1,message:'Thank you. Your application is accepted.',notes:'',reason:''};
 rejectPatch=true;r=await call({body:decision});check('register failure stays visibly pending',!r.ok&&fields.status==='under_review'&&!!(await call({op:'get'})).value.pending_action);
 const count=(await db.prepare('SELECT COUNT(*) n FROM mail_capture').first()).n;
 rejectPatch=false;r=await call({op:'retry',id:decision.action_id});check('pending delivery reconciles without duplicate mail',r.ok&&fields.status==='accepted'&&(await db.prepare('SELECT COUNT(*) n FROM mail_capture').first()).n===count);
 check('accepted application cannot be reopened',!(await call({body:{...decision,action_id:randomUUID(),status:'info_requested',expected_status:'accepted'}})).ok);
 check('Fiona is protected before any register write',!(await call({ref:'PA-AP-261116-7C1EB4',body:decision})).ok);
 check('Founding 25 cannot enter this workflow',!(await call({ref:'F25-261116-AABBCC',body:decision})).ok);
 console.log(`${passed} checks passed`);
}finally{await mf.dispose();}
