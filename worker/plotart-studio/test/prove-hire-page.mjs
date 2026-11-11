// PROVE · Art for Hire public page and navigation (Stage 3B-4, development 10 Nov 2026). Local only: a temporary preview
// copy of the PlotArt pages, synthetic FIXTURE artists with generated test images, and a Miniflare relay. Nothing here
// touches the repository's pages, the live site, Cloudflare or any record.
//   node test/prove-hire-page.mjs [SHOTS_DIR]
import { mkdtempSync, readFileSync, writeFileSync, rmSync, mkdirSync, cpSync } from 'node:fs';
import { execSync, execFileSync, spawnSync } from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import { buildPreview, relay, open, chromium } from './hire-page-harness.mjs';

const HERE = new URL('..', import.meta.url).pathname, REPO = path.resolve(HERE, '../..');
const SHOTS = process.argv[2] || null;
if (SHOTS) mkdirSync(SHOTS, { recursive: true });
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 600)}]` : ''}`); };
const TMP = mkdtempSync(path.join(os.tmpdir(), 'hire-page-'));
const P = { empty: path.join(TMP, 'empty'), fix: path.join(TMP, 'fix'), form: path.join(TMP, 'form') };
const AXE = readFileSync('/tmp/claude-0/studio-tools/node_modules/axe-core/axe.min.js', 'utf8');
const RIBBON = 'LOCAL TEST RENDER · synthetic fixture artists and generated test images · not real listings';
async function shot(page, name, { full = true, ribbon = false } = {}) {
  if (!SHOTS) return;
  await page.evaluate(async () => { document.querySelectorAll('img[loading=lazy]').forEach(i => { i.loading = 'eager'; });
    await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; }))); });
  await page.waitForTimeout(300);
  if (ribbon) await page.evaluate(([t, full]) => { const d = document.createElement('div'); d.textContent = t; d.style.cssText = (full ? 'position:absolute;top:0;' : 'position:fixed;bottom:0;') + 'left:0;right:0;z-index:9999;background:#5b2a17;color:#fff;font:600 12px/1.4 system-ui;letter-spacing:.06em;text-align:center;padding:6px'; document.body.appendChild(d); }, [RIBBON, full]);
  await page.screenshot({ path: path.join(SHOTS, name + '.png'), fullPage: full });
}
async function axe(page) {
  await page.addScriptTag({ content: AXE });
  // the whole page, shared footer included (its in-sentence link underline was fixed in Stage 3B-5)
  const r = await page.evaluate(async () => (await window.axe.run(document, { resultTypes: ['violations'] })).violations.map(v => ({ id: v.id, impact: v.impact, n: v.nodes.length, t: v.nodes[0] && v.nodes[0].target.join(' ') })));
  return r.filter(v => ['serious', 'critical'].includes(v.impact));
}
const visible = page => page.$$eval('[data-hire-work]', a => a.filter(x => !x.hidden && x.getBoundingClientRect().height > 0).map(x => x.dataset.hireWork));

