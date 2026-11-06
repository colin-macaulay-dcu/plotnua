// PROVE · founding year (Irish time, leap years) and the enquiry log (development, 6 Nov 2026). Local only.
//   node test/prove-enquiry-log.mjs
import { start, token, FOUNDER } from './local.mjs';
import { createRequire } from 'node:module';
import { foundingYear, foundingAt, dublinMidnightUtc } from '../src/founding.js';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };

console.log('PROVE · founding year and enquiry log\n— the founding year (agreement 2.4), Irish calendar dates');
// [first published (UTC), start, end (last day), first instant after the year (UTC)]
const CASES = [
  ['2026-11-05T17:05:00Z', '2026-11-05', '2027-11-04', '2027-11-05T00:00:00.000Z', 'winter (GMT): Leah-shaped'],
  ['2027-06-30T23:30:00Z', '2027-07-01', '2028-06-30', '2028-06-30T23:00:00.000Z', 'summer (IST): 23:30 UTC is already the next Irish day'],
  ['2026-12-31T23:59:00Z', '2026-12-31', '2027-12-30', '2027-12-31T00:00:00.000Z', 'last minute of the year (GMT)'],
  ['2028-02-29T10:00:00Z', '2028-02-29', '2029-02-28', '2029-03-01T00:00:00.000Z', '29 February: ends 28 February (a full twelve months)'],
  ['2027-02-28T10:00:00Z', '2027-02-28', '2028-02-27', '2028-02-28T00:00:00.000Z', '28 February before a leap year'],
  ['2027-03-01T10:00:00Z', '2027-03-01', '2028-02-29', '2028-03-01T00:00:00.000Z', '1 March before a leap year: ends on 29 February'],
  ['2027-03-28T00:30:00Z', '2027-03-28', '2028-03-27', '2028-03-27T23:00:00.000Z', 'published as summer time begins; the anniversary falls in summer time'],
  ['2027-10-31T00:30:00Z', '2027-10-31', '2028-10-30', '2028-10-31T00:00:00.000Z', 'published on the night summer time ends (01:30 IST); anniversary in winter time'],
];
const calc = cases => cases.map(([p]) => { const f = foundingYear(p); return [f.start, f.end, f.ends_at]; });
const node = calc(CASES);
CASES.forEach(([p, s, e, x, why], i) => check(`Y${i + 1} ${why}: ${p} → ${s} to ${e}`, node[i][0] === s && node[i][1] === e && node[i][2] === x, JSON.stringify(node[i])));
// the same code inside the Workers runtime (workerd), where Studio and the relay actually run
const HERE = new URL('..', import.meta.url).pathname;
const w = new Miniflare({ modules: true, modulesRoot: HERE, modulesRules: [{ type: 'ESModule', include: ['**/*.js'] }], scriptPath: HERE + 'test/founding-worker.js', compatibilityDate: '2026-08-01' });
const wr = await (await w.dispatchFetch('http://localhost/', { method: 'POST', body: JSON.stringify(CASES.map(c => c[0])) })).json();
await w.dispose();
check('Y9 the Workers runtime computes exactly the same dates as above (same Irish time zone data)', JSON.stringify(wr.years) === JSON.stringify(node), JSON.stringify(wr.years));
check('Y10 the boundary is the Irish midnight: 23:59 IST on the last day is Founding, 00:00 IST the next day is not (in the Workers runtime)',
  wr.edge[0].founding === 1 && wr.edge[1].founding === 0 && wr.edge[0].year_end === '2028-06-30', JSON.stringify(wr.edge));
check('Y11 before first publication an enquiry counts as Founding; a non-Founding artist never has Founding Enquiries; no publication → no year',
  foundingAt({ founding: 1, first_published_at: null }, '2026-11-06T10:00:00Z').founding === 1 && foundingAt({ founding: 0, first_published_at: '2026-11-05T17:05:00Z' }, '2026-11-06T10:00:00Z').founding === 0
  && foundingYear(null) === null && dublinMidnightUtc('2027-07-01') === '2027-06-30T23:00:00.000Z');

