// PROVE · Founding Artist Agreement acceptance in PlotArt Studio (development, 6 Nov 2026). Local only: Miniflare D1/R2,
// synthetic artists. Covers the documents and their fingerprints, one tick for both texts, the immutable record, the
// existing published artist (Leah-shaped: 11 works, earlier licence label only), the invited artist (Nick-shaped), the
// founder's Publish rule, the Review Desk record, the pipeline licence, and Studio before migration 0005.
//   node test/prove-agreement.mjs
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
import { snapshot } from '../src/lib.js';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { statements } from './sql.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const sha = b => createHash('sha256').update(b).digest('hex');
const HERE = new URL('..', import.meta.url).pathname;
const FP = JSON.parse(readFileSync(HERE + 'agreements/issued/fingerprints.json', 'utf8')).documents;
const FAA = 'PA-FAA-2026-11', GPIL = 'PA-GPIL-2026-11', LEGACY = 'PA-GPIL-2026-10-29';

const { mf, url, db } = await start({ port: 8831 });
const H = (email, extra = {}) => ({ ...(email ? { 'Cf-Access-Jwt-Assertion': token(email) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json', ...extra });
const call = async (method, path, email, body) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: H(email), body: body === undefined ? undefined : JSON.stringify(body) });
  const t = Buffer.from(await r.arrayBuffer()); let j; try { j = JSON.parse(t.toString('utf8')); } catch { j = null; }
  return { s: r.status, j, raw: t, h: r.headers };
};
const pipe = async (method, path) => { const r = await mf.dispatchFetch(url + path, { method, headers: { Authorization: `Bearer ${PIPELINE_TOKEN}` } }); return { s: r.status, j: await r.json().catch(() => null) }; };
const q1 = (sql, ...b) => db.prepare(sql).bind(...b).first();
const qa = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
const tryRun = async (sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return 'ran'; } catch (e) { return 'refused: ' + String(e.message).slice(0, 90); } };
const T0 = '2026-11-05T17:05:00.000Z';

