// PROVE · Three galleries (Phase B) · integrity checks requested at final verification (24 Nov 2026). Synthetic artists only;
// the Worker runs locally (Miniflare/workerd) with a local D1, which enforces foreign keys as Cloudflare D1 does. Nothing here
// touches Cloudflare. (I8.0 uses a Contemporary take-out: revision 1 still used the earlier gallery names.)
//   I1 artwork placements cannot associate an artwork with the wrong artist
//   I2 Artists in Focus cannot reference another artist's artwork
//   I3 image-use consent cannot be recorded against another artist's artwork or an unrelated request
//   I4 expired, cancelled and withdrawn permissions cannot authorise future use
//   I5 a new invitation or renewed membership cannot reuse an obsolete acceptance
//   I6 simultaneous approval / acceptance / withdrawal cannot bypass the state transitions (forced interleavings + a stress run)
//   I7 artist creation and gallery writes cannot leave partially created records (fault injection)
//   I8 existing deletion, withdrawal and account-management processes work with the new foreign keys
//   node test/prove-galleries-integrity.mjs
import { execFileSync } from 'node:child_process';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished, artistRows } from './seed.mjs';
import * as G from '../src/galleries.js';

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
console.log('PROVE · Three galleries · integrity (final verification)');

/* ---- I8 (part 0) · the defect this revision fixes: with revision 1 of migration 0023 (no ON DELETE CASCADE), D1 refuses an
   existing Studio deletion once a gallery row points at the artwork ---- */
{
  const mainSchema = execFileSync('git', ['-C', HERE, 'show', 'b4ee6708:worker/plotart-studio/schema.sql']   /* the schema before migration 0023 (pinned 25 Nov 2026) */, { encoding: 'utf8' });
  const rev1 = execFileSync('git', ['-C', HERE, 'show', 'e026ccd:worker/plotart-studio/migrations/0023_three_galleries.sql'], { encoding: 'utf8' });
  const S0 = await start({ port: 8861, schemaSql: mainSchema + '\n' + rev1 });
  const c0 = mkcall(S0.mf, S0.url);
  await seedPublished(S0.db, { id: 'aold', slug: 'old-rev', email: 'old@example.test', name: 'Old Rev', works: 1 });
  // a gallery row that every revision accepts: the founder takes a draft out of Contemporary (an explicit 'withdrawn' placement)
  const wid = (await c0('POST', '/api/artworks', 'old@example.test')).j.id;
  await c0('POST', `/api/admin/galleries/contemporary/artworks/${wid}/withdraw`, FOUNDER);
  const del = await c0('DELETE', `/api/artworks/${wid}`, 'old@example.test');
  check('I8.0 (the defect found) with revision 1 of the migration, deleting a draft that has a gallery placement is REFUSED by the database (foreign key)',
    del.s >= 500 && (await S0.db.prepare('SELECT COUNT(*) n FROM artworks WHERE id = ?').bind(wid).first()).n === 1, `${del.s} ${del.t.slice(0, 120)}`);
  await S0.mf.dispose();
}

const S = await start({ port: 8862, env: { PARTICIPATION_DELETION: 'on' } });
const { mf, url, db } = S, call = mkcall(mf, url), env = { DB: db };
const A = 'ana@example.test', B = 'ben@example.test', C = 'cara@example.test', D = 'dia@example.test', E = 'eve@example.test';
await seedPublished(db, { id: 'aana', slug: 'ana-test', email: A, name: 'Ana Test', works: 3, number: 1 });
await seedPublished(db, { id: 'aben', slug: 'ben-test', email: B, name: 'Ben Test', works: 2, number: 2 });
await seedPublished(db, { id: 'acara', slug: 'cara-test', email: C, name: 'Cara Test', works: 2, number: 3 });
await seedPublished(db, { id: 'adia', slug: 'dia-test', email: D, name: 'Dia Test', works: 2, number: 4 });
await seedPublished(db, { id: 'aeve', slug: 'eve-test', email: E, name: 'Eve Test', works: 1, number: 5 });
const state = async (aid, g) => (await db.prepare('SELECT * FROM gallery_memberships WHERE artist_id = ? AND gallery_id = ?').bind(aid, g).first());
const pstate = async (wid, g) => (await db.prepare('SELECT * FROM artwork_placements WHERE artwork_id = ? AND gallery_id = ?').bind(wid, g).first());
const pipe = async () => (await call('GET', '/api/pipeline/galleries', null, undefined, PIPE)).j.galleries;
const pg = async g => (await pipe()).find(x => x.gallery === g);
const join = async (aid, email, g) => { const a = await call('POST', `/api/admin/galleries/${g}/members`, FOUNDER, { artist_id: aid }); const b = await call('POST', `/api/galleries/${g}/accept`, email); return a.s === 200 && b.s === 200; };
const placeLive = async (wid, email, g) => { const a = await call('POST', `/api/admin/galleries/${g}/artworks/${wid}/place`, FOUNDER); const b = await call('POST', `/api/galleries/${g}/artworks/${wid}/accept`, email); return a.s === 200 && b.s === 200; };
const ana0 = JSON.stringify(await artistRows(db, 'aeve'));   // an artist nothing here should touch

