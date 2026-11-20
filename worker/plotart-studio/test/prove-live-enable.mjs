// PlotArt managed checkout · LIVE enablement and OFF switching are fail-closed (20 Nov 2026, PR #38 reviews 1 and 2).
//   node test/prove-live-enable.mjs
// Runs the REAL scripts exactly as the workflow does (from the repository root, by relative path, with a relative worker
// directory) and the REAL outside check (checkout-outside-check.sh, curl) against a local HTTP server that answers like the
// checkout Worker in whatever state was last deployed. Only wrangler is a stub: it records every deployment and secret and
// fails on demand, including half-way through the secret writes. Nothing reaches Cloudflare or Stripe.
import { mkdtempSync, writeFileSync, readFileSync, existsSync, rmSync, chmodSync, mkdirSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = join(dirname(fileURLToPath(import.meta.url)), '..') + '/';
const ROOT = join(HERE, '..', '..');
let pass = 0, fail = 0;
const check = (n, ok, info) => { ok ? pass++ : fail++; console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${ok || info === undefined ? '' : '  ' + String(info).slice(0, 900)}`); };

// stub wrangler. FAIL_ON: deploy:on deploy:off (first OFF deploy) deploy:off:again (any later OFF deploy) put:<w>:<NAME>
// list:<w> delete:<w>, where <w> is checkout or studio. DROP_CHECKOUT hides a name from the checkout list. A secret put
// records which configuration was deployed at that moment (it must never be "on").
const STUB = `#!/usr/bin/env bash
S="$STATE"; echo "$*" >> "$S/log"
has() { [[ " $FAIL_ON " == *" $1 "* ]]; }
tgt() { local p=""; for a in "$@"; do [ "$p" = --name ] && { [ "$a" = plotart-studio ] && echo studio || echo checkout; return; }; p="$a"; done; echo checkout; }
case "$1 $2" in
  "deploy --config")
    kind=on; grep -q '^CHECKOUT_PILOT_ENABLED = "false"' "$3" && kind=off
    if [ "$kind" = off ]; then c=$(( $(cat "$S/offcount" 2>/dev/null || echo 0) + 1 )); echo $c > "$S/offcount"
      [ $c = 1 ] && has deploy:off && exit 1; [ $c -ge 2 ] && has deploy:off:again && exit 1; fi
    [ "$kind" = on ] && has deploy:on && exit 1
    echo "$kind" > "$S/deployed"; echo "Current Version ID: v-$kind"; exit 0 ;;
  "secret put")
    t=$(tgt "$@"); cat > /dev/null; echo "put $t $3 while=$(cat "$S/deployed")" >> "$S/puts"; has "put:$t:$3" && exit 1
    grep -qx "$3" "$S/$t" 2>/dev/null || echo "$3" >> "$S/$t"; exit 0 ;;
  "secret delete")
    t=$(tgt "$@"); has "delete:$t" && exit 1; touch "$S/$t"; grep -vx "$3" "$S/$t" > "$S/$t.n"; mv "$S/$t.n" "$S/$t"; exit 0 ;;
  "secret list")
    t=$(tgt "$@"); has "list:$t" && exit 1
    python3 -c 'import json,sys,os; n=[l.strip() for l in open(sys.argv[1]) if l.strip()] if os.path.exists(sys.argv[1]) else []; print(json.dumps([{"name":x,"type":"secret_text"} for x in n if x!=sys.argv[2]]))' "$S/$t" "$([ "$t" = checkout ] && echo "$DROP_CHECKOUT")"; exit 0 ;;
