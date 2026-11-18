// PROVE · PlotArt Studio · artwork photographs sit whole and centred (founder brief 18 Nov 2026, "two artwork images are
// not centred"). Synthetic artist, local Worker only. Three awkward photographs: a very tall portrait, a wide panorama and a
// phone photograph whose pixels are stored sideways with an EXIF "rotate 90°" tag (how most phones save portrait shots).
//   node test/prove-image-position.mjs [--shots DIR]
import { acceptAgreement } from './agree.mjs';
import { start, token, FOUNDER } from './local.mjs';
import { execFileSync } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { chromium } from 'playwright';

const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 700)}]` : ''}`); };
const shot = async (pg, name, full = true) => { if (SHOTS) await pg.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: full }); };
console.log('PROVE · PlotArt Studio · image positioning');

const TMP = mkdtempSync(join(tmpdir(), 'pa-img-'));
execFileSync('python3', ['-c', `
import sys
from PIL import Image, ImageDraw
def art(w, h, c, name, exif=None):
    im = Image.new("RGB", (w, h), c); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), outline=(240, 200, 60), width=max(w, h) // 60)   # a frame line to see the edges
    d.line((0, 0, w, h), fill=(240, 240, 240), width=12); d.line((0, h, w, 0), fill=(240, 240, 240), width=12)
    if exif: e = Image.Exif(); e[0x0112] = exif; im.save(sys.argv[1] + "/" + name, "JPEG", quality=85, exif=e)
    else: im.save(sys.argv[1] + "/" + name, "JPEG", quality=85)
art(1500, 4000, (60, 90, 130), "tall.jpg")
art(5000, 1400, (130, 70, 60), "wide.jpg")
# stored 4032 x 3024 (landscape pixels), tagged "rotate 90° clockwise": it is a portrait photograph, 3024 x 4032 when shown
im = Image.new("RGB", (4032, 3024), (70, 120, 80)); d = ImageDraw.Draw(im)
d.rectangle((0, 0, 4031, 3023), outline=(240, 200, 60), width=60); d.rectangle((0, 0, 900, 3023), fill=(200, 60, 60))
e = Image.Exif(); e[0x0112] = 6; im.save(sys.argv[1] + "/phone.jpg", "JPEG", quality=85, exif=e)
`, TMP]);

const { mf, url, db } = await start({ port: 8850 });
const call = async (method, path, who, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' }; if (who) h['Cf-Access-Jwt-Assertion'] = token(who);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
};
const all = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
const browser = await chromium.launch();
const open = async (email, w = 1280, h = 900) => {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email, { exp: 3600 }) } });
  const pg = await ctx.newPage(); pg.errs = []; pg.on('pageerror', e => pg.errs.push(String(e))); return pg;
};
const savedAll = pg => pg.waitForFunction(() => /^All changes saved/.test(document.querySelector('#sb-state')?.textContent || ''), null, { timeout: 10000 });

const EM = 'ines@example.test';
const aid = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Ines Test', email: EM, founding: true })).j.id;
await acceptAgreement(mf, url, EM);
const pg = await open(EM);
let EDITOR_TEXT = '';
const works = [['tall.jpg', 'Tall Study'], ['wide.jpg', 'Wide Shore'], ['phone.jpg', 'Phone Portrait']];
for (const [file, title] of works) {
  await pg.goto(url + '/#/'); await pg.reload(); await pg.waitForSelector('[data-act=add]');
  await pg.click('[data-act=add]'); await pg.waitForSelector('#mdrop');
  await pg.setInputFiles('#mdrop input[type=file]', join(TMP, file));
  await pg.waitForFunction(() => !!document.querySelector('#mdrop img'), null, { timeout: 20000 });
  await pg.fill('[data-img] input[name=alt]', `A test picture called ${title}`);
  await pg.check('[data-img] input[type=radio][value=self]');
  for (const [k, v] of [['#f-title', title], ['#f-year', '2026'], ['#f-medium', 'Oil on linen'], ['#f-h_cm', '60'], ['#f-w_cm', '80'], ['#f-price_eur', '900']]) await pg.fill(k, v);
  await savedAll(pg); await pg.waitForTimeout(500);
  if (file === 'phone.jpg') { await shot(pg, 'img-01-editor-phone-photo'); EDITOR_TEXT = await pg.textContent('#app, main, body'); }
}
const rows = await all("SELECT a.title, i.width, i.height, i.preview_key FROM images i JOIN artworks a ON a.id=i.artwork_id WHERE i.artist_id=? AND i.role='main'", aid);
const ph = rows.find(r => r.title === 'Phone Portrait');
check('I1 a phone portrait (stored sideways with an EXIF rotate tag) is recorded at its upright size, 3024 × 4032', ph.width === 3024 && ph.height === 4032, JSON.stringify(rows));
check('I2 the artwork page states the upright size', /3024 × 4032 px/.test(EDITOR_TEXT), EDITOR_TEXT.slice(0, 200));

