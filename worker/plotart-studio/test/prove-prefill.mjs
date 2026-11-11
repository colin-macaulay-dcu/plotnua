// PROVE · PlotArt Studio · profile pre-fill from a Founding 25 application (founder decision 11 Nov 2026).
// Synthetic applicants only; the real Worker runs locally (Miniflare/workerd) with a local D1 and R2. Nothing here
// touches Cloudflare, Airtable, the production database or any real artist.        node test/prove-prefill.mjs
// The "Nessa-shaped" fixture copies the SHAPE of a real application (lower-case county, @handle, long biography,
// additional information, five images) with invented text, so the real case is exercised without real data.
import { start, token, FOUNDER } from './local.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const { mf, url, db } = await start({ port: 8811 });
const AB = await mf.getR2Bucket('APPLICATIONS', 'studio');
const call = async (method, path, who, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' };
  if (who) h['Cf-Access-Jwt-Assertion'] = token(who);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const row = id => db.prepare('SELECT * FROM artists WHERE id=?').bind(id).first();
const auditOf = async (id, action) => (await db.prepare('SELECT * FROM audit WHERE artist_id=? AND action=?').bind(id, action).all()).results;
const mail = to => db.prepare('SELECT * FROM mail_capture WHERE to_addr=? ORDER BY at DESC').bind(to).first();
const putApp = async (ref, app, images = 5) => {
  for (let n = 1; n <= images; n++) await AB.put(`applications/${ref}/${n}.jpg`, new Uint8Array([0xff, 0xd8, 0xff, n]), { httpMetadata: { contentType: 'image/jpeg' } });
  await AB.put(`applications/${ref}/application.json`, JSON.stringify({ application_ref: ref, submitted_at: '2026-11-11T13:08:52.000Z',
    images: Array.from({ length: images }, (_, i) => ({ file: `${i + 1}.jpg`, w: 2000, h: 1500 })), ...app }));
};
const create = (name, email, ref, founding = true, slug) => call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, application_ref: ref, founding, ...(slug ? { slug } : {}) });

const BIO = 'I am an abstract painter living in a coastal county. My work celebrates rhythm, colour and the energy of place. '.repeat(7).trim(); // ~800 chars
const EXTRA = 'Represented by an online gallery; group shows in several countries; shortlisted for a residency award.';

console.log('PROVE · PlotArt Studio · profile pre-fill from an application');

/* ---- 1 · the Nessa-shaped case: every transferable field present, plus additional information and five images */
const REF_N = 'F25-261111-B3DFF0';
await putApp(REF_N, { artist_name: 'Nessa Synthetic', medium: 'painting', region: 'wicklow', bio: BIO,
  portfolio: 'https://www.nessa-synthetic.example/', website: 'https://www.nessa-synthetic.example/', social_link: '@nessasyntheticart',
  additional_info: EXTRA, airtable_record: 'recABCDEFGHIJKLMN' });
const N_EMAIL = 'nessa.synthetic@example.test';
let r = await create('Nessa Synthetic', N_EMAIL, REF_N);
const nid = r.j.id; let a = await row(nid);
check('P1 creating an account with an application reference fills biography, medium, county, website and Instagram',
  r.s === 200 && JSON.stringify(r.j.prefill.fields) === JSON.stringify(['bio', 'medium', 'county', 'website', 'instagram']) &&
  a.bio === BIO && a.medium === 'painting' && a.county === 'Wicklow' && a.website === 'https://www.nessa-synthetic.example/' && a.instagram === 'nessasyntheticart',
  JSON.stringify([r.j, a]));
check('P2 values go through the Studio\'s own rules: county capitalised to the Studio list, "@" removed from the Instagram handle',
  a.county === 'Wicklow' && !a.instagram.startsWith('@'));
