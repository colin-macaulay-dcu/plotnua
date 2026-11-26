// PROVE · PlotArt Studio · Report 36 (26 Nov 2026): privacy and consent (private answers never in any public output,
// withdrawal reaches the published gallery, older pages cannot bypass consent, public delivery stays off without fresh
// recorded consent) and test-account safeguards (founder-only identifiers, the pipeline's test-account list, builder and
// publisher fail closed on a missing list or a mismatch). Synthetic artists only; local Worker.
//   node test/prove-report36.mjs
import { execFileSync } from 'node:child_process';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname, TOOLS = HERE + '../../atlas-tools';
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
console.log('PROVE · PlotArt Studio · Report 36 (privacy, consent and test-account safeguards)');
const TEST = 'atestacct';
// public delivery switched ON here on purpose, to prove that the switch alone never shows anything
const { mf, url, db } = await start({ port: 8871, env: { TEST_ARTIST_IDS: TEST, DELIVERY_PUBLIC: 'true', INSTANT_AUTOPUBLISH: 'true' } });
const call = async (method, path, email, body, headers = {}) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json', ...headers };
  if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const PIPE = { Authorization: 'Bearer ' + PIPELINE_TOKEN };
const A = 'ana@example.test';
await seedPublished(db, { id: 'aana', slug: 'ana-test', email: A, name: 'Ana Test', works: 2 });
await seedPublished(db, { id: TEST, slug: 'makaulay-test', email: 'test@example.test', name: 'Test Account', works: 1 });

/* ---- P · private answers never leave the Studio in any public output ---- */
// sentinels: values that appear ONLY in private answers
await call('PUT', '/api/me/location', A, { country: 'IE', county: 'Longford', town: 'Granard', show_location: false, show_town: false });
await call('PUT', '/api/me/delivery', A, { scope: 'counties', counties: ['Leitrim', 'Monaghan'], methods: ['specialist'] });
await call('PUT', '/api/opportunities', A, { interests: ['art_for_hire', 'living_gallery'], artwork_county: 'Offaly', transport: ['specialist', 'deliver'],
  coverage: { mode: 'counties', counties: ['Carlow'] }, placement_area: 'own', note: 'SENTINEL-PRIVATE-NOTE', care_condition: true, public_display: true });
// a stored "show once available" tick from before Report 36 (written directly, as older answers are)
await db.prepare("UPDATE artist_delivery SET show_delivery = 1 WHERE artist_id = 'aana'").run();
await db.prepare("INSERT INTO artwork_hire (artwork_id, artist_id, offered, review_state, updated_at) VALUES ('waana1','aana',1,'approved',?)").bind(new Date().toISOString()).run().catch(() => {});
const outs = {};
for (const p of ['/api/pipeline/queue', '/api/pipeline/gallery-order', '/api/pipeline/featured-artists', '/api/pipeline/galleries', '/api/pipeline/homepage', '/api/pipeline/hire-catalogue', '/api/pipeline/test-artists'])
  outs[p] = (await call('GET', p, null, undefined, PIPE)).t;
const q = await db.prepare("SELECT id FROM publish_queue WHERE artist_id='aana' AND status IN ('ready','awaiting_founder') ORDER BY created_at DESC").first();
if (q) { await db.prepare("UPDATE publish_queue SET status='ready' WHERE id=?").bind(q.id).run(); outs.export = (await call('POST', '/api/pipeline/export/' + q.id, null, undefined, PIPE)).t; }
const pubTxt = Object.values(outs).join('\n');
const leaks = ['SENTINEL-PRIVATE-NOTE', 'Granard', 'Longford', 'Offaly', 'Leitrim', 'Monaghan', 'Carlow', 'specialist', 'care_condition', 'coverage', 'artwork_county', 'transport', 'methods', 'placement_area', 'show_delivery', 'delivers']
  .filter(x => pubTxt.includes(x));
check('P1 nothing private reaches any public output (every pipeline route and the gallery export): artwork location, placement area and transport, care, note, general delivery area and method, hidden county and town',
  !!outs.export && leaks.length === 0, JSON.stringify({ leaks, exported: !!outs.export }));
check('P2 public delivery stays off: the founder switch is on here and the artist has an earlier tick, yet no delivery area is published (fresh recorded consent is required)',
  !/"delivers"/.test(outs['/api/pipeline/hire-catalogue']) && (await call('GET', '/api/admin/locations', FOUNDER)).j.artists.find(a => a.id === 'aana').delivery_public === false);
