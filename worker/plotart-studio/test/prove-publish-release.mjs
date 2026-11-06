// PROVE · PlotArt content publishing · the real release path (--push), end to end (5 Nov 2026).
// The journey test runs the pipeline with --simulate, which stops before pushing, so it never exercised the release.
// Here a local bare repository stands in for GitHub: the pipeline pushes its saved copy, starts the gate (stub `gh`),
// and promotes with the shared promote-after-gate.sh / promote.sh exactly as in production; the gate result, the live
// check and "another release moving main" are supplied by stand-ins. Synthetic artists only; local Studio (Miniflare);
// nothing leaves this machine.            node test/prove-publish-release.mjs --release DIR [--shots DIR]
// Scenarios A–H (founder brief 5 Nov 2026), then E2E: a gallery shaped like the one that failed in production.
import { acceptAgreement } from './agree.mjs';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { execFileSync, execSync, spawnSync, spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, chmodSync, mkdirSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';

const arg = k => process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : null;
const REL = arg('--release'), SHOTS = arg('--shots');
if (!REL) { console.log('usage: node test/prove-publish-release.mjs --release DIR [--shots DIR]'); process.exit(2); }
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(-700)}]` : ''}`); };
const TMP = mkdtempSync(join(tmpdir(), 'pa-release-'));

// images: per artist one portrait and up to 11 portrait-format artworks (distinct, so no duplicate-photo blocks)
execFileSync('python3', ['-c', `
import random, sys
from PIL import Image, ImageDraw
def make(name, seed, w, h):
    r = random.Random(seed); im = Image.new("RGB", (w, h), tuple(r.randrange(40, 200) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(24):
        x, y = r.randrange(w), r.randrange(h); d.rectangle((x, y, x + r.randrange(w // 6, w // 2), y + r.randrange(h // 6, h // 2)), outline=tuple(r.randrange(256) for _ in range(3)), width=18)
    im.save(f"{sys.argv[1]}/{name}.jpg", "JPEG", quality=86)
for k in "abcdefgh":
    make(k + "-portrait", ord(k) * 7, 1400, 1800); make(k + "-w1", ord(k) * 7 + 1, 2200, 3300)
for i in range(1, 12):
    make("l-w%d" % i, 900 + i, 2400, 3600)
make("l-portrait", 899, 1600, 2000)
`, TMP]);

// "GitHub": a bare repository holding main; the pipeline works in a clone of it, as the workflow's checkout does
const ORIGIN = join(TMP, 'origin.git'), SITE = join(TMP, 'site'), OTHER = join(TMP, 'other');
execSync(`mkdir -p ${SITE} && git -C ${REL} archive HEAD | tar -x -C ${SITE}`);
const G = (cwd, ...a) => execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@plotnua.invalid', ...a], { cwd, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 }).trim();
G(SITE, 'init', '-q', '-b', 'main'); G(SITE, 'add', '-A'); G(SITE, 'commit', '-q', '-m', 'main (test copy)');
execSync(`git init -q --bare -b main ${ORIGIN} && git -C ${SITE} remote add origin ${ORIGIN} && git -C ${SITE} push -q origin main`);
execSync(`git clone -q ${ORIGIN} ${OTHER}`);
const originMain = () => G(ORIGIN, 'rev-parse', 'main');
const onMain = path => { try { G(ORIGIN, 'cat-file', '-e', `main:${path}`); return true; } catch { return false; } };
const branches = pat => G(ORIGIN, 'for-each-ref', '--format=%(refname:short)', `refs/heads/${pat}`).split('\n').filter(Boolean);
const ancestor = (a, b) => { try { G(ORIGIN, 'merge-base', '--is-ancestor', a, b); return true; } catch { return false; } };
const otherRelease = (file) => { G(OTHER, 'pull', '-q', '--ff-only', 'origin', 'main'); writeFileSync(join(OTHER, file), file + '\n'); G(OTHER, 'add', '-A'); G(OTHER, 'commit', '-q', '-m', 'another release: ' + file); G(OTHER, 'push', '-q', 'origin', 'main'); };

