// PROVE · PlotArt Studio · gallery preview image sizes (12 Nov 2026).
// The preview serves the 1600-px preview copy; its srcset must describe THAT file, not the original. Describing the
// original (e.g. 7200w for a 1600-px file) made browsers draw the picture at 1600/7200 of its proper size on desktop.
// Real Worker (Miniflare) and Chromium, synthetic artist only.        node test/prove-preview-image-size.mjs
import { start, token, FOUNDER } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';

const req = createRequire(import.meta.url);
let chromium; try { ({ chromium } = req('playwright')); } catch { try { ({ chromium } = createRequire('/usr/lib/node_modules/')('playwright')); } catch { ({ chromium } = createRequire('/opt/npm-tools/node_modules/')('playwright')); } }
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const TMP = mkdtempSync(join(tmpdir(), 'pa-pis-'));
// originals of very different sizes and shapes (as an artist's camera files would be) + their 1600-px preview copies
const SPEC = [['big-landscape', 7200, 5901], ['portrait', 2500, 3500], ['landscape', 3169, 2515], ['small-portrait', 1500, 2100]];
execFileSync('python3', ['-c', `
import sys, json, random
from PIL import Image, ImageDraw
for name, w, h in json.loads(sys.argv[2]):
    r = random.Random(name); im = Image.new("RGB", (w, h), tuple(r.randrange(40, 200) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(30):
        x, y = r.randrange(w), r.randrange(h); s = max(w, h) // 8; d.rectangle((x, y, x + s, y + s), outline=tuple(r.randrange(256) for _ in range(3)), width=max(8, s // 30))
    im.save(f"{sys.argv[1]}/{name}.jpg", "JPEG", quality=85)
    k = min(1, 1600 / max(w, h)); im.resize((round(w * k), round(h * k))).save(f"{sys.argv[1]}/{name}-p.jpg", "JPEG", quality=86)
`, TMP, JSON.stringify(SPEC)]);

const { mf, url, db } = await start({ port: 8833, env: { TEST_MIN_LONG_EDGE: '1000' } });
const call = async (method, path, who, body, raw) => {
  const h = { 'X-Studio': '1', 'Cf-Access-Jwt-Assertion': token(who) }; if (!raw) h['Content-Type'] = 'application/json';
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: raw || (body === undefined ? undefined : JSON.stringify(body)) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
};
const email = 'sizes@example.test';
await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Size Tester', email, founding: true });
await call('PUT', '/api/me/profile', email, { medium: 'painting', bio: 'A synthetic painter used only to test preview image sizes in the Studio.' });
const ids = {};
for (const [name, w, h] of SPEC) {
  const wid = (await call('POST', '/api/artworks', email)).j.id;
  await call('PUT', `/api/artworks/${wid}`, email, { title: name, year: 2025, medium: 'Oil on canvas', h_cm: 90, w_cm: 70, price_eur: 2000, ai_involvement: 'none' });
  const up = await call('PUT', `/api/artworks/${wid}/images?role=main`, email, undefined, readFileSync(join(TMP, `${name}.jpg`)));
  if (up.s !== 200) { console.log('upload refused', name, up.t.slice(0, 200)); }
  ids[name] = up.j.id;
  if (name !== 'small-portrait') await call('PUT', `/api/images/${up.j.id}/preview`, email, undefined, readFileSync(join(TMP, `${name}-p.jpg`)));  // the small one keeps its original
  await call('PATCH', `/api/images/${up.j.id}`, email, { alt: `Synthetic painting ${name}`, photographer: 'self' });
}
console.log('PROVE · PlotArt Studio · gallery preview image sizes');
const page = await call('GET', '/preview/index.html', email);
const tag = id => (page.t.match(new RegExp(`<img src="img/${id}"[^>]*>`)) || [''])[0];
const attr = (t, a) => (t.match(new RegExp(`${a}="([^"]*)"`)) || [])[1];
const expect = { 'big-landscape': [1600, 1311], portrait: [1143, 1600], landscape: [1600, 1270], 'small-portrait': [1500, 2100] };
for (const [name] of SPEC) {
  const t = tag(ids[name]), [ew, eh] = expect[name];
  check(`P1 ${name}: srcset and width/height describe the file actually served (${ew}×${eh})`,
    attr(t, 'srcset') === `img/${ids[name]} ${ew}w` && +attr(t, 'width') === ew && +attr(t, 'height') === eh, t);
}
const served = await mf.dispatchFetch(url + `/preview/img/${ids['big-landscape']}`, { headers: { 'Cf-Access-Jwt-Assertion': token(email) } });
const buf = new Uint8Array(await served.arrayBuffer());
let i = 2, dims = null; while (i < buf.length) { if (buf[i] !== 0xFF) { i++; continue; } const mk = buf[i + 1]; if (mk >= 0xC0 && mk <= 0xC3) { dims = [(buf[i + 7] << 8) | buf[i + 8], (buf[i + 5] << 8) | buf[i + 6]]; break; } i += 2 + ((buf[i + 2] << 8) | buf[i + 3]); }
check('P2 the file served for the 7200×5901 work really is the 1600×1311 preview copy', dims && dims[0] === 1600 && dims[1] === 1311, JSON.stringify(dims));
// the founder's review preview uses the same package
await acceptAgreement(mf, url, email);
const sub = await call('POST', '/api/submit', email, { note: null });
if (sub.s !== 200) console.log('submit refused', sub.t.slice(0, 300));
const sid = sub.j.id || (await db.prepare("SELECT id FROM submissions WHERE status='pending' ORDER BY created_at DESC").first())?.id;
const fpage = await call('GET', `/admin/preview/${sid}/index.html`, FOUNDER);
check('P3 the founder review preview carries the same corrected sizes', fpage.s === 200 && fpage.t.includes(`img/${ids['big-landscape']} 1600w`) && !fpage.t.includes('7200w'), `${fpage.s} ${sid}`);

