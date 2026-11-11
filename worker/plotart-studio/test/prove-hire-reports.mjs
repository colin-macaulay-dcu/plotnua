// PROVE · Art for Hire hire reports (migration 0008; PA-AFH-2026-11 r5 clauses 6.2–6.6 and 10.1; development 11 Nov 2026).
// Local only: Miniflare D1/R2, synthetic artists, synthetic enquiry-log rows and a synthetic PA-AFH test text (the real text is
// not issued). Nothing here touches Cloudflare or any real record.
//   node test/prove-hire-reports.mjs [--shots DIR]
import { cpSync, readFileSync, writeFileSync, rmSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished, artistRows } from './seed.mjs';
import { chromium } from './hire-page-harness.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
if (SHOTS) mkdirSync(SHOTS, { recursive: true });
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const Hd = e => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
const sha = b => createHash('sha256').update(b).digest('hex');
const ago = days => new Date(Date.now() - days * 86400_000).toISOString();
const ymd = days => new Date(Date.now() + days * 86400_000).toISOString().slice(0, 10);

/* A test copy of the Studio carrying a SYNTHETIC PA-AFH text, as prove-hire.mjs does. */
const FIX = 'test/.hire-reports-fixture/';
rmSync(HERE + FIX, { recursive: true, force: true });
cpSync(HERE + 'src', HERE + FIX + 'src', { recursive: true });
const TXT = '<!DOCTYPE html><title>TEST ONLY · synthetic Art for Hire terms</title><p>Synthetic text for local tests. Not the PA-AFH terms.</p>';
const PDF = '%PDF-1.4 synthetic test document, not the PA-AFH terms';
const T = { title: 'PlotArt Art for Hire Artist Terms (TEST)', html: TXT, pdf_b64: Buffer.from(PDF).toString('base64'), html_sha256: sha(TXT), pdf_sha256: sha(PDF) };
const af = HERE + FIX + 'src/assets.js';
writeFileSync(af, readFileSync(af, 'utf8').replace('export const HIRE_TERMS = {};', `export const HIRE_TERMS = ${JSON.stringify({ 'PA-AFH-2026-11': T })};`));
const DOC = 'PA-AFH-2026-11';

let S, browser;
try {
console.log('PROVE · Art for Hire hire reports');
S = await start({ port: 8861, env: { HIRE_TERMS_ENABLED: 'true' }, script: FIX + 'src/index.js' });
const { db } = S;
const call = async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: Hd(email), body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* csv */ } return { s: r.status, j, t, h: r.headers }; };
const LEAH = 'leah-like@example.test', BEA = 'bea-other@example.test', CAL = 'cal-third@example.test';
// Leah: Founding Artist in her founding year. Bea: her founding year ended long ago. Cal: has never accepted PA-AFH.
await seedPublished(S.db, { id: 'aleah', slug: 'leah-like', email: LEAH, name: 'Leah Like', works: 3, number: 1, publishedAt: ago(20) });
await seedPublished(S.db, { id: 'abea', slug: 'bea-other', email: BEA, name: '=Bea Other', works: 3, number: 2, publishedAt: ago(800) });
await seedPublished(S.db, { id: 'acal', slug: 'cal-third', email: CAL, name: 'Cal Third', works: 2, number: 3, publishedAt: ago(800) });
for (const [id, n] of [['aleah', 'Leah Like'], ['abea', '=Bea Other'], ['acal', 'Cal Third']])
  await db.prepare(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, accepted_at, display_name, method, statement, created_at) VALUES (?, ?, ?, 'PA-GPIL-2026-10-29', ?, ?, 'migrated_from_artists_table', 'test', ?)`)
    .bind('acc' + id, 'ev' + id, id, ago(5), n, ago(5)).run();
await db.prepare('INSERT INTO hire_terms (doc_id, title, html_sha256, pdf_sha256, effective_at, created_at) VALUES (?, ?, ?, ?, ?, ?)').bind(DOC, T.title, T.html_sha256, T.pdf_sha256, '2018-01-01T00:00:00Z', ago(0)).run();
// The enquiry log, as the relay and the founder's "Log enquiry" write it: the founding flag is fixed at introduction (6.3).
const LOG = [
  ['l1', 'PA-H-261101-AAAAAA', 'aleah', 'waleah1', 'relay', ago(10), 1],   // Leah, founding year: protected
  ['l2', 'PA-H-250101-BBBBBB', 'abea', 'wabea1', 'relay', ago(60), 0],     // Bea, after her founding year: commission
  ['l3', 'PA-EM-250201-CCCCCC', 'abea', 'wabea2', 'email', ago(500), 0],    // Bea, email introduction 500 days ago: 12-month window passed
  ['l4', 'PA-E-250301-DDDDDD', 'abea', 'wabea3', 'relay', ago(30), 0],      // Bea, a PURCHASE enquiry: not a hire introduction
  ['l5', 'PA-H-250401-EEEEEE', 'acal', 'wacal1', 'relay', ago(30), 0],      // Cal: never accepted the terms
];
for (const [id, ref, a, w, route, at, f] of LOG)
  await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at) VALUES (?,?,?,?,?,?,?,?,?,?)`)
    .bind(id, ref, a, w, route, at, f, f ? ymd(345) : ymd(-400), route === 'relay' ? 'relay' : FOUNDER, at).run();
