// PROVE · Opportunities shown publicly, end to end (Stage 3, 16 Nov 2026). Synthetic artist; local only.
//   node test/prove-opportunities-e2e.mjs --release RELEASE_TREE
// The real PlotArt Studio (Miniflare, schema with migration 0015) and the real content pipeline
// (atlas-tools/plotart-gallery-publish.py --simulate) against a temporary git copy of RELEASE_TREE standing in for main.
// Every guard runs exactly as in production (content boundary, launch guard with manifest, provenance, image rights);
// nothing is pushed. Journey: an existing artist's earlier answers stay private → the gallery is published → the artist
// confirms → listed → withdraws one interest → keeps everything private → unpublished.
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { execFileSync, spawnSync, execSync } from 'node:child_process';
import { mkdtempSync, readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const REL = process.argv.includes('--release') ? process.argv[process.argv.indexOf('--release') + 1] : null;
if (!REL) { console.log('usage: node test/prove-opportunities-e2e.mjs --release DIR'); process.exit(2); }
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 700)}]` : ''}`); };
const TMP = mkdtempSync(join(tmpdir(), 'pa-opp-e2e-'));
execFileSync('python3', ['-c', `
import random, sys
from PIL import Image, ImageDraw
for i in range(1, 3):
    r = random.Random(900 + i); w, h = 2400, 1800
    im = Image.new("RGB", (w, h), tuple(r.randrange(40, 200) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(30):
        x, y = r.randrange(w), r.randrange(h); c = tuple(r.randrange(256) for _ in range(3))
        (d.ellipse if r.random() < .5 else d.rectangle)((x, y, x + r.randrange(w // 6, w // 2), y + r.randrange(h // 6, h // 2)), outline=c, width=r.randrange(10, 40))
    im.save(f"{sys.argv[1]}/w{i}.jpg", "JPEG", quality=90)
`, TMP]);
const SITE = join(TMP, 'site');
execSync(`mkdir -p ${SITE} && git -C ${REL} archive HEAD | tar -x -C ${SITE}`);
const git = (...a) => execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@plotnua.invalid', ...a], { cwd: SITE, encoding: 'utf8' }).trim();
git('init', '-q'); git('add', '-A'); git('commit', '-q', '-m', 'main (test copy)');
const read = p => existsSync(join(SITE, p)) ? readFileSync(join(SITE, p), 'utf8') : null;
const region = p => { const s = read(p) || ''; const m = s.match(/<!-- pa-opportunity-artists:begin -->[\s\S]*?<!-- pa-opportunity-artists:end -->/); return m ? m[0] : null; };
const PAGES = ['plotart/living-gallery.html', 'plotart/art-for-hire/index.html', 'plotart/mobile-gallery/index.html', 'plotart/opportunities/index.html'];
const SLUG = 'orla-e2e', NAME = 'Orla Endtoend', EMAIL = 'orla-e2e@example.test';
const PRIVATE = /Kilkenny|courier|anywhere|Private practical note|087 000 0000|care, handling|online_only|orla-e2e@example/;

let S;
try {
console.log('PROVE · opportunities shown publicly, end to end');
S = await start({ port: 8899, env: { INSTANT_AUTOPUBLISH: 'true' } });
const { mf, db, url } = S;
const R2 = await mf.getR2Bucket('IMAGES', 'studio');
const call = async (method, path, email, body) => {
  // a fresh connection per call: the publisher runs for minutes between calls and the kept-alive socket can be closed
  let r; for (let k = 0; ; k++) { try { r = await mf.dispatchFetch(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) }); break; } catch (e) { if (k >= 2) throw e; await new Promise(z => setTimeout(z, 500)); } }
  return { s: r.status, j: await r.json().catch(() => ({})) };
};
const publish = () => spawnSync('python3', [join(SITE, 'atlas-tools/plotart-gallery-publish.py'), '--studio', url, '--token', PIPELINE_TOKEN, '--simulate'], { cwd: SITE, encoding: 'utf8' });

