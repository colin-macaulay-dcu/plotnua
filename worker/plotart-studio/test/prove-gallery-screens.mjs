// PROVE · the three-gallery screens and the founder's Locations tab (Phase C), driven through the real Studio pages in a
// browser. Synthetic artists only; local Miniflare D1; nothing touches Cloudflare.   node test/prove-gallery-screens.mjs [--shots DIR]
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
console.log('PROVE · three-gallery screens and Locations (Phase C)');
const { mf, url, db } = await start({ port: 8895 });
await seedPublished(db, { id: 'aava', slug: 'ava-sample', email: 'ava@example.test', name: 'Ava Sample', works: 2, number: 1 });
await seedPublished(db, { id: 'aben', slug: 'ben-sample', email: 'ben@example.test', name: 'Ben Sample', works: 1, number: 2 });
const b = await chromium.launch();
const as = async (email, w = 1280, h = 1000) => b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: SHOTS ? 2 : 1, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1' } });
const errs = [];
const open = async (ctx, path) => { const p = await ctx.newPage(); p.on('pageerror', e => errs.push(e.message)); await p.goto(url + path, { waitUntil: 'networkidle' }); await p.waitForTimeout(700); return p; };
const fctx = await as(FOUNDER), actx = await as('ava@example.test');
let fp = await open(fctx, '/admin/galleries');
check('G1 the founder’s Galleries tab shows Contemporary, Spaces and Being; Spaces and Being In preparation',
  (await fp.$$eval('section[data-g] h2', hs => hs.map(h => h.textContent))).join() === 'Contemporary,Spaces,Being'
  && (await fp.$eval('section[data-g="spaces"] .st-pill', e => e.textContent)) === 'In preparation' && (await fp.$eval('section[data-g="being"] .st-pill', e => e.textContent)) === 'In preparation');
await fp.selectOption('section[data-g="spaces"] [data-inv]', 'aava'); await fp.click('section[data-g="spaces"] [data-act="invite"]'); await fp.waitForTimeout(800);
check('G2 the founder invites Ava to Spaces: recorded as an invitation waiting for the artist (not a member yet)', /Invited, waiting for the artist/.test(await fp.$eval('section[data-g="spaces"]', e => e.textContent)));
let ap = await open(actx, '/#/galleries');
check('G3 Ava sees the invitation on her Galleries page', /PlotArt has invited you/.test(await ap.$eval('section[data-g="spaces"]', e => e.textContent)));
if (SHOTS) await (await ap.$('section[data-g="spaces"]')).screenshot({ path: SHOTS + '/GAL-artist-invitation.png' });
await ap.click('section[data-g="spaces"] [data-m="accept"]'); await ap.waitForTimeout(800);
check('G4 Ava accepts: she is a member of Spaces, and can propose her own works', /You’re a member/.test(await ap.$eval('section[data-g="spaces"]', e => e.textContent)) && (await ap.$$('section[data-g="spaces"] [data-p="propose"]')).length === 2);
fp = await open(fctx, '/admin/galleries');
await fp.selectOption('section[data-g="spaces"] [data-placew]', { index: 1 }); await fp.click('section[data-g="spaces"] [data-act="place"]'); await fp.waitForTimeout(800);
ap = await open(actx, '/#/galleries');
await ap.click('section[data-g="spaces"] [data-p="accept"]'); await ap.waitForTimeout(800);
check('G5 the founder places one of Ava’s works; it shows in Spaces only after Ava accepts', /Shown here/.test(await ap.$eval('section[data-g="spaces"]', e => e.textContent)));
if (SHOTS) { await ap.addStyleTag({ content: '.st-top{position:static!important}' }); await ap.screenshot({ path: SHOTS + '/GAL-artist-galleries.png', fullPage: true }); }
fp = await open(fctx, '/admin/galleries');
await fp.click('section[data-g="spaces"] [data-act="order-init"]'); await fp.waitForTimeout(800);
const spaces = await fp.$eval('section[data-g="spaces"]', e => e.textContent);
check('G6 the founder orders Spaces from 01, with readiness against its targets; Spaces is still In preparation', /01 · Ava Sample/.test(spaces) && /1 live artist · 1 work/.test(spaces) && /not yet ready/.test(spaces)
  && (await fp.$eval('section[data-g="spaces"] .st-pill', e => e.textContent)) === 'In preparation', spaces.slice(0, 300));
