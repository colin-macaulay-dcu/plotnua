// PROVE · PlotArt Studio · photograph details reliability (11 Nov 2026).
// Real Worker (Miniflare/workerd), real Studio page in Chromium, desktop and mobile. Synthetic artists only.
//   node test/prove-photo-details.mjs
import { start, token, FOUNDER } from './local.mjs';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';

const req = createRequire(import.meta.url);
let chromium; try { ({ chromium } = req('playwright')); } catch { try { ({ chromium } = createRequire('/usr/lib/node_modules/')('playwright')); } catch { ({ chromium } = createRequire('/opt/npm-tools/node_modules/')('playwright')); } }
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const TMP = mkdtempSync(join(tmpdir(), 'pa-pd-'));
execFileSync('python3', ['-c', `
import sys, random
from PIL import Image, ImageDraw
for i in range(12):
    r = random.Random(1300 + i); im = Image.new("RGB", (2200, 3000), tuple(r.randrange(40, 200) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(22):
        x, y = r.randrange(2200), r.randrange(3000); d.rectangle((x, y, x + r.randrange(200, 900), y + r.randrange(200, 900)), outline=tuple(r.randrange(256) for _ in range(3)), width=16)
    im.save(f"{sys.argv[1]}/p{i}.jpg", "JPEG", quality=88)
`, TMP]);
const pic = n => join(TMP, `p${n}.jpg`);

const { mf, url, db } = await start({ port: 8821 });
const call = async (method, path, who, body, raw) => {
  const h = { 'X-Studio': '1', 'Cf-Access-Jwt-Assertion': token(who) }; if (!raw) h['Content-Type'] = 'application/json';
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: raw || (body === undefined ? undefined : JSON.stringify(body)) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j };
};
const img = id => db.prepare('SELECT * FROM images WHERE id=?').bind(id).first();
const browser = await chromium.launch();
let n = 0;

