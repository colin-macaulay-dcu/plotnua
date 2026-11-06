// PROVE · the complete PlotArt artist journey (Phase 3, 29 Oct 2026). Synthetic artist and buyer; local only.
//   node test/prove-journey.mjs --release RELEASE_TREE
// A temporary git copy of RELEASE_TREE stands in for main. The content pipeline (atlas-tools/plotart-gallery-publish.py)
// runs in --simulate mode against it: it commits and runs every guard exactly as in production, but does not push.
import { acceptAgreement } from './agree.mjs';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { execFileSync, spawnSync, execSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const REL = process.argv.includes('--release') ? process.argv[process.argv.indexOf('--release') + 1] : null;
if (!REL) { console.log('usage: node test/prove-journey.mjs --release DIR'); process.exit(2); }
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const TMP = mkdtempSync(join(tmpdir(), 'pa-journey-'));
execFileSync('python3', ['-c', `
import random, sys
from PIL import Image, ImageDraw
for i in range(1, 13):
    r = random.Random(500 + i); w, h = 2400, 1800 if i % 2 else 2200
    im = Image.new("RGB", (w, h), tuple(r.randrange(40, 200) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(30):
        x, y = r.randrange(w), r.randrange(h); c = tuple(r.randrange(256) for _ in range(3))
        (d.ellipse if r.random() < .5 else d.rectangle)((x, y, x + r.randrange(w // 6, w // 2), y + r.randrange(h // 6, h // 2)), outline=c, width=r.randrange(10, 40))
    im.save(f"{sys.argv[1]}/j{i}.jpg", "JPEG", quality=90)
r = random.Random(499); pw, ph = 1600, 2000           # the artist's portrait (portrait format, larger than shown)
im = Image.new("RGB", (pw, ph), (90, 80, 70)); d = ImageDraw.Draw(im)
for _ in range(20):
    x, y = r.randrange(pw), r.randrange(ph); d.ellipse((x, y, x + r.randrange(100, 600), y + r.randrange(100, 600)), outline=tuple(r.randrange(256) for _ in range(3)), width=24)
im.save(f"{sys.argv[1]}/portrait.jpg", "JPEG", quality=90)
`, TMP]);

// main, after the opening release: a git copy of the release tree, with the relay switched on for this test
const SITE = join(TMP, 'site');
execSync(`mkdir -p ${SITE} && git -C ${REL} archive HEAD | tar -x -C ${SITE}`);
// the gallery opening release: opening wording on every PlotArt page, switch on, manifest rebuilt
const TOOLS = process.argv.includes('--gallery-tools') ? process.argv[process.argv.indexOf('--gallery-tools') + 1] : null;
if (!TOOLS) { console.log('usage: node test/prove-journey.mjs --release DIR --gallery-tools DIR'); process.exit(2); }
// Galleries opened on main on 29 Oct 2026 (4d5edf3): when the release tree is already open, test it exactly as it is.
if (JSON.parse(readFileSync(join(SITE, 'atlas-tools/release/plotart-launch-switches.json'), 'utf8')).galleries_open !== true) {
  const swp = join(SITE, 'atlas-tools/release/plotart-launch-switches.json'), sw = JSON.parse(readFileSync(swp, 'utf8')); sw.galleries_open = true;
  writeFileSync(swp, JSON.stringify(sw, null, 2));
  const lj = join(TOOLS, '../plotart/data/launch.json'), keep = readFileSync(lj);
  writeFileSync(lj, JSON.stringify(sw));
  const OB = join(TMP, 'opening');
  const b = spawnSync('python3', [join(TOOLS, 'build-plotart.py'), '--launch', '--out', OB], { encoding: 'utf8' });
  writeFileSync(lj, keep);
  if (b.status) { console.log(b.stdout + b.stderr); process.exit(1); }
  for (const f of ['index.html', 'founding-25.html', 'living-gallery.html', 'gallery/index.html', 'assets/plotart.css']) writeFileSync(join(SITE, 'plotart', f), readFileSync(join(OB, 'plotart', f)));
  execFileSync('python3', ['-c', `
import json, hashlib, os, re
m = json.load(open("atlas-tools/release/plotart-launch-manifest.json")); files = {}
for dp, _, fs in os.walk("plotart"):
    for f in fs:
        rel = os.path.relpath(os.path.join(dp, f), "plotart")
        if not rel.startswith("artists/"): files[rel] = hashlib.sha256(open(os.path.join(dp, f), "rb").read()).hexdigest()
m["files"] = files
raw = open("plotart/gallery/index.html", "rb").read()
m["outside_grid"] = {"gallery/index.html": hashlib.sha256(re.sub(rb'<!-- pa-vg-collection:begin -->.*?(?=<!-- pa-vg-collection:end -->)', b'<!-- pa-vg-collection:begin --><!-- collection -->', raw, flags=re.S)).hexdigest()}
json.dump(m, open("atlas-tools/release/plotart-launch-manifest.json", "w"), indent=2)
`], { cwd: SITE });
}
const cfg = join(SITE, 'atlas-tools/release/plotart-gallery-config.json');
writeFileSync(cfg, JSON.stringify({ ...JSON.parse(readFileSync(cfg, 'utf8')), enquiry_endpoint: 'http://127.0.0.1:8796/v1/enquiry' }, null, 2));
const git = (...a) => execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@plotnua.invalid', ...a], { cwd: SITE, encoding: 'utf8' }).trim();
git('init', '-q'); git('add', '-A'); git('commit', '-q', '-m', 'main after the opening release (test copy)');
const BASE = git('rev-parse', 'HEAD');

const { mf, url, enquiryWorker } = await start({ port: 8796, env: { INSTANT_AUTOPUBLISH: 'true' }, enquiry: {} });
const db = await mf.getD1Database('DB', 'studio');
const call = async (method, path, email, body, raw) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': raw ? 'application/octet-stream' : 'application/json' },
    body: raw || (body === undefined ? undefined : JSON.stringify(body)) });
  return { s: r.status, j: await r.json().catch(() => ({})) };
};
const publish = () => spawnSync('python3', ['atlas-tools/plotart-gallery-publish.py', '--studio', url, '--token', PIPELINE_TOKEN, '--simulate'], { cwd: SITE, encoding: 'utf8' });
const page = p => existsSync(join(SITE, 'plotart', p)) ? readFileSync(join(SITE, 'plotart', p), 'utf8') : '';
const enquire = (body, origin = 'https://plotnua.ie') => mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  .then(async r => ({ s: r.status, j: await r.json() }));
const A = 'niamh@example.test';

