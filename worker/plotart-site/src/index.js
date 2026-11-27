// PlotArt public site on plotart.ie (domain migration R1, prepared 26 Nov 2026).
// Serves the static build of plotart/ (atlas-tools/plotart_site_build.py) from Workers Static Assets.
// It reproduces the GitHub Pages URL behaviour exactly, so every existing PlotArt address maps one-to-one:
//   /gallery/        -> gallery/index.html            /gallery   -> 301 /gallery/   (directories)
//   /about.html      -> about.html                    /about     -> about.html      (Pages serves it, no redirect)
//   anything else    -> 404.html with status 404
// www.plotart.ie and any other host 301 to https://plotart.ie (path and query kept).
// INDEXING = "noindex" (testing) adds X-Robots-Tag: noindex to every response; "index" (after cutover) does not.
// Nothing here reads cookies, stores data or calls another service.

const APEX = 'plotart.ie';

// Consent (founder instruction 26 Nov 2026): no non-essential tracking until an approved consent solution exists.
// With ANALYTICS = "off", scripts may come only from plotart.ie itself and pages may talk only to PlotArt's own Workers,
// so no analytics, advertising or consent-platform script can run here, even if one were added to a page by mistake.
const CSP_PARTS = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self'",                                        // fonts are self-hosted (27 Nov 2026)
  "img-src 'self' data: https:",
  "connect-src 'self' https://plotart-enquiry.colin-a41.workers.dev https://plotart-checkout.colin-a41.workers.dev https://plotnua-art-space-register.colin-a41.workers.dev https://plotart-studio.colin-a41.workers.dev",
  "form-action 'self' https://plotart-checkout.colin-a41.workers.dev https://plotart-studio.colin-a41.workers.dev",
  "frame-src 'none'", "object-src 'none'", "base-uri 'self'", "frame-ancestors 'self'",
];
// ANALYTICS = "consent" (together with site.json, only after founder approval): the Google Analytics hosts are added so
// the self-hosted consent module can load GA4 AFTER a visitor accepts analytics. Nothing else is opened.
const GA = ['https://www.googletagmanager.com', 'https://*.google-analytics.com', 'https://*.analytics.google.com'];
const csp = env => (env.ANALYTICS === 'consent'
  ? CSP_PARTS.map(p => p.startsWith('script-src') ? `${p} ${GA[0]}` : p.startsWith('connect-src') ? `${p} ${GA.join(' ')}` : p)
  : CSP_PARTS).join('; ');

const SECURITY = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Strict-Transport-Security': 'max-age=31536000',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'X-Frame-Options': 'SAMEORIGIN',
};

const hasExt = path => /\.[a-z0-9]+$/i.test(path.split('/').pop());

async function asset(env, url, path) {
  const u = new URL(url);
  u.pathname = path;
  u.search = '';
  const r = await env.ASSETS.fetch(new Request(u.toString(), { method: 'GET' }));
  return r.status === 200 ? r : null;
}

function finish(env, response, extra = {}) {
  const r = new Response(response.body, response);
  for (const [k, v] of Object.entries(SECURITY)) r.headers.set(k, v);
  r.headers.set('Content-Security-Policy', csp(env));
  for (const [k, v] of Object.entries(extra)) r.headers.set(k, v);
  // only https://plotart.ie itself may ever be indexed: the workers.dev test address is always noindex
  if ((env.INDEXING || 'noindex') !== 'index' || (env.HOST && env.HOST !== APEX)) r.headers.set('X-Robots-Tag', 'noindex, nofollow');
  return r;
}

const redirect = (env, location) => finish(env, new Response(null, { status: 301, headers: { Location: location } }));

export async function handle(request, env0) {
  const url = new URL(request.url);
  const env = { ...env0, HOST: url.hostname };
  const local = url.hostname === 'localhost' || url.hostname === '127.0.0.1' || url.hostname.endsWith('.workers.dev');
  if (!local && url.hostname !== APEX) return redirect(env, `https://${APEX}${url.pathname}${url.search}`);
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    return finish(env, new Response('Method not allowed', { status: 405, headers: { Allow: 'GET, HEAD' } }));
  }
  let path;
  try { path = decodeURIComponent(url.pathname); } catch { path = null; }
  if (path === null || path.includes('\0') || path.split('/').includes('..')) {
    return notFound(env, request.url);
  }
  let found = null;
  if (path.endsWith('/')) {
    found = await asset(env, request.url, url.pathname + 'index.html');
  } else if (hasExt(path)) {
    found = await asset(env, request.url, url.pathname);
  } else {
    if (await asset(env, request.url, url.pathname + '/index.html')) {
      return redirect(env, `${url.origin}${url.pathname}/${url.search}`);
    }
    found = await asset(env, request.url, url.pathname + '.html');
  }
  if (!found) return notFound(env, request.url);
  const body = request.method === 'HEAD' ? null : found.body;
  return finish(env, new Response(body, found));
}

async function notFound(env, url) {
  const page = await asset(env, url, '/404.html');
  return finish(env, new Response(page ? page.body : 'Not found', {
    status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8' },
  }));
}

export default { fetch: (request, env) => handle(request, env) };