/* ---------------------------------------------------------------- seed an existing published artist, as production holds */
async function seedPublished({ id, slug, email, name, works = 11, migrated = true }) {
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, founding_number, practice, medium, county, county_public, bio, account_status,
    licence_version, licence_accepted_at, first_published_at, created_at, updated_at) VALUES (?,?,?,?,1,?,?,?,?,1,?, 'active', ?,?,?,?,?)`)
    .bind(id, slug, email, name, works === 11 ? 1 : 2, 'Painter', 'painting', 'Dublin', `${name} is a synthetic test artist standing in for an artist who is already published.`, LEGACY, '2026-11-05T16:40:00.000Z', T0, '2026-10-30T10:00:00.000Z', T0).run();
  for (let i = 1; i <= works; i++) {
    await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at)
      VALUES (?,?,?,?,2026,'Oil on board',40,50,?, 'available', ?, ?, 'none', 0, ?, ?)`).bind(`w${id}${i}`, id, `work-${i}`, `Work ${i}`, 500 + i * 10, `Synthetic published work number ${i}.`, i, T0, T0).run();
    await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
      VALUES (?,?,?,'main',?,?,1000,2400,1800,'jpeg',?, 'self', '{"blocks":[],"warns":[]}', 0, ?)`).bind(`i${id}${i}`, id, `w${id}${i}`, `orig/${id}/${i}.jpg`, sha(`${id}-${i}`), `Work ${i}, a test painting`, T0).run();
  }
  const a = await q1('SELECT * FROM artists WHERE id=?', id), w = await qa('SELECT * FROM artworks WHERE artist_id=?', id), im = await qa('SELECT * FROM images WHERE artist_id=?', id);
  await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?, 1, ?, 'seed', ?)").bind(id, JSON.stringify(snapshot(a, w, im)), T0).run();
  await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?, ?, 1, 'reviewed', 'published', ?, ?)").bind(`q${id}seed`, id, T0, T0).run();
  if (migrated) {   // migration 0005 section 6, exactly as written, for this artist only
    const sql = readFileSync(HERE + 'migrations/0005_agreements_and_enquiry_log.sql', 'utf8').split('-- 6 · Carry across')[1].split('\n-- 6b ·')[0];
    const ins = statements(sql.slice(sql.indexOf('INSERT INTO')))[0].replace("WHERE a.licence_version = 'PA-GPIL-2026-10-29'", `WHERE a.id = '${id}' AND a.licence_version = 'PA-GPIL-2026-10-29'`);
    await db.prepare(ins).run();
  }
}

console.log('PROVE · Founding Artist Agreement\n— the documents');
const LEAH = 'leah-like@example.test', NICK = 'nick-like@example.test', NEW = 'niamh-new@example.test', OTHER = 'other@example.test', PLAIN = 'plain@example.test';
await seedPublished({ id: 'aleah', slug: 'leah-like', email: LEAH, name: 'Leah Like' });
let r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Niamh New', email: NEW, founding: true }); const NID = r.j.id;
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Nick Like', email: NICK, founding: true }); const KID = r.j.id;
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Pat Plain', email: PLAIN, founding: false }); const PID = r.j.id;
const docs = {};
for (const id of [FAA, GPIL]) for (const k of ['html', 'pdf']) docs[`${id}.${k}`] = await call('GET', `/agreements/${id}.${k}`, NEW);
check('A1 both documents are served in full to a signed-in artist, as HTML and PDF, byte-for-byte matching their recorded fingerprints',
  [FAA, GPIL].every(id => docs[`${id}.html`].s === 200 && sha(docs[`${id}.html`].raw) === FP[id].html_sha256 && docs[`${id}.pdf`].s === 200 && sha(docs[`${id}.pdf`].raw) === FP[id].pdf_sha256
    && docs[`${id}.pdf`].h.get('content-disposition').startsWith('attachment') && docs[`${id}.html`].h.get('x-document-sha256') === FP[id].html_sha256));
const fhtml = await call('GET', `/agreements/${FAA}.html`, FOUNDER), anon = await call('GET', `/agreements/${FAA}.pdf`), unk = await call('GET', '/agreements/PA-FAA-2099-01.html', NEW), leg = await call('GET', `/agreements/${LEGACY}.html`, NEW);
check('A2 the founder can read them too; signed-out requests are refused; an unknown identifier or the earlier label-only licence has no document (404)',
  fhtml.s === 200 && anon.s === 401 && unk.s === 404 && leg.s === 404, `${fhtml.s} ${anon.s} ${unk.s} ${leg.s}`);
const src = readFileSync(HERE + 'agreements/source/PA-FAA-2026-11.cjs', 'utf8'), nums = [...src.matchAll(/\['c', '(\d+\.\d+)'/g)].map(m => m[1]);
const fText = docs[`${FAA}.html`].raw.toString('utf8');
check(`A3 the agreement page carries every clause of the approved text (${nums.length} clauses), the acceptance statement, and no review or draft wording`,
  nums.length > 60 && nums.every(n => fText.includes(`id="c${n}"`)) && fText.includes('I have read and accept the PlotArt Founding Artist Agreement PA-FAA-2026-11, including the Gallery Publication and Image Licence PA-GPIL-2026-11.')
  && !/PROPOSED|NOT YET ISSUED|founder approval/i.test(fText));
const pdfText = (await import('node:child_process')).execFileSync('pdftotext', ['-', '-'], { input: docs[`${FAA}.pdf`].raw }).toString();
check('A4 the PDF is the same text (no review note), 7 pages', /No compulsory fees, ever/.test(pdfText) && !/PROPOSED|NOT YET ISSUED/.test(pdfText) && /Page 7 of 7/.test(pdfText));

console.log('— a new artist: nothing is accepted until they tick, and their first publication waits for it');
let me = (await call('GET', '/api/me', NEW)).j;
check('N1 a new artist sees the agreement as not accepted, required for both documents, with the exact one-tick statement',
  me.status.agreement.installed && !me.status.agreement.accepted && me.status.agreement.status === 'not_accepted' && JSON.stringify(me.status.agreement.required) === JSON.stringify([FAA, GPIL])
  && me.status.agreement.statement === 'I have read and accept the PlotArt Founding Artist Agreement PA-FAA-2026-11, including the Gallery Publication and Image Licence PA-GPIL-2026-11.');
const agItem = me.status.checklist.find(i => i.area === 'agreement');
check('N2 it is an item on their submission checklist (shown first, under “Agreement”, linking to the agreement page)', agItem && /Founding Artist Agreement/.test(agItem.text) && me.status.checklist.filter(i => i.area === 'agreement').length === 1);
// make the new artist's gallery complete (one work) so the agreement is the only thing missing
await call('PUT', '/api/me/profile', NEW, { medium: 'painting', bio: 'Niamh New is a synthetic test artist used to prove the agreement step in PlotArt Studio.' });
const nw = (await call('POST', '/api/artworks', NEW)).j.id;
await call('PUT', `/api/artworks/${nw}`, NEW, { title: 'First Light', medium: 'Oil', h_cm: 30, w_cm: 40, ai_involvement: 'none' });
await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
  VALUES ('inew1', ?, ?, 'main', 'orig/new/1.jpg', ?, 1000, 2400, 1800, 'jpeg', 'First Light, a test painting', 'self', '{"blocks":[],"warns":[]}', 0, ?)`).bind(NID, nw, sha('new-1'), T0).run();
