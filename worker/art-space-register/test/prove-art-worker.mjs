/* ART SPACE REGISTER · WORKER GUARD PROOF
 * ===========================================================================
 * Drives every refusal deliberately, then — with a STUBBED fetch that never
 * leaves this process — asserts exactly what a permitted write would send to
 * Airtable. No test can reach the network: globalThis.fetch is replaced before
 * the Worker runs, and the token is a fake.
 * Run: node worker/art-space-register/test/prove-art-worker.mjs
 * ========================================================================= */
import worker, { __test as T } from '../src/index.js';

let pass = 0, fail = 0;
const out = [];
const check = (name, cond, detail = '') => {
  if (cond) { pass++; out.push('  ok    ' + name); }
  else { fail++; out.push('  FAIL  ' + name + (detail ? '  — ' + detail : '')); }
};

const ORIGIN = 'https://plotnua.ie';
const OFF = { ORIGIN, WRITES_ENABLED: 'false', EMAIL_ENABLED: 'false', PRIVACY_VERSION: '2026-10-PHASE2-V4' };
const ON = { ...OFF, WRITES_ENABLED: 'true', AIRTABLE_BASE: 'appARTTESTONLY0001', AIRTABLE_TOKEN: 'patFAKE_NEVER_REAL' };

/* ---- the network stub ---- */
let calls = [];
let existing = false;
let failWith = 0;
globalThis.fetch = async (url, init = {}) => {
  calls.push({ url: String(url), method: init.method, body: init.body ? JSON.parse(init.body) : null,
               auth: init.headers && init.headers.authorization });
  if (failWith) return new Response('{}', { status: failWith });
  if (init.method === 'GET') {
    return new Response(JSON.stringify({ records: existing ? [{ id: 'recX', fields: {} }] : [] }), { status: 200 });
  }
  return new Response(JSON.stringify({ records: [{ id: 'recNEW' + calls.length }] }), { status: 200 });
};

function req(path, body, { origin = ORIGIN, site = 'cross-site', mode = 'cors', method = 'POST', raw } = {}) {
  const h = { 'content-type': 'application/json' };
  if (origin) h.origin = origin;
  if (site) h['sec-fetch-site'] = site;
  if (mode) h['sec-fetch-mode'] = mode;
  return new Request('https://w.example' + path, {
    method, headers: h,
    body: method === 'GET' || method === 'OPTIONS' ? undefined : (raw !== undefined ? raw : JSON.stringify(body || {}))
  });
}
const R = T.ROUTE;
const run = async (env, r) => { calls = []; T.resetRateLimit(); const res = await worker.fetch(r, env); let j = null; try { j = await res.clone().json(); } catch {} return { s: res.status, j, h: res.headers }; };
const good = (over = {}) => ({
  first_name: 'Test', email: 'Guard.Test@example.com', county: 'dublin', ways: ['display', 'store'],
  over_18: true, consent_text: T.CONSENT_TEXT, source: 'property_check', ...over
});
const refusedAs = (r, field) => r.s === 400 && r.j && r.j.state === 'refused' && (field === undefined || r.j.field === field);

/* ---- 1 · switches, origin, method, route ---- */
let r = await run(OFF, req(R, good()));
check('W1 writes off -> 503 not_open, and no Airtable call', r.s === 503 && r.j.state === 'not_open' && calls.length === 0);
r = await run({ ...ON, AIRTABLE_TOKEN: '' }, req(R, good()));
check('W2 no token -> not_open, no call', r.s === 503 && calls.length === 0);
r = await run({ ...ON, AIRTABLE_BASE: '' }, req(R, good()));
check('W3 no base -> not_open, no call', r.s === 503 && calls.length === 0);
r = await run(ON, req(R, good(), { origin: 'https://evil.example' }));
check('W4 foreign origin -> 403, no CORS header, no call', r.s === 403 && !r.h.get('access-control-allow-origin') && calls.length === 0);
r = await run(ON, req(R, good(), { origin: null }));
check('W5 no origin -> 403', r.s === 403 && calls.length === 0);
r = await run(ON, req(R, good(), { site: 'same-origin' }));
check('W6 sec-fetch-site not cross-site -> refused', refusedAs(r) && calls.length === 0);
r = await run(ON, req(R, null, { method: 'GET' }));
check('W7 GET -> 405, there is no read surface', r.s === 405 && calls.length === 0);
r = await run(ON, req('/v1/art-space-register/list', good()));
check('W8 unknown route -> 404', r.s === 404 && calls.length === 0);
r = await run(ON, req('/v1/garden-register/garden', good()));
check('W9 the garden route does not exist here', r.s === 404 && calls.length === 0);
r = await run(ON, req(R, null, { method: 'OPTIONS' }));
check('W10 preflight from plotnua.ie -> 204, exact origin, no credentials',
  r.s === 204 && r.h.get('access-control-allow-origin') === ORIGIN && !r.h.get('access-control-allow-credentials'));

