// LOCAL PREVIEW ONLY · the Review Desk Featured Artists view, filled with the PUBLISHED PlotArt galleries (public data read from
// plotart/artists/*/gallery.json and their published 600px images). Runs the Studio locally (Miniflare); touches nothing live.
//   node test/preview-featured-desk.mjs OUT.png
import { readFileSync, readdirSync } from 'node:fs';
import { start, token, FOUNDER } from './local.mjs';
import { snapshot } from '../src/lib.js';
const SITE = new URL('../../../plotart/artists/', import.meta.url).pathname, T = '2026-11-05T17:05:00.000Z';
const { mf, url, db } = await start({ port: 8801 });
const IMAGES = await mf.getR2Bucket('IMAGES', 'studio');
const ids = {};
for (const slug of readdirSync(SITE).sort()) {
  let p; try { p = JSON.parse(readFileSync(SITE + slug + '/gallery.json', 'utf8')); } catch { continue; }
  const aid = 'a' + slug.replace(/-/g, '').slice(0, 20); ids[slug] = aid;
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, practice, bio, account_status, first_published_at, created_at, updated_at)
    VALUES (?,?,?,?,1,?,?,'active',?,?,?)`).bind(aid, slug, slug + '@preview.invalid', p.artist.display_name, p.artist.practice || null, p.artist.bio || null, T, T, T).run();
  let n = 0;
  for (const w of p.works) {
    n++; const im = (w.images || []).find(i => i.role === 'main'); if (!im) continue;
    await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'none',0,?,?)`).bind(w.id, aid, w.slug, w.title, w.year || 2026, w.medium || 'x', w.h_cm || 1, w.w_cm || 1, w.price_eur || null, w.availability, '', n, T, T).run();
    const d = im.derivatives.find(x => x.long_edge === 600) || im.derivatives[0], key = `previews/${aid}/${n}.webp`;
    await IMAGES.put(key, Uint8Array.from(readFileSync(SITE + slug + '/img/' + d.file)).buffer);
    await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, preview_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
      VALUES (?,?,?,'main',?,?,?,1,?,?,'webp',?,'self','{}',0,?)`).bind(`i${aid.slice(1)}${n}`, aid, w.id, key, key, 'x', im.pixels[0], im.pixels[1], im.alt, T).run();
  }
  const a = await db.prepare('SELECT * FROM artists WHERE id=?').bind(aid).first();
  const ws = (await db.prepare('SELECT * FROM artworks WHERE artist_id=?').bind(aid).all()).results, is = (await db.prepare('SELECT * FROM images WHERE artist_id=?').bind(aid).all()).results;
  await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?,1,?,'preview',?)").bind(aid, JSON.stringify(snapshot(a, ws, is)), T).run();
  await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?,?,1,'reviewed','published',?,?)").bind('q' + aid, aid, T, T).run();
}
// the founder's current homepage choices (as plotart/index.html showed them before this change), stored as migration 0016
// holds them: four artists and two single artworks (kind 'artwork'), which the Featured Artists tab reads as their artists
const SEL = [['leah-hewson', 'wxcp1v5y210', 'artist'], ['ciaran-mccoy', 'w2j298wac6v', 'artist'], ['mark-kavanagh-rasher', 'wxf94pphfgy', 'artist'],
  ['fintan-whelan', 'wi2ggh2x2rt', 'artwork'], ['anna-marie-savage', 'wx8gh81e5bu', 'artwork'], ['daniel-chester', 'wfhtcyurvgf', 'artist']];
let n0 = 0;
for (const [s, w, k] of SEL) await db.prepare('INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (?,?,?,?,?)').bind(++n0, k, ids[s], w, T).run();
const r = { status: 'seeded' };
console.log('saved', r.status);
const { chromium } = await import('playwright');
const b = await chromium.launch();
const OUT = process.argv[2].replace(/\.png$/, '');
const overflow = [];
for (const [w, h, tag] of [[1360, 900, 'desktop'], [820, 1180, 'tablet'], [390, 844, 'mobile']]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { exp: 3600 }) } });
  const pg = await ctx.newPage(); await pg.goto(url + '/admin/featured');
  await pg.waitForSelector('.st-fa-card'); await pg.waitForTimeout(1500);
  await pg.evaluate(() => document.querySelectorAll('.st-top, header, .st-go-bar').forEach(n => { n.style.position = 'static'; }));
  const o = await pg.evaluate(() => { const g = document.querySelector('.st-hp-grid'); return { page: document.documentElement.scrollWidth - document.documentElement.clientWidth, grid: g.scrollWidth - g.clientWidth,
    cols: getComputedStyle(g).gridTemplateColumns.split(' ').length, cards: g.children.length }; });
  overflow.push({ tag, ...o });
  const sec = pg.locator('.st-card:has(.st-fa-grid)');
  const box = await sec.boundingBox();
  await pg.screenshot({ path: `${OUT}-${tag}.png`, fullPage: true, clip: { x: 0, y: 0, width: w, height: box.y + box.height + 24 } });
  if (tag === 'desktop') {   // the artwork chooser, opened from a featured artist's "Change artwork"
    await pg.click('[data-change="5"]'); await pg.waitForTimeout(900);
    await pg.evaluate(() => document.querySelectorAll('.st-go-bar').forEach(n => { n.style.position = 'static'; }));
    const gb = await pg.evaluate(() => { const r = document.querySelector('.st-hp-gal--choosing').getBoundingClientRect(); return { y: r.top + scrollY, h: r.height }; });
    await pg.screenshot({ path: `${OUT}-choose-artwork.png`, fullPage: true, clip: { x: 0, y: Math.max(0, gb.y - 30), width: w, height: gb.h + 50 } });
  }
  await ctx.close();
}
console.log(JSON.stringify(overflow));
await b.close(); await mf.dispose();
