// PROVE · safe completion of an earlier Founding Artist invitation with an open permanent number (27 Nov 2026).
// Local Miniflare/D1 only; ENVIRONMENT is staging so the production refusal and grandfathering rules are exercised.
import { readFileSync } from 'node:fs';
import { start, token, FOUNDER, TEST_JWKS } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';

const results = [];
const check = (name, ok, detail = '') => {
  results.push(!!ok);
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${!ok && detail ? `  [${String(detail).slice(0, 600)}]` : ''}`);
};
const headers = email => ({ 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(email) });
const call = S => async (method, path, email, body) => {
  const r = await S.mf.dispatchFetch(S.url + path, { method, headers: headers(email), body: body === undefined ? undefined : JSON.stringify(body) });
  const text = await r.text(); let json = null; try { json = JSON.parse(text); } catch { /* html */ }
  return { status: r.status, json, text };
};
const certs = req => new URL(req.url).pathname === '/cdn-cgi/access/certs'
  ? new Response(TEST_JWKS, { headers: { 'Content-Type': 'application/json' } }) : new Response('no', { status: 404 });

console.log('PROVE · grandfathered Founding invitation');
const S = await start({ port: 8932, env: { ENVIRONMENT: 'staging', ACCESS_JWKS_JSON: '' }, outbound: certs });
const api = call(S), { db } = S;
try {
  // Exercise the live transition as well as the pre-R2 schema: even with R2 installed for new Gallery Artists, the
  // grandfathered artist must never receive an artist_agreement_versions row.
  for (const sql of statements(readFileSync(new URL('../migrations/0030_artist_agreement_r2.sql', import.meta.url), 'utf8'))) await db.prepare(sql).run();
  // schema.sql contains 0031 for fresh installations. Recreate the production transition here: remove only that empty
  // new table, seed an existing Founding Artist, then apply the migration file and prove that existing records do not move.
  await db.prepare('DROP TABLE founding_artist_numbers').run();
  await seedPublished(db, { id: 'aexisting', slug: 'existing-founder', email: 'existing@example.test', name: 'Existing Founder', works: 1, number: 4 });
  const beforeMigration = JSON.stringify(await db.prepare("SELECT id, founding_number, licence_version, licence_accepted_at FROM artists WHERE id='aexisting'").first());
  for (const sql of statements(readFileSync(new URL('../migrations/0031_open_founding_numbers.sql', import.meta.url), 'utf8'))) await db.prepare(sql).run();
  check('G0 migration 0031 creates only the additive open-number table and leaves an existing Founding Artist unchanged', beforeMigration === JSON.stringify(
    await db.prepare("SELECT id, founding_number, licence_version, licence_accepted_at FROM artists WHERE id='aexisting'").first()));
  await db.prepare(`INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at)
    VALUES (12,NULL,1,'Jonathan Dickson · accepted before closure','2026-11-20T12:00:00.000Z')`).run();
  const before = JSON.stringify({
    artist: await db.prepare("SELECT * FROM artists WHERE id='aexisting'").first(),
    works: (await db.prepare("SELECT * FROM artworks WHERE artist_id='aexisting' ORDER BY id").all()).results,
    acceptances: (await db.prepare("SELECT * FROM agreement_acceptances WHERE artist_id='aexisting' ORDER BY id").all()).results,
  });

  let r = await api('POST', '/api/admin/artists', FOUNDER, { display_name: 'Generic Founding', email: 'generic@example.test', programme: 'founding' });
  check('G1 the general Founding route stays closed', r.status === 409 && /initiative has ended/.test(r.json?.error || r.text));

  r = await api('GET', '/api/admin/overview', FOUNDER);
  check('G2 only the founder sees the private reservation evidence and whether open Founding numbers are installed', r.status === 200
    && r.json.founding_reservations.length === 1 && r.json.founding_reservations[0].position === 12
    && r.json.founding_reservations[0].note.includes('Jonathan Dickson')
    && r.json.open_founding_numbers_installed === true);

  const base = { display_name: 'Jonathan Dickson', email: 'jonathan@example.test', programme: 'founding', application_ref: 'F25-261120-A1B2C3',
    grandfathered_founding: { founding_number: 29, confirm: 'COMPLETE EARLIER FOUNDING INVITATION' }, galleries: ['spaces'] };
  r = await api('POST', '/api/admin/artists', FOUNDER, { ...base, grandfathered_founding: { ...base.grandfathered_founding, confirm: 'yes' } });
  check('G3 the server requires the exact, explicit grandfathering confirmation and writes nothing on refusal', r.status === 400
    && !(await db.prepare("SELECT id FROM artists WHERE email='jonathan@example.test'").first()));
  r = await api('POST', '/api/admin/artists', FOUNDER, { ...base, application_ref: 'PA-AP-261120-ABCDEF' });
  check('G4 a new-programme application cannot be used to claim old Founding terms', r.status === 400
    && !(await db.prepare("SELECT id FROM artists WHERE email='jonathan@example.test'").first()));
  r = await api('POST', '/api/admin/artists', FOUNDER, { ...base, grandfathered_founding: { ...base.grandfathered_founding, founding_number: 5 } });
  check('G4b the open numbering cannot take or rewrite a historical 1-25 number', r.status === 400
    && !(await db.prepare("SELECT id FROM artists WHERE email='jonathan@example.test'").first()));

  r = await api('POST', '/api/admin/artists', FOUNDER, base);
  const id = r.json?.id;
  const artist = id && await db.prepare('SELECT * FROM artists WHERE id=?').bind(id).first();
  const openNumber = id && await db.prepare('SELECT founding_number FROM founding_artist_numbers WHERE artist_id=?').bind(id).first();
  const position = await db.prepare('SELECT * FROM gallery_positions WHERE position=12').first();
  const terms = id && await db.prepare('SELECT * FROM artist_terms WHERE artist_id=?').bind(id).first();
  const version = id && await db.prepare('SELECT * FROM artist_agreement_versions WHERE artist_id=?').bind(id).first();
  const memberships = id ? (await db.prepare('SELECT gallery_id, state FROM gallery_memberships WHERE artist_id=? ORDER BY gallery_id').bind(id).all()).results : [];
  check('G5 the valid earlier invitation creates one Founding account as No. 29 without changing a gallery-order reservation', r.status === 200 && artist?.founding === 1
    && artist.founding_number === null && openNumber?.founding_number === 29 && artist.application_ref === base.application_ref
    && position.artist_id === null && position.reserved === 1 && position.note.includes('Jonathan Dickson'), JSON.stringify({ r: r.status, response: r.json, artist, openNumber, position }));
  check('G6 it does not assign Gallery Artist commission terms or the R2 agreement version, and keeps the chosen gallery invitation', !terms && !version
    && JSON.stringify(memberships) === JSON.stringify([{ gallery_id: 'spaces', state: 'founder_approved' }]), JSON.stringify({ terms, version, memberships }));
  const agreement = await api('GET', '/api/agreement', base.email);
  check('G7 the artist is routed to the original Founding Artist Agreement and Image Licence', agreement.status === 200
    && agreement.json.programme === 'founding'
    && JSON.stringify(agreement.json.required) === JSON.stringify(['PA-FAA-2026-11', 'PA-GPIL-2026-11']));
  const [overview, participation, opportunities, agreementAdmin] = await Promise.all([
    api('GET', '/api/admin/overview', FOUNDER), api('GET', '/api/admin/participation', FOUNDER),
    api('GET', '/api/admin/opportunities', FOUNDER), api('GET', `/api/admin/artists/${id}/agreement`, FOUNDER),
  ]);
  check('G7b founder views consistently show Jonathan as Founding Artist No. 29',
    overview.json.artists.find(a => a.id === id)?.founding_number === 29
    && participation.json.items.find(a => a.id === id)?.founding_number === 29
    && opportunities.json.items.find(a => a.id === id)?.founding_number === 29
    && agreementAdmin.json.artist.founding_number === 29);
  check('G8 every pre-existing artist, artwork and acceptance row is byte-for-byte unchanged', before === JSON.stringify({
    artist: await db.prepare("SELECT * FROM artists WHERE id='aexisting'").first(),
    works: (await db.prepare("SELECT * FROM artworks WHERE artist_id='aexisting' ORDER BY id").all()).results,
    acceptances: (await db.prepare("SELECT * FROM agreement_acceptances WHERE artist_id='aexisting' ORDER BY id").all()).results,
  }));
  const audit = await db.prepare("SELECT detail FROM audit WHERE artist_id=? AND action='invite'").bind(id).first();
  check('G9 the exceptional basis and permanent number are audit-logged without claiming or exposing a reservation', audit && /"grandfathered":true/.test(audit.detail)
    && !/"reservation_position"/.test(audit.detail) && /"founding_number":29/.test(audit.detail) && !/Jonathan Dickson/.test(audit.detail), audit?.detail);

  r = await api('POST', '/api/admin/artists', FOUNDER, { ...base, display_name: 'Second Claim', email: 'second@example.test' });
  check('G10 the permanent number cannot be reused', r.status === 409 && !(await db.prepare("SELECT id FROM artists WHERE email='second@example.test'").first()));
  await db.prepare(`INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at)
    VALUES (13,NULL,1,'another earlier invitation','2026-11-20T12:00:00.000Z')`).run();
  r = await api('POST', '/api/admin/artists', FOUNDER, { ...base, display_name: 'Duplicate Number', email: 'duplicate@example.test',
    grandfathered_founding: { position: 13, founding_number: 29, confirm: 'COMPLETE EARLIER FOUNDING INVITATION' } });
  check('G11 a duplicate number is refused even when an optional reservation is supplied, and that reservation remains intact', r.status === 409
    && !(await db.prepare("SELECT id FROM artists WHERE email='duplicate@example.test'").first())
    && (await db.prepare('SELECT reserved, artist_id FROM gallery_positions WHERE position=13').first()).reserved === 1);

  const admin = await api('GET', '/assets/admin.js', FOUNDER);
  check('G12 the founder desk carries a separate, explicit earlier-invitation workflow rather than restoring a programme switch', admin.status === 200
    && /Complete an earlier Founding Artist invitation/.test(admin.text)
    && /COMPLETE EARLIER FOUNDING INVITATION/.test(admin.text)
    && !/name="i-prog"[^>]*value="founding"/.test(admin.text));
} catch (e) {
  console.error(e); results.push(false);
} finally {
  await S.mf.dispose();
}
const passed = results.filter(Boolean).length;
console.log(`\nGRANDFATHERED FOUNDING · ${results.length} checks, ${passed} passed, ${results.length - passed} failed`);
process.exit(passed === results.length ? 0 : 1);
