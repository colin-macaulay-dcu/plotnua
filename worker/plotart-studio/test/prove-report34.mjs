// PROVE · PlotArt Studio · Report 34 (26 Nov 2026): gallery choice at invitation, Remove from Contemporary, the closed
// Founding route and internal test accounts. Synthetic artists only; the Worker runs locally (Miniflare/workerd) with a
// local D1. Nothing here touches Cloudflare or any real artist.
//   node test/prove-report34.mjs
import { execFileSync } from 'node:child_process';
import { start, token, FOUNDER, PIPELINE_TOKEN, TEST_JWKS } from './local.mjs';
import { seedPublished } from './seed.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const mkcall = (mf, url) => async (method, path, email, body, headers = {}) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json', ...headers };
  if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const PIPE = { Authorization: 'Bearer ' + PIPELINE_TOKEN };
const T0 = '2026-11-05T17:05:00.000Z';
console.log('PROVE · PlotArt Studio · Report 34 (gallery choice, Founding route, test accounts)');

/* ---------------------------------------------------------------- F · the Founding route outside the local harness */
{
  // a non-local Studio: the test key set is served as the Access certs endpoint, exactly as Cloudflare Access would serve it
  const certs = req => new URL(req.url).pathname === '/cdn-cgi/access/certs' ? new Response(TEST_JWKS, { headers: { 'Content-Type': 'application/json' } }) : new Response('no', { status: 404 });
  const { mf, url, db } = await start({ port: 8841, env: { ENVIRONMENT: 'staging', ACCESS_JWKS_JSON: '' }, outbound: certs });
  const call = mkcall(mf, url);
  const n0 = (await db.prepare('SELECT COUNT(*) n FROM artists').first()).n;
  const f = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Fionn Synthetic', email: 'fionn@example.test', programme: 'founding' });
  const f2 = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Fia Synthetic', email: 'fia@example.test', founding: true });
  check('F1 a Founding invitation is refused on the server, whichever way it is asked for; no artist is created', f.s === 409 && f2.s === 409 && /Founding Artists initiative has ended/.test(f.j.error || f.t)
    && (await db.prepare('SELECT COUNT(*) n FROM artists').first()).n === n0, f.t);
  const g = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Gráinne Synthetic', email: 'grainne@example.test', programme: 'gallery_artist' });
  const terms = g.j.id && await db.prepare('SELECT track, commission_bp FROM artist_terms WHERE artist_id=?').bind(g.j.id).first();
  check('F2 a Gallery Artist invitation works as before (Gallery Artist terms, 15%)', g.s === 200 && terms && terms.track === 'gallery_artist' && terms.commission_bp === 1500, g.t);
  // an existing Founding Artist keeps everything
  await seedPublished(db, { id: 'afound', slug: 'found-test', email: 'found@example.test', name: 'Found Test', works: 1, number: 7 });
  const ov = (await call('GET', '/api/admin/overview', FOUNDER)).j;
  const fa = (ov.artists || []).find(a => a.id === 'afound');
  const row = await db.prepare('SELECT founding, founding_number FROM artists WHERE id=?').bind('afound').first();
  check('F3 an existing Founding Artist keeps their programme, number and agreement route', fa && fa.programme === 'founding' && row.founding === 1 && row.founding_number === 7, JSON.stringify(fa));
  const ui = (await call('GET', '/admin', FOUNDER)).t + (await call('GET', '/assets/admin.js', FOUNDER)).t;
  check('F4 the founder invitation form no longer offers the Founding route', !/name="i-prog"[^>]*value="founding"/.test(ui) && !/value="founding_artist"/.test(ui));
  await mf.dispose();
}

