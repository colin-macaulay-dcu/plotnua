// PROVE · PlotArt Studio · Three galleries: the gallery data model (Phase B, migration 0023). Synthetic artists only; the
// Worker runs locally (Miniflare/workerd) with a local D1. Nothing here touches Cloudflare.
//   node test/prove-galleries.mjs
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
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
console.log('PROVE · PlotArt Studio · Three galleries (Phase B)');

/* ---- Z · the Worker before migration 0023 is applied (production today): nothing changes, gallery routes say so ---- */
{
  const mainSchema = execFileSync('git', ['-C', HERE, 'show', 'origin/main:worker/plotart-studio/schema.sql'], { encoding: 'utf8' });
  const { mf, url, db } = await start({ port: 8811, schemaSql: mainSchema });
  const call = mkcall(mf, url);
  const v = await call('GET', '/api/admin/galleries', FOUNDER);
  check('Z1 without migration 0023 the founder view says the gallery records are not installed (defaults only)', v.s === 200 && v.j.installed === false && v.j.galleries.length === 3);
  const plain = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Zara Synthetic', email: 'zara@example.test', founding: false });
  check('Z2 an invitation without a gallery choice works exactly as today', plain.s === 200 && !!plain.j.id);
  const n0 = (await db.prepare('SELECT COUNT(*) n FROM artists').first()).n;
  const withG = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Yan Synthetic', email: 'yan@example.test', founding: false, galleries: ['places_and_spaces'] });
  check('Z3 an invitation WITH a gallery choice is refused before anything is written (no half-created artist)', withG.s === 503 && (await db.prepare('SELECT COUNT(*) n FROM artists').first()).n === n0);
  const art = await call('GET', '/api/galleries', 'zara@example.test');
  const pipe = await call('GET', '/api/pipeline/galleries', null, undefined, PIPE);
  check('Z4 the artist and pipeline gallery routes answer "not installed" without error', art.s === 503 && pipe.s === 200 && pipe.j.installed === false);
  await mf.dispose();
}

/* ---- the Studio with migration 0023 ---- */
const { mf, url, db } = await start({ port: 8812 });
const call = mkcall(mf, url);
const t0 = '2026-11-05T17:05:00.000Z';
await seedPublished(db, { id: 'aaoife', slug: 'aoife-test', email: 'aoife@example.test', name: 'Aoife Test', works: 3, number: 1 });
await seedPublished(db, { id: 'abrian', slug: 'brian-test', email: 'brian@example.test', name: 'Brian Test', works: 2, number: 2 });
await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, ?, 0, NULL, ?)').bind('aaoife', t0).run();
await db.prepare('INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (1, ?, ?, ?, ?)').bind('artist', 'aaoife', 'waaoife1', t0).run();
const EXISTING = ['artists', 'artworks', 'images', 'versions', 'publish_queue', 'submissions', 'gallery_positions', 'homepage_features', 'artist_terms', 'agreement_acceptances', 'enquiry_log', 'artwork_hire'];
const snap = async () => { const o = {}; for (const t of EXISTING) { try { o[t] = (await db.prepare(`SELECT * FROM ${t} ${t === 'artists' ? "WHERE id IN ('aaoife','abrian') " : ''}ORDER BY rowid`).all()).results; } catch { o[t] = 'absent'; } } return JSON.stringify(o); };   // the artists this proof invites are new rows, not changes
const count = async t => (await db.prepare(`SELECT COUNT(*) n FROM ${t}`).first()).n;
const before = await snap();
const featuredBefore = (await call('GET', '/api/pipeline/featured-artists', null, undefined, PIPE)).j;
const orderBefore = (await call('GET', '/api/pipeline/gallery-order', null, undefined, PIPE)).j;

// D · defaults: Contemporary Art as today; the new galleries empty; nothing written
let v = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
const gal = id => v.galleries.find(g => g.gallery_id === id);
check('D1 defaults: Contemporary Art open; Places & Spaces and Portraiture in preparation with targets 6 artists / 30 works',
  v.installed === true && gal('contemporary').status === 'open' && gal('places_and_spaces').status === 'in_preparation' && gal('portraiture').status === 'in_preparation'
  && gal('places_and_spaces').target_artists === 6 && gal('places_and_spaces').target_works === 30 && gal('portraiture').target_works === 30);
