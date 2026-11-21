// PROVE · PlotArt Refine on All Artworks, in a real browser (founder approval 21 Nov 2026). Development check, not in
// the gate (it needs Playwright and a local web server). Nothing leaves this machine: the Art for Hire relay is
// SIMULATED by intercepting its address, so the live, fail-closed hire rule can be exercised both ways.
//   python3 -m http.server 8767   (from the repository root)
//   node atlas-tools/prove-plotart-refine.cjs http://127.0.0.1:8767 EXPECTED.json [SHOTS_DIR]
const { chromium, devices } = require('playwright');
const fs = require('fs');
const BASE = process.argv[2], expected = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')), SHOTS = process.argv[4];
const PAGE = BASE + '/plotart/artworks/';
const RELAY = 'https://plotart-enquiry.colin-a41.workers.dev';
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${ok ? '' : '  [' + d + ']'}`); };
const shown = p => p.evaluate(() => document.querySelectorAll('.pa-coll-work:not([data-rf-out])').length);
const total = expected.order.length;

async function settle(page) {   // the founder's screenshot procedure: scroll through, let images load
  await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 700) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); } scrollTo(0, 0); });
  await page.waitForFunction(() => [...document.images].filter(i => !i.closest('[data-rf-out]')).every(i => i.complete && i.naturalWidth > 0), null, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(400);
}
const toLine = (page, off) => page.evaluate(o => scrollTo(0, document.querySelector('[data-rf-count]').getBoundingClientRect().top + scrollY - o), off);

// a simulated Art for Hire catalogue + relay answer (only inside this test)
async function simulateHire(ctx, { catalogue = [], answer = null, status = 200 }) {
  await ctx.route(BASE + '/plotart/art-for-hire/', async route => {
    const cards = catalogue.map(id => `<li data-hire-work="${id}" data-hire-slug="x" data-hire-artist-slug="y" hidden></li>`).join('');
    await route.fulfill({ status: 200, contentType: 'text/html', body: `<!doctype html><ul>${cards}</ul><script src="hire-live.js" data-api="${RELAY}" data-enquiries="off" defer></script>` });
  });
  await ctx.route(RELAY + '/v1/hire-listed', route => answer === 'network'
    ? route.abort() : route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(answer) }));
}
const future = () => new Date(Date.now() + 10 * 60 * 1000).toISOString();

(async () => {
  const b = await chromium.launch();
  console.log('PROVE · PlotArt Refine (All Artworks)');
  // ---------- desktop: real page, real (empty) hire catalogue ----------
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: SHOTS ? 2 : 1 });
  await ctx.route(RELAY + '/**', r => r.abort());   // never call the real relay from a test
  const d = await ctx.newPage(); const errors = []; d.on('pageerror', e => errors.push(String(e)));
  await d.goto(PAGE, { waitUntil: 'networkidle' }); await settle(d);
  check(`B1 all ${total} works show before any choice; the count is the page's own`, await shown(d) === total && (await d.textContent('[data-rf-count]')).trim() === expected.count);
  check('B2 "Clear" is hidden while nothing is chosen; "Available to hire" is not offered (no listed work)', await d.isHidden('.pa-rf-clear--line') && await d.isHidden('[data-rf-hire]'));
  check('B3 the label reads "Artist location"', (await d.textContent('[data-rf-group="county"] .pa-rf-name')).trim() === 'Artist location');
  if (SHOTS) { await toLine(d, 140); await d.screenshot({ path: SHOTS + '/01-desktop-refine-line.png' }); }
  // keyboard: Tab to Price, Enter opens, Tab into the options, Space ticks, Escape closes and returns focus
  await d.focus('[data-rf-group="price"] .pa-rf-trig'); await d.keyboard.press('Enter');
  check('K1 keyboard: Enter on "Price" opens its menu (aria-expanded true)', await d.getAttribute('[data-rf-group="price"] .pa-rf-trig', 'aria-expanded') === 'true' && await d.isVisible('#rf-price'));
  await d.keyboard.press('Tab'); await d.keyboard.press('Space');
  check('K2 keyboard: Tab reaches the first option and Space chooses it', await d.isChecked('#rf-price input[value="0-1000"]') && await shown(d) === expected.cases['price under 1,000'].n);
  if (SHOTS) { await toLine(d, 140); await d.screenshot({ path: SHOTS + '/02-desktop-price-open.png' }); }
  await d.keyboard.press('Escape');
  check('K3 keyboard: Escape closes the menu and returns focus to "Price"', await d.isHidden('#rf-price') && await d.evaluate(() => document.activeElement.closest('[data-rf-group]')?.dataset.rfGroup) === 'price');
  check('B4 the choice is kept in the address (shareable)', new URL(d.url()).searchParams.get('price') === '0-1000');
  for (const [k, v] of Object.entries(expected.cases)) {
    await d.goto(PAGE + '?' + v.q, { waitUntil: 'networkidle' });
    check(`C  ${k}: ${await shown(d)} shown, independent count ${v.n}`, await shown(d) === v.n, await d.textContent('[data-rf-count]'));
  }
  await d.goto(PAGE + '?price=1000-2500', { waitUntil: 'networkidle' });
  const order = await d.evaluate(() => [...document.querySelectorAll('.pa-coll-work:not([data-rf-out])')].map(c => c.dataset.work));
  check('O1 filtering never reorders: the works shown keep the collection order', JSON.stringify(order) === JSON.stringify(expected.order.filter(w => order.includes(w))));
  await d.goto(PAGE + '?price=1000-2500&size=100-150', { waitUntil: 'networkidle' }); await settle(d);
  if (SHOTS) { await toLine(d, 140); await d.screenshot({ path: SHOTS + '/03-desktop-filtered.png' }); }
  check('B5 a shared address restores the choices, the summary and "Clear"', (await d.textContent('[data-rf-group="price"] [data-rf-val]')) === '€1,000 – €2,499' && await d.isVisible('.pa-rf-clear--line'));
  await d.click('.pa-rf-clear--line');
  check('B6 "Clear" restores the full collection and the address', await shown(d) === total && !new URL(d.url()).search);
  await d.goto(PAGE + '?price=0-1000&size=150-', { waitUntil: 'networkidle' });
  const n0 = await shown(d);
  check('B7 no match: a calm line with "Clear the filters" (only then)', (n0 === 0) === await d.isVisible('[data-rf-none]'));
  check('B8 no script errors', errors.length === 0, errors.join(' | '));
  // ---------- fail safe ----------
  const nj = await (await b.newContext({ viewport: { width: 1440, height: 900 }, javaScriptEnabled: false })).newPage();
  await nj.goto(PAGE);
  check('F1 without JavaScript: the full collection and no Refine line (exactly as before)', await nj.isHidden('[data-rf]') && (await nj.$$('.pa-coll-work')).length === total);
  const blk = await b.newContext(); await blk.route('**/plotart-refine.js', r => r.abort()); const bp = await blk.newPage();
  await bp.goto(PAGE + '?price=0-1000', { waitUntil: 'networkidle' });
  check('F2 script blocked: the full collection, no Refine line, the address is ignored', await bp.isHidden('[data-rf]') && await shown(bp) === total);
  const brk = await b.newContext();
  await brk.route(u => u.href.startsWith(PAGE), async r => { const res = await r.fetch(); let t = await res.text(); t = t.replace(' data-rf-count aria-live="polite"', ''); await r.fulfill({ response: res, body: t }); });
  const bk = await brk.newPage(); await bk.goto(PAGE + '?price=0-1000', { waitUntil: 'networkidle' });
  check('F3 an error inside the script: it puts back the full collection and hides the Refine line', await bk.isHidden('[data-rf]') && await shown(bk) === total);
  // ---------- Art for Hire: live and fail-closed (SIMULATED relay) ----------
  const [w1, w2] = expected.order;
  const hireCase = async (label, sim, expectShown, query = '') => {
    const c = await b.newContext({ viewport: { width: 1440, height: 900 } });
    await simulateHire(c, sim);
    const p = await c.newPage(); await p.goto(PAGE + query, { waitUntil: 'networkidle' }); await p.waitForTimeout(300);
    const vis = await p.isVisible('[data-rf-hire]');
    check(`H  ${label}: "Available to hire" ${expectShown ? 'offered' : 'NOT offered'}`, vis === expectShown);
    return { p, c };
  };
  const ok = { ok: true, open: true, valid_until: future(), items: [{ id: w1 }] };
  const { p: hp } = await hireCase('listed in the catalogue AND by the live check', { catalogue: [w1, w2], answer: ok }, true, '?hire=1');
  check('H  ... a shared ?hire=1 applies once confirmed, showing only the confirmed work', await shown(hp) === 1 && await hp.evaluate(w => !document.querySelector(`[data-work="${w}"]`).hasAttribute('data-rf-out'), w1));
  await hireCase('live check names a work that is NOT in the catalogue', { catalogue: [w2], answer: ok }, false);
  await hireCase('relay unreachable', { catalogue: [w1], answer: 'network' }, false);
  await hireCase('relay error (500)', { catalogue: [w1], answer: { ok: false }, status: 500 }, false);
  await hireCase('Art for Hire not open', { catalogue: [w1], answer: { ...ok, open: false } }, false);
  await hireCase('answer out of date (expired)', { catalogue: [w1], answer: { ...ok, valid_until: new Date(Date.now() - 1000).toISOString() } }, false);
  const { p: hq } = await hireCase('no hire catalogue: ?hire=1 is ignored', { catalogue: [], answer: ok }, false, '?hire=1');
  check('H  ... and the whole collection stays visible', await shown(hq) === total);
  // ---------- mobile ----------
  const mctx = await b.newContext({ ...devices['iPhone 13'] }); await mctx.route(RELAY + '/**', r => r.abort());
  const m = await mctx.newPage(); await m.goto(PAGE, { waitUntil: 'networkidle' }); await settle(m);
  if (SHOTS) { await toLine(m, 90); await m.screenshot({ path: SHOTS + '/04-mobile-refine-button.png' }); }
  await m.click('.pa-rf-open'); await m.waitForTimeout(200);
  check('M1 the sheet opens with focus on its heading; the page behind is inert', await m.evaluate(() => document.activeElement.classList.contains('pa-rf-sheet-t')) && await m.evaluate(() => document.querySelector('.pa-coll-grid').inert === true));
  await m.click('[data-rf-group="price"] .pa-rf-trig'); await m.waitForTimeout(120);
  if (SHOTS) await m.screenshot({ path: SHOTS + '/05-mobile-sheet-price.png' });
  await m.click('text=€1,000 – €2,499'); await m.click('[data-rf-group="price"] .pa-rf-trig');
  await m.click('[data-rf-group="size"] .pa-rf-trig'); await m.click('text=100 – 149 cm'); await m.waitForTimeout(120);
  if (SHOTS) await m.screenshot({ path: SHOTS + '/06-mobile-sheet-chosen.png' });
  const n = expected.cases['price 1,000-2,499 + size 100-149'].n;
  check('M2 the sheet button names the live result', (await m.textContent('.pa-rf-show')).replace(/\s+/g, ' ').trim() === `Show ${n} ${n === 1 ? 'work' : 'works'}`);
  await m.keyboard.press('Escape');
  check('M3 Escape closes the sheet, focus returns to "Refine", the page is interactive again', await m.isHidden('.pa-rf-sheet') && await m.evaluate(() => document.activeElement.classList.contains('pa-rf-open') && !document.querySelector('.pa-coll-grid').inert));
  check('M4 the Refine button shows how many choices are active', (await m.textContent('[data-rf-badge]')).trim() === '2');
  await settle(m); if (SHOTS) { await toLine(m, 90); await m.screenshot({ path: SHOTS + '/07-mobile-filtered.png' }); }
  check('M5 no horizontal overflow on a phone', await m.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await b.close();
  console.log(`\nPLOTART REFINE · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
  process.exit(results.every(Boolean) ? 0 : 1);
})();
