# DISC-020 · Stay in the House You Love: development build record

**4 November 2026.** This is a development build on branch `dev/disc020-stay-in-the-house`.
- **Founder approval:** Phase 2 authorisation, 4 Nov 2026 (Phase 1 audit approved).
- **Not pushed, merged or deployed.** Production release needs the founder's explicit approval.

## Images (Governance 2.0)

| Role | Master in repository | sha256 | Founder source file |
|---|---|---|---|
| BEFORE | `assets/disc020/img/DISC-020-01-BEFORE-MASTER.png` | `084810b3…6abfb` | `Stay-in-the-House-You-Love-02-Reveal.png`, saved 4 Nov 2026 15:22 |
| POSSIBLE | `assets/disc020/img/DISC-020-02-POSSIBLE-MASTER.png` | `6057a461…d8814` | `a_realistic_high_resolution_interior_living_room.png` |

**Filename note.** The BEFORE file was saved by accident under the older "Reveal" filename (founder statement, 4 Nov 2026).
- It is identified by its content and sha256, never by that filename.

**Provenance.** Both masters are ChatGPT (OpenAI) outputs.
- Each carries a signed C2PA credential recording `trainedAlgorithmicMedia`.
- The claim signature and the data hash verify.
- The reader does not trust the signing certificate (`signingCredential.untrusted` / `invalid`). This is the same state as other OpenAI credentials in the register.
- **Signing times:** the BEFORE was signed at 15:17:07 UTC and the POSSIBLE at 15:12:03 UTC.
- No input image is recorded.
- The relationship between the two images is not asserted.
- Prompts are UNAVAILABLE.
- Reference disclosure is UNCERTAIN.

**Routine edits only** (Rule 3). Every web copy was made by `atlas-tools/build-disc020-images.py` and is recorded as a derivative of its master. The edits are:
- Lanczos resizes;
- WebP and JPEG encodes;
- one 4:5 phone crop at x 450–1200, applied identically to both images, which keeps the stair and the whole lift in view;
- two Library card WebPs;
- a 1200 × 630 social card from the POSSIBLE.

Nothing is generated or retouched; neither master carries a visible generator mark.

**Alignment.** The pair shares one geometry (1678 × 937). Strong pixel change is confined to columns 895–1168 (the lift). Outside that band, the mean absolute difference is 5.7–8.7 out of 255.

## Content limits applied (founder Phase 2 instruction)

**Hero.**
- Shared `pn-compare`, opening at 100% BEFORE.
- Disclosure: "Illustrative AI-generated visualisation. Not an actual installation."
- One visible title on phones and portrait tablets, with a single H1.

**Lift types.** Four ways up (A–D), drawn as PlotNua SVGs labelled "not to scale".
- Statements that come from manufacturers are marked **Maker claim**.
- No technical specification or price is invented.

**Grants.**
- Housing Adaptation Grant: €40,000 maximum, income bands, €20,000 for houses under 12 months old.
- Mobility Aids Grant: €8,000, for incomes up to €37,500.
- Both are stated with their means test and approval-first rule, from gov.ie and local authority pages checked on 4 Nov 2026.
- Revenue's VAT refund is described as naming stairlifts only; other items are case by case.

**Planning and fire.**
- Planning: interior-only works are generally exempt (s.4(1)(h)), but not automatically for a protected structure (s.57). External shafts need their own assessment. A Section 5 declaration is available.
- Fire: TGD B Vol 2 (1.3.3 protected stair where a floor is above 4.5 m; 3.7 protected openings). The page leaves the design to a competent professional.

**Price.**
- One advertised figure: €11,000–€19,000, from Stairlifts Access Lifts (accesslifts.ie). It is undated, so the date recorded is the check on 4 Nov 2026.
- It is labelled as an advertised figure and not a quote, with what may change the cost.
- No UK figure is shown.

**Suppliers.**
- No supplier gallery, supplier link or partner claim.
- Supplier research stays private.

**Homeowner route.**
- Standard `pn-two-route`. Route B is the existing WhatsApp conversation, "Free for homeowners."
- No form, no Atlas Journey.

**Library.**
- Category **Space**. Neither "Future Ready" nor "Home" exists as a Library category, and none was created.
- No action label; AI chip from the declared record.

## Integration

**Registries and builders:**
- registries: identity, header, Premium registries;
- search rail scope 30;
- `prove-compare-hero` pages;
- AI disclosure below;
- Library images and labels;
- card counts 17;
- sitemap;
- search index (possibilities 22).

**Shared-builder changes:**
- `build-library-card-webp.py` now also accepts a plain resize (`optimise`) of a declared, mark-free master as the card's `<img>`. It still requires a single routine edit and card WebPs recorded from that master.
- Count literals were updated to 17.

**New proof:** `atlas-tools/prove-disc020-page.py`, S1–S17. Its capability test caught 16 of 16 planted faults.
