/* PlotNua — INTRODUCTION REQUESTS  (PACKAGE N · SHIPS CLOSED)
 * ===========================================================================
 * POST /v1/introduction records a homeowner's request for an introduction and
 * (optionally) tells the founder that one has arrived. Nothing else.
 *
 * FOUNDER-APPROVED PRINCIPLES THIS FILE ENFORCES
 *   - Free to homeowners, no obligation. The Worker takes no payment field.
 *   - Supplier-specific requests are accepted ONLY for a supplier on
 *     INTRO_SUPPLIERS, and a supplier is added there only after a WRITTEN
 *     agreement to receive introductions exists. The list ships EMPTY, so
 *     today every request is a GENERAL request.
 *   - A general request gives PlotNua permission to review and reply. It is
 *     NOT permission to share with a supplier; that needs separate, later
 *     consent, recorded outside this Worker.
 *   - No automatic supplier forwarding. There is no supplier address in this
 *     file. The one email this file can send goes to the founder, and carries
 *     the reference, supplier, county and timeframe only — never the
 *     homeowner's name, email or words.
 *   - Status ceiling: RECEIVED. Every later status is a human act.
 *   - Retention: every record carries delete_after = created + 12 months.
 *
 * FOUR INDEPENDENT SWITCHES, ALL SHIPPING 'false' / ABSENT
 *   INTRO_PUBLIC_ENABLED   public route. Off -> only the preview secret gets in.
 *   INTRO_WRITES_ENABLED   off -> nothing is written (plus token and base).
 *   INTRO_NOTIFY_ENABLED   off -> no email (plus RESEND_API_KEY, NOTIFY_TO,
 *                          NOTIFY_FROM).
 *   INTRO_SUPPLIERS        empty -> no supplier-specific request is possible.
 *
 * The Yard Box Phase A route in index.js is untouched and keeps its own
 * switches; opening one route never opens the other.
 * ========================================================================= */

export const INTRO_PATH = '/v1/introduction';
export const T_INTROS = 'Introduction Requests';
export const INTRO_STATUS = 'RECEIVED';
export const RETENTION_MONTHS = 12;
export const MIN_FILL_MS = 3000;          /* a form completed faster is a bot */

const MAX_BODY_BYTES = 6 * 1024;
const MAX_NAME = 80, MAX_EMAIL = 120, MAX_DESC = 1000;

/* -------------------------------------------------------------- wording --
   The exact sentences the page renders. Hashed and compared: a page whose
   wording drifts is refused rather than recording consent to unapproved text. */
export const SUPPLIER_CONSENT_TEMPLATE =
  'I agree that PlotNua may share my enquiry and contact details with [supplier name] so they can contact me about this project.';
export const GENERAL_CONSENT =
  'I agree that PlotNua may use my enquiry and contact details to review my project and reply to me. PlotNua will not share my details with any supplier unless I give separate permission.';
export const supplierConsent = (name) => SUPPLIER_CONSENT_TEMPLATE.replace('[supplier name]', name);

/* -------------------------------------------------------- the allow-list --
   EMPTY BY DESIGN. Adding an entry is the act that lets a homeowner ask for
   their details to go to that supplier. It requires: a written agreement with
   the supplier to receive introductions, founder authorisation, and the same
   supplier added to atlas-tools/release/plotnua-introductions.json.
   Shape: 'supplier-slug': { name: 'Trading Name', agreement: 'ref/date' }   */
export const INTRO_SUPPLIERS = Object.freeze({});

export const TIMEFRAMES = Object.freeze({
  'within-3-months': 'Within 3 months',
  '3-6-months': '3 to 6 months',
  '6-12-months': '6 to 12 months',
  'over-12-months': 'More than 12 months',
  'not-sure': 'Not sure yet'
});

/* The island of Ireland, as the page's select lists them. */
export const COUNTIES = Object.freeze([
  'Antrim', 'Armagh', 'Carlow', 'Cavan', 'Clare', 'Cork', 'Derry', 'Donegal',
  'Down', 'Dublin', 'Fermanagh', 'Galway', 'Kerry', 'Kildare', 'Kilkenny',
  'Laois', 'Leitrim', 'Limerick', 'Longford', 'Louth', 'Mayo', 'Meath',
  'Monaghan', 'Offaly', 'Roscommon', 'Sligo', 'Tipperary', 'Tyrone',
  'Waterford', 'Westmeath', 'Wexford', 'Wicklow'
]);

