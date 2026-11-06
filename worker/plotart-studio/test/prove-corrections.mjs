// PROVE · corrections to acceptance records (development, 6 Nov 2026). Local only, synthetic artists.
//   node test/prove-corrections.mjs
import { start, token, FOUNDER } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
import { seedPublished } from './seed.mjs';
import { readFileSync } from 'node:fs';
import { statements } from './sql.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const { mf, url, db } = await start({ port: 8843 });
const call = async (method, path, email, body) => { const r = await mf.dispatchFetch(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) }); return { s: r.status, j: await r.json().catch(() => null) }; };
const rows = id => db.prepare('SELECT * FROM agreement_acceptances WHERE artist_id = ? ORDER BY doc_id').bind(id).all().then(x => x.results);
const tryRun = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return 'ran'; } catch (e) { return 'refused'; } };

console.log('PROVE · acceptance record corrections');
const A = 'aisling@example.test';
const aid = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Aisling Sample', email: A, founding: true })).j.id;
await acceptAgreement(mf, url, A, { legal_name: 'Aisling Ní Shamplah' });   // mistyped on purpose
// an existing artist with the earlier label only (carried over by migration 0005 section 6)
await seedPublished(db, { id: 'aleah', slug: 'leah-like', email: 'leah@example.test', name: 'Leah Like' });
const mig = readFileSync(new URL('../migrations/0005_agreements_and_enquiry_log.sql', import.meta.url), 'utf8').split('-- 6 · Carry across')[1].split('\n-- 6b ·')[0];
await db.prepare(statements(mig.slice(mig.indexOf('INSERT INTO')))[0]).run();
const before = await rows(aid), leahBefore = await rows('aleah');
const ev = before[0].event_id;
const base = { event_id: ev, field: 'legal_name', value: 'Aisling Ní Shamplach', reason: 'The artist emailed: one letter of her legal name was mistyped', requested_by: 'artist', confirm: true };
const bad = await Promise.all([
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, event_id: 'evt-nope' }),
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, field: 'accepted_at', value: '2020-01-01T00:00:00Z' }),
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, field: 'doc_sha256', value: 'a'.repeat(64) }),
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, reason: 'typo' }),
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, requested_by: 'someone' }),
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, confirm: false }),
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, value: 'Aisling Ní Shamplah' }),
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, value: '<b>x</b>' }),
  call('POST', '/api/admin/artists/aleah/acceptance-corrections', FOUNDER, { ...base, event_id: leahBefore[0].event_id }),
  call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, A, base),
]);
check('C1 refused: unknown acceptance (404), the time or fingerprint as a field, no real reason, unknown requester, unconfirmed, no change, unsafe text, a legal name on a label-only record; an artist cannot correct (403)',
  bad.map(b => b.s).join() === '404,400,400,400,400,400,400,400,400,403', bad.map(b => b.s + ':' + (b.j && b.j.error || '').slice(0, 30)).join(' | '));
const ok = await call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, base);
const after = await rows(aid), corr = (await db.prepare('SELECT * FROM acceptance_corrections WHERE artist_id = ? ORDER BY acceptance_id').bind(aid).all()).results;
check('C2 the correction is two separate rows (one per document of that acceptance), linked to each, with the same group, a time and the reason', ok.s === 200 && corr.length === 2
  && corr.every(c => c.correction_group === ok.j.correction_group && c.field === 'legal_name' && c.previous_value === 'Aisling Ní Shamplah' && c.corrected_value === 'Aisling Ní Shamplach'
    && c.reason === base.reason && c.requested_by === 'artist' && c.corrected_by === FOUNDER && c.corrected_at) && new Set(corr.map(c => c.acceptance_id)).size === 2, JSON.stringify(ok.j));
check('C3 the original acceptance rows are byte-for-byte unchanged: version, fingerprints, acceptance time, statement and the name as typed', JSON.stringify(after) === JSON.stringify(before));
const ag = (await call('GET', '/api/agreement', A)).j;
check('C4 no new acceptance: still exactly two rows, one event, and the artist is still “accepted” at the original time',
  after.length === 2 && new Set(after.map(r => r.event_id)).size === 1 && ag.accepted && ag.accepted_at === before[0].accepted_at);
