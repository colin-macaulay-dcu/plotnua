// Shared static-site core for PlotNua's public Workers (prepared 27 Nov 2026). Imported by two independently deployed
// Workers, worker/plotart-site (plotart.ie) and worker/plotnua-site (plotnua.ie): one maintained codebase, two separate
// Workers, deploys, versions and rollbacks, so neither website's deployment can replace or break the other's.
//
// It reproduces the GitHub Pages URL behaviour exactly, so every existing address maps one-to-one:
//   /dir/  -> dir/index.html     /dir -> 301 /dir/     /page -> page.html (served, no redirect)     else 404.html (404)
// Every other host (www, anything) 301s to the apex with path and query kept. workers.dev / localhost are test addresses
// and are ALWAYS noindex. INDEXING = "index" lets the apex be indexed; anything else adds X-Robots-Tag: noindex.
// site.redirect(url, env) may return an absolute URL for a permanent 301 before any file lookup (the PlotArt move).
// Nothing here reads cookies, stores data or calls another service.

export const SECURITY = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Strict-Transport-Security': 'max-age=31536000',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'X-Frame-Options': 'SAMEORIGIN',
};

const hasExt = path => /\.[a-z0-9]+$/i.test(path.split('/').pop());

export function createSite(site) {
  const { apex, csp = () => null } = site;

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
    const policy = csp(env);
    if (policy) r.headers.set('Content-Security-Policy', policy);
    for (const [k, v] of Object.entries(extra)) r.headers.set(k, v);
    if (site.cacheControl && !extra['Cache-Control']) r.headers.set('Cache-Control', site.cacheControl);
    // parity with GitHub Pages: text types carry charset=utf-8 (Workers assets send e.g. plain "text/html")
    const ct = r.headers.get('Content-Type') || '';
    if (/^(text\/(html|css|plain|javascript)|application\/(json|javascript))$/.test(ct)) r.headers.set('Content-Type', ct + '; charset=utf-8');
    if ((env.INDEXING || 'noindex') !== 'index' || (env.HOST && env.HOST !== apex)) r.headers.set('X-Robots-Tag', 'noindex, nofollow');
    return r;
  }

  const redirect = (env, location) => finish(env, new Response(null, { status: 301, headers: { Location: location } }));

  async function notFound(env, url) {
    const page = await asset(env, url, '/404.html');
    return finish(env, new Response(page ? page.body : 'Not found', {
      status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8' },
    }));
  }

  async function handle(request, env0) {
    const url = new URL(request.url);
    const env = { ...env0, HOST: url.hostname };
    const local = url.hostname === 'localhost' || url.hostname === '127.0.0.1' || url.hostname.endsWith('.workers.dev');
    if (!local && url.hostname !== apex) return redirect(env, `https://${apex}${url.pathname}${url.search}`);
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      return finish(env, new Response('Method not allowed', { status: 405, headers: { Allow: 'GET, HEAD' } }));
    }
    // Any address other than the live apex (workers.dev, local tests) tells every crawler to stay away entirely. Files that
    // bypass the Worker (static assets) carry no noindex header, so this robots.txt is what keeps the whole copy out of search.
    if (url.pathname === '/robots.txt' && (url.hostname !== apex || (env.INDEXING || 'noindex') !== 'index')) {
      return finish(env, new Response(request.method === 'HEAD' ? null : 'User-agent: *\nDisallow: /\n', { headers: { 'Content-Type': 'text/plain' } }));
    }
    const moved = site.redirect ? site.redirect(url, env) : null;
    if (moved) return redirect(env, moved);
    let path;
    try { path = decodeURIComponent(url.pathname); } catch { path = null; }
    if (path === null || path.includes('\0') || path.split('/').includes('..')) return notFound(env, request.url);
    let found = null;
    if (path.endsWith('/')) {
      found = await asset(env, request.url, url.pathname + 'index.html');
    } else if (hasExt(path)) {
      found = await asset(env, request.url, url.pathname);
    } else if ((found = await asset(env, request.url, url.pathname))) {
      // an extensionless file served as itself (e.g. /CNAME), as GitHub Pages does
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

  return { handle, fetch: (request, env) => handle(request, env) };
}
