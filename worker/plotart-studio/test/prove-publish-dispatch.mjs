// PROVE · PlotArt publish on approval (development, 6 Nov 2026). Local only: Miniflare D1/R2, synthetic artists, and a
// stand-in for GitHub that records every workflow start. Shows that ONLY a founder action that makes gallery content ready
// starts .github/workflows/plotart-content-publish.yml (once, on main, with the founder-only token), that nothing an
// artist does starts it (unless the founder switches instant updates on), that refusals start nothing, that a failure to
// start loses nothing (the item stays ready for the scheduled run and the desk says so), and that other artists' records
// never change. The publishing workflow itself (rebuild on the latest main, gate, fast-forward, rollback, failures shown)
// is proven by prove-publish-release.mjs and prove-journey.mjs.
//   node test/prove-publish-dispatch.mjs
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
import { seedPublished, artistRows } from './seed.mjs';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { snapshot } from '../src/lib.js';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const sha = b => createHash('sha256').update(b).digest('hex');
const WF = '/repos/colin-macaulay-dcu/plotnua/actions/workflows/plotart-content-publish.yml/dispatches';

// ---- a stand-in for GitHub's workflow_dispatch API
let hits = [], ghStatus = 204;
const gh = createServer((req, res) => { let body = ''; req.on('data', c => body += c); req.on('end', () => { hits.push({ url: req.url, auth: req.headers.authorization, body }); res.writeHead(ghStatus); res.end(); }); });
await new Promise(r => gh.listen(0, '127.0.0.1', r));
const GH = `http://127.0.0.1:${gh.address().port}`;
const fresh = () => { const h = hits; hits = []; return h; };
const onlyPublish = h => h.length === 1 && h[0].url === WF && h[0].auth === 'Bearer test-dispatch-token' && JSON.parse(h[0].body).ref === 'main';

