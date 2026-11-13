// PROVE · Opportunities & delivery (migration 0009; development 13 Nov 2026).
// Local only: Miniflare D1/R2 and synthetic artists. Nothing here touches Cloudflare or any real record.
//   node test/prove-opportunities.mjs [--shots DIR]
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished, artistRows } from './seed.mjs';
import { chromium } from './hire-page-harness.mjs';
import * as R from '../src/opportunities-rules.js';

const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
if (SHOTS) mkdirSync(SHOTS, { recursive: true });
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 600)}]` : ''}`); };
const Hd = (e, studio = true) => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), ...(studio ? { 'X-Studio': '1' } : {}), 'Content-Type': 'application/json' });

let S, browser;
try {
console.log('PROVE · Opportunities & delivery');
S = await start({ port: 8871 });
const { db } = S;
const call = async (method, path, email, body, studio = true) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: Hd(email, studio), body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t }; };
const ORLA = 'orla-test@example.test', BEN = 'ben-test@example.test', CIA = 'cia-test@example.test', DES = 'des-test@example.test';
await seedPublished(db, { id: 'aorla', slug: 'orla-test', email: ORLA, name: 'Orla Test', works: 2, number: 1 });
await seedPublished(db, { id: 'aben', slug: 'ben-test', email: BEN, name: 'Ben Test', works: 2, number: 2 });
await seedPublished(db, { id: 'acia', slug: 'cia-test', email: CIA, name: 'Cia Test', works: 2, number: 3 });
await seedPublished(db, { id: 'ades', slug: 'des-test', email: DES, name: 'Des Test', works: 2, number: 4 });
await db.prepare("UPDATE artists SET county = 'Galway' WHERE id = 'aorla'").run();
await db.prepare("UPDATE artists SET county = 'Atlantis' WHERE id = 'acia'").run();   // unreliable profile data: never offered
const snap = async () => Object.fromEntries(await Promise.all(['aorla', 'aben', 'acia', 'ades'].map(async id => [id, JSON.stringify(await artistRows(db, id))])));
const other = async () => JSON.stringify(await Promise.all(['artwork_hire', 'hire_terms_acceptances', 'hire_use_permissions', 'agreement_acceptances', 'agreement_documents', 'mail_capture', 'gallery_positions']
  .map(async t => (await db.prepare(`SELECT * FROM ${t} ORDER BY rowid`).all()).results)));
const before = await snap(), beforeOther = await other();
const row = id => db.prepare('SELECT * FROM artist_opportunities WHERE artist_id = ?').bind(id).first();
const rows = async () => (await db.prepare('SELECT COUNT(*) AS n FROM artist_opportunities').first()).n;

console.log('— the rules');
const all = Object.values(R.PROVINCES).flat();
check('P1 the four provinces hold all 32 counties exactly once (Leinster 12, Munster 6, Connacht 5, Ulster 9)',
  all.length === 32 && new Set(all).size === 32 && all.every(c => R.COUNTIES.includes(c)) && R.COUNTIES.length === 32
  && R.PROVINCES.Leinster.length === 12 && R.PROVINCES.Munster.length === 6 && R.PROVINCES.Connacht.length === 5 && R.PROVINCES.Ulster.length === 9
  && ['Antrim', 'Armagh', 'Derry', 'Down', 'Fermanagh', 'Tyrone', 'Cavan', 'Donegal', 'Monaghan'].every(c => R.PROVINCES.Ulster.includes(c)));

console.log('— the artist side');
let r = await call('GET', '/api/opportunities', ORLA);
check('O1 before answering: nothing saved (saved: null), no row, and the county on her profile is offered as a starting point only',
  r.s === 200 && r.j.installed && r.j.saved === null && r.j.suggested_county === 'Galway' && await rows() === 0, JSON.stringify(r.j).slice(0, 300));
r = await call('GET', '/api/opportunities', CIA);
check('O2 a profile county that is not one of the 32 is never offered', r.j.suggested_county === null);