check('P3 public county visibility stays OFF (county_public = 0)', a.county_public === 0, a.county_public);
check('P4 nothing else is transferred: statement, practice and portrait stay empty; "additional information" appears nowhere',
  a.statement === null && a.practice === null && a.portrait_image_id === null && !JSON.stringify(a).includes('residency'), JSON.stringify(a));
const imgs = (await db.prepare('SELECT COUNT(*) AS n FROM images WHERE artist_id=?').bind(nid).first()).n;
const works = (await db.prepare('SELECT COUNT(*) AS n FROM artworks WHERE artist_id=?').bind(nid).first()).n;
check('P5 no application image is transferred: the account has 0 images and 0 artworks', imgs === 0 && works === 0, JSON.stringify({ imgs, works }));
const stillThere = await AB.get(`applications/${REF_N}/1.jpg`);
check('P6 the application\'s review copy and images are left exactly where they were (read only)', !!stillThere);
const versions = (await db.prepare('SELECT COUNT(*) AS n FROM versions WHERE artist_id=?').bind(nid).first()).n;
const queue = (await db.prepare('SELECT COUNT(*) AS n FROM publish_queue WHERE artist_id=?').bind(nid).first()).n;
const subs = (await db.prepare('SELECT COUNT(*) AS n FROM submissions WHERE artist_id=?').bind(nid).first()).n;
check('P7 the pre-fill is a private draft: no submission, no approved version, nothing queued for publishing, not published',
  versions === 0 && queue === 0 && subs === 0 && a.first_published_at === null && a.account_status === 'invited', JSON.stringify({ versions, queue, subs }));
const au = await auditOf(nid, 'profile_prefilled_from_application');
const det = au[0] && JSON.parse(au[0].detail);
check('P8 the audit log records the pre-fill: who, which application, which fields (field names only, never the values)',
  au.length === 1 && au[0].actor === FOUNDER && det.ref === REF_N && det.fields.length === 5 && !au[0].detail.includes('abstract painter') && !au[0].detail.includes('nessasynthetic'),
  JSON.stringify(au));