/* ---------------------------------------------------------------- the Studio with 0023-0026 and one internal test account */
const TEST = 'atestacct';
const { mf, url, db } = await start({ port: 8842, env: { TEST_ARTIST_IDS: ` ${TEST} ` } });
const call = mkcall(mf, url);
await seedPublished(db, { id: 'aaoife', slug: 'aoife-test', email: 'aoife@example.test', name: 'Aoife Test', works: 3, number: 1 });
await seedPublished(db, { id: 'abrian', slug: 'brian-test', email: 'brian@example.test', name: 'Brian Test', works: 2, number: 2 });
// the test account is seeded as already published (as if published before it was designated)
await seedPublished(db, { id: TEST, slug: 'makaulay-test', email: 'test@example.test', name: 'Test Account', works: 2, number: 9 });
await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, ?, 0, NULL, ?)').bind('aaoife', T0).run();
const snapReal = async () => JSON.stringify(await Promise.all(['artists', 'artworks', 'images', 'artist_terms', 'agreement_acceptances'].map(async t =>
  (await db.prepare(`SELECT * FROM ${t} WHERE ${t === 'artists' ? 'id' : 'artist_id'} IN ('aaoife','abrian') ORDER BY rowid`).all()).results)));
const realBefore = await snapReal();
const rows = async id => (await db.prepare('SELECT gallery_id, state, source, application_ref FROM gallery_memberships WHERE artist_id=? ORDER BY gallery_id').bind(id).all()).results;
let v;
const gal = id => v.galleries.find(g => g.gallery_id === id);
const view = async () => { v = (await call('GET', '/api/admin/galleries', FOUNDER)).j; return v; };

/* I · founder invitation with a gallery choice */
const inv = async (name, galleries, extra = {}) => call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email: name.toLowerCase().split(' ')[0] + '@example.test', programme: 'gallery_artist', ...(galleries ? { galleries } : {}), ...extra });
const iC = await inv('Cian Synthetic', ['contemporary']);
const iS = await inv('Saoirse Synthetic', ['spaces']);
const iB = await inv('Blathnaid Synthetic', ['being']);
const iM = await inv('Muireann Synthetic', ['contemporary', 'spaces', 'being'], { application_ref: 'PA-AP-261126-ABCDEF' });
const iN = await inv('Niall Synthetic', []);
check('I1 Contemporary only (the pre-selected default): nothing is written; the artist is in Contemporary exactly as every new artist is today', iC.s === 200 && (await rows(iC.j.id)).length === 0);
const rS = await rows(iS.j.id), rB = await rows(iB.j.id);
check('I2 exclusive Spaces: Contemporary deselected, so the artist is NOT in Contemporary; Spaces waits for the artist', iS.s === 200 && rS.length === 1 && rS[0].gallery_id === 'spaces' && rS[0].state === 'founder_approved');
check('I3 exclusive Being: likewise', iB.s === 200 && rB.length === 1 && rB[0].gallery_id === 'being' && rB[0].state === 'founder_approved');
const rM = await rows(iM.j.id);
check('I4 several galleries from an application: Contemporary live by default; Spaces and Being record the application and wait for the artist',
  iM.s === 200 && rM.length === 3 && rM.find(r => r.gallery_id === 'contemporary').state === 'live'
  && rM.filter(r => r.gallery_id !== 'contemporary').every(r => r.state === 'founder_approved' && r.source === 'application' && r.application_ref === 'PA-AP-261126-ABCDEF'), JSON.stringify(rM));
check('I5 at least one gallery: an empty choice is refused and no artist is created', iN.s === 400 && !(await db.prepare("SELECT id FROM artists WHERE email='niall@example.test'").first()), iN.t);
await view();
check('I6 the exclusive Spaces and Being artists are not listed in Contemporary', !gal('contemporary').members.some(m => [iS.j.id, iB.j.id].includes(m.artist_id)), JSON.stringify(gal('contemporary').members));

