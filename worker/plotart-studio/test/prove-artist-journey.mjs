// PROVE · PlotArt Studio · the whole artist journey, in a real browser (founder brief 18 Nov 2026, "Artist Studio experience
// audit"). Synthetic artists only; the real Worker runs locally (Miniflare/workerd) with a local D1 and R2; nothing here
// touches Cloudflare, sends email or publishes anything (the publishing pipeline is simulated through its own endpoints).
//   node test/prove-artist-journey.mjs [--shots DIR]
// N-checks: a new artist from first sign-in to a live gallery. P-checks: a published artist returning to edit, including
// the regression for Lena Fawaz's report (two words changed in the biography; Review and submit appeared to show the old
// text). M-checks: phone layout.
import { acceptAgreement } from './agree.mjs';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { execFileSync } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { chromium } from 'playwright';

const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const shot = async (pg, name, full = true) => { if (SHOTS) await pg.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: full }); };
console.log('PROVE · PlotArt Studio · artist journey');

const TMP = mkdtempSync(join(tmpdir(), 'pa-journey-'));
execFileSync('python3', ['-c', `
import sys, random
from PIL import Image, ImageDraw
r = random.Random(11); im = Image.new("RGB", (2400, 3000), (70, 90, 120)); d = ImageDraw.Draw(im)
for _ in range(30):
    x, y = r.randrange(2400), r.randrange(3000); d.rectangle((x, y, x + 600, y + 500), outline=tuple(r.randrange(256) for _ in range(3)), width=20)
im.save(sys.argv[1] + "/painting.jpg", "JPEG", quality=88)
`, TMP]);

const { mf, url, db } = await start({ port: 8840 });
const call = async (method, path, who, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' }; if (who) h['Cf-Access-Jwt-Assertion'] = token(who);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
};
const pipe = (method, path, body) => mf.dispatchFetch(url + path, { method, headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN, 'Content-Type': 'application/json' }, body: body && JSON.stringify(body) }).then(r => r.json());
const one = (sql, ...b) => db.prepare(sql).bind(...b).first();
const all = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
const browser = await chromium.launch();
const open = async (email, w = 1280, h = 900) => {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email, { exp: 3600 }) } });
  const pg = await ctx.newPage(); pg.errs = []; pg.on('pageerror', e => pg.errs.push(String(e))); return pg;
};
const savedAll = pg => pg.waitForFunction(() => /^All changes saved/.test(document.querySelector('#sb-state')?.textContent || ''), null, { timeout: 10000 });
async function approveAndPublish(artistId) {
  const sid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(x => x.artist_id === artistId).id;
  await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve' });
  const q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === artistId && x.status === 'awaiting_founder');
  if (q) await call('POST', `/api/admin/queue/${q.id}/publish`, FOUNDER, {});
  const qq = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === artistId);
  await pipe('POST', `/api/pipeline/export/${qq.id}`); await pipe('POST', `/api/pipeline/result/${qq.id}`, { status: 'published', detail: 'test' });
  return sid;
}

/* ------------------------------------------------------------------ a new artist, first sign-in to live gallery */
const NEW = 'niamh@example.test';
const nid = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Niamh Test', email: NEW, founding: true })).j.id;
await acceptAgreement(mf, url, NEW);
const n = await open(NEW);
await n.goto(url + '/#/'); await n.waitForSelector('.st-h1');
const d0 = await n.textContent('main, #app, body');
check('N1 first sign-in: the gallery page says nothing is published yet and lists what to complete', /Not published yet/.test(d0) && /Your gallery checklist/.test(d0), d0.slice(0, 200));
await shot(n, 'journey-01-first-sign-in');

await n.goto(url + '/#/profile'); await n.waitForSelector('#sb-state');
await n.fill('#f-practice', 'Painter');
await n.selectOption('#f-medium', 'painting').catch(() => {});
await n.fill('#f-bio', 'Niamh paints the bogs of Offaly in layered oils, working from small studies made outdoors through the year.');
await savedAll(n);
const nb = await one('SELECT practice, bio FROM artists WHERE id=?', nid);
check('N2 profile: typing saves by itself; the bar says "Saved privately in your Studio"', nb.practice === 'Painter' && /^Niamh paints/.test(nb.bio) && /^Saved privately in your Studio/.test(await n.textContent('#sb-next')), JSON.stringify(nb));

