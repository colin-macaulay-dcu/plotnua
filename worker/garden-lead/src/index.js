/* PlotNua — GARDEN ROOM LEAD WORKER  (FIRST LEAD · PHASE A)
 * ===========================================================================
 * SHIPS CLOSED. WRITES_ENABLED, EMAIL_ENABLED and LEAD_PUBLIC_ENABLED all ship
 * 'false'. Deploying this file records nothing and exposes nothing.
 *
 * WHAT THIS WORKER IS
 *   ONE POST route that records a homeowner's enquiry about ONE supplier's
 *   Garden Room into Airtable, and returns the lead_id it minted. It is the
 *   only code path by which a PlotNua Garden Room lead can come into existence.
 *
 * WHAT THIS WORKER IS NOT
 *   It does not email anybody. There is NO mail adapter in this file, and
 *   EMAIL_ENABLED exists so that refusal is explicit rather than implied by
 *   absence. It does not forward to the supplier — forwarding is a human act.
 *   It does not match, rank, score or introduce. It has NO GET HANDLER, so
 *   there is no read surface, no listing and no lead to enumerate.
 *
 * THE STATUS CEILING
 *   This Worker can write exactly ONE status: 'RECEIVED'. FORWARDED,
 *   SUPPLIER_ACKNOWLEDGED, OUTCOME_KNOWN and NOT_FORWARDED are human acts
 *   recorded by a named reviewer. No automated path can promote a lead, which
 *   is what keeps "a lead was forwarded" a statement about something that
 *   actually happened.
 *
 * FIVE INDEPENDENT HARD STOPS
 *   LEAD_PUBLIC_ENABLED !== 'true' AND no valid preview key -> refused
 *   WRITES_ENABLED !== 'true'                               -> nothing written
 *   no AIRTABLE_TOKEN binding                               -> nothing to write with
 *   no AIRTABLE_BASE binding                                -> nowhere to write to
 *   supplier or product not on the allow-list                -> refused
 *
 * THE PREVIEW GATE IS NOT OBSCURITY.
 *   Phase A must prove the whole mechanism without exposing it. The page hides
 *   the control, but hiding is not a control: a hand-edited DOM could still
 *   post. So the real gate is HERE and it is a secret, not a URL. While
 *   LEAD_PUBLIC_ENABLED is 'false' every write must carry
 *   x-plotnua-lead-preview matching the LEAD_PREVIEW_KEY secret. The key is
 *   never in page source, never in this file, and never in wrangler.toml.
 *
 * SUCCESS REQUIRES A PERSISTED LEAD.
 *   RECEIVED is returned only after Airtable has created the row AND returned
 *   its record id. A 2xx from this Worker therefore means a lead exists. The
 *   page is required to check for lead_id, so a resolved fetch alone can never
 *   be shown to a homeowner as success.
 *
 * typecast:false ON EVERY WRITE, for the same reason as the register Worker:
 * an option that does not exist in Airtable is a REJECTED write, never a
 * silently created one.
 *
 * NOTHING IDENTIFYING IS LOGGED. No IP in clear, no IP hash stored, no user
 * agent. Abuse control is in-memory, per-isolate, and dies with the isolate.
 *
 * WHAT NEVER REACHES THIS WORKER. The page payload is a closed object and
 * carries no Eircode, address, coordinate, ranking position, score, budget
 * band, competitor product or Resolve state. This Worker rejects unknown
 * product ids, so it cannot be used to record an enquiry about anything else.
 * ========================================================================= */

const MAX_BODY_BYTES = 8 * 1024;
const MAX_MESSAGE_CHARS = 2000;
const MAX_NAME_CHARS = 80;
const MAX_EMAIL_CHARS = 120;
const MAX_COUNTY_CHARS = 60;

/* Table name, exactly as the schema creates it. */
const T_LEADS = 'Garden Room Leads';

/* THE ONLY STATUS THIS WORKER MAY WRITE. */
const SUBMIT_STATUS = 'RECEIVED';

