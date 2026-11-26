// PROVE · PlotArt Studio · Gallery Showcase (Report 37, migration 0028). Synthetic artists only; local Miniflare.
//   node test/prove-showcase.mjs
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const { chromium } = require('playwright');

const HERE = new URL('..', import.meta.url).pathname;
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const MIG_FILE = HERE + 'migrations/0028_gallery_showcase.sql', MIG = readFileSync(MIG_FILE, 'utf8');
console.log('PROVE · Gallery Showcase · migration 0028 SHA-256 ' + createHash('sha256').update(readFileSync(MIG_FILE)).digest('hex'));

/* ---- M · the migration on the release candidate's schema (everything up to 0027), with the three works that exist today ---- */
{
  const base = execFileSync('git', ['-C', HERE, 'show', 'dev/plotart-phase-c:worker/plotart-studio/schema.sql'], { encoding: 'utf8' });
  const mf = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'm28' } });
  const db = await mf.getD1Database('DB');
  const run = async sql => { for (const st of statements(sql)) await db.prepare(st).run(); };
  await run(base);
  for (const [id, slug] of [['acarmel', 'carmel-marrinan'], ['adaniel', 'daniel-chester'], ['aclare', 'clare-o-connor']])
    await seedPublished(db, { id, slug, email: slug + '@example.test', name: slug, works: 1 });
  for (const [w, a] of [['wg1by72jg3b', 'acarmel'], ['wfhtcyurvgf', 'adaniel'], ['w226r60hfsh', 'aclare']])
    await db.prepare("UPDATE artworks SET id = ? WHERE artist_id = ?").bind(w, a).run();
  const tables = async () => (await db.prepare("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name").all()).results;
  const dump = async names => { const o = {}; for (const t of names) o[t] = (await db.prepare(`SELECT * FROM ${t} ORDER BY rowid`).all()).results; return JSON.stringify(o); };
  const t0 = await tables(), names = t0.filter(t => /^CREATE TABLE/.test(t.sql || '')).map(t => t.name), d0 = await dump(names);
  await run(MIG);
  const t1 = await tables(), rows = (await db.prepare('SELECT gallery_id, stage, position, artist_id, artwork_id FROM gallery_showcase ORDER BY stage, position').all()).results;
  check('M1 one new table and two refusal-only triggers; every existing table and row unchanged',
    (await dump(names)) === d0 && JSON.stringify(t1.filter(t => !t.name.startsWith('gallery_showcase'))) === JSON.stringify(t0)
    && t1.filter(t => t.name.startsWith('gallery_showcase')).map(t => t.name).sort().join() === 'gallery_showcase,gallery_showcase_artist_insert,gallery_showcase_artist_update');
  check('M2 the existing Contemporary three are the initial configuration, as draft and published, in today’s order',
    rows.map(r => `${r.stage}:${r.position}:${r.artwork_id}`).join() === 'draft:1:wg1by72jg3b,draft:2:wfhtcyurvgf,draft:3:w226r60hfsh,published:1:wg1by72jg3b,published:2:wfhtcyurvgf,published:3:w226r60hfsh'
    && rows.every(r => r.gallery_id === 'contemporary'));
  let again = 'ok'; try { await run(MIG); } catch (e) { again = String(e.message); }
  check('M3 safe to run again: a second run changes nothing and raises nothing', again === 'ok' && (await db.prepare('SELECT COUNT(*) n FROM gallery_showcase').first()).n === 6 && (await dump(names)) === d0);
  const T = '2026-11-26T10:00:00.000Z';
  const tryIns = async (g, st, p, a, w) => { try { await db.prepare('INSERT INTO gallery_showcase VALUES (?,?,?,?,?,?,?)').bind(g, st, p, a, w, T, 'founder@x.ie').run(); return 'ok'; } catch { return 'refused'; } };
  const tryUpd = async () => { try { await db.prepare("UPDATE gallery_showcase SET artist_id = 'adaniel' WHERE stage = 'draft' AND position = 1").run(); return 'ok'; } catch { return 'refused'; } };
  check('M4 the database refuses an artwork that does not belong to the artist (insert and update), a repeated artwork, a fourth position and an unknown gallery or stage',
    [await tryIns('spaces', 'draft', 1, 'adaniel', 'wg1by72jg3b'), await tryUpd(), await tryIns('contemporary', 'draft', 4, 'acarmel', 'wg1by72jg3b'),
      await tryIns('environment', 'draft', 1, 'acarmel', 'wg1by72jg3b'), await tryIns('spaces', 'final', 1, 'acarmel', 'wg1by72jg3b')].every(x => x === 'refused')
    && await tryIns('spaces', 'draft', 1, 'acarmel', 'wg1by72jg3b') === 'ok' && await tryIns('spaces', 'draft', 2, 'acarmel', 'wg1by72jg3b') === 'refused');
  await mf.dispose();
}

