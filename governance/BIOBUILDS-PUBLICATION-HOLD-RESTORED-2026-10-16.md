# BIOBUILDS · PUBLICATION HOLD RESTORED

**Decision reference: revokes `FX-BIOBUILDS-PUBLISH-20261011`**
Founder instruction, Atlas Population Phase 2, 16 October 2026:
"BIOBUILDS: correct the five products incorrectly marked PUBLISHABLE and
preserve the supplier's explicit pre-publication review requirement. Prepare
the repository correction. Do not deploy until final founder approval."

**PREPARED, NOT DEPLOYED.** Branch `atlas-p2-biobuilds-hold`, based on `origin/main` aeeb844 (the deployed line), delivered as a patch. Nothing pushed.

## What changes

| File | Change |
|---|---|
| `image-rights-records.json` (BIOBUILDS row only) | `founder_exception` removed and preserved verbatim under `founder_exception_revoked.original`; `public_visibility` PUBLISHABLE → HOLD; `hold_reason` → `listing-review-awaiting-confirmation`; `waived_conditions` → [] |
| `image-rights-manifest.json` | Regenerated with `.github/scripts/generate_image_rights_manifest.py` (CI requires it to match the records). Only the BIOBUILDS row and the generated date change. |
| `additional-home-universe-v1.json` | The 5 BIOBUILDS products (Wanderlust, Serenity, Nest 24, Sanctuary, Bloom): `publicVisibility` HOLD, `holdReason` set, `imagery`/`imagerySet` null; `publicationGate.heldOrganisations` = ["BIOBUILDS"]. Exactly what the generator now derives. |
| `search-index-v1.json` | Rebuilt with `atlas-tools/build-search-index.py`; no BIOBUILDS entry remains. |
| `discovery-living-in-the-garden.html` | Maker explorer rebuilt (`build-maker-explorer.py --apply`): BIOBUILDS no longer listed in the Garden Homes tab (24 products, 9 makers). |
| `atlas-tools/build-maker-explorer.py` | Additional Home public figure now read as ELIGIBLE and PUBLISHABLE (as the wellness tab already is), with a cross-check that eligibleCount = publishable + gated. Without this, G1 refuses any page build while any Additional Home supplier is on HOLD. |
| `atlas-tools/build-publication-gate-records.py` | Exception no longer passed to the derivation; writes `founder_exception_revoked` instead. |
| `prove-supplier-publication-gate.mjs` (PG11), `-capability.mjs` (C-PG1), `prove-biobuilds-imagery.mjs` (BI11) | Re-aimed to assert the HOLD, as they were re-aimed on 11 October to assert the publication. |

## What does NOT change

- The BIOBUILDS **permission** (GRANTED 2 Oct 2026), its evidence, its seven conditions, `listing_review` (still AWAITING_CONFIRMATION), `asset_approval` and the 10 enumerated `approved_assets`.
- No image permission is added, removed or widened. The supplier's pre-live review requirement stands and is again binding.
- Imagery: held products receive no imagery, by the generator's own rule. `biobuilds-preview.html` (private, noindexed) is untouched.

## Known residuals

- `atlas-tools/verify-biobuilds-publication.mjs` and `deploy-biobuilds.sh` verify the
  revoked 11 October publication and now refuse (V4, V11). That is the correct
  outcome: they must not be used to re-publish. Neither runs in CI.
- `build-publication-gate-records.py` carries stale constants (6 approved assets,
  narrower exception scope) that pre-date the 11 October widening. It was NOT
  re-run for this change; the records row was edited surgically to avoid
  regressing the asset enumeration. Do not re-run it until that is reconciled.
- The rights row's condition text still contains the sentence describing the
  11 October supersession. It is grant text and was deliberately not edited.

## Verification (16 Oct 2026, on the branch)

Every CI command in `.github/workflows/*.yml` that runs locally without an Airtable token
(17 commands) exits 0 on the branch, including: PG suite 16/16; PG capability 18/18
mutations caught; BIOBUILDS containment + capability; OGNYX imagery containment +
capability; preview-only containment + capability; manifest matches records; wellness
universe tests; garden-retreat restructure; maker explorer --check (G1-G11) and
navigation; wellness publication records --check. Also: image-rights gate scan PASS,
gate self-test PASS, search guards 11/11, Results publication gate PASS.

Pre-existing failures on `origin/main` itself, unchanged by this patch and not in CI:
`prove-biobuilds-imagery.mjs` (7 of 14 fail on the base; BI11 re-aimed here),
`prove-search-acceptance.mjs` A5d, `build-404-search.py --check` and
`build-search-rail.py --check` (baseline hash drift).

## Return path

BIOBUILDS becomes PUBLISHABLE again only when Mateus confirms the corrected
listing (`listing_review.state` → CONFIRMED with a date), or by a new, separately
dated founder decision.
