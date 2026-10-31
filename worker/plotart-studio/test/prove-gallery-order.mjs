// PROVE · PlotArt Studio · Gallery order and Founding 25 numbers (founder decision 31 Oct 2026). Synthetic artists only;
// the Worker runs locally (Miniflare/workerd) with a local D1. Nothing here touches Cloudflare.
//   node test/prove-gallery-order.mjs
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
const { mf, url, db } = await start({ port: 8797 });
const call = async (method, path, email, body, headers = {}) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json', ...headers };
  if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text();
  let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const NOTE = 'Leah Hewson (private reservation)';

console.log('PROVE · PlotArt Studio · Gallery order');
const mk = async (name, email, founding = true) => (await call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, founding })).j.id;
const A = await mk('Aoife Synthetic', 'aoife@example.test'), B = await mk('Brian Synthetic', 'brian@example.test'), C = await mk('Ciara Synthetic', 'ciara@example.test', false);

let r = await call('GET', '/api/admin/gallery-order', FOUNDER);
check('G1 the founder sees all 25 positions (open on a new Studio) and the artists who can be placed',
  r.s === 200 && r.j.positions.length === 25 && r.j.positions.every((p, i) => p.position === i + 1 && p.state === 'open') && r.j.artists.length === 3);
r = await call('GET', '/admin/gallery', FOUNDER);
check('G2 the founder opens the Gallery order tab', r.s === 200 && r.t.includes('Gallery order'));

r = await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: NOTE }, { position: 5, state: 'artist', artist_id: A }] });
check('G3 the founder reserves 01 with a private note and places an artist at 05', r.s === 200 && r.j.positions[0].state === 'reserved' && r.j.positions[0].note === NOTE &&
  r.j.positions[4].artist_id === A && r.j.positions[4].live === false);

// security
const artistGet = await call('GET', '/api/admin/gallery-order', 'aoife@example.test');
const artistPut = await call('PUT', '/api/admin/gallery-order', 'aoife@example.test', { positions: [{ position: 2, state: 'artist', artist_id: A }] });
const artistPage = await call('GET', '/admin/gallery', 'aoife@example.test');
const artistFn = await call('PUT', `/api/admin/artists/${A}/founding-number`, 'aoife@example.test', { founding_number: 1 });
check('G4 an artist cannot see or change gallery positions or Founding numbers (403 on every route)',
  artistGet.s === 403 && artistPut.s === 403 && artistPage.s === 403 && artistFn.s === 403 && !artistGet.t.includes('Leah'));
const anon = await call('GET', '/api/admin/gallery-order', null);
const stranger = await call('GET', '/api/admin/gallery-order', 'stranger@example.test');
const pipeAdmin = await call('GET', '/api/admin/gallery-order', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
check('G5 no sign-in, an unknown email or the pipeline token cannot reach the founder routes', anon.s === 401 && stranger.s === 403 && pipeAdmin.s === 401);
const xsite = await mf.dispatchFetch(url + '/api/admin/gallery-order', { method: 'PUT', headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER), 'Content-Type': 'application/json' }, body: '{"positions":[]}' });
check('G6 a save without the Studio header (a cross-site request) is refused', xsite.status === 403);

// the pipeline view
const pipe = await call('GET', '/api/pipeline/gallery-order', null, undefined, { Authorization: 'Bearer ' + PIPELINE_TOKEN });
const pipeNo = await call('GET', '/api/pipeline/gallery-order', null);
check('G7 the pipeline sees 01 reserved and 05 empty (the artist is not published): no note, no unpublished name or address',
  pipe.s === 200 && pipeNo.s === 401 && !pipe.t.includes('Leah') && !pipe.t.includes('aoife') && !/note/.test(pipe.t) &&
  pipe.j.positions.find(e => e.position === 1).reserved === true && pipe.j.positions.find(e => e.position === 5).slug === null, pipe.t);

// validation
const bad = async b => (await call('PUT', '/api/admin/gallery-order', FOUNDER, b)).s;
const v = [await bad({ positions: [{ position: 26, state: 'reserved' }] }), await bad({ positions: [{ position: 2, state: 'artist', artist_id: A }, { position: 3, state: 'artist', artist_id: A }] }),
  await bad({ positions: [{ position: 2, state: 'reserved' }, { position: 2, state: 'reserved' }] }), await bad({ positions: [{ position: 2, state: 'reserved', note: 'x'.repeat(141) }] }),
  await bad({ positions: [{ position: 2, state: 'artist', artist_id: 'anotreal1' }] }), await bad({ positions: [{ position: 2, state: 'wild' }] })];
const still = (await call('GET', '/api/admin/gallery-order', FOUNDER)).j.positions;
check('G8 invalid orders are refused and change nothing (position 26, an artist twice, a position twice, a long note, an unknown artist, an unknown state)',
  v.every(s => s >= 400 && s < 500) && still[0].state === 'reserved' && still[4].artist_id === A, v.join(','));
