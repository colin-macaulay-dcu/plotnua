# DECISION BRIEF — FROM THE FROZEN G3 STATE TO THE FIRST GENUINE HOMEOWNER RECORD

**Status:** BRIEF · nothing here executed · 7 October 2026

**Frozen state.** local `main` `510a91c` · `origin/main` `30b49d8` · 4 ahead,
0 behind. Commits `8749df4` · `c6643bc` · `4bb048e` · `510a91c` — not to be
altered, squashed, amended or pushed.

G1B FROZEN · G2 DEPLOYED + CLOSED · G3 APPROVED + PRESERVED · PS-2 CLOSED ·
PS-1 OPEN · PS-3 OPEN (G7 only).

---

## TWO CORRECTIONS TO MY EARLIER FRAMING

Both change what the push decision actually is, so they come first.

**1 · The page is already live, and the footer is already live.** `origin/main`
already tracks `disc025-borrowed-garden-check.html` at `cf614c4fa476`
(111,039 bytes), and the footer sentence *"nothing on this page sends your
details anywhere"* is **already published today**. I previously framed pushing
as putting that claim on the live site — it is there already, and it is **true**
today and stays true after a push, because with `INTEREST_PUBLIC = false` the
section is removed from the DOM. **PS-1 is therefore not a push blocker. It is
an `INTEREST_PUBLIC` blocker.** That distinction matters and I had it wrong.

**2 · The G6 no-promise denial is present.** An earlier line-based grep of mine
returned zero for *"not a match and does not guarantee one"* because the
sentence wraps across two source lines. Whitespace-normalised, it appears once,
in the invitation. The founder-set G6 constraint is already satisfied in the
built page.

---

## 1 · BEFORE PUSHING THE FOUR LOCAL COMMITS

Pushing `main` triggers a **GitHub Pages native branch deployment** — no
workflow file performs it; it is configured in repository settings, evidenced
by deployment #313 having been tied to commit `30b49d8`.

What a push actually does: replaces the live page with the G3 version, which
**renders identically to today's** for every visitor, because the section is
removed from the DOM before anything is painted.

| required | why |
|---|---|
| Confirm nothing else is riding along | 4 commits, 20 paths. The 8 unrelated untracked paths must stay untracked |
| Accept that the **HTML source** becomes public | The form markup, the Worker endpoint URL and the consent sentence are all in the source. Anyone reading it learns PlotNua is building a register that is not open. Disclosure of intent, not of data |
| Accept that `?interest=preview` becomes **reachable by URL** on plotnua.ie | Not secret, merely unadvertised. A submission from there would reach the Worker with an allowed Origin and get `503 not_open`. Nothing is stored — writes are off — but the Worker will see requests |
| Decide whether the legacy Worker directory is retired first | It stays per founder instruction. A push does not touch it |

**Not required:** PS-1. **Not required:** the insurer answer.

**Recommendation:** push is low-risk and preserves the work off one machine.
The only genuine question is whether you are content for the unopened register
to be visible in page source.

---

## 2 · BEFORE ENABLING `INTEREST_PUBLIC`

This is the step **PS-1 blocks**, and it is a one-line change to a founder-owned
sentence.

| required | detail |
|---|---|
| **PS-1 resolved** | *"nothing on this page sends your details anywhere"* becomes false the moment the form is reachable — the browser necessarily POSTs before any answer. *"Local Garden Matching is the next capability PlotNua intends to build"* understates an open register. Both are founder-owned copy. The first clause, *"We do not arrange anything or introduce anybody through this Property Check"*, stays true and should not be touched |
| Decide the reachability surface | `INTEREST_PUBLIC = true` exposes the panel to **every** homeowner who completes the check. There is no half-open setting today |
| Re-run the frozen proofs | 166/0 · 25/25 · 65/0 · 46/0, and re-confirm the engine and 240-outcome hashes |
| Confirm the closed-state copy is still what a homeowner meets | With writes still off, every submission lands on *"The register isn't open yet…"*. **Founder decision 3 from G3A says do not send genuine acquisition traffic into that state** |

