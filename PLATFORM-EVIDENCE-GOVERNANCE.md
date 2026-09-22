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

Christophe Doye (Head of Partnerships) is expected to contact PlotNua through
the existing commercial route. **PlotNua does not initiate contact.** If fee
mechanics or ROI host protection are answered, those answers are recorded as
new claims with `provenance: SUPPLIER_PROVIDED` and `claim_basis: STATED` —
never promoted to OPERATIONAL, never merged into a PUBLIC_PRIMARY claim.

## 5 · Deferred governance debt — not addressed here

`Organisation Atlas Certification Audit v1` (`fldsmSYpVRJMkVjsW`) references
only `Notes` and `Status`. It restates a hand-set field and **has no completed
state for any Organisation** — product or platform. It is not product-
dependent; it is simply unimplemented. Requires later governance attention.
Deliberately not redesigned in this task.

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
