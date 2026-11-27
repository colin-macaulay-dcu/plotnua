// PROVE · migration 0030 (commercial leads and placements): runs on a database at 0029, adds only its six tables, is safe to
// run twice, and leaves every existing table byte-identical. Local Miniflare D1, synthetic rows; nothing touches Cloudflare.
//   node test/prove-migration-0030.mjs
import { readFileSync } from 'node:fs';
import { start } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { statements } from './sql.mjs';
const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
console.log('PROVE · migration 0030');
const schema = readFileSync(HERE + 'schema.sql', 'utf8');
const S = await start({ port: 8894, schemaSql: schema.split('-- PlotArt Studio · migration 0030')[0] });
await seedPublished(S.db, { id: 'am30', slug: 'm-thirty', email: 'm30@example.test', name: 'M Thirty', works: 2, number: 1 });
const tables = async () => (await S.db.prepare("SELECT name, sql FROM sqlite_master WHERE type IN ('table','trigger','index') AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name").all()).results;
const dump = async names => { const o = {}; for (const n of names) o[n] = JSON.stringify((await S.db.prepare(`SELECT * FROM "${n}"`).all()).results); return o; };
const before = await tables(), names = before.filter(t => t.sql && t.sql.startsWith('CREATE TABLE')).map(t => t.name), data = await dump(names);
const mig = readFileSync(HERE + 'migrations/0030_commercial.sql', 'utf8');
for (const s of statements(mig)) await S.db.prepare(s).run();
for (const s of statements(mig)) await S.db.prepare(s).run();   // second run: no error, no change
const after = await tables();
const added = after.map(t => t.name).filter(n => !before.some(b => b.name === n));
check('M1 adds exactly the six commercial tables (with their indexes and triggers)', ['commercial_documents', 'commercial_events', 'commercial_leads', 'commercial_payments', 'commercial_placements', 'commercial_selections'].every(n => added.includes(n)) && added.every(n => n.startsWith('commercial_')), added.join());
check('M2 every existing table, index and trigger definition is unchanged', before.every(b => (after.find(a => a.name === b.name) || {}).sql === b.sql));
const data2 = await dump(names);
check('M3 every existing row is unchanged', names.every(n => data[n] === data2[n]));
const ddl = mig.slice(mig.indexOf('-- @@DDL-BEGIN'), mig.indexOf('-- @@DDL-END')).split('\n').slice(1).join('\n').trim();
check('M4 schema.sql carries the migration’s DDL verbatim (new installs and tests match production)', schema.includes(ddl));
check('M5 the migration only creates (no ALTER, DROP outside comments, UPDATE or DELETE)', !statements(mig).some(s => /^\s*(ALTER|DROP|UPDATE|DELETE|INSERT)\b/i.test(s)));
await S.mf.dispose();
console.log(`PROVE MIGRATION 0030 · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exit(results.every(Boolean) ? 0 : 1);