/* ---- I1 · placements are always the artwork's own artist ---- */
check('I1.0 setup: Ana and Ben are live members of Spaces', await join('aana', A, 'spaces') && await join('aben', B, 'spaces'));
let r = await call('POST', '/api/admin/galleries/being/artworks/waben1/place', FOUNDER);
check('I1.1 the founder cannot place a work in a gallery its own artist is not a member of', r.s === 409 && !(await pstate('waben1', 'being')));
r = await call('POST', '/api/galleries/spaces/artworks/waben1/propose', A);
check('I1.2 an artist cannot propose another artist’s work (not found, nothing written)', r.s === 404 && !(await pstate('waben1', 'spaces')));
check('I1.3 a founder placement records the artwork’s OWN artist (read from the artwork, never from the request)',
  await placeLive('waana1', A, 'spaces') && (await pstate('waana1', 'spaces')).artist_id === 'aana');
// a deliberately corrupt row (as if written by hand): Ben's work recorded under Ana
await db.prepare(`INSERT INTO artwork_placements (artwork_id, artist_id, gallery_id, state, proposed_by, proposed_at, founder_approved_by, founder_approved_at, artist_accepted_at, updated_at)
  VALUES ('waben2','aana','spaces','live','x','2026-11-24T00:00:00.000Z','x','2026-11-24T00:00:00.000Z','2026-11-24T00:00:00.000Z','2026-11-24T00:00:00.000Z')`).run();
const l1 = await pg('spaces'), anaView = (await call('GET', '/api/galleries', A)).j, adm = (await call('GET', '/api/admin/galleries', FOUNDER)).j;
check('I1.4 even a corrupt row naming the wrong artist is ignored everywhere: not in the gallery, not in either artist’s view, not in the founder’s list',
  !l1.works.some(w => w.work === 'work-2' && w.artist === 'ben-test') && !anaView.placements.some(p => p.artwork_id === 'waben2') && !adm.placements.some(p => p.artwork_id === 'waben2'),
  JSON.stringify(l1.works));
await db.prepare("DELETE FROM artwork_placements WHERE artwork_id = 'waben2'").run();

/* ---- I2 · Artists in Focus only ever show an artist's own placed work ---- */
await placeLive('waben1', B, 'spaces');
r = await call('PUT', '/api/admin/galleries/spaces/features', FOUNDER, { items: [{ artist_id: 'aana', artwork_id: 'waben1' }] });
check('I2.1 Artists in Focus refuses an artist paired with another artist’s work', r.s === 409 && (await G.features(env, 'spaces')).length === 0);
r = await call('PUT', '/api/admin/galleries/spaces/features', FOUNDER, { items: [{ artist_id: 'aana', artwork_id: 'waana2' }] });
check('I2.2 … and the artist’s own work that is not placed in this gallery', r.s === 409);
r = await call('PUT', '/api/admin/galleries/spaces/features', FOUNDER, { items: [{ artist_id: 'aana', artwork_id: 'waana1' }, { artist_id: 'aben', artwork_id: 'waben1' }] });
check('I2.3 their own placed works are accepted', r.s === 200 && r.j.features.length === 2);
await db.prepare("INSERT INTO gallery_features (gallery_id, position, artist_id, artwork_id, updated_at, updated_by) VALUES ('spaces', 3, 'acara', 'waana2', '2026-11-24T00:00:00.000Z', 'x')").run();
check('I2.4 a corrupt feature row (Cara with Ana’s work) is never shown to the publisher or the founder',
  !(await pg('spaces')).features.some(f => f.artist_id === 'acara') && !(await call('GET', '/api/admin/galleries', FOUNDER)).j.galleries.find(g => g.gallery_id === 'spaces').features.some(f => f.artist_id === 'acara'));
