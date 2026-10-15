# DISC-026 THE HOUSE AS A POWER STATION — FREEZE RECORD · V3

**Status:** **ACTIVE.** Ratified by the founder, 15 October 2026 (founder direction "DISC-026 · Next Phase", Phase 1 item 1: *"Ratify freeze record V3 using the revised wording. Accept the existing baseline without inventing retrospective approvals."*).
**Replaces:** `disc-026-house-as-power-station-FREEZE-RECORD-V2.md` (15 Sep 2026) as the active freeze. V2 stands as history and is unaltered.
**Wording:** revision 2 of the V3 draft, ratified as worded, with **no §2B exceptions**.
**Intervention type:** GOVERNANCE CORRECTION ONLY. The live Discovery is not changed by this record.

> **What ratification means.** The article as it stood on 14–15 October 2026 (§1) is the frozen baseline.
>
> **What it does not mean.** It is **not** a retrospective founder approval of any change whose approval was not documented. The changes in §2B are *accepted into the baseline*; they are not described, here or elsewhere, as approved.

---

## 1 · THE BASELINE (live, verified 14 Oct 2026; re-verified 15 Oct 2026)

| | |
|---|---|
| **File** | `discovery-house-as-power-station.html` (deploy repo; live at plotnua.ie) |
| **SHA-256** | **`37139b2b760bbf073ae543d4d67618b60478cb82fe2c06ba40cb9f81925e9ee1`** |
| SHA-256 (16) | `37139b2b760bbf07` |
| **Byte size** | **158,070 bytes** (V2: 80,021) |
| Commit | `31a50ff` on `origin/main` (container equivalent `0041e65`, same tree) |
| Live check | The live page's SHA-256 equals the value above (read 14 Oct 2026; re-read at ratification, 15 Oct 2026: equal) |

## 2 · CHANGES SINCE V2 (V2 artefact: `e929b80`, `b02d9fef…`)

### 2A · Changes with documented founder approval

| Commit | Date | Change | Where the approval is documented |
|---|---|---|---|
| `f31eae5` | 26 Sep | "What We're Watching"; plug-in solar in the not-yet register | Commit message: "both founder-approved" |
| `a949ccc` | 5 Oct | Governed rebuild to the nine-section storyboard (S1–S9) | Commit message: "Founder-approved candidate 161306c381ca" |
| `8105b52` | 8 Oct | Search V1 (site-wide) | Commit message: "Founder-approved after four rounds of real-browser review" |
| `2e289f7` | 13 Oct | Electricity-export Provider Explorer; Thermify label correction | governance/HOUSE-AS-POWER-STATION-PROVIDER-EXPLORER-2026-10-13.md (approval 13 Oct, 19:19) |
| `6bf45ff` | 13 Oct | Two tab-note corrections | Commit message: "Founder-approved corrections (13 Oct 2026)" |
| `0041e65` / `31a50ff` | 14 Oct | One official supplier link per Explorer card | Commit message and governance addendum: founder decisions, 14 Oct |

### 2B · Changes accepted into the baseline, with no documented approval

These changes are in the live article. **No founder approval is recorded for them** in their commits or in any governance record found. Ratification of V3 accepts them as part of the frozen baseline; it does not state that they were approved.

| Commit | Date | Change | Scope |
|---|---|---|---|
| `233803f` | 5 Oct | Residential compute evidence update, S3 and S9 | DISC-026 only |
| `e350543` | 6 Oct | SEAI battery grant activated with governed evidence (evidence file 38 → 41 records) | DISC-026 and its evidence file |
| `8db350f` | 9 Oct | Job 4 accessibility: landmarks, footer nav, heading level, skip link | Site-wide |
| `8ccca1e` | 9 Oct | Job 5 accessibility: contrast, reduced motion, carousel targets | Site-wide |
| `a7652d6` · `546b29a` · `cb49980` | 10 Oct | SEO V1: search intent, contextual Discovery links, related-links presentation | Site-wide pattern |

**No exceptions were listed at ratification.** Any of these can still be reviewed or reverted later, but only under its own brief.

## 3 · DEPENDENT ARTEFACTS (state at this record; not frozen by it)

| Artefact | SHA-256 (16) | Note |
|---|---|---|
| `disc026-power-station.html` (V1 journey) | `8273c9db53d64aa1` | V2 recorded `f353f7cea70586a9`. It has changed since (e.g. Job 1 journey exits, 9 Oct). **`DISC-026-V1-JOURNEY-FREEZE-RECORD.md` needs its own review.** |
| `disc026-evidence.json` | `3f7e7bdbefa238e8` | 41 records (V2: 38) |
| `disc026-compute-readiness-check.html` | `e0c0b1336b75d352` | Register INACTIVE by construction |
| `power-station-provider-universe-v1.json` | `da9760f306b5257d` | U1–U5, W1–W6 |
| `provider-explorer.js` | `fa571dabb4d2ea65` | Re-pinned 14 Oct for `offLink()` |
| `maker-explorer.css` | `d571b8ca399ce265` | Unchanged |

## 4 · STANDING COMMITMENTS CARRIED FORWARD (stated precisely)

- **The Irish-availability denial stays and stays guarded:** *"None of this is available to an Irish homeowner today."*
- **The V2 money gate is carried forward:** no Zai Node figures and no `A$` followed by a digit.
  - *Recorded for accuracy:* the baseline article does carry **British** figures inside qualified international proof points: heata's "up to £340 a year" and Deep Green's "over £20,000 a year".
  - They entered with the founder-approved rebuild (`a949ccc`). This record notes them; it does not extend or remove them.
- **International proof points keep their qualifications:** Thermify is a limited trial; Zai Node is Australian; each is labelled as not Irish.
- **The Explorer** shows no rates, earnings, ranking or partner label. The Property Check remains the primary journey.

## 5 · VERIFICATION AT THIS RECORD

- `build-power-station-provider-explorer.py --check`: P1–P12 pass.
- `build-power-station-provider-universe.py --check`: U1–U5, W1–W6 pass. The next evidence review is due 11 Jan 2027.
- `prove-power-station-provider-guards.py`: 28/28.
- The live SHA-256 equals the baseline (§1), re-read 15 Oct 2026.

## 6 · MAINTENANCE RULE

The article changes only for a genuine defect, an evidence change, or a separately approved brief.

**Same-commit rule (ratified 15 Oct 2026):** any commit that changes `discovery-house-as-power-station.html` must, **in the same commit**, write a replacement freeze record carrying:
- the new SHA-256;
- the change;
- where its founder approval is documented.

A commit without it is not release-ready. This closes the gap that let 13 changes accumulate.

---

**Founder ratification**
☑ Adopt the current article (§1) as the new baseline, with §2B accepted as listed. No exceptions.
Founder direction, 15 October 2026 (Phase 1, item 1).

**Next freeze record.** The next change to the article (for example the "Look again at your house" build or the Heata sentence, if approved) writes **V4 in the same commit**, under the rule in §6.
