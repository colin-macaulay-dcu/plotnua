// PROVE · PlotArt Studio · consolidation of the artist-studio improvements (founder brief 18 Nov 2026, 16:58). Synthetic
// artists only; the real Worker runs locally (Miniflare/workerd) with its own D1 and R2. Nothing touches Cloudflare,
// sends email or publishes (the pipeline is simulated through its own endpoints).
//   B  biography paragraphs: typed with Enter, saved, previewed, submitted, approved, exported, rendered by the publisher
//   F  founder preview of an artist's unpublished draft: founder-only, read-only, labelled, the saved draft
//   A  agreement status on a submission in the Review Desk
//   M  simpler Studio: one Review and submit button, one row of tabs on a phone
//   node test/prove-consolidation.mjs [--shots DIR]
import { acceptAgreement } from './agree.mjs';
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';

const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 600)}]` : ''}`); };
const shot = async (pg, name, full = true) => { if (SHOTS) await pg.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: full }); };
console.log('PROVE · PlotArt Studio · consolidation');

const { mf, url, db } = await start({ port: 8860 });
const raw = (method, path, who, body) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' }; if (who) h['Cf-Access-Jwt-Assertion'] = token(who);
  return mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body), redirect: 'manual' });
};
const call = async (...a) => { const r = await raw(...a); const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t, h: r.headers }; };
const pipe = (method, path, body) => mf.dispatchFetch(url + path, { method, headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN, 'Content-Type': 'application/json' }, body: body && JSON.stringify(body) }).then(r => r.json());
const one = (sql, ...b) => db.prepare(sql).bind(...b).first();
const browser = await chromium.launch();
const open = async (email, w = 1280, h = 900) => {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(email, { exp: 3600 }) } });
  const pg = await ctx.newPage(); pg.errs = []; pg.on('pageerror', e => pg.errs.push(String(e))); return pg;
};
const savedAll = pg => pg.waitForFunction(() => /^All changes saved/.test(document.querySelector('#sb-state')?.textContent || ''), null, { timeout: 10000 });

const EM = 'rua@example.test', OTHER = 'other@example.test';
const bucket = await mf.getR2Bucket('IMAGES');
await seedPublished(db, { id: 'arua', slug: 'rua-test', email: EM, name: 'Rua Test', licence: null, bucket });
await seedPublished(db, { id: 'aoth', slug: 'other-test', email: OTHER, name: 'Other Test', licence: null });
const ag = await acceptAgreement(mf, url, EM, { legal_name: 'Rua Test' });
await acceptAgreement(mf, url, OTHER);

/* ---------------------------------------------------------------- B: biography paragraphs */
const pg = await open(EM);
await pg.goto(url + '/#/profile'); await pg.waitForSelector('#f-bio');
await pg.fill('#f-bio', '');
await pg.click('#f-bio');
await pg.keyboard.type('Rua paints the Atlantic coast in oil, working outdoors in all weathers.');
await pg.keyboard.press('Enter');
await pg.keyboard.type('Her studio is a converted boathouse in Connemara, where the larger canvases are finished over the winter.');
await pg.keyboard.press('Enter'); await pg.keyboard.press('Enter');
await pg.keyboard.type('She has shown in Galway and Dublin.');
await savedAll(pg);
const bio = (await one('SELECT bio FROM artists WHERE id=?', 'arua')).bio;
check('B1 the biography editor keeps paragraphs: Enter (once or twice) is saved as a line break', (bio.match(/\n/g) || []).length === 3 && bio.startsWith('Rua paints'), JSON.stringify(bio));
check('B2 the hint under the biography says how to start a new paragraph', /Press Enter at the end of a paragraph/.test(await pg.textContent('.st-f:has(#f-bio) small').catch(() => '')));
await shot(pg, 'cons-01-bio-editor');
const pv = await pg.context().newPage(); await pv.goto(url + '/preview/');
const pParas = await pv.$$eval('.pa-ag-bio > p:not(.pa-ag-links)', ps => ps.map(p => p.textContent));
check('B3 the private preview shows the biography as three paragraphs, as typed', pParas.length === 3 && pParas[2] === 'She has shown in Galway and Dublin.', JSON.stringify(pParas));
await shot(pv, 'cons-02-bio-preview'); await pv.close();
await pg.goto(url + '/#/submit'); await pg.waitForSelector('#go');
const brk = await pg.evaluate(() => [PAChanges.textDiff('One. Two.', 'One.\nTwo.'), PAChanges.textDiff('One.\nTwo.', 'One. Two.'), PAChanges.textDiff('in oil, working', 'in oil,\nworking'), PAChanges.textDiff('One.\nTwo.', 'One.\n\nTwo.')]);
check('B4 Review and submit names a paragraph added or removed (a layout-only change was invisible); a break the gallery joins, or a re-typed break, is not flagged',
  /st-brk">new paragraph/.test(brk[0]) && /st-brk">paragraph break/.test(brk[1]) && !/st-brk|<ins|<del/.test(brk[2]) && !/st-brk|<ins|<del/.test(brk[3]), JSON.stringify(brk));
