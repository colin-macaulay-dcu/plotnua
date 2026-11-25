// PROVE · PlotArt · Art for Hire filters: where, gallery and availability (Phase C, Track C, 25 Nov 2026). TEST ONLY.
// A private preview built from SYNTHETIC fixture artists (atlas-tools builders, temporary folder), the live check answered
// by the local relay (Miniflare, synthetic rows). Nothing here touches the real site, Cloudflare or any record.
//   node test/prove-hire-filters.mjs [--shots DIR]
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { relay, open, chromium } from './hire-page-harness.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const SHOTS = (() => { const i = process.argv.indexOf('--shots'); return i > 0 ? process.argv[i + 1] : null; })();
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
console.log('PROVE · PlotArt · Art for Hire filters');
const build = (dir, ...args) => execFileSync('python3', [HERE + 'test/make-hire-preview.py', dir, '--api', 'https://relay.test', '--fixture', ...args], { encoding: 'utf8' });
const P = { plain: '/tmp/afh-filters-plain', facets: '/tmp/afh-filters', open: '/tmp/afh-filters-open' };
build(P.plain); build(P.facets, '--facets'); build(P.open, '--facets', '--galleries-open');
const page = d => readFileSync(d + '/plotart/art-for-hire/index.html', 'utf8');

// B · what the builder writes
check('B1 every card still ships hidden, with only public facts as filter data (county, delivery counties, open galleries)',
  !/<li class="pa-hire-card"(?![^>]*\bhidden\b)[^>]*>/.test(page(P.facets)) && /data-hire-in="Dublin" data-hire-delivers="Kildare\|Wicklow"/.test(page(P.facets)) && !/PRIVATE|handling note|@artist/.test(page(P.facets)));
check('B2 while Spaces and Being are not open (today), no gallery choice is offered and cards carry Contemporary only',
  !/data-hire-filter="gallery"/.test(page(P.facets)) && !/data-hire-galleries="[^"]*(spaces|being)/.test(page(P.facets)));
check('B3 once they open, the gallery choice lists only galleries that have works', /<option value="spaces">Spaces<\/option><option value="being">Being<\/option>/.test(page(P.open)));
check('B4 the "Where" list holds only counties that some work is in or delivered to, grouped by province', (() => {
  const m = page(P.facets).match(/data-hire-filter="where">([\s\S]*?)<\/select>/); const v = m ? [...m[1].matchAll(/value="([A-Za-z]+)"/g)].map(x => x[1]) : [];
  return v.join() === 'Galway,Mayo,Dublin,Kildare,Wicklow,Cork'; })());
check('B5 without facets from the Studio (delivery not public, records not installed) the bar still works on the listed county alone',
  /data-hire-in="Galway"/.test(page(P.plain)) && !/data-hire-delivers/.test(page(P.plain)));
let bad = '';
try { execFileSync('python3', ['-c', `import json,sys; c=json.load(open('${P.facets}/fixture-catalogue.json')); c['items'][0]['facets']['delivers']=['Main Street 12']; json.dump(c,open('/tmp/afh-bad.json','w'))`]);
  execFileSync('python3', [HERE + '../../atlas-tools/plotart-hire-page.py', P.facets, '--catalogue', '/tmp/afh-bad.json', '--api', 'https://relay.test', '--preview'], { encoding: 'utf8', stdio: 'pipe' }); }