console.log('PROVE · the complete artist journey\n— selection to first publication');
let r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Niamh Synthetic', email: A, application_ref: 'F25-261029-1A2B3C' });
check('J1 the founder creates the selected artist’s Studio account', r.s === 200 && r.j.slug === 'niamh-synthetic');
r = await call('GET', '/api/me', A);
check('J2 the artist signs in (Access) and lands on “Not published yet”', r.s === 200 && r.j.status.state === 'draft' && r.j.artist.account_status === 'active');
await call('PUT', '/api/me/profile', A, { practice: 'Painter', medium: 'painting', county: 'Clare', county_public: true, statement: 'Burren light, painted slowly.',
  bio: 'Niamh Synthetic is an invented test artist. She paints the limestone and light of the Burren in thin layers of oil, slowly, over many months.' });
// a portrait (PLOTART-PUBLISHING-PORTRAIT-001: galleries with a portrait were refused by the provenance guard)
const por = await call('PUT', '/api/me/portrait', A, undefined, readFileSync(join(TMP, 'portrait.jpg')));
await call('PATCH', `/api/images/${por.j.id}`, A, { alt: 'Portrait of the synthetic test artist in her studio', photographer: 'self' });
const works = [];
for (let i = 1; i <= 10; i++) {
  const id = (await call('POST', '/api/artworks', A)).j.id; works.push(id);
  await call('PUT', `/api/artworks/${id}`, A, { title: `Burren ${i}`, year: 2026, medium: 'Oil on linen', h_cm: 50 + i, w_cm: 70, price_eur: 800 + i * 100, ai_involvement: 'none',
    description: `Test painting ${i}: limestone pavement in late light.` });
  const up = await call('PUT', `/api/artworks/${id}/images?role=main`, A, undefined, readFileSync(join(TMP, `j${i}.jpg`)));
  await call('PATCH', `/api/images/${up.j.id}`, A, { alt: `Test painting ${i}: grey limestone shapes`, photographer: 'self' });
}
const accA = await acceptAgreement(mf, url, A);
r = await call('POST', '/api/submit', A, { accept_licence: true, note: 'Ready when you are.' });
check('J3 the artist accepts the Founding Artist Agreement (one tick, both documents) and submits ten complete works', accA.s === 200 && r.s === 200 && r.j.tier === 'full');
const sid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions[0].id;
await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve', message: 'Beautiful. Welcome to PlotArt.' });
const q1 = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue[0];
r = publish();
check('J4 before the founder presses Publish, the pipeline publishes nothing', /nothing to publish/.test(r.stdout) && git('rev-parse', 'HEAD') === BASE, r.stdout + r.stderr);
// Gallery order (31 Oct 2026): the founder reserves position 01 (private note) before the first publication.
await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: 'Held for a named artist (private)' }] });
await call('POST', `/api/admin/queue/${q1.id}/publish`, FOUNDER, {});
r = publish();
const head1 = git('rev-parse', 'HEAD');
check('J5 Publish → the pipeline commits the gallery and every guard passes (boundary, L1–L14, provenance, image rights)', r.status === 0 && /verified \(simulated\)/.test(r.stdout) && head1 !== BASE, r.stdout + r.stderr);
const changed = git('diff', '--name-only', BASE, head1).split('\n');
check('J6 the commit touches only the artist’s folder, the Virtual Gallery grid and image records', changed.every(f => f.startsWith('plotart/artists/niamh-synthetic/') || f === 'plotart/gallery/index.html' || f === 'image-provenance-records.json'), changed.join(' '));
check('J7 the gallery, its 10 artwork pages and its Virtual Gallery card are on the site', page('artists/niamh-synthetic/index.html').includes('Niamh Synthetic') &&
  readdirSync(join(SITE, 'plotart/artists/niamh-synthetic')).filter(f => f.endsWith('.html')).length === 11 && page('gallery/index.html').includes('href="../artists/niamh-synthetic/"'));