async function harness(port, extra = {}) {
  const { mf, url, db } = await start({ port, env: { GITHUB_DISPATCH_TOKEN: 'test-dispatch-token', GITHUB_API: GH, INSTANT_AUTOPUBLISH: 'true', ...extra } });
  const H = email => ({ ...(email ? { 'Cf-Access-Jwt-Assertion': token(email) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
  const call = async (method, path, email, body) => { const r = await mf.dispatchFetch(url + path, { method, headers: H(email), body: body === undefined ? undefined : JSON.stringify(body) }); return { s: r.status, j: await r.json().catch(() => null) }; };
  const pipe = async (method, path, body) => { const r = await mf.dispatchFetch(url + path, { method, headers: { Authorization: `Bearer ${PIPELINE_TOKEN}`, 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); return { s: r.status, j: await r.json().catch(() => null) }; };
  return { mf, url, db, call, pipe, q1: (s, ...b) => db.prepare(s).bind(...b).first(), qa: async (s, ...b) => (await db.prepare(s).bind(...b).all()).results };
}
const T0 = '2026-11-05T17:05:00.000Z';
async function addWork(h, email, artistId, title, imgId) {
  const id = (await h.call('POST', '/api/artworks', email)).j.id;
  await h.call('PUT', `/api/artworks/${id}`, email, { title, medium: 'Oil', h_cm: 30, w_cm: 40, ai_involvement: 'none' });
  await h.db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
    VALUES (?, ?, ?, 'main', ?, ?, 1000, 2400, 1800, 'jpeg', ?, 'self', '{"blocks":[],"warns":[]}', 0, ?)`).bind(imgId, artistId, id, `orig/${imgId}.jpg`, sha(imgId), `${title}, a test painting`, T0).run();
  return id;
}
async function submitApprove(h, email, artistId, decision = 'approve') {
  const s = await h.call('POST', '/api/submit', email, {});
  const sid = (await h.call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(x => x.artist_id === artistId)?.id;
  const d = sid ? await h.call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, decision === 'approve' ? { decision } : { decision, message: 'Please add a description to the new work.' }) : null;
  const q = (await h.call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === artistId && x.status === 'awaiting_founder');
  return { s, d, q };
}

console.log('PROVE · PlotArt publish on approval');
const h = await harness(8851);
const LEAH = 'leah-like@example.test', NEW = 'niamh-new@example.test', PAT = 'pat-published@example.test';
await seedPublished(h.db, { id: 'aleah', slug: 'leah-like', email: LEAH, name: 'Leah Like', works: 11 });
await seedPublished(h.db, { id: 'apat', slug: 'pat-published', email: PAT, name: 'Pat Published', works: 3 });
const leahBefore = await artistRows(h.db, 'aleah');
let r = await h.call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Niamh New', email: NEW, founding: true }); const NID = r.j.id;
fresh();

console.log('— first gallery publication');
await h.call('PUT', '/api/me/profile', NEW, { medium: 'painting', bio: 'Niamh New is a synthetic test artist used to prove publishing on approval.' });
await addWork(h, NEW, NID, 'First Light', 'inew1');
let x = await h.call('POST', '/api/submit', NEW, {});
check('P1 an artist cannot submit a first gallery before accepting the agreements; nothing starts', x.s === 422 && fresh().length === 0, JSON.stringify(x.j));
await acceptAgreement(h.mf, h.url, NEW);
let sa = await submitApprove(h, NEW, NID);
check('P2 the artist submits and the founder approves: nothing starts yet (approval alone publishes nothing)', sa.s.s === 200 && sa.d.s === 200 && sa.q && fresh().length === 0);
x = await h.call('POST', `/api/admin/queue/${sa.q.id}/publish`, NEW, {});
check('P3 an artist cannot use the founder’s Publish (refused) and nothing starts', x.s === 403 && fresh().length === 0, x.s);
x = await h.call('POST', `/api/admin/queue/${sa.q.id}/publish`, FOUNDER, {});
let hh = fresh();
check('P4 the founder presses Publish: the publishing workflow starts ONCE, on main, with the founder-only token; the reply says "requested"',
  x.s === 200 && x.j.publish === 'requested' && onlyPublish(hh), JSON.stringify([x.j, hh]));
check('P5 the item is ready for the pipeline, which still lists it (the scheduled run remains the fallback)',
  (await h.q1('SELECT status FROM publish_queue WHERE id=?', sa.q.id)).status === 'ready' && (await h.pipe('GET', '/api/pipeline/queue')).j.items.some(i => i.id === sa.q.id));
const aud = await h.q1("SELECT detail FROM audit WHERE action='publish' AND artist_id=? ORDER BY id DESC LIMIT 1", NID);
check('P6 the audit log records the publish and that publishing was started; the token appears nowhere', /"publish":"requested"/.test(aud.detail)
  && !JSON.stringify(x.j).includes('test-dispatch-token') && !(await h.q1("SELECT 1 FROM audit WHERE detail LIKE '%test-dispatch-token%'")));
x = await h.call('POST', `/api/admin/queue/${sa.q.id}/publish`, FOUNDER, {});
check('P7 pressing Publish again on the same item is refused and starts nothing (no duplicate runs)', x.s === 409 && fresh().length === 0);
await h.pipe('POST', `/api/pipeline/export/${sa.q.id}`);
await h.pipe('POST', `/api/pipeline/result/${sa.q.id}`, { status: 'published', detail: 'commit test' });
fresh();

console.log('— later changes to a published gallery');
await addWork(h, NEW, NID, 'Second Light', 'inew2');
sa = await submitApprove(h, NEW, NID);
x = await h.call('POST', `/api/admin/queue/${sa.q.id}/publish`, FOUNDER, {}); hh = fresh();
check('P8 artwork addition (full review): submit → approve → Publish starts publishing once', sa.s.j?.tier === 'full' && x.j.publish === 'requested' && onlyPublish(hh), JSON.stringify([sa.s.j, x.j, hh.length]));
await h.pipe('POST', `/api/pipeline/export/${sa.q.id}`); await h.pipe('POST', `/api/pipeline/result/${sa.q.id}`, { status: 'published', detail: 'commit test' }); fresh();
const w1 = (await h.qa('SELECT id FROM artworks WHERE artist_id=? ORDER BY created_at', NID))[0].id;
await h.call('PUT', `/api/artworks/${w1}`, NEW, { title: 'First Light', medium: 'Oil', h_cm: 30, w_cm: 40, ai_involvement: 'none', price_eur: 950 });
sa = await submitApprove(h, NEW, NID);
x = await h.call('POST', `/api/admin/queue/${sa.q.id}/publish`, FOUNDER, {}); hh = fresh();
check('P9 artwork edit (price, light review): submit → approve → Publish starts publishing once', sa.q && x.j.publish === 'requested' && onlyPublish(hh), JSON.stringify([sa.s.j, x.j, hh.length]));
await h.pipe('POST', `/api/pipeline/export/${sa.q.id}`); await h.pipe('POST', `/api/pipeline/result/${sa.q.id}`, { status: 'published', detail: 'commit test' }); fresh();

console.log('— an artist’s own instant updates (pre-authorised; follow the schedule by default)');
x = await h.call('POST', `/api/artworks/${w1}/availability`, NEW, { availability: 'sold' });
let iq = await h.q1("SELECT status FROM publish_queue WHERE artist_id=? AND kind='instant' ORDER BY created_at DESC LIMIT 1", NID);
check('P10 sold: a new version is queued READY for publishing (as today) and starts nothing (artists never start publishing)', x.s === 200 && x.j.instant_version && iq.status === 'ready' && fresh().length === 0, JSON.stringify([x, iq]));
x = await h.call('POST', `/api/artworks/${w1}/archive`, NEW, { archived: true });
iq = await h.q1("SELECT status FROM publish_queue WHERE artist_id=? AND kind='instant' ORDER BY created_at DESC LIMIT 1", NID);
check('P11 withdrawal: queued READY (as today), starts nothing', x.s === 200 && iq.status === 'ready' && fresh().length === 0);
check('P12 the pipeline lists the instant items, so the next run (scheduled or started by the founder) publishes them', (await h.pipe('GET', '/api/pipeline/queue')).j.items.filter(i => i.artist_id === NID && i.kind === 'instant').length >= 1);

console.log('— refusals start nothing');
await h.call('PUT', '/api/me/profile', NEW, { medium: 'painting', bio: 'Niamh New is a synthetic test artist used to prove publishing on approval, with a changed biography.' });
sa = await submitApprove(h, NEW, NID, 'changes');
check('P13 changes requested: nothing queued, nothing starts', sa.d.s === 200 && !sa.q && fresh().length === 0, JSON.stringify(sa.d.j));
sa = await submitApprove(h, NEW, NID, 'decline');
check('P14 declined: nothing queued, nothing starts', sa.d.s === 200 && !sa.q && fresh().length === 0, JSON.stringify(sa.d.j));
await h.call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Una Unready', email: 'una@example.test', founding: true });
const UID = (await h.q1("SELECT id FROM artists WHERE email='una@example.test'")).id;
await h.call('PUT', '/api/me/profile', 'una@example.test', { medium: 'painting', bio: 'Una Unready is a synthetic test artist who has not accepted the agreement.' });
await addWork(h, 'una@example.test', UID, 'Unready', 'iuna1');
await h.db.prepare("INSERT INTO submissions (id, artist_id, created_at, tier, status, snapshot, changes, base_version) SELECT 'suna', id, ?, 'full', 'pending', '{}', '[]', 0 FROM artists WHERE id=?").bind(T0, UID).run();
{ const a = await h.q1('SELECT * FROM artists WHERE id=?', UID), w = await h.qa('SELECT * FROM artworks WHERE artist_id=?', UID), im = await h.qa('SELECT * FROM images WHERE artist_id=?', UID);
  await h.db.prepare("UPDATE submissions SET snapshot=? WHERE id='suna'").bind(JSON.stringify(snapshot(a, w, im))).run();
  await h.db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?, 1, ?, 'test', ?)").bind(UID, JSON.stringify(snapshot(a, w, im)), T0).run(); }
await h.db.prepare("UPDATE submissions SET status='approved', decided_at=? WHERE id='suna'").bind(T0).run();   // as if approved before the agreement rule (test only)
await h.db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('quna', ?, 1, 'reviewed', 'awaiting_founder', ?, ?)").bind(UID, T0, T0).run();
x = await h.call('POST', '/api/admin/queue/quna/publish', FOUNDER, {});
check('P15 Publish refused for a first gallery without the agreements: nothing starts', x.s === 409 && fresh().length === 0, JSON.stringify(x.j));

console.log('— other founder actions that change the public gallery');
let ord = (await h.call('GET', '/api/admin/gallery-order', FOUNDER)).j.positions;
x = await h.call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: ord.filter(p => p.state !== 'open').map(p => ({ position: p.position, state: p.state, artist_id: p.artist_id, note: p.note })) });
check('P16 saving the gallery order unchanged starts nothing', x.s === 200 && x.j.publish === 'none' && fresh().length === 0, JSON.stringify(x.j && x.j.publish));
const NEWPOS = ord.find(p => p.artist_id === NID)?.position;
x = await h.call('PUT', '/api/admin/gallery-order', FOUNDER, { positions: ord.filter(p => p.state !== 'open').map(p => ({ position: p.artist_id === NID ? 20 : p.position, state: p.state, artist_id: p.artist_id, note: p.note })) });
hh = fresh();
check('P17 moving an artist in the gallery order starts publishing once (the grid is rebuilt by the pipeline)', NEWPOS && x.s === 200 && x.j.publish === 'requested' && onlyPublish(hh), JSON.stringify([NEWPOS, x.s, x.j && x.j.publish, hh.length]));
x = await h.call('POST', '/api/admin/artists/apat/unpublish', FOUNDER, {}); hh = fresh();
check('P18 Unpublish (founder) starts publishing once', x.s === 200 && x.j.publish === 'requested' && onlyPublish(hh), JSON.stringify([x.j, hh.length]));
x = await h.call('POST', '/api/admin/artists/apat/end', FOUNDER, { confirm_name: 'Pat Published', source: 'founder', reason: 'Synthetic test of ending participation.' }); hh = fresh();
check('P19 ending an artist’s participation (removal queued) starts publishing once', x.s === 200 && x.j.removal_queue && x.j.publish === 'requested' && onlyPublish(hh), JSON.stringify([x.s, x.j, hh.length]));

console.log('— when publishing cannot be started');
ghStatus = 500;
await addWork(h, NEW, NID, 'Third Light', 'inew3');
sa = await submitApprove(h, NEW, NID);
x = await h.call('POST', `/api/admin/queue/${sa.q.id}/publish`, FOUNDER, {}); hh = fresh();
check('P20 GitHub refuses: the Publish is still saved (item ready), the reply says "failed" so the desk tells the founder, the schedule publishes it',
  x.s === 200 && x.j.publish === 'failed' && hh.length === 1 && (await h.q1('SELECT status FROM publish_queue WHERE id=?', sa.q.id)).status === 'ready', JSON.stringify(x.j));
ghStatus = 204;
await h.pipe('POST', `/api/pipeline/export/${sa.q.id}`);   // as the pipeline does: export, then report the outcome
await h.pipe('POST', `/api/pipeline/result/${sa.q.id}`, { status: 'failed', detail: 'gate refused (test)' });
const desk = (await h.call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(q => q.id === sa.q.id);
check('P21 a failed publication attempt stays visible in the Review desk (status failed, with its reason)', desk && desk.status === 'failed' && /gate refused/.test(desk.detail || ''), JSON.stringify(desk));

console.log('— nothing else changes');
check('P22 the already-published Leah-shaped artist: every record, table by table, is exactly as before', JSON.stringify(await artistRows(h.db, 'aleah')) === JSON.stringify(leahBefore));
await h.mf.dispose();

console.log('— with instant updates switched on by the founder (INSTANT_PUBLISH_DISPATCH = "true")');
const h2 = await harness(8852, { INSTANT_PUBLISH_DISPATCH: 'true' });
await seedPublished(h2.db, { id: 'aqi', slug: 'quinn-instant', email: 'quinn@example.test', name: 'Quinn Instant', works: 2 });
fresh();
x = await h2.call('POST', '/api/artworks/waqi1/availability', 'quinn@example.test', { availability: 'sold' }); hh = fresh();
check('P23 only then does a sold update start publishing (once); off by default', x.s === 200 && onlyPublish(hh), JSON.stringify([x, hh.length]));
await h2.mf.dispose();
const h3 = await harness(8853, { GITHUB_DISPATCH_TOKEN: '' });
await seedPublished(h3.db, { id: 'anot', slug: 'no-token', email: 'nt@example.test', name: 'No Token', works: 2 });
await h3.db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qnt', 'anot', 2, 'reviewed', 'awaiting_founder', ?, ?)").bind(T0, T0).run();
await h3.db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) SELECT artist_id, 2, snapshot, 'test', ? FROM versions WHERE artist_id='anot' AND version=1").bind(T0).run();
fresh();
x = await h3.call('POST', '/api/admin/queue/qnt/publish', FOUNDER, { confirm_without_agreement: true });
check('P24 with no token configured, Publish works exactly as before: "scheduled", nothing sent anywhere', x.s === 200 && x.j.publish === 'scheduled' && fresh().length === 0, JSON.stringify(x.j));
await h3.mf.dispose();
gh.close();

const bad = results.filter(z => !z).length;
console.log(bad ? `PUBLISH ON APPROVAL · REFUSED — ${bad} of ${results.length} failed` : `PUBLISH ON APPROVAL · ${results.length} checks, ${results.length} passed, 0 failed`);
process.exit(bad ? 2 : 0);
