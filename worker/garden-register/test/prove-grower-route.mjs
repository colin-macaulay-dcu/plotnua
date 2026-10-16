/* GROWER REGISTER · THE GROWER ROUTE'S OWN SWITCHES (16 October 2026)
 * ===========================================================================
 * Drives the REAL Worker with a STUB Airtable that records every call and
 * never touches the network. With the switches on, a request that is not
 * refused WOULD reach Airtable, so "zero Airtable calls" is a measured fact.
 *
 *   R1  the grower route is closed by default, even with the garden route open
 *   R2  each grower stop works on its own (switch, privacy version, base writes)
 *   R3  the garden route is unaffected by the grower switches
 *   R4  strict keys: anything outside the allow-list is refused, nothing written
 *   R5  an accepted registration writes Growers + Status log + Consent proof,
 *       carrying GROWER_PRIVACY_VERSION, typecast:false, status ceiling
 *   R6  a repeat address gets the same "received" and writes nothing
 *   R7  validation and the frozen consent sentence are still enforced
 *
 *   node test/prove-grower-route.mjs
 * ========================================================================= */
import worker, { __test as T } from '../src/index.js';

let pass = 0, fail = 0;
const check = (name, cond, detail) => {
  if (cond) { pass++; console.log('  [PASS] ' + name); }
  else { fail++; console.log('  [FAIL] ' + name + (detail ? '   ' + detail : '')); }
};

const ORIGIN = 'https://plotnua.ie';
const GROWER_PV = '2026-10-PHASE2-V6';
/* The production state today: garden route open, grower route shipped closed. */
const ENV_PROD = {
  ORIGIN, WRITES_ENABLED: 'true', EMAIL_ENABLED: 'false',
  PRIVACY_VERSION: '2026-10-PHASE2-V3', PILOT_DISTRICTS: 'raheny,killester,donnycarney,artane',
  GROWER_WRITES_ENABLED: 'false', GROWER_PRIVACY_VERSION: '',
  AIRTABLE_BASE: 'appSTUBSTUBSTUB00', AIRTABLE_TOKEN: 'patSTUB_NEVER_REAL'
};
const ENV_OPEN = { ...ENV_PROD, GROWER_WRITES_ENABLED: 'true', GROWER_PRIVACY_VERSION: GROWER_PV };
const GROWER_CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me about possible growing space nearby.";
const GARDEN_CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.";

/* ---- stub Airtable ------------------------------------------------------- */
let calls = [], rec = 0, existing = new Set();
globalThis.fetch = async (url, opts = {}) => {
  const u = String(url);
  if (!u.startsWith('https://api.airtable.com/')) throw new Error('unexpected fetch ' + u);
  const body = opts.body ? JSON.parse(opts.body) : null;
  calls.push({ method: opts.method, url: u, body });
  const ok = (j) => ({ ok: true, status: 200, json: async () => j });
  if (opts.method === 'GET') {
    const m = /email_key%7D%3D'([^']*)'|email_key\}='([^']*)'/.exec(decodeURIComponent(u));
    const key = m && (m[1] || m[2]);
    return ok({ records: key && existing.has(key) ? [{ id: 'recEXIST' }] : [] });
  }
  const f = body && body.records && body.records[0] && body.records[0].fields;
  if (/\/(Growers|Gardens)$/.test(u) && f && f.email_key) existing.add(f.email_key);
  return ok({ records: [{ id: 'recSTUB' + (++rec) }] });
};
const realNow = Date.now; let skew = 0;
Date.now = () => realNow() + skew;

function req(path, body, extraHeaders = {}) {
  skew += 61_000;
  return new Request('https://w.example' + path, {
    method: 'POST',
    headers: { 'content-type': 'application/json', origin: ORIGIN, 'sec-fetch-site': 'cross-site',
               'sec-fetch-mode': 'cors', ...extraHeaders },
    body: JSON.stringify(body)
  });
}
async function send(env, body, path = '/v1/garden-register/grower') {
  calls = [];
  const r = await worker.fetch(req(path, body), env);
  let j = null; try { j = await r.json(); } catch {}
  return { status: r.status, j, calls: calls.slice() };
}
let n = 0;
const grower = (over = {}) => ({
  first_name: 'Testgrower', email: `grower.${++n}@example.com`, county: 'dublin', district: 'raheny',
  town_area: 'Raheny village', travel_distance: 'up_to_5km', space_wanted: 'small', timing: 'flexible',
  over_18: true, consent_text: GROWER_CONSENT, source: 'grower_register', ...over
});
const garden = (over = {}) => ({
  first_name: 'Testhost', email: `host.${++n}@example.com`, district: 'artane',
  water: 'outside_tap', size_note: 'small', timing: 'flexible', inherited_tenure: 'own',
  over_18: true, consent_text: GARDEN_CONSENT, source: 'garden_interest', ...over
});
const isNotOpen = (r) => r.status === 503 && r.j && r.j.state === 'not_open';