await db.prepare("DELETE FROM gallery_features WHERE artist_id = 'acara'").run();
await call('POST', '/api/galleries/spaces/artworks/waben1/withdraw', B);
check('I2.5 when a placement closes, its Artists in Focus entry goes with it (stored and shown)',
  !(await G.features(env, 'spaces')).some(f => f.artwork_id === 'waben1') && !(await pg('spaces')).features.some(f => f.artwork_id === 'waben1'));

/* ---- I3 · consent belongs to its own artist and its own request ---- */
const ask = (aid, ids, extra = {}) => call('POST', '/api/admin/image-use/requests', FOUNDER, { artist_id: aid, scope: 'homepage_feature', gallery_id: 'spaces', artwork_ids: ids,
  purpose: 'Spaces homepage, Artists in Focus image', channels: 'plotnua.ie homepage', valid_until: '2027-06-30', ...extra });
r = await ask('aana', ['waana1', 'waben1']);
check('I3.1 a request for one artist cannot include another artist’s work', r.s === 409 && (await db.prepare('SELECT COUNT(*) n FROM image_use_requests').first()).n === 0);
const R1 = (await ask('aana', ['waana1'])).j.request.id;
r = await call('POST', `/api/image-use/${R1}/answer`, B, { answer: 'yes' });
check('I3.2 another artist cannot answer it (not found; nothing recorded; still open)', r.s === 404 && (await db.prepare('SELECT COUNT(*) n FROM image_use_consents').first()).n === 0
  && (await db.prepare('SELECT status FROM image_use_requests WHERE id = ?').bind(R1).first()).status === 'open');
r = await call('POST', '/api/admin/image-use/record', FOUNDER, { request_id: R1, artist_id: 'aben', answer: 'yes' });
check('I3.3 the founder cannot record an email answer against a request that belongs to a different artist', r.s === 409 && (await db.prepare('SELECT COUNT(*) n FROM image_use_consents').first()).n === 0);
r = await call('POST', '/api/admin/image-use/record', FOUNDER, { artist_id: 'aana', scope: 'social_media', artwork_ids: ['waben1'], purpose: 'Instagram post about the new gallery', channels: 'Instagram', answer: 'yes' });
check('I3.4 nor record a stand-alone answer for one artist that names another artist’s work', r.s === 409);
await db.prepare(`INSERT INTO image_use_consents (id, request_id, artist_id, scope, gallery_id, artwork_ids, purpose, channels, valid_until, answer, method, request_text_sha256, recorded_by, created_at)
  VALUES ('cforged', NULL, 'aana', 'social_media', NULL, '["waben1"]', 'forged for the test only', 'Instagram', NULL, 'yes', 'studio', ?, 'x', '2026-11-24T00:00:00.000Z')`).bind('0'.repeat(64)).run();
check('I3.5 even a forged consent row naming another artist’s work authorises nothing (for either artist)',
  !(await G.consentFor(env, 'aana', 'waben1', 'social_media')) && !(await G.consentFor(env, 'aben', 'waben1', 'social_media')));
await db.prepare("DELETE FROM image_use_consents WHERE id = 'cforged'").run();
r = await call('POST', `/api/image-use/${R1}/answer`, A, { answer: 'yes' });
const c1 = await db.prepare('SELECT * FROM image_use_consents WHERE request_id = ?').bind(R1).first(), q1 = await db.prepare('SELECT * FROM image_use_requests WHERE id = ?').bind(R1).first();
check('I3.6 the artist’s own answer copies the request exactly (artist, scope, gallery, works, purpose, channels, end date, request text hash)',
  r.s === 200 && ['artist_id', 'scope', 'gallery_id', 'artwork_ids', 'purpose', 'channels', 'valid_until', 'request_text_sha256'].every(k => c1[k] === q1[k]) && q1.status === 'answered');
check('I3.7 that yes authorises exactly that use: this work, this scope, in Spaces',
  await G.consentFor(env, 'aana', 'waana1', 'homepage_feature', { gallery: 'spaces', on: '2027-01-01' }) && !(await G.consentFor(env, 'aana', 'waana2', 'homepage_feature', { gallery: 'spaces', on: '2027-01-01' }))
  && !(await G.consentFor(env, 'aana', 'waana1', 'social_media', { gallery: 'spaces', on: '2027-01-01' })));

/* ---- I4 · expired, cancelled and withdrawn permissions authorise nothing ---- */
check('I4.1 after its end date the same yes no longer authorises anything', !(await G.consentFor(env, 'aana', 'waana1', 'homepage_feature', { gallery: 'spaces', on: '2027-07-01' })));
check('I4.2 a yes for Spaces never covers Being, nor a use with no gallery named',
  !(await G.consentFor(env, 'aana', 'waana1', 'homepage_feature', { gallery: 'being', on: '2027-01-01' })) && !(await G.consentFor(env, 'aana', 'waana1', 'homepage_feature', { on: '2027-01-01' })));