/* ---- S · the Studio (schema with 0028) ---- */
const TEST = 'atestacct';
// The Gallery Showcase on its own (migration 0028), as before unified curation: the schema without migration 0029 (with
// 0029 the showcase is saved and published through Curate, proven in prove-curation.mjs)
const SCHEMA28 = readFileSync(HERE + 'schema.sql', 'utf8').split(/\n-- PlotArt Studio · migration 0029\b/)[0];
const { mf, url, db } = await start({ port: 8881, env: { TEST_ARTIST_IDS: TEST }, schemaSql: SCHEMA28 });
const call = async (method, path, email, body, headers = {}) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json', ...headers }; if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j, t };
};
const PIPE = { Authorization: 'Bearer ' + PIPELINE_TOKEN };
await seedPublished(db, { id: 'aann', slug: 'ann-test', email: 'ann@example.test', name: 'Ann Test', works: 3, number: 1 });
await seedPublished(db, { id: 'aben', slug: 'ben-test', email: 'ben@example.test', name: 'Ben Test', works: 2, number: 2 });
await seedPublished(db, { id: 'acai', slug: 'cai-test', email: 'cai@example.test', name: 'Cai Test', works: 2 });
await seedPublished(db, { id: TEST, slug: 'test-account', email: 'test@example.test', name: 'Test Account', works: 1 });
await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (1,'artist','aben','waben1',?)").bind(new Date().toISOString()).run();
await db.prepare("INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1,'aann',0,NULL,?)").bind(new Date().toISOString()).run();
const others = async () => JSON.stringify(await Promise.all(['homepage_features', 'gallery_positions', 'gallery_features', 'gallery_order', 'gallery_memberships', 'artwork_placements'].map(async t => (await db.prepare(`SELECT * FROM ${t} ORDER BY rowid`).all()).results)));
const o0 = await others();
const pipe = async () => (await call('GET', '/api/pipeline/gallery-showcase', null, undefined, PIPE)).j;
const view = async () => (await call('GET', '/api/admin/showcase', FOUNDER)).j;
let v = await view();
const gc = () => v.galleries.find(x => x.gallery_id === 'contemporary');
check('S1 every gallery has its own showcase; eligible works are the published, available works of live members, never a test account',
  v.installed && v.galleries.map(x => x.gallery_id).join() === 'contemporary,spaces,being' && gc().artists.map(a => a.display_name).join() === 'Ann Test,Ben Test,Cai Test'
  && !JSON.stringify(gc().artists).includes(TEST) && v.galleries.find(x => x.gallery_id === 'spaces').artists.length === 0);
const p0 = await pipe();
let r = await call('PUT', '/api/admin/showcase/contemporary', FOUNDER, { items: [{ position: 1, artist_id: 'acai', artwork_id: 'wacai1' }, { position: 2, artist_id: 'aann', artwork_id: 'waann2' }, { position: 3, artist_id: 'aben', artwork_id: 'waben1' }] });
v = r.j;
check('S2 saving a draft never publishes: the pipeline is unchanged and the founder sees "the draft differs from the published showcase"',
  r.s === 200 && gc().draft.map(d => d.artwork_id).join() === 'wacai1,waann2,waben1' && gc().unpublished_changes === true && JSON.stringify(await pipe()) === JSON.stringify(p0), r.t);
