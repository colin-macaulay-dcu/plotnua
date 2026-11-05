// PROVE · PlotArt Studio · sign-in access and email correction (PLOTART-STUDIO-ACCESS-002, 5 Nov 2026).
// Synthetic artists only; the real Worker runs locally (Miniflare/workerd) with a local D1. Nothing here touches
// Cloudflare, the production database or any real artist.        node test/prove-access.mjs
// Numbered checks T1..T20 match section 10 of the brief; S-checks are the extra security checks from section 9.
import { start, token, otherKey, FOUNDER, AUD } from './local.mjs';
import * as L from '../src/lib.js';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
const { mf, url, db } = await start({ port: 8799 });
const call = async (method, path, who, body, { headers = {}, tok } = {}) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json', ...headers };
  const t = tok || (who ? token(who) : null);
  if (t) h['Cf-Access-Jwt-Assertion'] = t;
  const r = await mf.dispatchFetch(url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const text = await r.text();
  let j = {}; try { j = JSON.parse(text); } catch { /* html */ }
  return { s: r.status, j, t: text };
};
const row = id => db.prepare('SELECT * FROM artists WHERE id=?').bind(id).first();
const isStudio = r => r.s === 200 && r.t.includes('/assets/studio.js');
const isRefused = (r, email) => r.s === 403 && r.t.includes('data-signed-in-as') && r.t.includes(`>${email}<`) &&
  r.t.includes('We couldn’t find an active PlotArt Studio account associated with this email address.') &&
  r.t.includes('If you’ve already been invited, please sign in using the email address shown in your invitation.') &&
  r.t.includes('href="/cdn-cgi/access/logout"') && r.t.includes('Sign out and use a different email');

console.log('PROVE · PlotArt Studio · access and email correction');
const mk = async (name, email, founding = true) => call('POST', '/api/admin/artists', FOUNDER, { display_name: name, email, founding });
const INV = 'iona.invited@example.test', ACT = 'aine.active@example.test', SUS = 'sean.suspended@example.test', END = 'eva.ended@example.test';
const LEAH_LIKE = 'lara.synthetic@example.test', LEAH_OTHER = 'info@lara-studio.example.test';
const ids = {};
for (const [k, n, e] of [['inv', 'Iona Synthetic', INV], ['act', 'Áine Synthetic', ACT], ['sus', 'Seán Synthetic', SUS], ['end', 'Eva Synthetic', END], ['lara', 'Lara Synthetic', LEAH_LIKE]])
  ids[k] = (await mk(n, e)).j.id;
const mail0 = (await db.prepare('SELECT COUNT(*) n FROM mail_capture').first()).n;

// T1 / T2
let r = await call('GET', '/', INV);
check('T1  correct email of an INVITED artist → Studio opens (and the account becomes active, as before)', isStudio(r) && (await row(ids.inv)).account_status === 'active');
await call('GET', '/', ACT);
r = await call('GET', '/', ACT);
check('T2  correct email of an ACTIVE artist → Studio opens', isStudio(r) && (await row(ids.act)).account_status === 'active');

// set up suspended (through the founder route) and ended (directly in the LOCAL database; there is no route for it)
await call('GET', '/', SUS); await call('GET', '/', END);
await call('POST', `/api/admin/artists/${ids.sus}/suspend`, FOUNDER);
await db.prepare("UPDATE artists SET account_status='ended' WHERE id=?").bind(ids.end).run();

// T3 – T5: the Leah situation: a real, verified address that is not the registered one
r = await call('GET', '/', LEAH_OTHER);
check('T3  wrong email (verified by Access, not registered) → refused (403), Studio not served', r.s === 403 && !r.t.includes('/assets/studio.js'));
check('T4  the refusal page shows the address the person is signed in as, with the approved wording', isRefused(r, LEAH_OTHER), r.t.slice(0, 400));
// the only addresses on the page: the person's own, and PlotArt's public support address
const onPage = [...new Set((r.t.match(/[^\s<>":]+@[^\s<>"]+/g) || []))].sort().join(' ');
check('T4b the refusal page shows NO other address: not the registered one, not any artist’s, not the founder’s',
  onPage === ['hello@plotnua.ie', LEAH_OTHER].sort().join(' ') && ![LEAH_LIKE, INV, ACT, SUS, END, FOUNDER].some(x => r.t.includes(x)), onPage);