const PAGE_RE = /^\/[a-z0-9][a-z0-9\-\/]{0,100}\.html$/;
const SLUG_RE = /^[a-z0-9][a-z0-9-]{1,40}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/* ------------------------------------------------------------- helpers --- */
const enc = new TextEncoder();
export async function sha256Hex(s) {
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
function cleanText(v, max) {
  if (typeof v !== 'string') return null;
  const t = v.replace(/\s+/g, ' ').trim();
  if (!t) return null;
  return t.length > max ? t.slice(0, max) : t;
}
function cleanDesc(v) {
  if (v === undefined || v === null || v === '') return '';
  if (typeof v !== 'string') return null;
  const t = v.replace(/\r\n/g, '\n').replace(/[ \t]+\n/g, '\n').trim();
  return t.length > MAX_DESC ? t.slice(0, MAX_DESC) : t;
}
const utcStamp = (d) => d.toISOString().replace(/\.\d{3}Z$/, 'Z');

export function deleteAfter(now) {
  const d = new Date(now.getTime());
  d.setUTCMonth(d.getUTCMonth() + RETENTION_MONTHS);
  return d.toISOString().slice(0, 10);
}

export function mintIntroId(now) {
  const d = utcStamp(now).slice(0, 10).replace(/-/g, '');
  const r = crypto.randomUUID().replace(/-/g, '').slice(0, 8).toUpperCase();
  return 'PNI-' + d + '-' + r;
}

/* --------------------------------------------------------------- gates ---- */
export function introOpen(env, request) {
  if (env.INTRO_PUBLIC_ENABLED === 'true') return true;
  const key = env.LEAD_PREVIEW_KEY;
  if (typeof key !== 'string' || key.length < 16) return false;
  return sameString(key, request.headers.get('x-plotnua-lead-preview') || '');
}
export function introWritesEnabled(env) {
  return env.INTRO_WRITES_ENABLED === 'true' && !!env.AIRTABLE_TOKEN && !!env.AIRTABLE_BASE;
}
export function notifyEnabled(env) {
  return env.INTRO_NOTIFY_ENABLED === 'true' && !!env.RESEND_API_KEY &&
         !!env.NOTIFY_TO && !!env.NOTIFY_FROM;
}

const hits = new Map();
function tooMany(now) {
  const rec = hits.get('intro');
  if (!rec || now - rec.t > 60_000) { hits.set('intro', { t: now, n: 1 }); return false; }
  rec.n += 1;
  return rec.n > 10;
}
export const resetIntroRateLimit = () => hits.clear();

/* ----------------------------------------------------- founder notice ---- */
/* MINIMAL BY CONSTRUCTION: built only from the reference, the kind, the
   supplier name, the county and the timeframe label. The homeowner's name,
   email and description are not parameters of this function. */
export function founderNotice(ref, kind, supplierName, county, timeframeLabel) {
  const who = kind === 'supplier' ? supplierName : 'General (no supplier named)';
  return {
    subject: 'PlotNua introduction request ' + ref,
    text: [
      'A new introduction request has been recorded.',
      '',
      'Reference: ' + ref,
      'Supplier:  ' + who,
      'County:    ' + county,
      'Timeframe: ' + timeframeLabel,
      '',
      'Contact details are not included in this email. Review the request in the',
      'Airtable table "' + T_INTROS + '". Nothing has been sent to any supplier.'
    ].join('\n')
  };
}

async function sendFounderNotice(env, notice) {
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({ from: env.NOTIFY_FROM, to: [env.NOTIFY_TO], subject: notice.subject, text: notice.text })
  });
  return r.ok;
}