// Duplication with Artists in Focus: Ben's waben1 is also one of Contemporary's Artists in Focus (homepage_features)
check('D1 a showcase artwork that is also in Artists in Focus is allowed: the draft saves, and the work is marked for a discreet notice (Right only)',
  r.s === 200 && gc().draft.map(d => `${d.side}:${d.in_focus}`).join() === 'Left:false,Centre:false,Right:true'
  && JSON.stringify(gc().also_in_focus.map(x => x.side)) === '["Right"]' && gc().focus_artworks.join() === 'waben1', JSON.stringify(gc().draft));
const bad = [
  await call('PUT', '/api/admin/showcase/contemporary', FOUNDER, { items: [{ position: 1, artist_id: 'aann', artwork_id: 'waben1' }] }),        // another artist's work
  await call('PUT', '/api/admin/showcase/contemporary', FOUNDER, { items: [{ position: 1, artist_id: TEST, artwork_id: 'watestacct1' }] }),     // test account
  await call('PUT', '/api/admin/showcase/contemporary', FOUNDER, { items: [{ position: 1, artist_id: 'aann', artwork_id: 'waann1' }, { position: 1, artist_id: 'aben', artwork_id: 'waben2' }] }),   // same position
  await call('PUT', '/api/admin/showcase/contemporary', FOUNDER, { items: [{ position: 1, artist_id: 'aann', artwork_id: 'waann1' }, { position: 2, artist_id: 'aann', artwork_id: 'waann1' }] }),   // same work
  await call('PUT', '/api/admin/showcase/spaces', FOUNDER, { items: [{ position: 1, artist_id: 'aann', artwork_id: 'waann1' }] }),            // not a member of Spaces
  await call('PUT', '/api/admin/showcase/contemporary', FOUNDER, { items: [{ position: 4, artist_id: 'aann', artwork_id: 'waann1' }] }),       // fourth position
  await call('PUT', '/api/admin/showcase/contemporary', 'ann@example.test', { items: [] }),                                                    // an artist
];
check('S3 server checks: another artist’s work, a test account, a repeated position or artwork, a non-member of the gallery and a fourth position are refused; only the founder can edit',
  bad.slice(0, 6).every(x => x.s === 400 || x.s === 409) && bad[6].s === 403 && (await view()).galleries[0].draft.map(d => d.artwork_id).join() === 'wacai1,waann2,waben1', JSON.stringify(bad.map(x => x.s)));
r = await call('POST', '/api/admin/showcase/contemporary/publish', FOUNDER);
let p1 = await pipe();
check('S4 Publish makes the draft the published showcase, through the publishing workflow; the pipeline sends gallery addresses and artwork ids only, left to right',
  r.s === 200 && 'publish' in r.j && JSON.stringify(p1.galleries[0].items) === JSON.stringify([{ position: 1, artist: 'cai-test', work: 'wacai1' }, { position: 2, artist: 'ann-test', work: 'waann2' }, { position: 3, artist: 'ben-test', work: 'waben1' }])
  && !!(await db.prepare("SELECT 1 FROM audit WHERE action='gallery_showcase_published'").first()), r.t);
check('D2 publishing with the overlap is not blocked, and neither selection is removed or replaced: the work stays in both',
  r.s === 200 && p1.galleries[0].items.some(i => i.work === 'waben1')
  && (await db.prepare("SELECT artwork_id FROM homepage_features").all()).results.map(x => x.artwork_id).join() === 'waben1');
