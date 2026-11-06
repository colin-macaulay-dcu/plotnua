// PROVE · ending participation and scheduled deletion (development, 6 Nov 2026). Local only: Miniflare D1/R2, synthetic
// artists. Nothing here touches Cloudflare or any real record.
//   node test/prove-leaving.mjs
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished, artistRows } from './seed.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const H = e => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
const mk = s => async (method, path, email, body) => { const r = await s.mf.dispatchFetch(s.url + path, { method, headers: H(email), body: body === undefined ? undefined : JSON.stringify(body) }); return { s: r.status, j: await r.json().catch(() => null) }; };
const ago = (days) => new Date(Date.now() - days * 86400_000).toISOString();

console.log('PROVE · leaving PlotArt\n— with scheduled deletion ON (as it would be after release)');
const S = await start({ port: 8841, env: { PARTICIPATION_DELETION: 'on' }, enquiry: {} });
const { db } = S, call = mk(S), bucket = await S.mf.getR2Bucket('IMAGES', 'studio');
const objects = async prefix => (await bucket.list({ prefix })).objects.length;
const LEAH = 'leah-like@example.test', BEA = 'bea-other@example.test', NEW = 'new-leaver@example.test';
await seedPublished(db, { id: 'aleah', slug: 'leah-like', email: LEAH, name: 'Leah Like', works: 11, bucket, number: 1 });
await seedPublished(db, { id: 'abea', slug: 'bea-other', email: BEA, name: 'Bea Other', works: 4, bucket, number: 2 });
await db.prepare("INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, NULL, 1, NULL, ?), (2, 'aleah', 0, NULL, ?), (3, 'abea', 0, NULL, ?)").bind(ago(1), ago(1), ago(1)).run();
for (const [id, ref] of [['aleah', 'PA-E-261105-AAAAAA'], ['abea', 'PA-E-261105-BBBBBB']])
  await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at) VALUES (?, ?, ?, 'relay', ?, 1, '2027-11-04', 'relay', ?)`).bind('l' + id, ref, id, ago(1), ago(1)).run();

const beaBefore = JSON.stringify(await artistRows(db, 'abea')), beaObjects = await objects('originals/abea/');

let r = await call('POST', '/api/leave', LEAH, { reason: 'Moving my work elsewhere' });
check('V1 asking to leave needs the tick', r.s === 400);
r = await call('POST', '/api/leave', LEAH, { confirm: true, reason: 'Moving my work elsewhere' });
let pa = (await call('GET', '/api/admin/participation', FOUNDER)).j.items.find(i => i.id === 'aleah');
check('V2 the artist asks to leave in Studio; the founder sees the request and the removal deadline (14 days)', r.s === 200 && pa.request && Math.round((Date.parse(pa.request.due) - Date.parse(pa.request.at)) / 86400_000) === 14);
r = await call('POST', '/api/leave/withdraw', LEAH, {});
pa = (await call('GET', '/api/admin/participation', FOUNDER)).j.items.find(i => i.id === 'aleah');
const r2 = await call('POST', '/api/leave', LEAH, { confirm: true });
const pa2 = (await call('GET', '/api/admin/participation', FOUNDER)).j.items.find(i => i.id === 'aleah');
check('V3 she can withdraw the request (kept in the log) and ask again', r.s === 200 && !pa.request && r2.s === 200 && pa2.request && pa2.events.length === 3);
// a pending quick-check submission and an approved version waiting to publish, so the ending has something to stop
await db.prepare("INSERT INTO submissions (id, artist_id, created_at, tier, status, snapshot, changes, base_version) VALUES ('sleah', 'aleah', ?, 'light', 'pending', '{}', '[]', 1)").bind(ago(0.1)).run();
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) SELECT artist_id, 2, snapshot, 'test', ? FROM versions WHERE artist_id='aleah' AND version=1").bind(ago(0.1)).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qleah2', 'aleah', 2, 'reviewed', 'awaiting_founder', ?, ?)").bind(ago(0.1), ago(0.1)).run();
const bad = [await call('POST', '/api/admin/artists/aleah/end', FOUNDER, { confirm_name: 'Leah', source: 'artist_request', reason: 'Artist asked in Studio to leave' }),
  await call('POST', '/api/admin/artists/aleah/end', FOUNDER, { confirm_name: 'Leah Like', source: 'artist_request', reason: 'short' }),
  await call('POST', '/api/admin/artists/aleah/end', FOUNDER, { confirm_name: 'Leah Like', reason: 'Artist asked in Studio to leave' }),
  await call('POST', '/api/admin/artists/aleah/end', LEAH, { confirm_name: 'Leah Like', source: 'artist_request', reason: 'Artist asked in Studio to leave' })];
check('V4 refused without the exact name, a reason, or who asked; an artist cannot end anyone (403); nothing changed', bad.map(b => b.s).join() === '400,400,400,403'
  && (await db.prepare("SELECT account_status FROM artists WHERE id='aleah'").first()).account_status === 'active');
const t0 = Date.now();
r = await call('POST', '/api/admin/artists/aleah/end', FOUNDER, { confirm_name: 'Leah Like', source: 'artist_request', reason: 'Artist asked in Studio to leave' });
const leahA = await db.prepare("SELECT * FROM artists WHERE id='aleah'").first();
const q = (await db.prepare("SELECT * FROM publish_queue WHERE artist_id='aleah' ORDER BY version").all()).results;
const ret = await db.prepare("SELECT * FROM record_retention WHERE artist_id='aleah'").first();
check('V5 ending: her account is ended, the pending submission withdrawn, the waiting version superseded, and a removal of her gallery queued for the pipeline',
  r.s === 200 && leahA.account_status === 'ended' && (await db.prepare("SELECT status FROM submissions WHERE id='sleah'").first()).status === 'withdrawn'
  && q.find(x => x.id === 'qleah2').status === 'superseded' && q.find(x => x.kind === 'remove' && x.status === 'ready' && x.id === r.j.removal_queue), JSON.stringify(r.j));
check('V6 the retention date is fixed at six years after ending (agreement 11.2)', ret && Math.abs(Date.parse(ret.delete_after) - Date.parse(ret.ended_at) - (Date.parse(new Date(Date.parse(ret.ended_at)).toISOString().replace(/^(\d{4})/, y => +y + 6)) - Date.parse(ret.ended_at))) < 86400_000 * 2 && Date.parse(ret.ended_at) >= t0 - 2000);
const signin = await call('GET', '/api/me', LEAH);
const NOTICE = (await import('node:fs')).readFileSync(new URL('../src/enquiry.js', import.meta.url), 'utf8').match(/const NOTICE = '([^']+)'/)[1];
const enquire = slug => S.mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json' },
  body: JSON.stringify({ ref: 'PA-' + slug, notice: NOTICE, name: 'Test Buyer', email: 'buyer@example.test', message: 'Is this work still available?' }) }).then(x => x.status);
check('V7 she can no longer sign in, and her gallery takes no more enquiries', signin.s === 403 && await enquire('leah-like') === 404);
const ex = await (await S.mf.dispatchFetch(S.url + `/api/pipeline/export/${r.j.removal_queue}`, { method: 'POST', headers: { Authorization: `Bearer ${PIPELINE_TOKEN}` } })).json();
await S.mf.dispatchFetch(S.url + `/api/pipeline/result/${r.j.removal_queue}`, { method: 'POST', headers: { Authorization: `Bearer ${PIPELINE_TOKEN}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'published', detail: 'test' }) });
pa = (await call('GET', '/api/admin/participation', FOUNDER)).j.items.find(i => i.id === 'aleah');
const sch = Object.fromEntries(pa.ended.schedule.map(x => [x.key, x]));
check('V8 the pipeline receives the removal (no works) and, once published, the founder’s view shows the gallery removed', ex.ok && ex.kind === 'remove' && ex.gallery.works.length === 0 && sch.gallery.state === 'done');
check('V9 the founder’s view separates: originals (11 photographs, due in 12 months), records (due in 6 years), private repository history with its audit-branch pattern, and copies outside PlotArt’s control',
  sch.originals.state === 'scheduled' && /\(11 now\)/.test(sch.originals.what) && Math.round((Date.parse(sch.originals.due) - Date.parse(pa.ended.at)) / 86400_000) >= 365
  && sch.records.state === 'scheduled' && sch.history.state === 'manual' && sch.history.branches === 'content/plotart-aleah-v*' && sch.others.state === 'manual', JSON.stringify(pa.ended.schedule.map(x => [x.key, x.state])));
