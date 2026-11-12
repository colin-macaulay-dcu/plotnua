// PROVE · PlotArt content publishing · galleries with extra artwork views (PLOTART-PUBLISHING-VIEWS-001, 12 Nov 2026).
// Production: Fintan Whelan's first gallery (one artwork + three extra views) was refused by the image provenance guard,
// P9: each view's 1200-px copy was recorded but shown on no page (the artwork page shows a view at 600 and 2000 px only).
// Here the REAL pipeline (atlas-tools/plotart-gallery-publish.py --simulate: every guard, no push) publishes, against a
// git copy of the release tree, galleries shaped like Fintan's and Nessa's. Synthetic artists only; local Studio.
//   node test/prove-publish-views.mjs --release DIR          (DIR: a checkout whose HEAD is the code under test)
import { acceptAgreement } from './agree.mjs';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { execFileSync, spawnSync, execSync, spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, readdirSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const REL = process.argv.includes('--release') ? process.argv[process.argv.indexOf('--release') + 1] : null;
if (!REL) { console.log('usage: node test/prove-publish-views.mjs --release DIR'); process.exit(2); }
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(-900)}]` : ''}`); };
const TMP = mkdtempSync(join(tmpdir(), 'pa-views-'));
// distinct photographs (no duplicate-photo blocks): portrait and landscape, all above the 2000-px minimum
execFileSync('python3', ['-c', `
import sys, random
from PIL import Image, ImageDraw
def make(name, seed, w, h):
    r = random.Random(seed); im = Image.new("RGB", (w, h), tuple(r.randrange(40, 200) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(36):
        x, y = r.randrange(w), r.randrange(h); d.rectangle((x, y, x + r.randrange(w // 8, w // 2), y + r.randrange(h // 8, h // 2)), fill=tuple(r.randrange(256) for _ in range(3)))
    im.save(f"{sys.argv[1]}/{name}.jpg", "JPEG", quality=88)
for i in range(4):  make(f"f{i}", 700 + i, 2400, 3200 if i % 2 == 0 else 2100)      # Fintan-shaped: main + 3 views
for i in range(9):  make(f"n{i}", 800 + i, 3000 if i % 3 else 2200, 2400)           # Nessa-shaped: 5 works, 4 views
make("portrait", 900, 1600, 2000)
`, TMP]);

const SITE = join(TMP, 'site');
execSync(`mkdir -p ${SITE} && git -C ${REL} archive HEAD | tar -x -C ${SITE}`);
const git = (...a) => execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@plotnua.invalid', ...a], { cwd: SITE, encoding: 'utf8' }).trim();
git('init', '-q'); git('add', '-A'); git('commit', '-q', '-m', 'main (test copy)');
const BASE = git('rev-parse', 'HEAD');

const { mf, url } = await start({ port: 8871 });
const db = await mf.getD1Database('DB', 'studio');
const call = async (method, path, email, body, raw) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': raw ? 'application/octet-stream' : 'application/json' },
    body: raw || (body === undefined ? undefined : JSON.stringify(body)) });
  return { s: r.status, j: await r.json().catch(() => ({})) };
};
// asynchronous: a long synchronous run blocks this process, which the local Studio's bindings need (the database link drops)
const publish = () => new Promise(res => { const p = spawn('python3', ['atlas-tools/plotart-gallery-publish.py', '--studio', url, '--token', PIPELINE_TOKEN, '--simulate'], { cwd: SITE });
  let stdout = '', stderr = ''; p.stdout.on('data', d => stdout += d); p.stderr.on('data', d => stderr += d); p.on('close', status => res({ status, stdout, stderr })); });
const img = n => readFileSync(join(TMP, `${n}.jpg`));

