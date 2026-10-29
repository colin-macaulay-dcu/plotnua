/* PLOTART FOUNDING 25 · ARTWORK IMAGES WITH AN APPLICATION · WORKER PROOF (29 Oct 2026)
 * ===========================================================================
 * The real Worker code against an in-memory R2 bucket and a STUBBED Airtable
 * (nothing leaves this process). Proves: the upload route's hard stops and
 * validation (real format from the bytes, size, dimensions, count, origin,
 * no GET); "portfolio OR at least three images"; that only images this
 * application uploaded can be attached; that a received application has its
 * images in its own private folder with a review copy (no email address), and
 * the holding copies are removed; that a failed write leaves nothing behind
 * and can be retried; bare website addresses; schema agreement.
 * Run: node worker/art-space-register/test/prove-f25-images.mjs
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

/* ---- in-memory R2 (the subset the Worker uses) ---- */
class Bucket {
  constructor() { this.m = new Map(); this.failPut = false; }
  async put(k, v, o = {}) { if (this.failPut) throw new Error('r2 down'); const b = v instanceof Uint8Array ? v : typeof v === 'string' ? new TextEncoder().encode(v) : new Uint8Array(v);
    this.m.set(k, { b, httpMetadata: o.httpMetadata || {}, customMetadata: o.customMetadata || {} }); }
  async get(k) { const o = this.m.get(k); if (!o) return null;
    return { size: o.b.length, httpMetadata: o.httpMetadata, customMetadata: o.customMetadata, arrayBuffer: async () => o.b.slice().buffer, text: async () => new TextDecoder().decode(o.b) }; }
  async head(k) { const o = this.m.get(k); return o ? { size: o.b.length } : null; }
  async delete(k) { this.m.delete(k); }
  async list({ prefix = '', limit = 1000 } = {}) { return { objects: [...this.m.keys()].filter(k => k.startsWith(prefix)).slice(0, limit).map(key => ({ key })) }; }
  keys(p = '') { return [...this.m.keys()].filter(k => k.startsWith(p)).sort(); }
}

/* ---- stubbed Airtable ---- */
let calls = [], failCreate = 0;
globalThis.fetch = async (url, init = {}) => {
  const u = String(url);
  calls.push({ url: u, method: init.method, body: init.body ? JSON.parse(init.body) : null });
  if (init.method === 'GET') return new Response(JSON.stringify({ records: [] }), { status: 200 });
  if (failCreate && u.includes(encodeURIComponent('Founding 25 applications'))) return new Response('{}', { status: failCreate });
  return new Response(JSON.stringify({ records: [{ id: 'recNEW' + calls.length }] }), { status: 200 });
};
const appPosts = () => calls.filter(c => c.method === 'POST' && c.url.includes(encodeURIComponent('Founding 25 applications'))).map(c => c.body.records[0].fields);

const ORIGIN = 'https://plotnua.ie';
const BASE = 'https://w.example';
const R = T.F25_ROUTE, IR = T.F25_IMAGE_ROUTE;
let B = new Bucket();
const ENV = () => ({ ORIGIN, F25_WRITES_ENABLED: 'true', F25_PRIVACY_VERSION: '2026-10-PHASE2-V8', AIRTABLE_BASE: 'appF25TESTONLY001', AIRTABLE_TOKEN: 'patFAKE_NEVER_REAL',
  F25_IMAGES: B, F25_REVIEW_BASE: 'https://plotart-studio.colin-a41.workers.dev' });
