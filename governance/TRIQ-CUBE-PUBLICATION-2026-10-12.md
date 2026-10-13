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
6. *(13 October 2026)* "Made in Germany" chip and "Country of manufacture: Germany" row removed: not independently verifiable (§6.3).

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

## 6 · Founder decisions, 13 October 2026

**Design and presentation approved** by the founder after review.

### 6.1 · BOUNDED EXCEPTION to the commercial-position hold

`09 Commercial/TRIQ-COMMERCIAL-POSITION.md` §4.3 and §9 prohibit activating an ordinary
untracked outbound link before commercial terms are agreed. **The founder authorises an ordinary
outbound link to TRIQBRIQ as an explicit, bounded exception, for this initial supplier-approved
listing only.**

| | |
|---|---|
| Scope | One link destination, `https://triqbriq.de/produkt/triq-gartenoffice-3x3/`, from `triq-cube.html` only |
| Basis | TRIQBRIQ product management approved the page; Christian requested a one-month performance report |
| Nature | An **informational supplier listing, not a commercial partnership** |
| Commercial terms | **None.** No commission, referral fee or attribution agreement exists |
| Does NOT extend to | any other TRIQBRIQ page or product, any other supplier, Results/Compare/My Plot, CONNECT, or any future listing |
| Unchanged | §4.2 remains entirely open; PREFERRED PARTNER — NONE; CONNECT — NOT AUTHORISED; no percentage or term proposed |

Copy rules that follow from it: TRIQBRIQ is never described as a commercial partner, and the page
does not imply that Irish delivery, installation, availability or final Irish pricing is confirmed.

### 6.2 · Atlas

**The TRIQ CUBE stays outside Atlas recommendations, Results and Compare until its Irish
availability is established.** No product record is created.

### 6.3 · Product claim

The "Made in Germany" chip and the "Country of manufacture: Germany" row are **removed**, because the
claim could not be independently verified. On 13 October 2026, triqbriq.de's product page did not
state where the TRIQ Office 3×3 is made. Its production page names a Stammwerk in Tübingen and
licensed production in Austria, with Sweden, Portugal, Switzerland and the USA in preparation, and
never ties this product to a country. **Kept:** "Manufacturer: TRIQBRIQ AG, Stuttgart" (the AG's
published address).

### 6.4 · Analytics — the three GA4 custom dimensions

GA4 Admin → Data display → Custom definitions → Create custom dimension:

| Dimension name | Scope | Event parameter |
|---|---|---|
| Link location | Event | `link_location` |
| Supplier ID | Event | `supplier_id` |
| Product ID | Event | `product_id` |

`link_url`, `link_domain` and `outbound` map to GA4's built-in Link URL / Link domain / Outbound
dimensions and need no registration.

**Consent behaviour, verified on the live site 13 October 2026** (about.html, whose Cookiebot and
gtag block `triq-cube.html` copies byte for byte): Cookiebot auto-blocking holds the GA4 script
(`type="text/plain"`), and **no measurement request is sent before consent**, including for a
`supplier_outbound_click` fired before consent, or after a decline. Firing after consent could not
be exercised headlessly, because Cookiebot treats the test browser as a crawler. Confirm it in GA4
Realtime after publication.

### 6.5 · Still open

Irish availability (unanswered by TRIQBRIQ); §4.2 commercial terms.

---

## Addendum, 13 October 2026: product name corrected to TRIQ QUBE

TRIQBRIQ AG (Christian Klerner) confirmed that the correct product name is **TRIQ QUBE**, not "TRIQ CUBE". The founder instructed the correction the same day.

**Corrected:** every visible use on the public page:
- title, meta description, Open Graph and Twitter metadata;
- the H1;
- the Irish-availability sentence;
- the two handoff sentences.

The Search record title now reads "TRIQ QUBE by TRIQBRIQ AG". The sitemap comment is updated and lastmod is set to 2026-10-13.

**Kept on purpose:**
- **The URL `triq-cube.html`**, so existing links don't break.
- **The page marker, the Search record id `info-triq-cube`, and the GA4 `product_id: 'triq-cube'`.** These are identifiers, not visible text. Keeping them means the first-month outbound report to TRIQBRIQ is one continuous series.
- **The frozen supplier preview `triq-cube-preview.html`.** It is private (noindex, unlinked, not in the sitemap) and remains the approved record. The public-page builder corrects the name as an explicit, gated step after lifting its approved blocks.

**Old searches:** "TRIQ CUBE" is kept only as a hidden Search alias (record topics), so older searches still find the page while visitors only ever see TRIQ QUBE.

**Not changed:**
- specifications, prices, imagery permissions and availability statements;
- Irish delivery, which remains unconfirmed;
- Atlas eligibility (still not in Results, Compare or the Maker Explorer).

This file keeps its original name for traceability.

---

## Addendum, 13 October 2026: manufacturer delivery confirmation

Christian Klerner (TRIQBRIQ AG), in writing:

> "In principle, our building kit is available for delivery worldwide. We would be happy to review specific delivery addresses individually with each prospective customer upon enquiry."

**Change on `triq-cube.html`:** two items in "What PlotNua has not established" are replaced by one item carrying the founder-approved wording, verbatim. The two items were "Irish availability is not yet confirmed … no confirmation that the TRIQ QUBE can be supplied" and "Delivery to Ireland is not established". The new item reads:

> **Delivery to Ireland.** International delivery is available in principle. Delivery to Ireland is subject to individual confirmation by TRIQBRIQ AG based on the customer's delivery address. Contact the manufacturer to confirm delivery arrangements and obtain a quotation.

**Unchanged on purpose:**
- **"No Irish price" item:** the German price is not an Irish delivered price.
- **"Installation … not established" item.**
- **German-price caveat on the price card.**
- **"Irish availability not yet confirmed" tag, and the Search summary:** delivery to an Irish address still needs individual confirmation.
- **The outbound link and GA4 event.**
- **Manufacturer-information status.** TRIQ QUBE remains outside Atlas Results, Compare and the Maker Explorer; there is no product record.

The builder gate refuses the page if any of the following is missing or present:
- **missing:** the approved wording (exactly once), the "No Irish price" and "Installation" items, or the German-price caveat;
- **present:** guaranteed or included delivery or installation, a shipping price, or a delivery time.

**Evidence recorded in:**
- Atlas ORG-000195 notes (dated entry);
- `supplier-contact-register.json` (`delivery_evidence`, `delivery_evidence_state` INTERNATIONAL_IN_PRINCIPLE_IRELAND_CASE_BY_CASE). `irish_route_state` is deliberately left empty, because DELIVERY_TO_IRELAND would overclaim.
