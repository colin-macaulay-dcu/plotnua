// PROVE · Exhibitions & Achievements (Phase C, development 25 Nov 2026). Local only: Miniflare D1/R2 and synthetic
// artists. Shows that:
//   X1  the three copies of the format rule agree (Studio server src/lib.js, the Studio editor's live preview in
//       ui/studio.js, the publisher atlas-tools/plotart_gallery.py), and the Studio preview and the published page make
//       the same section markup (src/render.js vs atlas-tools/plotart_gallery_pages.py);
//   X2  the section is hidden entirely when empty, and a gallery without it is byte-for-byte what it was;
//   X3  the artist can write, change and clear it independently; the biography is never touched;
//   X4  it is a full-review change (the founder sees it before it is public); an instant update never carries it;
//   X5  what the Studio exports the publisher accepts, and the publisher refuses anything outside the rules;
//   X6  before migration 0026 the Studio hides the editor and refuses the field, and everything else works as before;
//   X7  migration 0026 adds one column to artists and changes no row.
//   node test/prove-exhibitions.mjs
import { start, token, FOUNDER } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
import { seedPublished, artistRows } from './seed.mjs';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import * as L from '../src/lib.js';
import { exhibitionsSection } from '../src/render.js';

const HERE = new URL('..', import.meta.url).pathname, ROOT = new URL('../../..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const py = (code, input) => execFileSync('python3', ['-c', `import sys, json; sys.path.insert(0, ${JSON.stringify(ROOT + 'atlas-tools')})\n${code}`],
  { input: JSON.stringify(input), encoding: 'utf8' });

console.log('PROVE · Exhibitions & Achievements');

// ------------------------------------------------------------------ X1 · one format rule, three copies; one markup, two copies
const FIX = [
  '## Solo exhibitions\n- 2025 · Tidelines, The Example Gallery, Dublin\n- 2023 · Salt and Stone, Harbour Arts Centre, Cork\n\n## Awards\n• 2024 · Shortlisted, Example Painting Prize',
  'Selected for the Example Open in 2022.\nWork held in private collections in Ireland and the UK.',
  '# One hash\n### Three hashes\n#### four hashes stay a paragraph\n#No space stays a paragraph',
  '* star item\n– en dash item\n-no space is a paragraph\n  -  indented item with spaces  \n\n\n- after blank lines',
  'Line with \r\nWindows endings\r- and an old Mac line end',
  'Quotes "and" ‘apostrophes’ & ampersands · and Irish fadas: Gaillimh, Éire, Ciarán',
  '',
];
const UI = readFileSync(HERE + 'ui/studio.js', 'utf8');
const uiSrc = UI.slice(UI.indexOf('  function cvBlocks(text) {'), UI.indexOf('  const cvHtml'));
const uiBlocks = new Function(`${uiSrc}; return cvBlocks;`)();
const pyBlocks = JSON.parse(py('import plotart_gallery as G\nprint(json.dumps([G.exhibition_blocks(t) for t in json.load(sys.stdin)]))', FIX));
const jsBlocks = FIX.map(t => L.exhibitionBlocks(t)), edBlocks = FIX.map(t => uiBlocks(t));
check('X1a the Studio server, the editor preview and the publisher read every fixture identically',
  JSON.stringify(jsBlocks) === JSON.stringify(pyBlocks) && JSON.stringify(jsBlocks) === JSON.stringify(edBlocks),
  JSON.stringify({ js: jsBlocks, py: pyBlocks, ed: edBlocks }));
check('X1b headings, list items and paragraphs are recognised as specified',
  JSON.stringify(jsBlocks[0]) === JSON.stringify([['h', 'Solo exhibitions'], ['ul', ['2025 · Tidelines, The Example Gallery, Dublin', '2023 · Salt and Stone, Harbour Arts Centre, Cork']], ['h', 'Awards'], ['ul', ['2024 · Shortlisted, Example Painting Prize']]])
  && jsBlocks[2].map(b => b[0]).join() === 'h,h,p,p' && jsBlocks[3].map(b => b[0]).join() === 'ul,p,ul', JSON.stringify([jsBlocks[2], jsBlocks[3]]));
const pySect = JSON.parse(py('import plotart_gallery_pages as P\nprint(json.dumps([P.exhibitions_section({"exhibitions": t}) for t in json.load(sys.stdin)]))', FIX));
const jsSect = FIX.map(t => exhibitionsSection({ exhibitions: t }));
check('X1c the Studio preview and the published page make byte-identical section markup', JSON.stringify(jsSect) === JSON.stringify(pySect),
  jsSect.map((s, i) => s === pySect[i] ? '' : `#${i}:\n${s}\n---\n${pySect[i]}`).join('\n'));
