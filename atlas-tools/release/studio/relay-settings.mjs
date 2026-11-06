// PlotArt · enquiry relay live-settings check (F2, 6 Nov 2026). READ-ONLY on Cloudflare: one GET of the relay Worker's
// settings. Compares them with what the deploy would set (enquiry-expected.json, written by render-enquiry-config.py) and
// stops the deploy if anything would change: a variable with a different value, a live variable or binding the deploy would
// drop, a different database, or a missing secret the configuration needs (e.g. RESEND_API_KEY when MAILER=resend).
// Prints only switch names and values, binding names and PASS/FAIL: never a secret, the database identifier or the account.
//   node relay-settings.mjs <enquiry-expected.json> [before|after]
// Needs CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID (the deploy job's existing token). Local tests may point
// CF_API_BASE at 127.0.0.1 only.
import { readFileSync } from 'node:fs';
const [file, when = 'before'] = process.argv.slice(2);
const E = process.env, SCRIPT = 'plotart-enquiry';
const SHOWN = ['ENQUIRIES_ENABLED', 'MAILER', 'GARDEN_ENQUIRIES_ENABLED', 'ENVIRONMENT', 'ORIGIN', 'MAIL_FROM', 'REPLY_TO'];
const fail = m => { console.log('FAIL  ' + m); process.exit(1); };
const base = E.CF_API_BASE && /^http:\/\/127\.0\.0\.1:\d+$/.test(E.CF_API_BASE) ? E.CF_API_BASE : 'https://api.cloudflare.com/client/v4';
if (!E.CLOUDFLARE_API_TOKEN || !/^[0-9a-f]{32}$/.test(E.CLOUDFLARE_ACCOUNT_ID || '')) fail('the Cloudflare token or account is not available: nothing was deployed');
const want = JSON.parse(readFileSync(file, 'utf8'));
let j;
try {
  const r = await fetch(`${base}/accounts/${E.CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${SCRIPT}/settings`, { headers: { Authorization: 'Bearer ' + E.CLOUDFLARE_API_TOKEN } });
  j = await r.json();
  if (!r.ok || !j.success || !Array.isArray(j.result?.bindings)) throw new Error('HTTP ' + r.status + ' ' + (j.errors || []).map(e => e.code).join(','));
} catch (e) { fail(`the live settings of ${SCRIPT} could not be read (${String(e.message).replace(/[A-Za-z0-9_-]{24,}/g, '[redacted]')}): nothing was deployed`); }
const B = j.result.bindings, problems = [];
const plain = Object.fromEntries(B.filter(b => b.type === 'plain_text').map(b => [b.name, b.text]));
const secrets = B.filter(b => b.type === 'secret_text').map(b => b.name).sort();
const d1 = B.filter(b => b.type === 'd1');
const other = B.filter(b => !['plain_text', 'secret_text', 'd1'].includes(b.type));
console.log(`live ${SCRIPT} (${when} deploy):`);
for (const k of SHOWN) console.log(`  ${k} = ${k in plain ? JSON.stringify(plain[k]) : '(not set)'}`);
for (const k of Object.keys(plain).filter(k => !SHOWN.includes(k))) console.log(`  ${k} = (set; not shown)`);
console.log(`  secrets: ${secrets.join(', ') || 'none'} (names only) · database bindings: ${d1.map(b => b.name).join(', ') || 'none'}${other.length ? ' · other bindings: ' + other.map(b => b.type + ':' + b.name).join(', ') : ''}`);
// Only this switch may be ADDED, and only as "false": the relay deployed on 29 Oct predates the Borrowed Garden route, and an
// absent switch already means closed, so adding it as "false" changes nothing. After the deploy it must be present.
const ADDABLE = { GARDEN_ENQUIRIES_ENABLED: 'false' }, added = [];
for (const [k, v] of Object.entries(want.vars)) {
  if (plain[k] === v) continue;
  if (when === 'before' && !(k in plain) && ADDABLE[k] === v) { added.push(`${k}=${JSON.stringify(v)}`); continue; }
  problems.push(`${k} would change from ${k in plain ? JSON.stringify(plain[k]) : '(not set)'} to ${JSON.stringify(v)}`);
}
if (added.length) console.log(`  will be added, with no change in behaviour: ${added.join(', ')}`);
for (const k of Object.keys(plain)) if (!(k in want.vars)) problems.push(`live variable ${k} would be removed`);
for (const b of d1) if (want.d1[b.name] !== b.id) problems.push(`database binding ${b.name} would ${b.name in want.d1 ? 'point elsewhere' : 'be removed'}`);
for (const n of Object.keys(want.d1)) if (!d1.some(b => b.name === n)) problems.push(`database binding ${n} would be added`);
for (const b of other) problems.push(`live ${b.type} binding ${b.name} would be removed`);
for (const s of want.secrets_required || []) if (!secrets.includes(s)) problems.push(`secret ${s} is not set on the live relay`);
if (want.vars.MAILER === 'resend' && !secrets.includes('RESEND_API_KEY')) problems.push('MAILER=resend needs the secret RESEND_API_KEY');
if (problems.length) fail((when === 'before' ? 'the deploy would change the live relay: ' : 'the live relay does not have the expected settings: ') + problems.join('; '));
console.log(when === 'before' ? 'PASS  the deploy keeps every live setting (open, email on, same database, secrets kept)' : 'PASS  the live relay has exactly the expected settings');
