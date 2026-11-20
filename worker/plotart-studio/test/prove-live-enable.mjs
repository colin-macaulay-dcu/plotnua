// PlotArt managed checkout · LIVE enablement is fail-closed (20 Nov 2026, PR #38 review).
//   node test/prove-live-enable.mjs
// Runs atlas-tools/release/studio/checkout-live-enable.sh against a STUB wrangler that records every deployment and secret,
// and fails on demand at each stage (including half-way through writing the secrets). Nothing reaches Cloudflare or Stripe.
import { mkdtempSync, writeFileSync, readFileSync, existsSync, rmSync, chmodSync, mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = join(dirname(fileURLToPath(import.meta.url)), '..') + '/';
const SCRIPT = join(HERE, '..', '..', 'atlas-tools/release/studio/checkout-live-enable.sh');
let pass = 0, fail = 0;
const check = (n, ok, info) => { ok ? pass++ : fail++; console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${ok || info === undefined ? '' : '  ' + String(info).slice(0, 500)}`); };

// the stub wrangler: state in $STATE; FAIL_ON lists stages to fail ("deploy:on", "deploy:off", "deploy:off:recovery",
// "put:checkout:RESEND_API_KEY", "put:studio:STRIPE_SECRET_KEY", "list:checkout", "delete:studio"); DROP_CHECKOUT drops a
// name from the checkout Worker's secret list (a write that "succeeded" but did not stick)
const STUB = `#!/usr/bin/env bash
S="$STATE"; echo "$*" >> "$S/log"
has() { [[ " $FAIL_ON " == *" $1 "* ]]; }
tgt() { for a in "$@"; do [ "$a" = plotart-studio ] && { echo studio; return; }; done; echo checkout; }
case "$1 $2" in
  "deploy --config")
    kind=on; [[ "$3" == *off.toml ]] && kind=off
    if [ "$kind" = off ]; then c=$(( $(cat "$S/offcount" 2>/dev/null || echo 0) + 1 )); echo $c > "$S/offcount"
      [ $c = 1 ] && has deploy:off && exit 1          # the first OFF deploy (step 1) fails
      [ $c -ge 2 ] && has deploy:off:recovery && exit 1; fi   # the recovery's OFF deploy fails
    [ "$kind" = on ] && has deploy:on && exit 1
    echo "$kind" > "$S/deployed"; echo "Current Version ID: v-$kind"; exit 0 ;;
  "secret put")
    t=$(tgt "$@"); cat > /dev/null; has "put:$t:$3" && exit 1
    grep -qx "$3" "$S/$t" 2>/dev/null || echo "$3" >> "$S/$t"; echo "$3" >> "$S/writes-$t"; exit 0 ;;
  "secret delete")
    t=$(tgt "$@"); has "delete:$t" && exit 1; grep -vx "$3" "$S/$t" > "$S/$t.n" 2>/dev/null; mv "$S/$t.n" "$S/$t"; exit 0 ;;
  "secret list")
    t=$(tgt "$@"); has "list:$t" && exit 1
    python3 -c 'import json,sys; n=[l.strip() for l in open(sys.argv[1]) if l.strip()] if __import__("os").path.exists(sys.argv[1]) else []; d=sys.argv[2]; print(json.dumps([{"name":x,"type":"secret_text"} for x in n if x!=d]))' "$S/$t" "$([ "$t" = checkout ] && echo "$DROP_CHECKOUT")"; exit 0 ;;
