# Pass 2 · Release 3 · Discovery hero sliders (private preview)

**Founder instruction:** 30 October 2026, "PlotNua — Hero Slider Release 3. Approved: private preview development only."
**Status:** branch `pass2/release-3-hero-sliders`, based on production `16e7a2b`. **Not pushed, merged or deployed.** Production needs separate, explicit founder approval.

## What changed

Three Discoveries move from a static hero to the shared `pn-compare` v1.2 hero standard, the same standard as The Natural Swimming Garden:
- opens at 35, labelled Before / Possible;
- on phones and portrait tablets: the compact title band, a 4:5 (or 1:1) frame, the jump bar, then the page's own hero copy.

Each slider uses the audit's measured 0 px pair (one framing). The hero copy is carried over byte for byte. **Nothing outside the hero changed on any of the three pages:** a script check removes the hero and the four head/end additions and finds the rest identical to production.

| Discovery | BEFORE | POSSIBLE | Notes |
|---|---|---|---|
| **DISC-029 The Hidden Bins** | `9805382f8164228a.jpg` (+ existing WebP) | `31b49fb60732073b.jpg` | The frozen hero annotation is **removed** (founder instruction). The hero is no longer a plate, which fixes the thin phone hero. |
| **DISC-026 The House as a Power Station** | `fec77c3f0bae107a.jpg` (+ existing WebP) | `ce9da2e51c945693.jpg` (+ existing WebP) | The Potential Asset annotation is unchanged, now inside the BEFORE layer, and hidden on stacked layouts. Freeze record **V8**. |
| **DISC-016 Above and Beyond** | `assets/disc016/img/DISC-016-HERO-BEFORE-MR.*` | `assets/disc016/img/DISC-016-HERO-POSSIBLE-MR.*` | **Visible-mark-removed copies** of `b53d75f9…` and `aecece07…` (see below). |

**Not changed:**
- the start position (35, the founder's site-wide decision);
- the shared `pn-compare` CSS and JS;
- every other page.

## Images and provenance

**The register is unchanged** (no record, backlog entry or derivative added).

**Hidden Bins POSSIBLE (`31b49fb6`):**
- Its embedded Google credential (valid, 15 Sep 2026: "Created by Google Generative AI") records one input ingredient ("Input ingredient 0") with **no credential, title or hash**.
- The 0 px alignment strongly suggests that input was the BEFORE picture, but **that is not established**.
- So **no derivative is made** (the hero-derivative rule requires an established lineage), and the original JPEG is served unchanged, as it already is further down the page.
- Cost: about 790 KB for the hero instead of about 200 KB.
- **To unlock a WebP:** the founder attests the input. No guard is changed.

**Power Station:**
- Both pictures already have hash-bound WebP derivatives with an established lineage (signed credentials, 19–20 Oct). They are reused.

**Above and Beyond:**
- **What was found:** both legacy sources carry the same faint Gemini sparkle (about 55 × 59 px, near (1288, 649)).
- **What was made:** `atlas-tools/build-disc016-hero-mark-removal.py` makes six **new** files: for each picture, a JPEG fallback plus 1408 and 960 WebP. The build is deterministic and has a `--check` mode.
- **The operation:** reverse alpha blending of a fitted four-point star at a measured uniform opacity, then a 3 px inpaint on its edge only.
- **What changed:** only pixels inside a 59 × 59 px box (about 0.1% of each image). The script refuses if any pixel outside it differs.
- **Sources untouched:** the two source files, and their other uses on the page, are not modified.
- **Why they can't be registered yet:** these are not P12 derivatives (removal is an edit), so they cannot be registered as the rules stand.
  - **Draft for review:** `governance/DISC-016-HERO-MARK-REMOVAL-REVIEW-DRAFT-2026-10-30.json`.
  - **Guards correctly refuse them:**
    - `validate-image-provenance.js` P1 ("6 unaccounted");
    - `prove-compare-hero.py` C7.
  - **This is the branch's only gate failure, by design. Founder decision needed** (pinned exception, or a P12 amendment, or reject).

**AI label:** none on these three heroes, following the Release 2 precedent (Living in the Garden, Home Exchange). Guard C6 labels only declared AI_ILLUSTRATION records, and none of these pictures is declared. All four credential-bearing pictures are recorded by Google as AI-generated. Declaring them, and so labelling them, is a separate founder decision.

## Guards

- `prove-compare-hero.py`: the three pages are added. It covers 8 pages and passes, except C7 on Above and Beyond (see above).
- `prove-disc026-discovery.mjs`: the Library-image check is narrowed in scope (freeze record V8 §3). Three planted faults were caught. Its one remaining failure ("exactly five SVGs") is pre-existing on production.
- `prove-gridnua-launch.py` GL12: passes with V8.
- New: `atlas-tools/build-release3-hero-sliders.py` (with `--check`) and `atlas-tools/build-disc016-hero-mark-removal.py` (with `--check`).
