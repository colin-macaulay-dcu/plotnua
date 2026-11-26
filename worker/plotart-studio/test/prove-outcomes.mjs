// PROVE · founder-only commercial outcomes (Commercial Conversion Sprint 1, 26 Nov 2026): aggregate, server-confirmed
// counts from existing records, counts and totals only. Local Miniflare D1, synthetic rows; nothing touches Cloudflare.
//   node test/prove-outcomes.mjs
import { readFileSync } from 'node:fs';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';
import { outcomes } from '../src/outcomes.js';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
console.log('PROVE · commercial outcomes (founder only, counts only)');

const { mf, url, db } = await start({ port: 8879 });
await seedPublished(db, { id: 'aout', slug: 'out-artist', email: 'out@example.test', name: 'Out Artist', works: 2, number: 1 });
const call = async (path, email) => {
  const h = { 'X-Studio': '1' }; if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { headers: h }); const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};

/* before the basket tables exist (migration 0019 not applied): basket figures are "not installed" (null), never an error */
const pre = await call('/api/admin/outcomes', FOUNDER);
check('O0 without the basket tables the report still answers; basket figures read "not installed" (null), enquiry figures are counts',
  pre.s === 200 && pre.j.checkout_started.all_time.live === null && pre.j.purchases.all_time.live_paid_baskets === null && pre.j.enquiries.all_time.from_gallery_pages === 0, pre.t.slice(0, 300));

for (const s of statements(readFileSync(HERE + 'migrations/0019_multi_artist_basket.sql', 'utf8'))) await db.prepare(s).run();
const now = Date.now(), ago = d => new Date(now - d * 864e5).toISOString();
const PII = ['Secret Buyer', 'secret.buyer@example.test', 'A very private message', '12 Private Road'];
// enquiries: 2 relay this week, 1 relay 20 days ago, 1 relay 90 days ago, 1 founder-logged email, 1 correction (not counted)
let n = 0;
const log = (route, at, corrects = null) => db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, logged_by, logged_at, corrects)
  VALUES (?, ?, 'aout', NULL, ?, ?, 1, 'relay', ?, ?)`).bind('el' + (++n), (route === 'email' ? 'PA-EM-' : 'PA-E-') + n, route, at, at, corrects).run();
await log('relay', ago(1)); await log('relay', ago(3)); await log('relay', ago(20)); await log('relay', ago(90)); await log('email', ago(2)); await log('relay', ago(1), 'el1');
await db.prepare(`INSERT INTO enquiries (id, reference, artist_id, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
  VALUES ('e1','PA-E-x1','aout',?,?,?,'PA-ENQ-2026-11',?,'sent',?), ('e2','PA-E-x2','aout','B','b@example.test','another message here','PA-ENQ-2026-11',?,'send_failed',?)`)
  .bind(PII[0], PII[1], PII[2], ago(1), ago(-300), ago(2), ago(-300)).run();
// checkout: live baskets 2 started (1 paid €1,250.00), test baskets 3 started (1 paid)
await db.prepare("INSERT INTO basket_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES ('PA-BBT-T','buyer_basket_terms','t',?, ?, ?)").bind('a'.repeat(64), ago(30), ago(30)).run();
let b = 0;
const basket = (live, status, cents, at) => db.prepare(`INSERT INTO checkout_baskets (id, reference, status, buyer_email, buyer_name, delivery_address, buyer_token_hash, terms_doc_id, terms_accepted_at,
  total_cents, line_count, expires_at, livemode, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'PA-BBT-T', ?, ?, 1, ?, ?, ?, ?)`)
  .bind('bk' + (++b), 'PA-B-' + b, status, PII[1], PII[0], JSON.stringify({ lines: [PII[3]] }), 'h' + b, at, cents, ago(-1), live, at, at).run();
await basket(1, 'paid', 125000, ago(2)); await basket(1, 'expired', 50000, ago(10)); await basket(0, 'paid', 900, ago(1)); await basket(0, 'open', 900, ago(1)); await basket(0, 'failed', 900, ago(40));

const r = await call('/api/admin/outcomes', FOUNDER), o = r.j;
check('O1 enquiries: relay counts by window (7 / 30 / all = 2 / 3 / 4), the founder-logged email separately (1), the correction not counted',
  r.s === 200 && o.enquiries.last_7_days.from_gallery_pages === 2 && o.enquiries.last_30_days.from_gallery_pages === 3 && o.enquiries.all_time.from_gallery_pages === 4 && o.enquiries.all_time.logged_by_email === 1, JSON.stringify(o.enquiries));
check('O2 relay email to artists: sent and failed counted from the retained enquiries', o.enquiry_delivery.sent === 1 && o.enquiry_delivery.send_failed === 1 && o.enquiry_delivery.received === 0, JSON.stringify(o.enquiry_delivery));
check('O3 checkout started: live and test kept apart (live 2, test 3 all time; test 2 in the last 30 days)',
  o.checkout_started.all_time.live === 2 && o.checkout_started.all_time.test === 3 && o.checkout_started.last_30_days.test === 2, JSON.stringify(o.checkout_started));
check('O4 purchases: live paid baskets 1 worth 125000 cents; test paid kept apart (1)',
  o.purchases.all_time.live_paid_baskets === 1 && o.purchases.all_time.live_paid_total_cents === 125000 && o.purchases.all_time.test_paid_baskets === 1, JSON.stringify(o.purchases));
check('O5 basket additions are reported as not measured on the server (never estimated)', /not measured/.test(o.basket_additions));
check('O6 the answer carries counts only: no buyer name, email, address or message from the records', !PII.some(x => r.t.includes(x)) && !/@/.test(r.t), r.t.slice(0, 200));
const art = await call('/api/admin/outcomes', 'out@example.test'), anon = await call('/api/admin/outcomes', null);
check('O7 only the founder: an artist is refused (403) and a request without sign-in is refused', art.s === 403 && anon.s !== 200, `${art.s} ${anon.s}`);
const direct = await outcomes({ DB: db }, new Date(now));
check('O8 the function and the route agree', JSON.stringify(direct.enquiries) === JSON.stringify(o.enquiries) && JSON.stringify(direct.purchases) === JSON.stringify(o.purchases));
const ui = readFileSync(HERE + 'ui/checkout-pilot.js', 'utf8');
check('O9 the founder’s Basket readiness page shows the outcomes section (no new tab)', /outcomesCard\(out\)/.test(ui) && /id="commercial-outcomes"/.test(ui));
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nCOMMERCIAL OUTCOMES · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
