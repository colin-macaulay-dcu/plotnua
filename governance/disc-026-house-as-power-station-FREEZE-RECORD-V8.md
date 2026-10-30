# DISC-026 THE HOUSE AS A POWER STATION — FREEZE RECORD · V8

**Status:** written in the same commit as the article change it records (same-commit rule, V3 §6; enforced by `prove-gridnua-launch.py` GL12).
**Becomes active:** only when this commit is released with the founder's approval. Until then, V7 is the active freeze.
**Replaces:** V7 (`governance/disc-026-house-as-power-station-FREEZE-RECORD-V7.md`). V7 stands as history.

**Branch note:** the unreleased branch `pass2/release-3-static-hero` (static-hero direction, 30 Oct 2026) carries a different V8. Only one V8 can reach production. If that branch is ever revived, its record must be renumbered against whichever V8 was released.

---

## 1 · The article at this record

| | |
|---|---|
| **File** | `discovery-house-as-power-station.html` |
| **SHA-256** | **`77226b1e9bbad5006a8a11ba38256199188e849bb1b2e072583212038d3ab868`** |
| SHA-256 (16) | `77226b1e9bbad500` |
| **Byte size** | **211,922 bytes** |
| Previous baseline | V7, `24774da62225df33…` (207,073 bytes) |

## 2 · The change: the hero only

**Founder approval:** 30 October 2026, "PlotNua — Hero Slider Release 3. Approved: private preview development only". The instruction: "Record a narrowly scoped amendment to the Power Station hero freeze, without changing the remainder of the Discovery."

**What changed in the hero:**
- **The static hero becomes the shared Before / Possible slider** (`pn-compare` v1.2, hero standard, as The Natural Swimming Garden).
- **BEFORE:** `assets/img/fec77c3f0bae107a.jpg`, the existing hero picture of the bare roof, unchanged.
- **POSSIBLE:** `assets/img/ce9da2e51c945693.jpg`, the existing S8 picture (solar, battery, charger), unchanged. The two pictures have one framing (0 px).
- **Both pictures stay inside the storyboard's permitted places** ("the hero and S8").
- **The Potential Asset annotation is unchanged** in classes, geometry and wording. It now sits inside the BEFORE layer, so it labels the bare roof and is wiped away with it.
  - It is drawn with xMidYMid slice at a layer focus of 50% 50%.
  - On stacked layouts (phones and portrait tablets) it is hidden. There the 4:5 or 1:1 crop would put the opening divider through its label.
- **The hero copy is byte-for-byte unchanged:** the eyebrow, the H1, the flagship question and the intro.

**What changed in the head and at the end of the page:**
- one stylesheet link (`pn-compare.css?v=1.2`);
- one image preload (the POSSIBLE WebP);
- one `<style>` block of hero rules, before `</head>`;
- one deferred script (`pn-compare.js?v=1.2`), before `</body>`.

**Nothing else in the article changed.**

**Proof of scope** (verified at preparation): putting the V7 hero back and removing those four head and end additions reproduces V7 (`24774da62225df33…`) byte for byte.

## 3 · Guards and dependent artefacts at this record

| Artefact | Change |
|---|---|
| `atlas-tools/prove-disc026-discovery.mjs` | **One check narrowed in scope, not weakened.** The governed Library image (`ce9da2e5`) must still appear exactly once in the article body (S8). It may also appear once in the hero, but **only** as the slider's POSSIBLE layer. Every occurrence must still carry no potential-asset marker. Three planted faults were caught: a marker in the hero alt, a third copy, and a copy elsewhere in the hero. The hero plate check (`fec77c3f` once, with its marker) is unchanged. |
| `atlas-tools/prove-compare-hero.py` | This page has been added (C1–C9). |
| `disc026-compute-readiness-check.html`, `disc026-power-station.html`, `disc026-evidence.json` | Unchanged |
| The pre-existing proof finding "exactly five SVGs" | **Unchanged and pre-existing.** It also fails on production `16e7a2b`, because of the shared header icons. This change adds no SVG: the annotation SVG moved, so the count is the same. |

## 4 · Standing commitments carried forward

- The money gate of V2–V7.
- The qualified international proof points.
- No rates, earnings, ranking or partner label in the Explorer.
- The same-commit rule.

## 5 · Founder approval

☐ Approve this change at release. Production approval for Pass 2 Release 3 is separate and is not given by the preview approval.
