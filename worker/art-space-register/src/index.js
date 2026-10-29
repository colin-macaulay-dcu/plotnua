/* PlotNua — ART SPACE REGISTER WORKER  (DISC-024 · Open Your Home to Art)
 * ===========================================================================
 * Deployed CLOSED (13 Oct 2026). WRITES_ENABLED and EMAIL_ENABLED both ship
 * 'false'. Deploying this file registers nobody.
 *
 * Founder approval for build: 13 October 2026. The technical reference is the
 * Borrowed Garden register Worker (worker/garden-register), which is NOT
 * modified, NOT imported and shares NO binding, base or credential with this
 * file. A garden token cannot reach this base and this token cannot reach the
 * garden base: each Worker holds its own secret, scoped to its own base.
 *
 * WHAT THIS WORKER IS
 *   ONE POST route that records a homeowner's expression of interest in
 *   offering space for artists' finished work, into the separate Art Space
 *   Register base. It is the ONLY code path by which an art-space record can
 *   come into existence.
 *
 * WHAT THIS WORKER IS NOT
 *   It does not match, rank, score, introduce, book or pay. It does not send
 *   email — there is no mail adapter in this file, and EMAIL_ENABLED exists so
 *   the refusal is explicit rather than implied. It has NO GET HANDLER, so
 *   there is no read surface, no listing, no count and no export.
 *
 * THE ARTIST REGISTER (PlotArt), ADDED 14 Oct 2026 (founder approval to build,
 *   CLOSED). A SECOND, SEPARATE POST route, /v1/art-space-register/artist,
 *   records an artist's expression of interest into its own 'Artists' table
 *   in the same base. It has its own switch (ARTIST_WRITES_ENABLED, shipped
 *   "false"), its own privacy version (ARTIST_PRIVACY_VERSION), its own field
 *   allow-list, consent sentence, duplicate check and 25-a-day cap. It shares
 *   the origin, fetch-metadata, body-size and burst protections, and the
 *   Consent proofs and Status log tables (each artist row is marked
 *   register = 'artist'). The homeowner route below is unchanged: neither
 *   route reads, writes or counts the other's table. Artist records are
 *   private; there is no public profile, listing or directory.
 *
 * THE STATUS CEILING
 *   This Worker can write exactly ONE status value: 'interest_submitted'.
 *   Any movement toward an introduction is a human act by a named reviewer,
 *   and introductions are not authorised (founder decision, 13 Oct 2026:
 *   evidence of genuine artist demand is required first).
 *
 * FOUR INDEPENDENT HARD STOPS
 *   WRITES_ENABLED !== 'true'        -> nothing is written, ever
 *   no AIRTABLE_TOKEN binding        -> nothing to write with
 *   no AIRTABLE_BASE binding         -> nowhere to write to
 *   canonical consent text absent    -> every submission refused
 *
 * STRICT FIELD VALIDATION. The garden Worker ignores keys it does not know;
 * this one REFUSES them. A request carrying any key outside ALLOWED_KEYS —
 * an address, an Eircode, a phone number, a tenure answer, a Property Check
 * result, the page's honeypot — is refused before validation, before the write
 * switch and before any Airtable call, and nothing about it is stored.
 *
 * typecast:false ON EVERY WRITE. An option that does not exist in Airtable is
 * a REJECTED write, never a silently created one.
 *
 * NOTHING IDENTIFYING IS LOGGED. No IP, no IP hash, no user agent. Abuse
 * control is (1) an in-memory burst limit, per isolate, and (2) a DURABLE
 * DAILY CAP: before creating a record, the Worker counts the Hosts records
 * submitted in the last 24 hours (in Airtable itself, so it holds across
 * isolates and restarts, costs nothing and needs no new binding). At
 * DAILY_CAP it creates nothing and replies slow_down. A flood can therefore
 * never add more than DAILY_CAP records a day, whatever the origin headers
 * say. If the count cannot be read, nothing is written (fail closed).
 * ========================================================================= */

const MAX_BODY_BYTES = 4 * 1024;
const MAX_NOTE_CHARS = 400;
const MAX_NAME_CHARS = 40;
const MAX_EMAIL_CHARS = 120;

/* At most this many NEW records in any rolling 24 hours (founder brief,
   14 Oct 2026: proportionate, simple, free). A small pilot expects far fewer;
   reaching it means automation or an unexpected surge, and a person looks. */
const DAILY_CAP = 25;

/* Tables, by name, exactly as the setup instructions create them. */
const T_HOSTS = 'Hosts';
const T_STATUS_LOG = 'Status log';
const T_CONSENT = 'Consent proofs';

const ROUTE = '/v1/art-space-register/host';

/* THE ONLY STATUS THIS WORKER MAY WRITE. */
const SUBMIT_STATUS = 'interest_submitted';

/* ----------------------------------------------------------- vocabularies --
   Identical to the page's lists and to the single-select / multi-select
   options the setup instructions create. typecast is false, so anything else
   would be rejected by Airtable; these exist so the refusal happens here
   first, with a useful shape.                                             */
const V = {
  county: ['carlow', 'cavan', 'clare', 'cork', 'donegal', 'dublin', 'galway',
           'kerry', 'kildare', 'kilkenny', 'laois', 'leitrim', 'limerick',
           'longford', 'louth', 'mayo', 'meath', 'monaghan', 'offaly',
           'roscommon', 'sligo', 'tipperary', 'waterford', 'westmeath',
           'wexford', 'wicklow'],
  ways: ['store', 'display', 'open', 'help_sell'],
  space: ['a_wall', 'a_room', 'dry_store', 'not_sure'],
  money: ['no_money', 'fee_for_space', 'share_if_sells', 'not_decided'],
  source: ['property_check']
};

/* The ONLY keys a submission may carry. Everything else is refused. */
const ALLOWED_KEYS = Object.freeze([
  'first_name', 'email', 'county', 'ways', 'space', 'money', 'host_note',
  'over_18', 'consent_text', 'source'
]);

/* ------------------------------------------------------- consent contract --
   Founder-approved verbatim, 13 October 2026, ASCII apostrophe. The page sends
   the sentence it rendered; this Worker hashes it and compares. A page whose
   wording drifts stops working rather than recording a consent to text nobody
   approved. Incidental whitespace normalises; a semantic change does not.  */
