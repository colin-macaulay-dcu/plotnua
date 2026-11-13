// PROVE · PlotArt Studio · PlotArt artist applications (PA-AP-…), Gallery Artist Programme Phase 3 (development 13 Nov 2026).
// Synthetic applicants only; the real Worker runs locally (Miniflare/workerd) with a local D1 and R2. Nothing here touches
// Cloudflare, Airtable or any real artist.        node test/prove-artist-applications.mjs
// Proves: the founder reviews PA-AP applications beside Founding 25 ones; only the founder can; an application never
// creates an account; a PA-AP application can only lead to a Gallery Artist invitation (with pre-fill), and only from
// the founder's own action; Founding 25 references keep working exactly as before.
import { start, token, FOUNDER } from './local.mjs';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const { mf, url, db } = await start({ port: 8897 });
const AB = await mf.getR2Bucket('APPLICATIONS', 'studio');
const call = async (method, path, who, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' };
  if (who) h['Cf-Access-Jwt-Assertion'] = token(who);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html or image */ }
  return { s: r.status, j, t };
};
const putApp = async (ref, app, images = 3) => {
  for (let n = 1; n <= images; n++) await AB.put(`applications/${ref}/${n}.jpg`, new Uint8Array([0xff, 0xd8, 0xff, n]), { httpMetadata: { contentType: 'image/jpeg' } });
  await AB.put(`applications/${ref}/application.json`, JSON.stringify({ application_ref: ref, submitted_at: '2026-11-20T10:00:00.000Z', source: 'plotart_gallery_application_form',
    images: Array.from({ length: images }, (_, i) => ({ file: `${i + 1}.jpg`, w: 2000, h: 1500 })), ...app }));
};
const count = async () => (await db.prepare('SELECT COUNT(*) n FROM artists').first()).n;
const BIO = 'I make large ink drawings of hedgerows and field boundaries, working outdoors through the seasons. '.repeat(3).trim();

console.log('PROVE · PlotArt Studio · PlotArt artist applications (PA-AP)');
const GA = 'PA-AP-261120-0A1B2C', F25 = 'F25-261029-0D1E2F';
await putApp(GA, { artist_name: 'Gráinne Synthetic', medium: 'drawing', region: 'sligo', bio: BIO, website: 'https://grainne.example/', social_link: '@grainnedraws', airtable_record: 'recABCDEFGHIJKLMN' });
await putApp(F25, { artist_name: 'Fionn Synthetic', medium: 'painting', region: 'cork', bio: BIO });
const n0 = await count();

let r = await call('GET', '/api/admin/applications', FOUNDER);
check('A1 the founder sees PlotArt (PA-AP) applications beside Founding 25 ones', r.s === 200 && r.j.items.map(i => i.ref).sort().join() === [F25, GA].sort().join(), JSON.stringify(r.j));
check('A2 receiving or reviewing an application never creates an account', await count() === n0);
r = await call('GET', '/api/admin/applications/' + GA, FOUNDER);
check('A3 the founder can open a PA-AP application (statement, links, images); no email address is shown', r.s === 200 && r.j.application.artist_name === 'Gráinne Synthetic' && r.j.application.images.length === 3 && !r.t.includes('@example'), r.t.slice(0, 300));
check('A4 without APP_AIRTABLE_TABLE_URL there is no Airtable link (the page says to find it by its reference)', r.j.application.airtable === null);
r = await call('GET', `/admin/applications/${GA}/img/1.jpg`, FOUNDER);
check('A5 its images are served to the founder only', r.s === 200);
for (const [m, p] of [['GET', '/api/admin/applications'], ['GET', '/api/admin/applications/' + GA], ['GET', `/admin/applications/${GA}/img/1.jpg`], ['POST', `/api/admin/applications/${GA}/erase`]]) {
  r = await call(m, p, 'someone@example.test');
  check(`A6 ${m} ${p.replace(GA, 'PA-AP-…')} is refused to anyone but the founder`, r.s === 403 || r.s === 401, r.s);
}
r = await call('GET', '/api/admin/applications/PA-AP-261120-0a1b2c', FOUNDER);
check('A7 a malformed reference is not a route (404)', r.s === 404);