const full = { interests: ['living_gallery', 'art_for_hire', 'commissions'], artwork_county: 'Clare', transport: ['deliver', 'courier'],
  coverage: { mode: 'counties', counties: ['Clare', 'Limerick', ...R.PROVINCES.Connacht] }, note: '  Large canvases need a van; =SUM(A1) available from March.  ' };
const bad = [
  ['no choice at all', { ...full, interests: [] }],
  ['an unknown opportunity', { ...full, interests: ['living_gallery', 'free_money'] }],
  ['a repeated opportunity', { ...full, interests: ['commissions', 'commissions'] }],
  ['online only with another opportunity', { ...full, interests: ['online_only', 'commissions'], transport: [], coverage: null }],
  ['online only with transport', { interests: ['online_only'], transport: ['deliver'] }],
  ['online only with delivery coverage', { interests: ['online_only'], transport: [], coverage: { mode: 'anywhere', counties: [] } }],
  ['"It depends" with another transport choice', { ...full, transport: ['depends', 'deliver'] }],
  ['a courier together with needing help', { ...full, transport: ['courier', 'need_help'], coverage: null }],
  ['delivery coverage when the artist needs help with transport', { ...full, transport: ['need_help'] }],
  ['"selected counties" with no county', { ...full, coverage: { mode: 'counties', counties: [] } }],
  ['"anywhere" with counties as well', { ...full, coverage: { mode: 'anywhere', counties: ['Cork'] } }],
  ['an unknown delivery county', { ...full, coverage: { mode: 'counties', counties: ['Cork', 'Atlantis'] } }],
  ['an unknown artwork county', { ...full, artwork_county: 'Co. Dublin' }],
  ['a note over 280 characters', { ...full, note: 'x'.repeat(281) }],
  ['an unexpected field', { ...full, enrol: true }],
  ['interests that are not a list', { ...full, interests: 'commissions' }],
];
const refused = [];
for (const [n, b] of bad) { const x = await call('PUT', '/api/opportunities', ORLA, b); refused.push([n, x.s, x.j && x.j.error]); }
check('O3 every invalid answer is refused (400) with a plain-words reason, and nothing is stored',
  refused.every(([, s, e]) => s === 400 && typeof e === 'string' && e.length > 10 && !/undefined|null/.test(e)) && await rows() === 0, JSON.stringify(refused));
r = await call('PUT', '/api/opportunities', ORLA, full);
const o1 = await row('aorla');
check('O4 a valid save stores exactly what was chosen (fixed order, note tidied), with the artwork county separate from her profile county',
  r.s === 200 && o1 && JSON.parse(o1.interests).join() === 'living_gallery,art_for_hire,commissions' && o1.artwork_county === 'Clare'
  && JSON.parse(o1.transport).join() === 'deliver,courier' && o1.coverage_mode === 'counties'
  && JSON.parse(o1.coverage_counties).join() === 'Clare,Galway,Leitrim,Limerick,Mayo,Roscommon,Sligo' && o1.note === 'Large canvases need a van; =SUM(A1) available from March.'
  && (await db.prepare("SELECT county FROM artists WHERE id='aorla'").first()).county === 'Galway', JSON.stringify([r.j, o1]));
r = await call('GET', '/api/opportunities', ORLA);
check('O5 the artist sees her saved answers when she returns (and no longer a suggested county)', r.j.saved && r.j.saved.artwork_county === 'Clare' && r.j.suggested_county === null);
const au = await db.prepare("SELECT * FROM audit WHERE action LIKE 'opportunities_%' ORDER BY id").all();
check('O6 the save is audited with the options chosen, never the text of the note',
  au.results.length === 1 && au.results[0].action === 'opportunities_saved' && au.results[0].actor === ORLA && !/canvases|SUM/.test(au.results[0].detail) && /"note":true/.test(au.results[0].detail), JSON.stringify(au.results));
