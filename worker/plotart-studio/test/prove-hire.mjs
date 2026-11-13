// PROVE · Art for Hire in Artist Studio (Stage 3B-2, development 10 Nov 2026). Local only: Miniflare D1/R2, synthetic
// artists and a synthetic PA-AFH test text (the real text is not issued). Nothing here touches Cloudflare or any real record.
//   node test/prove-hire.mjs
import { cpSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished, artistRows } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const Hd = e => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
const mk = s => async (method, path, email, body) => { const r = await s.mf.dispatchFetch(s.url + path, { method, headers: Hd(email), body: body === undefined ? undefined : JSON.stringify(body) }); return { s: r.status, j: await r.json().catch(() => null) }; };
const ago = days => new Date(Date.now() - days * 86400_000).toISOString();
const sha = b => createHash('sha256').update(b).digest('hex');

/* A test copy of the Studio carrying a SYNTHETIC PA-AFH text (fixture), as the build would once a real text is issued. */
const FIX = 'test/.hire-fixture/';
rmSync(HERE + FIX, { recursive: true, force: true });
cpSync(HERE + 'src', HERE + FIX + 'src', { recursive: true });
const TXT = '<!DOCTYPE html><title>TEST ONLY · synthetic Art for Hire terms</title><p>Synthetic text for local tests. Not the PA-AFH terms.</p>';
const PDF = '%PDF-1.4 synthetic test document, not the PA-AFH terms';
const T = { title: 'PlotArt Art for Hire Artist Terms (TEST)', html: TXT, pdf_b64: Buffer.from(PDF).toString('base64'), html_sha256: sha(TXT), pdf_sha256: sha(PDF) };
const af = HERE + FIX + 'src/assets.js';
writeFileSync(af, readFileSync(af, 'utf8').replace('export const HIRE_TERMS = {};', `export const HIRE_TERMS = ${JSON.stringify({ 'PA-AFH-2026-11': T })};`));
const DOC = 'PA-AFH-2026-11';