// stand-ins: `gh` (records calls), the gate (mode file), the live check (mode file); every call is logged
const BIN = join(TMP, 'bin'); mkdirSync(BIN);
writeFileSync(join(BIN, 'gh'), `#!/bin/sh\necho "gh $*" >> ${TMP}/gh.log\nexit 0\n`); chmodSync(join(BIN, 'gh'), 0o755);
const GATE = join(TMP, 'gate.sh'), HEALTH = join(TMP, 'health.sh');
writeFileSync(GATE, `#!/bin/sh
echo "$1 $2" >> ${TMP}/gate.log
mode=$(cat ${TMP}/gate.mode)
if [ "$mode" = "move-main" ]; then echo success > ${TMP}/gate.mode; cd ${OTHER} && git pull -q --ff-only origin main && echo moved >> moved-during-gate.txt && git add -A && git -c user.name=T -c user.email=t@t commit -q -m "another release during the gate" && git push -q origin main; mode=success; fi
printf 'completed\\t%s\\n' "$mode"
`); chmodSync(GATE, 0o755);
writeFileSync(HEALTH, `#!/bin/sh
echo "health $*" >> ${TMP}/health.log
mode=$(cat ${TMP}/health.mode)
if [ "$mode" = "fail-once" ]; then echo ok > ${TMP}/health.mode; exit 1; fi
exit 0
`); chmodSync(HEALTH, 0o755);
const setGate = m => writeFileSync(join(TMP, 'gate.mode'), m), setHealth = m => writeFileSync(join(TMP, 'health.mode'), m);
setGate('success'); setHealth('ok');
const TOOLS = join(TMP, 'release-tools'); execSync(`cp -r ${SITE}/atlas-tools/release ${TOOLS}`);   // the trusted copy (from main)

const { mf, url, db } = await start({ port: 8818 });
const call = async (method, path, email, body, raw) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': raw ? 'application/octet-stream' : 'application/json' },
    body: raw || (body === undefined ? undefined : JSON.stringify(body)) });
  return { s: r.status, j: await r.json().catch(() => ({})) };
};
const img = n => readFileSync(join(TMP, `${n}.jpg`));
// an artist with a portrait and n artworks (descriptions, prices), submitted, approved and sent to publishing
const ready = async (k, name, email, works) => {
  const id = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, founding: true })).j.id;
  await call('PUT', '/api/me/profile', email, { practice: 'Painter', medium: 'painting', county: 'Dublin', county_public: true, statement: 'Colour and light.',
    bio: `${name} is an invented test artist who paints coastlines and cities in thin layers of oil and acrylic.`, instagram: 'synthetic.artist', website: 'https://example.test' });
  const p = await call('PUT', '/api/me/portrait', email, undefined, img(`${k}-portrait`));
  await call('PATCH', `/api/images/${p.j.id}`, email, { alt: `Portrait of ${name}`, photographer: 'self' });
  for (const w of works) {
    const id2 = (await call('POST', '/api/artworks', email)).j.id;
    await call('PUT', `/api/artworks/${id2}`, email, { title: w.title, year: 2026, medium: 'Oil on canvas', h_cm: 100, w_cm: 70, description: w.desc, ai_involvement: 'none',
      ...(w.por ? { price_on_request: true } : { price_eur: w.price }) });
    const u = await call('PUT', `/api/artworks/${id2}/images?role=main`, email, undefined, img(w.img));
    await call('PATCH', `/api/images/${u.j.id}`, email, { alt: `${w.title}: a test painting`, photographer: w.other ? 'other_with_permission' : 'self', ...(w.other ? { photo_credit: 'Sam Synthetic' } : {}) });
  }
  await acceptAgreement(mf, url, email);
  const sub = await call('POST', '/api/submit', email, { accept_licence: true });
  if (sub.s !== 200) throw new Error('submit refused: ' + JSON.stringify(sub.j));
  const sid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(s => s.artist_id === id).id;
  await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve' });
  const q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === id);
  await call('POST', `/api/admin/queue/${q.id}/publish`, FOUNDER);
  return { id, email, q: q.id, version: q.version, slug: (await call('GET', '/api/me', email)).j.artist.slug };
};
const one = (k, name) => ready(k, name, `${k}@example.test`, [{ title: 'Tide', img: `${k}-w1`, price: 900, desc: 'A test painting of a tide line.' }]);
const qrow = qid => db.prepare('SELECT status, detail FROM publish_queue WHERE id=?').bind(qid).first();
const requeue = qid => db.prepare("UPDATE publish_queue SET status='ready' WHERE id=? AND status='failed'").bind(qid).run();   // what the founder's console command does
const publish = () => spawnSync('python3', ['atlas-tools/plotart-gallery-publish.py', '--studio', url, '--token', PIPELINE_TOKEN, '--push'], {
  cwd: SITE, encoding: 'utf8', env: { ...process.env, PATH: `${BIN}:${process.env.PATH}`, GITHUB_REPOSITORY: 'test/plotnua', RELEASE_TOOLS: TOOLS,
    GATE_STATUS_CMD: GATE, GATE_POLL: '0', GATE_TRIES: '3', HEALTH_CMD: HEALTH, PAGES_CMD: 'true', DISPATCH_CMD: 'true' } });
