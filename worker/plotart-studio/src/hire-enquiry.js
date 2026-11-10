/* PlotArt · Art for Hire enquiry relay (Stage 3B-3, development 10 Nov 2026). NOT DEPLOYED. PREPARED, SWITCHED OFF.
   Served by the existing enquiry Worker (enquiry.js) on two NEW paths; /v1/enquiry and /v1/garden-enquiry are untouched.

   POST /v1/hire-enquiry  A business asks to hire one listed work. Refused (503) unless HIRE_ENQUIRIES_ENABLED and
                          HIRE_TERMS_ENABLED are both "true". The work must be listed for hire AT THIS MOMENT, checked
                          live in D1 with the same rules as the Studio (hire-rules.js): a withdrawn, sold, unavailable,
                          unapproved or non-consenting work is refused. Recorded in `enquiries` (reference PA-H-…),
                          `enquiry_log` and `hire_enquiries`; e-mailed to the artist with Reply-To set to the hirer.
                          The artist's address is never shown to the hirer.
   GET  /v1/hire-listed   The IDs (and hire availability) of works listed right now. No personal data. The hire page shows
                          a work as available only while this answers and names it; on any failure it shows none. */
import { send } from './mailer.js';
import { foundingAt } from './founding.js';
import { listedFor } from './hire-rules.js';

export const HIRE_NOTICE = 'PA-ENQ-HIRE-2026-11';
const NOTICES = [HIRE_NOTICE];
const HONEYPOT = 'fax_number';            // NOT "website": the purchase and garden routes use that name
const KEYS = ['ref', 'notice', 'privacy', 'name', 'email', 'business', 'role', 'business_url', 'project_type', 'intended_use',
  'date_from', 'date_to', 'use_place', 'territory', 'message', HONEYPOT];
const PROJECT = { film_tv: 'Film or television', advertising: 'Advertising', photography: 'Photography', staging: 'Property or event staging', interiors: 'Interiors or office', other: 'Other' };
const USE = { display_staging: 'Display or staging (not filmed)', photography: 'Photography', filming: 'Filming', other: 'Other' };
const TERRITORY = { ie: 'Republic of Ireland', ni: 'Northern Ireland', gb: 'Great Britain', other: 'Elsewhere' };
const DAILY_PER_ARTIST = 40, DAILY_TOTAL = 300, HIRE_DAILY_PER_WORK = 10, HIRE_DAILY_TOTAL = 100, BURST = 5, BURST_MS = 10 * 60_000;
const hits = new Map();
const now = () => new Date().toISOString();

/* The statements every hirer sees before sending (and in the receipt), and every artist sees with the enquiry. */
export const EXPLAIN = [
  'PlotArt only introduces you to the artist. It is not a party to any hire and takes no payment.',
  'The hire fee (rental price) is agreed directly between you and the artist.',
  'Insurance, transport, installation and return are agreed between you and the artist.',
  'Screen and photo use is never included in a hire and is never granted automatically. Any permission must be agreed in writing with the artist.',
  'Film and television screen-use arrangements cannot be made through PlotArt until its legal review is complete.',
];

function cors(env, origin, methods) {
  const ok = origin && origin === env.ORIGIN;
  return { 'Access-Control-Allow-Origin': ok ? origin : 'null', 'Vary': 'Origin', 'Access-Control-Allow-Methods': methods,
    'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600', 'X-Content-Type-Options': 'nosniff' };
}
const reply = (env, origin, status, body, extra = {}) => new Response(JSON.stringify(body), { status,
  headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...cors(env, origin, 'POST'), ...extra } });

/* Two switches (Stage 3B-4): HIRE_TERMS_ENABLED lists works (the page may show them); HIRE_ENQUIRIES_ENABLED additionally
   opens enquiries, so the gallery can be shown while the enquiry form stays closed pending legal and privacy approval. */
