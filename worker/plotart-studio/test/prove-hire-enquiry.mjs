// PROVE · Art for Hire enquiries (Stage 3B-3, development 10 Nov 2026). Local only: Miniflare D1/R2, synthetic artists,
// a synthetic PA-AFH test text and captured (never sent) mail. Nothing here touches Cloudflare, a real record or a real inbox.
//   node test/prove-hire-enquiry.mjs
import { cpSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const Hd = e => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
const ago = days => new Date(Date.now() - days * 86400_000).toISOString();
const sha = b => createHash('sha256').update(b).digest('hex');
const ORIGIN = 'https://plotnua.ie', DOC = 'PA-AFH-2026-11';
const plusDays = n => new Date(Date.now() + n * 86400_000).toISOString().slice(0, 10);

// a Studio copy carrying a SYNTHETIC PA-AFH text, so the Studio's own controls (withdraw, sell, approve) can be used
const FIX = 'test/.hire-enq-fixture/';
rmSync(HERE + FIX, { recursive: true, force: true });
cpSync(HERE + 'src', HERE + FIX + 'src', { recursive: true });
const TXT = '<p>Synthetic test text, not the PA-AFH terms.</p>', PDF = '%PDF-1.4 synthetic';
const T = { title: 'Art for Hire Artist Terms (TEST)', html: TXT, pdf_b64: Buffer.from(PDF).toString('base64'), html_sha256: sha(TXT), pdf_sha256: sha(PDF) };
const af = HERE + FIX + 'src/assets.js';
writeFileSync(af, readFileSync(af, 'utf8').replace('export const HIRE_TERMS = {};', `export const HIRE_TERMS = ${JSON.stringify({ [DOC]: T })};`));

const ON = { HIRE_ENQUIRIES_ENABLED: 'true', HIRE_TERMS_ENABLED: 'true' };
async function scenario(S, { accept = true } = {}) {
  const { db } = S;
  await db.prepare('INSERT INTO hire_terms (doc_id, title, html_sha256, pdf_sha256, effective_at, created_at) VALUES (?, ?, ?, ?, ?, ?)').bind(DOC, T.title, T.html_sha256, T.pdf_sha256, '2018-01-01T00:00:00Z', ago(0)).run();
  for (const [id, slug, name, n] of [['aleah', 'leah-like', 'Leah Like', 5], ['abea', 'bea-other', 'Bea Other', 3], ['anon', 'no-terms', 'Non Consent', 2]]) {
    await seedPublished(db, { id, slug, email: `${slug}@artist.example.test`, name, works: n, number: { aleah: 1, abea: 2, anon: 3 }[id] });
    if (accept && id !== 'anon') await db.prepare(`INSERT INTO hire_terms_acceptances (id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, statement, method, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'test', 'studio_checkbox', ?)`).bind('ha' + id, id, DOC, T.html_sha256, T.pdf_sha256, ago(1), `${slug}@artist.example.test`, name, ago(1)).run();
    for (let i = 1; i <= n; i++) await list(db, `w${id}${i}`, id);
  }
}
async function list(db, wid, aid) {
  const ap = { availability: 'now', available_from: null, county: 'Dublin', screen_use: 'background', photo_use: 'none', framing: 'framed', glazed: 0, weight_band: '5_15kg', collection: 'ask', deliver_km: null };
  await db.prepare(`INSERT INTO artwork_hire (artwork_id, artist_id, offered, availability, county, screen_use, photo_use, framing, glazed, weight_band, collection, handling_note, review_state, approved_public, approved_at, approved_by, updated_at, created_at)
    VALUES (?, ?, 1, 'now', 'Dublin', 'background', 'none', 'framed', 0, '5_15kg', 'ask', 'PRIVATE handling note', 'approved', ?, ?, 'founder@plotnua.invalid', ?, ?)`).bind(wid, aid, JSON.stringify(ap), ago(1), ago(1), ago(1)).run();
}
const NOTICE = 'PA-ENQ-HIRE-2026-11';
const good = (ref, extra = {}) => ({ ref, notice: NOTICE, privacy: true, name: 'Hana Hirer', email: 'hana@studio.example.test', business: 'Example Productions Ltd', role: 'Art director',
  business_url: 'https://productions.example.test', project_type: 'staging', intended_use: 'display_staging', date_from: plusDays(10), date_to: plusDays(24),
  use_place: 'Dublin 8', territory: 'ie', message: 'We would like to show this work at a launch event.', ...extra });
let ipn = 0;
const hire = (S, body, { ip = `198.51.100.${++ipn % 250}`, origin = ORIGIN, method = 'POST' } = {}) => S.mf.dispatchFetch('http://enquiry.local/v1/hire-enquiry', { method,
  headers: { Origin: origin, 'Content-Type': 'application/json', 'CF-Connecting-IP': ip }, body: method === 'POST' ? JSON.stringify(body) : undefined }).then(async r => ({ s: r.status, j: await r.json().catch(() => null), h: r.headers }));
const listed = S => S.mf.dispatchFetch('http://enquiry.local/v1/hire-listed', { headers: { Origin: ORIGIN } }).then(async r => ({ s: r.status, j: await r.json().catch(() => null), h: r.headers }));
const mails = async db => (await db.prepare('SELECT * FROM mail_capture ORDER BY id').all()).results;
const count = async (db, t, w = '1=1') => (await db.prepare(`SELECT COUNT(*) n FROM ${t} WHERE ${w}`).first()).n;

try {
console.log('PROVE · Art for Hire enquiries\n— switched off (the default)');
{
  const S = await start({ port: 8871, enquiry: {} });
  await scenario(S);
  const r = await hire(S, good('PA-leah-like-waleah1')), l = await listed(S);
  check('OFF1 with the default configuration, a hire enquiry is refused (503) and nothing is stored or sent', r.s === 503 && await count(S.db, 'enquiries') === 0 && (await mails(S.db)).length === 0);
  check('OFF2 the live listed-works check answers “not open” with no works', l.s === 200 && l.j.open === false && l.j.items.length === 0);
  await S.mf.dispose();
  const S2 = await start({ port: 8872, enquiry: { HIRE_ENQUIRIES_ENABLED: 'true' } });
  await scenario(S2);
  const r2 = await hire(S2, good('PA-leah-like-waleah1'));
  check('OFF3 enquiries switched on but HIRE_TERMS_ENABLED off: still refused (both switches are needed)', r2.s === 503 && (await listed(S2)).j.items.length === 0);
  await S2.mf.dispose();
  const wr = readFileSync(HERE + 'wrangler.enquiry.toml', 'utf8');
  check('OFF4 the relay configuration ships with HIRE_ENQUIRIES_ENABLED, HIRE_TERMS_ENABLED and HIRE_SCREEN_USE all "false"',
    /HIRE_ENQUIRIES_ENABLED = "false"/.test(wr) && /HIRE_TERMS_ENABLED = "false"/.test(wr) && /HIRE_SCREEN_USE = "false"/.test(wr));
}

console.log('— switched on (local test only)');
const S = await start({ port: 8873, enquiry: ON, env: { HIRE_TERMS_ENABLED: 'true' }, script: FIX + 'src/index.js' });
const { db } = S;
await scenario(S);
const studio = async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: Hd(email), body: body === undefined ? undefined : JSON.stringify(body) }); return { s: r.status, j: await r.json().catch(() => null) }; };
const LEAH = 'leah-like@artist.example.test', BEA = 'bea-other@artist.example.test';