await fp.fill('section[data-g="spaces"] [data-confirm]', 'OPEN'); await fp.click('section[data-g="spaces"] [data-act="open"]'); await fp.waitForTimeout(800);
check('G7 opening needs the exact typed confirmation: "OPEN" alone is refused and Spaces stays In preparation', (await fp.$eval('section[data-g="spaces"] .st-pill', e => e.textContent)) === 'In preparation');
if (SHOTS) await (await fp.$('section[data-g="spaces"]')).screenshot({ path: SHOTS + '/GAL-founder-spaces.png' });
if (SHOTS) { await fp.addStyleTag({ content: '.st-top{position:static!important}' }); await fp.screenshot({ path: SHOTS + '/GAL-founder-dashboard.png', fullPage: true }); }
const w = (await db.prepare("SELECT id FROM artworks WHERE artist_id='aava' ORDER BY ord LIMIT 1").first()).id;
await fp.selectOption('#iu-w', [w]); await fp.fill('#iu-p', 'Homepage entrance for Spaces while the gallery is prepared'); await fp.fill('#iu-c', 'plotnua.ie homepage'); await fp.click('[data-act="iu"]'); await fp.waitForTimeout(800);
ap = await open(actx, '/#/galleries');
const before = (await db.prepare('SELECT COUNT(*) n FROM image_use_consents').first()).n;
if (SHOTS) await (await ap.$$('section.st-card')).at(-1).screenshot({ path: SHOTS + '/GAL-artist-image-use.png' });
await ap.click('[data-u="yes"]'); await ap.waitForTimeout(800);
check('G8 an image-use request reaches Ava; her yes is recorded for that one use, and she can withdraw it later',
  (await db.prepare('SELECT COUNT(*) n FROM image_use_consents').first()).n === before + 1 && (await ap.$$('[data-wd]')).length === 1);
const bctx = await as('ben@example.test'); const bp = await open(bctx, '/#/galleries');
check('G9 Ben sees only his own galleries: not a member of Spaces, no request for him', /Not a member/.test(await bp.$eval('section[data-g="spaces"]', e => e.textContent)) && !(await bp.$$('[data-u]')).length);
const deny = await bp.evaluate(async () => (await fetch('/api/admin/galleries', { headers: { 'X-Studio': '1' } })).status);
check('G10 an artist cannot open the founder’s gallery routes', deny === 403);
const T = '2026-11-25T10:00:00.000Z';
await db.prepare("INSERT INTO artist_locations (artist_id, country, county, town, show_location, show_town, confirmed_at, confirmed_by, updated_at) VALUES ('aava','IE','Sligo',NULL,1,0,?,'artist',?), ('aben','IE','Cork',NULL,0,0,?,'artist',?)").bind(T, T, T, T).run();
await db.prepare("INSERT INTO artist_delivery (artist_id, scope, counties, show_delivery, confirmed_at, confirmed_by, updated_at) VALUES ('aben','island','[]',1,?,'artist',?)").bind(T, T).run();
const lp = await open(fctx, '/admin/locations?county=Sligo');
const rows = await lp.$$eval('tbody tr', trs => trs.map(t => [...t.children].map(c => c.textContent.trim())));
check('L1 the founder’s Locations tab filtered by Sligo: Ava "Based here" first, then Ben "Delivers here" (all-island)',
  rows.length === 2 && rows[0][0] === 'Ava Sample' && rows[0][1] === 'Based here' && rows[1][0] === 'Ben Sample' && rows[1][1] === 'Delivers here', JSON.stringify(rows));
if (SHOTS) await lp.screenshot({ path: SHOTS + '/LOC-founder-sligo.png', fullPage: true });
const home = await open(actx, '/#/');
const hs = await home.$$eval('.st-card > h3', hs => hs.map(h => [h.textContent, getComputedStyle(h).textTransform, getComputedStyle(h).letterSpacing]));
const bul = await home.$$eval('.st-list li', ls => ls.map(l => getComputedStyle(l, '::before').content));
check('L3 the new screens’ styles stay on those screens: the Studio dashboard’s card headings and checklist keep their approved look',
  hs.length >= 2 && hs.every(([, t, l]) => t === 'none' && !(parseFloat(l) > 0)) && bul.length > 0 && bul.every(c => c !== 'none'), JSON.stringify({ hs, bul }));
check('L2 no script errors on any screen', !errs.length, errs.join(' | '));
await b.close(); await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nGALLERY SCREENS AND LOCATIONS · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
