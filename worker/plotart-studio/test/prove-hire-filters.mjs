// PROVE · Art for Hire filters (Phase C): county (based / delivers), gallery, availability; built by the real page builder
// into a temporary copy of the site and driven in a real browser with a stubbed live check. Real artists appear only with
// their real public counties; delivery coverage here is synthetic and exists only inside this test.
//   node test/prove-hire-filters.mjs [--shots DIR]
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, existsSync, readFileSync, cpSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, extname } from 'node:path';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const HERE = new URL('..', import.meta.url).pathname, ROOT = join(HERE, '../..');
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
console.log('PROVE · Art for Hire filters (Phase C)');
const tmp = mkdtempSync(join(tmpdir(), 'pa-afh-'));
for (const d of ['plotart', 'assets']) cpSync(join(ROOT, d), join(tmp, d), { recursive: true });
const it = (slug, id, extra = {}) => ({ artwork_id: id, artist_id: 'a-' + slug, artist_slug: slug, work_slug: 'x', hire: { availability: 'now', available_from: null, price: 'Price on request' }, ...extra });
const cat = { items: [
  it('olivia-jones', 'w4xytln2tm7'),                                                                   // based in Sligo
  it('daniel-chester', 'wychp9cm2em', { coverage: { counties: ['Sligo', 'Mayo'], line: 'Delivers to Co. Mayo, Co. Sligo' } }),   // Leitrim, delivers to Sligo (synthetic)
  it('carolyn-walsh', 'wh4ve2xmvb1', { coverage: { counties: ['Antrim', 'Carlow', 'Cavan', 'Clare', 'Cork', 'Derry', 'Donegal', 'Down', 'Dublin', 'Fermanagh', 'Galway', 'Kerry', 'Kildare', 'Kilkenny', 'Laois', 'Leitrim', 'Limerick', 'Longford', 'Louth', 'Mayo', 'Meath', 'Monaghan', 'Offaly', 'Roscommon', 'Sligo', 'Tipperary', 'Tyrone', 'Waterford', 'Westmeath', 'Wexford', 'Wicklow', 'Armagh'], line: 'Delivers anywhere on the island of Ireland' } }),   // Dublin, all-island (synthetic)
  it('paul-kerr', 'w7qm51rtg2y', { hire: { availability: 'from', available_from: '2027-03-01', price: 'Price on request' } }),   // Donegal, later
] };
const cf = join(tmp, 'catalogue.json'); writeFileSync(cf, JSON.stringify(cat));
const out = execFileSync('python3', ['-c', `import sys, json, importlib.util as u; sys.path.insert(0, ${JSON.stringify(join(ROOT, 'atlas-tools'))});
s = u.spec_from_file_location('h', ${JSON.stringify(join(ROOT, 'atlas-tools/plotart-hire-page.py'))}); m = u.module_from_spec(s); s.loader.exec_module(m)
print(m.build(${JSON.stringify(tmp)}, json.load(open(${JSON.stringify(cf)})), 'https://relay.example'))`], { encoding: 'utf8' }).trim();
const page = readFileSync(join(tmp, 'plotart/art-for-hire/index.html'), 'utf8');
check('B1 the real builder writes four cards and a filter bar (county, availability; no gallery choice while only Contemporary is open)',
  out === '4' && page.includes('data-hire-filter hidden') && page.includes('data-hire-f="county"') && page.includes('data-hire-f="avail"') && !page.includes('data-hire-f="gallery"'));
check('B2 each card carries only public data: home county, public coverage, galleries, availability (no address, no email)',
  /data-hire-work="w4xytln2tm7"[^>]*data-hire-county="Sligo"/.test(page) && /data-hire-work="wychp9cm2em"[^>]*data-hire-county="Leitrim" data-hire-covers="Sligo Mayo"/.test(page) && !/@|eircode/i.test(page.split('pa-hire-catalogue:begin')[1].split('pa-hire-catalogue:end')[0]));
let refused = ''; try { execFileSync('python3', ['-c', `import sys, json, importlib.util as u; sys.path.insert(0, ${JSON.stringify(join(ROOT, 'atlas-tools'))});
s = u.spec_from_file_location('h', ${JSON.stringify(join(ROOT, 'atlas-tools/plotart-hire-page.py'))}); m = u.module_from_spec(s); s.loader.exec_module(m)
m.build(${JSON.stringify(tmp)}, {"items": [dict(json.loads(${JSON.stringify(JSON.stringify(cat.items[0]))}), coverage={"counties": ["Atlantis"]})]}, 'https://relay.example')`], { encoding: 'utf8', stdio: 'pipe' }); } catch (e) { refused = String(e.stderr || e); }
check('B3 the builder refuses coverage that is not public counties', /coverage must be public counties/.test(refused));
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg' };
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: SHOTS ? 2 : 1 });
await ctx.route('https://plotnua.local/**', r => { let p = new URL(r.request().url()).pathname; if (p.endsWith('/')) p += 'index.html'; const f = join(tmp, decodeURIComponent(p)); existsSync(f) ? r.fulfill({ body: readFileSync(f), contentType: types[extname(f)] || 'application/octet-stream' }) : r.fulfill({ status: 404, body: '' }); });
await ctx.route('https://relay.example/v1/hire-listed', r => r.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, open: true, enquiries: false, valid_until: new Date(Date.now() + 600000).toISOString(),
  items: [{ id: 'w4xytln2tm7', availability: 'now' }, { id: 'wychp9cm2em', availability: 'now' }, { id: 'wh4ve2xmvb1', availability: 'now' }, { id: 'w7qm51rtg2y', availability: 'from', available_from: '2027-03-01' }] }) }));