const before = { leah: await artistRows(db, 'aleah'), bea: await artistRows(db, 'abea'), docs: (await db.prepare('SELECT * FROM agreement_documents ORDER BY rowid').all()).results };
const count = async () => (await db.prepare('SELECT (SELECT COUNT(*) FROM hire_reports) + (SELECT COUNT(*) FROM hire_report_records) AS n').first()).n;

console.log('— the artist side');
let r = await call('GET', '/api/hire/reports', BEA);
const notYet = await call('POST', '/api/hire/reports', BEA, { reference: 'PA-H-250101-BBBBBB', artwork_ids: ['wabea1'], hire_start: ymd(-20), hire_end: ymd(-5), net_fee_cents: 45000, more_to_pay: false, payment_received: true });
check('R1 before accepting PA-AFH an artist sees no report form (accepted: false) and a report is refused (409); nothing written',
  r.s === 200 && r.j.installed === true && r.j.accepted === false && notYet.s === 409 && await count() === 0, JSON.stringify([r.j, notYet.j]));
for (const e of [LEAH, BEA]) await call('POST', '/api/hire/accept', e, { confirm: true, doc_id: DOC });
r = await call('GET', '/api/hire/reports', BEA);
const refsB = r.j.introductions.map(i => i.reference).sort(), lr = await call('GET', '/api/hire/reports', LEAH);
check('R2 an artist sees only their OWN hire introductions (relay PA-H- and logged email PA-EM-), never purchase enquiries or another artist\'s',
  JSON.stringify(refsB) === JSON.stringify(['PA-EM-250201-CCCCCC', 'PA-H-250101-BBBBBB']) && lr.j.introductions.length === 1 && lr.j.introductions[0].reference === 'PA-H-261101-AAAAAA', JSON.stringify([refsB, lr.j.introductions]));
check('R3 Founding Artist enquiries introduced in the founding year are marked protected; others are not, with their 12-month window shown',
  lr.j.introductions[0].protected === true && r.j.introductions.every(i => i.protected === false && /^\d{4}-\d{2}-\d{2}$/.test(i.window_ends)), JSON.stringify(r.j.introductions));
const good = { reference: 'PA-H-250101-BBBBBB', artwork_ids: ['wabea1'], hire_start: ymd(-20), hire_end: ymd(-5), net_fee_cents: 45000, more_to_pay: false, payment_received: true };
const bad = [
  ['another artist\'s reference', BEA, { ...good, reference: 'PA-H-261101-AAAAAA' }],
  ['a purchase enquiry', BEA, { ...good, reference: 'PA-E-250301-DDDDDD' }],
  ['an unknown reference', BEA, { ...good, reference: 'PA-H-999999-ZZZZZZ' }],
  ['another artist\'s artwork', BEA, { ...good, artwork_ids: ['waleah1'] }],
  ['no artwork', BEA, { ...good, artwork_ids: [] }],
  ['end before start', BEA, { ...good, hire_end: ymd(-30) }],
  ['an impossible date', BEA, { ...good, hire_start: '2026-02-30' }],
  ['a negative fee', BEA, { ...good, net_fee_cents: -1 }],
  ['a fee in euro with decimals', BEA, { ...good, net_fee_cents: 450.5 }],
  ['payment not confirmed', BEA, { ...good, payment_received: false }],
  ['an unknown field', BEA, { ...good, commission_cents: 0 }],
  ['an artist without the terms', CAL, { ...good, reference: 'PA-H-250401-EEEEEE', artwork_ids: ['wacal1'] }],
  ['no sign-in', null, good],
];
const out = [];
for (const [why, who, body] of bad) { const x = await call('POST', '/api/hire/reports', who, body); out.push([why, x.s]); }
check('R4 refused, with nothing written: ' + bad.map(b => b[0]).join('; '), out.every(([, s]) => s >= 400) && await count() === 0, JSON.stringify(out));