try {
console.log('PROVE · Art for Hire page\n— building the private previews');
buildPreview(P.empty); buildPreview(P.fix, { fixture: true }); buildPreview(P.form, { fixture: true, form: true });

console.log('— existing pages and galleries unchanged');
const SHELL_DIFF = execFileSync('python3', ['-c', `
import importlib.util,subprocess,sys
sys.path.insert(0,'atlas-tools'); import plotart_shell as new
src=subprocess.check_output(['git','show','origin/main:atlas-tools/plotart_shell.py'],text=True)
old=importlib.util.module_from_spec(importlib.util.spec_from_loader('old',loader=None)); exec(src,old.__dict__)
ok=all(old.artist_page(p,'T','D','<p>b</p>')==new.artist_page(p,'T','D','<p>b</p>') for p in ['artists/a/index.html','artists/a/w.html','artists/a/b/c.html'])
print('same' if ok and new.HIRE_NAV is False else 'DIFF')`], { cwd: REPO, encoding: 'utf8' }).trim();
check('G2 artist gallery pages the pipeline writes are byte-identical (plotart_shell HIRE_NAV is off by default)', SHELL_DIFF === 'same', SHELL_DIFF);
const strip = s => s.replace(' pa-pills--hire', '').replace(/<a class="pa-pill" href="[^"]*art-for-hire\/"[^>]*>Art for Hire<\/a>/, '')
  .replace(/<a class="pn-sm-link" href="[^"]*art-for-hire\/"[^>]*>Art for Hire<\/a>/, '').replace(/<li><a href="[^"]*art-for-hire\/">Art for Hire<\/a><\/li>/, '');
/* G1 (11 Nov 2026: Art for Hire published). Against main, whatever main holds today, Art for Hire may change PlotArt only
   by: the tab on a page (nothing else on that page), the footer rule and the scoped nav block in plotart.css, and new
   files under plotart/art-for-hire/. No gallery, gallery.json, image or other page change. Nothing changed also passes. */
{
  const git = a => execSync('git ' + a, { cwd: REPO }).toString();
  const changedFiles = (git('diff origin/main --name-only -- plotart') + git('ls-files --others --exclude-standard -- plotart')).split('\n').filter(Boolean);
  const old = f => { try { return execSync(`git show origin/main:${f}`, { cwd: REPO, stdio: ['ignore', 'pipe', 'ignore'] }).toString(); } catch { return null; } };
  const cssBase = c => c.replace(/\n*\/\* ==== pa-hire-nav:begin[\s\S]*?pa-hire-nav:end ==== \*\/\n?/, '\n').replace(/^\.pa-foot p a\{ text-decoration:underline;[^\n]*\n/m, '').trimEnd();
  const wrong = changedFiles.filter(f => {
    if (f.startsWith('plotart/art-for-hire/')) return false;
    const o = old(f); if (o === null) return true;
    const n = readFileSync(path.join(REPO, f), 'utf8');
    // 11 Nov 2026: the gallery marks add one block to plotart.css and one self-contained block to plotart.js (nothing else in either)
    const marksCss = c => c.replace(/\n\/\* Art for Hire marks, added by plotart\.js[\s\S]*?\.pa-aw-hire\{[^\n]*\}/, '');
    const marksJs = c => c.replace(/\n\n\/\* ---- Art for Hire marks in an artist's gallery[\s\S]*$/, '\n');
    if (f === 'plotart/assets/plotart.css') return cssBase(marksCss(n)) !== cssBase(marksCss(o));
    if (f === 'plotart/assets/plotart.js') return marksJs(n) !== marksJs(o);
    return !f.endsWith('.html') || strip(n) !== strip(o);
  });
  check(`G1 against main, Art for Hire changes PlotArt only by the tab, the footer rule, the scoped nav block, the gallery-marks blocks in plotart.css and plotart.js, and its own folder (${changedFiles.length} file(s) differ); no gallery, gallery.json, image or other content changed`,
    wrong.length === 0, wrong.join(', '));
}
const pages = execSync('git ls-files plotart', { cwd: REPO }).toString().split('\n').filter(f => f.endsWith('.html') && !f.startsWith('plotart/art-for-hire/'));
let same = 0, withNav = 0, bad = [];
for (const f of pages) {
  const a = readFileSync(path.join(REPO, f), 'utf8'), b = readFileSync(path.join(P.fix, f), 'utf8');
  if (a.includes('class="pa-pills')) withNav++;
  if (strip(b) === strip(a)) same++; else bad.push(f);   // the published site may already carry the tab (11 Nov 2026)
}
check(`G3 in the preview, each of the ${pages.length} existing PlotArt pages differs from the original ONLY by the added tab (pill, Menu link, footer link): ${withNav} pages gain it`, bad.length === 0 && withNav >= 37 && pages.every(f => !readFileSync(path.join(REPO, f), 'utf8').includes('class="pa-pills') || readFileSync(path.join(P.fix, f), 'utf8').includes('nav_art_for_hire')), bad.join(', '));
const cssA = readFileSync(path.join(REPO, 'plotart/assets/plotart.css'), 'utf8'), cssB = readFileSync(path.join(P.fix, 'plotart/assets/plotart.css'), 'utf8');
check('G4 the shared stylesheet only gains one appended block, scoped to .pa-pills--hire', cssB.startsWith(cssA.trimEnd()) && /pa-hire-nav:begin/.test(cssB) && !/^(?!.*pa-pills--hire).*\{/m.test(cssB.slice(cssA.trimEnd().length).split('\n').filter(l => l.includes('{')).join('\n')));
const again = execFileSync('python3', [path.join(REPO, 'atlas-tools/plotart-hire-nav.py'), P.fix, '--preview'], { encoding: 'utf8' });
cpSync(path.join(REPO, 'plotart'), path.join(TMP, 'raw/plotart'), { recursive: true });
// a tab-free copy, as before publication (11 Nov 2026), so the tool's strictness is tested on pages it would patch
for (const f of pages) { const q = path.join(TMP, 'raw', f); writeFileSync(q, strip(readFileSync(q, 'utf8'))); }
rmSync(path.join(TMP, 'raw/plotart/art-for-hire'), { recursive: true, force: true });
const rawLg = path.join(TMP, 'raw/plotart/about.html'); writeFileSync(rawLg, readFileSync(rawLg, 'utf8').replace(/<a class="pa-pill" href="[^"]*living-gallery\.html"[^>]*>Living Gallery<\/a>/, ''));
const rawBefore = readFileSync(path.join(TMP, 'raw/plotart/index.html'), 'utf8');
const refuse2 = spawnSync('python3', [path.join(REPO, 'atlas-tools/plotart-hire-nav.py'), path.join(TMP, 'raw'), '--preview'], { encoding: 'utf8' });
check('G5 the navigation tool is idempotent (a second run changes nothing) and strict (an unexpected page stops it with nothing written)',
  /\d+ pages, 0 patched/.test(again) && refuse2.status === 2 && /REFUSED/.test(refuse2.stdout) && readFileSync(path.join(TMP, 'raw/plotart/index.html'), 'utf8') === rawBefore, again + refuse2.stdout);

const S = await relay({ port: 8891 }), browser = await chromium.launch();

console.log('— navigation: the fourth gallery tab');
const navGeom = page => page.$$eval('nav.pa-pills a.pa-pill', a => a.map(x => { const r = x.getBoundingClientRect(); return { t: x.textContent.trim(), x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height), r: Math.round(r.right), cur: x.getAttribute('aria-current') }; }));
const ORDER = 'Discover PlotArt,Artists’ Gallery,Mobile Gallery,Living Gallery,Art for Hire,PlotNua ↗';
let o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 900 } });
let g = await navGeom(o.page), vw = 1440;
const gaps = g.slice(1).map((p, i) => p.x - g[i].r);
check('N1 desktop (1440): six pills in order, Art for Hire after Living Gallery, current on this page; one row, equal heights, equal spacing, inside the header',
  g.map(p => p.t).join() === ORDER && g[4].cur === 'page' && new Set(g.map(p => p.y)).size === 1 && new Set(g.map(p => p.h)).size === 1 && Math.max(...gaps) - Math.min(...gaps) <= 1 && g[5].r <= vw, JSON.stringify(g));
await o.page.evaluate(() => window.scrollTo(0, 0)); if (SHOTS) await o.page.screenshot({ path: path.join(SHOTS, 'nav-1440.png'), clip: { x: 0, y: 0, width: 1440, height: 90 } });
await o.ctx.close();
const geo = {};
for (const w of [1280, 1181, 1180, 1024, 860, 800, 721]) {
  o = await open(browser, P.fix, S, { viewport: { width: w, height: 900 } });
  g = await navGeom(o.page); geo[w] = g;
  if (SHOTS && [1280, 1024, 800].includes(w)) await o.page.screenshot({ path: path.join(SHOTS, `nav-${w}.png`), clip: { x: 0, y: 0, width: w, height: w > 1180 ? 90 : 170 } });
  await o.ctx.close();
}
const rows = g => [...new Set(g.map(p => p.y))].length, widthsEven = g => { const byRow = {}; g.forEach(p => (byRow[p.y] ||= []).push(p.w)); return Object.values(byRow).every(r => Math.max(...r) - Math.min(...r) <= 1); };
const noOverflow = (g, w) => g.every(p => p.r <= w && p.x >= 0);
check('N2 1181–1280: still one aligned row that fits (the small “Part of PlotNua” tag gives way)', [1280, 1181].every(w => rows(geo[w]) === 1 && noOverflow(geo[w], w) && new Set(geo[w].map(p => p.h)).size === 1), JSON.stringify(geo[1181]));
check('N3 tablets 981–1180: one row of six equal pills', [1180, 1024].every(w => rows(geo[w]) === 1 && widthsEven(geo[w]) && noOverflow(geo[w], w)), JSON.stringify(geo[1024]));
check('N4 tablets 721–980: two rows of three equal pills, galleries on the second row aligned under the first', [860, 800, 721].every(w => rows(geo[w]) === 2 && widthsEven(geo[w]) && noOverflow(geo[w], w)
  && geo[w][0].x === geo[w][3].x && geo[w][2].r === geo[w][5].r), JSON.stringify(geo[800]));
o = await open(browser, P.fix, S, { device: 'iPhone 13' });
const pillsShown = await o.page.$eval('nav.pa-pills', n => getComputedStyle(n).display);
await o.page.click('.pn-sm-btn'); await o.page.waitForTimeout(300);
const menu = await o.page.$$eval('.pn-sm-panel a', a => a.map(x => [x.textContent.trim(), x.getAttribute('aria-current')]));
if (SHOTS) await o.page.screenshot({ path: path.join(SHOTS, 'nav-phone-menu.png') });
check('N5 phones: the pills give way to the shared Menu, which lists Art for Hire after Living Gallery (marked current here)', pillsShown === 'none' && menu.map(m => m[0]).join() === ORDER && menu[4][1] === 'page', JSON.stringify(menu));
await o.ctx.close();
const others = [['/plotart/living-gallery.html', 'Living Gallery'], ['/plotart/gallery/', 'Artists’ Gallery'], ['/plotart/mobile-gallery/', 'Mobile Gallery'], ['/plotart/artists/leah-hewson/', 'Artists’ Gallery'], ['/plotart/founding-25.html', null]];
const nav2 = [];
for (const [u, cur] of others) {
  o = await open(browser, P.fix, S, { url: u, viewport: { width: 1440, height: 900 } });
  g = await navGeom(o.page);
  if (SHOTS && u === '/plotart/living-gallery.html') await o.page.screenshot({ path: path.join(SHOTS, 'nav-on-living-gallery-1440.png'), clip: { x: 0, y: 0, width: 1440, height: 90 } });
  await o.page.click('nav.pa-pills a[data-pa-track="nav_art_for_hire"]'); await o.page.waitForLoadState();
  const h1 = await o.page.textContent('h1');
  nav2.push(g.map(p => p.t).join() === ORDER && (cur ? g.find(p => p.cur === 'page')?.t === cur : !g.some(p => p.cur)) && rows(g) === 1 && /Original art/.test(h1) && o.page.url().endsWith('/plotart/art-for-hire/'));
  await o.ctx.close();
}
check('N6 on the existing pages the tab sits in the same place, each page keeps its own current tab, and the link reaches the Art for Hire page', nav2.every(Boolean), nav2.join());

console.log('— the gallery and its cards');
{
  const foot = async u => { const x = await open(browser, P.fix, S, { url: u, viewport: { width: 1440, height: 900 } }); await x.page.addScriptTag({ content: AXE });
    const v = await x.page.evaluate(async () => (await window.axe.run({ include: [['.pa-foot']] }, { resultTypes: ['violations'] })).violations.map(v => v.id + ':' + v.impact)); await x.ctx.close(); return v.sort().join(); };
  const fa = await foot('/plotart/art-for-hire/'), fb = await foot('/plotart/living-gallery.html');
  check('A0 the shared PlotArt footer now passes accessibility checks, here and on an existing page (links in footer sentences are underlined)', fa === '' && fb === '', fa + ' vs ' + fb);
}
o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 1000 } });
let vis = await visible(o.page);
const cardsInfo = await o.page.$$eval('[data-hire-work]:not([hidden])', a => a.map(c => ({ artist: c.querySelector('.pa-hire-artist').textContent, title: c.querySelector('h3').textContent,
  dl: [...c.querySelectorAll('dt')].map(d => d.textContent + ':' + d.nextElementSibling.textContent), btn: c.querySelector('[data-hire-enquire]').textContent, alt: c.querySelector('img').alt })));
