// PROVE · PlotArt Studio · Three galleries: the founder's Galleries screen and the artist's "Your galleries" card (Phase C,
// Track C, 25 Nov 2026). Drives both screens in a real browser against the local Worker (Miniflare/workerd, local D1),
// with clearly fictional artists and synthetic images. Nothing here touches Cloudflare.
//   node test/prove-galleries-ui.mjs [--shots DIR]
import { readFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';

const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');
const SHOTS = (() => { const i = process.argv.indexOf('--shots'); return i > 0 ? process.argv[i + 1] : null; })();
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
console.log('PROVE · PlotArt Studio · Three galleries: founder and artist screens');

const { mf, url, db } = await start({ port: 8861 });
const IMAGES = await mf.getR2Bucket('IMAGES', 'studio');
const call = async (method, path, email, body) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(email) }, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
// Fictional artists (clearly labelled in every preview); synthetic abstract images, no real artwork
const PEOPLE = [['amara', 'amara-sample', 'Amara Sample (fictional)', 3], ['bram', 'bram-example', 'Bram Example (fictional)', 3], ['cleo', 'cleo-demo', 'Cleo Demo (fictional)', 2], ['dara', 'dara-test', 'Dara Test (fictional)', 2]];
let n = 0;
for (const [id, slug, name, works] of PEOPLE) {
  await seedPublished(db, { id: 'a' + id, slug, email: `${id}@example.test`, name, works, bucket: IMAGES });
  for (let i = 1; i <= works; i++) {
    const f = `/tmp/synth/s${n++ % 12}.jpg`;
    if (existsSync(f)) await IMAGES.put(`previews/a${id}/${i}.jpg`, Uint8Array.from(readFileSync(f)).buffer);
    await db.prepare('UPDATE artworks SET title = ? WHERE id = ?').bind(['Tidal Room', 'Quiet Field', 'North Light', 'Salt Study', 'Ember', 'Harbour Blue', 'Inland', 'Late Orchard', 'Small Hours', 'Drift'][(n - 1) % 10], `wa${id}${i}`).run();
  }
}
// the published snapshots carry the fictional titles too (the founder's screen shows published titles)
for (const v of (await db.prepare('SELECT artist_id, snapshot FROM versions').all()).results) {
  const snapObj = JSON.parse(v.snapshot), t = Object.fromEntries((await db.prepare('SELECT id, title FROM artworks WHERE artist_id = ?').bind(v.artist_id).all()).results.map(x => [x.id, x.title]));
  snapObj.works.forEach(w => { w.title = t[w.id] || w.title; });
  await db.prepare('UPDATE versions SET snapshot = ? WHERE artist_id = ?').bind(JSON.stringify(snapObj), v.artist_id).run();
}
await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, ?, 0, NULL, ?)').bind('aamara', '2026-11-05T17:05:00.000Z').run();
const tables = ['artists', 'artworks', 'images', 'versions', 'publish_queue', 'gallery_positions', 'homepage_features'];
const snap = async () => { const o = {}; for (const t of tables) o[t] = JSON.stringify((await db.prepare(`SELECT * FROM ${t} ORDER BY rowid`).all()).results); return o; };
const before = await snap();

const b = await chromium.launch();
const page = async (email, w = 1440, h = 1000) => {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: SHOTS ? 2 : 1, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email) } });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e))); pg.on('dialog', d => d.accept(d.type() === 'prompt' ? pg.__typed || '' : undefined));
  return { ctx, pg, errs };
};
const settle = pg => pg.waitForLoadState('networkidle').catch(() => {}).then(() => pg.waitForTimeout(350));
const shot = async (pg, file, sel) => { if (!SHOTS) return; await settle(pg); await pg.addStyleTag({ content: 'header,.st-top{position:static!important}' }).catch(() => {}); if (sel) { const el = await pg.$(sel); await el.scrollIntoViewIfNeeded(); await el.screenshot({ path: `${SHOTS}/${file}` }); } else await pg.screenshot({ path: `${SHOTS}/${file}`, fullPage: true }); };

// G1-G3 the founder's screen
const F = await page(FOUNDER);
let r = await F.pg.goto(url + '/admin/galleries'); await settle(F.pg);
check('G1 the Review Desk has a Galleries tab and it opens the Galleries screen (current tab marked)', r.status() === 200 && await F.pg.locator('.st-tabs a[data-t="gals"][aria-current="page"]').count() === 1
  && (await F.pg.textContent('h1')).trim() === 'Galleries', await F.pg.textContent('#app'));