const tick = await call('PUT', '/api/me/delivery', A, { scope: 'counties', counties: ['Leitrim', 'Monaghan'], methods: ['specialist'], show_delivery: true });
check('P3 an older page cannot switch public delivery on (a "show" tick is refused; only a withdrawal is accepted)', tick.s === 400 && /asked separately/.test(tick.j.error || ''));

/* ---- W · withdrawal reaches the published gallery ---- */
await call('PUT', '/api/me/location', A, { country: 'IE', county: 'Longford', town: 'Granard', show_location: true, show_town: true });
const v0 = (await db.prepare("SELECT MAX(version) v FROM versions WHERE artist_id='aana'").first()).v;
const showSnap = JSON.parse((await db.prepare("SELECT snapshot FROM versions WHERE artist_id='aana' AND version=?").bind(v0).first()).snapshot);
check('W1 a NEW showing does not travel as an instant update: it waits for the founder’s review as before', !showSnap.artist.location && !showSnap.artist.county_public);
// simulate the showing having been reviewed and published (a version that shows county, town and place)
const shown = { ...showSnap, artist: { ...showSnap.artist, county: 'Longford', county_public: true, location: { country: 'IE', county: 'Longford', town: 'Granard', line: 'Granard, Co. Longford, Ireland' } } };
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('aana', ?, ?, 'test', ?)").bind(v0 + 1, JSON.stringify(shown), new Date().toISOString()).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qshown','aana',?,'reviewed','published',?,?)").bind(v0 + 1, new Date().toISOString(), new Date().toISOString()).run();
const t1 = await call('PUT', '/api/me/location', A, { country: 'IE', county: 'Longford', town: 'Granard', show_location: true, show_town: false });
const s1 = JSON.parse((await db.prepare("SELECT snapshot FROM versions WHERE artist_id='aana' ORDER BY version DESC").first()).snapshot);
check('W2 removing the town reaches the published gallery at once (instant update): the place reads "Co. Longford, Ireland"', !!t1.j.instant_version && s1.artist.location && !s1.artist.location.town && s1.artist.location.line === 'Co. Longford, Ireland');
const t2 = await call('PUT', '/api/me/location', A, { country: 'IE', county: 'Longford', town: 'Granard', show_location: false, show_town: false });
const s2 = JSON.parse((await db.prepare("SELECT snapshot FROM versions WHERE artist_id='aana' ORDER BY version DESC").first()).snapshot);
const q2 = await db.prepare("SELECT id, status FROM publish_queue WHERE artist_id='aana' AND version=?").bind(t2.j.instant_version).first();
const ex2 = q2 ? (await call('POST', '/api/pipeline/export/' + q2.id, null, undefined, PIPE)).j : {};
check('W3 withdrawing "show where I’m based" reaches the published gallery at once: no location, county not public, and the export carries no county',
  !!t2.j.instant_version && !s2.artist.location && s2.artist.county_public === false && q2 && q2.status === 'ready' && ex2.gallery && ex2.gallery.artist.county === null && !JSON.stringify(ex2).includes('Longford'),
  JSON.stringify({ iv: t2.j.instant_version, q2, county: ex2.gallery && ex2.gallery.artist.county }));
const o1 = await call('PUT', '/api/opportunities/visibility', A, { show: false });
const s3 = JSON.parse((await db.prepare("SELECT snapshot FROM versions WHERE artist_id='aana' ORDER BY version DESC").first()).snapshot);
check('W4 withdrawing the public opportunities listing removes "Open to" from the next published version at once', o1.s === 200 && !('open_to' in s3.artist), o1.t);
const old = await call('PUT', '/api/me/profile', A, { county_public: true });
const locAfter = await db.prepare("SELECT show_location FROM artist_locations WHERE artist_id='aana'").first();
const s4 = JSON.parse((await db.prepare("SELECT snapshot FROM versions WHERE artist_id='aana' ORDER BY version DESC").first()).snapshot);
check('W5 the older "show my county" switch cannot publish anything by itself: it updates both answers together and, as a new showing, waits for review',
  old.s === 200 && locAfter.show_location === 1 && !s4.artist.county_public && !s4.artist.location);

