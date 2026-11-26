// PROVE · PlotArt Studio · unified gallery curation (migration 0029, founder approval for development 26 Nov 2026).
// Synthetic artists only; local Miniflare.   node test/prove-curation.mjs
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { chromium } = require('playwright');

const HERE = new URL('..', import.meta.url).pathname;
const OUT = process.env.SHOTS || null;
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
console.log('PROVE · PlotArt Studio · unified gallery curation (0029)');
const TEST = 'atestacct', T = '2026-11-20T10:00:00.000Z';
const { mf, url, db } = await start({ port: 8886, env: { TEST_ARTIST_IDS: TEST } });
const call = async (method, path, email, body, headers = {}) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json', ...headers }; if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j, t };
};
const PIPE = { Authorization: 'Bearer ' + PIPELINE_TOKEN };
for (const [i, n] of ['ann', 'ben', 'cai', 'dan', 'eve', 'fay'].entries()) await seedPublished(db, { id: 'a' + n, slug: n + '-test', email: n + '@example.test', name: n[0].toUpperCase() + n.slice(1) + ' Test', works: 3, number: i + 1 });
await seedPublished(db, { id: TEST, slug: 'test-account', email: 'test@example.test', name: 'Test Account', works: 2 });
// today's production shape: founding positions, the published showcase, Artists in Focus; then migration 0029 sets up
for (const [p, a] of [[1, 'ann'], [2, 'ben'], [3, 'cai'], [4, 'dan'], [5, 'eve']])
  await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(p, 'a' + a, T).run();
await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (1, 'artist', 'aeve', 'waeve2', ?)").bind(T).run();
await db.prepare('DELETE FROM gallery_showcase').run();
for (const st of ['draft', 'published']) for (const [p, a] of [[1, 'ann'], [2, 'ben'], [3, 'cai']])
  await db.prepare("INSERT INTO gallery_showcase VALUES ('contemporary',?,?,?,?,?,'f@x.ie')").bind(st, p, 'a' + a, `wa${a}1`, T).run();
const MIG = readFileSync(HERE + 'migrations/0029_gallery_curation.sql', 'utf8');
for (const st of statements(MIG)) await db.prepare(st).run();
const keep = async () => JSON.stringify(await Promise.all(['homepage_features', 'gallery_positions', 'gallery_features', 'gallery_order', 'gallery_memberships', 'artwork_placements', 'artists', 'artworks', 'images']
  .map(async t => (await db.prepare(`SELECT * FROM ${t} ORDER BY rowid`).all()).results)));
const k0 = await keep();
const view = async () => (await call('GET', '/api/admin/curation', FOUNDER)).j;
const pipe = async () => (await call('GET', '/api/pipeline/gallery-curation', null, undefined, PIPE)).j;
const C = v => v.galleries.find(x => x.gallery_id === 'contemporary');
const fmt = list => list.map(r => `${r.artist_id.slice(1)}${r.opening ? '*' : ''}${r.artwork_id ? '=' + r.artwork_id : ''}${r.new ? '+new' : ''}`).join(',');
let v = await view();
check('C1 one arrangement: the opening row (*) then today\'s order, the Artists in Focus artwork kept, an unplaced published artist added at the end and flagged; no test account anywhere',
  v.installed && fmt(C(v).draft) === 'ann*=waann1,ben*=waben1,cai*=wacai1,dan,eve=waeve2,fay+new' && fmt(C(v).published) === fmt(C(v).draft)
  && !JSON.stringify(v).includes(TEST) && C(v).artists.length === 6, fmt(C(v).draft));
const p0 = await pipe();
check('C2 the pipeline sends gallery addresses and artwork ids only: opening row, then the rest (null = their first available work), held empty',
  JSON.stringify(p0.galleries[0]) === JSON.stringify({ gallery: 'contemporary', status: 'open', opening: [{ position: 1, artist: 'ann-test', work: 'waann1' }, { position: 2, artist: 'ben-test', work: 'waben1' }, { position: 3, artist: 'cai-test', work: 'wacai1' }],
    rest: [{ artist: 'dan-test', work: null }, { artist: 'eve-test', work: 'waeve2' }], held: [] }), JSON.stringify(p0.galleries[0]));
// the founder moves Dan into the opening row (first place, with his second work), Ann out to place 5 (automatic artwork)
const items = [{ artist_id: 'adan', artwork_id: 'wadan2' }, { artist_id: 'aben', artwork_id: 'waben1' }, { artist_id: 'acai', artwork_id: 'wacai1' },
  { artist_id: 'aeve', artwork_id: 'waeve3' }, { artist_id: 'aann', artwork_id: null }, { artist_id: 'afay', artwork_id: 'wafay2' }];