check('T5  a prominent "Sign out and use a different email" button uses the existing Access logout (/cdn-cgi/access/logout)',
  /<a class="st-refused-out" href="\/cdn-cgi\/access\/logout" data-signout>Sign out and use a different email<\/a>/.test(r.t));
const api = await call('GET', '/api/me', LEAH_OTHER);
check('T5b the API refusal carries the same message, the person’s own address and the sign-out link; no artist data',
  api.s === 403 && api.j.ok === false && api.j.error.includes(`signed in as ${LEAH_OTHER}`) && api.j.signout === '/cdn-cgi/access/logout' && !api.j.artist);
const ck = await mf.dispatchFetch(url + '/', { headers: { Cookie: `CF_Authorization=${token(LEAH_OTHER)}` } });
check('T5c the same page is shown when the identity comes from the Access cookie (the browser case)', isRefused({ s: ck.status, t: await ck.text() }, LEAH_OTHER));

// T6: sign-out → new email. Sign-out itself is Cloudflare's (/cdn-cgi/access/logout is answered at Cloudflare's edge and
// never reaches the Worker; checked live separately). What the Worker must guarantee: it keeps NO session of its own,
// so the next request with a token for the registered address opens the Studio, and the refusal changed nothing.
const before = await row(ids.lara);
r = await call('GET', '/', LEAH_LIKE);
check('T6  after signing out, signing in with the registered email opens the Studio (refusal left no state behind)',
  before.account_status === 'invited' && isStudio(r) && (await row(ids.lara)).account_status === 'active');
r = await call('GET', '/', LEAH_OTHER);
check('T6b …and the other address is still refused afterwards (nothing was linked to it)', isRefused(r, LEAH_OTHER));

// T7 – T9
const sameText = x => x.t.replace(/data-signed-in-as>[^<]*</, '');
const rs = await call('GET', '/', SUS), re = await call('GET', '/', END), ru = await call('GET', '/', 'nobody@example.test');
check('T7  SUSPENDED artist → refused', isRefused(rs, SUS) && (await row(ids.sus)).account_status === 'suspended');
check('T8  ENDED artist → refused', isRefused(re, END) && (await row(ids.end)).account_status === 'ended');
check('T9  UNREGISTERED address → refused', isRefused(ru, 'nobody@example.test'));
check('T9b suspended, ended and unregistered see the identical page (no account status disclosed)', sameText(rs) === sameText(re) && sameText(re) === sameText(ru));
const as = await call('GET', '/api/artworks', SUS), ae = await call('POST', '/api/artworks', END), an = await call('GET', '/api/me', null);
check('T9c suspended/ended get no API access; no token → 401 "Please sign in" page, not the refusal page',
  as.s === 403 && ae.s === 403 && an.s === 401 && !(await call('GET', '/', null)).t.includes('data-signed-in-as'));

// T10 / T11
r = await call('GET', '/admin', FOUNDER);
check('T10 founder → Review Desk opens', r.s === 200 && r.t.includes('/assets/admin.js'));
const a1 = await call('GET', '/admin', ACT), a2 = await call('GET', '/api/admin/overview', ACT), a3 = await call('POST', `/api/admin/artists/${ids.inv}/email`, ACT, { email: 'x@example.test', confirm_email: 'x@example.test', confirm: true });
check('T11 artist → founder administration refused (page, data and the new email route all 403)', a1.s === 403 && a2.s === 403 && a3.s === 403 && (await row(ids.inv)).email === INV);
const a4 = await call('POST', `/api/admin/artists/${ids.act}/email`, ACT, { email: 'mine@example.test', confirm_email: 'mine@example.test', confirm: true });
check('T11b an artist cannot change even their OWN email (founder-only)', a4.s === 403 && (await row(ids.act)).email === ACT);