/* measure every artwork picture: centred in its box, whole (not cropped), and its proportions those of the photograph */
const MEASURE = `(sel) => [...document.querySelectorAll(sel)].map(im => {
  const box = im.closest('.pa-ag-art, .pa-aw-frame, .st-thumb, .st-drop') || im.parentElement;
  const a = im.getBoundingClientRect(), b = box.getBoundingClientRect(), cs = getComputedStyle(box);
  const L = a.left - b.left - parseFloat(cs.paddingLeft), R = b.right - a.right - parseFloat(cs.paddingRight);
  const T = a.top - b.top - parseFloat(cs.paddingTop), B = b.bottom - a.bottom - parseFloat(cs.paddingBottom);
  return { src: (im.currentSrc || '').split('/').pop().slice(0, 30), offX: Math.round(L - R), offY: Math.round(T - B), top: Math.round(b.top), over: Math.round(Math.min(L, R, T, B)), natural: +(im.naturalWidth / im.naturalHeight).toFixed(3),
    shown: +(a.width / a.height).toFixed(3), fit: getComputedStyle(im).objectFit, w: Math.round(a.width), h: Math.round(a.height), boxW: Math.round(b.width), boxH: Math.round(b.height) }; })`;
const report = {};
for (const [w, h, tag] of [[1440, 900, 'desktop'], [390, 844, 'mobile']]) {
  const p = await open(EM, w, h);
  await p.goto(url + '/preview/'); await p.waitForFunction(() => [...document.images].every(i => i.complete));
  report[tag + ' gallery'] = await p.evaluate(`(${MEASURE})('.pa-ag-art img')`);
  await shot(p, `img-02-preview-gallery-${tag}`);
  for (const t of ['tall-study', 'wide-shore', 'phone-portrait']) {
    await p.goto(url + `/preview/${t}.html`); await p.waitForFunction(() => [...document.images].every(i => i.complete));
    report[`${tag} ${t}`] = await p.evaluate(`(${MEASURE})('.pa-aw-frame img')`);
    if (t === 'phone-portrait') await shot(p, `img-03-preview-artwork-phone-${tag}`, false);
  }
  await p.goto(url + '/#/works'); await p.reload(); await p.waitForSelector('.st-work');
  await shot(p, `img-04-studio-works-${tag}`);
}
const flat = Object.entries(report).flatMap(([k, v]) => v.map(r => ({ k, ...r })));
const offc = flat.filter(r => Math.abs(r.offX) > 2 || Math.abs(r.offY) > 2);
check('I3 every picture sits centred in its frame (gallery and artwork pages, desktop and phone)', flat.length === 12 && !offc.length, JSON.stringify(offc));
const bad = flat.filter(r => Math.abs(r.natural / r.shown - 1) > 0.02 || r.fit === 'cover' || r.over < -1);
check('I4 every picture is whole: never cropped, stretched or spilling out of its frame', !bad.length, JSON.stringify(bad));
const rowsD = {}; for (const r of report['desktop gallery']) (rowsD[r.top] ||= []).push(r.boxH);
check('I5 desktop gallery: the frames side by side are the same height (a tall work no longer leaves its neighbours sitting high)',
  Object.values(rowsD).every(h => Math.max(...h) - Math.min(...h) <= 1) && Object.keys(rowsD).length === 1, JSON.stringify(rowsD));
await browser.close(); await mf.dispose();
console.log(`${results.filter(Boolean).length}/${results.length} checks passed`);