console.log('— commission only where the agreement allows it');
const rep = async (who, body) => (await call('POST', '/api/hire/reports', who, body)).j;
const lf = await rep(LEAH, { reference: 'PA-H-261101-AAAAAA', artwork_ids: ['waleah1'], hire_start: ymd(-3), hire_end: ymd(10), net_fee_cents: 80000, more_to_pay: false, payment_received: true });
const bc = await rep(BEA, good);
const bround = await rep(BEA, { ...good, net_fee_cents: 12345, more_to_pay: true });
const bwin = await rep(BEA, { ...good, reference: 'PA-EM-250201-CCCCCC', artwork_ids: ['wabea2'] });
const bzero = await rep(BEA, { ...good, net_fee_cents: 0 });
const row = id => db.prepare('SELECT r.*, c.invoice_status, c.payment_status FROM hire_reports r JOIN hire_report_records c ON c.report_id = r.id WHERE r.id = ?').bind(id).first();
const [L1, B1, B2, B3, B4] = await Promise.all([lf, bc, bround, bwin, bzero].map(x => row(x.report.id)));
check('R5 a hire from a founding-year introduction carries NO commission (clause 6.3), whatever the fee; its record says nothing is due',
  L1.basis === 'founding_year' && L1.commission_cents === 0 && L1.founding === 1 && L1.invoice_status === 'no_commission' && L1.payment_status === 'not_due', JSON.stringify(L1));
check('R6 a hire outside the founding year carries 10% of the net hire fee (€450.00 → €45.00), recorded as not yet invoiced and unpaid',
  B1.basis === 'commission' && B1.commission_cents === 4500 && B1.rate_bp === 1000 && B1.invoice_status === 'not_invoiced' && B1.payment_status === 'unpaid' && B1.terms_doc === DOC, JSON.stringify(B1));
check('R7 commission is rounded to the cent (€123.45 → €12.35) and an instalment is marked', B2.commission_cents === 1235 && B2.more_to_pay === 1, JSON.stringify(B2));
check('R8 a hire starting more than 12 months after the introduction carries no commission (6.2(c)); a hire with no fee carries none (6.4)',
  B3.basis === 'outside_window' && B3.commission_cents === 0 && B4.basis === 'no_fee' && B4.commission_cents === 0, JSON.stringify([B3, B4]));
const auditRep = (await db.prepare("SELECT detail FROM audit WHERE action = 'hire_reported'").all()).results.map(x => x.detail);
check('R9 every report is audited, with no fee or commission amounts in the audit trail', auditRep.length === 5 && auditRep.every(d => !/45000|4500|12345|80000|cents/.test(d)), auditRep.join(' | '));

console.log('— reports are kept as made');
const upd = await db.prepare('UPDATE hire_reports SET net_fee_cents = 1 WHERE id = ?').bind(B1.id).run().then(() => 'changed', e => 'refused');
const del = await db.prepare('DELETE FROM hire_reports WHERE id = ?').bind(B1.id).run().then(() => 'deleted', e => 'refused');
const delRec = await db.prepare('DELETE FROM hire_report_records WHERE report_id = ?').bind(B1.id).run().then(() => 'deleted', e => 'refused');
const forged = await db.prepare(`INSERT INTO hire_reports (id, artist_id, reference, artwork_ids, hire_start, hire_end, net_fee_cents, more_to_pay, introduced_at, founding, basis, rate_bp, commission_cents, terms_doc, reported_at, reported_by)
  VALUES ('hrx', 'aleah', 'PA-H-261101-AAAAAA', '["waleah1"]', '2026-11-01', '2026-11-02', 1000, 0, ?, 0, 'founding_year', 1000, 100, ?, ?, 'x')`).bind(ago(1), DOC, ago(0)).run().then(() => 'written', e => 'refused');
check('R10 the database refuses to change or delete a report or its record before retention ends, and refuses a report whose basis and amount disagree',
  upd === 'refused' && del === 'refused' && delRec === 'refused' && forged === 'refused', JSON.stringify([upd, del, delRec, forged]));
