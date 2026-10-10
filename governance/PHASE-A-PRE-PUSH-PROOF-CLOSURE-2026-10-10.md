# PHASE A · PRE-PUSH PROOF CLOSURE — 10 October 2026

Follow-up to the First Lead Phase A implementation commit
`3e9f5c2184967afca75db84a9c1aef1293c019d8`. **Proof-only.** No production
behaviour, no homeowner-visible surface, and no part of the lead architecture
was altered by anything recorded here.

---

## 1 · M01 was a vacuous guard, not a missed mutation

`validate-journey-contract.js --self-test` reported 27 of 28, missing
`M01 · code claims the Irish route`.

The detector was never at fault. The regex, executed directly against a
mutated page, returned `true`; against clean source, `false`. **The assertion
was simply never reached.** It sat below two data-dependent early returns
inside `MARKET_TRUTH.forEach`, and the second of them fires:

```js
const rows = uni.products.filter(p =>
  String(p.organisation || '') === rule.organisation && (p.imagery || {}).url);
if (!rows.length) { note(...); return; }   // ← returned here, every run
```

`MARKET_TRUTH` spells the organisation `Power Sheds`; the universe spells it
`Powersheds`. The exact-match filter found nothing, the callback returned, and
M01 emitted **neither `ok` nor `bad`** — it contributed 0 of the 92 checks and
could not fail. That is worse than a missed mutation: a guard that cannot fail
was being counted as governance.

**Correction (proof-only).** The assertion is hoisted above the data-dependent
returns so it always runs, and the organisation name is matched with its spaces
optional (`Power\s*Sheds`) so an Irish-route claim is caught under either
spelling. The data notes keep their early returns.

**After:** 93 checks, M01 contributes one real check, `--self-test` 28 of 28.
Counter-proofs: clean source still passes M01 (no false positive); a
joined-spelling claim — which the old regex could never have matched — now
fails M01.

**Pre-existing, proven not assumed.** Byte-identical at parent `260f24a`:
`MARKET_TRUTH` `b77844fa…`, the M01 section body `326b0ac3…`,
`stripComments`/`lift`/`run()` prologue `caffc0f9…`, the mutation line
`diff`-identical, the universe artefact unchanged, and the `PB046_NO_PRICE`
anchor present exactly once in both. The Phase A diff contains no line
mentioning `MARKET_TRUTH`, `M01`, `Irish`, `PB046` or `UNIVERSE`.

**It could not have concealed a lead regression.** M01's only assertion
concerns Power Sheds Irish-route claims in code. Power Sheds is on no lead
path — `prove-first-lead.mjs` F10 drives the lifted shipped gate and requires
`null` for it. The lead invariants are carried by J13 (six assertions) and J14,
all seven of which emit and are reachable, each with a mutation only it catches.

## 2 · PARKED · the Power Sheds / Powersheds market-truth issue

Recorded, deliberately **not** acted on, per founder instruction of
10 October 2026.

- `MARKET_TRUTH` says `Power Sheds`; the universe says `Powersheds`. The data
  arm of M01 therefore prints `no publishable rows; nothing to check`, which is
  untrue — the universe holds **3** Powersheds rows, all with imagery.
- Those 3 rows are now **EUR on `ie.powersheds.com`**. The recorded status
  (`MISMATCH RECORDED — not repaired in the stabilisation pass`, recorded host
  `www.powersheds.com`, recorded currency `GBP`) may therefore be stale,
  apparently closed by PSP-4.
- Correcting the lookup would make the data notes honest *and* would surface a
  change to a recorded contract violation. That is a contract decision, not a
  proof repair.

**Not investigated further in this job.** No lookup change, no status change,
no PSP-4 review.

## 3 · The default-template freeze exception

**Root cause.** `prove-default-templates.js` asserts that no supplier is named
anywhere in the default product journey, outside one recorded exception (the
frozen supplier-county data). Phase A added `LEAD_SUPPLIERS`, which must name
the supplier twice — `Yardbox` as the universe spells it, `Yard Box` as the
rights grant, the Atlas organisation record and the consent sentence say it.
Five live occurrences, so the guard turned red. Proven to be Phase A's doing:
parent `260f24a`'s page passes the same proof against the same universe
(exit 0); HEAD's page fails (exit 1).

**This was mis-reported.** Phase A was reported as green. It was not. The
failure was found only on the pre-push re-run.

**Authorised decision (founder, 10 October 2026).** The exact `LEAD_SUPPLIERS`
allow-list is permitted as **bounded, contract-governed release
configuration**. It is explicitly **not** a supplier-specific template
exception.

**Exception as implemented — the literal, not the idea.**

| Boundary | Mechanism |
| --- | --- |
| one literal only | anchored on the full text `const LEAD_SUPPLIERS = Object.freeze({`, which must appear **exactly once** |
| no surrounding logic | brace-matched; the carve-out ends at that object's own closing brace |
| data, not code | the carved text must contain no `function`, arrow, branch, loop, DOM call, class or style reference |
| cannot be widened | length-capped at 800 characters (it is 338) |
| cannot be hollowed | the literal must still carry the names it is exempted for |
| everything else intact | the supplier-named-CSS assertion, the layout and template checks, and all of sections B onward are untouched |

No general "supplier data" exemption exists. No arbitrary object is exempt.
A supplier named in markup, in CSS, in presentation logic, or in a second copy
of the structure still fails.

**Capability proof.** `atlas-tools/prove-default-templates-capability.mjs`,
7 mutations, **7/7 caught by the assertions that own them**, 0 blind,
0 vacuous, 0 misattributed, plus a control proving the unmutated guard passes
with the allow-list exempted.

| # | Mutation | Caught by |
| --- | --- | --- |
| C1 | a supplier named in ordinary template markup | the `Yard Box` name assertion |
| C2 | a supplier named in CSS / class architecture | the CSS-fork assertion |
| C3 | a supplier named in executable presentation logic | the `Yardbox` name assertion |
| C4 | a renamed duplicate of the allow-list structure | both name assertions |
| C5 | the authorised literal declared a second time, verbatim | declared-exactly-once, plus four more |
| C6 | executable logic grown inside the authorised literal | the data-only assertion |
| C7 | a name moved out, leaving the exemption hollow | carries-the-names, plus the name assertion |

## 4 · Instrument note, recorded because it limits what can be claimed

A single monolithic `prove-job6-interaction.py` run hangs in this sandbox after
the fourth page, at Chromium context recycling — roughly nine minutes with no
further activity. That is the harness in this environment, not the page, and it
is neither a pass nor a failure. Run in bounded chunks the proof completes
cleanly: 4 pages × 2 widths (J1–J12) plus the tail (J13 `search.html`,
J14–J18 My Plot season semantics), **54 checks, 0 failed**, every chunk exit 0.

## 5 · Lesson

Phase A's own proof suites were all green, and the regression that mattered was
in a guard Phase A had never been pointed at. Adding a new frozen data
structure to a page that is under a no-supplier-names freeze is exactly the
kind of change that trips a guard somewhere else, and "my suites pass" is not
the same statement as "the repository's guards pass". The full gate set, not
the new one, is the closure condition.
