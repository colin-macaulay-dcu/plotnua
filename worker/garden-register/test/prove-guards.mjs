/* G2 GUARD-CAPABILITY PROOF
 * ===========================================================================
 * This suite does not merely assert that the Worker works. It asserts that
 * every refusal CAN FIRE, by driving each one deliberately. A guard that has
 * never been seen to fail is not a proven guard.
 *
 * Nothing here touches the network: AIRTABLE_TOKEN is never set to a real
 * value, and every test that would reach Airtable is a test that the Worker
 * refuses BEFORE composing a request.
 * ========================================================================= */
import worker, { __test as T } from '../src/index.js';

let pass = 0, fail = 0;
const results = [];
function check(name, cond, detail) {
  if (cond) { pass++; results.push(['PASS', name, '']); }
  else { fail++; results.push(['FAIL', name, detail || '']); }
}

const ORIGIN = 'https://plotnua.ie';
const BASE_ENV = {
  ORIGIN,
  WRITES_ENABLED: 'false',
  EMAIL_ENABLED: 'false',
  PRIVACY_VERSION: '2026-10-PHASE2-V2',
  PILOT_DISTRICTS: 'raheny,killester,donnycarney,artane'
};
/* A deliberately fake token. If any test reaches Airtable with this, the test
   that matters has already failed. */
const WRITES_ON = { ...BASE_ENV, WRITES_ENABLED: 'true',
                    AIRTABLE_BASE: 'appUie3wPmPITfMW7', AIRTABLE_TOKEN: 'patFAKE_NEVER_REAL' };

function post(path, body, { origin = ORIGIN, site = 'cross-site', mode = 'cors', method = 'POST' } = {}) {
  const h = { 'content-type': 'application/json' };
  if (origin) h.origin = origin;
  if (site) h['sec-fetch-site'] = site;
  if (mode) h['sec-fetch-mode'] = mode;
  return new Request('https://w.example' + path, {
    method, headers: h,
    body: method === 'GET' ? undefined : JSON.stringify(body || {})
  });
}
const run = (env, req) => worker.fetch(req, env);
const asJson = async (r) => { try { return await r.json(); } catch { return null; } };

const GROWER_CONSENT = T.CONSENT_TEXT.grower;

function growerBody(over = {}) {
  return {
    first_name: 'Test', email: 'guard.test@example.com', district: 'raheny',
    travel_radius: 'walking', space_wanted: 'small', timing: 'flexible',
    over_18: true, consent_text: GROWER_CONSENT, ...over
  };
}
function gardenBody(over = {}) {
  return {
    first_name: 'Test', email: 'guard.garden@example.com', district: 'raheny',
    water: 'outside_tap', size_note: 'small', timing: 'flexible',
    inherited_tenure: 'own', over_18: true, consent_text: 'anything', ...over
  };
}

/* ======================================================= 1 · HARD STOPS == */
check('G1  writesEnabled false when switch off',
  T.writesEnabled({ ...BASE_ENV, AIRTABLE_BASE: 'x', AIRTABLE_TOKEN: 'y' }) === false);
check('G2  writesEnabled false when token missing',
  T.writesEnabled({ ...BASE_ENV, WRITES_ENABLED: 'true', AIRTABLE_BASE: 'x' }) === false);
check('G3  writesEnabled false when base missing',
  T.writesEnabled({ ...BASE_ENV, WRITES_ENABLED: 'true', AIRTABLE_TOKEN: 'y' }) === false);
check('G4  writesEnabled true ONLY with all three',
  T.writesEnabled(WRITES_ON) === true);

/* ===================================================== 2 · THE CEILING === */
check('G5  the only writable status is interest_submitted',
  T.SUBMIT_STATUS === 'interest_submitted');
const promotable = ['qualified_garden_opportunity', 'registered_grower',
                    'needs_a_conversation', 'contact_confirmed', 'paused', 'withdrawn'];
const src = await (await import('node:fs/promises')).readFile(
  new URL('../src/index.js', import.meta.url), 'utf8');
check('G6  no promotable status appears as a writable value',
  promotable.every(s => !new RegExp('status:\\s*[\'"]' + s).test(src)));
check('G7  typecast:false is written explicitly and nowhere set true',
  /typecast:\s*false/.test(src) && !/typecast:\s*true/.test(src));

