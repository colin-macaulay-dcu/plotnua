/* G6 · R3 — DEPRECATED PROPERTY CHECK FIELDS ARE REFUSED, AND NOTHING IS STORED
 * ===========================================================================
 * Founder instruction, 12 October 2026. Drives the REAL Worker (src/index.js)
 * with the write switch ON and a STUB Airtable that records every call. With
 * writes on, a request that is not refused WOULD reach Airtable, so "zero
 * Airtable calls" is a measured fact about a refusal rather than a by-product
 * of the switch being off. The stub never touches the network.
 *
 *   D1  legitimate registrations still work (own, rent with permission, buying)
 *   D2  required tenure is preserved, exactly as sent
 *   D3  the renter-permission safeguard still refuses
 *   D4  each deprecated key is refused — alone, with any value, and together
 *   D5  every refused request makes ZERO Airtable calls
 *   D6  consent verification is still enforced
 *   D7  status ceiling, privacy version, consent-proof shape, typecast,
 *       origin and the write switch are intact, ranged over EVERY write made
 *
 *   node test/prove-g6-deprecated-fields.mjs
 * ========================================================================= */
import worker, { __test as T } from '../src/index.js';

let pass = 0, fail = 0;
const check = (name, cond, detail) => {
  if (cond) { pass++; console.log('  [PASS] ' + name); }
  else { fail++; console.log('  [FAIL] ' + name + (detail ? '   ' + detail : '')); }
};

const ORIGIN = 'https://plotnua.ie';
const ENV_ON = {
  ORIGIN, WRITES_ENABLED: 'true', EMAIL_ENABLED: 'false',
  PRIVACY_VERSION: '2026-10-PHASE2-V3',
  PILOT_DISTRICTS: 'raheny,killester,donnycarney,artane',
  AIRTABLE_BASE: 'appSTUBSTUBSTUB00', AIRTABLE_TOKEN: 'patSTUB_NEVER_REAL'
};
const ENV_OFF = { ...ENV_ON, WRITES_ENABLED: 'false' };
const CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.";
const DEPRECATED = ['inherited_spare_corner', 'inherited_way_in',
                    'inherited_your_own_use', 'inherited_result_key'];

/* ---- stub Airtable: records every call; never the network --------------- */
let calls = [];
let rec = 0;
globalThis.fetch = async (url, opts = {}) => {
  const u = String(url);
  if (!u.startsWith('https://api.airtable.com/')) throw new Error('unexpected fetch ' + u);
  const body = opts.body ? JSON.parse(opts.body) : null;
  calls.push({ method: opts.method, url: u, body });
  const ok = (j) => ({ ok: true, status: 200, json: async () => j });
  if (opts.method === 'GET') return ok({ records: [] });           // no existing address
  return ok({ records: [{ id: 'recSTUB' + (++rec) }] });
};

/* ---- the rate limiter is per-isolate (30/min). Time is advanced past its
   window before every request so this suite measures the handler, not the
   limiter. Only Date.now is moved; the handler's own `new Date()` is real. */
const realNow = Date.now; let skew = 0;
Date.now = () => realNow() + skew;

function req(body, { origin = ORIGIN } = {}) {
  skew += 61_000;
  const h = { 'content-type': 'application/json', 'sec-fetch-site': 'cross-site',
              'sec-fetch-mode': 'cors' };
  if (origin) h.origin = origin;
  return new Request('https://w.example/v1/garden-register/garden',
    { method: 'POST', headers: h, body: JSON.stringify(body) });
}
async function send(env, body, opt) {
  calls = [];
  const r = await worker.fetch(req(body, opt), env);
  let j = null; try { j = await r.json(); } catch {}
  return { status: r.status, j, calls: calls.slice() };
}
const base = (over = {}) => ({
  first_name: 'Test', email: 'g6.r3@example.com', district: 'raheny',
  water: 'outside_tap', size_note: 'small', timing: 'flexible',
  inherited_tenure: 'own', over_18: true, consent_text: CONSENT,
  source: 'garden_interest', ...over
});
const RENT_OK = { inherited_tenure: 'rent', permission_confirmed: true,
                  garden_note: 'My landlord knows and has agreed to it.' };
const gardensWrite = (cs) => cs.find((c) => c.method === 'POST' && /\/Gardens$/.test(c.url));
const allWrites = [];   // every Airtable create made by an ACCEPTED request, for D7

