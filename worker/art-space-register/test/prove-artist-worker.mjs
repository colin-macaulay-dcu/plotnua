/* ARTIST REGISTER (PlotArt) · WORKER GUARD PROOF
 * ===========================================================================
 * The artist route, driven against a STUBBED fetch that never leaves this
 * process (the token is a fake). Every refusal is exercised deliberately,
 * then what a permitted write would send to Airtable is asserted exactly,
 * and the homeowner route is shown to be unaffected and separate.
 * Run: node worker/art-space-register/test/prove-artist-worker.mjs
 * ========================================================================= */
import worker, { __test as T } from '../src/index.js';
import { readFileSync } from 'node:fs';

let pass = 0, fail = 0;
const out = [];
const check = (name, cond, detail = '') => {
  if (cond) { pass++; out.push('  ok    ' + name); }
  else { fail++; out.push('  FAIL  ' + name + (detail ? '  — ' + detail : '')); }
};

const ORIGIN = 'https://plotnua.ie';
const BASE = { ORIGIN, EMAIL_ENABLED: 'false', PRIVACY_VERSION: '2026-10-PHASE2-V4',
               AIRTABLE_BASE: 'appARTTESTONLY0001', AIRTABLE_TOKEN: 'patFAKE_NEVER_REAL' };
/* The live posture: homeowner writes on, artist writes off. */
const LIVE = { ...BASE, WRITES_ENABLED: 'true', ARTIST_WRITES_ENABLED: 'false', ARTIST_PRIVACY_VERSION: '2026-10-PHASE2-V5' };
const ON = { ...LIVE, ARTIST_WRITES_ENABLED: 'true' };