check('X1d text is escaped (no markup can be injected)', jsSect[5].includes('&amp; ampersands') && !/<script/.test(exhibitionsSection({ exhibitions: '<script>x</script>' })));
check('X1e the section has its own heading and an anchor the page links to', jsSect[0].includes('id="exhibitions"') && jsSect[0].includes('<h2 id="agCvH">Exhibitions &amp; Achievements</h2>'));

// ------------------------------------------------------------------ X2 · hidden when empty
check('X2a no text, no section (empty, blank or missing)', exhibitionsSection({}) === '' && exhibitionsSection({ exhibitions: null }) === '' && jsSect[6] === '');
const snapNone = L.snapshot({ slug: 'a', display_name: 'A', bio: 'b' }, [], []);
const snapSome = L.snapshot({ slug: 'a', display_name: 'A', bio: 'b', exhibitions: '## X\n- y' }, [], []);
check('X2b a snapshot without the section has no exhibitions key at all (every earlier snapshot stays byte-for-byte the same)',
  !('exhibitions' in snapNone.artist) && snapSome.artist.exhibitions === '## X\n- y');

// ------------------------------------------------------------------ Studio harness
async function harness(port, opts = {}) {
  const { mf, url, db } = await start({ port, ...opts });
  const H = email => ({ ...(email ? { 'Cf-Access-Jwt-Assertion': token(email) } : {}), 'X-Studio': '1', 'Content-Type': 'application/json' });
  const call = async (method, path, email, body) => { const r = await mf.dispatchFetch(url + path, { method, headers: H(email), body: body === undefined ? undefined : JSON.stringify(body) }); const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch {} return { s: r.status, j, t }; };
  return { mf, db, url, call };
}
const CV = '## Solo exhibitions\n- 2025 · Tidelines, The Example Gallery, Dublin\n\n## Collections\n- Example County Council public collection';
const h = await harness(8871, { env: { INSTANT_AUTOPUBLISH: 'true' } });
const ANN = 'ann-example@example.test', BEN = 'ben-example@example.test';
await seedPublished(h.db, { id: 'aann', slug: 'ann-example', email: ANN, name: 'Ann Example', works: 3, licence: null });
await seedPublished(h.db, { id: 'aben', slug: 'ben-example', email: BEN, name: 'Ben Example', works: 2 });
const acc = await acceptAgreement(h.mf, h.url, ANN);
const annBefore = await artistRows(h.db, 'aann'), benBefore = await artistRows(h.db, 'aben');
const bioBefore = (await h.db.prepare('SELECT bio FROM artists WHERE id = ?').bind('aann').first()).bio;

// ------------------------------------------------------------------ X3 · the artist edits it independently
let r = await h.call('GET', '/api/me', ANN);
check('X3a the Studio offers the editor once the column exists', r.s === 200 && r.j.exhibitions_available === true && (r.j.artist.exhibitions ?? null) === null);
r = await h.call('PUT', '/api/me/profile', ANN, { exhibitions: CV });
let row = await h.db.prepare('SELECT bio, exhibitions FROM artists WHERE id = ?').bind('aann').first();
check('X3b the artist saves the section; the biography is not touched', r.s === 200 && row.exhibitions === CV && row.bio === bioBefore, JSON.stringify([r.s, r.j]));
r = await h.call('PUT', '/api/me/profile', ANN, { exhibitions: 'x'.repeat(6001) });
check('X3c more than 6,000 characters is refused, with a clear message', r.s === 400 && /6000|6,000/.test(r.j.error || r.t), r.t);
r = await h.call('PUT', '/api/me/profile', ANN, { exhibitions: '## ' + 'A'.repeat(101) + '\n- item' });
check('X3d a heading longer than 100 characters is refused', r.s === 400 && /heading/i.test(r.j.error || r.t), r.t);
r = await h.call('PUT', '/api/me/profile', ANN, { exhibitions: 'Shown at <b>X</b> Gallery' });
check('X3e < or > is refused (no markup)', r.s === 400, r.t);
r = await h.call('PUT', '/api/me/profile', ANN, { exhibitions: 'Contact me at ann@example.test for my full CV' });
check('X3f contact details are refused, as in the biography', r.s === 400 && /email|contact/i.test(r.j.error || r.t), r.t);
row = await h.db.prepare('SELECT exhibitions FROM artists WHERE id = ?').bind('aann').first();
check('X3g refused saves leave the saved text exactly as it was', row.exhibitions === CV);
r = await h.call('GET', '/preview/', ANN);
check('X3h the artist\'s preview shows the section after "About" and the link under the name', r.s === 200
  && r.t.indexOf('id="agAboutH"') < r.t.indexOf('id="exhibitions"') && r.t.includes('<p class="pa-ag-jump"><a href="#exhibitions">')
  && r.t.includes('<li>2025 · Tidelines, The Example Gallery, Dublin</li>'), r.t.slice(0, 300));
