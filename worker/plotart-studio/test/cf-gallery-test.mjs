// PlotArt · three galleries (Phase B) · test on a REAL, TEMPORARY Cloudflare D1 database (final verification, 24 Nov 2026).
// Never production: the database is created for one run by .github/workflows/plotart-galleries-cloudflare-test.yml (TEST
// credentials, founder approval) and deleted at the end of that run. The Studio Worker runs on the runner (wrangler dev,
// the workerd runtime) with its D1 binding pointing at that remote database ("remote = true"), so every query, batch,
// foreign key and migration runs inside Cloudflare D1 itself. A test key pair stands in for Cloudflare Access, exactly as in
// the local tests (the Worker accepts it only with ENVIRONMENT = "local"; nothing is deployed to Cloudflare's edge).
//   node test/cf-gallery-test.mjs --target remote --database-id <id> --out DIR    (CI: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID)
//   node test/cf-gallery-test.mjs --target local --out DIR                        (the same steps on a local D1, to test this script)
// Steps: 1 staging copy of the live galleries (production schema from main) loaded into the database; 2 the PRODUCTION Studio
// code (main) reads everything the publisher and founder read; 3 restore point (remote: Time Travel); 4 migration 0023 applied
// with the production command; every existing table byte-identical, exactly seven new empty tables; 5 the Phase B Studio reads
// the same things identically, the gallery model on the live data, and the integrity behaviour on real D1 (foreign keys,
// cascades, atomic batches, simultaneous requests); 6 rollback rehearsal: the gallery rows are exported, the database is
// restored to the restore point (remote: Time Travel restore), checked identical to before the migration, then 0023 is
// re-applied and the exported gallery rows re-imported and checked identical. Logs show PASS/FAIL, counts and table names only.
import { readFileSync, writeFileSync, mkdirSync, existsSync, rmSync } from 'node:fs';
import { execFileSync, spawn } from 'node:child_process';
import { generateKeyPairSync, createSign, randomUUID, createHash } from 'node:crypto';
import { join } from 'node:path';
import http from 'node:http';
import { DatabaseSync } from 'node:sqlite';
import { seedStaging } from './staging-seed.mjs';

const arg = k => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
const TARGET = arg('--target'), DBID = arg('--database-id'), OUT = arg('--out');
if (!['local', 'remote'].includes(TARGET) || !OUT || (TARGET === 'remote' && !/^[0-9a-f-]{36}$/.test(DBID || ''))) { console.log('usage: --target local|remote [--database-id ID] --out DIR'); process.exit(2); }
const REMOTE = TARGET === 'remote';
const HERE = new URL('..', import.meta.url).pathname, ROOT = join(HERE, '../..');
mkdirSync(OUT, { recursive: true });
const PERSIST = join(OUT, 'local-state'), MAIN = join(OUT, 'main');
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
const step = s => console.log(`\n— ${s}`);
const WR = ['--yes', 'wrangler@4.150.0'];
const GTABLES = ['gallery_settings', 'gallery_memberships', 'artwork_placements', 'gallery_order', 'gallery_features', 'image_use_requests', 'image_use_consents'];
const sha = v => createHash('sha256').update(typeof v === 'string' ? v : JSON.stringify(v)).digest('hex');