console.log('— Log enquiry (founder only)');
const { mf, url, db } = await start({ port: 8833, enquiry: {} });
const call = async (method, path, email, body) => {
  const r = await mf.dispatchFetch(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  return { s: r.status, j: await r.json().catch(() => null) };
};
const T = '2025-11-01T10:00:00.000Z';   // first published a year ago: the founding year ended on 31 Oct 2026
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, first_published_at, created_at, updated_at)
  VALUES ('aold1', 'older-artist', 'older@example.test', 'Older Artist', 1, 'active', ?, ?, ?)`).bind(T, T, T).run();
await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, ord, created_at, updated_at) VALUES ('wold1', 'aold1', 'harbour', 'Harbour', 1, ?, ?)`).bind(T, T).run();
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, created_at, updated_at) VALUES ('aoth', 'someone-else', 'else@example.test', 'Someone Else', 1, 'active', ?, ?)`).bind(T, T).run();
await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, ord, created_at, updated_at) VALUES ('woth1', 'aoth', 'not-theirs', 'Not Theirs', 1, ?, ?)`).bind(T, T).run();
const today = new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' });
const base = { artist_id: 'aold1', confirm: true };
const e1 = await call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, artwork_id: 'wold1', introduced_on: '2026-10-31', note: 'Forwarded from the hello@ inbox'.replace('@', ' at ') });
const e2 = await call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: '2026-11-01' });
check('E1 the last day of the founding year (31 Oct, Irish date) logs as a Founding Enquiry; the next day does not', e1.s === 200 && e1.j.founding === 1 && e1.j.founding_year_end === '2026-10-31' && e2.s === 200 && e2.j.founding === 0, JSON.stringify([e1.j && e1.j.founding, e2.j && e2.j.founding, e1.j && e1.j.error]));
const late = await call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: '2026-10-20' });
const lateExpected = (Date.parse(today) - Date.parse('2026-10-20')) / 86400_000 > 7 ? 1 : 0, e1Expected = (Date.parse(today) - Date.parse('2026-10-31')) / 86400_000 > 7 ? 1 : 0;
check('E2 references are new PA-EM-… numbers; an entry made more than 7 days after the date it records is marked as a late entry', /^PA-EM-\d{6}-[0-9A-F]{6}$/.test(e1.j.reference)
  && late.j.late_entry === lateExpected && lateExpected === 1 && e1.j.late_entry === e1Expected, JSON.stringify([today, late.j.late_entry, e1.j.late_entry]));
const bad = await Promise.all([
  call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: '2099-01-01' }),
  call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: '2026-09-15' }),
  call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: '2026-02-30' }),
  call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: today, note: 'Buyer is mary.buyer@example.com' }),
  call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: today, note: 'Call her on 087 123 4567' }),
  call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: today, note: 'Lives at D02 X285' }),
  call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: today, artwork_id: 'woth1' }),
  call('POST', '/api/admin/enquiry-log', FOUNDER, { artist_id: 'aold1', introduced_on: today }),
  call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: today, note: 'x'.repeat(281) }),
]);
check('E3 refused: a future date, a date before PlotArt, an impossible date, an email address / phone number / Eircode in the note, another artist’s artwork, no confirmation, an over-long note',
  bad.every(b => b.s === 400), bad.map(b => b.s + ':' + (b.j && b.j.error || '').slice(0, 40)).join(' | '));
const e3 = await call('POST', '/api/admin/enquiry-log', FOUNDER, { ...base, introduced_on: today });
check('E4 an entry for today is not a late entry', e3.s === 200 && e3.j.late_entry === 0);
const orig = await db.prepare('SELECT * FROM enquiry_log WHERE reference=?').bind(e2.j.reference).first();
const fix = await call('POST', '/api/admin/enquiry-log', FOUNDER, { artist_id: 'aold1', introduced_on: '2026-10-30', corrects: orig.id, note: 'Correct date from the sent email' });
const after = await db.prepare('SELECT * FROM enquiry_log WHERE id=?').bind(orig.id).first();
const fixed = await db.prepare('SELECT * FROM enquiry_log WHERE reference=?').bind(fix.j.reference).first();
check('E5 a correction is a NEW entry linked to the original; the original is unchanged', fix.s === 200 && fixed.corrects === orig.id && fixed.founding === 1 && JSON.stringify(after) === JSON.stringify(orig));
let u = 'ran'; try { await db.prepare("UPDATE enquiry_log SET founding=1 WHERE id=?").bind(orig.id).run(); } catch { u = 'refused'; }
let d = 'ran'; try { await db.prepare('DELETE FROM enquiry_log WHERE id=?').bind(orig.id).run(); } catch { d = 'refused'; }
check('E6 log entries cannot be edited or deleted', u === 'refused' && d === 'refused');
const cols = (await db.prepare("SELECT name FROM pragma_table_info('enquiry_log')").all()).results.map(c => c.name);
check('E7 the log has no column for a buyer’s name, email address or message', !cols.some(c => /buyer|email|message|name|phone/.test(c)) && cols.includes('reference'), cols.join(','));
const a1 = await call('POST', '/api/admin/enquiry-log', 'older@example.test', { ...base, introduced_on: today }), a2 = await call('GET', '/api/admin/enquiry-log', 'older@example.test');
check('E8 artists cannot log or read the founder’s enquiry log (403)', a1.s === 403 && a2.s === 403);
const lg = (await call('GET', '/api/admin/enquiry-log', FOUNDER)).j;
check('E9 the founder’s list shows the entries with artist, artwork, route and Founding status, newest introduction first', lg.items.length === 5 && lg.items[0].introduced_at >= lg.items[1].introduced_at
  && lg.items.find(i => i.reference === e1.j.reference).artwork_title === 'Harbour' && lg.items.every(i => i.route === 'email') && lg.items.every(i => i.logged_by === 'founder'));

