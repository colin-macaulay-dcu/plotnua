/* PlotNua · The Borrowed Garden noticeboard intake (MVP, founder decision 4 Nov 2026). NOT DEPLOYED, NOT ENABLED.
   A SEPARATE public Worker ("plotnua-garden-board") bound to the Studio's D1 database, on the pattern of the Idea Board
   intake (ideas.js). It only ever INSERTS a 'received' listing: nothing it does can make a listing public. Every public
   listing needs the founder's approval in PlotArt Studio (Garden tab), and only the content pipeline publishes it.

   POST /v1/garden-listings   from https://plotnua.ie only (Origin checked).
     · JSON (the page's script)          -> JSON { ok, reference } with CORS for that origin only
     · a plain HTML form (no JavaScript) -> a small "thank you" page with a link back to the noticeboard
   Stores: the kind (I have space / I want space), county, a general area, the type of space, approximate
   availability, a short description, and a contact e-mail address that is PRIVATE: it is never published, never
   returned to anyone, and exists only so PlotNua (and, once switched on, the enquiry relay) can reach the person.
   No name, telephone number, address, Eircode, IP address or cookie. Links, e-mail addresses, telephone numbers,
   Eircodes, house numbers and markup are refused in the public text. A honeypot field and a minimum time on the page
   silently drop automated posts; a per-isolate burst limit (memory only) and a daily total in D1 limit volume.
   Monetisation fields exist in the table but are never set here: every listing arrives free, individual, unfeatured. */