/* ---- Access stand-in and the Worker configuration (the same for both code versions; only the code differs) ---- */
const TEAM = 'https://plotnua-test.cloudflareaccess.com', AUD = 'test-aud-plotart-cftest', KID = 'cftest-' + randomUUID().slice(0, 8);
const FOUNDER = 'founder@plotnua.invalid', PIPELINE_TOKEN = 'cftest-pipeline-' + randomUUID();
const { publicKey, privateKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
const JWKS = JSON.stringify({ keys: [{ ...publicKey.export({ format: 'jwk' }), kid: KID, alg: 'RS256', use: 'sig' }] });
const b64u = b => Buffer.from(b).toString('base64url');
function token(email) {
  const t = Math.floor(Date.now() / 1000), h = b64u(JSON.stringify({ alg: 'RS256', kid: KID, typ: 'JWT' }));
  const p = b64u(JSON.stringify({ aud: [AUD], iss: TEAM, email, sub: randomUUID(), iat: t, exp: t + 3600, type: 'app' }));
  const s = createSign('RSA-SHA256'); s.update(h + '.' + p); return `${h}.${p}.${b64u(s.sign(privateKey))}`;
}
const toml = v => JSON.stringify(v);
function writeConfig(codeDir) {
  const f = join(codeDir, 'wrangler.cftest.toml');
  writeFileSync(f, [
    'name = "plotart-studio-cftest"', 'main = "src/studio-entry.js"', 'compatibility_date = "2026-08-01"', '',
    '[vars]', `ENVIRONMENT = "local"`, `ACCESS_TEAM_DOMAIN = ${toml(TEAM)}`, `ACCESS_AUD = ${toml(AUD)}`, `ACCESS_JWKS_JSON = ${toml(JWKS)}`,
    `FOUNDER_EMAILS = ${toml(FOUNDER)}`, `PIPELINE_TOKEN = ${toml(PIPELINE_TOKEN)}`, 'INSTANT_AUTOPUBLISH = "false"', 'INSTANT_PUBLISH_DISPATCH = "false"',
    'HIRE_TERMS_ENABLED = "false"', 'HIRE_RETENTION = "off"', 'MAILER = "none"', 'CHECKOUT_PILOT_ENABLED = "false"', '',
    '[[d1_databases]]', 'binding = "DB"', 'database_name = "plotart-studio-cftest"', `database_id = ${toml(REMOTE ? DBID : '00000000-0000-0000-0000-00000000cf7e')}`, ...(REMOTE ? ['remote = true'] : []), '',
    '[[r2_buckets]]', 'binding = "IMAGES"', 'bucket_name = "cftest-images-local-only"', '',
    '[[r2_buckets]]', 'binding = "APPLICATIONS"', 'bucket_name = "cftest-applications-local-only"', ''].join('\n'));
  return f;
}
const CFG = writeConfig(HERE);

/* ---- D1: every query through wrangler, against the remote database (or the local one when testing this script) ---- */
const where = () => REMOTE ? ['--remote'] : ['--local', '--persist-to', PERSIST];
function wrangler(args, { cwd = HERE, input } = {}) {
  return execFileSync('npx', [...WR, ...args], { cwd, encoding: 'utf8', maxBuffer: 1 << 28, input, stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, WRANGLER_SEND_METRICS: 'false', CI: '1' } });
}
function q(sql) {
  const out = wrangler(['d1', 'execute', 'plotart-studio-cftest', ...where(), '--json', '-c', CFG, '--command', sql]);
  return JSON.parse(out.slice(out.indexOf('[')));
}
const rows = sql => q(sql)[0].results;
function runFile(file) { wrangler(['d1', 'execute', 'plotart-studio-cftest', ...where(), '-c', CFG, '--file', file, '-y']); }
function tryQ(sql) { try { q(sql); return 'ok'; } catch (e) { return String((e.stderr || '') + (e.stdout || '') + e.message); } }
const tablesNow = () => rows("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' AND name NOT LIKE 'd1_%' ORDER BY name").map(r => r.name);
// a fingerprint of every table (SHA-256 of all rows in rowid order) and of every schema object's definition
function fingerprint() {
  const t = tablesNow(), res = q(t.map(x => `SELECT * FROM "${x}" ORDER BY rowid`).join('; '));
  const defs = rows("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' AND name NOT LIKE 'd1_%' ORDER BY type, name");
  return { tables: Object.fromEntries(t.map((x, i) => [x, { n: res[i].results.length, h: sha(res[i].results) }])), defs: Object.fromEntries(defs.map(d => [`${d.type}:${d.name}`, sha(d.sql || '')])) };
}

