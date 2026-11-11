// PROVE · PlotArt Studio · "Start profile from application" for an EXISTING account (founder decision 11 Nov 2026).
// Synthetic artists and applications only; the real Worker runs locally (Miniflare/workerd) with a local D1 and R2.
// Nothing here touches Cloudflare, Airtable, the production database or any real artist.
//   node test/prove-prefill-existing.mjs
import { start, token, FOUNDER } from './local.mjs';
import { acceptAgreement } from './agree.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const { mf, url, db } = await start({ port: 8812 });
const AB = await mf.getR2Bucket('APPLICATIONS', 'studio');
const call = async (method, path, who, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' };
  if (who) h['Cf-Access-Jwt-Assertion'] = token(who);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const row = id => db.prepare('SELECT * FROM artists WHERE id=?').bind(id).first();
const q1 = (sql, ...b) => db.prepare(sql).bind(...b).first();
const qa = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
const mails = async () => (await q1('SELECT COUNT(*) AS n FROM mail_capture')).n;
const putApp = async (ref, app, images = 5) => {
  for (let n = 1; n <= images; n++) await AB.put(`applications/${ref}/${n}.jpg`, new Uint8Array([0xff, 0xd8, 0xff, n]), { httpMetadata: { contentType: 'image/jpeg' } });
  await AB.put(`applications/${ref}/application.json`, JSON.stringify({ application_ref: ref, submitted_at: '2026-11-11T13:08:52.000Z',
    images: Array.from({ length: images }, (_, i) => ({ file: `${i + 1}.jpg`, w: 2000, h: 1500 })), ...app }));
};
const create = async (name, email, ref = null, slug) => (await call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, founding: true, application_ref: ref, ...(slug ? { slug } : {}) })).j;
const prefill = (id, ref, who = FOUNDER) => call('POST', `/api/admin/artists/${id}/prefill`, who, { application_ref: ref });
const BIO = 'I am an abstract painter living in a coastal county. My work celebrates rhythm, colour and the energy of place. '.repeat(7).trim();
const APP = name => ({ artist_name: name, medium: 'painting', region: 'wicklow', bio: BIO, portfolio: 'https://www.example-artist.example/',
  website: 'https://www.example-artist.example/', social_link: '@example_artist', additional_info: 'Shortlisted for a residency award; group shows abroad.' });

console.log('PROVE · PlotArt Studio · start profile from application (existing accounts)');

/* ---- 1 · the Nessa-shaped case: account created BEFORE the feature (no reference), invited, never signed in */
const REF1 = 'F25-261111-A0A0A1';
await putApp(REF1, APP('Nora Synthetic'));
const n1 = await create('Nora Synthetic', 'nora@example.test');               // as if made before the deploy: no reference
await db.prepare('UPDATE artists SET founding_number=7 WHERE id=?').bind(n1.id).run();
await db.prepare("INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (5, ?, 0, NULL, '2026-11-11T00:00:00Z')").bind(n1.id).run();
const before = await row(n1.id);
const auditBefore = await qa('SELECT * FROM audit ORDER BY id');
const mailBefore = await mails();
let r = await prefill(n1.id, REF1);
let a = await row(n1.id);
check('E1 an existing account (no reference, not signed in) is filled: biography, medium, county, website, Instagram',
  r.s === 200 && JSON.stringify(r.j.fields) === JSON.stringify(['bio', 'medium', 'county', 'website', 'instagram']) &&
  a.bio === BIO && a.medium === 'painting' && a.county === 'Wicklow' && a.website === 'https://www.example-artist.example/' && a.instagram === 'example_artist', JSON.stringify([r.j, a]));
check('E2 the application reference is linked to the account (it had none)', r.j.linked === true && a.application_ref === REF1);
check('E3 public county visibility stays OFF', a.county_public === 0);
check('E4 statement, practice, portrait stay empty; "additional information" is never copied',
  a.statement === null && a.practice === null && a.portrait_image_id === null && !JSON.stringify(a).includes('residency'));
check('E5 no application image is transferred (0 images, 0 artworks)',
  (await q1('SELECT COUNT(*) AS n FROM images WHERE artist_id=?', n1.id)).n === 0 && (await q1('SELECT COUNT(*) AS n FROM artworks WHERE artist_id=?', n1.id)).n === 0);