try {
console.log('PROVE · Art for Hire (Studio)\n— switched on, test text bundled');
const S = await start({ port: 8851, env: { HIRE_TERMS_ENABLED: 'true', PARTICIPATION_DELETION: 'on', HIRE_RETENTION: 'on' }, enquiry: {}, script: FIX + 'src/index.js' });
const { db } = S, call = mk(S), bucket = await S.mf.getR2Bucket('IMAGES', 'studio');
const LEAH = 'leah-like@example.test', BEA = 'bea-other@example.test';
await seedPublished(db, { id: 'aleah', slug: 'leah-like', email: LEAH, name: 'Leah Like', works: 4, bucket, number: 1 });
await seedPublished(db, { id: 'abea', slug: 'bea-other', email: BEA, name: 'Bea Other', works: 3, bucket, number: 2 });
await db.prepare("INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, 'aleah', 0, NULL, ?), (2, 'abea', 0, NULL, ?), (3, NULL, 1, NULL, ?)").bind(ago(1), ago(1), ago(1)).run();
await db.prepare(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, accepted_at, display_name, method, statement, created_at) VALUES ('accleah', 'evleah', 'aleah', 'PA-GPIL-2026-10-29', ?, 'Leah Like', 'migrated_from_artists_table', 'test', ?)`).bind(ago(5), ago(5)).run();
const pipe = (path, method = 'GET') => S.mf.dispatchFetch(S.url + path, { method, headers: { Authorization: `Bearer ${PIPELINE_TOKEN}` } }).then(r => r.json());
const cat = () => pipe('/api/pipeline/hire-catalogue');
const NOTICE = readFileSync(HERE + 'src/enquiry.js', 'utf8').match(/const NOTICE = '([^']+)'/)[1];
const enquire = slug => S.mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json' },
  body: JSON.stringify({ ref: 'PA-' + slug, notice: NOTICE, name: 'Test Buyer', email: 'buyer@example.test', message: 'Is this work still available?' }) }).then(x => x.status);
const hireRow = id => db.prepare('SELECT * FROM artwork_hire WHERE artwork_id = ?').bind(id).first();

// the gallery and agreement state before any Art for Hire activity (E)
const galleryState = async () => JSON.stringify({ leah: await artistRows(db, 'aleah'), bea: await artistRows(db, 'abea'),
  order: await pipe('/api/pipeline/gallery-order'), queue: await pipe('/api/pipeline/queue'), docs: (await db.prepare('SELECT * FROM agreement_documents ORDER BY rowid').all()).results });
const before = await galleryState();

console.log('— 1 · switched off until the terms are issued');
let r = await call('GET', '/api/hire', LEAH);
check('G1 with no PA-AFH text installed, Studio reports Art for Hire as not open (no terms, not active)', r.s === 200 && r.j.enabled === true && r.j.terms === null && r.j.active === false && r.j.works.length === 4);
r = await call('POST', '/api/hire/accept', LEAH, { confirm: true, doc_id: DOC });
const off = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { offered: true });
check('G2 acceptance and opting a work in are both refused (409); catalogue empty', r.s === 409 && off.s === 409 && (await cat()).items.length === 0 && !(await hireRow('waleah1')));
await db.prepare("INSERT INTO hire_terms (doc_id, title, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-AFH-2026-10', 'Not the bundled text', ?, ?, '2017-01-01T00:00:00Z', ?)").bind('a'.repeat(64), 'b'.repeat(64), ago(0)).run();
r = await call('POST', '/api/hire/accept', LEAH, { confirm: true, doc_id: 'PA-AFH-2026-10' });
const tf = await S.mf.dispatchFetch(S.url + '/hire-terms/PA-AFH-2026-10.pdf', { headers: Hd(LEAH) });
check('G3 a terms row whose fingerprints do not match a bundled text is ignored: acceptance refused, nothing served', r.s === 409 && tf.status === 404);
await db.prepare('INSERT INTO hire_terms (doc_id, title, html_sha256, pdf_sha256, effective_at, created_at) VALUES (?, ?, ?, ?, ?, ?)').bind(DOC, T.title, T.html_sha256, T.pdf_sha256, '2018-01-01T00:00:00Z', ago(0)).run();

console.log('— 2 · separate, optional acceptance');
const pdf = await S.mf.dispatchFetch(S.url + `/hire-terms/${DOC}.pdf`, { headers: Hd(LEAH) });
check('A1 the issued text is served to a signed-in artist with its fingerprint', pdf.status === 200 && pdf.headers.get('X-Document-SHA256') === T.pdf_sha256 && sha(Buffer.from(await pdf.arrayBuffer())) === T.pdf_sha256);
const a1 = await call('POST', '/api/hire/accept', LEAH, { doc_id: DOC }), a2 = await call('POST', '/api/hire/accept', LEAH, { confirm: true, doc_id: 'PA-AFH-2099-01' });
check('A2 acceptance needs the tick and the current identifier (400 otherwise)', a1.s === 400 && a2.s === 400);
const bOff = await call('PUT', '/api/hire/artwork/wabea1', BEA, { offered: true });
check('A3 an artist who has not accepted cannot offer a work (409)', bOff.s === 409 && /Accept/.test(bOff.j.error));
r = await call('POST', '/api/hire/accept', LEAH, { confirm: true, doc_id: DOC });
const acc = await db.prepare("SELECT * FROM hire_terms_acceptances WHERE artist_id='aleah'").first();
const r2b = await call('POST', '/api/hire/accept', LEAH, { confirm: true, doc_id: DOC });
check('A4 accepted: one append-only row with both fingerprints, the account email and the exact statement; accepting twice records nothing new',
  r.s === 200 && acc.doc_sha256 === T.html_sha256 && acc.pdf_sha256 === T.pdf_sha256 && acc.account_email === LEAH && acc.method === 'studio_checkbox'
  && /optional/.test(acc.statement) && /PA-AFH-2026-11/.test(acc.statement) && r2b.j.already === true && (await db.prepare("SELECT COUNT(*) n FROM hire_terms_acceptances WHERE artist_id='aleah'").first()).n === 1);
check('A5 the Founding Artist agreement records are untouched by the hire acceptance', (await db.prepare("SELECT COUNT(*) n FROM agreement_acceptances WHERE artist_id='aleah'").first()).n === 1);

console.log('— 3 · the hire panel and the three gates');
const row0 = await call('GET', '/api/hire', LEAH);
check('P1 every work starts OFF with no screen or photo use', row0.j.works.every(w => w.hire.offered === 0 && w.hire.screen_use === 'none' && w.hire.photo_use === 'none' && !w.listed));
const pr = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { price_eur: 100 }), ar = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { artist_id: 'abea' });
check('P2 no price, fee or value field, and no way to set the owner (unknown fields refused)', pr.s === 400 && ar.s === 400 && !(await hireRow('waleah1')));
const draft = await call('POST', '/api/artworks', LEAH);
const dr = await call('PUT', `/api/hire/artwork/${draft.j.id}`, LEAH, { offered: true });
check('P3 a work not in the published gallery cannot be offered (409)', dr.s === 409);
r = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { offered: true, availability: 'now', county: 'Dublin', framing: 'framed', glazed: true, weight_band: '5_15kg',
  collection: 'deliver_local', deliver_km: 40, screen_use: 'background', photo_use: 'yes', handling_note: 'Two people to lift; keep out of direct sun.' });
let hr = await hireRow('waleah1');
check('P4 gates 1 and 2 met (accepted, opted in): waiting for the founder, NOT listed; catalogue still empty', r.s === 200 && r.j.review_state === 'pending' && r.j.listed === false && hr.approved_public === null && (await cat()).items.length === 0);
const q1 = (await call('GET', '/api/admin/hire', FOUNDER)).j;
check('P5 the founder’s separate queue shows it with the proposed details', q1.pending.length === 1 && q1.pending[0].artwork_id === 'waleah1' && q1.pending[0].proposed.county === 'Dublin' && q1.listed.length === 0);
const dn = await call('POST', '/api/admin/hire/artwork/waleah1/decision', FOUNDER, { decision: 'decline' });
r = await call('POST', '/api/admin/hire/artwork/waleah1/decision', FOUNDER, { decision: 'approve' });
let c = await cat();
const it = c.items[0];
check('P6 declining needs a reason; after approval (gate 3) the work is listed', dn.s === 400 && r.s === 200 && c.items.length === 1 && it.artwork_id === 'waleah1');
check('P7 the catalogue holds only approved public fields: no handling note, email, price figure or licence; price on request',
  !('handling_note' in it.hire) && !JSON.stringify(c).includes(LEAH) && !JSON.stringify(c).includes('Two people') && it.hire.price === 'Price on request'
  && !/licen[cs]e|fee|replacement|value_eur|price_eur/i.test(JSON.stringify(it)) && it.hire.county === 'Dublin' && it.hire.deliver_km === 40);

console.log('— A · artwork and artist always correspond');
const snapLeah = JSON.stringify(await hireRow('waleah1'));
const x1 = await call('PUT', '/api/hire/artwork/waleah1', BEA, { offered: false });
const x2 = await call('PUT', '/api/hire/artwork/waleah2', BEA, { offered: true });
const x3 = (await call('GET', '/api/hire', BEA)).j;
check('X1 another artist cannot withdraw, change or offer Leah’s works (404, as if they did not exist); Leah’s row unchanged',
  x1.s === 404 && x2.s === 404 && JSON.stringify(await hireRow('waleah1')) === snapLeah && !(await hireRow('waleah2')));
check('X2 an artist’s view lists only their own works', x3.works.length === 3 && x3.works.every(w => w.artwork_id.startsWith('wabea')));
const x4 = await call('POST', '/api/admin/hire/artwork/waleah1/decision', BEA, { decision: 'decline', reason: 'Trying to decline' });
const x5 = await call('GET', '/api/admin/hire', LEAH), x6 = await call('POST', '/api/admin/hire/permissions', BEA, {});
check('X3 artists cannot reach the founder’s queue, decisions or permission records (403)', x4.s === 403 && x5.s === 403 && x6.s === 403);
const x7 = await call('POST', '/api/admin/hire/permissions', FOUNDER, { artist_id: 'abea', use_kind: 'lookbook', purpose: 'Lookbook for Dublin production companies', recipients: 'Three named companies', artwork_ids: ['waleah1'], answer: 'yes', answered_at: ago(1) });
check('X4 a permission cannot name another artist’s work (400)', x7.s === 400 && /belong/.test(x7.j.error));
const x8 = await S.mf.dispatchFetch(S.url + '/api/hire', { headers: { 'X-Studio': '1' } }), x9 = await S.mf.dispatchFetch(S.url + '/api/pipeline/hire-catalogue');
check('X5 no access without sign-in, and the catalogue needs the pipeline token', [401, 403].includes(x8.status) && x9.status === 401);
await db.prepare(`INSERT INTO hire_terms_acceptances (id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, statement, method, created_at)
  VALUES ('habea', 'abea', ?, ?, ?, ?, ?, 'Bea Other', 'test', 'studio_checkbox', ?)`).bind(DOC, T.html_sha256, T.pdf_sha256, ago(0), BEA, ago(0)).run();
r = await call('PUT', '/api/hire/artwork/wabea1', BEA, { offered: true, county: 'Cork' });
check('X6 a row is always created under the signed-in artist’s own id', r.s === 200 && (await hireRow('wabea1')).artist_id === 'abea');

console.log('— D · screen use is willingness only; narrowing at once, widening reviewed');
check('D1 the catalogue states that screen and photo use is never included and that permission is agreed with the artist; the value is a willingness label only',
  /never included/.test(c.notice) && /agreed in writing with the artist/.test(c.notice) && it.hire.screen_use === 'background' && typeof it.hire.screen_use === 'string');
r = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { screen_use: 'featured' });
c = await cat();
check('D2 widening (background → featured) waits for the founder; the listing keeps the approved value meanwhile', r.j.review_state === 'pending' && c.items[0].hire.screen_use === 'background');
r = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { screen_use: 'none', photo_use: 'none' });
c = await cat(); hr = await hireRow('waleah1');
check('D3 narrowing to none applies at once, in the listing and in the approved record', c.items[0].hire.screen_use === 'none' && c.items[0].hire.photo_use === 'none'
  && JSON.parse(hr.approved_public).screen_use === 'none' && r.j.review_state === 'approved');
r = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { screen_use: 'background' });
c = await cat();
check('D4 widening back again needs a fresh founder check (not restored automatically)', r.j.review_state === 'pending' && c.items[0].hire.screen_use === 'none');
await call('POST', '/api/admin/hire/artwork/waleah1/decision', FOUNDER, { decision: 'decline', reason: 'Please confirm the framing first' });
hr = await hireRow('waleah1'); c = await cat();
check('D5 a declined change keeps the earlier approved listing and returns the artist’s values to it, with the reason', hr.review_state === 'approved' && hr.screen_use === 'none'
  && hr.decline_reason === 'Please confirm the framing first' && c.items.length === 1);
r = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { county: 'Wicklow' });
check('D6 other public changes wait for review; the listing keeps the approved county', r.j.review_state === 'pending' && (await cat()).items[0].hire.county === 'Dublin');
await call('POST', '/api/admin/hire/artwork/waleah1/decision', FOUNDER, { decision: 'approve' });
check('D7 … and appear once approved', (await cat()).items[0].hire.county === 'Wicklow');

console.log('— 7 · immediate withdrawal');
r = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { availability: 'not_now' });
check('W1 “not available at the moment” takes it out of the catalogue at once, no review', r.j.review_state === 'approved' && (await cat()).items.length === 0);
await call('PUT', '/api/hire/artwork/waleah1', LEAH, { availability: 'from', available_from: '2027-01-15' });
c = await cat();
check('W2 a “from” date is shown straight away (availability needs no review)', c.items.length === 1 && c.items[0].hire.availability === 'from' && c.items[0].hire.available_from === '2027-01-15');
r = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { offered: false });
hr = await hireRow('waleah1');
check('W3 switching a work off removes it at once (withdrawn time recorded, nothing waits)', r.s === 200 && r.j.listed === false && hr.offered === 0 && hr.withdrawn_at && (await cat()).items.length === 0);
r = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { offered: true });
hr = await hireRow('waleah1');
check('W4 switching it on again needs a full new founder approval', r.j.review_state === 'pending' && hr.approved_public === null && hr.withdrawn_at === null && (await cat()).items.length === 0);
await call('POST', '/api/admin/hire/artwork/waleah1/decision', FOUNDER, { decision: 'approve' });
await call('PUT', '/api/hire/artwork/waleah2', LEAH, { offered: true, county: 'Dublin' });
await call('POST', '/api/admin/hire/artwork/waleah2/decision', FOUNDER, { decision: 'approve' });
await call('POST', '/api/admin/hire/artwork/wabea1/decision', FOUNDER, { decision: 'approve' });
check('W5 three works listed across two artists', (await cat()).items.length === 3);

console.log('— 9 · lookbook and other use permissions');
const okP = await call('POST', '/api/admin/hire/permissions', FOUNDER, { artist_id: 'aleah', use_kind: 'lookbook', purpose: 'Winter 2026 lookbook PDF for Dublin production companies', recipients: 'Three named production companies', artwork_ids: ['waleah1', 'waleah2'], answer: 'yes', answered_at: ago(1) });
const badP = [await call('POST', '/api/admin/hire/permissions', FOUNDER, { artist_id: 'aleah', use_kind: 'lookbook', purpose: 'All uses', recipients: 'Anyone', artwork_ids: ['waleah3'], answer: 'yes', answered_at: ago(1) }),
  await call('POST', '/api/admin/hire/permissions', FOUNDER, { artist_id: 'aleah', use_kind: 'lookbook', purpose: 'Lookbook', recipients: 'x', artwork_ids: ['waleah1'], answer: 'yes', answered_at: ago(1) }),
  await call('POST', '/api/admin/hire/permissions', FOUNDER, { artist_id: 'aleah', use_kind: 'lookbook', purpose: 'Winter lookbook', recipients: 'Named companies', artwork_ids: ['waleah1'], answer: 'yes', answered_at: '2099-01-01T00:00:00Z' }),
  await call('POST', '/api/admin/hire/permissions', FOUNDER, { artist_id: 'aleah', use_kind: 'everything', purpose: 'Winter lookbook', recipients: 'Named companies', artwork_ids: ['waleah1'], answer: 'yes', answered_at: ago(1) })];
const noP = await call('POST', '/api/admin/hire/permissions', FOUNDER, { artist_id: 'aleah', use_kind: 'social', purpose: 'Instagram post about Art for Hire', recipients: 'PlotArt followers', artwork_ids: ['waleah3'], answer: 'no', answered_at: ago(1) });
const pr1 = await db.prepare('SELECT * FROM hire_use_permissions WHERE id = ?').bind(okP.j.id).first();
check('L1 a permission is recorded for one specific use, named recipients and listed works, with the artist’s answer and date', okP.s === 200 && pr1.use_kind === 'lookbook' && JSON.parse(pr1.artwork_ids).length === 2 && pr1.method === 'email_logged_by_founder' && pr1.recorded_by === FOUNDER);
check('L2 refused: a “yes” for a work not listed (409), no named recipients, a future answer date, an unknown kind of use (400); a “no” is recorded too',
  badP.map(b => b.s).join() === '409,400,400,400' && noP.s === 200);
let g = 'ran'; try { await db.prepare("UPDATE hire_use_permissions SET purpose = 'All uses' WHERE id = ?").bind(okP.j.id).run(); } catch { g = 'refused'; }
let g2 = 'ran'; try { await db.prepare("DELETE FROM hire_participation_events").run(); await db.prepare('DELETE FROM hire_use_permissions').run(); } catch { g2 = 'refused'; }
check('L3 a recorded permission can never be widened or deleted within retention', g === 'refused' && g2 === 'refused');

console.log('— E · gallery, agreements and purchase enquiries unchanged');
const after = await galleryState();
check('E1 after all of the above, every gallery, version, publish-queue, gallery-order, agreement and artist row is exactly as before (except Leah’s new draft work)',
  JSON.stringify(JSON.parse(after).bea) === JSON.stringify(JSON.parse(before).bea) && JSON.parse(after).order && JSON.stringify(JSON.parse(after).order.items ?? JSON.parse(after).order) === JSON.stringify(JSON.parse(before).order.items ?? JSON.parse(before).order)
  && JSON.stringify(JSON.parse(after).leah.versions) === JSON.stringify(JSON.parse(before).leah.versions) && JSON.stringify(JSON.parse(after).leah.publish_queue) === JSON.stringify(JSON.parse(before).leah.publish_queue)
  && JSON.stringify(JSON.parse(after).leah.agreement_acceptances) === JSON.stringify(JSON.parse(before).leah.agreement_acceptances) && JSON.stringify(JSON.parse(after).docs) === JSON.stringify(JSON.parse(before).docs)
  && JSON.stringify(JSON.parse(after).queue) === JSON.stringify(JSON.parse(before).queue)
  && JSON.stringify(JSON.parse(after).leah.artworks.filter(w => w.id !== draft.j.id)) === JSON.stringify(JSON.parse(before).leah.artworks));
const qn = (await db.prepare('SELECT COUNT(*) n FROM publish_queue').first()).n;
check('E2 no hire action created a submission, version or publish job', qn === 2 && (await db.prepare('SELECT COUNT(*) n FROM versions').first()).n === 2 && (await db.prepare('SELECT COUNT(*) n FROM submissions').first()).n === 0);
check('E3 the purchase enquiry route works as before for both galleries', await enquire('leah-like') === 200 && await enquire('bea-other') === 200
  && (await db.prepare("SELECT COUNT(*) n FROM enquiries WHERE artist_id='aleah'").first()).n === 1);
const relayDiff = (await import('node:child_process')).execSync('git diff origin/main -- src/enquiry.js', { cwd: HERE }).toString().split('\n');
// Art for Hire is released (11 Nov 2026). On a later branch the relay may change for another approved release (Open for
// Commissions, 13 Nov 2026), so this now checks what Art for Hire owns: no hire line of the relay is added, removed or changed.
check('E4 no Art for Hire line of the relay is changed by this branch (the hire paths stay exactly as released)', !relayDiff.filter(l => /^[-+][^-+]/.test(l)).some(l => /hire/i.test(l)));

console.log('— C · withdrawn and sold works are never eligible');
r = await call('POST', '/api/artworks/waleah2/availability', LEAH, { availability: 'sold' });
c = await cat();
check('C1 a work marked sold in the gallery leaves the hire catalogue at once (before any republish)', r.s === 200 && !c.items.some(x => x.artwork_id === 'waleah2') && c.items.length === 2);
await S.mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
hr = await hireRow('waleah2');
check('C2 the daily run then switches the sold work off hire and records when', hr.offered === 0 && !!hr.withdrawn_at);
const isListedSrc = readFileSync(HERE + 'src/hire.js', 'utf8');
check('C3 one check (listedRows / isListed) decides listing, for the catalogue now and for hire enquiries in Stage 3B-3', /export const isListed/.test(isListedSrc));
r = await call('POST', '/api/hire/leave', LEAH, {});
const lv = await call('POST', '/api/hire/leave', LEAH, { confirm: true });
c = await cat();
const evs = (await db.prepare("SELECT kind FROM hire_participation_events WHERE artist_id='aleah'").all()).results.map(e => e.kind);
check('C4 leaving Art for Hire needs the tick, then removes all her works at once and is recorded; Bea’s listing stays', r.s === 400 && lv.s === 200 && !c.items.some(x => x.artist_id === 'aleah')
  && c.items.length === 1 && evs.join() === 'left' && (await db.prepare("SELECT COUNT(*) n FROM artwork_hire WHERE artist_id='aleah' AND offered=1").first()).n === 0);
const lo = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { offered: true }), lw = await call('PUT', '/api/hire/artwork/waleah1', LEAH, { availability: 'not_now' });
check('C5 after leaving she cannot offer works (409) but can still narrow', lo.s === 409 && lw.s === 200);
r = await call('POST', '/api/hire/accept', LEAH, { confirm: true, doc_id: DOC });
const evs2 = (await db.prepare("SELECT kind FROM hire_participation_events WHERE artist_id='aleah' ORDER BY at, rowid").all()).results.map(e => e.kind);
check('C6 rejoining records a new acceptance and a “rejoined” event; her works stay off until she offers them again', r.s === 200 && evs2.join() === 'left,rejoined'
  && (await db.prepare("SELECT COUNT(*) n FROM hire_terms_acceptances WHERE artist_id='aleah'").first()).n === 2 && !(await cat()).items.some(x => x.artist_id === 'aleah'));
const ab = await call('POST', '/api/admin/artists/abea/end', FOUNDER, { confirm_name: 'Bea Other', source: 'artist_request', reason: 'Artist asked in Studio to leave' });
check('C7 an artist whose PlotArt participation ends leaves the hire catalogue at once', ab.s === 200 && (await cat()).items.length === 0);

console.log('— 10 · retention and deletion');
await db.prepare(`INSERT INTO artwork_hire (artwork_id, artist_id, offered, review_state, withdrawn_at, updated_at, created_at) VALUES ('waleah3', 'aleah', 0, 'draft', ?, ?, ?)`).bind(ago(31), ago(31), ago(40)).run();
await db.prepare(`INSERT INTO artwork_hire (artwork_id, artist_id, offered, review_state, withdrawn_at, updated_at, created_at) VALUES ('waleah4', 'aleah', 0, 'draft', ?, ?, ?)`).bind(ago(10), ago(10), ago(40)).run();
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after) VALUES ('eh1','PA-E-H1','aleah','Hirer','h@example.test','Hire','t',?, 'sent', ?)`).bind(ago(400), ago(-300)).run();
await db.prepare(`INSERT INTO hire_enquiries (enquiry_id, business, role, project_type, intended_use, territory_flag, delete_after, created_at) VALUES ('eh1', 'Test Productions', 'Art director', 'film_tv', 'display_staging', 'ie', ?, ?)`).bind(ago(1), ago(400)).run();
await S.mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
{
  const SD = await start({ port: 8854, env: { HIRE_TERMS_ENABLED: 'true' }, script: FIX + 'src/index.js' });
  await seedPublished(SD.db, { id: 'adry', slug: 'dry-run', email: 'dry@example.test', name: 'Dry Run', works: 1 });
  await SD.db.prepare("INSERT INTO artwork_hire (artwork_id, artist_id, offered, review_state, withdrawn_at, updated_at, created_at) VALUES ('wadry1', 'adry', 0, 'draft', ?, ?, ?)").bind(ago(31), ago(31), ago(40)).run();
  await SD.mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
  const kept = await SD.db.prepare("SELECT 1 FROM artwork_hire WHERE artwork_id='wadry1'").first();
  const aud = await SD.db.prepare("SELECT detail FROM audit WHERE action='cleanup' ORDER BY id DESC LIMIT 1").first();
  check('R0 retention is a DRY RUN until HIRE_RETENTION is on: the daily run deletes nothing and reports what is due', !!kept && /"hire":\{"withdrawn":0,"dry_run":true,"details_due":1/.test(aud.detail), aud && aud.detail);
  await SD.mf.dispose();
}
check('R1 hire details of a work withdrawn more than 30 days ago are deleted; one withdrawn 10 days ago is kept', !(await hireRow('waleah3')) && !!(await hireRow('waleah4')));
check('R2 the business details of a hire enquiry are deleted at their own date, the enquiry itself kept to its 24 months', !(await db.prepare("SELECT 1 FROM hire_enquiries WHERE enquiry_id='eh1'").first()) && !!(await db.prepare("SELECT 1 FROM enquiries WHERE id='eh1'").first()));
const au = await db.prepare("SELECT detail FROM audit WHERE action='cleanup' ORDER BY id DESC LIMIT 1").first();
check('R3 the daily run reports its Art for Hire counts without error', /"hire":\{"withdrawn"/.test(au.detail) && !/"hire":\{"error"/.test(au.detail), au.detail);

console.log('— B · six-year deletion with hire records (deletion order)');
async function oldLeaver(id, endedDaysAgo) {
  await seedPublished(db, { id, slug: id, email: `${id}@example.test`, name: `Old ${id}`, works: 2, bucket, publishedAt: ago(endedDaysAgo + 400) });
  const at = ago(endedDaysAgo);
  await db.prepare(`INSERT INTO hire_terms_acceptances (id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, statement, method, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'test', 'studio_checkbox', ?)`).bind('ha' + id, id, DOC, T.html_sha256, T.pdf_sha256, ago(endedDaysAgo + 300), `${id}@example.test`, `Old ${id}`, ago(endedDaysAgo + 300)).run();
  await db.prepare(`INSERT INTO hire_participation_events (id, artist_id, kind, at, actor, created_at) VALUES (?, ?, 'left', ?, 'test', ?)`).bind('hp' + id, id, ago(endedDaysAgo + 10), ago(endedDaysAgo + 10)).run();
  await db.prepare(`INSERT INTO artwork_hire (artwork_id, artist_id, offered, review_state, updated_at, created_at) VALUES (?, ?, 0, 'draft', ?, ?)`).bind(`w${id}1`, id, ago(endedDaysAgo + 20), ago(endedDaysAgo + 20)).run();
  await db.prepare(`INSERT INTO hire_use_permissions (id, artist_id, use_kind, purpose, recipients, artwork_ids, answer, answered_at, method, recorded_by, created_at) VALUES (?, ?, 'lookbook', 'Old lookbook', 'Named firms', '[]', 'yes', ?, 'email_logged_by_founder', 'test', ?)`)
    .bind('hu' + id, id, ago(endedDaysAgo + 50), ago(endedDaysAgo + 50)).run();
  await db.prepare("UPDATE artists SET account_status='ended' WHERE id=?").bind(id).run();
  await db.prepare("INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES (?, ?, 'ended', ?, 'founder@example.test', 'Test: left long ago', '{}')").bind('pe' + id, id, at).run();
  const del = new Date(Date.parse(at)); del.setUTCFullYear(del.getUTCFullYear() + 6);
  await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES (?, ?, ?, 'test', ?)").bind(id, at, del.toISOString(), at).run();
}
await oldLeaver('aold7y', 7 * 366);
await oldLeaver('aold2y', 2 * 366);
const cnt = async id => { const o = {}; for (const t of ['hire_terms_acceptances', 'hire_participation_events', 'hire_use_permissions', 'artwork_hire', 'record_retention', 'artists'])
  o[t] = (await db.prepare(`SELECT COUNT(*) n FROM ${t} WHERE ${t === 'artists' ? 'id' : 'artist_id'} = ?`).bind(id).first()).n; return o; };
await S.mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
const c7 = await cnt('aold7y'), c2 = await cnt('aold2y');
const au2 = await db.prepare("SELECT detail FROM audit WHERE action='cleanup' ORDER BY id DESC LIMIT 1").first();
check('B1 six years after leaving, every Art for Hire record is deleted with the rest, BEFORE the retention row (no orphans, no error)', Object.values(c7).every(n => n === 0)
  && !/"participation_deletion":\{"error"/.test(au2.detail), JSON.stringify(c7) + ' ' + au2.detail);
check('B2 an artist inside the six years keeps every hire record', c2.hire_terms_acceptances === 1 && c2.hire_participation_events === 1 && c2.hire_use_permissions === 1 && c2.record_retention === 1);
const src = readFileSync(HERE + 'src/index.js', 'utf8');
const order = src.match(/'participation_events',\s*\n\s*\.\.\.\(await H\.recordTables\(env\)\), 'record_retention'\]/);
check('B3 the deletion list places the hire tables after the artist’s other records and before record_retention', !!order);

console.log('— flag OFF (as released before legal approval)');
const S2 = await start({ port: 8852, env: {}, script: FIX + 'src/index.js' });
const call2 = mk(S2);
await seedPublished(S2.db, { id: 'aleah', slug: 'leah-like', email: LEAH, name: 'Leah Like', works: 2 });
await S2.db.prepare('INSERT INTO hire_terms (doc_id, title, html_sha256, pdf_sha256, effective_at, created_at) VALUES (?, ?, ?, ?, ?, ?)').bind(DOC, T.title, T.html_sha256, T.pdf_sha256, '2018-01-01T00:00:00Z', ago(0)).run();
await S2.db.prepare(`INSERT INTO hire_terms_acceptances (id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, statement, method, created_at)
  VALUES ('ha', 'aleah', ?, ?, ?, ?, ?, 'Leah Like', 'test', 'studio_checkbox', ?)`).bind(DOC, T.html_sha256, T.pdf_sha256, ago(0), LEAH, ago(0)).run();
await S2.db.prepare(`INSERT INTO artwork_hire (artwork_id, artist_id, offered, review_state, approved_public, approved_at, approved_by, updated_at, created_at)
  VALUES ('waleah1', 'aleah', 1, 'approved', '{"county":"Dublin","screen_use":"none","photo_use":"none"}', ?, 'founder', ?, ?)`).bind(ago(0), ago(0), ago(0)).run();
const cat2 = await (await S2.mf.dispatchFetch(S2.url + '/api/pipeline/hire-catalogue', { headers: { Authorization: `Bearer ${PIPELINE_TOKEN}` } })).json();
const ac2 = await call2('POST', '/api/hire/accept', LEAH, { confirm: true, doc_id: DOC }), of2 = await call2('PUT', '/api/hire/artwork/waleah2', LEAH, { offered: true });
const wd2 = await call2('PUT', '/api/hire/artwork/waleah1', LEAH, { offered: false });
const st2 = (await call2('GET', '/api/hire', LEAH)).j;
check('F1 with HIRE_TERMS_ENABLED off, nothing is listed even when all three gates are otherwise met', cat2.ok && cat2.items.length === 0);
check('F2 … no acceptance and no new offer (409), but switching a work off still works', ac2.s === 409 && of2.s === 409 && wd2.s === 200 && st2.enabled === false && st2.active === false);
const sh = await (await S2.mf.dispatchFetch(S2.url + '/', { headers: Hd(LEAH) })).text();
check('F3 the Studio page carries no Art for Hire tab (the panel appears only once switched on)', !/Art for Hire/.test(sh));
await S2.mf.dispose();

const S3 = await start({ port: 8853, env: { HIRE_TERMS_ENABLED: 'true' } });   // the real build: no PA-AFH text bundled
await seedPublished(S3.db, { id: 'aleah', slug: 'leah-like', email: LEAH, name: 'Leah Like', works: 1 });
await S3.db.prepare('INSERT INTO hire_terms (doc_id, title, html_sha256, pdf_sha256, effective_at, created_at) VALUES (?, ?, ?, ?, ?, ?)').bind(DOC, T.title, T.html_sha256, T.pdf_sha256, '2018-01-01T00:00:00Z', ago(0)).run();
const ac3 = await mk(S3)('POST', '/api/hire/accept', LEAH, { confirm: true, doc_id: DOC });
check('F4 the real build carries no PA-AFH text, so even switched on with a terms row, no artist can accept', ac3.s === 409);
await S3.mf.dispose();

await S.mf.dispose();
} finally { rmSync(HERE + FIX, { recursive: true, force: true }); }
const pass = results.filter(Boolean).length;
console.log(`\n${pass}/${results.length} passed`);
process.exit(pass === results.length ? 0 : 1);