export const listing = env => env.HIRE_TERMS_ENABLED === 'true';
export const open = env => env.HIRE_ENQUIRIES_ENABLED === 'true' && listing(env);
async function listed(env, opts = {}) {
  if (!listing(env)) return [];
  const t = await env.DB.prepare('SELECT doc_id FROM hire_terms WHERE effective_at <= ? ORDER BY effective_at DESC LIMIT 1').bind(now()).first();
  return t ? listedFor(env, { docId: t.doc_id, ...opts }) : [];
}

/* GET /v1/hire-listed: fails CLOSED. Any error answers 503 and the page must then show nothing as available. */
export async function hireListed(req, env, origin) {
  const h = { ...cors(env, origin, 'GET'), 'Content-Type': 'application/json' };
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
  if (req.method !== 'GET') return new Response(JSON.stringify({ ok: false }), { status: 405, headers: { ...h, 'Cache-Control': 'no-store' } });
  try {
    const items = (await listed(env)).map(r => ({ id: r.artwork_id, availability: r.hire.availability, available_from: r.hire.available_from }));
    const at = Date.now();
    return new Response(JSON.stringify({ ok: true, open: listing(env), enquiries: open(env), generated_at: new Date(at).toISOString(), valid_until: new Date(at + 120_000).toISOString(), items }),
      { status: 200, headers: { ...h, 'Cache-Control': 'public, max-age=30' } });
  } catch {
    return new Response(JSON.stringify({ ok: false, error: 'unavailable' }), { status: 503, headers: { ...h, 'Cache-Control': 'no-store' } });
  }
}

const bad = (env, origin, error, status = 400) => reply(env, origin, status, { ok: false, error });
const ymd = s => /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(Date.parse(s + 'T12:00:00Z')) && new Date(s + 'T12:00:00Z').toISOString().slice(0, 10) === s;
const dublinToday = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Dublin' }).format(new Date());