r = await call('POST', '/api/admin/artists/aleah/end', FOUNDER, { confirm_name: 'Leah Like', source: 'artist_request', reason: 'Artist asked in Studio to leave' });
check('V10 ending twice is refused (409)', r.s === 409);
await S.mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
check('V11 the daily run deletes nothing before the dates: her 11 originals and previews and all her records are still there', await objects('originals/aleah/') === 11 && await objects('previews/aleah/') === 11
  && (await db.prepare("SELECT COUNT(*) n FROM images WHERE artist_id='aleah'").first()).n === 11 && (await db.prepare("SELECT COUNT(*) n FROM enquiry_log WHERE artist_id='aleah'").first()).n === 1);
// she asks for earlier deletion of her originals (licence 6.5)
const e1 = await call('POST', '/api/admin/artists/aleah/erase-originals', FOUNDER, { confirm: true, reason: 'x' });
const e2 = await call('POST', '/api/admin/artists/abea/erase-originals', FOUNDER, { confirm: true, reason: 'Testing that an active artist cannot be erased' });
const e3 = await call('POST', '/api/admin/artists/aleah/erase-originals', FOUNDER, { confirm: true, reason: 'Artist asked by email for her originals to be deleted now' });
const leah2 = await db.prepare("SELECT * FROM artists WHERE id='aleah'").first();
check('V12 earlier deletion on request: refused without a reason, refused for an artist who has not left; then her originals, previews, works and drafts are deleted and her contact details cleared',
  e1.s === 400 && e2.s === 409 && e3.s === 200 && await objects('originals/aleah/') === 0 && await objects('previews/aleah/') === 0
  && (await db.prepare("SELECT COUNT(*) n FROM images WHERE artist_id='aleah'").first()).n === 0 && (await db.prepare("SELECT COUNT(*) n FROM artworks WHERE artist_id='aleah'").first()).n === 0
  && (await db.prepare("SELECT COUNT(*) n FROM submissions WHERE artist_id='aleah'").first()).n === 0 && leah2.email === 'ended-aleah@deleted.invalid' && leah2.bio === null, JSON.stringify([e1.s, e2.s, e3.s]));
