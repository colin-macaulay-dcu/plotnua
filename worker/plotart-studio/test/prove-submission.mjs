// PROVE · PlotArt Studio · submission checklist (PLOTART-STUDIO-SUBMISSION-002, 5 Nov 2026).
// Synthetic artists only; the real Worker runs locally (Miniflare/workerd) with a local D1 and R2, and a real browser
// (Playwright Chromium) checks navigation, focus, keyboard use and the phone layout. Nothing here touches Cloudflare.
//   node test/prove-submission.mjs [--shots DIR]
// Numbered checks T1..T18 follow the brief's test list; X-checks are extra.
import { start, token, FOUNDER } from './local.mjs';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import * as L from '../src/lib.js';

const req = createRequire(import.meta.url);
let chromium; try { ({ chromium } = req('playwright')); } catch { try { ({ chromium } = createRequire('/usr/lib/node_modules/')('playwright')); } catch { ({ chromium } = createRequire('/opt/npm-tools/node_modules/')('playwright')); } }
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };

const TMP = mkdtempSync(join(tmpdir(), 'pa-sub-'));
execFileSync('python3', ['-c', `
import sys, random
from PIL import Image, ImageDraw
for i in range(16):
    r = random.Random(700 + i); w, h = (1000, 1200) if i == 15 else (2200, 3000)
    im = Image.new("RGB", (w, h), tuple(r.randrange(40, 200) for _ in range(3))); d = ImageDraw.Draw(im)
    for _ in range(24):
        x, y = r.randrange(w), r.randrange(h); d.rectangle((x, y, x + r.randrange(w // 6, w // 2), y + r.randrange(h // 6, h // 2)), outline=tuple(r.randrange(256) for _ in range(3)), width=18)
    im.save(f"{sys.argv[1]}/{'portrait' if i == 15 else 'w%d' % i}.jpg", "JPEG", quality=88)
`, TMP]);

const { mf, url, db } = await start({ port: 8815 });
const call = async (method, path, who, body, raw) => {
  const h = { 'X-Studio': '1' }; if (who) h['Cf-Access-Jwt-Assertion'] = token(who);
  if (!raw) h['Content-Type'] = 'application/json';
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: raw || (body === undefined ? undefined : JSON.stringify(body)) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
};
const img = n => readFileSync(join(TMP, `${n}.jpg`));
const mk = async (name, email) => (await call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, founding: true })).j.id;
const me = async e => (await call('GET', '/api/me', e)).j.status;
const PROFILE = { practice: 'Painter', medium: 'painting', county: 'Dublin', bio: 'A synthetic test painter used only for these checks. Oil and acrylic on canvas.' };
const addWork = async (e, i, details = {}) => {
  const id = (await call('POST', '/api/artworks', e)).j.id;
  await call('PUT', `/api/artworks/${id}`, e, { title: `Night Study ${i}`, year: 2026, medium: 'Oil on canvas', h_cm: 100, w_cm: 70, price_eur: 1200, ai_involvement: 'none' });
  const up = await call('PUT', `/api/artworks/${id}/images?role=main`, e, undefined, img('w' + (i % 15)));
  if (Object.keys(details).length) await call('PATCH', `/api/images/${up.j.id}`, e, details);
  return { id, image: up.j.id };
};

console.log('PROVE · PlotArt Studio · submission checklist');

// T1 incomplete profile
const P = 'pia@example.test'; const PID = await mk('Pia Synthetic', P);
let s = await me(P);
check('T1 incomplete profile: biography, main medium and "add your first artwork" listed, each tagged with where it belongs',
  s.checklist.length === 3 && s.checklist.map(i => `${i.area}:${i.field}`).join() === 'profile:bio,profile:medium,works:add' && s.problems.join('|') === s.checklist.map(i => i.text).join('|'), JSON.stringify(s.checklist));

// Leah-like artist: complete profile, portrait without description, 11 works with photographs but no photo details
const A = 'lena@example.test'; const AID = await mk('Lena Synthetic', A);
await call('PUT', '/api/me/profile', A, PROFILE);
const por = await call('PUT', '/api/me/portrait', A, undefined, img('portrait'));
const W = []; for (let i = 1; i <= 11; i++) W.push(await addWork(A, i));
s = await me(A);
const pItem = s.checklist.find(i => i.field === 'portrait_alt');
check('T2 missing portrait description: listed under Profile, pointing at the portrait', pItem && pItem.area === 'profile' && pItem.image_id === por.j.id && pItem.text === 'Describe your portrait photograph (for people using screen readers)');
const w1 = s.checklist.find(i => i.work_id === W[0].id);
check('T3 missing photo description: the artwork is listed with "photograph description" and the photograph it concerns',
  w1 && w1.area === 'work' && w1.needs.includes('photo_alt') && w1.image_id === W[0].image && w1.field === 'photo_alt' && w1.title === 'Night Study 1');