r = await h.call('GET', '/preview/', BEN);
check('X3i another artist\'s preview has no section and no link', r.s === 200 && !r.t.includes('pa-ag-cv') && !r.t.includes('pa-ag-jump'));

// ------------------------------------------------------------------ X4 · full review; instant updates never carry it
const live = (await h.db.prepare('SELECT snapshot FROM versions WHERE artist_id = ? ORDER BY version DESC LIMIT 1').bind('aann').first()).snapshot;
const w1 = (await h.db.prepare('SELECT id FROM artworks WHERE artist_id = ? ORDER BY ord LIMIT 1').bind('aann').first()).id;
r = await h.call('POST', `/api/artworks/${w1}/availability`, ANN, { availability: 'sold' });
const inst = r.j?.instant_version ? JSON.parse((await h.db.prepare('SELECT snapshot FROM versions WHERE artist_id = ? AND version = ?').bind('aann', r.j.instant_version).first()).snapshot) : null;
check('X4a an instant update (sold) publishes the approved profile, never the unreviewed section',
  inst && !('exhibitions' in inst.artist) && inst.works.find(w => w.id === w1)?.availability === 'sold', JSON.stringify([r.j, inst && inst.artist]));
r = await h.call('POST', '/api/submit', ANN, {});
const subRow = await h.db.prepare("SELECT tier, changes FROM submissions WHERE artist_id = ? ORDER BY created_at DESC LIMIT 1").bind('aann').first();
const subChanges = subRow ? JSON.parse(subRow.changes) : [];
check('X4b submitting it is a full-review change, listed as "Exhibitions & Achievements" in what the founder reviews', r.s === 200 && r.j.tier === 'full'
  && subChanges.some(c => c.tier === 'full' && JSON.stringify(c).includes('Exhibitions & Achievements')), JSON.stringify([r.j, subChanges]).slice(0, 500));
const ov = (await h.call('GET', '/api/admin/overview', FOUNDER)).j;
const sub = ov.submissions.find(x => x.artist_id === 'aann');
check('X4c the founder sees it waiting for review; nothing is public yet', !!sub && !JSON.parse(live).artist.exhibitions);
r = sub ? await h.call('POST', `/api/admin/submissions/${sub.id}/decision`, FOUNDER, { decision: 'approve' }) : { s: 0 };
const appr = JSON.parse((await h.db.prepare('SELECT snapshot FROM versions WHERE artist_id = ? ORDER BY version DESC LIMIT 1').bind('aann').first()).snapshot);
check('X4d after the founder approves, the approved version carries the section', r.s === 200 && appr.artist.exhibitions === CV, JSON.stringify(r.j));

// ------------------------------------------------------------------ X5 · the publisher accepts the export and refuses what breaks the rules
const exp = L.exportGallery(appr, { version: 9, approvedAt: '2026-11-25T20:00:00.000Z', licenceVersion: 'PA-GPIL-2026-11', licenceAcceptedAt: '2026-11-05T17:00:00.000Z', artistId: 'aann' });
const verdict = g => py(`import plotart_gallery as G
g = json.load(sys.stdin)
try:
    G.validate_export(g); print("OK")
except G.Refused as e:
    print("REFUSED " + str(e))`, g).trim();
const okNone = verdict(L.exportGallery(L.snapshot({ ...appr.artist, exhibitions: null }, [], []), { version: 9, approvedAt: '2026-11-25T20:00:00.000Z', licenceVersion: 'x', licenceAcceptedAt: 'y', artistId: 'aann' }));
const base = verdict(exp);
check('X5a the export carries the section and the publisher\'s field check accepts it', exp.artist.exhibitions === CV && !/exhibitions/.test(base), base);
const bad = [['x'.repeat(6001), 'too long'], ['## ' + 'A'.repeat(101), 'long heading'], ['<b>x</b> gallery', 'markup'], ['Call 087 123 4567 for details', 'phone']];
const refusals = bad.map(([t, why]) => [why, verdict({ ...exp, artist: { ...exp.artist, exhibitions: t } })]);
check('X5b the publisher refuses a section outside the rules (too long, long heading, markup, contact details)',
  refusals.every(([, v]) => v.startsWith('REFUSED') && /exhibition/i.test(v)), JSON.stringify(refusals));
