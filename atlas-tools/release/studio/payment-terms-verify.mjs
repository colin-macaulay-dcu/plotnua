// PlotArt Studio · read-only check of the installed payment texts after migration 0018 (20 Nov 2026).
//   node payment-terms-verify.mjs <wrangler config> <fingerprints.json>
// Runs ONE read-only query (SELECT doc_id, kind, html_sha256 FROM payment_terms) and compares the rows with the issued
// fingerprints bundled into the Workers (agreements/payment-issued/fingerprints.json). Prints only identifiers, kinds and
// SHA-256 fingerprints (GitHub Actions logs are public). Passes only if the table holds exactly the issued texts.
// WRANGLER may be overridden (tests only).
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

const [config, prints] = process.argv.slice(2);
const SQL = 'SELECT doc_id, kind, html_sha256 FROM payment_terms ORDER BY doc_id';
const [cmd, ...pre] = (process.env.WRANGLER || 'npx --yes wrangler@4.150.0').split(' ');
let rows, want;
try {
  want = JSON.parse(readFileSync(prints, 'utf8')).documents;
  const out = execFileSync(cmd, [...pre, 'd1', 'execute', 'plotart-studio', '--remote', '--json', '--config', config, '--command', SQL],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 16 << 20 });
  rows = JSON.parse(out)[0].results;
  if (!Array.isArray(rows)) throw new Error('rows');
} catch { console.log('FAIL  the payment texts could not be read (nothing was changed)'); process.exit(1); }
const ok = /^[0-9a-f]{64}$/, id = /^[A-Z0-9-]{1,40}$/, kind = /^[a-z_]{1,40}$/;
for (const r of rows) console.log(`  installed  ${id.test(r.doc_id) ? r.doc_id : '(unexpected identifier)'}  ${kind.test(r.kind) ? r.kind : '(unexpected kind)'}  ${ok.test(r.html_sha256) ? r.html_sha256 : '(not a SHA-256)'}`);
const problems = [];
const ids = Object.keys(want).sort();
if (JSON.stringify(rows.map(r => r.doc_id)) !== JSON.stringify(ids)) problems.push(`expected exactly ${ids.join(', ')}; found ${rows.length} row(s)`);
for (const d of ids) {
  const r = rows.find(x => x.doc_id === d);
  if (r && (r.kind !== want[d].kind || r.html_sha256 !== want[d].html_sha256)) problems.push(`${d} does not match its issued kind and fingerprint`);
}
if (problems.length) { console.log('FAIL  ' + problems.join('; ')); process.exit(1); }
console.log(`PASS  payment_terms holds exactly the issued texts: ${ids.map(d => `${d} ${want[d].html_sha256}`).join(' · ')}`);