await n.goto(url + '/#/'); await n.waitForSelector('[data-act=add]');
await n.click('[data-act=add]'); await n.waitForSelector('#mdrop');
const drafts = (await all('SELECT id FROM artworks WHERE artist_id=?', nid)).length;
check('N3 "Add an artwork" opens one new artwork (no duplicate drafts)', drafts === 1, drafts);
await n.setInputFiles('#mdrop input[type=file]', join(TMP, 'painting.jpg'));
await n.waitForFunction(() => !!document.querySelector('#mdrop img'), null, { timeout: 20000 });
const im = await one("SELECT width, height, role FROM images WHERE artist_id=? AND role='main'", nid);
check('N4 the main photograph uploads from the artwork page and shows straight away', im && im.width === 2400 && im.height === 3000, JSON.stringify(im));
await n.fill('[data-img] input[name=alt]', 'A layered oil painting of a bog under a grey sky');
await n.check('[data-img] input[type=radio][value=self]');
for (const [k, v] of [['#f-title', 'Bog Light'], ['#f-year', '2026'], ['#f-medium', 'Oil on linen'], ['#f-h_cm', '60'], ['#f-w_cm', '80'], ['#f-price_eur', '1200']]) await n.fill(k, v);
await n.check('input[name=ai_involvement][value=none]').catch(() => {});
await savedAll(n); await n.waitForTimeout(800);
const nw = await one('SELECT title, price_eur, h_cm, w_cm, ai_involvement FROM artworks WHERE artist_id=?', nid);
check('N5 artwork details and price save as typed', nw.title === 'Bog Light' && Number(nw.price_eur) === 1200 && Number(nw.w_cm) === 80, JSON.stringify(nw));
await shot(n, 'journey-02-artwork-saved');

const pv = await n.context().newPage(); await pv.goto(url + '/preview/'); const pvt = await pv.textContent('body');
check('N6 the preview shows the saved profile and says it is a private preview of saved changes, not the live gallery', /Niamh paints the bogs/.test(pvt) && /not your live gallery/.test(pvt), pvt.slice(0, 160));
await pv.close();

await n.goto(url + '/#/submit'); await n.waitForSelector('#go');
const sv = await n.textContent('body');
check('N7 Review and submit: the first publication is listed, "What happens next" explains the review, and Submit is available', /First publication of your gallery/.test(sv) && /What happens next/.test(sv) && await n.isEnabled('#go'), sv.slice(0, 300));
await shot(n, 'journey-03-review-and-submit');
await n.click('#go'); await n.waitForFunction(() => document.querySelector('.st-status h2')?.textContent === 'Submitted for review', null, { timeout: 8000 });
const done = await n.textContent('.st-status');
check('N8 after submitting: a clear confirmation ("Submitted for review"), what happens next, nothing else to do', /Submitted for review/.test(done) && /nothing else you need to do/.test(done), done);
await shot(n, 'journey-04-submitted');
const sub = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(x => x.artist_id === nid);
check('N9 the founder Review Desk receives the submission', !!sub);
await approveAndPublish(nid);
await n.goto(url + '/#/'); await n.reload(); await n.waitForSelector('.st-status h2');
check('N10 after approval and publication the gallery page says "Live on plotnua.ie" with the address', (await n.textContent('.st-status h2')) === 'Live on plotnua.ie' && /plotnua\.ie\/plotart\/artists\//.test(await n.textContent('.st-status')),
  JSON.stringify([await n.textContent('.st-status'), await all('SELECT status, kind FROM publish_queue WHERE artist_id=?', nid), await all('SELECT status FROM submissions WHERE artist_id=?', nid)]));