r = await call('POST', '/api/submit', NEW, { accept_licence: true });
check('N3 submitting without accepting is refused, even with the old “accept_licence” flag (nothing is accepted on submission any more)',
  r.s === 422 && r.j.problems.length === 1 && /Founding Artist Agreement/.test(r.j.problems[0]) && (await qa('SELECT * FROM agreement_acceptances WHERE artist_id=?', NID)).length === 0
  && (await q1('SELECT licence_version FROM artists WHERE id=?', NID)).licence_version === null, JSON.stringify(r.j));
const bad1 = await acceptAgreement(mf, url, NEW, { tamper: true });
const bad2 = await acceptAgreement(mf, url, NEW, { statement: 'I accept.' });
const bad3 = await call('POST', '/api/agreement/accept', NEW, { accept: false, documents: bad1.documents, statement: bad1.statement });
const bad4 = await acceptAgreement(mf, url, NEW, { legal_name: '<b>x</b>' });
const bad5 = await acceptAgreement(mf, url, NEW, { legal_name: 'N' });
const bad6 = await call('POST', '/api/agreement/accept', NEW, { accept: true, documents: { [FAA]: FP[FAA].html_sha256 }, statement: bad1.statement });
check('N4 refused: a text that differs from what Studio serves (409), a different statement (409), no tick (400), an unsafe or too-short legal name (400), only one of the two documents (409)',
  bad1.s === 409 && bad2.s === 409 && bad3.s === 400 && bad4.s === 400 && bad5.s === 400 && bad6.s === 409 && (await qa('SELECT * FROM agreement_acceptances WHERE artist_id=?', NID)).length === 0,
  [bad1.s, bad2.s, bad3.s, bad4.s, bad5.s, bad6.s].join(' '));
