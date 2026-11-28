// PROVE · Opportunities shown publicly (migration 0015; founder approval 16 Nov 2026).
// Local only: Miniflare D1/R2, synthetic artists. Nothing here touches Cloudflare or any real record.
//   node test/prove-opportunities-public.mjs [--export-dir DIR] [--shots DIR]
//   --export-dir writes pipeline exports (shown / none) for the website proof (atlas-tools/prove-plotart-opportunities.py).
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished, artistRows } from './seed.mjs';
import { chromium } from './hire-page-harness.mjs';
import * as L from '../src/lib.js';
import * as R from '../src/opportunities-rules.js';

const arg = k => process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : null;
const OUT = arg('--export-dir'), SHOTS = arg('--shots');
if (OUT) mkdirSync(OUT, { recursive: true });
if (SHOTS) mkdirSync(SHOTS, { recursive: true });
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 600)}]` : ''}`); };
const HERE = new URL('..', import.meta.url).pathname;
const SCHEMA = readFileSync(HERE + 'schema.sql', 'utf8');
const Hd = e => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
const mk = S => async (method, path, email, body) => {
  const r = await S.mf.dispatchFetch(S.url + path, { method, headers: Hd(email), body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
};
const T0 = '2026-11-14T10:00:00.000Z';
const answer = (db, id, interests, extra = {}) => db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, practical_note, care_condition, created_at, updated_at, updated_by)
  VALUES (?,?,?,?,?,?,?,?,?,?,?)`).bind(id, JSON.stringify(interests), extra.county ?? 'Cork', JSON.stringify(extra.transport ?? ['courier']), ('mode' in extra ? extra.mode : 'anywhere'), '[]',
  extra.note ?? 'Private practical note: large canvases, phone 087 000 0000.', extra.care ?? 1, T0, T0, `${id}@example.test`).run();
const SECRET = /Cork|courier|anywhere|Private practical note|087 000|care|online_only|@example/;

let S, P, browser;
try {
console.log('PROVE · Opportunities shown publicly');

/* ---------------------------------------------------------------- before migration 0015 */
console.log('— before migration 0015 (production today)');
const before = SCHEMA.replace(/\n-- PlotArt Studio · migration 0015[\s\S]*$/, '\n');
check('B0 the schema without 0015 has no public columns', !/public_display/.test(before) && /public_display/.test(SCHEMA));
P = await start({ port: 8895, schemaSql: before });
const pcall = mk(P);
await seedPublished(P.db, { id: 'apre', slug: 'pre-test', email: 'pre@example.test', name: 'Pre Test', works: 2, number: 1 });
await answer(P.db, 'apre', ['living_gallery', 'commissions']);
let r = await pcall('GET', '/api/opportunities', 'pre@example.test');
const sv = await pcall('PUT', '/api/opportunities', 'pre@example.test', { interests: ['talks'], artwork_county: 'Cork', transport: ['courier'], coverage: { mode: 'anywhere' }, note: 'x', care_condition: false });
const svPub = await pcall('PUT', '/api/opportunities', 'pre@example.test', { interests: ['talks'], public_display: true });
const vis = await pcall('PUT', '/api/opportunities/visibility', 'pre@example.test', { show: true });
const me = await pcall('GET', '/api/me', 'pre@example.test');
const vs = (await P.db.prepare("SELECT snapshot FROM versions WHERE artist_id='apre'").all()).results;
check('B1 before 0015 the Studio works as before: no public choice offered, saving works, a public choice is refused, the dashboard asks nothing new, and no version carries open_to',
  r.j.options.public === null && sv.s === 200 && sv.j.instant_version === null && svPub.s === 400 && vis.s === 409 && me.j.opportunities === 'answered'
  && vs.every(v => !/open_to/.test(v.snapshot)), JSON.stringify([r.j.options.public, sv.s, sv.j.instant_version, svPub.s, vis.s, me.j.opportunities]));
await P.mf.dispose(); P = null;

/* ---------------------------------------------------------------- after migration 0015 */
console.log('— after migration 0015');
S = await start({ port: 8896 });
const call = mk(S), { db } = S;
const ORLA = 'orla-test@example.test', BEN = 'ben-test@example.test', NEW = 'new-test@example.test', OFF = 'off-test@example.test', UNPUB = 'unpub-test@example.test';
await seedPublished(db, { id: 'aorla', slug: 'orla-test', email: ORLA, name: 'Orla Test', works: 2, number: 1 });
await seedPublished(db, { id: 'aben', slug: 'ben-test', email: BEN, name: 'Ben Test', works: 2, number: 2 });
await seedPublished(db, { id: 'anew', slug: 'new-test', email: NEW, name: 'New Test', works: 1, number: 3 });
await seedPublished(db, { id: 'aoff', slug: 'off-test', email: OFF, name: 'Off Test', works: 1, number: 4 });
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('aunpub','unpub-test',?,'Unpub Test',0,'active',?,?)`).bind(UNPUB, T0, T0).run();
// answers saved before 0015 (Orla, Ben, Off), under "Your answers are never published"
await answer(db, 'aorla', ['exhibitions', 'living_gallery', 'commissions', 'talks']);
await answer(db, 'aben', ['art_for_hire', 'mobile_gallery', 'venues']);
await answer(db, 'aoff', ['online_only'], { transport: [], mode: null, care: 0 });
const row = id => db.prepare('SELECT * FROM artist_opportunities WHERE artist_id=?').bind(id).first();
const versions = async id => (await db.prepare('SELECT * FROM versions WHERE artist_id=? ORDER BY version').bind(id).all()).results;
const queue = async id => (await db.prepare('SELECT * FROM publish_queue WHERE artist_id=? ORDER BY version').bind(id).all()).results;
const lastSnap = async id => { const v = await versions(id); return JSON.parse(v[v.length - 1].snapshot); };
const strip = s => JSON.stringify({ ...s, artist: { ...s.artist, open_to: undefined, open_for_commissions: undefined } });

