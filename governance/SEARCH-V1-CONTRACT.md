# PLOTNUA SEARCH V1 · FROZEN CONTRACT

**Status:** APPROVED FOR BUILD · 8 October 2026 · founder decisions B-1 to B-4 and the
additional decisions recorded below.
**Baseline commit:** `1bf7d4b`
**Baseline universe:** `garden-room-recommendation-universe-v1.json`
sha256 `db4ecb7ff99ebaa0e2d88b89ce395f0bcb78c5a2750630aefbc3669413ff82db`
(re-frozen 14 Oct 2026 for the ÖÖD House targeted update: sha256
`c64fe26ebb5b5cf35abe0abe3e6effa82845a81f24f627ab974624bfdcc9d3c7`; only the seven ÖÖD
records differ)

---

## 1 · THE ARCHITECTURAL CONTRACT — ONE DIRECTION ONLY

```
PUBLISHED / GOVERNED CORPUS
        ↓
GENERATED SEARCH INDEX          search-index-v1.json
        ↓
CLIENT-SIDE SEARCH              search.js
        ↓
SEARCH RELEVANCE                orders search results ONLY
        ↓
EXISTING PUBLIC ROUTES
```

**There is no reverse influence into Atlas.** Search must never change Atlas ranking,
qualification, confidence, evidence, pricing governance, matching or My Plot state. The
index is generated FROM the universe and is downstream of it by construction. The build
records the universe sha256 and refuses if it moved.

---

## 2 · RECORD SCHEMA — CLOSED

Envelope:

```
schema version generated sourceCommit sourceUniverseSha256
counts{possibility,product,supplier,journey} synonymMapVersion records[]
aliases{k,t}   (amendment A6, 12 Nov 2026)
```

Four record types. No field outside these lists may be emitted.

| type | fields |
|---|---|
| `possibility` | id type title standfirst topics[] route |
| `product` | id type name organisation productType price? priceBasis? tier caveats[] rt? (route composed from the envelope `routes` template; see amendment A1) |
| `supplier` | id type name productCount priceRange? tiersPresent[] caveats[] route |
| `journey` | id type title possibilityId route |

**Forbidden, and guarded:** `qualification`, `priceEvidence`, `priceEvidenceRef`,
`evidenceSignals`, `hardBlockers`, `organisationEvidence`, `features`, `imagery`, any
score, any rank, any Airtable record id.

`tier` carries the literal `HIGH_CONFIDENCE` / `WITH_CAVEAT` string. Never derived,
never rounded, never upgraded.

`price` is emitted **only** where `priceSafeForMatching === true` **and the source
record's currency is EUR** (amendment A2). The other products carry no `price` key at
all, so there is nothing to filter on or display wrongly. Every `price` and
`priceRange` in the index is therefore a euro amount; the runtime formats them as euro.

### FEATURES — NEVER INDEXED IN V1

Founder decision. The evidence: four products mention sauna/wellness and every mention
is incidental or negative — MyCabin explicitly EXCLUDES the Cube Sauna from that range;
Iglucraft Igluoffice 1 is a warranty exclusion for a sauna heater; Igluoffice 2 is an
office variant by a maker of saunas; Koto Niwa is "suited to a sauna or small garden
studio". Indexing `features` would return three products that are not saunas. The field
is prose, not identity, and it stays out.

### IMAGERY — SEARCH V1 IS TEXT-ONLY

Founder decision. The schema carries no imagery field, so Search V1 shows no product or
supplier imagery. Guard G8 proves the absence rather than checking a credit: the index
holds no imagery/asset/image-URL field, and the runtime holds no code path that could
render product or supplier imagery from any other source. Unauthorised imagery therefore
cannot leak through Search at all. The existing image-rights system is unchanged.

---

## 3 · SUPPLIER PUBLICATION ELIGIBILITY — APPROVED

A `supplier` record is emitted for an organisation if and only if:

- **S1** it is the `organisation` of at least one product in the universe; and
- **S2** at least one of those products is ELIGIBLE under the universe's own
  qualification; and
- **S3** it holds `organisationEvidence`; and
- **S4** it is not present solely in `atlas-recognition-pool.json`; and
- **S5** it has no private-preview-only provenance.

Where ALL of an organisation's products carry `noPublishedIrishRoute`, the record is
still emitted AND MUST carry the caveat. Suppression would hide a supplier PlotNua knows
about; silent inclusion would imply an Irish route that is not evidenced.

**The resulting count is an output of governance, not a target.** Measured at this
baseline: 64 organisations, 9 of them caveated under the final clause.

---

## 4 · PROHIBITED SOURCES — ABSOLUTE

| source | rule |
|---|---|
| 106 private supplier previews | **NEVER SEARCHABLE.** Not by name, not by filename, not by URL. |
| `supplier-preview-system/` templates | never |
| 6 retired noindex Discoveries | never — all are `Moved \| PlotNua` redirect stubs |
| legacy / orphan pages | never — includes `campaign-look-again.html`, which is noindex WITH real content |
| `atlas-recognition-pool.json` | **NEVER A PUBLICATION SOURCE.** Search must not convert recognition knowledge into publication eligibility. |
| `your-plot.html` / My Plot state | never indexed; it is a destination, not a result |
| `garden-room-detail-*.json` | not in V1 |
| `additional-home-universe-v1.json` | held; eligibility not reconciled |

**The gate is an ALLOWLIST, not a denylist:** a page enters the index only if its URL is
present in `sitemap.xml`. Not "if not noindex" — under a denylist a preview added later
would silently inherit indexability.

Knowing the exact hidden name must not make Search reveal it. See §8.

---

## 5 · RELEVANCE, GROUPING AND REFINEMENT

