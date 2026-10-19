# Possibility Reveal homepage images: provenance recording sheet
19 October 2026 · **For the founder to complete.** Nothing here is a declaration yet.

## Why this is needed
The homepage Reveal shows nine image files: three widths, each as AVIF, WebP and JPEG. All nine are encodings of the founder-locked **L1 + L2A** composite (pixel SHA-256 `5dd29abe…88a0`). The encoding record is `assets/possibility-reveal/img/encodings.json`.

Under the image-provenance register, a new published image must be declared as an `AI_ILLUSTRATION`. The guard (`validate-image-provenance.js`, rule P5) requires a declaration to carry:
- the tool and date;
- the **prompt, word for word**;
- an explicit list of **reference inputs**;
- a **named human review**.

The guard (P1) refuses the homepage until all nine are declared. That refusal is correct, and the guard has not been changed.

## What the records already establish
Sources: the lock records, the two signed Google C2PA manifests (read 19 Oct 2026, copies in `governance/c2pa-source-credentials/`) and the encoding record.

| Step | Evidence | Gap |
|---|---|---|
| BEFORE, generation 1: 17 Oct, 20:37:03 UTC | Google LLC credential: "Created by Google Generative AI" from **one input image** | **The input image is not identified.** The prompt is not recorded. |
| BEFORE, generation 2: 17 Oct, 20:39:14 UTC | Google LLC credential: an edit of generation 1, giving the 1× original `7d8d6296…b9d0` | Prompt not recorded |
| BEFORE master | A Lanczos upscale, verified pixel-identical | — |
| L1 candidate 2: 17 Oct, 21:52:42 UTC | Google LLC credential: "Created by Google Generative AI" from **one input image that carries no credential** | **The input is not identified.** It was meant to be the 1× original, but that file carries its own credential and this ingredient has none, so the credential can't confirm it. The prompt is not recorded. |
| L1 composite, L2A objects | Deterministic build tools. No generation step and no reference images recorded. | — |
| Nine web encodings | `build-possibility-reveal-images.py`: re-encode bit-identically from the locked master | — |

## Please record (word for word, from your Gemini history)
1. **BEFORE, 20:37.** What image did you upload: a sketch, a photograph of your own, an earlier generation, or something else? Was it in any way a supplier's or another third party's photograph? Then give the prompt, word for word.
2. **BEFORE, 20:39.** The prompt, word for word.
3. **L1 candidate 2, 21:52.** What image did you upload? For example, the 1× original, a re-saved copy of it, or a screenshot. Then give the prompt, word for word. On 17 Oct I recommended a candidate 2 prompt; please confirm whether you pasted exactly that one, or give the one you used.
4. **The Google service and account** used (Gemini app, AI Studio or other). Have you confirmed that its terms allow commercial use on a website? This item has been open since 16 Oct.
5. **Human review.** Your name, the date, and whether you can attest to the following (edit it if you wish):
   > *I reviewed this image. It is an AI-generated illustration of a generic house and garden. It reproduces no supplier's photograph and no distinctive product design, depicts no named product or organisation, and no third party's photograph was given to the tool as an input.*
6. **Caption.** When the images are declared, rule P8 requires the page to carry the register's approved label exactly: **"AI-generated illustration"**. The caption under the Reveal currently reads "Illustration, AI-assisted composite."
   - Approve changing it to "AI-generated illustration", or keep the current wording and ask for the register label to be amended.
7. **Policy.** `AI-ILLUSTRATION-POLICY-PROPOSAL-2026-10-11.md` is still marked PROPOSAL. Please confirm that it is approved for these nine images, or record an exception.

## If an input can't be identified
The 17 Oct rule for the Living in the Garden "Possible" plate applies: an unidentified input is treated as possibly third-party, and the image is **held**.

In that case the homepage can't publish these images. The honest options are:
- regenerate BEFORE (and therefore L1–L5) from documented inputs;
- or keep the current production hero until the inputs are identified.

## When this is complete
I will:
1. move the nine drafted records (`governance/POSSIBILITY-REVEAL-PROVENANCE-DRAFT-2026-10-19.json`) into `image-provenance-records.json`, with your answers;
2. apply the caption decision;
3. run the full gate.

Nothing in this sheet grants any image permission. Provenance is never evidence of rights.