const CONSENT_TEXT =
  "I'm over 18 and agree that PlotNua may keep my registration details and contact me about the Open Your Home to Art pilot. I understand I can withdraw my consent at any time.";

/* ------------------------------------------------------------------ cors -- */
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
    /* NO access-control-allow-credentials: no cookie, no session. */
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

/* FIXED REPLY SHAPES. 'received' is returned for a new record AND for an
   address already on the register; the body never says which, so it cannot be
   used to test whether somebody is registered. */
const RECEIVED    = (cors) => json(200, { ok: true,  state: 'received' }, cors);
const REFUSED     = (cors, field) =>
  json(400, { ok: false, state: 'refused', ...(field ? { field } : {}) }, cors);
const NOT_OPEN    = (cors) => json(503, { ok: false, state: 'not_open' }, cors);
const SLOW_DOWN   = (cors) => json(429, { ok: false, state: 'slow_down' }, cors);
const NOT_FOUND   = (cors) => json(404, { ok: false, state: 'refused' }, cors);
const UNAVAILABLE = (cors, reason) =>
  json(503, { ok: false, state: 'unavailable', ...(reason ? { reason } : {}) }, cors);

/* An HTTP status class only — never a credential, a base id or any row. */
function atReason(e) {
  const m = /^airtable_(\d{3})$/.exec((e && e.message) || '');
  if (!m) return (e && e.name === 'SyntaxError') ? 'atparse' : 'atnet';
  const s = Number(m[1]);
  if ([401, 403, 404, 422, 429].includes(s)) return 'at' + s;
  return s >= 500 ? 'at5xx' : 'at' + s;
}

function fetchMetadataOk(request) {
  const site = request.headers.get('sec-fetch-site');
  const mode = request.headers.get('sec-fetch-mode');
  if (site && site !== 'cross-site') return false;
  if (mode && mode !== 'cors') return false;
  return true;
}

/* ---------------------------------------------------------------- crypto -- */
const enc = new TextEncoder();
async function sha256Hex(s) {
  const d = await crypto.subtle.digest('SHA-256', enc.encode(String(s)));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('');
}
function sameString(a, b) {
  const A = String(a), B = String(b);
  if (A.length !== B.length) return false;
  let diff = 0;
  for (let i = 0; i < A.length; i++) diff |= A.charCodeAt(i) ^ B.charCodeAt(i);
  return diff === 0;
}

/* ------------------------------------------------------------ rate limit -- */
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
    headers: { authorization: 'Bearer ' + env.AIRTABLE_TOKEN, 'content-type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!r.ok) throw new Error('airtable_' + r.status);
  return r.json();
}

/* typecast written out false at the call site, never defaulted. */
const atCreate = (env, table, fields) =>
  atRequest(env, 'POST', '/' + encodeURIComponent(table),
            { records: [{ fields }], typecast: false });