r = await ask('aana', ['waana1'], { valid_until: '2020-01-01' });
check('I4.3 a request whose end date has already passed cannot be made', r.s === 400);
await db.prepare(`INSERT INTO image_use_requests (id, artist_id, scope, gallery_id, artwork_ids, purpose, channels, valid_until, request_text_sha256, status, requested_by, requested_at)
  VALUES ('uexpired','aana','video_feature','spaces','["waana1"]','A video about Spaces artists','YouTube','2020-01-01',?, 'open', ?, '2019-12-01T00:00:00.000Z')`).bind('1'.repeat(64), FOUNDER).run();
r = await call('POST', '/api/image-use/uexpired/answer', A, { answer: 'yes' });
check('I4.4 an open request that has expired can no longer be answered yes (nothing recorded)', r.s === 409 && !(await db.prepare("SELECT id FROM image_use_consents WHERE request_id = 'uexpired'").first()));
const R3 = (await ask('aana', ['waana1'], { scope: 'editorial_feature' })).j.request.id;
await call('POST', `/api/admin/image-use/requests/${R3}/cancel`, FOUNDER);
r = await call('POST', `/api/image-use/${R3}/answer`, A, { answer: 'yes' });
check('I4.5 a cancelled request cannot be answered, records nothing and authorises nothing',
  r.s === 404 && !(await db.prepare('SELECT id FROM image_use_consents WHERE request_id = ?').bind(R3).first()) && !(await G.consentFor(env, 'aana', 'waana1', 'editorial_feature', { gallery: 'spaces' })));
r = await call('POST', `/api/image-use/consents/${c1.id}/withdraw`, A);
const answers = (await db.prepare('SELECT answer FROM image_use_consents WHERE request_id = ? ORDER BY rowid').bind(R1).all()).results.map(x => x.answer).join(',');
check('I4.6 the artist withdraws the yes: it no longer authorises anything; the earlier yes stays on record (append-only: yes,no)',
  r.s === 200 && answers === 'yes,no' && !(await G.consentFor(env, 'aana', 'waana1', 'homepage_feature', { gallery: 'spaces', on: '2027-01-01' })), answers);
r = await call('POST', `/api/image-use/consents/${c1.id}/withdraw`, B);
check('I4.7 another artist cannot withdraw (or see) it', r.s === 404);
const R4 = (await ask('aana', ['waana1'])).j.request.id; await call('POST', `/api/image-use/${R4}/answer`, A, { answer: 'yes' });
const yesAgain = await G.consentFor(env, 'aana', 'waana1', 'homepage_feature', { gallery: 'spaces', on: '2027-01-01' });
await call('POST', '/api/galleries/spaces/withdraw', A);
check('I4.8 a fresh yes works again, and stops working the moment the artist leaves that gallery',
  yesAgain && !(await G.consentFor(env, 'aana', 'waana1', 'homepage_feature', { gallery: 'spaces', on: '2027-01-01' })));

/* ---- I5 · no obsolete acceptance is ever reused ---- */
await call('POST', '/api/galleries/being/request', D);
await call('POST', '/api/galleries/being/withdraw', D);
await call('POST', '/api/admin/galleries/being/members', FOUNDER, { artist_id: 'adia' });
let m = await state('adia', 'being');
check('I5.1 a request the artist withdrew does not count as acceptance of a later invitation (invited, not live; no acceptance date)',
  m.state === 'founder_approved' && m.artist_accepted_at === null, JSON.stringify(m));
await call('POST', '/api/galleries/being/decline', D);
await call('POST', '/api/galleries/being/request', D);
m = await state('adia', 'being');
check('I5.2 an invitation the artist declined does not count as the founder’s approval of their later request (requested, not live; no approval)',
  m.state === 'artist_accepted' && m.founder_approved_at === null && m.founder_approved_by === null, JSON.stringify(m));