esac
exit 3
`;
const GOOD = { LIVE_RUNTIME_KEY: 'rk_live_r1', LIVE_WEBHOOK_SECRET: 'whsec_w1', LIVE_RESEND_KEY: 're_m1', LIVE_STUDIO_KEY: 'sk_live_s1' };
const OFFTOML = 'name = "plotart-checkout"\n[vars]\nENVIRONMENT = "production"\nCHECKOUT_PILOT_ENABLED = "false"\n';
const ONTOML = 'name = "plotart-checkout"\n[vars]\nENVIRONMENT = "production"\nCHECKOUT_PILOT_ENABLED = "true"\nCHECKOUT_LIVE = "true"\n';

// a local server that answers like the checkout Worker in the state last deployed.
// SERVER: 'ok' | 'broken' (500 everywhere) | 'notlive' (pilot on but status reports test mode, e.g. a refused live key)
let STATEDIR = null, SERVER = 'ok';
const server = createServer((req, res) => {
  const send = (code, body = '') => { res.writeHead(code, { 'X-Robots-Tag': 'noindex', 'Content-Type': 'application/json' }); res.end(body); };
  if (SERVER === 'broken') return send(500, '{}');
  const on = (existsSync(STATEDIR + '/deployed') ? readFileSync(STATEDIR + '/deployed', 'utf8').trim() : 'off') === 'on';
  if (req.url === '/v1/status') return send(200, JSON.stringify({ installed: true, pilot_enabled: on, mode: on ? (SERVER === 'notlive' ? 'test' : 'live') : 'refused' }));
  if (req.url.startsWith('/q/')) return send(on ? 404 : 503);
  if (req.url === '/v1/stripe/webhook') return send(req.method === 'POST' ? (on ? 400 : 503) : 405);
  return send(404);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

async function run(script, { failOn = '', drop = '', env = {}, studio = ['RESEND_API_KEY'], checkout = [], deployed = 'on', srv = 'ok', onToml = ONTOML, offToml = OFFTOML, args = null } = {}) {
  const T = mkdtempSync(join(tmpdir(), 'pa-live-en-')), S = T + '/state', W = T + '/w';
  mkdirSync(S); mkdirSync(W);
  writeFileSync(T + '/wrangler', STUB); chmodSync(T + '/wrangler', 0o755);
  writeFileSync(W + '/wrangler.checkout.production.off.toml', offToml);
  writeFileSync(W + '/wrangler.checkout.production.toml', onToml);
  writeFileSync(S + '/studio', studio.join('\n') + (studio.length ? '\n' : ''));
  if (checkout.length) writeFileSync(S + '/checkout', checkout.join('\n') + '\n');
  writeFileSync(S + '/deployed', deployed);
  STATEDIR = S; SERVER = srv;
  const wdRel = relative(ROOT, W);   // a relative worker directory, as in the workflow
  const argv = args || (script === 'enable' ? [wdRel] : [wdRel, 'wrangler.checkout.production.off.toml']);
  const res = await new Promise(resolve => {
    // no OUTSIDE_CHECK override: the scripts resolve and run the real checkout-outside-check.sh themselves
    const p = spawn('bash', [`atlas-tools/release/studio/checkout-live-${script}.sh`, ...argv], { cwd: ROOT,
      env: { PATH: process.env.PATH, STATE: S, FAIL_ON: failOn, DROP_CHECKOUT: drop, WRANGLER: T + '/wrangler', CHECK_ALLOW_LOCAL: '1', ORIGIN,
        LIVE_WAIT: '0', OFF_WAIT: '0', RUNNER_TEMP: T, ...GOOD, ...env } });
    let out = ''; p.stdout.on('data', d => out += d); p.stderr.on('data', d => out += d); p.on('close', code => resolve({ code, out }));
  });
  const rd = f => existsSync(S + '/' + f) ? readFileSync(S + '/' + f, 'utf8') : '';
  const st = { ...res, log: rd('log').trim().split('\n').filter(Boolean), deployed: rd('deployed').trim(), puts: rd('puts').trim().split('\n').filter(Boolean),
    studio: rd('studio').trim().split('\n').filter(Boolean), checkout: rd('checkout').trim().split('\n').filter(Boolean) };
  rmSync(T, { recursive: true, force: true });
  return st;
}
const onDeploys = st => st.log.filter(l => l === 'deploy --config wrangler.checkout.production.toml').length;
const recoveredOff = st => st.code !== 0 && st.deployed === 'off' && !st.studio.includes('STRIPE_SECRET_KEY') && /OFF VERIFIED:/.test(st.out) && !/OFF NOT VERIFIED/.test(st.out);

console.log('— E1 success, with the REAL outside check resolved from the script directory, invoked as in the workflow');
let st = await run('enable');
check('E1a exit 0; LIVE deployed; both Workers hold their secrets; the real outside check confirmed LIVE mode', st.code === 0 && st.deployed === 'on'
  && ['RESEND_API_KEY', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET'].every(n => st.checkout.includes(n)) && st.studio.includes('STRIPE_SECRET_KEY')
  && /PASS  status reports LIVE mode/.test(st.out) && /CHECKOUT OUTSIDE CHECK OK \(on\)/.test(st.out) && /LIVE CHECKOUT ENABLED/.test(st.out), st.out);
check('E1b order: OFF deploy → 4 secret writes → 2 secret lists → the single LIVE deploy', st.log[0] === 'deploy --config wrangler.checkout.production.off.toml'
  && st.log.slice(1, 5).every(l => l.startsWith('secret put')) && st.log.slice(5, 7).every(l => l.startsWith('secret list')) && st.log[7] === 'deploy --config wrangler.checkout.production.toml' && onDeploys(st) === 1 && st.log.length === 8, st.log.join(' | '));
check('E1c every secret command targets a Worker by NAME (never the LIVE config file) and every write happens while OFF is deployed',
  st.log.filter(l => l.startsWith('secret')).every(l => /--name plotart-(checkout|studio)$/.test(l) && !/--config/.test(l)) && st.puts.length === 4 && st.puts.every(p => /while=off$/.test(p)), st.puts.join(' | '));
st = await run('enable', { studio: ['RESEND_API_KEY', 'STRIPE_SECRET_KEY'], checkout: ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'RESEND_API_KEY'] });
check('E1d secrets already present from an earlier run are all written again (none left stale)', st.code === 0 && st.puts.length === 4, st.out);
st = await run('enable', { args: [join(ROOT, 'does-not-exist')] });
check('E1e a missing worker directory: refused before any command, exit 1', st.code !== 0 && st.log.length === 0, st.out);

console.log('— E2 every failure after the start recovers to OFF, with evidence (the real outside check confirms OFF)');
const cases = {
  'the OFF deployment fails (a live version may still be running)': { failOn: 'deploy:off' },
  'the first secret write fails': { failOn: 'put:checkout:STRIPE_SECRET_KEY' },
  'PARTIAL: two checkout secrets written, the third (email key) fails': { failOn: 'put:checkout:RESEND_API_KEY' },
  'PARTIAL: all checkout secrets written, the Studio key fails': { failOn: 'put:studio:STRIPE_SECRET_KEY' },
  'a credential is empty': { env: { LIVE_WEBHOOK_SECRET: '' } },
  'a write reports success but the secret is not listed': { drop: 'STRIPE_WEBHOOK_SECRET' },
  'the checkout secret list cannot be read': { failOn: 'list:checkout' },
  'the Studio has no email key': { studio: [] },
  'the LIVE deployment fails': { failOn: 'deploy:on' },
  'LIVE deployed but the real outside check does not see live mode': { srv: 'notlive' },
};
for (const [why, c] of Object.entries(cases)) {
  const s2 = await run('enable', c);
  check(`E2 ${why}: run FAILS, checkout ends OFF, no Studio live key, OFF VERIFIED from outside`, recoveredOff(s2), `${s2.code} ${s2.deployed} [${s2.studio}] ${s2.out}`);
  if (!/LIVE deploy/.test(why)) check(`E2 ${why}: the LIVE configuration was never deployed`, onDeploys(s2) === 0, s2.log.join(' | '));
}
// a partial failure in the deploy step must not reach the live secrets of a different step later (sanity of the stub)
st = await run('enable', { failOn: 'put:checkout:RESEND_API_KEY' });
check('E2 PARTIAL: after the failed third write nothing else is written (no Studio live key written at all)', st.puts.length === 3 && !st.puts.some(p => /^put studio/.test(p)), st.puts.join(' | '));

console.log('— E3 recovery never reports success without evidence');
st = await run('enable', { failOn: 'deploy:on deploy:off:again' });
check('E3a LIVE deploy fails and the recovery OFF deploy fails: OFF NOT VERIFIED; the run fails', st.code !== 0 && /FAILED to deploy the OFF/.test(st.out) && /OFF NOT VERIFIED/.test(st.out) && !/OFF VERIFIED:/.test(st.out), st.out);
st = await run('enable', { failOn: 'put:checkout:RESEND_API_KEY delete:studio', studio: ['RESEND_API_KEY', 'STRIPE_SECRET_KEY'] });
check('E3b the Studio key cannot be removed (still listed): OFF NOT VERIFIED', st.code !== 0 && /STILL holds a Stripe key/.test(st.out) && /OFF NOT VERIFIED/.test(st.out) && !/OFF VERIFIED:/.test(st.out), st.out);
st = await run('enable', { failOn: 'deploy:on list:studio' });
check('E3c the Studio secret list cannot be read during recovery: removal NOT confirmed, OFF NOT VERIFIED', st.code !== 0 && /could not be read/.test(st.out) && /OFF NOT VERIFIED/.test(st.out) && !/OFF VERIFIED:/.test(st.out), st.out);
st = await run('enable', { failOn: 'deploy:on', srv: 'broken' });
check('E3d the outside check gets errors during recovery: OFF NOT VERIFIED', st.code !== 0 && /did NOT confirm the pilot OFF/.test(st.out) && /OFF NOT VERIFIED/.test(st.out), st.out);
st = await run('enable', { env: { ORIGIN: 'http://127.0.0.1:1' } });
check('E3e the Worker cannot be reached at all (live check and OFF check): OFF redeployed, Studio key removed, but OFF NOT VERIFIED', st.code !== 0 && st.deployed === 'off' && !st.studio.includes('STRIPE_SECRET_KEY') && /OFF NOT VERIFIED/.test(st.out) && !/OFF VERIFIED:/.test(st.out), st.out);

console.log('— E4 the plain production OFF path (no enable_live_pilot) actively switches a live deployment off, with evidence');
st = await run('off', { deployed: 'on', studio: ['RESEND_API_KEY', 'STRIPE_SECRET_KEY'] });
check('E4a a live deployment is switched OFF: OFF deployed, Studio key removed and confirmed, real outside check OFF', st.code === 0 && st.deployed === 'off' && !st.studio.includes('STRIPE_SECRET_KEY') && /OFF VERIFIED:/.test(st.out), st.out);
st = await run('off', { deployed: 'off' });
check('E4b nothing live (no Studio key): OFF VERIFIED, the absence confirmed from the list', st.code === 0 && /holds no Stripe key/.test(st.out) && /OFF VERIFIED:/.test(st.out), st.out);
st = await run('off', { failOn: 'list:studio' });
check('E4c the Studio list cannot be read: OFF NOT VERIFIED, exit 1', st.code !== 0 && /OFF NOT VERIFIED/.test(st.out), st.out);
st = await run('off', { args: ['does-not-exist', 'wrangler.checkout.production.off.toml'] });
check('E4d a wrong worker directory: OFF NOT VERIFIED, exit 1, nothing run', st.code !== 0 && /OFF NOT VERIFIED/.test(st.out) && st.log.length === 0, st.out);
st = await run('off', { offToml: ONTOML, deployed: 'on', studio: ['RESEND_API_KEY', 'STRIPE_SECRET_KEY'] });
check('E4e an "OFF" file that is actually live is never deployed, and the run fails', st.code !== 0 && !st.log.some(l => l.startsWith('deploy')) && /OFF NOT VERIFIED/.test(st.out), st.out);
st = await run('off', { srv: 'broken' });
check('E4f the outside check fails: OFF NOT VERIFIED, exit 1', st.code !== 0 && /OFF NOT VERIFIED/.test(st.out), st.out);

console.log('— E5 the enable script refuses wrong configuration files before touching anything');
st = await run('enable', { offToml: ONTOML });
check('E5a an OFF file that is actually live: refused, no command run', st.code !== 0 && st.log.length === 0 && /nothing changed/.test(st.out), st.out);
st = await run('enable', { onToml: ONTOML.replace('plotart-checkout', 'plotart-studio') });
check('E5b a LIVE file for the wrong Worker: refused, no command run', st.code !== 0 && st.log.length === 0 && /nothing changed/.test(st.out), st.out);

console.log('— E6 the workflow');
const wf = readFileSync(join(ROOT, '.github/workflows/plotart-checkout-deploy.yml'), 'utf8');
const prod = wf.split('# ---------------------------------------------------------------- PRODUCTION')[1] || '';
check('E6a production: no inline secret write; the OFF path runs checkout-live-off.sh, the live path checkout-live-enable.sh, both by relative path from the repository root',
  prod.length > 0 && !/secret put/.test(prod) && /!inputs\.enable_live_pilot[\s\S]{0,400}bash atlas-tools\/release\/studio\/checkout-live-off\.sh worker\/plotart-studio wrangler\.checkout\.production\.off\.toml/.test(prod)
  && /bash atlas-tools\/release\/studio\/checkout-live-enable\.sh worker\/plotart-studio/.test(prod));
check('E6b no plain production deploy or rollback to an earlier (possibly live) version remains', !/roll back/i.test(prod) && !/wrangler@[\d.]+ (deploy|rollback)/.test(prod.split('\n').filter(l => !/--dry-run/.test(l)).join('\n')));
check('E6c the credentials check runs before the enable step', prod.indexOf('check-stripe-live-secrets.sh') > -1 && prod.indexOf('check-stripe-live-secrets.sh') < prod.indexOf('checkout-live-enable.sh'));
check('E6d the protected approval is unchanged: production runs in the studio-production. environment', wf.includes("environment: ${{ inputs.target == 'production' && 'studio-production.' || 'checkout-test' }}"));
check('E6e the workflow states that a run stopping before deployment changes nothing (refuses activation, does not disable)', /changes nothing: it refuses the new activation and\s*\n#\s+leaves whatever is deployed as it was/.test(wf));

server.close();
console.log(`LIVE ENABLEMENT FAIL-CLOSED · ${pass + fail} checks, ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