check('T4 missing photographer confirmation: listed for the same artwork', w1.needs.includes('photographer') && w1.text === 'Night Study 1 needs a description of each photograph, who took each photograph');
check('T7 multiple incomplete artworks: one item per artwork (11) plus the portrait = 12, exactly as before',
  s.checklist.length === 12 && s.checklist.filter(i => i.area === 'work').length === 11 && s.problems.length === 12);

// T5 third-party photographer without a name, then with one
await call('PATCH', `/api/images/${W[0].image}`, A, { alt: 'Synthetic painting with coloured rectangles', photographer: 'other_with_permission' });
s = await me(A); const w1b = s.checklist.find(i => i.work_id === W[0].id);
check('T5 "Another photographer" without a name: the photographer’s name is required (listed, pointing at that field)',
  w1b && w1b.needs.join() === 'photo_credit' && w1b.field === 'photo_credit' && /the photographer’s name$/.test(w1b.text));
await call('PATCH', `/api/images/${W[0].image}`, A, { photo_credit: 'Sam Synthetic' });
s = await me(A);
check('T6 complete artwork: once description, photographer and name are given, the artwork leaves the checklist', !s.checklist.some(i => i.work_id === W[0].id) && s.checklist.length === 11);

// browser
const browser = await chromium.launch();
const page = async (who, vp = { width: 1280, height: 900 }) => {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: SHOTS ? 2 : 1, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(who) } });
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.errs = errs; p.ctx = ctx; return p;
};
const shot = async (p, f, full = true) => { if (!SHOTS) return; if (full) { await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(150); } await p.screenshot({ path: join(SHOTS, f), fullPage: full }); };
const go = async (p, h) => { await p.goto(url + '/' + h, { waitUntil: 'load' }); await p.waitForTimeout(500); };

let p = await page(A);
await go(p, '#/submit');
let why = await p.locator('#why').innerText(), dis = await p.locator('#go').isDisabled();
check('T8a submit page: button disabled and the explanation beside it gives the live count ("11 details still need your attention…")',
  dis && /^11 details still need your attention before you can submit your gallery\./.test(why) && (await p.locator('#go').getAttribute('aria-describedby')) === 'why', why);
await go(p, '#/');
const home = await p.locator('section[aria-labelledby=ck-h]').innerText();
check('T3b Studio home: grouped checklist (Profile / Artworks), "10 artworks need photograph details", no truncation ("and N more" gone)',
  /Your gallery checklist/.test(home) && /11 details to complete/i.test(home) && /PROFILE/i.test(home) && /10 artworks need photograph details/.test(home) && !/and \d+ more/.test(home), home);
await shot(p, '01-home-checklist-collapsed-1280.png');

// T9 navigation: open the artwork group, follow an artwork, the photo description is focused
await p.locator('.st-ck-d > summary').click();
await shot(p, '02-home-checklist-expanded-1280.png');
await p.locator(`a.st-ck-link[href^="#/work/${W[1].id}"]`).click(); await p.waitForTimeout(700);
let focus = await p.evaluate(() => ({ id: document.activeElement.id, hash: location.hash, marked: !!document.querySelector('.st-fix'), needs: document.querySelector('#wneeds').innerText }));
check('T9a checklist → artwork: opens that artwork and focuses + highlights "Describe the photo"', focus.hash.startsWith(`#/work/${W[1].id}?fix=photo_alt`) && focus.id === `alt-${W[1].image}` && focus.marked, JSON.stringify(focus));
check('T9b the artwork page says what is still needed ("photograph description, who took the photograph")', /Still needed to submit: photograph description, who took the photograph/.test(focus.needs), focus.needs);
await shot(p, '03-artwork-focused-photo-description-1280.png', false);
// fill it in through the page: the "still needed" line updates as each field saves
await p.fill(`#alt-${W[1].image}`, 'Synthetic painting, red and blue rectangles'); await p.keyboard.press('Tab');
await p.waitForFunction(() => !/photograph description/.test(document.querySelector('#wneeds').innerText), null, { timeout: 8000 }).catch(() => {});
const after1 = await p.locator('#wneeds').innerText();
await p.check(`[name="photographer-${W[1].image}"][value="self"]`);
await p.waitForFunction(() => document.querySelector('#wneeds').hidden, null, { timeout: 8000 }).catch(() => {});
const after2 = await p.evaluate(() => ({ hidden: document.querySelector('#wneeds').hidden }));
check('T8b dynamic: the artwork’s line shrinks to "who took the photograph", then disappears when complete', /Still needed to submit: who took the photograph$/.test(after1) && after2.hidden, after1);
await go(p, '#/');
check('T8c dynamic: the home count drops to 10', /10 details to complete/i.test(await p.locator('section[aria-labelledby=ck-h]').innerText()));

