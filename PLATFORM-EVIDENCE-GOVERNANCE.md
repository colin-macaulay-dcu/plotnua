# PlotNua — Platform Evidence Governance

Recorded 2026-09-22. Closes the controlled cross-category platform experiment.

## 1 · Canonical evidence model

The existing PlotNua evidence-manifest **decomposition remains canonical**:
`authority` · `source_type` · `evidence_type` · `verification_method` ·
`verification_status` · `maturity` · validity/staleness · `provenance` ·
`homeowner_safe` · `logic_safe`.

The parking pilot's flat `evidence_state` vocabulary is **withdrawn as a stored
field**. A simplified label (`evidence_state_derived`) is computed from the
dimensions above at generation time, for display only. It is never hand-set and
never the stored truth.

## 2 · claim_basis

| Basis | Meaning |
|---|---|
| **STATED** | PlotNua established that the cited authoritative, primary or first-party source **currently states or provides** the claim. |
| **OPERATIONAL** | PlotNua has evidence the claimed behaviour **actually occurs or operates** in practice. |

**STATED is not a weaker grade.** For legislation, contractual terms and other
operative instruments the published text *is* the operative thing — a parking
contract does not describe its cancellation policy, it constitutes it. Such
claims are legitimately decision-useful and may be logic-safe.

**No claim may be marked OPERATIONAL without actual operational evidence.**
As at this date, **all 75 claims across all three manifests are STATED**;
none is OPERATIONAL, because PlotNua holds no operational evidence about any
platform.

## 3 · Platform completion

**Dimensions:** Identity · Route · Jurisdiction · Commercial Terms ·
Protection · Exit · Currency.

**Rule:** a VERIFIED or evidenced **negative may satisfy** a dimension
("this platform offers no host protection", established, is an answer).
**UNKNOWN does not satisfy** a dimension.

**Completion means:** *PlotNua has enough current evidence across the
decision-critical dimensions for a homeowner to understand the route, the
material terms, the material protections and limitations, and the material
remaining uncertainty, sufficiently to make the next decision.*

**Not a mechanical 7-of-7 count.** A non-critical unknown does not prevent
usefulness; a decision-critical unknown may prevent completion. Completion is
a judgement made by a person against the sentence above.

**YourParkingSpace (Ireland) Limited — completion UNRESOLVED.** Established:
Identity, Route, Jurisdiction, Exit, Currency. Open and material: **host fee
rate** (Commercial Terms) and **ROI host protection** (Protection). A
homeowner cannot work out what they would receive, or whether they are
covered.

## 4 · Supplier-provided evidence

Where a platform answers a question directly, that answer is recorded as a new
claim with `provenance: SUPPLIER_PROVIDED` and `claim_basis: STATED` — never
promoted to OPERATIONAL, and never merged into a `PUBLIC_PRIMARY` claim.

**Private commercial correspondence and relationship status are maintained
separately from publicly served evidence artefacts.**

## 4a · PUBLIC DISCLOSURE FIREWALL

Evidence artefacts in this repository are served from the site root and are
**publicly fetchable**. Publication is therefore a disclosure decision, not
only an engineering one.

> **PUBLIC EVIDENCE ARTEFACTS MUST NOT CONTAIN PRIVATE COMMERCIAL
> CORRESPONDENCE OR INTERNAL RELATIONSHIP STATUS.**
>
> Where commercial correspondence contributes to internal knowledge, it
> remains separately governed and must not become publicly fetchable merely
> because an evidence artefact is published.

A publicly served artefact **may** carry: public primary-source evidence,
governed claim states, public organisation and platform facts, public source
URLs, evidence limitations, and public provenance.

It **must not** carry, merely because PlotNua knows it internally: private
correspondence, negotiation or outreach status, expected third-party contact,
individuals named from private commercial conversations, internal Airtable
record IDs, or other non-public relationship intelligence.

The `COMMERCIAL_CORRESPONDENCE` provenance correctly stops such a claim
reaching a *homeowner*. It does not stop a published file being *fetched* —
which is why placement, not only labelling, is governed. Enforced by the
public-disclosure firewall tests in
`.github/scripts/test_public_disclosure_firewall.py`.

## 5 · Deferred governance debt — not addressed here

The `Organisation Atlas Certification Audit v1` formula references only the
Organisation's `Notes` and `Status` fields. It restates a hand-set field and
**has no completed state for any Organisation** — product or platform. It is
not product-dependent; it is simply unimplemented. Requires later governance
attention. Deliberately not redesigned in this task.

*(Internal field identifiers are omitted here by the public disclosure
firewall in §4a. They are held in the internal Atlas schema record.)*

## 5a · FIRST-PARTY RULE FOR GRANTS AND FINANCIAL-SUPPORT AMOUNTS — ACTIVE

Recorded 2026-10-04. **Platform-wide. Not DISC-026-specific.**

> **NO IRISH GRANT OR FINANCIAL-SUPPORT AMOUNT ENTERS PLOTNUA FROM A SECONDARY
> SOURCE.**

Secondary sources — installer sites, comparison sites, trade press, aggregators —
**may be used for discovery**: to learn that a scheme exists, that it changed, or
that it is worth checking. They may not be the source of a published figure.

Before any of the following reaches a homeowner-facing surface or a governed
evidence record, it must be verified against the **current responsible
authority's own first-party source**, with that source's URL and the read date
recorded:

- a grant or financial-support **amount**;
- an **eligibility threshold**;
- an **application or scheme date** (opening, closing, deadline);
- a **property-age condition**;
- a **technology requirement**.

**Why this is a rule and not a preference.** In a single week of DISC-026
research, secondary Irish sources were wrong three times on figures that would
have been published:

| Secondary source said | The authority's own page says |
|---|---|
| Heat pump grant maximum **€12,500** | **€14,500** bundle ceiling (SEAI) |
| Heat Loss Indicator threshold **2.0** | **2.3 W/(K.m²)** (SEAI) |
| Ground-source grant **"up to €6,500"** | €6,500 is the **replacement** heat-pump cap; the bundle ceiling is **€14,500** (SEAI) |

Each error favoured a plausible-sounding, wrong number. A homeowner acting on any
of them would have mis-planned their money.

**Retrospective application is NOT authorised by this rule.** Existing evidence
records are not to be altered merely to apply it. The rule governs what enters
from now, and applies on the normal recheck cycle.

## 6 · Scale gate — ACTIVE

| | State |
|---|---|
| Second parking platform | **HOLD** |
| Home Exchange platform population | **HOLD** |
| Atlas Record Type | Not introduced. Architecture question remains **OPEN** |

Both preconditions for lifting the hold are now met by this record: the
canonical vocabulary is established for the existing pilot, and the platform
completion rule is recorded. **The holds nonetheless remain in force until the
founder lifts them explicitly.**