// give the active artist real content: profile, two works, Founding status, so T18 can prove nothing is reset
await call('PUT', '/api/me/profile', ACT, { practice: 'Painter', county: 'Clare' });
const w1 = (await call('POST', '/api/artworks', ACT)).j.id, w2 = (await call('POST', '/api/artworks', ACT)).j.id;
await call('PUT', `/api/artworks/${w1}`, ACT, { title: 'Burren Light', year: 2026, medium: 'Oil on linen', h_cm: 50, w_cm: 70, price_eur: 900, ai_involvement: 'none' });
const snap = async id => ({ a: await row(id), works: (await db.prepare('SELECT id, title FROM artworks WHERE artist_id=? ORDER BY id').bind(id).all()).results });
const pre = await snap(ids.act), others = { inv: await row(ids.inv), lara: await row(ids.lara), sus: await row(ids.sus), end: await row(ids.end) };

// T12 – T14
const NEW = 'aine.studio@example.test';
r = await call('POST', `/api/admin/artists/${ids.act}/email`, FOUNDER, { email: '  Aine.Studio@Example.test ', confirm_email: 'aine.studio@example.test', confirm: true });
check('T12 founder changes the artist’s email (typed twice + confirmed) → saved', r.s === 200 && r.j.email === NEW && r.j.email_sent === false && (await row(ids.act)).email === NEW, r.t);
const aud = await db.prepare("SELECT * FROM audit WHERE action='email_changed' AND artist_id=?").bind(ids.act).first();
check('T12b the change is in the audit log (founder, artist, masked old and new address); no email was sent',
  aud && aud.actor === FOUNDER && aud.role === 'founder' && JSON.parse(aud.detail).from === 'ai…@example.test' && JSON.parse(aud.detail).to === 'ai…@example.test' &&
  !aud.detail.includes(ACT) && (await db.prepare('SELECT COUNT(*) n FROM mail_capture').first()).n === mail0);
r = await call('GET', '/', ACT);
check('T13 the OLD email no longer grants access (refusal page, and the API gives nothing)', isRefused(r, ACT) && (await call('GET', '/api/artworks', ACT)).s === 403);
r = await call('GET', '/', NEW);
const me = await call('GET', '/api/me', NEW);
check('T14 the NEW email grants access to the same account', isStudio(r) && me.s === 200 && me.j.artist.id === ids.act && me.j.artist.email === NEW);

// T15 – T17
const tryChange = (id, email, confirm_email = email, confirm = true) => call('POST', `/api/admin/artists/${id}/email`, FOUNDER, { email, confirm_email, confirm });
const d1 = await tryChange(ids.lara, INV), d2 = await tryChange(ids.lara, INV.toUpperCase()), d3 = await tryChange(ids.lara, SUS);
check('T15 duplicate email rejected (another artist’s address, in any capitalisation, including a suspended account’s)',
  [d1, d2, d3].every(x => x.s === 409 && /already uses that email/.test(x.j.error)) && (await row(ids.lara)).email === LEAH_LIKE);
const bad = await Promise.all(['', 'not-an-email', 'a@b', 'two@@example.test', 'space in@example.test', 'x@example', 'x@-bad.example.test'].map(e => tryChange(ids.lara, e)));
const mism = await tryChange(ids.lara, 'lara.new@example.test', 'lara.neu@example.test'), unconf = await tryChange(ids.lara, 'lara.new@example.test', 'lara.new@example.test', false);
const nohdr = await call('POST', `/api/admin/artists/${ids.lara}/email`, FOUNDER, { email: 'lara.new@example.test', confirm_email: 'lara.new@example.test', confirm: true }, { headers: { 'X-Studio': '' } });
const same = await tryChange(ids.lara, LEAH_LIKE), fnd = await tryChange(ids.lara, FOUNDER), ghost = await tryChange('a0000000000', 'g@example.test');
check('T16 invalid changes rejected: malformed, mismatched confirmation, not confirmed, unchanged, founder address, unknown artist, cross-site (no X-Studio)',
  bad.every(x => x.s === 400) && mism.s === 400 && unconf.s === 400 && same.s === 400 && fnd.s === 409 && ghost.s === 404 && nohdr.s === 403 && (await row(ids.lara)).email === LEAH_LIKE,
  JSON.stringify([...bad.map(x => x.s), mism.s, unconf.s, same.s, fnd.s, ghost.s, nohdr.s]));