Relevance orders results and nothing else. Ordering key, strict precedence:

1. exact name match
2. name prefix
3. organisation match
4. productType match
5. remainder

**No tier, confidence, price or Atlas signal participates in ordering.** A WITH_CAVEAT
exact match outranks a HIGH_CONFIDENCE partial every time, because that is what the
homeowner asked for.

Result surface, fixed order, counts always shown:

```
Possibilities (n)   first — PlotNua's own thinking
Suppliers (n)       grouped, collapsed, expandable
Products (n)        grouped by supplier; <=3 per supplier shown, "show all n"
Journeys (n)        only where not already reached via a possibility
```

Refinement is lightweight and non-Atlas: has-a-price (restricted to price-safe only),
price band, supplier. **No confidence filter, no evidence filter, no "best match" badge**
— any of those would masquerade as Atlas.

`productCategory` is a single value ("Garden Rooms") for every product and is therefore
useless as a facet. `productType` is the real discriminator.

---

## 6 · GOVERNED TOPIC / SYNONYM MAP

`atlas-tools/search-topic-map.json`. Human-readable, flat, versioned. **No AI or API
query expansion. No fuzzy matching. No edit distance.**

Founder is the approval authority. V1 ships ONLY these four audited mappings:

| phrase | target | note |
|---|---|---|
| `spare garden` | The Borrowed Garden | naive matching returns open-your-home-to-art + about and MISSES the right page |
| `solar`, `solar battery` | The House as a Power Station | 0 products; this Discovery is the only truthful answer |
| `sauna` | Garden Retreat | Garden Retreat first, then governed wellness saunas only (amended 14 Oct 2026; was POSSIBILITY ONLY — see §2 features) |
| `parking` | Hidden Cars + Driveway Income | narrowing map; naive matching returns 7 pages on incidental prose |