/* ============================================================ R1 · R2 ==== */
{
  const r = await send(ENV_PROD, grower());
  check('R1 production state: a valid grower gets not_open', isNotOpen(r), JSON.stringify(r.j));
  check('R1b production state: ZERO Airtable calls for the grower', r.calls.length === 0, r.calls.length);
}
for (const [label, env] of [
  ['GROWER_WRITES_ENABLED absent', { ...ENV_OPEN, GROWER_WRITES_ENABLED: undefined }],
  ['GROWER_WRITES_ENABLED "TRUE" (not exactly "true")', { ...ENV_OPEN, GROWER_WRITES_ENABLED: 'TRUE' }],
  ['GROWER_PRIVACY_VERSION empty', { ...ENV_OPEN, GROWER_PRIVACY_VERSION: '' }],
  ['GROWER_PRIVACY_VERSION whitespace', { ...ENV_OPEN, GROWER_PRIVACY_VERSION: '   ' }],
  ['GROWER_PRIVACY_VERSION absent', { ...ENV_OPEN, GROWER_PRIVACY_VERSION: undefined }],
  ['base WRITES_ENABLED off', { ...ENV_OPEN, WRITES_ENABLED: 'false' }],
  ['no token', { ...ENV_OPEN, AIRTABLE_TOKEN: '' }],
  ['no base', { ...ENV_OPEN, AIRTABLE_BASE: '' }]]) {
  const r = await send(env, grower());
  check(`R2 ${label}: not_open and zero Airtable calls`, isNotOpen(r) && r.calls.length === 0,
        `${r.status} ${JSON.stringify(r.j)} calls=${r.calls.length}`);
}
check('R2b growerWritesEnabled is true only with all five conditions', T.growerWritesEnabled(ENV_OPEN) === true &&
      T.growerWritesEnabled(ENV_PROD) === false);

/* ================================================================= R3 ==== */
{
  const r = await send(ENV_PROD, garden(), '/v1/garden-register/garden');
  check('R3 garden route still writes in the production state (grower closed)',
    r.status === 200 && r.j.state === 'received' && r.calls.some((c) => /\/Gardens$/.test(c.url)));
  const g = r.calls.find((c) => /\/Gardens$/.test(c.url) && c.method === 'POST');
  check('R3b garden record keeps the GARDEN privacy version (V3), not the grower one',
    g && g.body.records[0].fields.privacy_version === '2026-10-PHASE2-V3');
  const cp = r.calls.find((c) => /Consent%20proofs$/.test(c.url));
  check('R3c garden consent proof keeps V3', cp && cp.body.records[0].fields.privacy_version === '2026-10-PHASE2-V3');
  const r2 = await send(ENV_OPEN, garden(), '/v1/garden-register/garden');
  check('R3d opening the grower route changes nothing for gardens',
    r2.status === 200 && r2.calls.find((c) => /\/Gardens$/.test(c.url)).body.records[0].fields.privacy_version === '2026-10-PHASE2-V3');
}

/* ================================================================= R4 ==== */
for (const k of ['newsletter_consent', 'surname', 'last_name', 'address', 'eircode', 'phone',
                 'website', 'experience', 'inherited_tenure', 'status', 'privacy_version']) {
  const r = await send(ENV_OPEN, grower({ [k]: k === 'newsletter_consent' ? true : 'x' }));
  check(`R4 extra key "${k}" refused by name, zero Airtable calls`,
    r.status === 400 && r.j.field === k && r.calls.length === 0, `${r.status} ${JSON.stringify(r.j)} ${r.calls.length}`);
}
{
  const r = await send(ENV_PROD, grower({ phone: '0870000000' }));
  check('R4b strict keys fire BEFORE the switch (closed route still names the key)',
    r.status === 400 && r.j.field === 'phone');
  check('R4c allow-list is exactly the twelve documented keys',
    JSON.stringify([...T.GROWER_ALLOWED_KEYS].sort()) === JSON.stringify(
      ['consent_text','county','district','email','first_name','growing_note','over_18','source','space_wanted','timing','town_area','travel_distance']));
}

