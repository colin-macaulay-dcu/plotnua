# DISC-034 · The Water Wall: development build record

**4 November 2026.** This is a development build on branch `dev/disc034-water-wall`.
- **Founder approval:** build authorisation, private preview only, 4 Nov 2026 (Discovery approved and DISC-034 allocated the same day).
- **Not pushed, merged or deployed.** Production release needs the founder's explicit approval.

## Images (Governance 2.0)

| Role | Master in repository | sha256 | Founder source file |
|---|---|---|---|
| BEFORE | `assets/disc034/img/DISC-034-01-BEFORE-MASTER.png` | `145eff52…53ccad` | `Images/Discoveries/DISC-034 The Water Wall/DISC-034-01-BEFORE-MASTER.png`, saved 4 Nov 2026 19:58 |
| POSSIBLE | `assets/disc034/img/DISC-034-02-POSSIBLE-MASTER.png` | `8620f378…b532` | `Images/Discoveries/DISC-034 The Water Wall/DISC-034-02-POSSIBLE-MASTER.png`, saved 4 Nov 2026 20:06 |

Both masters are copied byte for byte; the founder's files are unchanged.

**Provenance.** Both masters are ChatGPT (OpenAI) outputs, 1536 × 1024 px RGB PNG.
- Each carries a signed C2PA credential (claim generator "OpenAI Media Service API", c2pa-rs 0.79.2). The credential records `c2pa.created` with `trainedAlgorithmicMedia`, then `c2pa.converted` and `c2pa.watermarked.unbound`.
- The claim signature, the data hash and the timestamp verify.
- The reader does not trust the signing certificate (`signingCredential.untrusted` / `invalid`). This is the same state as other OpenAI credentials in the register.
- **Signing times:** the BEFORE was signed at 19:55:46 UTC and the POSSIBLE at 19:59:09 UTC.
- No input image is recorded.
- Prompts are UNAVAILABLE.
- Reference disclosure is UNCERTAIN. The pair's near-identical geometry suggests the POSSIBLE was made from the BEFORE, but this is not asserted.

**Routine edits only** (Rule 3). Every web copy was made by `atlas-tools/build-disc034-images.py` and is recorded as a derivative of its master. The edits are:
- Lanczos resizes to 768, 1024 and 1376 px, plus the 1536 px original width;
- WebP (quality 80) and JPEG encodes;
- one 4:5 phone crop at x 690–1509, applied identically to both images, which keeps the downpipe filter and the whole storage wall in view;
- two Library card WebPs;
- a 1200 × 630 social card from the POSSIBLE.

Nothing is generated or retouched.

**Alignment** (measured on the masters, no resampling). The camera, house, shed, rear houses and patio are unchanged between the two images.
- **Phase correlation:** sub-pixel shift on the sky and rear houses (0.2 px, response 0.998) and on the house wall and door (≤ 1.0 px, response 0.94).
- **ORB feature matches** in the unchanged regions (3,992 within 20 px): median 1.4 px, p90 3.5 px.
- **Result: PASS.** Change is confined to the boundary-wall side (storage wall, filter, climbers, raised bed and planting).

**AI label.** The founder asked for the caption "Illustration — not a real installation."
- Governance 2.0 Rule 2 and the 31 Oct 2026 slider standard keep an explicit AI disclosure.
- The register therefore gains one approved variant, `AI-generated illustration — not a real installation.`, which carries the founder's wording with the register's base label.

## Content limits applied (founder build authorisation)

**Hero.** The page uses the shared `pn-compare` slider.
- It opens at 100% BEFORE and works with mouse, touch and keyboard (arrow keys, Home, End).
- The images keep their 3:2 proportions.
- There is one visible title on phones and portrait tablets, with a single H1.

**Chapters.** The six approved chapters, in order:
1. The possibility
2. More than a water butt
3. How it works (a bespoke PlotNua SVG with desktop and phone layouts, labelled "Not to scale")
4. Is it right for your garden?
5. What's out there?
6. Two ways to take the next step

**Practicalities.**
- Structure and footing, filled weight (about a tonne per 1,000 L), wind, overflow, frost, planning (Class 5: 2 m, or 1.2 m in front; exemption status unsettled; Section 5), shared boundaries and professional installation are all covered.
- The page says a full-sized wall is not a simple DIY project.
- No water-bill savings: Irish households pay no domestic water charges.

**Products.**
- Harves and ThinTanks appear as European examples. Each price is labelled as an advertised figure, with country, VAT basis and the date checked (4 Nov 2026).
- The page says "Not yet confirmed through an Irish distributor."
- Irish slimline tanks are shown with tanks.ie prices.
- No manufacturer photograph is used; product statements are marked Maker claim.
- No business is called a partner, and the page says PlotNua does not sell, import or install the products.

**Interest route.** Route B is the existing free WhatsApp link.
- The link is unprefilled, because the global header guard G5 forbids prefilled text. Visitors are asked to quote reference **WW**.
- The page also links the existing contact page and My Plot.
- There is no form, payment, order or new data collection.

**Cross-links.** The page links to DISC-031 The Natural Swimming Garden and DISC-033 The Hidden Flood Barrier. Those pages are not modified.

## Integration

- **Registries:** `pn_header.py`, `premium_pages.py`, `build-identity-stage1.py`, `build-ai-disclosure-below.py` and `prove-compare-hero.py`.
- **Counts:** search rail EXPECTED_PAGES 31; Library card builders 18 cards.
- **Library:** card `data-cat="Garden"` showing the POSSIBLE.
- **Sitemap:** one entry added.
- **Search index:** one new possibility record. The index is 183,763 bytes (179.5 KB) against the unchanged 180 KB guard, with no record removed.
- **Proof:** `atlas-tools/prove-disc034-page.py` (W1–W16). It is added to the Image Rights Gate and to the release script's standard checks.

## Finalisation (founder decision, 4 Nov 2026 evening: "Finalise and prepare for launch")

**Images.** The original BEFORE and POSSIBLE are approved and stay unchanged; the proposed pipe correction was rejected. The Experience image is not a launch blocker.

**Retained as built:**
- the disclosure "AI-generated illustration — not a real installation.";
- the standard unprefilled WhatsApp link (reference WW);
- the existing My Plot integration.

**Search.**
- A governed topic-map entry is added: "water butt" → `discovery-the-water-wall.html`, possibility scope only. The topic map moves to version 3 under the founder's approval.
- The index is 179.5 KB, against the unchanged 180 KB guard.
- The wellness route-template optimisation was **not** made. The frozen SEARCH-V1 contract (§2) lists `route` as a product field, so the change needs a contract amendment. It is reported separately.

**Reciprocal exits.**
- DISC-031 and DISC-033 each gain one closing-panel exit link to The Water Wall.
- The DISC-031 content guard declares that link as an addition (ADDED_LINKS); every other pin is unchanged.
- The DISC-033 page proof passes unchanged.

**Rebase.** The branch is rebased onto production `main` `b4af57a` (Superior Pergola commits); there are no conflicts.