// mirror the real site's gallery order in the test Studio (as prove-journey does): the pipeline treats the Studio's order
// as authoritative, so published artists are seeded at their positions and reserved positions stay reserved
const vg = readFileSync(join(SITE, 'plotart/gallery/index.html'), 'utf8');
const plan = [...((vg.match(/<ol class="pa-vgc-plan"[^>]*>([\s\S]*?)\n    <\/ol>/) || [, ''])[1]).matchAll(/<li class="pa-vgc-pos is-(pub|res|prep|av)">([\s\S]*?)<\/li>/g)]
  .map(m => m[1] === 'pub' ? 'card:' + ((m[2].match(/artists\/([a-z0-9-]+)\//) || [])[1]) : m[1] === 'res' ? 'reserved' : m[1] === 'prep' ? 'prep' : 'space');
let k = 0;
for (const [i, it] of plan.entries()) {
  if (it.startsWith('card:')) {
    const slug = it.slice(5), g = JSON.parse(readFileSync(join(SITE, 'plotart/artists', slug, 'gallery.json'), 'utf8')), id = 'areal' + (++k);
    await seedPublished(db, { id, slug, email: `${slug}@real-mirror.invalid`, name: g.artist.display_name, works: 1, publishedAt: new Date(Date.parse('2026-11-01') + k * 60000).toISOString() });
    if (i < 25) await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(i + 1, id, '2026-11-01').run();
  } else if (it === 'reserved') await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,NULL,1,?,?)').bind(i + 1, 'Held (private)', '2026-11-01').run();
}
const publishedBefore = readdirSync(join(SITE, 'plotart/artists'));

async function gallery(name, email, works, portrait) {
  await call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, founding: true });
  await call('PUT', '/api/me/profile', email, { medium: 'painting', bio: `${name} is an invented test artist used to prove that galleries with extra artwork views publish.` });
  if (portrait) { const p = await call('PUT', '/api/me/portrait', email, undefined, img(portrait)); await call('PATCH', `/api/images/${p.j.id}`, email, { alt: `Portrait of ${name}`, photographer: 'self' }); }
  for (const [t, photos] of works) {
    const id = (await call('POST', '/api/artworks', email)).j.id;
    await call('PUT', `/api/artworks/${id}`, email, { title: t, year: 2025, medium: 'Oil on canvas', h_cm: 90, w_cm: 70, price_eur: 2000, ai_involvement: 'none' });
    for (const [n, ph] of photos.entries()) {
      const up = await call('PUT', `/api/artworks/${id}/images?role=${n ? 'view' : 'main'}`, email, undefined, img(ph));
      await call('PATCH', `/api/images/${up.j.id}`, email, { alt: `${t}, photograph ${n + 1}`, photographer: 'self' });
    }
  }
  await acceptAgreement(mf, url, email);
  const s = await call('POST', '/api/submit', email, {});
  const ov = (await call('GET', '/api/admin/overview', FOUNDER)).j, a = ov.artists.find(x => x.display_name === name);
  await call('POST', `/api/admin/submissions/${ov.submissions.find(x => x.artist_id === a.id).id}/decision`, FOUNDER, { decision: 'approve' });
  const q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === a.id);
  await call('POST', `/api/admin/queue/${q.id}/publish`, FOUNDER, {});
  const r = await publish();
  const after = await db.prepare('SELECT status, detail FROM publish_queue WHERE id=?').bind(q.id).first();
  return { s, a, r, after, slug: a.slug };
}
const files = slug => readdirSync(join(SITE, 'plotart/artists', slug, 'img')).sort();
const pageOf = (slug, p) => readFileSync(join(SITE, 'plotart/artists', slug, p), 'utf8');
const dims = f => execFileSync('python3', ['-c', 'import sys;from PIL import Image;print(*Image.open(sys.argv[1]).size)', f], { encoding: 'utf8' }).trim().split(' ').map(Number);

console.log('PROVE · PlotArt publishing · galleries with extra artwork views');
console.log('— Fintan-shaped: one artwork, main photograph + 3 extra views, with a portrait');
const F = await gallery('Fion Test', 'fion@example.test', [['Walk Test', ['f0', 'f1', 'f2', 'f3']]], 'portrait');
check('V1 it publishes: every guard passes, image provenance included (no P9 refusal)', F.r.status === 0 && /verified \(simulated\)/.test(F.r.stdout) && F.after.status === 'published', F.r.stdout + F.r.stderr + JSON.stringify(F.after));
const ff = files(F.slug);
check('V2 the main photograph keeps all its sizes (600, 1200, 2000)', ['walk-test-1-600.webp', 'walk-test-1-1200.webp', 'walk-test-1-2000.webp'].every(f => ff.includes(f)), ff.join(' '));
check('V3 each extra view keeps exactly the sizes its page shows (600 and 2000), no 1200',
  [2, 3, 4].every(n => ff.includes(`walk-test-${n}-600.webp`) && ff.includes(`walk-test-${n}-2000.webp`) && !ff.includes(`walk-test-${n}-1200.webp`)), ff.join(' '));
const fp = pageOf(F.slug, 'walk-test.html');
check('V4 the artwork page shows all three views (thumbnail + full-size link) and every link resolves to a published file',
  [2, 3, 4].every(n => fp.includes(`img/walk-test-${n}-600.webp`) && fp.includes(`href="img/walk-test-${n}-2000.webp"`)), fp.slice(0, 200));
const recs = JSON.parse(readFileSync(join(SITE, 'image-provenance-records.json'), 'utf8')).records.filter(r => (r.asset || '').includes(`/artists/${F.slug}/`));
const htmlAll = readdirSync(join(SITE, 'plotart/artists', F.slug)).filter(f => f.endsWith('.html')).map(f => pageOf(F.slug, f)).join('\n');
check('V5 every published image has exactly one provenance record and is referenced by a page (nothing unreferenced)',
  recs.length === ff.length && ff.every(f => recs.filter(r => r.asset.endsWith('/img/' + f)).length === 1 && htmlAll.includes('img/' + f)), `${recs.length} records, ${ff.length} files`);
