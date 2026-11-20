// PlotArt managed checkout · LIVE-MODE GATE (20 Nov 2026). Proves that live mode cannot activate accidentally, that TEST
// credentials and resources cannot be used in production, and that the TEST environment is unchanged.
//   node test/prove-live-gate.mjs
// Local only: no network (fetch is replaced), no Cloudflare, no Stripe. Uses node:sqlite for a scratch database.
import { createHmac } from 'node:crypto';
import { readFileSync, mkdtempSync, cpSync, rmSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';

const HERE = join(dirname(fileURLToPath(import.meta.url)), '..') + '/';
const ROOT = join(HERE, '..', '..') + '/';
let pass = 0, fail = 0;
const check = (n, ok, info) => { ok ? pass++ : fail++; console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${ok || info === undefined ? '' : '  ' + JSON.stringify(info).slice(0, 300)}`); };
const S = await import(HERE + 'src/stripe.js');
const C = await import(HERE + 'src/checkout.js');
const P = (await import(HERE + 'src/checkout-public.js')).default;

const LIVE = { ENVIRONMENT: 'production', CHECKOUT_LIVE: 'true', STRIPE_SECRET_KEY: 'rk_live_abc123' };
const TEST = { ENVIRONMENT: 'test', STRIPE_SECRET_KEY: 'rk_test_abc123' };

console.log('— L1 the gate: live only by every condition together; everything else refused or test');
const M = e => S.stripeMode(e);
check('L1a the verified live configuration is live', M(LIVE).ok && M(LIVE).live === true && M(LIVE).mode === 'live');
check('L1b the TEST environment is test mode, unchanged (rk_test_/sk_test_, ENVIRONMENT test or local)', M(TEST).ok && !M(TEST).live
  && M({ ENVIRONMENT: 'local', STRIPE_SECRET_KEY: 'sk_test_x1' }).mode === 'test' && M({ STRIPE_SECRET_KEY: 'sk_test_x1' }).mode === 'test');
const refused = {
  'a live key with no switch (test environment)': { ENVIRONMENT: 'test', STRIPE_SECRET_KEY: 'sk_live_x1' },
  'a live key with no switch (production)': { ENVIRONMENT: 'production', STRIPE_SECRET_KEY: 'sk_live_x1' },
  'a live key with the switch "false"': { ENVIRONMENT: 'production', CHECKOUT_LIVE: 'false', STRIPE_SECRET_KEY: 'sk_live_x1' },
  'the switch outside production (test)': { ENVIRONMENT: 'test', CHECKOUT_LIVE: 'true', STRIPE_SECRET_KEY: 'sk_live_x1' },
  'the switch with no ENVIRONMENT': { CHECKOUT_LIVE: 'true', STRIPE_SECRET_KEY: 'sk_live_x1' },
  'the switch in sandbox mode': { ...LIVE, SANDBOX: 'true' },
  'the switch with a Stripe API override': { ...LIVE, STRIPE_API_BASE: 'https://stripe.mock' },
  'the switch with a TEST key': { ...LIVE, STRIPE_SECRET_KEY: 'sk_test_x1' },
  'a TEST key in production (no switch)': { ENVIRONMENT: 'production', STRIPE_SECRET_KEY: 'rk_test_x1' },
  'a switch value that is not exactly true/false': { ...LIVE, CHECKOUT_LIVE: 'TRUE' },
  'a switch value "1"': { ...LIVE, CHECKOUT_LIVE: '1' },
  'no key at all': { ENVIRONMENT: 'production', CHECKOUT_LIVE: 'true' },
  'an unrecognised key': { ...LIVE, STRIPE_SECRET_KEY: 'pk_live_x1' },
};
for (const [why, env] of Object.entries(refused)) check(`L1c refused: ${why}`, !M(env).ok, M(env));
check('L1d the old name testKey is the same gate', S.testKey === S.stripeMode);

console.log('— L2 a refused configuration makes no request; objects of the other mode are refused');
const realFetch = globalThis.fetch;
let calls = 0, reply = {};
globalThis.fetch = async () => { calls++; return new Response(JSON.stringify(reply), { status: 200 }); };
for (const env of [refused['a live key with no switch (production)'], refused['a TEST key in production (no switch)'], refused['the switch outside production (test)']]) {
  calls = 0; let err = null;
  try { await S.getAccount(env, 'acct_1'); } catch (e) { err = e; }
  check(`L2a refused before any request (${env.ENVIRONMENT || 'none'}, ${String(env.STRIPE_SECRET_KEY).slice(0, 8)})`, calls === 0 && err && err.code === 'not_configured', err && err.message);
}
const got = async (env, livemode) => { reply = { id: 'acct_1', object: 'account', livemode }; try { await S.getAccount(env, 'acct_1'); return 'ok'; } catch (e) { return e.code; } };
check('L2b live mode accepts live objects and refuses test objects', await got(LIVE, true) === 'ok' && await got(LIVE, false) === 'livemode');
check('L2c test mode accepts test objects and refuses live objects (as before)', await got(TEST, false) === 'ok' && await got(TEST, true) === 'livemode');
globalThis.fetch = realFetch;

console.log('— L3 signed webhooks: each mode accepts only its own events; nothing is recorded before the check');
const WH = 'whsec_testsecret';
const signed = ev => { const raw = JSON.stringify(ev), t = Math.floor(Date.now() / 1000); return [raw, `t=${t},v1=${createHmac('sha256', WH).update(`${t}.${raw}`).digest('hex')}`]; };
const noDb = { prepare() { throw new Error('the database must not be touched'); } };
const hook = async (env, livemode) => { const [raw, sig] = signed({ id: 'evt_1', type: 'checkout.session.completed', livemode, data: { object: {} } }); return C.webhook({ ...env, STRIPE_WEBHOOK_SECRET: WH, DB: noDb }, raw, sig); };
check('L3a a live-mode Worker refuses a test-mode event (400) without touching the database', (await hook(LIVE, false)).status === 400);
check('L3b a test-mode Worker refuses a live-mode event (400), as before', (await hook(TEST, true)).status === 400);
check('L3c a refused configuration answers 503 to a signed event, so Stripe retries once it is fixed', (await hook(refused['a live key with no switch (production)'], true)).status === 503);
check('L3d an unsigned event is refused in live mode too', (await C.webhook({ ...LIVE, STRIPE_WEBHOOK_SECRET: WH, DB: noDb }, '{"id":"evt_1","livemode":true}', 't=1,v1=00')).status === 400);

console.log('— L4 emails: real recipients only in verified live mode; test-mode wording removed only there');
const mail = { CHECKOUT_MAIL: 'resend', RESEND_API_KEY: 're_x', CHECKOUT_MAIL_FROM: 'PlotArt <orders@plotnua.ie>', CHECKOUT_MAIL_APPROVED: 'true' };
check('L4a live mode with approved Resend sends to real recipients', C.mailMode({ ...LIVE, ...mail }).external_sending && C.mailMode({ ...LIVE, ...mail }).live);
check('L4b live mode without approval sends nothing', !C.mailMode({ ...LIVE, ...mail, CHECKOUT_MAIL_APPROVED: 'false' }).external_sending);
check('L4c a live key without the gate sends nothing', !C.mailMode({ ...mail, ENVIRONMENT: 'production', STRIPE_SECRET_KEY: 'sk_live_x1' }).external_sending);
check('L4d test mode sends only to listed test inboxes, as before', !C.mailMode({ ...TEST, ...mail }).external_sending && C.mailMode({ ...TEST, ...mail, CHECKOUT_MAIL_TEST_RECIPIENTS: 'a@plotnua.ie' }).external_sending);
const msg = { subject: 'Purchase confirmation · Work · PA-O-1', body: 'PURCHASE CONFIRMATION\nTEST MODE: this is a PlotArt payment-pilot test. No real payment was taken and no artwork was sold.\n\nText.\nThis message comes from the PlotArt payment pilot (test mode).' };
const lv = C.modeText(LIVE, msg), tv = C.modeText(TEST, msg), rv = C.modeText(refused['a live key with no switch (production)'], msg);
check('L4e live mode removes the TEST MODE line and the "(test mode)" footer', !/TEST MODE|test mode/.test(lv.body) && lv.body.includes('PURCHASE CONFIRMATION') && lv.body.includes('This message comes from the PlotArt payment pilot.'));
check('L4f test mode and any refused configuration keep the test wording exactly', tv.body === msg.body && rv.body === msg.body && tv.subject === msg.subject);

console.log('— L5 pages and switches report the real mode; the buyer page banner is removed only in live mode');
check('L5a switches: live, test or refused, never assumed', C.switches({ ...LIVE, CHECKOUT_PILOT_ENABLED: 'true' }).mode === 'live' && C.switches({ ...LIVE, CHECKOUT_PILOT_ENABLED: 'true' }).live
  && C.switches(TEST).mode === 'test' && !C.switches(TEST).live && C.switches(refused['a TEST key in production (no switch)']).mode === 'refused'
  && !C.switches({ ...refused['a TEST key in production (no switch)'], CHECKOUT_PILOT_ENABLED: 'true' }).enabled);
const status = async env => JSON.parse(await (await P.fetch(new Request('https://checkout.example/v1/status'), { ...env, DB: { prepare() { throw new Error('no db'); } } })).text());
check('L5b the public status reports live / test', (await status(LIVE)).mode === 'live' && (await status(TEST)).mode === 'test');
const pub = readFileSync(HERE + 'src/checkout-public.js', 'utf8');
check('L5c the buyer page uses the banner only through the live gate', /const banner = env => \{ const m = S\.stripeMode\(env\); return m\.ok && m\.live \? '' : TEST_BANNER_HTML; \};/.test(pub) && !/\$\{TEST_BANNER\}|TEST_BANNER \+/.test(pub));

console.log('— L6 database: accounts, orders and events of the other mode are never used');
const db = new DatabaseSync(':memory:');
db.exec(readFileSync(HERE + 'migrations/0017_managed_checkout_pilot.sql', 'utf8'));
const D1 = { prepare(sql) { const stmt = db.prepare(sql); let args = []; const o = { bind(...a) { args = a; return o; }, first: async () => stmt.get(...args) ?? null, all: async () => ({ results: stmt.all(...args) }), run: async () => { const r = stmt.run(...args); return { meta: { changes: r.changes } }; } }; return o; } };
db.exec("INSERT INTO payment_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES ('PA-PAY-X','artist_payment_addendum','t','" + 'a'.repeat(64) + "','2026-01-01','2026-01-01')");
for (const [a, lm] of [['art_test', 0], ['art_live', 1]]) {
  db.exec(`INSERT INTO payment_pilot_events (id, artist_id, kind, doc_id, doc_sha256, account_email, display_name, statement, at) VALUES ('e_${a}','${a}','opted_in','PA-PAY-X','${'a'.repeat(64)}','${a}@example.test','A','I agree','2026-01-01')`);
  db.exec(`INSERT INTO payment_accounts (artist_id, account_id, country, livemode, charges_enabled, payouts_enabled, details_submitted, created_at, updated_at) VALUES ('${a}','acct_${a}','IE',${lm},1,1,1,'2026-01-01','2026-01-01')`);
}
const ready = async (env, a) => (await C.membership({ ...env, DB: D1 }, a)).ready;
check('L6a a TEST account is ready only in test mode; a LIVE account only in live mode', await ready(TEST, 'art_test') && !(await ready(LIVE, 'art_test')) && await ready(LIVE, 'art_live') && !(await ready(TEST, 'art_live')));
let ck = null; try { db.exec("INSERT INTO payment_events (event_id, type, livemode, created, status, received_at) VALUES ('evt_9','x',2,0,'received','t')"); } catch (e) { ck = e; }
check('L6b livemode can only be 0 (test) or 1 (live)', !!ck);
const src = readFileSync(HERE + 'src/checkout.js', 'utf8');
check('L6c orders, accounts and events record the mode from the gate, and an order of the other mode cannot be paid',
  /INSERT INTO checkout_orders \([^)]*livemode/.test(src) && /INSERT INTO payment_accounts \(artist_id, account_id, country, livemode/.test(src)
  && src.includes("VALUES (?,?,?,?,?,?, 'received', ?)") && src.includes('This quote was prepared in the other Stripe mode and cannot be paid here'));

console.log('— L7 configuration: live only through the explicit production path; TEST never carries it');
const tmp = mkdtempSync(join(tmpdir(), 'pa-live-'));
cpSync(HERE, tmp + '/w', { recursive: true, filter: s => !s.includes('node_modules') && !s.includes('.checkout-fixture') });
const render = (target, extra) => { try { return { ok: true, out: execFileSync('python3', [ROOT + 'atlas-tools/release/studio/render-checkout-config.py', tmp + '/w', target], { env: { ...process.env, ...extra }, encoding: 'utf8', stdio: 'pipe' }) }; } catch (e) { return { ok: false, out: String(e.stdout) + String(e.stderr) }; } };
const prodEnv = { STUDIO_D1_DATABASE_ID: '00000000-0000-0000-0000-000000000000', CHECKOUT_PRODUCTION_ORIGIN: 'https://plotart-checkout.example.workers.dev', CHECKOUT_LIVE_MAIL_FROM: 'PlotArt <orders@plotnua.ie>', CHECKOUT_LIVE_NOTIFY_EMAIL: 'hello@plotnua.ie' };
const toml = () => readFileSync(tmp + '/w/wrangler.checkout.production.toml', 'utf8');
let r = render('production', prodEnv);
check('L7a production by default: pilot OFF and no live switch', r.ok && /CHECKOUT_PILOT_ENABLED = "false"/.test(toml()) && !/^CHECKOUT_LIVE\s*=/m.test(toml()), r.out);
r = render('production', { ...prodEnv, ENABLE_LIVE_PILOT: 'true' });
check('L7b live without the confirmation phrase is refused', !r.ok && /exact confirmation phrase/.test(r.out));
r = render('production', { ...prodEnv, ENABLE_LIVE_PILOT: 'true', LIVE_CONFIRMATION: 'enable live plotart checkout' });
check('L7c a wrong-case phrase is refused', !r.ok);
r = render('production', { ...prodEnv, ENABLE_LIVE_PILOT: 'true', LIVE_CONFIRMATION: 'ENABLE LIVE PLOTART CHECKOUT' });
check('L7d with both: pilot ON, CHECKOUT_LIVE true, live email approved, founder alerts addressed, no test settings', r.ok && /CHECKOUT_PILOT_ENABLED = "true"/.test(toml()) && /CHECKOUT_LIVE = "true"/.test(toml())
  && /CHECKOUT_MAIL_APPROVED = "true"/.test(toml()) && /CHECKOUT_NOTIFY_EMAIL = "hello@plotnua.ie"/.test(toml()) && !/TEST_RECIPIENTS|SANDBOX|STRIPE_API_BASE/.test(toml()), r.out);
const testEnv = { CHECKOUT_TEST_D1_DATABASE_ID: '11111111-1111-1111-1111-111111111111', CHECKOUT_TEST_ACCESS_AUD: 'a'.repeat(64), CHECKOUT_TEST_ACCESS_TEAM: 'https://x.cloudflareaccess.com', CHECKOUT_TEST_ORIGIN: 'https://plotart-checkout-test.example.workers.dev', ENABLE_TEST_PILOT: 'true' };
r = render('test', testEnv);
const tt = r.ok ? readFileSync(tmp + '/w/wrangler.checkout.test.toml', 'utf8') + readFileSync(tmp + '/w/wrangler.studio.test.toml', 'utf8') : '';
check('L7e the TEST configuration is unchanged by this gate: no live switch, sandbox Studio, test database', r.ok && !/^CHECKOUT_LIVE\s*=/m.test(tt) && /SANDBOX = "true"/.test(tt) && /plotart-checkout-test/.test(tt), r.out);
r = render('test', { ...testEnv, ENABLE_LIVE_PILOT: 'true', LIVE_CONFIRMATION: 'ENABLE LIVE PLOTART CHECKOUT' });
check('L7f live can never be enabled for the TEST environment', !r.ok && /never be enabled in the TEST environment/.test(r.out));
// the Studio production configuration (render-config.py): off by default; live only by a complete checkout_live block
const studio = (prodJson) => { if (prodJson) require_write(tmp + '/w/production.json', prodJson); try { return { ok: true, out: execFileSync('python3', [ROOT + 'atlas-tools/release/studio/render-config.py', tmp + '/w'], { env: { ...process.env, STUDIO_D1_DATABASE_ID: '22222222-2222-2222-2222-222222222222', STUDIO_ACCESS_AUD: 'b'.repeat(64), STUDIO_ACCESS_TEAM: 'https://y.cloudflareaccess.com' }, encoding: 'utf8', stdio: 'pipe' }) }; } catch (e) { return { ok: false, out: String(e.stdout) + String(e.stderr) }; } };
const { writeFileSync } = await import('node:fs');
function require_write(f, o) { writeFileSync(f, JSON.stringify(o, null, 2)); }
const base = JSON.parse(readFileSync(HERE + 'production.json', 'utf8'));
const st = () => readFileSync(tmp + '/w/wrangler.production.toml', 'utf8');
r = studio(base);
check('L7g Studio production as committed: pilot OFF, no live switch', r.ok && /CHECKOUT_PILOT_ENABLED = "false"/.test(st()) && !/^CHECKOUT_LIVE\s*=/m.test(st()), r.out);
check('L7h production.json as committed has no checkout_live block', !('checkout_live' in base));
r = studio({ ...base, vars: { ...base.vars, CHECKOUT_PILOT_ENABLED: 'true' } });
check('L7i switching the pilot on through production.json vars is refused', !r.ok && /only by its checkout_live block/.test(r.out));
r = studio({ ...base, vars: { ...base.vars, CHECKOUT_LIVE: 'true' } });
check('L7j setting CHECKOUT_LIVE through vars is refused', !r.ok);
const block = { confirmation: 'ENABLE LIVE PLOTART CHECKOUT', checkout_origin: 'https://plotart-checkout.example.workers.dev', mail_from: 'PlotArt <orders@plotnua.ie>', notify_email: 'hello@plotnua.ie' };
r = studio({ ...base, checkout_live: { ...block, confirmation: 'yes' } });
check('L7k a checkout_live block without the exact phrase is refused', !r.ok);
r = studio({ ...base, checkout_live: { ...block, checkout_origin: 'https://plotart-checkout-test.example.workers.dev' } });
check('L7l a TEST checkout origin is refused for production', !r.ok);
r = studio({ ...base, checkout_live: block });
check('L7m a complete block: pilot ON, CHECKOUT_LIVE true, live email, production origin', r.ok && /CHECKOUT_PILOT_ENABLED = "true"/.test(st()) && /CHECKOUT_LIVE = "true"/.test(st()) && /CHECKOUT_ORIGIN = "https:\/\/plotart-checkout\.example/.test(st()), r.out);
rmSync(tmp, { recursive: true, force: true });

console.log('— L8 the protected workflow: live is explicit, production-only, approved, and checks credentials');
const wf = readFileSync(ROOT + '.github/workflows/plotart-checkout-deploy.yml', 'utf8');
check('L8a enable_live_pilot defaults to false and needs the typed confirmation', /enable_live_pilot:\n[\s\S]*?default: false/.test(wf) && wf.includes('[ "$LIVE_CONFIRMATION" != "ENABLE LIVE PLOTART CHECKOUT" ]'));
check('L8b live is refused for the test target and without the issued texts', wf.includes('live checkout can be enabled only for the production target') && wf.includes('live checkout needs the issued payment texts'));
check('L8c every production run still waits for the studio-production. environment approval; test keeps checkout-test', wf.includes("environment: ${{ inputs.target == 'production' && 'studio-production.' || 'checkout-test' }}"));
check('L8d LIVE credentials are checked (live keys only, never the TEST values) before they are written', (p => p.includes('check-stripe-live-secrets.sh') && p.indexOf('check-stripe-live-secrets.sh') < p.indexOf('bash atlas-tools/release/studio/checkout-live-enable.sh'))(wf.split('# ---------------------------------------------------------------- PRODUCTION')[1] || ''));
check('L8e the guard requires the production-only gate in the committed code', wf.includes('Live checkout can be enabled only in the production environment') && wf.includes('a Stripe TEST key is refused in production'));
const chk = (vars) => { try { execFileSync('bash', [ROOT + 'atlas-tools/release/studio/check-stripe-live-secrets.sh'], { env: { PATH: process.env.PATH, ...vars }, stdio: 'pipe' }); return true; } catch { return false; } };
const good = { LIVE_STUDIO_KEY: 'sk_live_a1', LIVE_RUNTIME_KEY: 'rk_live_b2', LIVE_WEBHOOK_SECRET: 'whsec_c3', LIVE_RESEND_KEY: 're_d4' };
check('L8f the live credentials check passes live values and refuses test values or a reused TEST secret',
  chk(good) && !chk({ ...good, LIVE_RUNTIME_KEY: 'rk_test_b2' }) && !chk({ ...good, LIVE_STUDIO_KEY: 'sk_test_a1' }) && !chk({ ...good, LIVE_WEBHOOK_SECRET: '' })
  && !chk({ ...good, TEST_WEBHOOK_SECRET: 'whsec_c3' }));

console.log('— L9 committed defaults: the pilot ships OFF everywhere');
check('L9a wrangler.toml and wrangler.checkout.toml ship CHECKOUT_PILOT_ENABLED = "false" and no CHECKOUT_LIVE', /^CHECKOUT_PILOT_ENABLED = "false"/m.test(readFileSync(HERE + 'wrangler.toml', 'utf8'))
  && /^CHECKOUT_PILOT_ENABLED = "false"/m.test(readFileSync(HERE + 'wrangler.checkout.toml', 'utf8')) && !/^CHECKOUT_LIVE\s*=/m.test(readFileSync(HERE + 'wrangler.toml', 'utf8') + readFileSync(HERE + 'wrangler.checkout.toml', 'utf8')));
check('L9b the issued payment texts are present for the live-path guard, but nothing ships live: the defaults above stay OFF and live still needs enable_live_pilot, its confirmation and the founder approval',
  existsSync(HERE + 'agreements/payment-issued/fingerprints.json') && /enable_live_pilot:\n[\s\S]*?default: false/.test(wf) && wf.includes('ENABLE LIVE PLOTART CHECKOUT'));

console.log(`LIVE GATE · ${pass + fail} checks, ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
