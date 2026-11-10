#!/usr/bin/env node
// PlotArt · proof of the F2 enquiry relay release (6 Nov 2026). Runs locally; touches nothing real.
//   A  the production configuration keeps the relay open with email on and the garden route off; the repo file still ships closed
//   B  relay-settings.mjs, against a stand-in for the Cloudflare API: accepts a deploy that keeps every live setting; refuses
//      one that would close the relay, switch email off, drop a variable or binding, change the database or lack a secret
//   C  the new relay code itself: open, both notice versions accepted, the garden route present and off, refusals unchanged;
//      the code live today (29 Oct) accepts only the first notice version, which is why C2 waits for F2
//   D  the workflow: founder approval, settings read before and after, outside check, automatic rollback, never activate.sh
//   node atlas-tools/release/studio/prove-relay-release.mjs
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, copyFileSync, mkdirSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const HERE = dirname(fileURLToPath(import.meta.url)), ROOT = join(HERE, '..', '..', '..'), W = join(ROOT, 'worker', 'plotart-studio');
const T = mkdtempSync(join(tmpdir(), 'pa-relay-'));
const results = [];
const check = (name, ok, detail = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${ok || !detail ? '' : ' :: ' + String(detail).slice(0, 300)}`); };
const DB = '0123abcd-0123-4567-89ab-0123456789ab', ACCT = 'a'.repeat(32);

// ---------------------------------------------------------------- A · production configuration
console.log('A · production configuration');
const wt = join(T, 'w'); mkdirSync(wt);
for (const f of ['wrangler.enquiry.toml', 'enquiry-production.json']) copyFileSync(join(W, f), join(wt, f));
const render = env => spawnSync('python3', [join(HERE, 'render-enquiry-config.py'), wt], { env: { ...process.env, ...env }, encoding: 'utf8' });
let r = render({ STUDIO_D1_DATABASE_ID: DB });
const toml = r.status === 0 ? readFileSync(join(wt, 'wrangler.enquiry.production.toml'), 'utf8') : '';
check('renders with the relay OPEN, email ON (resend), garden route OFF', r.status === 0 && /^ENQUIRIES_ENABLED = "true"/m.test(toml) && /^MAILER = "resend"/m.test(toml) && /^GARDEN_ENQUIRIES_ENABLED = "false"/m.test(toml), r.stdout + r.stderr);
check('Art for Hire (3B-5): production renders all three hire switches CLOSED, and the settings file cannot open them',
  /^HIRE_ENQUIRIES_ENABLED = "false"/m.test(toml) && /^HIRE_TERMS_ENABLED = "false"/m.test(toml) && /^HIRE_SCREEN_USE = "false"/m.test(toml));
check('the database identifier comes from the environment and is not printed', toml.includes(DB) && !(r.stdout + r.stderr).includes(DB));
const expected = r.status === 0 ? JSON.parse(readFileSync(join(wt, 'enquiry-expected.json'), 'utf8')) : null;
check('writes what the deploy will set, for the live comparison', expected && expected.vars.ENQUIRIES_ENABLED === 'true' && expected.d1.DB === DB && expected.secrets_required.includes('RESEND_API_KEY'));
r = render({ STUDIO_D1_DATABASE_ID: 'not-an-id' });
check('refuses without a proper database identifier', r.status !== 0 && /REFUSED/.test(r.stdout + r.stderr));
const repo = readFileSync(join(W, 'wrangler.enquiry.toml'), 'utf8');
check('wrangler.enquiry.toml itself still ships CLOSED and sending nothing (activate.sh contract unchanged)', /^ENQUIRIES_ENABLED = "false"/m.test(repo) && /^MAILER = "none"/m.test(repo));
const guard = json => spawnSync('python3', ['-c', 'import json,sys; v=json.load(sys.stdin)["vars"]; sys.exit(0 if v["ENQUIRIES_ENABLED"]=="true" and v["MAILER"]=="resend" and v["GARDEN_ENQUIRIES_ENABLED"]=="false" else 1)'], { input: JSON.stringify(json) }).status;
check("the workflow's guard refuses a settings file that would close the relay, switch email off or open the garden route",
  guard({ vars: { ENQUIRIES_ENABLED: 'true', MAILER: 'resend', GARDEN_ENQUIRIES_ENABLED: 'false' } }) === 0
  && guard({ vars: { ENQUIRIES_ENABLED: 'false', MAILER: 'resend', GARDEN_ENQUIRIES_ENABLED: 'false' } }) !== 0
  && guard({ vars: { ENQUIRIES_ENABLED: 'true', MAILER: 'none', GARDEN_ENQUIRIES_ENABLED: 'false' } }) !== 0
  && guard({ vars: { ENQUIRIES_ENABLED: 'true', MAILER: 'resend', GARDEN_ENQUIRIES_ENABLED: 'true' } }) !== 0);

// ---------------------------------------------------------------- B · live settings check
console.log('B · live-settings check (stand-in for the Cloudflare API)');
let live, status = 200;
const server = createServer((req, res) => {
  const ok = req.url === `/accounts/${ACCT}/workers/scripts/plotart-enquiry/settings` && req.headers.authorization === 'Bearer test-token';
  res.writeHead(ok ? status : 403, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(ok && status === 200 ? { success: true, result: { bindings: live } } : { success: false, errors: [{ code: 10000 }] }));
});
await new Promise(res => server.listen(0, '127.0.0.1', res));
const API = `http://127.0.0.1:${server.address().port}`;
const plain = (name, text) => ({ type: 'plain_text', name, text });
const TODAY = [plain('ENVIRONMENT', 'production'), plain('ORIGIN', 'https://plotnua.ie'), plain('ENQUIRIES_ENABLED', 'true'), plain('MAILER', 'resend'),
  plain('MAIL_FROM', 'PlotArt <enquiries@plotnua.ie>'), plain('REPLY_TO', 'hello@plotnua.ie'), { type: 'secret_text', name: 'RESEND_API_KEY' }, { type: 'd1', name: 'DB', id: DB }];
const settings = (bindings, when = 'before') => new Promise(resolve => {
  live = bindings;
  import('node:child_process').then(({ execFile }) => execFile('node', [join(HERE, 'relay-settings.mjs'), join(wt, 'enquiry-expected.json'), when],
    { env: { ...process.env, CF_API_BASE: API, CLOUDFLARE_API_TOKEN: 'test-token', CLOUDFLARE_ACCOUNT_ID: ACCT } },
    (err, stdout) => resolve({ code: err ? err.code : 0, out: String(stdout) })));
});
const noLeak = o => !o.includes(DB) && !o.includes('test-token') && !o.includes(ACCT);
const sc = async (name, bindings, expect, when = 'before', must) => {
  const s = await settings(bindings, when);
  check(`${name} → ${expect ? 'deploy proceeds' : 'deploy REFUSED'}`, (s.code === 0) === expect && noLeak(s.out) && (!must || must.test(s.out)), s.out.trim().split('\n').pop());
};
await sc("today's live relay (29 Oct: open, email on, no garden switch yet)", TODAY, true, 'before', /will be added, with no change in behaviour: GARDEN_ENQUIRIES_ENABLED="false", HIRE_ENQUIRIES_ENABLED="false", HIRE_TERMS_ENABLED="false", HIRE_SCREEN_USE="false"/);
const HIRE_OFF = ['HIRE_ENQUIRIES_ENABLED', 'HIRE_TERMS_ENABLED', 'HIRE_SCREEN_USE'].map(k => plain(k, 'false'));
await sc('after the deploy: exactly the expected settings', [...TODAY, plain('GARDEN_ENQUIRIES_ENABLED', 'false'), ...HIRE_OFF], true, 'after');
await sc('after the deploy: an Art for Hire switch missing', [...TODAY, plain('GARDEN_ENQUIRIES_ENABLED', 'false'), ...HIRE_OFF.slice(1)], false, 'after');
await sc('live Art for Hire enquiries ON: the deploy would close them', [...TODAY, plain('HIRE_ENQUIRIES_ENABLED', 'true')], false);
await sc('after the deploy: the garden switch missing', TODAY, false, 'after');
await sc('live relay with email OFF (MAILER none): the deploy would switch it on', TODAY.map(b => b.name === 'MAILER' ? plain('MAILER', 'none') : b), false);
await sc('live relay CLOSED: the deploy would open it', TODAY.map(b => b.name === 'ENQUIRIES_ENABLED' ? plain('ENQUIRIES_ENABLED', 'false') : b), false);
await sc('live garden route ON: the deploy would close it', [...TODAY, plain('GARDEN_ENQUIRIES_ENABLED', 'true')], false);
await sc('a live variable the deploy would drop', [...TODAY, plain('EXTRA_SWITCH', 'x')], false);
await sc('the email key secret missing', TODAY.filter(b => b.name !== 'RESEND_API_KEY'), false);
await sc('the relay bound to another database', TODAY.map(b => b.type === 'd1' ? { ...b, id: 'ffffffff-ffff-ffff-ffff-ffffffffffff' } : b), false);
await sc('a live binding of another kind the deploy would drop', [...TODAY, { type: 'kv_namespace', name: 'CACHE' }], false);
await sc('a different sender address', TODAY.map(b => b.name === 'MAIL_FROM' ? plain('MAIL_FROM', 'x@example.com') : b), false);
status = 500; await sc('the live settings cannot be read', TODAY, false); status = 200;
{ const s = await settings(TODAY); check('prints switch values and binding names only: no secret, database or account identifier', noLeak(s.out) && /MAILER = "resend"/.test(s.out) && /secrets: RESEND_API_KEY \(names only\)/.test(s.out), s.out); }
server.close();

// ---------------------------------------------------------------- C · the relay code
console.log('C · the relay code (no database touched: every request is refused before it)');
async function relay(srcDir, env) {
  const d = join(T, 'r' + Math.random().toString(36).slice(2)); mkdirSync(d);
  for (const f of ['enquiry.js', 'mailer.js', 'founding.js', 'hire-enquiry.js', 'hire-rules.js']) { try { copyFileSync(join(srcDir, f), join(d, f)); } catch {} }   // + Art for Hire (3B-3)
  writeFileSync(join(d, 'package.json'), '{"type":"module"}');
  const mod = (await import(pathToFileURL(join(d, 'enquiry.js')).href)).default;
  let ip = 0;
  const DBguard = { prepare() { throw new Error('the database was touched'); }, batch() { throw new Error('the database was touched'); } };
  return async (path, { method = 'POST', origin = 'https://plotnua.ie', body } = {}) => {
    const h = { 'CF-Connecting-IP': '10.0.0.' + (++ip) }; if (origin) h.Origin = origin; if (body !== undefined) h['Content-Type'] = 'application/json';
    const res = await mod.fetch(new Request('https://relay.test' + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) }), { ...env, DB: DBguard });
    return { status: res.status, body: await res.text(), acao: res.headers.get('Access-Control-Allow-Origin') };
  };
}
const ENV_OPEN = { ENVIRONMENT: 'production', ORIGIN: 'https://plotnua.ie', ENQUIRIES_ENABLED: 'true', GARDEN_ENQUIRIES_ENABLED: 'false', MAILER: 'resend', MAIL_FROM: 'x', REPLY_TO: 'hello@plotnua.ie' };
const NEW = await relay(join(W, 'src'), ENV_OPEN);
let x;
x = await NEW('/v1/enquiry', { body: { notice: 'PA-ENQ-2026-10-29', name: '' } }); check('new code, open: notice PA-ENQ-2026-10-29 accepted (refused only for the blank name)', x.status === 400 && /check your name/.test(x.body), x.body);
x = await NEW('/v1/enquiry', { body: { notice: 'PA-ENQ-2026-11', name: '' } }); check('new code, open: notice PA-ENQ-2026-11 accepted (refused only for the blank name)', x.status === 400 && /check your name/.test(x.body), x.body);
x = await NEW('/v1/enquiry', { body: { notice: 'PA-ENQ-2099-01', name: 'A' } }); check('new code: an unknown notice version is still refused', x.status === 400 && /reload the page/.test(x.body), x.body);
x = await NEW('/v1/enquiry', { origin: 'https://evil.example', body: {} }); check('new code: another website refused (403)', x.status === 403);
x = await NEW('/v1/enquiry', { method: 'OPTIONS' }); check('new code: plotnua.ie CORS pre-check (204, plotnua.ie only)', x.status === 204 && x.acao === 'https://plotnua.ie');
x = await NEW('/v1/enquiry', { method: 'GET' }); check('new code: GET refused (405)', x.status === 405);
x = await NEW('/v1/garden-enquiry', { body: {} }); check('new code: Borrowed Garden route present and OFF (503)', x.status === 503, x.body);
x = await NEW('/v1/enquiry', { body: { notice: 'PA-ENQ-2026-10-29', website: 'bot', name: 'A' } }); check('new code: the spam trap still drops silently without touching anything', x.status === 200 && /PA-E-000000-0000/.test(x.body), x.body);
const CLOSED = await relay(join(W, 'src'), { ...ENV_OPEN, ENQUIRIES_ENABLED: 'false' });
x = await CLOSED('/v1/enquiry', { body: { notice: 'PA-ENQ-2026-10-29', name: '' } }); check('the same code CLOSED answers 503 (what activate.sh would have done)', x.status === 503);
const oldDir = join(T, 'old'); mkdirSync(oldDir);
for (const f of ['enquiry.js', 'mailer.js']) writeFileSync(join(oldDir, f), execFileSync('git', ['-C', ROOT, 'show', `330206f:worker/plotart-studio/src/${f}`], { encoding: 'utf8' }));
let OLD = null; try { OLD = await relay(oldDir, ENV_OPEN); } catch (e) { check('the 29 Oct relay code loads', false, e.message); }
if (OLD) {
  x = await OLD('/v1/enquiry', { body: { notice: 'PA-ENQ-2026-10-29', name: '' } }); check('code live today (29 Oct): notice PA-ENQ-2026-10-29 accepted', x.status === 400 && /check your name/.test(x.body), x.body);
  x = await OLD('/v1/enquiry', { body: { notice: 'PA-ENQ-2026-11', name: '' } }); check('code live today (29 Oct): notice PA-ENQ-2026-11 REFUSED, so C2 must wait for F2', x.status === 400 && /reload the page/.test(x.body), x.body);
  x = await OLD('/v1/garden-enquiry', { body: {} }); check('code live today (29 Oct): no garden route (404), as seen live', x.status === 404);
}

