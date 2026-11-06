#!/usr/bin/env node
// PlotArt Studio · proof of the gallery-order safeguards (founder approval 6 Nov 2026). Runs locally; touches nothing real.
// d1-snapshot.mjs (migrations) runs against a stand-in for Wrangler on PATH that answers from an in-memory database;
// order-check.mjs (deployments) runs against a local stand-in for the Studio's pipeline view. Every planted change to the
// gallery order, to position 01 or to an artist record must stop the operation; the real order (Leah Hewson at 01, a
// reserved 02, an unpublished artist at 03) and a migration that only creates its declared tables must pass. Neither script
// may print a name, an email address or a private note.
//   node atlas-tools/release/studio/prove-gallery-order-safeguards.mjs
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, chmodSync, existsSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const HERE = dirname(fileURLToPath(import.meta.url));
const SNAP = join(HERE, 'd1-snapshot.mjs'), ORDER = join(HERE, 'order-check.mjs');
const T = mkdtempSync(join(tmpdir(), 'pa-order-'));
const results = [];
const check = (name, ok, detail = '') => { results.push(ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${ok || !detail ? '' : ' :: ' + detail}`); };
const clone = o => JSON.parse(JSON.stringify(o));
const SECRET = ['Leah', 'Artist B', '@example.invalid', 'private note'];

// ---------------------------------------------------------------- d1-snapshot.mjs against a stand-in for Wrangler
const bin = join(T, 'bin'); execFileSync('mkdir', ['-p', bin]);
writeFileSync(join(bin, 'npx'), `#!/usr/bin/env node
const fs = require('fs'); const a = process.argv.slice(2); const sql = a[a.indexOf('--command') + 1];
if (process.env.FAKE_DB_BROKEN) process.exit(1);
const db = JSON.parse(fs.readFileSync(process.env.FAKE_DB, 'utf8'));
if (/sqlite_master/.test(sql)) { console.log(JSON.stringify([{ results: Object.keys(db).sort().map(name => ({ name })) }])); process.exit(0); }
const out = sql.split('; ').map(s => ({ results: db[s.match(/FROM "([^"]+)"/)[1]] }));
console.log(JSON.stringify(out));
`); chmodSync(join(bin, 'npx'), 0o755);
const BASE = {
  artists: [
    { id: 'a-leah', slug: 'leah-hewson', email: 'leah@example.invalid', display_name: 'Leah Hewson', licence_version: 'PA-GPIL-2026-10-29' },
    { id: 'a-artist-b', slug: 'artist-b', email: 'b@example.invalid', display_name: "Artist B", licence_version: null },
    { id: 'a-artist-c', slug: 'artist-c', email: 'c@example.invalid', display_name: 'Artist C', licence_version: null } ],
  gallery_positions: [
    { position: 1, artist_id: 'a-leah', reserved: 0, note: null, updated_at: '2026-11-05T17:08:25Z' },
    { position: 2, artist_id: null, reserved: 1, note: 'Leah Hewson private note', updated_at: '2026-11-05T17:00:00Z' },
    { position: 3, artist_id: 'a-artist-b', reserved: 0, note: null, updated_at: '2026-11-05T17:00:00Z' } ],
  artworks: [{ id: 'w1', artist_id: 'a-leah', title: 'Blowout Series II #1' }],
  enquiries: [] };
const MIGRATED = db => ({ ...db, agreement_documents: [{ doc_id: 'PA-FAA-2026-11' }], agreement_acceptances: [{ id: 'x1', artist_id: 'a-leah' }],
  enquiry_log: [], record_retention: [], acceptance_corrections: [], participation_events: [] });
const DECLARED = 'agreement_documents,agreement_acceptances,enquiry_log,record_retention,acceptance_corrections,participation_events';
function snap(mode, db, file, declared, broken = false) {
  const dbf = join(T, `db-${Math.random().toString(36).slice(2)}.json`); writeFileSync(dbf, JSON.stringify(db));
  const env = { ...process.env, PATH: bin + ':' + process.env.PATH, FAKE_DB: dbf, ...(broken ? { FAKE_DB_BROKEN: '1' } : {}) };
  try { const out = execFileSync('node', [SNAP, 'cfg.toml', mode, file, ...(declared ? [declared] : [])], { env, encoding: 'utf8' }); return { code: 0, out }; }
  catch (e) { return { code: e.status, out: String(e.stdout || '') }; }
}
function migrationCase(name, after, { declared = DECLARED, beforeDb = BASE, expect }) {
  const f = join(T, `snap-${results.length}.json`);
  const s = snap('save', beforeDb, f);
  const c = s.code === 0 ? snap('compare', after(clone(beforeDb)), f, declared) : s;
  const passed = c.code === 0;
  const leak = SECRET.find(x => (s.out + c.out).includes(x));
  check(`migration · ${name} → ${expect ? 'proceeds' : 'STOPS'}`, passed === expect && !leak, leak ? 'printed ' + leak : (s.out + c.out).trim().split('\n').pop());
}
console.log('d1-snapshot.mjs (migration workflow)');
migrationCase('Leah at 01, 02 reserved, 03 assigned; the migration creates only its six declared tables', MIGRATED, { expect: true });
migrationCase('nothing changes at all', db => db, { declared: 'none', expect: true });
migrationCase('an artist is moved (03 to 04)', db => { db.gallery_positions[2].position = 4; return MIGRATED(db); }, { expect: false });
migrationCase('two positions are swapped', db => { db.gallery_positions[0].artist_id = 'a-artist-b'; db.gallery_positions[2].artist_id = 'a-leah'; return MIGRATED(db); }, { expect: false });
migrationCase('Leah is moved from 01 to 04', db => { db.gallery_positions[0].position = 4; return MIGRATED(db); }, { expect: false });
migrationCase('Leah is removed from the gallery', db => { db.gallery_positions.shift(); return MIGRATED(db); }, { expect: false });
migrationCase('Leah is removed and 01 becomes an empty reservation', db => { db.gallery_positions[0] = { position: 1, artist_id: null, reserved: 1, note: null, updated_at: 'x' }; return MIGRATED(db); }, { expect: false });
migrationCase('the reservation at 02 is released', db => { db.gallery_positions.splice(1, 1); return MIGRATED(db); }, { expect: false });
migrationCase('the reservation at 02 is reassigned to an artist', db => { db.gallery_positions[1] = { position: 2, artist_id: 'a-artist-c', reserved: 0, note: null, updated_at: 'x' }; return MIGRATED(db); }, { expect: false });
migrationCase('the private note at 02 is changed', db => { db.gallery_positions[1].note = 'changed'; return MIGRATED(db); }, { expect: false });
migrationCase('a new position is added (another artist at 05)', db => { db.gallery_positions.push({ position: 5, artist_id: 'a-artist-c', reserved: 0, note: null, updated_at: 'x' }); return MIGRATED(db); }, { expect: false });
migrationCase('gallery_positions is declared, and still nobody may move', db => { db.gallery_positions[2].position = 4; return MIGRATED(db); }, { declared: DECLARED + ',gallery_positions', expect: false });
migrationCase("an existing artist record is changed (Leah's licence)", db => { db.artists[0].licence_version = 'PA-GPIL-2026-11'; return MIGRATED(db); }, { expect: false });
migrationCase('an artwork is changed', db => { db.artworks[0].title = 'x'; return MIGRATED(db); }, { expect: false });
migrationCase("Leah's gallery address changes (01 no longer the approved artist)", db => { db.artists[0].slug = 'someone-else'; return MIGRATED(db); }, { declared: DECLARED + ',artists', expect: false });
{ const f = join(T, 'snap-x.json');
  const s = snap('save', { ...clone(BASE), gallery_positions: [{ position: 1, artist_id: null, reserved: 1, note: null, updated_at: 'x' }] }, f);
  check('migration · before: 01 is an empty reservation (the withdrawn rule) → STOPS before anything is changed', s.code !== 0 && /not held by the approved artist/.test(s.out), s.out.trim());
  const s2 = snap('save', { ...clone(BASE), gallery_positions: [{ position: 1, artist_id: 'a-artist-b', reserved: 0, note: null, updated_at: 'x' }] }, f);
  check('migration · before: 01 held by another artist → STOPS before anything is changed', s2.code !== 0, s2.out.trim());
  const s3 = snap('save', BASE, f, undefined, true);
  check('migration · before: the database cannot be read → STOPS', s3.code !== 0 && /could not be read/.test(s3.out), s3.out.trim());
  const ok = snap('save', BASE, f);
  check('migration · before: the real order (Leah at 01) is accepted and recorded', ok.code === 0 && /position 01 held by the approved artist: yes/.test(ok.out) && /3 positions \(1 reserved\)/.test(ok.out), ok.out.trim()); }

// ---------------------------------------------------------------- order-check.mjs against a stand-in for the pipeline view
console.log('order-check.mjs (Studio deploy workflow)');
let view;
const server = createServer((req, res) => {
  if (req.url !== '/api/pipeline/gallery-order' || req.headers.authorization !== 'Bearer test-token') { res.writeHead(403); return res.end('{}'); }
  res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(view));
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const URL_ = `http://127.0.0.1:${server.address().port}`;
const LIVE = { positions: [{ position: 1, slug: 'leah-hewson', reserved: false }, { position: 2, slug: null, reserved: true }, { position: 3, slug: null, reserved: false }], extra: [] };
const run = (mode, f) => new Promise(resolve => {
  import('node:child_process').then(({ execFile }) => execFile('node', [ORDER, mode, f], { env: { ...process.env, STUDIO_URL: URL_, STUDIO_PIPELINE_TOKEN: 'test-token' } },
    (err, stdout) => resolve({ code: err ? err.code : 0, out: String(stdout) })));
});
async function deployCase(name, mutate, expect) {
  const f = join(T, `order-${results.length}.txt`);
  view = clone(LIVE); const s = await run('save', f);
  view = mutate(clone(LIVE)); const c = s.code === 0 ? await run('compare', f) : s;
  const leak = SECRET.find(x => (s.out + c.out).includes(x));
  check(`deploy · ${name} → ${expect ? 'proceeds' : 'STOPS'}`, (c.code === 0) === expect && !leak, leak ? 'printed ' + leak : (s.out + c.out).trim().split('\n').pop());
}
await deployCase('the order is unchanged (Leah at 01, 02 reserved, 03 unpublished)', v => v, true);
await deployCase('an artist is moved (03 to 04)', v => { v.positions[2].position = 4; return v; }, false);
await deployCase('Leah is moved from 01 to 04', v => { v.positions[0].position = 4; return v; }, false);
await deployCase('Leah is removed (01 no longer listed)', v => { v.positions.shift(); return v; }, false);
await deployCase("Leah's gallery is unpublished (01 shows no gallery)", v => { v.positions[0].slug = null; return v; }, false);
await deployCase('the reservation at 02 is released', v => { v.positions.splice(1, 1); return v; }, false);
await deployCase('the reservation at 02 is reassigned to a published artist', v => { v.positions[1] = { position: 2, slug: 'artist-c', reserved: false }; return v; }, false);
await deployCase('a published gallery appears outside the order', v => { v.extra = ['artist-c']; return v; }, false);
await deployCase('the view carries an unexpected field (e.g. a private note)', v => { v.positions[1].note = 'x'; return v; }, false);
{ const f = join(T, 'order-y.txt');
  view = { positions: [{ position: 1, slug: null, reserved: true }], extra: [] }; const s = await run('save', f);
  check('deploy · before: 01 is an empty reservation (the withdrawn rule) → STOPS before deploying', s.code !== 0 && /not held by the approved artist/.test(s.out), s.out.trim());
  view = clone(LIVE); const ok = await run('save', f);
  check('deploy · before: the real order (Leah at 01) is accepted and recorded', ok.code === 0 && /position 01 held by the approved artist: yes/.test(ok.out), ok.out.trim()); }
server.close();

const bad = results.filter(r => !r).length;
console.log(bad ? `GALLERY ORDER SAFEGUARDS · REFUSED — ${bad} of ${results.length} failed`
  : `GALLERY ORDER SAFEGUARDS · OK — ${results.length} checks: an occupied 01 (Leah Hewson) is accepted; any move, removal, release, reassignment, note change, artist-record change or unpublished 01 stops the operation; nothing private is printed`);
process.exit(bad ? 2 : 0);
