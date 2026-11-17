// PROVE · PlotArt Studio · Featured Artists (founder brief 17 Nov 2026: the homepage curation moved to the Artists' Gallery;
// migration 0016 and its table reused unchanged). Synthetic artists only; the Worker
// runs locally (Miniflare/workerd) with a local D1. Nothing here touches Cloudflare.
//   node test/prove-featured-artists.mjs [--shots DIR] [--real SELECTION.json]
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
console.log('PROVE · PlotArt Studio · Featured Artists');

const IMAGES = await mf.getR2Bucket('IMAGES', 'studio');
await seedPublished(db, { id: 'aaoi', slug: 'aoife-test', email: 'aoife@example.test', name: 'Aoife Test', works: 3, number: 1, bucket: IMAGES });
await seedPublished(db, { id: 'abri', slug: 'brian-test', email: 'brian@example.test', name: 'Brian Test', works: 2, number: 2 });
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('aunp','unpub-test','unpub@example.test','Unpub Test',0,'active',?,?)`).bind(T, T).run();
await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at)
  VALUES ('waunp1','aunp','draft','Draft work',2026,'Oil',40,50,600,'available','x',1,'none',0,?,?)`).bind(T, T).run();
const before = { a: await artistRows(db, 'aaoi'), b: await artistRows(db, 'abri'), works: (await db.prepare('SELECT * FROM artworks ORDER BY id').all()).results };

// H1 what the founder sees
let r = await call('GET', '/api/admin/featured', FOUNDER);
check('H1 the founder sees only published galleries, their shown works with a main photograph and the start of each published biography (an unpublished artist is not offered)',
  r.s === 200 && r.j.installed === true && r.j.max === 6 && r.j.items.length === 0 && r.j.galleries.map(g => g.slug).join() === 'aoife-test,brian-test' &&
  r.j.galleries[0].works.length === 3 && typeof r.j.galleries[0].intro === 'string' && !r.t.includes('Draft work') && !r.t.includes('unpub'), r.t);
r = await call('GET', '/admin/featured', FOUNDER);
const old = await mf.dispatchFetch(url + '/admin/homepage', { redirect: 'manual', headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } }).then(x => ({ s: x.status, loc: x.headers.get('location') || '' }));
check('H2 the Review Desk tab is now "Featured Artists" (no "Homepage" tab); its earlier address redirects to it',
  r.s === 200 && r.t.includes('href="/admin/featured" data-t="feat">Featured Artists</a>') && !r.t.includes('>Homepage</a>') && old.s === 302 && old.loc.endsWith('/admin/featured'), `${r.s} ${old.s} ${old.loc}`);

// H3 select, order, save: artists only, each with the artwork the founder chose
const F = (a, w) => ({ artist_id: a, artwork_id: w });
const sel = [F('abri', 'wabri2'), F('aaoi', 'waaoi2')];
r = await call('PUT', '/api/admin/featured', FOUNDER, { items: sel });
check('H3 the founder saves two artists in her order, each with the artwork she chose; stored as artists; publishing is requested',
  r.s === 200 && r.j.changed === true && ['scheduled', 'requested', 'failed'].includes(r.j.publish) &&
  r.j.items.map(i => `${i.position}:${i.earlier_kind}:${i.artist_id}:${i.artwork_id}`).join() === '1:artist:abri:wabri2,2:artist:aaoi:waaoi2', r.t);
const again = await call('PUT', '/api/admin/featured', FOUNDER, { items: sel });
check('H4 saving the same selection again changes nothing and starts no publication', again.s === 200 && again.j.changed === false && again.j.publish === 'none');
r = await call('PUT', '/api/admin/featured', FOUNDER, { items: [sel[1], sel[0]] });
check('H5 the founder reorders the artists', r.s === 200 && r.j.items[0].artist_id === 'aaoi' && r.j.items[1].artist_id === 'abri');
r = await call('PUT', '/api/admin/featured', FOUNDER, { items: [sel[1]] });
check('H6 the founder removes an artist', r.s === 200 && r.j.items.length === 1 && r.j.items[0].artist_id === 'aaoi');
r = await call('PUT', '/api/admin/featured', FOUNDER, { items: [F('aaoi', 'waaoi3'), F('abri', 'wabri1')] });
const ordAfter = (await db.prepare("SELECT id, ord FROM artworks WHERE artist_id='aaoi' ORDER BY id").all()).results;
check('H6b the founder changes the artwork that represents an artist and adds another (the artist\'s own order of works is unchanged)',
  r.s === 200 && r.j.changed === true && r.j.items[0].artwork_id === 'waaoi3' && r.j.items[0].shown.work.id === 'waaoi3' &&
  JSON.stringify(ordAfter) === JSON.stringify(before.works.filter(w => w.artist_id === 'aaoi').map(w => ({ id: w.id, ord: w.ord }))));