await call('POST', '/api/admin/galleries/being/members/adia/approve', FOUNDER);
await call('POST', '/api/galleries/being/artworks/wadia1/propose', D);
await call('POST', '/api/galleries/being/artworks/wadia1/withdraw', D);
await call('POST', '/api/admin/galleries/being/artworks/wadia1/place', FOUNDER);
let p = await pstate('wadia1', 'being');
check('I5.3 a work proposal the artist withdrew does not count as acceptance of a later placement (approved, not live)', p.state === 'founder_approved' && p.artist_accepted_at === null, JSON.stringify(p));
await call('POST', '/api/galleries/being/artworks/wadia1/accept', D);
await call('PUT', '/api/admin/galleries/being/order', FOUNDER, { artists: ['adia'] });
await call('PUT', '/api/admin/galleries/being/features', FOUNDER, { items: [{ artist_id: 'adia', artwork_id: 'wadia1' }] });
const before5 = (await pg('being'));
await call('POST', '/api/galleries/being/withdraw', D);
await call('POST', '/api/admin/galleries/being/members', FOUNDER, { artist_id: 'adia' });
await call('POST', '/api/galleries/being/accept', D);
const after5 = await pg('being');
p = await pstate('wadia1', 'being');
check('I5.4 leaving a gallery closes the artist’s placements, order position and Artists in Focus there; re-joining later revives none of them',
  before5.works.length === 1 && before5.order.length === 1 && before5.features.length === 1 && p.state === 'withdrawn'
  && after5.artists.includes('dia-test') && after5.works.length === 0 && after5.order.length === 0 && after5.features.length === 0, JSON.stringify({ before5, after5 }));

/* ---- I6 · simultaneous requests cannot bypass the transitions ---- */
// Forced interleavings: the competing request runs exactly between this request's read and its write.
const racing = (compete) => { let h = compete; return { DB: { prepare: (...a) => db.prepare(...a), batch: async s => { if (h) { const f = h; h = null; await f(); } return db.batch(s); } } }; };
const outcome = async f => { try { await f(); return 'ok'; } catch (e) { return e.status || e.message; } };
const founderE = FOUNDER, artE = { id: 'aeve', email: E };
await G.founderPropose(env, founderE, 'spaces', { artist_id: 'aeve' });
let o = await outcome(() => G.artistAct(racing(() => G.founderClose(env, founderE, 'spaces', 'aeve', 'withdrawn')), artE, 'spaces', 'accept'));
check('I6.1 artist accepts while the founder withdraws the invitation: the accept is refused (409); the membership stays withdrawn, never live',
  o === 409 && (await state('aeve', 'spaces')).state === 'withdrawn', o);
await G.founderPropose(env, founderE, 'spaces', { artist_id: 'aeve' });
o = await outcome(() => G.founderClose(racing(() => G.artistAct(env, artE, 'spaces', 'accept')), founderE, 'spaces', 'aeve', 'withdrawn'));
check('I6.2 the founder withdraws an invitation the artist accepted a moment earlier: refused (409) rather than acting on stale state; live stands (the founder can then withdraw it knowingly)',
  o === 409 && (await state('aeve', 'spaces')).state === 'live', o);
await G.artistAct(env, artE, 'being', 'request');
o = await outcome(() => G.founderApprove(racing(() => G.artistAct(env, artE, 'being', 'withdraw')), founderE, 'being', 'aeve'));
check('I6.3 the founder approves a request the artist is withdrawing: refused (409); withdrawn, never live', o === 409 && (await state('aeve', 'being')).state === 'withdrawn', o);
await G.founderPlacement(env, founderE, 'spaces', 'waeve1', 'place');
o = await outcome(() => G.artistPlacement(racing(() => G.founderPlacement(env, founderE, 'spaces', 'waeve1', 'withdraw')), artE, 'spaces', 'waeve1', 'accept'));
check('I6.4 a work is accepted while the founder withdraws it: refused (409); the placement stays withdrawn', o === 409 && (await pstate('waeve1', 'spaces')).state === 'withdrawn', o);
await G.founderPlacement(env, founderE, 'spaces', 'waeve1', 'place');
o = await outcome(() => G.artistPlacement(racing(() => G.founderClose(env, founderE, 'spaces', 'aeve', 'withdrawn')), artE, 'spaces', 'waeve1', 'accept'));
check('I6.5 a work is accepted while the artist’s membership is withdrawn: refused (409); the work is not live in a gallery its artist has left',
  o === 409 && (await pstate('waeve1', 'spaces')).state === 'withdrawn' && (await state('aeve', 'spaces')).state === 'withdrawn', o);