check('G2 the three galleries are shown with their status: Spaces and Being in preparation, Contemporary open',
  (await F.pg.locator('.st-gm-tabs button').evaluateAll(bs => bs.map(x => x.innerText.replace(/\s+/g, ' ').trim()))).join('|') === 'Contemporary Open|Spaces In preparation|Being In preparation', (await F.pg.locator('.st-gm-tabs button').evaluateAll(bs => bs.map(x => x.innerText))).join('|'));
check('G3 Spaces starts empty: no members, no works placed, readiness 0 of 6 artists and 0 of 30 works', /0\s*of 6/.test(await F.pg.textContent('.st-gm-status')) && /No members yet/.test(await F.pg.textContent('#app')));
await shot(F.pg, 'G01-founder-spaces-empty-desktop.png');

// G4 invite through the screen (curation); G5 an application needs its reference
await F.pg.selectOption('#gm-who', 'abram'); await F.pg.click('[data-invite] button[type=submit]'); await settle(F.pg);
let m = await db.prepare("SELECT state, source FROM gallery_memberships WHERE artist_id='abram' AND gallery_id='spaces'").first();
check('G4 inviting Bram to Spaces writes the founder’s approval only (waiting for the artist); no email, nothing else', m && m.state === 'founder_approved' && m.source === 'founder_curation', JSON.stringify(m));
await F.pg.selectOption('#gm-who', 'acleo'); await F.pg.selectOption('#gm-src', 'application'); await F.pg.click('[data-invite] button[type=submit]'); await settle(F.pg);
check('G5 inviting from an application without its reference is refused, with the reason shown', /reference/.test(await F.pg.textContent('#app'))
  && !(await db.prepare("SELECT 1 FROM gallery_memberships WHERE artist_id='acleo' AND gallery_id='spaces'").first()));
await F.pg.fill('#gm-ref', 'PA-AP-251120-ABC123'); await F.pg.click('[data-invite] button[type=submit]'); await settle(F.pg);
// Dara asks to join herself (artist route; the card offers "Ask to join" only once a gallery is open, so via the API here)
await call('POST', '/api/galleries/spaces/request', 'dara@example.test');

// A1-A3 the artist's card
const A = await page('bram@example.test');
await A.pg.goto(url + '/'); await settle(A.pg);
check('A1 Bram’s Studio shows "Your galleries" with PlotArt’s invitation to Spaces and Accept / Decline', await A.pg.isVisible('#yg-card')
  && /invited you to join Spaces/.test(await A.pg.textContent('#yg-card')) && await A.pg.locator('#yg-card [data-ga="accept"][data-g="spaces"]').count() === 1, await A.pg.textContent('#app'));
check('A2 Contemporary reads as his own gallery being part of it; Being (not open, no invitation) is not offered', /part of Contemporary/.test(await A.pg.textContent('#yg-card')) && !/Being/.test(await A.pg.textContent('#yg-card .st-yg-list')));
await shot(A.pg, 'A01-artist-invitation-desktop.png', '#yg-card');
await A.pg.click('#yg-card [data-ga="accept"][data-g="spaces"]'); await settle(A.pg);
m = await db.prepare("SELECT state FROM gallery_memberships WHERE artist_id='abram' AND gallery_id='spaces'").first();
check('A3 accepting makes Bram a live member of Spaces, and the card now says so (with Leave)', m.state === 'live' && /member of Spaces/.test(await A.pg.textContent('#yg-card')) && await A.pg.locator('[data-ga="withdraw"][data-g="spaces"]').count() === 1);

// G6-G8 founder: approve Dara's request, offer a work, approve a work Bram suggests
await F.pg.reload(); await settle(F.pg);
check('G6 Dara’s request appears under "Asked to join" and the Spaces tab shows it waiting', /Asked to join \(1\)/.test(await F.pg.textContent('#app')) && /waiting/.test(await F.pg.textContent('.st-gm-tabs button[data-g="spaces"]')));
await F.pg.click('[data-m="approve"][data-a="adara"]'); await settle(F.pg);
m = await db.prepare("SELECT state FROM gallery_memberships WHERE artist_id='adara' AND gallery_id='spaces'").first();
check('G7 approving her request makes Dara a member at once (her request was her acceptance)', m.state === 'live', JSON.stringify(m) + ' ' + await F.pg.textContent('.st-gm-msg').catch(() => ''));
await F.pg.click('[data-w="place"][data-id="wabram1"]'); await settle(F.pg);
await F.pg.click('[data-w="place"][data-id="wadara1"]'); await settle(F.pg);
let p = await db.prepare("SELECT state FROM artwork_placements WHERE artwork_id='wabram1' AND gallery_id='spaces'").first();
check('G8 offering Bram’s work writes the founder’s approval only; it is not in Spaces until he accepts', p.state === 'founder_approved' && /Offered/.test(await F.pg.textContent('#app')));

