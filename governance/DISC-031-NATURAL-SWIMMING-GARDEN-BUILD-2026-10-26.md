# DISC-031 · The Natural Swimming Garden: build record

**Founder build instruction:** 26 October 2026 ("BUILD THE COMPLETE PREMIUM DISCOVERY PAGE").
**Page:** `discovery-natural-swimming-garden.html`, Premium from the start (`premium_pages.py`).
**Status:** local release candidate. Not pushed, not deployed.

## Sources of truth

| What | Source |
|---|---|
| Copy | `00-DISC-031-COMPLETE-EDITORIAL-COPY.md` (claims A1–A13; revised A7, A8, A9, A12), with founder edits 1 and 2 |
| Three approaches | Founder decision, 26 Oct 2026 (plant-led primary; hybrid; compact, availability in the Republic not verified) |
| Prohibited claims | Stage 2 evidence pack §9 (25 items) |
| Images | The four founder masters, verified by SHA-256 on the founder's Mac (HOW-IT-WORKS **V2**; the first version is superseded and not used) |

## Images

The four masters are kept on the founder's Mac, unchanged. The repository carries 13 web encodings in `assets/disc031/img/`:
- 960 and 1536 px WebP, plus a 1536 px JPEG fallback, for Before, Reveal and Experience;
- 1536 px WebP and JPEG for the diagram;
- a 960 px JPEG Library card;
- a 1200 × 630 social preview cropped from Reveal.

Every image on the page is labelled **"AI-generated illustration"**, which is the register's approved label for `AI_ILLUSTRATION`.

**Provenance: the one open item.** The build instruction gave the masters but not their tool, prompts or reference history. So the 13 records are prepared as an **unsigned draft**: `governance/DISC-031-PROVENANCE-DECLARATION-DRAFT-2026-10-26.json`.
- It uses the founder-attested form (`PN-FDR-2026-10-26-DISC031`, pinned by SHA-256 in `validate-image-provenance.js`).
- It is applied with `atlas-tools/declare-disc031-provenance.py`.
- **Until it is signed, gate step "Every locally hosted image must be declared or enumerated" fails (P1),** by design.
- A simulated signature in a scratch copy passes all 15 provenance checks and the 68-mutation capability proof.

## Rule 6

**The plate:** the Before illustration, shown whole, with the PLOTNUA DISCOVERY cue "Room for a swimming pond?" and three observations at fixed anchors (viewBox 1536 × 1024):

| # | Observation | Anchor |
|---|---|---|
| 01 | Available ground | lawn (900, 590) |
| 02 | Existing landscape | hedge line (1362, 470) |
| 03 | Practical feasibility | lawn edge (640, 712) |

**Two geometries:**
- **Desktop** carries short wording on the plate.
- **From 899 px down,** the cue is in larger type and each observation is its number at the same anchor.

**On every width,** the founder's full observation sentences sit directly below the plate, together with the statement that PlotNua has not assessed this or any real property.

## Integration

| Area | Change |
|---|---|
| **Registries** | `premium_pages.py`, `pn_header.py` (IDENTITY_PAGES), `build-identity-stage1.py` (PAGES, DISC); `build-search-rail.py` EXPECTED_PAGES 25 → 26 (after rebase) |
| **Generated blocks** | Identity head, header and search rail inserted by the builders themselves |
| **Sitemap and search** | `sitemap.xml` entry (lastmod 2026-10-26); `search-index-v1.json` rebuilt (rebuilt on the rebased tree: possibility 18, product 697, supplier 64, journey 9; 179,710 bytes against the 180 KB guard) |
| **Discovery Library** | One new card (Garden), image row in `atlas-tools/discovery-library-images.json` |
| **Related** | Garden Retreat (DISC-001), Above and Beyond, Living in the Garden. **DISC-015 Underground Swimming Pool has no published page,** so it is not linked |
| **SEO** | Unique title, description, canonical, Open Graph and Twitter, JSON-LD (WebPage, BreadcrumbList, WebSite, Organization). **No price, product or supplier structured data** |

## Not changed

- No other Discovery page.
- The homepage.
- The shared stylesheets.
- No supplier, Atlas or image-rights record.
- No lead form.

## Recorded, not fixed (outside scope)

1. **`build-search-rail.py`, when run in apply mode, moves the header bar below the search rail on all 22 existing pages.** It predates the global header v2. Its output was discarded on every page but this one; the rail on this page sits exactly where the identity builder expects it.
2. **`discoveries.html` meta description says "10 ideas".** The Library already showed 12 before this card.

## Rebase and acceptance (26 Oct 2026, evening)

**Rebased** onto `origin/main` `cc34046`. Since the morning build, 20 or more commits had landed: maker guides, price corrections and the Shomera guide.
- **Conflicts:**
  - `build-search-rail.py`: EXPECTED_PAGES now **26**.
  - `search-index-v1.json`: rebuilt from main's version by its own builder.

**Gate (`image-rights-gate.yml`, 26 steps run locally):** **25 pass.**
- **Step 05 fails (P1, undeclared DISC-031 images).** This is by design, until the provenance declaration is signed.

**Other workflows run:**
- `atlas-figures-check` and `garden-maker-pages`: pass.
- `garden-room-prices-freshness`, step "Cost evidence reproduces…": **fails identically on unmodified `origin/main`.** It's pre-existing and unrelated.

**Browser checks** (Chromium; 1440, 820, 390 and 360 px):
- all four DISC-031 images load;
- no horizontal page overflow;
- the Before/Possible range works: keyboard Home/End/arrows, and pointer;
- the full-size diagram dialog opens (1536 px image) and closes with Esc;
- the diagram stays readable on phones (swipe area plus full size plus text version);
- no missing local references;
- one JSON-LD block parses;
- "wild" appears once (the question);
- no €, £, partner or banned phrases.

**Not linked: DISC-015 Underground Swimming Pool.** It has no published page, so it isn't linked.

## Founder review and signature (26 Oct 2026, late evening)

**Diagram wording**
- **Caption added** under the diagram: "A simplified illustration: clear water still needs regular water-quality testing, and maintenance varies with the design."
- **The approved image is unchanged.**

**Diagram spacing**
- **The V2 diagram is now shown as two exact crops of the master** (rows 0–547 and 548–1023; no pixel changed).
- **The gap between the panels:** 28 px on phones, 32 px on tablet and desktop.
- **The full-size view** still shows the whole diagram (JPEG).
- **The unused full WebP** was removed. **16 encodings.**

**Provenance**
- **Completed from the OpenAI C2PA content credentials in the four masters:**
  - ChatGPT, `gpt-image`, *trainedAlgorithmicMedia*;
  - no ingredients recorded;
  - content hashes match.
- **Signed by the founder, Colin MacAulay, on 26 Oct 2026, with his statement:**
  - no real photographs, supplier images or third-party web images were used;
  - all four masters were created with ChatGPT image generation;
  - the Before illustration was the reference for the Reveal.
- **Reference disclosure stays UNCERTAIN.** The credentials don't record conversation inputs, so the founder's statement can't be independently verified.
- **Resemblance review:** accepted.
- **Register:** 16 records applied under `PN-FDR-2026-10-26-DISC031`; provenance guard **15/15**.

**Release checks**
- The standard list now expects **27 identity pages**.
- **The historical SEO Phase 1 builder check is retired.** It refuses on production main since `bac3ab8`.
- **The page is proved by `atlas-tools/prove-disc031-page.py`** (S1–S10).