const u5 = (await G.requestConsent(env, founderE, { artist_id: 'aeve', scope: 'social_media', artwork_ids: ['waeve1'], purpose: 'A post about the new galleries', channels: 'Instagram' })).id;
o = await outcome(() => G.answerConsent(racing(() => G.answerConsent(env, artE, u5, { answer: 'no' })), artE, u5, { answer: 'yes' }));
const ans5 = (await db.prepare('SELECT answer FROM image_use_consents WHERE request_id = ?').bind(u5).all()).results;
check('I6.6 two answers to one request at once: exactly one is recorded (the first), the other is refused; no yes slips in',
  o === 409 && ans5.length === 1 && ans5[0].answer === 'no' && !(await G.consentFor(env, 'aeve', 'waeve1', 'social_media')), JSON.stringify({ o, ans5 }));
o = await outcome(() => G.founderPropose(racing(() => G.artistAct(env, { id: 'acara', email: C }, 'being', 'request')), founderE, 'being', { artist_id: 'acara' }));
const cRows = (await db.prepare("SELECT gallery_id, state FROM gallery_memberships WHERE artist_id = 'acara' ORDER BY gallery_id").all()).results;
check('I6.7 the founder invites while the artist requests the same gallery: one wins, the other is refused (409); one row per gallery; Contemporary written once, as it was',
  o === 409 && JSON.stringify(cRows) === JSON.stringify([{ gallery_id: 'being', state: 'artist_accepted' }, { gallery_id: 'contemporary', state: 'live' }]), JSON.stringify({ o, cRows }));
// Stress: real concurrent HTTP requests, 25 rounds of "artist accepts" against "founder withdraws".
let bad = 0, both = 0, rounds = 0;
for (let i = 0; i < 25; i++) {
  await G.founderPropose(env, founderE, 'spaces', { artist_id: 'aeve' }).catch(() => {});
  if ((await state('aeve', 'spaces')).state !== 'founder_approved') { bad++; continue; }
  const [x, y] = await Promise.all([call('POST', '/api/galleries/spaces/accept', E), call('POST', '/api/admin/galleries/spaces/members/aeve/withdraw', FOUNDER)]);
  const st = (await state('aeve', 'spaces')).state; rounds++;
  if (x.s === 200 && y.s === 200) both++;
  const okEnd = (y.s === 200 && st === 'withdrawn') || (y.s === 409 && x.s === 200 && st === 'live');
  if (!okEnd || ![200, 409].includes(x.s) || ![200, 409].includes(y.s)) bad++;
  if (st === 'live') await G.founderClose(env, founderE, 'spaces', 'aeve', 'withdrawn');
}
check(`I6.8 stress: ${rounds} rounds of simultaneous accept and withdraw over HTTP end only in valid states (withdrawn, or live with the withdrawal refused)`, rounds === 25 && bad === 0, JSON.stringify({ bad, both }));

/* ---- I7 · nothing half-created (a fault is injected into the database mid-write) ---- */
const fault = (name, sql) => db.prepare(`CREATE TRIGGER ${name} ${sql} BEGIN SELECT RAISE(ABORT, 'injected test fault'); END`).run();
const unfault = name => db.prepare(`DROP TRIGGER ${name}`).run();
await fault('f1', "BEFORE INSERT ON gallery_memberships WHEN NEW.gallery_id = 'being'");
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Faye Fault', email: 'faye@example.test', programme: 'gallery_artist', galleries: ['spaces', 'being'] });
const faye = await db.prepare("SELECT id FROM artists WHERE email = 'faye@example.test'").first();
check('I7.1 an invitation whose second gallery fails to write creates NOTHING: no artist, no commission terms, no gallery rows',
  r.s >= 500 && !faye && (await db.prepare("SELECT COUNT(*) n FROM artist_terms t JOIN artists a ON a.id = t.artist_id WHERE a.email = 'faye@example.test'").first()).n === 0
  && (await db.prepare("SELECT COUNT(*) n FROM gallery_memberships WHERE proposed_at >= '2026-11-24' AND artist_id NOT IN (SELECT id FROM artists)").first()).n === 0, `${r.s}`);
await unfault('f1');
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Faye Fault', email: 'faye@example.test', programme: 'gallery_artist', galleries: ['spaces', 'being'] });
const fRows = r.j.id ? (await db.prepare('SELECT gallery_id, state, source FROM gallery_memberships WHERE artist_id = ? ORDER BY gallery_id').bind(r.j.id).all()).results : [];
check('I7.2 the same invitation without the fault creates the artist, the 15% terms and both invitations together (not Contemporary: it was not chosen)',
  r.s === 200 && JSON.stringify(fRows) === JSON.stringify([{ gallery_id: 'being', state: 'founder_approved', source: 'founder_invitation' }, { gallery_id: 'spaces', state: 'founder_approved', source: 'founder_invitation' }])
  && (await db.prepare('SELECT commission_bp FROM artist_terms WHERE artist_id = ?').bind(r.j.id).first()).commission_bp === 1500, JSON.stringify(fRows));
