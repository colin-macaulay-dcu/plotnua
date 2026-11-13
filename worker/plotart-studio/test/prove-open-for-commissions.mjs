// PROVE · Open for Commissions (migration 0011; founder approval 13 Nov 2026).
// Local only: Miniflare D1/R2, synthetic artists, captured mail. Nothing here touches Cloudflare or any real record.
//   node test/prove-open-for-commissions.mjs [--export-dir DIR]
//   --export-dir writes the pipeline exports (on / off) for the website proof (atlas-tools/prove-plotart-commissions.py).
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished, artistRows } from './seed.mjs';
import * as L from '../src/lib.js';

const OUT = process.argv.includes('--export-dir') ? process.argv[process.argv.indexOf('--export-dir') + 1] : null;
if (OUT) mkdirSync(OUT, { recursive: true });
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 600)}]` : ''}`); };
const Hd = (e, studio = true) => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), ...(studio ? { 'X-Studio': '1' } : {}), 'Content-Type': 'application/json' });
const HERE = new URL('..', import.meta.url).pathname;
const SCHEMA = readFileSync(HERE + 'schema.sql', 'utf8');
const NOTICE = readFileSync(HERE + 'src/enquiry.js', 'utf8').match(/const NOTICE = '([^']+)'/)[1];
const mk = S => async (method, path, email, body, studio = true) => {
  const r = await S.mf.dispatchFetch(S.url + path, { method, headers: Hd(email, studio), body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
};

let S, P;
try {
console.log('PROVE · Open for Commissions');

/* ---------------------------------------------------------------- before migration 0011 */
console.log('— before migration 0011 (production today)');
const before0011 = SCHEMA.replace(/\n-- PlotArt Studio · migration 0011[\s\S]*$/, '\n');
check('B0 the test schema without 0011 is production’s (no open_for_commissions column)', !/open_for_commissions/.test(before0011) && /open_for_commissions/.test(SCHEMA));
P = await start({ port: 8893, schemaSql: before0011 });
const pcall = mk(P);
await seedPublished(P.db, { id: 'apre', slug: 'pre-test', email: 'pre@example.test', name: 'Pre Test', works: 2, number: 1 });
let r = await pcall('GET', '/api/me', 'pre@example.test');
const pp = await pcall('PUT', '/api/me/commissions', 'pre@example.test', { open: true });
const prof = await pcall('PUT', '/api/me/profile', 'pre@example.test', { practice: 'Painter and printmaker' });
check('B1 before 0011 the Studio works as before: the switch is reported unavailable (not shown), turning it on is refused with 503, and profile saves still work',
  r.s === 200 && r.j.commissions_available === false && pp.s === 503 && prof.s === 200, JSON.stringify([r.j && r.j.commissions_available, pp.s, prof.s]));
await P.mf.dispose(); P = null;

/* ---------------------------------------------------------------- after migration 0011 */
console.log('— after migration 0011');
S = await start({ port: 8894, enquiry: {} });
const call = mk(S), { db } = S;
const ORLA = 'orla-test@example.test', BEN = 'ben-test@example.test', NEW = 'new-test@example.test';
await seedPublished(db, { id: 'aorla', slug: 'orla-test', email: ORLA, name: 'Orla Test', works: 2, number: 1 });
await seedPublished(db, { id: 'aben', slug: 'ben-test', email: BEN, name: 'Ben Test', works: 2, number: 2 });
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('anew','new-test',?,'New Test',0,'invited',?,?)`)
  .bind(NEW, new Date().toISOString(), new Date().toISOString()).run();
const flags = async () => (await db.prepare('SELECT id, open_for_commissions FROM artists ORDER BY id').all()).results;
check('S1 every existing artist starts OFF (0), Founding and future artists alike', (await flags()).every(x => x.open_for_commissions === 0), JSON.stringify(await flags()));
let refused = 'no';
try { await db.prepare("UPDATE artists SET open_for_commissions=2 WHERE id='aorla'").run(); } catch { refused = 'yes'; }
check('S2 the column accepts only 0 or 1', refused === 'yes');
const benBefore = JSON.stringify(await artistRows(db, 'aben'));
const versions = async id => (await db.prepare('SELECT * FROM versions WHERE artist_id=? ORDER BY version').bind(id).all()).results;
const queue = async id => (await db.prepare('SELECT * FROM publish_queue WHERE artist_id=? ORDER BY version').bind(id).all()).results;

r = await call('GET', '/api/me', ORLA);
check('S3 the Studio reports the switch available and off', r.j.commissions_available === true && r.j.artist.open_for_commissions === 0);
const studioJs = readFileSync(HERE + 'ui/studio.js', 'utf8');
check('S4 the checkbox has no name attribute (never swept into the profile autosave) and its own labelled hint',
  /<input type="checkbox" id="f-ofc"[^>]*aria-describedby="f-ofc-h"/.test(studioJs) && !/id="f-ofc"[^>]*\bname=/.test(studioJs) && /You agree any commission directly with them/.test(studioJs));

console.log('— who can switch it, and what is accepted');
const un = await S.mf.dispatchFetch(S.url + '/api/me/commissions', { method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-Studio': '1' }, body: '{"open":true}' });
const bads = [await call('PUT', '/api/me/commissions', ORLA, { open: 'yes' }), await call('PUT', '/api/me/commissions', ORLA, { open: 1 }),
  await call('PUT', '/api/me/commissions', ORLA, { open: true, artist_id: 'aben' }), await call('PUT', '/api/me/commissions', ORLA, {})];
check('S5 no sign-in is refused; only a true/false "open" is accepted (no other field, so an artist can switch only their own); nothing changed',
  [401, 403].includes(un.status) && bads.every(b => b.s === 400) && (await flags()).every(x => x.open_for_commissions === 0), JSON.stringify([un.status, ...bads.map(b => b.s)]));
const fnd = await call('PUT', '/api/me/commissions', FOUNDER, { open: true });
check('S6 the founder address has no artist profile to switch (refused)', fnd.s >= 400 && (await flags()).every(x => x.open_for_commissions === 0), fnd.s);

console.log('— switching on: one instant update, nothing else');
const v0 = await versions('aorla');
r = await call('PUT', '/api/me/commissions', ORLA, { open: true });
const v1 = await versions('aorla'), q1 = await queue('aorla');
const last = v1[v1.length - 1], lastSnap = JSON.parse(last.snapshot), prevSnap = JSON.parse(v0[v0.length - 1].snapshot);
const strip = s => JSON.stringify({ ...s, artist: { ...s.artist, open_for_commissions: undefined } });
check('S7 switching on saves 1, makes exactly one new version marked instant with ONLY the switch changed, and queues it for the founder’s one-click Publish',
  r.s === 200 && r.j.changed && r.j.instant_version === v0.length + 1 && v1.length === v0.length + 1 && last.source === 'instant'
  && lastSnap.artist.open_for_commissions === true && strip(lastSnap) === strip(prevSnap)
  && q1[q1.length - 1].kind === 'instant' && q1[q1.length - 1].status === 'awaiting_founder', JSON.stringify([r.j, last.source, q1.map(x => x.status)]));
const au = (await db.prepare("SELECT action, artist_id, actor FROM audit WHERE action LIKE 'commissions_%' ORDER BY id").all()).results;
check('S8 the change is audited with the artist’s own address', au.length === 1 && au[0].action === 'commissions_on' && au[0].actor === ORLA && au[0].artist_id === 'aorla');
r = await call('PUT', '/api/me/commissions', ORLA, { open: true });
check('S9 switching on again changes nothing (no version, no audit)', r.j.changed === false && (await versions('aorla')).length === v1.length
  && (await db.prepare("SELECT COUNT(*) n FROM audit WHERE action LIKE 'commissions_%'").first()).n === 1);
const st = (await call('GET', '/api/me', ORLA)).j.status;
check('S10 the switch never appears as a change waiting for review (instant tier)', !st.unsubmitted.some(c => /commission/i.test(c.what)), JSON.stringify(st.unsubmitted));
check('S11 the other artist’s records are untouched', JSON.stringify(await artistRows(db, 'aben')) === benBefore);

console.log('— publishing it');
const qid = q1[q1.length - 1].id;
let pub = await call('POST', `/api/admin/queue/${qid}/publish`, FOUNDER, {});
if (pub.j && pub.j.needs_confirmation) pub = await call('POST', `/api/admin/queue/${qid}/publish`, FOUNDER, { confirm_without_agreement: true });
const ex = await (await S.mf.dispatchFetch(S.url + `/api/pipeline/export/${qid}`, { method: 'POST', headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } })).json();
check('S12 after the founder’s Publish the gallery export carries open_for_commissions: true', pub.s === 200 && ex.ok && ex.gallery.artist.open_for_commissions === true, JSON.stringify([pub.s, ex.gallery && ex.gallery.artist]));
if (OUT) writeFileSync(OUT + '/export-on.json', JSON.stringify(ex.gallery, null, 2));
await S.mf.dispatchFetch(S.url + `/api/pipeline/result/${qid}`, { method: 'POST', headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN, 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'published', detail: 'test' }) });

console.log('— the enquiry relay');
const mails = async () => (await db.prepare('SELECT * FROM mail_capture ORDER BY id').all()).results;
const counts = async () => JSON.stringify(await Promise.all(['enquiries', 'enquiry_log', 'mail_capture'].map(async t => (await db.prepare(`SELECT COUNT(*) n FROM ${t}`).first()).n)));
let ipN = 0;   // each test enquiry from its own address, so the relay's burst limit (5 per address per 10 minutes) doesn't interfere
const enq = body => S.mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json', 'CF-Connecting-IP': `192.0.2.${++ipN}` }, body: JSON.stringify(body) });
const base = { notice: NOTICE, name: 'Cara Client', email: 'cara.client@example.test', message: 'Could you paint a large piece for our hallway?' };
let c0 = await counts();
const badKinds = [await enq({ ...base, ref: 'PA-orla-test', kind: 'hire' }), await enq({ ...base, ref: 'PA-orla-test', kind: '' }), await enq({ ...base, ref: 'PA-orla-test', kind: null }),
  await enq({ ...base, ref: 'PA-orla-test-waorla1', kind: 'commission' })];
check('R1 any kind but "commission" is refused, and a commission enquiry about a particular artwork is refused (400); nothing stored or sent',
  badKinds.every(x => x.status === 400) && await counts() === c0, JSON.stringify(badKinds.map(x => x.status)));
c0 = await counts();
const off = await enq({ ...base, ref: 'PA-ben-test', kind: 'commission' });
const offJ = await off.json();
check('R2 an artist whose published gallery is not open for commissions: 409 with a plain message; nothing stored, logged or sent',
  off.status === 409 && /isn’t taking commission enquiries/.test(offJ.error) && await counts() === c0, JSON.stringify([off.status, offJ]));
const m0 = (await mails()).length;
const on = await enq({ ...base, ref: 'PA-orla-test', kind: 'commission' }), onJ = await on.json();
const ms = (await mails()).slice(m0), toArtist = ms.find(m => m.to_addr === ORLA), toClient = ms.find(m => m.to_addr === base.email);
const logRow = await db.prepare('SELECT * FROM enquiry_log WHERE reference=?').bind(onJ.reference).first();
const enqRow = await db.prepare('SELECT * FROM enquiries WHERE reference=?').bind(onJ.reference).first();
check('R3 a commission enquiry to an artist who is open: accepted with the usual PA-E reference, relayed to the artist (Reply-To the client) and confirmed to the client',
  on.status === 200 && /^PA-E-\d{6}-[0-9A-F]{6}$/.test(onJ.reference) && toArtist && toArtist.reply_to === base.email && toClient, JSON.stringify([on.status, onJ, ms.map(m => m.subject)]));
check('R4 the artist’s email is clearly a commission enquiry about a NEW work, with the direct-agreement line',
  toArtist && toArtist.subject === `PlotArt commission enquiry · ${onJ.reference}` && /asked through your PlotArt gallery about commissioning a new work from you/.test(toArtist.body)
  && /Any commission for new work is agreed directly between you and the client\./.test(toArtist.body), toArtist && toArtist.body);
check('R5 a Founding Artist’s commission email never mentions the founding-year line or PlotArt taking commission',
  toArtist && !/founding year/i.test(toArtist.body) && !/PlotArt takes/.test(toArtist.body));
check('R6 the client’s confirmation names the commission', toClient && toClient.subject === `Your PlotArt commission enquiry · ${onJ.reference}` && /about a commission from Orla Test/.test(toClient.body), toClient && toClient.body);
check('R7 logged like any introduction (relay, Founding status), with no artwork and the note "commission enquiry"; no buyer details in the log',
  logRow && logRow.route === 'relay' && logRow.artwork_id === null && logRow.note === 'commission enquiry' && logRow.founding === 1 && !/Cara|cara\.client|hallway/.test(JSON.stringify(logRow))
  && enqRow && enqRow.artwork_id === null && enqRow.delete_after > new Date().toISOString(), JSON.stringify(logRow));
const auE = await db.prepare("SELECT detail FROM audit WHERE action='enquiry' ORDER BY id DESC LIMIT 1").first();
check('R8 the audit row says kind "commission" (no buyer details)', /"kind":"commission"/.test(auE.detail) && !/Cara|cara\.client/.test(auE.detail), auE.detail);

console.log('— ordinary enquiries are exactly as before');
const m1 = (await mails()).length;
const a1 = await enq({ ...base, ref: 'PA-orla-test-waorla1', message: 'Is Work 1 still available, please?' }), a1j = await a1.json();
const a2 = await enq({ ...base, ref: 'PA-ben-test', message: 'I love your work. Do you have anything smaller?' }), a2j = await a2.json();
const om = (await mails()).slice(m1);
const art1 = om.find(m => m.to_addr === ORLA), art2 = om.find(m => m.to_addr === BEN), cl1 = om.find(m => m.subject === `Your PlotArt enquiry · ${a1j.reference}`);
const expect1 = `Hello Orla,\n\nCara Client has sent an enquiry about “Work 1” through your PlotArt gallery.\n\n"Is Work 1 still available, please?"\n\nReply to this email to answer Cara Client directly (your reply goes to cara.client@example.test).\n\nReference: ${a1j.reference}\nArtwork: https://plotnua.ie/plotart/artists/orla-test/work-1.html\n\nPlotArt takes no commission on enquiries from your founding year. Any sale is agreed directly between you and the buyer.\n\nPlotArt · part of PlotNua`;
const expect2 = `Hello Ben,\n\nCara Client has sent an enquiry about your work through your PlotArt gallery.\n\n"I love your work. Do you have anything smaller?"\n\nReply to this email to answer Cara Client directly (your reply goes to cara.client@example.test).\n\nReference: ${a2j.reference}\n\nPlotArt takes no commission on enquiries from your founding year. Any sale is agreed directly between you and the buyer.\n\nPlotArt · part of PlotNua`;
check('O1 an artwork enquiry: subject and email to the artist exactly as today, word for word',
  a1.status === 200 && art1 && art1.subject === `PlotArt enquiry about Work 1 · ${a1j.reference}` && art1.body === expect1, art1 && art1.body);
check('O2 an enquiry about the artist’s work: exactly as today, word for word', a2.status === 200 && art2 && art2.subject === `PlotArt enquiry about your work · ${a2j.reference}` && art2.body === expect2, art2 && art2.body);
check('O3 the client confirmation is unchanged', cl1 && cl1.body.startsWith('Hello Cara Client,\n\nThank you. Your enquiry about “Work 1” has been passed to Orla Test'), cl1 && cl1.body);
const l1 = await db.prepare('SELECT note, artwork_id FROM enquiry_log WHERE reference=?').bind(a1j.reference).first();
const aud1 = await db.prepare("SELECT detail FROM audit WHERE action='enquiry' AND detail LIKE ? LIMIT 1").bind(`%${a1j.reference}%`).first();
check('O4 an ordinary enquiry’s log row and audit carry no note or kind, as before', l1.note === null && l1.artwork_id === 'waorla1' && !/kind/.test(aud1.detail));

console.log('— switching off');
r = await call('PUT', '/api/me/commissions', ORLA, { open: false });
const v2 = await versions('aorla'), q2 = await queue('aorla');
check('S13 switching off makes one instant version with the switch off, audited "commissions_off"', r.j.changed && v2[v2.length - 1].source === 'instant'
  && JSON.parse(v2[v2.length - 1].snapshot).artist.open_for_commissions === false && (await db.prepare("SELECT action FROM audit WHERE action LIKE 'commissions_%' ORDER BY id DESC LIMIT 1").first()).action === 'commissions_off');
c0 = await counts();
const stillLive = await enq({ ...base, ref: 'PA-orla-test', kind: 'commission' });
check('R9 until the founder publishes the switch-off, the live page (still on) keeps working', stillLive.status === 200);
const qid2 = q2[q2.length - 1].id;
let pub2 = await call('POST', `/api/admin/queue/${qid2}/publish`, FOUNDER, {});
if (pub2.j && pub2.j.needs_confirmation) pub2 = await call('POST', `/api/admin/queue/${qid2}/publish`, FOUNDER, { confirm_without_agreement: true });
const ex2 = await (await S.mf.dispatchFetch(S.url + `/api/pipeline/export/${qid2}`, { method: 'POST', headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } })).json();
check('S14 once published off, the export carries NO open_for_commissions key at all (exactly the shape exported today)',
  ex2.ok && !('open_for_commissions' in ex2.gallery.artist), JSON.stringify(ex2.gallery && Object.keys(ex2.gallery.artist)));
if (OUT) writeFileSync(OUT + '/export-off.json', JSON.stringify(ex2.gallery, null, 2));
await S.mf.dispatchFetch(S.url + `/api/pipeline/result/${qid2}`, { method: 'POST', headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN, 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'published', detail: 'test' }) });
c0 = await counts();
const stale = await enq({ ...base, ref: 'PA-orla-test', kind: 'commission' });
check('R10 a stale page (cached with the button) is refused once the switch-off is live; nothing stored or sent', stale.status === 409 && await counts() === c0);

