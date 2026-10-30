# Pass 2 · Release 2 · Discovery hero slider consolidation

**Founder instruction:** 30 October 2026, "Pass 2 Release 2: Discovery hero slider rollout".
**Status:** development branch `pass2/release-2`. NOT DEPLOYED. Production needs separate, explicit founder approval.

## What changed
Three Discoveries moved from their own `.cmp` slider (DISC-008 v2 code) to the shared `pn-compare` component, hero standard. Each keeps its approved image pair and framing.

| Discovery | Labels | Start | AI label |
|---|---|---|---|
| The Hidden Flood Barrier (DISC-033) | Before / Possible | 35% (unchanged) | yes (declared records) |
| Living in the Garden (DISC-008) | Before / Possible (was Today / Possible) | 35% (was 65%) | none, as before (legacy undeclared images) |
| Home Exchange (DISC-005) | Home / Away (was Your home / Their home) | 35% (was 65%) | none, as before (legacy undeclared images) |

The old `.cmp` markup, CSS and scripts were removed from the three pages only after the shared component passed its browser tests.

**What is retained:**
- Hidden Flood Barrier: its approved hero typography (left copy column on desktop; on stacked layouts the title shows once above the slider and the copy leads with the question).
- Living in the Garden: its screen-reader wording, through the new opt-in `data-say-before` / `data-say-after` attributes (pn-compare v1.2, additive).
- Page content, links, supplier and pricing content, titles, canonical URLs, JSON-LD and footers: verified identical to `main`.

## Images and provenance
- **DISC-033:** 10 AVIF derivatives of the pinned encodings (768/1024/1536 and the 4:5 M-640/M-819 crops). Each has a full record in `image-provenance-records.json`, placed beside the DISC-033 records. The PN-FDR-2026-10-27-DISC033 pin is extended to these derivatives, the same precedent as DISC-031 on 30 Oct.
- **DISC-005:** 4 WebP derivatives (960 w and 1376 w of both images). They are registered as hash-bound derivatives under the P12 rule (WebP only, no crop, no upscale, source JPEG kept as fallback). They inherit LEGACY_UNDECLARED and declare nothing.
- **DISC-008:** the BEFORE image reuses its existing WebP derivatives. The POSSIBLE image (`8c60a8f27eb9c697.jpg`) is on a provenance hold (an unidentified second generation input in its C2PA credential, held since 17 Oct 2026). No derivative was made, and it is served exactly as before.
- **Not done, and needing a founder decision:** AVIF or 4:5 phone crops for legacy-undeclared images. The P12 rule permits WebP resizes only.

## Guards updated
- `prove-compare-hero.py`: covers five pages. C6 requires the AI label only where a layer is a declared AI_ILLUSTRATION record.
- `prove-cluster1-hero-slider.py`: the 12 assertions retargeted to pn-compare.
- `prove-disc033-page.py`: F3 (title band), F5 (23 derivatives) and F6 (pn-compare hero) retargeted.
- `validate-image-provenance.js`: DISC-033 pin extended.