let r = await hire(S, good('PA-leah-like-waleah1'));
const e1 = await db.prepare("SELECT * FROM enquiries WHERE reference = ?").bind(r.j && r.j.reference).first();
const h1 = e1 && await db.prepare('SELECT * FROM hire_enquiries WHERE enquiry_id = ?').bind(e1.id).first();
const l1 = e1 && await db.prepare('SELECT * FROM enquiry_log WHERE reference = ?').bind(e1.reference).first();
check('V1 a valid enquiry for a listed work is accepted with its own PA-H- reference', r.s === 200 && /^PA-H-\d{6}-[0-9A-F]{6}$/.test(r.j.reference), JSON.stringify(r.j));
check('V2 recorded through the existing enquiry records: the enquiry (24-month deletion), its hire details, and the enquiry log (relay, no hirer details)',
  e1 && e1.artist_id === 'aleah' && e1.artwork_id === 'waleah1' && e1.notice_version === NOTICE && Math.round((Date.parse(e1.delete_after) - Date.parse(e1.created_at)) / 86400_000) === 730
  && h1 && h1.business === 'Example Productions Ltd' && h1.role === 'Art director' && h1.project_type === 'staging' && h1.territory_flag === 'ie' && h1.phone === null
  && l1 && l1.route === 'relay' && l1.artwork_id === 'waleah1' && !JSON.stringify(l1).includes('hana'));