const created = o1.created_at;
await new Promise(res => setTimeout(res, 15));
r = await call('PUT', '/api/opportunities', ORLA, { interests: ['exhibitions', 'talks'], artwork_county: 'Clare', transport: ['need_help'], coverage: null, note: '' });
const o2 = await row('aorla');
check('O7 editing later replaces the answers, keeps when they were first given, and is audited as an update; clearing the note stores none',
  r.s === 200 && o2.created_at === created && o2.updated_at > created && JSON.parse(o2.transport).join() === 'need_help' && o2.coverage_mode === null && o2.note === null
  && (await db.prepare("SELECT COUNT(*) AS n FROM audit WHERE action = 'opportunities_updated'").first()).n === 1);
r = await call('PUT', '/api/opportunities', BEN, { interests: ['online_only'], artwork_county: 'Dublin', transport: [], coverage: null });
check('O8 "Online gallery only for now" is saved as its own explicit answer', r.s === 200 && JSON.parse((await row('aben')).interests).join() === 'online_only');
r = await call('PUT', '/api/opportunities', DES, { interests: ['mobile_gallery', 'venues'], artwork_county: null, transport: ['deliver'], coverage: { mode: 'anywhere', counties: [] }, note: null });
check('O9 the artwork county and the note may be left unanswered', r.s === 200 && (await row('ades')).artwork_county === null);

console.log('— the founder side');
r = await call('GET', '/api/admin/opportunities', FOUNDER);
const by = Object.fromEntries((r.j.items || []).map(i => [i.id, i]));
check('F1 the Review Desk lists every artist: unanswered (Cia) kept apart from "Online only for now" (Ben), with totals',
  r.s === 200 && r.j.items.length === 4 && by.acia.prefs === null && by.aben.prefs.interests[0] === 'online_only'
  && r.j.totals.answered === 3 && r.j.totals.unanswered === 1 && r.j.totals.online_only === 1 && r.j.totals.by_interest.mobile_gallery === 1 && r.j.totals.by_interest.living_gallery === 0, JSON.stringify(r.j.totals));
check('F2 the founder view covers "anywhere" for every county and counties only where chosen (filter rule)',
  R.covers(by.ades.prefs, 'Kerry') && !R.covers(by.aorla.prefs, 'Kerry') && !R.covers(by.aben.prefs, 'Dublin') && !R.covers(null, 'Cork'));

console.log('— access');
const acc = [
  ['an artist asking for the founder list', await call('GET', '/api/admin/opportunities', ORLA), 403],
  ['the founder trying to save as an artist', await call('PUT', '/api/opportunities', FOUNDER, full), 403],
  ['a save without the Studio header', await call('PUT', '/api/opportunities', ORLA, full, false), 403],
  ['no sign-in at all', await call('GET', '/api/opportunities', null), null],
  ['a stranger\'s address', await call('GET', '/api/opportunities', 'stranger@example.test'), null],
];
check('A1 artists cannot see the founder list; the founder cannot write an artist\'s answers; no header, no sign-in or an unknown address is refused',
  acc.every(([, x, want]) => want ? x.s === want : x.s >= 300 && !(x.j && x.j.saved)), JSON.stringify(acc.map(([n, x]) => [n, x.s])));
const benRow = JSON.stringify(await row('aben'));
await call('PUT', '/api/opportunities', ORLA, { interests: ['commissions'] });
check('A2 each artist reads and writes only their own answers', JSON.stringify(await row('aben')) === benRow && (await call('GET', '/api/opportunities', BEN)).j.saved.interests[0] === 'online_only');

console.log('— nothing else changes');
const after = await snap();
check('N1 saving answers changes no artist, artwork, image, version, publication, agreement, enquiry or gallery-order record (byte-identical)',
  Object.keys(before).every(k => before[k] === after[k]), Object.keys(before).filter(k => before[k] !== after[k]).join());
check('N2 no Art for Hire offer or acceptance, no image permission, no agreement document and no email was created', beforeOther === await other());