const before = Date.now();
const ok = await acceptAgreement(mf, url, NEW, { legal_name: '  Niamh Ní Shintéiseach  ' });
const rows = await qa('SELECT * FROM agreement_acceptances WHERE artist_id=? ORDER BY doc_id', NID);
check('N5 one tick records ONE event with TWO rows (agreement and licence), each with its exact fingerprints, the time, the signed-in address, both names and the method',
  ok.s === 200 && rows.length === 2 && rows[0].event_id === rows[1].event_id && rows.map(x => x.doc_id).join() === [FAA, GPIL].join()
  && rows.every(x => x.doc_sha256 === FP[x.doc_id].html_sha256 && x.pdf_sha256 === FP[x.doc_id].pdf_sha256 && x.account_email === NEW && x.display_name === 'Niamh New'
    && x.legal_name === 'Niamh Ní Shintéiseach' && x.method === 'studio_checkbox' && x.statement === ok.statement && Date.parse(x.accepted_at) >= before - 1000), JSON.stringify(rows).slice(0, 300));
const aud = await qa("SELECT * FROM audit WHERE action='agreement_accepted' AND artist_id=?", NID);
check('N6 the audit log records the acceptance (event and documents) without copying the legal name', aud.length === 1 && /evt/.test(aud[0].detail) && !/Shint/.test(aud[0].detail));
const again = await acceptAgreement(mf, url, NEW);
check('N7 accepting again is refused (409) and adds nothing', again.s === 409 && (await qa('SELECT * FROM agreement_acceptances WHERE artist_id=?', NID)).length === 2);
const ag = (await call('GET', '/api/agreement', NEW)).j;
check('N8 the artist’s Agreement page shows the record: both documents with fingerprints, date, names, account; no founding year yet (not published)',
  ag.accepted && ag.history.length === 2 && ag.history.every(h => h.doc_sha256) && ag.founding_year === null && ag.documents.length === 2);
r = await call('POST', '/api/submit', NEW, {});
check('N9 after accepting, the first submission goes through (full review); the old licence columns stay empty', r.s === 200 && r.j.tier === 'full' && (await q1('SELECT licence_version FROM artists WHERE id=?', NID)).licence_version === null);
const nsid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(s => s.artist_id === NID).id;
await call('POST', `/api/admin/submissions/${nsid}/decision`, FOUNDER, { decision: 'approve' });
const nq = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === NID);
r = await call('POST', `/api/admin/queue/${nq.id}/publish`, FOUNDER, {});
const ex = await pipe('POST', `/api/pipeline/export/${nq.id}`);
check('N10 the founder can publish the first gallery; the export carries licence PA-GPIL-2026-11 and its acceptance time', r.s === 200 && ex.s === 200
  && ex.j.gallery.publication.licence_version === GPIL && ex.j.gallery.publication.licence_accepted_at === rows[0].accepted_at, JSON.stringify(ex.j && ex.j.gallery && ex.j.gallery.publication));

console.log('— an invited artist who has not signed in (Nick-shaped)');
const nickBefore = await q1('SELECT account_status FROM artists WHERE id=?', KID);
me = (await call('GET', '/api/me', NICK)).j;
check('K1 an invited artist signs in normally; the agreement is waiting, nothing is recorded for them', nickBefore.account_status === 'invited' && me.artist.account_status === 'active'
  && me.status.agreement.status === 'not_accepted' && (await qa('SELECT * FROM agreement_acceptances WHERE artist_id=?', KID)).length === 0);
// a reviewed version reaching the founder without an acceptance (e.g. queued by an earlier Studio): a first publication is blocked
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?, 1, ?, 'test', ?)").bind(KID, JSON.stringify({ artist: { slug: 'nick-like' }, works: [] }), T0).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qnick1', ?, 1, 'reviewed', 'awaiting_founder', ?, ?)").bind(KID, T0, T0).run();
const kp = await call('POST', '/api/admin/queue/qnick1/publish', FOUNDER, { confirm_without_agreement: true });
check('K2 the founder cannot publish a NEW artist’s gallery for the first time without their acceptance, even when confirming (409)',
  kp.s === 409 && !kp.j.needs_confirmation && /first time/.test(kp.j.error) && (await q1("SELECT status FROM publish_queue WHERE id='qnick1'")).status === 'awaiting_founder', JSON.stringify(kp.j));

