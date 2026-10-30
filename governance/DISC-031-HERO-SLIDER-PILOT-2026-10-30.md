# DISC-031 · Natural Swimming Garden · Hero slider pilot (Pass 2)

**Founder approval:** D1, 30 October 2026 ("Proceed with the Natural Swimming Garden Before / Possible hero slider pilot").
**Status:** development branch `pass2/hero-slider-pilot`. NOT DEPLOYED. Production release needs separate, explicit founder approval.

## What changed
- `assets/identity/pn-compare.js` / `.css` upgraded from v1 to **v1.1**. The additions are opt-in:
  - configurable labels (`data-label-before` / `data-label-after`) for the tags and jump buttons;
  - a hero standard (`.pn-hero-compare--std`) with a compact Discovery title above the image on phones and portrait tablets, a higher handle position, and the eyebrow visually hidden where it repeats that title.
  - Markup without the new attributes or class renders exactly as v1. DISC-032 was screenshot-compared at 1440, 1280, 768, 390 and 320 px before and after: 0 pixels differ.
- `discovery-natural-swimming-garden.html`: the static hero image was replaced by the shared component, using the **existing approved pair**:
  - BEFORE: `DISC-031-before-*`
  - POSSIBLE: `DISC-031-reveal-*`
  - Both are 1536 × 1024 in one framing. They are the same files already used by the flagship comparison further down the page.
- Hero typography, copy, H1, subtitle, intro, eyebrow text, metadata, JSON-LD, canonical URL, Open Graph image and the inline flagship comparison are unchanged.
- `atlas-tools/prove-compare-hero.py`: new read-only guard (C1–C9) with a self-test (9/9 planted faults caught).

## Image provenance
- No new image, encoding or derivative was created. Every hero file has an existing record in `governance/DISC-031-PROVENANCE-DECLARATION-DRAFT-2026-10-26.json`. Those records already describe the before image as "the BEFORE side of the comparison".
- The "AI-generated illustration" label stays on the hero (component label). The page's illustration-label count is unchanged.

## SEO and no-JavaScript
- POSSIBLE is the base layer and the no-JavaScript picture, carrying the same `alt` text and `id="dHeroImg"` as before. Search engines, social cards and browsers without JavaScript therefore see the same hero image as the live page.

## Known follow-up (not a blocker)
- First-load hero weight on a 3× phone rises from about 358 KB (POSSIBLE only) to about 697 KB (pair).
  - For a reader who reaches the flagship comparison, the total weight of the page is effectively unchanged, because both files are reused from cache.
  - Proposed for the rollout: 1200 w WebP encodings of the approved masters, recorded as derivatives.
- The inline flagship comparison now repeats the hero pair. Retaining or replacing it is a separate content decision; it was not changed in this pilot.
