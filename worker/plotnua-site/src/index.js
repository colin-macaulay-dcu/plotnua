// PlotNua public site on plotnua.ie (prepared 27 Nov 2026, NOT in use: GitHub Pages serves plotnua.ie).
// Serves the exact files GitHub Pages publishes (atlas-tools/plotnua_site_build.py, fail-closed allowlist) with the
// same URL behaviour, from Workers Static Assets. Its own Worker, deploy, versions and rollback: independent of plotart.ie.
// Shared serving logic: worker/site-common/serve.js. No Content-Security-Policy yet (parity with GitHub Pages, which
// sends none); one is added with the shared consent work, after its own testing.
//
// PLOTART_ADDRESS = "plotart.ie" (only at the founder-approved cutover) answers /plotart and /plotart/<path> with an
// exact 301 to https://plotart.ie/<path>, query kept. Paths that merely begin with the same letters are never matched.
import { createSite } from '../../site-common/serve.js';

export function plotartMove(url, env) {
  if (env.PLOTART_ADDRESS !== 'plotart.ie') return null;
  const p = url.pathname;
  if (p !== '/plotart' && !p.startsWith('/plotart/')) return null;
  return 'https://plotart.ie' + (p.length > 8 ? p.slice(8) : '/') + url.search;
}

const site = createSite({ apex: 'plotnua.ie', redirect: plotartMove });
export const handle = site.handle;
export default { fetch: site.fetch };