check('V13 … while the contractual records stay: her enquiry log, publication record (versions) and Founding number', (await db.prepare("SELECT COUNT(*) n FROM enquiry_log WHERE artist_id='aleah'").first()).n === 1
  && (await db.prepare("SELECT COUNT(*) n FROM versions WHERE artist_id='aleah'").first()).n === 3 && leah2.founding_number === 1 && leah2.display_name === 'Leah Like');
check('V14 no other artist changed: every row of Bea’s, in every table, is identical, and all her originals are still stored', JSON.stringify(await artistRows(db, 'abea')) === beaBefore && await objects('originals/abea/') === beaObjects);

console.log('— retention expiry');
// Artists who left long ago (dates written directly for the test; the append-only log cannot be back-dated through Studio).
async function oldLeaver(id, endedDaysAgo, works = 2) {
  await seedPublished(db, { id, slug: id, email: `${id}@example.test`, name: `Old ${id}`, works, bucket, publishedAt: ago(endedDaysAgo + 400) });
  await db.prepare("UPDATE artists SET account_status='ended', application_ref='F25-251001-ABCDEF' WHERE id=?").bind(id).run();
  const at = ago(endedDaysAgo);
  await db.prepare("INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES (?, ?, 'ended', ?, 'founder@example.test', 'Test: left long ago', '{}')").bind('pe' + id, id, at).run();
  const del = new Date(Date.parse(at)); del.setUTCFullYear(del.getUTCFullYear() + 6);
  await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES (?, ?, ?, 'test', ?)").bind(id, at, del.toISOString(), at).run();
  await db.prepare(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, accepted_at, display_name, method, statement, created_at) VALUES (?, ?, ?, 'PA-GPIL-2026-10-29', ?, ?, 'migrated_from_artists_table', 'test', ?)`)
    .bind('acc' + id, 'evt' + id, id, ago(endedDaysAgo + 300), `Old ${id}`, ago(endedDaysAgo + 300)).run();
  await db.prepare(`INSERT INTO acceptance_corrections (id, acceptance_id, artist_id, correction_group, field, previous_value, corrected_value, reason, requested_by, corrected_by, corrected_at)
    VALUES (?, ?, ?, ?, 'display_name', ?, ?, 'Test correction long ago', 'artist', 'founder@example.test', ?)`).bind('cor' + id, 'acc' + id, id, 'cg' + id, `Old ${id}`, `Old ${id} (corrected)`, ago(endedDaysAgo + 200)).run();
  await db.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, route, introduced_at, founding, logged_by, logged_at) VALUES (?, ?, ?, 'relay', ?, 1, 'relay', ?)`).bind('l' + id, 'PA-E-OLD-' + id, id, ago(endedDaysAgo + 100), ago(endedDaysAgo + 100)).run();
}
await oldLeaver('aold13m', 400);          // left 13 months ago: originals due
await oldLeaver('aold7y', 7 * 366);       // left 7 years ago: everything due
const beforeRun = JSON.stringify(await artistRows(db, 'abea'));
await S.mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
const o13 = await artistRows(db, 'aold13m'), o7 = await artistRows(db, 'aold7y');
check('X1 12 months after leaving, the daily run deletes the originals (storage and rows), works and Studio details (including the application reference), and logs it',
  await objects('originals/aold13m/') === 0 && o13.images.length === 0 && o13.artworks.length === 0 && o13.artists[0].email === 'ended-aold13m@deleted.invalid' && o13.artists[0].application_ref === null
  && o13.participation_events.some(e => e.kind === 'originals_deleted' && e.actor === 'scheduler'));