const srcAspect = { 1: 2400 / 3200, 2: 2400 / 2100, 3: 2400 / 3200, 4: 2400 / 2100 };
check('V6 proportions are kept: every derivative has its photograph\'s aspect ratio (never cropped or stretched)',
  ff.filter(f => /^walk-test-\d-/.test(f)).every(f => { const [w, h] = dims(join(SITE, 'plotart/artists', F.slug, 'img', f)); return Math.abs(w / h - srcAspect[f.split('-')[2]]) < 0.006; }));
check('V7 never upscaled: the 2000-px copies are 2000 px on the long edge (sources are 3200/2400)',
  [1, 2, 3, 4].every(n => Math.max(...dims(join(SITE, 'plotart/artists', F.slug, 'img', `walk-test-${n}-2000.webp`))) === 2000));
check('V8 the portrait is still published once, at the size the page shows (unchanged rule)', ff.filter(f => f.startsWith('portrait')).length === 1, ff.join(' '));

console.log('— Nessa-shaped: five artworks, four of them with one extra view');
const N = await gallery('Nell Test', 'nell@example.test', [['Light', ['n0']], ['Light II', ['n1', 'n2']], ['Light I', ['n3', 'n4']], ['Blue City', ['n5', 'n6']], ['Messenger', ['n7', 'n8']]]);
check('V9 it publishes with every guard passing', N.r.status === 0 && /verified \(simulated\)/.test(N.r.stdout) && N.after.status === 'published', N.r.stdout + N.r.stderr + JSON.stringify(N.after));
const nf = files(N.slug);
check('V10 four views published at 600 and 2000 only; five main photographs at all three sizes',
  nf.filter(f => /-2-(600|2000)\.webp$/.test(f)).length === 8 && !nf.some(f => /-2-1200\.webp$/.test(f)) && nf.filter(f => /-1-(600|1200|2000)\.webp$/.test(f)).length === 15, nf.join(' '));

console.log('— nothing else changed');
const changed = git('diff', '--name-only', BASE, 'HEAD').split('\n').filter(Boolean);
const outside = changed.filter(p => !p.startsWith(`plotart/artists/${F.slug}/`) && !p.startsWith(`plotart/artists/${N.slug}/`) &&
  !['plotart/gallery/index.html', 'image-provenance-records.json', 'sitemap.xml'].includes(p) && !/^plotart\/(guides?|[a-z-]+\.html$)/.test(p));
check('V11 previously published galleries are untouched: the only changes are the two new galleries, the grid, records and sitemap',
  outside.length === 0 && publishedBefore.every(s => !changed.some(p => p.startsWith(`plotart/artists/${s}/`))), outside.join(' '));
const oldRecs = JSON.parse(execFileSync('git', ['show', `${BASE}:image-provenance-records.json`], { cwd: SITE, encoding: 'utf8', maxBuffer: 1 << 28 })).records;
const newRecs = JSON.parse(readFileSync(join(SITE, 'image-provenance-records.json'), 'utf8')).records;
check('V12 every existing provenance record is unchanged (only the new galleries\' records were added)',
  oldRecs.every(r => newRecs.some(n => JSON.stringify(n) === JSON.stringify(r))) && newRecs.length === oldRecs.length + recs.length + newRecs.filter(r => (r.asset || '').includes(`/artists/${N.slug}/`)).length, `${oldRecs.length} → ${newRecs.length}`);
const guard = spawnSync('node', ['atlas-tools/validate-image-provenance.js'], { cwd: SITE, encoding: 'utf8' });
check('V13 the image provenance guard passes on the final tree, unweakened (19 checks)', /19 checks, 19 passed, 0 failed/.test(guard.stdout), guard.stdout.slice(-400));

console.log('— error reporting');
const msg = spawnSync('python3', ['-c', `
import sys; sys.argv = ["x", "--studio", "http://x", "--token", "t"]; sys.path.insert(0, "atlas-tools")
import importlib.util as u
import plotart_gallery as m
out = "IMAGE PROVENANCE GUARD\\n  PASS  P1 a\\n  FAIL  P9 no declared record describes an unreferenced asset  [3: a-2-1200.webp, a-3-1200.webp]\\n" + "  PASS  P10 b\\n" * 40 + "  PASS  P14 every brand vector is bound to unchanged brand sources and is pure vector  [1 checked]\\n19 checks, 18 passed, 1 failed"
print(m.refusal("image provenance", out))
`], { cwd: SITE, encoding: 'utf8' });
check('V14 a refusal message now names the failing check first (e.g. "FAIL P9 … [3: …]"), then the summary',
  /^image provenance refused: FAIL\s+P9 no declared record describes an unreferenced asset\s+\[3: a-2-1200\.webp, a-3-1200\.webp\]\n19 checks, 18 passed, 1 failed/.test(msg.stdout), msg.stdout + msg.stderr);

const pass = results.filter(Boolean).length;
console.log(`\nPUBLISHING WITH EXTRA VIEWS · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
await mf.dispose();
process.exit(pass === results.length ? 0 : 1);