console.log('— an existing published artist (Leah-shaped: 11 works, the earlier licence label only)');
const leahRow0 = await q1("SELECT * FROM artists WHERE id='aleah'");
const leahMig0 = await qa("SELECT * FROM agreement_acceptances WHERE artist_id='aleah'");
me = (await call('GET', '/api/me', LEAH)).j;
check('L1 her gallery is live with 11 works; Studio shows “earlier licence only”, no agreement item until she has something to submit for review',
  me.status.state === 'live' && me.status.counts.works === 11 && me.status.agreement.status === 'legacy_licence_only' && me.status.agreement.legacy.version === LEGACY
  && me.status.agreement.legacy.migrated && !me.status.checklist.some(i => i.area === 'agreement'));
check('L2 her earlier acceptance is held exactly as recorded: label only, no text, no fingerprint, no email, same date', leahMig0.length === 1 && leahMig0[0].doc_id === LEGACY
  && leahMig0[0].method === 'migrated_from_artists_table' && leahMig0[0].doc_sha256 === null && leahMig0[0].account_email === null && leahMig0[0].accepted_at === leahRow0.licence_accepted_at);
const lw = (await call('GET', '/api/artworks', LEAH)).j.works;
const av = await call('POST', `/api/artworks/${lw[0].id}/availability`, LEAH, { availability: 'sold' });
const wd = await call('POST', `/api/artworks/${lw[1].id}/archive`, LEAH, { archived: true });
const ed = await call('PUT', `/api/artworks/${lw[2].id}`, LEAH, { price_eur: 950, description: 'Synthetic published work, description corrected.' });
const pr = await call('PUT', '/api/me/profile', LEAH, { county_public: false });
check('L3 without accepting she can still mark a work sold, withdraw a work, edit prices and details, and change her profile', av.s === 200 && av.j.instant_version && wd.s === 200 && wd.j.instant_version && ed.s === 200 && pr.s === 200,
  [av.s, wd.s, ed.s, pr.s].join(' '));
const liq = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.filter(x => x.artist_id === 'aleah' && x.kind === 'instant');
const ip = await call('POST', `/api/admin/queue/${liq[liq.length - 1].id}/publish`, FOUNDER, {});
const iex = await pipe('POST', `/api/pipeline/export/${liq[liq.length - 1].id}`);
check('L4 her sold / withdrawn updates publish without any agreement question, and still carry her earlier licence label', ip.s === 200 && iex.s === 200 && iex.j.gallery.publication.licence_version === LEGACY
  && iex.j.gallery.works.length === 10, JSON.stringify(iex.j && iex.j.gallery && iex.j.gallery.publication));