/* ---- 2 · body ---- */
r = await run(ON, req(R, null, { raw: 'x'.repeat(T.MAX_BODY_BYTES + 1) }));
check('B1 oversized body refused', refusedAs(r, 'body') && calls.length === 0);
r = await run(ON, req(R, null, { raw: '{not json' }));
check('B2 malformed JSON refused', refusedAs(r, 'body'));
r = await run(ON, req(R, null, { raw: '[1,2]' }));
check('B3 array body refused', refusedAs(r, 'body'));

/* ---- 3 · strict keys: refused BEFORE the write switch ---- */
for (const k of ['address', 'eircode', 'phone', 'surname', 'inherited_tenure', 'host_state', 'website', 'artwork_value', 'photo']) {
  const ro = await run(OFF, req(R, good({ [k]: 'x' })));
  check('K ' + k + ' refused even with writes off', refusedAs(ro, 'unexpected_field') && calls.length === 0);
}

/* ---- 4 · fields ---- */
const fieldCases = [
  ['first_name', { first_name: '  ' }], ['email', { email: 'not-an-email' }],
  ['county', { county: 'antrim' }], ['county', { county: '' }],
  ['ways', { ways: [] }], ['ways', { ways: ['display', 'display'] }], ['ways', { ways: ['studio'] }],
  ['ways', { ways: 'display' }], ['ways', { ways: ['store', 'display', 'open', 'help_sell', 'store'] }],
  ['space', { space: 'garden' }], ['money', { money: 'guaranteed_income' }],
  ['host_note', { host_note: 42 }], ['over_18', { over_18: false }], ['over_18', { over_18: 'true' }],
  ['consent_text', { consent_text: 'I agree.' }],
  ['consent_text', { consent_text: T.CONSENT_TEXT.replace('withdraw', 'revoke') }]
];
for (const [f, o] of fieldCases) {
  const rr = await run(ON, req(R, good(o)));
  check('F ' + f + ' ' + JSON.stringify(o).slice(0, 60), refusedAs(rr, f) && calls.length === 0, JSON.stringify(rr.j));
}
const missing = good(); delete missing.ways;
r = await run(ON, req(R, missing));
check('F ways required', refusedAs(r, 'ways'));
const noCounty = good(); delete noCounty.county;
r = await run(ON, req(R, noCounty));
check('F county required', refusedAs(r, 'county'));

/* ---- 5 · consent: whitespace normalises, meaning does not ---- */
r = await run(OFF, req(R, good({ consent_text: '  ' + T.CONSENT_TEXT.replace(/ /g, '  ') + ' ' })));
check('C1 incidental whitespace still matches (reaches the write switch)', r.s === 503 && r.j.state === 'not_open');
check('C2 canonical sentence is the founder-approved text, ASCII apostrophe',
  T.CONSENT_TEXT === "I'm over 18 and agree that PlotNua may keep my registration details and contact me about the Open Your Home to Art pilot. I understand I can withdraw my consent at any time.");

/* ---- 6 · a permitted write, against the stub ---- */
existing = false;
r = await run(ON, req(R, good({ space: 'a_room', money: 'not_decided', host_note: '  A   spare room upstairs.  ' })));
const posts = calls.filter(c => c.method === 'POST');
const host = posts.find(c => c.url.endsWith('/Hosts'));
const log = posts.find(c => c.url.endsWith('/Status%20log'));
const proof = posts.find(c => c.url.endsWith('/Consent%20proofs'));
check('P1 received', r.s === 200 && r.j.state === 'received');
check('P2 exactly one lookup and three creates, all to the configured base only',
  calls.length === 4 && calls.every(c => c.url.startsWith('https://api.airtable.com/v0/appARTTESTONLY0001/')));