let r = await call('PUT', '/api/admin/curation/contemporary', FOUNDER, { items });
const rows = async (t, st) => (await db.prepare(`SELECT position, artist_id, artwork_id FROM ${t} WHERE gallery_id='contemporary' AND stage=? ORDER BY position`).bind(st).all()).results.map(x => `${x.position}:${x.artist_id.slice(1)}${x.artwork_id ? '=' + x.artwork_id : ''}`).join(',');
check('C3 moves between the opening row and the rest are saved together as the draft (both tables in one batch); nothing is published',
  r.s === 200 && await rows('gallery_showcase', 'draft') === '1:dan=wadan2,2:ben=waben1,3:cai=wacai1' && await rows('gallery_curation', 'draft') === '4:eve=waeve3,5:ann,6:fay=wafay2'
  && JSON.stringify(await pipe()) === JSON.stringify(p0) && C(r.j).unpublished_changes === true, r.t);
const d1 = (await rows('gallery_showcase', 'draft')) + '|' + (await rows('gallery_curation', 'draft'));
const bad = [
  await call('PUT', '/api/admin/curation/contemporary', FOUNDER, { items: [...items, { artist_id: 'adan', artwork_id: null }] }),                         // an artist twice
  await call('PUT', '/api/admin/curation/contemporary', FOUNDER, { items: [{ artist_id: TEST, artwork_id: 'watestacct1' }] }),                          // test account
  await call('PUT', '/api/admin/curation/contemporary', FOUNDER, { items: [{ artist_id: 'aann', artwork_id: null }, ...items.slice(1, 4)] }),          // opening without an artwork
  await call('PUT', '/api/admin/curation/contemporary', FOUNDER, { items: [{ artist_id: 'aann', artwork_id: 'waben1' }] }),                             // another artist's work
  await call('PUT', '/api/admin/curation/contemporary', FOUNDER, { items: [...items.slice(0, 3), { artist_id: 'aeve', artwork_id: 'waann2' }] }),       // 4+ another artist's work
  await call('PUT', '/api/admin/curation/contemporary', FOUNDER, { items: [...items.slice(0, 3), { artist_id: 'azzz', artwork_id: null }] }),           // not a member
  await call('PUT', '/api/admin/curation/contemporary', 'ann@example.test', { items }),                                                                 // an artist
];
check('C4 refused, changing nothing: an artist twice, a test account, an opening place without an available artwork, another artist\'s work (opening or later), a non-member; only the founder can save',
  bad.slice(0, 6).every(x => x.s === 400 || x.s === 409) && bad[6].s === 403 && (await rows('gallery_showcase', 'draft')) + '|' + (await rows('gallery_curation', 'draft')) === d1,
  JSON.stringify(bad.map(x => x.s)));
const old = [await call('PUT', '/api/admin/showcase/contemporary', FOUNDER, { items: [{ position: 1, artist_id: 'aann', artwork_id: 'waann1' }] }), await call('POST', '/api/admin/showcase/contemporary/publish', FOUNDER)];
check('C5 the separate showcase writes are closed once curation is installed (no partial update outside Curate)', old.every(x => x.s === 409) && (await rows('gallery_showcase', 'draft')).startsWith('1:dan'), JSON.stringify(old.map(x => x.s)));
let dup = 'refused'; try { await db.prepare("INSERT INTO gallery_curation VALUES ('contemporary','draft',9,'adan',NULL,'2026-11-26T00:00:00.000Z','f@x.ie')").run(); dup = 'ok'; } catch { /* */ }
check('C6 the database itself refuses an opening-row artist in the rest of the same stage', dup === 'refused');
r = await call('POST', '/api/admin/curation/contemporary/publish', FOUNDER);
const p1 = await pipe();
check('C7 Publish replaces both published stages from the drafts and starts publishing; the pipeline sends the new arrangement',
  r.s === 200 && 'publish' in r.j && await rows('gallery_showcase', 'published') === '1:dan=wadan2,2:ben=waben1,3:cai=wacai1' && await rows('gallery_curation', 'published') === '4:eve=waeve3,5:ann,6:fay=wafay2'
  && JSON.stringify(p1.galleries[0].opening.map(o => o.artist)) === '["dan-test","ben-test","cai-test"]' && JSON.stringify(p1.galleries[0].rest) === JSON.stringify([{ artist: 'eve-test', work: 'waeve3' }, { artist: 'ann-test', work: null }, { artist: 'fay-test', work: 'wafay2' }])
  && !!(await db.prepare("SELECT 1 FROM audit WHERE action='gallery_curation_published'").first()) && C(r.j).unpublished_changes === false, r.t);