check('X2 … but keeps that artist’s acceptance, correction, enquiry log and publication record until the six years are up', o13.agreement_acceptances.length === 1 && o13.acceptance_corrections.length === 1
  && o13.enquiry_log.length === 1 && o13.versions.length === 1 && o13.record_retention.length === 1);
check('X3 six years after leaving, every record of that artist is deleted, the artist row last', Object.values(o7).every(rows => rows.length === 0) && await objects('originals/aold7y/') === 0,
  JSON.stringify(Object.fromEntries(Object.entries(o7).map(([k, v]) => [k, v.length]))));
const au = (await db.prepare("SELECT action, artist_id FROM audit WHERE action IN ('originals_deleted','records_deleted') ORDER BY id").all()).results;
const au7 = (await db.prepare("SELECT action FROM audit WHERE artist_id='aold7y'").all()).results.map(x => x.action);
check('X3b at six years the artist’s own audit trail is deleted too, leaving one bare “records deleted” entry', au7.length === 1 && au7[0] === 'records_deleted', au7.join(','));
check('X4 the audit log keeps a bare record of each deletion (artist id and counts only)', au.some(a => a.action === 'records_deleted' && a.artist_id === 'aold7y') && au.some(a => a.action === 'originals_deleted' && a.artist_id === 'aold13m'));
check('X5 the run touched no other artist (Bea identical; Leah’s kept records unchanged in count)', JSON.stringify(await artistRows(db, 'abea')) === beforeRun
  && (await db.prepare("SELECT COUNT(*) n FROM versions WHERE artist_id='aleah'").first()).n === 3);
let gd = 'ran'; try { await db.prepare("DELETE FROM enquiry_log WHERE artist_id='abea'").run(); } catch { gd = 'refused'; }
let gd2 = 'ran'; try { await db.prepare("DELETE FROM enquiry_log WHERE artist_id='aleah'").run(); } catch { gd2 = 'refused'; }
check('X6 records of an artist who has not left, or who left inside the six years, still cannot be deleted directly', gd === 'refused' && gd2 === 'refused' && (await db.prepare("SELECT COUNT(*) n FROM enquiry_log WHERE artist_id IN ('abea','aleah')").first()).n === 2);

check('X7 another artist’s gallery still takes enquiries normally', await enquire('bea-other') === 200);