const html = readFileSync(path.join(P.fix, 'plotart/art-for-hire/index.html'), 'utf8');
check('C1 after the live check, all six listed works show: image, artist, title, medium, size, location, availability and an “Enquire about hire” button',
  vis.length === 6 && cardsInfo.every(c => c.artist && c.title && c.dl.length === 4 && /^Medium:.+/.test(c.dl[0]) && /^Size:.+cm$/.test(c.dl[1]) && /^Location:Co\. /.test(c.dl[2]) && c.dl[3] === 'Availability:Available for hire now' && /^Enquire about hire/.test(c.btn) && c.alt), JSON.stringify(cardsInfo[0]));
await o.page.evaluate(() => document.querySelectorAll('img[loading=lazy]').forEach(i => { i.loading = 'eager'; }));
await o.page.waitForTimeout(500);
const imgs = await o.page.$$eval('[data-hire-work] img', a => a.map(i => [i.complete && i.naturalWidth > 0, i.getAttribute('src')]));
check('C2 images come from each artist’s existing published image folder and load; uncropped (contained, natural proportions)', imgs.every(([ok, s]) => ok && /^\.\.\/artists\/fixture-artist-[abc]\/img\//.test(s))
  && await o.page.$eval('.pa-hire-art img', i => getComputedStyle(i).objectFit === 'contain'));
check('C3 the page carries no artist contact details, handling notes, price figures or Studio data', !/@artist|PRIVATE|handling|€|price_eur|mailto:(?!hello@plotnua\.ie)/i.test(html) && /Price on request/.test(html));
check('C4 every card is written HIDDEN in the HTML (shown only by a successful live check)', (html.match(/data-hire-work="[^"]+"[^>]*hidden>/g) || []).length === 6);
check('C5 the empty-state panel and status line stay hidden while works are shown; no script errors', await o.page.$eval('[data-hire-empty]', e => e.hidden) && await o.page.$eval('[data-hire-status]', e => e.hidden) && o.errors.length === 0, o.errors.join());
check('C6 while the live check is showing works, the hero action becomes “See works for hire” and leads to them (v3)', (await o.page.$eval('[data-hire-cta]', e => e.textContent + e.getAttribute('href'))) === 'See works for hire#afh3-works' && !!(await o.page.$('#afh3-works')));
let ax = await axe(o.page);
check('A1 accessibility (axe-core): no serious or critical issues on the desktop page', ax.length === 0, JSON.stringify(ax));
await shot(o.page, 'desktop-1440-test-render', { ribbon: true });
await o.ctx.close();
o = await open(browser, P.fix, S, { device: 'iPhone 13' });
vis = await visible(o.page);
const mob = await o.page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, cols: getComputedStyle(document.querySelector('.pa-hire-grid')).gridTemplateColumns.split(' ').length }));
ax = await axe(o.page);
check('R1 phone (iPhone 13): one column, no sideways scrolling, all six works, no serious accessibility issues', vis.length === 6 && mob.sw <= mob.cw && mob.cols === 1 && ax.length === 0, JSON.stringify(mob) + JSON.stringify(ax));
for (const [n, sel] of [['top', null], ['card', '[data-hire-work="wfixa1"]'], ['how', '#afh3-how']]) {
  await o.page.evaluate(q => q ? document.querySelector(q).scrollIntoView() : window.scrollTo(0, 0), sel); await o.page.waitForTimeout(300);
  await shot(o.page, `phone-390-${n}-test-render`, { full: false, ribbon: true });
}
await o.ctx.close();
o = await open(browser, P.fix, S, { viewport: { width: 900, height: 1000 } });
const tab = await o.page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, cols: getComputedStyle(document.querySelector('.pa-hire-grid')).gridTemplateColumns.split(' ').length }));
check('R2 tablet (900): two columns, no sideways scrolling', tab.cols === 2 && tab.sw <= tab.cw, JSON.stringify(tab));
await o.ctx.close();