check('S5 Artists in Focus, Gallery order, memberships and placements are untouched by the showcase', (await others()) === o0);
// a routine artist publication: Ben publishes an update in which the showcase work is sold
const lv = await db.prepare("SELECT version, snapshot FROM versions WHERE artist_id='aben' ORDER BY version DESC").first();
const snap = JSON.parse(lv.snapshot); snap.works.find(w => w.id === 'waben1').availability = 'sold';
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('aben', ?, ?, 'test', ?)").bind(lv.version + 1, JSON.stringify(snap), new Date().toISOString()).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qbensold','aben',?,'instant','published',?,?)").bind(lv.version + 1, new Date().toISOString(), new Date().toISOString()).run();
v = await view(); const p2 = await pipe();
const kept = (await db.prepare("SELECT artwork_id FROM gallery_showcase WHERE gallery_id='contemporary' AND stage='published' ORDER BY position").all()).results.map(x => x.artwork_id).join();
check('S6 a sold work drops out of the public showcase with nothing substituted; the founder’s record keeps it; the Review Desk names the position, the work and the reason',
  JSON.stringify(p2.galleries[0].items.map(i => i.work)) === JSON.stringify(['wacai1', 'waann2']) && kept === 'wacai1,waann2,waben1'
  && gc().vacant.length === 1 && gc().vacant[0].side === 'Right' && gc().vacant[0].artwork_id === 'waben1' && gc().vacant[0].reason === 'the artwork has been sold', JSON.stringify(gc().vacant));
// withdrawn (removed from the version) and unpublished (artist removed)
const snap2 = JSON.parse((await db.prepare("SELECT snapshot FROM versions WHERE artist_id='aann' ORDER BY version DESC").first()).snapshot); snap2.works = snap2.works.filter(w => w.id !== 'waann2');
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('aann', 9, ?, 'test', ?)").bind(JSON.stringify(snap2), new Date().toISOString()).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qannw','aann',9,'reviewed','published',?,?)").bind(new Date().toISOString(), new Date().toISOString()).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qcair','acai',9,'remove','published',?,?)").bind(new Date().toISOString(), new Date().toISOString()).run();
v = await view(); const p3 = await pipe();
const reasons = Object.fromEntries(gc().vacant.map(x => [x.side, x.reason]));
check('S7 withdrawn and unpublished works drop out too, each named with its reason; with every place vacant the pipeline sends an empty showcase (no row, no broken image)',
  p3.galleries[0].items.length === 0 && reasons.Left === 'the artist’s gallery is not published' && reasons.Centre === 'the artwork has been withdrawn or is not published' && reasons.Right === 'the artwork has been sold', JSON.stringify(reasons));
r = await call('POST', '/api/admin/showcase/contemporary/publish', FOUNDER);
check('S8 a showcase whose choices are no longer eligible cannot be published again until the founder chooses again', r.s === 409, r.t);
// Spaces: prepared privately, never published while in preparation
await call('POST', '/api/admin/galleries/spaces/members', FOUNDER, { artist_id: 'aben', source: 'founder_curation' });
await call('POST', '/api/galleries/spaces/accept', 'ben@example.test');
await call('POST', '/api/admin/galleries/spaces/artworks/waben2/place', FOUNDER); await call('POST', '/api/galleries/spaces/artworks/waben2/accept', 'ben@example.test');
const sp1 = await call('PUT', '/api/admin/showcase/spaces', FOUNDER, { items: [{ position: 2, artist_id: 'aben', artwork_id: 'waben2' }] });
const sp2 = await call('POST', '/api/admin/showcase/spaces/publish', FOUNDER);
const p4 = await pipe();
check('S9 Spaces: a showcase can be prepared privately from works placed in Spaces, but it cannot be published while Spaces is in preparation, and the pipeline sends nothing for it',
  sp1.s === 200 && sp2.s === 409 && /in preparation/.test(sp2.j.error || '') && p4.galleries.find(x => x.gallery === 'spaces').items.length === 0 && p4.galleries.find(x => x.gallery === 'spaces').status === 'in_preparation', JSON.stringify([sp1.s, sp2.s]));