check('X5c an export without the section has no exhibitions key', !('exhibitions' in L.exportGallery(snapNone, { version: 1, approvedAt: 'x', licenceVersion: 'x', licenceAcceptedAt: 'x', artistId: 'a' }).artist), okNone);

// ------------------------------------------------------------------ X3 continued · clearing, and other artists untouched
r = await h.call('PUT', '/api/me/profile', ANN, { exhibitions: '' });
row = await h.db.prepare('SELECT bio, exhibitions FROM artists WHERE id = ?').bind('aann').first();
check('X3j the artist can clear it (stored as empty, so the section would disappear after review)', r.s === 200 && row.exhibitions === null && row.bio === bioBefore);
check('X3k another artist\'s records never change', JSON.stringify(await artistRows(h.db, 'aben')) === JSON.stringify(benBefore));
await h.mf.dispose();

// ------------------------------------------------------------------ X6 · before migration 0026
const SCHEMA = readFileSync(HERE + 'schema.sql', 'utf8');
const PRE = SCHEMA.replace(/\nALTER TABLE artists ADD COLUMN exhibitions[^\n]*\n?/, '\n');
const p = await harness(8872, { schemaSql: PRE });
await seedPublished(p.db, { id: 'aann', slug: 'ann-example', email: ANN, name: 'Ann Example', works: 3 });
r = await p.call('GET', '/api/me', ANN);
check('X6a without the column the Studio reports the editor unavailable (it is not drawn)', PRE !== SCHEMA && r.s === 200 && r.j.exhibitions_available === false);
r = await p.call('PUT', '/api/me/profile', ANN, { exhibitions: CV });
check('X6b and refuses the field politely, changing nothing', r.s === 503, r.t);
r = await p.call('PUT', '/api/me/profile', ANN, { bio: 'Ann Example is a synthetic test artist whose biography still saves before the migration.' });
const r2 = await p.call('GET', '/preview/', ANN);
check('X6c everything else works as before (biography saves, preview renders, no section)', r.s === 200 && r2.s === 200 && !r2.t.includes('pa-ag-cv'), r.t);
await p.mf.dispose();

// ------------------------------------------------------------------ X7 · migration 0026 on the schema without it
const MIG = readFileSync(HERE + 'migrations/0026_artist_exhibitions.sql', 'utf8');
const ddl = MIG.slice(MIG.indexOf('@@DDL-BEGIN'), MIG.indexOf('@@DDL-END')).split('\n').filter(l => l.trim() && !l.startsWith('--') && !l.includes('@@')).join('\n');
const m = await harness(8873, { schemaSql: PRE });
await seedPublished(m.db, { id: 'aann', slug: 'ann-example', email: ANN, name: 'Ann Example', works: 3 });
const objs = async () => (await m.db.prepare("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' AND name <> 'artists' ORDER BY type, name").all()).results;
const allRows = async () => { const o = {}; for (const { name } of (await m.db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%'").all()).results) o[name] = (await m.db.prepare(`SELECT * FROM ${name} ORDER BY rowid`).all()).results; return o; };
const o0 = await objs(), d0 = await allRows();
await m.db.prepare(ddl).run();
const o1 = await objs(), d1 = await allRows();
const cols = (await m.db.prepare("SELECT name FROM pragma_table_info('artists')").all()).results.map(x => x.name);
const sameRows = Object.keys(d0).every(t => JSON.stringify(t === 'artists' ? d0[t] : d0[t]) === JSON.stringify(t === 'artists' ? d1[t].map(({ exhibitions, ...x }) => x) : d1[t]));
check('X7a the migration is the one ALTER in its DDL block', /^ALTER TABLE artists ADD COLUMN exhibitions TEXT CHECK/.test(ddl) && ddl.split(';').filter(x => x.trim()).length === 1, ddl);
check('X7b it adds one column to artists, every existing artist starts empty, and no other table, index, trigger or row changes',
  cols.includes('exhibitions') && d1.artists.every(a => a.exhibitions === null) && JSON.stringify(o0) === JSON.stringify(o1) && sameRows);
let again = false; try { await m.db.prepare(ddl).run(); } catch { again = true; }
check('X7c running it a second time is refused by the database and changes nothing', again);
await m.mf.dispose();

const pass = results.filter(Boolean).length;
console.log(`EXHIBITIONS & ACHIEVEMENTS · ${results.length} checks, ${pass} passed, ${results.length - pass} failed`);
process.exit(pass === results.length ? 0 : 1);