let m = await mail(N_EMAIL);
check('P9 the invitation explains the profile was started from the application, names the fields, and asks the artist to review it',
  m && /started your profile using the details from your Founding 25 application: your biography, medium, county, website and Instagram\./.test(m.body) &&
  /Please review these when you sign in/.test(m.body) && /stays private/.test(m.body) && /not shown publicly unless you choose/.test(m.body) &&
  /images you sent with your application aren't used/.test(m.body), m && m.body);
check('P10 the rest of the invitation is unchanged (sign-in link, exact email, one-time code, published only after approval)',
  m && m.body.includes(url) && m.body.includes(N_EMAIL) && /one-time code/.test(m.body) && /only be published once you've submitted it and PlotArt has approved it/.test(m.body) &&
  m.subject === 'Your PlotArt Studio is ready' && m.reply_to === 'hello@plotnua.ie');

/* ---- 2 · the artist sees it and can change it with the normal Profile form; their edits stand */
r = await call('GET', '/api/me', N_EMAIL);
check('P11 the artist sees the pre-filled profile in their Studio (GET /api/me)', r.s === 200 && r.j.artist.bio === BIO && r.j.artist.county === 'Wicklow' && r.j.artist.county_public === 0);
r = await call('PUT', '/api/me/profile', N_EMAIL, { bio: 'My own rewritten biography, longer than forty characters, in my words.', county_public: true });
a = await row(nid);
check('P12 the artist edits normally: their change replaces the draft, and only they can switch county visibility on',
  r.s === 200 && a.bio.startsWith('My own rewritten') && a.county_public === 1);

/* ---- 3 · never overwrite: an account whose fields already hold text keeps them */
const REF_O = 'F25-261111-0A0A0A';
await putApp(REF_O, { artist_name: 'Orla Existing', medium: 'printmaking', region: 'cork', bio: BIO, website: 'https://orla-app.example/', social_link: '@orla_app' });
const O_EMAIL = 'orla.existing@example.test';
// simulate an account that already has information: created without a reference, profile written, then pre-fill run
r = await create('Orla Existing', O_EMAIL, null); const oid = r.j.id;
check('P13 without an application reference nothing is pre-filled and no pre-fill audit entry is written',
  r.j.prefill.fields.length === 0 && (await auditOf(oid, 'profile_prefill_not_applied')).length === 0 && (await row(oid)).bio === null);
await call('PUT', '/api/me/profile', O_EMAIL, { bio: 'Orla wrote this biography herself, and it must never be replaced.', website: 'https://orla-own.example/' });
// a second account for the same person is refused, exactly as before (no duplicate, no pre-fill)
r = await create('Orla Existing', O_EMAIL, REF_O);
a = await row(oid);
check('P14 creating a second account with the same email is still refused (409), and the existing profile is untouched',
  r.s === 409 && a.bio.startsWith('Orla wrote this') && a.website === 'https://orla-own.example/' && a.medium === null);
{ // field-level: run the SQL guard against a half-filled account through a fresh creation whose row is pre-seeded by a trigger
  await db.exec("CREATE TRIGGER t_seed AFTER INSERT ON artists WHEN NEW.email = 'pat.partial@example.test' BEGIN UPDATE artists SET bio = 'Pat already has a biography of their own, written earlier.', website = 'https://pat-own.example/' WHERE id = NEW.id; END;");
  const REF_P = 'F25-261111-0B0B0B';
  await putApp(REF_P, { artist_name: 'Pat Partial', medium: 'sculpture', region: 'galway', bio: BIO, website: 'https://pat-app.example/', social_link: 'https://www.instagram.com/pat.partial/' });
  r = await create('Pat Partial', 'pat.partial@example.test', REF_P);
  a = await row(r.j.id);
  await db.exec('DROP TRIGGER t_seed;');
  check('P15 fields that already hold text are never overwritten; only the empty ones are filled (and the skip is recorded)',
    a.bio.startsWith('Pat already has') && a.website === 'https://pat-own.example/' && a.medium === 'sculpture' && a.county === 'Galway' &&
    a.instagram === 'pat.partial' && r.j.prefill.skipped.bio === 'already filled in' && r.j.prefill.skipped.website === 'already filled in', JSON.stringify([r.j.prefill, a]));
  check('P16 an instagram.com profile link becomes the handle the Studio stores', a.instagram === 'pat.partial');
}

/* ---- 4 · existing validation rules are kept: a value the Profile form would refuse is skipped, never altered */
const REF_V = 'F25-261111-0C0C0C';
await putApp(REF_V, { artist_name: 'Val Checks', medium: 'digital', region: 'outside_ireland', bio: 'Call me on 087 123 4567 for my biography and prices please.',
  website: 'http://not-secure.example/', social_link: 'https://www.facebook.com/val' });
r = await create('Val Checks', 'val.checks@example.test', REF_V);
a = await row(r.j.id);
check('P17 values the Studio would refuse are skipped (phone number in biography, non-https website, unknown county, non-Instagram link)',
  a.bio === null && a.website === null && a.county === null && a.instagram === null &&
  r.j.prefill.skipped.bio === 'did not pass Studio checks' && r.j.prefill.skipped.website === 'did not pass Studio checks' &&
  r.j.prefill.skipped.county === 'did not pass Studio checks' && r.j.prefill.skipped.instagram === 'not an Instagram handle', JSON.stringify([r.j.prefill, a]));
check('P18 the application\'s "digital" medium maps to the Studio\'s "digital and new media"', a.medium === 'digital_new_media', a.medium);
m = await mail('val.checks@example.test');
check('P19 the invitation lists only what was actually filled ("your medium")', m && /application: your medium\. Please review/.test(m.body), m && m.body);
const REF_T = 'F25-261111-0D0D0D';
await putApp(REF_T, { artist_name: 'Tess Short', medium: 'textiles', region: 'mayo', bio: 'Too short.', social_link: '@' + 'x'.repeat(40) });
r = await create('Tess Short', 'tess.short@example.test', REF_T); a = await row(r.j.id);
check('P20 a biography below the Studio minimum, and an over-long handle, are skipped rather than trimmed or padded',
  a.bio === null && a.instagram === null && a.medium === 'textiles' && a.county === 'Mayo', JSON.stringify([r.j.prefill, a]));

/* ---- 5 · safeguards against the wrong person's details */
const REF_W = 'F25-261111-0E0E0E';
await putApp(REF_W, { artist_name: 'Wanda Applicant', medium: 'painting', region: 'kerry', bio: BIO });
r = await create('Someone Else', 'someone.else@example.test', REF_W); a = await row(r.j.id);
check('P21 a reference whose application name does not match the name entered fills nothing (account still created, reason given)',
  r.s === 200 && a.bio === null && a.county === null && r.j.prefill.fields.length === 0 && /name on the application does not match/.test(r.j.prefill.reason), JSON.stringify(r.j));
const na = await auditOf(r.j.id, 'profile_prefill_not_applied');
check('P22 a pre-fill that was not applied is also recorded in the audit log, with the reason', na.length === 1 && /does not match/.test(na[0].detail));
m = await mail('someone.else@example.test');
check('P23 when nothing was pre-filled the invitation is exactly the previous wording (no pre-fill paragraph)',
  m && !/started your profile/.test(m.body) && /one-time code; there's no password\.\n\nYour gallery will only be published/.test(m.body), m && m.body);
r = await create('Nessa Synthetic', 'nessa.second@example.test', REF_N, true, 'nessa-synthetic-two'); a = await row(r.j.id);
check('P24 an application already linked to another account is never used again', a.bio === null && /already linked/.test(r.j.prefill.reason), JSON.stringify(r.j.prefill));
r = await create('Róisín Ó Briain', 'roisin@example.test', (await (async () => { const ref = 'F25-261111-0F0F0F'; await putApp(ref, { artist_name: 'Roisin O Briain', medium: 'drawing', region: 'Donegal', bio: BIO }); return ref; })()));
a = await row(r.j.id);
check('P25 names match regardless of accents, capitals and spacing (Róisín Ó Briain = Roisin O Briain)', a.medium === 'drawing' && a.county === 'Donegal', JSON.stringify(r.j.prefill));
r = await create('Gary Gone', 'gary.gone@example.test', 'F25-261111-999999'); a = await row(r.j.id);
check('P26 a reference with no Studio copy (e.g. an application sent without images) creates the account normally, fills nothing',
  r.s === 200 && a && a.bio === null && /no Studio copy/.test(r.j.prefill.reason) && r.j.invitation_sent === true, JSON.stringify(r.j));
r = await create('Bad Ref', 'bad.ref@example.test', 'not-a-reference');
check('P27 a malformed reference is still refused before anything is created (unchanged rule)', r.s === 400 && !(await db.prepare("SELECT id FROM artists WHERE email='bad.ref@example.test'").first()));
await AB.put('applications/F25-261111-1A1A1A/application.json', '{not json');
r = await create('Broken Copy', 'broken@example.test', 'F25-261111-1A1A1A');
check('P28 an unreadable application copy never blocks account creation', r.s === 200 && r.j.prefill.fields.length === 0 && r.j.invitation_sent === true, JSON.stringify(r.j));
r = await call('POST', '/api/admin/artists', 'nessa.synthetic@example.test', { display_name: 'Hacker', email: 'h@example.test', application_ref: REF_W });
check('P29 only the founder can create accounts (an artist is refused), so only the founder can trigger a pre-fill', r.s === 403 || r.s === 401, r.s);

const pass = results.filter(Boolean).length;
console.log(`\nPROFILE PRE-FILL · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
await mf.dispose();
process.exit(pass === results.length ? 0 : 1);