/* ------------------------------------------------------------------ a published artist returns to edit (Lena's case) */
const LIVE = 'lena-like@example.test';
await seedPublished(db, { id: 'alive', slug: 'live-test', email: LIVE, name: 'Lia Test', works: 1, number: 4, licence: null, bucket: await mf.getR2Bucket('IMAGES', 'studio') });
const BIO1 = 'Lia is an emerging abstract artist based in Dublin. She cherishes her practice as a chance to reflect on life and let her inner child take the stage. With a love for bold colours, shapes and marks, she likes to layer her paints and use various scratching techniques to create unique textures.';
const BIO2 = BIO1.replace('reflect on life and let her inner child', 'reflect on life where she lets her inner child').replace('layer her paints and use various', 'layer her paints and uses various');
await db.prepare('UPDATE artists SET bio=? WHERE id=?').bind(BIO1, 'alive').run();
await db.prepare("UPDATE versions SET snapshot=json_set(snapshot, '$.artist.bio', ?) WHERE artist_id='alive'").bind(BIO1).run();
{ const r = await acceptAgreement(mf, url, LIVE, { legal_name: 'Lia Test' }); if (r.s !== 200) console.log('    (agree)', r.s, JSON.stringify(r.j)); }
const liveBefore = JSON.stringify(await all('SELECT version, snapshot FROM versions WHERE artist_id=?', 'alive'));
const p = await open(LIVE);
await p.goto(url + '/#/profile'); await p.waitForSelector('#f-bio');
await p.fill('#f-bio', BIO2);
await p.click('#sb-submit:not([hidden]), .st-tabs a[href="#/"]').catch(() => {});
await p.goto(url + '/#/submit');            // straight to Review and submit, without waiting for the save
await p.waitForSelector('#go');
const ch = await p.innerHTML('.st-changes');
const ins = await p.$$eval('.st-changes ins', e => e.map(x => x.textContent.trim())), del = await p.$$eval('.st-changes del', e => e.map(x => x.textContent.trim()));
check('P1 regression (Lena): edit the biography and go straight to Review and submit: the edit is saved first, and the page shows exactly the changed words (struck through and added), not the whole old biography first',
  (await one('SELECT bio FROM artists WHERE id=?', 'alive')).bio === BIO2 && ins.join(' ').includes('where she lets') && ins.join(' ').includes('uses') && del.join(' ').includes('let') &&
  !ch.includes(BIO1.slice(0, 120)) && /Profile · biography/.test(await p.textContent('.st-changes')), JSON.stringify({ ins, del }));
await shot(p, 'journey-05-lena-regression-review-and-submit');
const pv2 = await p.context().newPage(); await pv2.goto(url + '/preview/');
check('P2 the preview opened from Review and submit shows the new wording (the saved version that will be submitted)', (await pv2.textContent('body')).includes('where she lets her inner child')); await pv2.close();
await p.click('#go'); await p.waitForFunction(() => document.querySelector('.st-status h2')?.textContent === 'Submitted for review');
const s2 = await one("SELECT id, snapshot FROM submissions WHERE artist_id='alive' ORDER BY created_at DESC LIMIT 1");
const snapBio = s2 && (JSON.parse(s2.snapshot || '{}').artist || {}).bio;
const adminSub = await call('GET', `/api/admin/submissions/${s2.id}`, FOUNDER);
check('P3 the submission (what the founder reviews) contains the new biography exactly', (snapBio || (adminSub.j.artist || {}).bio) === BIO2, String(snapBio).slice(0, 80));
check('P4 nothing is public before approval: the published version is unchanged', JSON.stringify(await all('SELECT version, snapshot FROM versions WHERE artist_id=?', 'alive')) === liveBefore);
await p.goto(url + '/#/submit'); await p.reload(); await p.waitForSelector('#go');
const why = await p.textContent('#why').catch(() => '');
check('R1 with nothing new since submitting, Submit is unavailable and the page says everything saved is already in the submission (no needless resubmission)',
  !(await p.isEnabled('#go')) && /already in your submission/.test(why), why);
await p.goto(url + '/#/profile'); await p.waitForSelector('#f-statement'); await p.fill('#f-statement', 'Bold colour, scratched surfaces.'); await savedAll(p);
const nx = await p.innerText('#sb-next'), sbtn = await p.textContent('#sb-submit');
await p.goto(url + '/#/'); await p.waitForSelector('.st-status'); const dash = await p.textContent('.st-status');
check('R2 a change saved after submitting is called out as NOT in the submission, with "Submit again (1)"',
  /1 change saved since then isn’t included: submit again to add it\./.test(nx) && sbtn === 'Submit again (1)' && /1 saved change not submitted yet\. Made since your submission/.test(dash), nx + ' | ' + sbtn + ' | ' + dash);
