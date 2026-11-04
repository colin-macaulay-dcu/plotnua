// PROVE · The Borrowed Garden noticeboard (MVP, 4 Nov 2026). Local only: Miniflare + a local D1 + a local page build.
//   node test/prove-garden-board.mjs [--shots DIR]
// S  intake: switched off by default, origin, closed lists, no contact details or addresses in public text, private
//    e-mail and consent required, honeypot and timing, unknown keys refused, nothing but 'received' ever inserted
// M  founder moderation in PlotArt Studio: approve, reject, remove, expire, tidy, delete; wrong transitions refused;
//    founder only
// P  the pipeline: token required; approved and unexpired only; public fields only (no e-mail, id, moderation detail
//    or monetisation field); newest first by date
// X  expiry: a listing past its date leaves the board on the next sweep
// F  monetisation fields exist, default free / individual / unfeatured, and nothing can set them
// R  the enquiry relay: OFF by default (503); when switched on in a local test only, it relays to the private address
//    with Reply-To and stores no message or address
// B  the page builder: only public fields, re-checked; refuses an e-mail, a phone number, an extra field or a tier
// W  a real browser: post a listing through the page form, approve it in Studio, publish, filter by side and county
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const REPO = fileURLToPath(new URL('../../..', import.meta.url));
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
let fails = 0;
const check = (name, ok, extra = '') => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : '  ' + extra}`); if (!ok) fails++; };

const SITE = process.env.GB_SITE_ORIGIN || 'https://plotnua.ie';
const { mf, url } = await start({ port: 8790, garden: { ORIGIN: SITE }, enquiry: { ORIGIN: SITE, GARDEN_ENQUIRIES_ENABLED: 'false' } });
const db = await mf.getD1Database('DB', 'studio');
let ipn = 0;
const df = (...a) => mf.dispatchFetch(...a);
const post = async (body, { origin = SITE, type = 'application/json', ip } = {}) => {
  const headers = { 'CF-Connecting-IP': ip || '10.1.0.' + (++ipn), 'Content-Type': type };
  if (origin) headers.Origin = origin;
  const r = await df('http://garden.local/v1/garden-listings', { method: 'POST', headers, body: type === 'application/json' ? JSON.stringify(body) : new URLSearchParams(body).toString() });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const old = () => String(Date.now() - 10_000);
const L = (o = {}) => ({ kind: 'have', county: 'Dublin', area: 'Raheny', space_type: 'raised_beds', availability: 'this_season',
  description: 'Two raised beds at the end of a quiet back garden, with side access and an outside tap.', email: 'owner@example.invalid', consent: true, t: old(), ...o });
const count = async (w = '') => (await db.prepare('SELECT COUNT(*) n FROM garden_listings ' + w).first()).n;
const call = async (method, path, email, body) => {
  const r = await df(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body) });
  return { s: r.status, j: await r.json().catch(() => ({})) };
};
const pipe = async (auth = 'Bearer ' + PIPELINE_TOKEN) => { const r = await df(url + '/api/pipeline/garden', { headers: auth ? { Authorization: auth } : {} }); return { s: r.status, j: await r.json().catch(() => ({})) }; };

console.log('S · intake');
{
  // switched off: a separate instance without GARDEN_ENABLED
  const off = await start({ garden: { GARDEN_ENABLED: 'false' } });
  const r = await off.mf.dispatchFetch('http://garden.local/v1/garden-listings', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json' }, body: JSON.stringify(L()) });
  check('S1 switched off by default (GARDEN_ENABLED not "true") -> 503', r.status === 503);
  await off.mf.dispose();
  const toml = readFileSync(new URL('../wrangler.garden.toml', import.meta.url), 'utf8');
  check('S2 the deploy config ships closed', /^GARDEN_ENABLED = "false"$/m.test(toml));
}
check('S3 wrong origin refused', (await post(L(), { origin: 'https://evil.example' })).s === 403);
check('S4 no origin refused', (await post(L(), { origin: null })).s === 403);
for (const [name, o] of [['an e-mail address', { description: 'Lovely sunny corner, write to me at mary@example.com for details please.' }],
  ['a telephone number', { description: 'Lovely sunny corner with good soil, ring 087 123 4567 any evening.' }],
  ['a link', { description: 'Lovely sunny corner with good soil, see pictures at mygarden.ie today.' }],
  ['an Eircode', { description: 'Lovely sunny corner with good soil at D05 X2Y3, side gate access.' }],
  ['a house number and street', { description: 'Lovely sunny corner at 12 Kilbarrack Road with good soil and access.' }],
  ['markup', { description: 'Lovely sunny corner with good soil <b>and</b> side access available.' }],
  ['digits in the area', { area: '12 Main' }], ['a county not on the list', { county: 'Atlantis' }], ['a kind not on the list', { kind: 'sell' }],
  ['a type not on the list', { space_type: 'roof' }], ['too short a description', { description: 'Small bed.' }],
  ['no e-mail', { email: '' }], ['no consent', { consent: false }]]) {
  const r = await post(L(o));
  check(`S5 refused: ${name}`, r.s === 400 && r.j && !r.j.ok, `${r.s} ${r.t.slice(0, 80)}`);
}
check('S6 unknown keys refused (no name, phone or tier can be sent)', (await post(L({ name: 'Mary' }))).s === 400 && (await post(L({ listing_tier: 'premium' }))).s === 400 && (await post(L({ phone: '0871234567' }))).s === 400);
const before = await count();
const hp = await post(L({ website: 'x' })); const fast = await post(L({ t: String(Date.now()) }));
check('S7 honeypot and too-fast posts answered as accepted, never stored', hp.s === 200 && fast.s === 200 && (await count()) === before);
const ok1 = await post(L());
check('S8 a good listing is accepted with a reference', ok1.s === 200 && /^PN-G-\d{6}-[0-9A-F]{4}$/.test(ok1.j.reference));
const row = await db.prepare('SELECT * FROM garden_listings WHERE ref = ?').bind(ok1.j.reference).first();
check('S9 stored as received, e-mail private, free / individual / unfeatured', row.status === 'received' && row.contact_email === 'owner@example.invalid' && row.listing_tier === 'free' && row.account_type === 'individual' && row.featured_until === null && row.organisation_id === null && !row.published_at);
check('S10 no IP address or name column is stored', !Object.keys(row).some(k => /^(ip|ip_address|client_ip|name|first_name|surname|phone|telephone|address|eircode)$/.test(k)));
const form = await post({ ...L(), consent: '1', t: '' }, { type: 'application/x-www-form-urlencoded' });
check('S11 a plain HTML form works without JavaScript (thank-you page, no e-mail echoed)', form.s === 200 && /Thank you/.test(form.t) && !form.t.includes('owner@example.invalid'));
// two more listings for moderation and filtering
const ok2 = await post(L({ kind: 'want', county: 'Cork', area: 'Ballincollig', space_type: 'vegetable_patch', availability: 'now', description: 'Keen grower with my own tools looking for a small patch within cycling distance.', email: 'grower@example.invalid' }));
const ok3 = await post(L({ county: 'Dublin', area: 'Artane', space_type: 'lawn', availability: 'next_season', description: 'A sunny strip of lawn we barely use, happy for it to become beds next spring.', email: 'owner2@example.invalid' }));

console.log('M · moderation in PlotArt Studio');
const adm = await call('GET', '/api/admin/garden', FOUNDER);
check('M1 the founder sees the waiting listings, with the private e-mail', adm.s === 200 && adm.j.waiting.length >= 3 && adm.j.waiting.every(l => l.contact_email));
check('M2 not the founder: refused', (await call('GET', '/api/admin/garden', 'someone@example.invalid')).s >= 401);
const id = r => adm.j.waiting.find(l => l.ref === r).id;
const ap = await call('POST', `/api/admin/garden/${id(ok1.j.reference)}`, FOUNDER, { action: 'approve', public_text: 'Two raised beds at the end of a quiet back garden, with side access and an outside tap nearby.' });
const r1 = await db.prepare('SELECT * FROM garden_listings WHERE ref = ?').bind(ok1.j.reference).first();
check('M3 approve: on the board, tidied wording kept, expiry 90 days out', ap.s === 200 && r1.status === 'approved' && r1.edited === 1 && Math.round((Date.parse(r1.expires_at) - Date.parse(r1.published_at)) / 86400_000) === 90);
check('M4 approve refuses wording with contact details', (await call('POST', `/api/admin/garden/${id(ok3.j.reference)}`, FOUNDER, { action: 'approve', public_text: 'A sunny strip of lawn, call 087 123 4567 to see it any time.' })).s === 400);
await call('POST', `/api/admin/garden/${id(ok2.j.reference)}`, FOUNDER, { action: 'approve' });
await call('POST', `/api/admin/garden/${id(ok3.j.reference)}`, FOUNDER, { action: 'approve' });
const rej = await post(L({ area: 'Killester', description: 'A corner of a back garden, would suit someone who likes herbs and salads.' }));
const adm2 = await call('GET', '/api/admin/garden', FOUNDER);
const rid = adm2.j.waiting.find(l => l.ref === rej.j.reference).id;
check('M5 reject', (await call('POST', `/api/admin/garden/${rid}`, FOUNDER, { action: 'reject' })).s === 200 && (await db.prepare('SELECT status FROM garden_listings WHERE id=?').bind(rid).first()).status === 'rejected');
check('M6 a rejected listing cannot be approved', (await call('POST', `/api/admin/garden/${rid}`, FOUNDER, { action: 'approve' })).s === 409);
check('M7 delete now (a removal request)', (await call('POST', `/api/admin/garden/${rid}`, FOUNDER, { action: 'delete' })).s === 200 && !(await db.prepare('SELECT 1 FROM garden_listings WHERE id=?').bind(rid).first()));
const extra = await post(L({ area: 'Donnycarney', description: 'Half a vegetable patch, already dug, that we cannot keep up with ourselves.' }));
const eid = (await call('GET', '/api/admin/garden', FOUNDER)).j.waiting.find(l => l.ref === extra.j.reference).id;
await call('POST', `/api/admin/garden/${eid}`, FOUNDER, { action: 'approve' });
check('M8 remove from the board', (await call('POST', `/api/admin/garden/${eid}`, FOUNDER, { action: 'remove' })).s === 200 && (await db.prepare('SELECT status FROM garden_listings WHERE id=?').bind(eid).first()).status === 'removed');
check('M9 an approved listing must be removed before it can be deleted', (await call('POST', `/api/admin/garden/${id(ok1.j.reference)}`, FOUNDER, { action: 'delete' })).s === 409);

console.log('P · the pipeline');
check('P1 no token: refused', (await pipe(null)).s === 401 && (await pipe('Bearer wrong')).s === 401);
const p1 = await pipe();
const ls = p1.j.listings || [];
check('P2 approved listings only', ls.length === 3 && !ls.some(l => l.ref === extra.j.reference || l.ref === rej.j.reference));
const allowed = new Set(['ref', 'kind', 'county', 'area', 'space_type', 'availability', 'text', 'photo', 'posted', 'expires']);
check('P3 public fields only (no e-mail, id, status, moderation or monetisation field)', ls.every(l => Object.keys(l).every(k => allowed.has(k))) && !JSON.stringify(p1.j).includes('@'));
check('P4 the founder’s tidied wording is what is published', ls.find(l => l.ref === ok1.j.reference).text.endsWith('outside tap nearby.'));

console.log('X · expiry');
await db.prepare("UPDATE garden_listings SET expires_at = ? WHERE ref = ?").bind(new Date(Date.now() - 60_000).toISOString(), ok3.j.reference).run();
const p2 = await pipe();
check('X1 a listing past its expiry leaves the board on the next sweep', !p2.j.listings.some(l => l.ref === ok3.j.reference) && (await db.prepare('SELECT status FROM garden_listings WHERE ref=?').bind(ok3.j.reference).first()).status === 'expired');
await db.prepare("UPDATE garden_listings SET status='approved', removed_at=NULL, expires_at=? WHERE ref = ?").bind(new Date(Date.now() + 30 * 86400_000).toISOString(), ok3.j.reference).run();
const ex = await call('POST', `/api/admin/garden/${id(ok3.j.reference)}`, FOUNDER, { action: 'expire' });
check('X2 the founder can expire a listing now', ex.s === 200 && (await db.prepare('SELECT status FROM garden_listings WHERE ref=?').bind(ok3.j.reference).first()).status === 'expired');

console.log('F · monetisation fields (present, unused)');
const cols = (await db.prepare("SELECT name FROM pragma_table_info('garden_listings')").all()).results.map(r => r.name);
check('F1 account type, listing tier, featured-until, expiry and organisation fields exist', ['account_type', 'listing_tier', 'featured_until', 'expires_at', 'organisation_id'].every(c => cols.includes(c)));
check('F2 every listing is free, individual and unfeatured', (await count("WHERE listing_tier <> 'free' OR account_type <> 'individual' OR featured_until IS NOT NULL OR organisation_id IS NOT NULL")) === 0);
const src = ['src/garden.js', 'src/index.js', 'src/enquiry.js'].map(f => readFileSync(new URL('../' + f, import.meta.url), 'utf8')).join('\n');
check('F3 no code path sets a tier, a featured date or an organisation', !/SET[^;]*(listing_tier|featured_until|organisation_id|account_type)\s*=/i.test(src) && !/ORDER BY[^"'`]*(listing_tier|featured_until)/i.test(src));
let refused = false; try { await db.prepare("UPDATE garden_listings SET listing_tier='gold' WHERE ref=?").bind(ok1.j.reference).run(); } catch { refused = true; }
check('F4 the database refuses an unknown tier', refused);

