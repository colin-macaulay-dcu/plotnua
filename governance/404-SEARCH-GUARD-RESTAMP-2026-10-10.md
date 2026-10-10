# 404 SEARCH GUARD · BASELINE RE-STAMP

**Date:** 10 October 2026
**Base:** `d6e577938d400efce98e1c0b6e8b092dc9ca1f7e`
**Scope:** tooling and governance only. No shipped page changed. No builder logic changed.
No guard weakened.

---

## What was wrong

`atlas-tools/build-404-search.py` carries a pre-flight, `EXPECTED_BEFORE`, pinning
`sha256(404.html with the Search rail region stripped out)` — the page *around* the region the
builder owns. It is hand-maintained; nothing re-stamps it automatically.

**Job 4** (`8db350f`, landmarks and semantics) legitimately changed `404.html` and **correctly
re-stamped** the constant, `97c83162cdaa → 6297c0f13499`.

**Job 5** (`8ccca1e`, shared visual accessibility layer) then legitimately changed `404.html`
again — 97 insertions, 0 deletions, entirely its marked `PLOTNUA A11Y VISUAL` override block —
and **omitted the corresponding re-stamp**. From that commit the pre-flight refused, and
`prove-404-search-mutations.py` could not run its control, for two releases.

## The Job 6 diagnosis was wrong, and was corrected

During Job 6 this was reported as "already stale at `8db350f`, before Job 5." That was an
instrument error: it compared the **whole-file** hash of `404.html` against a constant that is a
**region-stripped** hash. Comparing like with like reverses the answer.

### Corrected like-for-like history

| Commit | Job | 404 full | 404 **stripped** | `EXPECTED_BEFORE` then | |
|---|---|---|---|---|---|
| `9a7c136` | Job 1 — rail injected | `48ed52028c67` | `97c83162cdaa` | `97c83162cdaa` | correct |
| `8db350f` | Job 4 — landmarks | `51d58b4f1cbd` | `6297c0f13499` | `6297c0f13499` | correct, re-stamped |
| `8ccca1e` | **Job 5** — a11y layer | `2079617af90f` | **`515e0897dd83`** | `6297c0f13499` | **stale from here** |
| `d6e5779` | Job 6 — Search focus | unchanged | unchanged | `6297c0f13499` | still stale; Job 6 never touched the 404 |

## A second, independent staleness

`atlas-tools/404-search-baseline.json` had **also** gone stale, and one commit *earlier*. Its
`before` and `after` still held the Job 1 values. Those feed the builder's `--revert` path, so
**`--revert` had been broken since Job 4** — proven, not inferred:

```
REFUSED: cannot revert cleanly: stripping the region gives 515e0897dd83,
         baseline was 97c83162cdaa          (exit 1)
```

Its `region` and `donor` entries were, and remain, correct.

## The Search rail region never changed

| | sha256 |
|---|---|
| `9a7c136` (Job 1) | `0b7f22d2486985507140e8f7b896abfe4391db094eee45b8b9eeab3043f592ac` |
| `8db350f` (Job 4) | `0b7f22d2486985507140e8f7b896abfe4391db094eee45b8b9eeab3043f592ac` |
| `8ccca1e` (Job 5) | `0b7f22d2486985507140e8f7b896abfe4391db094eee45b8b9eeab3043f592ac` |
| current, and `index.html` donor | `0b7f22d2486985507140e8f7b896abfe4391db094eee45b8b9eeab3043f592ac` |

**No shipped 404 or Search defect existed.** The guard went silent; it never protected less. The
current `404.html` is legitimate in every byte: all difference from Job 1 traces to Job 4 and
Job 5, both founder-authorised and both built through their own governed builders.

## What this repair changed

| File | Field | From | To |
|---|---|---|---|
| `atlas-tools/build-404-search.py` | `EXPECTED_BEFORE` | `6297c0f13499` | `515e0897dd83` |
| `atlas-tools/404-search-baseline.json` | `before` | `97c83162cdaa…` | `515e0897dd83…` |
| `atlas-tools/404-search-baseline.json` | `after` | `48ed52028c67…` | `2079617af90f…` |

Plus this record. Nothing else. `region` and `donor` untouched. No builder logic, no guard
behaviour, no shipped file, no Search V1 asset.

## Lesson

A bounded builder that pins a file a **sibling builder writes** will go stale silently, and the
proof that would have caught it fails closed into silence rather than reporting. Three
consequences worth carrying forward, none implemented here:

1. `build-a11y-visual.py` writes `404.html`; `build-404-search.py` pins it. Neither knows about
   the other. Any future builder pinning a file another builder writes needs an explicit
   cross-check considered at design time.
2. `prove-404-search-mutations.py` aborts at its control when the constant is stale, so twelve
   working guards report nothing instead of "eleven fine, one baseline stale". A CI signal would
   have surfaced this in a day rather than two releases.
3. The baseline JSON is written only on a real run, never on `--check`, so `--revert` can rot
   while `--check` looks healthy.

Cross-builder logic and CI were explicitly **out of scope** for this repair and are recorded
here as considerations, not as a project.