const out = r => (r.stdout + r.stderr);
const galleryFolders = () => G(ORIGIN, 'ls-tree', '-d', '--name-only', 'main:plotart/artists').split('\n').filter(Boolean);
// one open gallery on the Virtual Gallery wall per artist (Direction C2, 5 Nov 2026: the index of positions links it too, separately)
const cards = slug => (G(ORIGIN, 'show', 'main:plotart/gallery/index.html').match(new RegExp(`href="\\.\\./artists/${slug}/" data-pa-track="vg_artist"`, 'g')) || []).length;

console.log('PROVE · PlotArt content publishing · the release path, retries and failures');

// A — first publication
const A = await one('a', 'Aine Synthetic');
const m0 = originMain();
let r = publish();
check('A  first publication: saved copy pushed, gate passed on that exact commit, promoted to main, Studio says published, artist live',
  r.status === 0 && onMain(`plotart/artists/${A.slug}/index.html`) && (await qrow(A.q)).status === 'published' && (await call('GET', '/api/me', A.email)).j.status.state === 'live'
  && readFileSync(join(TMP, 'gate.log'), 'utf8').includes(originMain()) && readFileSync(join(TMP, 'health.log'), 'utf8').includes(originMain()), out(r));
check('A2 the saved copy is named after the version AND its commit (content/plotart-<artist>-v<n>-<commit>)', branches(`content/plotart-${A.id}-v1-*`).length === 1, branches('content/*').join(' '));

// B — a failed attempt, then a successful retry of the same version
const B = await one('b', 'Brid Synthetic');
setGate('failure'); const mB = originMain();
r = publish();
const bFail = (await qrow(B.q)).status, mainAfterFail = originMain();
setGate('success'); await requeue(B.q);
r = publish();
check('B  a failed attempt (gate refused) releases nothing and marks the item failed; the retry of the same version publishes',
  bFail === 'failed' && mainAfterFail === mB && onMain(`plotart/artists/${B.slug}/index.html`) && (await qrow(B.q)).status === 'published', out(r));
check('B2 both attempts keep their own saved copy (the first is never overwritten)', branches(`content/plotart-${B.id}-v1-*`).length === 2);

// C — multiple retries of the same version (gate refused, then promotion refused by a failed live check, then success)
const C = await one('c', 'Cara Synthetic');
setGate('failure'); publish(); const c1 = (await qrow(C.q)).status; await requeue(C.q);
setGate('success'); setHealth('fail-once'); const mC = originMain();
r = publish(); const c2 = (await qrow(C.q)).status, cRolledBack = !onMain(`plotart/artists/${C.slug}/index.html`) && ancestor(mC, 'main');
await requeue(C.q); setHealth('ok');
r = publish();
check('C  three attempts of one version: refused, released-then-rolled-back, then published; exactly one gallery and one card at the end',
  c1 === 'failed' && c2 === 'failed' && cRolledBack && (await qrow(C.q)).status === 'published' && galleryFolders().filter(f => f === C.slug).length === 1 && cards(C.slug) === 1, out(r));
