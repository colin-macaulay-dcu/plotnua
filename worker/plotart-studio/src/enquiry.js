/* PlotArt · buyer-to-artist enquiry relay (Phase 3, 29 Oct 2026). A SEPARATE public Worker ("plotart-enquiry") bound to
   the Studio's D1 database. NOT DEPLOYED.

   POST /v1/enquiry  from plotnua.ie artwork and gallery pages only (Origin checked; CORS for that origin only).
   It accepts an enquiry only for a PUBLISHED gallery (and, for a work, one that is live and available or reserved),
   records it with a reference, and emails it to the artist with Reply-To set to the buyer, so the artist answers the
   buyer directly: the founder is not an intermediary. The buyer gets a short receipt. Nothing is shown to the buyer
   about the artist's address. No IP address is stored; rate limits are per-isolate and per-day caps in D1. */
import { send } from './mailer.js';

const NOTICE = 'PA-ENQ-2026-10-29';   // (a Worker entry module may export only handlers)
const DAILY_PER_ARTIST = 40, DAILY_TOTAL = 300, BURST = 5, BURST_MS = 10 * 60_000;
const hits = new Map();
const now = () => new Date().toISOString();

function cors(env, origin) {
  const ok = origin && origin === env.ORIGIN;
  return { 'Access-Control-Allow-Origin': ok ? origin : 'null', 'Vary': 'Origin', 'Access-Control-Allow-Methods': 'POST',
    'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
}
const reply = (env, origin, status, body) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...cors(env, origin) } });