await shot(pg, 'cons-03-submit');
await pg.click('#go'); await pg.waitForFunction(() => document.querySelector('.st-status h2')?.textContent === 'Submitted for review', null, { timeout: 8000 });

/* ---------------------------------------------------------------- A: agreement status in the Review Desk */
const sid = (await call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(x => x.artist_id === 'arua').id;
const det = (await call('GET', `/api/admin/submissions/${sid}`, FOUNDER)).j;
check('A1 the submission carries the artist\'s real agreement status (accepted, with the time), not the pre-agreement licence column',
  det.agreement?.accepted === true && !!det.agreement.accepted_at && det.artist.licence_version === null, JSON.stringify({ ag: det.agreement, licence: det.artist?.licence_version, accept: ag.s }));
const fd = await open(FOUNDER);
await fd.goto(url + `/admin#/s/${sid}`); await fd.waitForTimeout(400);
let deskTxt = await fd.textContent('body');
if (!/agreement accepted|licence/.test(deskTxt)) { await fd.goto(url + '/admin'); await fd.waitForTimeout(500); const a = await fd.$(`a[href*="${sid}"]`); if (a) { await a.click(); await fd.waitForTimeout(600); } deskTxt = await fd.textContent('body'); }
check('A2 the Review Desk says "agreement accepted" for an artist who accepted the current agreement (it said "licence not accepted")',
  /agreement accepted/.test(deskTxt) && !/licence not accepted/.test(deskTxt), deskTxt.match(/Submitted[^\n]{0,200}/)?.[0]);
await shot(fd, 'cons-04-review-desk-submission', false);
const preRows = { s: (await one('SELECT COUNT(*) n FROM gallery_agreement_acceptances WHERE artist_id=?', 'arua').catch(() => ({ n: -1 }))).n, a: (await one('SELECT COUNT(*) n FROM agreement_acceptances WHERE artist_id=?', 'arua')).n };

/* approve and publish (simulated pipeline), then the publisher's renderer on the exported package */
await call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve' });
let q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === 'arua' && x.status === 'awaiting_founder');
if (q) await call('POST', `/api/admin/queue/${q.id}/publish`, FOUNDER, {});
q = (await call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === 'arua' && x.version > 1);
const ex = await pipe('POST', `/api/pipeline/export/${q.id}`);
const pkgBio = JSON.stringify(ex).match(/"bio":"((?:[^"\\]|\\.)*)"/)?.[1];
const pyParas = execFileSync('python3', ['-c', `import sys, json; sys.path.insert(0, "../../atlas-tools"); import plotart_gallery_pages as P
b = json.loads(sys.stdin.read()); print(json.dumps(P.paragraphs(b)))`], { input: JSON.stringify(JSON.parse(`"${pkgBio}"`)) }).toString();
check('B5 after approval the exported biography keeps its line breaks, and the publisher renders the same three paragraphs',
  JSON.parse(pyParas).length === 3 && JSON.parse(pyParas)[0] === pParas[0], pyParas);