const ls = await call('POST', '/api/submit', LEAH, { note: 'Price correction' });
check('L5 a quick-check submission (prices and details) goes through without the new agreement', ls.s === 200 && ls.j.tier === 'light', JSON.stringify(ls.j));
const lnw = (await call('POST', '/api/artworks', LEAH)).j.id;
await call('PUT', `/api/artworks/${lnw}`, LEAH, { title: 'Work 12', medium: 'Oil', h_cm: 30, w_cm: 40, ai_involvement: 'none' });
await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
  VALUES ('ileah12', 'aleah', ?, 'main', 'orig/aleah/12.jpg', ?, 1000, 2400, 1800, 'jpeg', 'Work 12, a test painting', 'self', '{"blocks":[],"warns":[]}', 0, ?)`).bind(lnw, sha('leah-12'), T0).run();
me = (await call('GET', '/api/me', LEAH)).j;
const lfull = await call('POST', '/api/submit', LEAH, {});
check('L6 a NEW artwork (full review) asks for the agreement: it is on her checklist and the submission is refused until she accepts', me.status.tier === 'full'
  && me.status.checklist.some(i => i.area === 'agreement') && lfull.s === 422 && lfull.j.problems.some(p => /Founding Artist Agreement/.test(p)), JSON.stringify(lfull.j));
// the founder approves the quick check; Publish warns (she is published but has not accepted) and goes ahead only when confirmed
const lsid = (await qa("SELECT id FROM submissions WHERE artist_id='aleah' AND status='pending'"))[0].id;
await call('POST', `/api/admin/submissions/${lsid}/decision`, FOUNDER, { decision: 'approve' });
const lq = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === 'aleah' && x.kind === 'reviewed' && x.status === 'awaiting_founder');
const w1 = await call('POST', `/api/admin/queue/${lq.id}/publish`, FOUNDER, {});
const w2 = await call('POST', `/api/admin/queue/${lq.id}/publish`, FOUNDER, { confirm_without_agreement: true });
const pubAudit = await qa("SELECT detail FROM audit WHERE action='publish' AND artist_id='aleah' ORDER BY id DESC LIMIT 1");
check('L7 Publish for an already-published artist without the agreement asks the founder to confirm (409 + warning), then publishes and notes it in the audit',
  w1.s === 409 && w1.j.needs_confirmation && /hasn’t accepted/.test(w1.j.error) && w2.s === 200 && /without_current_agreement/.test(pubAudit[0].detail), JSON.stringify(w1.j));
check('L8 her gallery is never unpublished or blocked: no removal was queued, her account is active, her sign-in works',
  (await qa("SELECT * FROM publish_queue WHERE artist_id='aleah' AND kind='remove'")).length === 0 && (await q1("SELECT account_status FROM artists WHERE id='aleah'")).account_status === 'active'
  && (await call('GET', '/api/me', LEAH)).s === 200);
const lacc = await acceptAgreement(mf, url, LEAH);
const leahAll = await qa("SELECT * FROM agreement_acceptances WHERE artist_id='aleah' ORDER BY accepted_at");
const leahRow1 = await q1("SELECT * FROM artists WHERE id='aleah'");
check('L9 when she accepts, two new rows are added beside her earlier record, which is unchanged byte for byte; her artist row’s licence columns are untouched',
  lacc.s === 200 && leahAll.length === 3 && JSON.stringify(leahAll.find(x => x.method === 'migrated_from_artists_table')) === JSON.stringify(leahMig0[0])
  && leahRow1.licence_version === leahRow0.licence_version && leahRow1.licence_accepted_at === leahRow0.licence_accepted_at, JSON.stringify(lacc.j));
me = (await call('GET', '/api/me', LEAH)).j;
check('L10 her founding year is shown from her first publication (5 Nov 2026 to 4 Nov 2027, Irish dates), and her new artwork can now be submitted',
  me.status.agreement.founding_year.start === '2026-11-05' && me.status.agreement.founding_year.end === '2027-11-04' && (await call('POST', '/api/submit', LEAH, {})).s === 200);
const lexp = await pipe('POST', `/api/pipeline/export/${lq.id}`);
check('L11 from now on her publications carry PA-GPIL-2026-11 (the newest acceptance)', lexp.s === 200 && lexp.j.gallery.publication.licence_version === GPIL);

console.log('— an existing artist whose earlier record has NOT been carried over');
await seedPublished({ id: 'aother', slug: 'other-like', email: OTHER, name: 'Other Like', works: 2, migrated: false });
const oa = await acceptAgreement(mf, url, OTHER);
check('L12 accepting is refused (503) until migration 0005 has carried her earlier licence record across, so nothing new can be written beside a missing record',
  oa.s === 503 && (await qa("SELECT * FROM agreement_acceptances WHERE artist_id='aother'")).length === 0, JSON.stringify(oa.j));

console.log('— an artist who is not a Founding Artist');
const pa = await call('GET', '/api/agreement', PLAIN);
const pacc = await acceptAgreement(mf, url, PLAIN);
check('P1 a non-Founding artist sees and accepts the licence alone (one document, its own statement)', pa.j.documents.length === 1 && pa.j.documents[0].id === GPIL
  && pa.j.statement === 'I have read and accept the PlotArt Gallery Publication and Image Licence PA-GPIL-2026-11.' && pacc.s === 200 && (await qa('SELECT * FROM agreement_acceptances WHERE artist_id=?', PID)).length === 1);

console.log('— the Review Desk');
const ov = (await call('GET', '/api/admin/overview', FOUNDER)).j;
const st = Object.fromEntries(ov.artists.map(a => [a.id, a.agreement.status]));
const lh = (await call('GET', '/api/admin/artists/aleah/agreement', FOUNDER)).j;
check('R1 the desk shows each artist’s agreement status (accepted / earlier licence only / not accepted)',
  st[NID] === 'accepted' && st.aleah === 'accepted' && st.aother === 'legacy_licence_only' && st[KID] === 'not_accepted' && ov.agreement_installed === true, JSON.stringify(st));
check('R2 the founder sees the full history (earlier label + both new rows, with fingerprints, address and method) and the founding year',
  lh.agreement.history.length === 3 && lh.agreement.history.filter(h => h.method === 'studio_checkbox').every(h => h.account_email === LEAH && h.doc_sha256) && lh.agreement.founding_year.end === '2027-11-04');
const art = await call('GET', '/api/admin/artists/aleah/agreement', LEAH), art2 = await call('GET', '/api/agreement', FOUNDER), cross = await call('GET', '/api/admin/enquiry-log', NEW);
check('R3 artists cannot read the founder’s records (403); the founder has no artist agreement page', art.s === 403 && art2.s === 403 && cross.s === 403, `${art.s} ${art2.s} ${cross.s}`);

console.log('— the record cannot be changed');
const u1 = await tryRun("UPDATE agreement_acceptances SET legal_name='Changed' WHERE artist_id=?", NID);
const u2 = await tryRun('DELETE FROM agreement_acceptances WHERE artist_id=?', NID);
const u3 = await tryRun(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at)
  VALUES ('x1','e1',?, ?, ?, ?, ?, 'x@example.test', 'X', 'studio_checkbox', 'I accept', ?)`, KID, FAA, 'f'.repeat(64), FP[FAA].pdf_sha256, new Date().toISOString(), new Date().toISOString());