async function scenario(label, vp) {
  console.log(`\n— ${label} (${vp.width}×${vp.height}${vp.mobile ? ', touch, mobile' : ''})`);
  const email = `pd${++n}@example.test`;
  const aid = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: `Photo Tester ${n}`, email, founding: true })).j.id;
  await call('PUT', '/api/me/profile', email, { medium: 'painting', bio: 'A synthetic painter used only to test photograph details in the Studio.' });
  const wid = (await call('POST', '/api/artworks', email)).j.id;
  await call('PUT', `/api/artworks/${wid}`, email, { title: 'Test Light', year: 2026, medium: 'Oil on canvas', h_cm: 90, w_cm: 70, price_eur: 1500, ai_involvement: 'none' });
  const main = (await call('PUT', `/api/artworks/${wid}/images?role=main`, email, undefined, readFileSync(pic(n * 4)))).j.id;
  const v1 = (await call('PUT', `/api/artworks/${wid}/images?role=view`, email, undefined, readFileSync(pic(n * 4 + 1)))).j.id;
  const v2 = (await call('PUT', `/api/artworks/${wid}/images?role=view`, email, undefined, readFileSync(pic(n * 4 + 2)))).j.id;
  // a second artwork whose photograph is already complete: must never be touched
  const w2 = (await call('POST', '/api/artworks', email)).j.id;
  await call('PUT', `/api/artworks/${w2}`, email, { title: 'Kept As Is', year: 2025, medium: 'Ink', h_cm: 30, w_cm: 20, ai_involvement: 'none' });
  const kept = (await call('PUT', `/api/artworks/${w2}/images?role=main`, email, undefined, readFileSync(pic(n * 4 + 3)))).j.id;
  await call('PATCH', `/api/images/${kept}`, email, { alt: 'Original description, saved earlier', photographer: 'self' });
  const keptBefore = JSON.stringify(await img(kept));

  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, isMobile: !!vp.mobile, hasTouch: !!vp.mobile,
    extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email) } });
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  p.on('dialog', d => d.dismiss());
  const go = async h => { await p.goto(url + '/' + h, { waitUntil: 'load' }); await p.waitForTimeout(600); };
  const tap = async sel => vp.mobile ? p.tap(sel) : p.click(sel);
  await go(`#/work/${wid}`);

  // R2 · every photograph's details are visible, each marked as needed
  const blocks = await p.locator('[data-img]').count();
  const collapsed = await p.locator('details [data-img]').count();
  const badges = await p.locator('[data-badge]').allInnerTexts();
  const flags = await p.locator('.st-view-flag:visible').count();
  const intro = await p.locator('text=Each view needs its own description and photographer').count();
  check(`${label} · R2 all three photographs show their own details (none collapsed), each marked "Needed to submit", views flagged`,
    blocks === 3 && collapsed === 0 && badges.every(b => b === 'Needed to submit') && flags === 2 && intro === 1, JSON.stringify({ blocks, collapsed, badges, flags, intro }));
  const head = await p.locator('.st-photo-h').allInnerTexts();
  check(`${label} · R2 the photographs are labelled "Main photograph", "View 1", "View 2"`,
    /^Main photograph details/.test(head[0]) && /^View 1 details/.test(head[1]) && /^View 2 details/.test(head[2]), JSON.stringify(head));

  // R1 · saves while typing, without leaving the field
  await p.locator(`#alt-${main}`).fill('Large abstract painting in blues and gold');
  await p.waitForTimeout(1600);
  check(`${label} · R1 a description saves a moment after typing stops, without leaving the field`, (await img(main)).alt === 'Large abstract painting in blues and gold');
  check(`${label} · R3 a "Saved" status stays on that photograph`, /^Saved \d\d:\d\d/.test(await p.locator(`[data-img="${main}"] [data-pstat]`).innerText()));

  // R1 · an upload redraws the page while a description is mid-typing: the text is saved, not lost
  await p.locator(`#alt-${v1}`).fill('Close detail of the gold layer');            // typed, field not left, no pause
  await p.locator('#vadd').setInputFiles(pic(11));                                 // a new view: upload → page redraw
  await p.waitForFunction(() => document.querySelectorAll('[data-img]').length === 4, null, { timeout: 30000 });
  await p.waitForTimeout(500);
  check(`${label} · R1 a description typed just before an upload redraw is saved, not lost`,
    (await img(v1)).alt === 'Close detail of the gold layer' && (await p.locator(`#alt-${v1}`).inputValue()) === 'Close detail of the gold layer');
  const v3 = await p.locator('[data-img]').nth(3).getAttribute('data-img');

  // R1 · leaving the page (Done) mid-typing saves first
  await p.locator(`#alt-${v2}`).fill('The painting installed above a fireplace');
  await tap('text=Done');
  await p.waitForTimeout(900);
  check(`${label} · R1 tapping Done mid-typing saves the description first`, (await img(v2)).alt === 'The painting installed above a fireplace');
  await go(`#/work/${wid}`);

  // R3 · an interrupted save: persistent failure with Retry, then success
  await p.route('**/api/images/*', r => r.request().method() === 'PATCH' ? r.abort() : r.continue());
  await p.locator(`#alt-${v3}`).fill('Side view showing the canvas edge');
  await p.locator(`#alt-${v3}`).press('Tab');
  await p.waitForTimeout(7000);                                                    // longer than the old 5-second message
  const failTxt = await p.locator(`[data-img="${v3}"] [data-pstat]`).innerText();
  check(`${label} · R3 an interrupted save shows "Not saved" with Retry, and it is still there after 7 seconds`,
    /^Not saved: No connection/.test(failTxt) && await p.locator(`[data-img="${v3}"] [data-retry]`).count() === 1 && (await img(v3)).alt === null, failTxt);
  await p.unroute('**/api/images/*');
  await tap(`[data-img="${v3}"] [data-retry]`);
  await p.waitForTimeout(1200);
  check(`${label} · R3 Retry saves it and the status changes to "Saved"`,
    (await img(v3)).alt === 'Side view showing the canvas edge' && /^Saved/.test(await p.locator(`[data-img="${v3}"] [data-pstat]`).innerText()));

  // a value the Studio refuses (too short) is never sent while typing, and gives a clear error when the field is left
  await p.locator(`#alt-${v3}`).fill('Hi');
  await p.waitForTimeout(1500);
  check(`${label} · a too-short description is not sent while typing (the saved one stays)`, (await img(v3)).alt === 'Side view showing the canvas edge');
  await p.locator(`#alt-${v3}`).press('Tab'); await p.waitForTimeout(900);
  check(`${label} · leaving it shows a persistent "Not saved" with the reason; the earlier description is kept`,
    /Not saved: Photo description/.test(await p.locator(`[data-img="${v3}"] [data-pstat]`).innerText()) && (await img(v3)).alt === 'Side view showing the canvas edge');
  await p.locator(`#alt-${v3}`).fill('Side view showing the canvas edge'); await p.locator(`#alt-${v3}`).press('Tab'); await p.waitForTimeout(700);

  // photographer for each photograph; the artwork's "still needed" line and the checklist follow
  for (const id of [main, v1, v2, v3]) { await tap(`input[name="photographer-${id}"][value="self"]`); await p.waitForTimeout(700); }
  const badges2 = await p.locator('[data-badge]').allInnerTexts();
  const flags2 = await p.locator('.st-view-flag:visible').count();
  check(`${label} · R2 every photograph now shows "Complete" and the view flags have gone`, badges2.length === 4 && badges2.every(b => b === 'Complete') && flags2 === 0, JSON.stringify({ badges2, flags2 }));
  check(`${label} · R5 the artwork's "Still needed" line has cleared`, await p.locator('#wneeds').isHidden());
  const ck = (await call('GET', `/api/admin/artists/${aid}/checklist`, FOUNDER)).j;
  check(`${label} · R5 the Review Desk checklist no longer lists this artwork`, !ck.items.some(i => i.work_id === wid), JSON.stringify(ck.items));
  await go('#/works');
  check(`${label} · R5 the works list no longer says "photo details"`, !(await p.locator(`.st-work:has(a[href="#/work/${wid}"]) .st-chip--todo`).count()));

  // R6 · nothing previously saved was overwritten
  check(`${label} · R6 a photograph saved earlier on another artwork is untouched (identical record)`, JSON.stringify(await img(kept)) === keptBefore);
  // R4 · audit: one entry per save, field names only, never the text
  const au = (await db.prepare("SELECT detail FROM audit WHERE artist_id=? AND action='image_details'").bind(aid).all()).results.map(r => r.detail);
  check(`${label} · R4 photograph-detail saves are in the audit log with field names, never the text`,
    au.length >= 8 && au.every(d => { const x = JSON.parse(d); return Array.isArray(x.fields) && x.image && x.role; }) &&
    !au.some(d => /blues and gold|fireplace|canvas edge|gold layer|Original description/.test(d)), `${au.length} rows`);
  check(`${label} · no browser errors`, errs.length === 0, JSON.stringify(errs));
  await ctx.close();
}

console.log('PROVE · PlotArt Studio · photograph details reliability');
await scenario('Desktop', { width: 1280, height: 900 });
await scenario('Mobile', { width: 390, height: 844, mobile: true });

await browser.close();
const pass = results.filter(Boolean).length;
console.log(`\nPHOTOGRAPH DETAILS · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
await mf.dispose();
process.exit(pass === results.length ? 0 : 1);