check('S1 every earlier answer is kept unchanged and starts "not decided" (NULL): nothing is shown', (await row('aorla')).public_display === null && (await row('aben')).public_display === null
  && (await row('aorla')).practical_note.startsWith('Private') && (await row('aorla')).care_condition === 1);
let bad = 'no'; try { await db.prepare("UPDATE artist_opportunities SET public_display=2 WHERE artist_id='aorla'").run(); } catch { bad = 'yes'; }
check('S2 public_display accepts only NULL, 0 or 1', bad === 'yes');
r = await call('GET', '/api/me', ORLA);
const rb = await call('GET', '/api/me', BEN), roff = await call('GET', '/api/me', OFF);
check('S3 the dashboard asks Orla and Ben to confirm (they chose something that could be shown); "Online only" Off is not asked', r.j.opportunities === 'confirm' && rb.j.opportunities === 'confirm' && roff.j.opportunities === 'answered',
  JSON.stringify([r.j.opportunities, rb.j.opportunities, roff.j.opportunities]));
r = await call('GET', '/api/opportunities', ORLA);
check('S4 the artist view offers the choice (the explained wording and notice version) and shows nothing yet', r.j.options.public && r.j.options.public.notice === R.PUBLIC_NOTICE && r.j.shown.length === 0 && r.j.saved.public_display === null);

console.log('— saving the form never decides for an earlier answer');
const v0 = (await versions('aorla')).length;
r = await call('PUT', '/api/opportunities', ORLA, { interests: ['exhibitions', 'living_gallery', 'commissions', 'talks'], artwork_county: 'Cork', transport: ['courier'], coverage: { mode: 'anywhere' }, note: 'Private practical note.', care_condition: true });
check('S5 re-saving the answers without the choice keeps "not decided": nothing shown, no version made', r.s === 200 && (await row('aorla')).public_display === null && r.j.shown.length === 0 && r.j.instant_version === null && (await versions('aorla')).length === v0,
  JSON.stringify(r.j));

console.log('— the one-click confirmation');
const benBefore = JSON.stringify(await artistRows(db, 'aben'));
const bads = [await call('PUT', '/api/opportunities/visibility', ORLA, {}), await call('PUT', '/api/opportunities/visibility', ORLA, { show: 'yes' }),
  await call('PUT', '/api/opportunities/visibility', ORLA, { show: true, artist_id: 'aben' }), await call('PUT', '/api/opportunities/visibility', ORLA, { show: false, commissions: true }),
  await call('PUT', '/api/opportunities/visibility', FOUNDER, { show: true }), await call('PUT', '/api/opportunities/visibility', UNPUB, { show: true })];
