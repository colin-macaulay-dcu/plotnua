// PROVE · managed checkout pilot · deployment tooling (development 16 Nov 2026). Local only: nothing is sent to Cloudflare
// or Stripe. Covers the configuration renderer (test vs production separation), the Stripe test-credential guard, the
// build-time guard on TEST ONLY texts, the outside check against local Workers (pilot off and on), the test-database seed
// on a database built exactly as the setup instructions say, and the workflow's guards.
//   node test/prove-checkout-deploy.mjs [--wrangler]   (--wrangler also runs `wrangler deploy --dry-run` builds; needs npm)
import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync, rmSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { statements } from './sql.mjs';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');
const HERE = new URL('..', import.meta.url).pathname, ROOT = HERE + '../../', TOOLS = ROOT + 'atlas-tools/release/studio/';
const results = []; const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 500)}]` : ''}`); };
const py = (target, env) => spawnSync('python3', [TOOLS + 'render-checkout-config.py', HERE, target], { env: { PATH: process.env.PATH, ...env }, encoding: 'utf8' });
const toml = f => readFileSync(HERE + f, 'utf8');
const clean = () => ['wrangler.checkout.test.toml', 'wrangler.studio.test.toml', 'wrangler.checkout.production.toml'].forEach(f => rmSync(HERE + f, { force: true }));
const PROD_DB = '11111111-2222-4333-8444-555555555555', TEST_DB = '99999999-8888-4777-8666-555555555555';
const TEST_ENV = { CHECKOUT_TEST_D1_DATABASE_ID: TEST_DB, CHECKOUT_TEST_ACCESS_AUD: 'a'.repeat(64), CHECKOUT_TEST_ACCESS_TEAM: 'https://plotnua-test.cloudflareaccess.com',
  CHECKOUT_TEST_ORIGIN: 'https://plotart-checkout-test.example.workers.dev', ENABLE_TEST_PILOT: 'true', STUDIO_D1_DATABASE_ID: PROD_DB };
console.log('PROVE · checkout pilot deployment tooling');

console.log('— configuration renderer');
clean();
let r = py('production', { STUDIO_D1_DATABASE_ID: PROD_DB, CHECKOUT_PRODUCTION_ORIGIN: 'https://plotart-checkout.example.workers.dev' });
let t = r.status === 0 ? toml('wrangler.checkout.production.toml') : '';
check('P1 production renders plotart-checkout on the production database with the pilot OFF', r.status === 0 && /^name = "plotart-checkout"$/m.test(t) && /CHECKOUT_PILOT_ENABLED = "false"/.test(t) && t.includes(PROD_DB) && !r.stdout.includes(PROD_DB), r.stderr + r.stdout);
r = py('production', { STUDIO_D1_DATABASE_ID: PROD_DB, CHECKOUT_PRODUCTION_ORIGIN: 'https://x.example', ENABLE_TEST_PILOT: 'true' });
check('P2 production refuses to switch the pilot on', r.status !== 0 && /cannot be switched on/.test(r.stderr));
r = py('production', { CHECKOUT_PRODUCTION_ORIGIN: 'https://x.example' });
check('P3 production refuses without its database identifier', r.status !== 0 && /STUDIO_D1_DATABASE_ID/.test(r.stderr));
r = py('test', TEST_ENV);
const ct = r.status === 0 ? toml('wrangler.checkout.test.toml') : '', stt = r.status === 0 ? toml('wrangler.studio.test.toml') : '';
check('P4 test renders separate Workers, the TEST database and the pilot switch as asked', r.status === 0 && /^name = "plotart-checkout-test"$/m.test(ct) && /^name = "plotart-studio-test"$/m.test(stt)
  && /database_name = "plotart-checkout-test"/.test(ct) && /database_name = "plotart-checkout-test"/.test(stt) && ct.includes(TEST_DB) && !ct.includes(PROD_DB) && !stt.includes(PROD_DB)
  && /CHECKOUT_PILOT_ENABLED = "true"/.test(ct), r.stderr);
