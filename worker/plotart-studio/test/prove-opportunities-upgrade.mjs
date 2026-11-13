// PROVE · Opportunities & delivery across the deployment order of migration 0010 (development 13 Nov 2026).
// Runs the Studio CURRENTLY LIVE (production commit, given as an argument) and the NEW Studio in turn on ONE local database:
//   1. the live Studio saves an answer with a note (before 0010);
//   2. migration 0010 runs (the note is copied into practical_note);
//   3. the artist edits the note with the live Studio (it still writes the old column) — before the new deployment;
//   4. the new Studio is deployed: it must show that LATEST edit, not the earlier copied note, to the artist and the founder;
//   5. the artist saves with the new Studio: the longer note and the care condition are stored and shown.
// Local only (Miniflare D1, synthetic artists).   node test/prove-opportunities-upgrade.mjs <live-commit>
import { execSync } from 'node:child_process';
import { mkdirSync, rmSync, writeFileSync, readFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';

const LIVE = process.argv[2];
if (!/^[0-9a-f]{7,40}$/.test(LIVE || '')) { console.log('usage: node test/prove-opportunities-upgrade.mjs <live-commit>'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
// The live Studio's source, exactly as committed on production.
const OLD = 'test/.upgrade-live/';
rmSync(HERE + OLD, { recursive: true, force: true }); mkdirSync(HERE + OLD + 'src', { recursive: true });
for (const f of execSync(`git ls-tree --name-only ${LIVE} src/`, { cwd: HERE }).toString().trim().split('\n'))
  writeFileSync(HERE + OLD + f, execSync(`git show ${LIVE}:worker/plotart-studio/${f}`, { cwd: HERE, maxBuffer: 64 << 20 }));
const liveSchema = execSync(`git show ${LIVE}:worker/plotart-studio/schema.sql`, { cwd: HERE }).toString();
const MIG = readFileSync(HERE + 'migrations/0010_opportunities_care.sql', 'utf8');
const P = mkdtempSync(join(tmpdir(), 'opp-upgrade-'));
const ART = 'eve-test@example.test';
const Hd = e => ({ 'Cf-Access-Jwt-Assertion': token(e), 'X-Studio': '1', 'Content-Type': 'application/json' });
const caller = S => async (method, path, email, body) => { const r = await S.mf.dispatchFetch(S.url + path, { method, headers: Hd(email), body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* */ } return { s: r.status, j }; };
const ans = note => ({ interests: ['living_gallery', 'art_for_hire'], artwork_county: 'Cork', transport: ['deliver'], coverage: { mode: 'counties', counties: ['Cork', 'Kerry'] }, note });
let S;
try {
  console.log(`PROVE · Opportunities & delivery: live Studio ${LIVE.slice(0, 7)} → migration 0010 → new Studio, on one database`);
  S = await start({ port: 8881, script: OLD + 'src/index.js', persist: P, schemaSql: liveSchema });
  let call = caller(S);
  await seedPublished(S.db, { id: 'aeve', slug: 'eve-test', email: ART, name: 'Eve Test', works: 2, number: 9 });
  let r = await call('PUT', '/api/opportunities', ART, ans('First note, before the migration.'));
  check('S1 the live Studio saves an answer and note before migration 0010', r.s === 200 && r.j.saved.note === 'First note, before the migration.', JSON.stringify(r.j));
  for (const st of statements(MIG)) await S.db.prepare(st).run();
  let row = await S.db.prepare("SELECT note, practical_note, care_condition FROM artist_opportunities WHERE artist_id='aeve'").first();
  check('S2 migration 0010 copies the note into the new column and leaves the care box unticked',
    row.note === 'First note, before the migration.' && row.practical_note === row.note && row.care_condition === 0, JSON.stringify(row));
  r = await call('PUT', '/api/opportunities', ART, ans('Edited with the live Studio AFTER the migration.'));
  row = await S.db.prepare("SELECT note, practical_note FROM artist_opportunities WHERE artist_id='aeve'").first();
  check('S3 the live Studio keeps working after the migration; its edit goes to the old note column (the copy is now out of date)',
    r.s === 200 && row.note === 'Edited with the live Studio AFTER the migration.' && row.practical_note === 'First note, before the migration.', JSON.stringify(row));
  await S.mf.dispose(); S = null;

  S = await start({ port: 8882, persist: P, schemaSql: null });   // the NEW Studio on the same database
  call = caller(S);
  r = await call('GET', '/api/opportunities', ART);
  const adm = await call('GET', '/api/admin/opportunities', FOUNDER), eve = adm.j.items.find(i => i.id === 'aeve');
  check('S4 the new Studio shows the LATEST edit (not the earlier copied note) to the artist and to the founder',
    r.j.saved.note === 'Edited with the live Studio AFTER the migration.' && eve.prefs.note === 'Edited with the live Studio AFTER the migration.'
    && r.j.saved.care_condition === false && r.j.options.note_max === 2000 && !!r.j.options.care, JSON.stringify([r.j.saved, eve.prefs]));
  const long = 'Handled with gloves; hung away from direct sunlight; insured for any time away from the studio. '.repeat(21).slice(0, 2000).trim();
  r = await call('PUT', '/api/opportunities', ART, { ...ans(long), care_condition: true });
  row = await S.db.prepare("SELECT note, practical_note, care_condition FROM artist_opportunities WHERE artist_id='aeve'").first();
  const back = await call('GET', '/api/opportunities', ART), adm2 = await call('GET', '/api/admin/opportunities', FOUNDER);
  check('S5 saving with the new Studio stores the long note in the new column, clears the old one and records the care condition; both views show it',
    r.s === 200 && row.practical_note === long && row.note === null && row.care_condition === 1 && back.j.saved.note === long && back.j.saved.care_condition === true
    && adm2.j.items.find(i => i.id === 'aeve').prefs.note === long, JSON.stringify([r.s, r.j && r.j.error, row && row.practical_note && row.practical_note.length]));
  r = await call('PUT', '/api/opportunities', ART, { ...ans('Short again.'), care_condition: false });
  row = await S.db.prepare("SELECT note, practical_note, care_condition FROM artist_opportunities WHERE artist_id='aeve'").first();
  check('S6 a later edit with the new Studio replaces the note and unticks the box', row.practical_note === 'Short again.' && row.note === null && row.care_condition === 0);
} catch (e) { console.error(e); results.push(false); }
finally {
  if (S) await S.mf.dispose();
  rmSync(HERE + OLD, { recursive: true, force: true }); rmSync(P, { recursive: true, force: true });
}
const fail = results.filter(x => !x).length;
console.log(`\nOPPORTUNITIES UPGRADE · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