// T9c portrait link + credit link
await p.locator('a.st-ck-link[href="#/profile?fix=portrait_alt"]').click(); await p.waitForTimeout(700);
check('T9c checklist → portrait description: opens the profile and focuses "Describe your portrait" (marked Required)',
  await p.evaluate(() => document.activeElement.id === 'f-palt' && /Required/i.test(document.querySelector('label[for=f-palt]').innerText)));
await call('PATCH', `/api/images/${W[2].image}`, A, { alt: 'Synthetic painting', photographer: 'other_with_permission' });
await go(p, `#/work/${W[2].id}?fix=photo_credit&img=${W[2].image}`);
check('T9d an item for a missing photographer’s name opens the artwork with that field shown and focused',
  await p.evaluate(id => document.activeElement.id === `cr-${id}` && getComputedStyle(document.querySelector('[data-credit]')).display !== 'none', W[2].image));
await call('PATCH', `/api/images/${W[2].image}`, A, { photo_credit: 'Sam Synthetic' });

// X1 display bug: the photographer's name is hidden until "Another photographer" is chosen, then shown and focused
await go(p, `#/work/${W[3].id}`);
const crBefore = await p.evaluate(id => getComputedStyle(document.querySelector(`#cr-${id}`).closest('[data-credit]')).display, W[3].image);
await p.check(`[name="photographer-${W[3].image}"][value="other_with_permission"]`); await p.waitForTimeout(800);
const crAfter = await p.evaluate(id => ({ d: getComputedStyle(document.querySelector(`#cr-${id}`).closest('[data-credit]')).display, f: document.activeElement.id }), W[3].image);
check('X1 fixed: "Photographer’s name" is hidden until "Another photographer" is chosen, then appears (focused)', crBefore === 'none' && crAfter.d !== 'none' && crAfter.f === `cr-${W[3].image}`, JSON.stringify([crBefore, crAfter]));
check('X2 the three photograph fields are marked Required, with short helper text, and the radios are a labelled group',
  await p.evaluate(id => /Describe the photo\s*Required/i.test(document.querySelector(`label[for=alt-${id}]`).innerText) && document.querySelector(`#alt-${id}`).getAttribute('aria-required') === 'true'
    && /Who took this photograph\?\s*Required/i.test(document.querySelector(`[data-img="${id}"] fieldset legend`).innerText) && /Photographer’s name\s*Required/i.test(document.querySelector(`label[for=cr-${id}]`).innerText)
    && /screen readers/.test(document.querySelector(`#alth-${id}`).innerText), W[3].image));
await shot(p, '04-artwork-photo-details-other-photographer-1280.png', false);
await call('PATCH', `/api/images/${W[3].image}`, A, { alt: 'Synthetic painting with rectangles', photographer: 'self' });