`garden office` is deliberately NOT a synonym: the corpus already says it natively in
`productType` (28 "Contemporary garden office", 12 "UK insulated garden office
configuration", 9 "Compact garden office pod", and more). Adding it would double-count.

No speculative synonyms during implementation. Future additions require founder approval.

---

## 7 · THE 180 KB CONTRACT

**180 KB is a V1 PERFORMANCE GUARD. IT IS NOT A CORPUS CEILING.**

No otherwise eligible record may be omitted, truncated or suppressed merely to satisfy
the limit. If the complete governed corpus exceeds the limit, **THE BUILD FAILS** and the
architecture is reconsidered. The corpus is never silently reduced.

---

## 8 · GUARD SUITE

| # | Guard |
|---|---|
| G1 | Allowlist: every `route` is a URL present in `sitemap.xml` |
| G2 | Zero `-preview.html` and zero `supplier-preview-system/` anywhere in the index |
| G3 | No retired noindex Discovery, no legacy orphan |
| G4 | Universe sha256 byte-identical across the build; recorded in the envelope |
| G5 | No forbidden field present |
| G6 | Every product carries its literal tier; none upgraded or dropped |
| G7 | A `price` key exists only where `priceSafeForMatching === true` and the currency is EUR (A2) |
| G7c | Checked independently of the builder's rule: no product `price` comes from a non-EUR record, and every supplier `priceRange` is exactly the min/max of that supplier's EUR prices (A2) |
| G8 | **No imagery/asset/image-URL field in the index, and no runtime path that could render product or supplier imagery** |
| G9 | `noPublishedIrishRoute` caveat present on every affected product and supplier |
| G10 | **Amended by A4 (10 Nov 2026):** G10a compressed (gzip-9) <= 40 KB; G10b uncompressed <= 256 KB; G10c <= 1,100 searchable records. Performance guards; no record dropped to achieve any of them. (Was: index <= 180 KB.) |
| G11 | No term in URL, history, storage or any network call |
| G11b | No term reaches `dataLayer`, GTM or any analytics call |
| G12 | Every route resolves to a file that exists |
| G16 | Published guide pages (17 Oct 2026, SEO Phase 2): an explicit allowlist (`GUIDE_PAGES`: market pricing guide, the three founder-approved text-only maker guides of 26 Oct 2026, and the Garden Offices in Ireland guide, added 11 Nov 2026) enters as a **possibility-shape record, no new type**, title and standfirst from the page's own `<title>` and meta description only. Refuses a guide not in `sitemap.xml` or marked noindex. Same precedent as the G15 supplier information pages |
| G13 | Catch-all: nothing outside the four declared types and their declared fields. **RUNS LAST**, so every specific guard stays independently fireable |

### Hostile leak tests — knowing the hidden name must not reveal it

| # | Test | Expected |
|---|---|---|
| H1 | exact private-preview organisation names (Auroom Wellness, Capsule Castle, Escapod, …) | zero records |
| H2 | retired-Discovery concepts: Artist Studio, Garden Power, Potential Asset, Room to Grow, Start Something | zero |
| H3 | `LOOK AGAIN — Hidden Cars` (noindex WITH real content) | zero |
| H4 | recognition-pool-only organisations (Steeltech Sheds, Posh Sheds NI, Quinn Offsite, Luxury Garden Studios) | zero |
| H5 | literal filenames and paths (`auroom-wellness-preview.html`, `supplier-preview-system/`, `your-plot.html`) | zero |

H1–H5 run against the full 106-preview set, not samples. Every guard must be
demonstrated capable of failing before the build is trusted.

---

## 9 · THE GLOBAL RAIL

### B-1 · Approved order

```
PLOTNUA MARK
    ↓
SEARCH          higher-frequency navigation control
    ↓
INFO
```

The existing info-popover collision is NOT accepted. Measured in a real browser before
this contract was frozen:

| width | mark | info | info 44px hit | popover when open | collision |
|---|---|---|---|---|---|
| 1440x900 | top 22, 46px | top 92, 22px | 81 → **125** | **124** → 355 | **1px overlap** |
| 375x812 | top 16, 40px | top 80, 20px | 68 → **112** | **108** → 325 | **4px overlap** |

There is no vertical room beneath the information control. The popover is re-anchored as
part of this work, and final geometry is verified in a real browser at **1440 / 1024 /
390** with no overlap, no clipping and no horizontal overflow.

The stylesheet's own instruction applies: *"If the circle size changes, re-measure."*

### B-2 · First shared assets — scope-limited approval

`search.js` and `search.css` are approved as PlotNua's first shared local front-end
assets. **This approval is SPECIFIC TO SEARCH.**

Do NOT: extract existing inline CSS/JS; refactor existing pages into shared assets;
create a wider component system; alter unrelated page architecture.

Public pages receive a **bounded canonical stub** injected by
`atlas-tools/build-search-rail.py`: the rail control plus the two asset references, and
nothing else. Proofs required:

- the injected region's sha256 is identical across every page
- every byte outside the injection point is unchanged
- Discovery editorial text byte-identical
- Property Check logic untouched — no journey page is modified in V1

### Global navigation completeness

The rail appears on all applicable public surfaces **including `search.html` itself**. On
`search.html` the control renders as the active/current state rather than opening a
second redundant Search instance. **The rail must not visually disappear when the
homeowner reaches Search.**

---

## 10 · THE SEARCH SURFACE

`search.html`, public and indexable, and **static-first**: it is a useful page with
JavaScript disabled — a server-rendered explanation of what PlotNua holds, with real
links to all 13 public Discoveries. Search then enhances it.

### Search terms are local and ephemeral only

- no query string, ever — no `?q=`, no hash
- no `history.pushState` carrying a term
- no `localStorage` / `sessionStorage` / IndexedDB write
- no `fetch` / `XHR` / `sendBeacon` carrying a term
- **no `dataLayer.push` carrying raw search text** — GTM and Cookiebot are live on every
  public page, so this is a real leak path and has its own guard
- one canonical indexable URL; no per-term URL can exist

---

## 11 · EXPECTED ACCEPTANCE BEHAVIOUR

| query | required behaviour |
|---|---|
| Powersheds | 1 supplier + 3 products (€6,129 / €6,959 / €9,199), each carrying its governed tier: all HIGH_CONFIDENCE since the founder-approved Powersheds targeted update of 4 Nov 2026 recorded organisation-wide Irish availability (WITH_CAVEAT before). *Amended 11 Nov 2026.* |
| garden office | ~4 possibilities, suppliers grouped, 140 products **grouped by supplier with counts** — never flat |
| garden room under €20,000 | price intent parsed; restricted to price-safe products; surface says prices shown are the evidenced ones |
| solar battery | **0 products**; returns The House as a Power Station via the map |
| artist | **0 products** — Hutsmith Type III Cabin, the only product typed "Artist Studio / Writer's Retreat Cabin", was withdrawn by the targeted update of 16 Oct 2026 and must not reappear; returns A Home for Art (DISC-024 was merged into it, 13 Oct 2026); must NOT surface the retired Artist Studio Discovery. Native `productType` matching is proved by the garden office query. *Amended 11 Nov 2026; until then: 1 product, Hutsmith Type III Cabin, plus art possibilities.* |
| spare garden | The Borrowed Garden; must NOT return open-your-home-to-art or about |
| parking | Hidden Cars + Driveway Income; must NOT return hidden-bins or your-home-on-screen |
| https://www.sproutpod.ie/ | *Amendment A6, 12 Nov 2026.* Sprout Pod's supplier summary and its 25 products only. `harvia.com`, or any address without a published supplier, returns nothing. `saunas` returns Garden Retreat first, then the same saunas as `sauna`. |
| sauna | **Garden Retreat first.** Then only saunas from the governed wellness corpus (wellness-universe-v1.json, published through the supplier publication gate), each routed to its own entry in the Garden Retreat maker explorer (`discovery-garden-retreat.html#p-<record id>`, which the explorer opens; amended 14 Oct 2026, pre-launch corrections). Zero suppliers. Auroom and every other private preview stay invisible; the incidental features mentions still cannot answer. *Amended 14 Oct 2026 by founder decision (OGNYX public integration); until then: Garden Retreat only, zero products.* |

---

## AMENDMENT A1 · ROUTE TEMPLATES (4 November 2026)

**Authority:** founder instruction "Search index capacity — prepare for DISC-035" (4 Nov 2026), authorising a narrowly scoped SEARCH-V1 amendment for the lossless route-template optimisation.

**What changes (representation only).**
- Before, each of the 128 governed wellness products carried a per-record `route` string, `discovery-garden-retreat.html#p-<record id>`.
- That destination is now stored **once**, as a second envelope template:
  - `routes.wellness = "discovery-garden-retreat.html#p-{id}"`
  - Each wellness product names it with `"rt": "wellness"`.
  - `{id}` is the governed record id with `prod-` removed.
- `search.js` composes it exactly as the stored string read, with nothing appended.
- `routes.product` is unchanged.

**Products now carry no per-record `route`.**
- Garden Room and Additional Home products compose from `routes.product`, as before.
- Wellness products compose from `routes.wellness`.

**What does not change.**
- Every record and every field other than the route representation.
- Record order.
- Every resolved destination: all 801 records were measured byte-identical against the previous index, including all 128 wellness routes.
- The 180 KB G10 guard.
- The topic map, and every allowlist and leak guard.

**Guards (tightened, not relaxed).**
- G1, G1b and G12 judge the composed route of a templated record exactly as they judged the stored string.
- R1 refuses:
  - an envelope whose templates are not exactly `product` and `wellness`;
  - any product carrying a per-record `route`;
  - a wellness product without `"rt": "wellness"`, or a non-wellness product with it;
  - a wellness product whose composed route is not its own explorer entry, or whose entry the Garden Retreat explorer does not list.
- `prove-search-guards.py` adds C20–C22 to prove those refusals.
- `sync-discovery-makers.py` S7 and its test compose the same route.

**Effect.** The index is 183,775 → 178,193 bytes (−5,582), leaving 6,127 bytes under the 180 KB guard.

---

## AMENDMENT A2 · EURO-ONLY PRICES (6 November 2026, Stage 3D-B1; founder-approved and released to production 6 November 2026, commit 8d7e882)

**Defect.** `search.js` formats every `price` as euro (`money()`) and the price intent
("under €30,000") filters products on `price` and suppliers on `priceRange[0]`. The
index carried no currency, and for the garden-room and Additional Home corpora the
builder's rule was `priceSafeForMatching` alone, which is currency-blind. So 46
garden-room prices recorded in GBP (43) or USD (3) were shown with a euro sign and
matched euro filters, and 13 suppliers had a "from €…" range built from them. Example:
Berko Pod Systems — The Aurora Garden Room, GBP 26,000, appeared as "€26,000" in
"garden room under €30,000". The wellness corpus already applied the EUR rule
(founder currency register, 22 Oct 2026).

**Rule.** One builder predicate, `euro_price()`: price-safe **and** EUR. It decides the
product `price`, the supplier `priceRange`, and G7/G7b. G7c re-checks the result
directly against each source record's currency. No conversion, no exchange rate.

**What does not change.** Every product keeps its record, name, organisation, type,
tier and caveats, so it stays discoverable by text. Its currency and price stay in the
universe, Your Plot and the Maker Explorer, which display them correctly. EUR prices,
holds (NOOK, ECC, Rayco), ranking and the record schema are unchanged. A future
amendment could add a currency field so Search can show "£26,000"; that would extend
the closed schema and is deliberately not part of A2.

---

## AMENDMENT A3 · PUBLISHED SUPPLIER PROFILES (8 November 2026, SEO-GR5b; FOUNDER-APPROVED 8 November 2026, effective from the SEO-GR5b release)

**Gap.** Six published supplier profiles were not reachable through Search:
- The Mobile Pods
- Gardenhouse24
- Elm Landscaping
- Garden Room Ireland
- Don Modular Homes
- Superior Pergola Ireland

Four of them appeared only as unlinked supplier summaries (R2: a supplier record carries no route). The Mobile Pods and Superior Pergola were absent from Search.

**Rule.** Each profile enters through the existing G15 supplier-information mechanism.

The profiles are declared in their own list, `SUPPLIER_PROFILE_PAGES`, beside `SUPPLIER_INFO_PAGES`, for two reasons:
- `build-maker-explorer.py` G7 reads `SUPPLIER_INFO_PAGES` to keep manufacturer-information pages out of the explorers;
- the explorer's A–Z index already links four of these profiles under its own G12b (SEO-GR4).

Both lists pass through the same G15 checks:
- sitemap-listed;
- not noindex;
- `page_must_contain`;
- possibility shape;
- own route;
- `info-` prefix.

**Record shape**
- Possibility-shape record, no new type and no new field.
- Id: `info-<slug>`.
- Title: "Supplier profile: <name>". The result says plainly what it opens.
- Standfirst: one factual line. Every phrase in it is pinned to the page by `page_must_contain`.
- No topics: no synonym is added to the governed map.
- Route: the published page.

**What the record does not carry**
- price, tier or product count;
- verification state, rank or endorsement;
- any partner or referral wording.

**What does not change**
- **Supplier summaries are untouched.** All 65 `supplier` records are byte-identical, R2 still holds, and the product expansion is unchanged.
- **Indexing rules.** No product is added or removed. G7–G7e, G9, R-MATCH and the holds are unchanged.
- **The G10 size guard is not raised.** It stays at 184,320 bytes. The index is 183,946 bytes, 374 bytes under it. This includes the DISC-037 record released just before SEO-GR5b. **Capacity constraint:** the next significant addition to Search needs the size decision in §7 first.

**G15b (new).** A profile record is described, never rated. The build refuses a profile record when:
- its title does not begin "Supplier profile: ";
- its title or standfirst carries a currency or percentage sign;
- its standfirst carries a figure;
- either field carries endorsement or commercial wording: recommend, verified, approved, partner, endorse, best, top, trusted, featured, preferred, commission, referral, discount, saving, offer, rated or award.

**G2, narrowed exactly.** Two published profiles share a slug with a private, noindex preview:
- `suppliers/elm-landscaping.html` and `elm-landscaping-preview.html`;
- `suppliers/garden-room-ireland.html` and `garden-room-ireland-preview.html`.

How the narrowed G2 works:
1. G2's slug test now excuses each G15 route **once**, as the exact JSON `"route":"<route>"`. G15 has already proved that route sitemap-listed and indexable.
2. Any other appearance of a preview slug still refuses the build. This includes a second copy of the same route.
3. The `-preview.html` and template checks are unchanged.

Capability:
- the baseline builds;
- a duplicate profile route, a slug in a product field, a preview filename, and a non-exact profile route are each refused;
- the three G15b sabotages are each refused.

The evidence file is `guard-capability.txt`.

**Price intent.** A published supplier profile carries no price. So a search with a price clause ("under €N") never shows one, exactly as an unpriced product is excluded.

- **Why.** Without this rule, "garden room under €15,000" excluded Don Modular Homes from Suppliers on price and then offered its profile under Possibilities. This was caught by the functional suite.
- **Effect.** Priced searches return exactly what production returned. Discoveries and guides are unaffected.

**Ordering.** In `search.js`, at **equal** relevance, a result whose route is a published supplier profile (`suppliers/…`) follows every other result of its group.

- **Why.** Ties were broken by title alone, so "Supplier profile: …" sorted ahead of Discoveries titled "The …". For example, "outdoor room" would have opened on Gardenhouse24.
- **Effect.** A higher score still wins outright. No tier, price or Atlas signal takes part. Every result that existed before keeps exactly its previous membership and order: measured across 74 queries.

---

## 12 · OUT OF SCOPE FOR V1

- product deep-links depend on JC-2 / JC-4; product results route to supplier-grouped
  Results, not to an invented product URL
- `P12_no_new_css` remains open, unrelated, and is NOT fixed opportunistically
- Powersheds is CLOSED and untouched
- G5 is not started

---

## AMENDMENT A4 · PERFORMANCE BUDGET (10 November 2026; FOUNDER-APPROVED 10 November 2026, Stage 7 Option B; not yet released)

**Why.** G10 measured the raw, uncompressed index against 180 KB. By 10 November the index stood at 184,294 bytes, 26 bytes under it, so the next Discovery (DISC-038, a ~350-byte record) could not be indexed. The Stage 7 investigation found that the raw size is not what a visitor pays:
- GitHub Pages serves the index gzip-compressed: **28,582 bytes** measured live (`content-encoding: gzip`).
- Parsing it costs under 4 ms even at 6x CPU throttling.
- Per-keystroke search time scales with the **number of records**, not bytes. 87% of the index is the 715 products; Discoveries are 6%.

**Rule.** G10 becomes three guards on what the phone actually pays. Each refuses the build:

| Guard | Limit | Measures |
|---|---|---|
| G10a | gzip level 9, mtime 0 (deterministic) ≤ 40 KB (40,960 bytes) | The download |
| G10b | uncompressed ≤ 256 KB (262,144 bytes) | Parse time and memory |
| G10c | ≤ 1,100 searchable records (all types) | Per-keystroke scan time |

**§7 is unchanged in principle.** These are performance guards, not a corpus ceiling. No eligible record may be omitted, truncated or suppressed to fit any of them. If the complete governed corpus exceeds one, THE BUILD FAILS and the architecture is reconsidered. Every refusal says so.

**Early warnings (A4).** Each prints a warning and never fails a build. When any is reached, an architecture review (Option C: a small core index loaded first, with products in a separate shard) is due:
1. 1,000 searchable records (`build-search-index.py`);
2. 36 KB compressed (`build-search-index.py`);
3. 95th-percentile query time above 100 ms at 6x CPU throttling, taking the worse of warmed runs and the cold first pass (`atlas-tools/bench-search-mobile.py`, local tool).

**What does not change.**
- `search.js`, the index format, every record, field, order, route, ranking and result.
- Verified: a rebuild under A4 produces all 822 records identical to the committed index (only `generated` and `sourceCommit` differ).
- Across 971 queries, results are identical to the pre-A4 index.

**Proved capable.** `prove-search-guards.py`:
- C13a–C13c each lower one limit in the builder and must be refused by that guard alone;
- C13d checks the refusal states it is not a corpus ceiling;
- C13e, C13f and C13g grow the real corpus past exactly one limit (records, raw size, compressed size), each refused by its own guard.

The harness also creates sub-folders for sitemap pages before copying them. It had crashed on `plotart/` pages, a pre-existing defect.

**Measured at approval (10 Nov 2026).**

| Index | G10a | G10b | G10c |
|---|---|---|---|
| Live index | 27,194 B (26.6 KB) | 184,294 B | 822 records |
| With DISC-038 | 27,299 B (26.7 KB) | 184,640 B | 823 records |

Mobile emulation, 390 × 844, 6x CPU, 39 queries including the 1–2 character prefixes:
- Warm: median 11.5 ms, p95 18.8 ms.
- Cold first pass: median 11.7 ms, p95 17.7 ms, max 93.7 ms.
- Slowest query: "garden room under €30,000", median 60.6 ms.

No early warning is reached.

**Capacity gained.** About 277 more records before G10c, or about 76 KB raw before G10b, whichever comes first.

## AMENDMENT A5 · STARTING PRICES (10 November 2026; founder brief "Correct the display of starting prices in PlotNua site-search results"; NOT YET RELEASED)

**Defect.** A product row showed every price as a bare figure, "€X". For a product whose Atlas price is recorded as a starting price (Atlas Price Type "Starting From"), that read as a fixed price. For example, Arctic Wellness Ember showed "€11,550"; its supplier publishes €11,550 to €11,800.

**Rule.**
- A product record may carry `"pf": 1` only when both are true:
  - it shows a price; and
  - its source corpus records that price's type as exactly "Starting From". The source fields are: garden-room `priceType`; Additional Home `price.priceType`; wellness `price.type`.
- `search.js` then reads the row "From €X".
- Nothing is inferred. A Standard Price or Sale Price stays "€X". This includes a garden-room Standard Price that is the floor of a published range (`priceIsRangeFloor`).
- Supplier ranges ("· from €X") are unchanged.

**Guard G7f.** The builder refuses:
- a "pf" mark without a shown price;
- a "pf" mark on a price whose source type is not "Starting From"; and
- a shown "Starting From" price without the mark.

The source corpora are read directly for this check. Capability cases C9d (a "From" inferred for a fixed price) and C9e (an explicit starting price losing its "From") are in `atlas-tools/prove-search-guards.py`.

**Effect at introduction:**
- 90 of 346 shown prices carried "From" at release (51 wellness, 39 garden-room). After the Loghouse Starting From refresh (founder approval 10 Nov 2026; 8 Atlas records) it is 98: 51 wellness and 47 garden-room. No Additional Home product shows a price figure in Search today, so none is marked; the rule applies to them unchanged if one does.
- No record is added or removed, and no other field changes.
- Index: 187,104 bytes raw, 27.0 KB gzip-9, 831 records (rebuilt on main fbd272b). All are within the A4 guards.

**Shared asset.** `search.js` changes in one expression, `productItem()` ("From" plus a non-breaking space before the figure, so the two never wrap apart). Its frozen hash is re-stamped in `atlas-tools/prove-landmarks.mjs` and in the freeze record. `search.css` is unchanged.

## AMENDMENT A6 · SUPPLIER RECOGNITION (12 November 2026; founder-approved for implementation and local testing only; NOT RELEASED)

**Authority.** Founder decision, 12 Nov 2026: the unified A6 proposal (consolidating the garden-room and garden-sauna supplier audits of the same day) is approved for implementation and local testing. Production publication needs separate approval.

**Defect.** Search could not recognise a supplier from its web address, or from its trading name written as one word, and it mishandled accents and plurals:
- 0 of 37 garden-room and 0 of every sauna domain/`www.`/`https://` query answered;
- `timberin.com` matched only through "com" inside "combination";
- `normalise()` deleted accented letters, so "ÖÖD" returned 713 products and "Möön" 627;
- `saunas` and `hot tubs` returned no products.

**Rule.**
1. **Aliases (envelope only).** The index gains `aliases: {k, t}`. `k` maps a key to an index into `t`; each `t` entry is `{o: organisation}` plus, where one exists, `p`: the ids of published G15/G16 page records about that organisation.
   - Keys are hosts and compact names (letters and digits only, at least 4 characters).
   - **Sources, and no others:** Atlas `Organisations.Website`; Image Permission Outreach `Permitted Domain` on rows whose outcome is founder-confirmed and granted; the founder-approved `tradingNames` and `excludedNames` lines. All live in `atlas-tools/search-supplier-aliases.json`, written by `atlas-tools/build-search-aliases.py` from a read-only Atlas read.
   - **Retail-channel aliases are deferred** (Summerhouse24 → Hansa24 Group) and refused by the builder.
2. **Eligibility is unchanged (§3).** An alias is emitted only for an organisation that already has an emitted product or supplier record, or a published G15/G16 page. No alias creates a record, a supplier card or a route. S1–S5, G15 and G16 still decide publication.
3. **Prohibited sources (§4).** A private-preview-only or recognition-pool-only organisation has no alias, by host or by name.
4. **Query recognition (`search.js`).** A query that starts with `http(s)://` or `www.`, or is a bare `label.tld`, is reduced to its host (scheme, `www.`, path, query and port removed; parent domains tried in turn).
   - A known host answers with that organisation's existing records only.
   - An unknown host answers nothing.
   - A compact trading name adds its organisation's records only when ordinary matching did not already find that organisation, so every query that already found its supplier is untouched.
5. **Normalisation (§6 clarified).** Two deterministic rules are added. Neither is fuzzy matching, edit distance or AI/API expansion; the topic map is unchanged and the founder remains the approval authority for any further rule.
   - Accent folding in `normalise()` (NFD, combining marks removed), applied to query and record alike.
   - One plural rule: a term of four or more letters ending in a single `s` (not `-ss`, `-us`, `-is`) may also match its singular. It is **product-gated**: tried only when ordinary matching found no product and no supplier, and it adds products and suppliers only.
6. **Relevance (§5).** Unchanged. Alias answers carry only the organisation's own records; ordering among them follows §5. No tier, price or Atlas signal participates.
7. **Performance.** Each record's normalised text is computed once per loaded index and held as a non-enumerable property, so it never reaches JSON, the renderer or any serialised result.
8. **Exact supplier name (A6 r2, 12 Nov 2026, before release).** When the query is a published supplier's name, the whole leading word(s) of it ("ÖÖD" for "ÖÖD House"), or a recognised trading name, **and** that name is distinctive (no other supplier's product or supplier record matches every query term at the start of a word), a Possibility that matches the query only inside another word is not shown. Example: "ood" inside "flood", "food" and "wood".
   - Untouched: the supplier's own records; its own G15/G16 pages; governed topic-map entries; any Possibility matching at the start of a word.
   - Products and suppliers are never removed by this rule. No score changes and no new ranking signal. It is a filter, not fuzzy matching.
   - Ordinary words do not qualify ("home", "garden" and "car" each appear at the start of words in other suppliers' records).
   - "All" qualifies, because "All In One Cabins" is the only supplier with a word starting "all". It drops guides that contain "all" only inside "wall", "install" or "small".
9. **Known limit, left unchanged.** "cars" answers exactly as "car" does in production, because ordinary matching is substring matching and "car" occurs inside Carin, CARLOW, Carroz and Carpentry. A whole-word singular would fix it but removes legitimate plural answers ("pools" → Poolhouse, "gardens" → GardenDreams and Gardenhouse24, "offices" → ZomeOffice). A start-of-word singular does not fix it. The approved plural rule is therefore unchanged.

**Guards (builder; each refuses the build).**
- **A6a** every host is re-derived from the Atlas value itself and must be a hostname; a permitted domain must be a bare hostname on a founder-confirmed grant.
- **A6b** no key may resolve to two organisations. A collision is resolved in `excludedNames`, never by dropping a record. (On its first run A6b caught "(Garden Rooms)" in Elm Landscaping's record colliding with GardenRooms.ie.)
- **A6c** a hand-declared trading name must name an organisation with published records and carry evidence.
- **A6d** no key under four characters.
- **A6e** no alias may name an organisation without published records or a recognition-pool-only organisation.
- The A6 block also refuses a retail-channel section, and a `PAGE_ORG` entry naming a page that is not published.
- G10a–c are unchanged; no limit is raised. G13 lists `aliases` as a declared envelope key.

**Proved capable.** `prove-search-guards.py` C23–C30, each refused by its own guard (40 of 40 guards capable). `prove-search-acceptance.mjs`:
- **Part D** D1–D8: garden-room and sauna addresses and trading names; addresses of unpublished suppliers return nothing; unknown and look-alike domains; accents; plurals including the product gate; every alias key in every address form; no alias without published records.
- **D9–D9d (r2):** "ÖÖD", "OOD" and "ÖÖD House" lead with ÖÖD House and show no unrelated guide; the rule removes no product or supplier; "home" is not treated as a supplier name; Shomera keeps its own guide. Each was shown capable by sabotage: rule removed → D9 fails; distinctiveness removed → D9c fails; rule widened to products → D1, D7 and D9b fail.
- **H-A6:** 180 addresses of preview-only and pool-only organisations reveal nothing.

**Targeted updates keep aliases current.** `publish-targeted-update.py` refreshes the updated organisation's alias entry (name, Website) from the same Atlas read (`build-search-aliases.py --merge-snapshot`). Its boundary check refuses a change to any other organisation's alias entry, to the hand sections, or to any alias outside the updated organisation.

**Effect at introduction (main a737684).**
- Records: 833, every one byte-identical to the previous index.
- Aliases: 169 keys for 76 organisations; 179 Atlas organisations have no published record and get none.
- Index: 187,427 → 193,121 bytes raw; 27,711 → 29,462 bytes gzip-9. All within the A4 guards.
- Regression over 2,244 queries: 2,203 identical; 41 changed, all intended (7 accent corrections; 34 plural queries that previously returned no product or supplier).

**Effect after r2 (main 0cc5ed3).**
- Records: 833, every one byte-identical.
- Regression over 2,245 queries: 2,202 identical; 43 changed. These are:
  - the 41 above;
  - "OOD", which now leads with ÖÖD House;
  - "All", which loses 7 guides matching only inside words.
- No query that already returned products or suppliers loses one, except the accent corrections.

**Effect after r3 (main cf5f106, after the Garden Saunas in Ireland release).** A6 was rebuilt, not hand-merged:
- `search-index-v1.json` and the alias file were regenerated from current governed sources: the Atlas read-only export of 12 Nov 2026 ~12:40, with no material change since r2.
- Records: 832, every one byte-identical to production.
- Aliases are unchanged (169 keys → 76 organisations).
- The withdrawn Irish Sauna Company models are not restored. `irishsaunacompany.com` answers with The Clare and The Inis Mor only.
- Regression over 2,248 queries: 2,203 identical; 45 changed, all of the kinds listed above. Products or suppliers lost: accent corrections only.
- Proof D6 was restated: production now ranks the new Garden Saunas in Ireland guide first for "saunas". A6 does not reorder Possibilities, and the A6 promise it tests is unchanged.

**Shared asset.** `search.js` is re-stamped in `atlas-tools/prove-landmarks.mjs` and the freeze record. `search.css` is unchanged.

## TARGETED-UPDATE RE-FREEZES

The universe pin above is moved only by a targeted publication whose boundary check proved every other record byte-identical.
- 2026-10-16 · re-frozen to `19f846ef2522a3adfe37e1d34516d3290bffc6915da9b7dfaa5206fa26f92e5a` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261016-112927-hutsmith.md); only the targeted records differ.
- 2026-10-16 · re-frozen to `5d134a4e25f7946d69df1bf63b9306e84d012e50f6c117f7c6ce89b6b25cbc3c` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261016-112952-elm-landscaping-garden-rooms.md); only the targeted records differ.
- 2026-10-16 · re-frozen to `b7b864535d43c47517b138ad3f97951cb476b5fa93651e7115b5dc89aae7d5f5` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261016-113042-don-modular-homes.md); only the targeted records differ.
- 2026-10-16 · re-frozen to `3821b6487d670f086d75a67125ae02d707464b485dedb62b03470bb5ecb611cf` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261016-113120-garden-room-ireland.md); only the targeted records differ.
- 2026-10-16 · re-frozen to `dcabb199b183b01d2763ab3d2f6db61d9e488300fe1726a0922c6279b23cae10` for the Authorised Imagery Integration (founder approval to build, 16 Oct 2026). Boundary check: the universe differs from GitHub main only in the `imagery`/`imagerySet` keys of two products (Garden Room Ireland QC6, Don Modular Garden Room), written by .github/scripts/apply_authorised_imagery.py; ids, order, header and every matching field are byte-identical. The search index carries no imagery (contract §2) and is unchanged.
- 2026-10-19 · re-frozen to `b45a9a84990384308332e40110bbdb55135b3b907d920a9f4d3933a17c1a4bcf` for the founder-approved SAFETY HOLD of five Premium Log House products (atlas-tools/safety-hold-products.json, applied by atlas-tools/apply-safety-hold.py; Blocker G). Not a supplier update: the five held records leave the universe and their search records go with them; every other record is byte-identical (checked in the same change).
- 2026-10-20 · re-frozen to `3da2c97699ba18cf38ca6eb1285c8157cd264c19bca6c4db294cd16d6f25ca83` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261020-091711-outdoor-living-modpod.md); only the targeted records differ.