check('C2 each attempt kept its own saved copy (3 for this version)', branches(`content/plotart-${C.id}-v1-*`).length === 3, branches(`content/plotart-${C.id}-*`).join(' '));

// D — a saved copy already exists under the OLD fixed name (as in production for Leah's version 2)
const D = await one('d', 'Dara Synthetic');
G(SITE, 'push', '-q', 'origin', `${G(SITE, 'rev-parse', 'HEAD')}:refs/heads/content/plotart-${D.id}-v1`);       // a stale copy, different commit
const staleSha = G(ORIGIN, 'rev-parse', `content/plotart-${D.id}-v1`);
r = publish();
check('D  an earlier attempt’s copy under the old name does not block publishing, and is left exactly as it was (no force)',
  r.status === 0 && onMain(`plotart/artists/${D.slug}/index.html`) && (await qrow(D.q)).status === 'published' && G(ORIGIN, 'rev-parse', `content/plotart-${D.id}-v1`) === staleSha, out(r));

// E — main moves (1) before the run and (2) while the gate is running
const E = await one('e', 'Eabha Synthetic');
otherRelease('released-before-run.txt'); const before = originMain();
r = publish();
check('E1 main moved before the run: the gallery is built on the latest main and released (the other release kept)',
  r.status === 0 && onMain(`plotart/artists/${E.slug}/index.html`) && onMain('released-before-run.txt') && ancestor(before, 'main'), out(r));
const E2 = await one('f', 'Fia Synthetic');
setGate('move-main'); const m5 = originMain();
r = publish();
const e2 = (await qrow(E2.q)).status, movedKept = onMain('moved-during-gate.txt') && !onMain(`plotart/artists/${E2.slug}/index.html`) && ancestor(m5, 'main');
await requeue(E2.q);
r = publish();
check('E2 main moved while the gate ran: promotion is refused (never forced), nothing lost; the retry publishes on the new main',
  e2 === 'failed' && movedKept && onMain(`plotart/artists/${E2.slug}/index.html`) && onMain('moved-during-gate.txt') && (await qrow(E2.q)).status === 'published', out(r));

// F — a failed image-rights / provenance check
const F = await one('g', 'Grainne Synthetic');
G(OTHER, 'pull', '-q', '--ff-only', 'origin', 'main');
const recP = join(OTHER, 'image-provenance-records.json'), rec = JSON.parse(readFileSync(recP, 'utf8'));
rec.records.push({ asset: 'plotart/artists/nobody/img/x.webp', class: 'ARTIST_SUPPLIED_ARTWORK', artist_slug: 'nobody' });   // an undeclared, unreferenced record
writeFileSync(recP, JSON.stringify(rec, null, 2) + '\n'); G(OTHER, 'add', '-A'); G(OTHER, 'commit', '-q', '-m', 'a broken record (test)'); G(OTHER, 'push', '-q', 'origin', 'main');
const mF = originMain(), gatesBefore = readFileSync(join(TMP, 'gate.log'), 'utf8').split('\n').length;
r = publish();
const fRefused = (await qrow(F.q)).status === 'failed' && originMain() === mF && /(launch guard|image provenance|image rights) refused[\s\S]*provenance/.test(r.stdout) && readFileSync(join(TMP, 'gate.log'), 'utf8').split('\n').length === gatesBefore;
check('F  a provenance problem (caught by the launch guard’s provenance rule L14 or the provenance validator) stops before anything is pushed: no copy, no gate, main unchanged, item failed',
  fRefused && branches(`content/plotart-${F.id}-*`).length === 0, out(r));
G(OTHER, 'pull', '-q', '--ff-only', 'origin', 'main'); G(OTHER, 'revert', '--no-edit', 'HEAD'); G(OTHER, 'push', '-q', 'origin', 'main');   // repair main for the rest
await requeue(F.q); r = publish();
check('F2 once the record problem is fixed on main, the retry publishes', (await qrow(F.q)).status === 'published' && onMain(`plotart/artists/${F.slug}/index.html`), out(r));

