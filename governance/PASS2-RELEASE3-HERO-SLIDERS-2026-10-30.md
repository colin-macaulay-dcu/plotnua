# Pass 2 · Release 3 · Discovery hero sliders

**Approvals:**
- **Development:** founder, 30 Oct 2026.
- **Rules applied:** PlotNua Governance 2.0 (`governance/PLOTNUA-GOVERNANCE-2.0.md`).

**Status:** branch `pass2/release-3-hero-sliders`. **Not deployed:** production awaits the founder's approval.

**What changed:** three Discoveries now open on the shared `pn-compare` v1.2 Before / Possible hero, the same as The Natural Swimming Garden. Each uses its measured 0 px image pair.
- **The Hidden Bins:** the hero annotation is removed and the phone hero is fixed.
- **The House as a Power Station:** the Potential Asset annotation is unchanged. It now sits on the Before side and is hidden on stacked layouts.
- **Above and Beyond:** the slider uses copies of the two pictures with an incidental generator sparkle removed. The edit is a routine artefact removal (Rule 3) inside one 59 × 59 px area. The originals are untouched. Details: `governance/DISC-016-HERO-MARK-REMOVAL-2026-10-30.json` and `atlas-tools/build-disc016-hero-mark-removal.py --check`.

**Nothing outside the three heroes changed.**

**AI labels (Rule 2):**
- **Declared and labelled:** Hidden Bins Before and Possible, and Power Station Before. Each one's own Google C2PA credential records an AI generation, so all three were declared from metadata (`atlas-tools/declare-ai-from-metadata.py`) and the heroes carry "AI-generated illustration".
- **Not declared yet:** Power Station Possible (`ce9da2e5`), also credential-verified, appears on six other pages. It waits for a small label pass on those pages.
- **Never declared:** the Above and Beyond pictures carry no credential and no project record of their origin, so they are not declared and not labelled.

**Hidden Bins Possible:** the original JPEG is retained. Its credential records one unidentified input, which is disclosed as such. No relationship to the Before picture is asserted.