// the artist told PlotArt by email five days before the founder ended it: the schedule runs from that day (agreement 10.1)
await seedPublished(db, { id: 'amail', slug: 'mail-leaver', email: 'mail@example.test', name: 'Mail Leaver', works: 1 });
const told = new Date(Date.now() - 5 * 86400_000).toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' });
const em = await call('POST', '/api/admin/artists/amail/end', FOUNDER, { confirm_name: 'Mail Leaver', source: 'artist_request', reason: 'Artist emailed hello@ asking to leave', told_on: told });
const emi = (await call('GET', '/api/admin/participation', FOUNDER)).j.items.find(i => i.id === 'amail');
const emr = await db.prepare("SELECT ended_at FROM record_retention WHERE artist_id='amail'").first();
check('X8 an artist who told PlotArt by email: the 14 days, the 12 months and the six years run from the day they told PlotArt, not from the day the founder ended it',
  em.s === 200 && emr.ended_at === em.j.notice_at && em.j.notice_at < em.j.ended_at && Math.round((Date.parse(emi.ended.schedule[0].due) - Date.parse(em.j.notice_at)) / 86400_000) === 14
  && emi.ended.notice_at === em.j.notice_at, JSON.stringify(em.j));
const bad8 = await call('POST', '/api/admin/artists/abea/end', FOUNDER, { confirm_name: 'Bea Other', source: 'artist_request', reason: 'Artist emailed hello@ asking to leave', told_on: '2099-01-01' });
check('X9 a future “told on” date is refused and nothing changes', bad8.s === 400 && (await db.prepare("SELECT account_status FROM artists WHERE id='abea'").first()).account_status === 'active');

console.log('— a new artist who never published');
await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'New Leaver', email: NEW });
await call('GET', '/api/me', NEW);
const nid = (await db.prepare('SELECT id FROM artists WHERE email=?').bind(NEW).first()).id;
r = await call('POST', `/api/admin/artists/${nid}/end`, FOUNDER, { confirm_name: 'New Leaver', source: 'founder', reason: 'Did not go ahead with the programme' });
pa = (await call('GET', '/api/admin/participation', FOUNDER)).j.items.find(i => i.id === nid);
check('N1 ending an artist who never published queues no removal and shows “never published”', r.s === 200 && r.j.removal_queue === null && pa.ended.schedule[0].state === 'not_published'
  && (await db.prepare("SELECT COUNT(*) n FROM publish_queue WHERE artist_id=?").bind(nid).first()).n === 0);
await S.mf.dispose();

console.log('— with scheduled deletion OFF (the default until switched on at release)');
const O = await start({ port: 8842 });
const ocall = mk(O), obucket = await O.mf.getR2Bucket('IMAGES', 'studio');
await seedPublished(O.db, { id: 'aoff', slug: 'aoff', email: 'off@example.test', name: 'Off Artist', works: 2, bucket: obucket, publishedAt: ago(800) });
await O.db.prepare("UPDATE artists SET account_status='ended' WHERE id='aoff'").run();
await O.db.prepare("INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES ('peoff', 'aoff', 'ended', ?, 'founder@example.test', 'Test', '{}')").bind(ago(400)).run();
await O.db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('aoff', ?, ?, 'test', ?)").bind(ago(400), new Date(Date.now() + 5 * 365 * 86400_000).toISOString(), ago(400)).run();
await O.mf.getWorker('studio').then(w => w.scheduled({ cron: '23 3 * * *' }));
const off = (await ocall('GET', '/api/admin/participation', FOUNDER)).j, offItem = off.items.find(i => i.id === 'aoff');
const offImgs = (await O.db.prepare("SELECT COUNT(*) n FROM images WHERE artist_id='aoff'").first()).n;
const offErase = await ocall('POST', '/api/admin/artists/aoff/erase-originals', FOUNDER, { confirm: true, reason: 'Artist asked by email for deletion' });
check('F1 with scheduled deletion off the daily run deletes nothing and the founder sees “due, but deletion is switched off”; an artist’s request for earlier deletion can still be honoured by the founder’s explicit action',
  !off.deletion_enabled && offItem.ended.schedule.find(x => x.key === 'originals').state === 'due_job_off' && offImgs === 2 && offErase.s === 200
  && (await obucket.list({ prefix: 'originals/aoff/' })).objects.length === 0, JSON.stringify([offImgs, offErase.s]));
await O.mf.dispose();

console.log(`\nLEAVING PLOTART · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exit(results.every(Boolean) ? 0 : 1);