await pipe('POST', `/api/pipeline/result/${q.id}`, { status: 'published', detail: 'test' });

/* ---------------------------------------------------------------- F: founder preview of the unpublished draft */
await pg.goto(url + '/#/profile'); await pg.reload(); await pg.waitForSelector('#f-statement');
await pg.fill('#f-statement', 'Weather, salt and light: a draft line not yet submitted.'); await savedAll(pg);
const counts = async () => JSON.stringify(await Promise.all(['submissions', 'versions', 'publish_queue'].map(t => one(`SELECT COUNT(*) n FROM ${t} WHERE artist_id='arua'`))));
const before = await counts(), bioBefore = (await one('SELECT bio, statement, updated_at FROM artists WHERE id=?', 'arua'));
const P = '/admin/preview/d-arua/index.html';
const f1 = await call('GET', P, FOUNDER);
check('F1 the founder opens the artist\'s saved draft, including a change not yet submitted, clearly labelled unpublished and read-only',
  f1.s === 200 && /draft line not yet submitted/.test(f1.t) && /Unpublished draft/.test(f1.t) && /not live/.test(f1.t) && /read-only, founder only/.test(f1.t), f1.t.slice(0, 300));
check('F2 the draft preview is never cached or indexed', f1.h.get('cache-control') === 'no-store' && /noindex/.test(f1.t), f1.h.get('cache-control'));
const f3a = await call('GET', P, EM), f3b = await call('GET', P, OTHER), f3c = await call('GET', P, null);
check('F3 the artist, another artist and a signed-out visitor cannot open the founder draft preview', ![f3a.s, f3b.s, f3c.s].includes(200) && !/draft line not yet submitted/.test(f3a.t + f3b.t + f3c.t), [f3a.s, f3b.s, f3c.s].join(','));
const img = (await one("SELECT id FROM images WHERE artist_id='arua' AND role='main'")).id;
const f4 = await call('GET', `/admin/preview/d-arua/img/${img}`, FOUNDER), f4b = await call('GET', `/admin/preview/d-arua/img/${img}`, OTHER), f4c = await call('GET', `/admin/preview/d-aoth/img/${img}`, FOUNDER);
check('F4 photographs in the draft preview are served to the founder only, and only for that artist', f4.s === 200 && f4b.s !== 200 && f4c.s === 404, [f4.s, f4b.s, f4c.s].join(','));
const f5 = await call('POST', P, FOUNDER, {});
const after = await counts(), bioAfter = await one('SELECT bio, statement, updated_at FROM artists WHERE id=?', 'arua');
check('F5 read-only: a POST is refused, and opening the preview changes no record (no submission, version or publication)',
  f5.s === 404 && before === after && JSON.stringify(bioBefore) === JSON.stringify(bioAfter), JSON.stringify([f5.s, before, after]));