Shomera guide publication, 26 October 2026: one informational possibility record (`poss-shomera-garden-rooms`), title/description from its indexable sitemap-listed page. No supplier/product eligibility or Search ranking change. Public-page count deliberately moves from 24 to 25.
- 2026-10-26 · re-frozen to `7f70a52b0650966f929bee3d54f91be6a5f42f2d63bd69b25182024109c8f0ba` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261026-202742-pineca-ireland.md); only the targeted records differ.
- 2026-10-26 · re-frozen to `6d003a920ce6cbbaf67b51f5980112319555c87f4ea3f331d72bd3e67ddadbd5` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261026-205704-gardenhouse24-ireland.md); only the targeted records differ.
- 2026-10-30 · re-frozen to `c5e5a65048c2167d71c31414f2d257bef799a22caed475fe2b77a257a58a72e8` for the DISC-008 Powersheds medium correction (founder decision, 30 Oct 2026, Option B: the two CGI Powersheds assets are labelled Visualisation on every surface). Boundary check: the universe differs from production main (1aff5ee) only in the `imagery` key of three Powersheds products (12x12 and 14x14 Apex Classic Log Cabin, 16x12 Apex Log Cabin), whose alt text now begins "Visualisation:", written by .github/scripts/apply_authorised_imagery.py; ids, order, header and every matching field are byte-identical. The search index carries no imagery (contract §2): its records are byte-identical; only its source metadata (sourceCommit, sourceUniverseSha256, generated) moved.
- 2026-11-04 · re-frozen to `c4713085a4359c8fab2cc5ac6f8ddec30e17268c01e20b5bf3554df020153556` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261104-142554-powersheds.md); only the targeted records differ.
- 2026-11-06 · re-frozen to `565971774b00f4187fc72ab84f158052eace8c96650437edca0274147ebda0f3` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261106-091826-price-recheck-dates.md); only the targeted records differ.
- 2026-11-06 · re-frozen to `51394c35c3daec5141a522bf35f731957164cb5d0d810f730cc9f8a77d4a9c22` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261106-100702-price-recheck-dates.md); only the targeted records differ.
- 2026-11-06 · re-frozen to `52a51130414f05dbf6a547d014d2d08ee213615ee5b080a649ac2ee203626e15` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261106-151018-nook-prefab-espacio-nook.md); only the targeted records differ.
- 2026-11-06 · re-frozen to `1be874ad227c76a2b6af900d12bedd4177bc9ddac5549eec196586a435885c96` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261106-201546-east-coast-carpentry.md); only the targeted records differ.
- 2026-11-06 · re-frozen to `030338cbe12d237a2227ec521bf3e4d52c54ef8787fbc2966bc232cbb574da36` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261106-222549-presentation-hold.md); only the targeted records differ.
- 2026-11-06 · re-frozen to `238b26cbf2f56be9100408b6b25ce581623cc2fe71fa58f05ccef873fb907095` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261106-222617-price-recheck-dates.md); only the targeted records differ.
- 2026-11-07 · re-frozen to `7eef16c3621630dde3c19d17429faffcff0d1fd47c4dec4ddb78d6f6aa5f6ff1` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261107-085522-price-refresh.md); only the targeted records differ.
- 2026-11-07 · re-frozen to `33ea49448343e8a93c66d76a0fea825c96a2794f2def02766bb09a98580b19d8` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261107-095121-presentation-hold.md); only the targeted records differ.
- 2026-11-07 · re-frozen to `b09fc66f8f9647ea31daea493ea013a5cd60a8f667409e2e2df7d3ff58d0854f` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261107-131108-methodology-correction.md); only the targeted records differ.
- 2026-11-07 · re-frozen to `3b889907eec3a2fd7ffb3aee8f9eac6c02c2bdb7ab8b472933042086a7f9dc78` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261107-175815-eligibility-r-match.md); only the targeted records differ.
- 2026-11-10 · re-frozen to `6a30d341d91a03adfd9bcde9838749501cdb11691230d61101d4fc1500aa9ee7` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261110-124337-price-refresh.md); only the targeted records differ.
- 2026-11-11 · re-frozen to `f6e10315b4c3d0055e61a70b6aa7571f31793d79f69eb823885a63e7bcb60c66` after the M8C Stage 1 privacy corrections (540d3e6, 10 Nov 2026), which removed a supplier contact name and private e-mail identifiers from `features.irishAvailability.text` and `features.installationModel.text` on seven ÖÖD House products by direct edit, so the pin was not moved at the time (investigation 11 Nov 2026; founder approval 11 Nov 2026). Neither field is carried by the search index: its 832 records are byte-identical; only its source metadata (sourceCommit, sourceUniverseSha256, generated) moved. From this release the Image rights gate runs `build-search-index.py --check`, so a universe change without a re-freeze now fails the release.
- 2026-11-11 · G16 amended (founder approval, 11 Nov 2026): `garden-offices-ireland.html` added to `GUIDE_PAGES` as `poss-garden-offices-ireland`, same possibility shape and same title/meta-description rule, no new type and no ranking change; one governed topic entry, 'home office' -> the guide, possibility scope only. Index 832 -> 833 records (37 possibilities); every existing record byte-identical; 27.1 KB gzip of the 40 KB guard. Universe pin unchanged.
- 2026-11-11 · re-frozen to `1f31730f57412157e2d819447167cb786dcb93c7d64c4578148f7be5dc96f74e` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261111-190927-presentation-hold.md); only the targeted records differ.
- 2026-11-13 · re-frozen to `ce008ade2fd2842501f36297b667692d54870ef3144b98b3c46d26bcf5c4195d` by atlas-tools/publish-targeted-update.py for a targeted update (atlas-tools/targeted-updates/20261113-090938-modern-garden-rooms.md); only the targeted records differ.