console.log('— the database itself');
const dbBad = [
  `INSERT INTO artist_opportunities (artist_id, interests, transport, created_at, updated_at, updated_by) VALUES ('acia', '["online_only","commissions"]', '[]', 'x', 'x', 'x')`,
  `INSERT INTO artist_opportunities (artist_id, interests, transport, created_at, updated_at, updated_by) VALUES ('acia', '["online_only"]', '["deliver"]', 'x', 'x', 'x')`,
  `INSERT INTO artist_opportunities (artist_id, interests, transport, coverage_mode, coverage_counties, created_at, updated_at, updated_by) VALUES ('acia', '["talks"]', '["deliver"]', 'counties', '[]', 'x', 'x', 'x')`,
  `INSERT INTO artist_opportunities (artist_id, interests, transport, coverage_mode, coverage_counties, created_at, updated_at, updated_by) VALUES ('acia', '["talks"]', '["deliver"]', NULL, '["Cork"]', 'x', 'x', 'x')`,
  `INSERT INTO artist_opportunities (artist_id, interests, transport, created_at, updated_at, updated_by) VALUES ('acia', '[]', '[]', 'x', 'x', 'x')`,
  `INSERT INTO artist_opportunities (artist_id, interests, transport, note, created_at, updated_at, updated_by) VALUES ('acia', '["talks"]', '[]', '${'y'.repeat(281)}', 'x', 'x', 'x')`,
];
const dbRes = [];
for (const q of dbBad) { try { await db.prepare(q).run(); dbRes.push('stored'); } catch { dbRes.push('refused'); } }
check('D1 the table itself refuses online-only mixed with anything, counties without "selected counties" (and the reverse), no interest and an over-long note',
  dbRes.every(x => x === 'refused') && !(await row('acia')), dbRes.join());

console.log('— leaving PlotArt');
r = await call('POST', '/api/admin/artists/ades/end', FOUNDER, { confirm_name: 'Des Test', source: 'artist_request', reason: 'Artist asked in Studio to leave' });
const er = await call('POST', '/api/admin/artists/ades/erase-originals', FOUNDER, { confirm: true, reason: 'The artist asked for earlier deletion' });
check('L1 the first-stage deletion (12 months after leaving, or sooner on request) removes the artist\'s answers too',
  r.s === 200 && er.s === 200 && er.j.opportunities === 1 && !(await row('ades')) && !!(await row('aorla')), JSON.stringify([r.j, er.j]));

console.log('— in the browser');
browser = await chromium.launch();
const page = async (who, vp = { width: 1280, height: 900 }) => {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: SHOTS ? 2 : 1, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(who) } });
  const p = await ctx.newPage(); p.errs = []; p.on('pageerror', e => p.errs.push(e.message)); p.ctx = ctx; return p;
};
const shot = async (p, f) => { if (!SHOTS) return; await p.evaluate(() => { scrollTo(0, 0); document.querySelectorAll('.st-opp-save, .st-top').forEach(n => { n.style.position = 'static'; }); }); await p.waitForTimeout(100);
  await p.screenshot({ path: join(SHOTS, f), fullPage: true }); await p.evaluate(() => document.querySelectorAll('.st-opp-save, .st-top').forEach(n => { n.style.position = ''; })); };
const pressed = p => p.$$eval('.st-opt[aria-pressed="true"]', bs => bs.map(b => b.dataset.k));
// Cia: never answered; her profile county is not a real county, so nothing is preselected.
let p = await page(CIA);
await p.goto(S.url + '/#/opportunities', { waitUntil: 'load' }); await p.waitForTimeout(700);
const t0 = await p.locator('#app').innerText();
check('U1 a first visit: nothing selected, "Not answered yet", no county chosen, the reassurance text shown, and the tab is in the Studio menu',
  (await pressed(p)).length === 0 && /Not answered yet/.test(t0) && await p.inputValue('#o-county') === '' && /does not commit you to anything/.test(t0)
  && await p.locator('.st-tabs a[href="#/opportunities"]').count() === 1 && p.errs.length === 0, t0.slice(0, 300) + p.errs.join());
