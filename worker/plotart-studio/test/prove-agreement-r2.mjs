// PROVE · Artist Agreement PA-GAA-2026-11-R2 and Image Licence PA-GPIL-2026-11-R2 (migration 0030, development 27 Nov 2026).
// Regression tests for new invitations, existing agreements and historical downloads, plus the version lock.
// Local only: Miniflare D1, synthetic artists, captured mail. Nothing here touches Cloudflare or any real record.
//   node test/prove-agreement-r2.mjs
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { start, FOUNDER } from './local.mjs';
import { token } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
import { statements } from './sql.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 600)}]` : ''}`); };
const HERE = new URL('..', import.meta.url).pathname;
const MIG13 = readFileSync(HERE + 'migrations/0013_gallery_artist_agreement_text.sql', 'utf8');
const MIG30 = readFileSync(HERE + 'migrations/0030_artist_agreement_r2.sql', 'utf8');
const FP = JSON.parse(readFileSync(HERE + 'agreements/issued/fingerprints.json', 'utf8')).documents;
const FAA = 'PA-FAA-2026-11', GPIL = 'PA-GPIL-2026-11', GAA = 'PA-GAA-2026-11', GAA2 = 'PA-GAA-2026-11-R2', GPIL2 = 'PA-GPIL-2026-11-R2';
const sha = b => createHash('sha256').update(b).digest('hex');
const Hd = e => ({ ...(e ? { 'Cf-Access-Jwt-Assertion': token(e) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
const mk = S => async (method, path, email, body) => {
  const r = await S.mf.dispatchFetch(S.url + path, { method, headers: Hd(email), body: body === undefined ? undefined : JSON.stringify(body) });
  const buf = Buffer.from(await r.arrayBuffer()); const t = buf.toString('utf8'); let j = null; try { j = JSON.parse(t); } catch { /* html or pdf */ }
  return { s: r.status, j, t, buf };
};
const refused = async (db, sql, ...b) => { try { await db.prepare(sql).bind(...b).run(); return null; } catch (e) { return String(e.message || e); } };

let S;
try {
console.log('PROVE · Artist Agreement R2 for new invitations (migration 0030)');
S = await start({ port: 8931, enquiry: {} });
const call = mk(S), { db } = S;
const q1 = (sql, ...b) => db.prepare(sql).bind(...b).first();
const qa = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
for (const st of statements(MIG13)) await db.prepare(st).run();   // the original Gallery Artist Agreement text, as in production

/* ------------------------------------------------------------ before 0030: production today */
console.log('— before migration 0030 (production today)');
const OLDG = 'olga-gallery@example.test', FRAN = 'fran-founding@example.test';
let r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Olga Gallery', email: OLDG, programme: 'gallery_artist' }); const OID = r.j && r.j.id;
const r2f = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Fran Founding', email: FRAN, programme: 'founding' }); const FID = r2f.j && r2f.j.id;
check('P1 before 0030 a Gallery Artist invitation and a Founding invitation work as today (no version row table yet)', r.s === 200 && r2f.s === 200
  && await refused(db, 'SELECT 1 FROM artist_agreement_versions') !== null, JSON.stringify([r.s, r2f.s]));
r = await call('GET', '/api/agreement', OLDG);
check('P2 the existing Gallery Artist is asked for the original agreement (PA-GAA-2026-11 with PA-GPIL-2026-11)', r.s === 200 && JSON.stringify(r.j.required) === JSON.stringify([GAA, GPIL]), JSON.stringify(r.j && r.j.required));
const oAcc = await acceptAgreement(S.mf, S.url, OLDG, { legal_name: 'Olga Gallery' });
const fAcc = await acceptAgreement(S.mf, S.url, FRAN);
check('P3 both existing artists accept their own documents', oAcc.s === 200 && fAcc.s === 200, JSON.stringify([oAcc.s, oAcc.j, fAcc.s, fAcc.j]));
r = await call('GET', `/agreements/${GAA2}.pdf`, OLDG);
const r2g = await call('GET', `/agreements/${GPIL2}.pdf`, OLDG);
const r2fd = await call('GET', `/agreements/${GAA2}.html`, FOUNDER);
check('P4 before 0030 artists cannot download the R2 texts (404); the founder can preview the bundled R2 text', r.s === 404 && r2g.s === 404 && r2fd.s === 200 && sha(r2fd.buf) === FP[GAA2].html_sha256, JSON.stringify([r.s, r2g.s, r2fd.s]));
const before = { o: await qa('SELECT * FROM gallery_agreement_acceptances WHERE artist_id=? ORDER BY id', OID), oL: await qa('SELECT * FROM agreement_acceptances WHERE artist_id=? ORDER BY id', OID),
  f: await qa('SELECT * FROM agreement_acceptances WHERE artist_id=? ORDER BY id', FID), oT: await q1('SELECT * FROM artist_terms WHERE artist_id=?', OID), artists: await qa('SELECT * FROM artists ORDER BY id') };

/* ------------------------------------------------------------ migration 0030 */
console.log('— migration 0030 applied');
for (const st of statements(MIG30)) await db.prepare(st).run();
const after = { o: await qa('SELECT * FROM gallery_agreement_acceptances WHERE artist_id=? ORDER BY id', OID), oL: await qa('SELECT * FROM agreement_acceptances WHERE artist_id=? ORDER BY id', OID),
  f: await qa('SELECT * FROM agreement_acceptances WHERE artist_id=? ORDER BY id', FID), oT: await q1('SELECT * FROM artist_terms WHERE artist_id=?', OID), artists: await qa('SELECT * FROM artists ORDER BY id') };
check('M1 the migration changes no existing artist, terms or acceptance row, and assigns no version to anyone', JSON.stringify(before) === JSON.stringify(after)
  && (await q1('SELECT COUNT(*) n FROM artist_agreement_versions')).n === 0);
const docs = await qa("SELECT doc_id, html_sha256, pdf_sha256 FROM gallery_agreement_documents WHERE doc_id=? UNION ALL SELECT doc_id, html_sha256, pdf_sha256 FROM agreement_documents WHERE doc_id=?", GAA2, GPIL2);
check('M2 the R2 documents are registered with the fingerprints of the bundled files', docs.length === 2 && docs.every(d => d.html_sha256 === FP[d.doc_id].html_sha256 && d.pdf_sha256 === FP[d.doc_id].pdf_sha256));

/* ------------------------------------------------------------ existing agreements unchanged */
console.log('— existing agreements after 0030');
r = await call('GET', '/api/agreement', OLDG);
check('E1 the existing Gallery Artist keeps PA-GAA-2026-11 with PA-GPIL-2026-11, still accepted, original statement', r.s === 200 && JSON.stringify(r.j.required) === JSON.stringify([GAA, GPIL])
  && r.j.accepted === true && /Gallery Artist Agreement PA-GAA-2026-11[^-]/.test(r.j.statement), JSON.stringify(r.j && [r.j.required, r.j.accepted, r.j.statement]));
r = await call('GET', '/api/agreement', FRAN);
check('E2 the Founding Artist keeps PA-FAA-2026-11 with PA-GPIL-2026-11, still accepted, founding programme', r.s === 200 && JSON.stringify(r.j.required) === JSON.stringify([FAA, GPIL])
  && r.j.accepted === true && r.j.programme === 'founding', JSON.stringify(r.j && [r.j.required, r.j.accepted, r.j.programme]));

/* ------------------------------------------------------------ historical downloads */
console.log('— historical downloads');
const dl = async (email, id, ext) => { const x = await call('GET', `/agreements/${id}.${ext}`, email); return x.s === 200 && sha(x.buf) === FP[id][ext + '_sha256']; };
check('H1 the existing Gallery Artist can still download the exact accepted PDFs and HTML (PA-GAA-2026-11, PA-GPIL-2026-11)',
  await dl(OLDG, GAA, 'pdf') && await dl(OLDG, GPIL, 'pdf') && await dl(OLDG, GAA, 'html') && await dl(OLDG, GPIL, 'html'));
check('H2 the Founding Artist can still download the exact accepted PDFs (PA-FAA-2026-11, PA-GPIL-2026-11)', await dl(FRAN, FAA, 'pdf') && await dl(FRAN, GPIL, 'pdf'));
r = await call('GET', '/api/agreement', OLDG);
check('H3 the acceptance history still lists the original documents with their fingerprints', r.j.history.filter(h => h.method === 'studio_checkbox').map(h => h.doc_id).sort().join() === [GAA, GPIL].sort().join()
  && r.j.history.every(h => !h.doc_sha256 || h.doc_sha256 === FP[h.doc_id].html_sha256));

/* ------------------------------------------------------------ new invitations */
console.log('— new invitations after 0030');
const NEWG = 'nora-new@example.test', NEWF = 'finn-founding@example.test';
const m0 = (await qa('SELECT * FROM mail_capture')).length;
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Nora New', email: NEWG, programme: 'gallery_artist' }); const NID = r.j && r.j.id;
const nv = await q1('SELECT * FROM artist_agreement_versions WHERE artist_id=?', NID), nt = await q1('SELECT * FROM artist_terms WHERE artist_id=?', NID), na = await q1('SELECT * FROM artists WHERE id=?', NID);
check('N1 a new Gallery Artist invitation fixes R2 (agreement and licence) at the moment the artist is created, on the standard 15% terms', r.s === 200 && nv && nv.agreement_version === GAA2
  && nv.licence_version === GPIL2 && nv.assigned_at === na.created_at && nt.commission_bp === 1500, JSON.stringify([r.s, nv, nt && nt.commission_bp]));
const nMail = (await qa('SELECT * FROM mail_capture')).slice(m0).find(m => m.to_addr === NEWG);
check('N2 the invitation email names the Artist Agreement and Image Licence and links to the public copies', nMail && /Artist Agreement and Image Licence/.test(nMail.body) && /plotnua\.ie\/plotart\/for-artists\.html/.test(nMail.body));
r = await call('GET', '/api/agreement', NEWG);
check('N3 the new artist is asked for PA-GAA-2026-11-R2 with PA-GPIL-2026-11-R2, with the R2 statement', r.s === 200 && JSON.stringify(r.j.required) === JSON.stringify([GAA2, GPIL2])
  && r.j.statement.includes(GAA2) && r.j.statement.includes(GPIL2) && r.j.accepted === false, JSON.stringify(r.j && [r.j.required, r.j.statement]));
check('N4 the new artist can read and download both R2 documents (exact fingerprints)', await dl(NEWG, GAA2, 'pdf') && await dl(NEWG, GPIL2, 'pdf') && await dl(NEWG, GAA2, 'html') && await dl(NEWG, GPIL2, 'html'));
const tam = await acceptAgreement(S.mf, S.url, NEWG, { tamper: true });
const nAcc = await acceptAgreement(S.mf, S.url, NEWG, { legal_name: 'Nora New' });
const nRows = [...await qa('SELECT doc_id, doc_sha256 FROM gallery_agreement_acceptances WHERE artist_id=?', NID), ...await qa('SELECT doc_id, doc_sha256 FROM agreement_acceptances WHERE artist_id=?', NID)];
check('N5 a tampered text is refused; the real texts are accepted together and recorded against R2 with their fingerprints', tam.s !== 200 && nAcc.s === 200
  && nRows.map(x => x.doc_id).sort().join() === [GAA2, GPIL2].sort().join() && nRows.every(x => x.doc_sha256 === FP[x.doc_id].html_sha256), JSON.stringify([tam.s, nAcc.s, nRows]));
r = await call('GET', '/api/agreement', NEWG);
check('N6 after acceptance the new artist holds R2 and can still download both documents', r.j.accepted === true && await dl(NEWG, GAA2, 'pdf') && await dl(NEWG, GPIL2, 'pdf'));
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Finn Founding', email: NEWF, programme: 'founding' });
const fv = await q1('SELECT COUNT(*) n FROM artist_agreement_versions WHERE artist_id=?', r.j && r.j.id), fr = await call('GET', '/api/agreement', NEWF);
check('N7 a new Founding Artist invitation is unchanged: no R2 assignment, PA-FAA-2026-11 with PA-GPIL-2026-11', r.s === 200 && fv.n === 0 && JSON.stringify(fr.j.required) === JSON.stringify([FAA, GPIL]));
r = await call('GET', '/api/agreement', OLDG);
check('N8 other artists can now download the R2 public texts too, but their own required documents are unchanged', await dl(OLDG, GAA2, 'pdf') && JSON.stringify(r.j.required) === JSON.stringify([GAA, GPIL]));

/* ------------------------------------------------------------ version lock (no trigger on an existing table) */
console.log('— version lock');
const NOW = new Date().toISOString();
let e1 = await refused(db, 'UPDATE artist_agreement_versions SET agreement_version=? WHERE artist_id=?', GAA2, NID);
let e2 = await refused(db, "UPDATE artist_agreement_versions SET assigned_by='someone' WHERE artist_id=?", NID);
let e3 = await refused(db, 'DELETE FROM artist_agreement_versions WHERE artist_id=?', NID);
check('L1 after acceptance the new artist’s assigned version cannot be changed or removed', /never changes/.test(e1 || '') && /never changes/.test(e2 || '') && /retention/.test(e3 || ''), JSON.stringify([e1, e2, e3]));
let e4 = await refused(db, 'INSERT INTO artist_agreement_versions (artist_id, agreement_version, licence_version, assigned_by, assigned_at) VALUES (?,?,?,?,?)', OID, GAA2, GPIL2, 'founder', NOW);
let e4b = await refused(db, 'INSERT INTO artist_agreement_versions (artist_id, agreement_version, licence_version, assigned_by, assigned_at) VALUES (?,?,?,?,?)', OID, GAA2, GPIL2, 'founder', before.artists.find(a => a.id === OID).created_at);
let e5 = await refused(db, 'INSERT INTO artist_agreement_versions (artist_id, agreement_version, licence_version, assigned_by, assigned_at) VALUES (?,?,?,?,?)', FID, GAA2, GPIL2, 'founder', before.artists.find(a => a.id === FID).created_at);
check('L2 an existing Gallery Artist cannot be moved onto R2 retrospectively, even with their original creation time; nor can a Founding Artist',
  [e4, e4b, e5].every(e => /only when the artist is invited/.test(e || '')), JSON.stringify([e4, e4b, e5]));
const fAfter = await call('GET', '/api/agreement', FRAN), oAfter = await call('GET', '/api/agreement', OLDG);
check('L3 after the refused attempts both existing artists still hold exactly their original documents, accepted',
  JSON.stringify(fAfter.j.required) === JSON.stringify([FAA, GPIL]) && fAfter.j.accepted === true && JSON.stringify(oAfter.j.required) === JSON.stringify([GAA, GPIL]) && oAfter.j.accepted === true);
let e6 = await refused(db, 'INSERT INTO artist_agreement_versions (artist_id, agreement_version, licence_version, assigned_by, assigned_at) VALUES (?,?,?,?,?)', NID, GAA2, GPIL2, 'founder', na.created_at);
let e7 = await refused(db, "INSERT INTO artist_agreement_versions (artist_id, agreement_version, licence_version, assigned_by, assigned_at) VALUES (?,'PA-GAA-2026-11',?,?,?)", OID, GPIL2, 'founder', before.artists.find(a => a.id === OID).created_at);
check('L4 a second assignment for the new artist is refused, and no version other than R2 can be recorded', !!e6 && /CHECK|constraint/i.test(e7 || ''), JSON.stringify([e6, e7]));
r = await call('GET', '/api/agreement', NEWG);
check('L5 the new artist still holds R2 after the refused changes', JSON.stringify(r.j.required) === JSON.stringify([GAA2, GPIL2]) && r.j.accepted === true);

/* ------------------------------------------------------------ managed checkout */
console.log('— managed checkout');
r = await call('GET', '/api/checkout', NEWG);
const o = await call('POST', '/api/checkout/opt-in', NEWG, { accept: true });
const ob = await call('POST', '/api/checkout/basket/opt-in', NEWG, { accept: true });
check('C1 an R2 artist is told managed checkout is unavailable until compatible payment terms are issued, and cannot opt in (409)',
  r.s === 200 && /compatible payment terms are issued/.test(r.j.agreement_unavailable || '') && r.j.checkout_available === false
  && o.s === 409 && /compatible payment terms/.test(o.j.error) && ob.s === 409, JSON.stringify([r.s, r.j && r.j.agreement_unavailable, o.s, o.j, ob.s]));
r = await call('GET', '/api/checkout', OLDG);
const oo = await call('POST', '/api/checkout/opt-in', OLDG, { accept: true });
check('C2 an existing Gallery Artist sees no R2 notice and is not refused for that reason', r.s === 200 && !r.j.agreement_unavailable && !/compatible payment terms/.test((oo.j && oo.j.error) || ''), JSON.stringify([r.j && r.j.agreement_unavailable, oo.s, oo.j]));

/* ------------------------------------------------------------ Studio summary shown only to R2 artists */
console.log('— Studio summary');
const UI = readFileSync(HERE + 'ui/studio.js', 'utf8');
const ASSETS = readFileSync(HERE + 'src/assets.js', 'utf8');
check('U1 the revised summary lines are conditional on R2; the original line remains for everyone else; the bundle carries the same code',
  /const r2 = \(g\.required \|\| \[\]\)\.includes\('PA-GAA-2026-11-R2'\)/.test(UI) && /\$\{r2 \? `<li>Independent sales carry no PlotArt commission/.test(UI)
  && /Collectors pay you directly\. You report each sale and PlotArt invoices you for its commission\./.test(UI) && !/Managed checkout is optional where offered/.test(UI)
  && ASSETS.includes('PA-GAA-2026-11-R2') && ASSETS.includes("const r2 = (g.required || []).includes('PA-GAA-2026-11-R2')"));
} catch (e) { console.error(e); results.push(false); }
finally { if (S) await S.mf.dispose(); }
const pass = results.filter(Boolean).length;
console.log(`\nARTIST AGREEMENT R2 · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
process.exit(pass === results.length ? 0 : 1);