console.log('R · the enquiry relay (prepared, switched off)');
const rq = await df('http://enquiry.local/v1/garden-enquiry', { method: 'POST', headers: { Origin: SITE, 'Content-Type': 'application/json' }, body: JSON.stringify({ ref: ok1.j.reference, email: 'reader@example.invalid', message: 'Hello, I would love to grow there.' }) });
check('R1 off: 503, nothing sent or stored', rq.status === 503 && (await db.prepare('SELECT COUNT(*) n FROM garden_enquiries').first()).n === 0 && (await db.prepare('SELECT COUNT(*) n FROM mail_capture').first()).n === 0);
const etoml = readFileSync(new URL('../wrangler.enquiry.toml', import.meta.url), 'utf8');
check('R2 the deploy config ships it off', /^GARDEN_ENQUIRIES_ENABLED = "false"/m.test(etoml));
{
  const on = await start({ enquiry: { GARDEN_ENQUIRIES_ENABLED: 'true' } });
  const odb = await on.mf.getD1Database('DB', 'studio');
  await odb.prepare(`INSERT INTO garden_listings (id, ref, kind, county, area, space_type, availability, description, contact_email, consent_at, status, created_at, published_at, expires_at)
    VALUES ('g1','PN-G-261104-ABCD','have','Dublin','Raheny','raised_beds','now','Two raised beds at the end of a quiet back garden.','owner@example.invalid',?, 'approved', ?, ?, ?)`).bind(new Date().toISOString(), new Date().toISOString(), new Date().toISOString(), new Date(Date.now() + 86400_000).toISOString()).run();
  const r = await on.mf.dispatchFetch('http://enquiry.local/v1/garden-enquiry', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json' }, body: JSON.stringify({ ref: 'PN-G-261104-ABCD', email: 'reader@example.invalid', message: 'Hello, I would love to grow there.' }) });
  const mails = (await odb.prepare('SELECT * FROM mail_capture ORDER BY id').all()).results;
  const stored = await odb.prepare('SELECT * FROM garden_enquiries').first();
  check('R3 when switched on (local test only): relayed to the private address with Reply-To the sender', r.status === 200 && mails[0].to_addr === 'owner@example.invalid' && mails[0].reply_to === 'reader@example.invalid');
  check('R4 ... and stores only a reference, the listing and the time', stored && Object.keys(stored).sort().join() === 'created_at,id,listing_id,ref');
  await on.mf.dispose();
}

console.log('B · the page builder');
const tmp = mkdtempSync(join(tmpdir(), 'gb-'));
const build = (data, endpoint) => { const f = join(tmp, 'd.json'); writeFileSync(f, JSON.stringify(data));
  try { return { ok: true, out: execFileSync('python3', ['atlas-tools/build-garden-board.py', '--data', f, '--root', tmp, ...(endpoint ? ['--endpoint', endpoint] : [])], { cwd: REPO, encoding: 'utf8', stdio: 'pipe' }) }; }
  catch (e) { return { ok: false, out: String(e.stderr || e) }; } };
const live = (await pipe()).j;
const b1 = build(live);
const pageHtml = readFileSync(join(tmp, 'borrowed-garden-board.html'), 'utf8');
check('B1 builds from the pipeline snapshot', b1.ok, b1.out);
check('B2 the page carries no e-mail address, and is noindex', !/[^\s@"]+@[^\s@"]+\.[a-z]{2,}/i.test(pageHtml.replace(/hello@plotnua\.ie/g, '')) && /<meta name="robots" content="noindex, follow">/.test(pageHtml));
{ const ep = JSON.parse(readFileSync(new URL('../../../atlas-tools/garden-board/config.json', import.meta.url), 'utf8')).endpoint;
  check(ep ? 'B3 the form posts only to the configured intake address' : 'B3 with no intake address, the page shows no form',
    ep ? (pageHtml.match(/<form[^>]*action="([^"]*)"/g) || []).length === 1 && pageHtml.includes('action="' + ep + '"')
       : !/<form/.test(pageHtml) && /isn&rsquo;t taking listings yet/.test(pageHtml)); }
const bad = (mut) => { const d = JSON.parse(JSON.stringify(live)); mut(d.listings[0]); return build(d).ok; };
check('B4 refuses an e-mail in the text', !bad(l => { l.text = 'Lovely garden corner, contact me at me@example.com for a look.'; }));
check('B5 refuses a phone number in the text', !bad(l => { l.text = 'Lovely garden corner with good soil, ring 087 765 4321 please.'; }));
check('B6 refuses an extra field (e.g. a private e-mail or a tier)', !bad(l => { l.contact_email = 'x@y.ie'; }) && !bad(l => { l.listing_tier = 'premium'; }));
check('B7 refuses listings not ordered newest first', (() => { const d = JSON.parse(JSON.stringify(live)); d.listings[d.listings.length - 1].posted = '2026-01-01'; d.listings.reverse(); return !build(d).ok; })());

console.log('W · a real browser');
{
  const req = createRequire(join(REPO, 'package.json'));
  let chromium; try { ({ chromium } = req('playwright')); } catch { ({ chromium } = createRequire('/usr/lib/node_modules/')('playwright')); }
  const port = 8811;   // a static server on the repository root (started by the caller)
  const endpoint = `http://127.0.0.1:8790/v1/garden-listings`;
  const b2 = build((await pipe()).j, endpoint);
  // The page is built into the repository root's preview copy so its stylesheets resolve.
  const previewPath = join(REPO, '_preview-borrowed-garden-board.html');
  writeFileSync(previewPath, readFileSync(join(tmp, 'borrowed-garden-board.html'), 'utf8').replace('<main class="gb"', '<main class="gb"'));
  const browser = await chromium.launch();
  const p = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await p.goto(`http://localhost:${port}/_preview-borrowed-garden-board.html`, { waitUntil: 'networkidle' });
  check('W1 the page renders the approved listings, both sides distinct', b2.ok && (await p.locator('.gb-card.is-have').count()) >= 1 && (await p.locator('.gb-card.is-want').count()) >= 1);
  await p.click('.gb-seg [data-k="want"]');
  check('W2 filter: "I want space" shows growers only', await p.evaluate(() => [...document.querySelectorAll('.gb-card')].every(c => c.hidden === (c.dataset.kind !== 'want'))));
  await p.click('.gb-seg [data-k="all"]');
  await p.selectOption('#gbFCounty', 'Dublin');
  check('W3 filter by county: Dublin only', await p.evaluate(() => [...document.querySelectorAll('.gb-card')].every(c => c.hidden === (c.dataset.county !== 'Dublin'))));
  check('W4 the area list follows the county', await p.evaluate(() => !document.getElementById('gbFArea').disabled && [...document.getElementById('gbFArea').options].map(o => o.value).includes('Raheny')));
  await p.selectOption('#gbFArea', 'Raheny');
  check('W5 filter by area', await p.evaluate(() => [...document.querySelectorAll('.gb-card')].every(c => c.hidden === (c.dataset.area !== 'Raheny'))));
  if (SHOTS) { mkdirSync(SHOTS, { recursive: true }); await p.selectOption('#gbFCounty', ''); await p.evaluate(() => document.getElementById('gbFCounty').dispatchEvent(new Event('change'))); await p.screenshot({ path: join(SHOTS, '1-noticeboard-desktop.png'), fullPage: true }); }
  // post through the page form (the intake Worker in the harness, origin = this page)
  await p.waitForTimeout(3200);   // the page's minimum time on the page
  await p.check('input[name="kind"][value="want"]');
  await p.selectOption('#gbCounty', 'Galway'); await p.fill('#gbArea', 'Salthill');
  await p.selectOption('#gbType', 'flexible'); await p.selectOption('#gbWhen', 'flexible');
  await p.fill('#gbText', 'Retired teacher with time on my hands, looking for a little ground to grow salads and herbs.');
  await p.fill('#gbEmail', 'browser@example.invalid'); await p.check('input[name="consent"]');
  await p.click('.gb-btn');
  await p.waitForSelector('#gbResult:not([hidden])');
  const msg = await p.textContent('#gbResult');
  check('W6 posting through the page form works and returns a reference', /PN-G-\d{6}-[0-9A-F]{4}/.test(msg), msg);
  const ref = msg.match(/PN-G-\d{6}-[0-9A-F]{4}/)[0];
  check('W7 the new listing waits for the founder (not on the page)', (await db.prepare('SELECT status FROM garden_listings WHERE ref=?').bind(ref).first()).status === 'received' && !(await pipe()).j.listings.some(l => l.ref === ref));
  // Studio: the founder's Garden tab, then approve, publish and see it
  const sp = await browser.newPage({ viewport: { width: 1280, height: 1000 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  await sp.goto(url + '/admin/garden', { waitUntil: 'networkidle' });
  await sp.waitForSelector('[data-a="approve"]');
  check('W8 the Studio Garden tab shows the waiting listing with its private e-mail', (await sp.textContent('body')).includes(ref) && (await sp.textContent('body')).includes('browser@example.invalid'));
  if (SHOTS) await sp.screenshot({ path: join(SHOTS, '3-studio-garden-tab.png'), fullPage: true });
  await sp.locator(`li:has-text("${ref}") [data-a="approve"]`).click();
  await sp.waitForTimeout(600);
  check('W9 approved in the Studio', (await db.prepare('SELECT status FROM garden_listings WHERE ref=?').bind(ref).first()).status === 'approved');
  const b3 = build((await pipe()).j, endpoint);
  writeFileSync(previewPath, readFileSync(join(tmp, 'borrowed-garden-board.html'), 'utf8'));
  await p.goto(`http://localhost:${port}/_preview-borrowed-garden-board.html`, { waitUntil: 'networkidle' });
  check('W10 after publishing, the listing is on the page, without the e-mail', b3.ok && (await p.textContent('body')).includes(ref) && !(await p.content()).includes('browser@example.invalid'));
  if (SHOTS) {
    const m = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
    await m.goto(`http://localhost:${port}/_preview-borrowed-garden-board.html`, { waitUntil: 'networkidle' });
    await m.screenshot({ path: join(SHOTS, '2-noticeboard-phone.png'), fullPage: true });
    console.log('  page width on a phone: ' + await m.evaluate(() => document.documentElement.scrollWidth));
  }
  {
    const m = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await m.goto(`http://localhost:${port}/_preview-borrowed-garden-board.html`, { waitUntil: 'networkidle' });
    const cta = m.locator('.gb-cta');
    const box = await cta.boundingBox();
    check('W11 phone: "Post a listing — Free" is on the first screen', !!box && box.y + box.height <= 844 && /Post a listing/.test(await cta.textContent()) && /Free/.test(await cta.textContent()));
    await cta.click(); await m.waitForTimeout(600);
    const top = await m.evaluate(() => document.getElementById('post').getBoundingClientRect().top);
    check('W12 phone: the button takes you straight to the form', top >= 0 && top < 300, String(top));
    check('W13 phone: the status points are shown (free, reviewed, no contact yet, no arrangements)', await m.evaluate(() => { const t = document.querySelector('.gb-status').innerText; return /Free/.test(t) && /Reviewed/.test(t) && /contact/.test(t) && /arrange/.test(t); }));
    check('W14 phone: nothing scrolls sideways', (await m.evaluate(() => document.documentElement.scrollWidth)) === 390);
  }
  await browser.close();
  rmSync(previewPath, { force: true });   // never leave the preview page in the repository
}

console.log('U · publishing (the real publisher, --simulate, in a throw-away clone of this commit)');
{
  const clone = mkdtempSync(join(tmpdir(), 'gbpub-'));
  execFileSync('git', ['clone', '-q', '--no-hardlinks', REPO, clone]);
  execFileSync('git', ['-C', clone, 'checkout', '-q', execFileSync('git', ['-C', REPO, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim()]);
  const snapFile = join(clone, 'atlas-tools/garden-board/approved-listings.json');
  check('U1 the repository starts with no listings (no demonstration listing is ever committed)', JSON.parse(readFileSync(snapFile, 'utf8')).listings.length === 0);
  const publish = (mode = '--simulate', studio = url) => { try { return { ok: true, out: execFileSync('python3', ['atlas-tools/plotnua-garden-publish.py', '--studio', studio, '--token', PIPELINE_TOKEN, mode], { cwd: clone, encoding: 'utf8', stdio: 'pipe' }) }; }
    catch (e) { return { ok: false, out: String(e.stdout || '') + String(e.stderr || e) }; } };
  const shown = () => { const t = readFileSync(join(clone, 'borrowed-garden-board.html'), 'utf8'); return [...t.matchAll(/PN-G-\d{6}-[0-9A-F]{4}/g)].map(m => m[0]); };
  const push = publish('--push', url);
  check('U2 a local Studio (demonstration listings) can never be published (--push refused)', !push.ok && /never published/.test(push.out));
  const live = (await pipe()).j.listings.map(l => l.ref);
  const r1 = publish();
  check('U3 the publisher builds the page from the approved listings, through every guard', r1.ok && /verified \(simulated\)/.test(r1.out), r1.out.slice(-300));
  const s1 = shown();
  check('U4 approved listings appear on the page', live.length > 0 && live.every(r => s1.includes(r)));
  check('U5 rejected, removed and expired listings never appear', !s1.includes(rej.j.reference) && !s1.includes(extra.j.reference) && !s1.includes(ok3.j.reference));
  check('U6 the published page carries no e-mail address', !/@example\.invalid/.test(readFileSync(join(clone, 'borrowed-garden-board.html'), 'utf8')));
  // remove one, expire another, publish again
  const a2 = await call('GET', '/api/admin/garden', FOUNDER);
  const onBoard = a2.j.approved.map(l => l.ref);
  const [rm, xp] = onBoard;
  await call('POST', `/api/admin/garden/${a2.j.approved.find(l => l.ref === rm).id}`, FOUNDER, { action: 'remove' });
  if (xp) await db.prepare("UPDATE garden_listings SET expires_at = ? WHERE ref = ?").bind(new Date(Date.now() - 1000).toISOString(), xp).run();
  const r2 = publish();
  const s2 = shown();
  check('U7 after removal, the listing disappears from the published page', r2.ok && !s2.includes(rm), r2.out.slice(-200));
  check('U8 after expiry, the listing disappears from the published page', !xp || !s2.includes(xp));
  check('U9 publishing again with nothing new changes nothing', /nothing to publish/.test(publish().out));
  const commits = execFileSync('git', ['-C', clone, 'log', '--format=%s', '-3'], { encoding: 'utf8' });
  const files = execFileSync('git', ['-C', clone, 'diff', '--name-only', 'HEAD~2', 'HEAD'], { encoding: 'utf8' }).trim().split('\n').sort();
  check('U10 each publish commit changes only the snapshot and the page', /noticeboard content/.test(commits) && files.join() === 'atlas-tools/garden-board/approved-listings.json,borrowed-garden-board.html', files.join());
}

await mf.dispose();
console.log(fails ? `\nGARDEN NOTICEBOARD · FAIL (${fails})` : '\nGARDEN NOTICEBOARD · PASS');
process.exit(fails ? 1 : 0);