// invitations: only the founder's own action, and only as a Gallery Artist
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Gráinne Synthetic', email: 'grainne@example.test', application_ref: GA, programme: 'founding' });
check('I1 a PA-AP application cannot lead to a Founding Artist invitation (409, nothing created)', r.s === 409 && /Gallery Artist/.test(r.j.error) && await count() === n0, JSON.stringify(r.j));
r = await call('POST', '/api/admin/artists', 'grainne@example.test', { display_name: 'Gráinne Synthetic', email: 'grainne@example.test', application_ref: GA, programme: 'gallery_artist' });
check('I2 nobody but the founder can create the invitation', (r.s === 403 || r.s === 401) && await count() === n0);
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Gráinne Synthetic', email: 'grainne@example.test', application_ref: GA, programme: 'gallery_artist' });
const gid = r.j.id, ga = await db.prepare('SELECT * FROM artists WHERE id=?').bind(gid).first();
const terms = await db.prepare('SELECT * FROM artist_terms WHERE artist_id=?').bind(gid).first();
check('I3 the founder invites the accepted applicant as a Gallery Artist (15% terms row), linked to the application', r.s === 200 && ga.founding === 0 && ga.application_ref === GA && terms && terms.commission_bp === 1500, JSON.stringify(r.j));
check('I4 the profile starts from the application: biography, medium, county, website, Instagram; county stays private',
  JSON.stringify(r.j.prefill.fields) === JSON.stringify(['bio', 'medium', 'county', 'website', 'instagram']) && ga.county === 'Sligo' && ga.county_public === 0 && ga.instagram === 'grainnedraws', JSON.stringify(r.j.prefill));
const m = await db.prepare('SELECT * FROM mail_capture WHERE to_addr=?').bind('grainne@example.test').first();
check('I5 the invitation says "your PlotArt application" and names the Gallery Artist Agreement', m && /details from your PlotArt application/.test(m.body) && /joining PlotArt as a Gallery Artist/.test(m.body) && !/Founding 25 application/.test(m.body));
const imgs = (await db.prepare('SELECT COUNT(*) n FROM images WHERE artist_id=?').bind(gid).first()).n;
check('I6 no application image becomes a gallery image', imgs === 0);

// Founding 25 references behave exactly as before
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Fionn Synthetic', email: 'fionn@example.test', application_ref: F25, programme: 'founding' });
const fm = await db.prepare('SELECT * FROM mail_capture WHERE to_addr=?').bind('fionn@example.test').first();
check('F1 a Founding 25 reference still leads to a Founding Artist invitation, with its own wording', r.s === 200 && r.j.prefill.fields.length > 0 && /Founding 25 application/.test(fm.body) && !/Gallery Artist/.test(fm.body));
const fid = r.j.id;
r = await call('POST', `/api/admin/artists/${fid}/prefill`, FOUNDER, { application_ref: 'PA-AP-261120-0F0F0F' });
check('F2 a PA-AP application can never start the profile of a Founding Artist account (409)', r.s === 409 && /Gallery Artist/.test(r.j.error), JSON.stringify(r.j));
r = await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Bad Ref', email: 'bad@example.test', application_ref: 'XX-261120-0A1B2C', programme: 'gallery_artist' });
check('F3 any other reference shape is refused', r.s === 400 && /PA-AP-YYMMDD/.test(r.j.error));

// erasing images under the retention rules
r = await call('POST', `/api/admin/applications/${GA}/erase`, FOUNDER, {});
const left = (await AB.list({ prefix: `applications/${GA}/` })).objects.length;
check('E1 the founder can erase a PA-AP application\'s images when it is closed', r.s === 200 && left === 0, JSON.stringify([r.s, left]));
await mf.dispose();
const fail = results.filter(x => !x).length;
console.log(`\nPLOTART ARTIST APPLICATIONS · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