check('D2 every existing published artist is a live Contemporary Art member with all their shown works; nothing is assigned anywhere else',
  gal('contemporary').members.map(m => m.slug).sort().join() === 'aoife-test,brian-test' && gal('contemporary').live_works === 5
  && gal('places_and_spaces').members.length === 0 && gal('portraiture').members.length === 0 && gal('places_and_spaces').live_works === 0);
check('D3 no membership, placement or setting row was written for existing artists', await count('gallery_memberships') === 0 && await count('artwork_placements') === 0 && await count('gallery_settings') === 0);

// I · invitation with a gallery choice (direct invitation and application-based)
const invC = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Ciara Synthetic', email: 'ciara@example.test', founding: false, galleries: ['places_and_spaces'] });
const C = invC.j.id;
const invD = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Dara Synthetic', email: 'dara@example.test', founding: false, galleries: ['portraiture', 'contemporary'], application_ref: 'F25-261124-ABCDEF' });
const D = invD.j.id;
const invE = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Eoin Synthetic', email: 'eoin@example.test', founding: false });
const mC = (await db.prepare('SELECT * FROM gallery_memberships WHERE artist_id=?').bind(C).all()).results;
const mD = (await db.prepare('SELECT * FROM gallery_memberships WHERE artist_id=? ORDER BY gallery_id').bind(D).all()).results;
check('I1 a direct invitation to Places & Spaces records the founder’s approval, waits for the artist, and does NOT put the artist in Contemporary Art',
  invC.s === 200 && mC.length === 1 && mC[0].gallery_id === 'places_and_spaces' && mC[0].state === 'founder_approved' && mC[0].source === 'founder_invitation' && mC[0].artist_accepted_at === null);
check('I2 an application-based invitation records the application reference for each chosen gallery',
  invD.s === 200 && mD.length === 2 && mD.every(r => r.source === 'application' && r.application_ref === 'F25-261124-ABCDEF' && r.state === 'founder_approved'));
check('I3 an invitation with no gallery choice writes nothing (Contemporary Art by default, as today)', invE.s === 200 && (await db.prepare('SELECT COUNT(*) n FROM gallery_memberships WHERE artist_id=?').bind(invE.j.id).first()).n === 0);
const bad = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Fay Synthetic', email: 'fay@example.test', founding: false, galleries: ['sculpture'] });
check('I4 an unknown gallery at invitation is refused before the artist is created', bad.s === 400 && !(await db.prepare("SELECT id FROM artists WHERE email='fay@example.test'").first()));

// M · founder approval and artist acceptance
let r = await call('POST', '/api/galleries/places_and_spaces/accept', 'ciara@example.test');
check('M1 the invited artist accepts: Places & Spaces membership is live only now', r.s === 200 && r.j.galleries.find(g => g.gallery_id === 'places_and_spaces').state === 'live');
r = await call('POST', '/api/admin/galleries/places_and_spaces/members', FOUNDER, { artist_id: 'aaoife', source: 'founder_curation' });
const aRows = (await db.prepare("SELECT * FROM gallery_memberships WHERE artist_id='aaoife' ORDER BY gallery_id").all()).results;
check('M2 the founder invites an existing artist to Places & Spaces: their Contemporary membership is first written down as it was (live), Places & Spaces waits for them',
  r.s === 200 && aRows.length === 2 && aRows[0].gallery_id === 'contemporary' && aRows[0].state === 'live' && aRows[0].source === 'existing_contemporary' && aRows[1].state === 'founder_approved');
v = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
check('M3 until the artist accepts, the founder’s approval alone does not make them a member', !gal('places_and_spaces').members.some(m => m.slug === 'aoife-test') && gal('contemporary').members.some(m => m.slug === 'aoife-test'));
r = await call('POST', '/api/galleries/places_and_spaces/accept', 'aoife@example.test');
check('M4 the artist accepts; they are now in Contemporary Art AND Places & Spaces', r.s === 200 && r.j.galleries.filter(g => g.state === 'live').map(g => g.gallery_id).join() === 'contemporary,places_and_spaces');
r = await call('POST', '/api/galleries/portraiture/request', 'brian@example.test');
const brianReq = (await db.prepare("SELECT * FROM gallery_memberships WHERE artist_id='abrian' AND gallery_id='portraiture'").first());
check('M5 an artist’s own request counts as their acceptance but waits for the founder', r.s === 200 && brianReq.state === 'artist_accepted' && brianReq.source === 'artist_request' && !brianReq.founder_approved_at);
r = await call('POST', '/api/admin/galleries/portraiture/members/abrian/approve', FOUNDER);
check('M6 the founder approves the request: live', r.s === 200 && r.j.galleries.find(g => g.gallery_id === 'portraiture').state === 'live');
r = await call('POST', '/api/galleries/portraiture/accept', 'ciara@example.test');
const r2 = await call('POST', '/api/admin/galleries/places_and_spaces/members/abrian/approve', FOUNDER);
check('M7 nobody can accept without an invitation, and the founder cannot approve a request that does not exist', r.s === 409 && r2.s === 409);
r = await call('POST', '/api/galleries/portraiture/decline', 'dara@example.test');
check('M8 an artist can decline an invitation', r.s === 200 && r.j.galleries.find(g => g.gallery_id === 'portraiture').state === 'declined');

// S · security
const artistAdmin = await call('GET', '/api/admin/galleries', 'aoife@example.test');
const artistPropose = await call('POST', '/api/admin/galleries/places_and_spaces/members', 'aoife@example.test', { artist_id: 'abrian' });
const anon = await call('GET', '/api/admin/galleries', null);
const pipeAdmin = await call('GET', '/api/admin/galleries', null, undefined, PIPE);
const xsite = await mf.dispatchFetch(url + '/api/galleries/places_and_spaces/request', { method: 'POST', headers: { 'Cf-Access-Jwt-Assertion': token('brian@example.test') } });
check('S1 artists, signed-out visitors and the pipeline token cannot reach the founder’s gallery routes; cross-site requests are refused',
  artistAdmin.s === 403 && artistPropose.s === 403 && anon.s === 401 && pipeAdmin.s === 401 && xsite.status === 403);
const founderAsArtist = await call('GET', '/api/galleries', FOUNDER);
check('S2 the founder uses the founder routes, not an artist’s', founderAsArtist.s === 403);

// P · artwork placement (founder approval + artist acceptance), and Contemporary Art take-out
r = await call('POST', '/api/admin/galleries/places_and_spaces/artworks/waaoife2/place', FOUNDER);
check('P1 the founder places an artist’s work in Places & Spaces: it waits for the artist', r.s === 200 && r.j.placements.find(p => p.artwork_id === 'waaoife2').state === 'founder_approved');
v = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
check('P2 a work is not in Places & Spaces until the artist accepts', gal('places_and_spaces').live_works === 0);
r = await call('POST', '/api/galleries/places_and_spaces/artworks/waaoife2/accept', 'aoife@example.test');
v = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
check('P3 the artist accepts: the work is in Places & Spaces AND still in Contemporary Art', r.s === 200 && gal('places_and_spaces').live_works === 1 && gal('contemporary').live_works === 5);
r = await call('POST', '/api/admin/galleries/places_and_spaces/artworks/wabrian1/place', FOUNDER);
check('P4 a work cannot be placed in a gallery its artist is not a member of', r.s === 409);
r = await call('POST', '/api/galleries/portraiture/artworks/wabrian1/propose', 'brian@example.test');
const r3 = await call('POST', '/api/admin/galleries/portraiture/artworks/wabrian1/place', FOUNDER);
check('P5 an artist proposes their own work; the founder’s approval makes it live', r.s === 200 && r3.s === 200 && r3.j.placements.find(p => p.artwork_id === 'wabrian1' && p.gallery_id === 'portraiture').state === 'live');
r = await call('POST', '/api/galleries/places_and_spaces/artworks/wabrian1/propose', 'aoife@example.test');
check('P6 an artist cannot propose another artist’s work', r.s === 404);
r = await call('POST', '/api/admin/galleries/contemporary/artworks/waaoife3/withdraw', FOUNDER);
v = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
const out1 = gal('contemporary').live_works;
r = await call('POST', '/api/admin/galleries/contemporary/artworks/waaoife3/restore', FOUNDER);
v = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
check('P7 the founder can take a work out of Contemporary Art and put it back (the only Contemporary placement action)', out1 === 4 && gal('contemporary').live_works === 5);
const r4 = await call('POST', '/api/admin/galleries/contemporary/artworks/waaoife3/place', FOUNDER);
check('P8 placing in Contemporary Art is refused (every member’s work is there by default)', r4.s === 409);