/* ---- the Studio Worker on the runner (wrangler dev) ---- */
let PORT = 8790;
// plain HTTP with a fresh connection per request (no keep-alive: the dev server closes idle connections while the test is
// busy querying the database, and a reused socket would fail)
function httpReq(u, method, headers, body) {
  return new Promise((res, rej) => {
    const r = http.request(u, { method, headers: { ...headers, Connection: 'close' }, agent: false }, x => { let t = ''; x.setEncoding('utf8'); x.on('data', d => { t += d; }); x.on('end', () => res({ s: x.statusCode, t })); });
    r.on('error', rej); if (body !== undefined) r.write(body); r.end();
  });
}
async function startStudio(codeDir) {
  const cfg = writeConfig(codeDir), port = PORT++;
  const p = spawn('npx', [...WR, 'dev', '-c', cfg, '--ip', '127.0.0.1', '--port', String(port), '--inspector-port', String(port + 1000), ...(REMOTE ? [] : ['--persist-to', PERSIST]), '--log-level', 'info'],
    { cwd: codeDir, stdio: ['ignore', 'pipe', 'pipe'], detached: true, env: { ...process.env, WRANGLER_SEND_METRICS: 'false', CI: '1' } });
  let log = ''; p.stdout.on('data', d => { log += d; }); p.stderr.on('data', d => { log += d; });
  const base = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 180; i++) {
    try { const r = await httpReq(base + '/api/pipeline/galleries', 'GET', { Authorization: 'Bearer ' + PIPELINE_TOKEN }); if (r.s) break; } catch { /* not yet */ }
    if (p.exitCode !== null) throw new Error('the Studio did not start: ' + log.split('\n').filter(l => /error/i.test(l)).slice(0, 5).join(' | '));
    await new Promise(r => setTimeout(r, 1000));
  }
  const call = async (method, path, email, body, headers = {}) => {
    const h = { 'X-Studio': '1', 'Content-Type': 'application/json', ...headers };
    if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
    const r = await httpReq(base + path, method, h, body === undefined ? undefined : JSON.stringify(body));
    const t = r.t; let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.s, j, t };
  };
  globalThis.__devlog = () => log;
  return { call, stop: () => new Promise(res => { try { process.kill(-p.pid, 'SIGTERM'); } catch { /* gone */ } setTimeout(res, 1500); }) };
}
const PIPE = { Authorization: 'Bearer ' + PIPELINE_TOKEN };
const READS = [['/api/pipeline/gallery-order', 'pipe'], ['/api/pipeline/featured-artists', 'pipe'], ['/api/pipeline/queue', 'pipe'], ['/api/pipeline/hire-catalogue', 'pipe'],
  ['/api/admin/gallery-order', 'founder'], ['/api/admin/featured', 'founder'], ['/api/admin/opportunities', 'founder']];
const norm = s => s.replace(/"generated_at":"[^"]*"/g, '"generated_at":"(time of the read)"');
async function readAll(S) { const o = {}; for (const [p, who] of READS) { const r = await S.call('GET', p, who === 'founder' ? FOUNDER : null, undefined, who === 'pipe' ? PIPE : {}); o[p] = { s: r.s, t: norm(r.t) }; } return o; }

/* ---- an SQL file of rows (data only) from a local SQLite database ---- */
const lit = v => v === null || v === undefined ? 'NULL' : typeof v === 'number' || typeof v === 'bigint' ? String(v) : `'${String(v).replace(/'/g, "''")}'`;
function insertsFrom(sdb, tables) {
  const out = [];
  for (const t of tables) for (const r of sdb.prepare(`SELECT * FROM "${t}" ORDER BY rowid`).all()) {
    const cols = Object.keys(r); out.push(`INSERT INTO "${t}" (${cols.map(c => `"${c}"`).join(', ')}) VALUES (${cols.map(c => lit(r[c])).join(', ')});`);
  }
  return out;
}
function d1Adapter(sdb) {   // just enough of D1's API for the staging seeder
  return { prepare: sql => { const st = sdb.prepare(sql); const mk = (b = []) => ({ bind: (...x) => mk(x), run: async () => st.run(...b), first: async () => st.get(...b) || null, all: async () => ({ results: st.all(...b) }) }); return mk(); } };
}