**Consequence to hold in view:** `INTEREST_PUBLIC` without `WRITES_ENABLED`
means real homeowners can submit and nothing is kept. That is the deliberately
closed state, and it is not a place to leave real people.

---

## 3 · BEFORE ENABLING `WRITES_ENABLED`

| required | detail |
|---|---|
| `AIRTABLE_TOKEN` and `AIRTABLE_BASE` set as Cloudflare **secrets** | `writesEnabled()` requires both plus the flag. Never in `wrangler.toml` |
| Erasure route exercised **before** the first real record | Email-to-delete is the only withdrawal mechanism in V1. Prove it works on a Colin-controlled record first |
| Consent-proof write verified | A row must land in Consent proofs with a **hash** of the address, never the address |
| `typecast:false` behaviour confirmed against the live vocabularies | An option that does not exist is a rejected write, not a silently created one |
| 24-month retention has an owner | The rule is frozen; nothing enforces it automatically. Decide who runs it |
| Re-run deployed negative controls after the flip | 13/13 and 10/0 were measured with writes **off**; several assertions change meaning when on |

**Not required:** the insurer answer. G6 is explicitly unblocked.

---

## 4 · WHAT THE PRIVATE / DRY-RUN STAGE IS

This is **G5**, and it is Colin-only.

1. `INTEREST_PUBLIC = true`, `WRITES_ENABLED = true`, **no acquisition traffic**
2. Colin submits **his own** records end to end — owner, renter-with-permission,
   out-of-pilot district
3. Verify each in Airtable: field by field, hash present, no prohibited field
4. Exercise erasure on each; verify the consent proof **survives** the deletion
5. Return all five tables to **zero**
6. Only then consider real traffic

The dry run proves the write path, the erasure path and the retention story on
records that belong to Colin. Nothing about it needs another person.

---

## 5 · EVIDENCE REQUIRED BEFORE THE FIRST GENUINE HOMEOWNER RECORD

| # | evidence |
|---|---|
| 1 | PS-1 resolved and the corrected footer live |
| 2 | G5 completed: write, read-back, erasure, consent proof surviving, tables returned to zero |
| 3 | All five tables confirmed at zero immediately before opening |
| 4 | Frozen proofs green at the live commit |
| 5 | A named human-review route — `human_review_by` / `human_review_at` are stamped by a person, not a system |
| 6 | The zero-spend acquisition channel chosen, in the founder's priority order: community Facebook pages → local press → residents' groups → newsletters → posters → doorstep. **Paid acquisition remains HOLD at €0** |
| 7 | A stated stopping rule — what number or what signal ends the experiment |

**R4 (reconfirmation rate) is unmeasurable in V1** by founder ruling and must
not be manufactured.

---

## 6 · DELIBERATELY DEFERRED UNTIL G7

**PS-3 blocks G7 — the first real introduction — and nothing earlier.** It does
**not** block G5 test records and does **not** block G6 registration or
validation. The frozen gate model must not be restated to make insurance a
prerequisite for collecting expressions of interest.

Deferred until the insurer / broker question is answered:

- any introduction between two people
- the two introduction-consent emails, and the joint email
- the tenure rule's *matchable* consequence (storage is already permitted;
  promotion to an introduction is not)
- `EMAIL_ENABLED` — there is **no mail adapter in the Worker at all**, so this
  is a build, not a flag
- grower-side recruitment at scale — Homegrown's 78 / 3 / 0 shows gardens are
  the constraint, so gardens come first

Collecting interest while G7 is blocked is the intended order of operations.

---

## THE ONE DECISION THAT UNLOCKS THE REST

**PS-1.** It is a short piece of founder-owned copy. Until it is resolved,
`INTEREST_PUBLIC` cannot be enabled honestly — and every step from §2 onwards
waits behind it. §1 does not.