/* A · artist acceptance and rejection */
let r = await call('POST', '/api/galleries/spaces/accept', 'saoirse@example.test');
check('A1 the artist accepts Spaces: live only now', r.s === 200 && r.j.galleries.find(g => g.gallery_id === 'spaces').state === 'live', r.t);
r = await call('POST', '/api/galleries/being/decline', 'blathnaid@example.test');
const declined = (await rows(iB.j.id))[0];
check('A2 the artist declines Being: not a member; nothing else changes', r.s === 200 && declined.state !== 'live', r.t + JSON.stringify(declined));
r = await call('POST', '/api/galleries/spaces/accept', 'muireann@example.test');
const r2 = await call('POST', '/api/galleries/being/accept', 'muireann@example.test');
check('A3 multiple memberships: accepting both leaves the artist live in Contemporary, Spaces and Being', r.s === 200 && r2.s === 200
  && r2.j.galleries.filter(g => g.state === 'live').map(g => g.gallery_id).sort().join() === 'being,contemporary,spaces', r2.t);

/* P · an existing artist joins Spaces; independent artwork placement */
r = await call('POST', '/api/admin/galleries/spaces/members', FOUNDER, { artist_id: 'abrian', source: 'founder_curation' });
await call('POST', '/api/galleries/spaces/accept', 'brian@example.test');
const bRows = await rows('abrian');
check('P1 Contemporary preserved: an existing artist invited to Spaces stays live in Contemporary', bRows.find(x => x.gallery_id === 'contemporary').state === 'live' && bRows.find(x => x.gallery_id === 'spaces').state === 'live');
r = await call('POST', '/api/admin/galleries/spaces/artworks/wabrian1/place', FOUNDER);
const pa = await call('POST', '/api/galleries/spaces/artworks/wabrian1/accept', 'brian@example.test');
await view();
check('P2 a work is placed in Spaces only with the artist’s acceptance', r.s === 200 && pa.s === 200 && gal('spaces').live_works === 1, pa.t);
check('P3 placement is independent: the same work stays in Contemporary, and the artist’s other work is not placed in Spaces',
  gal('contemporary').live_works >= 5 && !(await db.prepare("SELECT 1 FROM artwork_placements WHERE artwork_id='wabrian2' AND gallery_id='spaces'").first()));

/* R · Remove from Contemporary */
r = await call('POST', '/api/admin/galleries/contemporary/members/aaoife/withdraw', FOUNDER);
check('R1 removal is refused while the artist holds a Contemporary position in Gallery order', r.s === 409 && /Release that position first/.test(r.j.error || r.t), r.t);
r = await call('POST', '/api/admin/galleries/contemporary/members/abrian/withdraw', FOUNDER);
await view();
const bAfter = await rows('abrian');
check('R2 removal from Contemporary: the artist leaves Contemporary only; Spaces membership and placement are untouched',
  r.s === 200 && bAfter.find(x => x.gallery_id === 'contemporary').state === 'withdrawn' && bAfter.find(x => x.gallery_id === 'spaces').state === 'live'
  && !gal('contemporary').members.some(m => m.artist_id === 'abrian') && gal('spaces').live_works === 1, r.t);
check('R3 removal never deletes the artist, their works, images, terms or agreements', (await snapReal()) === realBefore);
r = await call('POST', '/api/admin/galleries/contemporary/members/' + iC.j.id + '/withdraw', FOUNDER);
check('R4 an implicit Contemporary member (no rows yet) can be removed too; their default membership is written down first', r.s === 200
  && (await rows(iC.j.id)).find(x => x.gallery_id === 'contemporary').state === 'withdrawn', r.t);

