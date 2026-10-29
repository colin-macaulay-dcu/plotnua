/* PlotArt Studio · who is signing in (Phase 2, 29 Oct 2026).
   Cloudflare Access authenticates (one-time code to the person's email); this Worker AUTHORISES. Every request's
   Access token (Cf-Access-Jwt-Assertion header, or the CF_Authorization cookie) is verified here: RS256 signature
   against Access's published keys, audience, issuer and expiry. The email in a verified token is the only identity
   used; nothing the browser sends can choose an artist. Fail closed on any doubt. */
import { Bad } from './lib.js';

let JWKS = { at: 0, keys: null };
const b64u = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)), c => c.charCodeAt(0));
const json = u8 => JSON.parse(new TextDecoder().decode(u8));

async function keys(env) {
  if (env.ACCESS_JWKS_JSON) {
    // Local tests only: a test key set. Refused anywhere but the local environment.
    if (env.ENVIRONMENT !== 'local') throw new Bad('Studio configuration error', 500);
    return JSON.parse(env.ACCESS_JWKS_JSON).keys;
  }
  if (JWKS.keys && Date.now() - JWKS.at < 600_000) return JWKS.keys;
  const r = await fetch(`${env.ACCESS_TEAM_DOMAIN}/cdn-cgi/access/certs`);
  if (!r.ok) throw new Bad('Sign-in service unavailable', 503);
  JWKS = { at: Date.now(), keys: (await r.json()).keys };
  return JWKS.keys;
}

export async function verifyAccess(req, env) {
  if (!env.ACCESS_AUD || !env.ACCESS_TEAM_DOMAIN) throw new Bad('Studio configuration error', 500);
  const cookie = (req.headers.get('Cookie') || '').match(/(?:^|;\s*)CF_Authorization=([^;]+)/);
  const tok = req.headers.get('Cf-Access-Jwt-Assertion') || (cookie && cookie[1]);
  if (!tok) return null;
  const parts = tok.split('.');
  if (parts.length !== 3) return null;
  let head, body;
  try { head = json(b64u(parts[0])); body = json(b64u(parts[1])); } catch { return null; }
  if (head.alg !== 'RS256') return null;
  const jwk = (await keys(env)).find(k => k.kid === head.kid);
  if (!jwk) return null;
  const key = await crypto.subtle.importKey('jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
  const ok = await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, b64u(parts[2]), new TextEncoder().encode(parts[0] + '.' + parts[1]));
  if (!ok) return null;
  const aud = Array.isArray(body.aud) ? body.aud : [body.aud];
  const t = Math.floor(Date.now() / 1000);
  if (!aud.includes(env.ACCESS_AUD) || body.iss !== env.ACCESS_TEAM_DOMAIN || !(body.exp > t) || (body.nbf && body.nbf > t + 60)) return null;
  if (typeof body.email !== 'string' || !body.email.includes('@')) return null;
  return body.email.trim().toLowerCase();
}

/* Role: the founder (by configured email) or an invited/active artist. Suspended or unknown: no access. */
export async function who(req, env) {
  const email = await verifyAccess(req, env);
  if (!email) return { role: 'none' };
  const founders = String(env.FOUNDER_EMAILS || '').toLowerCase().split(',').map(s => s.trim()).filter(Boolean);
  if (founders.includes(email)) return { role: 'founder', email };
  const a = await env.DB.prepare('SELECT * FROM artists WHERE email = ?').bind(email).first();
  if (!a || !['invited', 'active'].includes(a.account_status)) return { role: 'none', email, reason: a ? a.account_status : 'unknown' };
  if (a.account_status === 'invited') {
    await env.DB.prepare("UPDATE artists SET account_status='active', updated_at=? WHERE id=?").bind(new Date().toISOString(), a.id).run();
    a.account_status = 'active';
  }
  return { role: 'artist', email, artist: a };
}
