/* PlotNua · Idea Board intake (Phase 1, founder approval of the build 1 Nov 2026). NOT DEPLOYED, NOT ENABLED.
   A SEPARATE public Worker ("plotnua-ideas") bound to the Studio's D1 database, on the pattern of the PlotArt enquiry
   relay. It only ever INSERTS a 'received' idea: nothing it does can make an idea public. Every public idea needs the
   founder's approval in PlotArt Studio (Ideas tab), and only the content pipeline publishes approved ideas.

   POST /v1/ideas   from https://plotnua.ie/ideas.html only (Origin checked).
     · JSON (the page's script)             -> JSON { ok, reference } with CORS for that origin only
     · a plain HTML form (no JavaScript)    -> a small "thank you" page with a link back to the board
   Phase 1 stores: the idea (8-160 characters), an optional area, an optional county and whether to show it.
   It stores NO name, e-mail, telephone, IP address or cookie. Rate limits: a per-isolate burst limit held in memory
   only (never stored), and a daily total in D1 (a number per day). Links, e-mail addresses, telephone numbers and
   markup are refused. A honeypot field and a minimum time on the page silently drop automated posts. */
import { AREAS, COUNTIES, clean, problem } from './ideas-rules.js';
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
  const back = (env.ORIGIN || 'https://plotnua.ie') + '/ideas.html';
  return new Response(`<!doctype html><html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>${E(title)} · PlotNua</title><style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#1B1C1E;color:#F2EBE0;font:17px/1.6 system-ui,sans-serif}
main{max-width:520px;padding:40px 28px}.k{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#B39272;margin:0 0 14px}
h1{font:400 40px/1.1 Georgia,serif;margin:0 0 16px}p{margin:0 0 14px;color:#E7DED0}.ref{font-family:ui-monospace,monospace;color:#F2EBE0}
a{display:inline-block;margin-top:10px;background:#F2EBE0;color:#1B1C1E;text-decoration:none;padding:12px 18px;border-radius:2px;font-weight:600}
</style></head><body><main><p class="k">PlotNua Idea Board</p>${body}<a href="${E(back)}">Back to the Idea Board</a></main></body></html>`,
    { status, headers: { 'Content-Type': 'text/html; charset=utf-8', ...PAGE_SEC } });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), origin = req.headers.get('Origin');
    if (url.pathname !== '/v1/ideas') return new Response('Not found', { status: 404 });
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env, origin) });
    const type = (req.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
    const isForm = type === 'application/x-www-form-urlencoded';
    const reply = (status, body) => isForm
      ? (body.ok ? page(env, status, 'Thank you', `<h1>Thank you.</h1><p>PlotNua will read your idea. If it is approved, it will appear on the board without your name.</p><p>Your reference: <span class="ref">${E(body.reference)}</span></p><p>To ask for an idea to be removed, e-mail hello@plotnua.ie with this reference.</p>`)
                 : page(env, status, 'Not sent', `<h1>Not sent.</h1><p>${E(body.error || 'Your idea could not be sent.')}</p>`))
      : new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...cors(env, origin) } });
    if (req.method !== 'POST') return reply(405, { ok: false, error: 'Refused' });
    if (!origin || origin !== env.ORIGIN) return reply(403, { ok: false, error: 'Refused' });
    if (env.IDEAS_ENABLED !== 'true') return reply(503, { ok: false, error: 'The Idea Board isn’t taking ideas at the moment.' });
    if (type !== 'application/json' && !isForm) return reply(415, { ok: false, error: 'Refused' });

    const ip = req.headers.get('CF-Connecting-IP') || 'local', t = Date.now();
    const h = (hits.get(ip) || []).filter(x => t - x < BURST_MS);
    if (h.length >= BURST) return reply(429, { ok: false, error: 'Thank you — that’s plenty for now. Please try again a little later.' });
    if (hits.size > 10_000) hits.clear();   // bounded: memory only
    hits.set(ip, [...h, t]);

    const raw = await req.text();
    if (raw.length > 2000) return reply(413, { ok: false, error: 'That is too long.' });
    let b;
    if (isForm) b = Object.fromEntries(new URLSearchParams(raw));
    else { try { b = JSON.parse(raw); } catch { return reply(400, { ok: false, error: 'Refused' }); } }
    const keys = ['idea', 'area', 'county', 'show_county', 'website', 't'];
    if (!b || typeof b !== 'object' || Array.isArray(b) || Object.keys(b).some(k => !keys.includes(k))) return reply(400, { ok: false, error: 'Refused' });
    // automated posts: answered as if accepted, never stored
    const fake = () => reply(200, { ok: true, reference: 'PN-I-000000-0000' });
    if (b.website) return fake();
    if (b.t !== undefined && b.t !== '') {
      const shown = Number(b.t);
      if (!Number.isFinite(shown) || t - shown < MIN_MS || t - shown > MAX_AGE_MS) return fake();
    }
    const text = clean(b.idea);
    const why = problem(text);
    if (why) return reply(400, { ok: false, error: why });
    const area = clean(b.area) || null, county = clean(b.county) || null;
    if (area && !AREAS.includes(area)) return reply(400, { ok: false, error: 'Please choose an area from the list.' });
    if (county && !COUNTIES.includes(county)) return reply(400, { ok: false, error: 'Please choose a county from the list.' });
    const show = county && (b.show_county === true || b.show_county === 'on' || b.show_county === '1') ? 1 : 0;

    const day = now().slice(0, 10), cap = Number(env.IDEAS_DAILY_CAP || 60);
    const c = await env.DB.prepare('SELECT n FROM idea_intake_days WHERE day = ?').bind(day).first();
    if (c && c.n >= cap) return reply(429, { ok: false, error: 'The board has had a lot of ideas today. Please try again tomorrow.' });
    const ref = `PN-I-${day.slice(2).replace(/-/g, '')}-${[...crypto.getRandomValues(new Uint8Array(2))].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
    const id = 'i' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
    await env.DB.batch([
      env.DB.prepare('INSERT INTO ideas (id, ref, text, area, county, show_county, status, created_at) VALUES (?,?,?,?,?,?,?,?)').bind(id, ref, text, area, county, show, 'received', now()),
      env.DB.prepare('INSERT INTO idea_intake_days (day, n) VALUES (?, 1) ON CONFLICT(day) DO UPDATE SET n = n + 1').bind(day),
    ]);
    return reply(200, { ok: true, reference: ref });
  },
};