catch (e) { bad = String(e.stderr || e.message); }
check('B6 the builder refuses a catalogue whose facets carry anything but county names and galleries (writes nothing)', /facets must be public/.test(bad) && /data-hire-delivers="Kildare/.test(page(P.facets)), bad.slice(-300));

// L · in the browser, against the live check
const S = await relay({ port: 8897 });
await S.db.prepare("UPDATE artwork_hire SET availability = 'from', available_from = '2026-12-15' WHERE artwork_id = 'wfixb2'").run();
const browser = await chromium.launch();
let o = await open(browser, P.open, S, { viewport: { width: 1440, height: 1000 }, scale: SHOTS ? 2 : 1 });
const vis = () => o.page.$$eval('[data-hire-work]', cs => cs.filter(c => !c.hidden).map(c => c.dataset.hireWork));
const set = async (k, v) => { await o.page.selectOption(`[data-hire-filter="${k}"]`, v); await o.page.waitForTimeout(120); };
check('L1 with every work listed, the bar appears with all six works and its count', (await vis()).length === 6 && await o.page.isVisible('[data-hire-filters]') && /6 works/.test(await o.page.textContent('[data-hire-count]')));
if (SHOTS) await o.page.locator('#afh3-works').screenshot({ path: `${SHOTS}/H01-hire-filters-all-desktop.png` });
await set('where', 'Kildare');
check('L2 Where = Co. Kildare: no work is there, but Artist A delivers there: shown and labelled "Delivers to Co. Kildare"',
  (await vis()).join() === 'wfixa1,wfixa2' && (await o.page.textContent('[data-hire-work="wfixa1"] [data-hire-rel]')) === 'Delivers to Co. Kildare');
await set('where', 'Galway');
check('L3 Where = Co. Galway: Artist B’s works, labelled "In Co. Galway"', (await vis()).join() === 'wfixb1,wfixb2' && (await o.page.textContent('[data-hire-work="wfixb1"] [data-hire-rel]')) === 'In Co. Galway');
await set('where', 'Dublin');
const order = await o.page.$$eval('[data-hire-work]:not([hidden])', cs => cs.map(c => getComputedStyle(c).order));
check('L4 works in the county come before works delivered there (A is in Dublin: order unchanged)', order.every(x => x === '0'));
await set('where', 'Wicklow'); await set('gallery', 'spaces');
check('L5 filters combine: Wicklow (delivered) AND Spaces → only A1', (await vis()).join() === 'wfixa1');
await set('where', ''); await set('gallery', ''); await set('when', 'now');
check('L6 Available now leaves out B2, which is available from 15 December', !(await vis()).includes('wfixb2') && (await vis()).length === 5 && /5 of 6 works/.test(await o.page.textContent('[data-hire-count]')));
await set('when', ''); await set('where', 'Mayo'); await set('gallery', 'spaces');
check('L7 no match: a clear note and a "Show all works" button that resets the choices', (await vis()).length === 0 && await o.page.isVisible('[data-hire-nomatch]'));
if (SHOTS) await o.page.locator('#afh3-works').screenshot({ path: `${SHOTS}/H03-hire-filters-nomatch-desktop.png` });
await o.page.click('[data-hire-clear]'); await o.page.waitForTimeout(120);
check('L8 "Show all works" brings every listed work back', (await vis()).length === 6 && await o.page.isHidden('[data-hire-nomatch]'));
await set('where', 'Kildare');
if (SHOTS) await o.page.locator('#afh3-works').screenshot({ path: `${SHOTS}/H02-hire-filters-kildare-desktop.png` });
// fail closed: the live check stops answering → everything hidden, the bar too, whatever was chosen
o.page._hireFail = '503';
await o.page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await o.page.waitForTimeout(700);
check('L9 fails closed: when the live check fails, every card and the filter bar are hidden, whatever was chosen', (await vis()).length === 0 && await o.page.isHidden('[data-hire-filters]'));
o.page._hireFail = null;
await o.page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await o.page.waitForTimeout(700);
check('L10 when it answers again, the chosen filter still applies', (await vis()).join() === 'wfixa1,wfixa2');
// a work withdrawn from hire disappears even if it matches
await S.db.prepare("UPDATE artwork_hire SET offered = 0 WHERE artwork_id = 'wfixa2'").run();
await o.page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await o.page.waitForTimeout(700);
check('L11 filters never show a work the live check no longer lists', (await vis()).join() === 'wfixa1');
check('L12 no script errors', !o.errors.length, o.errors.join(' | '));
await o.ctx.close();
await S.db.prepare("UPDATE artwork_hire SET offered = 1 WHERE artwork_id = 'wfixa2'").run();

o = await open(browser, P.open, S, { viewport: { width: 390, height: 844 }, scale: SHOTS ? 2 : 1 });
const ov = await o.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
check('M1 phone (390 px): the three choices stack full width, no sideways scrolling', ov && await o.page.$eval('#hfl-where', e => e.getBoundingClientRect().width > 300));
if (SHOTS) { await set('where', 'Kildare'); await o.page.locator('#afh3-works').screenshot({ path: `${SHOTS}/H02-hire-filters-kildare-mobile.png` }); }
await o.ctx.close(); await browser.close(); await S.mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nART FOR HIRE · FILTERS · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
