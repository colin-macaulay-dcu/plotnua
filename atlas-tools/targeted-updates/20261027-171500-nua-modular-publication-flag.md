# Targeted correction — Nua Modular publication flag (Additional Home)

- Founder decision: "ATLAS DATA CORRECTION AND PRIVATE PREVIEW RELEASE", 27 Oct 2026 17:11,
  approval "strictly limited to the stale publication status". NOT approval to publish
  Nua Modular as a supplier, and not a commercial change.
- Organisation: `recuvqPv7XW0b0PFJ` (Nua Modular, ORG-000194)
- Product: `rec69fv1mZSlnuEt0` (Nua Ultra, PROD-000932)
- File: `additional-home-universe-v1.json` (generated 2026-10-11T20:42:38Z)
- Tool: a single scoped edit with a JSON boundary proof. `publish-targeted-update.py`
  refuses Additional Home products by design (they need their own regeneration),
  and a full regeneration would have touched every other supplier.

## Why

The file was generated on 11 Oct 2026, before the 14 Oct fail-closed correction to the
publication gate. Nua Modular had no rights record and is not in
`atlas-tools/publication-gate-legacy-baseline.json`, so under the current rule it derives
HOLD; its PUBLISHABLE flag was a pre-safeguard leftover, not a decision. Its rights record
(added 27 Oct, `PREVIEW-NUA-MODULAR-20261027`) grants imagery and product information for the
PlotNua presentation only, with no "feature" (public listing) scope, and derives
`permission-scope-excludes-listing`. `prove-supplier-publication-gate.mjs` PG2 refused the
disagreement.

## Exact change

| Field | Before | After |
|---|---|---|
| products[`rec69fv1mZSlnuEt0`].publicVisibility | `PUBLISHABLE` | `HOLD` |
| products[`rec69fv1mZSlnuEt0`].holdReason | `null` | `permission-scope-excludes-listing` |
| publicationGate.heldOrganisations | `["BIOBUILDS"]` | `["BIOBUILDS", "Nua Modular"]` (sorted, as the generator emits it) |

sha256 before `0e8d985b6fb0d89c3979ae663b26273b4fc7a40e5edd221f6b3ce99f43f0edcb`
sha256 after  `020ffa037c295d2afee2ba3df17f619c8599fc794273200e983400fff57ff59f`

## Unchanged (proved by a field-by-field comparison of all products)

- Every other product, byte-for-byte in value; every header count (eligible 28, held 112, …).
- Nua Ultra's qualification: **HELD**, `habitation-unconfirmed`; its Class 3A assessment,
  specifications, area evidence, sources, description, imagery (null).
- Supplier details, the image-permission scope, commercial terms, public Discovery content.
- `search-index-v1.json`: not rebuilt. It indexes only PUBLISHABLE and ELIGIBLE products and
  Nua Ultra was never ELIGIBLE, so its content cannot change; its recorded
  `sourceAdditionalHomeSha256` (recorded, not pinned) still names the pre-correction file.

## Effect on homeowners

None. Public Additional Home products (PUBLISHABLE and ELIGIBLE): 24 before, 24 after;
Nua Modular: 0 before, 0 after. Nua Ultra stays absent from homeowner results, now behind
two independent locks (habitation and publication).