// O · unlimited, independent order
r = await call('PUT', '/api/admin/galleries/places_and_spaces/order', FOUNDER, { artists: [C, 'aaoife'] });
check('O1 Places & Spaces has its own order, starting at 1', r.s === 200 && r.j.order.map(o => o.position).join() === '1,2' && r.j.order[0].artist_id === C);
r = await call('PUT', '/api/admin/galleries/contemporary/order', FOUNDER, { artists: ['abrian'] });
check('O2 Contemporary Art beyond the 25 positions starts at 26', r.s === 200 && r.j.order[0].position === 26 && r.j.order[0].artist_id === 'abrian');
r = await call('PUT', '/api/admin/galleries/contemporary/order', FOUNDER, { artists: ['aaoife'] });
check('O3 an artist already holding one of positions 01–25 cannot be given a second Contemporary position', r.s === 409);
r = await call('PUT', '/api/admin/galleries/portraiture/order', FOUNDER, { artists: [C] });
check('O4 only live members of a gallery can be ordered in it', r.s === 409);
let deep = true; try { await db.prepare("INSERT INTO gallery_order (gallery_id, position, artist_id, updated_at, updated_by) VALUES ('places_and_spaces', 4000, 'abrian', ?, 'test')").bind('2026-11-24T00:00:00.000Z').run(); } catch { deep = false; }
let low = false; try { await db.prepare("INSERT INTO gallery_order (gallery_id, position, artist_id, updated_at, updated_by) VALUES ('contemporary', 5, ?, ?, 'test')").bind(invE.j.id, '2026-11-24T00:00:00.000Z').run(); } catch { low = true; }
await db.prepare("DELETE FROM gallery_order WHERE gallery_id='places_and_spaces' AND position=4000").run();
check('O5 there is no 25-position limit (position 4000 is accepted), and the database itself refuses a Contemporary position below 26', deep && low);

// F · independent Artists in Focus
r = await call('PUT', '/api/admin/galleries/places_and_spaces/features', FOUNDER, { items: [{ artist_id: 'aaoife', artwork_id: 'waaoife2' }] });
check('F1 Places & Spaces has its own Artists in Focus, from works placed in it', r.s === 200 && r.j.features.length === 1);
r = await call('PUT', '/api/admin/galleries/places_and_spaces/features', FOUNDER, { items: [{ artist_id: 'aaoife', artwork_id: 'waaoife1' }] });
const r5 = await call('PUT', '/api/admin/galleries/contemporary/features', FOUNDER, { items: [] });
check('F2 a work not placed in that gallery is refused; Contemporary Art keeps its existing Artists in Focus route', r.s === 409 && r5.s === 409);
const featuredAfter = (await call('GET', '/api/pipeline/featured-artists', null, undefined, PIPE)).j;
check('F3 Contemporary Art’s Artists in Focus (homepage_features) is unchanged', JSON.stringify(featuredAfter) === JSON.stringify(featuredBefore));

// C · optional, recorded, per-use image consent
r = await call('POST', '/api/admin/image-use/requests', FOUNDER, { artist_id: 'aaoife', scope: 'homepage_feature', gallery_id: 'places_and_spaces', artwork_ids: ['waaoife2'], purpose: 'Places & Spaces entrance on the PlotArt homepage', channels: 'plotnua.ie/plotart/', valid_until: '2027-12-31' });
const req1 = r.j.request && r.j.request.id;
check('C1 the founder sends a specific per-use request (no answer yet means no consent)', r.s === 200 && r.j.request.status === 'open' && r.j.request.request_text_sha256.length === 64);
const other = await call('POST', `/api/image-use/${req1}/answer`, 'brian@example.test', { answer: 'yes' });
r = await call('POST', `/api/image-use/${req1}/answer`, 'aoife@example.test', { answer: 'yes' });
const again = await call('POST', `/api/image-use/${req1}/answer`, 'aoife@example.test', { answer: 'no' });
check('C2 only that artist can answer, once; their yes is recorded with the method and the exact request text', other.s === 404 && r.s === 200 && again.s === 404
  && (await db.prepare('SELECT answer, method FROM image_use_consents WHERE request_id=?').bind(req1).first()).method === 'studio');