console.log('— empty state (the real state today: no work is listed)');
o = await open(browser, P.empty, S, { viewport: { width: 1440, height: 1000 } });
const emp = await o.page.evaluate(() => ({ cards: document.querySelectorAll('[data-hire-work]').length, empty: !document.querySelector('[data-hire-empty]').hidden, h: document.querySelector('[data-hire-empty] strong').textContent,
  cta: [document.querySelector('[data-hire-cta]').textContent, document.querySelector('[data-hire-cta]').getAttribute('href'), !!document.querySelector('#afh3-how')],
  closed: document.querySelector('[data-hire-closed]').hidden }));
ax = await axe(o.page);
check('E1 with no listed works the page shows a polished empty state, no cards and no invented listings; no serious accessibility issues', emp.cards === 0 && emp.empty && /No works are available for hire just now/.test(emp.h) && emp.closed && ax.length === 0, JSON.stringify(emp) + JSON.stringify(ax));
check('E4 with no listed works the hero’s primary action is “How it works” and leads to that section (v3, 11 Nov 2026)', emp.cta[0] === 'How it works' && emp.cta[1] === '#afh3-how' && emp.cta[2], JSON.stringify(emp.cta));
const intro = await o.page.evaluate(() => ({ h1: document.querySelector('h1').textContent, lede: document.querySelector('.afh3-sub').textContent }));
check('I1 the approved headline “Original art, on hire.” is kept; the introduction speaks to creative uses, with no sales language', intro.h1 === 'Original art,on hire.'
  && /film and television, interiors and staged homes/.test(intro.lede) && /directly with the artist/.test(intro.lede) && !/\b(buy|sale|deal|discount|offer|price|cheap|best|exclusive|book now)\b/i.test(intro.lede), JSON.stringify(intro));
