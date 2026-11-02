# PlotNua · Customer Journey Evolution · Approved architecture

**Founder approval:** 2 November 2026, for the strategic architecture audit of the same date.
**Status:** Phase 0 (this record and the Journey Contract amendments) and Phase 1 (homepage, navigation, maker explanation) are authorised for development. Production deployment of Phase 1 needs a separate founder approval. Phase 2 and later are **not** authorised.

---

## 1 · The proposition

> **Discover the possibilities. Explore them yourself, or let PlotNua do the homework.**

PlotNua has two complementary routes. They connect naturally, and a homeowner can move between them at any point.

### Route A · Explore yourself

Visitors browse:
- Discoveries;
- products and makers (the Supplier Galleries, Maker Explorers and Provider Explorers);
- site search.

They save to My Plot and contact makers where that is available.

### Route B · Let PlotNua do the homework

1. **The Brief.** The homeowner gives property details, interests, requirements and budget.
2. **An immediate shortlist,** only where qualified Atlas data supports one. It is produced by the **existing** Match → Results engine; there is no second matching engine.
3. **A free, founder-reviewed detailed comparison,** on request, when further research is needed. It is delivered as a branded PDF with an accompanying email.

---

## 2 · Permanent business rule · free to homeowners, supplier-funded

**PlotNua is free for homeowners. This rule is permanent.**

There must be:
- no homeowner comparison fees;
- no premium research charges;
- no paid homeowner subscriptions;
- no suggestion, anywhere, that detailed comparisons might become a paid service.

**Revenue model.** PlotNua helps homeowners discover possibilities, research products, compare options and connect with relevant suppliers. The commercial objective is to generate genuine purchasing interest. PlotNua may earn referral fees or sales commissions from participating suppliers.

**Disclosure.** Commission arrangements are disclosed where they apply, next to the offer concerned.

**Independence.** Commercial relationships must **never** influence product suitability, matching or ranking. This is already enforced in code:
- `commercial/referral-offers.json` is read only by the Maker Explorer builder;
- that file is never read by the Atlas snapshot, Search, matching, scoring, ranking or the maker order.

Every Route B component must inherit the same separation and prove it with a guard.

---

## 3 · Approved founder decisions (2 Nov 2026)

1. The two-route architecture is approved.
2. The existing homepage H6 hero stays exactly as it is (locked).
3. A premium two-route section sits immediately beneath the hero.
4. Navigation uses the wording **"Get help choosing"**.
5. All homeowner comparison services are free.
6. The initial aim is a three-working-day response, subject to founder capacity.
7. Detailed comparisons are delivered as branded PDFs with accompanying emails.
8. Comparison requests are stored in a **separate** Airtable base, not Atlas Core.
9. Misleading supplier counts are replaced with clearly defined Atlas research figures, refreshed from source data.
10. Garden rooms, additional homes and wellness products are prioritised first.
11. Requests about other categories are allowed where Atlas has research.
12. Actual homeowner demand guides future Atlas data priorities.

---

## 4 · Architecture

```
Homepage · Discovery · Search
        │
   ┌────┴─────────────────────────────┐
 ROUTE A                           ROUTE B  ("Get help choosing")
 Discovery Library → Discovery     BRIEF (Phase 3, in-browser, nothing sent)
 → Meet the makers (granted images) → MATCH → RESULTS (existing engine, published universes only)
 → Browse every product (text where      │
   no image)                             │
 → Save ────────────► MY PLOT ◄──────────┘   (Compare · Resolve · Progress unchanged)
                          │
                 COMPARISON REQUEST (Phase 2, to PlotNua only; intake OFF until approved)
                          │
                 Founder review → branded PDF + email (free)
```

**Binding constraints (Journey Contract §8):**
- no second matching engine;
- no second enquiry composer;
- no supplier handoff before Progress.

The two recorded amendments live in `PLOTNUA-JOURNEY-CONTRACT.md` §10. They are **designed, not built**.

---

## 5 · What Phase 1 delivers

| Item | Delivery |
|---|---|
| Homepage two-route section | Directly beneath the locked H6 hero and above the Atlas strip, in `index.html`, between fenced `TWO-ROUTE` markers |
| "Get help choosing" | Global header (`atlas-tools/pn_header.py`): a desktop control beside WhatsApp, and in the phone Menu under "Talk to PlotNua". It links to `help-choosing.html` |
| `help-choosing.html` | Route B landing page. It states truthfully what works today: the existing garden-room and garden-home journeys lead to an Atlas shortlist; wellness makers can be explored on Garden Retreat. The free detailed comparison is described as **not yet open for requests**. There is no form and no intake |
| `how-plotnua-works-with-makers.html` | Explains featured makers (image permission), wider Atlas research (text where no image), commission disclosure, evidence states, and independence of ranking |
| Atlas research figures | "Suppliers" (Organisation Type = Supplier, 37) is replaced by **Makers researched**: distinct organisations linked to at least one Atlas product, fixtures excluded. Generated by `.github/scripts/atlas_stats.py` from Atlas Core and refreshed by the existing daily workflow |
| Homepage footer | Adds "Get help choosing" and "How PlotNua works with makers" |

**Phase 1 does not include:**
- the comparison request form, Worker or Airtable base (Phase 2);
- the Brief and shortlist widening (Phase 3);
- Discovery closing panels;
- My Plot and Search entry points (each would promise inactive functionality, or would touch hash-frozen or frozen components).

**Untouched:** the H6 hero, all Discoveries, PlotArt, GridNua, the Idea Board, Supplier Galleries, `your-plot.html`, the Results/Resolve freeze, image-rights records and Automation V1's files.

---

## 6 · Phases

| Phase | Scope | Status |
|---|---|---|
| 0 | This record; Journey Contract amendments; commercial model | Done (this branch) |
| 1 | Homepage section, navigation, makers page, research figures | Built on branch; **awaiting founder production approval** |
| 2 | Comparison request service: form, Worker (switch off), separate Airtable base, privacy V10, PDF template | Needs separate founder approval |
| 3 | Brief → existing Match/Results; wellness pool; freshness date; commercial-field exclusion guard | Not started |
| 4 | Atlas data improvement (AT-1 contacts, availability, VAT, features, new universes by demand) | Continuous |
| 5 | Supplier introductions, automatic acknowledgement, Studio requests view | Later |

---

## 7 · Guard

`atlas-tools/prove-two-route.py` holds the Phase 1 promises:
- the section appears once, after the hero and before the Atlas strip;
- the H6 component is byte-identical to its base;
- every link resolves to an existing page;
- no comparison intake, form or endpoint exists;
- free-to-homeowners wording is present and no paid-service wording appears;
- the header control is present.

`--self-test` proves that each check can fail.
