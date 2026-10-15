# DISC-026 THE HOUSE AS A POWER STATION — FREEZE RECORD · V4

**Status:** written in the same commit as the article change it records, under the V3 same-commit rule (V3 §6).
**Becomes active:** when this commit is released with the founder's approval. Until then, V3 remains the active freeze for the live site.
**Replaces:** V3 (ratified 15 Oct 2026, `governance/disc-026-house-as-power-station-FREEZE-RECORD-V3.md`). V3 stands as history, unaltered.

---

## 1 · The article at this record

| | |
|---|---|
| **File** | `discovery-house-as-power-station.html` |
| **SHA-256** | **`78322b402492b755f600b3ad32c13371f52cfaed4888ad9ebe8d2b9967ea7b48`** |
| SHA-256 (16) | `78322b402492b755` |
| **Byte size** | **190,488 bytes** (V3: 158,070) |
| Previous baseline | V3, `37139b2b760bbf07…` |

## 2 · The change: "Look again at your house"

**Founder approval (documented):**
- 15 October 2026, "DISC-026 · Look Again at Your House · Founder Approval": *"DECISION: APPROVED FOR INTEGRATION."*
- This follows approval of the concept (V1 feedback, 15 Oct) and the V2 visual direction (15 Oct).
- The copy is the R2 package draft, carried unchanged through V1 and V2.

**Built by:** `atlas-tools/build-disc026-look-again.py --apply`, from the three fragments in `atlas-tools/disc026-look-again/`.

**What changed in the article, and nothing else:**
1. **A section directly after `<main id="pn-main">`**, before the first article section, between the `LOOK-AGAIN:BEGIN` and `LOOK-AGAIN:END` markers. It contains:
   - six discoveries;
   - eleven revelations, each with one of four availability labels;
   - the interactive section drawing;
   - links to the existing sections, the Readiness Check and the Property Check.
2. **One `<style id="lag-css">`** before `</head>`. Every selector is under `.lag`.
3. **One `<script id="lag-js">`** before `</body>`.
4. **Five `id` attributes on existing elements**, so the section's links land: `home-compute` (S3), `data-centre-heat` (S4), and `anat-roof`, `anat-battery`, `anat-grid` (S7 positions). No text, class or other attribute changed.

**Proven:** removing exactly those four things reproduces the V3 baseline byte for byte (guard L2).

## 3 · What the section says, and does not say

- **Every claim is already on the page.** The organisations and places it names (ESB Networks, Tallaght, Tandem Compute, Sustainable Energy Communities, Germany, Britain) all appear in the V3 article.
- **No company in residential computing is named.** heata, Thermify, Deep Green, Zai Node and others are guarded out of the section.
- **No currency and no figures.** The only number is "2023" (Tallaght), plus the chapter numbers 1–6.
- **Only the four availability labels:**
  - Here today;
  - Being worked on in Ireland;
  - Operating elsewhere, not in Ireland;
  - Large sites in Ireland, not homes.
- **Host computing ends on** "None of this is available to an Irish homeowner today", with the Readiness Check described as "information, not an application".
- **Property Check:** the section adds a second route into it. The existing handoff after the Explorer is unchanged.

## 4 · Correction to V3 §4 (recorded, not a change to the page)

V3 §4 quoted the article's standing denial as *"None of this is available to an Irish homeowner today."* That is not the article's wording. The article says, in S3: **"None of it is open to an Irish homeowner."** (unchanged since `a949ccc`).

From V4:
- the **article's** denial is guarded as it actually reads (guard L6);
- the **section's** own sentence, "None of this is available to an Irish homeowner today.", is guarded separately.

## 5 · Dependent artefacts

| Artefact | SHA-256 (16) | Note |
|---|---|---|
| `disc026-power-station.html` | `8273c9db53d64aa1` | Unchanged |
| `disc026-compute-readiness-check.html` | `e0c0b1336b75d352` | Unchanged. The register remains inactive. |
| `disc026-evidence.json` | `3f7e7bdbefa238e8` | Unchanged (41 records) |
| `power-station-provider-universe-v1.json` | `da9760f306b5257d` | Unchanged |
| `provider-explorer.js` | `fa571dabb4d2ea65` | Unchanged |
| `maker-explorer.css` | `d571b8ca399ce265` | Unchanged |
| `atlas-tools/build-power-station-provider-explorer.py` | — | **P8 narrowed:** the handoff is found as the *last* Property Check link (`rfind`). Its docstring no longer calls the handoff "the only route into a check". |

## 6 · Standing commitments carried forward from V3

- The V2 money gate: no Zai Node figures and no `A$` followed by a digit. The British figures (£340, £20,000) remain inside their qualified proof points, as recorded in V3.
- International proof points keep their qualifications.
- The Explorer shows no rates, earnings, ranking or partner label.
- **Same-commit rule:** any change to the article writes a replacement freeze record in the same commit.

## 7 · Verification at this record

- `build-disc026-look-again.py --check`: **L1–L13 pass**.
- `build-disc026-look-again.py --prove`: **10/10 guards caught their break**.
- The Explorer builder (P1–P12), the provider universe (U1–U5, W1–W6), the provider guards (28/28), the search index and guards, the Discovery library and maker sync were each re-run on this commit. Results are in the delivery notes.
- Browser checks at 1366 px and 390 px:
  - section order;
  - Explorer (four cards);
  - search, footer navigation and both check handoffs;
  - all eleven revelations;
  - all link targets;
  - reduced motion and no-JavaScript reading;
  - no horizontal scroll and no script errors.
- **Pre-existing failures, unrelated and unchanged** (they fail identically on the V3 baseline):
  - `build-landmarks.py` and `build-a11y-visual.py` refuse because DISC-025's frozen `<main>` hash has moved;
  - `prove-disc026-discovery-capability.py` fails its own control on the clean page ("exactly five SVGs").