async function live(env, slug) {
  const a = await env.DB.prepare("SELECT * FROM artists WHERE slug = ? AND account_status IN ('invited','active')").bind(slug).first();
  if (!a) return null;
  const q = await env.DB.prepare("SELECT version FROM publish_queue WHERE artist_id = ? AND status = 'published' ORDER BY version DESC LIMIT 1").bind(a.id).first();
  if (!q) return null;
  const v = await env.DB.prepare('SELECT snapshot FROM versions WHERE artist_id = ? AND version = ?').bind(a.id, q.version).first();
  const snap = JSON.parse(v.snapshot);
  return snap.works.length ? { artist: a, snap } : null;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), origin = req.headers.get('Origin');
    if (url.pathname !== '/v1/enquiry') return new Response('Not found', { status: 404 });
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env, origin) });
    if (req.method !== 'POST') return reply(env, origin, 405, { ok: false });
    if (origin !== env.ORIGIN) return reply(env, origin, 403, { ok: false, error: 'Refused' });
    if (env.ENQUIRIES_ENABLED !== 'true') return reply(env, origin, 503, { ok: false, error: 'Enquiries aren’t open yet. Please email hello@plotnua.ie.' });
    const ip = req.headers.get('CF-Connecting-IP') || 'local', t = Date.now();
    const h = (hits.get(ip) || []).filter(x => t - x < BURST_MS);
    if (h.length >= BURST) return reply(env, origin, 429, { ok: false, error: 'Too many enquiries just now. Please try again later.' });
    hits.set(ip, [...h, t]);
    const raw = await req.text();
    if (raw.length > 8000) return reply(env, origin, 413, { ok: false, error: 'That message is too long.' });
    let b; try { b = JSON.parse(raw); } catch { return reply(env, origin, 400, { ok: false, error: 'Refused' }); }
    const keys = ['ref', 'notice', 'name', 'email', 'message', 'website'];
    if (!b || typeof b !== 'object' || Object.keys(b).some(k => !keys.includes(k))) return reply(env, origin, 400, { ok: false, error: 'Refused' });
    if (b.website) return reply(env, origin, 200, { ok: true, reference: 'PA-E-000000-0000' });       // honeypot: silently dropped
    if (b.notice !== NOTICE) return reply(env, origin, 400, { ok: false, error: 'Please reload the page and try again.' });
    const name = String(b.name || '').trim(), email = String(b.email || '').trim(), message = String(b.message || '').trim();
    if (name.length < 1 || name.length > 80 || /[<>]/.test(name)) return reply(env, origin, 400, { ok: false, error: 'Please check your name.' });
    if (!/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(email) || email.length > 254) return reply(env, origin, 400, { ok: false, error: 'Please check your email address.' });
    if (message.length < 10 || message.length > 1500) return reply(env, origin, 400, { ok: false, error: 'Please write a message of 10 to 1,500 characters.' });
    const m = /^PA-([a-z0-9]+(?:-[a-z0-9]+){0,6}?)(?:-(w[0-9a-z]{2,24}))?$/.exec(String(b.ref || ''));
    if (!m) return reply(env, origin, 400, { ok: false, error: 'Refused' });
    const g = await live(env, m[1]);
    if (!g) return reply(env, origin, 404, { ok: false, error: 'This gallery isn’t taking enquiries. Please email hello@plotnua.ie.' });
    let work = null;
    if (m[2]) {
      work = g.snap.works.find(w => w.id === m[2]);
      if (!work || !['available', 'reserved'].includes(work.availability)) return reply(env, origin, 409, { ok: false, error: 'This work isn’t available. You can still ask about the artist’s other work.' });
    }
    const day = new Date().toISOString().slice(0, 10);
    const perArtist = await env.DB.prepare('SELECT COUNT(*) AS n FROM enquiries WHERE artist_id = ? AND created_at >= ?').bind(g.artist.id, day).first();
    const total = await env.DB.prepare('SELECT COUNT(*) AS n FROM enquiries WHERE created_at >= ?').bind(day).first();
    if (perArtist.n >= DAILY_PER_ARTIST || total.n >= DAILY_TOTAL) return reply(env, origin, 429, { ok: false, error: 'We’re receiving a lot of enquiries. Please try again tomorrow or email hello@plotnua.ie.' });
    const ymd = day.slice(2).replace(/-/g, '');
    const ref = `PA-E-${ymd}-${[...crypto.getRandomValues(new Uint8Array(3))].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
    const id = 'e' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
    const del = new Date(Date.now() + 730 * 86400_000).toISOString();
    await env.DB.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).bind(id, ref, g.artist.id, work ? work.id : null, work ? work.title : null, name, email, message, NOTICE, now(), 'received', del).run();
    const about = work ? `“${work.title}”` : 'your work';
    const r1 = await send(env, { to: g.artist.email, replyTo: email,
      subject: `PlotArt enquiry about ${work ? work.title : 'your work'} · ${ref}`,
      text: `Hello ${g.artist.display_name.split(' ')[0]},\n\n${name} has sent an enquiry about ${about} through your PlotArt gallery.\n\n` +
        `"${message}"\n\nReply to this email to answer ${name} directly (your reply goes to ${email}).\n\n` +
        `Reference: ${ref}${work ? `\nArtwork: https://plotnua.ie/plotart/artists/${g.artist.slug}/${work.slug}.html` : ''}\n\n` +
        `PlotArt takes no commission on enquiries from your founding year. Any sale is agreed directly between you and the buyer.\n\nPlotArt · part of PlotNua` });
    await send(env, { to: email, replyTo: env.REPLY_TO || 'hello@plotnua.ie', subject: `Your PlotArt enquiry · ${ref}`,
      text: `Hello ${name},\n\nThank you. Your enquiry about ${work ? `“${work.title}”` : `work by ${g.artist.display_name}`} has been passed to ${g.artist.display_name}, who will reply to you by email.\n\n` +
        `Reference: ${ref}\n\nHow we handle enquiries: https://plotnua.ie/privacy.html#plotart-enquiries\n\nPlotArt · part of PlotNua` });
    await env.DB.prepare('UPDATE enquiries SET status=?, sent_at=?, detail=? WHERE id=?').bind(r1.sent ? 'sent' : 'received', r1.sent ? now() : null, r1.detail, id).run();
    await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)').bind(now(), 'buyer', 'public', 'enquiry', g.artist.id, JSON.stringify({ ref, work: work ? work.id : null, mail: r1.detail })).run();
    return reply(env, origin, 200, { ok: true, reference: ref });
  },
};