let M = await mails(db);
const toArtist = M.find(m => m.to_addr === 'leah-like@artist.example.test'), toHirer = M.find(m => m.to_addr === 'hana@studio.example.test');
check('V3 the artist receives it, marked as a HIRE enquiry, with the hire details; Reply-To is the hirer', toArtist && toArtist.reply_to === 'hana@studio.example.test'
  && /hire enquiry/i.test(toArtist.subject) && /not a purchase/.test(toArtist.body) && /Art director, Example Productions Ltd/.test(toArtist.body) && /Dublin 8, Republic of Ireland/.test(toArtist.body));
const STATE = [/only introduces you/, /hire fee \(rental price\) is agreed directly/, /Insurance, transport/, /never granted automatically/, /Film and television screen-use arrangements cannot be made through PlotArt until its legal review is complete/];
check('V4 the hirer’s receipt and the on-page confirmation state all five points: introducer only, price with the artist, insurance and transport between the parties, screen use never automatic, film/TV not until legal review',
  toHirer && STATE.every(x => x.test(toHirer.body)) && r.j.reminders.length === 5 && STATE.every(x => r.j.reminders.some(y => x.test(y))) && /passed to Leah Like/.test(r.j.message));
check('V5 the artist’s email repeats that nothing has been licensed and film/TV is not facilitated yet', /Nothing has been licensed/.test(toArtist.body) && /legal review is complete/.test(toArtist.body));
check('V6 the artist’s address is never given to the hirer (receipt, response) and the private handling note goes nowhere',
  !toHirer.body.includes('leah-like@artist') && !JSON.stringify(r.j).includes('leah-like@artist') && !M.some(m => m.body.includes('PRIVATE handling')) && toHirer.reply_to === 'hello@plotnua.ie');

console.log('— the form’s fields and spam safeguards');
const before = await count(db, 'enquiries');
const v = [
  ['privacy acknowledgement missing', good('PA-leah-like-waleah2', { privacy: false }), 400],
  ['a field called “website” (the purchase route’s honeypot) is not part of this form', good('PA-leah-like-waleah2', { website: 'https://x.example' }), 400],
  ['no business name', good('PA-leah-like-waleah2', { business: '' }), 400],
  ['no role', good('PA-leah-like-waleah2', { role: 'x' }), 400],
  ['a website that is not a web address', good('PA-leah-like-waleah2', { business_url: 'javascript:alert(1)' }), 400],
  ['unknown project type', good('PA-leah-like-waleah2', { project_type: 'wedding' }), 400],
  ['unknown use', good('PA-leah-like-waleah2', { intended_use: 'resale' }), 400],
  ['dates in the past', good('PA-leah-like-waleah2', { date_from: '2020-01-01', date_to: '2020-01-10' }), 400],
  ['end before start', good('PA-leah-like-waleah2', { date_from: plusDays(20), date_to: plusDays(5) }), 400],
  ['no location', good('PA-leah-like-waleah2', { use_place: '' }), 400],
  ['unknown territory', good('PA-leah-like-waleah2', { territory: 'mars' }), 400],
  ['an old notice version', good('PA-leah-like-waleah2', { notice: 'PA-ENQ-2026-10-29' }), 400],
  ['a message over 1,500 characters', good('PA-leah-like-waleah2', { message: 'x'.repeat(1501) }), 400],
  ['a purchase-style reference with no work', good('PA-leah-like'), 400],
  ['filming (screen use) while legal review is pending', good('PA-leah-like-waleah2', { intended_use: 'filming', project_type: 'film_tv' }), 422],
];
const vr = []; for (const [, b, want] of v) vr.push((await hire(S, b)).s === want);
check(`F1 ${v.length} invalid enquiries are refused with the right status (including the privacy tick and no “website” field)`, vr.every(Boolean), v.filter((_, i) => !vr[i]).map(x => x[0]).join('; '));
const fv = await hire(S, good('PA-leah-like-waleah2', { intended_use: 'display_staging', project_type: 'film_tv' }));
check('F2 a film or television production may still ask about display or staging that is not filmed', fv.s === 200);
const hp = await hire(S, good('PA-leah-like-waleah2', { fax_number: '01 555 0100' }));
check('F3 the honeypot (“fax_number”, not “website”) silently drops the enquiry: a dummy reference, nothing stored, nothing sent', hp.s === 200 && hp.j.reference === 'PA-H-000000-000000'
  && await count(db, 'enquiries') === before + 1 && (await mails(db)).length === M.length + 2);