check('P3 every create has typecast:false', posts.every(c => c.body.typecast === false));
const hf = host && host.body.records[0].fields;
check('P4 status ceiling: interest_submitted only', hf && hf.status === 'interest_submitted');
const allowedOut = ['first_name', 'email', 'email_key', 'county', 'ways', 'space', 'money', 'host_note', 'over_18',
  'status', 'submitted_at', 'privacy_version', 'consent_text_hash', 'source'];
check('P5 Hosts row carries only the listed fields', hf && Object.keys(hf).every(k => allowedOut.includes(k)), hf && Object.keys(hf).join(','));
check('P6 ways stored in canonical order', hf && JSON.stringify(hf.ways) === '["store","display"]');
check('P7 email_key lower-cased; note whitespace collapsed', hf && hf.email_key === 'guard.test@example.com' && hf.host_note === 'A spare room upstairs.');
check('P8 privacy version recorded from env', hf && hf.privacy_version === '2026-10-PHASE2-V4');
const pf = proof && proof.body.records[0].fields;
check('P9 consent proof holds a hash, never the address', pf && /^[0-9a-f]{64}$/.test(pf.email_hash) &&
  !JSON.stringify(pf).includes('@') && Object.keys(pf).sort().join() === 'consent_text_hash,email_hash,given_at,privacy_version');
check('P10 status log row from nothing to interest_submitted', log && log.body.records[0].fields.to_status === 'interest_submitted' && log.body.records[0].fields.actor === 'system');
check('P11 token sent only to Airtable, as a bearer', calls.every(c => c.auth === 'Bearer patFAKE_NEVER_REAL'));

/* ---- 7 · optional fields absent -> not written ---- */
r = await run(ON, req(R, good()));
const hf2 = calls.find(c => c.method === 'POST' && c.url.endsWith('/Hosts')).body.records[0].fields;
check('O1 absent optional fields are not written', !('space' in hf2) && !('money' in hf2) && !('host_note' in hf2));

/* ---- 8 · repeat address: same reply, nothing written ---- */
existing = true;
r = await run(ON, req(R, good()));
check('D1 repeat address -> the same "received", no write (no oracle)', r.s === 200 && r.j.state === 'received' && calls.filter(c => c.method === 'POST').length === 0);
existing = false;

/* ---- 9 · upstream failure: truthful, no detail leaked ---- */
failWith = 422;
r = await run(ON, req(R, good()));
check('U1 Airtable 422 -> unavailable with a status class only', r.s === 503 && r.j.state === 'unavailable' && r.j.reason === 'at422');
failWith = 0;

/* ---- 9b · rate limit ---- */
T.resetRateLimit();
let last;
for (let i = 0; i < 31; i++) last = await worker.fetch(req(R, good()), OFF);
check('RL1 the 31st request in a minute is told to slow down', last.status === 429);
T.resetRateLimit();

/* ---- 10 · source code properties ---- */
import { readFileSync } from 'node:fs';
const src = readFileSync(new URL('../src/index.js', import.meta.url), 'utf8');
const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
check('S1 no mail adapter (no mail/smtp/resend/sendgrid call)', !/sendgrid|resend|smtp|mailchannels|sendEmail|send_email/i.test(code));
check('S2 the only status literal written is interest_submitted', (code.match(/'interest_submitted'/g) || []).length === 1 && !/qualified|introduc|matched|booked/i.test(code));
check('S3 no garden base id, table or route in the code', !/appUie3wPmPITfMW7|Gardens|Growers|garden-register\/(garden|grower)/.test(code));
check('S4 no console logging of request data', !/console\./.test(code));
const toml = readFileSync(new URL('../wrangler.toml', import.meta.url), 'utf8');
check('S5 wrangler ships WRITES_ENABLED and EMAIL_ENABLED "false"', /WRITES_ENABLED\s*=\s*"false"/.test(toml) && /EMAIL_ENABLED\s*=\s*"false"/.test(toml));
check('S6 no secret, token or base id in wrangler.toml', !/pat[A-Za-z0-9]{10}|app[A-Za-z0-9]{14}/.test(toml));
check('S7 worker name is its own', /name = "plotnua-art-space-register"/.test(toml));

console.log(out.join('\n'));
console.log('\n  ' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