const hdr = (o = {}) => ({ origin: ORIGIN, 'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'cors', ...o });
const run = async (env, req) => { calls = []; T.resetRateLimit(); const res = await worker.fetch(req, env); let j = null; try { j = await res.clone().json(); } catch {} return { s: res.status, j }; };
const upload = (env, sid, bytes, type, extra = {}) => run(env, new Request(BASE + IR + '?s=' + sid, { method: 'POST', headers: hdr({ 'content-type': type, ...extra }), body: bytes }));
const apply = (env, body) => run(env, new Request(BASE + R, { method: 'POST', headers: hdr({ 'content-type': 'application/json' }), body: JSON.stringify(body) }));
const SID = '6f1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f', SID2 = '7a1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f';
const good = (over = {}) => ({ artist_name: 'Synthetic Test Artist', email: 'Img.Test@example.com', region: 'galway', medium: 'painting',
  bio: 'A synthetic biography for testing only. Paints coastal light in oil, working from a studio near the sea.',
  eligibility_text: T.F25_ELIGIBILITY_TEXT, ownership_text: T.F25_OWNERSHIP_TEXT, privacy_text: T.F25_PRIVACY_TEXT, submission_id: SID, ...over });
const refused = (r, f) => r.s === 400 && r.j && r.j.state === 'refused' && (f === undefined || r.j.field === f);

/* ---- U · the upload route ---- */
let r = await upload({ ...ENV(), F25_WRITES_ENABLED: 'false' }, SID, fx('a.jpg'), 'image/jpeg');
check('U1 applications closed -> not_open, nothing stored', r.s === 503 && r.j.state === 'not_open' && B.keys().length === 0);
r = await upload({ ...ENV(), F25_IMAGES: undefined }, SID, fx('a.jpg'), 'image/jpeg');
check('U2 no image bucket configured -> not_open', r.s === 503 && r.j.state === 'not_open');
r = await run(ENV(), new Request(BASE + IR + '?s=' + SID, { method: 'POST', headers: hdr({ origin: 'https://evil.example', 'content-type': 'image/jpeg' }), body: fx('a.jpg') }));
check('U3 another website -> refused (403), nothing stored', r.s === 403 && B.keys().length === 0);
r = await run(ENV(), new Request(BASE + IR + '?s=' + SID, { method: 'GET', headers: hdr() }));
check('U4 there is no GET: an image can never be read back from the public route', r.s === 405);
r = await upload(ENV(), 'not-a-uuid', fx('a.jpg'), 'image/jpeg');
check('U5 a bad submission id -> refused', refused(r, 'submission_id'));
r = await upload(ENV(), SID, fx('e.gif'), 'image/gif');
check('U6 GIF (or any type but JPG, PNG, WebP) -> refused', refused(r, 'image_type'));
r = await upload(ENV(), SID, fx('b.png'), 'image/jpeg');
check('U7 the declared type must match the bytes (PNG sent as JPEG) -> refused', refused(r, 'image_type'));
r = await upload(ENV(), SID, new TextEncoder().encode('<script>alert(1)</script>'.repeat(20)), 'image/jpeg');
check('U8 a non-image disguised as JPEG -> refused', refused(r, 'image_type'));
const big = new Uint8Array(T.F25_MAX_IMAGE_BYTES + 1); big.set(fx('a.jpg'));
r = await upload(ENV(), SID, big, 'image/jpeg');
check('U9 larger than 8 MB -> refused', refused(r, 'image_size'));
r = await upload(ENV(), SID, fx('tiny.jpg'), 'image/jpeg');
check('U10 smaller than 200 px -> refused', refused(r, 'image_dimensions'));
check('U11 nothing at all was stored by any refused upload', B.keys().length === 0, B.keys().join());
const ids = [];
for (const [f, t] of [['a.jpg', 'image/jpeg'], ['b.png', 'image/png'], ['c.webp', 'image/webp'], ['d.jpg', 'image/jpeg']]) {
  r = await upload(ENV(), SID, fx(f), t); ids.push(r.j && r.j.id);
}
check('U12 JPG, PNG and WebP accepted, each stored in the holding area under its application', ids.every(i => /^[0-9a-f]{16}$/.test(i)) && B.keys('pending/' + SID + '/').length === 4);
const meta = B.m.get('pending/' + SID + '/' + ids[1]);
check('U13 the real dimensions and type are recorded (PNG 500x700)', meta.customMetadata.w === '500' && meta.customMetadata.h === '700' && meta.httpMetadata.contentType === 'image/png');
check('U14 the upload response holds only an id (no storage address)', calls.length === 0 && !JSON.stringify(r.j).includes('pending') && !JSON.stringify(r.j).includes('http'));
for (let i = 0; i < 6; i++) await upload(ENV(), SID2, fx('a.jpg'), 'image/jpeg');
r = await upload(ENV(), SID2, fx('a.jpg'), 'image/jpeg');
check('U15 at most 10 held images per application (5 plus replacements) -> then refused', (await (async () => { for (let i = 0; i < 4; i++) await upload(ENV(), SID2, fx('a.jpg'), 'image/jpeg'); return refused(await upload(ENV(), SID2, fx('a.jpg'), 'image/jpeg'), 'image_count'); })()));

/* ---- A · applying ---- */
r = await apply(ENV(), good());
check('A1 neither a portfolio link nor images -> refused (portfolio)', refused(r, 'portfolio') && appPosts().length === 0);
r = await apply(ENV(), good({ images: ids.slice(0, 2) }));
check('A2 two images and no portfolio -> refused (at least three, or a link)', refused(r, 'portfolio') && appPosts().length === 0);
r = await apply(ENV(), good({ images: [...ids, ids[0]] }));
check('A3 the same image twice -> refused', refused(r, 'images'));
r = await apply(ENV(), good({ images: ['ab', ...ids.slice(1)] }));
check('A4 a malformed image id -> refused', refused(r, 'images'));
r = await apply(ENV(), good({ images: ['0123456789abcdef', ...ids.slice(1, 3)] }));
check('A5 an image this application did not upload -> refused, no record, nothing left in its folder', refused(r, 'images') && appPosts().length === 0 && B.keys('applications/').length === 0);
const other = (await upload(ENV(), SID2.replace('7a', '8a'), fx('a.jpg'), 'image/jpeg')).j.id;
r = await apply(ENV(), good({ images: [other, ...ids.slice(0, 2)] }));
check("A6 another applicant's image id cannot be attached", refused(r, 'images') && appPosts().length === 0);
r = await apply(ENV(), good({ images: ['a', 'b', 'c', 'd', 'e', 'f'].map(c => c.repeat(16)) }));
check('A7 more than five images -> refused', refused(r, 'images'));

failCreate = 503;
r = await apply(ENV(), good({ images: ids.slice(0, 3) }));
check('A8 Airtable unavailable -> unavailable, the copies are removed, the held images stay for a retry', r.s === 503 && r.j.state === 'unavailable' && B.keys('applications/').length === 0 && B.keys('pending/' + SID + '/').length === 4);
failCreate = 0;

r = await apply(ENV(), good({ images: ids.slice(0, 4), website: 'colinmacaulay.ie', social_link: '@synthetic' }));
const rec = appPosts()[0] || {};
check('A9 four images, no portfolio link, no Instagram needed -> received', r.s === 200 && r.j.state === 'received', JSON.stringify(r.j));
check('A10 the record counts the images and links to the founder-only review page, never to storage',
  rec.artwork_images === 4 && /^https:\/\/plotart-studio\.colin-a41\.workers\.dev\/admin\/applications\/F25-\d{6}-[0-9A-F]{6}$/.test(rec.artwork_review) && !JSON.stringify(rec).includes('pending/') && !('portfolio' in rec), JSON.stringify(rec));
check('A11 a website typed without https:// is stored as https://colinmacaulay.ie/', rec.website === 'https://colinmacaulay.ie/');
const ref = rec.application_ref, folder = 'applications/' + ref + '/';
check('A12 the images are in the application\'s own private folder, numbered in the order chosen, with their types',
  JSON.stringify(B.keys(folder)) === JSON.stringify([folder + '1.jpg', folder + '2.png', folder + '3.webp', folder + '4.jpg', folder + 'application.json'].sort()), B.keys(folder).join());
check('A13 the bytes are exactly what was uploaded', Buffer.from(B.m.get(folder + '2.png').b).equals(Buffer.from(fx('b.png'))));
const man = JSON.parse(new TextDecoder().decode(B.m.get(folder + 'application.json').b));
check('A14 the review copy has what the founder needs (name, statement, links, images, Airtable record) and NO email address',
  man.application_ref === ref && man.artist_name === 'Synthetic Test Artist' && man.bio.startsWith('A synthetic') && man.website === 'https://colinmacaulay.ie/' && man.images.length === 4 &&
  man.images[1].w === 500 && /^recNEW/.test(man.airtable_record) && !JSON.stringify(man).toLowerCase().includes('img.test@example.com') && !('email_key' in man));
check('A15 every holding copy for the application is removed once it is received (including one the applicant removed)', B.keys('pending/' + SID + '/').length === 0);

/* portfolio link only, typed without https */
B = new Bucket();
r = await apply(ENV(), good({ portfolio: 'www.example.com/my-work', submission_id: SID2 }));
const rec2 = appPosts()[0] || {};
check('A16 portfolio link only (no images, no website) -> received; "www.example.com/my-work" stored as https', r.s === 200 && rec2.portfolio === 'https://www.example.com/my-work' && !('artwork_images' in rec2) && !('artwork_review' in rec2) && B.keys().length === 0);
r = await apply(ENV(), good({ portfolio: 'http://example.com', submission_id: '9b1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f' }));
check('A17 an http:// link is upgraded to https://', r.s === 200 && appPosts()[0].portfolio === 'https://example.com/');
for (const bad of ['javascript:alert(1)', 'https://user:pw@example.com', 'not a link', 'localhost/x']) {
  r = await apply(ENV(), good({ portfolio: bad, submission_id: '9c1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f' }));
  check(`A18 an unsafe or invalid link "${bad}" -> refused`, refused(r, 'portfolio'));
}
r = await apply({ ...ENV(), F25_IMAGES: undefined }, good({ images: ['a'.repeat(16), 'b'.repeat(16), 'c'.repeat(16)] }));
check('A19 images with no image bucket configured -> not_open (never a record without its images)', r.s === 503 && appPosts().length === 0);

/* ---- O · the ownership confirmation R3 (29 Oct 2026), with the R2 wording accepted during the switch-over */
B = new Bucket();
r = await apply(ENV(), good({ portfolio: 'example.com', submission_id: 'aa1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f' }));
check('O1 the new wording ("The artwork I\'ve submitted or linked to…") is accepted and recorded as R3', r.s === 200 && appPosts()[0].consent_version === 'F25-APPLICATION-2026-10-29-R3');
r = await apply(ENV(), good({ portfolio: 'example.com', ownership_text: T.F25_OWNERSHIP_TEXT_R2, submission_id: 'ab1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f' }));
check('O2 the previous wording, from a page loaded before the release, is still accepted and recorded as R2', r.s === 200 && appPosts()[0].consent_version === 'F25-APPLICATION-2026-10-28-R2');
r = await apply(ENV(), good({ portfolio: 'example.com', ownership_text: 'The work is mine.', submission_id: 'ac1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f' }));
check('O3 any other wording is refused', refused(r, 'ownership_text'));

/* ---- S · schema ---- */
const schema = JSON.parse(readFileSync(new URL('../airtable-schema-founding-25.proposed.json', import.meta.url), 'utf8'));
const w = schema.new_table.fields.filter(x => x.writer === 'worker').map(x => x.name);
check('S1 every field written (with images) exists in the schema as worker-written', Object.keys(rec).every(k => w.includes(k)), Object.keys(rec).filter(k => !w.includes(k)).join());
check('S2 the two new fields are a number and a url', schema.new_table.fields.find(x => x.name === 'artwork_images').type === 'number' && schema.new_table.fields.find(x => x.name === 'artwork_review').type === 'url');

console.log('PROVE · Founding 25 · artwork images with an application\n' + out.join('\n'));
console.log(`\n  ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