/* ============================================ 3 · GARDEN CONSENT (G1B §9) =
   The homeowner sentence was approved verbatim on 7 October 2026. These guards
   changed shape at that approval: the route is no longer structurally closed,
   so what must now be proven is that the APPROVED sentence is the only one
   that opens it, and that the write switch still stops the write. */
const GARDEN_CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.";

check('G8  garden canonical consent is the exact approved sentence',
  T.CONSENT_TEXT.garden === GARDEN_CONSENT, 'got: ' + JSON.stringify(T.CONSENT_TEXT.garden));
check('G8b garden and grower sentences are different strings',
  T.CONSENT_TEXT.garden !== T.CONSENT_TEXT.grower);

const gValid = await run(BASE_ENV, post('/v1/garden-register/garden',
  gardenBody({ consent_text: GARDEN_CONSENT })));
check('G9  approved garden consent PASSES validation, then writes off stops it',
  gValid.status === 503 && (await asJson(gValid)).state === 'not_open');

/* THE DECISIVE ONE. Validation passed at G9, so this proves the refusal is the
   WRITE SWITCH and not a validation error wearing the same reply. */
const gWritesOn = await run({ ...WRITES_ON, WRITES_ENABLED: 'false' },
  post('/v1/garden-register/garden', gardenBody({ consent_text: GARDEN_CONSENT })));
check('G9b with base+token present but switch off, still nothing written',
  gWritesOn.status === 503 && (await asJson(gWritesOn)).state === 'not_open');

async function gardenRefused(body, field) {
  const r = await run(BASE_ENV, post('/v1/garden-register/garden', body));
  const j = await asJson(r);
  return r.status === 400 && j.state === 'refused' && j.field === field;
}
check('G10a garden SEMANTIC alteration is refused',
  await gardenRefused(gardenBody({ consent_text: GARDEN_CONSENT.replace('over 18', 'over 16') }), 'consent_text'));
check('G10b the GROWER sentence is refused on the garden route',
  await gardenRefused(gardenBody({ consent_text: T.CONSENT_TEXT.grower }), 'consent_text'));
check('G10c empty garden consent is refused',
  await gardenRefused(gardenBody({ consent_text: '' }), 'consent_text'));
check('G10d incidental markup whitespace still normalises on the garden text',
  T.cleanText('\n  ' + GARDEN_CONSENT.replace(/ /g, '\n  ') + ' \n', 1000) === GARDEN_CONSENT);
check('G10e the null-consent stop is RETAINED in source for future edits',
  /if \(!CONSENT_TEXT\.garden\) return NOT_OPEN/.test(src));

/* ======================================================= 4 · ORIGIN ====== */
check('G11 allowedOrigin accepts the exact origin',
  T.allowedOrigin(BASE_ENV, post('/x', {})) === ORIGIN);
check('G12 allowedOrigin rejects a lookalike origin',
  T.allowedOrigin(BASE_ENV, post('/x', {}, { origin: 'https://plotnua.ie.evil.example' })) === null);
check('G13 allowedOrigin rejects a missing origin',
  T.allowedOrigin(BASE_ENV, post('/x', {}, { origin: null })) === null);
const noOrigin = await run(BASE_ENV, post('/v1/garden-register/grower', growerBody(), { origin: null }));
check('G14 request with no origin is refused 403 with no CORS header',
  noOrigin.status === 403 && !noOrigin.headers.get('access-control-allow-origin'));
check('G15 CORS is never a wildcard',
  T.corsHeaders(ORIGIN)['access-control-allow-origin'] === ORIGIN &&
  !Object.values(T.corsHeaders(ORIGIN)).includes('*'));
check('G16 CORS headers absent entirely for a disallowed origin',
  !T.corsHeaders(null)['access-control-allow-origin']);
check('G17 credentials are never allowed',
  !('access-control-allow-credentials' in T.corsHeaders(ORIGIN)));

/* ================================================= 5 · FETCH METADATA ==== */
check('G18 same-origin is refused', T.fetchMetadataOk(post('/x', {}, { site: 'same-origin' })) === false);
check('G19 sec-fetch-site none is refused', T.fetchMetadataOk(post('/x', {}, { site: 'none' })) === false);
check('G20 navigate mode is refused', T.fetchMetadataOk(post('/x', {}, { mode: 'navigate' })) === false);
check('G21 cross-site + cors is accepted', T.fetchMetadataOk(post('/x', {})) === true);

