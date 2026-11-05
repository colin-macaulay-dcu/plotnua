# DISC-036 · Extend the House: development build record

**5 November 2026.** Development build on the local branch `dev/disc036-extend-the-house`, based on production `104f499`.
- **Authorisation:** PLOTNUA-BUILD-001 Stage 1, founder development authorisation, private preview only.
- **Status:** not pushed, not merged and not deployed. Production needs the founder's explicit approval.

## What the page is

A six-chapter Discovery in the existing design system (category **Space**):
1. the possibility;
2. six types;
3. planning and regulations;
4. who does what;
5. the parts of the cost;
6. other ways to get the room.

It also carries a browser-only **extension brief**.

## Hero (founder image pair, integrated 5 Nov 2026)

**Authorisation:** DISC-036 Final Hero Integration and Private Preview (founder, private preview only, €0).

The interim PlotNua drawing is retired. The hero is now the founder's Before / Possible pair in the shared `pn-compare` component, opening at 100 % BEFORE.
- **Masters (kept unchanged):**
  - `assets/disc036/img/DISC-036-01-BEFORE-MASTER.png` (1672 × 941, C2PA OpenAI, signed 13:52:59 UTC);
  - `assets/disc036/img/DISC-036-02-POSSIBLE-MASTER.png` (1671 × 941, signed 13:57:34 UTC).
  - Both are declared `AI_ILLUSTRATION` in `image-provenance-records.json`. The POSSIBLE is permitted on the Discovery and the Library card; the BEFORE only on the Discovery.
- **Alignment:** measured before the build at a median of about 2–3 px on the house, roof, chimneys, upstairs windows and neighbouring house, and judged a pass. The only correction is a 1-pixel crop of the BEFORE's left column to the common 1671 × 941 frame. Nothing was resampled, warped or stretched.
- **Web copies:** 17 recorded derivatives built by `atlas-tools/build-disc036-images.py` (`--check` reproduces them byte for byte):
  - WebP at 768 / 1024 / 1376 / 1671;
  - a 1024 JPEG fallback;
  - a 753 × 941 phone crop (x 480–1233);
  - two Library-card WebPs;
  - the 1200 × 630 share image, made from the POSSIBLE.
- **Disclosure:** the registered PROPERTY label "Illustrative AI-generated visualisation. Not an actual property." appears in the figure and under the hero (`build-ai-disclosure-below.py`). The Library card carries the "AI-generated illustration" chip.

The chapter plans and footprints are still PlotNua vector drawings (`build-disc036-drawings.py`).

## Content limits applied

**Planning (chapter 03).** Checked 5 Nov 2026 against the published regulations and council and Department circulars:
- S.I. 338/2026 Class 1: 45 m² (was 40), rear only, since 1 Oct 1964.
- Upstairs: 12 m² (terraced or semi-detached), 20 m² (detached), 2 m from a party boundary.
- Windows: upstairs 8 m (was 11), ground floor 1 m. Height limits. 25 m² open space. Main house only.
- S.I. 344/2026 dormers.
- S.I. 359/2026 and circular BC07/2026: no Commencement Notice for an exempt extension of up to 45 m²; above that, a CN 14–28 days before work, with certification or opt-out.
- HSA project supervisors. Section 5 (€80, four weeks).
- PlotNua's reading is labelled "not legal advice", with no exemption guarantee.

**Cost (chapter 05).** Eleven components. No €/m², no estimate, no calculator. The only euro figure on the page is the Section 5 fee.

**Professionals (chapter 04).**
- Protected titles are shown only for architect, quantity surveyor and building surveyor (Building Control Act 2007).
- Links go to the RIAI, SCSI, Engineers Ireland and HSA.
- No firms are named.

**Routes (chapter 06).**
- The DISC-006 four-way comparison is revisited without its cost figures.
- Every route answers the same five questions. Parity is checked by the page proof.
- Attic and garage say plainly that no Discovery exists yet.

**Commerce.** No partner, supplier, referral, commission or paid-service wording. The value caveat is present.

## Privacy

The brief runs in the page only:
- no `<form>`, no fetch or beacon, no endpoint, no external form service;
- **save to My Plot** uses the frozen journey-save block (byte-identical to the Hidden Cars copy) and stores the multiple-choice answers only, in this browser (`plotnua.myplot.v1`, journeyId `disc036-extension-brief`);
- the free-text note is never stored.

## Analytics

`extension_brief_open`, `extension_brief_print` and `extension_route_click` go through the page's existing gtag, behind Cookiebot. Parameters are `journey` and `destination` only; no answers are sent.

## Integration (this branch)

**Registries:**
- identity (36 pages);
- header;
- Premium;
- search rail (33);
- sitemap;
- search index (174.8 KB, under the 180 KB guard);
- four governed topic entries: kitchen extension, rear extension, side extension, extension planning permission.

**Release and gate:**
- release-check counts: identity 36, header pages 38;
- the page proof `prove-disc036-page.py` (E1–E16, plus an 11-fault self-test; E16 is provenance) runs in the gate and in the release checks;
- the page is registered in `build-ai-disclosure-below.py` and `prove-compare-hero.py`.

**Library card (added with the hero pair):** one card in Space, showing the POSSIBLE. `discovery-library-images.json` and `discovery-library-labels.json` (no action label) are updated, and the card builders now expect 20 cards.

**Held:**
- **No `your-plot.html` change.** A kept brief appears in My Plot with its title and a Remove button, but without the reopen links. Adding them is a founder decision.