const v3 = await o.page.evaluate(() => {
  const scenes = [...document.querySelectorAll('.afh3-scene')];
  const credit = 'Painting by Colin Macaulay, PlotArt’s founder. Not offered for hire.';
  const pics = [...document.querySelectorAll('main img')].map(i => i.getAttribute('src'));
  return { scenes: scenes.length, tags: scenes.filter(f => f.querySelector('.afh3-tag')?.textContent === 'Illustration').length,
    credits: scenes.filter(f => f.querySelector('.afh3-credit')?.textContent === credit).length, heroCredit: document.querySelector('.afh3-hero-credit')?.textContent === credit,
    mCredit: document.querySelector('.afh3-hero + .afh3-hero-credit-m')?.textContent === credit, pics: [...new Set(pics)],
    intro: /The settings are illustrations; the painting is real\./.test(document.querySelector('.afh3-scenes-h').textContent) };
});
check('V1 three environments, each labelled “Illustration” and credited; the founder painting is the only image and is credited in the hero (v3)', v3.scenes === 3 && v3.tags === 3 && v3.credits === 3 && v3.heroCredit && v3.mCredit && v3.intro
  && v3.pics.length === 1 && v3.pics[0] === '../assets/hero/founder-01-abstract.webp', JSON.stringify(v3));
await shot(o.page, 'empty-desktop-1440');
await o.ctx.close();
o = await open(browser, P.empty, S, { device: 'iPhone 13' });
await shot(o.page, 'empty-phone-390-top', { full: false });
await o.page.evaluate(() => document.querySelector('[data-hire-empty]').scrollIntoView()); await o.page.waitForTimeout(300);
await shot(o.page, 'empty-phone-390-empty-state', { full: false });
await o.ctx.close();
await S.db.prepare("UPDATE artwork_hire SET offered = 0, withdrawn_at = '2026-11-10T22:00:00Z'").run();
o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 1000 } });
check('E2 if every listed work is withdrawn, the built cards stay hidden, the empty state appears and the hero action stays “How it works”', (await visible(o.page)).length === 0 && !(await o.page.$eval('[data-hire-empty]', e => e.hidden))
  && (await o.page.$eval('[data-hire-cta]', e => e.textContent + e.getAttribute('href'))) === 'How it works#afh3-how');
await o.ctx.close();
await S.db.prepare("UPDATE artwork_hire SET offered = 1, withdrawn_at = NULL").run();
await S.db.prepare("UPDATE artwork_hire SET offered = 0, withdrawn_at = '2026-11-10T22:00:00Z' WHERE artwork_id = 'wfixb2'").run();
o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 1000 } });
vis = await visible(o.page);
check('E3 a single withdrawn work is not shown; the others are', vis.length === 5 && !vis.includes('wfixb2'), vis.join());
await o.ctx.close();
await S.db.prepare("UPDATE artwork_hire SET offered = 1, withdrawn_at = NULL WHERE artwork_id = 'wfixb2'").run();

console.log('— links to the artist and the gallery marks (11 Nov 2026)');
o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 1000 } });
const lk = await o.page.$eval('[data-hire-work="wfixa1"]', c => ({ title: c.querySelector('h3 a')?.getAttribute('href'), artist: c.querySelector('.pa-hire-artist a')?.getAttribute('href'),
  more: c.querySelector('.pa-hire-more a')?.getAttribute('href'), moreText: c.querySelector('.pa-hire-more a')?.textContent, slug: c.dataset.hireArtistSlug + '/' + c.dataset.hireSlug }));