export async function hireEnquiry(req, env, origin) {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env, origin, 'POST') });
  if (req.method !== 'POST') return reply(env, origin, 405, { ok: false });
  if (origin !== env.ORIGIN) return bad(env, origin, 'Refused', 403);
  if (!open(env)) return bad(env, origin, 'Hire enquiries aren’t open yet. Please email hello@plotnua.ie.', 503);
  const ip = req.headers.get('CF-Connecting-IP') || 'local', t = Date.now();
  const hh = (hits.get(ip) || []).filter(x => t - x < BURST_MS);
  if (hh.length >= BURST) return bad(env, origin, 'Too many enquiries just now. Please try again later.', 429);
  hits.set(ip, [...hh, t]);
  const raw = await req.text();
  if (raw.length > 8000) return bad(env, origin, 'That message is too long.', 413);
  let b; try { b = JSON.parse(raw); } catch { return bad(env, origin, 'Refused'); }
  if (!b || typeof b !== 'object' || Array.isArray(b) || Object.keys(b).some(k => !KEYS.includes(k))) return bad(env, origin, 'Refused');
  if (b[HONEYPOT]) return reply(env, origin, 200, { ok: true, reference: 'PA-H-000000-000000' });       // honeypot: silently dropped
  if (!NOTICES.includes(b.notice)) return bad(env, origin, 'Please reload the page and try again.');
  if (b.privacy !== true) return bad(env, origin, 'Please confirm you have read how PlotArt handles hire enquiries.');
  const s = k => typeof b[k] === 'string' ? b[k].trim() : '';
  const name = s('name'), email = s('email'), business = s('business'), role = s('role'), url = s('business_url'), place = s('use_place'), message = s('message');
  if (name.length < 1 || name.length > 80 || /[<>]/.test(name)) return bad(env, origin, 'Please check your name.');
  if (!/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(email) || email.length > 254) return bad(env, origin, 'Please check your email address.');
  if (business.length < 2 || business.length > 160 || /[<>]/.test(business)) return bad(env, origin, 'Please give your business or production name.');
  if (role.length < 2 || role.length > 80 || /[<>]/.test(role)) return bad(env, origin, 'Please give your role.');
  if (url && (url.length > 300 || !/^https?:\/\/[^\s<>"]+\.[^\s<>"]+$/i.test(url))) return bad(env, origin, 'Please check the website address, or leave it blank.');
  if (!(b.project_type in PROJECT)) return bad(env, origin, 'Please choose the type of project.');
  if (!(b.intended_use in USE)) return bad(env, origin, 'Please choose how the work would be used.');
  if (b.intended_use === 'filming' && env.HIRE_SCREEN_USE !== 'true')
    return bad(env, origin, 'Filming a work can’t be arranged through PlotArt yet: film and television screen-use arrangements wait for legal review. You can still ask about display or staging that is not filmed.', 422);
  const from = s('date_from'), to = s('date_to'), today = dublinToday();
  if (!ymd(from) || !ymd(to)) return bad(env, origin, 'Please give the dates you need the work (from and to).');
  if (from < today || to < from) return bad(env, origin, 'Please check the dates: they must be in the future and in order.');
  if (Date.parse(to) - Date.parse(today) > 730 * 86400_000 || Date.parse(to) - Date.parse(from) > 365 * 86400_000) return bad(env, origin, 'Please check the dates: up to a year’s hire, within the next two years.');
  if (place.length < 2 || place.length > 40 || /[<>]/.test(place)) return bad(env, origin, 'Please give the town or county where the work would be used.');
  if (!(b.territory in TERRITORY)) return bad(env, origin, 'Please choose where the project is.');
  if (message.length > 1500) return bad(env, origin, 'Please keep the message to 1,500 characters.');
  const m = /^PA-([a-z0-9]+(?:-[a-z0-9]+){0,6}?)-(w[0-9a-z]{2,24})$/.exec(String(b.ref || ''));
  if (!m) return bad(env, origin, 'Refused');

  // the live check: the same rules as the Studio, at this moment, for this artist's work
  let hit;
  try { hit = (await listed(env, { artworkId: m[2] })).find(r => r.artist_slug === m[1]); }
  catch { return bad(env, origin, 'Hire enquiries are unavailable just now. Please try again later.', 503); }
  if (!hit) return bad(env, origin, 'This work isn’t available for hire at the moment.', 409);

  const day = now().slice(0, 10);
  const q = (sql, ...v) => env.DB.prepare(sql).bind(...v).first();
  const perArtist = await q('SELECT COUNT(*) AS n FROM enquiries WHERE artist_id = ? AND created_at >= ?', hit.artist_id, day);
  const total = await q('SELECT COUNT(*) AS n FROM enquiries WHERE created_at >= ?', day);
  const hireWork = await q("SELECT COUNT(*) AS n FROM enquiries WHERE artwork_id = ? AND reference LIKE 'PA-H-%' AND created_at >= ?", hit.artwork_id, day);
  const hireAll = await q("SELECT COUNT(*) AS n FROM enquiries WHERE reference LIKE 'PA-H-%' AND created_at >= ?", day);
  if (perArtist.n >= DAILY_PER_ARTIST || total.n >= DAILY_TOTAL || hireWork.n >= HIRE_DAILY_PER_WORK || hireAll.n >= HIRE_DAILY_TOTAL)
    return bad(env, origin, 'We’re receiving a lot of enquiries. Please try again tomorrow or email hello@plotnua.ie.', 429);

  const ref = `PA-H-${day.slice(2).replace(/-/g, '')}-${[...crypto.getRandomValues(new Uint8Array(3))].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
  const id = 'e' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
  const at = now(), del = new Date(Date.now() + 730 * 86400_000).toISOString();
  const title = hit.private.title, artist = hit.private;
  const summary = `Hire enquiry. Project: ${PROJECT[b.project_type]}. Use: ${USE[b.intended_use]}. Dates: ${from} to ${to}. Location: ${place} (${TERRITORY[b.territory]}).`;
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO enquiries (id, reference, artist_id, artwork_id, artwork_title, buyer_name, buyer_email, message, notice_version, created_at, status, delete_after)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).bind(id, ref, hit.artist_id, hit.artwork_id, title, name, email, message ? `${summary}\n\n${message}` : summary, b.notice, at, 'received', del),
    env.DB.prepare(`INSERT INTO hire_enquiries (enquiry_id, business, role, business_url, phone, project_type, date_from, date_to, intended_use, use_county, territory_flag, delete_after, created_at)
      VALUES (?,?,?,?,NULL,?,?,?,?,?,?,?,?)`).bind(id, business, role, url || null, b.project_type, from, to, b.intended_use, place, b.territory, del, at),
  ]);
  // Enquiry log (Founding Artist Agreement 5.4): an introduction through the relay, logged like any other, with no hirer details.
  let logged = 'logged';
  try {
    const a = await q('SELECT * FROM artists WHERE id = ?', hit.artist_id), f = foundingAt(a, at);
    await env.DB.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry)
      VALUES (?,?,?,?,?,?,?,?,?,?,0)`).bind('l' + id.slice(1), ref, hit.artist_id, hit.artwork_id, 'relay', at, f.founding, f.year_end, 'relay', at).run();
  } catch (e) { logged = 'not logged: ' + String(e.message || e).slice(0, 80); }

  const outside = b.territory !== 'ie';
  const r1 = await send(env, { to: artist.artist_email, replyTo: email, subject: `PlotArt hire enquiry about ${title} · ${ref}`,
    text: `Hello ${artist.display_name.split(' ')[0]},\n\n${name} (${role}, ${business}) has asked about HIRING “${title}” through PlotArt Art for Hire. This is a hire enquiry, not a purchase.\n\n` +
      `Project: ${PROJECT[b.project_type]}\nIntended use: ${USE[b.intended_use]}\nDates: ${from} to ${to}\nLocation: ${place}, ${TERRITORY[b.territory]}${url ? `\nWebsite: ${url}` : ''}\n\n` +
      (message ? `"${message}"\n\n` : '') +
      (outside ? `Please note: this project is outside the Republic of Ireland, which the Art for Hire pilot covers. Take advice before agreeing to send the work abroad.\n\n` : '') +
      `Reply to this email to answer ${name} directly (your reply goes to ${email}). You decide whether to go ahead.\n\n` +
      `Remember:\n- ${EXPLAIN[0]}\n- The hire fee, insurance, transport and return are for you and the hirer to agree, in writing.\n` +
      `- Your screen and photo choices are only a willingness to discuss. Nothing has been licensed. Any permission must be agreed by you in writing.\n- ${EXPLAIN[4]}\n\n` +
      `Reference: ${ref}\nArtwork: https://plotnua.ie/plotart/artists/${hit.artist_slug}/${hit.work_slug}.html\n\nPlotArt · part of PlotNua` });
  await send(env, { to: email, replyTo: env.REPLY_TO || 'hello@plotnua.ie', subject: `Your PlotArt hire enquiry · ${ref}`,
    text: `Hello ${name},\n\nThank you. Your hire enquiry about “${title}” has been passed to ${artist.display_name}, who will reply to you by email if they can help.\n\n` +
      EXPLAIN.map(x => `- ${x}`).join('\n') + `\n\nReference: ${ref}\n\nHow we handle hire enquiries: https://plotnua.ie/privacy.html#plotart-hire-enquiries\n\nPlotArt · part of PlotNua` });
  await env.DB.prepare('UPDATE enquiries SET status=?, sent_at=?, detail=? WHERE id=?').bind(r1.sent ? 'sent' : 'received', r1.sent ? now() : null, r1.detail, id).run();
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)').bind(now(), 'hirer', 'public', 'hire_enquiry', hit.artist_id,
    JSON.stringify({ ref, work: hit.artwork_id, territory: b.territory, mail: r1.detail, log: logged })).run();
  return reply(env, origin, 200, { ok: true, reference: ref,
    message: `Thank you. Your enquiry has been passed to ${artist.display_name}, who will reply to you by email if they can help. We’ve sent you a copy with reference ${ref}.`,
    reminders: EXPLAIN });
}