import { COUNTIES, clean, listingProblem, EMAIL } from './garden-rules.js';
const BURST = 3, BURST_MS = 10 * 60_000, MIN_MS = 3000, MAX_AGE_MS = 24 * 3600_000;
const hits = new Map();   // per-isolate, in memory only: never written anywhere
const now = () => new Date().toISOString();
const E = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function cors(env, origin) {
  const ok = origin && origin === env.ORIGIN;
  return { 'Access-Control-Allow-Origin': ok ? origin : 'null', 'Vary': 'Origin', 'Access-Control-Allow-Methods': 'POST',
    'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
}
const PAGE_SEC = { 'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  'X-Frame-Options': 'DENY', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store' };
function page(env, status, title, body) {
  const back = (env.ORIGIN || 'https://plotnua.ie') + '/borrowed-garden-board.html';
  return new Response(`<!doctype html><html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>${E(title)} · PlotNua</title><style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#1B1C1E;color:#F2EBE0;font:17px/1.6 system-ui,sans-serif}
main{max-width:520px;padding:40px 28px}.k{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#CFE0B4;margin:0 0 14px}
h1{font:400 40px/1.1 Georgia,serif;margin:0 0 16px}p{margin:0 0 14px;color:#E7DED0}.ref{font-family:ui-monospace,monospace;color:#F2EBE0}
a{display:inline-block;margin-top:10px;background:#F2EBE0;color:#1B1C1E;text-decoration:none;padding:12px 18px;border-radius:2px;font-weight:600}
</style></head><body><main><p class="k">The Borrowed Garden noticeboard</p>${body}<a href="${E(back)}">Back to the noticeboard</a></main></body></html>`,
    { status, headers: { 'Content-Type': 'text/html; charset=utf-8', ...PAGE_SEC } });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), origin = req.headers.get('Origin');
    if (url.pathname !== '/v1/garden-listings') return new Response('Not found', { status: 404 });
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env, origin) });
    const type = (req.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
    const isForm = type === 'application/x-www-form-urlencoded';
    const reply = (status, body) => isForm
      ? (body.ok ? page(env, status, 'Thank you', `<h1>Thank you.</h1><p>PlotNua will read your listing. If it is approved, it appears on the noticeboard without your name or contact details.</p><p>Your reference: <span class="ref">${E(body.reference)}</span></p><p>To change or remove it, e-mail hello@plotnua.ie with this reference.</p>`)
                 : page(env, status, 'Not sent', `<h1>Not sent.</h1><p>${E(body.error || 'Your listing could not be sent.')}</p>`))
      : new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...cors(env, origin) } });
    if (req.method !== 'POST') return reply(405, { ok: false, error: 'Refused' });
    if (!origin || origin !== env.ORIGIN) return reply(403, { ok: false, error: 'Refused' });
    if (env.GARDEN_ENABLED !== 'true') return reply(503, { ok: false, error: 'The noticeboard isn’t taking listings at the moment.' });
    if (type !== 'application/json' && !isForm) return reply(415, { ok: false, error: 'Refused' });

    const ip = req.headers.get('CF-Connecting-IP') || 'local', t = Date.now();
    const h = (hits.get(ip) || []).filter(x => t - x < BURST_MS);
    if (h.length >= BURST) return reply(429, { ok: false, error: 'Thank you — that’s plenty for now. Please try again a little later.' });
    if (hits.size > 10_000) hits.clear();   // bounded: memory only
    hits.set(ip, [...h, t]);

    const raw = await req.text();
    if (raw.length > 3000) return reply(413, { ok: false, error: 'That is too long.' });
    let b;
    if (isForm) b = Object.fromEntries(new URLSearchParams(raw));
    else { try { b = JSON.parse(raw); } catch { return reply(400, { ok: false, error: 'Refused' }); } }
    const keys = ['kind', 'county', 'area', 'space_type', 'availability', 'description', 'email', 'consent', 'website', 't'];
    if (!b || typeof b !== 'object' || Array.isArray(b) || Object.keys(b).some(k => !keys.includes(k))) return reply(400, { ok: false, error: 'Refused' });
    // automated posts: answered as if accepted, never stored
    const fake = () => reply(200, { ok: true, reference: 'PN-G-000000-0000' });
    if (b.website) return fake();
    if (b.t !== undefined && b.t !== '') {
      const shown = Number(b.t);
      if (!Number.isFinite(shown) || t - shown < MIN_MS || t - shown > MAX_AGE_MS) return fake();
    }
    const l = { kind: clean(b.kind), county: clean(b.county), area: clean(b.area), space_type: clean(b.space_type),
      availability: clean(b.availability), description: clean(b.description) };
    const why = listingProblem(l);
    if (why) return reply(400, { ok: false, error: why });
    const email = clean(b.email).toLowerCase();
    if (!EMAIL.test(email) || email.length > 120) return reply(400, { ok: false, error: 'Please give an e-mail address PlotNua can reach you at. It is never shown on the noticeboard.' });
    if (!(b.consent === true || b.consent === 'on' || b.consent === '1')) return reply(400, { ok: false, error: 'Please tick the box to agree how your listing is shown.' });
    if (!COUNTIES.includes(l.county)) return reply(400, { ok: false, error: 'Please choose a county from the list.' });

    const day = now().slice(0, 10), cap = Number(env.GARDEN_DAILY_CAP || 40);
    const c = await env.DB.prepare('SELECT n FROM garden_intake_days WHERE day = ?').bind(day).first();
    if (c && c.n >= cap) return reply(429, { ok: false, error: 'The noticeboard has had a lot of listings today. Please try again tomorrow.' });
    const ref = `PN-G-${day.slice(2).replace(/-/g, '')}-${[...crypto.getRandomValues(new Uint8Array(2))].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
    const id = 'g' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO garden_listings (id, ref, kind, county, area, space_type, availability, description, contact_email, consent_at, status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).bind(id, ref, l.kind, l.county, l.area, l.space_type, l.availability, l.description, email, now(), 'received', now()),
      env.DB.prepare('INSERT INTO garden_intake_days (day, n) VALUES (?, 1) ON CONFLICT(day) DO UPDATE SET n = n + 1').bind(day),
    ]);
    return reply(200, { ok: true, reference: ref });
  },
};
