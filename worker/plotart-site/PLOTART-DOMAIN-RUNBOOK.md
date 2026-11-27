# PlotArt on plotart.ie: runbook (domain migration R1)

Prepared on 26 Nov 2026. The founder approved R1 the same day: genuine permanent 301 redirects through Cloudflare.

Nothing in this runbook is active. Each checkpoint below needs the founder's explicit approval before it starts.

## How it works

The repository's `plotart/` folder remains the **single source** of every PlotArt page.

- The Studio publisher, website releases and every guard keep working on it unchanged.
- `atlas-tools/plotart_site_build.py` turns it into the plotart.ie site.
  - `https://plotnua.ie/plotart/<path>` → `https://plotart.ie/<path>`
  - Links that leave PlotArt go to `https://plotnua.ie/...`
  - The brand and menu assets PlotArt uses are copied in.
  - plotart.ie gets its own sitemap and robots.txt.
- The `plotart-site` Worker serves the build with the exact GitHub Pages URL behaviour, so every existing address maps one-to-one.
- `.github/workflows/plotart-site-deploy.yml` rebuilds and deploys it whenever main changes PlotArt.
  - Routine content (Studio publications) propagates automatically, with no new approvals.
  - Software and configuration still change only through founder-approved releases.

The Studio, Checkout, Enquiry and Applications Workers keep their workers.dev addresses.

- **Stripe** is untouched: the webhook endpoint and the Connect accounts are unchanged.
- **Accepting plotart.ie:** each Worker accepts plotart.ie only when its configuration names it:
  - `EXTRA_ORIGINS` for Enquiry and Applications;
  - `EXTRA_GALLERY_ORIGINS` for Checkout.
- **Email links:** emailed artwork links follow `PUBLIC_GALLERY_URL`. The default is the old address, which the redirect keeps working.
- **Studio sign-in:** Cloudflare Access is unaffected because the Studio address does not change.

## Consent and tracking (founder instruction 26 Nov 2026)

plotart.ie runs **no non-essential tracking** until a consent solution is approved. This holds during testing too.

- **On plotnua.ie (since the SEO and analytics package, 26 Nov 2026):** every PlotArt page carries the approved analytics head block (`plotart_shell.ANALYTICS_HEAD`): Consent Mode v2 defaults denied, then Cookiebot (domain group b8abbc45), then GA4.
- **On plotart.ie:** the build removes that exact block from every page (`worker/plotart-site/site.json`: `"analytics": "off"`), because the Cookiebot domain group covers plotnua.ie only. The guarded event calls in `pa-enquiry.js` and `pa-basket.js` never fire without gtag and statistics consent.
- **The 404 page:** plotart.ie has its own "not found" page, with no third-party script. PlotNua's 404 page loads Cookiebot and GA4, so it is not used.
- **Build guard:** the build refuses any analytics, advertising or consent-platform script (`TRACKERS` in `plotart_site_build.py`).
- **Browser block:** the Worker's Content-Security-Policy lets scripts run only from plotart.ie itself. Pages may connect only to PlotArt's own Workers, so a tracker added by mistake is blocked by the browser. A browser test confirmed this: a test page with a GA4 tag was refused, and 12 real pages ran with no CSP violation.
- **Adding measurement later:** it needs an approved release that changes the guard, the CSP and the consent banner together.

## Checkpoints (each needs the founder's approval)