/* ======================================================= 6 · NO GET ====== */
const getR = await run(BASE_ENV, post('/v1/garden-register/grower', null, { method: 'GET' }));
check('G22 GET is refused 405 — there is no read surface at all', getR.status === 405);
check('G23 source contains no GET route handler',
  !/method\s*===\s*'GET'/.test(src));

/* ================================================== 7 · VALIDATION ======= */
async function refusedField(body, field, env = BASE_ENV) {
  const r = await run(env, post('/v1/garden-register/grower', body));
  const j = await asJson(r);
  return r.status === 400 && j.state === 'refused' && j.field === field;
}
check('G24 unknown district is refused', await refusedField(growerBody({ district: 'cork_city' }), 'district'));
check('G25 unknown space band is refused', await refusedField(growerBody({ space_wanted: 'huge' }), 'space_wanted'));
check('G26 unknown travel radius is refused', await refusedField(growerBody({ travel_radius: 'up_to_50km' }), 'travel_radius'));
check('G27 bad email is refused', await refusedField(growerBody({ email: 'not-an-email' }), 'email'));
check('G28 missing first name is refused', await refusedField(growerBody({ first_name: '   ' }), 'first_name'));
check('G29 over_18 false is refused', await refusedField(growerBody({ over_18: false }), 'over_18'));
check('G30 over_18 absent is refused', await refusedField(growerBody({ over_18: undefined }), 'over_18'));
/* CONSENT HASHING, STATED PRECISELY. cleanText normalises whitespace before
   hashing, DELIBERATELY: a rendered checkbox label carries incidental newlines
   and indentation from the markup, and a guard that fired on formatting rather
   than wording would be noise. What must be refused is a SEMANTIC change. The
   first version of this test asserted that a trailing space was refused, which
   normalisation legitimately absorbs — the test was wrong, not the Worker. */
check('G31a a SEMANTIC change to the consent text is refused',
  await refusedField(growerBody({ consent_text: GROWER_CONSENT.replace('over 18', 'over 16') }), 'consent_text'));
check('G31b a different consent sentence entirely is refused',
  await refusedField(growerBody({ consent_text: 'I agree to the terms.' }), 'consent_text'));
check('G31c incidental markup whitespace is tolerated, by design',
  T.cleanText('\n   ' + GROWER_CONSENT.replace(/ /g, '\n   ') + '  \n', 1000) === GROWER_CONSENT);
check('G32 empty consent text is refused',
  await refusedField(growerBody({ consent_text: '' }), 'consent_text'));

/* A valid grower with writes OFF must reach not_open — proving validation
   passed and the switch, not a validation error, is what stopped it. */
const validOff = await run(BASE_ENV, post('/v1/garden-register/grower', growerBody()));
check('G33 valid grower + writes off => not_open (nothing written)',
  validOff.status === 503 && (await asJson(validOff)).state === 'not_open');

/* ============================================ 8 · TENURE RULE (D3) =======
   Now driven THROUGH THE ROUTE, not read off the source. The garden route
   opened at founder approval, so the rule is behaviour rather than intent. */
const gb = (o) => gardenBody({ consent_text: GARDEN_CONSENT, ...o });

check('G34a owner passes the tenure rule (stopped only by the switch)',
  (await run(BASE_ENV, post('/v1/garden-register/garden',
    gb({ inherited_tenure: 'own' })))).status === 503);
check('G34b tenant with NO permission tick is refused',
  await gardenRefused(gb({ inherited_tenure: 'rent' }), 'permission_confirmed'));
/* G34c INVERTED 8 October 2026 under founder decision D-G5-1 = option 1.
   It previously asserted that `buying` with no permission tick is refused.
   That encoded the divergence, not the contract: FROZEN G1B §5 makes `buying`
   storable with no permission and no statement. The assertion now requires the
   contract's behaviour — the submission passes every validator and is stopped
   only by the WRITE SWITCH, exactly as an owner's is (G34a). */
check('G34c buying with NO tick and NO note passes (stopped only by the switch)',
  (await run(BASE_ENV, post('/v1/garden-register/garden',
    gb({ inherited_tenure: 'buying' })))).status === 503);
check('G34c2 buying with NO tick and NO note is NOT refused on permission',
  !(await gardenRefused(gb({ inherited_tenure: 'buying' }), 'permission_confirmed')));