check('S6 refused: no choice, a non-true/false choice, another artist’s id, commissions without showing, the founder address, an artist with no answers', bads.every(b => b.s >= 400) && (await row('aorla')).public_display === null,
  JSON.stringify(bads.map(b => b.s)));
r = await call('PUT', '/api/opportunities/visibility', ORLA, { show: true });
const v1 = await versions('aorla'), q1 = await queue('aorla'), s1 = JSON.parse(v1[v1.length - 1].snapshot);
const s0 = JSON.parse(v1[v1.length - 2].snapshot);
check('S7 "Yes, show them": shown (1, dated, notice recorded), ONE instant version whose only change is open_to in the fixed public order, queued like any instant update',
  r.s === 200 && (await row('aorla')).public_display === 1 && (await row('aorla')).public_notice === R.PUBLIC_NOTICE && !!(await row('aorla')).public_decided_at
  && v1.length === v0 + 1 && v1[v1.length - 1].source === 'instant' && JSON.stringify(s1.artist.open_to) === '["exhibitions","living_gallery","commissions","talks"]'
  && strip(s1) === strip(s0) && q1[q1.length - 1].kind === 'instant' && q1[q1.length - 1].status === 'awaiting_founder', JSON.stringify([r.j, s1.artist]));
check('S8 commissions were NOT switched on: the separate public setting is unchanged unless the artist ticks it', (await db.prepare("SELECT open_for_commissions o FROM artists WHERE id='aorla'").first()).o === 0 && s1.artist.open_for_commissions === false);
check('S9 nothing private travels: the snapshot carries no county of the artwork, transport, coverage, care box or note', !SECRET.test(JSON.stringify(s1.artist.open_to)) && !/practical|transport|coverage|care_condition/.test(JSON.stringify(s1)));
const st = (await call('GET', '/api/me', ORLA)).j;
check('S10 it is never a change waiting for review (instant tier), and the dashboard no longer asks', !st.status.unsubmitted.some(c => /pportunit/.test(c.what)) && st.opportunities === 'answered');
check('S11 another artist’s records are untouched', JSON.stringify(await artistRows(db, 'aben')) === benBefore);

console.log('— the commissions setting in the same click (Ben has not chosen Commissions; Orla has)');
r = await call('PUT', '/api/opportunities/visibility', BEN, { show: true, commissions: true });
check('S12 Ben cannot switch commissions on through the confirmation (he did not choose Commissions); nothing changed', r.s === 400 && (await row('aben')).public_display === null
  && (await db.prepare("SELECT open_for_commissions o FROM artists WHERE id='aben'").first()).o === 0, JSON.stringify(r.j));
r = await call('PUT', '/api/opportunities/visibility', BEN, { show: true });
const nV = (await versions('aorla')).length;
r = await call('PUT', '/api/opportunities/visibility', ORLA, { show: true, commissions: true });
const sC = await lastSnap('aorla'), au = (await db.prepare("SELECT action, actor, detail FROM audit WHERE artist_id='aorla' AND action IN ('commissions_on','opportunities_shown') ORDER BY id").all()).results;
check('S13 Orla ticks the commissions box: "Open for commissions" switches on as her explicit, audited choice, in ONE instant version with her opportunities',
  r.j.commissions_switched_on === true && (await versions('aorla')).length === nV + 1 && sC.artist.open_for_commissions === true && sC.artist.open_to.length === 4
  && au.some(a => a.action === 'commissions_on' && a.actor === ORLA && /opportunities confirmation/.test(a.detail)), JSON.stringify([r.j, au]));

console.log('— withdrawing interest, keeping private, and new artists');
r = await call('PUT', '/api/opportunities', ORLA, { interests: ['exhibitions', 'commissions'], artwork_county: 'Cork', transport: ['courier'], coverage: { mode: 'anywhere' }, note: 'Private practical note.', care_condition: true });
const sW = await lastSnap('aorla');
check('S14 deselecting Living Gallery and Talks removes them at the next instant update (the choice to show stays as it was)', JSON.stringify(sW.artist.open_to) === '["exhibitions","commissions"]' && r.j.instant_version > 0 && (await row('aorla')).public_display === 1, JSON.stringify(sW.artist));
r = await call('PUT', '/api/opportunities/visibility', ORLA, { show: false });
const sP = await lastSnap('aorla');
check('S15 "Keep them private" removes every listing at the next instant update (open_to removed), keeps every answer, and leaves the commissions setting to its own switch',
  !('open_to' in sP.artist) && (await row('aorla')).public_display === 0 && JSON.parse((await row('aorla')).interests).length === 2 && sP.artist.open_for_commissions === true, JSON.stringify(sP.artist));
