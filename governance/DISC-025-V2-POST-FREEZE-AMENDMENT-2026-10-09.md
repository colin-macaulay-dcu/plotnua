# DISC-025 V2 · POST-FREEZE AMENDMENT — WHOLE-PAGE HASH

**Date:** 9 October 2026
**Status:** APPEND-ONLY AMENDMENT — applied, proven, awaiting founder visual acceptance
**Authority:** founder ruling and governance decision, 9 October 2026
**Amends:** [`DISC-025-V2-EXPERIENCE-FREEZE-RECORD.md`](DISC-025-V2-EXPERIENCE-FREEZE-RECORD.md) (VISUALLY FROZEN 8 October 2026)
**Produced by:** JOB 1 · P0 JOURNEY EXITS — see [`JOB1-JOURNEY-EXITS-2026-10-09.md`](JOB1-JOURNEY-EXITS-2026-10-09.md)

This is a **dated post-freeze amendment, append-only**. The freeze record's own
text is left historically accurate: it froze the V2 homeowner experience on
8 October 2026 at whole-page hash `df54fd5e3405…`, and it still says so. This
record carries the change, in the same convention as
[`G1B-V2-AMENDMENT-2026-10-08.md`](G1B-V2-AMENDMENT-2026-10-08.md).

---

## 1 · The hashes

| | |
|---|---|
| Original frozen whole-page hash | `df54fd5e3405…` |
| New whole-page hash | `12e442393b13…` |
| **Frozen `<main>` experience hash** | **`05bf977f0d4f…` — UNCHANGED** |

Full values, computed from the candidate files on disk:

| | |
|---|---|
| Whole page, before | `df54fd5e3405d6551f925d94d3df6e5a3a5b0254e7d2353da91b6950cb9c2fd6` |
| Whole page, after | `12e442393b135ab9598890e4ea1936454cb46312e0a47466790b6afb96d6a3c7` |
| `<main>` … `</main>`, before **and** after | `05bf977f0d4fb05a3310e1e3dc9bfb757b2d92d529f226f2c8bb97c805844a29` |

The `<main>` hash is the governing figure: it is the frozen V2 experience, and
it is identical before and after, byte for byte.

---

## 2 · Reason for the whole-page hash change

**Founder-authorised `PLOTNUA JOURNEY EXIT v1` site chrome inserted strictly
outside the frozen `<main>` experience.**

The page has the shape

```
<header class="bg-top"> … </header>
<main class="bg-wrap">   THE FROZEN V2 CHECK / RESULT / INTEREST EXPERIENCE   </main>
<script>                 THE ENGINE                                        </script>
```

and exactly one `</main>`. The region is spliced **immediately after that
`</main>`** and nowhere else. The diff is **+70 insertions, 0 deletions**.

Guard `E6` in `atlas-tools/build-journey-exit.py` proves the `<main>` element
byte-identical, **compared against the page on disk** rather than against the
builder's own intermediate. Guard `E6b` proves the region cannot land inside
`<main>`. Guard `E2` proves every byte outside the splice point unchanged. All
three were demonstrated **capable of failing** against deliberately mutated
copies before this record was written.

---

## 3 · This amendment does NOT reopen DISC-025 V2

The V2 homeowner experience remains **VISUALLY FROZEN**. No copy, spacing,
styling or UX change was authorised or made inside it. Specifically:

| | |
|---|---|
| Questions | **unchanged** |
| Options | **unchanged** |
| Engine | **unchanged** |
| Result | **unchanged** |
| Evidence | **unchanged** |
| Consent / privacy | **unchanged** |
| `intPayload()` | **unchanged** — byte-identical, verified against `HEAD` |
| Funnel | **unchanged** |
| Worker | **unchanged** — `git diff` on `worker/garden-register/src/index.js` is EMPTY; sha256 `66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79` |
| `INTEREST_PUBLIC` | **`false`** |
| `WRITES_ENABLED` | **`false`** |
| `EMAIL_ENABLED` | **`false`** |

All three switches are unchanged. `INTEREST_PUBLIC` is verified in the page;
`WRITES_ENABLED` and `EMAIL_ENABLED` are Worker environment variables and the
Worker is byte-identical, so neither could have moved.

The consent contract is proven by that byte-identity rather than by inspection:
`prove-g3.mjs` G4, G4b, G4c, G4d and G11 all PASS, and the garden and grower
consent SHA-256 values recorded in §5 of the freeze record stand. `privacy_version`
remains `2026-10-PHASE2-V2`.

---

## 4 · What the added region is, and what it is not

A `<footer class="pnx">` carrying one `<h2>`, three onward routes
(`discoveries.html` · `search.html` · `your-plot.html`), a labelled `<nav>`
(Home · About · Contact · Privacy · Terms) and the contact line. Byte-identical
on all ten Property Checks, sha256
`83dcd3f1418a1b797d94b3707097b23b760738a0c88388c4d477f88d39e03469`.

It contains **no script, no storage, no analytics and no network call**
(guard E7), **no external asset** (E8), and **no demand, matching,
registration, pricing or earnings claim and no sign-up invitation** (E13). Its
CSS declares only selectors beginning `.pnx` (E11), so it cannot reach the
frozen `bg-` stylesheet. Every pre-existing anchor on the page — href **and**
anchor text — survives unchanged (E9), so the frozen "Join the register" and
"View in My Plot" calls to action are not removed, reworded, demoted or
restyled.

---

## 5 · Still not authorised

- **The homeowner register remains CLOSED.** This amendment does not open it.
- **R0 — `hello@plotnua.ie` receipt — remains outstanding** and must PASS before
  genuine registrations are accepted.
- **G7 remains BLOCKED** pending the insurer / broker prerequisite.
- **G6 remains PASS and closed.** The proven browser-path integration was not
  touched.
- No further V2 copy, spacing, styling or UX change is authorised without a new
  founder decision.