await seedPublished(db, { id: 'agus', slug: 'gus-test', email: 'gus@example.test', name: 'Gus Test', works: 1, number: 6 });
await fault('f2', "BEFORE INSERT ON gallery_memberships WHEN NEW.gallery_id = 'spaces'");
r = await call('POST', '/api/admin/galleries/spaces/members', FOUNDER, { artist_id: 'agus' });
check('I7.3 a first gallery invitation that fails also leaves the default Contemporary membership unwritten (all or nothing)',
  r.s >= 500 && (await db.prepare("SELECT COUNT(*) n FROM gallery_memberships WHERE artist_id = 'agus'").first()).n === 0);
await unfault('f2');
await join('agus', 'gus@example.test', 'spaces'); await placeLive('wagus1', 'gus@example.test', 'spaces');
await call('PUT', '/api/admin/galleries/spaces/features', FOUNDER, { items: [{ artist_id: 'agus', artwork_id: 'wagus1' }] });
await fault('f3', 'BEFORE DELETE ON gallery_features');
r = await call('POST', '/api/admin/galleries/spaces/members/agus/withdraw', FOUNDER);
check('I7.4 withdrawing a membership whose follow-on clean-up fails changes nothing (still live, work still placed, still in focus)',
  r.s >= 500 && (await state('agus', 'spaces')).state === 'live' && (await pstate('wagus1', 'spaces')).state === 'live' && (await G.features(env, 'spaces')).some(f => f.artist_id === 'agus'));
await unfault('f3');
const u7 = (await ask('agus', ['wagus1'])).j.request.id;
await fault('f4', 'BEFORE UPDATE ON image_use_requests');
r = await call('POST', `/api/image-use/${u7}/answer`, 'gus@example.test', { answer: 'yes' });
check('I7.5 an answer whose request cannot be closed records no consent (the request stays open)',
  r.s >= 500 && !(await db.prepare('SELECT id FROM image_use_consents WHERE request_id = ?').bind(u7).first()) && (await db.prepare('SELECT status FROM image_use_requests WHERE id = ?').bind(u7).first()).status === 'open');
await unfault('f4');

/* ---- I8 · existing deletion, leaving and account processes with the new foreign keys ---- */
const wd = (await call('POST', '/api/artworks', 'gus@example.test')).j.id;
await call('POST', `/api/galleries/spaces/artworks/${wd}/propose`, 'gus@example.test');
r = await call('DELETE', `/api/artworks/${wd}`, 'gus@example.test');
check('I8.1 an artist deletes a draft that has a gallery placement: works as today; its placement goes with it',
  r.s === 200 && !(await db.prepare('SELECT id FROM artworks WHERE id = ?').bind(wd).first()) && !(await pstate(wd, 'spaces')));
// Cara: memberships in three galleries, live placement, order, Artists in Focus, requests and consents
await G.founderApprove(env, founderE, 'being', 'acara'); await placeLive('wacara1', C, 'being');
await call('PUT', '/api/admin/galleries/being/order', FOUNDER, { artists: ['acara', 'adia'] });
await call('PUT', '/api/admin/galleries/being/features', FOUNDER, { items: [{ artist_id: 'acara', artwork_id: 'wacara1' }] });
const u8 = (await ask('acara', ['wacara1'], { gallery_id: null })).j.request.id; await call('POST', `/api/image-use/${u8}/answer`, C, { answer: 'yes' });
const yesBefore = await G.consentFor(env, 'acara', 'wacara1', 'homepage_feature');
r = await call('POST', '/api/admin/artists/acara/end', FOUNDER, { confirm_name: 'Cara Test', source: 'artist_request', reason: 'Artist asked by email to leave PlotArt' });
check('I8.2 ending an artist’s participation works as today with gallery records present, and their permissions stop authorising anything',
  r.s === 200 && yesBefore && !(await G.consentFor(env, 'acara', 'wacara1', 'homepage_feature')), r.t.slice(0, 200));
r = await call('POST', '/api/admin/artists/acara/erase-originals', FOUNDER, { confirm: true, reason: 'Artist asked by email for her originals to be deleted now' });
const cnt = async (t, col = 'artist_id') => (await db.prepare(`SELECT COUNT(*) n FROM ${t} WHERE ${col} = 'acara'`).first()).n;
check('I8.3 erasing an ended artist’s originals works as today; their works’ placements and Artists in Focus go with the works',
  r.s === 200 && await cnt('artworks') === 0 && await cnt('artwork_placements') === 0 && await cnt('gallery_features') === 0 && await cnt('gallery_memberships') === 2, r.t.slice(0, 200));
