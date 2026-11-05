// PROVE · PlotArt content publishing · the real release path (--push), end to end (fix 5 Nov 2026).
// The journey test runs the pipeline with --simulate, which stops before pushing, so it never exercised the release.
// Here a local bare repository stands in for GitHub: the pipeline pushes, starts the gate (stub `gh`), and promotes
// with the shared promote-after-gate.sh / promote.sh exactly as in production, with the gate result and the live check
// supplied by stand-ins. Synthetic artists only; local Studio (Miniflare); nothing leaves this machine.
//   node test/prove-publish-release.mjs --release DIR
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { execFileSync, execSync, spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, chmodSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const REL = process.argv.includes('--release') ? process.argv[process.argv.indexOf('--release') + 1] : null;
if (!REL) { console.log('usage: node test/prove-publish-release.mjs --release DIR'); process.exit(2); }
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 600)}]` : ''}`); };
const TMP = mkdtempSync(join(tmpdir(), 'pa-release-'));

execFileSync('python3', ['-c', `
import random, sys
from PIL import Image, ImageDraw
def make(name, seed, w, h):
    r = random.Random(seed); im = Image.new("RGB", (w, h), tuple(r.randrange(40, 200) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(26):
        x, y = r.randrange(w), r.randrange(h); d.rectangle((x, y, x + r.randrange(w // 6, w // 2), y + r.randrange(h // 6, h // 2)), outline=tuple(r.randrange(256) for _ in range(3)), width=20)
    im.save(f"{sys.argv[1]}/{name}.jpg", "JPEG", quality=88)
for k, s in (("a", 11), ("b", 22), ("c", 33)):
    make(k + "-work", s, 2400, 3200); make(k + "-portrait", s + 1, 1400, 1800)
`, TMP]);

// "GitHub": a bare repository holding main; the pipeline works in a clone of it, as the workflow's checkout does
const ORIGIN = join(TMP, 'origin.git'), SITE = join(TMP, 'site'), OTHER = join(TMP, 'other');
execSync(`mkdir -p ${SITE} && git -C ${REL} archive HEAD | tar -x -C ${SITE}`);
const G = (cwd, ...a) => execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@plotnua.invalid', ...a], { cwd, encoding: 'utf8' }).trim();
G(SITE, 'init', '-q', '-b', 'main'); G(SITE, 'add', '-A'); G(SITE, 'commit', '-q', '-m', 'main (test copy)');
execSync(`git init -q --bare -b main ${ORIGIN} && git -C ${SITE} remote add origin ${ORIGIN} && git -C ${SITE} push -q origin main`);
execSync(`git clone -q ${ORIGIN} ${OTHER}`);
const originMain = () => G(ORIGIN, 'rev-parse', 'main');

// stand-ins: `gh` (records every call), the gate result, the live check and the Pages build
const BIN = join(TMP, 'bin'); mkdirSync(BIN);
writeFileSync(join(BIN, 'gh'), `#!/bin/sh\necho "gh $*" >> ${TMP}/gh.log\nexit 0\n`); chmodSync(join(BIN, 'gh'), 0o755);
const GATE = join(TMP, 'gate.sh'), HEALTH = join(TMP, 'health.sh');
const setGate = r => writeFileSync(GATE, `#!/bin/sh\necho "$1 $2" >> ${TMP}/gate.log\nprintf 'completed\\t${r}\\n'\n`); setGate('success'); chmodSync(GATE, 0o755);
writeFileSync(HEALTH, `#!/bin/sh\necho "health $*" >> ${TMP}/health.log\nexit 0\n`); chmodSync(HEALTH, 0o755);
const TOOLS = join(TMP, 'release-tools'); execSync(`cp -r ${SITE}/atlas-tools/release ${TOOLS}`);   // the trusted copy (from main)

