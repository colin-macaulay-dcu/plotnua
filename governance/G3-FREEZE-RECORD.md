# G3 FREEZE RECORD — DISC-025 BORROWED GARDEN EXPRESSION OF INTEREST

**Status:** FROZEN · 7 October 2026
**Founder visual sign-off:** PASS. G3 is no longer withheld.
**Approval is not permission to launch.** All three switches remain false.

| gate | state |
|---|---|
| G1B | **FROZEN** |
| G2 | **DEPLOYED + CLOSED** |
| G3 | **BUILT + TECHNICALLY PROVEN + VISUALLY APPROVED** |
| G4–G6 | not started |
| G7 | **BLOCKED** pending the insurer / broker question |

---

## 1 · THE APPROVED ARTEFACT

`disc025-borrowed-garden-check.html`

| | |
|---|---|
| bytes | 140,616 |
| sha256 | `1a20d6edea571e6e3915ae2c746810dd63625accbaac9a8918e38d6946e27170` |
| pre-G3 baseline | `cf614c4fa4769125fe314f21d57b79af52c7c1f0588d396fb98b5466c1adbabe` (111,039 bytes) |
| after the G3 build | `86cdf32abe7980d253bf00aa58ebcce69afd78bc6fa93805c57b83ad3944b67c` (139,703 bytes) |
| after Correction 1 | `1a20d6edea571e6e…` — the frozen state |

Built in two authorised passes, both purely additive:

1. **G3 build** — +590 lines, 0 removed, five anchored insertion sites.
2. **Correction 1** — +913 bytes, CSS only: `#bgIntOffer .bg-int-p, #bgIntOffer
   .bg-int-facts li { max-width: 68ch; }`, scoped to the invitation so the
   received / not_open / unavailable paragraphs were not touched.

## 2 · REGIONS PROVEN BYTE-IDENTICAL AT FREEZE

| region | sha256 | meaning |
|---|---|---|
| certified engine | `72c0f466ab4aa198…` | `decide()` never changed, in either pass |
| `PlotNuaJourneySave` | `df88b6e3bef36c4b…` | shared byte-for-byte with four other journeys |
| G3 JS region | `ef2cbbb44b1919f5…` | unchanged by Correction 1 |
| G3 HTML region | `829ff4f63724506c…` | unchanged by Correction 1 |
| 240 engine outcomes | `f59443dce4044f22…` | all 3×5×4×4 combinations identical |

Correction 1 additionally proved that **everything outside `<style>` is
byte-for-byte identical** — the patch could not have reached behaviour.

## 3 · THE SHIPPED GATE STATE

```
INTEREST_PUBLIC = false     (page, line 2473)
WRITES_ENABLED  = "false"   (wrangler.toml)
EMAIL_ENABLED   = "false"   (wrangler.toml; there is no mail adapter at all)
```

With `INTEREST_PUBLIC` false the section is **removed from the DOM** once the
Property Check resolves — not merely hidden. A third gate suppresses it
whenever `spare_corner === 'no_garden'` (founder decision Q1). Interest and
Save to My Plot are independent (founder decision Q2).

## 4 · PROOF AT FREEZE

| suite | result |
|---|---|
| `prove-g3.mjs` | **166 passed, 0 failed** |
| `prove-g3-mutations.mjs` | **25 / 25 mutations caught**, 0 blind |
| `prove-g3-builder-guards.py` | **25 / 25 guards capable** |
| `prove-guards.mjs` (G2 local) | **65 passed, 0 failed** |
| `prove-deployed.mjs` (G2 live) | **13 passed, 0 failed** |
| `prove-g3-deployed.mjs` (G3 live) | **10 passed, 0 failed** |
| `prove-g3-review-harness.mjs` | **46 passed, 0 failed** |
| Airtable, after the live test | **5 tables × 0 records** |

Deployed Worker at freeze: `https://plotnua-garden-register.colin-a41.workers.dev`
version `ed9d2dc6-69a0-4c88-91f3-9418a0954bc7`, `src/index.js` sha256
`4c5a47831ec85178f083f4535f1bbb732ee9c4542af43f28ef8b88105897a3ba`.

**The decisive live proof:** the page's own payload reaches the Worker, passes
every validator, and is stopped by the WRITE SWITCH — demonstrated by two
positive controls (a bad district and wrong consent wording both return 400
`refused`, so the 503 is the switch talking and not the validator).

## 5 · FOUNDER VISUAL SIGN-OFF, 7 October 2026

PASS on: overall PlotNua visual integration · invitation hierarchy and
commitment level · invitation desktop reading measure after the scoped 68ch
correction · form structure · field set · consent presentation · CTA · expanded
form · 390px · 1440px · closed 503/`not_open` state · no control or wrapping
failure.

**No further visual or copy changes required.**

## 6 · WHAT FREEZING DOES NOT AUTHORISE

Freezing records that the implementation is approved as built. It is not
permission to launch. Before any public activation the items in
`G3-PUBLIC-SWITCH-CHECKLIST.md` stand:

- **PS-1** footer wording reconciliation — a release blocker at the switch
- **PS-2** Worker / test source-control governance
- **PS-3** G7 insurer / broker block

No commit has been made. G4 has not begun, and G3 passing is not a reason to
begin it.