// routine artist publications: Ben's opening work and Eve's chosen work are sold
const sell = async (aid, wid, qid) => { const lv = await db.prepare('SELECT version, snapshot FROM versions WHERE artist_id=? ORDER BY version DESC').bind(aid).first(); const s = JSON.parse(lv.snapshot);
  s.works.find(w => w.id === wid).availability = 'sold';
  await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?, ?, ?, 'test', ?)").bind(aid, lv.version + 1, JSON.stringify(s), T).run();
  await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?,?,?,'instant','published',?,?)").bind(qid, aid, lv.version + 1, T, T).run(); };
await sell('aben', 'waben1', 'qb'); await sell('aeve', 'waeve3', 'qe');
const p2 = await pipe(); v = await view();
const n = C(v).notices;
check('C8 a sold opening work: the place is left empty (no substitute), its artist is held (not moved below), and the founder is told prominently',
  JSON.stringify(p2.galleries[0].opening.map(o => o.position)) === '[1,3]' && JSON.stringify(p2.galleries[0].held) === '["ben-test"]'
  && n.some(x => x.opening && x.position === 2 && /sold/.test(x.notice)) && await rows('gallery_showcase', 'published') === '1:dan=wadan2,2:ben=waben1,3:cai=wacai1', JSON.stringify({ p: p2.galleries[0], n }));
check('C9 a sold chosen work in place 4+: the artist keeps their place and the page shows their first available work instead, with a notice; the record keeps the choice',
  JSON.stringify(p2.galleries[0].rest[0]) === JSON.stringify({ artist: 'eve-test', work: null }) && n.some(x => !x.opening && /sold: showing “Work 1” instead/.test(x.notice))
  && (await rows('gallery_curation', 'published')).startsWith('4:eve=waeve3'), JSON.stringify(n));
// the founder can take a work out of Contemporary even if it was one of the (retired) Artists in Focus
r = await call('POST', '/api/admin/galleries/contemporary/artworks/waeve2/withdraw', FOUNDER);
check('C10 taking a work out is never blocked by a curatorial choice (the former Artists in Focus work)', r.s === 200, r.t);
await call('POST', '/api/admin/galleries/contemporary/artworks/waeve2/restore', FOUNDER);
// a newly published artist
await seedPublished(db, { id: 'agil', slug: 'gil-test', email: 'gil@example.test', name: 'Gil Test', works: 2 });
v = await view(); const p3 = await pipe();
check('C11 a newly published artist is added at the end of the founder\'s view (never the opening row), with a notice; the pipeline leaves the placing to the page (appended at the end)',
  C(v).draft.at(-1).artist_id === 'agil' && C(v).draft.at(-1).new && !C(v).draft.at(-1).opening && C(v).notices.some(x => x.display_name === 'Gil Test' && /newly published/.test(x.notice))
  && !JSON.stringify(p3.galleries[0]).includes('gil-test'), fmt(C(v).draft));
// Spaces: prepared privately, never published while in preparation
await call('POST', '/api/admin/galleries/spaces/members', FOUNDER, { artist_id: 'aben', source: 'founder_curation' });
await call('POST', '/api/galleries/spaces/accept', 'ben@example.test');
await call('POST', '/api/admin/galleries/spaces/artworks/waben2/place', FOUNDER); await call('POST', '/api/galleries/spaces/artworks/waben2/accept', 'ben@example.test');
const s1 = await call('PUT', '/api/admin/curation/spaces', FOUNDER, { items: [{ artist_id: 'aben', artwork_id: 'waben2' }] });
const s2 = await call('POST', '/api/admin/curation/spaces/publish', FOUNDER);
check('C12 Spaces: arranged privately from its own members and placed works; not published while in preparation; the pipeline sends nothing for it',
  s1.s === 200 && s2.s === 409 && /in preparation/.test(s2.j.error || '') && (await pipe()).galleries.find(x => x.gallery === 'spaces').opening.length === 0, JSON.stringify([s1.s, s1.t.slice(0, 200), s2.s]));
check('C13 the pipeline route needs the pipeline token; an artist cannot read or change the arrangement',
  (await call('GET', '/api/pipeline/gallery-curation', 'ann@example.test')).s >= 400 && (await call('GET', '/api/admin/curation', 'ann@example.test')).s === 403
  && (await call('POST', '/api/admin/curation/contemporary/publish', 'ann@example.test')).s === 403);