r = await call('POST', '/api/admin/image-use/record', FOUNDER, { artist_id: 'aaoife', scope: 'homepage_feature', gallery_id: 'places_and_spaces', artwork_ids: ['waaoife2'], purpose: 'Places & Spaces entrance on the PlotArt homepage', channels: 'plotnua.ie/plotart/', answer: 'no' });
const rows = (await db.prepare("SELECT answer FROM image_use_consents WHERE artist_id='aaoife' ORDER BY created_at, rowid").all()).results;
check('C3 a later "no" (here recorded by the founder from an email) is a new row; the earlier "yes" is kept, never changed', r.s === 200 && rows.map(x => x.answer).join() === 'yes,no');
const src = readFileSync(HERE + 'src/galleries.js', 'utf8') + readFileSync(HERE + 'src/index.js', 'utf8');
check('C4 the Studio never updates or deletes a consent answer (append-only in code; no trigger needed)', !/UPDATE\s+image_use_consents|DELETE\s+FROM\s+image_use_consents/i.test(src));
r = await call('POST', '/api/admin/image-use/requests', FOUNDER, { artist_id: 'aaoife', scope: 'homepage_feature', artwork_ids: ['wabrian1'], purpose: 'Wrong artist test', channels: 'homepage' });
check('C5 a request can only name the artist’s own artworks', r.s === 409);

// R · readiness targets and founder-controlled opening
r = await call('PUT', '/api/admin/galleries/places_and_spaces/targets', FOUNDER, { target_artists: 1, target_works: 1 });
check('R1 the founder edits the readiness targets; readiness is measured against them', r.s === 200 && r.j.gallery.target_artists === 1 && r.j.gallery.target_works === 1);
v = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
check('R2 readiness counts only published members: Places & Spaces has 1 published live artist (the newly invited one is not published yet) and 1 live work, and is ready', gal('places_and_spaces').live_artists === 1 && gal('places_and_spaces').live_works === 1 && gal('places_and_spaces').ready === true);
r = await call('POST', '/api/admin/galleries/places_and_spaces/status', FOUNDER, { status: 'open' });
const r6 = await call('POST', '/api/admin/galleries/places_and_spaces/status', FOUNDER, { status: 'open', confirm: 'OPEN PLACES & SPACES' });
check('R3 opening needs the founder’s typed confirmation', r.s === 409 && r6.s === 200 && r6.j.gallery.status === 'open' && !!r6.j.gallery.opened_at);
r = await call('PUT', '/api/admin/galleries/portraiture/targets', FOUNDER, { target_artists: 6, target_works: 30 });
r = await call('POST', '/api/admin/galleries/portraiture/status', FOUNDER, { status: 'open', confirm: 'OPEN PORTRAITURE' });
const r7 = await call('POST', '/api/admin/galleries/portraiture/status', FOUNDER, { status: 'open', confirm: 'OPEN PORTRAITURE', below_target: true });
const r8 = await call('POST', '/api/admin/galleries/portraiture/status', FOUNDER, { status: 'in_preparation' });
check('R4 below its target a gallery opens only when the founder confirms that too; it can be returned to In preparation', r.s === 409 && r7.s === 200 && r8.s === 200 && r8.j.gallery.status === 'in_preparation' && r8.j.gallery.opened_at === null);
r = await call('POST', '/api/admin/galleries/contemporary/status', FOUNDER, { status: 'paused' });
const r9 = await call('PUT', '/api/admin/galleries/contemporary/targets', FOUNDER, { target_artists: 1, target_works: 1 });
check('R5 Contemporary Art cannot be paused, closed or re-targeted here (it stays open, as today)', r.s === 409 && r9.s === 409);
check('R6 the Studio record of an opened gallery does not change the public site: the launch switches still say in_preparation',
  JSON.parse(readFileSync(HERE + '../../atlas-tools/release/plotart-launch-switches.json', 'utf8')).places_and_spaces_gallery_state === 'in_preparation');