await shot(p, 'artist-first-visit-1280.png');
await p.click('#o-save'); await p.waitForTimeout(200);
check('U2 saving with nothing chosen explains what is needed and stores nothing', /Choose at least one option/.test(await p.locator('#o-err').innerText()) && !(await row('acia')));
await p.click('[data-k="living_gallery"]'); await p.click('[data-k="mobile_gallery"]');
await p.click('[data-k="online_only"]');
const afterOnline = await pressed(p), hiddenTr = await p.locator('#o-tr-card').isHidden(), m1 = await p.locator('#o-i-msg').innerText();
await p.click('[data-k="commissions"]');
const afterOther = await pressed(p), m2 = await p.locator('#o-i-msg').innerText();
check('U3 "Online gallery only for now" clears the other choices (and hides transport); choosing another option unselects it, each explained on screen',
  afterOnline.join() === 'online_only' && hiddenTr && /cleared/.test(m1) && afterOther.join() === 'commissions' && /unselected/.test(m2), JSON.stringify([afterOnline, afterOther, m1, m2]));
check('U4 the delivery question appears only when the artist can deliver or arrange a courier',
  await p.locator('#o-cov-card').isHidden() && (await p.click('[data-k="need_help"]'), await p.locator('#o-cov-card').isHidden())
  && (await p.click('[data-k="deliver"]'), await p.locator('#o-cov-card').isVisible()));
await p.click('[data-k="courier"]');
const tr = (await pressed(p)).filter(k => Object.keys(R.TRANSPORT).includes(k));
check('U5 incompatible transport choices are resolved: choosing a courier unselects "need help", with a message', tr.join() === 'deliver,courier' && /unselected/.test(await p.locator('#o-t-msg').innerText()), tr.join());
await p.click('[data-prov="Ulster"]');
const ul = (await pressed(p)).filter(k => R.COUNTIES.includes(k));
check('U6 "Select all of Ulster" selects all nine Ulster counties and its button becomes "Clear Ulster"',
  ul.length === 9 && R.PROVINCES.Ulster.every(c => ul.includes(c)) && (await p.locator('[data-prov="Ulster"]').innerText()) === 'Clear Ulster');
await p.click('[data-k="anywhere"]');
const any = await pressed(p);
await p.click('[data-k="Cork"]');
const cork = await pressed(p);
check('U7 "Anywhere on the island" clears the counties; picking a county then unselects "Anywhere"',
  any.includes('anywhere') && !any.some(k => R.COUNTIES.includes(k)) && cork.includes('Cork') && !cork.includes('anywhere'), JSON.stringify([any, cork]));
await p.selectOption('#o-county', 'Kerry');
await p.fill('#o-note', 'Works up to 120 cm wide.');
await shot(p, 'artist-filled-1280.png');
await p.click('#o-save'); await p.waitForTimeout(500);
const saved = await row('acia'), t1 = await p.locator('#o-state').innerText();
check('U8 "Save preferences" stores the answers and shows "Saved" with the time',
  saved && JSON.parse(saved.interests).join() === 'commissions' && saved.artwork_county === 'Kerry' && saved.coverage_mode === 'counties' && JSON.parse(saved.coverage_counties).join() === 'Cork'
  && /Saved/.test(t1) && /Last saved/.test(t1), JSON.stringify(saved) + t1);
await p.reload({ waitUntil: 'load' }); await p.waitForTimeout(700);
check('U9 coming back later shows the saved answers ready to edit', (await pressed(p)).sort().join() === ['Cork', 'commissions', 'courier', 'deliver'].sort().join() && await p.inputValue('#o-county') === 'Kerry'
  && await p.inputValue('#o-note') === 'Works up to 120 cm wide.');
await p.click('[data-k="talks"]');
check('U10 a change after saving is flagged as unsaved', /unsaved changes/.test(await p.locator('#o-dirty').innerText()));
await p.ctx.close();
// Orla: first visit shows her profile county as a starting point, which she can change.
await db.prepare("DELETE FROM artist_opportunities WHERE artist_id = 'aorla'").run();
p = await page(ORLA, { width: 390, height: 844 });
await p.goto(S.url + '/#/opportunities', { waitUntil: 'load' }); await p.waitForTimeout(700);
check('U11 the county on the artist\'s profile is offered and labelled as changeable; on a phone nothing overflows sideways',
  await p.inputValue('#o-county') === 'Galway' && /Change it if your work is kept somewhere else/.test(await p.locator('#o-county-h').innerText())
  && await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth) && p.errs.length === 0);
