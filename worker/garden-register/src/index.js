/* PlotNua — BORROWED GARDEN REGISTER WORKER  (DISC-025 · G2)
 * ===========================================================================
 * NOT DEPLOYED AT TIME OF WRITING. WRITES_ENABLED and EMAIL_ENABLED both ship
 * 'false'. Deploying this file registers nobody.
 *
 * WHAT THIS WORKER IS
 *   Two POST routes that record an expression of interest, one per side, into
 *   the certified DISC-025 Airtable base. It is the ONLY code path by which a
 *   Borrowed Garden record can come into existence.
 *
 * WHAT THIS WORKER IS NOT
 *   It does not match. It does not rank. It does not score. It does not
 *   introduce. It does not send email — there is no mail adapter in this file
 *   and EMAIL_ENABLED exists so that refusal is explicit rather than implied.
 *   It has NO GET HANDLER AT ALL, so there is no read surface, no listing,
 *   no count, no export, and no token endpoint to probe.
 *
 * THE STATUS CEILING — the single most important rule here
 *   This Worker can write exactly ONE status value: 'interest_submitted'.
 *   It cannot write 'qualified_garden_opportunity', 'registered_grower',
 *   'needs_a_conversation', 'contact_confirmed', 'paused' or 'withdrawn'.
 *   Promotion toward introduction is a human act by a named reviewer, recorded
 *   in human_review_by / human_review_at. No automated path exists to make a
 *   record matchable, which is what keeps G7 behind the insurance gate even if
 *   every other switch were on.
 *
 * FOUR INDEPENDENT HARD STOPS
 *   WRITES_ENABLED !== 'true'        -> nothing is written, ever
 *   no AIRTABLE_TOKEN binding        -> nothing to write with
 *   no AIRTABLE_BASE binding         -> nowhere to write to
 *   canonical consent text absent    -> that side's submissions refused
 *
 *   The fourth stop is RETAINED, NOT SPENT. Both consent sentences are
 *   founder-approved as of 7 October 2026, so it does not fire today. It
 *   stays because a future edit that blanks or removes a canonical sentence
 *   must close that route rather than record a consent to nothing.
 *
 * typecast:false ON EVERY WRITE. An option that does not exist in Airtable is
 * a REJECTED write, never a silently created one. That is why every vocabulary
 * below is copied from the live base rather than guessed, and why validation
 * happens here as well: two checks that must agree.
 *
 * NOTHING IDENTIFYING IS LOGGED. No IP in clear, no IP hash stored, no user
 * agent, no page-view row. Abuse control is in-memory, per-isolate, and dies
 * with the isolate.
 *
 * CROSS-ORIGIN REALITY. plotnua.ie is not on Cloudflare, so the page calls
 * this Worker's workers.dev origin directly. Origin must be EXACTLY
 * env.ORIGIN, Sec-Fetch-Site must be 'cross-site' when present, and
 * Sec-Fetch-Mode must be 'cors' when present. No wildcard CORS, ever, and the
 * allowed origin is never reflected from the request.
 * ========================================================================= */

const MAX_BODY_BYTES = 4 * 1024;
const MAX_NOTE_CHARS = 600;
const MAX_NAME_CHARS = 40;
const MAX_EMAIL_CHARS = 120;

/* Tables, by name, exactly as the certified schema created them. */
const T_GARDENS = 'Gardens';
const T_GROWERS = 'Growers';
const T_STATUS_LOG = 'Status log';
const T_CONSENT = 'Consent proofs';

/* THE ONLY STATUS THIS WORKER MAY WRITE. */
const SUBMIT_STATUS = 'interest_submitted';

/* ----------------------------------------------------------- vocabularies --
   Copied from the LIVE base (appUie3wPmPITfMW7) on 7 October 2026, not from
   memory and not from the design document. Airtable rejects anything else
   because typecast is false; these exist so the rejection happens here first,
   with a useful shape, instead of as an opaque 422.                        */