/* ======================================================== D1 · D2 ======== */
for (const [label, over] of [['own', {}], ['rent with permission', RENT_OK],
                             ['buying', { inherited_tenure: 'buying' }]]) {
  const r = await send(ENV_ON, base(over));
  const g = gardensWrite(r.calls);
  allWrites.push(...r.calls.filter((c) => c.method === 'POST'));
  check(`D1 a legitimate ${label} registration is received`,
    r.status === 200 && r.j && r.j.state === 'received', JSON.stringify(r.j));
  check(`D1b ${label}: exactly one Gardens record is written`,
    r.calls.filter((c) => c.method === 'POST' && /\/Gardens$/.test(c.url)).length === 1);
  const f = g && g.body.records[0].fields;
  check(`D2 ${label}: inherited_tenure is stored exactly as sent`,
    !!f && f.inherited_tenure === (over.inherited_tenure || 'own'), f && f.inherited_tenure);
  if (label === 'rent with permission') {
    check('D2b rent: permission_confirmed and the statement are stored',
      !!f && f.permission_confirmed === true && /landlord knows/.test(f.garden_note || ''));
  }
}

/* ============================================================ D3 ========= */
for (const [label, over, field] of [
    ['rent without the permission tick', { inherited_tenure: 'rent', garden_note: RENT_OK.garden_note }, 'permission_confirmed'],
    ['rent with the tick but no statement', { inherited_tenure: 'rent', permission_confirmed: true }, 'garden_note'],
    ['tenure absent', { inherited_tenure: undefined }, 'inherited_tenure'],
    ['tenure not in the vocabulary', { inherited_tenure: 'squatting' }, 'inherited_tenure']]) {
  const r = await send(ENV_ON, base(over));
  check(`D3 ${label} is refused on ${field}, nothing written`,
    r.status === 400 && r.j.state === 'refused' && r.j.field === field && r.calls.length === 0,
    `${r.status} ${JSON.stringify(r.j)} calls=${r.calls.length}`);
}

/* ======================================================== D4 · D5 ======== */
const VALUES = { valid: { inherited_spare_corner: 'yes_a_clear_corner', inherited_way_in: 'its_own_gate',
                          inherited_your_own_use: 'now_and_then', inherited_result_key: 'ARRANGEMENT' } };
for (const k of DEPRECATED) {
  for (const [vlabel, v] of [['a valid value', VALUES.valid[k]], ['an empty string', ''],
                             ['null', null], ['a junk value', 'zzz']]) {
    const r = await send(ENV_ON, base({ [k]: v }));
    check(`D4 ${k} with ${vlabel} is refused, naming the key`,
      r.status === 400 && r.j && r.j.state === 'refused' && r.j.field === k,
      `${r.status} ${JSON.stringify(r.j)}`);
    check(`D5 ${k} with ${vlabel}: ZERO Airtable calls`, r.calls.length === 0,
      'calls=' + r.calls.length);
  }
  /* For a renter too: the refusal is not something the tenure path skips. */
  const rr = await send(ENV_ON, base({ ...RENT_OK, [k]: VALUES.valid[k] }));
  check(`D4b ${k} is refused for a valid renter as well`,
    rr.status === 400 && rr.j.field === k && rr.calls.length === 0);
}
const all4 = await send(ENV_ON, base(VALUES.valid));
check('D4c all four together are refused, nothing written',
  all4.status === 400 && DEPRECATED.includes(all4.j.field) && all4.calls.length === 0);
/* Refusal is explicit even while the register is closed: a deprecated key
   gets 400 refused, never a 503 not_open that would hide the reason. */
const offR = await send(ENV_OFF, base({ inherited_result_key: 'ARRANGEMENT' }));
check('D4d with writes OFF the refusal is still explicit (400, not 503 not_open)',
  offR.status === 400 && offR.j.field === 'inherited_result_key' && offR.calls.length === 0);
/* Invalid AND deprecated: the deprecated key is the reason given, so a caller
   cannot mistake the refusal for an ordinary validation slip. */
const both = await send(ENV_ON, base({ email: 'nope', inherited_way_in: 'its_own_gate' }));
check('D4e the deprecated key is refused ahead of ordinary validation',
  both.status === 400 && both.j.field === 'inherited_way_in');