/* ------------------------------------------------------------- handler ---- */
export async function handleIntroduction(request, env, now, cors, json) {
  const REFUSED = (field) => json(400, { ok: false, state: 'refused', ...(field ? { field } : {}) }, cors);
  const NOT_OPEN = () => json(503, { ok: false, state: 'not_open' }, cors);
  const UNAVAILABLE = () => json(503, { ok: false, state: 'unavailable' }, cors);

  /* gate before the body is read */
  if (!introOpen(env, request)) return NOT_OPEN();
  if (tooMany(Date.now())) return json(429, { ok: false, state: 'slow_down' }, cors);

  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) return REFUSED('body');
  let b;
  try { b = JSON.parse(raw); } catch { return REFUSED('body'); }
  if (!b || typeof b !== 'object' || Array.isArray(b)) return REFUSED('body');

  /* closed payload: no phone, no Eircode, no address, nothing unexpected */
  const ALLOWED = ['name', 'email', 'county', 'timeframe', 'description', 'supplier',
                   'page', 'consent', 'consent_text', 'elapsed_ms', 'gotcha'];
  for (const k of Object.keys(b)) if (!ALLOWED.includes(k)) return REFUSED('unexpected_field');

  /* honeypot and timing, before any field is considered */
  if (cleanText(b.gotcha, 200)) return REFUSED('gotcha');
  if (typeof b.elapsed_ms !== 'number' || !(b.elapsed_ms >= MIN_FILL_MS)) return REFUSED('timing');

  /* supplier: absent = general; present = must be on the written-agreement list */
  let kind = 'general', supplierSlug = '', supplierName = '';
  if (b.supplier !== undefined && b.supplier !== null && b.supplier !== '') {
    const s = cleanText(b.supplier, 41);
    if (!s || !SLUG_RE.test(s) || !Object.prototype.hasOwnProperty.call(INTRO_SUPPLIERS, s)) return REFUSED('supplier');
    kind = 'supplier'; supplierSlug = s; supplierName = INTRO_SUPPLIERS[s].name;
  }

  const name = cleanText(b.name, MAX_NAME);
  const email = cleanText(b.email, MAX_EMAIL);
  const county = cleanText(b.county, 20);
  const timeframe = cleanText(b.timeframe, 20);
  const description = cleanDesc(b.description);
  const page = cleanText(b.page, 120);

  if (!name) return REFUSED('name');
  if (!email || !EMAIL_RE.test(email)) return REFUSED('email');
  if (!county || !COUNTIES.includes(county)) return REFUSED('county');
  if (!timeframe || !Object.prototype.hasOwnProperty.call(TIMEFRAMES, timeframe)) return REFUSED('timeframe');
  if (description === null) return REFUSED('description');
  if (!page || !PAGE_RE.test(page)) return REFUSED('page');

  /* consent: an explicit true, and the exact approved sentence for this kind */
  if (b.consent !== true) return REFUSED('consent');
  const canonical = kind === 'supplier' ? supplierConsent(supplierName) : GENERAL_CONSENT;
  const canonicalHash = await sha256Hex(canonical);
  const sentHash = await sha256Hex(cleanText(b.consent_text, 400) || '');
  if (!sameString(canonicalHash, sentHash)) return REFUSED('consent_text');

  if (!introWritesEnabled(env)) return NOT_OPEN();

  const ref = mintIntroId(now);
  const stamp = utcStamp(now);
  const fields = {
    request_id: ref,
    created_at: stamp,
    kind,
    supplier_slug: supplierSlug,
    supplier_name: supplierName,
    homeowner_name: name,
    homeowner_email: email,
    county,
    timeframe: TIMEFRAMES[timeframe],
    description,
    page,
    consent_text_hash: canonicalHash,
    consent_at: stamp,
    privacy_version: env.INTRO_PRIVACY_VERSION || '',
    status: INTRO_STATUS,
    delete_after: deleteAfter(now),
    test_record: env.INTRO_PUBLIC_ENABLED !== 'true'
  };

  let recId = null;
  try {
    const r = await fetch('https://api.airtable.com/v0/' + env.AIRTABLE_BASE + '/' + encodeURIComponent(T_INTROS), {
      method: 'POST',
      headers: { authorization: 'Bearer ' + env.AIRTABLE_TOKEN, 'content-type': 'application/json' },
      body: JSON.stringify({ records: [{ fields }], typecast: false })
    });
    if (r.ok) { const j = await r.json(); recId = j && j.records && j.records[0] && j.records[0].id; }
  } catch { recId = null; }
  /* success requires a persisted row */
  if (!recId) return UNAVAILABLE();

  /* founder notice: best effort, AFTER the row exists, never blocking the reply */
  if (notifyEnabled(env)) {
    try { await sendFounderNotice(env, founderNotice(ref, kind, supplierName, county, TIMEFRAMES[timeframe])); }
    catch { /* the row exists; the founder sees it in Airtable */ }
  }

  return json(200, { ok: true, state: 'received', reference: ref }, cors);
}
