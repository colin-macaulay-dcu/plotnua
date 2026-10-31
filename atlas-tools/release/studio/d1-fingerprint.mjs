// PlotArt Studio · database check for migrations (31 Oct 2026). Reads the JSON that `wrangler d1 execute --json`
// prints for the check query (on stdin) and prints ONLY table names, PASS/FAIL and short fingerprints: never a row,
// a name, an email address or a count (GitHub Actions logs are public for this repository).
//   ... | node d1-fingerprint.mjs save <file>
//   ... | node d1-fingerprint.mjs compare <file> [--allow-record-changes]
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
const [mode, file, flag] = process.argv.slice(2);
let s = ''; for await (const c of process.stdin) s += c;
let res; try { res = JSON.parse(s); } catch { console.log('FAIL  the database check returned no readable result'); process.exit(1); }
const H = v => createHash('sha256').update(JSON.stringify(v)).digest('hex');
// result sets, in the order of the check query: counts per table, artists, gallery positions
const [counts, artists, positions] = res.map(r => r.results);
const snap = { counts: H(counts), counts_by_table: Object.fromEntries(Object.entries(counts[0]).map(([k, v]) => [k, H(v)])),
  artists: H(artists), positions: H(positions), reserved01: positions.some(p => p.position === 1 && p.reserved === 1 && p.artist_id === null) };
console.log(`position 01 reserved: ${snap.reserved01 ? 'yes' : 'NO'} · artist records fingerprint ${snap.artists.slice(0, 12)} · gallery fingerprint ${snap.positions.slice(0, 12)}`);
if (mode === 'save') { writeFileSync(file, JSON.stringify(snap)); process.exit(0); }
const b = JSON.parse(readFileSync(file, 'utf8'));
const changed = Object.keys(b.counts_by_table).filter(k => b.counts_by_table[k] !== snap.counts_by_table[k]);
const same = b.counts === snap.counts && b.artists === snap.artists && b.positions === snap.positions && snap.reserved01;
if (same) { console.log('PASS  record counts, every artist record and the gallery order are unchanged; 01 is still reserved'); process.exit(0); }
console.log(`${flag === '--allow-record-changes' && snap.reserved01 ? 'NOTE' : 'FAIL'}  changed: ${[...changed.map(t => 'count of ' + t), b.artists !== snap.artists ? 'artist records' : null, b.positions !== snap.positions ? 'gallery order' : null, snap.reserved01 ? null : '01 no longer reserved'].filter(Boolean).join(', ') || 'none'}`);
process.exit(flag === '--allow-record-changes' && snap.reserved01 ? 0 : 1);
