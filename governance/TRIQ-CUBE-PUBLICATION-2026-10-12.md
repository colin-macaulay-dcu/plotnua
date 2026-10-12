# TRIQ CUBE — PUBLIC PAGE · PUBLICATION RECORD

**Supplier:** TRIQBRIQ AG, Stuttgart (Atlas ORG-000195) · contact Christian Klerner
**Product:** TRIQ CUBE (TRIQ Office 3×3, "Gartenoffice")
**Prepared:** 12 October 2026 · **Status:** PREPARED, NOT LIVE. Goes live only when the founder pushes `main`.

---

## 1 · Authority

| | |
|---|---|
| Supplier approval | Christian Klerner, email of 12 October 2026: *"After consulting with our product management team, the landing page has now been approved."* |
| Approval received | 12 October 2026 |
| Founder decision | 12 October 2026: the approved page may proceed to public publication and integration |
| Image permission | Written grant of 22 September 2026, condition: credit "© TRIQBRIQ AG" (IPO-TRIQBRIQ-20260922) |
| Report requested | First-month summary: traffic, user behaviour, outbound engagement with buttons to TRIQBRIQ, content improvements |

## 2 · What was built

| | |
|---|---|
| Public page | `triq-cube.html` → **https://plotnua.ie/triq-cube.html** (canonical, `index, follow`, in `sitemap.xml`) |
| Built by | `atlas-tools/build-triq-cube-public.py` (bounded, gated, pinned to the preview's sha256) |
| Approved preview | `triq-cube-preview.html` — **unchanged and still frozen** (SUPPLIER-PREVIEW-SYSTEM-V1 §12). It stays `noindex` and unlinked. |
| Outbound target | `https://triqbriq.de/produkt/triq-gartenoffice-3x3/` — the page TRIQBRIQ asked purchases to go through |

**Lifted verbatim from the approved preview:** both images and their "© TRIQBRIQ AG" credits;
the published price card (€22,700.00, the three options, the German-price basis note); the
specification table; the published-equipment card and chips; every gap in "What PlotNua has
not established".

**Framing edits, and only these:**

1. Specification heading "How Atlas would record it" → "Published specification" (TRIQ is not an Atlas product).
2. The supplier-addressed sentence "A homeowner sees this panel too." dropped (the public reader *is* the homeowner).
3. Private-preview bar, "preview only" eyebrow, the stage rail and the "what this preview is / is not" block removed.
4. Stages 3–5 (Save to My Plot / Compare / Decide) **not carried over**: the TRIQ CUBE is not an Atlas product, so it cannot be saved or compared on PlotNua. Publishing them would claim a capability PlotNua does not have for this product.
5. The inert "Continue to TRIQBRIQ →" control is made live. The image-permission line no longer names the individual who granted it.

**Added:** the standard public chrome (Cookiebot, GA4 `G-PKKJ0RK6N8`, favicons, brand mark,
canonical search pill, site footer), one link to *Living in the Garden*, and the GA4 outbound event.

## 3 · Where TRIQBRIQ appears

- **The public page only**, reachable from the sitemap/search engines and from any link PlotNua or TRIQBRIQ shares.
- **Not** in Garden Room Results, Compare, My Plot, Search or any Discovery page. No product record exists in Atlas, and none was created.
- The page links *out* to `discovery-living-in-the-garden.html`; no Discovery page links *in*. Adding an inbound link or an Atlas product is a separate founder decision (see §6).

## 4 · Analytics — what Christian's report can and cannot contain

Uses the existing architecture only: GA4 property `G-PKKJ0RK6N8`, loaded behind Cookiebot
(auto-blocking). No new tool, cookie, identifier or personal data.

**New event:** `supplier_outbound_click`, fired on every link to triqbriq.de on the page.

| Parameter | Value |
|---|---|
| `supplier_id` | `triqbriq` |
| `product_id` | `triq-cube` |
| `link_location` | `handoff` (the button) · `source_note` (product-page link in the notes) · `image_source` (image source links) |
| `link_url`, `link_domain`, `outbound` | destination, `triqbriq.de`, `true` |

| Metric for the report | Source | Available |
|---|---|---|
| Landing-page views | GA4 `page_view`, page path `/triq-cube.html` | Yes |
| Traffic sources | Session source / medium for that page | Yes |
| Engagement | Engaged sessions, engagement rate, average engagement time on the page | Yes |
| Outbound button clicks | `supplier_outbound_click` where `link_location = handoff` | Yes, **once the parameter is registered** (below) |
| Outbound click-through rate | handoff clicks ÷ page views (and ÷ sessions) | Yes, computed |
| Scroll depth | GA4 enhanced measurement `scroll` (90% only), if enabled on the property | Unverified — property settings not visible from here |
| What happens on triqbriq.de (bounce, enquiries, sales) | TRIQBRIQ's own analytics | **No.** PlotNua cannot measure it. TRIQBRIQ will see plotnua.ie as the referring site in its own analytics (no `noreferrer`). |

**Caveats to state in the report:** figures cover only visitors who accept statistics cookies;
GA4 thresholds may hide very small numbers.

**FOUNDER ACTION BEFORE PUSH — GA4 Admin → Custom definitions → create event-scoped custom
dimensions `link_location`, `supplier_id`, `product_id`.** Registration is not retroactive:
clicks recorded before it exist only as raw event counts and cannot be broken down by button.

## 5 · Reporting period

Starts on the date the page is verified live (`public_page_live_at`, recorded in the supplier
contact register at verification) and runs one calendar month.

## 6 · Open founder decisions (not done)

1. **Commercial position.** `09 Commercial/TRIQ-COMMERCIAL-POSITION.md` §4.3 says *do not
   activate an ordinary untracked outbound link* before terms are agreed. This page activates an
   outbound link with PlotNua-side click measurement, but **no attribution agreement or
   commercial terms exist**. Publishing means accepting that, by founder decision.
2. **Irish availability** is still unanswered by TRIQBRIQ; the page states it as not established.
3. **Results / Atlas product.** Entering the TRIQ CUBE as an Atlas Garden Room product would put it in
   homeowners' Results and Compare. That needs a full Atlas ingestion and a universe refresh, and it is a
   recommendation decision. Not done.
4. **Country of manufacture.** The approved page shows "Germany" / "Made in Germany". On 12 October 2026
   the product page itself did not state it, although the rest of the specification matched. It is kept
   because TRIQBRIQ approved it. Consider confirming it with Christian.