for (const [n, ok] of Object.entries({ buckets: /plotart-studio-test-images/.test(stt) && /plotart-studio-test-applications/.test(stt), noProdBuckets: !/bucket_name = "plotart-(studio-images|applications)"/.test(stt), mailer: /MAILER = "none"/.test(stt), instant: /INSTANT_AUTOPUBLISH = "false"/.test(stt), register: !/APPLICATION_REGISTER/.test(stt), env: /ENVIRONMENT = "test"/.test(stt), aud: stt.includes('a'.repeat(64)) })) if (!ok) console.log('    P5 detail failing:', n);
check('P5 the test Studio has test buckets, its own Access application, no email, no instant publishing, no register binding, no production identifiers',
  /plotart-studio-test-images/.test(stt) && /plotart-studio-test-applications/.test(stt) && !/bucket_name = "plotart-(studio-images|applications)"/.test(stt) && /MAILER = "none"/.test(stt)
  && /INSTANT_AUTOPUBLISH = "false"/.test(stt) && !/APPLICATION_REGISTER/.test(stt) && /ENVIRONMENT = "test"/.test(stt) && stt.includes('a'.repeat(64)));
r = py('test', { ...TEST_ENV, CHECKOUT_TEST_D1_DATABASE_ID: PROD_DB });
check('P6 test refuses the production database', r.status !== 0 && /must not be the production database/.test(r.stderr));
r = py('test', { ...TEST_ENV, CHECKOUT_TEST_ORIGIN: 'https://plotart-checkout.example.workers.dev' });
check('P7 test refuses a non-test checkout origin', r.status !== 0);
check('P8 the shipped configurations keep the pilot off', /^CHECKOUT_PILOT_ENABLED = "false"/m.test(toml('wrangler.checkout.toml')) && /^CHECKOUT_PILOT_ENABLED = "false"/m.test(toml('wrangler.toml'))
  && !/CHECKOUT_PILOT_ENABLED/.test(toml('production.json')));

console.log('— Stripe credential guard');
const g = env => spawnSync('bash', [TOOLS + 'check-stripe-test-secrets.sh'], { env: { PATH: process.env.PATH, ...env }, encoding: 'utf8' });
const live = 'sk_live_' + 'Z'.repeat(24), test = 'sk_test_' + 'Y'.repeat(24), wh = 'whsec_' + 'X'.repeat(24);
r = g({ STRIPE_SECRET_KEY: live, STRIPE_WEBHOOK_SECRET: wh });
check('S1 a live key is refused, and its value is never printed', r.status !== 0 && !r.stdout.includes(live) && !r.stdout.includes(wh));
check('S2 a test key and signing secret pass', g({ STRIPE_SECRET_KEY: test, STRIPE_WEBHOOK_SECRET: wh }).status === 0 && g({ STRIPE_SECRET_KEY: 'rk_test_abc', STRIPE_WEBHOOK_SECRET: wh }).status === 0);
check('S3 a missing signing secret is refused', g({ STRIPE_SECRET_KEY: test }).status !== 0);

console.log('— build guard on TEST ONLY texts');
const b = env => spawnSync('node', [HERE + 'build-assets.mjs'], { env: { PATH: process.env.PATH, ...env }, encoding: 'utf8' });
check('B1 placeholders build only for the test target', b({ PAYMENT_TERMS_DIR: 'agreements/payment-test' }).status !== 0 && b({ PAYMENT_TERMS_DIR: 'agreements/payment-test', CHECKOUT_TARGET: 'production' }).status !== 0);
r = b({ PAYMENT_TERMS_DIR: 'agreements/payment-test', CHECKOUT_TARGET: 'test' });
const testBuild = readFileSync(HERE + 'src/payment-terms.js', 'utf8');
r = b({});
const normalBuild = readFileSync(HERE + 'src/payment-terms.js', 'utf8');
check('B2 the test build carries the TEST ONLY texts; the normal build carries only the issued texts and no TEST text', testBuild.includes('PA-PAY-TEST-01') && testBuild.includes('TEST ONLY')
  && normalBuild.includes('"PA-PAY-2026-11"') && normalBuild.includes('"PA-BPT-2026-11"') && !normalBuild.includes('TEST ONLY') && !normalBuild.includes('-TEST-'));