await o.ctx.close();
const exists = f => { try { readFileSync(path.join(P.fix, 'plotart', f)); return true; } catch { return false; } };
check('K1 each listing links its title to the work’s own page and its artist line and “See more by …” to the artist’s gallery (both exist)',
  lk.title === '../artists/fixture-artist-a/wfixa1.html' && lk.artist === '../artists/fixture-artist-a/' && lk.more === lk.artist && /^See more by Fixture Artist A/.test(lk.moreText)
  && lk.slug === 'fixture-artist-a/wfixa1' && exists('artists/fixture-artist-a/wfixa1.html') && exists('artists/fixture-artist-a/index.html'), JSON.stringify(lk));
const relayCalls = async (dir, url, fail = null, opts = {}) => {
  const r = await open(browser, dir, S, { viewport: { width: 1440, height: 1000 }, url, fail, ...opts }); await r.page.waitForTimeout(500);
  const marks = await r.page.$$eval('[data-pa-hire-mark]', a => a.map(x => x.className + ':' + x.textContent.trim().slice(0, 40)));
  const tiles = await r.page.$$eval('.pa-ag-work', a => a.filter(x => x.querySelector('.pa-ag-hire')).map(x => x.querySelector('a').getAttribute('href')));
  return { r, marks, tiles };
};
let gm = await relayCalls(P.fix, '/plotart/artists/fixture-artist-a/');
const noteHref = await gm.r.page.$eval('.pa-ag-hirenote a', a => a.getAttribute('href')).catch(() => null);
const axGal = await axe(gm.r.page);
await shot(gm.r.page, 'gallery-marks-1440-test-render', { ribbon: true });
await gm.r.ctx.close();
check('K2 while both works are listed, the artist’s gallery marks each “Available to hire” and adds one line linking to Art for Hire; no serious accessibility issue',
  gm.tiles.join() === 'wfixa1.html,wfixa2.html' && gm.marks.filter(m => m.startsWith('pa-ag-hire:')).length === 2 && gm.marks.some(m => m.startsWith('pa-ag-hirenote:'))
  && noteHref === '../../art-for-hire/#afh3-works' && axGal.length === 0, JSON.stringify([gm, noteHref, axGal]));
gm = await relayCalls(P.fix, '/plotart/artists/fixture-artist-a/wfixa1.html');
await gm.r.ctx.close();
check('K3 the work’s own page says it is also available to hire, with a link to Art for Hire', gm.marks.length === 1 && /^pa-aw-hire:Also available to hire/.test(gm.marks[0]), JSON.stringify(gm.marks));
await S.db.prepare("UPDATE artwork_hire SET offered = 0, withdrawn_at = '2026-11-10T22:00:00Z' WHERE artwork_id = 'wfixa2'").run();
gm = await relayCalls(P.fix, '/plotart/artists/fixture-artist-a/');
const one2 = await relayCalls(P.fix, '/plotart/artists/fixture-artist-a/wfixa2.html');
await gm.r.ctx.close(); await one2.r.ctx.close();
await S.db.prepare("UPDATE artwork_hire SET offered = 1, withdrawn_at = NULL WHERE artwork_id = 'wfixa2'").run();
check('K4 a withdrawn work loses its mark at once (gallery and its own page); the listed one keeps it', gm.tiles.join() === 'wfixa1.html' && one2.marks.length === 0, JSON.stringify([gm.tiles, one2.marks]));
const kf = [];
for (const fail of ['abort', '503', 'stale']) { const x = await relayCalls(P.fix, '/plotart/artists/fixture-artist-a/', fail); kf.push([fail, x.marks.length]); await x.r.ctx.close(); }
check('K5 if the live check fails, errors or is out of date, the gallery shows no mark (fail closed)', kf.every(([, n]) => n === 0), JSON.stringify(kf));
const seen = async (dir, url) => { const r = await open(browser, dir, S, { viewport: { width: 1440, height: 1000 }, url: 'about:blank' === url ? url : url });
  const n = []; r.page.on('request', q => { if (q.url().startsWith('https://relay.test')) n.push(q.url()); });
  await r.page.reload(); await r.page.waitForTimeout(900);
  const m = await r.page.$$eval('[data-pa-hire-mark]', a => a.length); await r.ctx.close(); return [n.length, m]; };
const real = await seen(P.fix, '/plotart/artists/leah-hewson/'), realW = await seen(P.fix, '/plotart/artists/leah-hewson/blowout-series-ii-1.html'),
  today = await seen(P.empty, '/plotart/artists/leah-hewson/'), fixA = await seen(P.fix, '/plotart/artists/fixture-artist-a/');
