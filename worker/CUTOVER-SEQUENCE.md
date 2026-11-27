# PlotNua hosting migration and PlotArt SEO cutover: sequence

Prepared on 27 November 2026. **Nothing here is active.** Each numbered step needs the founder's explicit approval when it starts. Every step has its own rollback, and stopping between steps is always safe.

## Two separate moves, in this order

**A. PlotNua hosting.** plotnua.ie moves from GitHub Pages to the plotnua-site Worker. Visitors see no change: the same files, the same URLs, the same analytics and consent. Its rollback is GitHub Pages, which stays current throughout.

**B. PlotArt SEO cutover.** plotart.ie becomes the indexed home of PlotArt, and plotnua.ie/plotart/* answers with 301 redirects.

A goes first because the redirects then live in the Worker's own code (`PLOTART_ADDRESS`), which is tested, versioned and rolls back with the site. With plotnua.ie on GitHub Pages, they would have to be a hand-maintained Cloudflare rule. Leave at least 7 calm days between A and B.

---

## Preparation: done 27 Nov 2026

1. **DNS reconciliation:** done. The Blacknight zone (18 records) was read with the founder signed in. Against public DNS it shows 0 items needing attention. The copy is in plotnua-infrastructure `hosting-migration/plotnua-dns-2026-11-27/`.
2. **Resend:** plotnua.ie is *Verified*, with three verified records:
   - `resend._domainkey` TXT (DKIM);
   - `send` CNAME → `send.forge.rmta.net`;
   - `rsend` CNAME → `rsend-euw1.forge.rmta.net`. This one was found in the dashboard and added to the tooling in #76.
3. **Parity:** the PlotNua test deploy and comparison ran green again on 27 Nov, after #72.

---

## A. PlotNua hosting migration

### A1. Add plotnua.ie to Cloudflare (Free plan, no cost): COMPLETE 27 Nov 2026

- **Founder:** added the site on the Free plan.
- **Records in Cloudflare:** Cloudflare discovered 11 records. Claude added the 3 it missed: the Google DKIM TXT, Resend `send` and Resend `rsend`.
- **Accounted for:** 14 records in Cloudflare, plus the 4 Blacknight NS records, which Cloudflare replaces with `rosalie` / `sevki` = 18.
- **Proxy:** every record is **DNS only**.
- **Check:** `dns-reconcile.py check <blacknight zone> --cloudflare <cloudflare export>` → 0 missing, 0 extra.
- **Zone state:** pending (nameservers unchanged). The export is in plotnua-infrastructure.
- **Rollback:** delete the pending zone. Nothing has changed until nameservers move.

### A2. Lower TTLs at Blacknight: DONE 27 Nov 2026, 18:46 UTC

- **Changed:** all 14 non-NS records went to **300 s**:
  - the A RRset (previously 600);
  - MX, every TXT, `www`, `send` and `rsend` (previously 3600).
- **Unchanged:**
  - the record contents;
  - the four NS records at the zone apex (3600). The founder's instruction is no nameserver change, and these are only meaningful while Blacknight is authoritative.
- **Public DNS:** verified the same evening. Google and Cloudflare resolvers serve the new values with TTL ≤ 300 once their old entries expire. Every old entry has expired by **19:46 UTC**, because the longest previous TTL was 3600 s.
- **Earliest safe A3 time:** the founder requires at least 24 hours, so **Saturday 28 Nov 2026, 19:00 UTC (19:00 Dublin)** or later.
- **Rollback:** restore the TTLs. This is harmless either way.

### A3. Change nameservers at Blacknight to `rosalie.ns.cloudflare.com` and `sevki.ns.cloudflare.com`

**Founder approval and action at Blacknight.** No other change in the same window: no website release, Studio publication batch, Worker deploy, D1 migration, Cloudflare setting or proxy change. The freeze runs from the baseline run to the +1 h compare; see *Coordination* below.

**Before:**
1. Run the **cutover check baseline**: Actions → *PlotNua cutover check* → `baseline`. All checks must pass. Note the run ID.
2. Re-run `dns-reconcile.py check <blacknight zone> --live` and `--cloudflare <fresh export>`. Both must show 0 items, so the two zones are still identical.
3. Check at Blacknight that DNSSEC is off for plotnua.ie. There must be no DS record; the reconcile check also confirms this.

**Change:** at Blacknight, set *Nameservers* to the two Cloudflare names. Cloudflare then activates the zone. The founder may need to click *Check nameservers* in Cloudflare. Its proxy settings stay DNS only.

**After:** run `compare` against the baseline run ID at +15 min, +1 h, +24 h and +48 h. The compare covers:
- every published PlotNua file (status and bytes);
- the plotart.ie pages and Studio (site health H1–H6);
- every Worker endpoint the forms and checkout use;
- DNS for Google Workspace and Resend;
- TLS certificates and redirects;
- robots, sitemaps, canonicals and noindex state;
- the Google Maps key and the Cesium token.

Expected change: only which nameservers answer.

**Email delivery, by hand at +1 h:**
- the founder sends from `hello@plotnua.ie` to an outside address and replies back;
- one PlotArt enquiry through the live form, which the founder receives through Resend;
- the Resend dashboard still shows the domain *Verified*.

**Rollback: two different kinds of propagation, which are not the same:**

- **Records (inside a zone):** these follow the record TTL, now 300 s.
  - If a record is wrong, correct it **in Cloudflare**; the fix reaches resolvers within about 5 minutes.
  - During the transition, make any correction **in both zones** (Cloudflare and Blacknight), because resolvers may still be asking either. Keep the Blacknight zone intact and identical for at least 7 days after A3.
- **Delegation (which nameservers answer):** this does **not** follow the 300 s record TTL.
  - The `.ie` registry publishes the delegation with its own NS TTL, which the zone owner cannot set and which is typically **one to two days**. Resolvers also cache the NS set from the zone itself: 3600 s at Blacknight, **86 400 s** at Cloudflare.
  - Registrars and registries apply nameserver changes on their own schedule (minutes to hours).
  - So setting the nameservers back to Blacknight can take **up to about 48 hours** to reach every resolver. During that time some visitors and mail servers are still answered by Cloudflare.
  - That is safe only because both zones hold identical records. A nameserver rollback is therefore a last resort, for a fault in Cloudflare's DNS service itself. Every other problem is fixed by correcting records in the zone that answers.
- **Do not delete the Cloudflare zone, or change records in only one zone,** while either delegation may still be cached.

**Website:** still served by GitHub Pages (DNS only), so it is unchanged. GitHub Pages hosting stays fully operational throughout A3 and A4.

**Coordination (other development workstreams):**
- The freeze window, from the baseline to the +1 h compare (about 90 minutes), is announced on the open PRs. These are the Art for Hire and Mobile Gallery release, the Studio Commercial branch and the cutover PRs.
- During the window no workstream merges to main, publishes, deploys a Worker or runs a D1 migration.
- A legitimate release that slips in anyway is recognised by the compare: a file that changed to exactly the new build is reported, not failed.

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
