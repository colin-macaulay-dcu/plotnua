// PROVE · Exhibitions & Achievements (Phase C; Dave King's feedback). Synthetic artists only; the Worker runs locally
// (Miniflare/workerd) with a local D1. Nothing here touches Cloudflare.
//   node test/prove-achievements.mjs
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import * as XA from '../src/achievements.js';
import * as L from '../src/lib.js';
import { xaSection, XA_JUMP } from '../src/render.js';

const HERE = new URL('..', import.meta.url).pathname, ROOT = HERE + '../../';
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
const mkcall = (mf, url) => async (method, path, email, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' };
  if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const py = (code, input) => execFileSync('python3', ['-c', `import sys, json; sys.path.insert(0, ${JSON.stringify(ROOT + 'atlas-tools')}); ${code}`], { input: JSON.stringify(input), encoding: 'utf8' });
const no = f => { try { f(); return false; } catch { return true; } };
console.log('PROVE · Exhibitions & Achievements (Phase C)');

/* ---- the format: free-form headings, paragraphs and lists; nothing structured is required ---- */
const messy = '  # Solo exhibitions  \r\n• 2025  The Lighthouse,   Dublin\r\n* 2023 Highlanes, Drogheda\n\n\n\nSelected group shows below.\nThey were curated.\n## Awards ##\n-   RHA Annual Exhibition prize, 2024\n\n### Collections\nOPW State Art Collection';
const stored = XA.normalise(messy);
check('F1 headings, list items and paragraphs are recognised however they are typed (#, ##, •, *, -; CRLF; extra spaces), and stored in one clean form',
  stored === '## Solo exhibitions\n\n- 2025 The Lighthouse, Dublin\n- 2023 Highlanes, Drogheda\n\nSelected group shows below.\nThey were curated.\n\n## Awards\n\n- RHA Annual Exhibition prize, 2024\n\n## Collections\n\nOPW State Art Collection', JSON.stringify(stored));
check('F2 the blocks read back as written: 3 headings, 2 lists, 2 paragraphs (lines of a paragraph join)',
  JSON.stringify(XA.blocks(stored)) === JSON.stringify([{ h: 'Solo exhibitions' }, { ul: ['2025 The Lighthouse, Dublin', '2023 Highlanes, Drogheda'] }, { p: 'Selected group shows below. They were curated.' },
    { h: 'Awards' }, { ul: ['RHA Annual Exhibition prize, 2024'] }, { h: 'Collections' }, { p: 'OPW State Art Collection' }]));
check('F3 empty or blank text means no section (null); a plain paragraph alone is fine (nothing structured is required)',
  XA.normalise('') === null && XA.normalise('  \n\n ') === null && XA.normalise(null) === null && XA.normalise('Shown widely in Ireland and abroad.') === 'Shown widely in Ireland and abroad.');
check('F4 the limits and plain-text rule refuse: over 6,000 characters, a 300-character heading, control characters, a non-string',
  no(() => XA.normalise('x'.repeat(6001))) && no(() => XA.normalise('## ' + 'h'.repeat(300))) && no(() => XA.normalise('a\u0007b')) && no(() => XA.normalise({ a: 1 })));
const evil = '## <script>alert(1)</script>\n\n- <img src=x onerror=alert(2)> & "quotes" \'single\'\n\n<a href="javascript:x">link</a>';
const evilHtml = XA.toHtml(XA.normalise(evil));
check('F5 the artist\u2019s text is never HTML: tags, attributes and entities are shown as text', !/<script|<img|<a /.test(evilHtml) && /&lt;script&gt;/.test(evilHtml) && /&amp; &quot;quotes&quot; &#x27;single&#x27;/.test(evilHtml));

/* ---- the publisher's Python twin gives exactly the same result ---- */
const fixtures = [messy, evil, 'Just one paragraph.', '- a\n- b\nc\n- d', '#hashtag is a paragraph\n##\n-\n- real item', 'line one\n\n\n\nline two  with   spaces', '## Heading only'];
const pyOut = JSON.parse(py('import plotart_achievements as X; d=json.load(sys.stdin); print(json.dumps([[X.normalise(t), X.to_html(X.normalise(t)) if X.normalise(t) else None] for t in d]))', fixtures));
const jsOut = fixtures.map(t => [XA.normalise(t), XA.normalise(t) ? XA.toHtml(XA.normalise(t)) : null]);
check('F6 the Studio (JS) and the publisher (Python) store and render every fixture identically', JSON.stringify(pyOut) === JSON.stringify(jsOut), JSON.stringify(pyOut).slice(0, 300));
const pyCheck = JSON.parse(py('import plotart_achievements as X\nd=json.load(sys.stdin)\nout=[]\nfor t in d:\n    try:\n        X.check(t); out.append("ok")\n    except X.Refused: out.append("refused")\nprint(json.dumps(out))',
  [stored, messy, 'x'.repeat(6001), '## A\n- b', '<b>raw</b>']));
check('F7 the publisher accepts only the Studio\u2019s stored form (and escapes everything): unnormalised or over-long text is refused',
  JSON.stringify(pyCheck) === JSON.stringify(['ok', 'refused', 'refused', 'refused', 'ok']), JSON.stringify(pyCheck));

/* ---- the Studio before migration 0026 (production today): nothing changes ---- */
{
  const before = execFileSync('git', ['-C', HERE, 'show', 'dac259f5:worker/plotart-studio/schema.sql'], { encoding: 'utf8' });
  const { mf, url, db } = await start({ port: 8871, schemaSql: before });
  const call = mkcall(mf, url);
  await seedPublished(db, { id: 'azoe', slug: 'zoe-test', email: 'zoe@example.test', name: 'Zoe Test', works: 1, number: 2 });
  const me = await call('GET', '/api/me', 'zoe@example.test');
  const put = await call('PUT', '/api/me/profile', 'zoe@example.test', { achievements: '## Awards\n- One' });
  const bio = await call('PUT', '/api/me/profile', 'zoe@example.test', { practice: 'Painter' });
  check('S0 before migration 0026: the field is not offered, saving it is refused politely, and the rest of the profile saves as today',
    me.s === 200 && me.j.achievements_available === false && put.s === 503 && bio.s === 200);
  await mf.dispose();
}

/* ---- the Studio with migration 0026 ---- */
const { mf, url, db } = await start({ port: 8872 });
const call = mkcall(mf, url);
await seedPublished(db, { id: 'aava', slug: 'ava-test', email: 'ava@example.test', name: 'Ava Test', works: 1, number: 1 });
const me = await call('GET', '/api/me', 'ava@example.test');
check('S1 the Studio offers the optional section once the column exists', me.s === 200 && me.j.achievements_available === true && (me.j.artist.achievements ?? null) === null);
const art0 = await db.prepare("SELECT * FROM artists WHERE id='aava'").first();
const snap0 = L.snapshot(art0, [], []);
check('S2 an artist with no section has exactly the snapshot they had before (no achievements key at all)', !('achievements' in snap0.artist));
const put = await call('PUT', '/api/me/profile', 'ava@example.test', { achievements: messy });
const row = await db.prepare("SELECT achievements FROM artists WHERE id='aava'").first();
check('S3 the artist saves the section from their profile; it is stored in the clean form', put.s === 200 && row.achievements === stored);
const art1 = await db.prepare("SELECT * FROM artists WHERE id='aava'").first();
const ch = L.changes(snap0, L.snapshot(art1, [], []));
const xaCh = (Array.isArray(ch) ? ch : ch.items || []).find(c => c.field === 'achievements' || /Exhibitions/.test(JSON.stringify(c)));
check('S4 the change goes through the normal founder review (a "full" change, like the statement), labelled Exhibitions & Achievements',
  xaCh && xaCh.tier === 'full' && /Exhibitions & Achievements/.test(JSON.stringify(xaCh)), JSON.stringify(ch).slice(0, 300));
const bad = await call('PUT', '/api/me/profile', 'ava@example.test', { achievements: 'x'.repeat(6001) });
check('S5 an over-long section is refused with a plain message and the saved text stays as it was',
  bad.s === 400 && /6,000/.test(bad.j.error || bad.t) && (await db.prepare("SELECT achievements FROM artists WHERE id='aava'").first()).achievements === stored);
const clear = await call('PUT', '/api/me/profile', 'ava@example.test', { achievements: '   ' });
check('S6 clearing the text removes the section (stored as nothing, so it is hidden)', clear.s === 200 && (await db.prepare("SELECT achievements FROM artists WHERE id='aava'").first()).achievements === null);
await call('PUT', '/api/me/profile', 'ava@example.test', { achievements: stored });
const other = await call('PUT', '/api/me/profile', 'ava@example.test', { achievements: '## X' });
check('S7 only the signed-in artist\u2019s own profile is written (the route has no artist id to tamper with)', other.s === 200
  && (await db.prepare("SELECT COUNT(*) n FROM artists WHERE achievements IS NOT NULL").first()).n === 1);
await mf.dispose();

/* ---- the public profile ---- */
const pkg = JSON.parse(readFileSync(ROOT + 'plotart/artists/leah-hewson/gallery.json', 'utf8'));
const render = (p) => py('import plotart_gallery_pages as P; print(P.artist_body(json.load(sys.stdin)), end="")', p);
const without = render(pkg), withXa = render({ ...pkg, artist: { ...pkg.artist, achievements: stored } });
check('P1 hidden when empty: no section, no link (the profile is exactly as today)', !without.includes('exhibitions-achievements') && !without.includes('pa-ag-xa'));
check('P2 when present: its own section with its own heading, after About (separate from the statement and the biography)',
  withXa.includes('<h2 id="agXaH">Exhibitions &amp; Achievements</h2>') && withXa.indexOf('id="agAboutH"') < withXa.indexOf('id="agXaH"')
  && withXa.indexOf('pa-ag-statement') < withXa.indexOf('pa-ag-jump') && withXa.split('pa-ag-xa"').length === 2);
check('P3 easy to reach: a link under the statement jumps to the section', withXa.includes('<a href="#exhibitions-achievements" data-pa-track="artist_achievements_jump">') && withXa.includes('id="exhibitions-achievements"'));
check('P4 the artist\u2019s preview in the Studio shows exactly what will be published', withXa.includes(xaSection(stored).trim()) && withXa.includes(XA_JUMP));
const pyValid = py('import plotart_gallery as G\nd=json.load(sys.stdin)\nout=[]\nfor a in d:\n    try:\n        G.validate_export({"schema": G.SCHEMA, "artist": dict({"slug": "sample-artist", "display_name": "Sample Artist", "founding": False, "practice": "Painter", "medium": "painting", "county": None, "county_public": False, "statement": None, "bio": "A synthetic biography used only to check the export rules, long enough to be valid.", "website": None, "instagram": None, "portrait": None}, **{k: v for k, v in a.items() if k in ("location", "achievements")}), "works": []}); out.append("ok")\n    except Exception as e: out.append(type(e).__name__ + ":" + str(e)[:60])\nprint(json.dumps(out))',
  [{ ...pkg.artist, achievements: stored }, { ...pkg.artist, achievements: messy }]);
check('P5 the publisher\u2019s export check accepts the stored section and refuses anything else (the refusal names the section)',
  !/achievements|not a plotnua/.test(JSON.parse(pyValid)[0]) && /^Refused:.*achievements/.test(JSON.parse(pyValid)[1]), pyValid);

/* ---- migration 0026 ---- */
const M26 = HERE + 'migrations/0026_artist_achievements.sql';
const sha = execFileSync('sha256sum', [M26], { encoding: 'utf8' }).split(' ')[0];
let cls = ''; try { cls = execFileSync('python3', [ROOT + 'atlas-tools/release/studio/migration-check.py', M26, sha, 'artists', 'Adds one optional column, achievements, to artists (NULL for every existing artist); changes no row and no other table.'], { encoding: 'utf8' }); } catch (e) { cls = String(e.stdout || e); }
const block = s => s.slice(s.indexOf('\n', s.indexOf('-- @@DDL-BEGIN')) + 1, s.indexOf('-- @@DDL-END')).trim();
check('M1 migration 0026 adds one optional column to artists only; the check accepts it with artists declared and it waits for the founder (destructive class: an existing table)',
  /MIGRATION CHECK OK/.test(cls) && /MIGRATION CLASS: destructive/.test(cls) && readFileSync(HERE + 'schema.sql', 'utf8').includes(block(readFileSync(M26, 'utf8'))));
console.log(`  (migration 0026 SHA-256: ${sha})`);
const fail = results.filter(x => !x).length;
console.log(`\nEXHIBITIONS & ACHIEVEMENTS · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