const fs1 = await call('PUT', '/api/admin/galleries/spaces/features', FOUNDER, { items: [{ artist_id: 'aben', artwork_id: 'waben2' }] });
const gsp = (await view()).galleries.find(x => x.gallery_id === 'spaces');
check('D3 Spaces uses its own Artists in Focus: the same work in both is noted, and saving either selection is not refused',
  fs1.s === 200 && gsp.draft.length === 1 && gsp.draft[0].in_focus === true && gsp.focus_artworks.join() === 'waben2'
  && gc().draft.every(d => d.artwork_id !== 'waben2' || d.in_focus === false), JSON.stringify([fs1.s, fs1.t, gsp.draft]));
check('S10 the pipeline route needs the pipeline token', (await call('GET', '/api/pipeline/gallery-showcase', 'ann@example.test')).s >= 400);

/* ---- U · the founder's panel and notice ---- */
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1400, height: 1100 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
const pg = await ctx.newPage(); pg.on('dialog', d => d.accept());
await pg.goto(url + '/admin', { waitUntil: 'networkidle' }); await pg.waitForTimeout(600);
const alert = await pg.locator('.st-sc-alert').first().innerText().catch(() => '');
check('U1 the Review desk shows a prominent notice naming each vacant position, artwork and reason', /Gallery Showcase/.test(alert) && /Contemporary, right:/.test(alert) && /sold/.test(alert), alert);
await pg.goto(url + '/admin/galleries', { waitUntil: 'networkidle' }); await pg.waitForTimeout(700);
await pg.locator('.st-gm-tabs button[data-g="contemporary"]').click(); await pg.waitForTimeout(400);
const panel = await pg.locator('.st-sc').innerText();
check('U2 the Galleries tab has a Gallery Showcase panel with left, centre and right, the vacancies and the published showcase', /Gallery Showcase/.test(panel) && /Left/.test(panel) && /Centre/.test(panel) && /Right/.test(panel) && /empty on the public page/.test(panel), panel.slice(0, 300));
// choose Ben's other work on the left and Ann's first on the right, swap them, preview, save, publish
await pg.selectOption('[data-sc-a="0"]', 'aben'); await pg.waitForTimeout(150); await pg.selectOption('[data-sc-w="0"]', 'waben2'); await pg.waitForTimeout(150);
await pg.selectOption('[data-sc-a="1"]', ''); await pg.waitForTimeout(100);
await pg.selectOption('[data-sc-a="2"]', 'aann'); await pg.waitForTimeout(150); await pg.selectOption('[data-sc-w="2"]', 'waann1'); await pg.waitForTimeout(150);
const prev1 = await pg.locator('.st-sc-preview li').allInnerTexts();
await pg.click('[data-sc="swap"][data-i="2"][data-j="1"]'); await pg.waitForTimeout(150); await pg.click('[data-sc="swap"][data-i="1"][data-j="0"]'); await pg.waitForTimeout(150);
const prev2 = await pg.locator('.st-sc-preview li').allInnerTexts();
const pubDisabledWhileDirty = await pg.locator('[data-sc-publish]').isDisabled();
await pg.click('[data-sc-save]'); await pg.waitForTimeout(700);
const draftRows = (await db.prepare("SELECT position, artwork_id FROM gallery_showcase WHERE gallery_id='contemporary' AND stage='draft' ORDER BY position").all()).results.map(x => `${x.position}:${x.artwork_id}`).join();
const pubBefore = JSON.stringify(await pipe());
await pg.click('[data-sc-publish]'); await pg.waitForTimeout(900);
const p5 = await pipe();
check('U3 the founder chooses artist and artwork per position, swaps positions, previews the works together, saves a draft (nothing published), then publishes explicitly',
  prev1.length === 2 && /Work 2/.test(prev1[0]) && /Work 1/.test(prev1[1]) && /Work 1/.test(prev2[0]) && pubDisabledWhileDirty && draftRows === '1:waann1,2:waben2'
  && JSON.stringify(p5.galleries[0].items) === JSON.stringify([{ position: 1, artist: 'ann-test', work: 'waann1' }, { position: 2, artist: 'ben-test', work: 'waben2' }]) && pubBefore !== JSON.stringify(p5),
  JSON.stringify({ prev1, prev2, draftRows, p5: p5.galleries[0].items }));