const corr = await call('POST', '/api/hire/reports', BEA, { ...good, net_fee_cents: 40000, corrects: B1.id });
const corr2 = await call('POST', '/api/hire/reports', BEA, { ...good, corrects: B1.id });
const corrX = await call('POST', '/api/hire/reports', LEAH, { reference: 'PA-H-261101-AAAAAA', artwork_ids: ['waleah1'], hire_start: ymd(-3), hire_end: ymd(10), net_fee_cents: 1, more_to_pay: false, payment_received: true, corrects: B2.id });
const B1after = await row(B1.id);
check('R11 a mistake is corrected by a new report that names the old one (kept unchanged); a second correction of the same report and correcting another artist\'s report are refused',
  corr.s === 200 && corr.j.report.commission_cents === 4000 && corr2.s === 409 && corrX.s === 400 && B1after.net_fee_cents === 45000, JSON.stringify([corr.j, corr2.j, corrX.j]));
r = await call('GET', '/api/hire/reports', BEA);
check('R12 the artist sees their own reports with the invoice and payment status, never another artist\'s and never the founder\'s private note',
  r.j.reports.length === 5 && r.j.reports.every(x => x.reference.startsWith('PA-') && !('note' in x)) && r.j.reports.some(x => x.corrected_by === corr.j.report.id), JSON.stringify(r.j.reports.map(x => x.reference)));

console.log('— the founder\'s records (manual)');
const art = [await call('GET', '/api/admin/hire/reports', BEA), await call('GET', '/api/admin/hire/reports.csv', BEA), await call('POST', `/api/admin/hire/reports/${B2.id}/record`, BEA, { payment_status: 'paid', paid_on: ymd(0) })];
check('R13 an artist cannot see the founder table, download the CSV or change a record (refused)', art.every(x => x.s === 403 || x.s === 404), JSON.stringify(art.map(x => x.s)));
let a = await call('GET', '/api/admin/hire/reports', FOUNDER);
const rB2 = a.j.reports.find(x => x.id === B2.id);
check('R14 the founder table lists every report with artist, enquiry reference, artwork, hire fee, commission, invoice and payment status',
  a.s === 200 && a.j.reports.length === 6 && rB2.artist === '=Bea Other' && rB2.reference === 'PA-H-250101-BBBBBB' && rB2.artworks[0] === 'Work 1' && rB2.net_fee_cents === 12345
  && rB2.commission_cents === 1235 && rB2.invoice_status === 'not_invoiced' && rB2.payment_status === 'unpaid', JSON.stringify(rB2));
const rec = async (id, body) => call('POST', `/api/admin/hire/reports/${id}/record`, FOUNDER, body);
const e1 = await rec(B2.id, { invoice_status: 'invoiced' }), e2 = await rec(B2.id, { payment_status: 'paid' }), e3 = await rec(L1.id, { invoice_status: 'invoiced', invoice_no: 'PN-001', invoiced_on: ymd(0) }),
  e4 = await rec(B2.id, { invoice_status: 'bogus' }), e5 = await rec(B2.id, { note: 'x'.repeat(281) }), e6 = await rec(B2.id, { amount: 1 });
check('R15 the record refuses an invoice without number and date, a payment without a date, invoicing a report with no commission due, unknown statuses or fields, and long notes',
  [e1, e2, e4, e5, e6].every(x => x.s === 400) && e3.s === 409, JSON.stringify([e1, e2, e3, e4, e5, e6].map(x => [x.s, x.j && x.j.error])));
const ok1 = await rec(B2.id, { invoice_status: 'invoiced', invoice_no: 'PN-2026-001', invoiced_on: ymd(-1), note: 'Sent by email' });
const ok2 = await rec(B2.id, { payment_status: 'paid', paid_on: ymd(0) });
const B2rec = await db.prepare('SELECT * FROM hire_report_records WHERE report_id = ?').bind(B2.id).first();
const auditRec = (await db.prepare("SELECT actor, detail FROM audit WHERE action = 'hire_record_updated'").all()).results;
check('R16 the founder records the invoice and payment by hand; each change is audited with who made it',
  ok1.s === 200 && ok2.s === 200 && B2rec.invoice_no === 'PN-2026-001' && B2rec.payment_status === 'paid' && B2rec.updated_by === FOUNDER && auditRec.length === 2 && auditRec.every(x => x.actor === FOUNDER), JSON.stringify([B2rec, auditRec]));
a = await call('GET', '/api/admin/hire/reports', FOUNDER);
check('R17 totals count only live commission (corrected reports excluded): reported €52.35, paid €12.35, not invoiced €40.00',
  a.j.totals.commission_cents === 5235 && a.j.totals.paid_cents === 1235 && a.j.totals.not_invoiced_cents === 4000 && a.j.totals.invoiced_unpaid_cents === 0, JSON.stringify(a.j.totals));
