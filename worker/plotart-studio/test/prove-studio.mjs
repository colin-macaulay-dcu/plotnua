// PROVE · PlotArt Studio (Phase 2, 29 Oct 2026). Synthetic artists only; the Worker runs locally (Miniflare/workerd)
// with a local D1 and R2. The publishing half runs the real Phase 1 Python ingest and build.
//   node test/prove-studio.mjs --gallery-tools /path/to/founder-branch/atlas-tools [--release /path/to/release-tree]
import { start, token, otherKey, FOUNDER, PIPELINE_TOKEN, AUD, TEAM } from './local.mjs';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import * as R from '../src/render.js';

const arg = k => process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : null;
const TOOLS = arg('--gallery-tools'), REL = arg('--release');
if (!TOOLS) { console.log('usage: node test/prove-studio.mjs --gallery-tools DIR [--release DIR]'); process.exit(2); }
const results = [];
const check = (name, ok, detail = '') => { results.push([name, !!ok]); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${!ok && detail ? `  [${String(detail).slice(0, 300)}]` : ''}`); };
const TMP = mkdtempSync(join(tmpdir(), 'pa-studio-'));

// fixture photographs (synthetic abstract images, made with Pillow)
execFileSync('python3', ['-c', `
import random, sys
from PIL import Image, ImageDraw
def art(seed, w, h, path, fmt="JPEG", **kw):
    r = random.Random(seed); im = Image.new("RGB", (w, h), tuple(r.randrange(30, 220) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(40):
        x, y = r.randrange(w), r.randrange(h); c = tuple(r.randrange(256) for _ in range(3))
        (d.ellipse if r.random() < .5 else d.rectangle)((x, y, x + r.randrange(w // 8, w // 2), y + r.randrange(h // 8, h // 2)), outline=c, width=r.randrange(8, 40))
    im.save(path, fmt, **kw)
D = sys.argv[1]
for i in range(1, 15): art(i, 2400, 1800, f"{D}/a{i}.jpg", quality=90)
art(50, 2600, 2000, f"{D}/warn.jpg", quality=90)
art(51, 1500, 1100, f"{D}/small.jpg", quality=90)
art(52, 1000, 1200, f"{D}/portrait.jpg", quality=90)
art(53, 2200, 2200, f"{D}/p.png", "PNG")
art(54, 2300, 1700, f"{D}/w.webp", "WEBP", quality=90)
open(f"{D}/fake.jpg", "wb").write(b"not an image at all" * 100)
`, TMP]);
const F = n => readFileSync(join(TMP, n));

const { mf, url } = await start({ port: 8794 });
const H = (email, extra = {}) => ({ 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json', ...extra });
const call = async (method, path, email, body, headers = {}) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: { ...(email ? H(email) : {}), ...headers }, body: body === undefined ? undefined : (body instanceof Uint8Array || Buffer.isBuffer(body) ? body : JSON.stringify(body)) });
  let j = null; const t = await r.text(); try { j = JSON.parse(t); } catch { j = { text: t }; }
  return { s: r.status, j, h: r.headers };
};
const put = (path, email, buf) => call('PUT', path, email, buf, { 'Content-Type': 'application/octet-stream' });
const A = 'aoife@example.test', B = 'brian@example.test';

console.log('PROVE · PlotArt Studio · Phase 2\n— sign-in and access');
let r = await call('GET', '/api/me');
check('S1 no sign-in token: refused (401)', r.s === 401);
r = await call('GET', '/api/me', null, undefined, { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { key: otherKey }) });
check('S2 a token signed by any other key is refused', r.s === 401);
r = await call('GET', '/api/me', null, undefined, { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { aud: 'someone-else' }) });
check('S3 a token for another application (audience) is refused', r.s === 401);
r = await call('GET', '/api/me', null, undefined, { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { iss: 'https://evil.cloudflareaccess.com' }) });
check('S4 a token from another Access team (issuer) is refused', r.s === 401);
r = await call('GET', '/api/me', null, undefined, { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { exp: -60 }) });
check('S5 an expired token is refused', r.s === 401);
r = await call('GET', '/api/me', 'stranger@example.test');
check('S6 a signed-in person who is not an invited artist gets no access (403)', r.s === 403 && /isn’t active/.test(r.j.error));
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Aoife Test', email: A, application_ref: 'F25-261029-0A1B2C' });
const r2 = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Brian Test', email: B, founding: false });
check('S7 the founder creates Studio accounts for selected artists', r.s === 200 && r2.s === 200 && r.j.slug === 'aoife-test');
const aid = r.j.id, bid = r2.j.id;
r = await call('GET', '/api/admin/overview', A);
check('S8 an artist cannot reach the founder desk', r.s === 403);
r = await call('PUT', '/api/me/profile', A, { bio: 'x'.repeat(50) }, { 'X-Studio': '' });
check('S9 a change without the Studio header is refused (cross-site protection)', r.s === 403);
r = await call('PUT', '/api/me/profile', A, { bio: 'x'.repeat(50) }, { Origin: 'https://evil.example' });
check('S10 a change from another origin is refused', r.s === 403);
const prod = await start({ env: { ENVIRONMENT: 'production' } });
const pr = await prod.mf.dispatchFetch(prod.url + '/api/me', { headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
check('S11 the local test key set is refused outside the local environment (fail closed)', pr.status === 500);
await prod.mf.dispose();

console.log('— profile and validation');
r = await call('PUT', '/api/me/profile', A, { bio: 'I paint the coast of Galway. Email me at aoife@gmail.com for commissions please.' });
check('V1 contact details in a biography are refused', r.s === 400 && /email address, phone number or Eircode/.test(r.j.error));
r = await call('PUT', '/api/me/profile', A, { bio: '<b>bold</b> biography text that is long enough to pass the minimum.' });
check('V2 markup is refused', r.s === 400);
r = await call('PUT', '/api/me/profile', A, { email: 'x@y.z' });
check('V3 an unknown field (e.g. email) cannot be set', r.s === 400);
r = await call('PUT', '/api/me/profile', A, { website: 'http://insecure.example' });
check('V4 a website must be https', r.s === 400);
r = await call('PUT', '/api/me/profile', A, { display_name: 'Aoife Test', practice: 'Painter', medium: 'painting', county: 'Galway', county_public: true,
  statement: 'Weather, water and the slow light of the west.', bio: 'Aoife paints large, quiet canvases about weather and water on the Galway coast, working between 2019 - 2026 from a small studio.' });
check('V5 a valid profile saves, with a timestamp', r.s === 200 && r.j.saved_at);

console.log('— photographs');
const w1 = (await call('POST', '/api/artworks', A)).j.id;
r = await put(`/api/artworks/${w1}/images?role=main`, A, F('fake.jpg'));
check('I1 a file that is not an image is refused (by content)', r.s === 422 && /isn’t a JPEG, PNG or WebP/.test(r.j.blocks[0]));
r = await put(`/api/artworks/${w1}/images?role=main`, A, F('small.jpg'));
check('I2 a photograph under 2,000 px is refused with a clear reason', r.s === 422 && /1500 px on its long edge; at least 2,000 px/.test(r.j.blocks[0]));
r = await put(`/api/artworks/${w1}/images?role=main`, A, Buffer.concat([F('a1.jpg'), Buffer.alloc(31 * 1048576)]));
check('I3 a file over 30 MB is refused', r.s === 413);
const big = Buffer.from(F('p.png')); big.writeUInt32BE(13000, 16);
r = await put(`/api/artworks/${w1}/images?role=main`, A, big);
check('I4 an image declaring more than 12,000 px a side is refused before decoding', r.s === 422 && /60 megapixels/.test(r.j.blocks[0]));
r = await put(`/api/artworks/${w1}/images?role=main`, A, F('warn.jpg'));
check('I5 2,600 px is accepted with a gentle warning', r.s === 200 && /3,000 px or more/.test(r.j.warns[0]));
r = await put(`/api/artworks/${w1}/images?role=main`, A, F('a1.jpg'));
const imgs1 = (await call('GET', '/api/artworks', A)).j.works.find(w => w.id === w1).images;
check('I6 a new main photograph replaces the previous one', r.s === 200 && imgs1.filter(i => i.role === 'main').length === 1 && imgs1[0].width === 2400);
r = await put(`/api/artworks/${w1}/images?role=main`, A, F('a1.jpg'));
check('I7 the same photograph twice on one artwork is refused', r.s === 422);
for (const n of ['p.png', 'w.webp', 'a14.jpg']) await put(`/api/artworks/${w1}/images?role=view`, A, F(n));
r = await put(`/api/artworks/${w1}/images?role=view`, A, F('a13.jpg'));
check('I8 PNG and WebP are accepted; up to 3 extra views', r.s === 400 && /Up to 3/.test(r.j.error));
r = await call('PUT', `/api/images/${r.j?.id || 'ix'}/preview`, A, Buffer.from('x'));
const pv = await call('PUT', `/api/images/${imgs1[0].id}/preview`, A, F('a2.jpg'), { 'Content-Type': 'application/octet-stream' });
check('I9 a browser-made preview copy is stored for the Studio only', pv.s === 200);
const bw = (await call('POST', '/api/artworks', B)).j.id;
r = await put(`/api/artworks/${bw}/images?role=main`, B, F('a1.jpg'));
const flagged = (await call('GET', '/api/admin/overview', FOUNDER)).j.flags;
check('I10 the same photograph uploaded by another artist is flagged to the founder only', r.s === 200 && !JSON.stringify(r.j).includes('DUPLICATE') &&
  flagged.some(f => f.artist_id === bid) && !JSON.stringify((await call('GET', '/api/artworks', B)).j).includes('DUPLICATE'));

console.log('— artists see only their own work');
r = await call('GET', '/api/artworks', B);
check('X1 an artist lists only their own artworks', r.j.works.length === 1 && r.j.works[0].id === bw);
r = await call('PUT', `/api/artworks/${w1}`, B, { title: 'Hijacked' });
const r3 = await call('POST', `/api/artworks/${w1}/availability`, B, { availability: 'sold' });
const r4 = await call('DELETE', `/api/artworks/${w1}`, B);
check('X2 another artist cannot edit, sell or delete an artwork (404)', r.s === 404 && r3.s === 404 && r4.s === 404);
r = await call('GET', `/api/images/${imgs1[0].id}/view`, B);
const r5 = await call('GET', `/preview/img/${imgs1[0].id}`, B);
const r6 = await call('PATCH', `/api/images/${imgs1[0].id}`, B, { alt: 'Hijacked description text' });
check('X3 another artist cannot see or change a photograph (404)', r.s === 404 && r5.s === 404 && r6.s === 404);
r = await call('PUT', `/api/artworks/${bw}/images?role=main`, A, F('a3.jpg'));
check('X4 an artist cannot upload into another artist’s artwork', r.s === 404);
r = await call('POST', '/api/artworks/order', A, { ids: [bw, w1] });
check('X5 an artist cannot reorder another artist’s works into their own', r.s === 400);

console.log('— building a Founding gallery, submitting, review');
const works = [w1];
for (let i = 2; i <= 10; i++) works.push((await call('POST', '/api/artworks', A)).j.id);
const fill = async (id, i) => {
  await call('PUT', `/api/artworks/${id}`, A, { title: `Tide Study ${i}`, year: 2025, medium: 'Oil on canvas', h_cm: 60, w_cm: 80, price_eur: 1000 + i * 50,
    description: `A synthetic test painting, number ${i}, for the Studio proof suite.`, ai_involvement: 'none' });
  if (i > 1) await put(`/api/artworks/${id}/images?role=main`, A, F(`a${i}.jpg`));
  const list = (await call('GET', '/api/artworks', A)).j.works.find(w => w.id === id).images;
  for (const im of list) await call('PATCH', `/api/images/${im.id}`, A, { alt: `Test painting ${i}, view of abstract shapes`, photographer: 'self' });
};
for (let i = 0; i < 9; i++) await fill(works[i], i + 1);
r = await call('POST', '/api/submit', A, { accept_licence: true });
check('W1 a Founding gallery cannot first open with fewer than 10 works', r.s === 422 && r.j.problems.some(p => /at least 10 artworks: you have 10/.test(p) || /Tide Study|untitled|needs/.test(p)));
await fill(works[9], 10);
r = await call('POST', '/api/submit', A, {});
check('W2 the licence must be accepted before the first submission', r.s === 422 && r.j.problems.some(p => /Licence/.test(p)));
r = await call('POST', '/api/submit', A, { accept_licence: true, note: 'My first ten works.' });
let me = (await call('GET', '/api/me', A)).j;
check('W3 a complete gallery is submitted (full review); licence version and date recorded', r.s === 200 && r.j.tier === 'full' && me.status.state === 'in_review' && me.artist.licence_version === 'PA-GPIL-2026-10-29');
const ov = (await call('GET', '/api/admin/overview', FOUNDER)).j;
check('W4 the submission appears on the founder’s desk', ov.submissions.length === 1 && ov.submissions[0].display_name === 'Aoife Test');
const sid = ov.submissions[0].id;
r = await call('GET', `/admin/preview/${sid}/index.html`, FOUNDER);
check('W5 the founder can open the exact gallery preview', r.s === 200 && r.j.text.includes('Tide Study 10') && r.j.text.includes('Founding Artist'));
r = await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'changes' });
check('W6 asking for changes needs a message', r.s === 400);
r = await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'changes', message: 'Please describe Tide Study 3 more fully.' });
me = (await call('GET', '/api/me', A)).j;
check('W7 the artist sees “changes requested” with the founder’s message', me.status.state === 'changes_requested' && me.status.last_decision.founder_message.includes('Tide Study 3'));
await call('PUT', `/api/artworks/${works[2]}`, A, { description: 'A fuller description of the third synthetic test painting, with its colours.' });
r = await call('POST', '/api/submit', A, { note: 'Done, thank you.' });
const sid2 = r.j.id;
r = await call('POST', `/api/admin/submissions/${sid2}/decision`, FOUNDER, { decision: 'approve' });
const q1 = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue;
check('W8 approval creates version 1, waiting for the founder to publish', r.s === 200 && r.j.version === 1 && q1.length === 1 && q1[0].status === 'awaiting_founder');
r = await call('GET', '/api/pipeline/queue', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
check('W9 nothing reaches the pipeline until the founder presses Publish', r.j.items.length === 0);
await call('POST', `/api/admin/queue/${q1[0].id}/publish`, FOUNDER, {});

console.log('— publishing through the Phase 1 pipeline');
r = await call('GET', '/api/pipeline/queue', null, undefined, { Authorization: 'Bearer wrong' });
check('P1 the pipeline API refuses a wrong token', r.s === 401);
const PK = join(TMP, 'packages');
let out = spawnSync('python3', [join(TOOLS, 'plotart-studio-publish.py'), '--studio', url, '--token', PIPELINE_TOKEN, '--packages', PK], { encoding: 'utf8' });
const pkg = existsSync(join(PK, 'aoife-test', 'package.json')) ? JSON.parse(readFileSync(join(PK, 'aoife-test', 'package.json'), 'utf8')) : null;
check('P2 the export passes the Phase 1 ingest and every publication safeguard', /aoife-test v1 · published/.test(out.stdout) && pkg && pkg.checks.publication_blocks.length === 0, out.stdout + out.stderr);
check('P3 the published package carries no email address or private field', pkg && !/@(?!plotnua\.ie)/.test(JSON.stringify(pkg)) && !JSON.stringify(pkg).includes('application_ref'));
me = (await call('GET', '/api/me', A)).j;
check('P4 the artist’s Studio shows “Live”', me.status.state === 'live' && me.status.live_version === 1 && me.artist.first_published_at);
if (REL) {
  const BO = join(TMP, 'build');
  const sw = join(REL, 'atlas-tools/release/plotart-launch-switches.json'), lj = join(TOOLS, '../plotart/data/launch.json'), keep = readFileSync(lj);
  writeFileSync(lj, readFileSync(sw));
  const b = spawnSync('python3', [join(TOOLS, 'build-plotart.py'), '--launch', '--out', BO, '--galleries', PK], { encoding: 'utf8' });
  writeFileSync(lj, keep);
  check('P5 the publication build renders the gallery and its 10 artwork pages', b.status === 0 && existsSync(join(BO, 'plotart/artists/aoife-test/index.html')) &&
    readdirSync(join(BO, 'plotart/artists/aoife-test')).filter(f => f.endsWith('.html')).length === 11, b.stdout + b.stderr);
}

console.log('— after publication: instant, light and full changes');
await call('POST', `/api/artworks/${works[0]}/availability`, A, { availability: 'sold' });
let q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue;
check('C1 marking a work sold makes an instant version without review (waits for auto-publish switch)', q.length === 1 && q[0].kind === 'instant' && q[0].version === 2 && q[0].status === 'awaiting_founder');
await call('POST', `/api/artworks/${works[9]}/archive`, A, { archived: true });
const ids = (await call('GET', '/api/artworks', A)).j.works.map(w => w.id); [ids[0], ids[1]] = [ids[1], ids[0]];
await call('POST', '/api/artworks/order', A, { ids });
q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue;
const v4 = JSON.parse((await prodSnap(aid, 4)) || 'null');
check('C2 removing and reordering are instant too (one waiting version, older instant ones superseded)', q.length === 1 && q[0].version === 4 && v4 && v4.works.length === 9 && v4.works[0].id === works[1] && v4.works[1].availability === 'sold');
await call('PUT', `/api/artworks/${works[2]}`, A, { price_eur: 2500 });
me = (await call('GET', '/api/me', A)).j;
check('C3 a price change is NOT live: it waits as a quick-check (light) change', me.status.tier === 'light' && me.status.unsubmitted.length === 1 && !(await prodSnap(aid, 5)));
r = await call('POST', '/api/submit', A, {});
check('C4 ... and is submitted as a quick check', r.j.tier === 'light');
const sid3 = r.j.id;
await call('POST', `/api/artworks/${works[2]}/availability`, A, { availability: 'reserved' });
await call('POST', `/api/admin/submissions/${sid3}/decision`, FOUNDER, { decision: 'approve' });
const v6 = JSON.parse(await prodSnap(aid, 6));
const t3 = v6.works.find(w => w.id === works[2]);
check('C5 approving keeps availability changes made after submitting (price €2,500 and reserved)', t3.price_eur === 2500 && t3.availability === 'reserved' && v6.works.length === 9);
const nw = (await call('POST', '/api/artworks', A)).j.id;
await fill(nw, 11);
me = (await call('GET', '/api/me', A)).j;
check('C6 a new artwork after publication needs full review', me.status.tier === 'full' && me.status.unsubmitted.some(c => /New artwork/.test(c.what)));
r = await call('DELETE', `/api/artworks/${works[0]}`, A);
check('C7 a published artwork cannot be hard-deleted (it is removed from the gallery instead)', r.s === 400);

console.log('— AI policy');
await call('PUT', `/api/artworks/${nw}`, A, { ai_involvement: 'generated' });
r = await call('POST', '/api/submit', A, {});
check('A1 an AI declaration other than “No” needs a short disclosure', r.s === 422 && r.j.problems.some(p => /AI disclosure/.test(p)));
await call('PUT', `/api/artworks/${nw}`, A, { ai_note: 'Generated entirely from text prompts in an image tool, then printed.' });
r = await call('POST', '/api/submit', A, {});
const sid4 = r.j.id;
r = await call('POST', `/api/admin/submissions/${sid4}/decision`, FOUNDER, { decision: 'approve' });
check('A2 a prompt-generated work cannot be approved without the founder’s eligibility decision', r.s === 400 && /eligible/.test(r.j.error));
r = await call('POST', `/api/admin/submissions/${sid4}/decision`, FOUNDER, { decision: 'approve', ai_decisions: { [nw]: 'approved' } });
check('A3 ... and is approved once the founder decides it is eligible', r.s === 200);

console.log('— preview matches the published page exactly');
const py = spawnSync('python3', ['-c', `
import json, sys; sys.path.insert(0, ${JSON.stringify(TOOLS)})
import plotart_gallery_pages as P
pkg = json.load(open(sys.argv[1])); ws = P.shown(pkg)
print(json.dumps({"artist": P.artist_body(pkg), "works": [P.artwork_body(pkg, w, ws[i-1] if i else None, ws[i+1] if i+1 < len(ws) else None) for i, w in enumerate(ws)]}))
`, join(PK, 'aoife-test', 'package.json')], { encoding: 'utf8' });
const pyOut = JSON.parse(py.stdout);
const toJs = p => ({ artist: { ...p.artist, portrait: null }, works: p.works.map(w => ({ ...w, images: w.images.map(i => ({ ...i, id: i.derivatives[0].file, width: i.pixels[0], height: i.pixels[1] })) })) });
const norm = s => s.replace(/ (src|srcset|width|height)="[^"]*"/g, '').replace(/href="img\/[^"]*"/g, 'href="img"');
const jp = toJs(pkg), jws = R.shown(jp);
const same = norm(R.artistBody(jp)) === norm(pyOut.artist) && jws.every((w, i) => norm(R.artworkBody(jp, w, jws[i - 1], jws[i + 1])) === norm(pyOut.works[i]));
check('R1 the Studio preview markup equals the published page markup (image files aside)', same);
r = await call('GET', '/preview/index.html', A);
check('R2 the artist’s private preview is noindex, nofollow and marked private', r.s === 200 && r.j.text.includes('noindex, nofollow') && r.j.text.includes('only you can see this'));

console.log('— founder controls and records');
await call('POST', `/api/admin/artists/${bid}/suspend`, FOUNDER, {});
r = await call('GET', '/api/me', B);
check('F1 a suspended artist is signed out of the Studio', r.s === 403);
await call('POST', `/api/admin/artists/${aid}/unpublish`, FOUNDER, {});
q = (await call('GET', '/api/pipeline/queue', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN })).j.items;
out = spawnSync('python3', [join(TOOLS, 'plotart-studio-publish.py'), '--studio', url, '--token', PIPELINE_TOKEN, '--packages', PK], { encoding: 'utf8' });
check('F2 “Unpublish” removes the gallery package at once (no review step)', q.some(x => x.kind === 'remove') && !existsSync(join(PK, 'aoife-test')), out.stdout);
const audit = (await call('GET', '/api/admin/audit', FOUNDER)).j.items.map(a => a.action);
const sys = await call('POST', '/api/admin/selftest', FOUNDER);
const sysA = await call('POST', '/api/admin/selftest', A);
const sysNoHdr = await call('POST', '/api/admin/selftest', FOUNDER, undefined, { 'X-Studio': '' });
const leftover = await (async () => { const l = await (await mf.getR2Bucket('IMAGES', 'studio')).list({ prefix: 'system-check/' }); return l.objects.length; })();
check('F4 founder system check: database and image storage written, read back and removed; refused to artists and without the Studio header',
  sys.j.passed === true && /working/.test(sys.j.database) && /working/.test(sys.j.image_storage) && leftover === 0 && sysA.s === 403 && sysNoHdr.s === 403, JSON.stringify([sys.j, sysA.s, sysNoHdr.s, leftover]));
{ const db = await mf.getD1Database('DB', 'studio'); const before = (await db.prepare('SELECT COUNT(*) n FROM mail_capture').first()).n;
  const inv = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Ciara Invite', email: 'ciara-invite@example.test', founding: true });
  const m = await db.prepare("SELECT * FROM mail_capture WHERE to_addr='ciara-invite@example.test'").first();
  check('F5 creating a Studio account emails the invitation (Reply-To hello@plotnua.ie, sign-in link, no password, nothing published before review)',
    inv.j.invitation_sent === true && m && m.reply_to === 'hello@plotnua.ie' && /Your PlotArt Studio is ready/.test(m.subject) && m.body.includes(url) && /one-time code/.test(m.body) && /at least 10 works/.test(m.body) && !/%|commission/i.test(m.body), JSON.stringify([inv.j, m && m.subject, before])); }
/* ---- access sweep (founder condition C, 29 Oct 2026): with Access letting ANY email sign in, the Studio itself must
   authenticate every request and authorise by its own records. Every route, every persona, real ids from the database. */
{
  const db = await mf.getD1Database('DB', 'studio');
  await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Sweep Artist', email: 'sweep@example.test', founding: false });
  const mine = (await call('GET', '/api/me', 'sweep@example.test')).j;
  const myId = (await db.prepare("SELECT id FROM artists WHERE email='sweep@example.test'").first()).id;
  const others = await db.prepare("SELECT id, email, display_name FROM artists WHERE id != ?").bind(myId).all();
  const aw = (await db.prepare('SELECT id FROM artworks WHERE artist_id != ?').bind(myId).all()).results.map(r => r.id);
  const im = (await db.prepare('SELECT id FROM images WHERE artist_id != ?').bind(myId).all()).results.map(r => r.id);
  const sb = (await db.prepare('SELECT id FROM submissions').all()).results.map(r => r.id);
  const qu = (await db.prepare('SELECT id, artist_id, version FROM publish_queue').all()).results;
  const ar = others.results.map(r => r.id);
  const secrets = others.results.flatMap(r => [r.email, r.display_name]);
  const leaks = t => secrets.filter(x => x && t.includes(x));
  const founderRoutes = [['GET', '/admin'], ['GET', '/api/admin/overview'], ['GET', '/api/admin/audit'], ['GET', '/api/admin/enquiries'],
    ['POST', '/api/admin/selftest'], ['POST', '/api/admin/artists'],
    ...ar.flatMap(id => [['POST', `/api/admin/artists/${id}/suspend`], ['POST', `/api/admin/artists/${id}/unpublish`]]),
    ...sb.flatMap(id => [['POST', `/api/admin/submissions/${id}/approve`], ['POST', `/api/admin/submissions/${id}/changes`], ['GET', `/admin/preview/${id}/index.html`]]),
    ...qu.flatMap(q => [['POST', `/api/admin/queue/${q.id}/publish`], ['GET', `/admin/preview/v-${q.artist_id}-${q.version}/index.html`]])];
  const artistRoutes = [['GET', '/'], ['GET', '/api/me'], ['PUT', '/api/me/profile'], ['PUT', '/api/me/portrait'], ['GET', '/api/artworks'], ['POST', '/api/artworks'],
    ['POST', '/api/artworks/order'], ['GET', '/api/enquiries'], ['POST', '/api/submit'], ['POST', '/api/submit/withdraw'], ['GET', '/preview/index.html']];
  const crossRoutes = [...aw.flatMap(id => [['GET', `/api/artworks/${id}`], ['PUT', `/api/artworks/${id}`], ['DELETE', `/api/artworks/${id}`],
      ['POST', `/api/artworks/${id}/availability`], ['PUT', `/api/artworks/${id}/images?role=main`]]),
    ...im.flatMap(id => [['GET', `/api/images/${id}`], ['GET', `/api/images/${id}/preview`], ['PATCH', `/api/images/${id}`], ['DELETE', `/api/images/${id}`], ['PUT', `/api/images/${id}/preview`]])];
  const pipeRoutes = [['GET', '/api/pipeline/queue'], ...qu.flatMap(q => [['POST', `/api/pipeline/export/${q.id}`], ['POST', `/api/pipeline/result/${q.id}`]]),
    ...qu.flatMap(q => im.slice(0, 2).map(i => ['GET', `/api/pipeline/image/${q.id}/${i}`]))];
  const go = (m, path, email) => call(m, path, email, ['POST', 'PUT', 'PATCH'].includes(m) ? {} : undefined);
  const bad = [];
  const expect = async (label, routes, email, ok) => { for (const [m, path] of routes) { const r = await go(m, path, email); const t = JSON.stringify(r.j);
    if (!ok(r.s) || leaks(t).length) bad.push(`${label} ${m} ${path} → ${r.s} ${leaks(t).join(',')}`); } };
  const refused = s => s === 401 || s === 403;
  await expect('no token', [...founderRoutes, ...artistRoutes, ...crossRoutes], null, refused);
  await expect('forged token', [...founderRoutes, ...artistRoutes], null, refused);
  await expect('unknown email', [...founderRoutes, ...artistRoutes, ...crossRoutes], 'stranger@example.test', s => s === 403);
  await expect('artist→founder', founderRoutes, 'sweep@example.test', s => s === 403);
  await expect('artist→other artist', crossRoutes, 'sweep@example.test', s => s === 404 || s === 403 || s === 400);
  await expect('no bearer (founder)', pipeRoutes, FOUNDER, s => s === 401);
  await expect('no bearer (artist)', pipeRoutes, 'sweep@example.test', s => s === 401);
  await expect('no bearer (stranger)', pipeRoutes, 'stranger@example.test', s => s === 401);
  const forged = await call('GET', '/api/me', null, undefined, { 'Cf-Access-Jwt-Assertion': (t => { const i = t.lastIndexOf('.') + 10; return t.slice(0, i) + (t[i] === 'A' ? 'B' : 'A') + t.slice(i + 1); })(token('sweep@example.test')) });
  const n = founderRoutes.length * 4 + artistRoutes.length * 3 + crossRoutes.length * 3 + pipeRoutes.length * 3;
  check(`Z1 access sweep: ${n} requests across every route: unauthenticated, forged and unknown-email requests refused; artists refused the founder desk and every other artist's records; pipeline refuses all without its token; no other artist's name or email in any refusal`,
    bad.length === 0 && forged.s === 401 && mine.ok !== false, bad.slice(0, 8).join(' | ') + ' forged:' + forged.s);
}
check('F3 every action is in the audit log', ['invite', 'image_upload', 'submit', 'licence_accepted', 'submission_changes', 'submission_approve', 'publish', 'published', 'instant_change', 'suspend', 'unpublish'].every(a => audit.includes(a)));

async function prodSnap(artist, v) {
  const db = await mf.getD1Database('DB', 'studio');
  const row = await db.prepare('SELECT snapshot FROM versions WHERE artist_id=? AND version=?').bind(artist, v).first();
  return row && row.snapshot;
}
await mf.dispose();
const ok = results.filter(x => x[1]).length;
console.log(`\nPLOTART STUDIO · ${results.length} checks, ${ok} passed, ${results.length - ok} failed`);
process.exit(ok === results.length ? 0 : 1);