await p.goto(url + '/#/submit'); await p.waitForSelector('#go'); await p.click('#go'); await p.waitForFunction(() => document.querySelector('.st-status h2')?.textContent === 'Submitted for review');
const s3 = await one("SELECT id, snapshot FROM submissions WHERE artist_id='alive' AND status='pending'");
const olds = await all("SELECT status FROM submissions WHERE artist_id='alive' ORDER BY created_at");
check('R3 submitting again replaces the earlier submission (one pending, with both changes)', JSON.parse(s3.snapshot).artist.bio === BIO2 && JSON.parse(s3.snapshot).artist.statement === 'Bold colour, scratched surfaces.' && olds.filter(x => x.status === 'pending').length === 1, JSON.stringify(olds));
const f = await open(FOUNDER); await f.goto(url + `/admin/submission/${s2.id}`).catch(() => {});
await f.goto(url + '/admin'); await f.waitForTimeout(900);
const link = await f.$(`a[href*="${s3.id}"]`); if (link) { await link.click(); await f.waitForTimeout(900); }
const fins = await f.$$eval('.st-diff ins', e => e.map(x => x.textContent.trim()));
check('P5 the founder Review Desk shows the same changed words for this submission', fins.join(' ').includes('where she lets'), JSON.stringify(fins));
await shot(f, 'journey-06-founder-review');
await approveAndPublish('alive');
const pub = await all('SELECT snapshot FROM versions WHERE artist_id=? ORDER BY version DESC LIMIT 1', 'alive');
check('P6 after approval, the published version carries the new biography', JSON.parse(pub[0].snapshot).artist.bio === BIO2);

// returning later: a price change (quick check) and availability (straight away)
const wid = (await one("SELECT id FROM artworks WHERE artist_id='alive'")).id;
await p.goto(url + `/#/work/${wid}`); await p.waitForSelector('#f-price_eur');
await p.fill('#f-price_eur', '1050'); await savedAll(p);
await p.selectOption('#av', 'reserved'); await p.waitForTimeout(900);
await p.goto(url + '/#/'); await p.waitForSelector('.st-status');
const pend = await p.textContent('.st-status');
check('P7 the gallery page says a saved change is not submitted yet and is not on the public gallery', /1 saved change not submitted yet/.test(pend) && /aren’t on your public gallery/.test(pend), pend);
await p.goto(url + '/#/submit'); await p.waitForSelector('#go');
const st = await p.textContent('.st-changes, section.st-card');
const all2 = await p.textContent('body');
const inst = await all("SELECT kind FROM publish_queue WHERE artist_id='alive' AND kind='instant'");
check('P8 the new price is listed as "600 → 1050" for a quick check; the availability change is not waiting for review (it went to the live gallery straight away)',
  /Quick check/.test(all2) && /600\s*→\s*1050/.test(all2) && !/available → reserved/.test(all2) && inst.length >= 1, JSON.stringify(all2.replace(/\s+/g, ' ').slice(0, 600)));
await shot(p, 'journey-07-price-and-availability');
// adding an artwork to a live gallery: listed as new, for review
await p.goto(url + '/#/'); await p.click('[data-act=add]'); await p.waitForSelector('#f-title');
await p.fill('#f-title', 'New Piece'); await savedAll(p);
await p.goto(url + '/#/submit'); await p.waitForSelector('#go');
check('P9 a new artwork on a live gallery is listed for review', /New artwork: New Piece/.test(await p.textContent('body')));

/* ------------------------------------------------------------------ phone */
const m = await open(LIVE, 390, 844);
for (const [path, name] of [['/#/', 'gallery'], ['/#/submit', 'submit'], ['/#/profile', 'profile']]) {
  await m.goto(url + path); await m.waitForSelector('.st-h1'); await m.waitForTimeout(400);
  const o = await m.evaluate(() => ({ over: document.documentElement.scrollWidth - innerWidth, hidden: [...document.querySelectorAll('button, a.st-btn')].filter(b => b.offsetParent && b.getBoundingClientRect().right > innerWidth + 1).map(b => b.textContent.trim()) }));
  check(`M ${name} page on a phone: no sideways scrolling, every button within the screen`, o.over === 0 && !o.hidden.length, JSON.stringify(o));
  await shot(m, `journey-mobile-${name}`);
}
check('X no script errors anywhere', ![n, p, f, m].some(x => x.errs.length), JSON.stringify([n.errs, p.errs, f.errs, m.errs]));

await browser.close(); await mf.dispose();
console.log(`\nPLOTART ARTIST JOURNEY · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exit(results.every(Boolean) ? 0 : 1);
