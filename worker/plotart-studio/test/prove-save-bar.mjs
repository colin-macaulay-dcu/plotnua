// PROVE · PlotArt Studio · saving made visible (18 Nov 2026, founder brief after Lena Fawaz's report: "I can edit my
// biography and prices but can't find a way to save"). Synthetic artists only; the Worker runs locally (Miniflare/workerd)
// with a local D1. Nothing here touches Cloudflare.
//   node test/prove-save-bar.mjs [--shots DIR]
// S1 reproduces the report with the Studio as released: no Save control on the Profile page, and an edit typed into the
// biography is lost if the artist closes the page without first leaving the field.
// The rest proves the correction, for a published artist and a new one: typing saves by itself, "Save changes" saves
// immediately, leaving or closing with unsaved text is guarded, the bar says what is saved and what happens next, saving
// never publishes (the published version and publish queue are untouched), and availability still updates straight away.
import { execFileSync } from 'node:child_process';
import { cpSync, rmSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('../', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const shots = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
console.log('PROVE · PlotArt Studio · saving made visible');

const CONTRAST = `(el => { const L = c => { const [r, g, b] = c.match(/[\\d.]+/g).slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * b; };
  let bg = 'rgb(35, 36, 39)'; for (let n = el; n; n = n.parentElement) { const c = getComputedStyle(n).backgroundColor; if (c && !/rgba\\(.*, 0\\)$|transparent/.test(c)) { bg = c; break; } }
  const s = getComputedStyle(el), x = L(s.color), y = L(bg), o = +s.opacity; return o < 1 ? 0 : (Math.max(x, y) + .05) / (Math.min(x, y) + .05); })`;
const LIVE = 'lena@example.test', NEW = 'nora@example.test', T = '2026-11-18T07:00:00.000Z';
const BIO = 'I paint the coast of Clare in oils, working outdoors in every season and finishing each canvas in my studio in Ennis.';

async function scenario(label, opts) {
  const { mf, url, db } = await start({ port: opts.port, ...(opts.script ? { script: opts.script } : {}) });
  const IMAGES = await mf.getR2Bucket('IMAGES', 'studio');
  await seedPublished(db, { id: 'alen', slug: 'len-test', email: LIVE, name: 'Len Test', works: 2, number: 3, bucket: IMAGES });
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('anor','nor-test',?,'Nor Test',1,'active',?,?)`).bind(NEW, T, T).run();
  const browser = await chromium.launch();
  const page = async (email, w = 1280) => {
    const ctx = await browser.newContext({ viewport: { width: w, height: 900 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email, { exp: 3600 }) } });
    const pg = await ctx.newPage(); pg.on('pageerror', e => (pg.errs = pg.errs || []).push(String(e)));
    return pg;
  };
  const bio = async id => (await db.prepare('SELECT bio FROM artists WHERE id=?').bind(id).first()).bio;
  return { mf, url, db, browser, page, bio, done: async () => { await browser.close(); await mf.dispose(); } };
}

// S1 as released (main's UI bundle)
{
  // the Studio as it was before the save bar (84b025f, live until 18 Nov 2026): that UI bundle with today's server code
  rmSync(HERE + '.oldsrc', { recursive: true, force: true }); cpSync(HERE + 'src', HERE + '.oldsrc', { recursive: true });
  writeFileSync(HERE + '.oldsrc/assets.js', execFileSync('git', ['show', '84b025f:worker/plotart-studio/src/assets.js'], { cwd: HERE }));
  const S = await scenario('released', { port: 8821, script: '.oldsrc/index.js' });
  const pg = await S.page(LIVE);
  await pg.goto(S.url + '/#/profile'); await pg.waitForSelector('#f-bio');
  const hasSaveNow = await pg.locator('button', { hasText: /save/i }).count();
  await pg.fill('#f-bio', BIO);            // typed, never left
  await pg.waitForTimeout(2500);
  const kept = await S.bio('alen');
  check('S1 reproduces the report on the current Studio: the Profile page has no Save button, and a biography typed but not followed by leaving the field is not saved (closing the page loses it)',
    hasSaveNow === 0 && kept !== BIO, JSON.stringify({ hasSaveNow, kept: String(kept).slice(0, 40) }));
  await S.done(); rmSync(HERE + '.oldsrc', { recursive: true, force: true });
}

const S = await scenario('corrected', { port: 8822 });
const pubBefore = JSON.stringify((await S.db.prepare("SELECT artist_id, version, status, kind FROM publish_queue ORDER BY artist_id, version").all()).results);
const verBefore = JSON.stringify((await S.db.prepare("SELECT artist_id, version, snapshot FROM versions ORDER BY artist_id, version").all()).results);

// a published artist edits her biography
const pg = await S.page(LIVE);
await pg.goto(S.url + '/#/profile'); await pg.waitForSelector('#sb-state');
const t0 = (await pg.textContent('#sb-state')).trim(), n0 = (await pg.textContent('#sb-next')).trim();
check('S2 a published artist\'s Profile page shows the save bar: "All changes saved", "Your public gallery is up to date", a Save button and Preview',
  t0.startsWith('All changes saved') && n0 === 'Your public gallery is up to date.' && await pg.isVisible('#sb-save') && await pg.locator('.st-savebar a', { hasText: 'Preview' }).count() === 1, t0 + ' | ' + n0);
await pg.fill('#f-bio', BIO);
const typing = (await pg.textContent('#sb-state')).trim(), btnTyping = await pg.isEnabled('#sb-save');
await pg.waitForFunction(() => /^All changes saved · /.test(document.querySelector('#sb-state').textContent), null, { timeout: 8000 });
check('S3 typing shows "Unsaved changes" with an active "Save changes" button, then saves by itself a moment after typing stops (no need to leave the field)',
  typing === 'Unsaved changes' && btnTyping && await S.bio('alen') === BIO && !(await pg.isEnabled('#sb-save')), typing);
const n1 = (await pg.innerText('#sb-next')).trim(), sub1 = await pg.textContent('#sb-submit');
check('S4 the bar then says (approved wording): "Your changes are saved in your Studio but are not yet visible on your public gallery. Select Review and submit when you’re ready for PlotArt to approve and publish them.", and offers "Review and submit (1)"',
  n1 === 'Your changes are saved in your Studio but are not yet visible on your public gallery. Select Review and submit when you’re ready for PlotArt to approve and publish them.' && await pg.isVisible('#sb-submit') && sub1 === 'Review and submit (1)', n1 + ' | ' + sub1);
const pubAfter = JSON.stringify((await S.db.prepare("SELECT artist_id, version, status, kind FROM publish_queue ORDER BY artist_id, version").all()).results);
const verAfter = JSON.stringify((await S.db.prepare("SELECT artist_id, version, snapshot FROM versions ORDER BY artist_id, version").all()).results);
check('S5 saving publishes nothing: the published version and the publishing queue are unchanged (founder review still required)', pubAfter === pubBefore && verAfter === verBefore);

// the "Save changes" button saves at once; leaving with unsaved text is guarded
await pg.fill('#f-statement', 'Light on water, in oil.');
await pg.click('#sb-save');
await pg.waitForFunction(() => /^All changes saved/.test(document.querySelector('#sb-state').textContent), null, { timeout: 4000 });
const st = (await S.db.prepare("SELECT statement FROM artists WHERE id='alen'").first()).statement;
check('S6 "Save changes" saves immediately', st === 'Light on water, in oil.', st);
await pg.fill('#f-practice', 'Painter of the Clare coast');
let dialog = null; pg.on('dialog', async d => { dialog = d.type(); await d.dismiss(); });
await pg.evaluate(() => { const e = new Event('beforeunload', { cancelable: true }); dispatchEvent(e); window.__blocked = e.defaultPrevented; });
check('S7 closing or reloading with typed-but-unsaved text is guarded (the browser asks before leaving)', await pg.evaluate(() => window.__blocked) === true);
await pg.click('.st-tabs a[href="#/works"]'); await pg.waitForSelector('.st-h1');
await pg.waitForTimeout(600);
check('S8 moving to another Studio page saves what was typed first', (await S.db.prepare("SELECT practice FROM artists WHERE id='alen'").first()).practice === 'Painter of the Clare coast');

// a too-short biography is not saved and the bar says why
await pg.goto(S.url + '/#/profile'); await pg.waitForSelector('#sb-state');
await pg.fill('#f-bio', 'Too short.'); await pg.click('#sb-save'); await pg.waitForTimeout(800);
const bad = (await pg.textContent('#sb-state')).trim(), err = (await pg.textContent('#f-bio ~ .st-err')).trim();
check('S9 a change the Studio refuses is never shown as saved: the bar says "Not saved" with the reason, the field shows it, and the saved biography is unchanged',
  bad.startsWith('Not saved:') && err.length > 0 && await S.bio('alen') === BIO, bad + ' | ' + err);

// artwork page: price
const wid = (await S.db.prepare("SELECT id FROM artworks WHERE artist_id='alen' ORDER BY ord LIMIT 1").first()).id;
await pg.goto(S.url + `/#/work/${wid}`); await pg.waitForSelector('#sb-state');
await pg.fill('#f-price_eur', '1450');
await pg.waitForFunction(() => /^All changes saved · /.test(document.querySelector('#sb-state').textContent), null, { timeout: 8000 });
const price = (await S.db.prepare('SELECT price_eur FROM artworks WHERE id=?').bind(wid).first()).price_eur;
const n2 = (await pg.innerText('#sb-next')).trim();
check('S10 on an artwork page, a new price saves by itself and the bar counts it as a change waiting to be submitted (now 3: biography, statement and price; practice too)',
  Number(price) === 1450 && n2 === 'Your changes are saved in your Studio but are not yet visible on your public gallery. Select Review and submit when you’re ready for PlotArt to approve and publish them.' && /Review and submit \(\d+\)/.test(await pg.textContent('#sb-submit')), n2);
const sub = await pg.locator('.st-savebar a', { hasText: 'Done' }).count();
check('S11 the artwork page keeps Preview and Done beside the save controls', sub === 1 && await pg.locator('.st-savebar a', { hasText: 'Preview' }).count() === 1);
const avBefore = JSON.stringify((await S.db.prepare("SELECT status, kind FROM publish_queue WHERE artist_id='alen' ORDER BY version").all()).results);
await pg.selectOption('#av', 'sold'); await pg.waitForTimeout(800);
const avQueue = (await S.db.prepare("SELECT kind FROM publish_queue WHERE artist_id='alen' AND kind='instant'").all()).results.length;
check('S12 availability still updates the live gallery straight away (an instant publication, as before); content changes still wait for review',
  avQueue >= 1 && avBefore !== JSON.stringify((await S.db.prepare("SELECT status, kind FROM publish_queue WHERE artist_id='alen' ORDER BY version").all()).results));

// Review and submit from the bar opens the existing submission page (nothing submitted automatically)
await pg.goto(S.url + `/#/work/${wid}`); await pg.waitForSelector('#sb-submit:not([hidden])');
await pg.click('#sb-submit'); await pg.waitForSelector('#go');
const subs = (await S.db.prepare("SELECT COUNT(*) n FROM submissions WHERE artist_id='alen'").first()).n;
check('S13 "Review and submit" opens the existing submission page; nothing is submitted until the artist chooses "Submit for review"', subs === 0 && await pg.isVisible('#go'));
const mob = await S.page(LIVE, 390); await mob.goto(S.url + '/#/profile'); await mob.waitForSelector('#sb-state');
const mb = await mob.evaluate(() => { const b = document.querySelector('.st-savebar').getBoundingClientRect(); return { bottom: Math.round(b.bottom), vh: innerHeight, over: document.documentElement.scrollWidth - innerWidth }; });
const mshort = await mob.evaluate(() => { const l = document.querySelector('.st-sb-short'); return l ? getComputedStyle(l).display !== 'none' && getComputedStyle(document.querySelector('.st-sb-long')).display === 'none' && l.textContent : 'none'; });
check('S14b on a phone the bar uses the short wording', mshort === 'Saved in your Studio, not yet on your public gallery. Select Review and submit for PlotArt to approve and publish them.', mshort);
check('S14 on a phone the bar stays at the foot of the screen with no sideways scrolling', mb.bottom <= mb.vh && mb.bottom > mb.vh - 4 && mb.over === 0, JSON.stringify(mb));
if (shots) { await pg.goto(S.url + `/#/work/${wid}`); await pg.waitForSelector('#sb-state'); await pg.fill('#f-price_eur', '1500'); await pg.screenshot({ path: shots + '/save-bar-artwork-typing.png' });
  await pg.waitForFunction(() => /^All changes saved · /.test(document.querySelector('#sb-state').textContent)); await pg.screenshot({ path: shots + '/save-bar-artwork-saved.png' });
  await pg.goto(S.url + '/#/profile'); await pg.waitForSelector('#sb-state'); await pg.screenshot({ path: shots + '/save-bar-profile-desktop.png' });
  await mob.screenshot({ path: shots + '/save-bar-profile-mobile.png' }); }

// a new artist (never published)
const np = await S.page(NEW);
await np.goto(S.url + '/#/profile'); await np.waitForSelector('#sb-state');
await np.fill('#f-bio', BIO);
await np.waitForFunction(() => /^All changes saved · /.test(document.querySelector('#sb-state').textContent), null, { timeout: 8000 });
const nn = (await np.textContent('#sb-next')).trim();
check('S15 a new artist: typing saves by itself and the bar says it is saved privately until the gallery is submitted and reviewed',
  await S.bio('anor') === BIO && nn === 'Saved privately in your Studio. Submit your gallery when it’s ready: PlotArt reviews it before it goes live.', nn);
await pg.goto(S.url + `/#/work/${wid}`); await pg.waitForSelector('#sb-submit:not([hidden])');
const contrast = await pg.evaluate(() => { const L = c => { const [r, g, b] = c.match(/\d+/g).slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * b; };
  const a = document.querySelector('#sb-submit'), s = getComputedStyle(a), x = L(s.color), y = L(s.backgroundColor); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); });
check('S17 "Review and submit" is legible: text contrast at least 4.5:1 on its button (it was white on off-white, about 1.4:1)', contrast >= 4.5, contrast.toFixed(2));
// the Save button in each state: "Save changes" (unsaved), "Saved" (nothing to save)
await pg.goto(S.url + '/#/profile'); await pg.waitForSelector('#sb-save');
const cSaved = await pg.$eval('#sb-save', new Function('return ' + CONTRAST)()), lSaved = await pg.textContent('#sb-save');
await pg.fill('#f-statement', 'Light on water, in oil, again.');
const cUnsaved = await pg.$eval('#sb-save', new Function('return ' + CONTRAST)()), lUnsaved = await pg.textContent('#sb-save');
await pg.click('#sb-save'); await pg.waitForFunction(() => /^All changes saved/.test(document.querySelector('#sb-state').textContent));
const name = await pg.$eval('#sb-save', b => b.getAttribute('aria-label') || b.textContent);
check('S18 the Save button is readable in every state (contrast ≥ 4.5:1): "Saved" when nothing is waiting, "Save changes" when something is', cSaved >= 4.5 && cUnsaved >= 4.5 && lSaved === 'Saved' && lUnsaved === 'Save changes' && name === 'Saved', JSON.stringify({ cSaved, cUnsaved, lSaved, lUnsaved }));
// signing out and back in: a new browser session sees everything saved
const again = await S.page(LIVE); await again.goto(S.url + '/#/profile'); await again.waitForSelector('#f-bio');
check('S19 saved changes are still there after signing out and back in (a fresh session)', await again.inputValue('#f-bio') === BIO && await again.inputValue('#f-statement') === 'Light on water, in oil, again.' && await again.inputValue('#f-practice') === 'Painter of the Clare coast');
// the founder Review Desk: every solid button readable
const fd = await S.page(FOUNDER); await fd.goto(S.url + '/admin'); await fd.waitForSelector('.st-h1, h1'); await fd.waitForTimeout(800);
const desk = [];
for (const path of ['/admin', '/admin/applications', '/admin/agreements', '/admin/gallery', '/admin/featured', '/admin/hire', '/admin/opportunities', '/admin/leaving', '/admin/ideas', '/admin/garden']) { await fd.goto(S.url + path); await fd.waitForTimeout(900);
  desk.push(...await fd.$$eval('.st-btn--solid', (els, src) => els.filter(e => e.offsetParent).map(e => [location.pathname, e.textContent.trim().slice(0, 30), new Function('return ' + src)()(e)]), CONTRAST)); }
check('S20 the founder Review Desk: every visible solid button is readable (contrast ≥ 4.5:1, or a disabled one shown as such)', desk.length > 0 && desk.every(([, , c]) => c >= 4.5 || c === 0), JSON.stringify(desk));
check('S16 no script errors on any page', ![pg, mob, np].some(p => (p.errs || []).length), JSON.stringify([pg.errs, mob.errs, np.errs]));
await S.done();

console.log(`\nPLOTART STUDIO SAVE BAR · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exit(results.every(Boolean) ? 0 : 1);