const csv = await call('GET', '/api/admin/hire/reports.csv', FOUNDER);
const lines = csv.t.trim().split('\r\n');
check('R18 the CSV downloads (text/csv, attachment, no-store) with one row per report and the agreed columns',
  csv.s === 200 && /text\/csv/.test(csv.h.get('Content-Type')) && /attachment; filename="plotart-hire-reports-/.test(csv.h.get('Content-Disposition')) && csv.h.get('Cache-Control') === 'no-store'
  && lines.length === 7 && lines[0].includes('"commission_eur"') && lines[0].includes('"invoice_status"') && lines[0].includes('"payment_status"') && lines.some(l => l.includes('"12.35"') && l.includes('"PN-2026-001"')), lines.slice(0, 2).join(' / '));
check('R19 the CSV makes formula-like cells literal (an artist name starting "=" is written as \'=…) and carries no hirer details or private notes',
  csv.t.includes('"\'=Bea Other"') && !/buyer|@example\.test|Sent by email/.test(csv.t), csv.t.slice(0, 300));
check('R20 the export is audited', (await db.prepare("SELECT COUNT(*) AS n FROM audit WHERE action = 'hire_reports_exported' AND actor = ?").bind(FOUNDER).first()).n === 1);

console.log('— nothing else changes');
const after = { leah: await artistRows(db, 'aleah'), bea: await artistRows(db, 'abea'), docs: (await db.prepare('SELECT * FROM agreement_documents ORDER BY rowid').all()).results };
check('R21 galleries, works, versions, agreements, enquiries and the enquiry log are unchanged by reporting and recording', JSON.stringify(after) === JSON.stringify(before));

console.log('— retention');
const H = await import(HERE + FIX + 'src/hire.js');
const tables = await H.recordTables({ DB: db });
check('R22 the six-year deletion clears hire_report_records, then hire_reports, before record_retention', tables.indexOf('hire_report_records') === 0 && tables.indexOf('hire_reports') === 1, JSON.stringify(tables));
const early = await db.prepare("DELETE FROM hire_reports WHERE artist_id = 'abea'").run().then(() => 'deleted', () => 'refused');
await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('abea', ?, ?, 'test', ?)").bind(ago(7 * 366), ago(1), ago(1)).run();
await db.prepare("DELETE FROM hire_report_records WHERE artist_id = 'abea'").run(); await db.prepare("DELETE FROM hire_reports WHERE artist_id = 'abea' AND corrects IS NOT NULL").run();
await db.prepare("DELETE FROM hire_reports WHERE artist_id = 'abea'").run();
check('R23 once the retention period has ended, the reports and records can be deleted (and only then)', early === 'refused' && (await db.prepare("SELECT COUNT(*) AS n FROM hire_reports WHERE artist_id = 'abea'").first()).n === 0
  && (await db.prepare("SELECT COUNT(*) AS n FROM hire_reports WHERE artist_id = 'aleah'").first()).n === 1);
check('R24 the commission rule itself: founding first, then the 12-month window, then no fee, else 10% rounded to the cent', [
  H.basisFor({ founding: 1, introduced_at: ago(1), hire_start: ymd(0), net_fee_cents: 99999 }).basis === 'founding_year',
  H.basisFor({ founding: 0, introduced_at: ago(400), hire_start: ymd(0), net_fee_cents: 1000 }).basis === 'outside_window',
  H.basisFor({ founding: 0, introduced_at: ago(300), hire_start: ymd(0), net_fee_cents: 1000 }).commission_cents === 100,
  H.basisFor({ founding: 0, introduced_at: ago(1), hire_start: ymd(0), net_fee_cents: 5 }).commission_cents === 1,
  H.basisFor({ founding: 0, introduced_at: ago(1), hire_start: ymd(0), net_fee_cents: 0 }).basis === 'no_fee'].every(Boolean));