// G — a failed release step (promotion refused because the gate never passes in time / gate failure after push)
const Gq = await one('h', 'Gobnait Synthetic');
setGate('failure'); const mG = originMain();
r = publish();
check('G  a failed release step leaves main untouched and the item failed (the saved copy stays as an audit record)',
  originMain() === mG && (await qrow(Gq.q)).status === 'failed' && branches(`content/plotart-${Gq.id}-*`).length === 1 && !onMain(`plotart/artists/${Gq.slug}/index.html`), out(r));
setGate('success'); await requeue(Gq.q); publish();

// H — an accidental duplicate publishing attempt after success
const galleriesBefore = galleryFolders().length, mH = originMain(), cardsA = cards(A.slug);
r = publish();
check('H1 running publishing again with nothing ready changes nothing', originMain() === mH && /nothing|^$/.test(r.stdout.trim().split('\n').pop() || ''), out(r));
await db.prepare("UPDATE publish_queue SET status='ready' WHERE id=?").bind(A.q).run();       // the same published version re-queued by mistake
r = publish();
const aRow = await qrow(A.q);
const sameRecords = (a, b) => { const rs = c => JSON.stringify(JSON.parse(G(ORIGIN, 'show', `${c}:image-provenance-records.json`)).records.map(x => JSON.stringify(x)).sort()); return rs(a) === rs(b); };
const changedH = G(ORIGIN, 'diff', '--name-only', mH, 'main').split('\n').filter(Boolean);
check('H2 re-publishing an already-published version creates no duplicate gallery or card and changes no published file (at most the image-records file is re-ordered, same records)',
  galleryFolders().length === galleriesBefore && cards(A.slug) === cardsA && changedH.every(f => f === 'image-provenance-records.json') && sameRecords(mH, 'main'), `${aRow.status} ${changedH.join(' ')} :: ${out(r)}`);
console.log(`        (H2 outcome: queue item marked "${aRow.status}"${aRow.detail ? ' · ' + String(aRow.detail).slice(0, 120) : ''})`);

// E2E — shaped like the production gallery: 11 artworks with descriptions and prices (one "price on request", one
// third-party photograph), a portrait, approved, a previously FAILED attempt with a stale saved copy, then re-queued
const L = await ready('l', 'Lia Synthetic', 'lia@example.test', Array.from({ length: 11 }, (_, i) => ({
  title: `Harbour Light ${i + 1}`, img: `l-w${i + 1}`, price: 1200 + i * 150, por: i === 10, other: i === 3, desc: `Test painting ${i + 1}: harbour light at dusk, layered oil.` })));
G(SITE, 'push', '-q', 'origin', `${G(SITE, 'rev-parse', 'HEAD')}:refs/heads/content/plotart-${L.id}-v1`);   // the old-name copy from a failed attempt
setGate('failure'); publish(); const lFailed = (await qrow(L.q)).status;                                  // a previously failed attempt
setGate('success'); await requeue(L.q);
const mL = originMain(); r = publish();
const ok = r.status === 0 && (await qrow(L.q)).status === 'published';
check('E2E-1 Leah-shaped gallery: failed attempt, re-queued, then queue → images → image rights → provenance → saved copy → gate → promotion: published',
  lFailed === 'failed' && ok && ancestor(mL, 'main'), out(r));
const S = join(TMP, 'live'); execSync(`git clone -q ${ORIGIN} ${S}`);
const page = f => readFileSync(join(S, 'plotart/artists', L.slug, f), 'utf8');
const idx = page('index.html'), workPages = execSync(`ls ${join(S, 'plotart/artists', L.slug)} | grep -v '^index.html$' | grep '\\.html$'`, { encoding: 'utf8' }).trim().split('\n');
check('E2E-2 public gallery generated: index + 11 artwork pages, all 11 titles on the index, Virtual Gallery card present once',
  workPages.length === 11 && Array.from({ length: 11 }, (_, i) => `Harbour Light ${i + 1}`).every(t => idx.includes(t)) && cards(L.slug) === 1, workPages.join(' '));
