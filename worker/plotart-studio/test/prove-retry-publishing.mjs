// PROVE · PlotArt Studio "Retry publishing" (development, 12 Nov 2026). Local only: Miniflare D1/R2, synthetic artists and
// a stand-in for GitHub that records every workflow start. Shows that a founder can send a FAILED publication back through
// the same protected publishing workflow (same queue record, same approved version, so every image-provenance check runs
// again), that nothing else can, that duplicate or concurrent presses queue it once, that invalid retries are refused and
// start nothing, that approval, agreement, artwork, gallery position and history are preserved, and that other artists'
// records and normal publishing never change. The Review Desk shows the failure, the button and the messages.
//   node test/prove-retry-publishing.mjs
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
import { seedPublished, artistRows } from './seed.mjs';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';

const req = createRequire(import.meta.url);
let chromium; try { ({ chromium } = req('playwright')); } catch { try { ({ chromium } = createRequire('/usr/lib/node_modules/')('playwright')); } catch { ({ chromium } = createRequire('/opt/npm-tools/node_modules/')('playwright')); } }

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const sha = b => createHash('sha256').update(b).digest('hex');
const WF = '/repos/colin-macaulay-dcu/plotnua/actions/workflows/plotart-content-publish.yml/dispatches';

let hits = [], ghStatus = 204;
const gh = createServer((rq, res) => { let body = ''; rq.on('data', c => body += c); rq.on('end', () => { hits.push({ url: rq.url, auth: rq.headers.authorization, body }); res.writeHead(ghStatus); res.end(); }); });
await new Promise(r => gh.listen(0, '127.0.0.1', r));
const GH = `http://127.0.0.1:${gh.address().port}`;
const fresh = () => { const h = hits; hits = []; return h; };
const onlyPublish = h => h.length === 1 && h[0].url === WF && h[0].auth === 'Bearer test-dispatch-token' && JSON.parse(h[0].body).ref === 'main';

