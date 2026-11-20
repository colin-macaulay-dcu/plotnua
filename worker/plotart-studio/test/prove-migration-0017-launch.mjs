// PlotArt Studio · production launch checks for migrations 0017 and 0018 (20 Nov 2026). Local only; nothing reaches Cloudflare.
//   node test/prove-migration-0017-launch.mjs
// The production schema is reconstructed from the migration workflow's history (studio-d1-migration runs, last 0016 on
// 17 Nov 2026): schema.sql up to its 0017 marker, without migration 0008 (hire reports), which has never run in production.
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = join(dirname(fileURLToPath(import.meta.url)), '..') + '/';
const ROOT = join(HERE, '..', '..') + '/';
let pass = 0, fail = 0;
const check = (n, ok, info) => { ok ? pass++ : fail++; console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${ok || info === undefined ? '' : '  ' + String(info).slice(0, 500)}`); };
const sha = b => createHash('sha256').update(b).digest('hex');
const M17 = HERE + 'migrations/0017_managed_checkout_pilot.sql', M18 = HERE + 'migrations/0018_payment_terms_issue.sql';
const APPROVED = { 'PA-PAY-2026-11': ['artist_payment_addendum', 'ff0a8c87f360a60159d9aa2491d957a207791b656c36ccfa517429f60d4464bd'],
  'PA-BPT-2026-11': ['buyer_purchase_terms', 'c570c06fe00577db3c5718c2b5b40fc6f834a2a2f2b97678b3a1978d74eb332a'] };
const T = mkdtempSync(join(tmpdir(), 'pa-0017-launch-'));

// reconstructed production schema
const schema = readFileSync(HERE + 'schema.sql', 'utf8');
const mark = schema.search(/^--[^\n]*\bmigration\s+0017\b/im);
const statements = sql => { const out = []; let buf = ''; for (const line of sql.split(/(?<=\n)/)) { buf += line;
  const clean = buf.replace(/--[^\n]*/g, ''); if ((/;\s*$/.test(clean) && !/\bBEGIN\b/i.test(clean)) || /\bEND\s*;\s*$/i.test(clean)) { out.push(buf); buf = ''; } } if (buf.trim()) out.push(buf); return out; };
const prod = statements(schema.slice(0, mark)).filter(s => !/\bhire_report(s|_records)\b/.test(s.replace(/--[^\n]*/g, ''))).join('');
writeFileSync(T + '/prod.sql', prod);
const db = new DatabaseSync(':memory:'); db.exec('PRAGMA foreign_keys = ON'); db.exec(prod);
const tables = () => db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").all().map(r => r.name);
console.log('— P1 the reconstructed production schema');
const before = tables();
check(`P1a ${before.length} tables, no pilot table and no hire-report table (0008 never ran in production)`, mark > 0 && !before.includes('checkout_orders') && !before.includes('payment_terms') && !before.includes('hire_reports') && before.includes('homepage_features') && before.includes('artists'));

console.log('— P2 the migration checker accepts 0017 (UPDATE OF guard) and 0018; class needs the founder approval');
const tables17 = [...readFileSync(M17, 'utf8').matchAll(/CREATE TABLE IF NOT EXISTS (\w+)/g)].map(m => m[1]);
const mc = (file, tbl) => spawnSync('python3', [ROOT + 'atlas-tools/release/studio/migration-check.py', file, sha(readFileSync(file)), tbl, 'Launch proof: the expected effects of this migration, as approved.'], { encoding: 'utf8' }).stdout;
const c17 = mc(M17, tables17.join(',')), c18 = mc(M18, 'payment_terms');
check('P2a 0017: MIGRATION CHECK OK, class destructive (founder approval), retention guard listed as UPDATE OF retain_until', /^MIGRATION CHECK OK$/m.test(c17) && /^MIGRATION CLASS: destructive$/m.test(c17) && c17.includes('checkout_orders_retention_fixed (refuses UPDATE OF retain_until on checkout_orders)'), c17.split('\n')[0]);
check('P2b 0018: MIGRATION CHECK OK, class destructive (founder approval)', /^MIGRATION CHECK OK$/m.test(c18) && /^MIGRATION CLASS: destructive$/m.test(c18), c18.split('\n')[0]);
check('P2c the full 0017 proof passes on the reconstructed schema (existing tables and rows unchanged, idempotent, rollback)', (r => r.status === 0 && /9 checks, 9 passed/.test(r.stdout))(spawnSync(process.execPath, [HERE + 'test/prove-migration-0017.mjs', T + '/prod.sql'], { encoding: 'utf8', env: { ...process.env } })));

console.log('— P3 0017 on the reconstructed production schema: session ids of both modes');
db.exec(readFileSync(M17, 'utf8'));
check('P3a exactly the 24 pilot tables were added', JSON.stringify(tables().filter(t => !before.includes(t)).sort()) === JSON.stringify([...tables17].sort()) && tables17.length === 24);
const now = '2026-11-20T18:00:00.000Z';
db.exec('PRAGMA foreign_keys = OFF');   // the session id rule is tested on its own; orders are covered by prove-checkout-pilot
const sess = (id, n) => { try { db.prepare(`INSERT INTO checkout_sessions (id, order_id, quote_version, amount_total, application_fee_cents, status, url, expires_at, created_at, updated_at) VALUES (?, ?, 1, 50000, 7500, 'expired', NULL, ?, ?, ?)`).run(id, 'o' + n, now, now, now); return true; } catch { return false; } };
check('P3b a TEST session id (cs_test_…) is accepted', sess('cs_test_a1B2c3D4e5', 1));
check('P3c a LIVE session id (cs_live_…) is accepted', sess('cs_live_a1B2c3D4e5', 2));
const bad = ['cs_a1B2', 'cs_LIVE_a1', 'CS_live_a1', 'pi_live_a1', 'cs_tests_a1', 'xcs_live_a1', '', 'cs_live', 'cs_test'];
check(`P3d every other id is refused (${bad.map(b => JSON.stringify(b)).join(', ')})`, bad.every((b, i) => !sess(b, 10 + i)));
db.exec('PRAGMA foreign_keys = ON');

console.log('— P4 the retention guard (BEFORE UPDATE OF retain_until) works as a refusal-only guard');
const sql17 = readFileSync(M17, 'utf8');
const trig = db.prepare("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='checkout_orders_retention_fixed'").get();
check('P4a installed as BEFORE UPDATE OF retain_until ON checkout_orders', trig && /BEFORE UPDATE OF retain_until ON checkout_orders/.test(trig.sql));
// exercise it on a scratch copy of the trigger over a minimal table with the same column (avoids building a full order)
const s2 = new DatabaseSync(':memory:');
s2.exec("CREATE TABLE checkout_orders (id TEXT PRIMARY KEY, retain_until TEXT, note TEXT);" + trig.sql + ';');
s2.exec("INSERT INTO checkout_orders VALUES ('o', NULL, 'a')");
const upd = sql => { try { s2.exec(sql); return true; } catch { return false; } };
check('P4b a first retention date can be set; other columns stay editable', upd("UPDATE checkout_orders SET retain_until = '2033-12-31' WHERE id = 'o'") && upd("UPDATE checkout_orders SET note = 'b' WHERE id = 'o'"));
check('P4c once set, the date can be neither changed nor cleared', !upd("UPDATE checkout_orders SET retain_until = '2030-01-01' WHERE id = 'o'") && !upd("UPDATE checkout_orders SET retain_until = NULL WHERE id = 'o'"));

console.log('— P5 0018 installs exactly the approved fingerprints');
db.exec(readFileSync(M18, 'utf8'));
const rows = db.prepare('SELECT doc_id, kind, html_sha256 FROM payment_terms ORDER BY doc_id').all().map(r => ({ ...r }));
const F = JSON.parse(readFileSync(HERE + 'agreements/payment-issued/fingerprints.json', 'utf8')).documents;
check('P5a exactly PA-BPT-2026-11 and PA-PAY-2026-11 with the approved kinds and SHA-256', rows.length === 2 && rows.every(r => APPROVED[r.doc_id] && APPROVED[r.doc_id][0] === r.kind && APPROVED[r.doc_id][1] === r.html_sha256), JSON.stringify(rows));
check('P5b they equal the issued files and their fingerprints.json', rows.every(r => F[r.doc_id].html_sha256 === r.html_sha256 && sha(readFileSync(HERE + `agreements/payment-issued/${r.doc_id}.html`)) === r.html_sha256));
check('P5c a second run of 0018 is refused; the rows can never change or be removed', (() => { try { db.exec(readFileSync(M18, 'utf8')); return false; } catch { } try { db.exec("UPDATE payment_terms SET html_sha256 = html_sha256"); return false; } catch { } try { db.exec('DELETE FROM payment_terms'); return false; } catch { return true; } })());

console.log('— P6 the read-only post-migration verification (payment-terms-verify.mjs) with a stub wrangler');
const STUB = T + '/wrangler.mjs';
writeFileSync(STUB, `import { readFileSync, appendFileSync } from 'node:fs';
appendFileSync(process.env.STUB_LOG, JSON.stringify(process.argv.slice(2)) + '\\n');
if (process.env.STUB_FAIL) process.exit(1);
console.log(JSON.stringify([{ results: JSON.parse(readFileSync(process.env.STUB_ROWS, 'utf8')), success: true }]));`);
const verify = (rs, extra = {}) => { writeFileSync(T + '/rows.json', JSON.stringify(rs)); writeFileSync(T + '/log', '');
  const r = spawnSync(process.execPath, [ROOT + 'atlas-tools/release/studio/payment-terms-verify.mjs', 'wrangler.production.toml', HERE + 'agreements/payment-issued/fingerprints.json'],
    { encoding: 'utf8', env: { PATH: process.env.PATH, WRANGLER: `${process.execPath} ${STUB}`, STUB_ROWS: T + '/rows.json', STUB_LOG: T + '/log', ...extra } });
  return { code: r.status, out: r.stdout + r.stderr, calls: readFileSync(T + '/log', 'utf8').trim().split('\n').filter(Boolean).map(l => JSON.parse(l)) }; };
let v = verify(rows);
check('P6a the installed rows pass; output is only identifiers, kinds and fingerprints', v.code === 0 && /^PASS {2}payment_terms holds exactly the issued texts/m.test(v.out)
  && v.out.split('\n').filter(Boolean).every(l => /^ {2}installed {2}PA-(PAY|BPT)-2026-11 {2}[a-z_]+ {2}[0-9a-f]{64}$/.test(l) || /^PASS /.test(l)), v.out);
check('P6b exactly one call: d1 execute --remote of a single SELECT on payment_terms (no write keyword)', v.calls.length === 1 && v.calls[0].includes('--remote')
  && v.calls[0][v.calls[0].indexOf('--command') + 1] === 'SELECT doc_id, kind, html_sha256 FROM payment_terms ORDER BY doc_id', JSON.stringify(v.calls));
v = verify(rows.map(r => r.doc_id === 'PA-PAY-2026-11' ? { ...r, html_sha256: 'a'.repeat(64) } : r));
check('P6c a wrong fingerprint fails', v.code === 1 && /FAIL {2}PA-PAY-2026-11 does not match/.test(v.out), v.out);
v = verify(rows.map(r => r.doc_id === 'PA-BPT-2026-11' ? { ...r, kind: 'artist_payment_addendum' } : r));
check('P6d a wrong kind fails', v.code === 1 && /FAIL/.test(v.out), v.out);
v = verify([...rows, { doc_id: 'PA-PAY-2026-12', kind: 'artist_payment_addendum', html_sha256: 'b'.repeat(64) }]);
check('P6e an extra row fails', v.code === 1 && /expected exactly/.test(v.out), v.out);
v = verify([rows[0]]);
check('P6f a missing row fails', v.code === 1 && /expected exactly/.test(v.out), v.out);
v = verify([]);
check('P6g an empty table fails', v.code === 1, v.out);
v = verify(rows, { STUB_FAIL: '1' });
check('P6h an unreadable table fails (never a silent pass)', v.code === 1 && /could not be read/.test(v.out), v.out);
v = verify([{ doc_id: 'x@example.com', kind: 'artist_payment_addendum', html_sha256: 'not-a-hash' }]);
check('P6i an unexpected value is never printed (only a placeholder)', v.code === 1 && !v.out.includes('x@example.com') && !v.out.includes('not-a-hash'), v.out);

console.log('— P7 the workflow: the check runs after 0018 only, after the backups and the table check; approvals unchanged');
const wf = readFileSync(ROOT + '.github/workflows/studio-d1-migration.yml', 'utf8');
const iV = wf.indexOf('payment-terms-verify.mjs'), iTT = wf.indexOf('Backup 1 of 2'), iEx = wf.indexOf('Backup 2 of 2'), iApply = wf.indexOf('Apply the migration'), iCmp = wf.indexOf('d1-snapshot.mjs "$CONFIG" compare');
check('P7a runs only for 0018 and never in a dry run', /if: \$\{\{ !inputs\.dry_run && inputs\.migration == '0018_payment_terms_issue\.sql' \}\}\n[\s\S]{0,400}payment-terms-verify\.mjs/.test(wf));
check('P7b order: both backups → apply → declared-tables check → payment texts check', iTT > 0 && iTT < iEx && iEx < iApply && iApply < iCmp && iCmp < iV);
check('P7c both backups and the protected environments are unchanged', wf.includes("environment: ${{ needs.check.outputs.environment }}") && wf.includes('E=studio-database-auto; else E=studio-database;')
  && wf.includes('d1 time-travel info plotart-studio') && wf.includes('d1 export plotart-studio --remote') && wf.includes('openssl enc -aes-256-cbc'));
check('P7d it uses the job\'s D1 token and the fingerprints at the migrated commit', /payment-terms-verify\.mjs "\$CONFIG" agreements\/payment-issued\/fingerprints\.json/.test(wf) && wf.slice(iV - 700, iV).includes('secrets.STUDIO_CF_D1_TOKEN'));

rmSync(T, { recursive: true, force: true });
console.log(`MIGRATIONS 0017-0018 LAUNCH · ${pass + fail} checks, ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