check('J8 published images carry no metadata and match their provenance records', spawnSync('python3', ['-c', `
import json,hashlib,glob,sys
from PIL import Image
recs={r["asset"]:r for r in json.load(open("image-provenance-records.json"))["records"] if r.get("class")=="ARTIST_SUPPLIED_ARTWORK"}
fs=glob.glob("plotart/artists/niamh-synthetic/img/*.webp")
ok=len(fs)>=20 and all(recs["plotart/"+f.split("plotart/",1)[1]]["sha256"]==hashlib.sha256(open(f,"rb").read()).hexdigest() and not Image.open(f).getexif() and "icc_profile" not in Image.open(f).info for f in fs)
sys.exit(0 if ok else 1)`], { cwd: SITE }).status === 0);
check('J8b the portrait is published once, at the size the page shows (600 px), with exactly one provenance record (subject portrait)', spawnSync('python3', ['-c', `
import json,glob,re,sys
recs=[r for r in json.load(open("image-provenance-records.json"))["records"] if r.get("class")=="ARTIST_SUPPLIED_ARTWORK" and r.get("artist_slug")=="niamh-synthetic" and r.get("subject")=="portrait"]
fs=sorted(glob.glob("plotart/artists/niamh-synthetic/img/portrait*"))
html=open("plotart/artists/niamh-synthetic/index.html",encoding="utf-8").read()
m=re.search(r'class="pa-ag-portrait"><img src="img/([^"]+)" width="(\\d+)" height="(\\d+)"',html)
ok=bool(m) and len(fs)==1 and fs[0].endswith("/"+m.group(1)) and len(recs)==1 and recs[0]["asset"]=="plotart/artists/niamh-synthetic/img/"+m.group(1) and max(int(m.group(2)),int(m.group(3)))==600 and recs[0]["photographer"]=="self"
print(fs, [r["asset"] for r in recs], m.groups() if m else None)
sys.exit(0 if ok else 1)`], { cwd: SITE }).status === 0);
r = await call('GET', '/api/me', A);
check('J9 the artist’s Studio shows “Live” with the founding year started', r.j.status.state === 'live' && r.j.artist.first_published_at);
check('J10 the live artwork pages carry the enquiry form (relay on) with the email fallback', page('artists/niamh-synthetic/burren-1.html').includes('class="pa-enq"') && page('artists/niamh-synthetic/burren-1.html').includes('mailto:hello@plotnua.ie'));