/* Equality on the one key the caller supplied; one field of at most one row. */
async function emailKeyExists(env, emailKey) {
  const f = encodeURIComponent("{email_key}='" + emailKey.replace(/'/g, "\\'") + "'");
  const out = await atRequest(env, 'GET',
    '/' + encodeURIComponent(T_HOSTS) + '?filterByFormula=' + f + '&maxRecords=1&fields%5B%5D=email_key');
  return Array.isArray(out.records) && out.records.length > 0;
}

/* The durable daily cap: how many Hosts records were submitted in the last
   24 hours, read as at most DAILY_CAP rows of one field. */
async function dailyCapReached(env) {
  const f = encodeURIComponent("IS_AFTER({submitted_at}, DATEADD(NOW(), -1, 'days'))");
  const out = await atRequest(env, 'GET',
    '/' + encodeURIComponent(T_HOSTS) + '?filterByFormula=' + f + '&maxRecords=' + DAILY_CAP +
    '&fields%5B%5D=submitted_at');
  return !Array.isArray(out.records) || out.records.length >= DAILY_CAP;
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
/* ways: a non-empty array of distinct known values, at most four. */
function pickWays(v) {
  if (!Array.isArray(v) || v.length < 1 || v.length > V.ways.length) return null;
  const seen = new Set();
  for (const w of v) {
    if (!V.ways.includes(w) || seen.has(w)) return null;
    seen.add(w);
  }
  return V.ways.filter(w => seen.has(w));
}
function unknownKeyIn(body) {
  for (const k of Object.keys(body)) if (!ALLOWED_KEYS.includes(k)) return k;
  return null;
}

/* ------------------------------------------------------------ the handler -- */
async function handleHost(env, body, now, cors) {
  if (!CONSENT_TEXT) return NOT_OPEN(cors);

  /* STRICT: refused FIRST, before validation and before the write switch, so a
     caller sending an address or a Property Check answer finds out even while
     writes are off, and nothing about the request is stored. */
  const unknown = unknownKeyIn(body);
  if (unknown) return REFUSED(cors, 'unexpected_field');

  const first_name = cleanText(body.first_name, MAX_NAME_CHARS);
  const email = cleanText(body.email, MAX_EMAIL_CHARS);
  const county = pickEnum(V.county, body.county);
  const ways = pickWays(body.ways);
  const has = (k) => Object.prototype.hasOwnProperty.call(body, k);
  const space = has('space') ? pickEnum(V.space, body.space) : undefined;
  const money = has('money') ? pickEnum(V.money, body.money) : undefined;
  const note = has('host_note') ? cleanText(body.host_note, MAX_NOTE_CHARS) : undefined;
  const source = pickEnum(V.source, body.source) || 'property_check';

  if (!first_name) return REFUSED(cors, 'first_name');
  if (!email || !EMAIL_RE.test(email)) return REFUSED(cors, 'email');
  if (!county) return REFUSED(cors, 'county');
  if (!ways) return REFUSED(cors, 'ways');
  /* Optional fields: absent is fine; present must be valid. */
  if (space === null) return REFUSED(cors, 'space');
  if (money === null) return REFUSED(cors, 'money');
  if (has('host_note') && typeof body.host_note !== 'string') return REFUSED(cors, 'host_note');
  if (body.over_18 !== true) return REFUSED(cors, 'over_18');

  const consentHash = await sha256Hex(CONSENT_TEXT);
  const sentHash = await sha256Hex(cleanText(body.consent_text, 1000) || '');
  if (!sameString(consentHash, sentHash)) return REFUSED(cors, 'consent_text');

  if (!writesEnabled(env)) return NOT_OPEN(cors);

  const emailKey = email.toLowerCase();
  const fields = {
    first_name, email, email_key: emailKey, county, ways,
    over_18: true,
    status: SUBMIT_STATUS,
    submitted_at: utcStamp(now),
    privacy_version: env.PRIVACY_VERSION,
    consent_text_hash: consentHash,
    source
  };
  if (space) fields.space = space;
  if (money) fields.money = money;
  if (note) fields.host_note = note;

  try {
    /* Cap first: at the cap EVERY new submission, repeat address or not, gets
       the same slow_down, so the cap can never reveal who is registered. */
    if (await dailyCapReached(env)) return SLOW_DOWN(cors);
    if (!(await emailKeyExists(env, emailKey))) {
      const created = await atCreate(env, T_HOSTS, fields);
      const recId = created && created.records && created.records[0] && created.records[0].id;
      if (recId) {
        await atCreate(env, T_STATUS_LOG, {
          record_ref: recId, from_status: '', to_status: SUBMIT_STATUS,
          at: utcStamp(now), actor: 'system', reason: 'submission_accepted'
        });
      }
      await atCreate(env, T_CONSENT, {
        email_hash: await sha256Hex(emailKey),
        privacy_version: env.PRIVACY_VERSION,
        consent_text_hash: consentHash,
        given_at: utcStamp(now)
      });
    }
  } catch (e) {
    return UNAVAILABLE(cors, atReason(e));
  }
  return RECEIVED(cors);
}

/* =========================================================================
 * ARTIST REGISTER (PlotArt) · founder approval to build, 14 October 2026.
 * SHIPPED CLOSED: ARTIST_WRITES_ENABLED is "false" in wrangler.toml, and the
 * route also needs ARTIST_PRIVACY_VERSION (the notice that covers artists)
 * and the shared token and base. Expressions of interest only.
 * ========================================================================= */
const T_ARTISTS = 'Artists';
const ARTIST_ROUTE = '/v1/art-space-register/artist';
const ARTIST_DAILY_CAP = 25;
const MAX_ARTIST_NAME_CHARS = 60;
const MAX_PLACES_CHARS = 120;
const MAX_PORTFOLIO_CHARS = 200;
const MAX_STATEMENT_CHARS = 400;

/* Closed artist vocabularies, identical to the artist page and to the
   Artists table's select options. based_in: the 32 counties of Ireland, or
   outside Ireland. */
const VA = {
  based_in: ['antrim', 'armagh', 'carlow', 'cavan', 'clare', 'cork', 'derry', 'donegal', 'down',
             'dublin', 'fermanagh', 'galway', 'kerry', 'kildare', 'kilkenny', 'laois', 'leitrim',
             'limerick', 'longford', 'louth', 'mayo', 'meath', 'monaghan', 'offaly', 'roscommon',
             'sligo', 'tipperary', 'tyrone', 'waterford', 'westmeath', 'wexford', 'wicklow',
             'outside_ireland'],
  reach: ['local_area', 'particular_places', 'anywhere_ireland'],
  disciplines: ['painting', 'drawing_print', 'photography', 'sculpture', 'ceramics_craft',
                'textiles', 'installation_mixed', 'digital_video', 'other'],
  interests: ['display', 'show_visitors', 'installation', 'store', 'reach_buyers'],
  needs: ['wall', 'floor_room', 'outdoor', 'dry_storage', 'not_sure']
};

/* The ONLY keys an artist submission may carry. Everything else is refused. */
const ARTIST_ALLOWED_KEYS = Object.freeze([
  'artist_name', 'email', 'based_in', 'reach', 'reach_places', 'disciplines', 'interests',
  'needs', 'portfolio', 'statement', 'over_18', 'consent_text'
]);

/* FOUNDER WORDING, 14 Oct 2026 (19:25), replacing the proposal of the same day.
   It is final only when the founder approves Privacy Notice V5's exact text,
   before opening. The page sends the sentence it rendered; this Worker hashes
   it and compares. Change it here, in build-artist-register.py (CONSENT) and in
   the V5 draft together, in one commit: guard A3 refuses any mismatch. */
const ARTIST_CONSENT_TEXT =
  "I confirm that I am 18 or over and consent to PlotNua storing my Artist Register details and contacting me about the development of PlotArt and potential opportunities to connect with homeowners. I understand that registering does not guarantee an opportunity and that I can withdraw my consent at any time.";

function artistWritesEnabled(env) {
  return env.ARTIST_WRITES_ENABLED === 'true' && !!env.ARTIST_PRIVACY_VERSION &&
    !!env.AIRTABLE_TOKEN && !!env.AIRTABLE_BASE;
}

/* A non-empty array of distinct known values, returned in canonical order. */
function pickMany(list, v) {
  if (!Array.isArray(v) || v.length < 1 || v.length > list.length) return null;
  const seen = new Set();
  for (const x of v) {
    if (!list.includes(x) || seen.has(x)) return null;
    seen.add(x);
  }
  return list.filter(x => seen.has(x));
}

/* https only, a real host, no credentials, no port; stored, never published. */
function cleanPortfolio(v) {
  if (typeof v !== 'string') return null;
  const t = v.trim();
  if (!t || t.length > MAX_PORTFOLIO_CHARS || /\s/.test(t)) return null;
  let u;
  try { u = new URL(t); } catch { return null; }
  if (u.protocol !== 'https:' || u.username || u.password || u.port || !/\.[a-z]{2,}$/i.test(u.hostname)) return null;
  return u.href;
}

async function artistEmailExists(env, emailKey) {
  const f = encodeURIComponent("{email_key}='" + emailKey.replace(/'/g, "\\'") + "'");
  const out = await atRequest(env, 'GET',
    '/' + encodeURIComponent(T_ARTISTS) + '?filterByFormula=' + f + '&maxRecords=1&fields%5B%5D=email_key');
  return Array.isArray(out.records) && out.records.length > 0;
}

/* The artist cap counts the Artists table only: homeowners never use it up. */
async function artistCapReached(env) {
  const f = encodeURIComponent("IS_AFTER({submitted_at}, DATEADD(NOW(), -1, 'days'))");
  const out = await atRequest(env, 'GET',
    '/' + encodeURIComponent(T_ARTISTS) + '?filterByFormula=' + f + '&maxRecords=' + ARTIST_DAILY_CAP +
    '&fields%5B%5D=submitted_at');
  return !Array.isArray(out.records) || out.records.length >= ARTIST_DAILY_CAP;
}

async function handleArtist(env, body, now, cors) {
  if (!ARTIST_CONSENT_TEXT) return NOT_OPEN(cors);

  for (const k of Object.keys(body)) {
    if (!ARTIST_ALLOWED_KEYS.includes(k)) return REFUSED(cors, 'unexpected_field');
  }

  const has = (k) => Object.prototype.hasOwnProperty.call(body, k);
  const artist_name = cleanText(body.artist_name, MAX_ARTIST_NAME_CHARS);
  const email = cleanText(body.email, MAX_EMAIL_CHARS);
  const based_in = pickEnum(VA.based_in, body.based_in);
  const reach = pickEnum(VA.reach, body.reach);
  const disciplines = pickMany(VA.disciplines, body.disciplines);
  const interests = pickMany(VA.interests, body.interests);
  const needs = has('needs') ? pickMany(VA.needs, body.needs) : undefined;
  const places = has('reach_places') ? cleanText(body.reach_places, MAX_PLACES_CHARS) : undefined;
  const portfolio = has('portfolio') ? cleanPortfolio(body.portfolio) : undefined;
  const statement = has('statement') ? cleanText(body.statement, MAX_STATEMENT_CHARS) : undefined;

  if (!artist_name) return REFUSED(cors, 'artist_name');
  if (!email || !EMAIL_RE.test(email)) return REFUSED(cors, 'email');
  if (!based_in) return REFUSED(cors, 'based_in');
  if (!reach) return REFUSED(cors, 'reach');
  if (has('reach_places') && typeof body.reach_places !== 'string') return REFUSED(cors, 'reach_places');
  if (!disciplines) return REFUSED(cors, 'disciplines');
  if (!interests) return REFUSED(cors, 'interests');
  if (needs === null) return REFUSED(cors, 'needs');
  if (portfolio === null) return REFUSED(cors, 'portfolio');
  if (has('statement') && typeof body.statement !== 'string') return REFUSED(cors, 'statement');
  if (body.over_18 !== true) return REFUSED(cors, 'over_18');

  const consentHash = await sha256Hex(ARTIST_CONSENT_TEXT);
  const sentHash = await sha256Hex(cleanText(body.consent_text, 1000) || '');
  if (!sameString(consentHash, sentHash)) return REFUSED(cors, 'consent_text');

  if (!artistWritesEnabled(env)) return NOT_OPEN(cors);

  const emailKey = email.toLowerCase();
  const stamp = utcStamp(now);
  const rec = {
    artist_name, email, email_key: emailKey, based_in, reach, disciplines, interests,
    over_18: true,
    status: SUBMIT_STATUS,
    submitted_at: stamp,
    privacy_version: env.ARTIST_PRIVACY_VERSION,
    consent_text_hash: consentHash
  };
  if (places && reach === 'particular_places') rec.reach_places = places;
  if (needs) rec.needs = needs;
  if (portfolio) rec.portfolio = portfolio;
  if (statement) rec.statement = statement;

  try {
    if (await artistCapReached(env)) return SLOW_DOWN(cors);
    if (!(await artistEmailExists(env, emailKey))) {
      const created = await atCreate(env, T_ARTISTS, rec);
      const recId = created && created.records && created.records[0] && created.records[0].id;
      if (recId) {
        await atCreate(env, T_STATUS_LOG, {
          record_ref: recId, from_status: '', to_status: SUBMIT_STATUS,
          at: stamp, actor: 'system', reason: 'artist_submission_accepted', register: 'artist'
        });
      }
      await atCreate(env, T_CONSENT, {
        email_hash: await sha256Hex(emailKey),
        privacy_version: env.ARTIST_PRIVACY_VERSION,
        consent_text_hash: consentHash,
        given_at: stamp,
        register: 'artist'
      });
    }
  } catch (e) {
    return UNAVAILABLE(cors, atReason(e));
  }
  return RECEIVED(cors);
}

/* =========================================================================
 * PLOTART FOUNDING 25 APPLICATIONS · v2, 28 October 2026 (founder
 * implementation authorisation of the same day). BUILT CLOSED; NOT DEPLOYED.
 *
 * A THIRD, SEPARATE POST route, /v1/art-space-register/founding-25, records an
 * artist's application to be CONSIDERED for the Founding 25 (the first 25
 * artists admitted to the PlotArt Virtual Gallery) into its own 'Founding 25
 * applications' table in the same PlotArt base. It does not read, write or
 * count the Artists or Hosts tables, and the Host and Artist routes above are
 * unchanged.
 *
 * WHAT AN APPLICATION IS, AND IS NOT (founder brief s.8): applying (A) is
 * separate from accepting a Founding Artist place (B, the Founding Artist
 * terms, by email) and from authorising publication of a gallery and artworks
 * (C, a separate approval of a gallery preview). This route records A only.
 * It asks for no publication permission, no Living Gallery interest, no image
 * upload, no address, no phone number and no date of birth.
 *
 * HARD STOPS (any one -> nothing written)
 *   F25_WRITES_ENABLED !== 'true'    (committed "false")
 *   F25_PRIVACY_VERSION empty        (the published notice covering applications)
 *   no AIRTABLE_TOKEN / no AIRTABLE_BASE
 *   the three confirmations must match the approved sentences exactly
 *   F25_TURNSTILE_SECRET set (optional) -> a valid challenge token is required
 *
 * The status ceiling for this route is 'received'. Review, shortlisting,
 * selection, terms, onboarding and publication are human acts in Airtable.
 * Nothing here creates anything public, and there is still NO GET handler.
 * ========================================================================= */
const T_F25 = 'Founding 25 applications';
const F25_ROUTE = '/v1/art-space-register/founding-25';
const F25_STATUS = 'received';
const F25_REGISTER = 'founding_25';
const F25_SOURCE = 'plotart_founding_25_form';
/* The version of the three confirmation sentences below. Recorded on every
   application, with the privacy notice version and the time. Change the
   sentences and this together. */
const F25_CONSENT_VERSION = 'F25-APPLICATION-2026-10-29-R3';   // R3: ownership covers submitted images or a link (founder decision, 29 Oct 2026)
const F25_CONSENT_VERSION_R2 = 'F25-APPLICATION-2026-10-28-R2';  // R2: island of Ireland (founder decision D2/D18, 28 Oct 2026)
const F25_MAX_BODY = 8 * 1024;
const F25_DEFAULT_DAILY_CAP = 50;
const F25_BURST_PER_MINUTE = 10;
const MAX_F25_NAME = 80;
const MAX_F25_BIO = 1000;
const MIN_F25_BIO = 40;
const MAX_F25_INFO = 800;
const MAX_F25_SOCIAL = 120;
const F25_PROBE_DOMAIN = '@probe.plotnua.invalid';

/* ---- Artwork images with an application (founder approval of development, 29 Oct 2026) -------------------------
   An applicant may upload up to five images of their work instead of (or as well as) a portfolio link. Images go to a
   PRIVATE, EU-jurisdiction R2 bucket (binding F25_IMAGES), separate from published gallery artwork, and are used only
   for selection. They are uploaded one by one to a holding area (pending/<submission_id>/), and only an application
   that is actually received moves them to applications/<reference>/. Abandoned uploads are removed by the bucket's
   lifecycle rule on pending/ (1 day). There is still no GET handler: nothing here can be read back from the public
   route; the founder reviews images in PlotArt Studio (Cloudflare Access, founder only). */
const F25_IMAGE_ROUTE = '/v1/art-space-register/founding-25/image';
const F25_MAX_IMAGES = 5;
const F25_MIN_IMAGES = 3;               // ...or a portfolio link
const F25_MAX_IMAGE_BYTES = 8 * 1024 * 1024;
const F25_IMAGE_BURST_PER_MINUTE = 30;
const F25_IMAGE_ID = /^[0-9a-f]{16}$/;
const F25_IMAGE_TYPES = { 'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp' };

/* The real format from the bytes (never the declared type alone), with pixel dimensions. */
function sniffImage(b) {
  const u16 = (i) => (b[i] << 8) | b[i + 1], le16 = (i) => b[i] | (b[i + 1] << 8), le24 = (i) => b[i] | (b[i + 1] << 8) | (b[i + 2] << 16);
  if (b.length > 24 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4E && b[3] === 0x47)
    return { type: 'image/png', w: ((b[16] << 24) | (b[17] << 16) | (b[18] << 8) | b[19]) >>> 0, h: ((b[20] << 24) | (b[21] << 16) | (b[22] << 8) | b[23]) >>> 0 };
  if (b.length > 30 && b[0] === 0x52 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x46 && b[8] === 0x57 && b[9] === 0x45 && b[10] === 0x42 && b[11] === 0x50) {
    const c = String.fromCharCode(b[12], b[13], b[14], b[15]);
    if (c === 'VP8X') return { type: 'image/webp', w: le24(24) + 1, h: le24(27) + 1 };
    if (c === 'VP8 ') return { type: 'image/webp', w: le16(26) & 0x3fff, h: le16(28) & 0x3fff };
    if (c === 'VP8L') { const v = b[21] | (b[22] << 8) | (b[23] << 16) | (b[24] << 24); return { type: 'image/webp', w: (v & 0x3fff) + 1, h: ((v >> 14) & 0x3fff) + 1 }; }
    return null;
  }
  if (b.length > 4 && b[0] === 0xFF && b[1] === 0xD8) {
    let i = 2;
    while (i + 9 < b.length) {
      if (b[i] !== 0xFF) { i++; continue; }
      const m = b[i + 1];
      if (m >= 0xC0 && m <= 0xCF && m !== 0xC4 && m !== 0xC8 && m !== 0xCC) return { type: 'image/jpeg', w: u16(i + 7), h: u16(i + 5) };
      if (m === 0xD8 || m === 0x01 || (m >= 0xD0 && m <= 0xD7)) { i += 2; continue; }
      i += 2 + u16(i + 2);
    }
  }
  return null;
}
function hexId() { const b = new Uint8Array(8); crypto.getRandomValues(b); return [...b].map(x => x.toString(16).padStart(2, '0')).join(''); }

async function handleF25Image(env, request, url, cors) {
  if (tooMany('f25img', Date.now(), F25_IMAGE_BURST_PER_MINUTE, 60_000)) return SLOW_DOWN(cors);
  if (!f25WritesEnabled(env) || !env.F25_IMAGES) return NOT_OPEN(cors);
  const sid = url.searchParams.get('s') || '';
  if (!UUID_RE.test(sid)) return REFUSED(cors, 'submission_id');
  const declared = (request.headers.get('content-type') || '').split(';')[0].trim().toLowerCase();
  if (!F25_IMAGE_TYPES[declared]) return REFUSED(cors, 'image_type');
  const len = Number(request.headers.get('content-length') || 0);
  if (len > F25_MAX_IMAGE_BYTES) return REFUSED(cors, 'image_size');
  const buf = new Uint8Array(await request.arrayBuffer());
  if (!buf.length) return REFUSED(cors, 'image_type');
  if (buf.length > F25_MAX_IMAGE_BYTES) return REFUSED(cors, 'image_size');
  const img = sniffImage(buf);
  if (!img || img.type !== declared) return REFUSED(cors, 'image_type');
  if (!(img.w >= 200 && img.h >= 200 && img.w <= 12000 && img.h <= 12000)) return REFUSED(cors, 'image_dimensions');
  try {
    const held = await env.F25_IMAGES.list({ prefix: 'pending/' + sid + '/', limit: 20 });
    /* five on the application, plus a little room for replaced images (the page sends only the ones kept) */
    if (held.objects.length >= F25_MAX_IMAGES * 2) return REFUSED(cors, 'image_count');
    const id = hexId();
    await env.F25_IMAGES.put('pending/' + sid + '/' + id, buf, {
      httpMetadata: { contentType: img.type },
      customMetadata: { w: String(img.w), h: String(img.h), at: utcStamp(new Date()) }
    });
    return json(200, { ok: true, state: 'stored', id }, cors);
  } catch {
    return UNAVAILABLE(cors);
  }
}

/* A website address typed without https:// is accepted: "example.ie/work" -> "https://example.ie/work". */
function f25Url(v) {
  if (typeof v !== 'string') return null;
  let t = v.trim();
  if (/^http:\/\//i.test(t)) t = 'https://' + t.slice(7);
  else if (!/^[a-z][a-z0-9+.-]*:/i.test(t)) t = 'https://' + t.replace(/^\/+/, '');
  return cleanPortfolio(t);
}

/* Closed vocabularies, identical to the Founding 25 page and to the proposed
   table's select options (airtable-schema-founding-25.proposed.json). The
   region is one of the 32 counties: the programme is for artists based or
   working in Ireland. */
const VF = {
  medium: ['painting', 'drawing', 'works_on_paper', 'printmaking', 'photography', 'sculpture',
           'ceramics_craft', 'textiles', 'mixed_media', 'digital', 'other'],
  region: VA.based_in.filter(c => c !== 'outside_ireland')
};

/* The ONLY keys an application may carry. */
const F25_KEYS = new Set([
  'artist_name', 'email', 'region', 'medium', 'bio', 'portfolio',
  'website', 'social_link', 'additional_info',
  'eligibility_text', 'ownership_text', 'privacy_text',
  'submission_id', 'challenge_token', 'images'
]);
/* portfolio is no longer required on its own: an application needs a portfolio link OR at least three images. */
const F25_REQUIRED = ['artist_name', 'email', 'region', 'medium', 'bio',
  'eligibility_text', 'ownership_text', 'privacy_text', 'submission_id'];

/* WORDING FOR FOUNDER APPROVAL (28 Oct 2026). The page renders these; the
   route hashes what it receives and compares. Change them here, in the
   Founding 25 page builder and in the privacy notice draft together; guard
   T14 (atlas-tools/prove-plotart.py) refuses any drift between page and route. */
const F25_ELIGIBILITY_TEXT =
  "I'm 18 or over, and I'm based or working on the island of Ireland.";
const F25_OWNERSHIP_TEXT =
  "The artwork I've submitted or linked to is my own original work, or I'm authorised to represent the artist who made it.";
/* The R2 wording, still accepted from a page loaded before the R3 release (recorded as R2). Remove after the switch-over. */
const F25_OWNERSHIP_TEXT_R2 =
  "The work in my portfolio is my own original work, or I'm authorised to represent the artist who made it.";
const F25_PRIVACY_TEXT =
  "I've read the privacy notice for Founding 25 applications, which explains how my application is used, who can see it and how long it's kept.";

function f25WritesEnabled(env) {
  return env.F25_WRITES_ENABLED === 'true' && !!env.F25_PRIVACY_VERSION &&
    !!env.AIRTABLE_TOKEN && !!env.AIRTABLE_BASE;
}

/* A durable cap on NEW applications in any rolling 24 hours. Configurable
   (founder decision), bounded 1-500, default 50. */
function f25DailyCap(env) {
  const n = Number.parseInt(env.F25_DAILY_CAP, 10);
  return Number.isInteger(n) && n >= 1 && n <= 500 ? n : F25_DEFAULT_DAILY_CAP;
}

/* A private reference for the artist's emails: F25-YYMMDD-XXXXXX. */
function f25Ref(now) {
  const b = new Uint8Array(3);
  crypto.getRandomValues(b);
  return 'F25-' + now.toISOString().slice(2, 10).replace(/-/g, '') + '-' +
    [...b].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
}

/* Longer free text: control characters removed, runs of spaces collapsed,
   at most one blank line kept. Over-length is REFUSED, never truncated. */
function cleanLong(v, min, max) {
  if (typeof v !== 'string') return null;
  const t = v.replace(/\r\n?/g, '\n').replace(/[\u0000-\u0008\u000B-\u001F\u007F]/g, '')
    .split('\n').map(l => l.replace(/[ \t]+/g, ' ').trim()).join('\n')
    .replace(/\n{3,}/g, '\n\n').trim();
  if (t.length < min || t.length > max) return null;
  return t;
}
function cleanShort(v, max) {
  if (typeof v !== 'string') return null;
  const t = v.replace(/[\u0000-\u001F\u007F]/g, '').replace(/\s+/g, ' ').trim();
  return t && t.length <= max ? t : null;
}
/* An Instagram-style handle, or an https link to a professional page. */
function cleanSocial(v) {
  if (typeof v !== 'string') return null;
  const t = v.trim();
  if (/^@?[A-Za-z0-9._]{1,60}$/.test(t)) return t.startsWith('@') ? t : '@' + t;
  return t.length <= MAX_F25_SOCIAL ? f25Url(t) : null;
}
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

async function f25Exists(env, emailKey, submissionId) {
  const q = (s) => "'" + s.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
  const f = encodeURIComponent('OR({email_key}=' + q(emailKey) + ',{submission_id}=' + q(submissionId) + ')');
  const out = await atRequest(env, 'GET',
    '/' + encodeURIComponent(T_F25) + '?filterByFormula=' + f + '&maxRecords=1&fields%5B%5D=email_key');
  return Array.isArray(out.records) && out.records.length > 0;
}

async function f25CapReached(env) {
  const cap = f25DailyCap(env);
  const f = encodeURIComponent("IS_AFTER({submitted_at}, DATEADD(NOW(), -1, 'days'))");
  const out = await atRequest(env, 'GET',
    '/' + encodeURIComponent(T_F25) + '?filterByFormula=' + f + '&maxRecords=' + cap +
    '&fields%5B%5D=submitted_at');
  return !Array.isArray(out.records) || out.records.length >= cap;
}

/* OPTIONAL bot challenge (Cloudflare Turnstile). Off unless the founder sets
   the secret (wrangler secret put F25_TURNSTILE_SECRET) and the site key on
   the page. Fail closed: no token, a bad token or an unreachable verifier is
   refused. Only the token is sent; never the application. */
async function f25ChallengeOk(env, token) {
  if (!env.F25_TURNSTILE_SECRET) return true;
  if (typeof token !== 'string' || !token || token.length > 2048) return false;
  try {
    const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ secret: env.F25_TURNSTILE_SECRET, response: token })
    });
    if (!r.ok) return false;
    const j = await r.json();
    return j && j.success === true;
  } catch { return false; }
}

async function sentenceMatches(expected, sent) {
  return sameString(await sha256Hex(expected), await sha256Hex(cleanText(sent, 1000) || ''));
}

async function handleFounding25(env, body, now, cors) {
  /* Per-route burst limit first, so even malformed floods are slowed. */
  if (tooMany('f25', Date.now(), F25_BURST_PER_MINUTE, 60_000)) return SLOW_DOWN(cors);
  for (const k of Object.keys(body)) {
    if (!F25_KEYS.has(k)) return REFUSED(cors, 'unexpected_field');
  }
  for (const k of F25_REQUIRED) {
    if (!Object.prototype.hasOwnProperty.call(body, k)) return REFUSED(cors, k);
  }
  const given = (k) => Object.prototype.hasOwnProperty.call(body, k) && body[k] !== '' && body[k] !== null;

  const artist_name = cleanShort(body.artist_name, MAX_F25_NAME);
  const email = cleanShort(body.email, MAX_EMAIL_CHARS);
  const region = pickEnum(VF.region, body.region);
  const medium = pickEnum(VF.medium, body.medium);
  const bio = cleanLong(body.bio, MIN_F25_BIO, MAX_F25_BIO);
  const portfolio = given('portfolio') ? f25Url(body.portfolio) : undefined;
  const website = given('website') ? f25Url(body.website) : undefined;
  const images = body.images === undefined ? [] : body.images;
  const social_link = given('social_link') ? cleanSocial(body.social_link) : undefined;
  const additional_info = given('additional_info') ? cleanLong(body.additional_info, 1, MAX_F25_INFO) : undefined;
  const submission_id = typeof body.submission_id === 'string' && UUID_RE.test(body.submission_id) ? body.submission_id : null;

  if (!artist_name) return REFUSED(cors, 'artist_name');
  if (!email || !EMAIL_RE.test(email)) return REFUSED(cors, 'email');
  if (!region) return REFUSED(cors, 'region');
  if (!medium) return REFUSED(cors, 'medium');
  if (!bio) return REFUSED(cors, 'bio');
  if (portfolio === null) return REFUSED(cors, 'portfolio');
  if (!Array.isArray(images) || images.length > F25_MAX_IMAGES || !images.every(i => typeof i === 'string' && F25_IMAGE_ID.test(i)) ||
      new Set(images).size !== images.length) return REFUSED(cors, 'images');
  if (!portfolio && images.length < F25_MIN_IMAGES) return REFUSED(cors, 'portfolio');
  if (website === null) return REFUSED(cors, 'website');
  if (social_link === null) return REFUSED(cors, 'social_link');
  if (additional_info === null) return REFUSED(cors, 'additional_info');
  if (!submission_id) return REFUSED(cors, 'submission_id');

  if (!(await sentenceMatches(F25_ELIGIBILITY_TEXT, body.eligibility_text))) return REFUSED(cors, 'eligibility_text');
  const ownR3 = await sentenceMatches(F25_OWNERSHIP_TEXT, body.ownership_text);
  if (!ownR3 && !(await sentenceMatches(F25_OWNERSHIP_TEXT_R2, body.ownership_text))) return REFUSED(cors, 'ownership_text');
  if (!(await sentenceMatches(F25_PRIVACY_TEXT, body.privacy_text))) return REFUSED(cors, 'privacy_text');

  /* Configuration probe (founder decision H-5): an address at
     probe.plotnua.invalid is NEVER written. It reports only whether the
     route WOULD accept; it is never evidence that an application was stored. */
  const probe = email.toLowerCase().endsWith(F25_PROBE_DOMAIN);

  if (!f25WritesEnabled(env)) return NOT_OPEN(cors);
  if (probe) return json(200, { ok: true, state: 'probe_open' }, cors);
  if (!(await f25ChallengeOk(env, body.challenge_token))) return REFUSED(cors, 'challenge');

  const emailKey = email.toLowerCase();
  const stamp = utcStamp(now);
  const confirmations = [F25_ELIGIBILITY_TEXT, ownR3 ? F25_OWNERSHIP_TEXT : F25_OWNERSHIP_TEXT_R2, F25_PRIVACY_TEXT].join('\n');
  const consentHash = await sha256Hex(confirmations);
  const application = {
    application_ref: f25Ref(now),
    artist_name, email, email_key: emailKey, region, medium, bio,
    eligibility_confirmed: true,
    ownership_confirmed: true,
    privacy_notice_read: true,
    status: F25_STATUS,
    submitted_at: stamp,
    submission_id,
    source: F25_SOURCE,
    privacy_version: env.F25_PRIVACY_VERSION,
    consent_version: ownR3 ? F25_CONSENT_VERSION : F25_CONSENT_VERSION_R2,
    consent_at: stamp,
    consent_text_hash: consentHash
  };
  if (portfolio) application.portfolio = portfolio;
  if (website) application.website = website;
  if (social_link) application.social_link = social_link;
  if (additional_info) application.additional_info = additional_info;
  if (images.length) {
    if (!env.F25_IMAGES || !env.F25_REVIEW_BASE) return NOT_OPEN(cors);
    application.artwork_images = images.length;
    application.artwork_review = env.F25_REVIEW_BASE.replace(/\/$/, '') + '/admin/applications/' + application.application_ref;
  }

  let recId, moved = [];
  try {
    if (await f25Exists(env, emailKey, submission_id)) return RECEIVED(cors);
    if (await f25CapReached(env)) return SLOW_DOWN(cors);
    /* The images first: each must be one this application uploaded. They are copied to the application's private
       folder BEFORE the record exists, so a received application always has its images; if anything fails the copies
       are removed and the applicant can simply send again (the holding copies are untouched until success). */
    const prefix = 'applications/' + application.application_ref + '/';
    const kept = [];
    for (let n = 0; n < images.length; n++) {
      const src = await env.F25_IMAGES.get('pending/' + submission_id + '/' + images[n]);
      if (!src) { await Promise.all(moved.map(k => env.F25_IMAGES.delete(k))); return REFUSED(cors, 'images'); }
      const type = (src.httpMetadata && src.httpMetadata.contentType) || 'image/jpeg';
      const key = prefix + (n + 1) + '.' + (F25_IMAGE_TYPES[type] || 'jpg');
      await env.F25_IMAGES.put(key, await src.arrayBuffer(), { httpMetadata: { contentType: type }, customMetadata: src.customMetadata || {} });
      moved.push(key);
      kept.push({ file: key.slice(prefix.length), type, w: Number((src.customMetadata || {}).w) || null, h: Number((src.customMetadata || {}).h) || null, bytes: src.size });
    }
    const created = await atCreate(env, T_F25, application);
    recId = created && created.records && created.records[0] && created.records[0].id;
    if (!recId) throw new Error('airtable_502');
    if (images.length) {
      /* The review copy for PlotArt Studio (founder only): what the founder needs beside the images. Private, EU. */
      const { email: _e, email_key: _k, ...review } = application;
      await env.F25_IMAGES.put(prefix + 'application.json', JSON.stringify({ ...review, airtable_record: recId, images: kept }), { httpMetadata: { contentType: 'application/json' } });
      /* every holding copy for this application goes, including images the applicant removed or replaced */
      const held = await env.F25_IMAGES.list({ prefix: 'pending/' + submission_id + '/', limit: 50 });
      await Promise.all(held.objects.map(o => env.F25_IMAGES.delete(o.key))).catch(() => {});
    }
  } catch (e) {
    if (!recId) await Promise.all(moved.map(k => env.F25_IMAGES.delete(k))).catch(() => {});
    if (recId) return RECEIVED(cors);            /* stored; only the review copy or tidy-up failed */
    return UNAVAILABLE(cors, atReason(e));
  }
  /* The application is stored, and carries its own consent record (version,
     time and hash). The two audit rows below are best-effort: if Airtable
     refuses them, the applicant is still told the truth (received). */
  try {
    await atCreate(env, T_STATUS_LOG, {
      record_ref: recId, from_status: '', to_status: F25_STATUS,
      at: stamp, actor: 'system', reason: 'f25_application_received', register: F25_REGISTER
    });
    await atCreate(env, T_CONSENT, {
      email_hash: await sha256Hex(emailKey),
      privacy_version: env.F25_PRIVACY_VERSION,
      consent_text_hash: consentHash,
      given_at: stamp,
      register: F25_REGISTER
    });
  } catch { /* the application row is the authoritative record */ }
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
        return new Response(null, { status: 403,
          headers: { allow: 'POST, OPTIONS', vary: 'Origin', 'cache-control': 'no-store' } });
      }
      return new Response(null, { status: 204,
        headers: { allow: 'POST, OPTIONS', 'cache-control': 'no-store', ...corsHeaders(cors) } });
    }

    if (!cors) return json(403, { ok: false, state: 'refused' }, null);
    if (!fetchMetadataOk(request)) return REFUSED(cors);

    /* THERE IS NO GET HANDLER. */
    if (request.method !== 'POST') return json(405, { ok: false, state: 'refused' }, cors);

    if (url.pathname === F25_IMAGE_ROUTE) return handleF25Image(env, request, url, cors);

    if (tooMany('post', Date.now(), 30, 60_000)) return SLOW_DOWN(cors);

    const raw = await request.text();
    if (raw.length > (url.pathname === F25_ROUTE ? F25_MAX_BODY : MAX_BODY_BYTES)) return REFUSED(cors, 'body');
    let body;
    try { body = JSON.parse(raw); } catch { return REFUSED(cors, 'body'); }
    if (!body || typeof body !== 'object' || Array.isArray(body)) return REFUSED(cors, 'body');

    if (url.pathname === ROUTE) return handleHost(env, body, now, cors);
    if (url.pathname === ARTIST_ROUTE) return handleArtist(env, body, now, cors);
    if (url.pathname === F25_ROUTE) return handleFounding25(env, body, now, cors);
    return NOT_FOUND(cors);
  }
};

