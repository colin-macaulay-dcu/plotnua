// PROVE · PlotArt Studio · Homepage curation (founder brief 17 Nov 2026; migration 0016). Synthetic artists only; the Worker
// runs locally (Miniflare/workerd) with a local D1. Nothing here touches Cloudflare.
//   node test/prove-homepage.mjs [--shots DIR] [--real SELECTION.json]
import { readFileSync } from 'node:fs';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished, artistRows } from './seed.mjs';

const HERE = new URL('../', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
const { mf, url, db } = await start({ port: 8798 });
const call = async (method, path, email, body, headers = {}) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json', ...headers };
  if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text();
  let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const T = '2026-11-05T17:05:00.000Z';
console.log('PROVE · PlotArt Studio · Homepage curation');

const IMAGES = await mf.getR2Bucket('IMAGES', 'studio');
await seedPublished(db, { id: 'aaoi', slug: 'aoife-test', email: 'aoife@example.test', name: 'Aoife Test', works: 3, number: 1, bucket: IMAGES });
await seedPublished(db, { id: 'abri', slug: 'brian-test', email: 'brian@example.test', name: 'Brian Test', works: 2, number: 2 });
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('aunp','unpub-test','unpub@example.test','Unpub Test',0,'active',?,?)`).bind(T, T).run();
await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at)
  VALUES ('waunp1','aunp','draft','Draft work',2026,'Oil',40,50,600,'available','x',1,'none',0,?,?)`).bind(T, T).run();
const before = { a: await artistRows(db, 'aaoi'), b: await artistRows(db, 'abri'), works: (await db.prepare('SELECT * FROM artworks ORDER BY id').all()).results };

// H1 what the founder sees
let r = await call('GET', '/api/admin/homepage', FOUNDER);
check('H1 the founder sees only published galleries and their shown works with a main photograph (an unpublished artist is not offered)',
  r.s === 200 && r.j.installed === true && r.j.max === 6 && r.j.items.length === 0 && r.j.galleries.map(g => g.slug).join() === 'aoife-test,brian-test' &&
  r.j.galleries[0].works.length === 3 && !r.t.includes('Draft work') && !r.t.includes('unpub'), r.t);
r = await call('GET', '/admin/homepage', FOUNDER);
check('H2 the Review Desk has a Homepage tab and page', r.s === 200 && r.t.includes('/admin/homepage') && r.t.includes('Homepage'));

// H3 select, order, save
const sel = [{ kind: 'artwork', artist_id: 'abri', artwork_id: 'wabri2' }, { kind: 'artwork', artist_id: 'aaoi', artwork_id: 'waaoi1' }, { kind: 'artist', artist_id: 'aaoi', artwork_id: 'waaoi2' }];
r = await call('PUT', '/api/admin/homepage', FOUNDER, { items: sel });
check('H3 the founder saves three items in her order (two artworks, and an artist shown with the artwork she chose); publishing is requested',
  r.s === 200 && r.j.changed === true && ['scheduled', 'requested', 'failed'].includes(r.j.publish) &&
  r.j.items.map(i => `${i.position}:${i.kind}:${i.artist_id}:${i.artwork_id}`).join() === '1:artwork:abri:wabri2,2:artwork:aaoi:waaoi1,3:artist:aaoi:waaoi2', r.t);
const again = await call('PUT', '/api/admin/homepage', FOUNDER, { items: sel });
check('H4 saving the same selection again changes nothing and starts no publication', again.s === 200 && again.j.changed === false && again.j.publish === 'none');
r = await call('PUT', '/api/admin/homepage', FOUNDER, { items: [sel[1], sel[0], sel[2]] });
check('H5 the founder rearranges the order', r.s === 200 && r.j.items[0].artwork_id === 'waaoi1' && r.j.items[1].artwork_id === 'wabri2');
r = await call('PUT', '/api/admin/homepage', FOUNDER, { items: [sel[1], sel[2]] });
check('H6 the founder removes items', r.s === 200 && r.j.items.length === 2 && r.j.items[1].kind === 'artist' && r.j.items[1].artwork_id === 'waaoi2');
r = await call('PUT', '/api/admin/homepage', FOUNDER, { items: [sel[1], { kind: 'artist', artist_id: 'aaoi', artwork_id: 'waaoi3' }] });
const ordAfter = (await db.prepare("SELECT id, ord FROM artworks WHERE artist_id='aaoi' ORDER BY id").all()).results;
check('H6b the founder changes the artwork that represents a featured artist (the artist\'s own order of works is unchanged)',
  r.s === 200 && r.j.changed === true && r.j.items[1].kind === 'artist' && r.j.items[1].artwork_id === 'waaoi3' && r.j.items[1].shown.work.id === 'waaoi3' &&
  JSON.stringify(ordAfter) === JSON.stringify(before.works.filter(w => w.artist_id === 'aaoi').map(w => ({ id: w.id, ord: w.ord }))));