esac
exit 3
`;
const OUT = `#!/usr/bin/env bash
S="$STATE"; echo "outside $2" >> "$S/log"
[[ " $FAIL_ON " == *" outside:$2 "* ]] && exit 1
d=$(cat "$S/deployed" 2>/dev/null); [ "$2" = live ] && [ "$d" = on ] && exit 0; [ "$2" = off ] && [ "$d" = off ] && exit 0; exit 1
`;
const GOOD = { LIVE_RUNTIME_KEY: 'rk_live_r1', LIVE_WEBHOOK_SECRET: 'whsec_w1', LIVE_RESEND_KEY: 're_m1', LIVE_STUDIO_KEY: 'sk_live_s1', ORIGIN: 'https://plotart-checkout.example.workers.dev' };

function run(name, { failOn = '', drop = '', env = {}, preStudio = [], preCheckout = [], preDeployed = 'on' } = {}) {
  const T = mkdtempSync(join(tmpdir(), 'pa-live-en-')), S = T + '/state', W = T + '/w';
  mkdirSync(S); mkdirSync(W);
  writeFileSync(T + '/wrangler', STUB); chmodSync(T + '/wrangler', 0o755);
  writeFileSync(T + '/outside', OUT); chmodSync(T + '/outside', 0o755);
  writeFileSync(W + '/wrangler.checkout.production.off.toml', 'name = "plotart-checkout"\n[vars]\nENVIRONMENT = "production"\nCHECKOUT_PILOT_ENABLED = "false"\n');
  writeFileSync(W + '/wrangler.checkout.production.toml', 'name = "plotart-checkout"\n[vars]\nENVIRONMENT = "production"\nCHECKOUT_PILOT_ENABLED = "true"\nCHECKOUT_LIVE = "true"\n');
  writeFileSync(S + '/studio', ['RESEND_API_KEY', ...preStudio].join('\n') + '\n');   // the Studio already has its email key
  if (preCheckout.length) writeFileSync(S + '/checkout', preCheckout.join('\n') + '\n');
  writeFileSync(S + '/deployed', preDeployed);
  const r = spawnSync('bash', [SCRIPT, W], { encoding: 'utf8', env: { PATH: process.env.PATH, STATE: S, FAIL_ON: failOn, DROP_CHECKOUT: drop, WRANGLER: T + '/wrangler', OUTSIDE_CHECK: T + '/outside',
    RECOVERY_WAIT: '0', LIVE_WAIT: '0', RUNNER_TEMP: T, ...GOOD, ...env } });
  const rd = f => existsSync(S + '/' + f) ? readFileSync(S + '/' + f, 'utf8') : '';
  const state = { code: r.status, out: r.stdout + r.stderr, log: rd('log').trim().split('\n'), deployed: rd('deployed').trim(),
    studio: rd('studio').trim().split('\n').filter(Boolean), checkout: rd('checkout').trim().split('\n').filter(Boolean), writesC: rd('writes-checkout').trim().split('\n').filter(Boolean), writesS: rd('writes-studio').trim().split('\n').filter(Boolean) };
  rmSync(T, { recursive: true, force: true });
  return state;
}
const onDeployIdx = st => st.log.findIndex(l => /^deploy --config wrangler\.checkout\.production\.toml$/.test(l));
const safe = st => st.code !== 0 && st.deployed === 'off' && !st.studio.includes('STRIPE_SECRET_KEY') && /RECOVERED: live checkout is OFF/.test(st.out);

console.log('— E1 success: live is enabled last, only after every secret is written and verified');
let st = run('ok');
const i = k => st.log.findIndex(l => l.startsWith(k));
check('E1a exit 0; the Worker is live; both Workers hold their secrets', st.code === 0 && st.deployed === 'on' && ['RESEND_API_KEY', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET'].every(n => st.checkout.includes(n)) && st.studio.includes('STRIPE_SECRET_KEY'), st.out);
check('E1b order: OFF deploy → 4 secret writes → secret lists → the single LIVE deploy → outside check (live)',
  st.log[0] === 'deploy --config wrangler.checkout.production.off.toml' && st.log.filter(l => l.startsWith('secret put')).length === 4
  && i('secret put') > 0 && i('secret list') > st.log.map((l, k) => l.startsWith('secret put') ? k : -1).reduce((a, b) => Math.max(a, b)) && onDeployIdx(st) > i('secret list')
  && st.log[st.log.length - 1] === 'outside live' && st.log.filter(l => /production\.toml$/.test(l) && l.startsWith('deploy')).length === 1, st.log.join(' | '));
st = run('stale', { preStudio: ['STRIPE_SECRET_KEY'], preCheckout: ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'RESEND_API_KEY'] });
check('E1c secrets already present from an earlier run are all written again (none is left stale)', st.code === 0 && st.writesC.length === 3 && st.writesS.length === 1, st.out);

console.log('— E2 every failure recovers to OFF: checkout redeployed OFF, the Studio live key removed, OFF verified from outside');
const cases = {
  'the OFF deployment fails (a live version may still be running)': { failOn: 'deploy:off' },
  'the first secret write fails': { failOn: 'put:checkout:STRIPE_SECRET_KEY' },
  'PARTIAL: two checkout secrets written, the third (email key) fails': { failOn: 'put:checkout:RESEND_API_KEY' },
  'PARTIAL: all checkout secrets written, the Studio key fails': { failOn: 'put:studio:STRIPE_SECRET_KEY' },
  'a credential is empty (missing in the environment)': { env: { LIVE_WEBHOOK_SECRET: '' } },
  'a write reports success but the secret is not there (verification)': { drop: 'STRIPE_WEBHOOK_SECRET' },
  'the secret list cannot be read (verification)': { failOn: 'list:checkout' },
  'the Studio has no email key (verification)': { studioNoEmail: true },
  'the LIVE deployment fails': { failOn: 'deploy:on' },
  'the outside check of live mode fails after the LIVE deployment': { failOn: 'outside:live' },
};
for (const [why, c] of Object.entries(cases)) {
  let s2;
  if (c.studioNoEmail) s2 = runNoStudioEmail();   // the Studio starts with no email key
  else s2 = run(why, c);
  check(`E2 ${why}: run FAILS, checkout ends OFF, no Studio live key, OFF verified`, safe(s2), `${s2.code} ${s2.deployed} [${s2.studio}] ${s2.out}`);
  if (!/LIVE deployment fails|outside check of live/.test(why)) check(`E2 ${why}: the LIVE configuration was never deployed`, onDeployIdx(s2) === -1, s2.log.join(' | '));
}
function runNoStudioEmail() {
  // same as run(), but the Studio starts with no secrets at all
  const T = mkdtempSync(join(tmpdir(), 'pa-live-en-')), S = T + '/state', W = T + '/w';
  mkdirSync(S); mkdirSync(W);
  writeFileSync(T + '/wrangler', STUB); chmodSync(T + '/wrangler', 0o755);
  writeFileSync(T + '/outside', OUT); chmodSync(T + '/outside', 0o755);
  writeFileSync(W + '/wrangler.checkout.production.off.toml', 'name = "plotart-checkout"\n[vars]\nCHECKOUT_PILOT_ENABLED = "false"\n');
  writeFileSync(W + '/wrangler.checkout.production.toml', 'name = "plotart-checkout"\n[vars]\nCHECKOUT_PILOT_ENABLED = "true"\nCHECKOUT_LIVE = "true"\n');
  writeFileSync(S + '/deployed', 'off');
  const r = spawnSync('bash', [SCRIPT, W], { encoding: 'utf8', env: { PATH: process.env.PATH, STATE: S, FAIL_ON: '', DROP_CHECKOUT: '', WRANGLER: T + '/wrangler', OUTSIDE_CHECK: T + '/outside', RECOVERY_WAIT: '0', LIVE_WAIT: '0', RUNNER_TEMP: T, ...GOOD } });
  const rd = f => existsSync(S + '/' + f) ? readFileSync(S + '/' + f, 'utf8') : '';
  const out = { code: r.status, out: r.stdout + r.stderr, log: rd('log').trim().split('\n'), deployed: rd('deployed').trim(), studio: rd('studio').trim().split('\n').filter(Boolean) };
  rmSync(T, { recursive: true, force: true });
  return out;
}

console.log('— E3 a recovery that cannot be verified says so plainly and still fails the run');
st = run('rec-fail', { failOn: 'deploy:on deploy:off:recovery' });
check('E3a LIVE deploy fails AND the OFF redeploy fails: "RECOVERY NOT VERIFIED" with the manual steps; the run fails', st.code !== 0 && /RECOVERY NOT VERIFIED/.test(st.out) && !/RECOVERED:/.test(st.out), st.out);
st = run('del-fail', { failOn: 'put:checkout:RESEND_API_KEY delete:studio', preStudio: ['STRIPE_SECRET_KEY'] });
check('E3b the Studio key cannot be removed: reported, recovery NOT claimed as verified, the run fails', st.code !== 0 && /STILL holds a Stripe key/.test(st.out) && /RECOVERY NOT VERIFIED/.test(st.out), st.out);

console.log('— E4 the script refuses wrong configuration files before touching anything');
{
  const T = mkdtempSync(join(tmpdir(), 'pa-live-en-')), W = T + '/w'; mkdirSync(W); mkdirSync(T + '/state');
  writeFileSync(T + '/wrangler', STUB); chmodSync(T + '/wrangler', 0o755);
  writeFileSync(W + '/wrangler.checkout.production.off.toml', '[vars]\nCHECKOUT_PILOT_ENABLED = "true"\nCHECKOUT_LIVE = "true"\n');
  writeFileSync(W + '/wrangler.checkout.production.toml', '[vars]\nCHECKOUT_PILOT_ENABLED = "true"\nCHECKOUT_LIVE = "true"\n');
  const r = spawnSync('bash', [SCRIPT, W], { encoding: 'utf8', env: { PATH: process.env.PATH, STATE: T + '/state', WRANGLER: T + '/wrangler', OUTSIDE_CHECK: 'true', ...GOOD } });
  check('E4a an "OFF" file that is actually live is refused, with no deployment or secret write', r.status !== 0 && !existsSync(T + '/state/log'), r.stdout);
  rmSync(T, { recursive: true, force: true });
}

console.log('— E5 the workflow uses this path, after the approval and the credentials check');
const wf = readFileSync(join(HERE, '..', '..', '.github/workflows/plotart-checkout-deploy.yml'), 'utf8');
const prod = wf.split('# ---------------------------------------------------------------- PRODUCTION')[1];
check('E5a the only production secret writes are inside checkout-live-enable.sh (no inline secret put in production)', !/secret put/.test(prod) && prod.includes('bash atlas-tools/release/studio/checkout-live-enable.sh worker/plotart-studio'));
check('E5b the credentials check runs before the enable step; the plain OFF deploy and its rollback are not used on the live path',
  prod.indexOf('check-stripe-live-secrets.sh') < prod.indexOf('checkout-live-enable.sh') && /deploy plotart-checkout \(pilot off\)\n\s+id: prod_deploy\n\s+if: \$\{\{ inputs\.target == 'production' && !inputs\.dry_run && !inputs\.enable_live_pilot \}\}/.test(prod));
check('E5c the OFF configuration is always rendered and kept for the live path and its recovery', prod.includes('cp worker/plotart-studio/wrangler.checkout.production.toml worker/plotart-studio/wrangler.checkout.production.off.toml'));
check('E5d the protected approval is unchanged: production runs in the studio-production. environment', wf.includes("environment: ${{ inputs.target == 'production' && 'studio-production.' || 'checkout-test' }}"));

console.log(`LIVE ENABLEMENT FAIL-CLOSED · ${pass + fail} checks, ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
