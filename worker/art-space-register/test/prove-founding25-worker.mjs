/* PLOTART FOUNDING 25 · WORKER GUARD PROOF · v2 (28 Oct 2026, CLOSED)
 * ===========================================================================
 * The Founding 25 route, driven against a STUBBED fetch that never leaves this
 * process. Every record is synthetic (example.com addresses, a fake token and
 * a fake base). Proves: closed in the committed configuration; every hard
 * stop; the allow-list and required keys; validation of every field; the
 * three confirmations; exactly what a permitted write sends; duplicate, cap,
 * burst and upstream handling; the optional challenge; the non-writing probe;
 * schema agreement; and that the Host and Artist routes are never touched.
 * Run: node worker/art-space-register/test/prove-founding25-worker.mjs
 * ========================================================================= */
import worker, { __test as T } from '../src/index.js';
import { readFileSync } from 'node:fs';

let pass = 0, fail = 0;
const out = [];
const check = (name, cond, detail = '') => {
  if (cond) { pass++; out.push('  ok    ' + name); }
  else { fail++; out.push('  FAIL  ' + name + (detail ? '  — ' + detail : '')); }
};

const toml = readFileSync(new URL('../wrangler.toml', import.meta.url), 'utf8');
const topToml = toml.split(/^\[env\./m)[0];
const tomlVars = Object.fromEntries([...topToml.matchAll(/^([A-Z0-9_]+)\s*=\s*"([^"]*)"/gm)].map(m => [m[1], m[2]]));
const FAKE = { AIRTABLE_BASE: 'appF25TESTONLY001', AIRTABLE_TOKEN: 'patFAKE_NEVER_REAL' };
const COMMITTED = { ...tomlVars, ...FAKE };
const ON = { ...COMMITTED, F25_WRITES_ENABLED: 'true', F25_PRIVACY_VERSION: '2026-11-PLOTART-F25-TEST' };
const schema = JSON.parse(readFileSync(new URL('../airtable-schema-founding-25.proposed.json', import.meta.url), 'utf8'));
const sField = Object.fromEntries(schema.new_table.fields.map(f => [f.name, f]));

/* ---- stubbed network ---- */
let capMalformed = false;
let calls = [], existing = false, failWith = 0, failCreateOnly = 0, failSecondary = 0, netDown = false, recent = 0, ts = { ok: true, success: true };
globalThis.fetch = async (url, init = {}) => {
  const u = String(url);
  calls.push({ url: u, method: init.method, body: init.body ? JSON.parse(init.body) : null,
               auth: init.headers && init.headers.authorization });
  if (u.startsWith('https://challenges.cloudflare.com/')) {
    if (ts === 'down') throw new TypeError('fetch failed');
    return new Response(JSON.stringify({ success: ts.success }), { status: ts.ok ? 200 : 500 });
  }
  if (netDown) throw new TypeError('fetch failed');
  if (failWith) return new Response('{}', { status: failWith });
  if (init.method === 'GET' && u.includes('IS_AFTER') && capMalformed) return new Response('{}', { status: 200 });
  if (init.method === 'GET' && u.includes('IS_AFTER')) {
    return new Response(JSON.stringify({ records: Array.from({ length: recent }, (_, i) => ({ id: 'recR' + i, fields: {} })) }), { status: 200 });
  }
  if (init.method === 'GET') return new Response(JSON.stringify({ records: existing ? [{ id: 'recX', fields: {} }] : [] }), { status: 200 });
  const isApp = u.includes(encodeURIComponent('Founding 25 applications'));
  if (failCreateOnly && isApp) return new Response('{}', { status: failCreateOnly });
  if (failSecondary && !isApp) return new Response('{}', { status: failSecondary });
  return new Response(JSON.stringify({ records: [{ id: 'recNEW' + calls.length }] }), { status: 200 });
};

const ORIGIN = 'https://plotnua.ie';
function req(path, body, { origin = ORIGIN, site = 'cross-site', mode = 'cors', method = 'POST', raw } = {}) {
  const h = { 'content-type': 'application/json' };
  if (origin) h.origin = origin;
  if (site) h['sec-fetch-site'] = site;
  if (mode) h['sec-fetch-mode'] = mode;
  return new Request('https://w.example' + path, { method, headers: h,
    body: method === 'GET' || method === 'OPTIONS' ? undefined : (raw !== undefined ? raw : JSON.stringify(body || {})) });
}
const R = T.F25_ROUTE;
const run = async (env, r, { keepRate = false } = {}) => {
  calls = []; if (!keepRate) T.resetRateLimit();
  const res = await worker.fetch(r, env); let j = null; try { j = await res.clone().json(); } catch {}
  return { s: res.status, j, h: res.headers };
};
const SID = '6f1c2d3e-4b5a-4c7d-8e9f-0a1b2c3d4e5f';
const good = (over = {}) => ({
  artist_name: 'Synthetic Test Artist', email: 'F25.Test@example.com', region: 'galway', medium: 'painting',
  bio: 'A synthetic biography for testing only. Paints coastal light in oil, working from a studio near the sea.',
  portfolio: 'https://example.com/portfolio',
  eligibility_text: T.F25_ELIGIBILITY_TEXT, ownership_text: T.F25_OWNERSHIP_TEXT, privacy_text: T.F25_PRIVACY_TEXT,
  submission_id: SID, ...over
});
const without = (k) => { const g = good(); delete g[k]; return g; };
const refusedAs = (r, field) => r.s === 400 && r.j && r.j.state === 'refused' && (field === undefined || r.j.field === field);
const atCalls = () => calls.filter(c => c.url.includes('api.airtable.com'));
const posts = () => atCalls().filter(c => c.method === 'POST').map(c => ({ ...c, body: { ...c.body, fields: c.body.records[0].fields } }));
const noCall = () => atCalls().length === 0;
const notOpenNoCall = (r) => r.s === 503 && r.j && r.j.state === 'not_open' && noCall();

/* ---- Z · closed in the committed configuration ---- */
check('Z1 wrangler.toml: F25_WRITES_ENABLED = "false"', tomlVars.F25_WRITES_ENABLED === 'false');
check('Z2 wrangler.toml: F25_PRIVACY_VERSION empty (no published notice covers applications yet)', tomlVars.F25_PRIVACY_VERSION === '');
check('Z3 wrangler.toml: no secret, token or base set as a variable', !/^\s*(F25_TURNSTILE_SECRET|AIRTABLE_TOKEN|AIRTABLE_BASE)\s*=/m.test(toml));
let r = await run(COMMITTED, req(R, good()));
check('Z4 a valid application under the COMMITTED config -> not_open, no Airtable call', notOpenNoCall(r));
for (const [k, v] of [['F25_WRITES_ENABLED', 'false'], ['F25_WRITES_ENABLED', 'TRUE'], ['F25_PRIVACY_VERSION', ''], ['AIRTABLE_TOKEN', ''], ['AIRTABLE_BASE', '']]) {
  r = await run({ ...ON, [k]: v }, req(R, good()));
  check(`Z5 ${k}=${JSON.stringify(v)} -> not_open, no call`, notOpenNoCall(r));
}
r = await run(ON, req(R, good()));
check('Z6 everything on -> received, three writes', r.s === 200 && r.j.state === 'received' && posts().length === 3);

/* ---- K · keys ---- */
r = await run(ON, req(R, good({ living_gallery: true })));
check('K1 Living Gallery interest is not accepted (a separate initiative)', refusedAs(r, 'unexpected_field') && noCall());
for (const k of ['address', 'eircode', 'phone', 'date_of_birth', 'location_public', 'publish', 'over_18', 'terms_text', 'images']) {
  r = await run(ON, req(R, good({ [k]: 'x' })));
  check(`K2 unexpected key '${k}' refused before any call`, refusedAs(r, 'unexpected_field') && noCall());
}
for (const k of T.F25_REQUIRED) {
  r = await run(ON, req(R, without(k)));
  check(`K3 missing required '${k}' refused`, refusedAs(r, k) && noCall());
}
check('K4 the allow-list is exactly the documented 14 keys', T.F25_KEYS.size === 14);

/* ---- V · validation ---- */
const bad = [
  ['artist_name', ''], ['artist_name', 'x'.repeat(81)], ['artist_name', 42],
  ['email', 'not-an-email'], ['email', 'a@b'], ['email', 'a b@example.com'], ['email', 'x'.repeat(115) + '@e.com'],
  ['region', 'outside_ireland'], ['region', 'Dublin'], ['region', ''], ['region', 'london'],
  ['medium', 'oil'], ['medium', ['painting']],
  ['bio', 'Too short.'], ['bio', 'x'.repeat(1001)], ['bio', 12345],
  ['portfolio', 'http://example.com'], ['portfolio', 'javascript:alert(1)'], ['portfolio', 'https://user:pw@example.com'],
  ['portfolio', 'https://example.com:8443/x'], ['portfolio', 'https://localhost/x'], ['portfolio', 'example.com'],
  ['website', 'ftp://example.com'], ['website', 'not a url'],
  ['social_link', 'has spaces in it'], ['social_link', 'http://instagram.com/x'], ['social_link', '<script>'],
  ['additional_info', 'x'.repeat(801)],
  ['submission_id', 'abc'], ['submission_id', '6F1C2D3E-4B5A-4C7D-8E9F-0A1B2C3D4E5F'], ['submission_id', '6f1c2d3e-4b5a-1c7d-8e9f-0a1b2c3d4e5f']
];
for (const [k, v] of bad) {
  r = await run(ON, req(R, good({ [k]: v })));
  check(`V1 ${k}=${JSON.stringify(String(v)).slice(0, 40)} refused as '${k}'`, refusedAs(r, k) && noCall(), JSON.stringify(r.j));
}
for (const [k, v] of [['eligibility_text', 'I am over 18.'], ['ownership_text', T.F25_OWNERSHIP_TEXT + ' Also yes.'], ['privacy_text', ''],
                      ['eligibility_text', T.F25_ELIGIBILITY_TEXT.replace("I'm", 'I’m')]]) {
  r = await run(ON, req(R, good({ [k]: v })));
  check(`V2 altered '${k}' refused`, refusedAs(r, k) && noCall());
}
r = await run(ON, req(R, good({ eligibility_text: '  ' + T.F25_ELIGIBILITY_TEXT.replace(/ /g, '   ') + '\n' })));
check('V3 incidental whitespace in a confirmation still matches', r.s === 200 && r.j.state === 'received');
r = await run(ON, req(R, good({ website: '', social_link: '', additional_info: '' })));
const v4 = posts()[0].body.fields;
check('V4 empty optional fields are accepted and not written', r.s === 200 && !('website' in v4) && !('social_link' in v4) && !('additional_info' in v4));
r = await run(ON, req(R, good({ social_link: 'synthetic.artist_ie' })));
check('V5 a bare handle is stored as @handle', r.s === 200 && posts()[0].body.fields.social_link === '@synthetic.artist_ie');
r = await run(ON, req(R, good({ social_link: 'https://www.instagram.com/synthetic.artist/' })));
check('V6 an https profile link is accepted', r.s === 200 && posts()[0].body.fields.social_link === 'https://www.instagram.com/synthetic.artist/');
r = await run(ON, req(R, good({ bio: 'Line one of a synthetic biography.\r\n\r\n\r\n\r\nLine two\u0007 with   spaces and a bell.' })));
check('V7 bio: control characters removed, blank lines collapsed, line breaks kept', r.s === 200 && posts()[0].body.fields.bio === 'Line one of a synthetic biography.\n\nLine two with spaces and a bell.', JSON.stringify(posts()[0] && posts()[0].body.fields.bio));
r = await run(ON, req(R, good({ artist_name: 'Áine Ní Fhaoláin', bio: 'Saothar le hÁine. ' + 'é'.repeat(900) })));
check('V8 Irish names and accented text accepted (under the 8 KB route limit)', r.s === 200 && posts()[0].body.fields.artist_name === 'Áine Ní Fhaoláin');
r = await run(ON, req(R, good({ artist_name: '<img src=x onerror=alert(1)>' })));
check('V9 markup is stored as inert text (the Worker renders nothing)', r.s === 200 && posts()[0].body.fields.artist_name === '<img src=x onerror=alert(1)>');

/* ---- W · exactly what a permitted write sends ---- */
r = await run(ON, req(R, good({ website: 'https://example.com', social_link: '@synthetic', additional_info: 'Not represented by a gallery. Synthetic.' })));
const [app, slog, cons] = posts();
const f = app.body.fields;
check('W1 three writes in order: application, status log, consent proof', posts().length === 3 &&
  app.url.endsWith('/' + encodeURIComponent('Founding 25 applications')) && slog.url.endsWith('/' + encodeURIComponent('Status log')) && cons.url.endsWith('/' + encodeURIComponent('Consent proofs')));
check('W2 typecast:false on every write', posts().every(p => p.body.typecast === false));
check('W3 status is received (the ceiling)', f.status === 'received');
check('W4 reference format F25-YYMMDD-XXXXXX', /^F25-\d{6}-[0-9A-F]{6}$/.test(f.application_ref));
check('W5 consent recorded: privacy version, consent version, timestamp, hash', f.privacy_version === ON.F25_PRIVACY_VERSION &&
  f.consent_version === T.F25_CONSENT_VERSION && f.consent_at === f.submitted_at && /^[0-9a-f]{64}$/.test(f.consent_text_hash));
check('W6 the three confirmations recorded as true', f.eligibility_confirmed === true && f.ownership_confirmed === true && f.privacy_notice_read === true);
check('W7 email stored, email_key lower-cased', f.email === 'F25.Test@example.com' && f.email_key === 'f25.test@example.com');
check('W8 the submission id is stored', f.submission_id === SID);
check('W9 no IP, user agent, country or header data in any write', !JSON.stringify(posts()).match(/user-?agent|cf-connecting|x-forwarded|"ip"|country/i));
check('W10 the consent proof holds an email HASH only, never the address', !!cons.body.fields.email_hash && !JSON.stringify(cons.body).includes('example.com') && cons.body.fields.register === 'founding_25');
check('W11 status log: nothing -> received, system, register founding_25', slog.body.fields.to_status === 'received' && slog.body.fields.from_status === '' && slog.body.fields.actor === 'system' && slog.body.fields.register === 'founding_25');
check('W12 the token goes only in the Authorization header, only to api.airtable.com/<base>', atCalls().every(c => c.auth === 'Bearer ' + FAKE.AIRTABLE_TOKEN && c.url.startsWith('https://api.airtable.com/v0/' + FAKE.AIRTABLE_BASE + '/')));
check('W13 the reply reveals nothing but the state', JSON.stringify(r.j) === '{"ok":true,"state":"received"}');
check('W14 reply headers: no-store, nosniff, no-referrer, CORS for plotnua.ie only, no credentials', r.h.get('cache-control') === 'no-store' && r.h.get('x-content-type-options') === 'nosniff' &&
  r.h.get('referrer-policy') === 'no-referrer' && r.h.get('access-control-allow-origin') === ORIGIN && !r.h.get('access-control-allow-credentials'));

/* ---- S · schema agreement ---- */
const wFields = schema.new_table.fields.filter(x => x.writer === 'worker').map(x => x.name);
check('S1 every field the Worker writes exists in the schema as worker-written', Object.keys(f).every(k => wFields.includes(k)), Object.keys(f).filter(k => !wFields.includes(k)).join());
check('S2 every select value written is a schema option', ['region', 'medium', 'status', 'source'].every(k => sField[k].options.includes(f[k])));
check('S3 region options = the Worker vocabulary (32 counties, no outside_ireland)', JSON.stringify(sField.region.options) === JSON.stringify(T.VF.region) && T.VF.region.length === 32);
check('S4 medium options = the Worker vocabulary', JSON.stringify(sField.medium.options) === JSON.stringify(T.VF.medium));
check('S5 the six statuses, in order', JSON.stringify(sField.status.options) === JSON.stringify(['received', 'under_review', 'shortlisted', 'selected', 'not_selected', 'withdrawn']));
check('S6 A/B/C kept apart: terms acceptance and publication approval are founder-only fields', sField.terms_accepted_at.writer === 'founder' && sField.publication_approved_at.writer === 'founder' && sField.first_published_at.writer === 'founder');
check('S7 the count comes only from selected + accepted terms', /'selected'/.test(sField.counts_toward_25.formula) && /terms_accepted_at/.test(sField.counts_toward_25.formula));

/* ---- D · duplicates ---- */
existing = true;
r = await run(ON, req(R, good()));
check('D1 an email or submission id already present -> received, NOTHING written', r.s === 200 && r.j.state === 'received' && posts().length === 0);
const dupGet = calls.find(c => c.method === 'GET' && !c.url.includes('IS_AFTER'));
const formula = decodeURIComponent(dupGet.url.split('filterByFormula=')[1].split('&')[0]);
check('D2 the duplicate check matches email_key OR submission_id, in this table only', /OR\(\{email_key\}='f25\.test@example\.com',\{submission_id\}='6f1c2d3e/.test(formula) && dupGet.url.includes(encodeURIComponent('Founding 25 applications')), formula);
check('D3 a duplicate gets exactly the reply a new application gets (no enumeration)', JSON.stringify(r.j) === '{"ok":true,"state":"received"}');
existing = false;
r = await run(ON, req(R, good({ email: "o'brien@example.com" })));
const g2 = decodeURIComponent(calls.find(c => c.method === 'GET' && !c.url.includes('IS_AFTER')).url.split('filterByFormula=')[1].split('&')[0]);
check("D4 a quote in the email cannot break out of the duplicate formula", g2.includes("'o\\'brien@example.com'") && r.s === 200, g2);

/* ---- C · durable daily cap ---- */
check('C1 default cap 50; env override bounded 1-500', T.f25DailyCap({}) === 50 && T.f25DailyCap({ F25_DAILY_CAP: '100' }) === 100 &&
  T.f25DailyCap({ F25_DAILY_CAP: '0' }) === 50 && T.f25DailyCap({ F25_DAILY_CAP: '9999' }) === 50 && T.f25DailyCap({ F25_DAILY_CAP: 'x' }) === 50);
recent = 50;
r = await run(ON, req(R, good()));
check('C2 at the cap -> slow_down, nothing written', r.s === 429 && r.j.state === 'slow_down' && posts().length === 0);
recent = 2;
r = await run({ ...ON, F25_DAILY_CAP: '2' }, req(R, good()));
check('C3 a lowered test cap (2) holds', r.s === 429 && posts().length === 0);
recent = 1;
r = await run({ ...ON, F25_DAILY_CAP: '2' }, req(R, good()));
check('C4 below the cap -> received', r.s === 200 && posts().length === 3);
recent = 0;
failWith = 500;
r = await run(ON, req(R, good()));
check('C5 the cap cannot be read -> nothing written (fail closed)', r.s === 503 && posts().length === 0);
failWith = 0;
capMalformed = true;
r = await run(ON, req(R, good()));
check('C6 a cap reply without a records list -> treated as full, nothing written (fail closed)', r.s === 429 && posts().length === 0);
capMalformed = false;

/* ---- B · burst ---- */
T.resetRateLimit();
let lastF25;
for (let i = 0; i < T.F25_BURST_PER_MINUTE + 1; i++) lastF25 = await run(ON, req(R, good({ artist_name: '' })), { keepRate: true });
check('B1 the 11th Founding 25 POST within a minute -> slow_down', lastF25.s === 429 && lastF25.j.state === 'slow_down');
const hostR = await run(ON, req('/v1/art-space-register/host', {}), { keepRate: true });
check('B2 the Founding 25 burst limit does not slow the Host route', hostR.s !== 429);
T.resetRateLimit();

/* ---- E · upstream errors, controlled replies ---- */
for (const [st, reason] of [[500, 'at5xx'], [422, 'at422'], [401, 'at401'], [429, 'at429']]) {
  failWith = st;
  r = await run(ON, req(R, good()));
  check(`E1 Airtable ${st} -> unavailable '${reason}', nothing else revealed`, r.s === 503 && r.j.state === 'unavailable' && r.j.reason === reason && Object.keys(r.j).length === 3);
}
failWith = 0; netDown = true;
r = await run(ON, req(R, good()));
check('E2 Airtable unreachable -> unavailable atnet', r.s === 503 && r.j.reason === 'atnet');
netDown = false; failCreateOnly = 422;
r = await run(ON, req(R, good()));
check('E3 application write refused -> unavailable, no audit rows written', r.s === 503 && posts().length === 1);
failCreateOnly = 0; failSecondary = 500;
r = await run(ON, req(R, good()));
check('E4 stored but an audit row fails -> still received (the row holds its own consent record)', r.s === 200 && r.j.state === 'received');
failSecondary = 0;

/* ---- P · non-writing configuration probe ---- */
r = await run(COMMITTED, req(R, good({ email: 'release-check@probe.plotnua.invalid' })));
check('P1 probe, closed -> not_open, no call', notOpenNoCall(r));
r = await run(ON, req(R, good({ email: 'release-check@probe.plotnua.invalid' })));
check('P2 probe, open -> probe_open, NO Airtable call at all', r.s === 200 && r.j.state === 'probe_open' && noCall());
r = await run(ON, req(R, good({ email: 'release-check@probe.plotnua.invalid', bio: 'short' })));
check('P3 an invalid probe is refused like any application', refusedAs(r, 'bio'));

/* ---- T · optional challenge (Turnstile) ---- */
const TS = { ...ON, F25_TURNSTILE_SECRET: '0x4AAAAAAAsynthetic' };
r = await run(TS, req(R, good()));
check('T1 secret set, no token -> refused challenge, nothing written', refusedAs(r, 'challenge') && posts().length === 0);
ts = { ok: true, success: false };
r = await run(TS, req(R, good({ challenge_token: 'bad' })));
check('T2 failed challenge -> refused, nothing written', refusedAs(r, 'challenge') && posts().length === 0);
ts = 'down';
r = await run(TS, req(R, good({ challenge_token: 'tok' })));
check('T3 verifier unreachable -> refused (fail closed)', refusedAs(r, 'challenge') && posts().length === 0);
ts = { ok: true, success: true };
r = await run(TS, req(R, good({ challenge_token: 'tok' })));
const tsCall = calls.find(c => c.url.startsWith('https://challenges.cloudflare.com/'));
check('T4 valid challenge -> received', r.s === 200 && posts().length === 3);
check('T5 only the secret and the token go to the verifier, never the application', !!tsCall && JSON.stringify(Object.keys(tsCall.body).sort()) === '["response","secret"]');
r = await run(ON, req(R, good({ challenge_token: 'ignored' })));
check('T6 no secret configured -> no challenge call', r.s === 200 && !calls.some(c => c.url.includes('challenges.cloudflare.com')));

/* ---- O · origin, method, size ---- */
r = await run(ON, req(R, good(), { origin: 'https://evil.example' }));
check('O1 foreign origin -> 403, nothing called', r.s === 403 && calls.length === 0);
r = await run(ON, req(R, good(), { origin: null }));
check('O2 no origin -> 403', r.s === 403 && calls.length === 0);
r = await run(ON, req(R, good(), { site: 'same-origin' }));
check('O3 fetch-metadata same-origin -> refused', refusedAs(r) && calls.length === 0);
r = await run(ON, req(R, null, { method: 'GET' }));
check('O4 GET -> 405 (there is no read surface)', r.s === 405 && calls.length === 0);
r = await run(ON, req(R, null, { method: 'OPTIONS' }));
check('O5 preflight from plotnua.ie -> 204', r.s === 204);
r = await run(ON, req(R, null, { raw: 'x'.repeat(T.F25_MAX_BODY + 1) }));
check('O6 body over 8 KB -> refused body', refusedAs(r, 'body') && calls.length === 0);
r = await run(ON, req(R, null, { raw: '{"artist_name":' }));
check('O7 malformed JSON -> refused body', refusedAs(r, 'body'));
r = await run(ON, req(R, null, { raw: '[1,2]' }));
check('O8 an array body -> refused body', refusedAs(r, 'body'));
r = await run(ON, req('/v1/art-space-register/host', null, { raw: JSON.stringify({ first_name: 'x'.repeat(5000) }) }));
check('O9 the Host route keeps its 4 KB limit', refusedAs(r, 'body'));

/* ---- I · isolation and source ---- */
r = await run(ON, req(R, good()));
check('I1 never reads or writes the Artists or Hosts tables', !calls.some(c => /\/(Artists|Hosts)(\?|$)/.test(c.url)));
const src = readFileSync(new URL('../src/index.js', import.meta.url), 'utf8');
const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
check('I2 no console logging anywhere in the Worker', !/console\./.test(code));
check('I3 no mail adapter', !/sendgrid|resend|smtp|mailchannels|sendEmail|send_email/i.test(code));
check('I4 the router has no GET branch', !/request\.method === 'GET'/.test(code));
check('I5 request logging (observability) stays disabled', /\[observability\]\s*\nenabled = false/.test(toml));
const f25code = code.slice(code.indexOf("const T_F25"), code.indexOf('export default'));
check('I6 the Founding 25 code writes only the status constant received', (f25code.match(/[^_]status: /g) || []).length === 1 && /[^_]status: F25_STATUS/.test(f25code) && /to_status: F25_STATUS/.test(f25code) && T.F25_STATUS === 'received');

console.log('PLOTART FOUNDING 25 · WORKER PROOF v2');
console.log(out.join('\n'));
console.log(`\n  ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
