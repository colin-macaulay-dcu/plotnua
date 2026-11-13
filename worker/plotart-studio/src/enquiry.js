/* PlotArt · buyer-to-artist enquiry relay (Phase 3, 29 Oct 2026). A SEPARATE public Worker ("plotart-enquiry") bound to
   the Studio's D1 database. NOT DEPLOYED.

   POST /v1/enquiry  from plotnua.ie artwork and gallery pages only (Origin checked; CORS for that origin only).
   It accepts an enquiry only for a PUBLISHED gallery (and, for a work, one that is live and available or reserved),
   records it with a reference, and emails it to the artist with Reply-To set to the buyer, so the artist answers the
   buyer directly: the founder is not an intermediary. The buyer gets a short receipt. Nothing is shown to the buyer
   about the artist's address. No IP address is stored; rate limits are per-isolate and per-day caps in D1. */
import { send } from './mailer.js';
import { foundingAt } from './founding.js';
import { hireEnquiry, hireListed } from './hire-enquiry.js';   // Art for Hire (Stage 3B-3): separate routes, switched off

const NOTICE = 'PA-ENQ-2026-10-29';
// Enquiry notice versions the relay accepts. The next version is accepted BEFORE any page shows it, so changing the notice
// on the website never interrupts enquiries (release step C2). NOTICE stays the version shown today.
const NOTICES = [NOTICE, 'PA-ENQ-2026-11'];   // (a Worker entry module may export only handlers)
const DAILY_PER_ARTIST = 40, DAILY_TOTAL = 300, BURST = 5, BURST_MS = 10 * 60_000;
const hits = new Map();
const now = () => new Date().toISOString();

function cors(env, origin) {
  const ok = origin && origin === env.ORIGIN;
  return { 'Access-Control-Allow-Origin': ok ? origin : 'null', 'Vary': 'Origin', 'Access-Control-Allow-Methods': 'POST',
    'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
}
const reply = (env, origin, status, body) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...cors(env, origin) } });

/* The closing line of the artist's enquiry email, in ONE place so the Gallery Artist Programme (Phase 2) changes it once.
   Open for Commissions (13 Nov 2026): a commission enquiry is about a NEW, bespoke work, so it never carries the
   founding-year sentence (whose "commission" means PlotArt's fee on a sale); every other enquiry is unchanged. */
// Gallery Artist Phase 2 (13 Nov 2026): a Gallery Artist (a row in artist_terms, migration 0012) is told that the
// enquiry is a PlotArt introduction under their Gallery Artist Agreement. Founding Artists' wording is unchanged.
const closingLine = (commission, gallery = false) => commission
  ? 'Any commission for new work is agreed directly between you and the client.'
  : gallery
    ? 'This enquiry is an introduction through PlotArt. If it leads to a sale, PlotArt’s commission applies as set out in your Gallery Artist Agreement. Any sale is agreed directly between you and the buyer, who pays you directly.'
    : 'PlotArt takes no commission on enquiries from your founding year. Any sale is agreed directly between you and the buyer.';
async function isGalleryArtist(env, artist) {
  if (artist.founding) return false;
  try { return !!(await env.DB.prepare("SELECT 1 AS x FROM artist_terms WHERE artist_id = ? AND track = 'gallery_artist'").bind(artist.id).first()); }
  catch { return false; } // 0012 not run: no Gallery Artists exist
}

async function live(env, slug) {
  const a = await env.DB.prepare("SELECT * FROM artists WHERE slug = ? AND account_status IN ('invited','active')").bind(slug).first();
  if (!a) return null;
  const q = await env.DB.prepare("SELECT version FROM publish_queue WHERE artist_id = ? AND status = 'published' ORDER BY version DESC LIMIT 1").bind(a.id).first();
  if (!q) return null;
  const v = await env.DB.prepare('SELECT snapshot FROM versions WHERE artist_id = ? AND version = ?').bind(a.id, q.version).first();
  const snap = JSON.parse(v.snapshot);
  return snap.works.length ? { artist: a, snap } : null;
}