const { mf, url, db } = await start({ port: 8863, env: { GITHUB_DISPATCH_TOKEN: 'test-dispatch-token', GITHUB_API: GH } });
const H = email => ({ ...(email ? { 'Cf-Access-Jwt-Assertion': token(email) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
const call = async (method, path, email, body) => { const r = await mf.dispatchFetch(url + path, { method, headers: H(email), body: body === undefined ? undefined : JSON.stringify(body) }); return { s: r.status, j: await r.json().catch(() => null) }; };
const pipe = async (method, path, body) => { const r = await mf.dispatchFetch(url + path, { method, headers: { Authorization: `Bearer ${PIPELINE_TOKEN}`, 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); return { s: r.status, j: await r.json().catch(() => null) }; };
const q1 = (s, ...b) => db.prepare(s).bind(...b).first();
const qa = async (s, ...b) => (await db.prepare(s).bind(...b).all()).results;
const T0 = '2026-11-05T17:05:00.000Z';
const P9 = 'Image provenance refused: FAIL P9 no declared record describes an unreferenced asset [3: walk-alike-2-1200.webp, walk-alike-3-1200.webp, walk-alike-4-1200.webp]\n19 checks, 18 passed, 1 failed\n--\n…nd is pure vector';

async function artistWithFailedV1(n, name) {
  const email = `retry${n}@example.test`;
  const id = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, founding: true })).j.id;
  await call('PUT', '/api/me/profile', email, { medium: 'painting', bio: `${name} is a synthetic test artist used to prove Retry publishing.` });
  const wid = (await call('POST', '/api/artworks', email)).j.id;
  await call('PUT', `/api/artworks/${wid}`, email, { title: `Walk ${n}`, medium: 'Oil', h_cm: 30, w_cm: 40, ai_involvement: 'none' });
  for (const [k, role] of [['m', 'main'], ['v2', 'view'], ['v3', 'view']]) await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
    VALUES (?, ?, ?, ?, ?, ?, 1000, 2400, 1800, 'jpeg', ?, 'self', '{"blocks":[],"warns":[]}', ?, ?)`).bind(`i${n}${k}`, id, wid, role, `orig/i${n}${k}.jpg`, sha(`i${n}${k}`), `Walk ${n}, a test painting`, role === 'main' ? 0 : 1, T0).run();
  await acceptAgreement(mf, url, email);
  await call('POST', '/api/submit', email, {});
  const sid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(x => x.artist_id === id).id;
  await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve' });
  const q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === id && x.status === 'awaiting_founder');
  await call('POST', `/api/admin/queue/${q.id}/publish`, FOUNDER, {});
  await pipe('POST', `/api/pipeline/export/${q.id}`);
  await pipe('POST', `/api/pipeline/result/${q.id}`, { status: 'failed', detail: P9 });
  fresh();
  return { id, email, wid, sid, q: q.id };
}
const preserved = async a => JSON.stringify({
  v: await qa('SELECT * FROM versions WHERE artist_id=?', a.id), s: await qa('SELECT * FROM submissions WHERE artist_id=?', a.id),
  ag: await qa('SELECT * FROM agreement_acceptances WHERE artist_id=?', a.id), w: await qa('SELECT * FROM artworks WHERE artist_id=?', a.id),
  i: await qa('SELECT * FROM images WHERE artist_id=?', a.id), g: await qa('SELECT * FROM gallery_positions WHERE artist_id=?', a.id) });

console.log('PROVE · PlotArt Retry publishing');
await seedPublished(db, { id: 'aleah', slug: 'leah-like', email: 'leah-like@example.test', name: 'Leah Like', works: 4 });
await seedPublished(db, { id: 'apat', slug: 'pat-published', email: 'pat-published@example.test', name: 'Pat Published', works: 3 });
const others0 = JSON.stringify([await artistRows(db, 'aleah'), await artistRows(db, 'apat')]);

console.log('— a failed first publication (Fintan-shaped: one artwork, extra views)');
const F = await artistWithFailedV1(1, 'Fin Failed');
let row = await q1('SELECT * FROM publish_queue WHERE id=?', F.q);
const posBefore = await q1('SELECT position FROM gallery_positions WHERE artist_id=?', F.id);
check('S0 set-up: version 1 was approved, the publisher refused it (P9), the job is failed and a gallery position was kept',
  row.status === 'failed' && /P9/.test(row.detail) && posBefore && posBefore.position >= 1, JSON.stringify(row));
const keep = await preserved(F);
const failRow = row;

let x = await call('POST', `/api/admin/queue/${F.q}/retry`, F.email, {});
check('R1 an artist cannot retry (refused) and nothing starts', x.s === 403 && fresh().length === 0, x.s);
x = await call('POST', `/api/admin/queue/${F.q}/retry`, null, {});
check('R2 signed out: refused, nothing starts', x.s >= 400 && x.s !== 200 && fresh().length === 0 && (await q1('SELECT status FROM publish_queue WHERE id=?', F.q)).status === 'failed', x.s);
x = await call('POST', `/api/admin/queue/${F.q}/publish`, FOUNDER, {});
check('R3 the ordinary Publish still refuses a failed job (unchanged rule)', x.s === 409 && fresh().length === 0, x.s);

x = await call('POST', `/api/admin/queue/${F.q}/retry`, FOUNDER, {});
let hh = fresh();
row = await q1('SELECT * FROM publish_queue WHERE id=?', F.q);
check('R4 the founder retries: the protected publishing workflow starts ONCE on main; the SAME job (same id, version 1) is ready',
  x.s === 200 && x.j.publish === 'requested' && x.j.attempt === 1 && onlyPublish(hh) && row.status === 'ready' && row.version === failRow.version
  && (await qa('SELECT id FROM publish_queue WHERE artist_id=?', F.id)).length === 1, JSON.stringify([x, hh, row]));
check('R5 the pipeline lists it exactly like a normal Publish (so every guard and image-provenance check runs again)',
  (await pipe('GET', '/api/pipeline/queue')).j.items.filter(i => i.id === F.q).length === 1);
check('R6 approval, licence acceptance, artwork, images and gallery position are unchanged', (await preserved(F)) === keep);
const ra = await q1("SELECT * FROM audit WHERE action='publish_retry' AND artist_id=? ORDER BY id DESC LIMIT 1", F.id);
check('R7 the audit log keeps the history: the earlier failure (with its P9 reason) and the retry by the founder; no token anywhere',
  ra && ra.actor === FOUNDER && /"previous_failure":"Image provenance refused: FAIL P9/.test(ra.detail) && /"attempt":1/.test(ra.detail)
  && await q1("SELECT 1 FROM audit WHERE action='publish_failed' AND artist_id=?", F.id) && !(await q1("SELECT 1 FROM audit WHERE detail LIKE '%test-dispatch-token%'")), ra && ra.detail);

console.log('— duplicate and concurrent presses');
x = await call('POST', `/api/admin/queue/${F.q}/retry`, FOUNDER, {});
check('R8 pressing again while it is queued: refused ("already being published"), nothing starts, still one job',
  x.s === 409 && /already being published/.test(x.j.error) && fresh().length === 0 && (await qa("SELECT id FROM publish_queue WHERE status IN ('ready','exporting')")).length === 1, JSON.stringify(x.j));
await pipe('POST', `/api/pipeline/export/${F.q}`);
x = await call('POST', `/api/admin/queue/${F.q}/retry`, FOUNDER, {});
check('R9 while the pipeline is exporting it: refused, nothing starts', x.s === 409 && fresh().length === 0);
await pipe('POST', `/api/pipeline/result/${F.q}`, { status: 'published', detail: 'published' });
row = await q1('SELECT * FROM publish_queue WHERE id=?', F.q);
check('R10 the retried job publishes; the artist is marked published; the gallery position is the one kept from the first attempt',
  row.status === 'published' && (await q1('SELECT first_published_at FROM artists WHERE id=?', F.id)).first_published_at
  && (await q1('SELECT position FROM gallery_positions WHERE artist_id=?', F.id)).position === posBefore.position);
x = await call('POST', `/api/admin/queue/${F.q}/retry`, FOUNDER, {});
check('R11 once published it cannot be retried ("already published"), nothing starts', x.s === 409 && /already published/.test(x.j.error) && fresh().length === 0, JSON.stringify(x.j));

const C = await artistWithFailedV1(2, 'Cora Concurrent');
const both = await Promise.all([1, 2, 3].map(() => call('POST', `/api/admin/queue/${C.q}/retry`, FOUNDER, {})));
hh = fresh();
check('R12 three simultaneous presses: exactly one is accepted, the others refused, the workflow starts once, one job only',
  both.filter(b => b.s === 200).length === 1 && both.filter(b => b.s === 409).length === 2 && onlyPublish(hh)
  && (await q1("SELECT COUNT(*) AS n FROM audit WHERE action='publish_retry' AND artist_id=?", C.id)).n === 1, JSON.stringify([both.map(b => b.s), hh.length]));

console.log('— invalid retries are refused and start nothing');
x = await call('POST', '/api/admin/queue/qnosuchjob/retry', FOUNDER, {});
check('R13 a job that does not exist: refused', x.s === 404 && fresh().length === 0, x.s);
const N = await artistWithFailedV1(3, 'Nora Newer');
await call('PUT', `/api/artworks/${N.wid}`, N.email, { title: 'Walk 3, revised', medium: 'Oil', h_cm: 30, w_cm: 40, ai_involvement: 'none' });
await call('POST', '/api/submit', N.email, {});
const nsid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(s => s.artist_id === N.id).id;
await call('POST', `/api/admin/submissions/${nsid}/decision`, FOUNDER, { decision: 'approve' });
const nq2 = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(q => q.artist_id === N.id && q.status === 'awaiting_founder');
fresh();
x = await call('POST', `/api/admin/queue/${nq2.id}/retry`, FOUNDER, {});
check('R14 a job waiting for the founder (not failed) cannot be "retried": use Publish', x.s === 409 && /Only a publication that failed/.test(x.j.error) && fresh().length === 0, JSON.stringify(x.j));
x = await call('POST', `/api/admin/queue/${N.q}/retry`, FOUNDER, {});
check('R15 an older failed version cannot be retried once a newer version exists; the old job stays failed',
  x.s === 409 && /newer version/.test(x.j.error) && fresh().length === 0 && (await q1('SELECT status FROM publish_queue WHERE id=?', N.q)).status === 'failed', JSON.stringify(x.j));

const D = await artistWithFailedV1(4, 'Dara Declined');
await db.prepare("UPDATE submissions SET status='declined' WHERE id=?").bind(D.sid).run();   // synthetic: approval withdrawn
x = await call('POST', `/api/admin/queue/${D.q}/retry`, FOUNDER, {});
check('R16 the submission behind the version is no longer approved: refused, job stays failed',
  x.s === 409 && /no longer approved/.test(x.j.error) && fresh().length === 0 && (await q1('SELECT status FROM publish_queue WHERE id=?', D.q)).status === 'failed', JSON.stringify(x.j));

const S = await artistWithFailedV1(5, 'Sam Suspended');
await call('POST', `/api/admin/artists/${S.id}/suspend`, FOUNDER);
fresh();
x = await call('POST', `/api/admin/queue/${S.q}/retry`, FOUNDER, {});
check('R17 a suspended artist: refused, nothing starts', x.s === 409 && /isn’t active/.test(x.j.error) && fresh().length === 0, JSON.stringify(x.j));

const B = await artistWithFailedV1(6, 'Bea Busy');
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qbusy', ?, 0, 'instant', 'exporting', ?, ?)").bind(B.id, T0, T0).run();
x = await call('POST', `/api/admin/queue/${B.q}/retry`, FOUNDER, {});
check('R18 another publication for the same artist is in progress: refused, nothing starts', x.s === 409 && /already in progress/.test(x.j.error) && fresh().length === 0, JSON.stringify(x.j));
await db.prepare("DELETE FROM publish_queue WHERE id='qbusy'").run();

// synthetic: an approved version 1 that failed, for an artist who has never accepted the agreement (records are append-only,
// so the state is built directly rather than by removing an acceptance)
const A = { id: (await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Ash Unaccepted', email: 'ash@example.test', founding: true })).j.id, q: 'qashfailed' };
const like = await q1('SELECT snapshot, changes FROM submissions WHERE id=?', D.sid);
await db.batch([
  db.prepare("INSERT INTO submissions (id, artist_id, created_at, tier, status, decided_at, snapshot, changes, base_version) VALUES ('sash', ?, ?, 'full', 'approved', ?, ?, ?, 0)").bind(A.id, T0, T0, like.snapshot, like.changes),
  db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?, 1, ?, 'sash', ?)").bind(A.id, like.snapshot, T0),
  db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, detail, created_at, updated_at) VALUES ('qashfailed', ?, 1, 'reviewed', 'failed', 'FAIL P9 test', ?, ?)").bind(A.id, T0, T0)]);
x = await call('POST', `/api/admin/queue/${A.q}/retry`, FOUNDER, {});
check('R19 the agreement rule is the same as Publish: a first publication without the accepted agreement is refused',
  x.s === 409 && /has not accepted/.test(x.j.error) && fresh().length === 0 && (await q1('SELECT status FROM publish_queue WHERE id=?', A.q)).status === 'failed', JSON.stringify(x.j));

console.log('— GitHub unreachable');
const G = await artistWithFailedV1(8, 'Gus GitHubDown');
ghStatus = 500;
x = await call('POST', `/api/admin/queue/${G.q}/retry`, FOUNDER, {});
ghStatus = 204; fresh();
check('R20 if the workflow cannot be started, the retry is kept (ready for the scheduled run) and the reply says so',
  x.s === 200 && x.j.publish === 'failed' && (await q1('SELECT status FROM publish_queue WHERE id=?', G.q)).status === 'ready', JSON.stringify(x.j));

console.log('— normal publishing and other artists');
const P = await (async () => {
  const email = 'plain@example.test';
  const id = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Plain Publish', email, founding: true })).j.id;
  await call('PUT', '/api/me/profile', email, { medium: 'painting', bio: 'Plain Publish is a synthetic test artist for the normal route.' });
  const wid = (await call('POST', '/api/artworks', email)).j.id;
  await call('PUT', `/api/artworks/${wid}`, email, { title: 'Plain', medium: 'Oil', h_cm: 30, w_cm: 40, ai_involvement: 'none' });
  await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
    VALUES ('iplain', ?, ?, 'main', 'orig/iplain.jpg', ?, 1000, 2400, 1800, 'jpeg', 'Plain, a test painting', 'self', '{"blocks":[],"warns":[]}', 0, ?)`).bind(id, wid, sha('iplain'), T0).run();
  await acceptAgreement(mf, url, email); await call('POST', '/api/submit', email, {});
  const sid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(s => s.artist_id === id).id;
  await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve' });
  return { id, q: (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(q => q.artist_id === id && q.status === 'awaiting_founder').id };
})();
fresh();
x = await call('POST', `/api/admin/queue/${P.q}/publish`, FOUNDER, {});
check('R21 normal Publish is unchanged: starts the workflow once, job ready', x.s === 200 && x.j.publish === 'requested' && onlyPublish(fresh())
  && (await q1('SELECT status FROM publish_queue WHERE id=?', P.q)).status === 'ready');
check('R22 previously published artists’ records are byte-for-byte unchanged', JSON.stringify([await artistRows(db, 'aleah'), await artistRows(db, 'apat')]) === others0);

console.log('— the Review Desk');
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', e => errs.push(e.message));
await pg.goto(url + '/admin', { waitUntil: 'load' }); await pg.waitForTimeout(800);
const li = pg.locator('li', { has: pg.locator(`[data-retry="${D.q}"]`) });
const txt = await li.innerText().catch(() => '');
check('R23 a failed job shows "publishing failed", the failing check (FAIL P9 …) and a Retry publishing button; ready/waiting jobs do not',
  /publishing failed/.test(txt) && /Last attempt: Image provenance refused: FAIL P9/.test(txt) && /Retry publishing/.test(txt)
  && !(await pg.locator(`[data-retry="${P.q}"]`).count()) && (await pg.locator('[data-retry]').count()) === 5, txt);
const btn = li.locator('[data-retry]');
await btn.click();
check('R24 the first press only asks to confirm (nothing sent)', /Retry publishing to plotnua.ie\?/.test(await btn.innerText()) && fresh().length === 0);
await btn.click(); await pg.waitForTimeout(600);
const warn = await li.locator('[data-pubwarn]').innerText();
check('R25 a refused retry shows a clear message in place', /^Not retried: The submission behind this version is no longer approved/.test(warn) && fresh().length === 0, warn);
const okLi = pg.locator('li', { has: pg.locator(`[data-retry="${B.q}"]`) });
await okLi.locator('[data-retry]').click(); await okLi.locator('[data-retry]').click(); await pg.waitForTimeout(900);
const body = await pg.locator('body').innerText();
check('R26 a successful retry shows "Retry started …" and the job leaves the failed list', /Retry started: plotnua\.ie updates once every check has passed/.test(body)
  && onlyPublish(fresh()) && !(await pg.locator(`[data-retry="${B.q}"]`).count()), body.slice(0, 300));
check('R27 no page errors', errs.length === 0, errs.join(' | '));
await browser.close();

await mf.dispose(); gh.close();
const pass = results.filter(Boolean).length;
console.log(`\nRETRY PUBLISHING · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
process.exit(pass === results.length ? 0 : 1);
