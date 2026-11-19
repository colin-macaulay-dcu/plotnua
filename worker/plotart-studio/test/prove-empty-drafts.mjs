// PROVE · PlotArt Studio · empty artwork drafts (17 Nov 2026 investigation: Olivia Jones, four "Untitled artwork" entries).
// Synthetic artists only; the Worker runs locally (Miniflare/workerd) with a local D1. Nothing here touches Cloudflare.
//   node test/prove-empty-drafts.mjs [--shots DIR]
// E1 reproduces the reported state with the Studio as released (main): four records made by "Add an artwork" and never
// saved to block a submission, each reported as missing title, medium, size, the AI question and the main photograph.
// The rest proves the correction: empty drafts never block or reach a submission or publication, "Add an artwork" reuses
// an empty draft instead of making another, a refused photo leaves no new record, real drafts are still checked in full,
// published works and their snapshots are untouched, and nothing is deleted unless the artist discards it.
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import * as L from '../src/lib.js';

const HERE = new URL('../', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
console.log('PROVE · PlotArt Studio · empty artwork drafts');

// the library as released BEFORE the correction (pinned to the parent of 38710a6, which made the correction; 19 Nov 2026:
// origin/main now contains the correction, so reading main no longer reproduces the reported state), loaded side by side, for the "before" reproduction and the snapshot comparison
const oldDir = mkdtempSync(tmpdir() + '/pa-oldlib-');
writeFileSync(oldDir + '/lib.mjs', execFileSync('git', ['show', '38710a6^:worker/plotart-studio/src/lib.js'], { cwd: HERE }));
const OLD = await import(oldDir + '/lib.mjs');

const { mf, url, db } = await start({ port: 8811 });
const IMAGES = await mf.getR2Bucket('IMAGES', 'studio');
const call = async (method, path, email, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' };
  if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ }
  return { s: r.status, j, t };
};
const T = '2026-11-17T19:00:00.000Z';
const A = 'olivia@example.test', B = 'bea@example.test';
// an artist whose first version was approved (7 complete works), like the reported case, and a second, live artist
await seedPublished(db, { id: 'aoli', slug: 'oli-test', email: A, name: 'Oli Test', works: 7, number: 5, bucket: IMAGES });
await seedPublished(db, { id: 'abea', slug: 'bea-test', email: B, name: 'Bea Test', works: 2, number: 6, bucket: IMAGES });
const load = async id => ({ artist: await db.prepare('SELECT * FROM artists WHERE id=?').bind(id).first(),
  works: (await db.prepare('SELECT * FROM artworks WHERE artist_id=? ORDER BY ord').bind(id).all()).results,
  images: (await db.prepare('SELECT * FROM images WHERE artist_id=? AND deleted_at IS NULL ORDER BY ord').bind(id).all()).results });
const beaBefore = await load('abea'), beaSnapOld = OLD.snapshot(beaBefore.artist, beaBefore.works, beaBefore.images);

// four records exactly as "Add an artwork" makes them (the released route inserts only these columns)
for (const n of [1, 2, 3, 4]) await db.prepare('INSERT INTO artworks (id, artist_id, slug, ord, created_at, updated_at) VALUES (?,?,?,?,?,?)')
  .bind(`wempty${n}`, 'aoli', `untitled-e${n}`, 100 + n, T, T).run();
const d = await load('aoli');

// E1 the reported state, reproduced with the released library
const oldList = OLD.checklist(OLD.snapshot(d.artist, d.works, d.images), { founding: true, firstPublication: false, licenceOk: true, imageBlocks: new Set() });
const oldWork = oldList.filter(i => i.area === 'work');
const oldChanges = OLD.changes(OLD.snapshot(d.artist, d.works, d.images), OLD.snapshot(d.artist, d.works, d.images));
check('E1 as released: four records that were never saved to block the gallery, each "Untitled artwork" missing title, medium, size, the AI question and the main photograph (the reported state)',
  oldWork.length === 4 && oldWork.every(i => !i.title && ['title', 'medium', 'size', 'ai', 'main_photo'].every(c => i.needs.includes(c))), JSON.stringify(oldWork.map(i => i.needs)));

// E2 with the correction: the same records hold up nothing, appear in no submission, and are still there
const me = await call('GET', '/api/me', A);
const works = (await call('GET', '/api/artworks', A)).j.works;
const rows = (await db.prepare("SELECT COUNT(*) n FROM artworks WHERE artist_id='aoli' AND id LIKE 'wempty%'").first()).n;
check('E2 corrected: the four empty drafts no longer block or join a submission (no checklist item, no "New artwork" change), and all four records are kept',
  me.s === 200 && !me.j.status.checklist.some(i => i.area === 'work') && !me.j.status.changes.some(c => /New artwork/.test(c.what)) &&
  works.filter(w => w.empty_draft).length === 4 && rows === 4, JSON.stringify(me.j.status && { checklist: me.j.status.checklist, changes: me.j.status.changes }));