check('G34c3 buying with NO tick and NO note is NOT refused on the note',
  !(await gardenRefused(gb({ inherited_tenure: 'buying' }), 'garden_note')));
/* T7 · the field is PERMITTED for buying, not forbidden. A homeowner who
   volunteers a statement is not punished for it. */
check('T7 buying WITH a tick and a note also passes (stopped only by the switch)',
  (await run(BASE_ENV, post('/v1/garden-register/garden',
    gb({ inherited_tenure: 'buying', permission_confirmed: true,
         garden_note: 'The current owner knows and is happy with the idea.' })))).status === 503);
check('T7b buying with a 3-character note passes: no minimum applies to buying',
  (await run(BASE_ENV, post('/v1/garden-register/garden',
    gb({ inherited_tenure: 'buying', garden_note: 'yes' })))).status === 503);
check('G35a tenant with tick but NO statement is refused',
  await gardenRefused(gb({ inherited_tenure: 'rent', permission_confirmed: true }), 'garden_note'));
check('G35b tenant with tick but a too-short statement is refused',
  await gardenRefused(gb({ inherited_tenure: 'rent', permission_confirmed: true,
                           garden_note: 'landlord ok' }), 'garden_note'));
check('G35c tenant with tick AND a real statement passes, switch then stops it',
  (await run(BASE_ENV, post('/v1/garden-register/garden',
    gb({ inherited_tenure: 'rent', permission_confirmed: true,
         garden_note: 'My landlord knows and has said it is fine with her.' })))).status === 503);
check('G35d unknown tenure value is refused outright',
  await gardenRefused(gb({ inherited_tenure: 'squatting' }), 'inherited_tenure'));
check('G35e absent tenure is refused outright',
  await gardenRefused(gb({ inherited_tenure: undefined }), 'inherited_tenure'));
/* T9 · THE PRESERVED DIVERGENCE. G1B §5 says absent/unconfirmed tenure is
   storable; the Worker refuses it. Founder instruction, 8 October 2026, is
   that this is NOT solved in this correction: it is unreachable through the
   homeowner journey, because decide() only runs once every question is
   answered, so inherited_tenure is always own/rent/buying when the register
   panel exists. G35e above is the assertion; this is the record that its
   survival is deliberate, and a guard against it being quietly "fixed". */
check('T9 absent tenure STILL refused — the documented divergence is preserved',
  await gardenRefused(gb({ inherited_tenure: undefined }), 'inherited_tenure'));
check('T9b empty-string tenure is refused the same way',
  await gardenRefused(gb({ inherited_tenure: '' }), 'inherited_tenure'));

