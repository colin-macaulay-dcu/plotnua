// PROVE · Phase C screens on a phone (390 x 844): every control of the new cards can be scrolled to and pressed, i.e. the
// sticky header and the save bar never cover it once it is in view. Synthetic artists, local Worker.  node test/prove-mobile-reach.mjs
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
const { chromium } = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json')('playwright');
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
console.log('PROVE · Phase C screens on a phone: nothing is covered');
const { mf, url, db } = await start({ port: 8883 });
const call = (m, p, e, b) => mf.dispatchFetch(url + p, { method: m, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(e) }, body: b ? JSON.stringify(b) : undefined }).then(r => r.json());
await seedPublished(db, { id: 'abram', slug: 'bram', email: 'bram@example.test', name: 'Bram Example', works: 3 });
await seedPublished(db, { id: 'acleo', slug: 'cleo', email: 'cleo@example.test', name: 'Cleo Demo', works: 2 });
await call('POST', '/api/admin/galleries/spaces/members', FOUNDER, { artist_id: 'abram' });
await call('POST', '/api/galleries/spaces/accept', 'bram@example.test');
await call('POST', '/api/admin/galleries/spaces/artworks/wabram1/place', FOUNDER);
await call('POST', '/api/admin/galleries/being/members', FOUNDER, { artist_id: 'abram' });
await call('POST', '/api/admin/image-use/requests', FOUNDER, { artist_id: 'abram', scope: 'social_media', gallery_id: null, artwork_ids: ['wabram1'], purpose: 'One post introducing the gallery', channels: 'PlotArt Instagram' });
await call('PUT', '/api/me/location', 'bram@example.test', { country: 'IE', county: 'Sligo', town: 'Strandhill', show_location: true, show_town: true });
const b = await chromium.launch();
async function reach(email, path, sel, name, prep) {
  const ctx = await b.newContext({ ...{ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email) } });
  const pg = await ctx.newPage(); await pg.goto(url + path, { waitUntil: 'networkidle' }).catch(() => {}); await pg.waitForTimeout(900);
  if (prep) await prep(pg);
  // a typed edit makes the save bar appear on the Profile page, the worst case for covering controls
  const bad = await pg.evaluate(async sel => {
    const out = [], els = [...document.querySelectorAll(sel)].filter(e => e.offsetParent !== null && !(e.closest('details:not([open])') && e.tagName !== 'SUMMARY'));   // folded content is not on screen
    for (const e of els) {
      for (const where of ['start', 'center', 'end', 'nearest']) {
        e.scrollIntoView({ block: where }); await new Promise(r => setTimeout(r, 30));
        const r = e.getBoundingClientRect(), x = r.left + Math.min(r.width / 2, 20), y = r.top + r.height / 2;
        const hit = document.elementFromPoint(x, y);
        if (where === 'center' && !(hit && (hit === e || e.contains(hit)))) out.push(`${e.tagName}#${e.id || ''}.${e.className} "${(e.textContent || e.value || '').trim().slice(0, 30)}" covered by ${hit ? hit.tagName + '.' + hit.className : 'nothing'}`);
      }
    }
    return { n: els.length, out };
  }, sel);
  check(`${name}: every control (${bad.n}) is unobstructed once scrolled into view`, bad.n > 0 && !bad.out.length, bad.out.join(' | '));
  await ctx.close();
}
const CTL = 'button, select, input:not([type=hidden]), textarea, summary, a.st-btn';
await reach('bram@example.test', '/', `#yg-card :is(${CTL})`, 'Artist Studio home · Your galleries');
await reach('bram@example.test', '/#/profile', `:is(#loc-card, #del-card, .st-cv) :is(${CTL})`, 'Artist Profile · location, delivery, Exhibitions (save bar showing)',
  async pg => { await pg.fill('#f-exhibitions', '## Solo exhibitions\n- 2025 · Example Gallery'); await pg.waitForTimeout(400); });
await reach(FOUNDER, '/admin/galleries', `#app :is(${CTL})`, 'Founder Galleries (Spaces)');
await reach(FOUNDER, '/admin/galleries', `[data-ask] :is(${CTL})`, 'Founder Galleries · Ask for permission (unfolded)', async pg => { await pg.click('[data-ask] > summary'); await pg.waitForTimeout(200); });
await reach(FOUNDER, '/admin/opportunities', `.st-loc-ov :is(${CTL})`, 'Founder Opportunities · Where artists are based');
await b.close(); await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nPHONE REACH · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