await shot(p, 'artist-first-visit-390.png');
await p.click('[data-k="living_gallery"]'); await p.click('[data-k="art_for_hire"]'); await p.click('[data-k="deliver"]'); await p.click('[data-prov="Connacht"]'); await p.click('[data-k="Clare"]');
await shot(p, 'artist-filled-390.png');
await p.click('#o-save'); await p.waitForTimeout(500);
await shot(p, 'artist-saved-390.png');
check('U12 keyboard: every choice is a real button with its state announced (aria-pressed), and each question is a labelled group',
  await p.$$eval('.st-opt', bs => bs.every(b => b.tagName === 'BUTTON' && b.type === 'button' && ['true', 'false'].includes(b.getAttribute('aria-pressed'))))
  && await p.locator('fieldset legend').count() >= 3 && await p.locator('label[for="o-county"]').count() === 1 && await p.locator('label[for="o-note"]').count() === 1);
await p.ctx.close();

p = await page(FOUNDER);
await p.goto(S.url + '/admin/opportunities', { waitUntil: 'load' }); await p.waitForTimeout(800);
const ft = await p.locator('#app').innerText();
check('U13 the founder\'s Opportunities page shows the totals, "Not answered yet" and "Online only for now" as different states',
  /Not answered yet/.test(ft) && /Online only for now/.test(ft) && /expressions of interest only/.test(ft) && p.errs.length === 0, ft.slice(0, 500) + p.errs.join());
await shot(p, 'founder-1280.png');
await p.selectOption('#of-reach', 'Kerry');
const kerry = await p.locator('#of-list > li').count(), kn = await p.locator('#of-n').innerText();
await p.selectOption('#of-reach', ''); await p.click('[data-int="living_gallery"]');
const lg = await p.locator('#of-list').innerText();
await p.selectOption('#of-status', 'unanswered');
const un = await p.locator('#of-list').innerText();
check('U14 the founder filters: by delivery county, by opportunity (the count buttons) and by unanswered', /Showing/.test(kn) && lg.includes('Orla Test') && !lg.includes('Ben Test') && /No artists match/.test(un) === true, JSON.stringify([kerry, kn, lg.slice(0, 200), un.slice(0, 200)]));
await p.click('#of-reset'); await p.selectOption('#of-status', 'online');
await shot(p, 'founder-filter-online-1280.png');
await p.ctx.close();
p = await page(FOUNDER, { width: 390, height: 844 });
await p.goto(S.url + '/admin/opportunities', { waitUntil: 'load' }); await p.waitForTimeout(800);
check('U15 the founder page fits a phone', await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth) && p.errs.length === 0);
await shot(p, 'founder-390.png');
await p.ctx.close();

console.log('— the dashboard prompt and the founder view after saves and edits');
await db.prepare("DELETE FROM artist_opportunities WHERE artist_id = 'aben'").run();
p = await page(BEN);
await p.goto(S.url + '/#/', { waitUntil: 'load' }); await p.waitForTimeout(700);
const dash = await p.locator('#app').innerText(), mailsBefore = (await db.prepare('SELECT COUNT(*) AS n FROM mail_capture').first()).n;
check('U16 an artist who has not answered sees a discreet dashboard prompt below the gallery tasks, which blocks nothing',
  await p.locator('.st-opp-ask').count() === 1 && /Add your preferences/.test(dash) && /doesn’t commit you to anything/.test(dash)
  && await p.locator('.st-opp-ask').evaluate(n => !!n.previousElementSibling && n === n.parentElement.lastElementChild)
  && await p.locator('[data-act=add]').isEnabled() && await p.locator('.st-card').first().locator('.st-opp-ask').count() === 0 && p.errs.length === 0, dash.slice(-400));
