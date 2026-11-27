/* PlotArt · commercial inbound routes on the enquiry Worker (migration 0031; founder approval in principle 27 Nov 2026).
   NOT DEPLOYED. Both write to the Studio's commercial records (commercial.js); neither sends anything to an artist.

   POST /v1/lead-capture     Gmail capture. Called only by the founder's Apps Script (integrations/gmail-leads.gs) with
                             "Authorization: Bearer <LEAD_CAPTURE_TOKEN>" (a Worker secret). No browser origin; no CORS.
                             Refused (503) unless LEAD_CAPTURE_ENABLED is "true". Records each message once.
   POST /v1/business-enquiry The Art for Hire "Request a selection" form (Phase 2). From the PlotArt website only (Origin
                             checked); refused (503) unless BUSINESS_ENQUIRIES_ENABLED is "true". Creates a lead
                             (source: website form) and, once a mailer is approved, tells hello@ that it arrived. */
import * as CM from './commercial.js';
import { send } from './mailer.js';
import { Bad } from './lib.js';

export const BUSINESS_NOTICE = 'PA-ENQ-BUSINESS-2026-12';
const KEYS = ['notice', 'name', 'email', 'business', 'role', 'phone', 'location', 'interest', 'message', 'fax_number'];
const hits = new Map(), BURST = 4, BURST_MS = 10 * 60_000;
const j = (status, body, headers = {}) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', ...headers } });

async function safeEqual(a, b) {   // constant-time comparison of the bearer token
  const enc = new TextEncoder(), [x, y] = await Promise.all([a, b].map(s => crypto.subtle.digest('SHA-256', enc.encode(String(s)))));
  const u = new Uint8Array(x), v = new Uint8Array(y); let d = 0; for (let i = 0; i < u.length; i++) d |= u[i] ^ v[i]; return d === 0;
}

export async function leadCapture(req, env) {
  if (req.method !== 'POST') return j(405, { ok: false });
  if (env.LEAD_CAPTURE_ENABLED !== 'true' || !env.LEAD_CAPTURE_TOKEN) return j(503, { ok: false, error: 'Lead capture is not switched on' });
  const auth = req.headers.get('Authorization') || '';
  if (!(await safeEqual(auth, `Bearer ${env.LEAD_CAPTURE_TOKEN}`))) return j(401, { ok: false });
  const raw = await req.text();
  if (raw.length > 600_000) return j(413, { ok: false, error: 'Too large' });
  let b; try { b = JSON.parse(raw); } catch { return j(400, { ok: false, error: 'Not JSON' }); }
  try { return j(200, { ok: true, ...(await CM.captureGmail(env, b && b.messages)) }); }
  catch (e) { return j(e instanceof Bad ? e.status : 500, { ok: false, error: e instanceof Bad ? e.message : 'Failed' }); }
}

export async function businessEnquiry(req, env, origin, { allowed, cors }) {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env, origin) });
  const reply = (s, body) => j(s, body, cors(env, origin));
  if (req.method !== 'POST') return reply(405, { ok: false });
  if (!allowed(env, origin)) return reply(403, { ok: false, error: 'Refused' });
  if (env.BUSINESS_ENQUIRIES_ENABLED !== 'true') return reply(503, { ok: false, error: 'Please email hello@plotnua.ie.' });
  const ip = req.headers.get('CF-Connecting-IP') || 'local', t = Date.now(), h = (hits.get(ip) || []).filter(x => t - x < BURST_MS);
  if (h.length >= BURST) return reply(429, { ok: false, error: 'Too many requests just now. Please try again later.' });
  hits.set(ip, [...h, t]);
  const raw = await req.text();
  if (raw.length > 6000) return reply(413, { ok: false, error: 'That message is too long.' });
  let b; try { b = JSON.parse(raw); } catch { return reply(400, { ok: false, error: 'Refused' }); }
  if (!b || typeof b !== 'object' || Object.keys(b).some(k => !KEYS.includes(k))) return reply(400, { ok: false, error: 'Refused' });
  if (b.fax_number) return reply(200, { ok: true, reference: 'PA-CL-000000-000000' });   // honeypot: silently dropped
  if (b.notice !== BUSINESS_NOTICE) return reply(400, { ok: false, error: 'Please reload the page and try again.' });
  if (!b.email) return reply(400, { ok: false, error: 'Please give your email address.' });
  try {
    const c = await CM.websiteEnquiry(env, b);
    await send(env, { to: env.REPLY_TO || 'hello@plotnua.ie', subject: `Art for Hire request: ${String(b.business).slice(0, 80)} (${c.reference})`,
      text: `A new request from the Art for Hire page is in Studio → Commercial (${c.reference}).`, idempotencyKey: c.reference }).catch(() => null);
    return reply(200, { ok: true, reference: c.reference });
  } catch (e) { return reply(e instanceof Bad ? 400 : 500, { ok: false, error: e instanceof Bad ? e.message : 'Something went wrong. Please email hello@plotnua.ie.' }); }
}