check('K6 an artist with no listed work gets no mark and their gallery makes no request beyond plotnua.ie (today, with nothing listed, no gallery does)',
  real[0] === 0 && real[1] === 0 && realW[0] === 0 && realW[1] === 0 && today[0] === 0 && today[1] === 0 && fixA[0] === 1 && fixA[1] === 3, JSON.stringify({ real, realW, today, fixA }));
{
  const S3 = await relay({ port: 8893, listing: false });
  const r = await open(browser, P.fix, S3, { viewport: { width: 1440, height: 1000 }, url: '/plotart/artists/fixture-artist-a/' }); await r.page.waitForTimeout(500);
  const m = await r.page.$$eval('[data-pa-hire-mark]', a => a.length); await r.ctx.close(); await S3.mf.dispose();
  check('K7 while Art for Hire is not open (artist terms switched off), no gallery mark appears even if a page lists works', m === 0, String(m));
}
const pj = readFileSync(path.join(REPO, 'plotart/assets/plotart.js'), 'utf8');
check('K8 the gallery marks need no change to any gallery page: they are added by the shared script, from the published Art for Hire page and the live check only',
  /data-hire-artist-slug/.test(pj) && /\/v1\/hire-listed/.test(pj) && !/localStorage|sessionStorage|document\.cookie/.test(pj.slice(pj.indexOf('Art for Hire marks'))));
{
  const r = await open(browser, P.fix, S, { device: 'iPhone 13', url: '/plotart/artists/fixture-artist-a/' }); await r.page.waitForTimeout(500);
  const ov = await r.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
  await r.page.evaluate(() => document.querySelector('.pa-ag-hirenote').scrollIntoView({ block: 'start' })); await r.page.evaluate(() => scrollBy(0, -80));
  await shot(r.page, 'gallery-marks-phone-test-render', { full: false, ribbon: true });
  const r2 = await open(browser, P.fix, S, { device: 'iPhone 13', url: '/plotart/artists/fixture-artist-a/wfixa1.html' }); await r2.page.waitForTimeout(500);
  await r2.page.evaluate(() => document.querySelector('.pa-aw-hire').scrollIntoView({ block: 'center' }));
  await shot(r2.page, 'artwork-mark-phone-test-render', { full: false, ribbon: true });
  check('K9 on a phone the marked gallery has no sideways scrolling', ov);
  await r.ctx.close(); await r2.ctx.close();
}

console.log('— live eligibility failures (fail closed)');
const fails = [];
for (const fail of ['abort', '503', 'stale', 'slow']) {
  o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 1000 }, fail });
  if (fail === 'slow') await o.page.waitForTimeout(6500);
  const st = await o.page.$eval('[data-hire-status]', e => e.hidden ? '' : e.textContent);
  fails.push([fail, (await visible(o.page)).length, /can’t confirm/.test(st)]);
  if (fail === 'abort') await shot(o.page, 'failure-check-unreachable-1440', { ribbon: true });
  await o.ctx.close();
}
check('F1 unreachable, error, out-of-date and no-answer checks all show NO works and say availability can’t be confirmed', fails.every(([, n, msg]) => n === 0 && msg), JSON.stringify(fails));
o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 1000 }, js: false });
check('F2 with scripts blocked, no work is shown and a note explains why', (await visible(o.page)).length === 0 && /turn on JavaScript/.test(await o.page.textContent('noscript')));
await o.ctx.close();
o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 1000 } });
o.page._hireFail = 'abort';
await o.page.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await o.page.waitForTimeout(600);
check('F3 works already shown are hidden again as soon as a later check fails', (await visible(o.page)).length === 0);
await o.ctx.close();
const S0 = await relay({ port: 8892, listing: false });
o = await open(browser, P.fix, S0, { viewport: { width: 1440, height: 1000 } });
check('F4 with Art for Hire switched off at the relay, no work is shown (“isn’t open yet”)', (await visible(o.page)).length === 0 && /isn’t open yet/.test(await o.page.$eval('[data-hire-status]', e => e.textContent)));
await o.ctx.close(); await S0.mf.dispose();

console.log('— the enquiry button and form');
o = await open(browser, P.fix, S, { viewport: { width: 1440, height: 1000 } });
await o.page.click('[data-hire-work="wfixa1"] [data-hire-enquire]', { force: true }); await o.page.waitForTimeout(300);
const b1 = await o.page.evaluate(() => ({ dialog: !!document.querySelector('dialog'), aria: document.querySelector('[data-hire-enquire]').getAttribute('aria-disabled'), closed: !document.querySelector('[data-hire-closed]').hidden,
  formInHtml: document.documentElement.outerHTML.includes('data-enquiries="on"') }));
check('B1 as built today (no enquiry form): the button is marked unavailable, opens nothing and points to “Hire enquiries are not yet open.”', !b1.dialog && b1.aria === 'true' && b1.closed && !b1.formInHtml, JSON.stringify(b1));
await o.ctx.close();
o = await open(browser, P.form, S, { viewport: { width: 1440, height: 1000 } });
await o.page.click('[data-hire-work="wfixa1"] [data-hire-enquire]', { force: true }); await o.page.waitForTimeout(300);
check('B2 even a page built with the form keeps it closed while the relay reports enquiries closed', !(await o.page.$('dialog')) && (await o.page.$eval('[data-hire-enquire]', b => b.getAttribute('aria-disabled'))) === 'true');
await o.ctx.close();
const S2 = await relay({ port: 8893, enquiries: true });
o = await open(browser, P.form, S2, { viewport: { width: 1440, height: 1000 } });
const btn = '[data-hire-work="wfixa1"] [data-hire-enquire]';
await o.page.focus(btn); await o.page.keyboard.press('Enter'); await o.page.waitForTimeout(400);
const d1 = await o.page.evaluate(() => ({ modal: !!document.querySelector('dialog[open]'), focus: document.activeElement && document.activeElement.id, label: document.querySelector('dialog').getAttribute('aria-labelledby'),
  film: [...document.querySelectorAll('#hf-intended_use option')].some(x => x.value === 'filming'), explain: document.querySelectorAll('.pa-hf-explain li').length }));