const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', e => errs.push(e.message));
await pg.goto('https://plotnua.local/plotart/art-for-hire/', { waitUntil: 'networkidle' }); await pg.waitForTimeout(600);
const vis = () => pg.evaluate(() => [...document.querySelectorAll('[data-hire-work]')].filter(c => !c.hidden).map(c => [c.dataset.hireWork, c.querySelector('[data-hire-rel]').hidden ? '' : c.querySelector('[data-hire-rel]').textContent]));
check('F1 with the live check answering, the filter bar appears and all four works are shown', !(await pg.$eval('[data-hire-filter]', f => f.hidden)) && (await vis()).length === 4);
await pg.selectOption('[data-hire-f="county"]', 'Sligo'); await pg.waitForTimeout(100);
const s1 = await vis();
check('F2 Co. Sligo: the Sligo-based artist first ("Based in Co. Sligo"), then the Leitrim and Dublin artists who deliver there ("Delivers to Co. Sligo"); the Donegal artist (no coverage) is not shown',
  JSON.stringify(s1) === JSON.stringify([['w4xytln2tm7', 'Based in Co. Sligo'], ['wychp9cm2em', 'Delivers to Co. Sligo'], ['wh4ve2xmvb1', 'Delivers to Co. Sligo']]), JSON.stringify(s1));
if (SHOTS) { const el = await pg.$('#afh3-works'); await el.screenshot({ path: SHOTS + '/AFH-filter-sligo-desktop.png' }); }
await pg.selectOption('[data-hire-f="county"]', 'Kerry'); await pg.waitForTimeout(100);
check('F3 Co. Kerry: nobody is based there, but the all-island artist is still offered ("Delivers to Co. Kerry")', JSON.stringify(await vis()) === JSON.stringify([['wh4ve2xmvb1', 'Delivers to Co. Kerry']]));
await pg.selectOption('[data-hire-f="county"]', ''); await pg.selectOption('[data-hire-f="avail"]', 'from'); await pg.waitForTimeout(100);
check('F4 availability "later" shows only the work available from a future date; the county line is cleared', JSON.stringify(await vis()) === JSON.stringify([['w7qm51rtg2y', '']]));
await pg.selectOption('[data-hire-f="avail"]', ''); await pg.selectOption('[data-hire-f="county"]', 'Kerry'); await pg.selectOption('[data-hire-f="avail"]', 'from'); await pg.waitForTimeout(100);
check('F5 combined: Kerry and "later" match nothing, and the page says so plainly', (await vis()).length === 0 && /No works match/.test(await pg.$eval('[data-hire-count]', e => e.textContent)));
await ctx.unroute('https://relay.example/v1/hire-listed'); await ctx.route('https://relay.example/v1/hire-listed', r => r.fulfill({ status: 500, body: '{}' }));
await pg.selectOption('[data-hire-f="avail"]', ''); await pg.selectOption('[data-hire-f="county"]', '');
await pg.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await pg.waitForTimeout(800);
check('F6 fails closed: when the live check fails, every card and the filter bar are hidden again, whatever is chosen', (await vis()).length === 0 && await pg.$eval('[data-hire-filter]', f => f.hidden));
check('F7 no script errors', !errs.length, errs.join(' | '));
if (SHOTS) {
  const m = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await m.route('https://plotnua.local/**', r => { let p = new URL(r.request().url()).pathname; if (p.endsWith('/')) p += 'index.html'; const f = join(tmp, decodeURIComponent(p)); existsSync(f) ? r.fulfill({ body: readFileSync(f), contentType: types[extname(f)] || 'application/octet-stream' }) : r.fulfill({ status: 404, body: '' }); });
  await m.route('https://relay.example/v1/hire-listed', r => r.fulfill({ contentType: 'application/json', body: JSON.stringify({ ok: true, open: true, enquiries: false, valid_until: new Date(Date.now() + 600000).toISOString(), items: [{ id: 'w4xytln2tm7', availability: 'now' }, { id: 'wychp9cm2em', availability: 'now' }, { id: 'wh4ve2xmvb1', availability: 'now' }, { id: 'w7qm51rtg2y', availability: 'from', available_from: '2027-03-01' }] }) }));
  const mp = await m.newPage(); await mp.goto('https://plotnua.local/plotart/art-for-hire/', { waitUntil: 'networkidle' }); await mp.waitForTimeout(500);
  await mp.selectOption('[data-hire-f="county"]', 'Sligo'); await mp.waitForTimeout(200);
  const f = await mp.$('[data-hire-filter]'); await f.scrollIntoViewIfNeeded(); await mp.screenshot({ path: SHOTS + '/AFH-filter-sligo-mobile.png' });
  await m.close();
}
await b.close();
const fail = results.filter(x => !x).length;
console.log(`\nART FOR HIRE FILTERS · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