check('E6 no email is sent (no new invitation or any other message)', (await mails()) === mailBefore && r.j.email_sent === false);
check('E7 the account itself is preserved: same id, email, gallery address, invited status, Founding status and Founding number',
  a.id === before.id && a.email === before.email && a.slug === before.slug && a.account_status === 'invited' && a.founding === 1 && a.founding_number === 7 && a.created_at === before.created_at);
check('E8 the gallery position is unchanged (position 5, not reserved)',
  (await q1('SELECT position, reserved FROM gallery_positions WHERE artist_id=?', n1.id)).position === 5);
const auditAfter = await qa('SELECT * FROM audit ORDER BY id');
const newRows = auditAfter.slice(auditBefore.length);
check('E9 earlier audit records are untouched; exactly one new entry records the operation (reference, fields; never the values)',
  JSON.stringify(auditAfter.slice(0, auditBefore.length)) === JSON.stringify(auditBefore) && newRows.length === 1 &&
  newRows[0].action === 'profile_prefilled_from_application' && newRows[0].actor === FOUNDER && newRows[0].artist_id === n1.id &&
  JSON.parse(newRows[0].detail).ref === REF1 && JSON.parse(newRows[0].detail).via === 'existing_account' && !newRows[0].detail.includes('abstract painter'), JSON.stringify(newRows));
check('E10 it stays a private draft: no submission, no version, nothing queued for publishing',
  (await q1('SELECT COUNT(*) AS n FROM submissions WHERE artist_id=?', n1.id)).n === 0 && (await q1('SELECT COUNT(*) AS n FROM versions WHERE artist_id=?', n1.id)).n === 0 &&
  (await q1('SELECT COUNT(*) AS n FROM publish_queue WHERE artist_id=?', n1.id)).n === 0 && a.first_published_at === null);

/* ---- 2 · repeat use: running it again changes nothing */
const snap = JSON.stringify(await row(n1.id));
r = await prefill(n1.id, REF1);
check('E11 repeat use with the same reference is harmless: nothing filled, nothing changed, reported as "nothing to fill"',
  r.s === 200 && r.j.fields.length === 0 && r.j.linked === false && JSON.stringify(await row(n1.id)) === snap && r.j.skipped.bio === 'already filled in', JSON.stringify(r.j));
check('E12 the repeat is still recorded in the audit log ("no empty field to fill")',
  (await q1("SELECT detail FROM audit WHERE artist_id=? AND action='profile_prefill_not_applied' ORDER BY id DESC", n1.id)).detail.includes('no empty field'));

/* ---- 3 · never overwrite: the artist's own words stay */
const REF2 = 'F25-261111-A0A0A2';
await putApp(REF2, APP('Owen Synthetic'));
const o = await create('Owen Synthetic', 'owen@example.test');
await call('PUT', '/api/me/profile', 'owen@example.test', { bio: 'Owen wrote this biography himself, and it must never be replaced.', website: 'https://owen-own.example/' });
r = await prefill(o.id, REF2); a = await row(o.id);
check('E13 fields the artist already filled are never overwritten; only the empty ones are filled',
  r.s === 200 && a.bio.startsWith('Owen wrote this') && a.website === 'https://owen-own.example/' && a.medium === 'painting' && a.county === 'Wicklow' && a.instagram === 'example_artist' &&
  r.j.skipped.bio === 'already filled in' && r.j.skipped.website === 'already filled in', JSON.stringify([r.j, a]));

/* ---- 4 · agreements are preserved: an artist who has signed in and accepted */
const REF3 = 'F25-261111-A0A0A3';
await putApp(REF3, APP('Aine Signed'));
const s3 = await create('Aine Signed', 'aine.signed@example.test');
await acceptAgreement(mf, url, 'aine.signed@example.test');
const acc = JSON.stringify(await qa('SELECT * FROM agreement_acceptances WHERE artist_id=? ORDER BY rowid', s3.id));
const st3 = (await row(s3.id));
r = await prefill(s3.id, REF3); a = await row(s3.id);
check('E14 agreement acceptances are untouched (identical rows) and the signed-in account keeps its status and licence',
  r.s === 200 && acc !== '[]' && JSON.stringify(await qa('SELECT * FROM agreement_acceptances WHERE artist_id=? ORDER BY rowid', s3.id)) === acc &&
  a.account_status === st3.account_status && a.licence_version === st3.licence_version && a.licence_accepted_at === st3.licence_accepted_at, JSON.stringify([r.j, acc.slice(0, 80)]));