await shot(p, 'artist-dashboard-prompt-1280.png');
await p.click('.st-opp-ask a'); await p.waitForTimeout(600);
check('U17 the prompt opens the Opportunities form', /#\/opportunities$/.test(p.url()) && await p.locator('#oform').count() === 1);
const mob = await p.locator('[data-k="mobile_gallery"]').innerText();
check('U18 the Mobile Gallery choice describes the existing service (home viewings through participating galleries)', mob === 'Mobile Gallery — home viewings through participating galleries', mob);
await p.click('[data-k="living_gallery"]'); await p.click('[data-k="deliver"]'); await p.click('[data-k="Dublin"]'); await p.click('#o-save'); await p.waitForTimeout(500);
let f = await page(FOUNDER);
await f.goto(S.url + '/admin/opportunities', { waitUntil: 'load' }); await f.waitForTimeout(800);
const benRow1 = await f.locator('#of-list > li', { hasText: 'Ben Test' }).innerText(), kp1 = await f.locator('.st-kpis').innerText();
await f.ctx.close();
await p.goto(S.url + '/#/', { waitUntil: 'load' }); await p.waitForTimeout(600);
const goneAfter = await p.locator('.st-opp-ask').count();
await p.goto(S.url + '/#/opportunities', { waitUntil: 'load' }); await p.waitForTimeout(600);
await p.click('[data-k="online_only"]'); await p.click('#o-save'); await p.waitForTimeout(500);
f = await page(FOUNDER);
await f.goto(S.url + '/admin/opportunities', { waitUntil: 'load' }); await f.waitForTimeout(800);
const benRow2 = await f.locator('#of-list > li', { hasText: 'Ben Test' }).innerText();
await f.selectOption('#of-status', 'online'); const onl = await f.locator('#of-list').innerText();
await f.selectOption('#of-status', 'unanswered'); const una = await f.locator('#of-list').innerText();
await f.selectOption('#of-status', ''); await f.selectOption('#of-reach', 'Dublin'); const dub = await f.locator('#of-list').innerText();
await f.ctx.close(); await p.ctx.close();
check('U19 once saved, the prompt is gone; the founder sees the saved answers (Living Gallery, delivers, Dublin)',
  goneAfter === 0 && /Living Gallery/.test(benRow1) && /Delivers · Dublin/.test(benRow1) && !/Not answered yet/.test(benRow1), JSON.stringify([goneAfter, benRow1, kp1]));
check('U20 after the artist edits to "Online gallery only for now", the founder sees Online only (not unanswered) and the old delivery answers are gone',
  /Online only for now/.test(benRow2) && !/Delivers/.test(benRow2) && onl.includes('Ben Test') && !una.includes('Ben Test') && !dub.includes('Ben Test')
  && (await db.prepare('SELECT COUNT(*) AS n FROM mail_capture').first()).n === mailsBefore, JSON.stringify([benRow2, onl.slice(0, 120), una.slice(0, 200)]));
const me = await call('GET', '/api/me', BEN);
check('U21 /api/me reports the artist\'s own state for the prompt only ("answered"), and nothing about other artists', me.j.opportunities === 'answered' && !('items' in me.j));

console.log('— before migration 0009 runs');
await db.prepare('DROP TABLE artist_opportunities').run();
const ni = [await call('GET', '/api/opportunities', BEN), await call('PUT', '/api/opportunities', BEN, { interests: ['talks'] }), await call('GET', '/api/admin/opportunities', FOUNDER), await call('GET', '/api/me', BEN)];
check('M1 without the new table the Studio carries on: the section says it is not available, saving is refused (409), the founder sees "not installed"',
  ni[0].j.installed === false && ni[1].s === 409 && ni[2].j.installed === false && ni[3].s === 200 && ni[3].j.opportunities === null, JSON.stringify(ni.map(x => x.s)));
} catch (e) { console.error(e); results.push(false); }
finally {
  if (browser) await browser.close();
  if (S) await S.mf.dispose();
}
const fail = results.filter(x => !x).length;
console.log(`\nOPPORTUNITIES · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