console.log('— test database exactly as the setup instructions build it, seeded');
const mf0 = new Miniflare({ modules: true, script: 'export default { fetch() { return new Response("") } }', d1Databases: { DB: 'checkout-test-db' } });
const db0 = await mf0.getD1Database('DB');
for (const s of statements(readFileSync(HERE + 'schema.sql', 'utf8'))) await db0.prepare(s).run();
for (const s of statements(readFileSync(HERE + 'migrations/0013_gallery_artist_agreement_text.sql', 'utf8'))) await db0.prepare(s).run();
r = spawnSync('node', [HERE + 'test/checkout-test-env-seed.mjs', '--target', 'plotart-studio', '--founding', 'a@x.ie', '--gallery', 'b@x.ie'], { encoding: 'utf8' });
check('E1 the seed refuses any database but plotart-checkout-test', r.status !== 0);
const seed = execFileSync('node', [HERE + 'test/checkout-test-env-seed.mjs', '--target', 'plotart-checkout-test', '--founding', 'colin+f1@example.test', '--gallery', 'colin+g1@example.test'], { encoding: 'utf8' });
let seeded = true; try { for (const s of statements(seed)) await db0.prepare(s).run(); } catch (e) { seeded = e.message; }
check('E2 the seed applies cleanly to schema.sql + 0013 (synthetic artists, published galleries, TEST ONLY texts installed)', seeded === true
  && (await db0.prepare("SELECT COUNT(*) AS n FROM payment_terms WHERE doc_id LIKE '%-TEST-%'").first()).n === 2
  && (await db0.prepare("SELECT COUNT(*) AS n FROM publish_queue WHERE status='published'").first()).n === 2
  && (await db0.prepare("SELECT COUNT(*) AS n FROM gallery_agreement_documents").first()).n === 1, seeded);
await mf0.dispose();

console.log('— outside check against local Workers');
for (const mode of ['off', 'on']) {
  const mf = new Miniflare({ modules: true, modulesRoot: HERE, modulesRules: [{ type: 'ESModule', include: ['**/*.js'] }], compatibilityDate: '2026-08-01', scriptPath: HERE + 'src/checkout-public.js',
    d1Databases: { DB: 'oc-' + mode }, port: mode === 'off' ? 8891 : 8892, host: '127.0.0.1',
    bindings: { ENVIRONMENT: 'local', CHECKOUT_PILOT_ENABLED: mode === 'on' ? 'true' : 'false', STRIPE_SECRET_KEY: 'sk_test_x', STRIPE_WEBHOOK_SECRET: wh, CHECKOUT_ORIGIN: 'http://127.0.0.1' } });
  const d = await mf.getD1Database('DB');
  for (const s of statements(readFileSync(HERE + 'schema.sql', 'utf8'))) await d.prepare(s).run();
  const url = (await mf.ready).toString().replace(/\/$/, '');
  r = spawnSync('bash', [TOOLS + 'checkout-outside-check.sh', url, mode], { env: { PATH: process.env.PATH, CHECK_ALLOW_LOCAL: '1' }, encoding: 'utf8' });
  check(`O-${mode} the outside check passes against a ${mode === 'on' ? 'switched-on' : 'switched-off'} Worker`, r.status === 0, r.stdout);
  r = spawnSync('bash', [TOOLS + 'checkout-outside-check.sh', url, mode === 'on' ? 'off' : 'on'], { env: { PATH: process.env.PATH, CHECK_ALLOW_LOCAL: '1' }, encoding: 'utf8' });
  check(`O-${mode}-x the outside check FAILS if the Worker is in the other state`, r.status !== 0);
  await mf.dispose();
}