// T10 keyboard only: Tab to the checklist, open the group with Enter, follow an item with Enter
await go(p, '#/');
let reached = null;
for (let k = 0; k < 40; k++) { await p.keyboard.press('Tab'); const t = await p.evaluate(() => document.activeElement.tagName + '|' + (document.activeElement.closest('.st-ck-d') ? 'grp' : '')); if (t === 'SUMMARY|grp') { reached = k; break; } }
await p.keyboard.press('Enter'); await p.waitForTimeout(200);
const opened = await p.evaluate(() => document.querySelector('.st-ck-d').open);
await p.keyboard.press('Tab'); await p.keyboard.press('Enter'); await p.waitForTimeout(800);
const kb = await p.evaluate(() => ({ id: document.activeElement.id, hash: location.hash }));
check('T10 keyboard only: Tab reaches the checklist, Enter opens the group, Enter on an item opens the artwork with the field focused',
  reached !== null && opened && /^#\/work\/.+\?fix=photo_alt/.test(kb.hash) && kb.id.startsWith('alt-'), JSON.stringify({ reached, opened, kb }));
check('X3 no script errors in the Studio during navigation', p.errs.length === 0, p.errs.join(' | '));
await p.ctx.close();

// T11 mobile
p = await page(A, { width: 390, height: 844 });
await go(p, '#/');
const mob = await p.evaluate(() => ({ over: document.documentElement.scrollWidth - document.documentElement.clientWidth, links: [...document.querySelectorAll('.st-ck-link, .st-ck-d > summary')].map(e => e.getBoundingClientRect().height) }));
await shot(p, '05-home-checklist-phone-390.png');
await p.locator('.st-ck-d > summary').click(); await shot(p, '06-home-checklist-expanded-phone-390.png');
await go(p, '#/submit');
const mobSub = await p.evaluate(() => { const b = document.querySelector('#go').getBoundingClientRect(), w = document.querySelector('#why').getBoundingClientRect(); return { over: document.documentElement.scrollWidth - document.documentElement.clientWidth, gap: w.top - b.bottom, wv: w.width > 200 }; });
await shot(p, '07-submit-disabled-with-explanation-phone-390.png');
check('T11 phone (390 px): no sideways scrolling, every checklist row is a ≥ 44 px tap target, the explanation sits directly under the button',
  mob.over <= 0 && mob.links.every(h => h >= 44) && mobSub.over <= 0 && mobSub.gap >= 0 && mobSub.gap < 40 && mobSub.wv, JSON.stringify({ mob, mobSub }));
await p.ctx.close();

// T12 founder view
const fv = await call('GET', `/api/admin/artists/${AID}/checklist`, FOUNDER);
s = await me(A);
check('T12 founder: read-only checklist for an artist: count, exact items, and the section/artwork each belongs to (identical to the artist’s own list)',
  fv.s === 200 && fv.j.count === s.checklist.length && JSON.stringify(fv.j.items) === JSON.stringify(s.checklist) && fv.j.items.some(i => i.area === 'profile') && fv.j.items.filter(i => i.area === 'work').every(i => i.title && i.work_id), fv.t.slice(0, 300));
p = await page(FOUNDER);
await go(p, 'admin'); await p.waitForTimeout(400);
await p.locator(`[data-ck="${AID}"]`).click(); await p.waitForTimeout(700);
const desk = await p.locator(`#ck-${AID}`).innerText();
check('T12b the Review Desk opens the list in place: "<n> items before they can submit", by section, with no buttons to change or waive anything',
  new RegExp(`Lena Synthetic · ${s.checklist.length} items before they can submit`).test(desk) && /Profile/.test(desk) && /Artwork/.test(desk) && (await p.locator(`#ck-${AID} button, #ck-${AID} input`).count()) === 0, desk.slice(0, 300));
await p.locator(`#ck-${AID}`).scrollIntoViewIfNeeded(); await shot(p, '08-review-desk-artist-checklist-1280.png', false);
await p.ctx.close();

// T13 isolation
const B = 'bo@example.test'; const BID = await mk('Bo Synthetic', B);
const i1 = await call('GET', `/api/admin/artists/${AID}/checklist`, B), i2 = await call('GET', `/api/admin/artists/${BID}/checklist`, B);
const bs = await me(B), bPage = await call('GET', `/#/work/${W[4].id}`, B), bWork = await call('GET', `/api/artworks/${W[4].id}`, B);
check('T13 artist isolation: an artist gets 403 on the founder checklist (another’s or their own); their own list holds only their items; another artist’s work → 404',
  i1.s === 403 && i2.s === 403 && !JSON.stringify(bs).includes(W[4].id) && !JSON.stringify(bs).includes('Night Study') && bWork.s === 404, `${i1.s} ${i2.s} ${bWork.s}`);

// T14 suspended
await call('POST', `/api/admin/artists/${BID}/suspend`, FOUNDER);
const sus = await call('GET', '/api/me', B), susSub = await call('POST', '/api/submit', B, { accept_licence: true });
const susF = await call('GET', `/api/admin/artists/${BID}/checklist`, FOUNDER);
check('T14 suspended account: no Studio, no checklist, no submission (403); the founder can still read their list', sus.s === 403 && susSub.s === 403 && susF.s === 200 && !sus.j.status);

// T16 server rejection when the button is bypassed
const rej = await call('POST', '/api/submit', A, { accept_licence: true });
s = await me(A);
check('T16 server still refuses an incomplete submission sent directly (422), listing exactly the checklist items', rej.s === 422 && rej.j.problems.join('|') === s.checklist.map(i => i.text).join('|'));

// T17 viewing changes nothing
const rows = async t => JSON.stringify((await db.prepare(`SELECT * FROM ${t} ORDER BY id`).all()).results);   // rows only (not the query timing metadata)
const snap = async () => (await rows('artists')) + (await rows('artworks')) + (await rows('images'));
const auditN = async () => (await db.prepare('SELECT COUNT(*) n FROM audit').first()).n;
const b0 = await snap(), a0 = await auditN();
await call('GET', `/api/admin/artists/${AID}/checklist`, FOUNDER); await call('GET', '/api/me', A); await call('GET', '/api/admin/overview', FOUNDER);
const b1 = await snap(), a1 = await auditN();
const firstDiff = () => { let k = 0; while (k < b0.length && b0[k] === b1[k]) k++; return b0.slice(Math.max(0, k - 160), k + 80) + ' ⟶ ' + b1.slice(Math.max(0, k - 20), k + 80); };
check('T17 reading checklists (artist or founder) changes no artist, artwork or image data and writes nothing to the audit log', b0 === b1 && a0 === a1, b0 === b1 ? `audit ${a0}→${a1}` : firstDiff());

// T15 complete everything through the API, then submit through the page
for (const w of W.slice(4)) await call('PATCH', `/api/images/${w.image}`, A, { alt: 'Synthetic painting with rectangles', photographer: 'self' });
p = await page(A, { width: 390, height: 844 });
await go(p, '#/submit');
const oneLeft = await p.locator('#why').innerText();
check('T8d dynamic: with only the portrait left the explanation reads "1 detail still needs your attention…"', /^1 detail still needs your attention before you can submit your gallery\./.test(oneLeft), oneLeft);
await call('PATCH', `/api/images/${por.j.id}`, A, { alt: 'Portrait of the synthetic artist', photographer: 'self' });
await p.reload({ waitUntil: 'load' }); await p.waitForTimeout(600);   // the portrait was described through the API here, so load the page again
const ready = await p.evaluate(() => ({ dis: document.querySelector('#go').disabled, why: !!document.querySelector('#why'), todo: !!document.querySelector('#todo-h') }));
await shot(p, '09-submit-ready-phone-390.png');
await p.check('#lic'); await p.click('#go'); await p.waitForTimeout(1200);
const done = await call('GET', '/api/admin/overview', FOUNDER);
const ov = done.j.artists.find(a => a.id === AID);
check('T8e/T15 all complete: explanation and list disappear, the button is enabled, and the submission goes through', !ready.dis && !ready.why && !ready.todo && ov.state === 'in_review' && ov.problems === 0, JSON.stringify(ready));
await p.ctx.close();
await browser.close();

// T18 authentication unchanged (fuller suite: prove-access.mjs)
const t18 = [await call('GET', '/', 'stranger@example.test'), await call('GET', '/api/me', null), await call('GET', '/admin', A), await call('GET', '/api/admin/overview', A)];
check('T18 authentication unchanged: unknown → refusal page (403), no token → 401, artist → founder desk 403', t18[0].s === 403 && /data-signed-in-as/.test(t18[0].t) && t18[1].s === 401 && t18[2].s === 403 && t18[3].s === 403);

// X4 the rules are word-for-word what they were: readiness() == checklist().map(text), and fixed expectations
const snapX = { artist: { display_name: 'X', bio: 'short', statement: 'abc', medium: null, portrait: { id: 'i1', alt: null } },
  works: [{ title: null, medium: null, h_cm: null, w_cm: 1, ai_involvement: 'assisted', ai_note: null, images: [{ id: 'm', role: 'main', alt: null, photographer: 'other_with_permission', photo_credit: null }] }] };
const got = L.readiness(snapX, { founding: true, licenceOk: false, imageBlocks: new Set(['m']) });
// expected = the output of the rules as released in f504230 for this snapshot (also checked on 40,000 random galleries)
check('X4 rule wording unchanged (every rule at once, identical to the released rules)', JSON.stringify(got) === JSON.stringify(['Your name must be 2–80 characters (now 1)', 'Your biography must be 40–2400 characters (now 5)',
  'Your statement must be 10–400 characters (now 3)', 'Choose your main medium in your profile', 'Describe your portrait photograph (for people using screen readers)',
  'An untitled artwork needs a title, the medium, its size, a short AI disclosure, a description of each photograph, the photographer’s name, a photograph that passes the checks',
  'Accept the Gallery Publication and Image Licence']), JSON.stringify(got));

await mf.dispose();
const pass = results.filter(Boolean).length;
console.log(`\n${pass}/${results.length} checks passed`);
process.exit(pass === results.length ? 0 : 1);
