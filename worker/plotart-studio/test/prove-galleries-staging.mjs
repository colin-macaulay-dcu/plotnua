// PROVE · three galleries (Phase B) on a STAGING copy of the live PlotArt galleries. Local only (Miniflare D1); nothing here
// touches Cloudflare or the production database.
//   node test/prove-galleries-staging.mjs
// 1. A staging database is built with the PRODUCTION schema (main) and the PRODUCTION Studio code (main), and filled from
//    the live, published PlotArt galleries in this repository: every published artist (plotart/artists/*/gallery.json, with
//    their real artwork ids, works, prices, availability and images), the gallery positions shown on the live Contemporary
//    Art page (01 is Leah Hewson), and the live Artists in Focus selection. Artists' email addresses are not public: each
//    gets a synthetic address. 2. Everything the publisher and the founder read today is recorded. 3. Migration 0023 is
//    applied to that same database and the Phase B Studio code is started on it. 4. The same reads must be identical, every
//    existing row must be unchanged, and the new galleries must be empty.
import { readFileSync, readdirSync, mkdtempSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';

const HERE = new URL('..', import.meta.url).pathname, ROOT = join(HERE, '../..');
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const tmp = mkdtempSync(join(tmpdir(), 'pa-staging-')), MAIN = join(tmp, 'main'), PERSIST = join(tmp, 'd1');
execFileSync('git', ['-C', ROOT, 'worktree', 'add', '-q', '--detach', MAIN, 'origin/main']);
execFileSync('ln', ['-s', join(HERE, 'node_modules'), join(MAIN, 'worker/plotart-studio/node_modules')]);
const mainSchema = readFileSync(join(MAIN, 'worker/plotart-studio/schema.sql'), 'utf8');
const MIG = readFileSync(join(HERE, 'migrations/0023_three_galleries.sql'), 'utf8');
console.log('PROVE · three galleries on a staging copy of the live PlotArt galleries');

const callFor = (mod, mf, url) => async (method, path, email, headers = {}) => {
  const h = { 'X-Studio': '1', ...headers };
  if (email) h['Cf-Access-Jwt-Assertion'] = mod.token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h });
  return { s: r.status, t: await r.text() };
};
const nn = (...v) => v.map(x => x === undefined ? null : x);   // public records omit some fields
const SHOWN = new Set(['available', 'reserved', 'sold', 'not_for_sale']);
const id = (p, s) => p + createHash('sha256').update(s).digest('hex').slice(0, 10);
const packages = readdirSync(join(ROOT, 'plotart/artists')).sort().map(s => JSON.parse(readFileSync(join(ROOT, 'plotart/artists', s, 'gallery.json'), 'utf8')));
const vg = readFileSync(join(ROOT, 'plotart/gallery/index.html'), 'utf8');
const positions = [['01', 'leah-hewson'], ...[...vg.matchAll(/<li class="pa-vgc-work" data-pa-position="(\d\d)">[\s\S]*?href="\.\.\/artists\/([a-z0-9-]+)\/"/g)].map(m => [m[1], m[2]])];
const featured = JSON.parse(execFileSync('python3', ['-c', 'import sys,json; sys.path.insert(0,"atlas-tools"); import plotart_featured as F; print(json.dumps(F.selection_in(open("plotart/gallery/index.html").read())))'], { cwd: ROOT, encoding: 'utf8' }));