check('G9 the database itself refuses an artist and a reservation in one position',
  await db.prepare("INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (9, ?, 1, NULL, 'x')").bind(B).run().then(() => false, () => true));

// moving, swapping, releasing
r = await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: NOTE }, { position: 2, state: 'artist', artist_id: A }, { position: 3, state: 'artist', artist_id: B }] });
const r2 = await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: NOTE }, { position: 2, state: 'artist', artist_id: B }, { position: 3, state: 'artist', artist_id: A }] });
check('G10 the founder moves and swaps artists between positions', r.s === 200 && r2.s === 200 && r2.j.positions[1].artist_id === B && r2.j.positions[2].artist_id === A);
r = await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 2, state: 'artist', artist_id: B }, { position: 3, state: 'artist', artist_id: A }] });
check('G11 the founder releases a reservation (01 open again)', r.s === 200 && r.j.positions[0].state === 'open');
await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: NOTE }, { position: 2, state: 'artist', artist_id: B }, { position: 3, state: 'artist', artist_id: A }] });

// Founding 25 numbers are separate from the order
const fn1 = await call('PUT', `/api/admin/artists/${A}/founding-number`, FOUNDER, { founding_number: 3 });
const fnDup = await call('PUT', `/api/admin/artists/${B}/founding-number`, FOUNDER, { founding_number: 3 });
const fnNon = await call('PUT', `/api/admin/artists/${C}/founding-number`, FOUNDER, { founding_number: 9 });
const fnRange = await call('PUT', `/api/admin/artists/${B}/founding-number`, FOUNDER, { founding_number: 26 });
check('G12 the founder sets a permanent Founding 25 number; a number held by another artist, a non-Founding artist and 26 are refused',
  fn1.s === 200 && fnDup.s === 409 && fnNon.s === 400 && fnRange.s === 400);
await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: NOTE }, { position: 2, state: 'artist', artist_id: A }, { position: 3, state: 'artist', artist_id: B }] });
const fnAfter = await db.prepare('SELECT founding_number FROM artists WHERE id = ?').bind(A).first();
check('G13 moving an artist in the gallery never changes their Founding 25 number', fnAfter.founding_number === 3);
r = await call('PUT', '/api/me/profile', 'aoife@example.test', { founding_number: 1, bio: 'A short biography of the artist.' });
const fnStill = await db.prepare('SELECT founding_number FROM artists WHERE id = ?').bind(A).first();
check('G14 an artist cannot set their own Founding 25 number', fnStill.founding_number === 3, r.s);

// founder brief 31 Oct 2026: Founding Artist No. 2 at display position 02 moves to 05; the number stays 2
await call('PUT', `/api/admin/artists/${A}/founding-number`, FOUNDER, { founding_number: 2 });
await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: NOTE }, { position: 2, state: 'artist', artist_id: A }, { position: 3, state: 'artist', artist_id: B }] });
const at2 = (await call('GET', '/api/admin/gallery-order', FOUNDER)).j.positions[1];
r = await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: NOTE }, { position: 5, state: 'artist', artist_id: A }, { position: 3, state: 'artist', artist_id: B }] });
const fnMoved = await db.prepare('SELECT founding_number FROM artists WHERE id = ?').bind(A).first();
check('G17 Founding Artist No. 2 moves from display position 02 to 05 and is still No. 2; 01 stays RESERVED',
  at2.artist_id === A && at2.founding_number === 2 && r.j.positions[4].artist_id === A && r.j.positions[4].founding_number === 2 && r.j.positions[1].state === 'open' &&
  fnMoved.founding_number === 2 && r.j.positions[0].state === 'reserved');
// audit
const au = await db.prepare("SELECT action, detail FROM audit WHERE action IN ('gallery_order','founding_number') ORDER BY id").all();
check('G15 every save is in the audit log (before and after), without the private note text',
  au.results.filter(x => x.action === 'gallery_order').length >= 6 && au.results.some(x => x.action === 'founding_number') && !au.results.some(x => (x.detail || '').includes('Leah')));

// a suspended artist keeps their position unless the founder releases it
await call('POST', `/api/admin/artists/${B}/suspend`, FOUNDER, {});
r = await call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: [{ position: 1, state: 'reserved', note: NOTE }, { position: 2, state: 'artist', artist_id: A }] });
check('G16 a suspended artist is not offered for placement and keeps their position until the founder releases it',
  r.s === 200 && r.j.positions[2].artist_id === B && !r.j.artists.some(a => a.id === B));

console.log(`\nPLOTART GALLERY ORDER · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose();
process.exit(results.every(Boolean) ? 0 : 1);