const V = {
  district: ['raheny', 'killester', 'donnycarney', 'artane',
             'elsewhere_in_dublin', 'elsewhere_in_ireland'],
  space_band: ['very_small', 'small', 'medium', 'large', 'not_sure'],
  timing: ['this_season', 'within_3_months', 'next_season', 'flexible'],
  travel_radius: ['walking', 'up_to_2km', 'up_to_5km', 'up_to_10km'],
  water: ['outside_tap', 'from_the_house', 'none', 'not_sure'],
  tenure: ['own', 'rent', 'buying'],
  spare_corner: ['yes_a_clear_corner', 'maybe_part_of_the_lawn',
                 'no_it_is_all_in_use', 'no_garden', 'not_sure'],
  way_in: ['side_or_rear_access', 'its_own_gate', 'through_the_house_only',
           'not_sure'],
  your_own_use: ['yes_regularly', 'now_and_then', 'i_would_leave_them_to_it',
                 'not_sure'],
  garden_source: ['direct', 'garden_interest', 'my_plot', 'discovery', 'other'],
  /* GROWER LOCATION · founder instruction 16 Oct 2026 (pre-launch refinement).
     county is required; town_area and travel_distance are optional. All three
     are written to their own single-line-text fields in Growers, so the
     Worker's vocabulary is the only gate on the values: kept strict here. */
  county: ['carlow', 'cavan', 'clare', 'cork', 'donegal', 'dublin', 'galway',
           'kerry', 'kildare', 'kilkenny', 'laois', 'leitrim', 'limerick',
           'longford', 'louth', 'mayo', 'meath', 'monaghan', 'offaly',
           'roscommon', 'sligo', 'tipperary', 'waterford', 'westmeath',
           'wexford', 'wicklow'],
  travel_distance: ['up_to_5km', 'up_to_10km', 'up_to_20km', 'more_than_20km',
                    'flexible'],
  grower_source: ['direct', 'grower_register', 'allotment_association',
                  'council', 'community_channel', 'discovery', 'other']
};

/* ------------------------------------------------------- consent contract --
   The page sends the consent string it ACTUALLY RENDERED. This Worker hashes
   it and compares against the canonical constant for PRIVACY_VERSION. A page
   whose wording drifts from the approved text therefore stops working rather
   than recording a consent to text nobody approved.

   BOTH SENTENCES ARE FOUNDER-APPROVED. The homeowner line was held at null
   through G2 because the G1B draft carried the gardener's sentence ("tell me
   about possible growing space nearby"), which is wrong for somebody OFFERING
   space. It was not changed on anybody's authority but the founder's, and was
   approved verbatim on 7 October 2026, resolving G1B §9.

   THE UI MAY LAY THE CHECKBOX OUT HOWEVER IT LIKES. What is hashed is the
   SENTENCE, not the markup: the page sends the sentence it rendered, this
   Worker hashes it and compares. Incidental whitespace normalises; a semantic
   change does not.                                                         */
const CONSENT_TEXT = {
  grower: "I'm over 18, and I'd like PlotNua to keep this and tell me about possible growing space nearby.",
  garden: "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space."
};

/* ------------------------------------------------------------------ cors --
   Headers are added ONLY for the allowed origin. For anything else they are
   absent, so a browser refuses to hand the body to the caller even in the
   cases where this Worker also refused on its own account.                 */
function allowedOrigin(env, request) {
  const o = request.headers.get('origin') || '';
  return o && o === env.ORIGIN ? o : null;
}

function corsHeaders(origin) {
  if (!origin) return { vary: 'Origin' };
  return {
    'access-control-allow-origin': origin,
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type',
    'access-control-max-age': '600',
    vary: 'Origin'
    /* NO access-control-allow-credentials. There is no cookie and no session,
       and allowing credentials on a cross-site API is exactly the mistake
       this note exists to prevent. */
  };
}

const json = (status, obj, origin) => new Response(JSON.stringify(obj), {
  status,
  headers: {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'referrer-policy': 'no-referrer',
    'x-content-type-options': 'nosniff',
    ...corsHeaders(origin)
  }
});

/* FIXED REPLY SHAPES. 'received' is returned for a new record AND for a
   repeat of an address already on the register. The body never says which,
   because a body that distinguishes them is an oracle: it would let anybody
   test whether a given address is registered. */
const RECEIVED   = (cors) => json(200, { ok: true,  state: 'received' }, cors);
const REFUSED    = (cors, field) =>
  json(400, { ok: false, state: 'refused', ...(field ? { field } : {}) }, cors);
const NOT_OPEN   = (cors) => json(503, { ok: false, state: 'not_open' }, cors);
const SLOW_DOWN  = (cors) => json(429, { ok: false, state: 'slow_down' }, cors);
const NOT_FOUND  = (cors) => json(404, { ok: false, state: 'refused' }, cors);
const UNAVAILABLE = (cors, reason) =>
  json(503, { ok: false, state: 'unavailable', ...(reason ? { reason } : {}) }, cors);