let main = null, phaseB = null;
try {
  console.log(`THREE GALLERIES · ${REMOTE ? 'REAL TEMPORARY CLOUDFLARE D1 DATABASE' : 'LOCAL REHEARSAL OF THE CLOUDFLARE TEST (no Cloudflare)'}`);
  /* 1 · the staging copy, production schema from main */
  step('1 · staging copy of the live galleries in the database (production schema from main)');
  if (existsSync(MAIN)) execFileSync('git', ['-C', ROOT, 'worktree', 'remove', '--force', MAIN]);
  execFileSync('git', ['-C', ROOT, 'worktree', 'add', '-q', '--detach', MAIN, 'origin/main']);
  const mainSchema = readFileSync(join(MAIN, 'worker/plotart-studio/schema.sql'), 'utf8');
  if (mainSchema.includes('gallery_memberships')) throw new Error('main already contains migration 0023: this test is for before the merge');
  const sdb = new DatabaseSync(':memory:'); sdb.exec('PRAGMA foreign_keys = ON;'); sdb.exec(mainSchema);
  const { snapshot } = await import(join(MAIN, 'worker/plotart-studio/src/lib.js'));
  const staged = await seedStaging(d1Adapter(sdb), { ROOT, snapshot });
  const order = ['artists', 'artworks', 'images', 'versions', 'publish_queue', 'gallery_positions', 'homepage_features'];   // what the seeder writes (schema.sql seeds its own reference rows)
  writeFileSync(join(OUT, 'schema-main.sql'), mainSchema);
  writeFileSync(join(OUT, 'seed.sql'), insertsFrom(sdb, order).join('\n') + '\n');
  if (!REMOTE) rmSync(PERSIST, { recursive: true, force: true });
  check('1.0 the database is new and empty before anything is loaded', tablesNow().length === 0, tablesNow().join());
  runFile(join(OUT, 'schema-main.sql'));
  runFile(join(OUT, 'seed.sql'));
  const n = rows('SELECT (SELECT COUNT(*) FROM artists) a, (SELECT COUNT(*) FROM artworks) w, (SELECT COUNT(*) FROM homepage_features) f, (SELECT COUNT(*) FROM gallery_positions) p')[0];
  check(`1.1 loaded: the production schema and the staging galleries (${n.a} artists, ${n.w} works, ${n.p} visible positions, ${n.f} Artists in Focus)`,
    n.a === 18 && n.w === staged.packages.reduce((s, p) => s + p.works.length, 0) && n.f === 6 && n.p === staged.positions.length, JSON.stringify(n));

  /* 2 · today's production Studio code */
  step('2 · the PRODUCTION Studio code (main) on this database');
  execFileSync('node', ['build-assets.mjs'], { cwd: join(MAIN, 'worker/plotart-studio'), stdio: 'ignore' });
  main = await startStudio(join(MAIN, 'worker/plotart-studio'));
  const before = await readAll(main);
  check('2.1 the production Studio serves the publisher’s and founder’s reads from the remote database', Object.values(before).every(r => r.s === 200), JSON.stringify(Object.fromEntries(Object.entries(before).map(([k, v]) => [k, v.s]))));
  await main.stop(); main = null;

  /* 3 · restore point, then 4 · migration 0023 with the production command */
  step('3 · restore point and fingerprint before the migration');
  const fpBefore = fingerprint();
  let bookmark = null;
  if (REMOTE) {
    const tt = wrangler(['d1', 'time-travel', 'info', 'plotart-studio-cftest', '--json', '-c', CFG]);
    bookmark = (tt.match(/"bookmark"\s*:\s*"([^"]+)"/) || [])[1] || null;
    check('3.1 a Cloudflare Time Travel restore point is taken (as the production workflow does)', !!bookmark);
  } else console.log('  (local rehearsal: no Time Travel; the rollback below uses the migration’s documented DROP TABLE lines)');
  step('4 · migration 0023, applied with the production command (wrangler d1 execute --remote --file)');
  const MIGF = join(HERE, 'migrations/0023_three_galleries.sql');
  console.log(`  migration SHA-256 ${createHash('sha256').update(readFileSync(MIGF)).digest('hex')}`);
  runFile(MIGF);
  const fpAfter = fingerprint();
  const existingSame = Object.keys(fpBefore.tables).every(t => JSON.stringify(fpBefore.tables[t]) === JSON.stringify(fpAfter.tables[t]));
  const defsSame = Object.entries(fpBefore.defs).every(([k, v]) => fpAfter.defs[k] === v);
  const added = Object.keys(fpAfter.tables).filter(t => !(t in fpBefore.tables)).sort();
  check('4.1 every existing table is byte-for-byte unchanged (every row of every table)', existingSame);
  check('4.2 every existing table, index and trigger definition is unchanged', defsSame);
  check('4.3 exactly the seven new tables were added, all empty', JSON.stringify(added) === JSON.stringify([...GTABLES].sort()) && added.every(t => fpAfter.tables[t].n === 0), added.join());
  const fk = tryQ("INSERT INTO artwork_placements (artwork_id, artist_id, gallery_id, state, proposed_by, proposed_at, closed_by, closed_at, updated_at) VALUES ('wnosuchwork','anosuchartist','contemporary','withdrawn','t','2026-11-24T00:00:00.000Z','t','2026-11-24T00:00:00.000Z','2026-11-24T00:00:00.000Z')");
  check('4.4 the database enforces the new foreign keys (a row pointing at no artwork is refused)', /FOREIGN KEY/i.test(fk), fk.slice(0, 200));

  /* 5 · the Phase B Studio */
  step('5 · the PHASE B Studio code on the same database');
  phaseB = await startStudio(HERE);
  const S = phaseB, after = await readAll(S);
  check('5.1 everything the publisher reads is identical (gallery order, Artists in Focus, publication queue, hire catalogue)',
    READS.filter(r => r[1] === 'pipe').every(([p]) => after[p].s === 200 && after[p].t === before[p].t), READS.filter(([p]) => after[p].t !== before[p].t).map(r => r[0]).join());
  check('5.2 everything the founder’s existing desks read is identical (Gallery order, Featured Artists, Opportunities)',
    READS.filter(r => r[1] === 'founder').every(([p]) => after[p].s === 200 && after[p].t === before[p].t));
  const g = (await S.call('GET', '/api/admin/galleries', FOUNDER)).j, gal = k => g.galleries.find(x => x.gallery_id === k);
  check(`5.3 Contemporary Art holds all 18 published artists and all ${staged.shownWorks} shown works; Landscape Art and Portraiture are empty and In preparation`,
    g.installed && gal('contemporary').members.length === 18 && gal('contemporary').live_works === staged.shownWorks
    && ['landscape', 'portraiture'].every(k => gal(k).status === 'in_preparation' && gal(k).live_artists === 0), JSON.stringify({ c: gal('contemporary').members.length, w: gal('contemporary').live_works }));
  check('5.4 nothing was written for any existing artist or artwork', GTABLES.every(t => rows(`SELECT COUNT(*) n FROM ${t}`)[0].n === 0));
  // the gallery model on real D1, with two synthetic artists invited through the Studio
  const inv = await S.call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Cloud Test One', email: 'cf-one@example.test', programme: 'gallery_artist', galleries: ['landscape'] });
  const inv2 = await S.call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Cloud Test Two', email: 'cf-two@example.test', programme: 'gallery_artist', galleries: ['portraiture', 'contemporary'] });
  const m1 = inv.j.id ? rows(`SELECT gallery_id, state FROM gallery_memberships WHERE artist_id = '${inv.j.id}' ORDER BY gallery_id`) : [];
  check('5.5 invitations with a gallery choice write the artist, the 15% terms and the invitations in one batch on real D1',
    inv.s === 200 && inv2.s === 200 && JSON.stringify(m1) === JSON.stringify([{ gallery_id: 'landscape', state: 'founder_approved' }])
    && rows(`SELECT commission_bp FROM artist_terms WHERE artist_id = '${inv.j.id}'`)[0].commission_bp === 1500, JSON.stringify(m1));
  const one = inv.j.id, ONE = 'cf-one@example.test';
  const acc = await S.call('POST', '/api/galleries/landscape/accept', ONE);
  const wid = (await S.call('POST', '/api/artworks', ONE)).j.id;
  const prop = await S.call('POST', `/api/galleries/landscape/artworks/${wid}/propose`, ONE);
  const place = await S.call('POST', `/api/admin/galleries/landscape/artworks/${wid}/place`, FOUNDER);
  check('5.6 founder approval + artist acceptance makes a membership and a placement live on real D1', acc.s === 200 && prop.s === 200 && place.s === 200
    && rows(`SELECT state FROM artwork_placements WHERE artwork_id = '${wid}'`)[0].state === 'live', `${acc.s} ${prop.s} ${place.s}`);
  const del = await S.call('DELETE', `/api/artworks/${wid}`, ONE);
  check('5.7 deleting that draft works as today on real D1: the database removes its placement with it (ON DELETE CASCADE)',
    del.s === 200 && rows(`SELECT COUNT(*) n FROM artwork_placements WHERE artwork_id = '${wid}'`)[0].n === 0 && rows(`SELECT COUNT(*) n FROM artworks WHERE id = '${wid}'`)[0].n === 0, del.t.slice(0, 200));
  // simultaneous requests against real D1: the artist accepts while the founder withdraws, 12 rounds
  const TWO = 'cf-two@example.test', two = inv2.j.id;
  let bad = 0, rounds = 0; const odd = [];
  for (let i = 0; i < 12; i++) {
    const st = rows(`SELECT state FROM gallery_memberships WHERE artist_id = '${two}' AND gallery_id = 'portraiture'`)[0].state;
    if (st !== 'founder_approved') { const r = await S.call('POST', '/api/admin/galleries/portraiture/members', FOUNDER, { artist_id: two }); if (r.s !== 200) { bad++; odd.push(`re-invite ${st} → ${r.s} ${r.t.slice(0, 80)}`); continue; } }
    const [x, y] = await Promise.all([S.call('POST', '/api/galleries/portraiture/accept', TWO), S.call('POST', `/api/admin/galleries/portraiture/members/${two}/withdraw`, FOUNDER)]);
    const end = rows(`SELECT state FROM gallery_memberships WHERE artist_id = '${two}' AND gallery_id = 'portraiture'`)[0].state; rounds++;
    if (!((y.s === 200 && end === 'withdrawn') || (y.s === 409 && x.s === 200 && end === 'live'))) { bad++; odd.push(`accept ${x.s} withdraw ${y.s} end ${end}`); }
    if (end === 'live') { const w = await S.call('POST', `/api/admin/galleries/portraiture/members/${two}/withdraw`, FOUNDER); if (w.s !== 200) odd.push(`cleanup withdraw ${w.s} ${w.t.slice(0, 80)}`); }
  }
  check(`5.8 ${rounds} rounds of a simultaneous accept and withdrawal on real D1 end only in valid states`, rounds === 12 && bad === 0, `bad=${bad} ${odd.join(' ; ')}`);
  // one of the live (staging) artists joins Landscape Art with a published work: Artists in Focus, order, targets and a permission
  const la = rows("SELECT a.id, a.email, w.id AS wid FROM artists a JOIN artworks w ON w.artist_id = a.id WHERE a.email LIKE '%@staging.invalid' AND w.availability = 'available' ORDER BY a.slug, w.ord LIMIT 1")[0];
  const steps = [await S.call('POST', '/api/admin/galleries/landscape/members', FOUNDER, { artist_id: la.id, source: 'founder_curation' }), await S.call('POST', '/api/galleries/landscape/accept', la.email),
    await S.call('POST', `/api/admin/galleries/landscape/artworks/${la.wid}/place`, FOUNDER), await S.call('POST', `/api/galleries/landscape/artworks/${la.wid}/accept`, la.email),
    await S.call('PUT', '/api/admin/galleries/landscape/order', FOUNDER, { artists: [la.id] }), await S.call('PUT', '/api/admin/galleries/landscape/features', FOUNDER, { items: [{ artist_id: la.id, artwork_id: la.wid }] }),
    await S.call('PUT', '/api/admin/galleries/landscape/targets', FOUNDER, { target_artists: 5, target_works: 25 })];
  const ur = await S.call('POST', '/api/admin/image-use/requests', FOUNDER, { artist_id: la.id, scope: 'homepage_feature', gallery_id: 'landscape', artwork_ids: [la.wid], purpose: 'Landscape Art homepage, Artists in Focus image', channels: 'plotnua.ie homepage', valid_until: '2027-06-30' });
  steps.push(ur, await S.call('POST', `/api/image-use/${ur.j.request && ur.j.request.id}/answer`, la.email, { answer: 'yes' }));
  const pl = (await S.call('GET', '/api/pipeline/galleries', null, undefined, PIPE)).j.galleries.find(x => x.gallery === 'landscape');
  check('5.10 a live gallery artist joins Landscape Art with a published work, in focus and ordered there, with a recorded permission; their Contemporary membership is untouched',
    steps.every(r => r.s === 200) && pl.artists.length === 1 && pl.works.length === 1 && pl.features.length === 1 && pl.order.length === 1
    && rows(`SELECT state FROM gallery_memberships WHERE artist_id = '${la.id}' AND gallery_id = 'contemporary'`)[0].state === 'live', steps.map(r => r.s).join());
  const pipe = (await S.call('GET', '/api/pipeline/galleries', null, undefined, PIPE)).j;
  check('5.9 the read-only pipeline view: 18 Contemporary artists by public address, no email address anywhere', pipe.installed && pipe.galleries[0].artists.length === 18 && !/@/.test(JSON.stringify(pipe)));
  await S.stop(); phaseB = null;

  /* 6 · rollback rehearsal that keeps the gallery records */
  step('6 · rollback rehearsal: keep the gallery records, restore, re-apply, re-import');
  const fpGallery = fingerprint();
  const exp = join(OUT, 'gallery-rows.sql');
  // remote: Cloudflare's own export (wrangler d1 export --no-schema --table …); local rehearsal: the same INSERTs built from the rows
  if (REMOTE) wrangler(['d1', 'export', 'plotart-studio-cftest', '--remote', '-c', CFG, '--no-schema', ...GTABLES.flatMap(t => ['--table', t]), '--output', exp]);
  else writeFileSync(exp, GTABLES.flatMap(t => rows(`SELECT * FROM ${t} ORDER BY rowid`).map(r => `INSERT INTO "${t}" (${Object.keys(r).map(c => `"${c}"`).join(',')}) VALUES (${Object.values(r).map(lit).join(',')});`)).join('\n') + '\n');
  const exported = readFileSync(exp, 'utf8'), nIns = (exported.match(/^INSERT INTO/gm) || []).length;
  const nRows = GTABLES.reduce((s, t) => s + fpGallery.tables[t].n, 0);
  check(`6.1 the gallery records are exported first (${nRows} rows in the seven gallery tables; data only)`, nIns === nRows && nRows > 0, `${nIns} vs ${nRows}`);
  // (a) the rollback for a live database: only the seven gallery tables are dropped (the migration's documented lines)
  for (const l of readFileSync(MIGF, 'utf8').split('\n').filter(x => /^--\s+DROP TABLE /.test(x))) q(l.replace(/^--\s*/, ''));
  const fpDropped = fingerprint();
  check('6.2 rollback by dropping only the seven gallery tables: they are gone; every other table and row is exactly as it was just before',
    JSON.stringify(Object.keys(fpDropped.tables).sort()) === JSON.stringify(Object.keys(fpBefore.tables).sort())
    && Object.keys(fpDropped.tables).every(t => JSON.stringify(fpDropped.tables[t]) === JSON.stringify(fpGallery.tables[t])));
  runFile(MIGF);
  writeFileSync(join(OUT, 'gallery-rows-import.sql'), 'PRAGMA defer_foreign_keys = ON;\n' + exported);
  runFile(join(OUT, 'gallery-rows-import.sql'));
  const fpBack = fingerprint();
  check('6.3 re-applying 0023 and re-importing the export brings back every gallery record exactly (all seven tables identical; nothing else changed)',
    Object.keys(fpGallery.tables).every(t => JSON.stringify(fpBack.tables[t]) === JSON.stringify(fpGallery.tables[t])),
    Object.keys(fpGallery.tables).filter(t => JSON.stringify(fpBack.tables[t]) !== JSON.stringify(fpGallery.tables[t])).join());
  // (b) Time Travel: the whole database back to the restore point taken before the migration
  if (REMOTE) {
    wrangler(['d1', 'time-travel', 'restore', 'plotart-studio-cftest', '--bookmark', bookmark, '-c', CFG, '-y']);
    const fpTT = fingerprint();
    check('6.4 Time Travel restore to the restore point: the whole database is exactly as before the migration (it also undoes every later write, so it is the right tool only straight after a failed migration)',
      JSON.stringify(fpTT.tables) === JSON.stringify(fpBefore.tables) && JSON.stringify(fpTT.defs) === JSON.stringify(fpBefore.defs));
  }
} catch (e) {
  if (globalThis.__devlog) console.log('  studio log (errors): ' + globalThis.__devlog().slice(-3000));
  console.log(`  FAIL  stopped: ${e.cause ? 'cause ' + (e.cause.code || e.cause.message) + ' · ' : ''}${String(e.stderr || e.message || e).split('\n').filter(l => l.trim()).slice(0, 6).join(' | ').replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g, '<id>')}`);
  results.push(false);
} finally {
  for (const s of [main, phaseB]) if (s) await s.stop();
  try { execFileSync('git', ['-C', ROOT, 'worktree', 'remove', '--force', MAIN]); } catch { /* already gone */ }
  for (const f of ['wrangler.cftest.toml']) rmSync(join(HERE, f), { force: true });
}
const fail = results.filter(x => !x).length;
writeFileSync(join(OUT, 'result.json'), JSON.stringify({ target: TARGET, checks: results.length, passed: results.length - fail, failed: fail }));
console.log(`\nTHREE GALLERIES · CLOUDFLARE D1 TEST (${TARGET}) · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