// W · leaving a gallery
r = await call('POST', '/api/galleries/places_and_spaces/withdraw', 'aoife@example.test');
v = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
check('W1 an artist who leaves Places & Spaces drops out of it with their works; Contemporary Art is untouched',
  r.s === 200 && !gal('places_and_spaces').members.some(m => m.slug === 'aoife-test') && gal('places_and_spaces').live_works === 0 && gal('contemporary').members.some(m => m.slug === 'aoife-test'));

// X · the pipeline view and the database's own rules
const pipe = await call('GET', '/api/pipeline/galleries', null, undefined, PIPE);
check('X1 the pipeline sees each gallery’s status, artists, works, order and features by public address only (no email)',
  pipe.s === 200 && pipe.j.installed === true && pipe.j.galleries.length === 3 && !pipe.t.includes('@example.test') && pipe.j.galleries[0].artists.includes('aoife-test'));
const refused = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return false; } catch { return true; } };
const T = '2026-11-24T00:00:00.000Z';
check('X2 the database refuses a live membership without both approval and acceptance, an unknown gallery, a live Contemporary placement, Contemporary features, and a paused Contemporary Art',
  await refused("INSERT INTO gallery_memberships (artist_id, gallery_id, state, source, proposed_by, proposed_at, updated_at) VALUES ('abrian','places_and_spaces','live','founder_curation','x',?,?)", T, T)
  && await refused("INSERT INTO gallery_memberships (artist_id, gallery_id, state, source, proposed_by, proposed_at, updated_at) VALUES ('abrian','sculpture','proposed','founder_curation','x',?,?)", T, T)
  && await refused("INSERT INTO artwork_placements (artwork_id, artist_id, gallery_id, state, proposed_by, proposed_at, founder_approved_by, founder_approved_at, artist_accepted_at, updated_at) VALUES ('wabrian2','abrian','contemporary','live','x',?,'x',?,?,?)", T, T, T, T)
  && await refused("INSERT INTO gallery_features (gallery_id, position, artist_id, artwork_id, updated_at, updated_by) VALUES ('contemporary',1,'aaoife','waaoife1',?,'x')", T)
  && await refused("INSERT INTO gallery_settings (gallery_id, status, target_artists, target_works, updated_at, updated_by) VALUES ('contemporary','paused',0,0,?,'x')", T));
const audits = (await db.prepare("SELECT action FROM audit WHERE action LIKE 'gallery_%' OR action LIKE 'artwork_placement_%' OR action LIKE 'image_use_%'").all()).results.map(a => a.action);
check('X3 every change is in the audit log (memberships, placements, order, features, targets, status, consent)',
  ['gallery_membership_proposed', 'gallery_membership_accept', 'gallery_membership_request', 'gallery_membership_approved', 'artwork_placement_place', 'gallery_order', 'gallery_features', 'gallery_targets', 'gallery_status', 'image_use_requested', 'image_use_answered', 'image_use_recorded'].every(a => audits.includes(a)), audits.join());

// E · existing data and functions untouched by everything above
const after = await snap();
check('E1 every existing table (artists, artworks, images, versions, publications, the 25 positions, Featured Artists, terms, agreements, enquiry log, hire) is byte-for-byte unchanged',
  after === before);
const orderAfter = (await call('GET', '/api/pipeline/gallery-order', null, undefined, PIPE)).j;
check('E2 the existing gallery order the publisher reads is unchanged', JSON.stringify(orderAfter) === JSON.stringify(orderBefore));
const go = await call('GET', '/api/admin/gallery-order', FOUNDER);
check('E3 the founder’s existing Gallery order (25 positions) still works as before', go.s === 200 && go.j.positions.length === 25 && go.j.positions[0].artist_id === 'aaoife');

await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nPLOTART THREE GALLERIES (STUDIO) · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
