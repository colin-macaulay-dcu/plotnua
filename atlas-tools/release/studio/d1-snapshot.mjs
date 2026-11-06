// PlotArt Studio · database snapshot for migrations (1 Nov 2026; gallery-order safeguard corrected 6 Nov 2026). Runs Wrangler
// itself (with the job's token) and keeps a SHA-256 of every table's full contents and of the complete gallery order. Prints
// ONLY table names, PASS/FAIL and counts of gallery positions: never a row, a name, an email address or a note (GitHub
// Actions logs are public for this repository).
//   node d1-snapshot.mjs <wrangler config> save <file>
//   node d1-snapshot.mjs <wrangler config> compare <file> "<declared tables or none>"
// save fails unless position 01 is held by the approved artist (below). compare fails if any table outside the declared
// list changed (artist records included), if ANY gallery position changed in any way (artist, reserved flag or private
// note: nobody moved, no reservation released or reassigned), or if position 01 is no longer held by the approved artist.
// Founder decision 6 Nov 2026: Leah Hewson correctly holds Virtual Gallery position 01, so 01 is no longer an empty
// reservation (the earlier rule "01 must be empty and reserved" is withdrawn). Change POSITION_01 only with his approval.
// It is a check, not a rollback: restoring needs the founder's separate approval.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
const POSITION_01 = 'leah-hewson';   // the artist (gallery address) who holds position 01, by founder decision
const [config, mode, file, declaredIn = 'none'] = process.argv.slice(2);
const q = sql => { const out = execFileSync('npx', ['--yes', 'wrangler@4.150.0', 'd1', 'execute', 'plotart-studio', '--remote', '--json', '--config', config, '--command', sql], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 256 << 20 }); return JSON.parse(out); };
let snap;
try {
  const tables = q("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name")[0].results.map(r => r.name);
  if (!tables.length || tables.some(t => !/^[A-Za-z0-9_]+$/.test(t))) throw new Error('table list');
  const res = q(tables.map(t => `SELECT * FROM "${t}" ORDER BY rowid`).join('; '));
  if (res.length !== tables.length) throw new Error('result count');
  const H = v => createHash('sha256').update(JSON.stringify(v)).digest('hex');
  if (!tables.includes('gallery_positions') || !tables.includes('artists')) throw new Error('gallery tables');
  const pos = res[tables.indexOf('gallery_positions')].results, arts = res[tables.indexOf('artists')].results;
  // the complete gallery order: every position with its artist, reserved flag and private note, exactly as stored
  const order = pos.map(p => [p.position, p.artist_id ?? null, p.reserved ? 1 : 0, p.note ?? null]).sort((a, b) => a[0] - b[0]);
  const p01 = pos.find(p => p.position === 1), a01 = p01 && p01.artist_id ? arts.find(a => a.id === p01.artist_id) : null;
  snap = { tables: Object.fromEntries(tables.map((t, i) => [t, H(res[i].results)])), order: H(order),
    positions: order.length, reserved: order.filter(o => o[2] === 1).length,
    held01: !!(p01 && !p01.reserved && a01 && a01.slug === POSITION_01) };
} catch { console.log('FAIL  the database could not be read for the check'); process.exit(1); }
console.log(`${Object.keys(snap.tables).length} tables fingerprinted · gallery order recorded: ${snap.positions} positions (${snap.reserved} reserved) · position 01 held by the approved artist: ${snap.held01 ? 'yes' : 'NO'}`);
if (mode === 'save') { writeFileSync(file, JSON.stringify(snap)); if (!snap.held01) console.log('FAIL  position 01 is not held by the approved artist: nothing was changed'); process.exit(snap.held01 ? 0 : 1); }
const before = JSON.parse(readFileSync(file, 'utf8'));
const declared = new Set(declaredIn.trim().toLowerCase() === 'none' ? [] : declaredIn.toLowerCase().split(',').map(s => s.trim()).filter(Boolean));
const names = [...new Set([...Object.keys(before.tables), ...Object.keys(snap.tables)])].sort();
const changed = names.filter(t => before.tables[t] !== snap.tables[t]);
const outside = changed.filter(t => !declared.has(t.toLowerCase()));
console.log(`tables changed: ${changed.join(', ') || 'none'} · declared: ${[...declared].join(', ') || 'none'}`);
const problems = [];
if (outside.length) problems.push('changed outside the approved declaration: ' + outside.join(', '));
if (typeof before.order !== 'string' || before.order !== snap.order) problems.push('the gallery order changed (a position, an artist, a reservation or a note)');
if (!snap.held01) problems.push('position 01 is no longer held by the approved artist');
if (problems.length) { console.log('FAIL  ' + problems.join('; ')); process.exit(1); }
console.log('PASS  only the declared tables changed; every gallery position is identical; 01 is still held by the approved artist');