// Hal left PlotArt more than six years ago (dates written directly, as prove-leaving does: the append-only records cannot be
// back-dated through Studio), with gallery records of every kind still present.
await seedPublished(db, { id: 'ahal', slug: 'hal-test', email: 'hal@example.test', name: 'Hal Test', works: 2, number: 7 });
await join('ahal', 'hal@example.test', 'being'); await placeLive('wahal1', 'hal@example.test', 'being');
await call('PUT', '/api/admin/galleries/being/order', FOUNDER, { artists: ['ahal', 'adia'] });
await call('PUT', '/api/admin/galleries/being/features', FOUNDER, { items: [{ artist_id: 'ahal', artwork_id: 'wahal1' }] });
const u9 = (await ask('ahal', ['wahal1'], { gallery_id: 'being' })).j.request.id; await call('POST', `/api/image-use/${u9}/answer`, 'hal@example.test', { answer: 'yes' });
await ask('ahal', ['wahal2'], { gallery_id: null });   // and one still-open request
const hcnt = async t => (await db.prepare(`SELECT COUNT(*) n FROM ${t} WHERE artist_id = 'ahal'`).first()).n;
const GT = ['gallery_memberships', 'gallery_order', 'gallery_features', 'artwork_placements', 'image_use_requests', 'image_use_consents'];
const had = {}; for (const t of GT) had[t] = await hcnt(t);
await db.prepare("UPDATE artists SET account_status = 'ended' WHERE id = 'ahal'").run();
await db.prepare("INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES ('pehal', 'ahal', 'ended', '2019-01-01T00:00:00.000Z', 'founder@example.test', 'Test: left long ago', '{}')").run();
await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('ahal', '2019-01-01T00:00:00.000Z', '2025-01-01T00:00:00.000Z', 'test', '2019-01-01T00:00:00.000Z')").run();
await mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
const left = {}; for (const t of GT) left[t] = await hcnt(t);
check('I8.4 the daily deletion run (originals, then six-year records) works as today for an artist with gallery records of every kind: the artist row and all of them are gone',
  Object.values(had).every(n => n > 0) && !(await db.prepare("SELECT id FROM artists WHERE id = 'ahal'").first()) && Object.values(left).every(n => n === 0), JSON.stringify({ had, left }));
check('I8.5 nobody else’s rows were touched (Dia still ordered in Being; Eve’s existing records identical)',
  (await G.order(env, 'being')).some(o => o.artist_id === 'adia') && JSON.stringify(await artistRows(db, 'aeve')) === ana0);
r = await call('POST', '/api/leave', B, { confirm: true, reason: 'Moving my work elsewhere' });
check('I8.6 an artist’s own request to leave works as today with gallery memberships present', r.s === 200);

/* ---- I9 · the final curatorial identity (25 Nov 2026): contemporary, spaces, being; no earlier identifier is accepted ---- */
const olds = {};
for (const old of ['environment', 'landscape', 'places_and_spaces', 'portraiture']) {
  const rr = await call('POST', `/api/admin/galleries/${old}/members`, FOUNDER, { artist_id: 'aben' });
  let dbr = 'accepted'; try { await db.prepare("INSERT INTO gallery_settings (gallery_id, status, target_artists, target_works, updated_at, updated_by) VALUES (?, 'in_preparation', 1, 1, '2026-11-24T00:00:00.000Z', 'x')").bind(old).run(); } catch { dbr = 'refused'; }
  olds[old] = `${rr.s}/${dbr}`;
}
check('I9.1 no earlier identifier (environment, landscape, places_and_spaces, portraiture) is a gallery: the Studio answers 404 and the database refuses it',
  Object.values(olds).every(v => v === '404/refused'), JSON.stringify(olds));
const gv = (await call('GET', '/api/admin/galleries', FOUNDER)).j.galleries.map(g => [g.gallery_id, g.title]);
check('I9.2 the Studio names the three galleries Contemporary, Spaces and Being (no full stops in functional labels)', JSON.stringify(gv) === JSON.stringify([['contemporary', 'Contemporary'], ['spaces', 'Spaces'], ['being', 'Being']]), JSON.stringify(gv));
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nTHREE GALLERIES · INTEGRITY · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