// H7 the pipeline
const pipe = await call('GET', '/api/pipeline/homepage', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
const pipeNo = await call('GET', '/api/pipeline/homepage', null);
check('H7 the pipeline receives only public identifiers (kind, gallery address and artwork id), in order; without its token it is refused',
  pipe.s === 200 && pipeNo.s === 401 && JSON.stringify(pipe.j.items) === JSON.stringify([{ kind: 'artwork', artist: 'aoife-test', work: 'waaoi1' }, { kind: 'artist', artist: 'aoife-test', work: 'waaoi3' }]) &&
  !/@|aaoi"|Aoife/.test(pipe.t), pipe.t);

// H8-H10 security
const art = ['GET', 'PUT'].map(m => call(m, '/api/admin/homepage', 'aoife@example.test', m === 'PUT' ? { items: [] } : undefined));
const [ag, ap] = await Promise.all(art);
const apage = await call('GET', '/admin/homepage', 'aoife@example.test');
const aimg = await call('GET', '/api/admin/homepage/image/iaaoi1', 'aoife@example.test');
check('H8 an artist cannot see or change the homepage selection or load its preview images (403 on every route)', ag.s === 403 && ap.s === 403 && apage.s === 403 && aimg.s === 403);
const anon = await call('GET', '/api/admin/homepage', null), stranger = await call('GET', '/api/admin/homepage', 'stranger@example.test');
const pipeAdmin = await call('PUT', '/api/admin/homepage', null, { items: [] }, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
check('H9 no sign-in, an unknown email or the pipeline token cannot reach the founder routes', anon.s === 401 && stranger.s === 403 && pipeAdmin.s === 401);
const xsite = await mf.dispatchFetch(url + '/api/admin/homepage', { method: 'PUT', headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER), 'Content-Type': 'application/json' }, body: '{"items":[]}' });
check('H10 a save without the Studio header (a cross-site request) is refused', xsite.status === 403);

// H11 validation
const bad = async b => (await call('PUT', '/api/admin/homepage', FOUNDER, b)).s;
const W = (a, w) => ({ kind: 'artwork', artist_id: a, artwork_id: w });
const v = [
  await bad({ items: [W('aaoi', 'waaoi1'), W('aaoi', 'waaoi2'), W('aaoi', 'waaoi3'), W('abri', 'wabri1'), W('abri', 'wabri2'), { kind: 'artist', artist_id: 'abri', artwork_id: 'wabri1' }, { kind: 'artist', artist_id: 'aaoi', artwork_id: 'waaoi1' }] }),
  await bad({ items: [W('aaoi', 'waaoi1'), W('aaoi', 'waaoi1')] }),
  await bad({ items: [W('aunp', 'waunp1')] }),
  await bad({ items: [{ kind: 'artist', artist_id: 'aunp', artwork_id: 'waunp1' }] }),
  await bad({ items: [{ kind: 'artist', artist_id: 'aaoi' }] }),
  await bad({ items: [{ kind: 'artist', artist_id: 'aaoi', artwork_id: 'wabri1' }] }),
  await bad({ items: [{ kind: 'artist', artist_id: 'aaoi', artwork_id: 'waaoi1' }, { kind: 'artist', artist_id: 'aaoi', artwork_id: 'waaoi2' }] }),
  await bad({ items: [W('aaoi', 'wabri1')] }),
  await bad({ items: [W('aaoi', 'wnotreal')] }),
  await bad({ items: [{ ...W('aaoi', 'waaoi1'), price_eur: 1 }] }),
  await bad({ items: [{ kind: 'artist', artist_id: 'aaoi', artwork_id: 'waaoi1', title: 'x' }] }),
  await bad({ items: [{ kind: 'gallery', artist_id: 'aaoi' }] }),
  await bad({ items: [], extra: 1 }),
  await bad([]),
];
const still = (await call('GET', '/api/admin/homepage', FOUNDER)).j.items;
check('H11 invalid selections are refused and change nothing (7 items, a repeat, unpublished work or artist, an artist without a chosen artwork or with another artist\'s, the same artist twice, an unknown work, extra fields, a wrong kind)',
  v.every(s => s >= 400 && s < 500) && still.length === 2 && still[1].artwork_id === 'waaoi3', v.join(','));
check('H12 the database itself refuses a seventh position, and an artwork or artist item without an artwork',
  await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (7, 'artwork', 'aaoi', 'waaoi1', '2026-11-17T19:00:00.000Z')").run().then(() => false, () => true) &&
  await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (5, 'artwork', 'aaoi', NULL, '2026-11-17T19:00:00.000Z')").run().then(() => false, () => true) &&
  await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (5, 'artist', 'aaoi', NULL, '2026-11-17T19:00:00.000Z')").run().then(() => false, () => true));

// H13 preview images
const okImg = await call('GET', '/api/admin/homepage/image/iaaoi1', FOUNDER);
const draftImg = await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, preview_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
  VALUES ('iaunp1','aunp','waunp1','main','originals/aunp/1.jpg','previews/aunp/1.jpg','x',1,10,10,'jpeg','x','self','{}',0,?)`).bind(T).run();
await IMAGES.put('previews/aunp/1.jpg', 'preview aunp 1');
const noImg = await call('GET', '/api/admin/homepage/image/iaunp1', FOUNDER);
check('H13 the founder preview loads only the main photograph of a work that can be featured (an unpublished artist\'s image is refused)', okImg.s === 200 && okImg.t === 'preview aaoi 1' && noImg.s === 404 && !!draftImg, `${okImg.s} ${noImg.s}`);

// H14 withdrawn or unpublished work drops out by itself
const a2 = await db.prepare('SELECT * FROM artists WHERE id=?').bind('aaoi').first();
const snap = JSON.parse((await db.prepare("SELECT snapshot FROM versions WHERE artist_id='aaoi' AND version=1").first()).snapshot);
snap.works = snap.works.filter(w => w.id !== 'waaoi3');
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('aaoi', 2, ?, 'seed', ?)").bind(JSON.stringify(snap), T).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qaaoi2','aaoi',2,'reviewed','published',?,?)").bind(T, T).run();
r = await call('GET', '/api/admin/homepage', FOUNDER);
let p2 = await call('GET', '/api/pipeline/homepage', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
check('H14 a work no longer in the published gallery drops out: an artist whose chosen artwork is withdrawn is not shown with another work (pipeline and Review Desk)',
  !!a2 && r.j.items[1].shown === null && JSON.stringify(p2.j.items) === JSON.stringify([{ kind: 'artwork', artist: 'aoife-test', work: 'waaoi1' }]), p2.t);
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('aaoi', 3, ?, 'seed', ?)").bind(JSON.stringify(snap), T).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qaaoi3','aaoi',3,'remove','published',?,?)").bind(T, T).run();
p2 = await call('GET', '/api/pipeline/homepage', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
r = await call('GET', '/api/admin/homepage', FOUNDER);
check('H15 a gallery taken down drops out entirely (pipeline and the works the founder can choose)', p2.j.items.length === 0 && !r.j.galleries.some(g => g.slug === 'aoife-test'), p2.t);

// H16 nothing else changes; H17 the audit
const after = { a: await artistRows(db, 'aaoi'), b: await artistRows(db, 'abri'), works: (await db.prepare('SELECT * FROM artworks ORDER BY id').all()).results };
const strip = o => { const c = structuredClone(o); delete c.versions; delete c.publish_queue; return c; };
check('H16 curating never changes an artist, artwork, image, price, availability, gallery position or permission (only the test\'s own publications differ)',
  JSON.stringify(strip(before.a)) === JSON.stringify(strip(after.a)) && JSON.stringify(before.b) === JSON.stringify(after.b) && JSON.stringify(before.works) === JSON.stringify(after.works.filter(w => w.id !== 'never')));
const au = (await db.prepare("SELECT actor, role, action, detail FROM audit WHERE action='homepage_features' ORDER BY id").all()).results;
check('H17 every change is in the audit log (who, before and after); an unchanged save is not',
  au.length === 4 && au.every(x => x.actor === FOUNDER && x.role === 'founder') && JSON.parse(au[0].detail).before.length === 0 &&
  JSON.parse(au[3].detail).before.join() === 'artwork:aaoi/waaoi1,artist:aaoi/waaoi2' && JSON.parse(au[3].detail).after.join() === 'artwork:aaoi/waaoi1,artist:aaoi/waaoi3', JSON.stringify(au));

// H18 the migration and the schema agree
const mig = readFileSync(HERE + 'migrations/0016_homepage_features.sql', 'utf8'), schema = readFileSync(HERE + 'schema.sql', 'utf8');
const ddl = s => s.slice(s.indexOf('CREATE TABLE IF NOT EXISTS homepage_features'), s.indexOf(');', s.indexOf('CREATE TABLE IF NOT EXISTS homepage_features')) + 2).replace(/\s+/g, ' ');
check('H18 migration 0016 creates only homepage_features, exactly as schema.sql declares it', ddl(mig).length > 50 && ddl(mig) === ddl(schema) && (mig.match(/CREATE TABLE/g) || []).length === 1 && !/ALTER|DROP TABLE (?!homepage)|UPDATE |DELETE /.test(mig.split('@@DDL-BEGIN')[1].split('@@DDL-END')[0]));

// H19 a Studio without the migration: the Homepage view says so and saving is refused, everything else unaffected
const { mf: mf2, url: url2, db: db2 } = await start({ port: 8799, schemaSql: schema.replace(/CREATE TABLE IF NOT EXISTS homepage_features[\s\S]*?\);\n/, '') });
const c2 = async (m, b) => { const x = await mf2.dispatchFetch(url2 + '/api/admin/homepage', { method: m, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(FOUNDER) }, body: b && JSON.stringify(b) }); return { s: x.status, j: await x.json().catch(() => ({})) }; };
const g2 = await c2('GET'), s2 = await c2('PUT', { items: [] });
const pp2 = await mf2.dispatchFetch(url2 + '/api/pipeline/homepage', { headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } }).then(x => x.json());
check('H19 before migration 0016 the view reports "not set up", a save is refused (409) and the pipeline reports not installed', g2.s === 200 && g2.j.installed === false && s2.s === 409 && pp2.installed === false && !!db2);
await mf2.dispose();

// H20 in a browser: the founder features an artist by choosing which published artwork represents them, then saves
{
  await db.prepare('DELETE FROM homepage_features').run();
  const { chromium } = await import('playwright');
  const br = await chromium.launch();
  const ctx = await br.newContext({ viewport: { width: 1280, height: 900 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { exp: 3600 }) } });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.goto(url + '/admin/homepage'); await pg.waitForSelector('[data-artist="abri"]');
  await pg.click('[data-artist="abri"]');
  const offered = await pg.$$eval('[data-rep]', bs => bs.map(b => b.dataset.rep));
  const added = await pg.$$eval('.st-hp-card', c => c.length);
  await pg.click('[data-rep="wabri2"]'); await pg.click('#hp-save'); await pg.waitForFunction(() => /Saved/.test(document.getElementById('hp-state').textContent));
  const saved = (await call('GET', '/api/admin/homepage', FOUNDER)).j.items;
  await pg.click('[data-change="0"]'); await pg.click('[data-rep="wabri1"]'); await pg.click('#hp-save'); await pg.waitForFunction(() => /Saved/.test(document.getElementById('hp-state').textContent));
  const changed = (await call('GET', '/api/admin/homepage', FOUNDER)).j.items;
  const grid = await pg.evaluate(() => { const g = document.querySelector('.st-hp-grid'); return g.scrollWidth <= g.clientWidth && document.documentElement.scrollWidth <= document.documentElement.clientWidth; });
  await br.close();
  check('H20 in the Review Desk: "Feature artist" offers only that artist\'s published works and adds nothing until one is chosen; the choice is saved and can be changed; no sideways scrolling',
    offered.join() === 'wabri1,wabri2' && added === 0 && saved.length === 1 && saved[0].kind === 'artist' && saved[0].artwork_id === 'wabri2' &&
    changed.length === 1 && changed[0].artwork_id === 'wabri1' && grid && !errs.length, JSON.stringify({ offered, added, saved, changed, grid, errs }));
}

// optional: screenshots of the Review Desk Homepage view
const shots = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
if (shots) {
  const { chromium } = await import('playwright');
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1360, height: 900 }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { exp: 3600 }) } });
  const pg = await ctx.newPage(); await pg.goto(url + '/admin/homepage'); await pg.waitForTimeout(800);
  await pg.screenshot({ path: shots + '/review-desk-homepage-synthetic.png', fullPage: true }); await b.close();
}

console.log(`\nPLOTART HOMEPAGE CURATION (Studio) · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose();
process.exit(results.every(Boolean) ? 0 : 1);