const u4 = await tryRun(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, accepted_at, display_name, method, statement, created_at)
  VALUES ('x2','e2',?, ?, '2026-11-01T00:00:00Z', 'Nick Like', 'migrated_from_artists_table', 'invented', '2026-11-06T00:00:00Z')`, KID, FAA);
const u5 = await tryRun(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at)
  VALUES ('x3','e3',?, ?, ?, ?, '2026-10-01T00:00:00Z', ?, 'Nick Like', 'studio_checkbox', 'I accept', '2026-10-01T00:00:00Z')`, KID, FAA, FP[FAA].html_sha256, FP[FAA].pdf_sha256, NICK);
const u6 = await tryRun("UPDATE agreement_documents SET html_sha256=? WHERE doc_id=?", 'a'.repeat(64), FAA);
const u7 = await tryRun("DELETE FROM agreement_documents WHERE doc_id=?", LEGACY);
check('I1 acceptances cannot be edited or deleted; an acceptance with a wrong fingerprint, a migrated (retrospective) agreement acceptance, or one dated before the text took effect is refused; installed documents cannot be changed or removed',
  [u1, u2, u3, u4, u5, u6, u7].every(x => x.startsWith('refused')), [u1, u2, u3, u4, u5, u6, u7].join(' | '));

console.log('— retention (GDPR) still possible, and only when the retention period has ended');
const ry = await tryRun("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES (?, '2026-11-06T00:00:00Z', '2027-01-01T00:00:00Z', 'test', '2026-11-06T00:00:00Z')", PID);
const r1 = await tryRun("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES (?, '2026-11-06T00:00:00Z', '2032-11-06T00:00:00Z', 'test', '2026-11-06T00:00:00Z')", PID);
const r2 = await tryRun('DELETE FROM agreement_acceptances WHERE artist_id=?', PID);
// an artist whose agreement ended more than six years ago (dates in the past, written directly for the test)
await db.prepare("INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('aold', 'old-like', 'old@example.test', 'Old Like', 0, 'ended', '2018-01-01T00:00:00Z', '2018-01-01T00:00:00Z')").run();
await db.prepare(`INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, accepted_at, display_name, method, statement, created_at)
  VALUES ('acc-old', 'evt-old', 'aold', ?, '2018-01-01T00:00:00Z', 'Old Like', 'migrated_from_artists_table', 'test', '2018-01-01T00:00:00Z')`).bind(LEGACY).run();