console.log('— workflow');
const wf = readFileSync(ROOT + '.github/workflows/plotart-checkout-deploy.yml', 'utf8');
let parsed = null; try { parsed = JSON.parse(execFileSync('python3', ['-c', 'import yaml,json,sys; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))', ROOT + '.github/workflows/plotart-checkout-deploy.yml'], { encoding: 'utf8' })); } catch (e) { parsed = String(e.message); }
const ON = parsed && (parsed.on || parsed['true']);   // YAML 1.1 reads the key `on` as true
check('W1 the workflow parses, is manual only and defaults to a TEST dry run', ON && Object.keys(ON).join() === 'workflow_dispatch' && ON.workflow_dispatch.inputs.dry_run.default === true
  && ON.workflow_dispatch.inputs.target.default === 'test' && ON.workflow_dispatch.inputs.enable_test_pilot.default === false, JSON.stringify(parsed).slice(0, 300));
check('W2 it never applies a migration or runs d1 execute', !/d1 (migrations|execute)/.test(wf));
// W3 (20 Nov 2026, live-mode gate; fail-closed after review): production writes no secret inline. The only production
// secret writes are in checkout-live-enable.sh (OFF deploy, secrets, verify, LIVE deploy, recovery), on the live path only,
// after the live credentials check; test keeps its own token and secrets. (Window 900: the step also carries the basket's two
// variables, 21 Nov 2026.)
const PROD = wf.split('# ---------------------------------------------------------------- PRODUCTION')[1] || '';
check('W3 production writes secrets only through the fail-closed live script (live path only, after the live credentials check); test uses its own token and secrets',
  !/secret put/.test(PROD) && !/CHECKOUT_TEST_/.test(PROD) && /if: \$\{\{ inputs\.target == 'production' && !inputs\.dry_run && inputs\.enable_live_pilot \}\}\n[\s\S]{0,900}checkout-live-enable\.sh/.test(PROD)
  && PROD.indexOf('check-stripe-live-secrets.sh') < PROD.indexOf('checkout-live-enable.sh')
  && (wf.match(/CHECKOUT_TEST_STRIPE_SECRET_KEY/g) || []).length >= 2 && /CHECKOUT_TEST_CF_TOKEN/.test(wf));
check('W3b live checkout is off by default and needs the typed confirmation', ON && ON.workflow_dispatch.inputs.enable_live_pilot.default === false
  && wf.includes('[ "$LIVE_CONFIRMATION" != "ENABLE LIVE PLOTART CHECKOUT" ]'));
check('W4 each target waits for approval in its own GitHub environment', /environment: \$\{\{ inputs\.target == 'production' && 'studio-production\.' \|\| 'checkout-test' \}\}/.test(wf));

if (process.argv.includes('--wrangler')) {
  console.log('— wrangler dry-run builds (nothing sent to Cloudflare)');
  py('test', TEST_ENV); py('production', { STUDIO_D1_DATABASE_ID: PROD_DB, CHECKOUT_PRODUCTION_ORIGIN: 'https://plotart-checkout.example.workers.dev' });
  for (const c of ['wrangler.checkout.test.toml', 'wrangler.studio.test.toml', 'wrangler.checkout.production.toml']) {
    const w = spawnSync('npx', ['--yes', 'wrangler@4.150.0', 'deploy', '--config', c, '--dry-run', '--outdir', `/tmp/checkout-build-${c}`], { cwd: HERE, encoding: 'utf8', timeout: 300_000 });
    check(`X ${c} builds`, w.status === 0, (w.stderr || '') .slice(-400));
  }
}
clean();
const passed = results.filter(Boolean).length;
console.log(`\nCHECKOUT DEPLOYMENT TOOLING · ${results.length} checks, ${passed} passed, ${results.length - passed} failed`);
process.exit(passed === results.length ? 0 : 1);