| # | What | Who | Reversible by |
|---|---|---|---|
| 0 | Add plotart.ie to Cloudflare (Free) and point its nameservers at Cloudflare | founder | nameservers back to Blacknight (plotart.ie is empty today) |
| 1 | Merge (done, PR #62). Environment `plotart-site` (main only, no reviewers) with secret `CLOUDFLARE_API_TOKEN` (Account · Workers Scripts · Edit) and variable `CLOUDFLARE_ACCOUNT_ID` (done). A **verify** run (manual, deploys nothing) proves the build, token and account. Then the founder sets the repository variable `PLOTART_SITE_ENABLED=true`, and the first deploy goes to the workers.dev address only, noindexed. | founder: the variable; Claude: the verify and deploy runs and their checks | variable off |
| 2 | **Test go-live:** attach plotart.ie and www.plotart.ie to the Worker (still noindexed and Disallow). Add `EXTRA_ORIGINS`/`EXTRA_GALLERY_ORIGINS` to the Enquiry, Applications and Checkout Workers. Test enquiries, applications, hire enquiries, and the basket with Stripe **test mode only**. | founder (dashboard) + approved Worker deploys | detach the domains; config back |
| 3 | **plotnua.ie DNS → Cloudflare**, a separate checkpoint. Import every record (inventory below), keep the GitHub Pages records as **DNS only (grey cloud)**, then switch nameservers. Verify the site, Google Workspace mail (send and receive), SPF/DKIM/DMARC and Search Console verification. **No redirects yet.** | founder | nameservers back to Blacknight (allow up to 48 h; records identical) |
| 4 | **Cutover**, grouped into one approval. See the list below. | founder approves; Claude deploys and verifies | rollback below |
| 5 | Search Console: add plotart.ie as a Domain property (TXT record in Cloudflare), submit `https://plotart.ie/sitemap.xml`, then monitor redirects and coverage. The Change of Address tool does not apply, because only a folder moves. | founder | n/a |

Checkpoint 4 (cutover) consists of:

- (a) `INDEXING = "index"` in `wrangler.toml`, which also switches robots.txt to allow crawling;
- (b) `plotart_domain_sitemap: true` in `plotart-launch-switches.json`, so PlotNua's sitemap drops PlotArt;
- (c) `PUBLIC_GALLERY_URL=https://plotart.ie` on the Enquiry and Checkout Workers;
- (d) a Cloudflare **Redirect Rule** on plotnua.ie;
- (e) proxy (orange cloud) for the `plotnua.ie` apex and `www`, which the Redirect Rule needs. Set SSL/TLS mode to **Full**: GitHub Pages already serves HTTPS, and Flexible would loop.

The Redirect Rule in (d) matches only the exact path `/plotart` and paths beginning `/plotart/`. Paths that merely start with the same letters (`/plotart-x.html`, `/plotartist/`) are never captured:

- When: `(http.host in {"plotnua.ie" "www.plotnua.ie"}) and (http.request.uri.path eq "/plotart" or starts_with(http.request.uri.path, "/plotart/"))`
- Then: dynamic redirect, expression `concat("https://plotart.ie", substring(http.request.uri.path, 8))`, status **301**, preserve query string.
  - `/plotart` → `https://plotart.ie` (the browser requests `/`)
  - `/plotart/x/y.html?q=1` → `https://plotart.ie/x/y.html?q=1`
- After the cutover, `atlas-tools/release/flags.json` `"plotart_address": "plotart.ie"` makes every release's health check (H6) require exactly this. Until then (`"plotnua.ie"`) it fails if any redirect appears.

## Rollback (tested at each checkpoint, in this order)

Reversing nameservers is **not** immediate: resolvers can cache NS records for up to 48 hours. Every step below therefore works without touching nameservers.

1. **Redirects off:** disable the Redirect Rule. This is instant, and plotnua.ie/plotart/ is served by GitHub Pages again, since those pages are never removed.
2. **Indexing:** set `INDEXING` back to `"noindex"` and `plotart_domain_sitemap` back to `false` with an approved release. The deploy workflow rebuilds both sites.
3. **Worker:** restore the previous plotart-site version (`wrangler rollback`, or the dashboard's Deployments tab). The workflow also does this automatically when its live check fails.
4. **Application configuration:** remove `EXTRA_ORIGINS`, `EXTRA_GALLERY_ORIGINS` and `PUBLIC_GALLERY_URL`. The defaults are exactly today's behaviour.
5. **Publishing:** set `PLOTART_SITE_ENABLED=false` to stop deploys. Studio publishing to plotnua.ie never depended on plotart.ie.
6. **Proxy:** plotnua.ie records go back to grey cloud (DNS only). Nameservers go back to Blacknight only as a last resort.

A 301 can be cached by browsers. After rolling back redirects, returning visitors may still be sent to plotart.ie, which keeps serving the same pages. Nothing breaks.

## plotnua.ie DNS inventory (public DNS, 26 Nov 2026)

| Name | Type | Value | Note |
|---|---|---|---|
| plotnua.ie | A ×4 | 185.199.108.153, .109, .110, .111 | GitHub Pages: grey cloud until cutover |
| www | CNAME | colin-macaulay-dcu.github.io | GitHub Pages |
| plotnua.ie | MX | 1 smtp.google.com | Google Workspace: never proxied |
| plotnua.ie | TXT | v=spf1 include:_spf.google.com ~all | SPF |
| plotnua.ie | TXT | google-site-verification=F60i8F… | Search Console / Workspace |
| plotnua.ie | TXT | pinterest-site-verification=43734d… | Pinterest |
| google._domainkey | TXT | v=DKIM1;k=rsa;p=MIIBIj… (full value in prove-plotart-domain.py) | DKIM |
| _dmarc | TXT | v=DMARC1; p=none; rua=mailto:hello@plotnua.ie; fo=1 | DMARC |

- **DNSSEC:** none (no DS record).
- **CAA:** none.
- **AAAA:** none.
- **TTLs:** all 3600.

Public lookups cannot list every subdomain, so export the full zone from Blacknight before checkpoint 3.

`python3 atlas-tools/prove-plotart-domain.py . dns` re-checks these records after the move. The `plotnua` check confirms the PlotNua pages.

## Checks

| Command | What it checks |
|---|---|
| `node worker/plotart-site/test/prove-site.mjs <dist> <repo>` | Every file is served byte-identical at its own path, plus directories, 404, www, noindex, headers and methods |
| `node worker/plotart-studio/test/prove-domain-origins.mjs` | Both addresses accepted only when configured, look-alikes refused, and unchanged by default |
| `python3 atlas-tools/prove-plotart-domain.py . site --base <url> --indexing noindex\|index` | Every PlotArt address live |
| `python3 atlas-tools/prove-plotart-domain.py . redirects` | Every old address answers a 301 to the exact new one, with the query kept |
