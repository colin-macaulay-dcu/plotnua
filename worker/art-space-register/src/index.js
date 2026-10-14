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

    if (tooMany('post', Date.now(), 30, 60_000)) return SLOW_DOWN(cors);

    const raw = await request.text();
    if (raw.length > MAX_BODY_BYTES) return REFUSED(cors, 'body');
    let body;
    try { body = JSON.parse(raw); } catch { return REFUSED(cors, 'body'); }
    if (!body || typeof body !== 'object' || Array.isArray(body)) return REFUSED(cors, 'body');

    if (url.pathname === ROUTE) return handleHost(env, body, now, cors);
    if (url.pathname === ARTIST_ROUTE) return handleArtist(env, body, now, cors);
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
  resetRateLimit: () => hits.clear()
};