console.log('— an artist not yet published');
r = await call('PUT', '/api/me/commissions', NEW, { open: true });
check('S15 a new (unpublished, non-Founding) artist can switch it on; it is saved and travels with their first publication (no instant version yet)',
  r.s === 200 && r.j.changed && r.j.instant_version === null && (await db.prepare("SELECT open_for_commissions o FROM artists WHERE id='anew'").first()).o === 1 && (await versions('anew')).length === 0);

console.log('— the rules, directly');
const oldSnap = { artist: { slug: 'x', display_name: 'X' }, works: [] };
const work = { artist: { slug: 'x', display_name: 'X', open_for_commissions: false }, works: [] };
check('U1 an older snapshot (no key) and a new one switched off are NOT a change', L.changes(oldSnap, work).length === 0, JSON.stringify(L.changes(oldSnap, work)));
check('U2 on → off and off → on are each one instant change', L.changes(oldSnap, { ...work, artist: { ...work.artist, open_for_commissions: true } }).map(c => c.tier).join() === 'instant');
check('U3 an unrelated instant change never rewrites an older snapshot with the new key', JSON.stringify(L.applyInstant(oldSnap, work)) === JSON.stringify(oldSnap));
check('U4 the export carries the key only when on', !('open_for_commissions' in L.exportGallery({ artist: { ...work.artist }, works: [] }, { version: 1 }).artist)
  && L.exportGallery({ artist: { ...work.artist, open_for_commissions: true }, works: [] }, { version: 1 }).artist.open_for_commissions === true);

console.log('— when an artist leaves');
await call('PUT', '/api/me/commissions', BEN, { open: true });
const end = await call('POST', '/api/admin/artists/aben/end', FOUNDER, { confirm_name: 'Ben Test', source: 'artist_request', reason: 'Artist asked by email to leave PlotArt' });
const ended = await enq({ ...base, ref: 'PA-ben-test', kind: 'commission' });
const erase = await call('POST', '/api/admin/artists/aben/erase-originals', FOUNDER, { confirm: true, reason: 'Artist asked by email for deletion' });
const benNow = await db.prepare("SELECT open_for_commissions o, account_status s FROM artists WHERE id='aben'").first();
check('S16 an ended artist receives no commission enquiries, and the switch is reset to off with their other profile details',
  end.s === 200 && ended.status === 404 && erase.s === 200 && benNow.o === 0 && benNow.s === 'ended', JSON.stringify([end.s, ended.status, erase.s, benNow]));

console.log(`\nOPEN FOR COMMISSIONS · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
} catch (e) { console.log('ERROR', e && e.stack || e); results.push(false); }
finally { if (P) await P.mf.dispose(); if (S) await S.mf.dispose(); }
process.exit(results.every(Boolean) ? 0 : 1);
