// PlotArt Studio · database snapshot for migrations (1 Nov 2026). Runs Wrangler itself (with the job's token) and keeps
// a SHA-256 of every table's full contents. Prints ONLY table names, PASS/FAIL and whether 01 is reserved: never a row,
// a count, a name, an email address or a note (GitHub Actions logs are public for this repository).
//   node d1-snapshot.mjs <wrangler config> save <file>
//   node d1-snapshot.mjs <wrangler config> compare <file> "<declared tables or none>"
// compare fails if any table outside the declared list changed, or if position 01 is no longer reserved.
// It is a check, not a rollback: restoring needs the founder's separate approval.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
const [config, mode, file, declaredIn = 'none'] = process.argv.slice(2);
const q = sql => { const out = execFileSync('npx', ['--yes', 'wrangler@4.150.0', 'd1', 'execute', 'plotart-studio', '--remote', '--json', '--config', config, '--command', sql], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 256 << 20 }); return JSON.parse(out); };
let snap;
try {
  const tables = q("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name")[0].results.map(r => r.name);
  if (!tables.length || tables.some(t => !/^[A-Za-z0-9_]+$/.test(t))) throw new Error('table list');
  const res = q(tables.map(t => `SELECT * FROM "${t}" ORDER BY rowid`).join('; '));
  if (res.length !== tables.length) throw new Error('result count');
  const H = v => createHash('sha256').update(JSON.stringify(v)).digest('hex');
  const pos = res[tables.indexOf('gallery_positions')]?.results || [];
  snap = { tables: Object.fromEntries(tables.map((t, i) => [t, H(res[i].results)])),
    reserved01: pos.some(p => p.position === 1 && p.reserved === 1 && p.artist_id === null) };
} catch { console.log('FAIL  the database could not be read for the check'); process.exit(1); }
console.log(`${Object.keys(snap.tables).length} tables fingerprinted · position 01 reserved: ${snap.reserved01 ? 'yes' : 'NO'}`);
if (mode === 'save') { writeFileSync(file, JSON.stringify(snap)); process.exit(snap.reserved01 ? 0 : 1); }
const before = JSON.parse(readFileSync(file, 'utf8'));
const declared = new Set(declaredIn.trim().toLowerCase() === 'none' ? [] : declaredIn.toLowerCase().split(',').map(s => s.trim()).filter(Boolean));
const names = [...new Set([...Object.keys(before.tables), ...Object.keys(snap.tables)])].sort();
const changed = names.filter(t => before.tables[t] !== snap.tables[t]);
const outside = changed.filter(t => !declared.has(t.toLowerCase()));
console.log(`tables changed: ${changed.join(', ') || 'none'} · declared: ${[...declared].join(', ') || 'none'}`);
if (outside.length || !snap.reserved01) {
  console.log(`FAIL  ${outside.length ? 'changed outside the approved declaration: ' + outside.join(', ') : ''}${!snap.reserved01 ? (outside.length ? '; ' : '') + 'position 01 is no longer reserved' : ''}`);
  process.exit(1);
}
console.log('PASS  only the declared tables changed, and 01 is still reserved');