// E3 "Add an artwork" reuses an empty draft
const add1 = await call('POST', '/api/artworks', A), add2 = await call('POST', '/api/artworks', A);
const count = (await db.prepare("SELECT COUNT(*) n FROM artworks WHERE artist_id='aoli'").first()).n;
check('E3 "Add an artwork" reopens an existing empty draft instead of making another (repeated taps add no records)',
  add1.j.reused === true && add2.j.reused === true && add1.j.id === add2.j.id && /^wempty/.test(add1.j.id) && count === 11, `${JSON.stringify(add1.j)} ${count}`);

// E4 a draft with anything saved is a real draft again, checked in full (nothing is weakened)
await call('PUT', `/api/artworks/wempty1`, A, { title: 'Half done' });
const me2 = (await call('GET', '/api/me', A)).j.status;
const half = me2.checklist.find(i => i.work_id === 'wempty1');
const sub = await call('POST', '/api/submit', A, {});
check('E4 once anything is saved (a title) the work is checked in full again: medium, size, AI and photograph still required, and submission is refused',
  half && ['medium', 'size', 'ai', 'main_photo'].every(c => half.needs.includes(c)) && me2.changes.some(c => /New artwork: Half done/.test(c.what)) && sub.s === 422, JSON.stringify({ half, sub: sub.j }));

// E5 an empty draft is never published: the submission and the version carry only works with content
await call('DELETE', '/api/artworks/wempty1', A);
await db.prepare('INSERT INTO artworks (id, artist_id, slug, ord, created_at, updated_at) VALUES (?,?,?,?,?,?)').bind('wempty1', 'aoli', 'untitled-e1', 101, T, T).run();
await call('PUT', '/api/artworks/waoli1', A, { description: 'A light change to a published work.' });
const sub2 = await call('POST', '/api/submit', A, {});
const subSnap = sub2.j.id ? JSON.parse((await db.prepare('SELECT snapshot FROM submissions WHERE id=?').bind(sub2.j.id).first()).snapshot) : null;
check('E5 a submission is accepted with empty drafts present, and its snapshot carries only the seven real works (no empty draft can reach publication)',
  sub2.s === 200 && subSnap && subSnap.works.length === 7 && !subSnap.works.some(w => /^wempty/.test(w.id)), JSON.stringify(sub2.j));

// E6 published works and other artists are untouched: the snapshot of an artist without empty drafts is byte-for-byte the released one
const beaAfter = await load('abea');
check('E6 an artist without empty drafts gets exactly the snapshot the released Studio made (byte for byte); published works are never treated as empty',
  JSON.stringify(L.snapshot(beaAfter.artist, beaAfter.works, beaAfter.images)) === JSON.stringify(beaSnapOld) &&
  d.works.filter(w => !/^wempty/.test(w.id)).every(w => !L.isEmptyDraft(w, d.images)));
const sample = { title: null, year: null, medium: null, materials: null, h_cm: null, w_cm: null, d_cm: null, price_eur: null, price_on_request: 0, description: null, ai_involvement: null, ai_note: null, id: 'wx' };
check('E7 any one saved detail (title, year, medium, materials, any size, price, price on request, description, AI answer or note) or a photograph makes a draft real',
  L.isEmptyDraft(sample, []) && ['title', 'year', 'medium', 'materials', 'h_cm', 'w_cm', 'd_cm', 'price_eur', 'price_on_request', 'description', 'ai_involvement', 'ai_note']
    .every(k => !L.isEmptyDraft({ ...sample, [k]: k === 'price_on_request' ? 1 : k.endsWith('_cm') || k === 'year' || k === 'price_eur' ? 1 : 'x' }, [])) &&
  !L.isEmptyDraft(sample, [{ artwork_id: 'wx', deleted_at: null }]) && L.isEmptyDraft(sample, [{ artwork_id: 'wx', deleted_at: T }]));

// E8 the founder sees the same: the Review Desk checklist for the artist lists no empty drafts
const fc = await call('GET', '/api/admin/artists/aoli/checklist', FOUNDER);
check('E8 the founder\'s Review Desk checklist for the artist no longer lists the empty drafts', fc.s === 200 && !JSON.stringify(fc.j).includes('wempty'), fc.t.slice(0, 300));

