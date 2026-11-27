# PlotNua hosting migration and PlotArt SEO cutover: sequence

Prepared on 27 November 2026. **Nothing here is active.** Each numbered step needs the founder's explicit approval when it starts. Every step has its own rollback, and stopping between steps is always safe.

## Two separate moves, in this order

**A. PlotNua hosting.** plotnua.ie moves from GitHub Pages to the plotnua-site Worker. Visitors see no change: the same files, the same URLs, the same analytics and consent. Its rollback is GitHub Pages, which stays current throughout.

**B. PlotArt SEO cutover.** plotart.ie becomes the indexed home of PlotArt, and plotnua.ie/plotart/* answers with 301 redirects.

A goes first because the redirects then live in the Worker's own code (`PLOTART_ADDRESS`), which is tested, versioned and rolls back with the site. With plotnua.ie on GitHub Pages, they would have to be a hand-maintained Cloudflare rule. Leave at least 7 calm days between A and B.

---

## Preparation (no approval needed; nothing changes)

1. **DNS reconciliation:**
   - Export the Blacknight zone (needs one sign-in).
   - Run `python3 atlas-tools/dns-reconcile.py check <zone> --live atlas-tools/release/plotnua-dns-live-2026-11-27.json`.
   - Every record must be classified, and nothing answering today may be missing.
2. **Resend:** the plotnua.ie domain shows *Verified* in the Resend dashboard. Its records today:
   - `resend._domainkey` (TXT, DKIM);
   - `send` CNAME → `send.forge.rmta.net`.
3. **Parity:** the PlotNua test deploy and comparison run green (last result 27 Nov: 1,647 URLs, 0 differences).

---

## A. PlotNua hosting migration

### A1. Add plotnua.ie to Cloudflare (Free plan, no cost)

- Import every record, **all DNS only (grey cloud)**: mail, verification, GitHub Pages A/CNAME.
- Check `dns-reconcile.py check <zone> --cloudflare <export>`: 0 missing, 0 extra.
- **Founder action:** add the site in the Cloudflare dashboard. The API token does not have zone permission, by design.
- **Rollback:** delete the pending zone. Nothing has changed until nameservers move.

### A2. Lower TTLs at Blacknight

- Set them to 300 s, 24 hours ahead. This keeps any later rollback fast.
- **Rollback:** restore the TTLs.

### A3. Change nameservers at Blacknight to the two Cloudflare names

- **Founder approval and action at Blacknight.**
- **Email continuity:**
  - MX, SPF, DKIM (Google and Resend), DMARC and the Resend `send` CNAME are identical and DNS only, so mail flow does not change.
  - Verify by sending to and from `hello@` and `colin@`, and by a Resend test send from the enquiry relay.
- **Website:** still on GitHub Pages (DNS only), unchanged.
- **Rollback:** set the Blacknight nameservers back. Records are identical on both sides, so either answer is correct during propagation.

### A4. Attach plotnua.ie and www.plotnua.ie to the plotnua-site Worker (Cloudflare dashboard, Custom Domains)

- The Worker serves byte-identical files. www → apex 301, as today.
- **Live check, immediately:**
  - the comparison run against the Pages origin;
  - privacy and consent checks;
  - enquiry and application forms;
  - Your Plot;
  - search.
- **Rollback, minutes:**
  1. Detach the custom domains.
  2. Restore the GitHub Pages A records (185.199.108–111.153) and the `www` CNAME, DNS only.
  3. GitHub Pages is still current because every release still publishes it.

### A5. A merged release finishes the move

- **Prepared (inert):** `plotnua-site-deploy.yml` runs on every push to main.
  - It does nothing while `atlas-tools/release/flags.json` has `"plotnua_host": "pages"`.
  - With `"worker"` it builds, runs the same proofs and privacy test, and deploys.
  - It then checks plotnua.ie live: served by the Worker, not noindexed, every page 200, and the site health checks.
  - It rolls the Worker back automatically if the live check fails.
- **The A5 release itself is two lines:** `"plotnua_host": "worker"` and `workers_dev = false`, so the test copy disappears. The job refuses the first without the second.
- GitHub Pages keeps publishing on every push, so it stays a current rollback.
- **Rollback:** revert the two lines. Detach the domains as in A4 if needed.

### A6. Optional, separate decision: make the repository private

- Possible once GitHub Pages is no longer the host. It stops public access to internal records and their history.
- **Cost:** private repositories get 2,000 free Actions minutes a month. Measured use is about 5,600 minutes a month, excluding Pages builds (gate, publishers, deploys), so a private repository would incur Actions charges unless usage is reduced.
- **Founder decision, 27 Nov 2026:** the repository stays public on the free plan.
- GitHub Pages could no longer be the rollback; Worker version rollback replaces it.

---

## B. PlotArt SEO cutover (one release, approved as a unit)

### B0. Before

- Content quiet window of a few hours (Studio queue paused or empty).
- Full live proofs on plotart.ie.
- Google Search Console:
  - plotart.ie added as a Domain property (TXT record, DNS only);
  - plotnua.ie property kept.
- Merge the H6 redirect health check from `dev/plotart-cutover-prep`.

### B1. The cutover release, all together

- **Indexing:** `worker/plotart-site/wrangler.toml` `INDEXING = "index"`. This removes `noindex`, and the build publishes a robots.txt Allow and the sitemap.
- **Redirects:** `worker/plotnua-site/wrangler.toml` `PLOTART_ADDRESS = "plotart.ie"`, so every `/plotart` and `/plotart/<path>` returns an exact 301 to `https://plotart.ie/<path>`, query kept, single hop. Look-alike paths such as `/plotart-health-probe.html` are untouched.
- **Canonical URLs** on plotart.ie pages: plotart.ie. The PlotNua sitemap stops listing PlotArt URLs.
- **Email links:** `PUBLIC_GALLERY_URL = "https://plotart.ie"` on the Enquiry and Checkout Workers, so emailed links point at the new address. Old links still work through the redirects.
- **Health:** `flags.json` `plotart_address = "plotart.ie"` turns on health check H6 on every release.

### B2. Immediately after

- **Redirect verification:** every old URL (sitemap plus all published files) returns an exact 301, with no chains.
- **Search Console:**
  - submit the plotart.ie sitemap;
  - request indexing for the home, gallery, artists and the available-works pages.
  - No *Change of Address*: plotnua.ie stays a live site.

### B3. Monitoring (weeks 1, 2, 4, 8 and 12)

- Search Console: indexed pages versus "Page with redirect"; crawl errors and 404s; Core Web Vitals.
- Clicks and impressions for PlotArt queries, old and new property.
- GA4 sessions by `site_name`.
- Enquiries and checkout starts.

A dip in weeks 1–4 is normal. A sustained drop triggers a review, not an automatic rollback.

### Rollback

- **One release:** `PLOTART_ADDRESS = "plotnua.ie"` (redirects off), `INDEXING = "noindex"`, sitemaps and canonicals back.
- Old URLs on plotnua.ie keep working throughout, and their files stay in place until at least week 12.
