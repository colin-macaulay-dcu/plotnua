# DISC-026 THE HOUSE AS A POWER STATION — FREEZE RECORD · V5

**Status:** written in the same commit as the article change it records, under the same-commit rule (V3 §6, carried into V4 §6).
**Becomes active:** when this commit is released with the founder's approval. Until then, the live article is as described in §2.
**Replaces:** V4 (15 Oct 2026, `governance/disc-026-house-as-power-station-FREEZE-RECORD-V4.md`). V4 stands as history, unaltered.
**Founder approval to ratify:** see §6. Ratification is part of the GridNua launch approval.

---

## 1 · The article at this record

| | |
|---|---|
| **File** | `discovery-house-as-power-station.html` |
| **SHA-256** | **`70c72eb19f1292b06fe9663ed7f743ec14b1fe184ac1de2ee942db60595001e1`** |
| SHA-256 (16) | `70c72eb19f1292b0` |
| **Byte size** | **202,680 bytes** |
| Previous live article | `1e3dbba997bd8606…` (202,189 bytes), production `571b22b` |
| Last freeze record | V4, `78322b402492b755…` (190,488 bytes) |

## 2 · Changes since V4 that were released without a replacement freeze record

The V4 same-commit rule was not followed after 15 October 2026: the article changed in **11 commits** with no replacement record. They are listed here so V5 starts from the truth.

**Accepting these changes into the baseline** is not a retrospective approval of any change whose approval is not documented.

| Commit | Date | Change | Approval documented where |
|---|---|---|---|
| `8b209fa` | 19 Oct | Search rail label | **None found** in the commit |
| `18a9afd` | 20 Oct | WebP images, search field name | Commit: "founder-approved scope" (crawl triage) |
| `fd0c464` | 21 Oct | Computing-led SEO title, description, anchors | Commit: refers to "previously approved meta"; no explicit approval of this change |
| `1981354` | 21 Oct | Factual corrections F1–F5 | Commit: "founder-approved 21 Oct 2026 (decision 4)" |
| `ee53016` | 21 Oct | Stage 2 bridge section, data centres in Ireland | Commit: founder approval 21 Oct ("STAGE 2 BRIDGE · APPROVED FOR LOCAL BUILD") |
| `d9db752` | 23 Oct | Global header v2 | Commit: "Founder approval, Phase B, 23 Oct 2026" |
| `3b5f344` | 24 Oct | Premium layer (Batch 4), editorial correction | **None found** in the commit |
| `0422dd1` | 26 Oct | H6 homepage release (site-wide shell change) | Commit: "founder release approval, 26 Oct 2026" |
| `d149305` | 27 Oct | PlotArt in the PlotNua navigation | Commit: "founder design approval, 27 Oct 2026" |
| `e5e0626` | 28 Oct | Header Direction C and My Plot | Commit: "founder approval 28 Oct 2026" |
| `13a7d99` | 28 Oct | Footer "Legal information" link | Commit: "founder decision A1-a, 28 Oct 2026" |

**Pre-existing guard drift, recorded and not repaired here:**
- On production `571b22b`, these refuse because the article has moved on through the layers above:
  - `build-disc026-look-again.py --check` fails L2 (the article no longer matches V3 outside the section);
  - `build-disc026-bridge.py --check` fails B3;
  - `build-power-station-provider-explorer.py --check` refuses at P2 (the `maker-explorer.css` pin).
- None of these is part of the standard release checks. Each needs its baseline moved forward in a separate, approved maintenance change. That is not done here, so this record does not touch any builder.

## 3 · The change in this commit: the GridNua handoff

**Founder approval:** 29 October 2026, "GridNua · Final Founder Review and Launch Preparation": *"Add the approved link from DISC-026. Update the DISC-026 freeze record … in the same release commit. Preserve all existing DISC-026 content."*

The founder's message says V4. V4 already exists (15 Oct), so this record is **V5**.

**What changed, and nothing else:**
- **Where:** one paragraph at the end of the computing section (S3, `id="home-compute"`), immediately before its existing image note.
- **Markers:** the paragraph sits between `<!-- GRIDNUA-HANDOFF:BEGIN … -->` and `<!-- GRIDNUA-HANDOFF:END -->`.
- **The paragraph:**

  > GridNua, a new initiative within PlotNua, follows residential computing and computing heat in more depth: who is doing it, where, and how far each technology has got. None of it is available through PlotNua in Ireland. *Follow residential computing in GridNua →* (`gridnua/`)

**Proof of scope:** removing exactly the marker block and its surrounding blank line reproduces the previous live article `1e3dbba9…` byte for byte. This was verified at preparation.

**What it does not do:**
- It names no company.
- It adds no figure.
- It does not touch the "Look again" section, the Explorer or the Property Check.
- It does not touch the Readiness Check, which stays at the same URL with the register closed.

## 4 · Dependent artefacts at this record

| Artefact | SHA-256 (16) | Note |
|---|---|---|
| `disc026-compute-readiness-check.html` | `ca60bf7b0881797b` | Unchanged in this commit. Register closed (`"writes_enabled": false`). Pinned by `prove-gridnua-launch.py` GL13 |
| `disc026-power-station.html` | `c324f8fb8d173c0e` | Unchanged |
| `disc026-evidence.json` | `3f7e7bdbefa238e8` | Unchanged (41 records) |
| `gridnua/` | see `atlas-tools/release/gridnua-launch-manifest.json` | New. Two pages, `noindex, follow` |

## 5 · Standing commitments carried forward

- The money gate of V2/V3/V4 holds.
- International proof points keep their qualifications.
- The Explorer shows no rates, earnings, ranking or partner label.
- **Same-commit rule:** any change to the article writes a replacement freeze record in the same commit. `prove-gridnua-launch.py` GL12 now refuses an article whose hash is not in the latest DISC-026 freeze record, so the rule is enforced at every release from this commit on, not only remembered. A future site-wide header or footer change that touches this article therefore writes V6 in its own commit.

## 6 · Founder ratification (to be confirmed with the GridNua release approval)

☐ Adopt the article in §1 as the frozen baseline. The §2 changes are accepted into it, and the rows without a documented approval are not recorded as approved.
☐ Approve the GridNua handoff paragraph in §3.