r = await call('PUT', '/api/opportunities', BEN, { interests: ['online_only'] });
check('S16 choosing "Online gallery only for now" shows nothing, even when showing is on', !('open_to' in (await lastSnap('aben')).artist) && (await row('aben')).public_display === 1);
r = await call('PUT', '/api/opportunities', NEW, { interests: ['venues', 'art_for_hire'], public_display: true });
const sN = await lastSnap('anew');
check('S17 a new answer where the artist ticked the box is shown, with the notice recorded', JSON.stringify(sN.artist.open_to) === '["art_for_hire","venues"]' && (await row('anew')).public_notice === R.PUBLIC_NOTICE, JSON.stringify(sN.artist));
await db.prepare("DELETE FROM artist_opportunities WHERE artist_id='anew'").run();
r = await call('PUT', '/api/opportunities', NEW, { interests: ['venues'], public_display: false });
check('S18 a new answer with the box unticked is kept private', (await row('anew')).public_display === 0 && !('open_to' in (await lastSnap('anew')).artist));
await db.prepare("DELETE FROM artist_opportunities WHERE artist_id='anew'").run();
r = await call('PUT', '/api/opportunities', NEW, { interests: ['venues'] });
check('S19 a new answer sent without the choice (an older page) stays "not decided": a box the artist never saw can never publish anything', (await row('anew')).public_display === null);
r = await call('PUT', '/api/opportunities', UNPUB, { interests: ['talks'], public_display: true });
check('S20 an artist with no published gallery: saved, but no version is made (nothing to update until a gallery is approved)', r.s === 200 && r.j.instant_version === null && (await versions('aunpub')).length === 0);

console.log('— exports, and only through an approved gallery');
const qid = (await queue('aorla')).filter(q => q.status === 'awaiting_founder').pop().id;
let pub = await call('POST', `/api/admin/queue/${qid}/publish`, FOUNDER, {});
if (pub.j && pub.j.needs_confirmation) pub = await call('POST', `/api/admin/queue/${qid}/publish`, FOUNDER, { confirm_without_agreement: true });
let ex = await (await S.mf.dispatchFetch(S.url + `/api/pipeline/export/${qid}`, { method: 'POST', headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } })).json();
check('S21 a "kept private" export carries no open_to', pub.s === 200 && ex.ok && !('open_to' in ex.gallery.artist), JSON.stringify(ex.gallery && ex.gallery.artist));
if (OUT) writeFileSync(OUT + '/export-none.json', JSON.stringify(ex.gallery, null, 2));
await S.mf.dispatchFetch(S.url + `/api/pipeline/result/${qid}`, { method: 'POST', headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN, 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'published', detail: 'test' }) });
await call('PUT', '/api/opportunities/visibility', ORLA, { show: true });
await call('PUT', '/api/opportunities', ORLA, { interests: ['exhibitions', 'living_gallery', 'art_for_hire', 'mobile_gallery', 'venues', 'commissions', 'talks'], artwork_county: 'Cork', transport: ['courier'], coverage: { mode: 'anywhere' }, note: 'Private practical note.', care_condition: true });
const q2 = (await queue('aorla')).filter(q => q.status === 'awaiting_founder').pop().id;
pub = await call('POST', `/api/admin/queue/${q2}/publish`, FOUNDER, {});
if (pub.j && pub.j.needs_confirmation) pub = await call('POST', `/api/admin/queue/${q2}/publish`, FOUNDER, { confirm_without_agreement: true });
ex = await (await S.mf.dispatchFetch(S.url + `/api/pipeline/export/${q2}`, { method: 'POST', headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } })).json();
check('S22 a shown export carries exactly the seven public keys in order, and nothing private', JSON.stringify(ex.gallery.artist.open_to) === JSON.stringify(R.PUBLIC_KEYS)
  && !/Cork|courier|Private practical|care_condition|practical_note|transport/.test(JSON.stringify(ex.gallery)), JSON.stringify(ex.gallery.artist));