/* ================================================================= R5 ==== */
{
  const body = grower({ growing_note: 'Beginner. Would love to grow salad and herbs, weekend mornings.' });
  const r = await send(ENV_OPEN, body);
  check('R5 open route: a valid grower is received', r.status === 200 && r.j.state === 'received', JSON.stringify(r.j));
  const posts = r.calls.filter((c) => c.method === 'POST');
  const gw = posts.find((c) => /\/Growers$/.test(c.url));
  const sl = posts.find((c) => /Status%20log$/.test(c.url));
  const cp = posts.find((c) => /Consent%20proofs$/.test(c.url));
  check('R5b exactly three writes: Growers, Status log, Consent proofs', posts.length === 3 && gw && sl && cp,
        posts.map((p) => p.url.split('/').pop()).join(','));
  check('R5c nothing is written to Gardens', !posts.some((c) => /\/Gardens$/.test(c.url)));
  const f = gw && gw.body.records[0].fields;
  check('R5d grower record carries GROWER_PRIVACY_VERSION', f && f.privacy_version === GROWER_PV);
  check('R5e status is interest_submitted only', f && f.status === 'interest_submitted');
  check('R5f email_key is lower-cased', f && f.email_key === body.email.toLowerCase());
  check('R5g note stored; no newsletter field written', f && /salad/.test(f.growing_note) && !('newsletter_consent' in f));
  check('R5h source is grower_register', f && f.source === 'grower_register');
  check('R5i consent proof: V6, 64-hex hash, no address', cp && cp.body.records[0].fields.privacy_version === GROWER_PV &&
        /^[0-9a-f]{64}$/.test(cp.body.records[0].fields.email_hash) && !JSON.stringify(cp.body).includes('@'));
  check('R5j status log: Growers / submission_accepted / system', sl && sl.body.records[0].fields.table === 'Growers' &&
        sl.body.records[0].fields.reason === 'submission_accepted' && sl.body.records[0].fields.actor === 'system');
  check('R5k typecast:false on every write', posts.every((c) => c.body.typecast === false));
  check('R5l the field set written is exactly the expected one', f && JSON.stringify(Object.keys(f).sort()) === JSON.stringify(
      ['consent_text_hash','county','district','email','email_key','first_name','growing_note','over_18','privacy_version','source',
       'space_wanted','status','submitted_at','timing','town_area','travel_distance']), f && Object.keys(f).sort().join(','));

  /* R6 · repeat address, different case: same reply, no second write. */
  const again = await send(ENV_OPEN, { ...body, email: body.email.toUpperCase() });
  check('R6 repeat address gets the same "received"', again.status === 200 && again.j.state === 'received');
  check('R6b repeat address writes nothing', again.calls.filter((c) => c.method === 'POST').length === 0);
  check('R6c reply bodies are identical (no oracle)', JSON.stringify(again.j) === JSON.stringify(r.j));
}
{
  const r = await send(ENV_OPEN, grower({ source: undefined }));
  const f = r.calls.find((c) => /\/Growers$/.test(c.url) && c.method === 'POST');
  check('R5m source defaults to direct when absent', f && f.body.records[0].fields.source === 'direct');
}

/* ===================================================== R8 · location ==== */
{
  const r = await send(ENV_OPEN, grower({ county: 'clare', district: 'elsewhere_in_ireland', town_area: 'Ennis', travel_distance: 'flexible' }));
  const f = r.calls.find((c) => /\/Growers$/.test(c.url) && c.method === 'POST');
  const ff = f && f.body.records[0].fields;
  check('R8 Clare + Ennis + flexible is received and stored as sent', r.status === 200 && ff && ff.county === 'clare' &&
        ff.district === 'elsewhere_in_ireland' && ff.town_area === 'Ennis' && ff.travel_distance === 'flexible', JSON.stringify(ff));
  const r2 = await send(ENV_OPEN, grower({ town_area: undefined, travel_distance: undefined }));
  const f2 = r2.calls.find((c) => /\/Growers$/.test(c.url) && c.method === 'POST');
  const g2 = f2 && f2.body.records[0].fields;
  check('R8b town and travel are optional: absent -> not written', r2.status === 200 && g2 && !('town_area' in g2) && !('travel_distance' in g2));
  const r3 = await send(ENV_OPEN, grower({ travel_distance: '' }));
  check('R8c an empty travel choice is treated as not given', r3.status === 200);
}

/* ================================================================= R7 ==== */
for (const [label, over, field] of [
  ['district outside the vocabulary', { district: 'cork' }, 'district'],
  ['travel distance outside the vocabulary', { travel_distance: 'up_to_50km' }, 'travel_distance'],
  ['county missing', { county: undefined }, 'county'],
  ['county outside the 26', { county: 'antrim' }, 'county'],
  ['Dublin county with elsewhere_in_ireland', { district: 'elsewhere_in_ireland' }, 'district'],
  ['Cork with a Dublin pilot area', { county: 'cork' }, 'district'],
  ['an Eircode in the town field', { town_area: 'D05 X2Y8' }, 'town_area'],
  ['an Eircode without a space', { town_area: 'near d05x2y8' }, 'town_area'],
  ['a house address in the town field', { town_area: '12 Main Street' }, 'town_area'],
  ['the old travel_radius key', { travel_radius: 'walking' }, 'travel_radius'],
  ['space outside the vocabulary', { space_wanted: 'huge' }, 'space_wanted'],
  ['timing outside the vocabulary', { timing: 'someday' }, 'timing'],
  ['missing first name', { first_name: '  ' }, 'first_name'],
  ['bad email', { email: 'nope' }, 'email'],
  ['over_18 false', { over_18: false }, 'over_18'],
  ['the GARDEN consent sentence', { consent_text: GARDEN_CONSENT }, 'consent_text'],
  ['an edited consent sentence', { consent_text: GROWER_CONSENT.replace('over 18', 'over 16') }, 'consent_text']]) {
  const r = await send(ENV_OPEN, grower(over));
  check(`R7 ${label} refused on ${field}, zero writes`, r.status === 400 && r.j.field === field &&
        r.calls.filter((c) => c.method === 'POST').length === 0, `${r.status} ${JSON.stringify(r.j)}`);
}
check('R7b the canonical grower sentence is the frozen G1B §3 text', T.CONSENT_TEXT.grower === GROWER_CONSENT);

console.log(`\n  ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
