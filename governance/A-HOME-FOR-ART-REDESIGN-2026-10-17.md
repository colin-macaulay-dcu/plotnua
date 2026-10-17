# A Home for Art: editorial redesign (governance record)

**Founder approval to build locally:** 17 October 2026, 16:10 ("PLOTNUA — A HOME FOR ART · EDITORIAL REDESIGN — FOUNDER APPROVAL TO BUILD LOCALLY").
**Branch:** `founder/a-home-for-art-design`, local only. Not pushed, not deployed.
**Builder:** `atlas-tools/build-a-home-for-art-merge.py`. The page is still generated entirely from the pinned BASE sources (`460c97a`), and `--check` regenerates it byte for byte.
**Proof:** `atlas-tools/prove-a-home-for-art-redesign.py`, a mutation proof of the new and amended guards.

## Founder decisions applied

1. **Top assessments.**
   - The two homeowner checks appear straight after the opening introduction and the SPACE ↔ SPACE board, on a deep forest band.
   - The same two checks are repeated at the foot of the page.
2. **Navigation.**
   - A compact sticky in-page navigation: `01 Open · 02 Live with · 03 Own · Practical guide · Checks`.
   - It is labelled `<nav aria-label="On this page">` and marks the section being read with `aria-current="location"`.
   - It sits between the brand mark and Search on every width, and it scrolls away before the closing assessment band.
3. **Colour.** Each colour has one job:

   | Colour | Hex | Use |
   |---|---|---|
   | Warm ivory | `#F8F5EC` | Reading surfaces |
   | Deep forest | `#1F3B2E` | The two assessment bands only |
   | Muted sage | `#EEF2E8` | 02 Live with art |
   | Warm stone | `#EFE9DA` | The ladder band and the practical guide |
   | Terracotta | `#BD6A46`, and `#A4532F` for small text | Numerals, thin rules and the PlotArt top edge. Never a background. |

4. **Photography.**
   - The same five photographs, each with its source `<img>` tag verbatim (file, alt text, dimensions) and its source caption.
   - The wall and the outcome are full-bleed.
   - The artist and the same-wall room are split image/text, at full frame on desktop.
   - The evening room is an inset, 1,100 px wide on desktop.
   - On a phone, the split and inset photographs run edge to edge at 4:3, as the full-bleed plates already did at 62vh.
5. **Editorial.**
   - Nothing is deleted.
   - The buying detail (what you are buying, size, commissioning, before you buy) and "Finding each other" sit behind labelled expanders. Their full text stays in the page source.
   - Retired as interface only: the three chooser cards, which the navigation replaces; and the labels "Where to start" and "Which sounds like you?".

## Guards amended or added

| Guard | Change |
|---|---|
| **M3** | Two placements of the same assessment section (`#hfa-checks-top` and `#discover-your-property`), each with exactly one hosting card then one buying card. The PlotArt homeowner button is still the only other link to a check. Every check link still carries `?start=1`. |
| **M10** | New order: hero → opening → top assessments → empty wall → navigation → 01 + artist → outcome → 02 + evening room → 03 + same wall → practical guide → PlotArt → `</main>` → closing assessments. |
| **M12** (extended) | Every photograph is its source tag verbatim, and two photographs never appear without a heading between them. Deep forest is used as a background only behind the assessments, and terracotta never is. No two bands of one colour sit in a row. The headline cautions stay on view, and every moved caution sits inside a labelled expander. There is one labelled navigation, in order, pointing to real anchors. The chooser stays retired. |
| **M1** | New interface labels declared: `01`, `02`, `03`, the five navigation labels, and "More on buying and commissioning". |

The headline cautions that stay on view are:
- "Nobody has to come to your door";
- "Do not assume a home policy protects somebody else's artwork";
- "If money changes hands, it is income";
- "PlotNua does not currently arrange…";
- "the artist is the seller";
- "PlotNua does not publish price guides";
- "This matching service is not live yet".

## Unchanged

- Both check engines and their URLs.
- Both registers. A11 still passes: one PlotArt section and one register link.
- Image files and rights.
- Title, meta description, OG, Twitter and JSON-LD: the `<head>` is byte-identical apart from the redesign stylesheet.
- The SEO block.
- The redirect page.
- Internal links.
- Every caution's wording.
- No Atlas, Worker, supplier record or image-rights record is touched.