/* The only source value this route may record. */
const SOURCE = 'plotnua.garden-room.resolve';

/* ------------------------------------------------------------ allow-list --
   ONE supplier and THREE products. Copied from
   garden-room-recommendation-universe-v1.json (generated 2026-10-07), not from
   memory. A product id absent from this map is refused before anything is
   written, so this Worker cannot record a lead for a supplier nobody has
   approved — which is the whole point of a bounded first proof.

   ADDING A SUPPLIER HERE IS THE ACT THAT MAKES THEM REACHABLE. It is not a
   configuration detail and must not happen without founder authorisation and
   that supplier having been told PlotNua may send them enquiries.           */
const SUPPLIERS = {
  'ORG-000157': {
    name: 'Yard Box',
    atlasRecord: 'recyfWvDVODL06P8l',
    /* The exact sentence the page must render and send. Hashed and compared,
       so a page whose wording drifts stops working rather than recording a
       consent to text nobody approved. */
    consentText: 'I’d like PlotNua to send this enquiry to Yard Box on my behalf, and I’m happy for them to use my name and email to reply to it.',
    products: {
      'receaph6vCI7xtS5K': { name: 'Yardbox The Whistler',  code: 'PROD-000529' },
      'reckMDqp4tVjAjM7b': { name: 'Yardbox The Vancouver', code: 'PROD-000530' },
      'recLEonLKyhNTUiAt': { name: 'Yardbox The Toronto',   code: 'PROD-000531' }
    }
  }
};

/* ------------------------------------------------------------------ cors --
   Headers are added ONLY for the allowed origin. For anything else they are
   absent, so a browser refuses to hand the body to the caller even where this
   Worker also refused on its own account. */
function allowedOrigin(env, request) {
  const o = request.headers.get('origin') || '';
  return o && o === env.ORIGIN ? o : null;
}