// H7 the pipeline
const pipe = await call('GET', '/api/pipeline/featured-artists', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
const pipeNo = await call('GET', '/api/pipeline/featured-artists', null);
const pipeOld = await call('GET', '/api/pipeline/homepage', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
check('H7 the pipeline receives only public identifiers (gallery address and artwork id), each artist once, in order; without its token it is refused; the earlier route gives the same artists',
  pipe.s === 200 && pipeNo.s === 401 && JSON.stringify(pipe.j.items) === JSON.stringify([{ artist: 'aoife-test', work: 'waaoi3' }, { artist: 'brian-test', work: 'wabri1' }]) &&
  JSON.stringify(pipeOld.j.items) === JSON.stringify([{ kind: 'artist', artist: 'aoife-test', work: 'waaoi3' }, { kind: 'artist', artist: 'brian-test', work: 'wabri1' }]) &&
  !/@|aaoi"|Aoife/.test(pipe.t), pipe.t);

// H7b earlier homepage records (migration 0016 rows of kind 'artwork', an artist listed twice) are read as artists, each once
await db.prepare('DELETE FROM homepage_features').run();
for (const [n, k, a, w] of [[1, 'artwork', 'abri', 'wabri2'], [2, 'artist', 'aaoi', 'waaoi1'], [3, 'artwork', 'aaoi', 'waaoi2']])
  await db.prepare('INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (?,?,?,?,?)').bind(n, k, a, w, T).run();
const lv = await call('GET', '/api/admin/featured', FOUNDER);
const lp = await call('GET', '/api/pipeline/featured-artists', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
const rows0 = (await db.prepare('SELECT * FROM homepage_features ORDER BY position').all()).results;
check('H7b earlier homepage records are read as artists (an earlier single artwork = its artist, shown with that artwork), an artist listed twice is shown once, and nothing is rewritten until the founder saves',
  JSON.stringify(lp.j.items) === JSON.stringify([{ artist: 'brian-test', work: 'wabri2' }, { artist: 'aoife-test', work: 'waaoi1' }]) &&
  lv.j.items[2].repeat === true && lv.j.items[2].shown === null && lv.j.items[0].earlier_kind === 'artwork' && rows0.length === 3 && rows0[0].kind === 'artwork', lp.t);
r = await call('PUT', '/api/admin/featured', FOUNDER, { items: [F('aaoi', 'waaoi3'), F('abri', 'wabri1')] });
check('H7c the founder\'s next save stores artists only', r.s === 200 && (await db.prepare("SELECT COUNT(*) n FROM homepage_features WHERE kind <> 'artist'").first()).n === 0);

// H8-H10 security
const art = ['GET', 'PUT'].map(m => call(m, '/api/admin/featured', 'aoife@example.test', m === 'PUT' ? { items: [] } : undefined));
const [ag, ap] = await Promise.all(art);
const apage = await call('GET', '/admin/featured', 'aoife@example.test');
const aold = await call('GET', '/admin/homepage', 'aoife@example.test');
const aimg = await call('GET', '/api/admin/featured/image/iaaoi1', 'aoife@example.test');
check('H8 an artist cannot see or change Featured Artists or load its preview images (403 on every route, the earlier address included)', ag.s === 403 && ap.s === 403 && apage.s === 403 && aold.s === 403 && aimg.s === 403);
const anon = await call('GET', '/api/admin/featured', null), stranger = await call('GET', '/api/admin/featured', 'stranger@example.test');
const pipeAdmin = await call('PUT', '/api/admin/featured', null, { items: [] }, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
check('H9 no sign-in, an unknown email or the pipeline token cannot reach the founder routes', anon.s === 401 && stranger.s === 403 && pipeAdmin.s === 401);
const xsite = await mf.dispatchFetch(url + '/api/admin/featured', { method: 'PUT', headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER), 'Content-Type': 'application/json' }, body: '{"items":[]}' });
check('H10 a save without the Studio header (a cross-site request) is refused', xsite.status === 403);

// H11 validation
const bad = async b => (await call('PUT', '/api/admin/featured', FOUNDER, b)).s;
const v = [
  await bad({ items: [F('aaoi', 'waaoi1'), F('abri', 'wabri1'), F('aaoi', 'waaoi2'), F('abri', 'wabri2'), F('aaoi', 'waaoi3'), F('abri', 'wabri1'), F('aaoi', 'waaoi1')] }),
  await bad({ items: [F('aaoi', 'waaoi1'), F('aaoi', 'waaoi1')] }),
  await bad({ items: [F('aaoi', 'waaoi1'), F('aaoi', 'waaoi2')] }),
  await bad({ items: [F('aunp', 'waunp1')] }),
  await bad({ items: [{ artist_id: 'aaoi' }] }),
  await bad({ items: [F('aaoi', 'wabri1')] }),
  await bad({ items: [F('aaoi', 'wnotreal')] }),
  await bad({ items: [{ ...F('aaoi', 'waaoi1'), price_eur: 1 }] }),
  await bad({ items: [{ ...F('aaoi', 'waaoi1'), kind: 'artwork' }] }),
  await bad({ items: [{ ...F('aaoi', 'waaoi1'), title: 'x' }] }),
  await bad({ items: [], extra: 1 }),
  await bad([]),
];
const still = (await call('GET', '/api/admin/featured', FOUNDER)).j.items;
check('H11 invalid selections are refused and change nothing (7 artists, an artist twice, unpublished work or artist, no chosen artwork or another artist\'s, an unknown work, extra fields, a single-artwork item)',
  v.every(s => s >= 400 && s < 500) && still.length === 2 && still[0].artwork_id === 'waaoi3', v.join(','));
check('H12 the database itself refuses a seventh position, and an artwork or artist item without an artwork',
  await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (7, 'artwork', 'aaoi', 'waaoi1', '2026-11-17T19:00:00.000Z')").run().then(() => false, () => true) &&
  await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (5, 'artwork', 'aaoi', NULL, '2026-11-17T19:00:00.000Z')").run().then(() => false, () => true) &&
  await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (5, 'artist', 'aaoi', NULL, '2026-11-17T19:00:00.000Z')").run().then(() => false, () => true));

// H13 preview images
const okImg = await call('GET', '/api/admin/featured/image/iaaoi1', FOUNDER);
const draftImg = await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, preview_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
  VALUES ('iaunp1','aunp','waunp1','main','originals/aunp/1.jpg','previews/aunp/1.jpg','x',1,10,10,'jpeg','x','self','{}',0,?)`).bind(T).run();
await IMAGES.put('previews/aunp/1.jpg', 'preview aunp 1');
const noImg = await call('GET', '/api/admin/featured/image/iaunp1', FOUNDER);
check('H13 the founder preview loads only the main photograph of a work that can be featured (an unpublished artist\'s image is refused)', okImg.s === 200 && okImg.t === 'preview aaoi 1' && noImg.s === 404 && !!draftImg, `${okImg.s} ${noImg.s}`);

// H14 withdrawn or unpublished work drops out by itself
const a2 = await db.prepare('SELECT * FROM artists WHERE id=?').bind('aaoi').first();
const snap = JSON.parse((await db.prepare("SELECT snapshot FROM versions WHERE artist_id='aaoi' AND version=1").first()).snapshot);
snap.works = snap.works.filter(w => w.id !== 'waaoi3');
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('aaoi', 2, ?, 'seed', ?)").bind(JSON.stringify(snap), T).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qaaoi2','aaoi',2,'reviewed','published',?,?)").bind(T, T).run();
r = await call('GET', '/api/admin/featured', FOUNDER);
let p2 = await call('GET', '/api/pipeline/featured-artists', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
check('H14 a work no longer in the published gallery drops out: an artist whose chosen artwork is withdrawn is not shown with another work (pipeline and Review Desk)',
  !!a2 && r.j.items[0].shown === null && JSON.stringify(p2.j.items) === JSON.stringify([{ artist: 'brian-test', work: 'wabri1' }]), p2.t);
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('aaoi', 3, ?, 'seed', ?)").bind(JSON.stringify(snap), T).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qaaoi3','aaoi',3,'remove','published',?,?)").bind(T, T).run();
p2 = await call('GET', '/api/pipeline/featured-artists', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
r = await call('GET', '/api/admin/featured', FOUNDER);
check('H15 a gallery taken down drops out entirely (pipeline and the artists the founder can choose)', JSON.stringify(p2.j.items) === JSON.stringify([{ artist: 'brian-test', work: 'wabri1' }]) && !r.j.galleries.some(g => g.slug === 'aoife-test'), p2.t);

// H16 nothing else changes; H17 the audit
const after = { a: await artistRows(db, 'aaoi'), b: await artistRows(db, 'abri'), works: (await db.prepare('SELECT * FROM artworks ORDER BY id').all()).results };
const strip = o => { const c = structuredClone(o); delete c.versions; delete c.publish_queue; return c; };
check('H16 curating never changes an artist, artwork, image, price, availability, gallery position or permission (only the test\'s own publications differ)',
  JSON.stringify(strip(before.a)) === JSON.stringify(strip(after.a)) && JSON.stringify(before.b) === JSON.stringify(after.b) && JSON.stringify(before.works) === JSON.stringify(after.works.filter(w => w.id !== 'never')));
const au = (await db.prepare("SELECT actor, role, action, detail FROM audit WHERE action='featured_artists' ORDER BY id").all()).results;
check('H17 every change is in the audit log (who, before and after); an unchanged save is not',
  au.length === 5 && au.every(x => x.actor === FOUNDER && x.role === 'founder') && JSON.parse(au[0].detail).before.length === 0 &&
  JSON.parse(au[4].detail).before.join() === 'artwork:abri/wabri2,artist:aaoi/waaoi1,artwork:aaoi/waaoi2' && JSON.parse(au[4].detail).after.join() === 'artist:aaoi/waaoi3,artist:abri/wabri1', JSON.stringify(au));

// H18 the migration and the schema agree
const mig = readFileSync(HERE + 'migrations/0016_homepage_features.sql', 'utf8'), schema = readFileSync(HERE + 'schema.sql', 'utf8');
const ddl = s => s.slice(s.indexOf('CREATE TABLE IF NOT EXISTS homepage_features'), s.indexOf(');', s.indexOf('CREATE TABLE IF NOT EXISTS homepage_features')) + 2).replace(/\s+/g, ' ');
check('H18 migration 0016 creates only homepage_features, exactly as schema.sql declares it', ddl(mig).length > 50 && ddl(mig) === ddl(schema) && (mig.match(/CREATE TABLE/g) || []).length === 1 && !/ALTER|DROP TABLE (?!homepage)|UPDATE |DELETE /.test(mig.split('@@DDL-BEGIN')[1].split('@@DDL-END')[0]));

// H19 a Studio without the migration: the Featured Artists view says so and saving is refused, everything else unaffected
const { mf: mf2, url: url2, db: db2 } = await start({ port: 8799, schemaSql: schema.replace(/CREATE TABLE IF NOT EXISTS homepage_features[\s\S]*?\);\n/, '') });
const c2 = async (m, b) => { const x = await mf2.dispatchFetch(url2 + '/api/admin/featured', { method: m, headers: { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(FOUNDER) }, body: b && JSON.stringify(b) }); return { s: x.status, j: await x.json().catch(() => ({})) }; };
const g2 = await c2('GET'), s2 = await c2('PUT', { items: [] });
const pp2 = await mf2.dispatchFetch(url2 + '/api/pipeline/featured-artists', { headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } }).then(x => x.json());
check('H19 before migration 0016 the view reports "not set up", a save is refused (409) and the pipeline reports not installed', g2.s === 200 && g2.j.installed === false && s2.s === 409 && pp2.installed === false && !!db2);
await mf2.dispose();

// H20 in a browser: the founder selects artists, chooses each one's artwork, reorders, replaces, changes, previews, removes and saves
{
  await db.prepare('DELETE FROM homepage_features').run();
  await seedPublished(db, { id: 'acar', slug: 'cara-test', email: 'cara@example.test', name: 'Cara Test', works: 2, number: 3, bucket: IMAGES });
  await seedPublished(db, { id: 'adar', slug: 'dara-test', email: 'dara@example.test', name: 'Dara Test', works: 1, number: 4, bucket: IMAGES });
  const { chromium } = await import('playwright');
  const br = await chromium.launch();
  const ctx = await br.newContext({ viewport: { width: 1280, height: 900 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { exp: 3600 }) } });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  // (the Studio's CSP forbids eval, so poll from here rather than with waitForFunction)
  const saveNow = async () => { await pg.click('#hp-save'); for (let n = 0; n < 100 && !/^Saved/.test(await pg.textContent('#hp-state')); n++) await pg.waitForTimeout(100); };
  await pg.goto(url + '/admin/featured'); await pg.waitForSelector('[data-artist="abri"]');
  const tab = await pg.$eval('.st-tabs a[aria-current]', a => a.textContent);
  await pg.click('[data-artist="abri"]');
  const offered = await pg.$$eval('[data-rep]', bs => bs.map(b => b.dataset.rep));
  const added = await pg.$$eval('.st-fa-card', c => c.length);
  await pg.click('[data-rep="wabri2"]');
  await pg.click('[data-artist="acar"]'); await pg.click('[data-rep="wacar1"]');
  const dupDisabled = await pg.$eval('[data-artist="abri"]', b => b.disabled);
  await pg.click('[data-up="1"]');                                              // Cara first
  await pg.click('[data-replace="1"]'); await pg.click('[data-artist="adar"]'); await pg.click('[data-rep="wadar1"]');   // Brian replaced by Dara
  await pg.click('[data-change="0"]'); await pg.click('[data-rep="wacar2"]');   // Cara shown with her second work
  const preview = await pg.evaluate(() => ({ head: document.querySelector('.st-fa-head').textContent, cards: [...document.querySelectorAll('.st-fa-card')].map(c => c.textContent) }));
  await saveNow();
  const saved = (await call('GET', '/api/admin/featured', FOUNDER)).j.items.map(i => `${i.artist_id}/${i.artwork_id}`);
  await pg.click('[data-rm="0"]'); await saveNow();
  const removed = (await call('GET', '/api/admin/featured', FOUNDER)).j.items.map(i => `${i.artist_id}/${i.artwork_id}`);
  const grid = await pg.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth);
  await br.close();
  check('H20 in the Review Desk ("Featured Artists" tab): "Feature artist" offers only that artist\'s published works and adds nothing until one is chosen; a featured artist cannot be added twice; reorder, replace, change artwork, preview (eyebrow, heading, introduction, credit, View Gallery), save and remove all work; no sideways scrolling',
    tab === 'Featured Artists' && offered.join() === 'wabri1,wabri2' && added === 0 && dupDisabled &&
    /Selected by PlotArt.*Featured Artists.*A changing selection of artists and their work\./.test(preview.head) &&
    preview.cards.length === 2 && /Cara Test is a synthetic test artist/.test(preview.cards[0]) && /Work 2.*Cara Test/.test(preview.cards[0]) && /View Gallery/.test(preview.cards[1]) &&
    saved.join() === 'acar/wacar2,adar/wadar1' && removed.join() === 'adar/wadar1' && grid && !errs.length,
    JSON.stringify({ tab, offered, added, dupDisabled, preview, saved, removed, grid, errs }));
}

// optional: screenshots of the Review Desk Featured Artists view
const shots = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
if (shots) {
  const { chromium } = await import('playwright');
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1360, height: 900 }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER, { exp: 3600 }) } });
  const pg = await ctx.newPage(); await pg.goto(url + '/admin/featured'); await pg.waitForTimeout(800);
  await pg.screenshot({ path: shots + '/review-desk-featured-synthetic.png', fullPage: true }); await b.close();
}

console.log(`\nPLOTART FEATURED ARTISTS (Studio) · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose();
process.exit(results.every(Boolean) ? 0 : 1);
