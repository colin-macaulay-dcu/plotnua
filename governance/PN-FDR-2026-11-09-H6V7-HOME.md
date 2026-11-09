# PN-FDR-2026-11-09-H6V7-HOME · Founder decision: H6 v7 daylight homepage hero, image provenance (Option A)

**Date:** 9 November 2026  **Decided by:** Colin MacAulay (founder)  **Surface:** homepage only

## Decision
The founder approved the H6 v7 daylight homepage hero (branch `founder/h6v7-daylight-hero`) for production release, and chose provenance **Option A**: a homepage-specific, founder-attested approval restricted to the exact H6 v7 image files listed in `atlas-tools/validate-image-provenance.js` (`FOUNDER_ATTESTED_H6V7`, pinned by SHA-256).

## Facts recorded (nothing invented)
- **Masters.** Both are the founder's ChatGPT images, each carrying an embedded OpenAI C2PA credential (issuer OpenAI OpCo, LLC; softwareAgent ChatGPT gpt-image; digitalSourceType trainedAlgorithmicMedia):
  - BEFORE: `hero-before.png`, SHA-256 373b6805…3b3, 1670 × 942, created 2026-11-08T20:10:23Z.
  - POSSIBLE: `hero-possible.png`, SHA-256 8af0550f…e7e, 1670 × 941, created 2026-11-08T20:04:37Z.
- **Prompts:** unavailable. **Reference inputs:** not recorded (the credentials list none; conversation context is not captured).
- **Processing.** Described in `governance/H6V7-PROVENANCE-DECLARATION-DRAFT-2026-11-09.json` and `atlas-tools/h6v7/pipeline/`:
  - One-row pad and a sub-pixel translation.
  - Masked feature layers over the unchanged BEFORE.
  - Local reconstruction from the same photograph's own pixels.
  - Battery, charger and heat-pump pixels transplanted from the approved H6 assets (PN-FDR-2026-10-26-H6-HOME) and re-graded.
  - Sky and water textures cut from the masters.
  - No generative fill.
- The served WebP/AVIF files cannot carry the credential. That is why the attested form is used rather than the Governance 2.0 C2PA_EMBEDDED basis.
- **Visible label:** "AI-generated illustration" (unchanged). No supplier product or organisation is depicted or named.

## Scope and limits
- The approval covers only the pinned files, and only on the homepage. It is not a precedent for any other image.
- The 22 records of the retired evening H6 image set are retired from the register (P9). Their files stay in the repository and in git history, and the PN-FDR-2026-10-26-H6-HOME pin is left unchanged.
- No other safeguard is changed.
- The cloud-lettering animation ships as it is, by founder decision; its improvement is a separate follow-up.