const sneaky = { 'zero-width space': 'lara​@example.test', 'soft hyphen': 'la­ra@example.test', 'no-break space': 'lara @example.test', 'BOM': '﻿lara@example.test',
  'word joiner': 'lara⁠@example.test', 'RTL override': 'lara‮@example.test', 'control char': 'lara\u0007@example.test', 'Cyrillic а': 'lаra@example.test',
  'Greek ο': 'lara@exampοle.test', 'full-width ＠': 'lara＠example.test', 'accented é': 'léa@example.test' };
const chg = await Promise.all(Object.values(sneaky).map(e => tryChange(ids.lara, e)));
const crt = await Promise.all(Object.values(sneaky).map((e, i) => mk('Sneaky ' + i, e)));
check('T17 invisible characters, control characters and look-alike letters rejected, on CHANGE and on CREATE, with a message naming the character',
  chg.every(x => x.s === 400 && /U\+[0-9A-F]{4}/.test(x.j.error)) && crt.every(x => x.s === 400 && /U\+[0-9A-F]{4}/.test(x.j.error)) &&
  (await db.prepare("SELECT COUNT(*) n FROM artists WHERE display_name LIKE 'Sneaky%'").first()).n === 0 && (await row(ids.lara)).email === LEAH_LIKE,
  JSON.stringify(chg.concat(crt).filter(x => x.s !== 400 || !/U\+/.test(x.j.error)).map(x => x.t)));
console.log('        e.g. ' + chg[0].j.error);

// T18 / T19
const post = await snap(ids.act);
const keep = ['id', 'slug', 'display_name', 'founding', 'account_status', 'application_ref', 'practice', 'county', 'licence_version', 'created_at', 'first_published_at', 'founding_number'];
check('T18 artwork, Founding status, account status and profile progress preserved; only email (and updated_at) changed',
  keep.every(k => pre.a[k] === post.a[k]) && JSON.stringify(pre.works) === JSON.stringify(post.works) && post.works.length === 2 && post.a.founding === 1 &&
  post.a.account_status === 'active' && post.a.practice === 'Painter' && Object.keys(pre.a).filter(k => pre.a[k] !== post.a[k]).sort().join() === 'email,updated_at',
  Object.keys(pre.a).filter(k => pre.a[k] !== post.a[k]).join());
const lv = await tryChange(ids.lara, 'lara.correct@example.test');  // an INVITED account (the Leah case) stays invited
await db.prepare("UPDATE artists SET account_status='invited' WHERE id=?").bind(ids.lara).run();
const lv2 = await tryChange(ids.lara, 'lara.right@example.test');
check('T18b correcting an INVITED account keeps it invited until the artist signs in with the new address',
  lv.s === 200 && lv2.s === 200 && lv2.j.account_status === 'invited' && (await row(ids.lara)).account_status === 'invited' && isStudio(await call('GET', '/', 'lara.right@example.test')));
const aft = { inv: await row(ids.inv), sus: await row(ids.sus), end: await row(ids.end) };
check('T19 other accounts unaffected (emails, statuses, updated_at) and still behave as before',
  ['inv', 'sus', 'end'].every(k => JSON.stringify(others[k]) === JSON.stringify(aft[k])) && isStudio(await call('GET', '/', INV)) && isRefused(await call('GET', '/', SUS), SUS));
const okCreate = await mk('Plain Synthetic', 'First.Last+gallery@Sub.Example.ie');
check('T19b legitimate addresses still accepted on create, kept exactly (dots and +tags preserved; only lower-cased, as before)',
  okCreate.s === 200 && (await row(okCreate.j.id)).email === 'first.last+gallery@sub.example.ie');