/* ---- X · test-account identifiers and configuration ---- */
const adminJs = (await call('GET', '/assets/admin.js', FOUNDER)).t, adminPage = await call('GET', '/admin', 'ana@example.test');
const ov = (await call('GET', '/api/admin/overview', FOUNDER)).j;
check('X1 founder-only identifiers: the Review desk shows each artist’s Studio ID and gallery address with Copy buttons; an artist cannot open the Review desk',
  /data-copy="\$\{E\(a\.id\)\}"/.test(adminJs) && /data-copy="\$\{E\(a\.slug\)\}"/.test(adminJs) && ov.artists.some(a => a.id === TEST && a.slug === 'makaulay-test') && adminPage.s === 403, adminPage.s);
const ta = await call('GET', '/api/pipeline/test-artists', null, undefined, PIPE), taA = await call('GET', '/api/pipeline/test-artists', A);
check('X2 the publisher can read the Studio’s test accounts (identifiers only); nobody else can', ta.s === 200 && JSON.stringify(ta.j.artists) === JSON.stringify([{ id: TEST, slug: 'makaulay-test' }]) && taA.s >= 400, JSON.stringify([ta.j, taA.s]));
const py = `
import sys, json, os, tempfile, importlib.util
tools = sys.argv[1]; sys.path.insert(0, tools)
import plotart_gallery as G
out = {}
d = tempfile.mkdtemp(); f = os.path.join(d, 't.json')
G.TEST_ARTISTS_FILE = os.path.join(d, 'missing.json')
try: G.test_artists(); out['missing'] = 'allowed'
except G.Refused: out['missing'] = 'refused'
sys.argv = ['publish', '--studio', 'http://127.0.0.1:9', '--token', 't', '--simulate']
spec = importlib.util.spec_from_file_location('pub', os.path.join(tools, 'plotart-gallery-publish.py')); pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(pub)
studio = json.loads(sys.argv[-1]) if False else None
def run(builder, studio_list):
    json.dump(builder, open(f, 'w')); G.TEST_ARTISTS_FILE = f
    pub.call = lambda m, p, b=None, raw=False: {'ok': True, 'artists': studio_list}
    try: pub.test_accounts_consistent(); return 'ok'
    except G.Refused: return 'refused'
S = [{'id': 'atestacct', 'slug': 'makaulay-test'}]
out['match'] = run({'artist_ids': ['atestacct'], 'slugs': ['makaulay-test']}, S)
out['studio_only'] = run({'artist_ids': [], 'slugs': []}, S)
out['slug_missing'] = run({'artist_ids': ['atestacct'], 'slugs': []}, S)
out['builder_first'] = run({'artist_ids': ['atestacct'], 'slugs': ['makaulay-test']}, [])
out['none'] = run({'artist_ids': [], 'slugs': []}, [])
print(json.dumps(out))`;
const r = JSON.parse(execFileSync('python3', ['-c', py, TOOLS], { encoding: 'utf8' }).trim().split('\n').pop());
check('X3 the builder fails closed when its test-account list is missing', r.missing === 'refused', JSON.stringify(r));
check('X4 the publisher refuses to publish anything when the Studio names a test account the builder does not (id or gallery address); the builder-first order and an empty pair are fine',
  r.match === 'ok' && r.studio_only === 'refused' && r.slug_missing === 'refused' && r.builder_first === 'ok' && r.none === 'ok', JSON.stringify(r));
{ // the founder corrects the test account to Gallery Artist from the Review desk (button offered only for the test account)
  const { createRequire } = await import('node:module');
  const { chromium } = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json')('playwright');
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1400, height: 1000 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
  const pg = await ctx.newPage(); pg.on('dialog', d => d.accept());
  await pg.goto(url + '/admin', { waitUntil: 'networkidle' }); await pg.waitForTimeout(600);
  const buttons = await pg.locator('[data-testprog]').count(), forTest = await pg.locator(`[data-testprog="${TEST}"]`).count();
  await pg.click(`[data-testprog="${TEST}"]`); await pg.waitForTimeout(1200);
  const row = await db.prepare('SELECT founding, founding_number FROM artists WHERE id=?').bind(TEST).first();
  const tr = await db.prepare('SELECT track FROM artist_terms WHERE artist_id=?').bind(TEST).first();
  check('X5 the programme correction is a founder button offered only for the test account; it asks first, then the account is a Gallery Artist with no Founding number',
    buttons === 1 && forTest === 1 && row.founding === 0 && row.founding_number === null && tr && tr.track === 'gallery_artist', JSON.stringify({ buttons, forTest, row, tr }));
  await b.close();
}
await mf.dispose();
console.log(`\n${results.filter(Boolean).length}/${results.length} passed`);
process.exit(results.every(Boolean) ? 0 : 1);