/* EXPORTED FOR TESTS ONLY. Nothing here reaches the network. */
export const __test = {
  V, ALLOWED_KEYS, CONSENT_TEXT, SUBMIT_STATUS, ROUTE, writesEnabled,
  allowedOrigin, fetchMetadataOk, sha256Hex, pickWays, cleanText,
  MAX_BODY_BYTES, MAX_NOTE_CHARS, DAILY_CAP,
  VA, ARTIST_ALLOWED_KEYS, ARTIST_CONSENT_TEXT, ARTIST_ROUTE, ARTIST_DAILY_CAP, artistWritesEnabled,
  cleanPortfolio, pickMany,
  VF, F25_KEYS, F25_REQUIRED, F25_ROUTE, F25_STATUS, F25_CONSENT_VERSION, F25_MAX_BODY, F25_DEFAULT_DAILY_CAP, F25_BURST_PER_MINUTE,
  F25_ELIGIBILITY_TEXT, F25_OWNERSHIP_TEXT, F25_OWNERSHIP_TEXT_R2, F25_CONSENT_VERSION_R2, F25_PRIVACY_TEXT, F25_PROBE_DOMAIN, f25WritesEnabled, f25DailyCap,
  F25_IMAGE_ROUTE, F25_MAX_IMAGES, F25_MIN_IMAGES, F25_MAX_IMAGE_BYTES, sniffImage, f25Url,
  resetRateLimit: () => hits.clear()
};
