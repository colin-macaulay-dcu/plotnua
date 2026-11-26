// PlotNua · garden-lead Worker live-settings check (Package N, Step C). READ-ONLY on Cloudflare: one GET of the Worker's
// settings. Prints switch names and values and secret NAMES only: never a secret, the Airtable base or the account.
//   node settings.mjs before   -> the Worker may not exist yet (first deployment); if it does, every switch must be closed
//   node settings.mjs after    -> the Worker exists and every switch is closed
// Needs CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID. Local tests may point CF_API_BASE at 127.0.0.1 only.
const [when = 'before'] = process.argv.slice(2);
const E = process.env, SCRIPT = 'plotnua-garden-lead';
const SWITCHES = ['LEAD_PUBLIC_ENABLED', 'WRITES_ENABLED', 'EMAIL_ENABLED', 'INTRO_PUBLIC_ENABLED', 'INTRO_WRITES_ENABLED', 'INTRO_NOTIFY_ENABLED', 'INTRO_RETENTION_ENABLED'];
const fail = m => { console.log('FAIL  ' + m); process.exit(1); };
const base = E.CF_API_BASE && /^http:\/\/127\.0\.0\.1:\d+$/.test(E.CF_API_BASE) ? E.CF_API_BASE : 'https://api.cloudflare.com/client/v4';
if (!E.CLOUDFLARE_API_TOKEN || !/^[0-9a-f]{32}$/.test(E.CLOUDFLARE_ACCOUNT_ID || '')) fail('the Cloudflare token or account is not available: nothing was deployed');
let r, j;
try {
  r = await fetch(`${base}/accounts/${E.CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${SCRIPT}/settings`, { headers: { Authorization: 'Bearer ' + E.CLOUDFLARE_API_TOKEN } });
  j = await r.json().catch(() => ({}));
} catch (e) { fail('the live settings could not be read: nothing was deployed'); }
if (r.status === 404 || (j.errors || []).some(e => e.code === 10007)) {
  if (when === 'before') { console.log(`live ${SCRIPT}: not deployed yet (this is its first deployment)`); process.exit(0); }
  fail(`${SCRIPT} does not exist after the deploy`);
}
if (!r.ok || !j.success || !Array.isArray(j.result?.bindings)) fail('the live settings could not be read (HTTP ' + r.status + '): nothing was deployed');
const B = j.result.bindings;
const plain = Object.fromEntries(B.filter(b => b.type === 'plain_text').map(b => [b.name, b.text]));
const secrets = B.filter(b => b.type === 'secret_text').map(b => b.name).sort();
console.log(`live ${SCRIPT} (${when} deploy):`);
for (const k of SWITCHES) console.log(`  ${k} = ${k in plain ? JSON.stringify(plain[k]) : '(not set: closed)'}`);
console.log(`  AIRTABLE_BASE ${'AIRTABLE_BASE' in plain ? 'set (not shown)' : 'not set'} · secrets: ${secrets.join(', ') || 'none'} (names only)`);
const open = SWITCHES.filter(k => plain[k] === 'true');
if (open.length) fail(`switch(es) open on the live Worker: ${open.join(', ')}. This workflow deploys a CLOSED Worker only; opening a switch is a separate founder step`);
console.log('PASS  every switch is closed');
