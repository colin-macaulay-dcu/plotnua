# A HOME FOR ART · FOUNDER DESIGN DECISIONS AND HOUSEKEEPING

**Date:** 17 October 2026
**Authority:** founder instruction "A Home for Art — Founder design decisions & housekeeping" (17 Oct 2026), following the read-only audit of the same day (`claude/a-home-for-art-audit-2026-10-17.md` in the PlotNua Project)
**Baseline:** `origin/main` @ `808c26f`
**Status:** committed locally on branch `founder/a-home-for-art-design`. **Not pushed, not deployed.** The founder must approve the revised experience before publication.

## Commits

| Commit | What |
|---|---|
| `7e874ef` | **M9 re-baseline.** No page output change. `--check` now reproduces the live page byte for byte. |
| `7ad6cc3` | **The Discovery changes:** spacing, one assessment section, one PlotArt section, Live with art, corrections, guard amendments, search index. |
| `0f6166a` | **"Check your wall" result copy only:** evergreen Culture Night, RHA/RDS seasons. A separate commit so it can be taken or dropped on its own. |
| `0464eda`, this record | Single-line M8/M9 refusal messages. This record. |
| Last commit on the branch | Independent-review wording fixes: the routes read as "may", the meta description keeps "by arrangement" (153 characters), the rental wording matches the FAQ, and a stale comment is updated. |

## 1. M9 re-baseline (before any content change)

The merge builder refused at HEAD. Two consolidation byte pairs had been moved legitimately by later work:

- **`sitemap.xml` lastmod for this page.**
  - The Artist Register set it to 14 Oct, and `808c26f` recomputed lastmods from git history.
  - M9 now holds only what the merge owns: the page is listed exactly once, and the pre-merge date `2026-08-27` is gone.
  - The date itself belongs to whatever maintains lastmod.
- **`build-search-rail.py` `EXPECTED_PAGES`.**
  - The count went from 21 back to 22 with the Garden Room Prices guide.
  - The pair is now anchored on the merge's recorded comment, not on the number.

## 2. Image spacing

**Measured before:** the empty-wall plate (`046ec577`) and the artist plate (`6442d19e`) were **0 px apart** on both desktop and mobile.

**Change:**
1. The empty-wall plate now directly follows the "What you have: **Space.**" board, which it illustrates.
2. The three-possibilities chooser comes next.
3. The artist plate ("The work exists already. What it lacks is a room.") now **opens Possibility one**, the hosting branch it argues for.

No image was added, removed, cropped, replaced or regenerated, and no spacer was added.

| Gap between full-bleed images | Before | After |
|---|---|---|
| 046ec → 6442d (desktop / mobile) | **0 / 0 px** | **567 / 954 px** |
| Smallest gap anywhere on the page | 0 px | 567 px |
| Page height (desktop) | 19,644 px | 19,215 px |

## 3. One assessment section

"What could art mean for your home?" replaces two things:

- the "Check this against your own home" panel;
- **every** check button in the branches.

**Layout:**
- **Card one**, "Could your home host art?", leads to the DISC-024 check.
- **Card two**, "Could original art work in your home?", leads to the DISC-023 check.
- Both URLs keep `?start=1`.
- The eyebrow labels "For your space" and "For your walls" are interface wording.
- Under the cards: "Five short questions. No address or personal details required."

**On mobile:** the buttons are full width and the cards stack.

**Unchanged:**
- section id `#discover-your-property`;
- the three exits (garden, all Discoveries, homepage).

**Action links on the page:** 9 before, 4 after.

| | Before | After |
|---|---|---|
| Check buttons | 5 ("Check how far you'd go" ×3, "Check your wall" ×2) | 2 (one per card) |
| PlotArt invitations | 4 (top invitation ×2, Take part cards ×2) | 2 (one section) |

## 4. One PlotArt section

"Help bring art into more homes" sits after the three possibilities, at the PlotArt anchor ("This matching service is not live yet.").

**It replaces:**
- the top-of-page "Be part of the idea" invitation;
- the two-card "Take part" section.