console.log('— a buyer enquires; the artist replies directly');
const wid = works[0];
r = await enquire({ ref: `PA-niamh-synthetic-${wid}`, notice: 'PA-ENQ-2026-10-29', name: 'Test Buyer', email: 'buyer@example.test', message: 'Is Burren 1 still available, and could it be shipped to Cork?', website: '' });
check('E1 an enquiry from the artwork page is accepted with a reference', r.s === 200 && /^PA-E-\d{6}-[0-9A-F]{6}$/.test(r.j.reference), JSON.stringify(r));
const ref = r.j.reference;
const mails = (await db.prepare("SELECT * FROM mail_capture WHERE subject LIKE '%enquiry%' ORDER BY id").all()).results;
check('E2 the artist is emailed the enquiry with Reply-To the buyer (the founder is not an intermediary)', mails.length === 2 && mails[0].to_addr === A && mails[0].reply_to === 'buyer@example.test' && mails[0].body.includes('could it be shipped'));
check('E3 the buyer gets a receipt that never shows the artist’s email address', mails[1].to_addr === 'buyer@example.test' && !mails[1].body.includes(A) && mails[1].body.includes(ref));
r = await call('GET', '/api/enquiries', A);
check('E4 the enquiry is in the artist’s Studio, with a reply link', r.j.items.length === 1 && r.j.items[0].reference === ref);
r = await call('GET', '/api/admin/enquiries', FOUNDER);
check('E5 the founder has the record (reference, date, artist, artwork) for founding-period enquiries', r.j.items.length === 1 && r.j.items[0].reference === ref);
r = await enquire({ ref: `PA-niamh-synthetic-${wid}`, notice: 'PA-ENQ-2026-10-29', name: 'X', email: 'x@example.test', message: 'A message long enough.' }, 'https://evil.example');
check('E6 an enquiry from any other website is refused', r.s === 403);
r = await enquire({ ref: 'PA-nobody-here', notice: 'PA-ENQ-2026-10-29', name: 'X', email: 'x@example.test', message: 'A message long enough.' });
check('E7 an enquiry for an unpublished gallery is refused', r.s === 404);
const before = (await db.prepare('SELECT COUNT(*) AS n FROM enquiries').first()).n;
r = await enquire({ ref: `PA-niamh-synthetic`, notice: 'PA-ENQ-2026-10-29', name: 'Bot', email: 'bot@example.test', message: 'Buy cheap things now!!', website: 'http://spam' });
check('E8 a bot filling the hidden field is silently dropped (nothing stored, nothing sent)', r.s === 200 && (await db.prepare('SELECT COUNT(*) AS n FROM enquiries').first()).n === before);
r = await enquire({ ref: `PA-niamh-synthetic-${wid}`, notice: 'PA-ENQ-2026-10-29', name: 'Test Buyer', email: 'not-an-email', message: 'A message long enough.' });
check('E9 an invalid email address is refused with a clear message', r.s === 400 && /email/.test(r.j.error));