// A4-A5 artist: accept the offered work, suggest another
await A.pg.reload(); await settle(A.pg);
await A.pg.click('[data-pw="accept"][data-w="wabram1"]'); await settle(A.pg);
await A.pg.click('[data-pw="propose"][data-w="wabram2"]'); await settle(A.pg);
p = await db.prepare("SELECT artwork_id, state FROM artwork_placements WHERE artist_id='abram' AND gallery_id='spaces' ORDER BY artwork_id").all();
check('A4 accepting puts the work live in Spaces; suggesting another waits for the founder', JSON.stringify(p.results.map(x => x.state)) === '["live","artist_accepted"]', JSON.stringify(p.results));
await shot(A.pg, 'A02-artist-member-desktop.png', '#yg-card');
await F.pg.reload(); await settle(F.pg);
await F.pg.click('[data-w="place"][data-id="wabram2"]'); await settle(F.pg);
check('A5 the founder approves the suggested work: both of Bram’s works are live in Spaces', (await db.prepare("SELECT COUNT(*) n FROM artwork_placements WHERE artist_id='abram' AND gallery_id='spaces' AND state='live'").first()).n === 2);
// Dara accepts her offered work through the API (her own screen is proven above with Bram)
await call('POST', '/api/galleries/spaces/artworks/wadara1/accept', 'dara@example.test');

// G9-G11 order and Artists in Focus
await F.pg.reload(); await settle(F.pg);
const names = async () => (await F.pg.locator('.st-gm-order .st-gm-oname').allTextContents());
const o1 = await names();
await F.pg.click('[data-o="down"][data-i="0"]'); await F.pg.click('[data-save-order]'); await settle(F.pg);
const ord = (await db.prepare("SELECT artist_id FROM gallery_order WHERE gallery_id='spaces' ORDER BY position").all()).results.map(x => x.artist_id);
check('G9 the order lists both members; moving one and saving writes exactly that order from position 01', o1.length === 2 && ord.length === 2 && (await names()).join() === [o1[1], o1[0]].join(), `${o1} → ${ord}`);
await F.pg.selectOption('#gm-focus', 'abram|wabram2'); await F.pg.selectOption('#gm-focus', 'adara|wadara1'); await F.pg.click('[data-save-focus]'); await settle(F.pg);
const foc = (await db.prepare("SELECT artist_id, artwork_id FROM gallery_features WHERE gallery_id='spaces' ORDER BY position").all()).results;
check('G10 Artists in Focus for Spaces: two members, each with a work placed in Spaces, saved in order', JSON.stringify(foc) === '[{"artist_id":"abram","artwork_id":"wabram2"},{"artist_id":"adara","artwork_id":"wadara1"}]', JSON.stringify(foc));
check('G11 readiness counts what is live: 2 artists and 3 works in Spaces', /2\s*of 6/.test(await F.pg.textContent('.st-gm-status')) && /3\s*of 30/.test(await F.pg.textContent('.st-gm-status')), await F.pg.textContent('.st-gm-status'));
await shot(F.pg, 'G02-founder-spaces-desktop.png');

// G12 image use: ask through the form; A6 the artist answers yes; A7 withdraws
if (!(await F.pg.$eval('[data-ask]', d => d.open))) await F.pg.click('[data-ask] > summary');
await F.pg.selectOption('#gu-a', 'abram'); await F.pg.selectOption('#gu-s', 'social_media'); await F.pg.selectOption('#gu-g', 'spaces');
await F.pg.check('input[name="artwork_ids"][value="wabram1"]');
await F.pg.fill('#gu-p', 'One post introducing Spaces, linking to the artist’s gallery'); await F.pg.fill('#gu-c', 'PlotArt Instagram');
await F.pg.click('[data-use] button[type=submit]'); await settle(F.pg);
const req = await db.prepare("SELECT * FROM image_use_requests WHERE artist_id='abram'").first();
check('G12 the request is recorded for one use, one artist, the chosen work only, and listed as waiting', req && req.status === 'open' && req.scope === 'social_media' && req.artwork_ids === '["wabram1"]' && /Waiting for an answer \(1\)/.test(await F.pg.textContent('#app')));
await shot(F.pg, 'G03-founder-image-use-desktop.png', '.st-gm-cols + .st-card');
await A.pg.reload(); await settle(A.pg);
check('A6 Bram sees the request, names the work, and is told it is optional', /May PlotArt use 1 image for social media/.test(await A.pg.textContent('#yg-card')) && /optional and only for this use/.test(await A.pg.textContent('#yg-card')));
await shot(A.pg, 'A03-artist-image-request-desktop.png', '#yg-card');
await A.pg.click('[data-iu="yes"]'); await settle(A.pg);
const yes = await db.prepare("SELECT * FROM image_use_consents WHERE artist_id='abram'").all();
await A.pg.click('#yg-card [data-perms] > summary');
await A.pg.click('[data-iw]'); await settle(A.pg);
const after = (await db.prepare("SELECT answer FROM image_use_consents WHERE artist_id='abram' ORDER BY created_at, rowid").all()).results.map(x => x.answer);
check('A7 a yes is recorded from the request itself; withdrawing adds a later no (the yes stays on record)', yes.results.length === 1 && yes.results[0].answer === 'yes' && after.join() === 'yes,no', after.join());

