# Hero image provenance verification: SEO Phase 1b (16 Oct 2026)

**Status:** EVIDENCE RECORD. Nothing is declared, classified or granted by it. `image-provenance-records.json` is unchanged: all six images stay LEGACY_UNDECLARED. No supplier image right was touched. Phase 1b is not deployed.

Machine-readable evidence: `governance/hero-image-content-credentials-evidence-2026-10-16.json`.

## Correction to the Phase 1b report

The Phase 1b report called these six images "PlotNua's own Discovery artwork". That wording went beyond the evidence and is withdrawn. Being published on plotnua.ie proves neither ownership nor permission.

## What the records establish

This time I read the signed C2PA Content Credentials embedded in the files: in the deployed files themselves and in the masters on the Mac. Two points matter:

- **This is not inference from appearance.** Each credential is a cryptographically signed statement by the generating service.
- **The 11 Oct recovery missed it.** That recovery read only EXIF tags, so it reported "0 assets with embedded metadata".

| Hero | Deployed file | Master (link) | Signed credential | What it says |
|---|---|---|---|---|
| Home | 9785fd99….jpg | The-Future.jpeg (byte-identical) | **In the deployed file**, Google LLC, 20 Aug 2026 | "Created by Google Generative AI" + SynthID watermark. No input images. |
| Hidden Bins | 9805382f….jpg | DISC-029-IMAGE-01-PROBLEM-MASTER.jpeg (byte-identical) | **In the deployed file**, Google LLC, 15 Sep 2026 | Same. No input images. |
| Driveway Income | b5cbac3f….jpg | DISC-014 Image 01 — Potential Asset.jpeg (perceptual match 0/256) | In the master only, Google LLC, 10 Sep 2026 | Same. No input images. The deployed copy is a re-encode with the credential stripped. |
| Living in the Garden, overlay (Today) | 5e17a24f….jpg | DISC-008-01-Recognition.png (match 0/256) | Master, Google LLC, 9 Aug 2026 | Created by Google Generative AI, then "Added visible watermark". No input images. |
| Living in the Garden, base (Possible) | 8c60a8f2….jpg | DISC-008-02-Opportunity.png (match 0/256) | Master, Google LLC, 9 Aug 2026 | Created by Google Generative AI from **two inputs**: (1) the DISC-008-01 generation; (2) **"Input ingredient 1", which carries no credential of its own and is unidentified**. The visible generator mark is also on the live file. |
| Garden Retreat | 7d5f5718….jpg | DISC-001-Hero-MASTER.png (match 0/256) | **None on the master** | A near-identical 1376 px predecessor, DISC-001-Hero.png, carries a Google LLC credential dated 1 Aug 2026: "Created by Google Generative AI", no inputs. The 1408 px master is a slightly wider version of it, and how that version was made is undocumented. |

## Answer to the founder's four categories

1. **Original PlotNua-created artwork: none.** No image is human-made artwork or a PlotNua photograph.
2. **AI-generated artwork: all six.** It is established by signed credentials for five, and for Garden Retreat by a credentialed near-identical predecessor. Every one was made with Google Generative AI.
3. **Licensed third-party imagery: none.** No licence or stock record exists.
4. **Insufficiently documented: all six, for authorisation.** The register's rule for declaring an AI illustration (P5) still lacks:
   - **Generation context, for all six:** which Google service and account made them, and the terms in force at the time. No record exists; `07 Legal` is empty.
   - **The prompt, for all six:** none is recorded anywhere.
   - **A named human review, for all six.** This is a founder attestation that the image reproduces no supplier photograph or identifiable product design.
   - **The second input to the Living in the Garden "Possible" plate (8c60a8f2):** what "Input ingredient 1" was. Until it is identified, the anti-laundering rule cannot be confirmed for this image.
   - **The Garden Retreat edit step (7d5f5718):** how DISC-001-Hero-MASTER.png was produced from the credentialed DISC-001-Hero.png.

Declaring any of them as AI_ILLUSTRATION also brings a visible "Illustration" label on the pages, under P8. That is a website and editorial decision for the founder.

## Two further findings

- **Phase 1b strips Content Credentials.** The home and Hidden Bins hero JPEGs carry their Google credential on the live site today. Their WebP derivatives don't, because re-encoding drops the C2PA manifest. A valid credential can't be copied across: it is bound to the exact bytes, and re-signing would need a PlotNua signing certificate. On the WebP copies, the machine-readable "AI-generated" statement would be lost. The pixel-level SynthID watermark is designed to survive re-encoding, but I can't verify that here.
- **The register's recovery claim is wrong in a way that matters.** 18 of the 110 backlog assets carry signed credentials: 17 from Google Generative AI and 1 from OpenAI (the Atlas brand image). The recovery tool should read C2PA. If it did, the register builder's G1 would correctly refuse to proceed until a person declares those assets. Proposed only; not changed here.

## Deployment recommendation

**Hold Phase 1b.** The WebP copies add no new rights exposure, because they are the same pictures already live as JPEGs. But two things should be settled first:

1. **The founder supplies, or accepts as unrecoverable, the missing declaration items above.** The second input to the Living in the Garden "Possible" plate is the one that matters most.
2. **A decision on Content Credentials.** Either:
   - (a) serve the original JPEG, not a WebP, for the two heroes that carry live credentials (home and Hidden Bins). That keeps four WebP heroes and gives up the two largest gains; or
   - (b) accept that the WebP copies drop the credential, and record that decision.

Once both are settled, Phase 1b can deploy unchanged, or with (a) applied as a small builder change.