// E9 in the browser: a refused photo says plainly it was not uploaded and leaves no new record; "Add an artwork" again
// reopens the same draft; the draft says nothing is saved yet and can be discarded in one tap
{
  const { chromium } = await import('playwright');
  const br = await chromium.launch();
  const ctx = await br.newContext({ viewport: { width: 1280, height: 900 }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(B, { exp: 3600 }) } });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  const n0 = (await db.prepare("SELECT COUNT(*) n FROM artworks WHERE artist_id='abea'").first()).n;
  // a double tap on "Add an artwork" (two clicks 50 ms apart) makes one record, not two
  await pg.goto(url + '/#/works'); await pg.waitForSelector('[data-act=add]');
  await pg.evaluate(() => { const b = document.querySelector('[data-act=add]'); b.click(); setTimeout(() => b.click(), 50); });
  await pg.waitForSelector('#mdrop input', { state: 'attached' });
  const nDouble = (await db.prepare("SELECT COUNT(*) n FROM artworks WHERE artist_id='abea'").first()).n;
  const viewsFirst = await pg.textContent('.st-views-first').catch(() => '');
  const vaddGone = !(await pg.$('#vadd'));
  await pg.click('[data-act=discard]'); for (let i = 0; i < 50 && !/#\/works$/.test(pg.url()); i++) await pg.waitForTimeout(100);
  await pg.goto(url + '/#/works'); await pg.waitForSelector('[data-act=add]');
  await pg.click('[data-act=add]'); await pg.waitForSelector('#mdrop input', { state: 'attached' });
  const note1 = await pg.textContent('#draft-note').catch(() => '');
  // a small screenshot-sized PNG (600 x 400), refused in the browser before upload
  const png = await pg.evaluate(async () => { const c = document.createElement('canvas'); c.width = 600; c.height = 400; c.getContext('2d').fillRect(0, 0, 600, 400);
    const b = await new Promise(r => c.toBlob(r, 'image/png')); return Array.from(new Uint8Array(await b.arrayBuffer())); });
  await pg.setInputFiles('#mdrop input', { name: 'small.png', mimeType: 'image/png', buffer: Buffer.from(png) });
  await pg.waitForSelector('.st-upfail');
  const refused = await pg.textContent('#mdrop');
  await pg.goto(url + '/#/works'); await pg.waitForSelector('[data-act=add]');
  const chip = await pg.textContent('.st-works');
  await pg.click('[data-act=add]'); await pg.waitForSelector('#draft-note');
  const n1 = (await db.prepare("SELECT COUNT(*) n FROM artworks WHERE artist_id='abea'").first()).n;
  const shots = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
  if (shots) await pg.screenshot({ path: shots + '/studio-empty-draft.png', fullPage: true });
  await pg.click('[data-act=discard]');
  for (let i = 0; i < 50 && !/#\/works$/.test(pg.url()); i++) await pg.waitForTimeout(100);
  const n2 = (await db.prepare("SELECT COUNT(*) n FROM artworks WHERE artist_id='abea'").first()).n;
  await br.close();
  check('E9 in the Studio: a refused photo says "This photo was not uploaded" with the reason; the work list labels the empty draft; "Add an artwork" again reopens it (one record, not two); one tap discards it',
    /Nothing is saved for this artwork yet/.test(note1) && /This photo was not uploaded\./.test(refused) && /at least 2,000 px/.test(refused) &&
    /Empty draft · nothing saved yet/.test(chip) && n1 === n0 + 1 && n2 === n0 && !errs.length, JSON.stringify({ note1, refused, n0, n1, n2, errs }));
  check('E11 a double tap on "Add an artwork" makes one record; on an artwork with no main photograph the "More views" upload asks for the main photograph first',
    nDouble === n0 + 1 && /Add the main photograph above first/.test(viewsFirst) && vaddGone, JSON.stringify({ n0, nDouble, viewsFirst, vaddGone }));
}

// E10 the A12 correction's export field: every export carries when the founder FIRST approved the gallery (version 1), and
// it stays the same when a later version is approved and when the licence is accepted again
{
  const { PIPELINE_TOKEN } = await import('./local.mjs');
  const exp = async (qid, ver, kind = 'reviewed') => {
    await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)").bind(qid, 'abea', ver, kind, 'ready', T, T).run();
    const r = await mf.dispatchFetch(url + '/api/pipeline/export/' + qid, { method: 'POST', headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } });
    return (await r.json()).gallery;
  };
  const v1 = (await db.prepare("SELECT created_at FROM versions WHERE artist_id='abea' AND version=1").first()).created_at;
  const g1 = await exp('qbea1x', 1);
  await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) SELECT artist_id, 2, snapshot, 'test', '2026-12-24T09:30:00.000Z' FROM versions WHERE artist_id='abea' AND version=1").run();
  await db.prepare("UPDATE artists SET licence_accepted_at='2026-12-25T10:00:00.000Z' WHERE id='abea'").run();
  const g2 = await exp('qbea2x', 2);
  check('E10 every export carries first_approved_at = the gallery\'s first approval (version 1); a later approval and a licence re-acceptance change approved_at and licence_accepted_at but never it',
    g1 && g2 && g1.publication.first_approved_at === v1 && g2.publication.first_approved_at === v1 && g2.publication.approved_at === '2026-12-24T09:30:00.000Z' &&
    g2.publication.licence_accepted_at !== g1.publication.licence_accepted_at, JSON.stringify({ v1, p1: g1 && g1.publication, p2: g2 && g2.publication }));
}

console.log(`\nPLOTART EMPTY DRAFTS (Studio) · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
await mf.dispose();
process.exit(results.every(Boolean) ? 0 : 1);