check('C14 founding positions, Artists in Focus records, gallery order, memberships (Spaces by the test excepted), artists, artworks and images are unchanged by curating',
  JSON.stringify(JSON.parse(await keep()).slice(0, 4)) === JSON.stringify(JSON.parse(k0).slice(0, 4)));

/* ---- U · the founder's Curate screen ---- */
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1400, height: 1100 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
const pg = await ctx.newPage(); pg.on('dialog', d => d.accept()); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
await pg.goto(url + '/admin', { waitUntil: 'networkidle' }); await pg.waitForTimeout(600);
const alert = await pg.locator('.st-sc-alert').first().innerText().catch(() => ''), notes = await pg.locator('main').innerText();
const tabs = await pg.$$eval('.st-tabs a', a => a.map(x => x.textContent));
check('U1 the Review desk names the empty opening place prominently and lists the other arrangement notes; the Featured Artists and Gallery order tabs are gone',
  /Contemporary, opening place 2/.test(alert) && /sold/.test(alert) && /Gallery arrangement/.test(notes) && /Gil Test/.test(notes) && !tabs.includes('Featured Artists') && !tabs.includes('Gallery order') && tabs.includes('Galleries'), alert + ' | ' + tabs.join());
await pg.goto(url + '/admin/galleries', { waitUntil: 'networkidle' }); await pg.waitForTimeout(700);
await pg.locator('.st-gm-tabs button[data-g="contemporary"]').click(); await pg.waitForTimeout(500);
const card = await pg.locator('.st-cu').innerText();
const names = async () => pg.$$eval('.st-cu-row .st-cu-who .st-work-t', x => x.map(e => e.textContent.replace('TEST', '').trim()));
const n0 = await names();
check('U2 Galleries → Curate: one list with the opening row marked, every artist once, a preview of the whole page; no separate Showcase, Artists in Focus or Order cards',
  /Curate Contemporary/.test(card) && n0.join() === 'Dan Test,Ben Test,Cai Test,Eve Test,Ann Test,Fay Test,Gil Test' && (await pg.locator('.st-cu-row.is-open').count()) === 3
  && (await pg.locator('.st-cu-prev .st-sc-preview li').count()) === 2 && (await pg.locator('.st-cu-grid li').count()) === 4
  && !(await pg.locator('.st-sc').count()) && !(await pg.locator('.st-gm-focuslist').count()) && !/Artists in Focus ·/.test(card), n0.join() + ' | ' + card.slice(0, 300));
// move Gil (last) into the opening row (position 1), choose Ben's other work, Ann to automatic; save; publish
await pg.selectOption('[data-cu-to="6"]', '0'); await pg.waitForTimeout(200);
const n1 = await names();
await pg.click('.st-cu-row[data-i="2"] [data-cu="pick"]:not(.st-cu-thumb)'); await pg.waitForTimeout(150);
await pg.click('.st-cu-row[data-i="2"] [data-cu="art"][data-w="waben3"]'); await pg.waitForTimeout(150);
if (OUT) { await pg.locator('.st-cu').screenshot({ path: OUT + '/studio-curate.png' }); }
const pubDisabled = await pg.locator('[data-cu-publish]').isDisabled();
await pg.click('[data-cu-save]'); await pg.waitForTimeout(800);
const saveMsg = await pg.locator('.st-gm-msg').innerText().catch(() => '');
const sd = await rows('gallery_showcase', 'draft'), cd = await rows('gallery_curation', 'draft');
if (saveMsg) console.log('save message:', saveMsg);
await pg.click('[data-cu-publish]', { timeout: 5000 }).catch(() => {}); await pg.waitForTimeout(900);
const p4 = await pipe();
check('U3 the founder moves an artist into the opening row (their first available work preselected), changes another artist\'s artwork through the thumbnail picker, saves a private draft, then publishes explicitly',
  n1.slice(0, 3).join() === 'Gil Test,Dan Test,Ben Test' && pubDisabled && sd === '1:gil=wagil1,2:dan=wadan2,3:ben=waben3' && cd === '4:cai=wacai1,5:eve=waeve3,6:ann,7:fay=wafay2'
  && JSON.stringify(p4.galleries[0].opening.map(o => `${o.artist}:${o.work}`)) === '["gil-test:wagil1","dan-test:wadan2","ben-test:waben3"]' && JSON.stringify(p4.galleries[0].held) === '[]' && !errs.length,
  JSON.stringify({ n1, sd, cd, op: p4.galleries[0].opening, errs }));
await b.close(); await mf.dispose();
console.log(`\n${results.filter(Boolean).length}/${results.length} passed`);
process.exit(results.every(Boolean) ? 0 : 1);
