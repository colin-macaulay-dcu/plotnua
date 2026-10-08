# PLOTNUA SEARCH V1 · FROZEN CONTRACT

**Status:** APPROVED FOR BUILD · 8 October 2026 · founder decisions B-1 to B-4 and the
additional decisions recorded below.
**Baseline commit:** `1bf7d4b`
**Baseline universe:** `garden-room-recommendation-universe-v1.json`
sha256 `db4ecb7ff99ebaa0e2d88b89ce395f0bcb78c5a2750630aefbc3669413ff82db`

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
```

Four record types. No field outside these lists may be emitted.

| type | fields |
|---|---|
| `possibility` | id type title standfirst topics[] route |
| `product` | id type name organisation productType price? priceBasis? tier caveats[] route |
| `supplier` | id type name productCount priceRange? tiersPresent[] caveats[] route |
| `journey` | id type title possibilityId route |

**Forbidden, and guarded:** `qualification`, `priceEvidence`, `priceEvidenceRef`,
`evidenceSignals`, `hardBlockers`, `organisationEvidence`, `features`, `imagery`, any
score, any rank, any Airtable record id.

`tier` carries the literal `HIGH_CONFIDENCE` / `WITH_CAVEAT` string. Never derived,
never rounded, never upgraded.

`price` is emitted **only** where `priceSafeForMatching === true`. The other products
carry no `price` key at all, so there is nothing to filter on or display wrongly.

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
| `sauna` | Garden Retreat | **POSSIBILITY ONLY** — see §2 features |
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
| G7 | A `price` key exists only where `priceSafeForMatching === true` |
| G8 | **No imagery/asset/image-URL field in the index, and no runtime path that could render product or supplier imagery** |
| G9 | `noPublishedIrishRoute` caveat present on every affected product and supplier |
| G10 | Index <= 180 KB as a performance guard; no record dropped to achieve it |
| G11 | No term in URL, history, storage or any network call |
| G11b | No term reaches `dataLayer`, GTM or any analytics call |
| G12 | Every route resolves to a file that exists |
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
| Powersheds | 1 supplier + 3 products (€6,129 / €6,959 / €9,199, all WITH_CAVEAT) |
| garden office | ~4 possibilities, suppliers grouped, 140 products **grouped by supplier with counts** — never flat |
| garden room under €20,000 | price intent parsed; restricted to price-safe products; surface says prices shown are the evidenced ones |
| solar battery | **0 products**; returns The House as a Power Station via the map |
| artist | 1 product — Hutsmith Type III Cabin, on `productType` — plus art possibilities; must NOT surface the retired Artist Studio Discovery |
| spare garden | The Borrowed Garden; must NOT return open-your-home-to-art or about |
| parking | Hidden Cars + Driveway Income; must NOT return hidden-bins or your-home-on-screen |
| sauna | **Garden Retreat only.** Zero products, zero suppliers, helpful zero-state. Auroom and every other private preview stay invisible. |

---

## 12 · OUT OF SCOPE FOR V1

- product deep-links depend on JC-2 / JC-4; product results route to supplier-grouped
  Results, not to an invented product URL
- `P12_no_new_css` remains open, unrelated, and is NOT fixed opportunistically
- Powersheds is CLOSED and untouched
- G5 is not started