await db.prepare("INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES ('aold', '2019-01-01T00:00:00Z', '2025-01-01T00:00:00Z', 'test', '2019-01-01T00:00:00Z')").run();
const r3 = await tryRun("DELETE FROM record_retention WHERE artist_id='aold'");
const r4 = await tryRun("DELETE FROM agreement_acceptances WHERE artist_id='aold'");
const r5 = await tryRun("DELETE FROM record_retention WHERE artist_id='aold'");
check('G1 a retention date shorter than six years after the end is refused; inside the period nothing can be deleted; after it the records can be deleted, then the retention row itself',
  ry.startsWith('refused') && r1 === 'ran' && r2.startsWith('refused') && r3.startsWith('refused') && r4 === 'ran' && r5 === 'ran', [ry, r1, r2, r3, r4, r5].join(' | '));

console.log('— Studio before migration 0005 (the tables do not exist yet)');
const pre = await start({ port: 8832 });
const pdb = pre.db;
for (const s of ['agreement_acceptances_valid', 'agreement_acceptances_no_update', 'agreement_acceptances_no_delete', 'enquiry_log_no_update', 'enquiry_log_no_delete', 'record_retention_no_update', 'record_retention_no_delete', 'agreement_documents_no_update', 'agreement_documents_no_delete'])
  await pdb.prepare(`DROP TRIGGER ${s}`).run();
for (const t of ['agreement_acceptances', 'enquiry_log', 'record_retention', 'agreement_documents']) await pdb.prepare(`DROP TABLE ${t}`).run();
const pcall = async (method, path, email, body) => { const x = await pre.mf.dispatchFetch(pre.url + path, { method, headers: H(email), body: body === undefined ? undefined : JSON.stringify(body) }); return { s: x.status, j: await x.json().catch(() => null) }; };
await pcall('POST', '/api/admin/artists', FOUNDER, { display_name: 'Pre Artist', email: 'pre@example.test' });
const pme = await pcall('GET', '/api/me', 'pre@example.test'), pov = await pcall('GET', '/api/admin/overview', FOUNDER), pac = await pcall('GET', '/api/agreement', 'pre@example.test');
const pacc2 = await pcall('POST', '/api/agreement/accept', 'pre@example.test', { accept: true, documents: {}, statement: 'x' });
const plog = await pcall('GET', '/api/admin/enquiry-log', FOUNDER);
check('B1 before the migration Studio and the desk work as before; the agreement reads “not installed”, accepting is refused (503), the enquiry log says it is not installed',
  pme.s === 200 && pme.j.status.agreement.installed === false && pov.s === 200 && pov.j.agreement_installed === false && pac.s === 200 && pacc2.s === 503 && plog.s === 200 && plog.j.installed === false,
  [pme.s, pov.s, pac.s, pacc2.s, plog.s].join(' '));
await pre.mf.dispose();

console.log(`\nFOUNDING ARTIST AGREEMENT · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose();
process.exit(results.every(Boolean) ? 0 : 1);