check('U4 still: Artists in Focus, Gallery order, memberships and placements were not changed by any showcase action (Spaces membership and placement made by the test itself excepted)',
  JSON.stringify(JSON.parse(await others()).slice(0, 2)) === JSON.stringify(JSON.parse(o0).slice(0, 2)));
// D · the discreet notice in the Studio, on both sides, and never a block
await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (2,'artist','aann','waann1',?)").bind(new Date().toISOString()).run();
await pg.goto(url + '/admin/galleries', { waitUntil: 'networkidle' }); await pg.waitForTimeout(700);
await pg.locator('.st-gm-tabs button[data-g="contemporary"]').click(); await pg.waitForTimeout(400);
const dup1 = await pg.locator('.st-sc .st-sc-dup').allInnerTexts();
await pg.locator('.st-sc-slots').screenshot({ path: '/tmp/showcase-dup-contemporary.png' }).catch(() => {});
const dupRole = await pg.locator('.st-sc .st-sc-dup[role="alert"], .st-sc-alert .st-sc-dup').count();
// non-blocking: swap and save with the overlap present; the selection is kept as chosen
await pg.click('[data-sc="swap"][data-i="1"][data-j="0"]'); await pg.waitForTimeout(150);
const dupAfterSwap = await pg.locator('.st-sc-slot').nth(1).locator('.st-sc-dup').count();
await pg.click('[data-sc-save]'); await pg.waitForTimeout(700);
const draftD = (await db.prepare("SELECT position, artwork_id FROM gallery_showcase WHERE gallery_id='contemporary' AND stage='draft' ORDER BY position").all()).results.map(x => `${x.position}:${x.artwork_id}`).join();
check('D4 Contemporary panel: a discreet note on the slot whose work is also in Artists in Focus, which follows the work when positions are swapped; saving is not blocked and nothing is removed',
  dup1.length === 1 && /Also chosen for Artists in Focus/.test(dup1[0]) && dupRole === 0 && dupAfterSwap === 1 && draftD === '1:waben2,2:waann1'
  && (await db.prepare("SELECT artwork_id FROM homepage_features ORDER BY position").all()).results.map(x => x.artwork_id).join() === 'waben1,waann1', JSON.stringify({ dup1, dupRole, dupAfterSwap, draftD }));
await pg.goto(url + '/admin/featured', { waitUntil: 'networkidle' }); await pg.waitForTimeout(700);
const dupF = await pg.locator('.st-fa-card .st-sc-dup').allInnerTexts();
check('D5 Featured Artists (Contemporary Artists in Focus) shows the same discreet note on the card whose work is in the Contemporary showcase',
  dupF.length === 1 && /Also in the Contemporary Gallery Showcase/.test(dupF[0]), JSON.stringify(dupF));
await pg.goto(url + '/admin/galleries', { waitUntil: 'networkidle' }); await pg.waitForTimeout(700);
await pg.locator('.st-gm-tabs button[data-g="spaces"]').click(); await pg.waitForTimeout(400);
await pg.locator('.st-gm-focus').first().screenshot({ path: '/tmp/showcase-dup-spaces-focus.png' }).catch(() => {});
const spShow = await pg.locator('.st-sc .st-sc-dup').count(), spFocus = await pg.locator('.st-gm-focus .st-sc-dup').count();
await pg.locator('.st-gm-focus [data-f="rm"]').first().click(); await pg.waitForTimeout(200);
const spShowAfter = await pg.locator('.st-sc .st-sc-dup').count();
check('D6 Spaces: the note shows on both the showcase slot and the Artists in Focus entry, and follows unsaved edits (removing the focus entry clears it)',
  spShow === 1 && spFocus === 1 && spShowAfter === 0, JSON.stringify({ spShow, spFocus, spShowAfter }));
await b.close(); await mf.dispose();
console.log(`\n${results.filter(Boolean).length}/${results.length} passed`);
process.exit(results.every(Boolean) ? 0 : 1);
