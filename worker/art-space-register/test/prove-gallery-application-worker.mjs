/* PLOTART GALLERY ARTIST APPLICATIONS · WORKER PROOF (Phase 3, development 13 Nov 2026)
 * ===========================================================================
 * The real Worker code against an in-memory R2 bucket and a STUBBED Airtable (nothing leaves this process; every
 * record is synthetic). Proves: the route is closed in the committed configuration and behind every hard stop; it
 * writes only to its own table, with its own reference, source, register, consent and privacy versions; it is fully
 * isolated from the Founding 25 route (switches, sentences, tables, rate limits); images go to the applicant's own
 * private folder with a review copy that holds no email address; the probe never writes; schema agreement.
 * Run: node worker/art-space-register/test/prove-gallery-application-worker.mjs
 * ========================================================================= */
import worker, { __test as T } from '../src/index.js';
import { readFileSync } from 'node:fs';

let pass = 0, fail = 0;
const out = [];
const check = (name, cond, detail = '') => {
  if (cond) { pass++; out.push('  ok    ' + name); }
  else { fail++; out.push('  FAIL  ' + name + (detail ? '  — ' + detail : '')); }
};
const fx = (n) => new Uint8Array(readFileSync(new URL('./fixtures/' + n, import.meta.url)));
const toml = readFileSync(new URL('../wrangler.toml', import.meta.url), 'utf8');
const topToml = toml.split(/^\[env\./m)[0];
const tomlVars = Object.fromEntries([...topToml.matchAll(/^([A-Z0-9_]+)\s*=\s*"([^"]*)"/gm)].map(m => [m[1], m[2]]));
const schema = JSON.parse(readFileSync(new URL('../airtable-schema-gallery-artist.proposed.json', import.meta.url), 'utf8'));
const sField = Object.fromEntries(schema.new_table.fields.map(f => [f.name, f]));

class Bucket {
  constructor() { this.m = new Map(); }
  async put(k, v, o = {}) { const b = v instanceof Uint8Array ? v : typeof v === 'string' ? new TextEncoder().encode(v) : new Uint8Array(v);
    this.m.set(k, { b, httpMetadata: o.httpMetadata || {}, customMetadata: o.customMetadata || {} }); }
  async get(k) { const o = this.m.get(k); if (!o) return null;
    return { size: o.b.length, httpMetadata: o.httpMetadata, customMetadata: o.customMetadata, arrayBuffer: async () => o.b.slice().buffer, text: async () => new TextDecoder().decode(o.b) }; }
  async delete(k) { this.m.delete(k); }
  async list({ prefix = '', limit = 1000 } = {}) { return { objects: [...this.m.keys()].filter(k => k.startsWith(prefix)).slice(0, limit).map(key => ({ key })) }; }
  keys(p = '') { return [...this.m.keys()].filter(k => k.startsWith(p)).sort(); }
}

let calls = [], existing = false, recent = 0;
globalThis.fetch = async (url, init = {}) => {
  const u = String(url);
  calls.push({ url: u, method: init.method, body: init.body ? JSON.parse(init.body) : null });
  if (init.method === 'GET' && u.includes('IS_AFTER')) return new Response(JSON.stringify({ records: Array.from({ length: recent }, (_, i) => ({ id: 'r' + i, fields: {} })) }), { status: 200 });
  if (init.method === 'GET') return new Response(JSON.stringify({ records: existing ? [{ id: 'recX', fields: {} }] : [] }), { status: 200 });
  return new Response(JSON.stringify({ records: [{ id: 'recNEW' + calls.length }] }), { status: 200 });
};
const GA_T = encodeURIComponent('Gallery Artist applications'), F25_T = encodeURIComponent('Founding 25 applications');
const at = () => calls.filter(c => c.url.includes('api.airtable.com'));
const posts = (t) => at().filter(c => c.method === 'POST' && (!t || c.url.includes(t))).map(c => c.body.records[0].fields);

const ORIGIN = 'https://plotnua.ie', BASE = 'https://w.example';
const R = T.GA_ROUTE, IR = T.GA_IMAGE_ROUTE;
let B = new Bucket();
const FAKE = { AIRTABLE_BASE: 'appGATESTONLY0001', AIRTABLE_TOKEN: 'patFAKE_NEVER_REAL' };
const COMMITTED = () => ({ ...tomlVars, ...FAKE, F25_IMAGES: B });
const ON = () => ({ ...COMMITTED(), APP_WRITES_ENABLED: 'true', APP_PRIVACY_VERSION: '2026-11-PLOTART-APPLICATIONS-TEST' });
const hdr = (o = {}) => ({ origin: ORIGIN, 'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'cors', ...o });
const run = async (env, req, keep = false) => { calls = []; if (!keep) T.resetRateLimit(); const res = await worker.fetch(req, env); let j = null; try { j = await res.clone().json(); } catch {} return { s: res.status, j }; };
const post = (path, body) => new Request(BASE + path, { method: 'POST', headers: hdr({ 'content-type': 'application/json' }), body: JSON.stringify(body) });
const upload = (env, sid, bytes, type) => run(env, new Request(BASE + IR + '?s=' + sid, { method: 'POST', headers: hdr({ 'content-type': type }), body: bytes }));
const SID = '6f1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f', SID2 = '7a1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f';
const good = (over = {}) => ({ artist_name: 'Synthetic Test Artist', email: 'GA.Test@example.com', region: 'galway', medium: 'painting',
  bio: 'A synthetic biography for testing only. Paints coastal light in oil, working from a studio near the sea.',
  portfolio: 'https://example.com/portfolio',
  eligibility_text: T.GA_ELIGIBILITY_TEXT, ownership_text: T.GA_OWNERSHIP_TEXT, privacy_text: T.GA_PRIVACY_TEXT, submission_id: SID, ...over });
const notOpen = (r) => r.s === 503 && r.j && r.j.state === 'not_open' && at().length === 0;

/* ---- Z · closed as committed, and every hard stop ---- */
check('Z1 wrangler.toml: APP_WRITES_ENABLED = "false" and APP_PRIVACY_VERSION empty (built closed)', tomlVars.APP_WRITES_ENABLED === 'false' && tomlVars.APP_PRIVACY_VERSION === '');
check('Z2 the Founding 25 switch is still committed off', tomlVars.F25_WRITES_ENABLED === 'false');
let r = await run(COMMITTED(), post(R, good()));
check('Z3 the committed configuration refuses a valid application: not_open, no Airtable call', notOpen(r));
r = await run(COMMITTED(), post(R, good({ email: 'release-check@probe.plotnua.invalid' })));
check('Z4 the committed configuration answers the release probe not_open', notOpen(r));
for (const [k, v] of [['APP_WRITES_ENABLED', 'false'], ['APP_WRITES_ENABLED', 'TRUE'], ['APP_PRIVACY_VERSION', ''], ['AIRTABLE_TOKEN', ''], ['AIRTABLE_BASE', '']]) {
  r = await run({ ...ON(), [k]: v }, post(R, good()));
  check(`Z5 ${k}=${JSON.stringify(v)} -> not_open, no call`, notOpen(r));
}
r = await upload(COMMITTED(), SID, fx('a.jpg'), 'image/jpeg');
check('Z6 the image address is closed too: not_open, nothing stored', r.s === 503 && r.j.state === 'not_open' && B.keys().length === 0);

/* ---- S · isolation from the Founding 25 route ---- */
r = await run({ ...COMMITTED(), F25_WRITES_ENABLED: 'true', F25_PRIVACY_VERSION: '2026-10-PHASE2-V8' }, post(R, good()));
check('S1 opening the Founding 25 switch does not open this route', notOpen(r));
r = await run(ON(), post(T.F25_ROUTE, { ...good(), privacy_text: T.F25_PRIVACY_TEXT }));
check('S2 opening this route does not open the Founding 25 route', notOpen(r));
r = await run(ON(), post(R, good({ privacy_text: T.F25_PRIVACY_TEXT })));
check('S3 the Founding 25 privacy confirmation is refused here (each route has its own notice sentence)', r.s === 400 && r.j.field === 'privacy_text' && at().length === 0);
r = await run({ ...ON(), F25_WRITES_ENABLED: 'true', F25_PRIVACY_VERSION: 'X' }, post(T.F25_ROUTE, { ...good(), privacy_text: T.GA_PRIVACY_TEXT }));
check('S4 and this route\'s privacy confirmation is refused on the Founding 25 route', r.s === 400 && r.j.field === 'privacy_text' && at().length === 0);
check('S5 the eligibility and ownership sentences are the Founding 25 ones (island of Ireland, 18 or over; own work)', T.GA_ELIGIBILITY_TEXT === T.F25_ELIGIBILITY_TEXT && T.GA_OWNERSHIP_TEXT === T.F25_OWNERSHIP_TEXT);
check('S6 the older R2 ownership sentence is NOT accepted on this new route', (await run(ON(), post(R, good({ ownership_text: T.F25_OWNERSHIP_TEXT_R2 })))).j.field === 'ownership_text');

/* ---- W · a permitted write ---- */
r = await run(ON(), post(R, good()));
const app = posts(GA_T)[0] || {};
check('W1 a valid application -> received', r.s === 200 && r.j.state === 'received');
check('W2 exactly one application row, in the Gallery Artist table; nothing written to the Founding 25 table', posts(GA_T).length === 1 && posts(F25_T).length === 0);
check('W3 reference PA-AP-YYMMDD-XXXXXX', /^PA-AP-\d{6}-[0-9A-F]{6}$/.test(app.application_ref || ''), app.application_ref);
check('W4 status received, source, privacy and consent versions are this route\'s', app.status === 'received' && app.source === 'plotart_gallery_application_form'
  && app.privacy_version === '2026-11-PLOTART-APPLICATIONS-TEST' && app.consent_version === 'PA-AP-APPLICATION-2026-11-R1' && /^[0-9a-f]{64}$/.test(app.consent_text_hash));
const log = posts(encodeURIComponent('Status log'))[0] || {}, cons = posts(encodeURIComponent('Consent proofs'))[0] || {};
check('W5 the status log and consent proof carry register gallery_artist and the route\'s reason', log.register === 'gallery_artist' && log.reason === 'gallery_application_received' && log.to_status === 'received'
  && cons.register === 'gallery_artist' && cons.privacy_version === '2026-11-PLOTART-APPLICATIONS-TEST' && !('email' in cons));
check('W6 email stored lower-cased as the duplicate key; nothing beyond the schema is written', app.email_key === 'ga.test@example.com' && Object.keys(app).every(k => k in sField), Object.keys(app).filter(k => !(k in sField)));
check('W7 every select value written is one of the schema\'s choices', ['region', 'medium', 'status', 'source'].every(k => sField[k].options.includes(app[k])));
const dupGet = at().find(c => c.method === 'GET' && !c.url.includes('IS_AFTER'));
check('W8 the duplicate check reads only the Gallery Artist table', dupGet && dupGet.url.includes(GA_T) && !at().some(c => c.url.includes(F25_T)));
existing = true; r = await run(ON(), post(R, good()));
check('W9 the same email or submission again -> received, nothing written (no duplicate)', r.j.state === 'received' && posts().length === 0); existing = false;
recent = 50; r = await run(ON(), post(R, good()));
check('W10 the daily cap (APP_DAILY_CAP, default 50) -> slow_down, nothing written', r.s === 429 && posts().length === 0);
r = await run({ ...ON(), APP_DAILY_CAP: '80' }, post(R, good()));
check('W11 the cap is this route\'s own setting', r.j.state === 'received' && at().some(c => c.url.includes('maxRecords=80'))); recent = 0;
r = await run(ON(), post(R, good({ email: 'release-check@probe.plotnua.invalid' })));
check('W12 the probe address reports probe_open when open and writes nothing', r.j && r.j.state === 'probe_open' && posts().length === 0);
r = await run(ON(), post(R, good({ living_gallery: true })));
check('W13 any field outside the form is refused before any call', r.j.field === 'unexpected_field' && at().length === 0);
r = await run(ON(), post(R, good({ portfolio: undefined })));
check('W14 no portfolio link and fewer than three images -> refused', r.j.field === 'portfolio' && at().length === 0);
for (const k of ['region', 'medium']) {
  r = await run(ON(), post(R, good({ [k]: 'outside_ireland' })));
  check(`W15 ${k} outside the closed list is refused`, r.s === 400 && r.j.field === k);
}

/* ---- B · burst limits are separate ---- */
T.resetRateLimit();
for (let i = 0; i < 10; i++) await worker.fetch(post(T.F25_ROUTE, good()), COMMITTED());
r = await run(COMMITTED(), post(R, good()), true);
check('B1 a burst on the Founding 25 route does not slow this route', r.j.state === 'not_open');
for (let i = 0; i < 10; i++) await worker.fetch(post(R, good()), COMMITTED());
r = await run(COMMITTED(), post(R, good()), true);
check('B2 this route has its own burst limit', r.s === 429);

/* ---- I · images ---- */
B = new Bucket();
for (const [f, t] of [['a.jpg', 'image/jpeg'], ['b.png', 'image/png'], ['c.webp', 'image/webp']]) await upload(ON(), SID2, fx(f), t);
const ids = B.keys('pending/' + SID2 + '/').map(k => k.split('/').pop());
check('I1 three images are held under pending/<submission>/ while the route is open', ids.length === 3);
r = await upload(ON(), SID2, fx('e.gif'), 'image/gif');
check('I2 a GIF is refused', r.s === 400 && r.j.field === 'image_type');
r = await run(ON(), post(R, good({ submission_id: SID2, portfolio: undefined, images: ids, email: 'img.ga@example.com' })));
const row = posts(GA_T)[0] || {}, ref = row.application_ref || '';
const folder = B.keys('applications/' + ref + '/');
check('I3 three images instead of a link -> received; images moved to applications/<PA-AP ref>/', r.j.state === 'received' && /^PA-AP-/.test(ref) && folder.length === 4, folder);
const review = JSON.parse(new TextDecoder().decode(B.m.get('applications/' + ref + '/application.json').b));
check('I4 the review copy for Studio holds no email address, and links the Studio review page', !JSON.stringify(review).includes('@') && row.artwork_review === 'https://plotart-studio.colin-a41.workers.dev/admin/applications/' + ref && row.artwork_images === 3);
check('I5 the holding copies are removed', B.keys('pending/').length === 0);

/* ---- R · routing ---- */
r = await run(ON(), new Request(BASE + R, { method: 'GET', headers: hdr() }));
check('R1 there is no GET on this route', r.s === 405);
r = await run(ON(), new Request(BASE + R, { method: 'POST', headers: hdr({ origin: 'https://evil.example', 'content-type': 'application/json' }), body: JSON.stringify(good()) }));
check('R2 another website is refused (403) with no call', r.s === 403 && at().length === 0);
check('R3 schema: no Founding-only field (counts_toward_25, terms_*, waiting_list) and the six statuses', !('counts_toward_25' in sField) && !('terms_sent_at' in sField) && !('waiting_list' in sField)
  && sField.status.options.join() === 'received,under_review,info_requested,accepted,declined,withdrawn');
check('R4 schema: the two automations are proposed switched off', schema.automations.length === 2 && schema.automations.every(a => a.state === 'created OFF'));

console.log('PLOTART GALLERY ARTIST APPLICATIONS · WORKER PROOF');
console.log(out.join('\n'));
console.log(`\n  ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
