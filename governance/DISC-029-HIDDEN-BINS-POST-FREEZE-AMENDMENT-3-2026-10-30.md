# DISC-029 · The Hidden Bins · Post-freeze amendment (Pass 2 Release 3 preview)

**Founder instruction:** 30 October 2026, "Pass 2 Release 3: static hero design refinement". It asks to remove floating ivory "PlotNua Discovery" plates from heroes and to correct the cropped Hidden Bins mobile hero. Hidden Bins is the representative preview.
**Status:** development branch `pass2/release-3-static-hero`. PREVIEW ONLY. Not merged, not deployed. The reference design needs founder approval; production needs separate approval.

## What changed

1. **The hero is the photograph alone.** It now uses the shared static hero standard, `assets/identity/pn-hero-static.css` (new, opt-in via `.pn-hero-static`).
   - The hero `<picture>` (same files, same alt text, still the priority image) is unchanged.
   - The hero copy (eyebrow, H1 "The Hidden Bins", subtitle) is unchanged.
2. **The frozen DISC-029 Image 01 annotation was moved, byte for byte, out of the hero** into an annotated plate immediately after "The Problem" (`.imagine-photo.pa-frame.pn-hs-plate`). Unchanged:
   - geometry, wording, viewBox and anchor (870,508);
   - the desktop/phone variants and the 767 px switch.

   The plate takes its height from the image, so neither the photograph nor the annotation is cropped. This follows the approved reference pattern (the Natural Swimming Garden's annotated plate in section 01). It is consistent with the Discovery Annotation Visual Signature, which is retained and not altered.
3. **Phones and portrait tablets:**
   - a compact title band above the image;
   - the image as a 4:5 frame on phones (1:1 on phones up to 700 px tall) and 4:3 on portrait tablets, positioned on the bins. **It replaces the 213 px strip.**
   - the copy below, leading with the subtitle; the H1 is visually hidden there, so the title shows once.
4. **Back control:** the desktop copy ends at least 104 px above the hero's bottom edge, and phone/tablet copy sits above the dock on first view. Tested at 1440, 1280×720, 1024, 768, 390 and 320.
5. **Retired:** the `.d-hero.is-plate` hero rules on this page only (no longer referenced).

## Verified unchanged

`<main>` content apart from the inserted plate, everything after `</main>`, title, meta, canonical and JSON-LD, the hero picture and hero copy. No image was created or edited. No provenance, rights or label state changed. The hero image remains LEGACY_UNDECLARED, with no AI label, as before.
