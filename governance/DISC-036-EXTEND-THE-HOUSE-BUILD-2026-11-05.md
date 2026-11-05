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

## Final governance review (5 Nov 2026)

**Authorisation:** DISC-036 Final Governance Review and Release Readiness (founder, private preview only, €0).

### F1: the 17 Oct and 28 Oct questions
- **17 Oct.** The independent professional review requirement was set for the standalone *Garden Room Planning Permission in Ireland* guide (founder approval "PLANNING GUIDE DEVELOPMENT APPROVAL", 17 Oct 2026).
  - It is written into that guide's own claims register (`professionalReview.requiredBeforePublication: true`) and enforced by its own `--release-check`.
  - The guide was never merged and is still held.
  - No record extends the requirement to Discoveries.
- **14, 19 and 28 Oct, and 30 Oct.** The later decisions moved PlotNua to risk-based, founder-approved compliance:
  - 14 Oct: mandatory external legal review replaced by a self-assessment plus founder approval (privacy);
  - 19 Oct: mandatory solicitor's review removed, legal advice made risk-based (images);
  - 28 Oct: no additional legal reviews without a specific, demonstrable reason;
  - 30 Oct: Governance 2.0, the authoritative policy. Its Rule 4 keeps legal content guarded by the existing content guards, and Rule 5 has no other approval stages.
- **None of these repeals the 17 Oct guide condition, and none extends it.** The two coexist:
  - the guide stays held under its own register;
  - Discoveries are governed by Governance 2.0.
- **Precedent:** DISC-008, DISC-033 and DISC-035 were published with planning chapters and no independent review.
- **For DISC-036:** no independent professional review is mandatory. Its chapter 03 is general, source-linked information, guarded by `prove-disc036-page.py` (E7).

### Regulatory content checked against S.I. 338/2026 (read 5 Nov 2026)
**Correction made:**
- Class 1 condition 5 now protects 25 m² of private open space "within the curtilage of the house", not "to the rear".
- The page and the brief questions are corrected.
- E7 now refuses the pre-2026 wording.

**Confirmed:**
- 45 m² (was 40);
- rear only;
- 1 October 1964;
- 12 / 20 m² upstairs;
- 2 m from a party boundary;
- upstairs windows 8 m (was 11);
- "balcony or terrace";
- the principal house only (new condition 8);
- Commencement Notice not required within the exemption up to 45 m² (S.I. 359/2026);
- Section 5: €80 and four weeks;
- the HSA project-supervisor triggers.

**Added:** a sentence under the opening that the extension in the hero is an illustration, not a checked design. A wrap-around like it would usually need planning permission, and suitability is for a qualified professional to assess. The sources footer now describes the hero as an AI-generated illustration.

### F5: My Plot reopen
- `your-plot.html` maps journeyId `disc036-extension-brief` to:
  - "Open your brief" → `discovery-extend-the-house.html?brief=1#extension-brief`;
  - "View the Discovery".
- The links are chosen by journeyId and never read from the record.
- A summary line from the STAGE key only.
- No Reopen-check link (there is no separate check page).
- No new storage, data or transmission. Other kept items render byte-identically.