**Buttons and wording:**
- "I have space for art" leads to the DISC-024 check (`?start=1`), whose result offers the Art Space Register.
- "I'm an artist looking for space" leads to `artist-register.html`.
- The note keeps the expressions-of-interest wording. It adds "PlotNua is not currently matching participants or arranging exhibitions" and one line explaining that the homeowner route starts with five questions.

**Register engines, Workers, collection and privacy:** untouched.

## 5. Live with art

The branch now carries:

1. **"What if the gallery came to your home?"**
2. The founder's **B2_P1**, verbatim.
3. **Three routes**, each written as something a third party *may* offer:
   - **Try it at home** (on approval);
   - **A home viewing**;
   - **Rental, where available**.
4. The founder's **B2_P2**, verbatim: PlotNua does not arrange loans, rentals or placements.
5. "Whether any of these is on offer is up to the artist or gallery."

**Guardrails on the wording:**
- No provider is named.
- Nothing is promised.
- No price is given.
- The duplicated **Display** tile is gone.

**Evidence (17 Oct 2026, read-only research):**

| Route | Evidence |
|---|---|
| On approval | This page's own FAQ. Irish galleries advertise "try before you buy" (secondary sources). |
| Home viewing | At least one Irish artist publishes free home viewings first-party. |
| Rental | Irish rental services exist; at least one rents to a home as well as a business. |

## 6. Factual corrections and links (applied once each, guard M12)

| Item | Before | After | Source |
|---|---|---|---|
| Culture Night | "18 September 2026 … through local authority arts offices … more than 1,800 events in 2025" | "every September, free, coordinated by the Arts Council with local authorities"; links culturenight.ie | culturenight.ie |
| RHA Annual | "through the summer, everything for sale" | "from late spring through the summer, with almost everything for sale"; links rhagallery.ie/rha-annual/ | RHA: 196th Annual ran 25 May–9 Aug 2026; terms exclude portraits from sale |
| RDS Visual Art Awards | "graduate work each winter" | "exhibition opens each November, showing emerging artists chosen from graduate shows"; links rds.ie | RDS: 6 Nov 2026–23 Jan 2027 |
| Chargeable person | "non-PAYE income … reaches €5,000" | "**net** non-PAYE income … reaches €5,000, or **gross** non-PAYE income reaches €30,000" | Revenue Form 12 (2025): "€5,000 or more" net; "€30,000 or more" gross |
| Rental FAQ | "aimed mainly at film, corporate and design clients rather than households" | "Most are aimed at film, corporate and design clients, though at least one also rents to homes" | Artysans (home or business) |
| Visual Artists Ireland | unlinked | links VAI's commercial-galleries manual | visualartists.ie |

**Notes:**
- **Chargeable person:** the audit's "over €5,000" came from a secondary source and was wrong. Revenue's own form says "or more", so the threshold is unchanged; the sentence now says *net* and adds the gross test.
- **Art Source:** left unlinked. Only a year-specific RDS event page exists, and it would go stale.
- **Link markup:** all external links open in a new tab with `rel="noopener"`, matching other Discoveries.

## 7. Other housekeeping

- **The lede** now names the possibilities in page order: host, then live with, then own.
- **The intro kicker** "Three possibilities. One home." repeated the hero, so it is now "Where to start".
- **The meta description** went from 212 to 153 characters, hosting first, and keeps "by arrangement" so it cannot read as a PlotNua service.
- **The title, OG and Twitter text** are unchanged.
- **Search:** `search-index-v1.json` was rebuilt through its builder. Only the `poss-a-home-for-art` standfirst changed.
- **Spacing fixes:** the "Finding each other" sub-heading had no space above it (pre-existing), and the Live with art disclaimer now has space above it.
- **Internal links:** all preserved. Chooser anchors, the cautions jump link, related cards, exits and the old-URL redirect all work.

## 8. Builder and guard changes

**`atlas-tools/build-a-home-for-art-merge.py`:**