/* T · advisory targets and independent opening */
r = await call('PUT', '/api/admin/galleries/spaces/targets', FOUNDER, { target_artists: 2, target_works: 1 });
await view();
check('T1 targets are advisory: the founder sets them; Spaces reports progress against them', r.s === 200 && gal('spaces').target_artists === 2 && gal('spaces').status === 'in_preparation', r.t);
r = await call('POST', '/api/admin/galleries/being/status', FOUNDER, { status: 'open', confirm: 'OPEN BEING' });
check('T2 below target, opening asks for an explicit confirmation (never automatic)', r.s === 409 && /below the target/.test(r.j.error || r.t), r.t);
r = await call('POST', '/api/admin/galleries/spaces/status', FOUNDER, { status: 'open', confirm: 'OPEN SPACES', below_target: true });
await view();
check('T3 opening Spaces is the founder’s own decision and leaves Being in preparation', r.s === 200 && gal('spaces').status === 'open' && gal('being').status === 'in_preparation', r.t);
const pipe = (await call('GET', '/api/pipeline/galleries', null, undefined, PIPE)).j;
const sw = JSON.parse(execFileSync('git', ['-C', HERE, 'show', 'HEAD:atlas-tools/release/plotart-launch-switches.json'], { encoding: 'utf8' }));
const shell = execFileSync('python3', ['-c', 'import sys; sys.path.insert(0, sys.argv[1]); import plotart_shell as s; print(",".join(s.GALLERY_STATES))', HERE + '../../atlas-tools'], { encoding: 'utf8' }).trim();
check('T4 a Studio opening is not a website release: the pipeline reports it, but the website keeps Spaces and Being in preparation until a separately approved launch switch (guard L21)',
  pipe.galleries.find(g => g.gallery === 'spaces').status === 'open' && sw.spaces_gallery_state === 'in_preparation' && sw.being_gallery_state === 'in_preparation' && shell === 'in_preparation',
  JSON.stringify({ shell, s: sw.spaces_gallery_state, b: sw.being_gallery_state }));
await call('POST', '/api/admin/galleries/spaces/status', FOUNDER, { status: 'in_preparation' });

/* X · the internal test account */
r = await call('GET', '/api/admin/test-artists', FOUNDER);
check('X1 the test account is designated by configuration (TEST_ARTIST_IDS), by its stable internal id', r.s === 200 && r.j.ids.join() === TEST);
r = await call('PUT', '/api/admin/artists/' + TEST + '/founding-number', FOUNDER, { founding_number: 9 });
check('X9 never holds a Founding 25 number (refused even while still marked Founding)', r.s === 409 && /internal test account/.test(r.j.error || r.t), r.t);
r = await call('POST', '/api/admin/artists/aaoife/test-programme', FOUNDER);
check('X2 the programme correction is refused for a real artist', r.s === 409);
r = await call('POST', '/api/admin/artists/' + TEST + '/test-programme', FOUNDER);
const tRow = await db.prepare('SELECT founding, founding_number FROM artists WHERE id=?').bind(TEST).first();
const tTerms = await db.prepare('SELECT track FROM artist_terms WHERE artist_id=?').bind(TEST).first();
check('X3 the test account is corrected to Gallery Artist (no Founding number), audit-logged', r.s === 200 && tRow.founding === 0 && tRow.founding_number === null && tTerms.track === 'gallery_artist'
  && !!(await db.prepare("SELECT 1 FROM audit WHERE action='test_account_programme' AND artist_id=?").bind(TEST).first()));
const pubF = (await call('GET', '/api/pipeline/featured-artists', null, undefined, PIPE)).j;
const order = (await call('GET', '/api/pipeline/gallery-order', null, undefined, PIPE)).j;
const pg = (await call('GET', '/api/pipeline/galleries', null, undefined, PIPE)).j;
check('X4 never in public listings: absent from the pipeline’s gallery order, Featured Artists and gallery contents even though it was published before designation',
  !JSON.stringify(order).includes('makaulay-test') && !JSON.stringify(pubF).includes(TEST) && !JSON.stringify(pubF).includes('makaulay-test') && !JSON.stringify(pg).includes('makaulay-test'), JSON.stringify(order));