/* Short upstream diagnostic. An HTTP status class only — never a credential,
   never a base id, never any part of a row. */
function atReason(e) {
  const m = /^airtable_(\d{3})$/.exec((e && e.message) || '');
  if (!m) return (e && e.name === 'SyntaxError') ? 'atparse' : 'atnet';
  const s = Number(m[1]);
  if (s === 401) return 'at401';
  if (s === 403) return 'at403';
  if (s === 404) return 'at404';
  if (s === 422) return 'at422';
  if (s === 429) return 'at429';
  return s >= 500 ? 'at5xx' : 'at' + s;
}

/* Fetch metadata, adjusted for a legitimate cross-site call and no looser. */
function fetchMetadataOk(request) {
  const site = request.headers.get('sec-fetch-site');
  const mode = request.headers.get('sec-fetch-mode');
  if (site && site !== 'cross-site') return false;   /* 'none' = navigation */
  if (mode && mode !== 'cors') return false;
  return true;
}

/* ---------------------------------------------------------------- crypto -- */
const enc = new TextEncoder();

async function sha256Hex(s) {
  const d = await crypto.subtle.digest('SHA-256', enc.encode(String(s)));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('');
}

/* Constant-time-ish string compare, so a hash mismatch leaks no timing. */
function sameString(a, b) {
  const A = String(a), B = String(b);
  if (A.length !== B.length) return false;
  let diff = 0;
  for (let i = 0; i < A.length; i++) diff |= A.charCodeAt(i) ^ B.charCodeAt(i);
  return diff === 0;
}

/* ------------------------------------------------------------ rate limit --
   In-memory, per-isolate, keyed on nothing identifying. It dies with the
   isolate and is never written anywhere. */
const hits = new Map();
function tooMany(key, now, limit, windowMs) {
  const rec = hits.get(key);
  if (!rec || now - rec.t > windowMs) { hits.set(key, { t: now, n: 1 }); return false; }
  rec.n += 1;
  return rec.n > limit;
}

/* ------------------------------------------------------------- airtable --- */
function writesEnabled(env) {
  return env.WRITES_ENABLED === 'true' && !!env.AIRTABLE_TOKEN && !!env.AIRTABLE_BASE;
}