console.log('— after publication: instant, reviewed and removal');
await call('POST', `/api/artworks/${wid}/availability`, A, { availability: 'sold' });
const imgBefore = readdirSync(join(SITE, 'plotart/artists/niamh-synthetic/img')).map(f => readFileSync(join(SITE, 'plotart/artists/niamh-synthetic/img', f)).toString('base64')).join();
r = publish();
const imgAfter = readdirSync(join(SITE, 'plotart/artists/niamh-synthetic/img')).map(f => readFileSync(join(SITE, 'plotart/artists/niamh-synthetic/img', f)).toString('base64')).join();
check('I1 “Sold” publishes automatically (switch on in this test) as an INSTANT content release', r.status === 0 && /instant · verified/.test(r.stdout) && page('artists/niamh-synthetic/burren-1.html').includes('is-sold'), r.stdout + r.stderr);
check('I2 ... re-processing is exact: no image changed', imgBefore === imgAfter);
r = await enquire({ ref: `PA-niamh-synthetic-${wid}`, notice: 'PA-ENQ-2026-10-29', name: 'Late Buyer', email: 'late@example.test', message: 'Is this one still for sale please?' });
check('I3 a sold work no longer takes enquiries (the buyer is pointed to other work)', r.s === 409);
await call('PUT', `/api/artworks/${works[1]}`, A, { price_eur: 1450 });
r = publish();
check('I4 a price change does not publish by itself (it waits for review)', /nothing to publish/.test(r.stdout));
const s2 = (await call('POST', '/api/submit', A, {})).j.id;
await call('POST', `/api/admin/submissions/${s2}/decision`, FOUNDER, { decision: 'approve' });
const q2 = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(q => q.status === 'awaiting_founder');
await call('POST', `/api/admin/queue/${q2.id}/publish`, FOUNDER, {});
r = publish();
check('I5 ... and publishes after the founder approves and presses Publish', r.status === 0 && page('artists/niamh-synthetic/burren-2.html').includes('€1,450'), r.stdout + r.stderr);
// ---- Gallery order (founder decision 31 Oct 2026)
// Direction C2 (5 Nov 2026): positions 01-25 are read from the index of founding positions ('card:<slug>' for a published
// gallery, 'reserved', 'prep' for an artist placed but not published, 'space' for an available position), then any open
// gallery on the wall that holds no position.
const gridItems = () => {
  const vg = page('gallery/index.html');
  const plan = [...((vg.match(/<ol class="pa-vgc-plan"[^>]*>([\s\S]*?)\n    <\/ol>/) || [, ''])[1]).matchAll(/<li class="pa-vgc-pos is-(pub|res|prep|av)">([\s\S]*?)<\/li>/g)]
    .map(m => m[1] === 'pub' ? 'card:' + ((m[2].match(/artists\/([a-z0-9-]+)\//) || [])[1]) : m[1] === 'res' ? 'reserved' : m[1] === 'prep' ? 'prep' : 'space');
  const extra = [...vg.matchAll(/<span class="pa-vgc-n" aria-hidden="true"><\/span><div><h3 class="pa-vgc-name"><a href="\.\.\/artists\/([a-z0-9-]+)\//g)].map(m => 'card:' + m[1]);
  return plan.concat(extra);
};
let gi = gridItems();
check('O1 position 01 shows RESERVED with no name; the first published Founding Artist took the lowest open position (02)',
  gi.length === 25 && gi[0] === 'reserved' && gi[1] === 'card:niamh-synthetic' && gi.slice(2).every(x => x === 'space') && !page('gallery/index.html').includes('Held for'), gi.join(','));
check('O2 the order the pipeline receives carries positions and gallery addresses only, never the private note',
  await (async () => { const t = await (await mf.dispatchFetch(url + '/api/pipeline/gallery-order', { headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } })).text();
    return !t.includes('Held for') && !/"note"/.test(t) && JSON.parse(t).positions.some(e => e.position === 2 && e.slug === 'niamh-synthetic'); })());
check('O3 after a reviewed update is published, the artist keeps position 02 (no automatic reordering)', gridItems()[1] === 'card:niamh-synthetic');
const aid = (await call('GET', '/api/admin/gallery-order', FOUNDER)).j.positions[1].artist_id;
r = await call('PUT', '/api/admin/gallery-order', A, { positions: [{ position: 9, state: 'artist', artist_id: aid }] });
check('O4 the artist cannot change gallery positions (403)', r.s === 403);
const headO = git('rev-parse', 'HEAD');
await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: 'Held for a named artist (private)' }, { position: 7, state: 'artist', artist_id: aid }] });
r = publish(); gi = gridItems();
check('O5 the founder moves the artist to 07: the next pipeline run commits ONLY the grid and every guard passes',
  r.status === 0 && /gallery order · verified \(simulated\)/.test(r.stdout) && gi[0] === 'reserved' && gi[6] === 'card:niamh-synthetic' && gi.filter(x => x.startsWith('card')).length === 1 &&
  git('diff', '--name-only', headO, 'HEAD') === 'plotart/gallery/index.html', r.stdout + r.stderr + gi.join(','));
r = publish();
check('O6 an unchanged order publishes nothing', /nothing to publish/.test(r.stdout) && !/gallery order/.test(r.stdout), r.stdout + r.stderr);
// One-artwork galleries (founder decision 1 Nov 2026): a Founding Artist may open with a single work.
console.log('— a one-artwork Founding gallery');
const B = 'orla@example.test';
await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Orla Synthetic', email: B });
await call('PUT', '/api/me/profile', B, { practice: 'Painter', medium: 'painting', county: 'Kerry', county_public: true,
  bio: 'Orla Synthetic is an invented test artist. She paints a single large view of the sea at a time, building it up over a whole season.' });
const ow = (await call('POST', '/api/artworks', B)).j.id;
await call('PUT', `/api/artworks/${ow}`, B, { title: 'Atlantic', year: 2026, medium: 'Oil on linen', h_cm: 90, w_cm: 120, price_eur: 2400, ai_involvement: 'none',
  description: 'Test painting: the Atlantic in winter light.' });
const oup = await call('PUT', `/api/artworks/${ow}/images?role=main`, B, undefined, readFileSync(join(TMP, 'j11.jpg')));
await call('PATCH', `/api/images/${oup.j.id}`, B, { alt: 'Test painting: a grey-blue sea under a low sky', photographer: 'self' });
await acceptAgreement(mf, url, B);
r = await call('GET', '/api/me', B);
check('S1 a Founding Artist with ONE complete artwork has nothing blocking submission (no minimum)', r.j.artist.founding && r.j.status.problems.length === 0 && r.j.status.counts.works === 1 && r.j.status.counts.min === undefined, JSON.stringify(r.j.status.problems));
r = await call('POST', '/api/submit', B, { accept_licence: true });
check('S2 ... submits it, accepting the licence (the licence is still required)', r.s === 200 && r.j.tier === 'full', JSON.stringify(r.j));
const osid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(x => x.display_name === 'Orla Synthetic').id;
await call('POST', `/api/admin/submissions/${osid}/decision`, FOUNDER, { decision: 'approve', message: 'Welcome.' });
const oq = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.display_name === 'Orla Synthetic' || x.slug === 'orla-synthetic') || (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.slice(-1)[0];
r = publish();
check('S3 the approved gallery is NOT published until the founder presses Publish', !existsSync(join(SITE, 'plotart/artists/orla-synthetic')), r.stdout + r.stderr);
await call('POST', `/api/admin/queue/${oq.id}/publish`, FOUNDER, {});
r = publish(); gi = gridItems();
check('S4 Publish → the one-artwork gallery passes every publication guard and goes live', r.status === 0 && / v1 · reviewed · verified \(simulated\)/.test(r.stdout) && existsSync(join(SITE, 'plotart/artists/orla-synthetic/atlantic.html')), r.stdout + r.stderr);
check('S5 its gallery page says “1 artwork”, has one artwork page, and the larger single-work image size', page('artists/orla-synthetic/index.html').includes('<p>1 artwork</p>') &&
  readdirSync(join(SITE, 'plotart/artists/orla-synthetic')).filter(f => f.endsWith('.html')).length === 2 && page('artists/orla-synthetic/index.html').includes('sizes="(max-width:639px) 92vw, 720px"'));
check('S6 it takes the lowest open position (02); 01 stays reserved; the other artist keeps 07', gi[0] === 'reserved' && gi[1] === 'card:orla-synthetic' && gi[6] === 'card:niamh-synthetic', gi.join(','));
r = await call('GET', '/api/me', B);
check('S7 the artist’s Studio shows “Live”, as a Founding Artist', r.j.status.state === 'live' && r.j.artist.founding);
console.log('— a live gallery whose only work is withdrawn');
const oid = (await db.prepare("SELECT id FROM artists WHERE slug='orla-synthetic'").first()).id;
await call('PUT', `/api/admin/artists/${oid}/founding-number`, FOUNDER, { founding_number: 7 });
const recsFor = slug => JSON.parse(readFileSync(join(SITE, 'image-provenance-records.json'), 'utf8')).records.filter(x => x.artist_slug === slug).length;
const oHead = git('rev-parse', 'HEAD');
await call('POST', `/api/artworks/${ow}/archive`, B, { archived: true });
r = publish(); gi = gridItems();
const ofiles = existsSync(join(SITE, 'plotart/artists/orla-synthetic')) ? readdirSync(join(SITE, 'plotart/artists/orla-synthetic'), { recursive: true }).map(String) : [];
check('Z1 withdrawing the final artwork publishes straight away and every guard passes', r.status === 0 && / v\d+ · instant · verified \(simulated\)/.test(r.stdout) && git('rev-parse', 'HEAD') !== oHead, r.stdout + r.stderr);
check('Z2 the withdrawn artwork is no longer public: its page, its images and its image records are gone', !existsSync(join(SITE, 'plotart/artists/orla-synthetic/atlantic.html')) &&
  !ofiles.some(f => /\.(webp|jpe?g|png)$/.test(f)) && recsFor('orla-synthetic') === 0, ofiles.join(','));
const og = page('artists/orla-synthetic/index.html');
check('Z3 the gallery stays live with its profile and biography, and shows the empty state', og.includes('Orla Synthetic') && og.includes('paints a single large view of the sea') &&
  og.includes('class="pa-ag-empty"') && og.includes('New work coming soon') && og.includes('None on show right now') && !og.includes('pa-ag-grid"'));
check('Z4 the artist keeps the Founding badge and gallery position 02 (01 still reserved); the card shows the empty state', og.includes('pa-gcard-badge">Founding Artist') &&
  gi[0] === 'reserved' && gi[1] === 'card:orla-synthetic' && page('gallery/index.html').includes('<div class="pa-vgc-art is-empty"><span>New work coming soon</span></div>'), gi.join(','));
r = await call('GET', '/api/me', B);
const fnum = (await db.prepare("SELECT founding, founding_number FROM artists WHERE id=?").bind(oid).first());
check('Z5 the Studio still shows Live; Founding status and the permanent Founding number (7) are unchanged', r.j.status.state === 'live' && fnum.founding === 1 && fnum.founding_number === 7);
const nw = (await call('POST', '/api/artworks', B)).j.id;
await call('PUT', `/api/artworks/${nw}`, B, { title: 'Spring Tide', year: 2026, medium: 'Oil on linen', h_cm: 60, w_cm: 80, price_eur: 1800, ai_involvement: 'none', description: 'Test painting: a calmer sea in spring.' });
const nup = await call('PUT', `/api/artworks/${nw}/images?role=main`, B, undefined, readFileSync(join(TMP, 'j12.jpg')));
await call('PATCH', `/api/images/${nup.j.id}`, B, { alt: 'Test painting: a pale green sea', photographer: 'self' });
r = await call('POST', '/api/submit', B, { accept_licence: true });
const r2 = publish();
check('Z6 a new artwork added later goes to review first: nothing is published before approval', r.s === 200 && r.j.tier === 'full' && !existsSync(join(SITE, 'plotart/artists/orla-synthetic/spring-tide.html')), JSON.stringify(r.j) + r2.stdout);
const zs = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(x => x.display_name === 'Orla Synthetic');
await call('POST', `/api/admin/submissions/${zs.id}/decision`, FOUNDER, { decision: 'approve', message: 'Lovely.' });
const zq = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.filter(x => x.display_name === 'Orla Synthetic' && x.status === 'awaiting_founder').pop();
await call('POST', `/api/admin/queue/${zq.id}/publish`, FOUNDER, {});
r = publish(); gi = gridItems();
check('Z7 ... and after approval and Publish it is live again: one work, empty state gone, still at position 02', r.status === 0 && existsSync(join(SITE, 'plotart/artists/orla-synthetic/spring-tide.html')) &&
  page('artists/orla-synthetic/index.html').includes('<p>1 artwork</p>') && !page('artists/orla-synthetic/index.html').includes('pa-ag-empty') && gi[1] === 'card:orla-synthetic', r.stdout + r.stderr + gi.join(','));
await call('POST', `/api/artworks/${works[9]}/archive`, A, { archived: true });
r = publish();
check('I6 removing a work publishes straight away; no minimum applies (9 works left)', r.status === 0 && !existsSync(join(SITE, 'plotart/artists/niamh-synthetic/burren-10.html')), r.stdout + r.stderr);
r = await call('GET', '/api/me', A);
check('I7 the artist sees no minimum, warning or top-up date', r.j.status.below_minimum === undefined && r.j.status.top_up_by === undefined && r.j.status.counts.min === undefined);
await mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
const remind = (await db.prepare("SELECT * FROM mail_capture WHERE subject LIKE '%time to add a work%'").all()).results;
check('I8 the daily job sends no top-up reminder', remind.length === 0);

console.log('— fail-safe');
const mp = join(SITE, 'atlas-tools/release/plotart-launch-manifest.json');
const man = JSON.parse(readFileSync(mp, 'utf8')); man.files['index.html'] = '0'.repeat(64); writeFileSync(mp, JSON.stringify(man, null, 2));
git('commit', '-qam', 'test: a broken manifest (simulates any guard failing)');
const broken = git('rev-parse', 'HEAD');
await call('POST', `/api/artworks/${works[2]}/availability`, A, { availability: 'reserved' });
r = publish();
const qf = (await db.prepare("SELECT status, detail FROM publish_queue ORDER BY updated_at DESC LIMIT 1").first());
check('F1 if any guard refuses, nothing is published: the commit is dropped and the Studio is told why', r.status === 1 && git('rev-parse', 'HEAD') === broken && qf.status === 'failed' && /launch guard refused/.test(qf.detail), r.stdout + qf.detail);
writeFileSync(join(SITE, 'stray.txt'), 'x');
r = publish();
check('F2 the pipeline refuses to run on an unclean checkout', r.status !== 0 && /not clean/.test(r.stdout + r.stderr));
execSync(`rm ${join(SITE, 'stray.txt')}`); git('reset', '-q', '--hard', 'HEAD~1');

console.log('— unpublish');
await call('POST', '/api/admin/artists/' + (await db.prepare("SELECT id FROM artists WHERE slug='niamh-synthetic'").first()).id + '/unpublish', FOUNDER, {});
await call('POST', '/api/admin/artists/' + (await db.prepare("SELECT id FROM artists WHERE slug='orla-synthetic'").first()).id + '/unpublish', FOUNDER, {});
r = publish();
const recsLeft = JSON.parse(readFileSync(join(SITE, 'image-provenance-records.json'), 'utf8')).records.filter(x => x.artist_slug === 'niamh-synthetic').length;
check('U1 “Unpublish” removes the gallery, its card (25 empty spaces again) and its image records', r.status === 0 && !existsSync(join(SITE, 'plotart/artists/niamh-synthetic')) &&
  (page('gallery/index.html').match(/<li class="pa-vgc-pos is-(?:av|res|prep)">/g) || []).length === 25 && !/artists\/(niamh|orla)-synthetic\//.test(page('gallery/index.html')) && recsLeft === 0, r.stdout + r.stderr);

await mf.dispose();
const ok = results.filter(Boolean).length;
console.log(`\nPLOTART JOURNEY · ${results.length} checks, ${ok} passed, ${results.length - ok} failed`);
process.exit(ok === results.length ? 0 : 1);