if (OUT) writeFileSync(OUT + '/export-shown.json', JSON.stringify(ex.gallery, null, 2));
check('S23 the shared rule and the snapshot agree: lib OPEN_TO is exactly the Studio’s PUBLIC_KEYS', JSON.stringify(L.OPEN_TO) === JSON.stringify(R.PUBLIC_KEYS));

console.log('— a full submission approved later keeps the newest choice');
await db.prepare("UPDATE artworks SET price_eur=750 WHERE id='waben1'").run();
let sub = await call('POST', '/api/submit', BEN, { note: 'New price' });
if (sub.s !== 200) sub = await call('POST', '/api/submit', BEN, {});
await call('PUT', '/api/opportunities', BEN, { interests: ['mobile_gallery'], public_display: true });
const sid = (await db.prepare("SELECT id FROM submissions WHERE artist_id='aben' AND status='pending'").first() || {}).id;
const dec = sid ? await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve' }) : { s: 0 };
const sA = await lastSnap('aben');
check('S24 approving a price change submitted before the artist changed their opportunities publishes the newest choice (as for availability)',
  dec.s === 200 && JSON.stringify(sA.artist.open_to) === '["mobile_gallery"]', JSON.stringify([sub.s, sub.j && sub.j.error, dec.s, sA.artist]));

console.log('— the founder’s view and the audit trail');
r = await call('GET', '/api/admin/opportunities', FOUNDER);
check('S25 the Review Desk shows who is shown, kept private or not confirmed (read-only)', r.s === 200 && r.j.totals.shown >= 2 && 'undecided' in r.j.totals && r.j.options.public && r.j.items.find(i => i.id === 'aorla').prefs.public_display === true, JSON.stringify(r.j.totals));
const audits = (await db.prepare("SELECT detail FROM audit WHERE action LIKE 'opportunities_%'").all()).results.map(a => a.detail || '').join(' ');
check('S26 the audit records each choice and the notice version, never the note text', /PA-OPP-PUBLIC-2026-11-R2/.test(audits) && !/Private practical note/.test(audits));

/* ---------------------------------------------------------------- browser */
console.log('— in the browser');
browser = await chromium.launch();
const page = async (who, vp = { width: 1280, height: 900 }) => {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: SHOTS ? 2 : 1, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(who) } });
  const p = await ctx.newPage(); p.errs = []; p.on('pageerror', e => p.errs.push(e.message)); return p;
};
const shot = async (p, f) => { if (SHOTS) { await p.evaluate(() => document.querySelectorAll('.st-opp-save, .st-top').forEach(n => { n.style.position = 'static'; })); await p.screenshot({ path: join(SHOTS, f), fullPage: true }); } };
// a fresh artist who answered before 0015, with Commissions and the commissions switch off
await seedPublished(db, { id: 'acia', slug: 'cia-test', email: 'cia-test@example.test', name: 'Cia Test', works: 1, number: 5 });
await answer(db, 'acia', ['living_gallery', 'commissions']);
let p = await page('cia-test@example.test');
await p.goto(S.url + '/#/', { waitUntil: 'load' }); await p.waitForTimeout(900);
const card = await p.locator('#opp-confirm-home').innerText().catch(() => '');
check('U1 the dashboard shows the one-click confirmation with her choices, the never-published promise explained, and an UNTICKED commissions box',
  /Show your opportunities on your gallery\?/.test(card) && /Art Hosting at home · Commissions/.test(card) && /wouldn’t be published/.test(card)
  && await p.locator('[data-cf-c]').count() === 1 && !(await p.locator('[data-cf-c]').isChecked()) && p.errs.length === 0, card + p.errs.join());
await shot(p, 'studio-dashboard-confirm-1280.png');
const p390 = await page('cia-test@example.test', { width: 390, height: 844 });
await p390.goto(S.url + '/#/', { waitUntil: 'load' }); await p390.waitForTimeout(900); await shot(p390, 'studio-dashboard-confirm-390.png');
await p.click('[data-cf="1"]'); await p.waitForTimeout(900);
check('U2 one click on "Yes, show them" saves it and the card goes; commissions stay off because the box was not ticked',
  (await row('acia')).public_display === 1 && await p.locator('#opp-confirm-home').count() === 0
  && (await db.prepare("SELECT open_for_commissions o FROM artists WHERE id='acia'").first()).o === 0);