check('T19c the validator never rewrites a stored address: no UPDATE of email outside the founder route (source check)',
  (await import('node:fs')).readFileSync(new URL('../src/index.js', import.meta.url), 'utf8').match(/UPDATE artists SET email/g).length === 1);

// T20 mobile: structural checks here; the screenshots at 390 px are taken by the report script
r = await call('GET', '/', LEAH_OTHER);
check('T20 refusal page is mobile-ready: viewport meta, full-width button ≥ 48 px tall, long addresses wrap',
  r.t.includes('name="viewport" content="width=device-width, initial-scale=1"') && /\.st-refused-out\{[^}]*min-height:52px[^}]*width:100%/.test((await call('GET', '/assets/studio.css', null)).t) &&
  /\.st-refused-email\{[^}]*overflow-wrap:anywhere/.test((await call('GET', '/assets/studio.css', null)).t));

// Section 9 security checks
const NEWB = 'brand.new@example.test';
await tryChange(ids.inv, NEWB);
const s1 = await call('GET', '/admin', NEWB), s2 = await call('GET', '/api/admin/overview', NEWB);
check('S1 changing an artist’s email never grants founder rights (new address → artist only; founder list is env-only)', s1.s === 403 && s2.s === 403 && isStudio(await call('GET', '/', NEWB)));
const xw = await call('GET', `/api/artworks/${w1}`, NEWB), xp = await call('PUT', `/api/artworks/${w1}`, NEWB, { title: 'Hijack' });
const xprev = await call('GET', `/admin/preview/v-${ids.act}-1/index.html`, NEWB);
check('S2 an artist cannot reach another artist’s works or previews', xw.s === 404 && xp.s === 404 && xprev.s === 403 && (await db.prepare('SELECT title FROM artworks WHERE id=?').bind(w1).first()).title === 'Burren Light', `${xw.s} ${xp.s} ${xprev.s}`);
const t1 = await call('GET', '/', null, undefined, { tok: token(NEW, { exp: -60 }) }), t2 = await call('GET', '/', null, undefined, { tok: token(NEW, { aud: 'other-aud' }) });
const t3 = await call('GET', '/', null, undefined, { tok: token(NEW, { key: otherKey }) }), t4 = await call('GET', '/', null, undefined, { tok: token(NEW).slice(0, -4) + 'AAAA' });
check('S3 tokens still validated: expired, wrong audience, wrong signing key and tampered tokens → 401, never the Studio or the refusal page',
  [t1, t2, t3, t4].every(x => x.s === 401 && !x.t.includes('data-signed-in-as') && !x.t.includes('/assets/studio.js')), [t1, t2, t3, t4].map(x => x.s).join());
const xss = await call('GET', '/', 'a"<script>alert(1)</script>@example.test');
check('S4 the address on the refusal page is HTML-escaped (defence in depth)', xss.s === 403 && !xss.t.includes('<script>alert') && xss.t.includes('&lt;script&gt;'));
const dollars = await call('GET', '/', "a$&$'$`@example.test");
check('S5 special replacement patterns in an address are shown literally', dollars.t.includes("a$&amp;$&#39;$`@example.test"));
check('S6 no new table and no refused-sign-in logging (brief §8): schema unchanged, refusals write nothing',
  !(await db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%refus%'").first()) &&
  (await db.prepare("SELECT COUNT(*) n FROM audit WHERE actor LIKE '%lara-studio%' OR actor LIKE 'nobody@%'").first()).n === 0);
check('S7 unit: the shared validator (create and update) accepts plain addresses and rejects hidden characters',
  L.artistEmail(' Leah@Gmail.com\n') === 'leah@gmail.com' && (() => { try { L.artistEmail('leah​hewson@gmail.com'); return false; } catch (e) { return /U\+200B/.test(e.message); } })());

await mf.dispose();
const pass = results.filter(Boolean).length;
console.log(`\n${pass}/${results.length} checks passed`);
process.exit(pass === results.length ? 0 : 1);