async function atRequest(env, method, path, body) {
  const r = await fetch('https://api.airtable.com/v0/' + env.AIRTABLE_BASE + path, {
    method,
    headers: {
      authorization: 'Bearer ' + env.AIRTABLE_TOKEN,
      'content-type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!r.ok) throw new Error('airtable_' + r.status);
  return r.json();
}

/* typecast is ALWAYS false and is written out at every call site rather than
   defaulted, so no future edit can quietly enable option creation. */
const atCreate = (env, table, fields) =>
  atRequest(env, 'POST', '/' + encodeURIComponent(table),
            { records: [{ fields }], typecast: false });

/* EXISTING ADDRESS CHECK. Returns true when email_key is already present.
   Reads one field of up to one record and nothing else — there is no listing
   path and this is not one: the formula is an equality on a single key the
   caller already supplied. */
async function emailKeyExists(env, table, emailKey) {
  const f = encodeURIComponent("{email_key}='" + emailKey.replace(/'/g, "\\'") + "'");
  const out = await atRequest(env, 'GET',
    '/' + encodeURIComponent(table) +
    '?filterByFormula=' + f + '&maxRecords=1&fields%5B%5D=email_key');
  return Array.isArray(out.records) && out.records.length > 0;
}

const utcStamp = (d) => d.toISOString().replace(/\.\d{3}Z$/, 'Z');

/* ---------------------------------------------------------- validation ---- */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function pickEnum(list, v) { return list.includes(v) ? v : null; }

function cleanText(v, max) {
  if (typeof v !== 'string') return null;
  const t = v.replace(/\s+/g, ' ').trim();
  if (!t) return null;
  return t.length > max ? t.slice(0, max) : t;
}

/* ------------------------------------------------------------ the writer --
   ONE function writes, for both sides, so the status ceiling, the consent
   proof and the status-log row cannot drift apart between two code paths. */
async function writeRecord(env, side, fields, emailKey, consentHash, now) {
  const table = side === 'garden' ? T_GARDENS : T_GROWERS;

  /* An address already on the register is not an error and is not told apart
     in the reply. Nothing is written a second time. */
  if (await emailKeyExists(env, table, emailKey)) return;

  const created = await atCreate(env, table, fields);
  const recId = created && created.records && created.records[0] && created.records[0].id;

  /* Status log — one row per transition, from nothing to interest_submitted. */
  if (recId) {
    await atCreate(env, T_STATUS_LOG, {
      record_ref: recId,
      table: side === 'garden' ? 'Gardens' : 'Growers',
      from_status: '',
      to_status: SUBMIT_STATUS,
      at: utcStamp(now),
      actor: 'system',
      reason: 'submission_accepted'
    });
  }

  /* Consent proof — survives erasure, holds a one-way fingerprint of the
     address and never the address. */
  await atCreate(env, T_CONSENT, {
    email_hash: await sha256Hex(emailKey),
    privacy_version: fields.privacy_version,
    consent_text_hash: consentHash,
    given_at: utcStamp(now)
  });
}

/* ------------------------------------------------ deprecated garden keys --
   G6-R3-DEPRECATED-FIELDS · founder instruction, 12 October 2026 (closes G6 R3).
   Under privacy notice 2026-10-PHASE2-V3 the register keeps ONE Property
   Check answer: tenure. These four keys were accepted as optional fields
   until then. The page stopped sending them (D2), and the Worker now REFUSES
   any garden submission that carries one — by presence, whatever the value —
   rather than silently dropping it, so a caller that is still sending them
   finds out, and nothing about the refused request is stored.
   They are also no longer parsed or written below: two independent layers. */
const DEPRECATED_GARDEN_KEYS = Object.freeze([
  'inherited_spare_corner', 'inherited_way_in',
  'inherited_your_own_use', 'inherited_result_key'
]);

function deprecatedKeyIn(body) {
  for (const k of DEPRECATED_GARDEN_KEYS) {
    if (Object.prototype.hasOwnProperty.call(body, k)) return k;
  }
  return null;
}

/* --------------------------------------------------------- garden handler -- */
async function handleGarden(env, body, now, cors) {
  /* HARD STOP FOUR, RETAINED AFTER APPROVAL. The canonical consent string is
     now set, so this no longer fires — but it stays, because a future edit
     that blanks or removes the canonical sentence must close the route rather
     than record a consent to nothing. A guard is cheapest when it is already
     there on the day it becomes necessary again. */
  if (!CONSENT_TEXT.garden) return NOT_OPEN(cors);

  /* G6 R3 · refused FIRST: before validation, before the write switch, before
     any Airtable call. Ordering matters — placed after the switch, a request
     with writes off would get 'not_open' and the refusal would be invisible. */
  const deprecated = deprecatedKeyIn(body);
  if (deprecated) return REFUSED(cors, deprecated);

  const first_name = cleanText(body.first_name, MAX_NAME_CHARS);
  const email = cleanText(body.email, MAX_EMAIL_CHARS);
  const district = pickEnum(V.district, body.district);
  const water = pickEnum(V.water, body.water);
  const size_note = pickEnum(V.space_band, body.size_note);
  const timing = pickEnum(V.timing, body.timing);
  const tenure = pickEnum(V.tenure, body.inherited_tenure);
  const source = pickEnum(V.garden_source, body.source) || 'direct';
  const note = cleanText(body.garden_note, MAX_NOTE_CHARS);

  if (!first_name) return REFUSED(cors, 'first_name');
  if (!email || !EMAIL_RE.test(email)) return REFUSED(cors, 'email');
  if (!district) return REFUSED(cors, 'district');
  if (!water) return REFUSED(cors, 'water');
  if (!size_note) return REFUSED(cors, 'size_note');
  if (!timing) return REFUSED(cors, 'timing');
  if (!tenure) return REFUSED(cors, 'inherited_tenure');

  /* over_18 must be TRUE. A false is never written — the schema says so. */
  if (body.over_18 !== true) return REFUSED(cors, 'over_18');

  /* G1B §5 TENURE RULE, as frozen. `rent` may reach an introduction ONLY with
     explicit permission, so `rent` alone requires the tick AND the homeowner's
     own statement. `buying` is storable with neither, is never promoted, and
     `own` needs ordinary confirmation only.
     PlotNua never asks for a deed, a lease, or a landlord's details: the
     homeowner's own sentence is evidence of what they said, not of the fact.
     Non-promotion is enforced at G7, which is
     BLOCKED — it is not, and must not become, a form control.
     Aligned 8 October 2026 under founder decision D-G5-1 = option 1: this
     block previously read `tenure !== 'own'`, which refused a `buying`
     homeowner the frozen contract says is storable. */
  const permission_confirmed = body.permission_confirmed === true;
  if (tenure === 'rent') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }

  const consentHash = await sha256Hex(CONSENT_TEXT.garden);
  const sentHash = await sha256Hex(cleanText(body.consent_text, 1000) || '');
  if (!sameString(consentHash, sentHash)) return REFUSED(cors, 'consent_text');

  if (!writesEnabled(env)) return NOT_OPEN(cors);

  const emailKey = email.toLowerCase();
  const fields = {
    first_name,
    email,
    email_key: emailKey,
    district,
    water,
    size_note,
    timing,
    over_18: true,
    status: SUBMIT_STATUS,
    inherited_tenure: tenure,
    submitted_at: utcStamp(now),
    privacy_version: env.PRIVACY_VERSION,
    consent_text_hash: consentHash,
    source
  };
  if (permission_confirmed) fields.permission_confirmed = true;
  if (note) fields.garden_note = note;
  const checkSaved = cleanText(body.check_saved_at, 40);
  if (checkSaved && !Number.isNaN(Date.parse(checkSaved))) {
    fields.check_saved_at = utcStamp(new Date(checkSaved));
  }

  try {
    await writeRecord(env, 'garden', fields, emailKey, consentHash, now);
  } catch (e) {
    return UNAVAILABLE(cors, atReason(e));
  }
  return RECEIVED(cors);
}

/* ------------------------------------------------- grower route switches --
   GROWER REGISTER · founder instruction, 16 October 2026 ("Community Roots
   Gardener Register development"). The grower route has existed since G2 but
   no page has ever sent to it, and the privacy notice in force (V3) describes
   the Garden Owner Register only. So the grower route now has its OWN two
   stops, independent of the garden route's WRITES_ENABLED, exactly as the
   Art Space Worker separates its artist route:
     GROWER_WRITES_ENABLED !== 'true'  -> nothing is written for a grower
     GROWER_PRIVACY_VERSION empty      -> nothing is written for a grower
   GROWER_PRIVACY_VERSION names the published notice that describes the
   Grower Register, and it is what a grower record and its consent proof
   carry. Opening the garden route never opens this one. */
function growerWritesEnabled(env) {
  return writesEnabled(env) && env.GROWER_WRITES_ENABLED === 'true' &&
    typeof env.GROWER_PRIVACY_VERSION === 'string' && env.GROWER_PRIVACY_VERSION.trim() !== '';
}

/* STRICT KEYS for the grower route. Anything else (an address, a phone
   number, a surname, a newsletter tick the notice does not describe, a
   honeypot) is refused by PRESENCE, before the switch, so a caller sending
   more than the register keeps finds out and nothing about it is stored. */
const GROWER_ALLOWED_KEYS = Object.freeze([
  'first_name', 'email', 'county', 'district', 'town_area', 'travel_distance',
  'space_wanted', 'timing', 'growing_note', 'over_18', 'consent_text', 'source'
]);
const MAX_TOWN_CHARS = 60;
/* A town or general area only (never a postal address). An Eircode-shaped string or a
   house-number pattern is refused by name, and nothing is stored. */
const EIRCODE_RE = /\b[ACDEFHKNPRTVWXY][0-9]{2}[0-9W]?\s?[0-9ACDEFHKNPRTVWXY]{4}\b/i;
const HOUSE_NO_RE = /^\s*\d+[a-z]?\b|\b\d+\s+[a-z]+\s+(road|street|avenue|park|drive|lane|close|crescent|grove|court|way|rd|st|ave)\b/i;
function unknownGrowerKey(body) {
  for (const k of Object.keys(body)) {
    if (!GROWER_ALLOWED_KEYS.includes(k)) return k;
  }
  return null;
}

/* --------------------------------------------------------- grower handler -- */
async function handleGrower(env, body, now, cors) {
  const extra = unknownGrowerKey(body);
  if (extra) return REFUSED(cors, extra);

  const first_name = cleanText(body.first_name, MAX_NAME_CHARS);
  const email = cleanText(body.email, MAX_EMAIL_CHARS);
  const county = pickEnum(V.county, body.county);
  const district = pickEnum(V.district, body.district);
  const town_area = cleanText(body.town_area, MAX_TOWN_CHARS);
  const travelGiven = body.travel_distance !== undefined && body.travel_distance !== '';
  const travel_distance = pickEnum(V.travel_distance, body.travel_distance);
  const space_wanted = pickEnum(V.space_band, body.space_wanted);
  const timing = pickEnum(V.timing, body.timing);
  const source = pickEnum(V.grower_source, body.source) || 'direct';
  const note = cleanText(body.growing_note, MAX_NOTE_CHARS);

  if (!first_name) return REFUSED(cors, 'first_name');
  if (!email || !EMAIL_RE.test(email)) return REFUSED(cors, 'email');
  if (!county) return REFUSED(cors, 'county');
  if (!district) return REFUSED(cors, 'district');
  /* district must agree with county: the four pilot areas and
     elsewhere_in_dublin only with Dublin; elsewhere_in_ireland only outside it. */
  if ((county === 'dublin') === (district === 'elsewhere_in_ireland')) return REFUSED(cors, 'district');
  if (town_area && (EIRCODE_RE.test(town_area) || HOUSE_NO_RE.test(town_area))) return REFUSED(cors, 'town_area');
  if (travelGiven && !travel_distance) return REFUSED(cors, 'travel_distance');
  if (!space_wanted) return REFUSED(cors, 'space_wanted');
  if (!timing) return REFUSED(cors, 'timing');
  if (body.over_18 !== true) return REFUSED(cors, 'over_18');

  const consentHash = await sha256Hex(CONSENT_TEXT.grower);
  const sentHash = await sha256Hex(cleanText(body.consent_text, 1000) || '');
  if (!sameString(consentHash, sentHash)) return REFUSED(cors, 'consent_text');

  if (!growerWritesEnabled(env)) return NOT_OPEN(cors);

  const emailKey = email.toLowerCase();
  const fields = {
    first_name,
    email,
    email_key: emailKey,
    county,
    district,
    space_wanted,
    timing,
    over_18: true,
    status: SUBMIT_STATUS,
    submitted_at: utcStamp(now),
    privacy_version: env.GROWER_PRIVACY_VERSION,
    consent_text_hash: consentHash,
    source
  };
  if (note) fields.growing_note = note;
  if (town_area) fields.town_area = town_area;
  if (travel_distance) fields.travel_distance = travel_distance;
  /* newsletter_consent: NOT written. The published notice does not describe a
     newsletter, so the key is outside GROWER_ALLOWED_KEYS and refused above. */

  try {
    await writeRecord(env, 'grower', fields, emailKey, consentHash, now);
  } catch (e) {
    return UNAVAILABLE(cors, atReason(e));
  }
  return RECEIVED(cors);
}

/* ========================================================================= */
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const now = new Date();

    const cors = allowedOrigin(env, request);

    if (request.method === 'OPTIONS') {
      if (!cors) {
        return new Response(null, {
          status: 403,
          headers: { allow: 'POST, OPTIONS', vary: 'Origin', 'cache-control': 'no-store' }
        });
      }
      return new Response(null, {
        status: 204,
        headers: { allow: 'POST, OPTIONS', 'cache-control': 'no-store', ...corsHeaders(cors) }
      });
    }

    if (!cors) return json(403, { ok: false, state: 'refused' }, null);
    if (!fetchMetadataOk(request)) return REFUSED(cors);

    /* THERE IS NO GET HANDLER. Not for context, not for status, not for a
       token. A register with no read surface cannot be enumerated, and a
       scanner or prefetcher following any URL here reaches nothing. */
    if (request.method !== 'POST') {
      return json(405, { ok: false, state: 'refused' }, cors);
    }

    if (tooMany('post', Date.now(), 30, 60_000)) return SLOW_DOWN(cors);

    const raw = await request.text();
    if (raw.length > MAX_BODY_BYTES) return REFUSED(cors, 'body');
    let body;
    try { body = JSON.parse(raw); } catch { return REFUSED(cors, 'body'); }
    if (!body || typeof body !== 'object') return REFUSED(cors, 'body');

    if (url.pathname === '/v1/garden-register/garden') {
      return handleGarden(env, body, now, cors);
    }
    if (url.pathname === '/v1/garden-register/grower') {
      return handleGrower(env, body, now, cors);
    }
    return NOT_FOUND(cors);
  }
};

/* EXPORTED FOR TESTS ONLY. Nothing here reaches the network. */
export const __test = {
  V, CONSENT_TEXT, SUBMIT_STATUS, writesEnabled, growerWritesEnabled,
  GROWER_ALLOWED_KEYS, allowedOrigin, corsHeaders,
  fetchMetadataOk, sha256Hex, sameString, pickEnum, cleanText, EMAIL_RE,
  atReason, MAX_BODY_BYTES, MAX_NOTE_CHARS
};
