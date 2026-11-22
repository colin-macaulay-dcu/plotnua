// PROVE (local) · the basket seed on the EXISTING TEST database is additive and safe to repeat. A local D1 is built the way
// plotart-checkout-test was (schema.sql + 0013 + its own synthetic seed), with one existing TEST artist already owning one of
// the two Stripe TEST accounts; then 0019 and the adaptive basket seed are applied TWICE. Nothing existing may change.
//   node test/prove-basket-test-seed.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { start, token, FOUNDER } from './local.mjs';
import { statements } from './sql.mjs';

const HERE = new URL('..', import.meta.url).pathname, TMP = '/tmp/claude-0/basket-test-seed-state.json';
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(typeof d === 'string' ? d : JSON.stringify(d)).slice(0, 600)}]` : ''}`); };
const ACC = ['acct_testSlotA', 'acct_testSlotB'];
const ENV = { ENVIRONMENT: 'test', STAGING_GALLERY: 'true', GALLERY_ORIGIN: 'https://checkout.local', STAGING_GALLERY_URL: 'https://studio.local/admin/basket-gallery', CHECKOUT_PILOT_ENABLED: 'true', BASKET_ENABLED: 'true', BASKET_COMMISSION_FREE: 'with_processing_consent', STRIPE_SECRET_KEY: 'rk_test_seedcheck', STRIPE_WEBHOOK_SECRET: 'whsec_x', CHECKOUT_ORIGIN: 'https://checkout.local' };
let S;
try {
  console.log('PROVE · basket seed on the existing TEST database (additive, repeatable)');
  S = await start({ port: 8897, env: { ...ENV, ENVIRONMENT: 'local' }, checkout: { env: ENV } });   // the Studio's local sign-in needs ENVIRONMENT=local; the checkout Worker runs as TEST
  const { db } = S, q = async (sql, ...b) => (await db.prepare(sql).bind(...b).all()).results;
  const run = async sql => { let err = null; for (const s of statements(sql)) { try { await db.prepare(s).run(); } catch (e) { err = err || `${e.message} :: ${s.slice(0, 100)}`; } } return err; };
  // the TEST database as it is today: 0013 + its own synthetic seed (+ the legacy licence rows), one artist on a TEST account
  await run(readFileSync(HERE + 'migrations/0013_gallery_artist_agreement_text.sql', 'utf8'));
  await run(execFileSync('node', [HERE + 'test/checkout-test-env-seed.mjs', '--target', 'plotart-checkout-test', '--founding', 'f1@example.invalid', '--gallery', 'g1@example.invalid'], { encoding: 'utf8' }));
  await db.prepare("UPDATE artists SET account_status = 'active'").run();
  await db.prepare("INSERT INTO payment_accounts (artist_id, account_id, country, livemode, charges_enabled, payouts_enabled, details_submitted, created_at, updated_at) VALUES ('atestfnd', ?, 'IE', 0, 1, 1, 1, ?, ?)").bind(ACC[1], new Date().toISOString(), new Date().toISOString()).run();
  const before = JSON.stringify({ artists: await q('SELECT * FROM artists ORDER BY id'), works: await q('SELECT * FROM artworks ORDER BY id'), versions: await q('SELECT * FROM versions ORDER BY artist_id, version'),
    accounts: await q('SELECT * FROM payment_accounts ORDER BY artist_id'), orders: await q('SELECT * FROM checkout_orders') });
  const state = { seller_profiles: await q('SELECT artist_id, legal_name, trading_name, address, returns_address, email, phone, vat_number FROM seller_profiles'), payment_accounts: await q('SELECT account_id, artist_id FROM payment_accounts'), artists: await q('SELECT id, slug, display_name, email, founding, account_status FROM artists') };
  writeFileSync(TMP, JSON.stringify(state));
  const seed = () => execFileSync('node', [HERE + 'test/basket-staging-seed.mjs', '--target', 'plotart-checkout-test', '--accounts', ACC.join(','), '--state', TMP], { encoding: 'utf8' });
  const mig = readFileSync(HERE + 'migrations/0019_multi_artist_basket.sql', 'utf8') + '\n' + readFileSync(HERE + 'migrations/0020_basket_consents.sql', 'utf8') + '\n' + readFileSync(HERE + 'migrations/0022_delivery_safety.sql', 'utf8');
  let err = (await run(mig)) || (await run(seed()));
  check('T1 0019 and the basket seed apply to the TEST database as it is', !err, err);
  err = (await run(mig)) || (await run(seed()));
  check('T2 applying both again changes nothing and fails nothing (idempotent)', !err && (await q("SELECT * FROM versions WHERE source = 'basket-test-seed'")).length === 1 && (await q("SELECT * FROM artworks WHERE id LIKE 'wbk%'")).length === 3, err);
  const after = { artists: await q("SELECT * FROM artists WHERE id NOT IN ('astgal') ORDER BY id"), works: await q("SELECT * FROM artworks WHERE id NOT LIKE 'wbk%' AND artist_id NOT IN ('astgal') ORDER BY id"),
    versions: await q("SELECT * FROM versions WHERE source <> 'basket-test-seed' AND artist_id NOT IN ('astgal') ORDER BY artist_id, version"), accounts: await q("SELECT * FROM payment_accounts WHERE artist_id NOT IN ('astgal') ORDER BY artist_id"), orders: await q('SELECT * FROM checkout_orders') };
  check('T3 nothing that existed changed: artists, artworks, versions, payment accounts, orders', JSON.stringify(after) === before);
  // a later redeploy reads the database again: our own synthetic artists now own their accounts, and nothing new may be added
  const state2 = { seller_profiles: await q('SELECT artist_id, legal_name, trading_name, address, returns_address, email, phone, vat_number FROM seller_profiles'), payment_accounts: await q('SELECT account_id, artist_id FROM payment_accounts'), artists: await q('SELECT id, slug, display_name, email, founding, account_status FROM artists') };
  writeFileSync(TMP, JSON.stringify(state2));
  const counts = async () => JSON.stringify([await q('SELECT COUNT(*) AS n FROM artworks'), await q('SELECT COUNT(*) AS n FROM versions'), await q('SELECT COUNT(*) AS n FROM artwork_delivery_offers')]);
  const c0 = await counts(); err = await run(seed());
  check('T2b a redeploy that reads the database again adds nothing (its own synthetic artists are recognised)', !err && (await counts()) === c0, { err, before: c0, after: await counts() });
  const v = JSON.parse((await q("SELECT snapshot FROM versions WHERE source = 'basket-test-seed'"))[0].snapshot);
  check('T4 the existing artist’s new published version keeps all their works and adds the synthetic basket works', v.works.length === 6 && v.works.filter(w => w.id.startsWith('wbk')).length === 3 && v.works.some(w => w.id === 'watestfnd1'));
  const r = await S.mf.dispatchFetch(S.url + '/api/admin/checkout/baskets/eligibility?ids=wastgal1,wbkatestfnd1,watestfnd1', { headers: { 'Cf-Access-Jwt-Assertion': token(FOUNDER), 'X-Studio': '1' } });
  const el = Object.fromEntries((await r.json()).items.map(i => [i.id, i]));
  check('T5 basket works: the new synthetic Gallery Artist at 15%, the existing Founding Artist’s new works at 0%; their older works untouched (no delivery offer: enquiry)',
    el.wastgal1.ok && el.wastgal1.commission_basis === 'gallery_artist_agreement' && el.wbkatestfnd1.ok && el.wbkatestfnd1.commission_basis === 'founding_enquiry' && !el.watestfnd1.ok, el);
  // the TEST arrangement: the synthetic gallery is a founder page in the TEST Studio (behind its Access); the checkout Worker
  // serves the basket and the images, never the gallery pages
  const st = async (path, email) => { const r = await S.mf.dispatchFetch(S.url + path, { headers: { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1' } }); return { s: r.status, t: await r.text() }; };
  const g = await st('/admin/basket-gallery', FOUNDER), gi = await st('/admin/basket-gallery/wastgal1', FOUNDER);
  check('T6 TEST: the founder sees the synthetic gallery in the TEST Studio; images and “Add to basket” point to the checkout Worker',
    g.s === 200 && /class="card" href="\/admin\/basket-gallery\/wastgal1"/.test(g.t) && /src="https:\/\/checkout\.local\/staging-img\/wastgal1\.svg"/.test(g.t)
    && gi.s === 200 && /href="https:\/\/checkout\.local\/basket\?add=wastgal1&amp;img=https%3A%2F%2Fcheckout\.local%2Fstaging-img%2Fwastgal1\.svg"/.test(gi.t), { gs: g.s, gis: gi.s, sample: gi.t.slice(gi.t.indexOf('Add to basket') - 220, gi.t.indexOf('Add to basket')) });
  const a = await st('/admin/basket-gallery', 'f1@example.invalid');
  check('T7 TEST: an artist (not the founder) cannot open it', a.s === 403 || a.s === 401, a.s);
  const CW = S.checkoutWorker, cw = async path => { const r = await CW.fetch('https://checkout.local' + path, { redirect: 'manual' }); return { s: r.status, t: await r.text() }; };
  const cg = await cw('/gallery'), ci = await cw('/staging-img/wastgal1.svg'), cb = await cw('/basket');
  check('T8 TEST: the checkout Worker does NOT serve the gallery pages; it serves the synthetic images and the basket (linking back to the Studio gallery)', cg.s === 404 && ci.s === 200 && cb.s === 200 && cb.t.includes('https://studio.local/admin/basket-gallery'), { cg: cg.s, ci: ci.s, cb: cb.s });
  console.log(`\nBASKET TEST SEED · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
  process.exitCode = results.every(Boolean) ? 0 : 1;
} finally { if (S) await S.mf.dispose(); }