// ---------------------------------------------------------------- D · the workflow
console.log('D · the deploy workflow');
const wf = readFileSync(join(ROOT, '.github', 'workflows', 'plotart-enquiry-relay-deploy.yml'), 'utf8');
const steps = [...wf.matchAll(/- name: (.+)/g)].map(m => m[1]);
const at = s => steps.findIndex(x => x.startsWith(s));
check('workflow_dispatch only; dry run by default; main only', /on:\s*\n\s*workflow_dispatch:/.test(wf) && !/\n\s*push:/.test(wf) && /dry_run:[\s\S]*?default: true/.test(wf) && wf.includes("github.ref == 'refs/heads/main'"));
check('deploy waits for the founder in "studio-production." and uses the existing token only', wf.includes('environment: "studio-production."') && !/secrets\.(?!STUDIO_CF_DEPLOY_TOKEN)\w+/.test(wf));
const order = [at('Production configuration'), at('Live relay settings'), at('The relay as it is now'), at('Deploy the relay'), at('After the deploy'), at('Automatic rollback')];
check('order: render → read live settings (refuse if any would change) → outside check → deploy → settings and outside check again → rollback on failure', !order.includes(-1) && order.join() === [...order].sort((a, b) => a - b).join(), JSON.stringify(order));
check('the live-settings read also runs in a dry run (a read-only inspection)', !/Live relay settings[\s\S]{0,80}if:/.test(wf.slice(wf.indexOf('Live relay settings'), wf.indexOf('The relay as it is now'))));
const code = wf.split('\n').filter(l => !/^\s*#/.test(l)).join('\n');   // commands only, not the warning in the header
check('never runs activate.sh or deploys wrangler.enquiry.toml directly; never --var', !/activate\.sh|--config wrangler\.enquiry\.toml|--var /.test(code));
check('shares the Cloudflare concurrency group with the Studio and migration workflows', wf.includes('group: plotart-studio-cloudflare'));

const bad = results.filter(x => !x).length;
console.log(bad ? `RELAY RELEASE · REFUSED — ${bad} of ${results.length} failed`
  : `RELAY RELEASE · OK — ${results.length} checks: open with email on and garden off; live settings kept or the deploy refused; both notice versions; outside checks and rollback; nothing private printed`);
process.exit(bad ? 2 : 0);