function corsHeaders(origin) {
  if (!origin) return { vary: 'Origin' };
  return {
    'access-control-allow-origin': origin,
    'access-control-allow-methods': 'POST, OPTIONS',
    /* the preview header must be allowed through preflight, or the private
       route cannot be exercised from the page at all */
    'access-control-allow-headers': 'content-type, x-plotnua-lead-preview',
    'access-control-max-age': '600',
    vary: 'Origin'
    /* NO access-control-allow-credentials. There is no cookie and no session. */
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

/* FIXED REPLY SHAPES. The only body that carries anything beyond a state is
   the success body, and the only thing it adds is the lead_id this Worker just
   minted — a value the caller did not supply and cannot use to probe for
   anybody else's record. */
const RECEIVED    = (cors, leadId) =>
  json(200, { ok: true, state: 'received', lead_id: leadId }, cors);
const REFUSED     = (cors, field) =>
  json(400, { ok: false, state: 'refused', ...(field ? { field } : {}) }, cors);
const NOT_OPEN    = (cors) => json(503, { ok: false, state: 'not_open' }, cors);
const SLOW_DOWN   = (cors) => json(429, { ok: false, state: 'slow_down' }, cors);
const NOT_FOUND   = (cors) => json(404, { ok: false, state: 'refused' }, cors);
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

/* Constant-time-ish string compare, so neither a consent mismatch nor a wrong
   preview key leaks timing. */
function sameString(a, b) {
  const A = String(a), B = String(b);
  if (A.length !== B.length) return false;
  let diff = 0;
  for (let i = 0; i < A.length; i++) diff |= A.charCodeAt(i) ^ B.charCodeAt(i);
  return diff === 0;
}

/* --------------------------------------------------------- the release gate --
   TWO WAYS TO BE OPEN, AND THE DEFAULT IS NEITHER.

   Public: LEAD_PUBLIC_ENABLED === 'true'. Ships 'false' and must not be
   flipped until the supplier has been told PlotNua may send them enquiries.

   Private: a preview key that matches the LEAD_PREVIEW_KEY secret. An absent
   or empty secret closes the private route too, so a deploy that forgets the
   secret is closed rather than open. */
function releaseOpen(env, request) {
  if (env.LEAD_PUBLIC_ENABLED === 'true') return true;
  const key = env.LEAD_PREVIEW_KEY;
  if (typeof key !== 'string' || key.length < 16) return false;
  const sent = request.headers.get('x-plotnua-lead-preview') || '';
  return sameString(key, sent);
}

/* ------------------------------------------------------------ rate limit --
   In-memory, per-isolate, keyed on nothing identifying. */
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

/* typecast is ALWAYS false and is written out here rather than defaulted, so
   no future edit can quietly enable option creation. */
const atCreate = (env, table, fields) =>
  atRequest(env, 'POST', '/' + encodeURIComponent(table),
            { records: [{ fields }], typecast: false });

const utcStamp = (d) => d.toISOString().replace(/\.\d{3}Z$/, 'Z');

/* ---------------------------------------------------------------- lead id --
   Minted here, never accepted from the caller. Date prefix so a founder can
   read it at a glance; random tail so it is not guessable or enumerable. */
function mintLeadId(now) {
  const d = utcStamp(now).slice(0, 10).replace(/-/g, '');
  const r = crypto.randomUUID().replace(/-/g, '').slice(0, 8).toUpperCase();
  return 'PNL-' + d + '-' + r;
}

/* ---------------------------------------------------------- validation ---- */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function cleanText(v, max) {
  if (typeof v !== 'string') return null;
  const t = v.replace(/\s+/g, ' ').trim();
  if (!t) return null;
  return t.length > max ? t.slice(0, max) : t;
}

/* The message keeps its line breaks — it is the homeowner's own words and the
   supplier will read it — so it is trimmed and capped but not collapsed. */
function cleanMessage(v, max) {
  if (typeof v !== 'string') return null;
  const t = v.replace(/\r\n/g, '\n').replace(/[ \t]+\n/g, '\n').trim();
  if (!t) return null;
  return t.length > max ? t.slice(0, max) : t;
}

/* -------------------------------------------------------------- handler --- */
async function handleEnquiry(env, body, now, cors) {
  /* 1 · the supplier and product must be on the allow-list, before anything
     else is considered. An unknown id is refused here, so no part of this
     Worker ever runs for a supplier nobody approved. */
  const orgId = cleanText(body.supplier_org_id, 40);
  const supplier = orgId ? SUPPLIERS[orgId] : null;
  if (!supplier) return REFUSED(cors, 'supplier_org_id');

  const productId = cleanText(body.product_id, 40);
  const product = productId ? supplier.products[productId] : null;
  if (!product) return REFUSED(cors, 'product_id');

  /* 2 · the homeowner's own fields */
  const name = cleanText(body.homeowner_name, MAX_NAME_CHARS);
  const email = cleanText(body.homeowner_email, MAX_EMAIL_CHARS);
  const county = cleanText(body.county, MAX_COUNTY_CHARS);
  const message = cleanMessage(body.message, MAX_MESSAGE_CHARS);

  if (!name) return REFUSED(cors, 'homeowner_name');
  if (!email || !EMAIL_RE.test(email)) return REFUSED(cors, 'homeowner_email');
  if (!county) return REFUSED(cors, 'county');
  if (!message) return REFUSED(cors, 'message');

  /* 3 · honeypot. A field no human can see and no human fills. */
  if (cleanText(body.gotcha, 200)) return REFUSED(cors, 'gotcha');

  /* 4 · consent. The page sends the sentence it ACTUALLY RENDERED; this
     Worker hashes it and compares against the canonical sentence for this
     supplier. Wording drift closes the route rather than recording a consent
     to text nobody approved. */
  if (body.consent !== true) return REFUSED(cors, 'consent');
  const canonicalHash = await sha256Hex(supplier.consentText);
  const sentHash = await sha256Hex(cleanText(body.consent_text, 1000) || '');
  if (!sameString(canonicalHash, sentHash)) return REFUSED(cors, 'consent_text');

  /* 5 · the source is fixed, never taken from the caller. */
  if (body.source !== undefined && body.source !== SOURCE) {
    return REFUSED(cors, 'source');
  }

  if (!writesEnabled(env)) return NOT_OPEN(cors);

  const leadId = mintLeadId(now);
  const stamp = utcStamp(now);

  const fields = {
    lead_id: leadId,
    created_at: stamp,
    product_id: productId,
    product_name: product.name,
    supplier_org_id: orgId,
    supplier_name: supplier.name,
    homeowner_name: name,
    homeowner_email: email,
    county,
    message,
    consent_text_hash: canonicalHash,
    consent_at: stamp,
    privacy_version: env.PRIVACY_VERSION,
    source: SOURCE,
    status: SUBMIT_STATUS
  };

  /* A TEST LEAD SAYS SO, IN THE RECORD. Phase A writes real rows to prove the
     mechanism; a row that cannot be told from a homeowner's is a trap for
     whoever reads the table later. The flag is set by the Worker from its own
     release state, never from the caller: while the public route is closed,
     every lead this Worker records is by definition a private test. */
  if (env.LEAD_PUBLIC_ENABLED !== 'true') {
    fields.message = '[PLOTNUA PHASE A TEST LEAD — NOT A HOMEOWNER]\n\n' + message;
  }

  let recId = null;
  try {
    const created = await atCreate(env, T_LEADS, fields);
    recId = created && created.records && created.records[0] && created.records[0].id;
  } catch (e) {
    return UNAVAILABLE(cors, atReason(e));
  }

  /* SUCCESS REQUIRES A PERSISTED ROW. If Airtable answered without a record
     id, nothing is claimed: the caller gets an unavailable, keeps what the
     homeowner typed, and can try again. */
  if (!recId) return UNAVAILABLE(cors, 'atnorec');

  return RECEIVED(cors, leadId);
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

    /* THERE IS NO GET HANDLER. Not for status, not for a lead, not for a
       count. A lead store with no read surface cannot be enumerated. */
    if (request.method !== 'POST') {
      return json(405, { ok: false, state: 'refused' }, cors);
    }

    /* THE RELEASE GATE, BEFORE THE BODY IS EVEN READ. A closed Worker does no
       work on an unauthorised request and reveals nothing about what it would
       have accepted. */
    if (!releaseOpen(env, request)) return NOT_OPEN(cors);

    if (tooMany('post', Date.now(), 20, 60_000)) return SLOW_DOWN(cors);

    const raw = await request.text();
    if (raw.length > MAX_BODY_BYTES) return REFUSED(cors, 'body');
    let body;
    try { body = JSON.parse(raw); } catch { return REFUSED(cors, 'body'); }
    if (!body || typeof body !== 'object') return REFUSED(cors, 'body');

    if (url.pathname === '/v1/garden-lead/enquiry') {
      return handleEnquiry(env, body, now, cors);
    }
    return NOT_FOUND(cors);
  }
};

/* EXPORTED FOR TESTS ONLY. Nothing here reaches the network. */
export const __test = {
  SUPPLIERS, SUBMIT_STATUS, SOURCE, T_LEADS,
  writesEnabled, releaseOpen, allowedOrigin, corsHeaders, fetchMetadataOk,
  sha256Hex, sameString, cleanText, cleanMessage, mintLeadId, atReason,
  EMAIL_RE, MAX_BODY_BYTES, MAX_MESSAGE_CHARS, handleEnquiry,
  /* The rate limiter is per-isolate and deliberately has no reset in
     production. A test suite is one isolate for dozens of cases, so without
     this the limiter would fire mid-suite and later cases would be measuring
     the limiter rather than the thing they name. Exposed for that reason
     only; nothing in the request path can reach it. */
  resetRateLimit: () => hits.clear()
};
