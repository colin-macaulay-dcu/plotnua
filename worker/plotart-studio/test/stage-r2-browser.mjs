// Local staging walk-through for R2 (27 Nov 2026): a fresh Gallery Artist and an existing Founding Artist, desktop and
// mobile, in a real browser against a local Studio (Miniflare D1). Nothing touches Cloudflare. Screenshots to argv[2].
//   node test/stage-r2-browser.mjs <screenshot folder>
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
import { statements } from './sql.mjs';

const { chromium, devices } = createRequire(import.meta.url)('playwright');   // the pre-installed Playwright
const OUT = process.argv[2] || '.';
const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const S = await start({ port: 8941, enquiry: {} });
const H = e => ({ 'Cf-Access-Jwt-Assertion': token(e), 'X-Studio': '1', 'Content-Type': 'application/json' });
const post = async (p, e, b) => (await S.mf.dispatchFetch(S.url + p, { method: 'POST', headers: H(e), body: JSON.stringify(b) })).json();
const FRAN = 'fran-founding@example.test', NORA = 'nora-new@example.test', OLGA = 'olga-gallery@example.test';
let browser;
try {
  for (const st of statements(readFileSync(HERE + 'migrations/0013_gallery_artist_agreement_text.sql', 'utf8'))) await S.db.prepare(st).run();
  await post('/api/admin/artists', FOUNDER, { display_name: 'Fran Founding', email: FRAN, programme: 'founding' });
  await post('/api/admin/artists', FOUNDER, { display_name: 'Olga Gallery', email: OLGA, programme: 'gallery_artist' });
  const fa = await acceptAgreement(S.mf, S.url, FRAN);
  check('S0 the existing Founding Artist accepted PA-FAA-2026-11 before migration 0030', fa.s === 200);
  for (const st of statements(readFileSync(HERE + 'migrations/0030_artist_agreement_r2.sql', 'utf8'))) await S.db.prepare(st).run();
  await post('/api/admin/artists', FOUNDER, { display_name: 'Nora New', email: NORA, programme: 'gallery_artist' });
  browser = await chromium.launch();
  const devs = [['desktop', { viewport: { width: 1440, height: 1000 } }], ['mobile', devices['iPhone 13']]];
  for (const [label, dev] of devs) {
    const page = async email => (await browser.newContext({ ...dev, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email) } })).newPage();
    const open = async (pg, path) => { await pg.goto(S.url + path); await pg.waitForSelector('h1'); await pg.waitForTimeout(700); };

    // fresh Gallery Artist (R2): accepts on desktop, then is checked on mobile
    const n = await page(NORA);
    await open(n, '/#/agreement');
    const h1 = await n.textContent('h1'), body = await n.textContent('body');
    if (label === 'desktop') {
      check('G1 desktop: the fresh Gallery Artist sees “Artist Agreement”, both R2 documents and the revised summary', /Artist Agreement/.test(h1) && !/Gallery Artist Agreement/.test(h1)
        && body.includes('PA-GAA-2026-11-R2') && body.includes('PA-GPIL-2026-11-R2') && /Independent sales carry no PlotArt commission/.test(body)
        && /until compatible payment terms are issued/.test(body) && !/Collectors pay you directly/.test(body), h1 + ' | ' + body.slice(0, 300));
      await n.screenshot({ path: `${OUT}/r2-new-gallery-artist-desktop-before.png`, fullPage: true });
      const pdfs = await n.$$eval('a[href$=".pdf"]', as => as.map(a => a.getAttribute('href')));
      check('G2 desktop: both R2 PDFs are offered for download', pdfs.some(h => h.includes('PA-GAA-2026-11-R2.pdf')) && pdfs.some(h => h.includes('PA-GPIL-2026-11-R2.pdf')), JSON.stringify(pdfs));
      for (const h of pdfs.filter(x => /R2\.pdf$/.test(x))) {
        const r = await n.request.get(new URL(h, S.url).toString());
        check(`G3 desktop: ${h} downloads as a PDF`, r.status() === 200 && /pdf/.test(r.headers()['content-type'] || ''), r.status());
      }
      await n.check('input[type=checkbox]');
      await n.getByRole('button', { name: /accept/i }).first().click();
      await n.waitForTimeout(1500);
      const after = await n.textContent('body');
      check('G4 desktop: one tick and Accept records both documents; the page then shows the acceptance', /You have accepted these documents/.test(after), after.slice(0, 400));
      await n.screenshot({ path: `${OUT}/r2-new-gallery-artist-desktop-accepted.png`, fullPage: true });
    } else {
      check('G5 mobile: the accepted R2 artist sees the Artist Agreement with both documents to download', /Artist Agreement/.test(h1) && /You have accepted these documents/.test(body)
        && (await n.$$('a[href$="R2.pdf"]')).length >= 2, h1);
      check('G6 mobile: no horizontal scrolling on the agreement page', await n.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1));
      await n.screenshot({ path: `${OUT}/r2-new-gallery-artist-mobile-accepted.png`, fullPage: true });
    }
    await n.goto(S.url + '/checkout-pilot'); await n.waitForTimeout(1200);
    const cb = await n.textContent('body');
    check(`G7 ${label}: Online sales tells the R2 artist managed checkout is unavailable until compatible payment terms are issued; no opt-in form`,
      /until compatible payment terms are issued/.test(cb) && !(await n.$('form[data-f="optin"]')), cb.slice(0, 300));
    await n.screenshot({ path: `${OUT}/r2-new-gallery-artist-${label}-online-sales.png`, fullPage: true });

    // existing Founding Artist
    const f = await page(FRAN);
    await open(f, '/#/agreement');
    const fh = await f.textContent('h1'), fb = await f.textContent('body');
    check(`F1 ${label}: the existing Founding Artist still sees the Founding Artist Agreement, accepted, with no R2 wording`, /Founding Artist Agreement/.test(fh) && /You have accepted these documents/.test(fb)
      && fb.includes('PA-FAA-2026-11') && !fb.includes('PA-GAA-2026-11-R2') && !/compatible payment terms/.test(fb), fh);
    const fp = await f.$$eval('a[href$=".pdf"]', as => as.map(a => a.getAttribute('href')));
    check(`F2 ${label}: the Founding Artist can still download PA-FAA-2026-11 and PA-GPIL-2026-11`, fp.some(h => h.includes('PA-FAA-2026-11.pdf')) && fp.some(h => h.includes('PA-GPIL-2026-11.pdf')), JSON.stringify(fp));
    await f.screenshot({ path: `${OUT}/existing-founding-artist-${label}.png`, fullPage: true });

    // existing Gallery Artist who has not accepted yet: original summary only
    const o = await page(OLGA);
    await open(o, '/#/agreement');
    const ob = await o.textContent('body');
    check(`O1 ${label}: an existing Gallery Artist (not yet accepted) sees the original agreement and summary, not the R2 lines`, /Gallery Artist Agreement/.test(await o.textContent('h1'))
      && /Collectors pay you directly/.test(ob) && !/Independent sales carry no PlotArt commission/.test(ob) && !ob.includes('PA-GAA-2026-11-R2'), ob.slice(0, 300));
    await o.screenshot({ path: `${OUT}/existing-gallery-artist-${label}.png`, fullPage: true });
  }
} catch (e) { console.error(e); results.push(false); }
finally { if (browser) await browser.close(); await S.mf.dispose(); }
const pass = results.filter(Boolean).length;
console.log(`\nR2 LOCAL STAGING (browser) · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
process.exit(pass === results.length ? 0 : 1);
