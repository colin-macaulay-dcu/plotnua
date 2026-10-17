# Hero image provenance: resolution for SEO Phase 1b (17 Oct 2026)

**Status:** the founder's 17 Oct instruction is applied on branch `seo-phase1b`. **Not deployed.**

`image-provenance-records.json` still holds all six sources as LEGACY_UNDECLARED. Nothing is declared authorised, and no supplier permission is inferred. The image-rights gate and the provenance ratchet are unchanged. Backlog: 110.

## 1. Living in the Garden "Possible" plate (8c60a8f2): second input NOT identified, so HELD

**What the signed credential records.** The master is DISC-008-02-Opportunity.png. It was made by Google Generative AI on 9 Aug 2026 at 18:37 UTC from two inputs:

- **Input ingredient 0:** the DISC-008-01 generation. Manifest `urn:c2pa:6ca39d5f…`, the same manifest carried by DISC-008-01-Recognition.png.
- **Input ingredient 1:** this entry records only its role ("inputTo") and the label "Input ingredient 1". It has no manifest, format, title, content hash or thumbnail. The credential holds nothing that could identify it.

**What was searched:**

- **Every image in the connected PlotNua folder:** 1,101 files, including Archive, Temporary and the deploy copies. I compared them against the whole "Possible" image and against the region where the home was added (x 218–896, y 201–415). No candidate. The closest region distance was 96/256. A match would be near 0, and unrelated pictures typically score 100–130.
- **Project docs, the image library map, the social register and the Discovery records:** none records how DISC-008-02 was made or what it was given.
- **Past Claude conversations:** none. The generation happened in a Google tool, outside Claude.

**Limits:** Images outside the connected folder (Downloads, Photos, the web) and supplier imagery held only as remote URLs were not searchable from here.

**Conclusion:** unidentified. Under the anti-laundering rule, the input must be treated as possibly third-party. **8c60a8f2 keeps the provenance hold. It gets no WebP derivative, and the page keeps serving the original JPEG.**

## 2. Garden Retreat (7d5f5718): edit history ESTABLISHED

- **The source:** DISC-001-Hero.png (1376 × 768, 1 Aug 2026). It carries a signed Google C2PA credential: "Created by Google Generative AI", SynthID, no input ingredients.
- **The edit:** DISC-001-Hero-MASTER.png (1408 × 768, 26 Sep 2026) is exactly that image mirror-extended by 16 px on each side.
  - The centre 1376 columns are pixel-identical (maximum difference 0).
  - The left and right 16 px strips are the edge columns reflected, also with maximum difference 0.
  - No generative fill, no retouching, no stretching.
- **The documented step:** commit `08237ff` (Colin MacAulay, 26 Sep 2026, "Release DISC-001 Garden Retreat"): *"Four approved images, each mirror-extended from the founder source to the 1408 plate without stretching."*
- **Why the master has no credential:** it is a bare RGB PNG with no metadata chunks, which is consistent with being written programmatically. Its three sibling masters share the same timestamp (26 Sep, 09:53).
- **The deployed file:** 7d5f5718cf9cd3da.jpg matches the master at 0/256.

**Conclusion:** the lineage runs from a credentialed Google AI generation to a verified, deterministic mirror-extension to the deployed JPEG. It is established.

## 3. Content credentials

- **Originals preserved.** All five released sources stay byte-identical on the site and remain the `<picture>` fallback. The home and Hidden Bins JPEGs keep their embedded signed Google credentials.
- **Re-encoding removes credentials.** WebP re-encoding removes the embedded C2PA credential. **The derivatives carry no signed credential.** Each derivative record says so (`content_credentials.derivative_embeds_c2pa: false`), and the builder refuses any derivative that contains C2PA data. A copied manifest would be invalid for the new bytes.
- **Credentials retained for the project.**
  - Full credential reports for the six masters, the Garden Retreat predecessor and the two credentialed deployed files are in `governance/c2pa-source-credentials/`.
  - The summary evidence is in `governance/hero-image-content-credentials-evidence-2026-10-16.json`.

## 4. Decision table

| Source | Lineage | WebP derivative |
|---|---|---|
| Home `9785fd99` | Signed credential in the deployed file | **Can proceed** (2 files) |
| Hidden Bins `9805382f` | Signed credential in the deployed file | **Can proceed** (2 files) |
| Driveway Income `b5cbac3f` | Signed credential on the master, match 0/256 | **Can proceed** (2 files) |
| Living in the Garden "Today" `5e17a24f` | Signed credential on the master, no inputs | **Can proceed** (2 files) |
| Garden Retreat `7d5f5718` | Credentialed predecessor + verified mirror-extension | **Can proceed** (2 files) |
| Living in the Garden "Possible" `8c60a8f2` | Unidentified second input | **HELD.** Original JPEG only |

"Can proceed" means only that the derivative's lineage is adequately established for a format re-encoding. It does **not** declare the image authorised: all six stay LEGACY_UNDECLARED, and the prompt, account/terms and human-review items from the 16 Oct record remain open.

## 5. Guard changes (tighten only)

- **P12 now also refuses:**
  - a derivative of any source listed in the register's `derivative_holds`;
  - any derivative that claims an embedded credential.
- **Capability proof:** two new cases, 45/45 proved.
- **Builder:** carries the hold. Its `--check` refuses if a held source has a derivative on disk or on any page.