// visual: desktop and mobile, every painting fills its frame the same way; the big one is no longer shrunk
const browser = await chromium.launch();
for (const [label, vp, mob] of [['desktop 1440', { width: 1440, height: 1000 }, false], ['tablet 900', { width: 900, height: 1000 }, false], ['mobile 390', { width: 390, height: 844 }, true]]) {
  const ctx = await browser.newContext({ viewport: vp, isMobile: mob, hasTouch: mob, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  const p = await ctx.newPage(); await p.goto(url + `/admin/preview/${sid}/index.html`, { waitUntil: 'load' });
  const m = await p.evaluate(async () => { const imgs = [...document.querySelectorAll('.pa-ag-art img')]; imgs.forEach(i => { i.loading = 'eager'; });
    await Promise.all(imgs.map(i => i.decode().catch(() => {})));
    return imgs.map(i => { const r = i.getBoundingClientRect(), f = i.parentElement.getBoundingClientRect(), cs = getComputedStyle(i.parentElement);
      const iw = f.width - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight), ih = f.height - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
      return { alt: i.alt, w: r.width, h: r.height, iw, ih, ratio: r.width / r.height, nat: i.naturalWidth / i.naturalHeight }; }); });
  const fills = m.length === 4 && m.every(x => Math.abs(x.w - x.iw) < 2 || Math.abs(x.h - x.ih) < 2);   // each touches its frame on one side (contain)
  const undistorted = m.every(x => Math.abs(x.ratio - x.nat) < 0.02);
  const big = m.find(x => x.alt === 'Synthetic painting big-landscape'), land = m.find(x => x.alt === 'Synthetic painting landscape');
  check(`V ${label}: every painting fills its frame (whole picture, no crop), aspect ratio kept`, fills && undistorted, JSON.stringify(m.map(x => [x.alt.slice(19), Math.round(x.w), Math.round(x.h), Math.round(x.iw), Math.round(x.ih)])));
  check(`V ${label}: the 7200×5901 painting is shown as large as the other landscape work`, big && land && big.w >= land.w - 2, JSON.stringify([big && big.w, land && land.w]));
  await ctx.close();
}
await browser.close();
const pass = results.filter(Boolean).length;
console.log(`\nPREVIEW IMAGE SIZES · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
await mf.dispose();
process.exit(pass === results.length ? 0 : 1);