const prov = JSON.parse(readFileSync(join(S, 'image-provenance-records.json'), 'utf8')).records.filter(x => x.artist_slug === L.slug);
const imgs = execSync(`ls ${join(S, 'plotart/artists', L.slug, 'img')}`, { encoding: 'utf8' }).trim().split('\n');
check('E2E-3 images: 11 artworks × 3 sizes + 1 portrait (600 px only), each with exactly one provenance record (third-party photo credited)',
  imgs.length === 34 && prov.length === 34 && imgs.filter(f => f.startsWith('portrait')).length === 1 && prov.filter(x => x.subject === 'portrait').length === 1
  && prov.filter(x => x.photographer === 'other_with_permission' && x.photo_credit === 'Sam Synthetic').length === 3, `${imgs.length} files, ${prov.length} records`);
const w1 = page(workPages.find(f => /harbour-light-1\.html$/.test(f))), w11 = page(workPages.find(f => /harbour-light-11\.html$/.test(f)));
check('E2E-4 descriptions and prices on the artwork pages (€1,200 on the first; "Price on request" on the eleventh); portrait on the index',
  w1.includes('harbour light at dusk') && /€\s?1,200/.test(w1) && /Price on request/i.test(w11) && /class="pa-ag-portrait"><img src="img\/portrait-600\.webp"/.test(idx), (w11.match(/[^>]{0,40}(Price|€)[^<]{0,40}/) || [''])[0]);
check('E2E-5 the full provenance and image-rights checks pass on the published result',
  spawnSync('node', ['atlas-tools/validate-image-provenance.js'], { cwd: S, encoding: 'utf8' }).status === 0
  && spawnSync('node', ['atlas-tools/validate-image-rights.js', '--scan-html', '.', '--permissions', 'image-rights-manifest.json', '--max-age-days', '30'], { cwd: S, encoding: 'utf8' }).status === 0);
check('E2E-6 no other content changed in that release: only the artist’s folder, the Virtual Gallery grid and image records',
  G(ORIGIN, 'diff', '--name-only', mL, 'main').split('\n').every(f => f.startsWith(`plotart/artists/${L.slug}/`) || f === 'plotart/gallery/index.html' || f === 'image-provenance-records.json'));
check('X1 main only ever moved forward (no force anywhere): the first main is an ancestor of the last', ancestor(m0, 'main'));

// desktop and phone views of the generated public gallery (served from the published tree, no network)
if (SHOTS) {
  const req = createRequire(import.meta.url);
  let chromium; try { ({ chromium } = req('playwright')); } catch { ({ chromium } = createRequire('/opt/npm-tools/node_modules/')('playwright')); }
  const srv = spawn('python3', ['-m', 'http.server', '8819', '--bind', '127.0.0.1'], { cwd: S, stdio: 'ignore' });
  await new Promise(res => setTimeout(res, 800));
  const b = await chromium.launch(); const errs = [];
  for (const [vp, f] of [[{ width: 1440, height: 900 }, 'desktop-1440'], [{ width: 390, height: 844 }, 'phone-390']]) {
    const p = await b.newPage({ viewport: vp, deviceScaleFactor: 1 }); p.on('pageerror', e => errs.push(e.message));
    await p.goto(`http://127.0.0.1:8819/plotart/artists/${L.slug}/`, { waitUntil: 'networkidle' });
    for (let y = 0; y < 30; y++) { await p.mouse.wheel(0, 900); await p.waitForTimeout(120); }   // images below the fold load lazily
    await p.waitForLoadState('networkidle'); await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(300);
    const broken = await p.evaluate(() => [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src));
    const over = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    await p.screenshot({ path: join(SHOTS, `e2e-gallery-${f}.png`), fullPage: true });
    check(`E2E-7 ${f}: every image loads (portrait and artworks), no sideways scroll`, broken.length === 0 && over <= 0, broken.join(' '));
    await p.goto(`http://127.0.0.1:8819/plotart/artists/${L.slug}/harbour-light-1.html`, { waitUntil: 'networkidle' });
    await p.screenshot({ path: join(SHOTS, `e2e-artwork-${f}.png`), fullPage: true }); await p.close();
  }
  await b.close(); srv.kill();
}

await mf.dispose();
const pass = results.filter(Boolean).length;
console.log(`\n${pass}/${results.length} checks passed`);
process.exit(pass === results.length ? 0 : 1);