check('F6 the public gallery path is separate: the draft preview lives only under /admin', !/\/plotart\/artists\//.test(P) && (await call('GET', '/preview/', FOUNDER)).s !== 200);
await fd.goto(url + '/admin'); await fd.waitForSelector(`a[href="/admin/preview/d-arua/index.html"]`, { timeout: 8000 }).catch(() => null);
check('F7 the Review Desk lists "Preview draft" for each artist', !!(await fd.$(`a[href="/admin/preview/d-arua/index.html"]`)));
const fp = await open(FOUNDER); await fp.goto(url + P); await shot(fp, 'cons-05-founder-draft-preview', false); await fp.close();
const aud = await one("SELECT COUNT(*) n FROM audit WHERE action='draft_preview_viewed' AND artist_id='arua'").catch(() => null);
check('F8 each founder draft preview is recorded in the audit log', aud && aud.n >= 1, JSON.stringify(aud));
const postRows = { s: (await one('SELECT COUNT(*) n FROM gallery_agreement_acceptances WHERE artist_id=?', 'arua').catch(() => ({ n: -1 }))).n, a: (await one('SELECT COUNT(*) n FROM agreement_acceptances WHERE artist_id=?', 'arua')).n };
check('A3 nothing here touches agreement records', JSON.stringify(preRows) === JSON.stringify(postRows), JSON.stringify([preRows, postRows]));

/* ---------------------------------------------------------------- M: simpler Studio */
for (const [w, h, tag] of [[1280, 900, 'desktop'], [390, 844, 'mobile']]) {
  const p = await open(EM, w, h);
  await p.goto(url + '/#/'); await p.waitForSelector('.st-status h2');
  const subs = await p.$$eval('main a, #app a', as => as.filter(a => /^(Review and submit|Submit again)/.test(a.textContent.trim())).length);
  check(`M1 ${tag}: the gallery page has one Review and submit button`, subs === 1, subs);
  if (tag === 'mobile') {
    const tops = await p.$$eval('.st-tabs a', as => [...new Set(as.map(a => Math.round(a.getBoundingClientRect().top)))]);
    check('M2 phone: the Studio tabs take one row (they took two)', tops.length === 1, JSON.stringify(tops));
    await p.goto(url + '/#/works'); await p.waitForSelector('.st-work');
    const ok = await p.$eval('.st-work', li => { const t = li.querySelector('.st-thumb').getBoundingClientRect(), c = li.querySelector(':scope > .st-row:last-child').getBoundingClientRect(); return c.left < t.right && c.top > t.bottom && c.width > li.getBoundingClientRect().width * 0.8; });
    check('M3 phone: order and Remove buttons sit in their own row, not stacked under the photograph', ok);
    await shot(p, 'cons-07-works-mobile');
    await p.goto(url + '/#/'); await p.waitForSelector('.st-status h2');
  }
  await shot(p, `cons-06-gallery-${tag}`);
  check(`M4 ${tag}: no script errors`, !p.errs.length, p.errs.join(' | '));
  await p.close();
}

/* ---------------------------------------------------------------- S: submission never silent; founder sees the state */
const CA = 'cara@example.test';
const cid = (await call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Cara Test', email: CA, founding: true })).j.id;
await acceptAgreement(mf, url, CA);
await call('PUT', '/api/profile', CA, { practice: 'Painter' });
const refused = await call('POST', '/api/submit', CA, {});
const ra = await one("SELECT COUNT(*) n FROM audit WHERE action='submit_refused' AND artist_id=?", cid);
check('S1 a submission that cannot go through is refused with the reasons, and the attempt is recorded for the founder', refused.s >= 400 && ra.n === 1 && !(await one('SELECT id FROM submissions WHERE artist_id=?', cid)), JSON.stringify([refused.s, refused.j, ra]));
const cp = await open(CA);
await cp.goto(url + '/#/submit'); await cp.waitForSelector('#go');
if (await cp.isEnabled('#go')) { await cp.click('#go'); await cp.waitForFunction(() => /Not submitted/.test(document.querySelector('#serr')?.textContent || ''), null, { timeout: 8000 }).catch(() => {}); }
const serr = await cp.textContent('#serr').catch(() => ''), goOff = !(await cp.isEnabled('#go'));
check('S2 the artist is never left guessing: either Submit is unavailable with what is missing, or a failed attempt says "Not submitted" and what is still needed',
  goOff || /Not submitted\. Nothing has been sent to PlotArt yet\. Still needed:/.test(serr), JSON.stringify([goOff, serr]));
await cp.close();
const od = await open(FOUNDER); await od.goto(url + '/admin'); await od.waitForTimeout(900);
const otxt = await od.textContent('body');
check('S3 the founder\'s artist list says "Submitted for review" / "Published" / "Setting up" in plain words', /Published/.test(otxt) && /Setting up/.test(otxt), otxt.match(/Artists[\s\S]{0,300}/)?.[0]);
await od.close();

await browser.close(); await mf.dispose();
const passed = results.filter(Boolean).length;
console.log(`PLOTART CONSOLIDATION · ${results.length} checks, ${passed} passed, ${results.length - passed} failed`);
process.exit(passed === results.length ? 0 : 1);