/* The Borrowed Garden noticeboard · enquiry relay (MVP, founder decision 4 Nov 2026). PREPARED, NOT SWITCHED ON.
   POST /v1/garden-enquiry answers 503 unless GARDEN_ENQUIRIES_ENABLED is "true", which it is not anywhere: the founder
   has not activated contact between participants (and introductions stay blocked pending the insurance question).
   When switched on: it accepts an enquiry only for an approved, unexpired listing, e-mails it to the listing's private
   contact address with Reply-To set to the sender (so the two people talk directly and neither address is published),
   sends the sender a receipt, and stores only a reference, the listing and the time. No automatic matching. */
const G_DAILY_PER_LISTING = 10, G_DAILY_TOTAL = 200;
async function gardenEnquiry(req, env, origin) {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env, origin) });
  if (req.method !== 'POST') return reply(env, origin, 405, { ok: false });
  if (origin !== env.ORIGIN) return reply(env, origin, 403, { ok: false, error: 'Refused' });
  if (env.GARDEN_ENQUIRIES_ENABLED !== 'true') return reply(env, origin, 503, { ok: false, error: 'Contact through the noticeboard isn’t open yet. Please email hello@plotnua.ie.' });
  const ip = req.headers.get('CF-Connecting-IP') || 'local', t = Date.now();
  const h = (hits.get(ip) || []).filter(x => t - x < BURST_MS);
  if (h.length >= BURST) return reply(env, origin, 429, { ok: false, error: 'Too many messages just now. Please try again later.' });
  hits.set(ip, [...h, t]);
  const raw = await req.text();
  if (raw.length > 4000) return reply(env, origin, 413, { ok: false, error: 'That message is too long.' });
  let b; try { b = JSON.parse(raw); } catch { return reply(env, origin, 400, { ok: false, error: 'Refused' }); }
  const keys = ['ref', 'email', 'message', 'website'];
  if (!b || typeof b !== 'object' || Object.keys(b).some(k => !keys.includes(k))) return reply(env, origin, 400, { ok: false, error: 'Refused' });
  if (b.website) return reply(env, origin, 200, { ok: true, reference: 'PN-GE-000000-0000' });       // honeypot
  const email = String(b.email || '').trim(), message = String(b.message || '').trim();
  if (!/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(email) || email.length > 254) return reply(env, origin, 400, { ok: false, error: 'Please check your email address.' });
  if (message.length < 10 || message.length > 1200) return reply(env, origin, 400, { ok: false, error: 'Please write a message of 10 to 1,200 characters.' });
  if (!/^PN-G-\d{6}-[0-9A-F]{4}$/.test(String(b.ref || ''))) return reply(env, origin, 400, { ok: false, error: 'Refused' });
  const l = await env.DB.prepare("SELECT id, ref, contact_email, area, county FROM garden_listings WHERE ref = ? AND status = 'approved' AND expires_at > ?").bind(b.ref, now()).first();
  if (!l) return reply(env, origin, 404, { ok: false, error: 'This listing isn’t on the noticeboard any more.' });
  const day = now().slice(0, 10);
  const per = await env.DB.prepare('SELECT n FROM garden_enquiry_days WHERE day = ? AND listing_id = ?').bind(day, l.id).first();
  const tot = await env.DB.prepare('SELECT COALESCE(SUM(n),0) AS n FROM garden_enquiry_days WHERE day = ?').bind(day).first();
  if ((per && per.n >= G_DAILY_PER_LISTING) || tot.n >= G_DAILY_TOTAL) return reply(env, origin, 429, { ok: false, error: 'This listing has had a lot of messages today. Please try again tomorrow.' });
  const ref = `PN-GE-${day.slice(2).replace(/-/g, '')}-${[...crypto.getRandomValues(new Uint8Array(2))].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
  await env.DB.batch([
    env.DB.prepare('INSERT INTO garden_enquiries (id, ref, listing_id, created_at) VALUES (?,?,?,?)').bind('q' + crypto.randomUUID().replace(/-/g, '').slice(0, 16), ref, l.id, now()),
    env.DB.prepare('INSERT INTO garden_enquiry_days (day, listing_id, n) VALUES (?, ?, 1) ON CONFLICT(day, listing_id) DO UPDATE SET n = n + 1').bind(day, l.id),
  ]);
  await send(env, { to: l.contact_email, replyTo: email, subject: `The Borrowed Garden · a reply to your listing ${l.ref}`,
    text: `Hello,\n\nSomeone has replied to your listing on The Borrowed Garden noticeboard (${l.area}, Co. ${l.county}, ${l.ref}).\n\n"${message}"\n\n` +
      `Reply to this email to answer them directly. Your reply will show your own e-mail address to them; nothing has been shared yet.\n` +
      `You decide whether to reply. Please read PlotNua's guidance before agreeing anything: https://plotnua.ie/discovery-the-borrowed-garden.html#bg-agree\n\nReference: ${ref}\n\nPlotNua` });
  await send(env, { to: email, replyTo: env.REPLY_TO || 'hello@plotnua.ie', subject: `Your message about listing ${l.ref}`,
    text: `Thank you. Your message has been passed on. The person who posted the listing decides whether to reply, and will reply by e-mail if they do.\n\nReference: ${ref}\n\nPlotNua` });
  return reply(env, origin, 200, { ok: true, reference: ref });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), origin = req.headers.get('Origin');
    if (url.pathname === '/v1/garden-enquiry') return gardenEnquiry(req, env, origin);   // prepared, OFF (see below)
    if (url.pathname === '/v1/hire-enquiry') return hireEnquiry(req, env, origin);       // prepared, OFF (hire-enquiry.js)
    if (url.pathname === '/v1/hire-listed') return hireListed(req, env, origin);         // live listed-works check, fails closed
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
    const keys = ['ref', 'notice', 'name', 'email', 'message', 'website', 'kind'];
    if (!b || typeof b !== 'object' || Object.keys(b).some(k => !keys.includes(k))) return reply(env, origin, 400, { ok: false, error: 'Refused' });
    // Open for Commissions (13 Nov 2026): the only kind there is. Absent = an ordinary enquiry, exactly as before.
    if ('kind' in b && b.kind !== 'commission') return reply(env, origin, 400, { ok: false, error: 'Refused' });
    const commission = b.kind === 'commission';
    if (b.website) return reply(env, origin, 200, { ok: true, reference: 'PA-E-000000-0000' });       // honeypot: silently dropped
    if (!NOTICES.includes(b.notice)) return reply(env, origin, 400, { ok: false, error: 'Please reload the page and try again.' });
    const name = String(b.name || '').trim(), email = String(b.email || '').trim(), message = String(b.message || '').trim();
    if (name.length < 1 || name.length > 80 || /[<>]/.test(name)) return reply(env, origin, 400, { ok: false, error: 'Please check your name.' });
    if (!/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(email) || email.length > 254) return reply(env, origin, 400, { ok: false, error: 'Please check your email address.' });
    if (message.length < 10 || message.length > 1500) return reply(env, origin, 400, { ok: false, error: 'Please write a message of 10 to 1,500 characters.' });
    const m = /^PA-([a-z0-9]+(?:-[a-z0-9]+){0,6}?)(?:-(w[0-9a-z]{2,24}))?$/.exec(String(b.ref || ''));
    if (!m) return reply(env, origin, 400, { ok: false, error: 'Refused' });
    const g = await live(env, m[1]);
    if (!g) return reply(env, origin, 404, { ok: false, error: 'This gallery isn’t taking enquiries. Please email hello@plotnua.ie.' });
    let work = null;
    if (commission) {
      // about the artist, never a particular artwork; and only while their PUBLISHED gallery says they are open for it
      if (m[2]) return reply(env, origin, 400, { ok: false, error: 'Refused' });
      if (!(g.snap.artist && g.snap.artist.open_for_commissions === true))
        return reply(env, origin, 409, { ok: false, error: 'This artist isn’t taking commission enquiries at the moment. You can still ask about their work.' });
    }
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
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).bind(id, ref, g.artist.id, work ? work.id : null, work ? work.title : null, name, email, message, b.notice, now(), 'received', del).run();
    // Enquiry log (Founding Artist Agreement 5.4; migration 0005): reference, artist, artwork, time and founding status, with
    // NO buyer details. Kept for the agreement's life plus six years; the row above is still deleted at 24 months. If the log
    // isn't installed yet the enquiry goes ahead exactly as before and the audit says so.
    let logged = 'logged';
    try {
      const f = foundingAt(g.artist, now());
      if (commission) await env.DB.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry, note)
        VALUES (?,?,?,?,?,?,?,?,?,?,0,?)`).bind('l' + id.slice(1), ref, g.artist.id, null, 'relay', now(), f.founding, f.year_end, 'relay', now(), 'commission enquiry').run();
      else await env.DB.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry)
        VALUES (?,?,?,?,?,?,?,?,?,?,0)`).bind('l' + id.slice(1), ref, g.artist.id, work ? work.id : null, 'relay', now(), f.founding, f.year_end, 'relay', now()).run();
    } catch (e) { logged = 'not logged: ' + String(e.message || e).slice(0, 80); }
    const about = work ? `“${work.title}”` : 'your work';
    const r1 = await send(env, { to: g.artist.email, replyTo: email,
      subject: commission ? `PlotArt commission enquiry · ${ref}` : `PlotArt enquiry about ${work ? work.title : 'your work'} · ${ref}`,
      text: `Hello ${g.artist.display_name.split(' ')[0]},\n\n` +
        (commission ? `${name} has asked through your PlotArt gallery about commissioning a new work from you.\n\n`
          : `${name} has sent an enquiry about ${about} through your PlotArt gallery.\n\n`) +
        `"${message}"\n\nReply to this email to answer ${name} directly (your reply goes to ${email}).\n\n` +
        `Reference: ${ref}${work ? `\nArtwork: https://plotnua.ie/plotart/artists/${g.artist.slug}/${work.slug}.html` : ''}\n\n` +
        `${closingLine(commission, !commission && await isGalleryArtist(env, g.artist))}\n\nPlotArt · part of PlotNua` });
    await send(env, { to: email, replyTo: env.REPLY_TO || 'hello@plotnua.ie', subject: commission ? `Your PlotArt commission enquiry · ${ref}` : `Your PlotArt enquiry · ${ref}`,
      text: `Hello ${name},\n\nThank you. Your enquiry about ${commission ? `a commission from ${g.artist.display_name}` : work ? `“${work.title}”` : `work by ${g.artist.display_name}`} has been passed to ${g.artist.display_name}, who will reply to you by email.\n\n` +
        `Reference: ${ref}\n\nHow we handle enquiries: https://plotnua.ie/privacy.html#plotart-enquiries\n\nPlotArt · part of PlotNua` });
    await env.DB.prepare('UPDATE enquiries SET status=?, sent_at=?, detail=? WHERE id=?').bind(r1.sent ? 'sent' : 'received', r1.sent ? now() : null, r1.detail, id).run();
    await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)').bind(now(), 'buyer', 'public', 'enquiry', g.artist.id, JSON.stringify({ ref, work: work ? work.id : null, ...(commission ? { kind: 'commission' } : {}), mail: r1.detail, log: logged })).run();
    return reply(env, origin, 200, { ok: true, reference: ref });
  },
};