console.log('— in the browser');
browser = await chromium.launch();
const page = async (who, vp = { width: 1280, height: 900 }) => {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: SHOTS ? 2 : 1, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(who) } });
  const p = await ctx.newPage(); p.errs = []; p.on('pageerror', e => p.errs.push(e.message)); p.ctx = ctx; return p;
};
const shot = async (p, f, sel) => { if (!SHOTS) return; if (sel) await p.locator(sel).screenshot({ path: join(SHOTS, f) }); else await p.screenshot({ path: join(SHOTS, f), fullPage: true }); };
// fresh rows for Bea so the artist page has something to show
await call('POST', '/api/hire/reports', BEA, { ...good, net_fee_cents: 60000 });
let p = await page(LEAH);
await p.goto(S.url + '/#/hire', { waitUntil: 'load' }); await p.waitForTimeout(800);
const lt = await p.locator('#hirereports').innerText();
check('U1 a Founding Artist sees "Report a hire", her enquiry marked "Founding year: no commission" and her report with no commission',
  /Report a hire/.test(lt) && /Founding year: no commission/.test(lt) && /No commission: founding year/.test(lt) && p.errs.length === 0, lt.slice(0, 600) + p.errs.join());
await shot(p, 'artist-report-founding-1280.png', '#hirereports');
await p.ctx.close();
p = await page(BEA);
await p.goto(S.url + '/#/hire', { waitUntil: 'load' }); await p.waitForTimeout(800);
await p.selectOption('#rp-ref', 'PA-H-250101-BBBBBB'); await p.fill('#rp-start', ymd(-10)); await p.fill('#rp-end', ymd(-2)); await p.fill('#rp-fee', '250.00');
const calc = await p.locator('#rp-calc').innerText(), disabled = await p.locator('#rp-go').isDisabled();
await p.check('#rp-paid'); await shot(p, 'artist-report-form-1280.png', '#hirereports');
await p.click('#rp-go'); await p.waitForTimeout(800);
const n = (await db.prepare("SELECT COUNT(*) AS n FROM hire_reports WHERE artist_id = 'abea' AND net_fee_cents = 25000 AND commission_cents = 2500").first()).n;
check('U2 the form previews 10% (€25.00 on €250.00), stays disabled until payment is confirmed, and submits a report', /€25\.00/.test(calc) && disabled && n === 1 && p.errs.length === 0, calc + p.errs.join());
await p.ctx.close();
const m = await page(BEA, { width: 390, height: 844 });
await m.goto(S.url + '/#/hire', { waitUntil: 'load' }); await m.waitForTimeout(800);
const ov = await m.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
await shot(m, 'artist-report-phone-390.png', '#hirereports');
check('U3 on a phone the report form and table fit the screen (tables scroll in their own box)', ov);
await m.ctx.close();
p = await page(FOUNDER);
await p.goto(S.url + '/admin/hire', { waitUntil: 'load' }); await p.waitForTimeout(900);
const ft = await p.locator('#hrep').innerText();
check('U4 the founder sees the hire reports table (artist, enquiry, artwork, fee, commission, invoice, payment) with totals and a CSV link',
  /Hire reports \(\d+\)/.test(ft) && /Bea Other/.test(ft) && /PA-H-250101-BBBBBB/.test(ft) && /Download CSV/.test(ft) && /Founding year: none/.test(ft) && p.errs.length === 0, ft.slice(0, 500) + p.errs.join());
await shot(p, 'founder-reports-1280.png', '#hrep');
const id = await p.locator('[data-edit]').first().getAttribute('data-edit');
await p.click(`[data-edit="${id}"]`); await shot(p, 'founder-record-edit-1280.png', '#hrep');
await p.ctx.close();

console.log('— before migration 0008 is installed');
await db.prepare('DROP TABLE hire_report_records').run(); await db.prepare('DROP TABLE hire_reports').run();
const g = await call('GET', '/api/hire/reports', BEA), po = await call('POST', '/api/hire/reports', BEA, good), ag = await call('GET', '/api/admin/hire/reports', FOUNDER), ac = await call('GET', '/api/admin/hire/reports.csv', FOUNDER),
  hv = await call('GET', '/api/hire', BEA), adm = await call('GET', '/api/admin/hire', FOUNDER);
check('R25 without migration 0008 the Studio carries on: no report form (installed: false), reports refused (409), founder table says not installed, the rest of Art for Hire works',
  g.s === 200 && g.j.installed === false && po.s === 409 && ag.j.installed === false && ac.s === 409 && hv.s === 200 && adm.s === 200, JSON.stringify([g.j, po.s, ag.j, ac.s, hv.s, adm.s]));
} finally {
  if (browser) await browser.close();
  if (S) await S.mf.dispose();
  rmSync(HERE + FIX, { recursive: true, force: true });
}
const pass = results.filter(Boolean).length;
console.log(`\nHIRE REPORTS · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
process.exit(pass === results.length ? 0 : 1);