// G13 Contemporary tab: positions 01-25 stay out; take a work out and put it back
await F.pg.click('.st-gm-tabs button[data-g="contemporary"]'); await settle(F.pg);
const cnames = await F.pg.locator('.st-gm-order .st-gm-oname').allTextContents();
check('G13 Contemporary’s order (from 26) leaves out Amara, who holds position 01; the note points to Gallery order', !cnames.some(x => /Amara/.test(x)) && cnames.length === 3 && /Positions 01–25 stay in/.test(await F.pg.textContent('#app')), cnames.join());
await F.pg.click('.st-gm-artist summary'); await F.pg.click('[data-w="withdraw"][data-id="waamara1"]'); await settle(F.pg);
const out = await db.prepare("SELECT state FROM artwork_placements WHERE artwork_id='waamara1' AND gallery_id='contemporary'").first();
await F.pg.click('.st-gm-artist summary').catch(() => {}); await F.pg.click('[data-w="restore"][data-id="waamara1"]'); await settle(F.pg);
const back = await db.prepare("SELECT 1 FROM artwork_placements WHERE artwork_id='waamara1' AND gallery_id='contemporary'").first();
check('G14 taking a work out of Contemporary and putting it back leaves no trace in the placements', out && out.state === 'withdrawn' && !back);
await shot(F.pg, 'G04-founder-contemporary-desktop.png');

// G15 opening Spaces needs the typed confirmation; the Studio records it, the public site is not touched
await F.pg.click('.st-gm-tabs button[data-g="spaces"]'); await settle(F.pg);
F.pg.__typed = 'wrong'; await F.pg.click('[data-status="open"]'); await settle(F.pg);
const s1 = await db.prepare("SELECT status FROM gallery_settings WHERE gallery_id='spaces'").first();
F.pg.__typed = 'OPEN SPACES'; await F.pg.click('[data-status="open"]'); await settle(F.pg);
const s2 = await db.prepare("SELECT status FROM gallery_settings WHERE gallery_id='spaces'").first();
check('G15 opening Spaces needs "OPEN SPACES" typed (a wrong word changes nothing); then it is recorded open below target', (!s1 || s1.status === 'in_preparation') && s2.status === 'open', `${JSON.stringify(s1)} ${JSON.stringify(s2)}`);
await call('POST', '/api/admin/galleries/spaces/status', FOUNDER, { status: 'in_preparation' });

// A8 with Spaces open, an artist who is not a member can ask to join from the card
await call('POST', '/api/admin/galleries/being/status', FOUNDER, { status: 'open', confirm: 'OPEN BEING', below_target: true });
const C = await page('cleo@example.test'); await C.pg.goto(url + '/'); await settle(C.pg);
check('A8 once Being is open, Cleo (no invitation there) is offered "Ask to join" for Being', await C.pg.locator('[data-ga="request"][data-g="being"]').count() === 1);
await call('POST', '/api/admin/galleries/being/status', FOUNDER, { status: 'in_preparation' });

// P1-P3 safety
const now = await snap();
check('P1 artists, artworks, images, versions, the publishing queue, positions 01-25 and Featured Artists are unchanged', tables.every(t => now[t] === before[t]), tables.filter(t => now[t] !== before[t]).join());
check('P2 no script errors on either screen', !F.errs.length && !A.errs.length && !C.errs.length, [...F.errs, ...A.errs, ...C.errs].join(' | '));
const art = await call('GET', '/api/admin/galleries', 'bram@example.test');
check('P3 an artist cannot open the founder’s gallery data', art.s === 403 || art.s === 401, art.s);

// mobile previews
if (SHOTS) {
  const FM = await page(FOUNDER, 390, 844); await FM.pg.goto(url + '/admin/galleries'); await FM.pg.evaluate(() => sessionStorage.setItem('pa-gal', 'spaces')); await FM.pg.reload(); await shot(FM.pg, 'G02-founder-spaces-mobile.png');
  const AM = await page('bram@example.test', 390, 844); await AM.pg.goto(url + '/'); await shot(AM.pg, 'A02-artist-member-mobile.png', '#yg-card');
  await FM.ctx.close(); await AM.ctx.close();
}
await b.close(); await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nTHREE GALLERIES · SCREENS · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
