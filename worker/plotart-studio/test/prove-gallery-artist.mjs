// PROVE · Gallery Artist programme, Phase 2 (agreement and Studio onboarding; development 13 Nov 2026).
// Local only: Miniflare D1/R2, synthetic artists, captured mail. Nothing here touches Cloudflare or any real record.
//   node test/prove-gallery-artist.mjs
import { readFileSync } from 'node:fs';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { acceptAgreement } from './agree.mjs';
import { statements } from './sql.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 600)}]` : ''}`); };
const HERE = new URL('..', import.meta.url).pathname;
const SCHEMA = readFileSync(HERE + 'schema.sql', 'utf8');
const MIG13 = readFileSync(HERE + 'migrations/0013_gallery_artist_agreement_text.sql', 'utf8');
const NOTICE = readFileSync(HERE + 'src/enquiry.js', 'utf8').match(/const NOTICE = '([^']+)'/)[1];
const FAA = 'PA-FAA-2026-11', GPIL = 'PA-GPIL-2026-11', GAA = 'PA-GAA-2026-11';
const Hd = e => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
const mk = S => async (method, path, email, body) => {
  const r = await S.mf.dispatchFetch(S.url + path, { method, headers: Hd(email), body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
};

let S, P;
try {
console.log('PROVE · Gallery Artist programme (Phase 2)');

/* ---------------------------------------------------------------- before migration 0012 (production today) */
console.log('— before migration 0012 (production today)');
const before0012 = SCHEMA.replace(/\n-- PlotArt Studio · migration 0012[\s\S]*$/, '\n');
check('B0 the test schema without 0012 has no Gallery Artist tables; the full schema has them', !/artist_terms/.test(before0012) && /CREATE TABLE IF NOT EXISTS artist_terms/.test(SCHEMA));
P = await start({ port: 8895, schemaSql: before0012 });
let pcall = mk(P);
let r = await pcall('GET', '/api/admin/overview', FOUNDER);
const ov0 = r;
const g0 = await pcall('POST', '/api/admin/artists', FOUNDER, { display_name: 'Gail Early', email: 'gail-early@example.test', programme: 'gallery_artist' });
const n0 = await pcall('POST', '/api/admin/artists', FOUNDER, { display_name: 'Nobody Chosen', email: 'nobody@example.test' });
const f0 = await pcall('POST', '/api/admin/artists', FOUNDER, { display_name: 'Fiona Founding', email: 'fiona-f@example.test', programme: 'founding' });
const cnt0 = (await P.db.prepare('SELECT COUNT(*) n FROM artists').first()).n;
check('B1 before 0012: the desk reports Gallery Artist invitations unavailable; a Gallery Artist invite is refused (503); an invite with no programme is refused (400); a Founding invite works as today',
  ov0.s === 200 && ov0.j.terms_installed === false && g0.s === 503 && n0.s === 400 && f0.s === 200 && cnt0 === 1, JSON.stringify([ov0.s, ov0.j && ov0.j.terms_installed, g0.s, n0.s, f0.s, cnt0]));
r = await pcall('GET', '/api/agreement', 'fiona-f@example.test');
check('B2 before 0012 a Founding Artist sees exactly today’s agreement (PA-FAA with PA-GPIL, the founding statement)',
  r.s === 200 && JSON.stringify(r.j.required) === JSON.stringify([FAA, GPIL]) && r.j.programme === 'founding' && /Founding Artist Agreement PA-FAA-2026-11/.test(r.j.statement));
await P.mf.dispose(); P = null;

/* ---------------------------------------------------------------- after 0012, before 0013 (text not yet approved) */
console.log('— after migration 0012, before the agreement text is installed (0013)');
S = await start({ port: 8896, enquiry: {} });
const call = mk(S), { db } = S;
const q1 = (sql, ...b) => db.prepare(sql).bind(...b).first();
const qa = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
const GAIL = 'gail-gallery@example.test', FRAN = 'fran-founding@example.test', LIC = 'lic-only@example.test';
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Gail Gallery', email: GAIL });
check('I1 an invitation without a programme is refused (400) and creates nothing', r.s === 400 && /Founding Artist or Gallery Artist/.test(r.j.error) && (await q1('SELECT COUNT(*) n FROM artists')).n === 0);
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Gail Gallery', email: GAIL, programme: 'something_else' });
check('I2 an unknown programme is refused (400)', r.s === 400);
const mail0 = (await qa('SELECT * FROM mail_capture')).length;
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Gail Gallery', email: GAIL, programme: 'gallery_artist' }); const GID = r.j.id;
const gRow = await q1('SELECT * FROM artists WHERE id=?', GID), gTerms = await q1('SELECT * FROM artist_terms WHERE artist_id=?', GID);
const gAud = await q1("SELECT detail FROM audit WHERE action='invite' AND artist_id=?", GID);
check('I3 a Gallery Artist invitation creates a non-Founding artist with a 15% terms row (1500 bp, no variation) and audits the programme',
  r.s === 200 && gRow.founding === 0 && gRow.founding_number === null && gTerms && gTerms.track === 'gallery_artist' && gTerms.commission_bp === 1500 && gTerms.variation_agreed_on === null
  && JSON.parse(gAud.detail).programme === 'gallery_artist', JSON.stringify([r.s, gRow && gRow.founding, gTerms]));
const gMail = (await qa('SELECT * FROM mail_capture')).slice(mail0).find(m => m.to_addr === GAIL);
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Fran Founding', email: FRAN, programme: 'founding' }); const FID = r.j.id;
const fMail = (await qa('SELECT * FROM mail_capture')).find(m => m.to_addr === FRAN);
check('I4 a Founding invitation (private, as promised) still creates a Founding Artist with no Gallery Artist terms',
  r.s === 200 && (await q1('SELECT founding FROM artists WHERE id=?', FID)).founding === 1 && !(await q1('SELECT 1 x FROM artist_terms WHERE artist_id=?', FID)));
check('I5 the Gallery Artist’s invitation names their agreement and the 15% commission; the Founding Artist’s invitation is unchanged (no Gallery Artist wording)',
  gMail && /joining PlotArt as a Gallery Artist/.test(gMail.body) && /15% commission/.test(gMail.body) && fMail && !/Gallery Artist/.test(fMail.body), JSON.stringify([!!gMail, !!fMail]));
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Lic Only', email: LIC, founding: false }); const LID = r.j.id;
check('I6 the older explicit founding:false invitation still means licence only, as before (no terms row)', r.s === 200 && !(await q1('SELECT 1 x FROM artist_terms WHERE artist_id=?', LID)));
r = await call('GET', '/api/admin/overview', FOUNDER);
const prog = Object.fromEntries(r.j.artists.map(a => [a.id, a.programme]));
check('I7 the founder’s desk shows each artist’s programme and that Gallery Artist invitations are available',
  r.j.terms_installed === true && prog[GID] === 'gallery_artist' && prog[FID] === 'founding' && prog[LID] === 'licence_only', JSON.stringify(prog));

r = await call('GET', '/api/agreement', GAIL);
const gHtml = await call('GET', `/agreements/${GAA}.html`, GAIL);
const acc0 = await acceptAgreement(S.mf, S.url, GAIL);
check('G1 before the text is installed, a Gallery Artist is told their agreement (PA-GAA with PA-GPIL) is not ready: not installed, the draft text is not served, and accepting is refused (503)',
  r.s === 200 && r.j.programme === 'gallery_artist' && r.j.installed === false && JSON.stringify(r.j.required) === JSON.stringify([GAA, GPIL])
  && gHtml.s === 404 && acc0.s === 503 && (await qa('SELECT * FROM agreement_acceptances WHERE artist_id=?', GID)).length === 0, JSON.stringify([r.j && r.j.installed, gHtml.s, acc0.s]));
r = await call('GET', '/api/me', GAIL);
const ck = JSON.stringify(r.j.status && r.j.status.checklist);
check('G1b the Gallery Artist’s submission checklist asks for the Gallery Artist Agreement and the image licence (not the Founding Artist Agreement)',
  /Read and accept the Gallery Artist Agreement and the Gallery Publication and Image Licence/.test(ck) && !/Founding Artist Agreement/.test(ck), ck.slice(0, 400));
r = await call('GET', '/api/agreement', FRAN);
check('G2 the Founding Artist’s agreement is unaffected: PA-FAA with PA-GPIL, installed, founding statement',
  r.j.programme === 'founding' && r.j.installed === true && JSON.stringify(r.j.required) === JSON.stringify([FAA, GPIL]) && /PA-FAA-2026-11/.test(r.j.statement));

/* ---------------------------------------------------------------- after 0013 (text installed) */
console.log('— after migration 0013 (the approved PA-GAA text installed)');
for (const st of statements(MIG13)) await db.prepare(st).run();
r = await call('GET', '/api/agreement', GAIL);
check('G3 the Gallery Artist now sees their agreement installed, with the exact one-tick statement',
  r.j.installed === true && r.j.statement === 'I have read and accept the PlotArt Gallery Artist Agreement PA-GAA-2026-11, including the Gallery Publication and Image Licence PA-GPIL-2026-11.');
const page = await call('GET', `/agreements/${GAA}.html`, GAIL);
check('G4 the installed text is served to the artist and carries the commercial terms (15%, no fees, no exclusivity, direct payment, commissioned work excluded)',
  page.s === 200 && /15%/.test(page.t) && /exclusiv/i.test(page.t) && /commission/i.test(page.t) && !/DRAFT|drafting note|NOT YET ISSUED|r5|⚖/i.test(page.t)
  && /Original Artwork/.test(page.t) && /Newly commissioned artwork/.test(page.t) && /whether or not it is shown on PlotArt/.test(page.t), page.s);
const bad = await acceptAgreement(S.mf, S.url, GAIL, { tamper: true });
check('G5 a tampered fingerprint is refused (409) and nothing is recorded', bad.s === 409 && (await qa('SELECT * FROM gallery_agreement_acceptances')).length === 0);
const okA = await acceptAgreement(S.mf, S.url, GAIL, { legal_name: 'Gail Gallery' });
const gaaRows = await qa('SELECT * FROM gallery_agreement_acceptances WHERE artist_id=?', GID), licRows = await qa('SELECT * FROM agreement_acceptances WHERE artist_id=?', GID);
check('G6 one tick records PA-GAA in gallery_agreement_acceptances and PA-GPIL in agreement_acceptances, under the same event, with the same statement',
  okA.s === 200 && gaaRows.length === 1 && gaaRows[0].doc_id === GAA && licRows.length === 1 && licRows[0].doc_id === GPIL && gaaRows[0].event_id === licRows[0].event_id
  && gaaRows[0].statement === licRows[0].statement && gaaRows[0].legal_name === 'Gail Gallery', JSON.stringify([okA.s, okA.j, gaaRows.length, licRows.length]));
r = await call('GET', '/api/agreement', GAIL);
check('G7 the Gallery Artist’s agreement then reads as accepted, with both documents in the history', r.j.accepted === true && r.j.history.length === 2 && r.j.status === 'accepted');
const again = await acceptAgreement(S.mf, S.url, GAIL);
check('G8 accepting again is refused (409)', again.s === 409 && (await qa('SELECT * FROM gallery_agreement_acceptances')).length === 1);
const fa = await acceptAgreement(S.mf, S.url, FRAN);
check('G9 a Founding Artist accepting is recorded exactly as today (both rows in agreement_acceptances, nothing in the Gallery Artist table)',
  fa.s === 200 && (await qa('SELECT doc_id FROM agreement_acceptances WHERE artist_id=? ORDER BY doc_id', FID)).map(x => x.doc_id).join() === [FAA, GPIL].join()
  && (await qa('SELECT * FROM gallery_agreement_acceptances WHERE artist_id=?', FID)).length === 0);
let refusedTrig = [];
for (const sql of [`UPDATE gallery_agreement_acceptances SET legal_name='X' WHERE artist_id='${GID}'`, `DELETE FROM gallery_agreement_acceptances WHERE artist_id='${GID}'`,
  `UPDATE gallery_agreement_documents SET title='x'`, `DELETE FROM gallery_agreement_documents`, `UPDATE artist_terms SET track='founding' WHERE artist_id='${GID}'`, `DELETE FROM artist_terms WHERE artist_id='${GID}'`])
  { try { await db.prepare(sql).run(); refusedTrig.push(false); } catch { refusedTrig.push(true); } }
check('G10 the database refuses to edit or remove acceptances, installed texts or a programme (and terms rows are kept until retention ends)', refusedTrig.every(Boolean), JSON.stringify(refusedTrig));
r = await call('GET', '/api/me', GAIL);
check('G11 the artist’s Studio shows their own terms (Gallery Artist, 15%), without the private note field',
  r.j.terms && r.j.terms.programme === 'gallery_artist' && r.j.terms.commission_bp === 1500 && !('variation_note' in r.j.terms), JSON.stringify(r.j && r.j.terms));
const fme = await call('GET', '/api/me', FRAN);
check('G12 a Founding Artist’s Studio reports the Founding programme and no commission rate', fme.j.terms && fme.j.terms.programme === 'founding' && !('commission_bp' in fme.j.terms), JSON.stringify(fme.j && fme.j.terms));

/* ---------------------------------------------------------------- the founder's terms panel */
console.log('— Gallery Artist terms (founder only)');
const put = (email, id, b) => call('PUT', `/api/admin/artists/${id}/terms`, email, b);
const today = new Date().toISOString().slice(0, 10), future = '2099-01-01';
const tries = [await put(GAIL, GID, { commission_bp: 1000, variation_agreed_on: today }), await put(FOUNDER, GID, { commission_bp: 1600, variation_agreed_on: today }),
  await put(FOUNDER, GID, { commission_bp: 1200 }), await put(FOUNDER, GID, { commission_bp: 1200, variation_agreed_on: future }),
  await put(FOUNDER, GID, { commission_bp: 12.5, variation_agreed_on: today }), await put(FOUNDER, GID, { commission_bp: 1200, variation_agreed_on: today, variation_note: 'x'.repeat(1001) }),
  await put(FOUNDER, FID, { commission_bp: 1500 })];
check('T1 refused: the artist themself (not founder), above 15%, a reduced rate without a written-variation date, a future date, a fraction of a basis point, a note over 1,000 characters, and a Founding Artist (no Gallery Artist terms)',
  tries[0].s >= 401 && tries[0].s <= 404 && tries.slice(1, 6).every(x => x.s === 400) && tries[6].s === 404 && (await q1('SELECT commission_bp FROM artist_terms WHERE artist_id=?', GID)).commission_bp === 1500,
  JSON.stringify(tries.map(x => x.s)));
const NOTE = 'Private: agreed by letter for a charity show';
r = await put(FOUNDER, GID, { commission_bp: 1200, variation_agreed_on: today, variation_note: NOTE });
const tAud = await qa("SELECT detail FROM audit WHERE action='terms_changed' AND artist_id=?", GID);
check('T2 the founder can record a written individual variation (12%, its date and a private note); the change is audited without the note’s text',
  r.s === 200 && r.j.terms.commission_bp === 1200 && r.j.terms.variation_agreed_on === today && tAud.length === 1 && !tAud[0].detail.includes('charity') && JSON.parse(tAud[0].detail).to_bp === 1200,
  JSON.stringify([r.s, r.j]));
const me2 = await call('GET', '/api/me', GAIL), ag2 = await call('GET', '/api/agreement', GAIL);
check('T3 the artist sees their varied rate (12%) and its date, never the private note', me2.j.terms.commission_bp === 1200 && me2.j.terms.variation_agreed_on === today && !me2.t.includes('charity') && !ag2.t.includes('charity'));
let dbRefuse = false; try { await db.prepare(`UPDATE artist_terms SET commission_bp=1200, variation_agreed_on=NULL WHERE artist_id='${GID}'`).run(); } catch { dbRefuse = true; }
let dbRefuse2 = false; try { await db.prepare(`UPDATE artist_terms SET commission_bp=1600 WHERE artist_id='${GID}'`).run(); } catch { dbRefuse2 = true; }
check('T4 the database itself refuses a reduced rate without a variation date, and any rate above 15%', dbRefuse && dbRefuse2);
r = await put(FOUNDER, GID, { commission_bp: 1500, variation_agreed_on: null, variation_note: null });
check('T5 returning to the standard 15% needs no date and clears the variation', r.s === 200 && r.j.terms.commission_bp === 1500 && r.j.terms.variation_agreed_on === null);
const pub = await call('GET', '/api/admin/overview', FOUNDER);
check('T6 the founder’s overview never carries the private note', !pub.t.includes('charity') && !pub.t.includes('variation_note'));

/* ---------------------------------------------------------------- enquiries: wording follows the programme */
console.log('— enquiry relay: the artist email follows the artist’s programme');
await seedPublished(db, { id: 'afound', slug: 'found-test', email: 'found-test@example.test', name: 'Found Test', works: 2, number: 1 });
await seedPublished(db, { id: 'agal', slug: 'gal-test', email: 'gal-test@example.test', name: 'Gal Test', works: 2 });
await db.prepare("UPDATE artists SET founding = 0, founding_number = NULL WHERE id = 'agal'").run();
await db.prepare("INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES ('agal','gallery_artist',1500,?,?,?)").bind(FOUNDER, today, today).run();
let ipN = 0;
const enq = body => S.mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json', 'CF-Connecting-IP': `198.51.100.${++ipN}` }, body: JSON.stringify(body) });
const base = { notice: NOTICE, name: 'Cara Client', email: 'cara.client@example.test', message: 'Is this still available?' };
const m0 = (await qa('SELECT * FROM mail_capture')).length;
const e1 = await enq({ ...base, ref: 'PA-found-test-wafound1' }), e1j = await e1.json();
const e2 = await enq({ ...base, ref: 'PA-gal-test-wagal1' }), e2j = await e2.json();
const ms = (await qa('SELECT * FROM mail_capture ORDER BY id')).slice(m0);
const toF = ms.find(m => m.to_addr === 'found-test@example.test'), toG = ms.find(m => m.to_addr === 'gal-test@example.test');
check('E1 a Founding Artist’s enquiry email is word for word as today (the founding-year sentence)',
  e1.status === 200 && toF && toF.body.includes('PlotArt takes no commission on enquiries from your founding year. Any sale is agreed directly between you and the buyer.') && !/Gallery Artist/.test(toF.body), JSON.stringify([e1.status, e1j]));
check('E2 a Gallery Artist’s enquiry email says it is a PlotArt introduction under their Gallery Artist Agreement, never the founding-year sentence',
  e2.status === 200 && toG && toG.body.includes('This enquiry is an introduction through PlotArt. If it leads to a sale, PlotArt’s commission applies as set out in your Gallery Artist Agreement.')
  && !/founding year/.test(toG.body), JSON.stringify([e2.status, e2j, toG && toG.body.slice(-300)]));
const lg = await q1('SELECT * FROM enquiry_log WHERE reference=?', e2j.reference);
check('E3 the Gallery Artist’s enquiry is logged as a non-Founding introduction (reference and date kept for attribution, no buyer details)',
  lg && lg.founding === 0 && lg.founding_year_end === null && !JSON.stringify(lg).includes('cara'), JSON.stringify(lg));
const toBuyer = ms.filter(m => m.to_addr === base.email);
check('E4 the buyer’s confirmation is the same for both programmes (no commercial terms shown to buyers)',
  toBuyer.length === 2 && toBuyer.every(m => !/commission|Gallery Artist|founding/i.test(m.body)), JSON.stringify(toBuyer.map(m => m.body.slice(0, 120))));
} catch (e) { check('the proof ran to the end', false, e && e.stack); }
finally { if (S) await S.mf.dispose(); if (P) await P.mf.dispose(); }
const fail = results.filter(x => !x).length;
console.log(`\nGALLERY ARTIST PHASE 2 · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