| Guard | Change |
|---|---|
| **M3** (amended) | Each check is offered exactly once, in the assessment section, hosting first. The PlotArt homeowner button is the only other link, to the DISC-024 check. `?start=1` is always used, and the old URL is never linked. *Previously required links from the branches and the panel (at least 2 and at least 3).* |
| **M8** (amended) | The DISC-023 check must equal BASE once the two-option entry **and** the declared `CHECK23_WORDING` result strings are reverted. The engine, questions, outcomes and save keys stay pinned. |
| **M9** | Re-baselined (§1). The DISC-023 wording pairs are applied through `CONSOLIDATION`. |
| **M10** (amended) | Order: hero → board → wall plate → chooser → artist plate → Open → outcome → Live with → Discover & own → cautions → PlotArt → hosting card → buying card. |
| **M12** (new) | No two full-bleed plates side by side. The retired buttons, descriptions, panel heading and invitation stay gone. PlotArt appears once with one register link. Live with art carries its three routes, the not-PlotNua line, and no Display tile. Each correction is present exactly once. |
| M1, M2, M4, M5, M6, M7, M11 | Unchanged. B2_P1 and B2_P2 are still required verbatim (M6). M4 still refuses service claims, including "guarantee". |

**`atlas-tools/build-artist-register.py`:**
- **A11** (amended): one PlotArt section (the TAKE-PART marker) after the PlotArt anchor, exactly **one** link to the register, and no top-of-page invitation. *It previously required two.*

## 9. Tests (17 Oct 2026)

**Builder and proof checks:**

| Check | Result |
|---|---|
| Merge builder `--check` | M1–M12 pass |
| Artist Register `--check` | A1–A13 pass |
| Art Space Register `--check` | E0–E7, R1–R14 pass |
| `prove-art-space-register.py` | 57/57 |
| Search index `--check` / rail `--check` | 14 / 12 guards pass |
| Discovery Library capability / images | 12/12; 0 cards change |
| Image provenance | 12/12 |
| `prove-landmarks.mjs` | 133/133 |
| CI image-rights gate | GATE PASS (133 publishable, 0 refused); manifest current |
| `build-landmarks.py`, `build-a11y-visual.py` | REFUSE on the pre-existing DISC-025 frozen-hash staleness. They refused identically on `808c26f` before this work, so this is unrelated and not touched. |

**Mutation proof of the new and amended guards: 13/13 breaks caught**, and the tree was byte-clean afterwards. The breaks covered:
- a branch button returning;
- a second DISC-023 link;
- the card order swapped;
- the plates stacked again;
- the invitation returning;
- the Display tile returning;
- a correction reverted;
- a "guaranteed" promise;
- B2_P2 edited;
- the DISC-023 engine edited;
- the DISC-023 wording removed;
- a second register link;
- the invitation marker returning.

**Browser checks** (Playwright Chromium; desktop 1440 and mobile 390): **37/37 pass.**
- **Calls to action:** the CTA inventory; `?start=1` on every check link; all five anchors present once; chooser cards and the cautions jump link land on their sections.
- **Mobile layout:** full-width assessment buttons on mobile; no horizontal scroll; buttons at least 24 px tall.
- **Links and scripts:** four official links open in a new tab with noopener; no script errors.
- **Journeys:**
  - both assessment cards open their check at Question 1;
  - the PlotArt artist button opens the Artist Register;
  - the old URL still redirects to `#open-your-home-to-art` with its query string kept;
  - each check's "Discover" or Back control returns to its branch.
- **Accessibility:** axe WCAG 2.1 A/AA finds **no new violations** against `main`. The two `color-contrast` findings are the known template kickers, identical before and after.

## 10. Not changed

- Both check engines, their questions, answer values, outcomes, My Plot journey IDs and save keys.
- Both registers: Workers, Airtable, consent, privacy notices, caps.
- All image assets and image rights.
- Title, OG and Twitter text.
- Unrelated Discoveries.
- `sitemap.xml`: lastmod for this page stays 2026-10-14. Set it to the release date at publication.