ax = await axe(o.page);
await shot(o.page, 'enquiry-dialog-1440-test-render', { full: false, ribbon: true });
await o.page.keyboard.press('Escape'); await o.page.waitForTimeout(300);
const back = await o.page.evaluate(() => ({ open: !!document.querySelector('dialog'), focus: document.activeElement && document.activeElement.closest('[data-hire-work]')?.dataset.hireWork }));
check('B3 once both approvals are in place: keyboard opens a labelled modal dialog with focus on the first field; Escape closes it and focus returns to the button', d1.modal && d1.focus === 'hf-name' && d1.label === 'hf-h' && !back.open && back.focus === 'wfixa1', JSON.stringify([d1, back]));
check('B4 the dialog shows the five statements, offers no filming option, and has no serious accessibility issues', d1.explain === 5 && d1.film === false && ax.length === 0, JSON.stringify(ax));
await o.page.click(btn); await o.page.waitForTimeout(300);
const f = 'dialog form';
for (const [k, v] of Object.entries({ name: 'Hana Hirer', email: 'hana@studio.example.test', business: 'Example Productions Ltd', role: 'Art director', use_place: 'Dublin 8' })) await o.page.fill(`${f} [name=${k}]`, v);
await o.page.selectOption(`${f} [name=project_type]`, 'staging'); await o.page.selectOption(`${f} [name=intended_use]`, 'display_staging'); await o.page.selectOption(`${f} [name=territory]`, 'ie');
const day = n => new Date(Date.now() + n * 86400_000).toISOString().slice(0, 10);
await o.page.fill(`${f} [name=date_from]`, day(10)); await o.page.fill(`${f} [name=date_to]`, day(20)); await o.page.check(`${f} [name=privacy]`);
await o.page.click(`${f} [type=submit]`); await o.page.waitForTimeout(900);
const done = await o.page.$eval('dialog', d => d.textContent);
check('B5 an enquiry sent from the page reaches the Stage 3B-3 relay and is confirmed with its PA-H- reference', /Thank you/.test(done) && /PA-H-\d{6}-/.test(done)
  && (await S2.db.prepare("SELECT COUNT(*) n FROM hire_enquiries").first()).n === 1);
await o.ctx.close();
o = await open(browser, P.form, S2, { device: 'iPhone 13' });
await o.page.click(btn); await o.page.waitForTimeout(400);
await shot(o.page, 'enquiry-dialog-phone-test-render', { full: false, ribbon: true });
const fits = await o.page.$eval('dialog', d => { const r = d.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth; });
check('R3 on a phone the dialog fits the screen', fits);
await o.ctx.close(); await S2.mf.dispose();

console.log('— the builder refuses anything not approved and published');
const cat = JSON.parse(readFileSync(path.join(P.fix, 'fixture-catalogue.json'), 'utf8'));
const tryBuild = mut => { const c = JSON.parse(JSON.stringify(cat)); mut(c); const fp = path.join(TMP, 'c.json'); writeFileSync(fp, JSON.stringify(c));
  return spawnSync('python3', [path.join(REPO, 'atlas-tools/plotart-hire-page.py'), P.fix, '--catalogue', fp, '--api', 'https://relay.test', '--preview'], { encoding: 'utf8' }); };
const r1 = tryBuild(c => { c.items[0].hire.handling_note = 'x'; }), r2 = tryBuild(c => { c.items[0].artwork_id = 'wnotthere'; }), r3 = tryBuild(c => { c.items[0].artist_slug = 'leah-hewson'; }),
  r4 = tryBuild(c => { c.items.push(c.items[0]); });
const sold = path.join(P.fix, 'plotart/artists/fixture-artist-a/gallery.json'), g0 = readFileSync(sold, 'utf8');
writeFileSync(sold, g0.replace('"availability": "available"', '"availability": "sold"'));
const r5 = tryBuild(() => {}); writeFileSync(sold, g0);
check('P1 the build stops (nothing written) for a private field, a work not in the gallery, another artist’s gallery, a duplicate, or a sold work', [r1, r2, r3, r4, r5].every(r => r.status === 1 && /REFUSED/.test(r.stderr)), [r1, r2, r3, r4, r5].map(r => r.stderr.trim()).join(' | '));
const seo = readFileSync(path.join(P.fix, 'plotart/art-for-hire/index.html'), 'utf8');
check('P2 the page is noindex until the founder decides otherwise, and is not in the sitemap', /<meta name="robots" content="noindex, follow">/.test(seo) && !/art-for-hire/.test(readFileSync(path.join(REPO, 'sitemap.xml'), 'utf8')));

await browser.close(); await S.mf.dispose();
} finally { rmSync(TMP, { recursive: true, force: true }); }
const pass = results.filter(Boolean).length;
console.log(`\nART FOR HIRE PAGE · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
process.exit(pass === results.length ? 0 : 1);
