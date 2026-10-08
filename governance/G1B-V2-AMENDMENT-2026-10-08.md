# G1B POST-FREEZE AMENDMENT — PRIVACY VERSION V1 → V2

**Date:** 8 October 2026
**Status:** CLOSED — applied, proven, pending founder commit authorisation
**Authority:** founder decision, 8 October 2026
**Amends:** [`G1B-BORROWED-GARDEN-CONTRACT.md`](G1B-BORROWED-GARDEN-CONTRACT.md) (FROZEN 7 October 2026)
**Produces:** [`PRIVACY-VERSION-2026-10-PHASE2-V2.md`](PRIVACY-VERSION-2026-10-PHASE2-V2.md)

This is a **dated post-freeze amendment**, not a rewrite. G1B's own text is left
historically accurate: it froze `2026-10-PHASE2-V1` on 7 October 2026, and it
still says so. This record carries the change.

---

## 1 · What G1B originally froze

G1B froze **`privacy_version = 2026-10-PHASE2-V1`** on 7 October 2026, with the
homeowner submission notice approved and three founder copy corrections applied.
That remains the accurate historical record and is not altered.

---

## 2 · The position at supersession

| | |
|---|---|
| V1 used for a genuine submission? | **No. Never.** |
| Gardens | 0 |
| Growers | 0 |
| Status log | 0 |
| Consent proofs | 0 |
| Incidents | 0 |
| `WRITES_ENABLED` | `"false"` |
| `EMAIL_ENABLED` | `"false"` |
| `INTEREST_PUBLIC` | `false` |

V1 was exercised only by G5's synthetic controlled-write proof, after which all
synthetic data was removed under founder decision D-G5-2 option (i). **No real
data subject was ever recorded under V1.**

This is the same ground on which V1 itself superseded `2026-09-PHASE2-DRAFT`,
whose supersession G1B records as "never published, never used for a real
submission". The precedent is the contract's own.

---

## 3 · What the founder identified

During the read-only G6 readiness assessment, before any genuine homeowner
registration, an audit of the stored field set against the homeowner-facing
notice found a mismatch:

The register stores **`inherited_result_key`** — the result the Property Check
produced — while the V1 notice described only *"what you told the Property Check
about your garden"*, that is, the answers the homeowner supplied. A derived value
was being stored with no homeowner-facing disclosure.

The notice's catch-all, *"the administrative records needed to manage your
registration"*, covered `check_saved_at` comfortably. It did not clearly cover a
derived assessment result.

---

## 4 · The founder decision

**KEEP `inherited_result_key`. Amend the notice to disclose it.**

The field is useful and is stored as a **key, never as prose**, so that the
stored value is re-read against today's copy rather than freezing a position
PlotNua may stop standing over. Removing it would lose that; leaving it
undisclosed would be a promise that did not match the implementation. Disclosure
was the correct remedy, and was free to make before any real data existed.

---

## 5 · The amendment

One paragraph of the privacy notice changed. Smallest natural amendment to the
existing sentence; no other homeowner wording touched.

**Before (V1)**

> … and whether you own the property. We also keep the administrative records
> needed to manage your registration, your consent and its status.

**After (V2)**

> … and whether you own the property **— and the result the Property Check
> produced from those answers.** We also keep the administrative records needed
> to manage your registration, your consent and its status.

`privacy_version` therefore advances to **`2026-10-PHASE2-V2`**, following the
established `YYYY-MM-PHASE2-V<n>` convention.

---

## 6 · What did NOT change

| | |
|---|---|
| Garden consent sentence | **byte-identical** |
| Garden consent SHA-256 | `85c436084349e841017171ef12e2c0d5e28fa24a82d99f4c2beaca8f6eee9b9c` — **unchanged** |
| Grower consent sentence | **byte-identical** |
| Grower consent SHA-256 | `32ba8b3ec621ed6e15edf0cc4c4fe95bec7b386d9c95179737fe9179990148f1` — **unchanged** |
| Stored fields | **none added, removed or altered** — `inherited_result_key` kept exactly as it was |
| Other nine notice paragraphs | **byte-identical** (builder guard P7) |
| 24-month retention rule | **unchanged**, and still a MANUAL operational commitment with no code enforcement. No retention automation was built. |
| Matching, promotion, introduction rules | **unchanged** |
| `worker/garden-register/src/index.js` | **unchanged** — it reads `env.PRIVACY_VERSION` and never contains the version string |
| `WRITES_ENABLED` · `EMAIL_ENABLED` · `INTEREST_PUBLIC` | **all still false** |
| G5 proof record and execution plan | **untouched** — they record what happened under V1 and amending them would falsify the proof |

**A privacy-version increment never, by itself, changes the consent sentence.**
Recorded here as a standing rule, because the consent sentence is hashed and
compared on every submission while the notice is not.

---

## 7 · G7 is unaffected

**G7 remains BLOCKED** pending the insurer / broker prerequisite. Introduction
eligibility must continue to exclude `buying`, absent tenure and unconfirmed
tenure. This amendment touches no matching or introduction rule and **does not
authorise G6**.

---

## 8 · How it was applied

Bounded builder `atlas-tools/build-g3-privacy-v2.py`, applied to both the
generator and the generated page, because `build-g3-garden-interest.py`
self-blocks on re-run and a hand edit of a generated page is not a controlled
change.

Eight guards, each demonstrated **capable of failing** against deliberately
mutated copies before the real run: a duplicated splice point, an absent splice
point, a second run, a duplicated version comment, a corrupted consent sentence,
a reworded sibling paragraph, `INTEREST_PUBLIC` flipped true, and a falsified
byte-delta expectation. All eight aborted or failed as intended.

One defect in the builder was found by that proof and fixed: the idempotence
check originally ran *after* the uniqueness check, so a second run aborted as if
the file were broken instead of exiting cleanly. Guard order now puts
idempotence first.

A new test guard, **`G23f3`**, asserts the disclosure in the rendered notice. The
"What we keep" sentence had **no guard at all** under V1, which is precisely how
the omission survived a freeze.

---

## 9 · Pointer added to G1B

A single dated line was appended to G1B under a clearly marked post-freeze
heading, referring to this record. **No original V1 statement in G1B was
altered.**

---

## 10 · Outstanding gate

**R0 — `hello@plotnua.ie` receipt test — remains a founder manual action and
must PASS before genuine registrations are accepted.** It is the entire
mechanism by which a homeowner can exercise the erasure right the notice
promises, and the Worker has no erasure route.
