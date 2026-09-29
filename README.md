# plotnua

PlotNua website.

## Before you change anything

**Read [`PLOTNUA-JOURNEY-CONTRACT.md`](PLOTNUA-JOURNEY-CONTRACT.md) first.**

It is the authoritative record of what exists, who owns each stage of the homeowner journey,
what may connect to what, and what must not be bypassed. Several stages are **BUILT and WIRED
but deliberately dormant** — hidden is not nonexistent, and rebuilding one under a new name is
the specific failure this contract exists to prevent.

The binding rule, from §8 of the contract: before adding any new screen, route, CTA,
next-action resolver or supplier handoff, search the contract, find the canonical owner, and
extend it. *"I did not know it existed"* is not an available justification.

## Test classes

An implementation is not complete unless all three pass.

| Class | Question | Command |
|---|---|---|
| **A · Feature** | Does the new functionality work? | the change's own guards + capability proof |
| **B · Governance** | Do rights, evidence and claim rules still hold? | `node atlas-tools/validate-image-rights.js --permissions <manifest>`<br>`node atlas-tools/prove-results-publication-gate.mjs` |
| **C · Journey** | Has the wider PlotNua journey been preserved? | `node atlas-tools/validate-journey-contract.js` |

Every gate can prove it is capable of failing:

```
node atlas-tools/validate-journey-contract.js --self-test
node atlas-tools/validate-image-rights.js --self-test
```

A guard that cannot fail proves nothing.