let calls = [], existing = false, failWith = 0, recent = 0;
globalThis.fetch = async (url, init = {}) => {
  calls.push({ url: String(url), method: init.method, body: init.body ? JSON.parse(init.body) : null,
               auth: init.headers && init.headers.authorization });
  if (failWith) return new Response('{}', { status: failWith });
  if (init.method === 'GET' && String(url).includes('IS_AFTER')) {
    return new Response(JSON.stringify({ records: Array.from({ length: recent }, (_, i) => ({ id: 'recR' + i, fields: {} })) }), { status: 200 });
  }
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
const A = T.ARTIST_ROUTE, H = T.ROUTE;
const run = async (env, r) => { calls = []; T.resetRateLimit(); const res = await worker.fetch(r, env); let j = null; try { j = await res.clone().json(); } catch {} return { s: res.status, j, h: res.headers }; };
const good = (over = {}) => ({
  artist_name: 'Test Artist', email: 'Artist.Test@example.com', based_in: 'galway', reach: 'anywhere_ireland',
  disciplines: ['sculpture', 'painting'], interests: ['installation', 'display'],
  over_18: true, consent_text: T.ARTIST_CONSENT_TEXT, ...over
});
const host = (over = {}) => ({
  first_name: 'Test', email: 'Host.Test@example.com', county: 'dublin', ways: ['display'],
  over_18: true, consent_text: T.CONSENT_TEXT, source: 'property_check', ...over
});
const refusedAs = (r, field) => r.s === 400 && r.j && r.j.state === 'refused' && (field === undefined || r.j.field === field);
const posts = () => calls.filter(c => c.method === 'POST');
const onlyBase = () => calls.every(c => c.url.startsWith('https://api.airtable.com/v0/appARTTESTONLY0001/'));

/* ---- 1 · closed: the artist switch is separate ---- */
let r = await run(LIVE, req(A, good()));
check('A1 artist writes off (homeowner writes ON) -> 503 not_open, no Airtable call', r.s === 503 && r.j.state === 'not_open' && calls.length === 0);
r = await run({ ...ON, ARTIST_PRIVACY_VERSION: '' }, req(A, good()));
check('A2 no artist privacy version -> not_open, no call', r.s === 503 && calls.length === 0);
r = await run({ ...ON, AIRTABLE_TOKEN: '' }, req(A, good()));
check('A3 no token -> not_open, no call', r.s === 503 && calls.length === 0);
r = await run({ ...ON, AIRTABLE_BASE: '' }, req(A, good()));
check('A4 no base -> not_open, no call', r.s === 503 && calls.length === 0);
r = await run({ ...LIVE, WRITES_ENABLED: 'false', ARTIST_WRITES_ENABLED: 'true' }, req(H, host()));
check('A5 the artist switch never opens the homeowner route', r.s === 503 && r.j.state === 'not_open' && calls.length === 0);
r = await run(ON, req(A, good(), { origin: 'https://evil.example' }));
check('A6 foreign origin -> 403, no call', r.s === 403 && calls.length === 0);
r = await run(ON, req(A, good(), { site: 'same-origin' }));
check('A7 fetch-metadata protection applies to the artist route', refusedAs(r) && calls.length === 0);
r = await run(ON, req(A, null, { method: 'GET' }));
check('A8 GET on the artist route -> 405, no read surface', r.s === 405 && calls.length === 0);
r = await run(ON, req(A, null, { raw: 'x'.repeat(T.MAX_BODY_BYTES + 1) }));
check('A9 oversized body refused', refusedAs(r, 'body') && calls.length === 0);

/* ---- 2 · separate allow-list, refused before the switch ---- */
for (const k of ['first_name', 'county', 'ways', 'host_note', 'source', 'address', 'eircode', 'phone', 'surname',
                 'website', 'public_profile', 'price', 'photo', 'instagram']) {
  const ro = await run(LIVE, req(A, good({ [k]: 'x' })));
  check('K ' + k + ' refused on the artist route, writes off', refusedAs(ro, 'unexpected_field') && calls.length === 0);
}
r = await run(LIVE, req(H, host({ artist_name: 'x' })));
check('K artist_name refused on the homeowner route', refusedAs(r, 'unexpected_field') && calls.length === 0);

/* ---- 3 · required fields and invalid values ---- */
const cases = [
  ['artist_name', { artist_name: '   ' }], ['email', { email: 'not-an-email' }], ['email', { email: '' }],
  ['based_in', { based_in: 'atlantis' }], ['based_in', { based_in: '' }],
  ['reach', { reach: 'worldwide' }],
  ['reach_places', { reach: 'particular_places', reach_places: 7 }],
  ['disciplines', { disciplines: [] }], ['disciplines', { disciplines: ['painting', 'painting'] }],
  ['disciplines', { disciplines: 'painting' }], ['disciplines', { disciplines: ['dance'] }],
  ['interests', { interests: [] }], ['interests', { interests: ['studio'] }], ['interests', { interests: ['commission'] }],
  ['needs', { needs: [] }], ['needs', { needs: ['garage'] }],
  ['portfolio', { portfolio: 'http://example.com' }], ['portfolio', { portfolio: 'javascript:alert(1)' }],
  ['portfolio', { portfolio: 'https://user:pw@example.com' }], ['portfolio', { portfolio: 'https://example.com:8443/x' }],
  ['portfolio', { portfolio: 'https://localhost/x' }], ['portfolio', { portfolio: 'https://exa mple.com' }],
  ['portfolio', { portfolio: 'https://example.com/' + 'a'.repeat(200) }],
  ['statement', { statement: 42 }],
  ['over_18', { over_18: false }], ['over_18', { over_18: 'true' }],
  ['consent_text', { consent_text: 'I agree.' }],
  ['consent_text', { consent_text: T.CONSENT_TEXT }],
  ['consent_text', { consent_text: T.ARTIST_CONSENT_TEXT.replace('withdraw', 'revoke') }]
];
for (const [f, o] of cases) {
  const rr = await run(ON, req(A, good(o)));
  check('F ' + f + ' ' + JSON.stringify(o).slice(0, 56), refusedAs(rr, f) && calls.length === 0, JSON.stringify(rr.j));
}
for (const k of ['artist_name', 'email', 'based_in', 'reach', 'disciplines', 'interests']) {
  const b = good(); delete b[k];
  const rr = await run(ON, req(A, b));
  check('F ' + k + ' required', refusedAs(rr, k) && calls.length === 0);
}
r = await run(ON, req(H, host({ consent_text: T.ARTIST_CONSENT_TEXT })));
check('C1 the artist consent sentence is refused on the homeowner route', refusedAs(r, 'consent_text'));
r = await run(LIVE, req(A, good({ consent_text: '  ' + T.ARTIST_CONSENT_TEXT.replace(/ /g, '  ') + ' ' })));
check('C2 incidental whitespace still matches (reaches the closed switch)', r.s === 503 && r.j.state === 'not_open');
check('C3 the artist consent names PlotArt and withdrawal, and differs from the homeowner one',
  /PlotArt/.test(T.ARTIST_CONSENT_TEXT) && /withdraw my consent at any time/.test(T.ARTIST_CONSENT_TEXT) &&
  T.ARTIST_CONSENT_TEXT !== T.CONSENT_TEXT);
check('C4 the artist consent is the founder wording of 14 Oct 2026, ASCII only, character for character',
  T.ARTIST_CONSENT_TEXT === 'I confirm that I am 18 or over and consent to PlotNua storing my Artist Register details and ' +
  'contacting me about the development of PlotArt and potential opportunities to connect with homeowners. I understand ' +
  'that registering does not guarantee an opportunity and that I can withdraw my consent at any time.' &&
  /^[\x20-\x7e]+$/.test(T.ARTIST_CONSENT_TEXT));
const v5 = readFileSync(new URL('../../../governance/PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md', import.meta.url), 'utf8');
check('C5 the V5 draft carries the same consent sentence', v5.includes(T.ARTIST_CONSENT_TEXT));
for (const ok of ['outside_ireland', 'antrim', 'derry', 'tyrone']) {
  const rr = await run(LIVE, req(A, good({ based_in: ok })));
  check('L based_in ' + ok + ' accepted (32 counties or outside Ireland)', rr.s === 503 && rr.j.state === 'not_open');
}
check('L based_in lists exactly 32 counties plus outside_ireland',
  T.VA.based_in.length === 33 && T.VA.based_in.includes('outside_ireland') && new Set(T.VA.based_in).size === 33);

/* ---- 4 · a permitted write ---- */
existing = false;
r = await run(ON, req(A, good({ reach: 'particular_places', reach_places: '  Galway and   Mayo ',
  needs: ['outdoor', 'wall'], portfolio: 'https://example.ie/work', statement: '  Large   outdoor sculpture. ' })));
const P = posts();
const art = P.find(c => c.url.endsWith('/Artists'));
const log = P.find(c => c.url.endsWith('/Status%20log'));
const proof = P.find(c => c.url.endsWith('/Consent%20proofs'));
check('P1 received', r.s === 200 && r.j.state === 'received');
check('P2 two lookups (cap, duplicate) on Artists only, three creates, all in the one base',
  calls.length === 5 && onlyBase() && calls.filter(c => c.method === 'GET').every(c => c.url.includes('/Artists?')));
check('P3 no Hosts read or write from the artist route', !calls.some(c => c.url.includes('/Hosts')));
check('P4 every create has typecast:false', P.every(c => c.body.typecast === false));
const af = art && art.body.records[0].fields;
const allowedOut = ['artist_name', 'email', 'email_key', 'based_in', 'reach', 'reach_places', 'disciplines', 'interests',
  'needs', 'portfolio', 'statement', 'over_18', 'status', 'submitted_at', 'privacy_version', 'consent_text_hash'];
check('P5 Artists row carries only the listed fields', af && Object.keys(af).every(k => allowedOut.includes(k)), af && Object.keys(af).join(','));
check('P6 status ceiling: interest_submitted only', af && af.status === 'interest_submitted');
check('P7 multi-selects in canonical order', af && JSON.stringify(af.disciplines) === '["painting","sculpture"]' &&
  JSON.stringify(af.interests) === '["display","installation"]' && JSON.stringify(af.needs) === '["wall","outdoor"]');
check('P8 email_key lower-cased; text whitespace collapsed',
  af && af.email_key === 'artist.test@example.com' && af.reach_places === 'Galway and Mayo' && af.statement === 'Large outdoor sculpture.');
check('P9 portfolio stored as a normalised https URL', af && af.portfolio === 'https://example.ie/work');
check('P10 artist privacy version recorded (V5), not the homeowner one', af && af.privacy_version === '2026-10-PHASE2-V5');
const pf = proof && proof.body.records[0].fields;
check('P11 consent proof: hash, never the address, marked register=artist',
  pf && /^[0-9a-f]{64}$/.test(pf.email_hash) && !JSON.stringify(pf).includes('@') && pf.register === 'artist' &&
  Object.keys(pf).sort().join() === 'consent_text_hash,email_hash,given_at,privacy_version,register');
const lf = log && log.body.records[0].fields;
check('P12 status log: nothing -> interest_submitted, system, register=artist',
  lf && lf.to_status === 'interest_submitted' && lf.actor === 'system' && lf.register === 'artist');
check('P13 one timestamp across the three rows (the deletion key)', af && pf && lf && af.submitted_at === pf.given_at && pf.given_at === lf.at);
check('P14 token sent only to Airtable, as a bearer', calls.every(c => c.auth === 'Bearer patFAKE_NEVER_REAL'));

r = await run(ON, req(A, good({ reach_places: 'Cork' })));
const af2 = posts().find(c => c.url.endsWith('/Artists')).body.records[0].fields;
check('O1 places are kept only when reach = particular_places; absent optionals not written',
  !('reach_places' in af2) && !('needs' in af2) && !('portfolio' in af2) && !('statement' in af2));

/* ---- 5 · duplicates, cap, upstream ---- */
existing = true;
r = await run(ON, req(A, good()));
check('D1 repeat address -> the same "received", nothing written (no oracle)', r.s === 200 && r.j.state === 'received' && posts().length === 0);
existing = false;
recent = T.ARTIST_DAILY_CAP;
r = await run(ON, req(A, good()));
check('CAP1 at the artist cap -> slow_down, nothing created', r.s === 429 && r.j.state === 'slow_down' && posts().length === 0);
const capQ = calls.find(c => c.method === 'GET' && c.url.includes('IS_AFTER'));
check('CAP2 the artist cap counts the Artists table, at most 25 rows of one field',
  capQ && capQ.url.includes('/Artists?') && capQ.url.includes('maxRecords=25') && capQ.url.includes('fields%5B%5D=submitted_at'));
check('CAP3 the artist cap is 25', T.ARTIST_DAILY_CAP === 25);
recent = T.ARTIST_DAILY_CAP - 1;
r = await run(ON, req(A, good()));
check('CAP4 one below the cap -> received', r.s === 200 && posts().length === 3);
recent = 0;
r = await run(ON, req(H, host()));
const hcap = calls.find(c => c.method === 'GET' && c.url.includes('IS_AFTER'));
check('CAP5 the homeowner cap still counts Hosts only', hcap && hcap.url.includes('/Hosts?') && !calls.some(c => c.url.includes('/Artists')));
failWith = 422;
r = await run(ON, req(A, good()));
check('U1 Airtable 422 -> unavailable, status class only', r.s === 503 && r.j.state === 'unavailable' && r.j.reason === 'at422');
failWith = 401;
r = await run(ON, req(A, good()));
check('U2 Airtable 401 -> unavailable at401, no detail', r.s === 503 && r.j.reason === 'at401' && Object.keys(r.j).length === 3);
failWith = 0;
T.resetRateLimit();
let last;
for (let i = 0; i < 31; i++) last = await worker.fetch(req(A, good()), LIVE);
check('RL1 the burst limit applies to the artist route', last.status === 429);
T.resetRateLimit();

/* ---- 6 · the homeowner route is unchanged ---- */
r = await run(ON, req(H, host()));
const hp = posts();
const hrow = hp.find(c => c.url.endsWith('/Hosts'));
const hproof = hp.find(c => c.url.endsWith('/Consent%20proofs'));
const hlog = hp.find(c => c.url.endsWith('/Status%20log'));
check('H1 homeowner registration still received, writing Hosts / Status log / Consent proofs',
  r.s === 200 && hrow && hproof && hlog && hp.length === 3);
check('H2 homeowner rows carry no register field and the V4 version (unchanged)',
  !('register' in hproof.body.records[0].fields) && !('register' in hlog.body.records[0].fields) &&
  hrow.body.records[0].fields.privacy_version === '2026-10-PHASE2-V4');
check('H3 homeowner write never touches Artists', !calls.some(c => c.url.includes('/Artists')));

/* ---- 7 · source and configuration ---- */
const src = readFileSync(new URL('../src/index.js', import.meta.url), 'utf8');
const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
check('S1 no mail adapter', !/sendgrid|resend|smtp|mailchannels|sendEmail|send_email/i.test(code));
check('S2 no matching, booking, payment or public-profile code', !/qualified|introduc|matched|booked|payment|commission|profile|publish/i.test(code));
check('S3 no console logging', !/console\./.test(code));
const artistCode = code.slice(code.indexOf('const T_ARTISTS'), code.indexOf('export default'));
check('S4 the artist code never names the Hosts table or the homeowner vocabularies',
  artistCode.length > 1000 && !/T_HOSTS|\bV\.|ALLOWED_KEYS\.includes|CONSENT_TEXT\b(?!_)/.test(artistCode.replace(/ARTIST_ALLOWED_KEYS|ARTIST_CONSENT_TEXT/g, '')));
const toml = readFileSync(new URL('../wrangler.toml', import.meta.url), 'utf8');
check('S5 wrangler: the artist register ships CLOSED', /^ARTIST_WRITES_ENABLED\s*=\s*"false"/m.test(toml));
check('S6 wrangler: artist privacy version is V5; homeowner stays V4',
  /^ARTIST_PRIVACY_VERSION\s*=\s*"2026-10-PHASE2-V5"/m.test(toml) && /^PRIVACY_VERSION\s*=\s*"2026-10-PHASE2-V4"/m.test(toml));
check('S7 no secret, token or base id in wrangler.toml', !/pat[A-Za-z0-9]{10}|app[A-Za-z0-9]{14}/.test(toml));
const schema = JSON.parse(readFileSync(new URL('../airtable-schema.json', import.meta.url), 'utf8'));
const tbl = (n) => schema.tables.find(t => t.name === n);
const artistsT = tbl('Artists');
check('S8 schema: an Artists table, separate from Hosts', !!artistsT && !!tbl('Hosts'));
const sf = Object.fromEntries((artistsT ? artistsT.fields : []).map(f => [f.name, f]));
check('S9 schema carries every field the artist route writes', allowedOut.every(k => k in sf));
check('S10 schema options equal the Worker vocabularies',
  ['based_in', 'reach', 'disciplines', 'interests', 'needs'].every(k => JSON.stringify(sf[k] && sf[k].options) === JSON.stringify(T.VA[k])) &&
  JSON.stringify(sf.status && sf.status.options) === '["interest_submitted"]');
check('S11 schema: register field on Status log, Consent proofs and Deletion log',
  ['Status log', 'Consent proofs', 'Deletion log'].every(n => tbl(n).fields.some(f => f.name === 'register' && JSON.stringify(f.options) === '["host","artist"]')));
check('S12 schema: Artists erase_after flags at 12 months', sf.erase_after && sf.erase_after.formula === "DATEADD({submitted_at}, 12, 'months')");

console.log(out.join('\n'));
console.log('\n  ' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
