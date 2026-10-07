# G3 · PUBLIC-SWITCH CHECKLIST — DISC-025 BORROWED GARDEN

**Status:** OPEN · recorded 7 October 2026
**Scope:** items that are acceptable while G3 is CLOSED but must be resolved
before `INTEREST_PUBLIC` or `WRITES_ENABLED` is flipped.

This file records obligations. It changes no behaviour and amends neither the
G1B contract (FROZEN) nor the G2 Worker contract.

---

## PS-1 · THE PAGE FOOTER CONTRADICTS AN OPEN REGISTER

**Founder-recorded, 7 October 2026.**

The Property Check footer currently reads, verbatim (shipped page, lines
1172–1175):

> PlotNua does the homework. You make the decision. We do not arrange anything
> or introduce anybody through this Property Check, and **nothing on this page
> sends your details anywhere**. Local Garden Matching is the next capability
> **PlotNua intends to build**.

### Why it is true today

With `INTEREST_PUBLIC = false` the G3 section is **removed from the DOM** on
load, not merely hidden. There is no form, no endpoint-bearing control and no
request. Both sentences are therefore accurate as the page currently ships,
and the founder has accepted them as accurate for the closed state.

### Why it stops being true at the public switch

| sentence | what breaks it |
|---|---|
| "nothing on this page sends your details anywhere" | **False the moment the form is reachable.** The browser necessarily POSTs to the Worker before receiving any answer — the same fact that forced the correction to the closed-state copy. A homeowner who submits has sent their details, whether or not they were stored. |
| "Local Garden Matching is the next capability PlotNua intends to build" | **Understates an open register.** Once homeowners can join, PlotNua is no longer only intending to build it; it is collecting for it. Left unchanged it reads as a denial of the very thing the panel above is asking them to do. |

### What must happen before the switch

1. The footer must be reconciled with whatever state the page is actually in.
   Both sentences are **founder-owned copy** and neither may be edited on any
   authority but the founder's.
2. The reconciliation must not overcorrect. The *first* clause — "We do not
   arrange anything or introduce anybody through this Property Check" — stays
   true even with the register open, because the register is not an
   introduction: G7 is a separate, still-blocked gate. Only the
   sends-nothing-anywhere clause and the intends-to-build clause are at issue.
3. Whatever replaces them must not promise or imply a match. The G6 constraint
   is unchanged.

### What is already consistent and needs no change

The G3 panel carries its own closing note, which does not make the broken
claim:

> PlotNua does not verify anybody's identity and has not met anyone on this
> register. Nothing is arranged through this page.

"Nothing is arranged" is about arrangement, not transmission, and remains true
with the register open.

### State

**NOT A DEFECT TODAY. A RELEASE BLOCKER AT THE PUBLIC SWITCH.**
No change is authorised now, and none has been made.

---

## PS-2 · THE WORKER AND ITS PROOF SUITE ARE OUTSIDE VERSION CONTROL

**STATUS: CLOSED — 7 October 2026.** See the closure note at the end of this
section. The text below is retained as the original finding.

Recorded 7 October 2026, from the G3 housekeeping pass.

`04 Deploy/plotnua-garden-register/` is **not a git repository and is not
inside one** (`git rev-parse` fails up to the mount point; `plotnua-github` is
a sibling). Consequently `src/index.js`, `wrangler.toml`, `package.json`,
`package-lock.json` and all four test suites — `prove-guards.mjs`,
`prove-deployed.mjs`, `prove-g3.mjs`, `prove-g3-mutations.mjs`,
`prove-g3-deployed.mjs` — have **no version history**. The deployed Worker
cannot be diffed against a committed source, and a proof suite that is lost is
lost.

There is also **no `.gitignore`** in that directory. If it is brought under
git, `node_modules` would be swept in unless one is added first.

**Not a G3 defect. Decided and executed, 7 October 2026** (founder decision
D-A = option A).

### CLOSURE EVIDENCE

The Worker source, its configuration and all six proof suites are now tracked
in `plotnua-github` under `worker/garden-register/`, committed locally as
`G3 closure 2/4`. Specifically:

| preserved | sha256 |
|---|---|
| `worker/garden-register/src/index.js` | `4c5a47831ec85178…` |
| `worker/garden-register/wrangler.toml` | `WRITES_ENABLED="false"`, `EMAIL_ENABLED="false"` |
| `package.json` / `package-lock.json` | jsdom `^30.1.2` **dev-only**; 37 packages, all `dev:true` |
| six suites under `test/` | re-run from the new path: 166/0, 25/25, 65/0, 46/0 |

**Reproducible, not merely stored.** Three suites resolved the journey page at
a fixed relative depth that the move would have broken silently; page
resolution now searches an ordered candidate list and throws rather than
guessing. All frozen proofs were re-run from the committed location and pass.

Excluded and verified absent from the repository: `node_modules/`,
`.wrangler/`, `.DS_Store`. Secret sweep repeated before copying: clean.

**One residual, not a blocker.** `04 Deploy/plotnua-garden-register` still
exists on disk, unchanged, and is now a duplicate. It was deliberately not
deleted: it is the source of a live Worker and had no version history at all
until this commit existed. It should be retired once a deployment from the
committed path has been confirmed, and `wrangler deploy` should be run from
`worker/garden-register/` thereafter.

---

## PS-3 · D1 INSURANCE — ALREADY RECORDED, RESTATED HERE FOR ONE LIST

**STATUS: OPEN, and scoped to G7 only.**

G7 — the **first real introduction** — remains **BLOCKED** until the insurer /
broker question is resolved. G1B §8 is authoritative.

### WHAT PS-3 DOES *NOT* BLOCK — DO NOT REWRITE THIS

Insurance is **not** a prerequisite for collecting expressions of interest.
The founder unblocked G6 explicitly, and the frozen gate model must not be
restated to make it a prerequisite:

| gate | what it is | PS-3 effect |
|---|---|---|
| **G5** | Colin-controlled test records, then erasure | **not blocked** |
| **G6** | real homeowner registration / expressions of interest and their validation | **not blocked** |
| **G7** | the first real introduction between two people | **BLOCKED** |

The distinction is substantive, not procedural. A register entry is a person
asking PlotNua to tell them something. An introduction is PlotNua putting two
strangers in contact over the use of private ground — which is where the
insurance question actually bites. Collecting interest while G7 is blocked is
the intended order of operations, not a loophole.

Opening the public and write switches does start accumulating people who will
eventually need G7 to be answered. That is a sequencing fact to manage, not a
reason to block G6.