console.log('— relay enquiries are logged automatically');
// a published Founding Artist whose year is running (first published yesterday)
const Y = new Date(Date.now() - 86400_000).toISOString();
await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, account_status, first_published_at, created_at, updated_at)
  VALUES ('arel', 'relay-artist', 'relay@example.test', 'Relay Artist', 1, 'active', ?, ?, ?)`).bind(Y, Y, Y).run();
const snap = { artist: { slug: 'relay-artist', display_name: 'Relay Artist' }, works: [{ id: 'wrel1', slug: 'tide', title: 'Tide', availability: 'available', images: [] }] };
await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES ('arel', 1, ?, 'seed', ?)").bind(JSON.stringify(snap), Y).run();
await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES ('qrel', 'arel', 1, 'reviewed', 'published', ?, ?)").bind(Y, Y).run();
const notice = (await import('node:fs')).readFileSync(new URL('../src/enquiry.js', import.meta.url), 'utf8').match(/const NOTICE = '([^']+)'/)[1];
const enq = await mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json' },
  body: JSON.stringify({ ref: 'PA-relay-artist-wrel1', notice, name: 'Bea Buyer', email: 'bea.buyer@example.test', message: 'Is Tide still available, please?' }) });
const ej = await enq.json();
const row = await db.prepare('SELECT * FROM enquiry_log WHERE reference=?').bind(ej.reference).first();
check('R1 an enquiry through the online form is logged at once with the same reference, the artwork, route “relay” and Founding status',
  enq.status === 200 && row && row.route === 'relay' && row.artwork_id === 'wrel1' && row.founding === 1 && row.logged_by === 'relay' && row.artist_id === 'arel', JSON.stringify([ej, row]));
check('R2 the log row holds no buyer details (name, address or message appear nowhere in it)', !/Bea|bea\.buyer|Tide still/.test(JSON.stringify(row)));
// the 24-month clean-up still deletes the buyer's details, never the log row
await db.prepare("UPDATE enquiries SET delete_after='2000-01-01T00:00:00Z' WHERE reference=?").bind(ej.reference).run();
await mf.getWorker('studio').then(x => x.scheduled({ cron: '23 3 * * *' }));
const gone = await db.prepare('SELECT COUNT(*) n FROM enquiries WHERE reference=?').bind(ej.reference).first(), kept = await db.prepare('SELECT COUNT(*) n FROM enquiry_log WHERE reference=?').bind(ej.reference).first();
check('R3 the daily clean-up deletes the buyer’s name, email and message at 24 months as before; the log entry remains', gone.n === 0 && kept.n === 1);
// relay before migration 0005: the enquiry still goes through, and the audit says it was not logged
await db.prepare('DROP TRIGGER enquiry_log_no_update').run(); await db.prepare('DROP TRIGGER enquiry_log_no_delete').run(); await db.prepare('DROP TRIGGER record_retention_no_delete').run();
await db.prepare('DROP TABLE enquiry_log').run();
const enq2 = await mf.dispatchFetch('http://enquiry.local/v1/enquiry', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json' },
  body: JSON.stringify({ ref: 'PA-relay-artist', notice, name: 'Cal Buyer', email: 'cal@example.test', message: 'A general question about commissions.' }) });
const au = await db.prepare("SELECT detail FROM audit WHERE action='enquiry' ORDER BY id DESC LIMIT 1").first();
check('R4 if the log is not installed yet, the enquiry still reaches the artist exactly as before and the audit records “not logged”', enq2.status === 200 && /not logged/.test(au.detail), au.detail);

console.log(`\nFOUNDING YEAR AND ENQUIRY LOG · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose();
process.exit(results.every(Boolean) ? 0 : 1);
