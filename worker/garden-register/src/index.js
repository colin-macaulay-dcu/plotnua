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
    privacy_version: env.PRIVACY_VERSION,
    consent_text_hash: consentHash,
    given_at: utcStamp(now)
  });
}

/* --------------------------------------------------------- garden handler -- */
async function handleGarden(env, body, now, cors) {
  /* HARD STOP FOUR, RETAINED AFTER APPROVAL. The canonical consent string is
     now set, so this no longer fires — but it stays, because a future edit
     that blanks or removes the canonical sentence must close the route rather
     than record a consent to nothing. A guard is cheapest when it is already
     there on the day it becomes necessary again. */
  if (!CONSENT_TEXT.garden) return NOT_OPEN(cors);

  const first_name = cleanText(body.first_name, MAX_NAME_CHARS);
  const email = cleanText(body.email, MAX_EMAIL_CHARS);
  const district = pickEnum(V.district, body.district);
  const water = pickEnum(V.water, body.water);
  const size_note = pickEnum(V.space_band, body.size_note);
  const timing = pickEnum(V.timing, body.timing);
  const tenure = pickEnum(V.tenure, body.inherited_tenure);
  const spare = pickEnum(V.spare_corner, body.inherited_spare_corner);
  const wayIn = pickEnum(V.way_in, body.inherited_way_in);
  const ownUse = pickEnum(V.your_own_use, body.inherited_your_own_use);
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

  /* G1B TENURE RULE. A non-owner needs the tick AND their own statement.
     PlotNua never asks for a deed, a lease, or a landlord's details: the
     homeowner's own sentence is the evidence, and it is evidence of what they
     said, not of the fact. Storage is still permitted — this refusal exists
     only because a submission with neither has nothing to review. */
  const permission_confirmed = body.permission_confirmed === true;
  if (tenure !== 'own') {
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
  if (spare) fields.inherited_spare_corner = spare;
  if (wayIn) fields.inherited_way_in = wayIn;
  if (ownUse) fields.inherited_your_own_use = ownUse;
  const resultKey = cleanText(body.inherited_result_key, 60);
  if (resultKey) fields.inherited_result_key = resultKey;
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

/* --------------------------------------------------------- grower handler -- */
async function handleGrower(env, body, now, cors) {
  const first_name = cleanText(body.first_name, MAX_NAME_CHARS);
  const email = cleanText(body.email, MAX_EMAIL_CHARS);
  const district = pickEnum(V.district, body.district);
  const travel_radius = pickEnum(V.travel_radius, body.travel_radius);
  const space_wanted = pickEnum(V.space_band, body.space_wanted);
  const timing = pickEnum(V.timing, body.timing);
  const source = pickEnum(V.grower_source, body.source) || 'direct';
  const note = cleanText(body.growing_note, MAX_NOTE_CHARS);

  if (!first_name) return REFUSED(cors, 'first_name');
  if (!email || !EMAIL_RE.test(email)) return REFUSED(cors, 'email');
  if (!district) return REFUSED(cors, 'district');
  if (!travel_radius) return REFUSED(cors, 'travel_radius');
  if (!space_wanted) return REFUSED(cors, 'space_wanted');
  if (!timing) return REFUSED(cors, 'timing');
  if (body.over_18 !== true) return REFUSED(cors, 'over_18');

  const consentHash = await sha256Hex(CONSENT_TEXT.grower);
  const sentHash = await sha256Hex(cleanText(body.consent_text, 1000) || '');
  if (!sameString(consentHash, sentHash)) return REFUSED(cors, 'consent_text');

  if (!writesEnabled(env)) return NOT_OPEN(cors);

  const emailKey = email.toLowerCase();
  const fields = {
    first_name,
    email,
    email_key: emailKey,
    district,
    travel_radius,
    space_wanted,
    timing,
    over_18: true,
    status: SUBMIT_STATUS,
    submitted_at: utcStamp(now),
    privacy_version: env.PRIVACY_VERSION,
    consent_text_hash: consentHash,
    source
  };
  if (note) fields.growing_note = note;
  /* newsletter_consent is a SEPARATE decision and defaults to absent. It is
     written only on an explicit true, never bundled with submitting. */
  if (body.newsletter_consent === true) fields.newsletter_consent = true;

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
  V, CONSENT_TEXT, SUBMIT_STATUS, writesEnabled, allowedOrigin, corsHeaders,
  fetchMetadataOk, sha256Hex, sameString, pickEnum, cleanText, EMAIL_RE,
  atReason, MAX_BODY_BYTES, MAX_NOTE_CHARS
};