const ni = await hire(S, good('PA-bea-other-wabea1', { territory: 'ni', use_place: 'Belfast' }));
M = await mails(db);
check('F4 a project outside the Republic is accepted but flagged to the artist (pilot covers Ireland)', ni.s === 200 && /outside the Republic of Ireland/.test(M.find(m => m.subject.includes(ni.j.reference) && m.to_addr.startsWith('bea')).body));
const ws = [await hire(S, good('PA-leah-like-waleah2'), { origin: 'https://evil.example' }), await hire(S, good('PA-leah-like-waleah2'), { method: 'GET' })];
check('F5 another site cannot post (403); only POST is accepted (405)', ws[0].s === 403 && ws[1].s === 405);
const sameIp = []; for (let i = 0; i < 6; i++) sameIp.push((await hire(S, good('PA-leah-like-waleah3'), { ip: '203.0.113.9' })).s);
check('F6 rate limit: the sixth enquiry from one address within ten minutes is refused (429)', sameIp.slice(0, 5).every(x => x === 200) && sameIp[5] === 429, sameIp.join());
for (let i = 0; i < 10; i++) await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
  VALUES (?, ?, 'abea', 'wabea2', 'x', 'x@example.test', 'x', ?, ?, 'sent', ?)`).bind('ecap' + i, 'PA-H-CAP-' + i, NOTICE, ago(0), plusDays(700)).run();
const cap = await hire(S, good('PA-bea-other-wabea2'));
check('F7 daily cap: at most ten hire enquiries per work per day (429), on top of the shared per-artist and total caps', cap.s === 429);

console.log('— only works listed right now (the same rules as the Studio)');
const refuse = async (ref, why) => { const x = await hire(S, good(ref)); return x.s === 409 ? true : `${why}: ${x.s}`; };
const out = [];
await studio('PUT', '/api/hire/artwork/waleah4', LEAH, { offered: false });
out.push(await refuse('PA-leah-like-waleah4', 'withdrawn by the artist'));
await studio('PUT', '/api/hire/artwork/waleah5', LEAH, { availability: 'not_now' });
out.push(await refuse('PA-leah-like-waleah5', 'not available at the moment'));
const sold = await studio('POST', '/api/artworks/wabea3/availability', BEA, { availability: 'sold' });
out.push(await refuse('PA-bea-other-wabea3', 'sold in the gallery'));
out.push(await refuse('PA-no-terms-wanon1', 'artist has not accepted the hire terms'));
await db.prepare("UPDATE artwork_hire SET approved_public = NULL, review_state = 'pending' WHERE artwork_id = 'waleah3'").run();
out.push(await refuse('PA-leah-like-waleah3', 'not approved by the founder'));
out.push(await refuse('PA-bea-other-waleah1', 'another artist’s slug with Leah’s work'));
out.push(await refuse('PA-leah-like-wbogus99', 'a work that does not exist'));
check('C1 refused (409) for works that are withdrawn, not available now, sold, unapproved, from a non-consenting artist, mismatched or unknown', out.every(x => x === true) && sold.s === 200, out.filter(x => x !== true).join('; '));
let L = await listed(S);
const ids = L.j.items.map(i => i.id);
check('C2 the live listed-works check drops each of them at once', !['waleah3', 'waleah4', 'waleah5', 'wabea3', 'wanon1', 'wanon2'].some(x => ids.includes(x)) && ids.includes('waleah1'), ids.join());
await studio('POST', '/api/hire/leave', BEA, { confirm: true });
const bl = await hire(S, good('PA-bea-other-wabea1'));
check('C3 an artist who leaves Art for Hire: refused at once, and gone from the live check', bl.s === 409 && !(await listed(S)).j.items.some(i => i.id.startsWith('wabea')));
await studio('POST', '/api/admin/artists/aleah/end', FOUNDER, { confirm_name: 'Leah Like', source: 'artist_request', reason: 'Artist asked to leave PlotArt' });
const el = await hire(S, good('PA-leah-like-waleah1'));
check('C4 an artist whose PlotArt participation ends: refused at once; no works remain listed', el.s === 409 && (await listed(S)).j.items.length === 0);
const msg = (await hire(S, good('PA-leah-like-waleah1'))).j.error;
check('C5 the refusal does not say why (no hint whether a work was withdrawn, unapproved or not consented)', msg === 'This work isn’t available for hire at the moment.');

console.log('— the live listed-works check fails closed');
await db.prepare("DELETE FROM participation_events WHERE artist_id='aleah' AND kind='ended'").run().catch(() => {});
await S.mf.dispose();
const S3 = await start({ port: 8874, enquiry: ON });
await scenario(S3);
L = await listed(S3);
check('L1 it returns only work IDs and hire availability: no names, addresses, notes or prices', L.s === 200 && L.j.items.length === 8 && L.j.items.every(i => Object.keys(i).sort().join() === 'availability,available_from,id')
  && !/@|PRIVATE|Leah Like|price|Dublin|handling/i.test(JSON.stringify(L.j.items)));
check('L2 every answer carries a short validity (two minutes) and a 30-second cache', Date.parse(L.j.valid_until) - Date.parse(L.j.generated_at) === 120_000 && L.h.get('Cache-Control') === 'public, max-age=30');
await S3.db.prepare('ALTER TABLE artwork_hire RENAME TO artwork_hire_broken').run();
const L3 = await listed(S3), E3 = await hire(S3, good('PA-leah-like-waleah1'));
check('L3 if the listing data cannot be read, the check answers 503 (never a list) and enquiries are refused (503), nothing stored',
  L3.s === 503 && L3.j.ok === false && !('items' in L3.j) && L3.h.get('Cache-Control') === 'no-store' && E3.s === 503 && await count(S3.db, 'enquiries') === 0);
await S3.db.prepare('ALTER TABLE artwork_hire_broken RENAME TO artwork_hire').run();

console.log('— purchase enquiries unchanged (E)');
const diff = execSync('git diff origin/main -- src/enquiry.js', { cwd: HERE }).toString();
const added = diff.split('\n').filter(l => /^\+[^+]/.test(l)), removed = diff.split('\n').filter(l => /^-[^-]/.test(l));
check('P1 the purchase relay file differs from main only by three added lines (the import and the two new paths); nothing removed or changed',
  removed.length === 0 && added.length === 3 && added.every(l => /hire-enquiry\.js|\/v1\/hire-enquiry|\/v1\/hire-listed/.test(l)), added.join(' | '));
const PN = readFileSync(HERE + 'src/enquiry.js', 'utf8').match(/const NOTICE = '([^']+)'/)[1];
const buy = (body) => S3.mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: ORIGIN, 'Content-Type': 'application/json', 'CF-Connecting-IP': '192.0.2.77' }, body: JSON.stringify(body) }).then(async x => ({ s: x.status, j: await x.json() }));
const S4 = await start({ port: 8875, enquiry: {} });   // purchase route with the default test settings (hire off)
await scenario(S4);
const buy4 = body => S4.mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: ORIGIN, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(async x => ({ s: x.status, j: await x.json() }));
const p1 = await buy4({ ref: 'PA-leah-like-waleah1', notice: PN, name: 'Bob Buyer', email: 'bob@example.test', message: 'Is this work still available to buy?' });
const p2 = await buy4({ ref: 'PA-leah-like-waleah1', notice: PN, name: 'Bot', email: 'bot@example.test', message: 'Spam spam spam spam', website: 'http://spam.example' });
const p3 = await buy4({ ref: 'PA-leah-like-waleah1', notice: PN, name: 'Bob Buyer', email: 'bob@example.test', message: 'Is this work still available?', business: 'X' });
const pe = await S4.db.prepare('SELECT * FROM enquiries WHERE reference = ?').bind(p1.j.reference).first();
check('P2 a purchase enquiry still works exactly as before: PA-E- reference, no hire record, logged, artist emailed with the purchase wording',
  p1.s === 200 && /^PA-E-\d{6}-[0-9A-F]{6}$/.test(p1.j.reference) && await count(S4.db, 'hire_enquiries') === 0 && await count(S4.db, 'enquiry_log', `reference='${p1.j.reference}'`) === 1
  && (await mails(S4.db)).some(m => /PlotArt enquiry about Work 1/.test(m.subject) && !/hire/i.test(m.body)) && pe.notice_version === PN);
check('P3 the purchase honeypot (“website”) still drops spam silently, and hire fields are still refused on the purchase route', p2.s === 200 && p2.j.reference === 'PA-E-000000-0000' && p3.s === 400
  && await count(S4.db, 'enquiries') === 1);
const p4 = await buy({ ref: 'PA-leah-like-waleah1', notice: PN, name: 'Bob Buyer', email: 'bob@example.test', message: 'Is this work still available to buy?' });
check('P4 with hire switched ON the purchase route is unaffected (still a PA-E- purchase enquiry)', p4.s === 200 && /^PA-E-/.test(p4.j.reference) && await count(S3.db, 'hire_enquiries') === 0);
await S4.mf.dispose();

console.log('— Studio: purchase and hire told apart; contact details protected');
const S5 = await start({ port: 8876, enquiry: ON, env: { HIRE_TERMS_ENABLED: 'true' }, script: FIX + 'src/index.js' });
await scenario(S5);
const st5 = async (path, email) => (await S5.mf.dispatchFetch(S5.url + path, { headers: Hd(email) })).json();
const hr5 = await hire(S5, good('PA-leah-like-waleah1'));
await S5.mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: ORIGIN, 'Content-Type': 'application/json' },
  body: JSON.stringify({ ref: 'PA-leah-like-waleah2', notice: PN, name: 'Bob Buyer', email: 'bob@example.test', message: 'Is this work still available to buy?' }) });
const ae = await st5('/api/enquiries', LEAH), be = await st5('/api/enquiries', BEA), fe = await st5('/api/admin/enquiries', FOUNDER);
const hi = ae.items.find(i => i.reference === hr5.j.reference), pi = ae.items.find(i => /^PA-E-/.test(i.reference));
check('S1 the artist sees both, labelled: the hire one with business and role, the purchase one unchanged', hi && hi.kind === 'hire' && hi.business === 'Example Productions Ltd' && hi.role === 'Art director'
  && pi && pi.kind === 'purchase' && pi.business === null);
check('S2 another artist sees neither; the founder’s list labels each Hire or Purchase', be.items.length === 0 && fe.items.find(i => i.reference === hr5.j.reference).kind === 'hire' && fe.items.find(i => /^PA-E-/.test(i.reference)).kind === 'purchase');
const cat5 = await (await S5.mf.dispatchFetch(S5.url + '/api/pipeline/hire-catalogue', { headers: { Authorization: `Bearer ${PIPELINE_TOKEN}` } })).json();
check('S3 the Studio catalogue and the relay use the one rule set (same works listed) and neither exposes an artist address', JSON.stringify(cat5.items.map(i => i.artwork_id).sort()) === JSON.stringify((await listed(S5)).j.items.map(i => i.id).sort())
  && !JSON.stringify(cat5).includes('@'));
const s5 = await (await S5.mf.dispatchFetch(S5.url + '/', { headers: Hd(LEAH) })).text();
check('S4 the hire script is not part of the Studio or the public site (no public Art for Hire page)', !/hire-live/.test(s5)
  && execSync('git ls-files ../../plotart ../../*.html', { cwd: HERE }).toString().split('\n').every(f => !/hire/i.test(f)));
await S5.mf.dispose();

console.log('— the page script fails closed (real browser)');
const { chromium } = createRequire('/tmp/claude-0/studio-tools/package.json')('playwright');
const S6 = await start({ port: 8877, enquiry: { ...ON, ORIGIN: 'https://plotnua.test' } });
await scenario(S6);
const script = readFileSync(HERE + 'public-hire/hire-live.js', 'utf8');
const page = `<!doctype html><meta charset="utf-8"><title>test</title><p data-hire-status></p>
  ${['waleah1', 'waleah2', 'wabea1'].map(w => `<article data-hire-work="${w}" data-hire-ref="PA-${w.startsWith('wal') ? 'leah-like' : 'bea-other'}-${w}" data-hire-title="Work ${w}" hidden><h3>${w}</h3><p data-hire-availability></p><button data-hire-enquire>Hire enquiry</button></article>`).join('')}
  <script src="https://plotnua.test/hire-live.js" data-api="https://relay.test" defer></script>`;
const browser = await chromium.launch();
async function run(mode, act) {
  const ctx = await browser.newContext({ javaScriptEnabled: mode !== 'nojs' });
  const p = await ctx.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.route('https://plotnua.test/**', rt => rt.request().url().endsWith('hire-live.js') ? rt.fulfill({ body: script, contentType: 'text/javascript' }) : rt.fulfill({ body: page, contentType: 'text/html' }));
  await p.route('https://relay.test/**', async rt => {
    const q = rt.request();
    if (mode.fail === 'abort') return rt.abort();
    if (mode.fail === '503') return rt.fulfill({ status: 503, body: '{"ok":false}', headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': 'https://plotnua.test' } });
    const res = await S6.mf.dispatchFetch('http://enquiry.local' + new URL(q.url()).pathname, { method: q.method(), headers: { Origin: 'https://plotnua.test', 'Content-Type': 'application/json' }, body: q.postData() || undefined });
    let body = await res.text();
    if (mode.fail === 'stale' && q.url().endsWith('hire-listed')) { const j = JSON.parse(body); j.valid_until = new Date(Date.now() - 1000).toISOString(); body = JSON.stringify(j); }
    return rt.fulfill({ status: res.status, body, headers: Object.fromEntries(res.headers) });
  });
  await p.goto('https://plotnua.test/hire.html');
  await p.waitForTimeout(900);
  const out = await (act ? act(p) : null);
  const vis = await p.$$eval('[data-hire-work]', a => a.filter(x => !x.hidden).map(x => x.dataset.hireWork));
  const statusText = await p.$eval('[data-hire-status]', x => x.textContent);
  await ctx.close();
  return { vis, statusText, out, errs };
}
let u = await run('nojs');
check('U1 with no script (blocked or failed to load), no work is shown as available for hire', u.vis.length === 0);
u = await run({ fail: 'abort' });
check('U2 if the live check cannot be reached, nothing is shown and the page says availability can’t be confirmed', u.vis.length === 0 && /can’t be confirmed/.test(u.statusText));
u = await run({ fail: '503' });
check('U3 if the live check answers with an error, nothing is shown', u.vis.length === 0 && /can’t be confirmed/.test(u.statusText));
u = await run({ fail: 'stale' });
check('U4 an out-of-date answer is treated as a failure: nothing is shown', u.vis.length === 0);
u = await run({}, async p => p.$eval('[data-hire-work="waleah1"] [data-hire-availability]', x => x.textContent));
check('U5 when the check answers, exactly the listed works are shown with their hire availability', u.vis.join() === 'waleah1,waleah2,wabea1' && u.out === 'Available for hire' && !u.errs.length, JSON.stringify(u));
u = await run({}, async p => {
  await S6.db.prepare("UPDATE artwork_hire SET offered = 0, withdrawn_at = ? WHERE artwork_id = 'waleah2'").bind(new Date().toISOString()).run();
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(700);
  await S6.db.prepare("UPDATE artwork_hire SET offered = 1, withdrawn_at = NULL WHERE artwork_id = 'waleah2'").run();
});
check('U6 a work withdrawn while the page is open disappears at the next check', u.vis.join() === 'waleah1,wabea1', u.vis.join());
u = await run({}, async p => {
  await p.click('[data-hire-work="waleah1"] [data-hire-enquire]');
  const f = '.pa-hire-form form';
  const hasFilming = await p.$eval(`${f} [name=intended_use]`, s => [...s.options].some(o => o.value === 'filming'));
  const explain = await p.$$eval('.pa-hire-explain li', l => l.map(x => x.textContent));
  for (const [k, val] of Object.entries({ name: 'Hana Hirer', email: 'hana@studio.example.test', business: 'Example Productions Ltd', role: 'Art director', use_place: 'Dublin 8' })) await p.fill(`${f} [name=${k}]`, val);
  await p.selectOption(`${f} [name=project_type]`, 'staging'); await p.selectOption(`${f} [name=intended_use]`, 'display_staging'); await p.selectOption(`${f} [name=territory]`, 'ie');
  await p.fill(`${f} [name=date_from]`, plusDays(10)); await p.fill(`${f} [name=date_to]`, plusDays(20));
  await p.click(`${f} [type=submit]`); await p.waitForTimeout(500);
  const noTick = await p.$eval('.pa-hire-err', x => x.textContent);
  await p.check(`${f} [name=privacy]`); await p.click(`${f} [type=submit]`); await p.waitForTimeout(900);
  return { hasFilming, explain, noTick, done: await p.$eval('.pa-hire-form', x => x.textContent) };
});
check('U7 the form collects every required field, shows the five statements, needs the privacy tick, and confirms with a PA-H- reference; it offers no filming option',
  u.out.explain.length === 5 && /privacy|handles hire enquiries|confirm/i.test(u.out.noTick) && /Enquiry sent/.test(u.out.done) && /PA-H-\d{6}-/.test(u.out.done) && u.out.hasFilming === false, JSON.stringify(u.out));
u = await run({}, async p => {
  await p.click('[data-hire-work="wabea1"] [data-hire-enquire]');
  await S6.db.prepare("UPDATE artwork_hire SET offered = 0, withdrawn_at = ? WHERE artwork_id = 'wabea1'").bind(new Date().toISOString()).run();
  const f = '.pa-hire-form form';
  for (const [k, val] of Object.entries({ name: 'Hana Hirer', email: 'hana@studio.example.test', business: 'Example Productions Ltd', role: 'Art director', use_place: 'Cork' })) await p.fill(`${f} [name=${k}]`, val);
  await p.selectOption(`${f} [name=project_type]`, 'interiors'); await p.selectOption(`${f} [name=intended_use]`, 'display_staging'); await p.selectOption(`${f} [name=territory]`, 'ie');
  await p.fill(`${f} [name=date_from]`, plusDays(10)); await p.fill(`${f} [name=date_to]`, plusDays(20)); await p.check(`${f} [name=privacy]`);
  await p.click(`${f} [type=submit]`); await p.waitForTimeout(1200);
  return (await p.$('.pa-hire-form')) ? await p.$eval('.pa-hire-form', x => x.textContent) : 'form closed';
});
check('U8 if the work is withdrawn while the form is open, the relay refuses it and the tile and form disappear', !u.vis.includes('wabea1') && await count(S6.db, 'hire_enquiries', "enquiry_id IN (SELECT id FROM enquiries WHERE artwork_id='wabea1')") === 0, JSON.stringify(u));
u = await run({}, async p => {
  await p.route('https://relay.test/**', rt => rt.abort());
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(700);
});
check('U9 if the check fails after works were shown, every work is hidden again', u.vis.length === 0 && /can’t be confirmed/.test(u.statusText));
await browser.close();
await S6.mf.dispose();
await S3.mf.dispose();
} finally { rmSync(HERE + FIX, { recursive: true, force: true }); }
const pass = results.filter(Boolean).length;
console.log(`\nHIRE ENQUIRIES · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
process.exit(pass === results.length ? 0 : 1);