// a published-in-Studio artist whose gallery is about to go out for the first time, with real photographs
await seedPublished(db, { id: 'aorla', slug: SLUG, email: EMAIL, name: NAME, works: 2, number: 1, licence: 'PA-GPIL-2026-11' });
for (const i of [1, 2]) {
  const buf = readFileSync(join(TMP, `w${i}.jpg`)), sha = createHash('sha256').update(buf).digest('hex');
  const img = await db.prepare('SELECT r2_key, preview_key FROM images WHERE id=?').bind(`iaorla${i}`).first();
  const u8 = new Uint8Array(buf); await R2.put(img.r2_key, u8, { httpMetadata: { contentType: "image/jpeg" } }); await R2.put(img.preview_key, u8, { httpMetadata: { contentType: "image/jpeg" } });
  await db.prepare('UPDATE images SET sha256=?, bytes=?, width=2400, height=1800 WHERE id=?').bind(sha, buf.length, `iaorla${i}`).run();
}
// the version-1 snapshot must carry the real fingerprints too: rebuild it from the records
const { snapshot } = await import('../src/lib.js');
const A0 = await db.prepare('SELECT * FROM artists WHERE id=?').bind('aorla').first();
const W0 = (await db.prepare('SELECT * FROM artworks WHERE artist_id=?').bind('aorla').all()).results, I0 = (await db.prepare('SELECT * FROM images WHERE artist_id=?').bind('aorla').all()).results;
await db.prepare('UPDATE versions SET snapshot=? WHERE artist_id=? AND version=1').bind(JSON.stringify(snapshot(A0, W0, I0)), 'aorla').run();
await db.prepare("UPDATE publish_queue SET status='ready' WHERE artist_id='aorla' AND version=1").run();
// answers saved BEFORE 0015 (production today): no public choice recorded
await db.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, practical_note, care_condition, created_at, updated_at, updated_by)
  VALUES ('aorla','["exhibitions","living_gallery","art_for_hire","commissions"]','Kilkenny','["courier"]','anywhere','[]','Private practical note: large canvases, phone 087 000 0000.',1,?,?,?)`)
  .bind('2026-11-14T10:00:00.000Z', '2026-11-14T10:00:00.000Z', EMAIL).run();

console.log('— 1 · first publication: the earlier, private answers are NOT published');
let p = publish();
const page = read(`plotart/artists/${SLUG}/index.html`), pkg = read(`plotart/artists/${SLUG}/gallery.json`);
check('E1 the gallery publishes through every guard (simulated push)', p.status === 0 && /verified \(simulated\)/.test(p.stdout) && page, p.stdout.slice(-500) + p.stderr.slice(-300));
check('E2 nothing about opportunities appears: no "Open to" line, no open_to in the package, every list still empty, nothing private anywhere',
  page && !/pa-ag-open/.test(page) && !/open_to/.test(pkg) && PAGES.every(x => !region(x).includes(SLUG)) && !PRIVATE.test(page + pkg + PAGES.map(region).join('')));

console.log('— 2 · the artist confirms (one click), and the update goes out automatically');
let r = await call('PUT', '/api/opportunities/visibility', EMAIL, { show: true });
check('E3 "Yes, show them" queues an automatic instant update (no founder step)', r.s === 200 && r.j.instant_version === 2
  && (await db.prepare("SELECT status FROM publish_queue WHERE artist_id='aorla' AND version=2").first()).status === 'ready', JSON.stringify(r.j));
p = publish();
const page2 = read(`plotart/artists/${SLUG}/index.html`);
check('E4 the instant update passes the content boundary (--instant) and every guard', p.status === 0 && /instant · verified \(simulated\)/.test(p.stdout), p.stdout.slice(-500));
check('E5 the gallery page shows "Open to" with Exhibitions, Living Gallery and Art for Hire (Commissions too, since the commissions switch is off)',
  /Open to: <a[^>]*>Exhibitions<\/a> · <a[^>]*>Living Gallery<\/a> · <a[^>]*>Art for Hire<\/a> · <a[^>]*>Commissions<\/a><\/p>/.test(page2), (page2.match(/pa-ag-open[^\n]*/) || [''])[0]);
const L = Object.fromEntries(PAGES.map(x => [x, region(x)]));
check('E6 listed on Living Gallery and Art for Hire with a link to the gallery; not on Mobile Gallery (not chosen); the Opportunities page lists the four choices',
  L[PAGES[0]].includes(`href="artists/${SLUG}/"`) && L[PAGES[1]].includes(`href="../artists/${SLUG}/"`) && !L[PAGES[2]].includes(SLUG)
  && ['exhibitions', 'living-gallery', 'art-for-hire', 'commissions'].every(a => new RegExp(`id="${a}"[\\s\\S]*?${SLUG}[\\s\\S]*?</section>`).test(L[PAGES[3]].split(/(?=<section)/).find(s => s.includes(`id="${a}"`)) || ''))
  && !/id="talks-and-events"[\s\S]*?orla-e2e/.test(L[PAGES[3]].split(/(?=<section)/).find(s => s.includes('id="talks-and-events"')) || ''));
const PRIV_G = new RegExp(PRIVATE.source, 'g'), count = t => (t.match(PRIV_G) || []).length;
const base = Object.fromEntries(PAGES.map(x => [x, count(execFileSync('git', ['show', git('rev-list', '--max-parents=0', 'HEAD') + ':' + x], { cwd: SITE, encoding: 'utf8' }))]));
const own = PAGES.map(region).join('') + page2 + read(`plotart/artists/${SLUG}/gallery.json`);
check('E7 only names and links are public: nothing from the private answers in the lists, the artist page or the package, and no new occurrence on the four pages',
  !PRIVATE.test(own) && PAGES.every(x => count(read(x)) === base[x]), (own.match(new RegExp('.{80}(?:' + PRIVATE.source + ').{80}', 's')) || [''])[0] + JSON.stringify(base));
check('E8 the Art for Hire works catalogue is untouched (artist interest stays separate from works approved for hire)',
  (read(PAGES[1]).match(/<!-- pa-hire-catalogue:begin -->[\s\S]*?<!-- pa-hire-catalogue:end -->/) || [''])[0] === (execFileSync('git', ['show', git('rev-list', '--max-parents=0', 'HEAD') + ':' + PAGES[1]], { cwd: SITE, encoding: 'utf8' }).match(/<!-- pa-hire-catalogue:begin -->[\s\S]*?<!-- pa-hire-catalogue:end -->/) || ['x'])[0]);

console.log('— 3 · withdrawing one interest');
r = await call('PUT', '/api/opportunities', EMAIL, { interests: ['exhibitions', 'art_for_hire', 'commissions'], artwork_county: 'Kilkenny', transport: ['courier'], coverage: { mode: 'anywhere' }, note: 'Private practical note: large canvases, phone 087 000 0000.', care_condition: true });
p = publish();
check('E9 deselecting Living Gallery removes the artist from the Living Gallery list and the "Open to" line at the next run; the rest stays',
  p.status === 0 && !region(PAGES[0]).includes(SLUG) && region(PAGES[1]).includes(SLUG) && !/>Living Gallery<\/a>/.test(read(`plotart/artists/${SLUG}/index.html`).match(/pa-ag-open[^\n]*/)[0]), p.stdout.slice(-400));

console.log('— 4 · opting out ("Keep them private")');
r = await call('PUT', '/api/opportunities/visibility', EMAIL, { show: false });
p = publish();
check('E10 keeping them private removes the artist from every list and removes the "Open to" line; the gallery and its works stay published',
  p.status === 0 && PAGES.every(x => !region(x).includes(SLUG)) && !/pa-ag-open/.test(read(`plotart/artists/${SLUG}/index.html`))
  && existsSync(join(SITE, `plotart/artists/${SLUG}/work-1.html`)), p.stdout.slice(-400));
check('E11 the answers themselves are kept in the Studio (only visibility changed)',
  JSON.parse((await db.prepare("SELECT interests FROM artist_opportunities WHERE artist_id='aorla'").first()).interests).length === 3);

console.log('— 5 · shown again, then the gallery is unpublished');
await call('PUT', '/api/opportunities/visibility', EMAIL, { show: true });
p = publish();
check('E12 shown again: back in the lists at the next run', p.status === 0 && region(PAGES[1]).includes(SLUG));
r = await call('POST', '/api/admin/artists/aorla/unpublish', FOUNDER, {});
if (r.s !== 200) r = await call('POST', '/api/admin/artists/aorla/unpublish', FOUNDER, { confirm: true });
p = publish();
check('E13 unpublishing the gallery removes the artist from every list automatically (only published artists appear)',
  r.s === 200 && p.status === 0 && !existsSync(join(SITE, `plotart/artists/${SLUG}/index.html`)) && PAGES.every(x => !region(x).includes(SLUG)),
  JSON.stringify(r) + p.stdout.slice(-400));
const commits = git('log', '--format=%s', '-8');
check('E14 every step was its own guarded content commit (no manual founder step after the first publication)', (commits.match(/PlotArt content: aorla/g) || []).length >= 6, commits);
} catch (e) { console.error(e); results.push(false); }
finally { if (S) await S.mf.dispose(); }
const fail = results.filter(x => !x).length;
console.log(`\nOPPORTUNITIES END TO END · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