await view();
check('X5 excluded from gallery statistics and targets', !gal('contemporary').members.some(m => m.artist_id === TEST) && gal('contemporary').live_artists === gal('contemporary').members.length);
r = await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'artist', artist_id: 'aaoife' }, { position: 2, state: 'artist', artist_id: TEST }] });
check('X6 never holds a Contemporary position', r.s === 409 && /internal test account/.test(r.j.error || r.t), r.t);
r = await call('PUT', '/api/admin/featured', FOUNDER, { items: [{ position: 1, artist_id: TEST }] });
check('X7 never a Featured Artist', r.s >= 400 && !(await db.prepare('SELECT 1 FROM homepage_features WHERE artist_id=?').bind(TEST).first()), r.t);
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qtest2',?,2,'reviewed','awaiting_founder',?,?)").bind(TEST, T0, T0).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qtest3',?,3,'reviewed','ready',?,?)").bind(TEST, T0, T0).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qtest4',?,4,'reviewed','failed',?,?)").bind(TEST, T0, T0).run();
const pq = (await call('GET', '/api/pipeline/queue', null, undefined, PIPE)).j;
const pp = await call('POST', '/api/admin/queue/qtest2/publish', FOUNDER);
const pe = await call('POST', '/api/pipeline/export/qtest3', null, undefined, PIPE);
const pr = await call('POST', '/api/admin/queue/qtest4/retry', FOUNDER);
const q3 = await db.prepare("SELECT status FROM publish_queue WHERE id='qtest3'").first();
check('X8 Studio publication safeguard: Publish, Retry and the pipeline export are refused; the pipeline never sees the job; nothing is marked exporting',
  pp.s === 409 && pe.s === 409 && pr.s === 409 && !JSON.stringify(pq).includes(TEST) && q3.status === 'ready', JSON.stringify({ pp: pp.s, pe: pe.s, pr: pr.s }));
r = await call('POST', '/api/admin/enquiry-log', FOUNDER, { artist_id: TEST, kind: 'enquiry', note: 'test' });
const hr = await call('POST', '/api/hire/reports', 'test@example.test', { artwork_id: 'watestacct1' });
check('X10 no genuine commercial record: enquiry log and hire reports are refused', r.s === 409 && hr.s === 409, r.t + hr.t);
r = await call('POST', '/api/checkout/onboarding', 'test@example.test', {});
check('X11 payments: refused unless Stripe is in test mode (here no key is configured, so refused)', r.s === 409 && /Stripe test mode/.test(r.j.error || r.t), r.t);
const ov = (await call('GET', '/api/admin/overview', FOUNDER)).j;
check('X12 the founder can still see and support the account (overview lists it)', (ov.artists || []).some(a => a.id === TEST));
const adminJs = (await call('GET', '/assets/admin.js', FOUNDER)).t;
check('X13 founder screens mark it TEST and mark its agreement acceptance as a test acceptance, not genuine consent', /st-test-badge/.test(adminJs) && /not genuine consent/.test(adminJs));
const realAfter = await snapReal();
check('Z1 no real artist record was changed by anything in this proof except the memberships the founder chose', realAfter === realBefore);
await mf.dispose();

/* B · the website builder refuses a test package independently of the Studio */
{
  const py = `
import sys, json, os, tempfile
sys.path.insert(0, sys.argv[1]); import plotart_gallery as G
d = tempfile.mkdtemp(); f = os.path.join(d, 't.json')
json.dump({"artist_ids": ["atestacct"], "slugs": ["makaulay-test"]}, open(f, "w")); G.TEST_ARTISTS_FILE = f
out = []
for g in ({"artist": {"slug": "makaulay-test"}}, {"artist": {"slug": "other"}, "publication": {"permission_ref": "PA-PERM-atestacct"}}, {"artist": {"slug": "aoife-test"}, "publication": {"permission_ref": "PA-PERM-aaoife"}}):
    out.append(G.is_test_package(g))
open(f, "w").write("{not json");
try: G.test_artists(); out.append("no-refusal")
except Exception as e: out.append(type(e).__name__)
print(json.dumps(out))`;
  const out = JSON.parse(execFileSync('python3', ['-c', py, HERE + '../../atlas-tools'], { encoding: 'utf8' }).trim());
  check('B1 the builder recognises a test package by slug or by permission reference, and not a real artist', out[0] === true && out[1] === true && out[2] === false, JSON.stringify(out));
  check('B2 a malformed test-account file stops the builder rather than letting a test package through', out[3] === 'Refused', JSON.stringify(out));
}

const ok = results.every(Boolean);
console.log(`\n${results.filter(Boolean).length}/${results.length} passed`);
process.exit(ok ? 0 : 1);