await p.goto(S.url + '/#/opportunities', { waitUntil: 'load' }); await p.waitForTimeout(800);
const pubTxt = await p.locator('#o-pub-card').innerText();
check('U3 the form now shows the public choice (ticked) with its explanation, and the footer says which answers are never published',
  await p.isChecked('#o-pub') && /never means anything has been arranged/.test(pubTxt) && /Where your artwork is kept, your placement transport and delivery area, the care box and your note are never published/.test(await p.locator('.st-opp-priv').innerText()));
await p.uncheck('#o-pub'); await p.click('#o-save'); await p.waitForTimeout(700);
check('U4 unticking and saving keeps them private in one step', (await row('acia')).public_display === 0 && !('open_to' in (await lastSnap('acia')).artist));
// a brand-new artist: the box starts UNTICKED (showing is always the artist's active choice), explanation beside it
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('adan','dan-test','dan-test@example.test','Dan Test',0,'active',?,?)`).bind(T0, T0).run();
p = await page('dan-test@example.test');
await p.goto(S.url + '/#/opportunities', { waitUntil: 'load' }); await p.waitForTimeout(800);
await p.click('[data-k="exhibitions"]'); await p.click('[data-k="commissions"]'); await p.waitForTimeout(150);
check('U5 a new artist sees the box UNTICKED by default, with the explanation beside it, and no commissions offer until they tick it',
  !(await p.isChecked('#o-pub')) && /If you tick this/.test(await p.locator('#o-pub-card').innerText()) && /Leave it unticked to keep everything private/.test(await p.locator('#o-pub-card').innerText())
  && !(await p.locator('#o-ofc-box').isVisible()) && p.errs.length === 0);
await shot(p, 'studio-opportunities-new-artist-1280.png');
await p.click('#o-save'); await p.waitForTimeout(700);
check('U6 saving without ticking keeps everything private: recorded as private, nothing shown, nothing published', (await row('adan')).public_display === 0
  && (await call('GET', '/api/opportunities', 'dan-test@example.test')).j.shown.length === 0);
await p.check('#o-pub'); await p.waitForTimeout(150);
check('U6b ticking it is the active choice: the optional commissions box then appears, UNTICKED', await p.locator('#o-ofc-box').isVisible() && !(await p.isChecked('#o-ofc')));
await shot(p, 'studio-opportunities-new-artist-ticked-1280.png');
await p.click('#o-save'); await p.waitForTimeout(700);
check('U6c saving after ticking records it as shown with the notice version', (await row('adan')).public_display === 1 && (await row('adan')).public_notice === R.PUBLIC_NOTICE);
const f = await page(FOUNDER);
await f.goto(S.url + '/admin/opportunities', { waitUntil: 'load' }); await f.waitForTimeout(900);
const ft = await f.locator('#app').innerText();
check('U7 the Review Desk shows "shown publicly" and "not confirmed yet" counts and each artist’s public status', /shown publicly/.test(ft) && /not confirmed yet/.test(ft) && /Public gallery: shown/.test(ft) && f.errs.length === 0, ft.slice(0, 400));
await shot(f, 'review-desk-opportunities-1280.png');

/* ---- founder confirmation of an agreement obtained in person (17 Nov 2026 correction) */
console.log('— founder confirmation');
await seedPublished(db, { id: 'afc', slug: 'fc-test', email: 'fc-test@example.test', name: 'Fay Confirm', works: 2, number: 7 });
await seedPublished(db, { id: 'afd', slug: 'fd-test', email: 'fd-test@example.test', name: 'Fred Decided', works: 1, number: 8 });
await answer(db, 'afc', ['exhibitions', 'living_gallery', 'art_for_hire', 'commissions']);   // saved before 0015: NULL
await answer(db, 'afd', ['living_gallery']);
await db.prepare("UPDATE artist_opportunities SET public_display=0, public_decided_at=?, public_notice=? WHERE artist_id='afd'").bind('2026-11-16T21:00:00.000Z', R.PUBLIC_NOTICE).run();
const fcBefore = await row('afc'), fcVers = (await versions('afc')).length;
const FC = { artist_id: 'afc', interests: ['exhibitions', 'living_gallery', 'art_for_hire', 'commissions'], confirm: true };
r = await call('POST', '/api/admin/opportunities/confirm', 'fc-test@example.test', FC);
const r2 = await call('POST', '/api/admin/opportunities/confirm', null, FC);
check('F1 only the founder can record it: the artist (403) and a signed-out caller are refused; nothing changes',
  r.s === 403 && r2.s !== 200 && (await row('afc')).public_display === null);
r = await call('POST', '/api/admin/opportunities/confirm', FOUNDER, { ...FC, interests: ['exhibitions'] });
const r3 = await call('POST', '/api/admin/opportunities/confirm', FOUNDER, { ...FC, confirm: 'yes' });
const r4 = await call('POST', '/api/admin/opportunities/confirm', FOUNDER, { ...FC, public_display: true });
check('F2 refused without the explicit confirmation, with stale answers, or with any extra field; nothing changes',
  r.s === 409 && r3.s === 400 && r4.s === 400 && (await row('afc')).public_display === null && (await versions('afc')).length === fcVers, JSON.stringify([r.s, r3.s, r4.s]));
r = await call('POST', '/api/admin/opportunities/confirm', FOUNDER, { artist_id: 'afd', interests: ['living_gallery'], confirm: true });
check('F3 it can never override the artist’s own choice ("kept private" stays private)', r.s === 409 && (await row('afd')).public_display === 0);
r = await call('POST', '/api/admin/opportunities/confirm', FOUNDER, FC);
const fc = await row('afc'), fcSnap = await lastSnap('afc');
const fcAud = await db.prepare("SELECT * FROM audit WHERE action='opportunities_shown_founder_confirmed' AND artist_id='afc'").first();
check('F4 confirmed: shown under the founder’s own notice id, answers and every other column unchanged, audited with the statement',
  r.s === 200 && fc.public_display === 1 && fc.public_notice === R.FOUNDER_NOTICE && fc.interests === fcBefore.interests && fc.practical_note === fcBefore.practical_note
  && fc.artwork_county === fcBefore.artwork_county && fc.transport === fcBefore.transport && fcAud && fcAud.actor === FOUNDER && /personally obtained Fay Confirm/.test(fcAud.detail), JSON.stringify(r.j));
check('F5 the live gallery gets an instant update carrying ONLY the public kinds (open_to), nothing private; works unchanged',
  JSON.stringify(fcSnap.artist.open_to) === '["exhibitions","living_gallery","art_for_hire","commissions"]' && !SECRET.test(JSON.stringify(fcSnap))
  && fcSnap.works.length === 2 && (await versions('afc')).length === fcVers + 1, JSON.stringify(fcSnap.artist));
r = await call('POST', '/api/admin/opportunities/confirm', FOUNDER, FC);
check('F6 a second confirmation is refused (already decided); the artist can still keep them private with one click',
  r.s === 409 && (await call('PUT', '/api/opportunities/visibility', 'fc-test@example.test', { show: false })).s === 200 && (await row('afc')).public_display === 0);
// the Review Desk control
await db.prepare("UPDATE artist_opportunities SET public_display=NULL, public_decided_at=NULL, public_notice=NULL WHERE artist_id='afc'").run();
await f.goto(S.url + '/admin/opportunities', { waitUntil: 'load' }); await f.waitForTimeout(900);
const box = f.locator('[data-fc="afc"]'), go = f.locator('[data-fcgo="afc"]');
const shownBefore = await box.count() === 1 && await go.isDisabled() && /I personally obtained Fay Confirm’s agreement to show these publicly: Exhibitions, Art Hosting, Art for Hire, Commissions/.test(await f.locator('#app').innerText());
const noneForDecided = await f.locator('[data-fc="afd"]').count() === 0 && await f.locator('[data-fc="aorla"]').count() === 0;
await box.check(); await go.click(); await f.waitForTimeout(900);
check('F7 Review Desk: only "not confirmed yet" answers offer it; the button stays disabled until the statement is ticked; one click shows them',
  shownBefore && noneForDecided && (await row('afc')).public_display === 1 && /agreement obtained by the founder/.test(await f.locator('#app').innerText()));
await shot(f, 'review-desk-founder-confirm-1280.png');
} catch (e) { console.error(e); results.push(false); }
finally { if (browser) await browser.close(); if (S) await S.mf.dispose(); if (P) await P.mf.dispose(); }
const fail = results.filter(x => !x).length;
console.log(`\nOPPORTUNITIES SHOWN PUBLICLY · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