/* ---- 5 · refusals: nothing is filled or linked */
const REF4 = 'F25-261111-A0A0A4';
await putApp(REF4, APP('Wanda Applicant'));
const w = await create('Someone Else', 'someone@example.test');
r = await prefill(w.id, REF4); a = await row(w.id);
check('E15 a mismatched name is refused (409): nothing filled, reference not linked, reason recorded',
  r.s === 409 && /name on the application does not match/.test(r.j.error || r.t) && a.bio === null && a.application_ref === null &&
  (await q1("SELECT detail FROM audit WHERE artist_id=? AND action='profile_prefill_not_applied'", w.id)).detail.includes('does not match'), JSON.stringify(r.j));
const REF5 = 'F25-261111-A0A0A5';
await putApp(REF5, APP('Cara Conflict'));
const c = await create('Cara Conflict', 'cara@example.test', 'F25-261111-FFFFF1');    // linked to a different application
r = await prefill(c.id, REF5); a = await row(c.id);
check('E16 an account already linked to a DIFFERENT application is refused; its reference is not replaced',
  r.s === 409 && /already linked to application F25-261111-FFFFF1/.test(r.j.error || r.t) && a.application_ref === 'F25-261111-FFFFF1' && a.bio === null, JSON.stringify(r.j));
const dup = await create('Nora Synthetic', 'nora.second@example.test', null, 'nora-synthetic-two');
r = await prefill(dup.id, REF1); a = await row(dup.id);
check('E17 an application already linked to ANOTHER account is refused (no second account gets the same details)',
  r.s === 409 && /already linked to another account/.test(r.j.error || r.t) && a.bio === null && a.application_ref === null, JSON.stringify(r.j));
const REF6 = 'F25-261111-A0A0A6';
await putApp(REF6, APP('Ended Artist'));
const e = await create('Ended Artist', 'ended@example.test');
await db.prepare("UPDATE artists SET account_status='ended' WHERE id=?").bind(e.id).run();
r = await prefill(e.id, REF6); a = await row(e.id);
check('E18 an ended account is refused (409) and left as it was', r.s === 409 && /has ended/.test(r.j.error || r.t) && a.bio === null && a.application_ref === null, JSON.stringify(r.j));
const g = await create('Gina Nocopy', 'gina@example.test');
r = await prefill(g.id, 'F25-261111-0000AA');
check('E19 an application with no Studio copy is refused with the reason; nothing linked', r.s === 409 && /no Studio copy/.test(r.j.error || r.t) && (await row(g.id)).application_ref === null, JSON.stringify(r.j));
r = await prefill(g.id, 'not-a-reference');
check('E20 a malformed reference is refused (400)', r.s === 400);
r = await prefill('a00000000000', REF6);
check('E21 an unknown account is refused (404)', r.s === 404);
r = await prefill(n1.id, REF1, 'nora@example.test');
check('E22 only the founder can use it: an artist calling it is refused', r.s === 401 || r.s === 403, r.s);

/* ---- 6 · an account created WITH the reference whose copy appeared later (same reference): allowed */
const REF7 = 'F25-261111-A0A0A7';
const l = await create('Lia Later', 'lia@example.test', REF7);                     // created before the copy existed: nothing filled
check('E23 (setup) account created with a reference whose copy did not exist yet: nothing filled', (await row(l.id)).bio === null);
await putApp(REF7, APP('Lia Later'));
r = await prefill(l.id, REF7); a = await row(l.id);
check('E24 the action then fills it; the existing (same) reference is kept, not re-linked', r.s === 200 && r.j.linked === false && a.application_ref === REF7 && a.medium === 'painting', JSON.stringify(r.j));

/* ---- 7 · duplicate prevention at creation is unchanged */
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Nora Synthetic', email: 'nora@example.test', application_ref: REF1, founding: true });
check('E25 creating a second account for an existing email is still refused (409); the action is the way to fill an existing one',
  r.s === 409 && (await q1("SELECT COUNT(*) AS n FROM artists WHERE email='nora@example.test'")).n === 1);

/* ---- 8 · the Review Desk shows the action */
r = await call('GET', '/assets/admin.js', FOUNDER);
check('E26 the Review Desk has the "Start profile from application" action, which states that no email is sent',
  r.s === 200 && r.t.includes('Start profile from application') && r.t.includes('/prefill') && r.t.includes('no email is sent'), r.s);

const pass = results.filter(Boolean).length;
console.log(`\nSTART PROFILE FROM APPLICATION · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
await mf.dispose();
process.exit(pass === results.length ? 0 : 1);
