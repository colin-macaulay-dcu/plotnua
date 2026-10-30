# PlotNua Governance 2.0

**Founder directive:** 30 October 2026. **This is the authoritative development and publication policy.**

**Older records are history.** That includes freeze records, founder decision records, release reports and exception records. They remain readable, but they block nothing that this document allows.

**Principle:** if an image is suitable, PlotNua has the right to use it, and the site works, it should be straightforward to publish.

---

## Rule 1 · Image rights

- **Supplier imagery stays within the permission received:**
  - its scope;
  - its required credit;
  - its surfaces;
  - its conditions (for example "unmodified" or "no implied endorsement").
- **Supplier-specific conditions and publication holds are never overridden.** Examples: TimberIN, OGNYX, BIOBUILDS containment, Powersheds, preview-only suppliers, and the Living in the Garden provenance hold.
- **PlotNua's own and properly licensed images need no further approval.** That covers AI illustrations, the founder's own work and licensed stock.
- **Enforced by** the Image Rights Gate (supplier grants, manifest, containment). It is unchanged.

## Rule 2 · AI imagery

- **No individual founder signatures.**
- **How origin is established:** from the image's own verifiable metadata (an embedded C2PA credential recording an AI generation) or from an existing project record.
- **Tool:** `atlas-tools/declare-ai-from-metadata.py` declares the picture and records exactly what the credential says.
- **Unknowns stay unknown.** No invented prompt and no "no references" claim. Unidentified inputs are disclosed as such.
- **No metadata and no record means no declaration.** The picture stays undeclared and unlabelled. Provenance is never inferred from appearance.
- **Every declared AI illustration carries the label** "AI-generated illustration".
- **AI illustrations are never presented as a named supplier's product.**

## Rule 3 · Image editing

**Routine edits of authorised images need no exception or signature:**
- cropping;
- resizing and optimisation;
- colour correction;
- background adjustment;
- removal of incidental artefacts;
- preparing Before / Possible pairs.

**How an edit is recorded:** as a derivative, with a method from the closed list, a one-line description and the sha256 of its unchanged source.

**Never allowed:**
- removing third-party copyright notices or required credits;
- editing supplier imagery beyond its grant (re-encode or resize only, unless the grant says otherwise);
- deriving from a held source;
- upscaling.

## Rule 4 · Website development

- **Routine visual and technical improvements** need no freeze amendment and no separate governance record.
- **What stays guarded:** commercial, legal and supplier-specific content, by the existing content guards. Examples: DISC-026 claims, supplier credits, price data, Atlas and search contracts, privacy pages.

## Rule 5 · Deployment

1. The founder approves the task.
2. Claude implements it.
3. Claude runs the essential checks (below).
4. The founder reviews the result.
5. The founder approves production deployment.

Deployment is a fast-forward of `main` (never forced), followed by a live check. **There are no other approval stages.**

## Essential checks (every release)

1. **Image Rights Gate:** all steps green. It covers supplier rights, provenance (P1–P14) and the content guards.
2. **The page's own guards:** for example the hero-slider checks, or the DISC-026 claims proof.
3. **A real-browser check:** desktop and phone, interaction, no errors, accessibility (axe).
4. **Scope:** nothing outside the task changed.

---

## What changed on 30 October 2026

| Was | Now |
|---|---|
| AI declarations needed a founder-attested pin, a founder signature, a named human review and a resemblance review | **Verified metadata is enough** (validator P5, form `origin: C2PA_EMBEDDED`). Existing pinned records stay valid. |
| Only WebP re-encodes and resizes were allowed as derivatives. Any other edit needed a hash-pinned exception. | **Routine edits are allowed** (validator P12): crop, optimise, colour-correction, background-adjustment, artefact-removal, pair-preparation. Still hash-bound; never for supplier imagery; never from a held source. |
| Every DISC-026 article change needed a freeze record (V1–V7, the same-commit rule, enforced by GL12) | **Freeze-hash rule retired.** V1–V7 are history. GL12 keeps its GridNua link check; the DISC-026 content proof keeps the claims. |
| Hero derivatives needed a recorded "lineage basis" (`build-hero-webp-derivatives.py`) | **Superseded by P12.** That builder already fails on production because of the homepage Reveal slot, and it is no longer part of the release. |
| A multi-stage approval chain (preview, signature, exception, freeze and release approvals) | **Rule 5.** |

**Kept unchanged (essential safeguards):**
- **The Image Rights Gate:** every supplier grant, containment and credit step.
- **The provenance ratchet (P1):** every published image must be accounted for.
- **Anti-laundering (P6).**
- **AI images:** no AI on product cards (P7); a label on every declared AI image (P8); never beside a supplier's name (P10).
- **Provenance never grants a permission (P11).**
- **Provenance holds** (`derivative_holds`).
- **The release reader:** it releases only the exact commit's own green run.