/* A key that merely resembles one is not refused — the check is exact. */
const near = await send(ENV_ON, base({ inherited_tenure_note: 'x' }));
check('D4f a non-deprecated unknown key is not mistaken for one (accepted, ignored)',
  near.status === 200 && near.j.state === 'received');
allWrites.push(...near.calls.filter((c) => c.method === 'POST'));
check('D4g the Worker exposes exactly these four as deprecated',
  /const DEPRECATED_GARDEN_KEYS = Object\.freeze\(\[\s*'inherited_spare_corner', 'inherited_way_in',\s*'inherited_your_own_use', 'inherited_result_key'\s*\]\);/
    .test(await (await import('node:fs/promises')).readFile(new URL('../src/index.js', import.meta.url), 'utf8')));

/* ============================================================ D6 ========= */
for (const [label, c] of [['altered', CONSENT.replace('over 18', 'over 16')],
                          ['the grower sentence', T.CONSENT_TEXT.grower], ['empty', '']]) {
  const r = await send(ENV_ON, base({ consent_text: c }));
  check(`D6 ${label} consent is refused, nothing written`,
    r.status === 400 && r.j.field === 'consent_text' && r.calls.length === 0);
}
const o18 = await send(ENV_ON, base({ over_18: false }));
check('D6b over_18 false is refused, nothing written',
  o18.status === 400 && o18.j.field === 'over_18' && o18.calls.length === 0);

/* ============================================================ D7 ========= */
check('D7pre accepted requests produced writes to range over',
  allWrites.length >= 12, 'writes=' + allWrites.length);
const gw = allWrites.filter((c) => /\/Gardens$/.test(c.url)).map((c) => c.body.records[0].fields);
check('D7a every Gardens write has status interest_submitted',
  gw.length === 4 && gw.every((f) => f.status === 'interest_submitted'), 'n=' + gw.length);
check('D7b no Gardens write carries any deprecated key',
  gw.every((f) => DEPRECATED.every((k) => !(k in f))));
check('D7c every Gardens write carries privacy_version from the environment (V3)',
  gw.every((f) => f.privacy_version === '2026-10-PHASE2-V3'));
const cp = allWrites.filter((c) => /Consent%20proofs$/.test(c.url)).map((c) => c.body.records[0].fields);
check('D7d every consent proof holds exactly four fields, an email HASH and no address',
  cp.length === 4 && cp.every((f) =>
    Object.keys(f).sort().join() === 'consent_text_hash,email_hash,given_at,privacy_version' &&
    /^[0-9a-f]{64}$/.test(f.email_hash) && !JSON.stringify(f).includes('@')));
check('D7e every create is sent with typecast:false',
  allWrites.every((c) => c.body.typecast === false));
const sl = allWrites.filter((c) => /Status%20log$/.test(c.url)).map((c) => c.body.records[0].fields);
check('D7f every status-log row moves from nothing to interest_submitted only',
  sl.length === 4 && sl.every((f) => f.from_status === '' && f.to_status === 'interest_submitted'));
const badOrigin = await send(ENV_ON, base(), { origin: 'https://plotnua.ie.evil.example' });
check('D7g a foreign origin is refused 403, nothing written',
  badOrigin.status === 403 && badOrigin.calls.length === 0);
const closed = await send(ENV_OFF, base());
check('D7h with the switch off a valid registration is not_open, nothing written',
  closed.status === 503 && closed.j.state === 'not_open' && closed.calls.length === 0);

/* ============================================================ D8 =========
   THE SECOND LAYER. With the refusal in place a re-added write line would
   never execute, so no request can observe it; it is asserted on the source.
   Comments are stripped first — the deprecation note names the keys, and a
   guard that punished its own documentation was a mistake made once already. */
{
  const srcText = await (await import('node:fs/promises')).readFile(
    new URL('../src/index.js', import.meta.url), 'utf8');
  const listM = /const DEPRECATED_GARDEN_KEYS = Object\.freeze\(\[[\s\S]*?\]\);/.exec(srcText);
  const code = (listM ? srcText.replace(listM[0], '') : srcText)
    .replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  for (const k of DEPRECATED) {
    check(`D8 ${k} is not read or written anywhere outside the deprecated list`,
      !!listM && !code.includes(k));
  }
}

Date.now = realNow;
console.log(`\n  ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