check('C5 the artist’s record shows the corrected legal name and that it was corrected', ag.history.every(h => h.legal_name === 'Aisling Ní Shamplach' && h.corrections.length === 1));
const fh = (await call('GET', `/api/admin/artists/${aid}/agreement`, FOUNDER)).j.agreement.history;
check('C6 the founder sees both: the value as recorded and the corrected value, with the correction history', fh.every(h => h.original.legal_name === 'Aisling Ní Shamplah' && h.legal_name === 'Aisling Ní Shamplach' && h.corrections.length === 1));
const rm = await call('POST', `/api/admin/artists/${aid}/acceptance-corrections`, FOUNDER, { ...base, value: '', reason: 'The artist asked for her legal name not to be held at all' });
const fh2 = (await call('GET', `/api/admin/artists/${aid}/agreement`, FOUNDER)).j.agreement.history;
check('C7 a later correction can remove a legal name; corrections stack in order and the original still shows', rm.s === 200 && fh2.every(h => h.legal_name === null && h.corrections.length === 2 && h.original.legal_name === 'Aisling Ní Shamplah'));
const lc = await call('POST', '/api/admin/artists/aleah/acceptance-corrections', FOUNDER, { event_id: leahBefore[0].event_id, field: 'display_name', value: 'Leah L. Like', reason: 'Professional name as she now works under it', requested_by: 'artist', confirm: true });
check('C8 a label-only (carried-over) record can have its professional name corrected, and stays label only and unchanged itself', lc.s === 200 && JSON.stringify(await rows('aleah')) === JSON.stringify(leahBefore));
const now = new Date().toISOString();
const d = await Promise.all([
  tryRun(`INSERT INTO acceptance_corrections (id, acceptance_id, artist_id, correction_group, field, previous_value, corrected_value, reason, requested_by, corrected_by, corrected_at) VALUES ('x1', ?, ?, 'g1', 'accepted_at', NULL, '2020-01-01', 'Trying to change the time', 'founder', 'f', ?)`, before[0].id, aid, now),
  tryRun(`INSERT INTO acceptance_corrections (id, acceptance_id, artist_id, correction_group, field, previous_value, corrected_value, reason, requested_by, corrected_by, corrected_at) VALUES ('x2', ?, 'aleah', 'g2', 'display_name', NULL, 'X', 'Pointing at another artist', 'founder', 'f', ?)`, before[0].id, now),
  tryRun(`INSERT INTO acceptance_corrections (id, acceptance_id, artist_id, correction_group, field, previous_value, corrected_value, reason, requested_by, corrected_by, corrected_at) VALUES ('x3', ?, 'aleah', 'g3', 'legal_name', NULL, 'Invented', 'A legal name on a label-only record', 'founder', 'f', ?)`, leahBefore[0].id, now),
  tryRun(`INSERT INTO acceptance_corrections (id, acceptance_id, artist_id, correction_group, field, previous_value, corrected_value, reason, requested_by, corrected_by, corrected_at) VALUES ('x4', ?, ?, 'g4', 'legal_name', NULL, 'Back-dated', 'Dated before the acceptance itself', 'founder', 'f', '2020-01-01T00:00:00Z')`, before[0].id, aid),
  tryRun("UPDATE acceptance_corrections SET corrected_value = 'Changed' WHERE artist_id = ?", aid),
  tryRun('DELETE FROM acceptance_corrections WHERE artist_id = ?', aid),
]);
check('C9 the database itself refuses: correcting the time (or any field other than names and address), pointing at another artist’s acceptance, a legal name on a label-only record, a back-dated correction, editing or deleting a correction',
  d.every(x => x === 'refused'), d.join(' '));
const au = (await db.prepare("SELECT detail FROM audit WHERE action='acceptance_corrected'").all()).results;
check('C10 each correction is in the audit log without copying the names themselves', au.length === 3 && au.every(a => !/Shampl|Leah L/.test(a.detail)));
console.log(`\nACCEPTANCE CORRECTIONS · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose(); process.exit(results.every(Boolean) ? 0 : 1);
