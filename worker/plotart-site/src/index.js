// PlotArt public site on plotart.ie (domain migration R1, prepared 26 Nov 2026).
// Serves the static build of plotart/ (atlas-tools/plotart_site_build.py) from Workers Static Assets.
// It reproduces the GitHub Pages URL behaviour exactly, so every existing PlotArt address maps one-to-one:
//   /gallery/        -> gallery/index.html            /gallery   -> 301 /gallery/   (directories)
//   /about.html      -> about.html                    /about     -> about.html      (Pages serves it, no redirect)
//   anything else    -> 404.html with status 404
// www.plotart.ie and any other host 301 to https://plotart.ie (path and query kept).
// INDEXING = "noindex" (testing) adds X-Robots-Tag: noindex to every response; "index" (after cutover) does not.
// The serving logic is shared with plotnua.ie (worker/site-common/serve.js); this file holds only what is PlotArt's.
// Nothing here reads cookies, stores data or calls another service.

import { createSite } from '../../site-common/serve.js';

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

const site = createSite({ apex: 'plotart.ie', csp });
export const handle = site.handle;
export default { fetch: site.fetch };