/* ---- 1. staging database: production schema, production code, live published data ---- */
const M = await import(join(MAIN, 'worker/plotart-studio/test/local.mjs'));
const L = await import(join(MAIN, 'worker/plotart-studio/src/lib.js'));
let { mf, db, url } = await M.start({ port: 8821, persist: PERSIST, schemaSql: mainSchema });
let shownWorks = 0;
for (const pkg of packages) {
  const a = pkg.artist, aid = id('a', a.slug), pub = pkg.publication, t = pub.approved_at || pub.first_approved_at || "2026-11-05T00:00:00.000Z", first = pub.first_approved_at || t;
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, practice, medium, county, county_public, statement, bio, website, instagram, account_status,
    licence_version, licence_accepted_at, first_published_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,1,?,?,?,?, 'active', ?,?,?,?,?)`)
    .bind(...nn(aid, a.slug, `${a.slug}@staging.invalid`, a.display_name, a.founding ? 1 : 0, a.practice || null, a.medium || null, a.county || null, a.statement || null, a.bio || null,
      a.website || null, a.instagram || null, pub.licence_version, pub.licence_accepted_at, first, first, t)).run();
  let ord = 0;
  for (const w of pkg.works) {
    ord++; if (SHOWN.has(w.availability)) shownWorks++;
    await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, materials, h_cm, w_cm, d_cm, price_eur, price_on_request, availability, description, ord,
      ai_involvement, ai_note, archived, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?)`)
      .bind(...nn(w.id, aid, w.slug, w.title, w.year || null, w.medium || null, w.materials || null, w.h_cm || null, w.w_cm || null, w.d_cm || null, w.price_eur ?? null,
        w.price_on_request ? 1 : 0, w.availability, w.description || null, ord, w.ai_involvement || 'none', w.ai_note || null, t, t)).run();
    let n = 0;
    for (const im of w.images || []) {
      n++;
      await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, preview_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
        VALUES (?,?,?,?,?,?,?,1000,?,?,'jpeg',?, 'self', '{"blocks":[],"warns":[]}', ?, ?)`)
        .bind(...nn(id('i', w.id + n), aid, w.id, im.role === 'main' ? 'main' : 'view', `originals/${aid}/${w.id}-${n}.jpg`, `previews/${aid}/${w.id}-${n}.jpg`,
          id('', w.id + n).padEnd(64, '0'), (im.pixels || [2000, 1500])[0], (im.pixels || [2000, 1500])[1], im.alt || '', n - 1, t)).run();
    }
  }
  const ar = await db.prepare('SELECT * FROM artists WHERE id=?').bind(aid).first();
  const ws = (await db.prepare('SELECT * FROM artworks WHERE artist_id=? ORDER BY ord').bind(aid).all()).results, ims = (await db.prepare('SELECT * FROM images WHERE artist_id=?').bind(aid).all()).results;
  await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?, 1, ?, 'staging', ?)").bind(...nn(aid, JSON.stringify(L.snapshot(ar, ws, ims)), t)).run();
  await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?, ?, 1, 'reviewed', 'published', ?, ?)").bind(...nn(id('q', aid), aid, t, t)).run();
}
const T = '2026-11-24T12:00:00.000Z';
for (const [p, slug] of positions) await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(...nn(Number(p), id('a', slug), T)).run();
let fp = 0; for (const f of featured) await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (?, 'artist', ?, ?, ?)").bind(...nn(++fp, id('a', f.artist), f.work, T)).run();
check('S0 the staging database holds the live galleries: every published artist, every work with its real id, the visible positions and the live Artists in Focus',
  packages.length === 18 && (await db.prepare('SELECT COUNT(*) n FROM artists').first()).n === 18 && (await db.prepare('SELECT COUNT(*) n FROM artworks').first()).n === packages.reduce((s, p) => s + p.works.length, 0)
  && (await db.prepare('SELECT COUNT(*) n FROM homepage_features').first()).n === featured.length && featured.length === 6, `${packages.length} artists`);

/* ---- 2. what the publisher and the founder read today, with today's production code ---- */
const READS = [['GET', '/api/pipeline/gallery-order', 'pipe'], ['GET', '/api/pipeline/featured-artists', 'pipe'], ['GET', '/api/pipeline/queue', 'pipe'], ['GET', '/api/pipeline/hire-catalogue', 'pipe'],
  ['GET', '/api/admin/gallery-order', 'founder'], ['GET', '/api/admin/featured', 'founder'], ['GET', '/api/admin/opportunities', 'founder']];
const readAll = async (mod, mf, url) => { const call = callFor(mod, mf, url), o = {};
  for (const [m, p, who] of READS) o[p] = await call(m, p, who === 'founder' ? mod.FOUNDER : null, who === 'pipe' ? { Authorization: 'Bearer ' + mod.PIPELINE_TOKEN } : {});
  return o; };
const before = await readAll(M, mf, url);
const tablesOf = async d => (await d.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' AND name <> 'mail_capture' ORDER BY name").all()).results.map(r => r.name);
const dump = async (d, names) => { const o = {}; for (const tb of names) o[tb] = (await d.prepare(`SELECT * FROM ${tb} ORDER BY rowid`).all()).results; return JSON.stringify(o); };
const beforeTables = await tablesOf(db), beforeRows = await dump(db, beforeTables.filter(x => x !== 'audit'));
check('S1 today’s production Studio serves the staging galleries (publisher and founder reads all answer)', Object.values(before).every(r => r.s === 200), JSON.stringify(Object.fromEntries(Object.entries(before).map(([k, v]) => [k, v.s]))));
await mf.dispose();

/* ---- 3. migration 0023 applied to the same database; the Phase B Studio started on it ---- */
const B = await import(join(HERE, 'test/local.mjs'));
({ mf, db, url } = await B.start({ port: 8822, persist: PERSIST, schemaSql: MIG }));
const afterRows = await dump(db, beforeTables.filter(x => x !== 'audit'));
check('S2 after migration 0023 every existing table and row of the staging galleries is byte-for-byte unchanged', afterRows === beforeRows);
const after = await readAll(B, mf, url);
const norm = s => s.replace(/"generated_at":"[^"]*"/g, '"generated_at":"(time of the read)"');   // the hire catalogue stamps the time it was read; nothing else is a clock value
check('S3 everything the publisher reads (gallery order, Artists in Focus, publication queue, hire catalogue) is identical with the Phase B code',
  READS.filter(r => r[2] === 'pipe').every(([, p]) => after[p].s === 200 && norm(after[p].t) === norm(before[p].t)), READS.filter(r => r[2] === 'pipe' && after[r[1]].t !== before[r[1]].t).map(r => r[1]).join());
check('S4 everything the founder’s existing desks read (Gallery order, Featured Artists, Opportunities) is identical',
  READS.filter(r => r[2] === 'founder').every(([, p]) => after[p].s === 200 && after[p].t === before[p].t), READS.filter(r => r[2] === 'founder' && after[r[1]].t !== before[r[1]].t).map(r => r[1]).join());

/* ---- 4. the gallery model on the live data ---- */
const call = callFor(B, mf, url);
const g = JSON.parse((await call('GET', '/api/admin/galleries', B.FOUNDER)).t);
const gal = k => g.galleries.find(x => x.gallery_id === k);
check(`S5 Contemporary Art holds all 18 published artists and all ${shownWorks} works shown on the live site, as today`, gal('contemporary').members.length === 18 && gal('contemporary').live_works === shownWorks, `${gal('contemporary').members.length} / ${gal('contemporary').live_works}`);
check('S6 Landscape Art and Portraiture are empty and In preparation (0 of 6 artists, 0 of 30 works); nobody was assigned to them',
  ['landscape', 'portraiture'].every(k => gal(k).status === 'in_preparation' && gal(k).live_artists === 0 && gal(k).live_works === 0 && gal(k).ready === false)
  && (await db.prepare('SELECT COUNT(*) n FROM gallery_memberships').first()).n === 0 && (await db.prepare('SELECT COUNT(*) n FROM artwork_placements').first()).n === 0);
const pipe = JSON.parse((await call('GET', '/api/pipeline/galleries', null, { Authorization: 'Bearer ' + B.PIPELINE_TOKEN })).t);
check('S7 the new read-only pipeline view lists the same 18 Contemporary artists by public address and the other two galleries empty',
  pipe.installed && pipe.galleries[0].artists.length === 18 && pipe.galleries[1].artists.length === 0 && pipe.galleries[2].artists.length === 0 && !JSON.stringify(pipe).includes('@staging.invalid'));
await mf.dispose();
execFileSync('git', ['-C', ROOT, 'worktree', 'remove', '--force', MAIN]);
rmSync(tmp, { recursive: true, force: true });
const fail = results.filter(x => !x).length;
console.log(`\nTHREE GALLERIES · STAGING · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
