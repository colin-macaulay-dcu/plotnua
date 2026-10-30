# DISC-026 THE HOUSE AS A POWER STATION — FREEZE RECORD · V8

**Status:** written in the same commit as the article change it records (same-commit rule, V3 §6; enforced by `prove-gridnua-launch.py` GL12).
**Becomes active:** when this commit is released with the founder's approval. Until then, V7 is the active freeze.
**Replaces:** V7 (`governance/disc-026-house-as-power-station-FREEZE-RECORD-V7.md`). V7 stands as history.

---

## 1 · The article at this record

| | |
|---|---|
| **File** | `discovery-house-as-power-station.html` |
| **SHA-256** | **`28e72178c8d48cad0eec0bdbb0db86d8c43062341e08a2d89bd2f2b722f3c272`** |
| SHA-256 (16) | `28e72178c8d48cad` |
| **Byte size** | **208,624 bytes** |
| Previous baseline | V7, `24774da62225df33…` (207,073 bytes) |

## 2 · The change

**Founder approval:** 30 October 2026, "Pass 2 · Release 3: static hero refinement rollout". The approval covers:
- D1: the shared `assets/identity/pn-hero-static.css`, with The Hidden Bins as the reference;
- D2: hero annotations move into an in-page annotated plate, unchanged;
- D4: this V8 amendment.

**Three changes, all presentational. No article wording, fact, figure, link, route, form, script or image changed.**

1. **One stylesheet link** is placed immediately after the generated `PLOTNUA IDENTITY v1 · HEAD · END` marker, outside the generated block:
   `<link rel="stylesheet" href="assets/identity/pn-hero-static.css?v=1">`
2. **The hero (`<header class="d-hero">…</header>`)** takes the static hero standard.
   - The hero opts in with `class="d-hero pn-hero-static"` and `--phs-focus:45% 40%`.
   - A visually separate phone and tablet title band (`.pn-hs-mtitle`, `aria-hidden`) is added. The H1 is unchanged and remains the only H1.
   - The hero image is wrapped in `.pn-hs-media`.
   - The hero no longer carries the Discovery annotation overlay.
   - The hero image, its `<picture>` and WebP sources, alt text, eyebrow, H1, subtitle and intro are byte-identical to V7.
3. **The annotated plate.** The hero's Discovery annotation ("PLOTNUA DISCOVERY / Potential Asset") is moved byte-for-byte into a new full-bleed plate, `section.imagine-photo.pa-frame.pn-hs-plate.pn-hs-plate--slice`.
   - The plate uses the same image and the same `xMidYMid slice` geometry.
   - It sits immediately after `<!-- LOOK-AGAIN:END -->` and before the article body.
   - It is outside the generated LOOK-AGAIN region. The look-again section and its fragment (`atlas-tools/disc026-look-again/`) are unchanged.
   - The plate image is `loading="lazy"`.
   - The annotation's SVG (`viewBox="0 0 1408 768"`), every coordinate, class and text node, and the Discovery Annotation Visual Signature are unchanged.

**Proof of scope** (verified at preparation, `ps_revert_proof.py`). Starting from this article:
- remove the one stylesheet link;
- restore the V7 `<header class="d-hero">…</header>`;
- remove the annotated plate.

The result reproduces V7 (`24774da62225df33…`) byte for byte.

## 3 · Dependent artefacts at this record

| Artefact | Change |
|---|---|
| `disc026-compute-readiness-check.html` | Unchanged (pinned in GL13) |
| `disc026-power-station.html` | Unchanged |
| `disc026-evidence.json` | Unchanged |
| `atlas-tools/disc026-look-again/` | Unchanged |
| `gridnua/`, `atlas-tools/release/gridnua-launch-manifest.json` | Unchanged |
| `assets/identity/pn-hero-static.css` | New shared stylesheet (Release 3). It applies only to pages that opt in with `.pn-hero-static` or `.pn-hs-plate`. |

**Governance tool note.** `atlas-tools/build-disc026-look-again.py --check` is not part of the Image Rights Gate, and it was already failing on production main at aca0556 (L2: "outside the section, the article differs from the V3 baseline"). On this record it stops one step earlier, in `derivative_picture_layer.py`, because the plate reuses the hero's approved WebP `<picture>` wrap. That means the same JPEG is now wrapped twice. No new derivative was created. The provenance register and the P12 guard pass. Updating that offline tool is out of scope for Release 3 and is recorded as a follow-up.

## 4 · Standing commitments carried forward

- The money gate of V2–V7.
- The qualified international proof points.
- No rates, earnings, ranking or partner label in the Explorer.
- The same-commit rule.

## 5 · Founder approval

☐ Approve this change at release (founder production approval for Pass 2 Release 3).