const { mf, url } = await start({ port: 8818 });
const call = async (method, path, email, body, raw) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': raw ? 'application/octet-stream' : 'application/json' },
    body: raw || (body === undefined ? undefined : JSON.stringify(body)) });
  return { s: r.status, j: await r.json().catch(() => ({})) };
};
// an artist with a portrait and one artwork, submitted, approved and sent to publishing by the founder
const ready = async (k, name, email) => {
  const id = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, founding: true })).j.id;
  await call('PUT', '/api/me/profile', email, { practice: 'Painter', medium: 'painting', county: 'Clare', bio: `${name} is an invented test artist who paints coastlines in thin layers of oil.` });
  const p = await call('PUT', '/api/me/portrait', email, undefined, readFileSync(join(TMP, `${k}-portrait.jpg`)));
  await call('PATCH', `/api/images/${p.j.id}`, email, { alt: `Portrait of ${name}`, photographer: 'self' });
  const w = (await call('POST', '/api/artworks', email)).j.id;
  await call('PUT', `/api/artworks/${w}`, email, { title: 'Tide', year: 2026, medium: 'Oil on linen', h_cm: 80, w_cm: 60, price_eur: 900, ai_involvement: 'none' });
  const u = await call('PUT', `/api/artworks/${w}/images?role=main`, email, undefined, readFileSync(join(TMP, `${k}-work.jpg`)));
  await call('PATCH', `/api/images/${u.j.id}`, email, { alt: 'Test painting of a tide line', photographer: 'self' });
  await call('POST', '/api/submit', email, { accept_licence: true });
  const sid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(s => s.artist_id === id).id;
  await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve' });
  const q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === id);
  await call('POST', `/api/admin/queue/${q.id}/publish`, FOUNDER);
  return { id, q: q.id, slug: (await call('GET', '/api/me', email)).j.artist.slug };
};
const qstatus = async qid => { const r = await call('GET', '/api/admin/overview', FOUNDER); const q = r.j.queue.find(x => x.id === qid); return q ? q.status : 'published'; };
const publish = () => spawnSync('python3', ['atlas-tools/plotart-gallery-publish.py', '--studio', url, '--token', PIPELINE_TOKEN, '--push'], {
  cwd: SITE, encoding: 'utf8', env: { ...process.env, PATH: `${BIN}:${process.env.PATH}`, GITHUB_REPOSITORY: 'test/plotnua', RELEASE_TOOLS: TOOLS,
    GATE_STATUS_CMD: GATE, GATE_POLL: '0', GATE_TRIES: '3', HEALTH_CMD: HEALTH, PAGES_CMD: 'true', DISPATCH_CMD: 'true' } });
const onMain = path => { try { G(ORIGIN, 'cat-file', '-e', `main:${path}`); return true; } catch { return false; } };

console.log('PROVE · PlotArt content publishing · the release path');

// R1: an approved gallery (with a portrait) is released to main and the Studio is told it is published
const A = await ready('a', 'Aine Synthetic', 'aine@example.test');
const before = originMain();
let r = publish();
const out1 = r.stdout + r.stderr;
check('R1 Publish → the gallery is pushed, its gate is started, and after the gate passes it is promoted to main (no waiting for a workflow that never starts)',
  r.status === 0 && originMain() !== before && onMain(`plotart/artists/${A.slug}/index.html`) && /gh workflow run image-rights-gate\.yml --ref release\/auto\/plotart-/.test(readFileSync(join(TMP, 'gh.log'), 'utf8')), out1);
check('R2 the gate was checked on the exact released commit and the live check ran on it', readFileSync(join(TMP, 'gate.log'), 'utf8').includes(originMain()) && readFileSync(join(TMP, 'health.log'), 'utf8').includes(originMain()));
check('R3 the Studio records the queue item as published and the artist is live', (await qstatus(A.q)) === 'published' && (await call('GET', '/api/me', 'aine@example.test')).j.status.state === 'live');
check('R4 the portrait is on main once, at the size the page shows', (() => { const ls = G(ORIGIN, 'ls-tree', '--name-only', `main:plotart/artists/${A.slug}/img`).split('\n'); return ls.filter(f => f.startsWith('portrait')).length === 1; })());

// R5: another release moves main while the gallery waits in the queue: the pipeline builds on the latest main
writeFileSync(join(OTHER, 'unrelated-release.txt'), 'another release\n'); G(OTHER, 'pull', '-q', 'origin', 'main'); G(OTHER, 'add', '-A'); G(OTHER, 'commit', '-q', '-m', 'an unrelated release'); G(OTHER, 'push', '-q', 'origin', 'main');
const moved = originMain();
const B = await ready('b', 'Brid Synthetic', 'brid@example.test');
r = publish();
check('R5 main moved after the pipeline’s checkout: the gallery is built on the latest main and still released (fast-forward, nothing lost)',
  r.status === 0 && G(ORIGIN, 'merge-base', '--is-ancestor', moved, 'main') === '' && onMain(`plotart/artists/${B.slug}/index.html`) && onMain('unrelated-release.txt') && (await qstatus(B.q)) === 'published', r.stdout + r.stderr);

// R6: the gate does NOT pass → nothing reaches main and the Studio is told it failed (the item can be retried)
setGate('failure');
const C = await ready('c', 'Cara Synthetic', 'cara@example.test');
const held = originMain();
r = publish();
check('R6 if the gate refuses, nothing is released: main is unchanged and the Studio marks the item failed',
  originMain() === held && !onMain(`plotart/artists/${C.slug}/index.html`) && (await qstatus(C.q)) === 'failed' && /not released/.test(r.stdout), r.stdout + r.stderr);
check('R7 the pipeline never forces main: every move of main was a fast-forward', (() => { try { G(ORIGIN, 'merge-base', '--is-ancestor', before, 'main'); return true; } catch { return false; } })());

await mf.dispose();
const pass = results.filter(Boolean).length;
console.log(`\n${pass}/${results.length} checks passed`);
process.exit(pass === results.length ? 0 : 1);
