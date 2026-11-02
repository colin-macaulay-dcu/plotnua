// PROVE · the Idea Board (Phase 1, 1 Nov 2026). Local only: Miniflare + a local D1 + a throw-away copy of the site.
//   node test/prove-ideas.mjs
// S  intake security and spam protection (the public Worker)
// M  founder moderation in PlotArt Studio
// P  the pipeline endpoint (public fields only)
// E  end to end: submit -> approve -> pipeline (--simulate) -> page and Library card show only approved ideas
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { execFileSync, spawnSync, spawn } from 'node:child_process';
import { mkdtempSync, cpSync, readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = fileURLToPath(new URL('../../..', import.meta.url));
let fails = 0;
const check = (name, ok, extra = '') => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : '  ' + extra}`); if (!ok) fails++; };

const { mf, url } = await start({ ideas: {} });
const db = await mf.getD1Database('DB', 'studio');
let ipn = 0;
// A long synchronous pipeline run can outlast the harness's idle keep-alive socket; one retry on a dropped socket.
const df = async (...a) => { try { return await mf.dispatchFetch(...a); } catch (e) { if (!/fetch failed/.test(String(e))) throw e; return mf.dispatchFetch(...a); } };
const post = async (body, { origin = 'https://plotnua.ie', type = 'application/json', method = 'POST', ip, raw } = {}) => {
  const headers = { 'CF-Connecting-IP': ip || '10.0.0.' + (++ipn) };
  if (origin) headers.Origin = origin;
  if (type) headers['Content-Type'] = type;
  const r = await df('http://ideas.local/v1/ideas', { method, headers, body: method === 'GET' ? undefined : (raw ?? (type === 'application/json' ? JSON.stringify(body) : new URLSearchParams(body).toString())) });
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t, h: r.headers };
};
const count = async () => (await db.prepare('SELECT COUNT(*) n FROM ideas').first()).n;
const old = () => String(Date.now() - 10_000);
const call = async (method, path, email, body, extra = {}) => {
  const r = await df(url + path, { method, headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json', ...extra },
    body: body === undefined ? undefined : JSON.stringify(body) });
  return { s: r.status, j: await r.json().catch(() => ({})) };
};
const pipe = async (auth = 'Bearer ' + PIPELINE_TOKEN) => { const r = await df(url + '/api/pipeline/ideas', { headers: auth ? { Authorization: auth } : {} }); return { s: r.status, j: await r.json().catch(() => ({})) }; };

console.log('S · intake security and spam protection');
let r = await post({ idea: 'A seed library box by the front gate', t: old() });
check('S1 a good idea is accepted with a PN-I reference', r.s === 200 && /^PN-I-\d{6}-[0-9A-F]{4}$/.test(r.j.reference));
check('S2 CORS is granted to plotnua.ie only', r.h.get('Access-Control-Allow-Origin') === 'https://plotnua.ie');
let row = await db.prepare('SELECT * FROM ideas').first();
check('S3 stored as "received" (never public on arrival)', row.status === 'received' && row.published_at === null);
const cols = (await db.prepare("SELECT name FROM pragma_table_info('ideas')").all()).results.map(c => c.name);
check('S4 no name, e-mail, phone, IP or user-agent is stored', !cols.some(c => /name|mail|phone|ip|agent|cookie/i.test(c)) && !JSON.stringify(row).includes('10.0.0.'));
let n0 = await count();
r = await post({ idea: 'From another site entirely here', t: old() }, { origin: 'https://evil.example' }); check('S5 a different Origin is refused (403)', r.s === 403);
r = await post({ idea: 'With no Origin header at all', t: old() }, { origin: null }); check('S6 a missing Origin is refused (403)', r.s === 403);
r = await post({}, { method: 'GET' }); check('S7 GET is refused (405)', r.s === 405);
r = await post({ idea: 'x' }, { type: 'text/plain', raw: 'idea=hello there friend' }); check('S8 another content type is refused (415)', r.s === 415);
r = await post({ idea: 'A perfectly normal idea here', website: 'http://spam', t: old() }); check('S9 honeypot: answered as accepted, nothing stored', r.s === 200 && r.j.reference === 'PN-I-000000-0000');
r = await post({ idea: 'Posted far too quickly by a bot', t: String(Date.now()) }); check('S10 posted < 3 s after the page loaded: silently dropped', r.s === 200 && r.j.reference === 'PN-I-000000-0000');
r = await post({ idea: 'Posted from a page left open too long', t: String(Date.now() - 2 * 86400_000) }); check('S11 page older than 24 h: silently dropped', r.j.reference === 'PN-I-000000-0000');
check('S12 none of the refused or dropped posts was stored', await count() === n0);
const bad = { 'too short': 'tiny', 'too long': 'x'.repeat(161), 'a link': 'See my plans at https://example.ie now', 'a bare domain': 'Look at mysite.com for the drawings',
  'an e-mail address': 'Write to me at me@example.ie please', 'a phone number': 'Call me on 087 123 4567 any evening', 'markup': 'A garden <b>bench</b> in the corner' };
for (const [k, v] of Object.entries(bad)) { r = await post({ idea: v, t: old() }); check(`S13 refused with a friendly reason: ${k}`, r.s === 400 && r.j.error && !/Refused/.test(r.j.error), JSON.stringify(r.j)); }
r = await post({ idea: 'Write to me at someone@example.ie about it', t: old() }); check('S13b an e-mail address is named as an e-mail address (not a website)', /e-mail/.test(r.j.error || ''), JSON.stringify(r.j));
r = await post({ idea: 'A good idea with a strange area', area: 'Crypto', t: old() }); check('S14 an area outside the list is refused', r.s === 400);
r = await post({ idea: 'A good idea with a strange county', county: 'Atlantis', t: old() }); check('S15 a county outside the list is refused', r.s === 400);
r = await post({ idea: 'A good idea with an extra field', email: 'me@example.ie', t: old() }); check('S16 an unexpected field (e.g. email) is refused', r.s === 400);
r = await post({ idea: 'x'.repeat(2100) }); check('S17 an over-sized body is refused (413)', r.s === 413);
check('S18 still nothing stored from S13-S17', await count() === n0);
r = await post({ idea: 'Keep my county private please', county: 'Cork', t: old() });
row = await db.prepare('SELECT * FROM ideas WHERE ref = ?').bind(r.j.reference).first();
check('S19 county is private unless the visitor ticks "show"', row.county === 'Cork' && row.show_county === 0);
r = await post({ idea: 'Show my county with this one', county: 'Kerry', show_county: true, t: old() });
row = await db.prepare('SELECT * FROM ideas WHERE ref = ?').bind(r.j.reference).first(); check('S20 ticked: the county may be shown', row.show_county === 1);
r = await post({ idea: 'Show county ticked but no county', show_county: true, t: old() });
row = await db.prepare('SELECT * FROM ideas WHERE ref = ?').bind(r.j.reference).first(); check('S21 "show" without a county stores nothing to show', row.show_county === 0 && row.county === null);
r = await post({ idea: '  Zero​width   and   spaces\u0007 tidied  ', t: old() });
row = await db.prepare('SELECT * FROM ideas WHERE ref = ?').bind(r.j.reference).first(); check('S22 control and zero-width characters removed, spaces collapsed', row.text === 'Zerowidth and spaces tidied', row.text);
const ip = '192.0.2.9'; const burst = [];
for (let k = 0; k < 4; k++) burst.push((await post({ idea: 'Burst test idea number ' + k, t: old() }, { ip })).s);
check('S23 more than 3 posts in 10 minutes from one address: 429', burst.join() === '200,200,200,429', burst.join());
r = await post({ idea: 'A plain form post without JavaScript', area: 'Garden', t: '' }, { type: 'application/x-www-form-urlencoded' });
check('S24 a no-JavaScript form post gets a thank-you page with the reference', r.s === 200 && /Thank you\./.test(r.t) && /PN-I-\d{6}/.test(r.t) && /ideas\.html/.test(r.t));
check('S25 the thank-you page has a strict CSP, does not echo the idea, and is noindex', /default-src 'none'/.test(r.h.get('Content-Security-Policy')) && !r.t.includes('A plain form post') && r.t.includes('noindex'));
r = await post({ idea: '<script>x</script>', t: '' }, { type: 'application/x-www-form-urlencoded' });
check('S26 a refused form post gets a plain error page (no echo of the input)', r.s === 400 && /Not sent/.test(r.t) && !r.t.includes('<script>x'));
const day = new Date().toISOString().slice(0, 10);
await db.prepare('UPDATE idea_intake_days SET n = 60 WHERE day = ?').bind(day).run();
n0 = await count(); r = await post({ idea: 'One more idea after the daily cap', t: old() });
check('S27 the daily cap (60) refuses further ideas', r.s === 429 && await count() === n0);
await db.prepare('UPDATE idea_intake_days SET n = 0 WHERE day = ?').bind(day).run();
{ const m2 = await start({ ideas: { IDEAS_ENABLED: 'false' } });
  const rr = await m2.mf.dispatchFetch('http://ideas.local/v1/ideas', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json' }, body: JSON.stringify({ idea: 'While the board is switched off' }) });
  check('S28 while not enabled (IDEAS_ENABLED false), every post is refused (503)', rr.status === 503 && (await m2.db.prepare('SELECT COUNT(*) n FROM ideas').first()).n === 0);
  await m2.mf.dispose(); }
for (const k of ['became_discovery', 'status', 'public_text', 'published_at']) {
  r = await post({ idea: 'Trying to set ' + k + ' from the public form', [k]: k === 'status' ? 'approved' : 'discovery-hidden-cars.html', t: old() });
  check(`S30 the public form cannot set ${k} (refused, nothing stored)`, r.s === 400 && !(await db.prepare('SELECT 1 FROM ideas WHERE text LIKE ?').bind('Trying to set ' + k + '%').first()));
}
check('S31 every stored idea arrived as "received", none approved, none linked to a Discovery', (await db.prepare("SELECT COUNT(*) n FROM ideas WHERE status <> 'received' OR became_discovery IS NOT NULL OR published_at IS NOT NULL").first()).n === 0);
const opt = await mf.dispatchFetch('http://ideas.local/v1/ideas', { method: 'OPTIONS', headers: { Origin: 'https://evil.example' } });
check('S29 a preflight from another origin is not granted', opt.headers.get('Access-Control-Allow-Origin') === 'null');

console.log('M · founder moderation in PlotArt Studio');
r = await call('GET', '/api/admin/ideas', 'artist@example.test'); check('M1 a non-founder cannot see the ideas', r.s === 403 || r.s === 401, r.s);
const rq = await mf.dispatchFetch(url + '/api/admin/ideas', { headers: {} }); check('M2 no sign-in: refused', rq.status === 401 || rq.status === 403, rq.status);
r = await call('GET', '/api/admin/ideas', FOUNDER);
check('M3 the founder sees the waiting ideas, none approved', r.s === 200 && r.j.waiting.length >= 8 && r.j.approved.length === 0);
const W = Object.fromEntries(r.j.waiting.map(w => [w.text, w]));
const seed = W['A seed library box by the front gate'], cork = W['Keep my county private please'], kerry = W['Show my county with this one'];
r = await call('POST', '/api/admin/ideas/' + seed.id, FOUNDER, { action: 'approve' }, { 'X-Studio': '' });
check('M4 a state change without the X-Studio header is refused', r.s === 403 || r.s === 400, r.s);
r = await call('POST', '/api/admin/ideas/' + seed.id, FOUNDER, { action: 'approve' }, { Origin: 'https://evil.example' });
check('M5 a cross-site state change is refused', r.s === 403, r.s);
r = await call('POST', '/api/admin/ideas/' + seed.id, FOUNDER, { action: 'approve', public_text: 'A seed-library box by the front gate', area: 'Garden' });
check('M6 approve with tidied wording and a corrected category', r.s === 200 && r.j.approved.length === 1 && r.j.approved[0].public_text === 'A seed-library box by the front gate' && r.j.approved[0].area === 'Garden');
r = await call('POST', '/api/admin/ideas/' + cork.id, FOUNDER, { action: 'approve', public_text: 'Email me at a@b.ie' });
check('M7 the founder cannot approve wording with contact details', r.s === 400);
r = await call('POST', '/api/admin/ideas/' + cork.id, FOUNDER, { action: 'approve', area: 'Space' });
check('M8 a private county stays private when approved', r.s === 200);
r = await call('POST', '/api/admin/ideas/' + kerry.id, FOUNDER, { action: 'approve', area: 'Neighbourhood', hide_county: true });
check('M9 the founder can hide a county the visitor chose to show', r.s === 200 && r.j.approved.find(a => a.id === kerry.id).show_county === 0);
const burst0 = Object.values(W).find(w => w.text === 'Burst test idea number 0');
r = await call('POST', '/api/admin/ideas/' + burst0.id, FOUNDER, { action: 'not_approve' });
check('M10 decline: moves to "declined", never public', r.s === 200 && r.j.decided.some(d => d.id === burst0.id && d.status === 'not_approved'));
r = await call('POST', '/api/admin/ideas/' + burst0.id, FOUNDER, { action: 'approve' }); check('M11 a declined idea cannot then be approved', r.s === 409);
r = await call('POST', '/api/admin/ideas/' + seed.id, FOUNDER, { action: 'save', became_discovery: 'http://evil.example' }); check('M12 a "Now a Discovery" link must be a Discovery page', r.s === 400);
r = await call('POST', '/api/admin/ideas/' + seed.id, FOUNDER, { action: 'save', became_discovery: 'discovery-hidden-cars.html' }); check('M13 the founder links an idea to the Discovery it became', r.s === 200);
r = await call('POST', '/api/admin/ideas/' + seed.id, FOUNDER, { action: 'teleport' }); check('M14 an unknown action is refused', r.s === 400);
const aud = (await db.prepare("SELECT action, actor FROM audit WHERE action LIKE 'idea_%'").all()).results;
check('M15 every decision is in the audit log', ['idea_approve', 'idea_not_approve', 'idea_save'].every(a => aud.some(x => x.action === a && x.actor === FOUNDER)), JSON.stringify(aud));

await db.prepare("UPDATE ideas SET public_text = 'Waiting idea with wording set' WHERE status = 'received' AND id = (SELECT id FROM ideas WHERE status='received' LIMIT 1)").run();
console.log('P · the pipeline endpoint');
r = await pipe(null); check('P1 no token: refused', r.s === 401 || r.s === 403, r.s);
r = await pipe('Bearer wrong'); check('P2 wrong token: refused', r.s === 401 || r.s === 403, r.s);
r = await pipe();
check('P3 returns approved ideas only (3)', r.s === 200 && r.j.ideas.length === 3);
const sentTexts = new Set(r.j.ideas.map(i => i.text)), notApproved = (await db.prepare("SELECT text, public_text FROM ideas WHERE status <> 'approved'").all()).results;
check('P3b no waiting, declined or removed idea is ever sent (even one with wording already set)', notApproved.length > 5 && notApproved.every(x => !sentTexts.has(x.text) && !sentTexts.has(x.public_text)));
check('P4 public fields only: wording, area, county, month and year, Discovery link (no id, reference, exact time, status or reviewer)', r.j.ideas.every(i => Object.keys(i).every(k => ['text', 'area', 'county', 'month', 'became_discovery'].includes(k)) && /^\d{4}-\d{2}$/.test(i.month)));
check('P5 approved wording is used; private and hidden counties are not sent', r.j.ideas.some(i => i.text === 'A seed-library box by the front gate') && r.j.ideas.every(i => i.county === null));
const order = (await db.prepare("SELECT COALESCE(public_text, text) t FROM ideas WHERE status='approved' ORDER BY published_at DESC, id DESC").all()).results.map(x => x.t);
check('P6 newest first', JSON.stringify(r.j.ideas.map(i => i.text)) === JSON.stringify(order));
await db.prepare("UPDATE ideas SET decided_at = '2026-01-01T00:00:00Z' WHERE id = ?").bind(burst0.id).run();
await pipe(); check('P7 declined ideas are deleted after 30 days', !(await db.prepare('SELECT 1 FROM ideas WHERE id = ?').bind(burst0.id).first()));
// Retention (founder decision 1 Nov 2026): waiting ideas 90 days with a warning; approved ideas never deleted automatically.
{ const ins = (id, status, created, extra = '') => db.prepare(`INSERT INTO ideas (id, ref, text, status, created_at, published_at, decided_at) VALUES (?,?,?,?,?,?,?)`)
    .bind(id, 'PN-I-RET-' + id.slice(-4), 'Retention test idea ' + id, status, created, status === 'approved' ? created : null, status === 'approved' ? created : null).run();
  const daysAgo = d => new Date(Date.now() - d * 86400_000).toISOString();
  await ins('iret0000000000091', 'received', daysAgo(91));
  await ins('iret0000000000080', 'received', daysAgo(80));
  await ins('iret0000000000010', 'received', daysAgo(10));
  await ins('iret0000000000400', 'approved', daysAgo(400));
  const adm = (await call('GET', '/api/admin/ideas', FOUNDER)).j;
  const has = id => db.prepare('SELECT 1 FROM ideas WHERE id = ?').bind(id).first();
  check('R1 a waiting idea older than 90 days is deleted automatically', !(await has('iret0000000000091')));
  check('R2 waiting ideas younger than 90 days are kept', !!(await has('iret0000000000080')) && !!(await has('iret0000000000010')));
  check('R3 an approved idea is never deleted automatically, however old (400 days)', !!(await has('iret0000000000400')));
  const w80 = adm.waiting.find(i => i.id === 'iret0000000000080'), w10 = adm.waiting.find(i => i.id === 'iret0000000000010');
  check('R4 the dashboard shows the deletion date and warns within 14 days', w80 && w80.days_left === 10 && w10 && w10.days_left === 80 && adm.expiring_soon >= 1 && adm.pending_days === 90 && adm.warn_days === 14, JSON.stringify([w80 && w80.days_left, w10 && w10.days_left, adm.expiring_soon]));
  r = await call('POST', '/api/admin/ideas/iret0000000000400', FOUNDER, { action: 'delete' });
  check('R5 "Delete now" refuses an idea that is on the board (remove it first)', r.s === 409 && !!(await has('iret0000000000400')));
  r = await call('POST', '/api/admin/ideas/iret0000000000010', FOUNDER, { action: 'delete' });
  check('R6 "Delete now" erases a waiting idea at once (removal request), audited by reference only', r.s === 200 && !(await has('iret0000000000010')) &&
    !!(await db.prepare("SELECT 1 FROM audit WHERE action = 'idea_delete' AND detail LIKE '%PN-I-RET-0010%' AND detail NOT LIKE '%Retention test%'").first()));
  r = await call('POST', '/api/admin/ideas/iret0000000000080', FOUNDER, { action: 'delete' }, { 'Cf-Access-Jwt-Assertion': token('artist@example.test') });
  check('R7 only the founder can delete', (r.s === 401 || r.s === 403) && !!(await has('iret0000000000080')));
  await db.prepare("DELETE FROM ideas WHERE id LIKE 'iret%'").run();
}

console.log('E · end to end (submit -> approve -> pipeline -> page)');
const SITE = mkdtempSync(join(tmpdir(), 'ib-site-'));
cpSync(REPO, SITE, { recursive: true, filter: src => !/[\\/]\.git([\\/]|$)|[\\/]node_modules([\\/]|$)/.test(src) });
const git = (...a) => execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@plotnua.invalid', ...a], { cwd: SITE, encoding: 'utf8' }).trim();
git('init', '-q'); git('add', '-A'); git('commit', '-q', '-m', 'main with the empty Idea Board (test copy of the branch)');
// asynchronous, so the local Studio keeps serving while the pipeline runs
const publish = () => new Promise(res => { const c = spawn('python3', ['atlas-tools/plotnua-ideas-publish.py', '--studio', url, '--token', PIPELINE_TOKEN, '--simulate'], { cwd: SITE });
  let stdout = '', stderr = ''; c.stdout.on('data', d => stdout += d); c.stderr.on('data', d => stderr += d); c.on('close', status => res({ status, stdout, stderr })); });
const pageText = () => readFileSync(join(SITE, 'ideas.html'), 'utf8'), libText = () => readFileSync(join(SITE, 'discoveries.html'), 'utf8');
let p = await publish();
check('E1 the pipeline publishes the three approved ideas (simulated)', p.status === 0 && /3 approved ideas · verified \(simulated\)/.test(p.stdout), p.stdout + p.stderr);
check('E2 only the snapshot, the page and the Library card changed', git('diff', '--name-only', 'HEAD~1', 'HEAD').split('\n').sort().join() === 'atlas-tools/idea-board/approved-ideas.json,discoveries.html,ideas.html');
let pg = pageText(), lib = libText();
check('E3 the page shows the approved wording, not the original', pg.includes('A seed-library box by the front gate') && !pg.includes('A seed library box'));
check('E4 nothing that was not approved appears (waiting, declined)', !['Show county ticked but no county', 'Burst test idea number', 'Zerowidth'].some(t => pg.includes(t) || lib.includes(t)));
check('E5 private and hidden counties are not shown', !/Co\. (Cork|Kerry)/.test(pg));
check('E6 the "Now a Discovery" link is shown', pg.includes('href="discovery-hidden-cars.html">Now a PlotNua Discovery'));
check('E7 the Library card shows the latest three, newest first', (lib.match(/<li class="ib-note">/g) || []).length === 3);
p = await publish(); check('E8 a second run with no change publishes nothing', p.status === 0 && /nothing to publish/.test(p.stdout), p.stdout);
for (let k = 1; k <= 2; k++) {
  const rr = await post({ idea: `A later idea, number ${k}, for a shared tool shed`, t: old() });
  const w = (await call('GET', '/api/admin/ideas', FOUNDER)).j.waiting.find(x => x.ref === rr.j.reference);
  await new Promise(res => setTimeout(res, 1100));
  await call('POST', '/api/admin/ideas/' + w.id, FOUNDER, { action: 'approve', area: 'Neighbourhood' });
}
p = await publish(); lib = libText(); pg = pageText();
const cardNotes = [...lib.matchAll(/<li class="ib-note">(.*?)<\/li>/g)].map(m => m[1]);
check('E9 with five approved, the card shows the latest three; the page shows all five', cardNotes.length === 3 && cardNotes[0].includes('number 2') && cardNotes[1].includes('number 1') && (pg.match(/<li class="ib-n">/g) || []).length === 5, cardNotes.join(' | '));
await call('POST', '/api/admin/ideas/' + seed.id, FOUNDER, { action: 'remove' });
p = await publish(); pg = pageText();
check('E10 a removed idea leaves the board on the next run', p.status === 0 && !pg.includes('seed-library'));
writeFileSync(join(SITE, 'discoveries.html'), libText().replace('Discovery Library', 'Discovery Libary'));
git('commit', '-qam', 'unrelated Library edit (test)');
await call('POST', '/api/admin/ideas/' + cork.id, FOUNDER, { action: 'save', public_text: 'Keep my county private, please' });
p = await publish();
check('E11 boundary: the pipeline stays within the card block (unrelated edits on main are untouched)', p.status === 0 && libText().includes('Discovery Libary'), p.stdout + p.stderr);
const before = git('rev-parse', 'HEAD');
const tampered = readFileSync(join(SITE, 'atlas-tools/build-idea-board.py'), 'utf8').replace('LIB.write_text(new_lib, encoding="utf-8")', 'LIB.write_text(new_lib.replace("</title>", " </title>", 1), encoding="utf-8")');
writeFileSync(join(SITE, 'atlas-tools/build-idea-board.py'), tampered); git('commit', '-qam', 'a builder that changes the Library (planted fault)');
await call('POST', '/api/admin/ideas/' + cork.id, FOUNDER, { action: 'save', public_text: 'Keep my county private, thanks' });
const head = git('rev-parse', 'HEAD'); p = await publish();
check('E12 planted fault: a change outside the card block is REFUSED and the commit dropped', p.status === 1 && /outside the Idea Board card/.test(p.stdout) && git('rev-parse', 'HEAD') === head, p.stdout);
const sp = spawnSync('python3', ['atlas-tools/plotnua-ideas-publish.py', '--studio', 'https://studio.example', '--token', 'x', '--simulate'], { cwd: SITE, encoding: 'utf8' });
check('E13 --simulate refuses anything but a local Studio', sp.status !== 0 && /REFUSED/.test(sp.stdout + sp.stderr));
rmSync(SITE, { recursive: true, force: true });
void before;

// D · publish on approval (2 Nov 2026): founder actions that change the public board start the publishing workflow
console.log('D · publish on approval');
{ const { createServer } = await import('node:http');
  const hits = []; let code = 204;
  const gh = createServer((req, res) => { let b = ''; req.on('data', c => b += c); req.on('end', () => { hits.push({ method: req.method, url: req.url, auth: req.headers.authorization, body: b }); res.statusCode = code; res.end(); }); });
  await new Promise(r => gh.listen(0, '127.0.0.1', r)); const GH = 'http://127.0.0.1:' + gh.address().port;
  const m3 = await start({ env: { GITHUB_DISPATCH_TOKEN: 'test-dispatch-token', GITHUB_API: GH }, ideas: {} });
  const db3 = m3.db;
  const c3 = async (id, body, email = FOUNDER) => { const r = await m3.mf.dispatchFetch(m3.url + '/api/admin/ideas/' + id, { method: 'POST', headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); return { s: r.status, j: await r.json().catch(() => ({})) }; };
  const sub = async (idea, ip) => (await m3.mf.dispatchFetch('http://ideas.local/v1/ideas', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json', 'CF-Connecting-IP': ip }, body: JSON.stringify({ idea, t: old() }) })).json();
  const a1 = await sub('A real-looking test idea for dispatch checks', '10.9.0.1'), a2 = await sub('A second test idea for the decline path', '10.9.0.2');
  check('D1 a public submission never starts publishing', hits.length === 0);
  const idOf = async ref => (await db3.prepare('SELECT id FROM ideas WHERE ref = ?').bind(ref).first()).id;
  const i1 = await idOf(a1.reference), i2 = await idOf(a2.reference);
  let r = await c3(i1, { action: 'approve' });
  const h = hits[0] || {};
  check('D2 approve starts the Idea Board publishing workflow on main, with the token, at once', r.s === 200 && r.j.publish === 'requested' && hits.length === 1 && h.method === 'POST' &&
    h.url === '/repos/colin-macaulay-dcu/plotnua/actions/workflows/plotnua-ideas-publish.yml/dispatches' && h.auth === 'Bearer test-dispatch-token' && JSON.parse(h.body).ref === 'main', JSON.stringify([r.j.publish, h]));
  r = await c3(i1, { action: 'save', public_text: 'A real-looking test idea for dispatch checks, tidied' });
  check('D3 an edit of an idea on the board starts publishing', r.s === 200 && r.j.publish === 'requested' && hits.length === 2);
  r = await c3(i2, { action: 'not_approve' });
  check('D4 declining a waiting idea changes nothing public: no publishing run', r.s === 200 && r.j.publish === 'none' && hits.length === 2);
  r = await c3(i2, { action: 'delete' });
  check('D5 deleting a declined idea: no publishing run', r.s === 200 && r.j.publish === 'none' && hits.length === 2);
  r = await c3(i1, { action: 'remove' });
  check('D6 removing an idea from the board starts publishing', r.s === 200 && r.j.publish === 'requested' && hits.length === 3);
  r = await c3(i1, { action: 'approve' }, 'artist@example.test');
  check('D7 a non-founder cannot trigger anything', (r.s === 401 || r.s === 403) && hits.length === 3);
  code = 500; const a3 = await sub('A third test idea when GitHub is unavailable', '10.9.0.3');
  r = await c3(await idOf(a3.reference), { action: 'approve' });
  check('D8 if GitHub refuses, the approval is still saved and the founder is told it falls back to the schedule', r.s === 200 && r.j.publish === 'failed' && r.j.approved.length === 1);
  check('D9 the token never appears in a reply or the audit log', !JSON.stringify(r.j).includes('test-dispatch-token') &&
    !(await db3.prepare("SELECT 1 FROM audit WHERE detail LIKE '%test-dispatch-token%'").first()));
  await m3.mf.dispose(); gh.close();
  const m4 = await start({ ideas: {} });
  const a4 = (await (await m4.mf.dispatchFetch('http://ideas.local/v1/ideas', { method: 'POST', headers: { Origin: 'https://plotnua.ie', 'Content-Type': 'application/json' }, body: JSON.stringify({ idea: 'Without a token configured at all', t: old() }) })).json());
  const id4 = (await m4.db.prepare('SELECT id FROM ideas WHERE ref = ?').bind(a4.reference).first()).id;
  const r4 = await m4.mf.dispatchFetch(m4.url + '/api/admin/ideas/' + id4, { method: 'POST', headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER), 'X-Studio': '1', 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'approve' }) });
  check('D10 without a token the Studio works as before (scheduled publishing)', (await r4.json()).publish === 'scheduled');
  await m4.mf.dispose();
  const intake = readFileSync(join(REPO, 'worker/plotart-studio/src/ideas.js'), 'utf8') + readFileSync(join(REPO, 'worker/plotart-studio/wrangler.ideas.toml'), 'utf8');
  check('D11 the public intake Worker has no GitHub credential or call', !/github|DISPATCH/i.test(intake));
}
await mf.dispose();
console.log(`\nIDEA BOARD · ${fails ? 'FAIL (' + fails + ')' : 'PASS'}`);
process.exit(fails ? 1 : 0);