/* T10 · NON-PROMOTION IS NOT A FORM CONTROL. `buying` is storable and must
   remain non-promotable, but nothing in this Worker promotes or introduces
   anybody — G7 does not exist and is BLOCKED. This asserts that remains true
   of the EXECUTABLE source, with comments stripped, because the comments
   legitimately discuss introductions and promotion and an earlier guard of
   this class fired on PlotNua's own denial. */
{
  const exe = (await import('node:fs')).readFileSync(
    new URL('../src/index.js', import.meta.url), 'utf8')
    .replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/^\s*\/\/.*$/gm, ' ');
  check('T10 no introduction / promotion / eligibility logic in the Worker',
    !/introduc|promot|eligib|matchable/i.test(exe));
  check('T10b the record status is only ever SUBMIT_STATUS',
    [...exe.matchAll(/(?<![\w_])status:\s*([A-Za-z_'"][\w'"]*)/g)]
      .every((m) => m[1] === 'SUBMIT_STATUS'));
  check('T10c buying is named nowhere in executable logic except the vocabulary',
    (exe.match(/'buying'/g) || []).length === 1, exe.match(/'buying'/g));
}
/* G36 TESTS ASSERTION, NOT MENTION — the DISC-025 failure class, avoided.
   The first version of this test matched the word 'landlord' anywhere, and
   fired on PlotNua's OWN DENIAL in a comment ("never asks for a deed, a lease,
   or a landlord's details"). That is exactly the class the certified contract
   records as designed out: "Six guards on the DISC-025 build originally fired
   on PlotNua's own denials." A guard must test what the code DOES. */
const landlordFields = ['deed', 'lease', 'landlord_name', 'landlord_email',
                        'landlord_contact', 'landlord']
  .filter(b => new RegExp('(^|[^a-z_])' + b + '\\s*:', 'm').test(src));
check('G36 no deed, lease or landlord FIELD is ever written',
  landlordFields.length === 0, 'found as field: ' + landlordFields.join(', '));
check('G36b the denial is still present in the source as a denial',
  /never asks for a deed, a lease, or a landlord/.test(src));

/* ================================================ 9 · PROHIBITIONS ======= */
const banned = ['address', 'eircode', 'postcode', 'latitude', 'longitude',
                'coordinates', 'phone', 'mobile', 'telephone', 'surname',
                'last_name', 'date_of_birth', 'dob', 'disability', 'health',
                'medical', 'photo', 'referee', 'ip_address', 'skill_level',
                'price', 'rent', 'fee', 'contribution', 'payment'];
const asField = banned.filter(b => new RegExp('(^|[^a-z_])' + b + ':', 'm').test(src));
check('G37 no prohibited field is ever written',
  asField.length === 0, 'found: ' + asField.join(', '));
check('G38 no mail adapter exists in this Worker',
  !/sendgrid|mailchannels|resend|ses\.|smtp|sendEmail/i.test(src));
check('G39 nothing identifying is logged',
  !/console\.(log|info|warn|error)/.test(src));

/* ================================================= 10 · BODY LIMITS ===== */
/* FRESH ISOLATE. The Worker rate-limits POSTs at 30 per 60 s per isolate
   (`tooMany('post', Date.now(), 30, 60_000)`), keyed on the literal string
   'post' — global, not per-caller. The baseline suite sat just under that
   ceiling; the tenure-alignment additions pushed it over and the last three
   assertions began returning 429, which reads as three product defects and is
   none. Re-importing with a cache-busting query gives a new module instance
   with an empty bucket, which is what a new isolate actually is.
   Recorded, not worked around quietly: a suite one request away from a false
   failure was a latent defect in the suite, found 8 October 2026. */
const worker2 = (await import('../src/index.js?isolate=2')).default;
const run2 = (env, req) => worker2.fetch(req, env);
const big = await run2(BASE_ENV, post('/v1/garden-register/grower',
  growerBody({ growing_note: 'x'.repeat(8000) })));
check('G40 oversized body is refused', big.status === 400 &&
  (await asJson(big)).field === 'body');
const badJson = await worker2.fetch(new Request('https://w.example/v1/garden-register/grower', {
  method: 'POST',
  headers: { origin: ORIGIN, 'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'cors',
             'content-type': 'application/json' },
  body: '{not json'
}), BASE_ENV);
check('G41 malformed JSON is refused', badJson.status === 400);
check('G42 note is truncated, not rejected, at the cap',
  T.cleanText('y'.repeat(T.MAX_NOTE_CHARS + 50), T.MAX_NOTE_CHARS).length === T.MAX_NOTE_CHARS);

/* ============================================= 11 · ROUTING / ORACLE ===== */
const unknown = await run2(BASE_ENV, post('/v1/garden-register/nope', growerBody()));
check('G43 unknown path is 404 with a fixed shape', unknown.status === 404);
check('G44 reply never distinguishes new from repeat',
  /'received'/.test(src) && !/already_registered|duplicate|repeat:\s*true/.test(src));

/* ========================================== 12 · VOCABULARY FIDELITY ==== */
/* Captured from the LIVE base on 7 October 2026. If these drift, typecast:false
   turns every submission into a rejected write, so the drift must be loud. */
const LIVE = {
  district: ['raheny','killester','donnycarney','artane','elsewhere_in_dublin','elsewhere_in_ireland'],
  space_band: ['very_small','small','medium','large','not_sure'],
  timing: ['this_season','within_3_months','next_season','flexible'],
  travel_radius: ['walking','up_to_2km','up_to_5km','up_to_10km'],
  water: ['outside_tap','from_the_house','none','not_sure'],
  tenure: ['own','rent','buying']
};
for (const k of Object.keys(LIVE)) {
  check('G45.' + k + ' matches the live base vocabulary',
    JSON.stringify(T.V[k]) === JSON.stringify(LIVE[k]),
    'worker: ' + JSON.stringify(T.V[k]));
}

/* =============================================================== report == */
const w = Math.max(...results.map(r => r[1].length));
for (const [s, n, d] of results) {
  console.log(`  [${s}] ${n.padEnd(w)}${d ? '   ' + d : ''}`);
}
console.log(`\n  ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
