# G5 EXECUTION PLAN — PRIVATE CONTROLLED-WRITE AND ERASURE PROOF

**Status:** PLAN ONLY · 8 October 2026 · nothing here executed
**Authority:** G1B (FROZEN) · G2 Worker contract · G3 freeze record
**Scope:** the Colin-only write and erasure proof that must complete before G6,
the first genuine homeowner registration.

Canonical state this plan starts from:

| | |
|---|---|
| production commit | `057bb81` |
| page sha256 | `bd08ce67d004a8b24be00bc50e75a31bcf18693dd5e9dfb6974267917e327c19` (140,738 B) |
| Worker sha256 | `4c5a47831ec85178f083f4535f1bbb732ee9c4542af43f28ef8b88105897a3ba` (21,293 B) |
| gates | G1B FROZEN · G2 DEPLOYED+CLOSED · G3 APPROVED+PRESERVED+DEPLOYED CLOSED · PS-1 CLOSED · PS-2 CLOSED · PS-3 OPEN (G7 only) |
| switches | `INTEREST_PUBLIC = false` · `WRITES_ENABLED = "false"` · `EMAIL_ENABLED = "false"` |
| Airtable | five tables × **0 records** |

**Nothing in this plan changes a switch, writes to Airtable, deploys, or edits
code.** Every step below is written to be executed later, under separate
founder authorisation, and three of them need a founder decision first (§12A).

---

## 1 · WHICH SWITCHES CHANGE, AND IN WHAT ORDER

**One switch changes. `INTEREST_PUBLIC` is not touched.**

| # | step | why this order |
|---|---|---|
| 0 | **Pre-flight, nothing changed.** Confirm five tables at zero; confirm the deployed Worker sha256 is `4c5a4783…`; re-run `prove-g3.mjs` (166/0), `prove-g3-mutations.mjs` (25/25), `prove-guards.mjs` (65/0); confirm the live page sha256 is `bd08ce67…` | A write proof that starts from a non-zero base cannot tell a new row from an old one |
| 1 | **Confirm the two Cloudflare secrets exist**: `AIRTABLE_TOKEN`, `AIRTABLE_BASE`. `writesEnabled(env)` is `env.WRITES_ENABLED === 'true' && !!env.AIRTABLE_TOKEN && !!env.AIRTABLE_BASE` — all three, or no write | If a secret is missing, flipping the flag produces `503 not_open` and looks like the switch failed. Establish this before the flag, not after |
| 2 | **Set `WRITES_ENABLED = "true"`** in `wrangler.toml` and `wrangler deploy` | The only switch G5 needs |
| 3 | Confirm the deploy took: one valid POST returns `200 {ok:true,state:"received"}` where it previously returned `503 not_open` | A deployment can carry different vars than the file on disk — this is the lesson `prove-deployed.mjs` was written for |
| 4 | Run the test matrix (§3), verify rows (§4), verify refusals (§5) | — |
| 5 | Run the erasure proof (§7) | — |
| 6 | **Set `WRITES_ENABLED = "false"`** and `wrangler deploy` (§10) | — |
| 7 | Re-verify `503 not_open` on the garden and grower routes; re-confirm table state (§8) | The flip back is not proven until a refusal is observed again |

`EMAIL_ENABLED` stays `"false"` throughout and is **not** an email capability:
there is no mail adapter in the Worker at all. No test in this plan sends,
expects or depends on an email.

---

## 2 · HOW `INTEREST_PUBLIC` STAYS PROTECTED DURING G5

It is never flipped. The register panel has **two independent gates** in the
shipped page, and the second one is sufficient for G5:

```
line 2491   var INTEREST_PUBLIC = false;
line 2543   /(?:^|[?&])interest=preview(?:&|$)/.test(location.search)
line 2548   if (!INTEREST_PUBLIC && !intPreviewRequested()) return false;
```

With `INTEREST_PUBLIC = false` and no query string, the section is **removed
from the DOM** (`sec.parentNode.removeChild(sec)`) once the Property Check
resolves. An ordinary visitor to `plotnua.ie/disc025-borrowed-garden-check.html`
during G5 sees exactly what they see today — no form, no endpoint-bearing
control, no request.

Colin reaches the panel at
`…/disc025-borrowed-garden-check.html?interest=preview`, which also reveals the
standing marker at line 1036:

> Private preview · not public

So the whole of G5 runs through **the real production page and the real
production payload builder**, with no code change and no public exposure. That
is a stronger proof than a synthetic POST, because it exercises the page's own
`intPayload()` rather than a hand-written body.

Residual, and it is unchanged by G5: `?interest=preview` is already reachable
by URL on the live site today — unadvertised, not secret. It was reachable
before this plan and will be after it. Anyone who found it during G5 could
submit, and their row **would** be written. Mitigations, all already true or
cheap: the URL is not linked from anywhere; no acquisition traffic is sent;
G5 is short and attended; §8 reconciles the exact row count at the end, so an
unexpected row would be detected rather than absorbed.

**Accepted limit, stated plainly:** G5 with writes on means that for its
duration the preview URL is a live write path. If the founder is not content
with that, the alternative is to run the matrix by direct POST from the test
suites rather than through the page — which proves less. The recommendation is
to run through the page, keep G5 to a single sitting, and reconcile counts.

---

## 3 · THE MINIMUM COLIN-ONLY TEST RECORDS

**No genuine homeowner data. Synthetic identities under Colin's own control
only.** Recommended address shape: `g5-<case>@plotnua.invalid` — the `.invalid`
TLD is reserved by RFC 2606 and can never be delivered to, which matters because
`email` is stored in clear in Gardens/Growers and the whole set is deleted at
the end. First name: `G5`. All submissions carry `source: 'garden_interest'`,
set by the page.

The frozen contract requires six accepted cases and no more.

| # | case | tenure | district | what it proves |
|---|---|---|---|---|
| **A1** | **Owner, in pilot** | `own` | `raheny` | The ordinary path. No permission tick, no note required |
| **A2** | **Renter with permission** | `rent` | `killester` | G1B §5: `permission_confirmed` **and** a ≥20-character `garden_note` in the homeowner's own words. Both fields land |
| **A3** | **Out-of-pilot district** | `own` | `elsewhere_in_dublin` | Accepted and stored. The page's `intReceived()` shows the out-of-pilot reply; the row is identical in kind to A1. Out-of-pilot is a *reply* difference, not a storage difference |
| **A4** | **Buying** | `buying` | `donnycarney` | **See §11.** Under the current code this case can only be submitted *with* a permission tick and a note. Under G1B it should not need either. This is the discrepancy, and A4 is the case that exposes it |
| **A5** | **De-duplication** | `own` | `artane` | Re-submit **A1's address** a second time. `emailKeyExists()` returns early: **no Gardens row, no Status log row, no Consent proof row** — and the homeowner still sees `received`. Proves the idempotency short-circuit and that a duplicate is not told apart in the reply |
| **A6** | **Grower side, one record** | — | `raheny` | The grower route is a separate handler with a separate consent sentence and its own vocabularies (`travel_radius`, `space_wanted`). One accepted grower record proves it. `newsletter_consent` deliberately **omitted**, to prove it defaults absent |

Six submissions. **Five rows expected** across Gardens (A1–A4) and Growers (A6);
A5 writes nothing.

`spare_corner` must not be `no_garden` in any case, or founder decision Q1
suppresses the panel entirely and there is nothing to submit.

Not required, and deliberately excluded: `absent tenure`. Via the page it is
**unreachable** — `decide()` is only called once every question is answered
(`if (!(QUESTIONS[i].var in answers)) return QUESTIONS[i]`), so
`inherited_tenure` is always one of `own` / `rent` / `buying` when the panel
appears. Testing it would mean a hand-written POST that no homeowner can
produce. Its behaviour is stated in §11 instead.

---

## 4 · EXPECTED AIRTABLE ROWS AND FIELDS

**One accepted submission writes to three tables**, in this order, from
`writeRecord()`:

### 4A · Gardens (A1–A4)

Always written, by name:

```
first_name, email, email_key (lower-cased), district, water, size_note,
timing, over_18 = true, status = 'interest_submitted',
inherited_tenure, submitted_at (UTC), privacy_version = '2026-10-PHASE2-V1',
consent_text_hash, source = 'garden_interest'
```

Conditionally written, only when present:

```
permission_confirmed (A2, and A4 under current code)
garden_note          (A2, A4)
inherited_spare_corner, inherited_way_in, inherited_your_own_use
inherited_result_key
check_saved_at       (only if the homeowner had saved the check, and only if
                      Date.parse succeeds)
```

Expected **empty** on every row: `confirmed_at`, `last_reconfirmed_at`,
`token_hash`, `token_expires_at`, `manage_token_hash` (no mail adapter, no
tokens are minted), and `human_review_by` / `human_review_at` — these are
stamped by a **person**, never by the Worker. A5 produces no row at all.

### 4B · Status log — one row per accepted submission

```
record_ref  = the Airtable record id of the row just created (rec + 14)
table       = 'Gardens' | 'Growers'
from_status = ''            (empty: from nothing)
to_status   = 'interest_submitted'
at          = UTC stamp
actor       = 'system'
reason      = 'submission_accepted'
```

**Watch item.** The certified schema records `reason` as approved-`singleSelect`
but **live as `singleLineText`**, pending a founder UI action the Meta API
cannot perform. As `singleLineText` the write succeeds. If the field is
converted to `singleSelect` **before** G5, the nine governed option names must
exist first, or `typecast:false` turns every status-log write into a rejected
write — which, because `writeRecord` does not catch per-table, surfaces as
`UNAVAILABLE` to the homeowner *after* the Gardens row already exists. Do not
convert that field during G5.

### 4C · Consent proofs — one row per accepted submission

```
consent_id        autoNumber
email_hash        SHA-256 hex of the LOWER-CASED address — never the address
privacy_version   '2026-10-PHASE2-V1'
consent_text_hash SHA-256 of the exact consent sentence
given_at          UTC stamp
withdrawn_at      empty
erased_at         empty
```

### 4D · The arithmetic to expect

| table | expected rows after §3 |
|---|---|
| Gardens | **4** (A1, A2, A3, A4) |
| Growers | **1** (A6) |
| Status log | **5** |
| Consent proofs | **5** |
| Incidents | **0** |

A5 contributes **nothing to any table**. If Gardens shows 5, the idempotency
guard has failed and G5 stops.

### 4E · Prohibited-field check

The schema names 29 prohibited fields — `address`, `eircode`, `latitude`,
`phone`, `last_name`, `age`, `date_of_birth`, `health`, `ip`, `price`, `rent`
and the rest. Read each written row **field by field** and confirm none is
present. This is not a formality: it is the one check that cannot be recovered
after real data arrives.

---

## 5 · EXPECTED REFUSALS AND THEIR EXACT REASONS

The Worker's reply shapes, verbatim:

```
RECEIVED     200  { ok: true,  state: 'received' }
REFUSED      400  { ok: false, state: 'refused', field: '<name>' }
NOT_OPEN     503  { ok: false, state: 'not_open' }
UNAVAILABLE  503  { ok: false, state: 'unavailable', reason: '<atReason>' }
```

Refusal order in `handleGarden`, which the tests must respect — an earlier
refusal masks a later one:

| order | condition | reply |
|---|---|---|
| 1 | `!CONSENT_TEXT.garden` | `not_open` |
| 2 | missing `first_name` | `refused` · `first_name` |
| 3 | missing or malformed `email` | `refused` · `email` |
| 4 | `district` not in the closed vocabulary | `refused` · `district` |
| 5 | `water` not in vocabulary | `refused` · `water` |
| 6 | `size_note` not in vocabulary | `refused` · `size_note` |
| 7 | `timing` not in vocabulary | `refused` · `timing` |
| 8 | `inherited_tenure` not in `own/rent/buying` — **including absent** | `refused` · `inherited_tenure` |
| 9 | `over_18 !== true` (strict; `"true"` fails) | `refused` · `over_18` |
| 10 | tenure ≠ `own` and no `permission_confirmed` | `refused` · `permission_confirmed` |
| 11 | tenure ≠ `own` and `garden_note` shorter than 20 characters | `refused` · `garden_note` |
| 12 | submitted consent text hashes differently from the Worker's | `refused` · `consent_text` |
| 13 | `!writesEnabled(env)` | `not_open` |
| 14 | Airtable error during the write | `unavailable` · `<reason>` |

Minimum refusals to exercise **with writes on** — six, each a positive control
proving the validator still refuses when the switch is no longer the thing
refusing:

| # | input | expected |
|---|---|---|
| R1 | `district: 'cork'` | `400 refused · district` |
| R2 | consent sentence altered by one character | `400 refused · consent_text` |
| R3 | `over_18: 'true'` (string) | `400 refused · over_18` |
| R4 | `inherited_tenure: 'rent'`, no permission tick | `400 refused · permission_confirmed` |
| R5 | `inherited_tenure: 'rent'`, tick present, 12-character note | `400 refused · garden_note` |
| R6 | `inherited_tenure` absent | `400 refused · inherited_tenure` |

**Every refusal must leave all five tables unchanged.** Count before and after
the refusal block. R1 and R2 were the two positive controls that made the G3
live proof decisive; with writes on they do the opposite job — they prove the
validator, not the switch.

Front-door refusals that must also still hold, and write nothing: no `Origin`
header → `403`, no CORS header; lookalike origin → `403`; `sec-fetch-site:
same-origin` → `400`; `sec-fetch-mode: navigate` → `400`; `GET` on either
route → `405`; unknown path → `404`.

---

## 6 · HOW CONSENT PROOFS AND STATUS LOG SHOULD BEHAVE

**Consent proofs.** Exactly one row per *accepted* submission. It holds
`email_hash` and never the address — verify by inspection that the value is 64
hexadecimal characters and that recomputing SHA-256 of the lower-cased test
address reproduces it exactly. It is the one artefact designed to **survive**
erasure (§7). `withdrawn_at` and `erased_at` are empty on creation and are
stamped later, by a person.

**Status log.** One row per transition. In G5 there is exactly one transition
per record — nothing → `interest_submitted`, `actor: 'system'`, `reason:
'submission_accepted'`. `from_status` is the **empty string**, not the word
"none" and not absent. The schema marks the log append-only *in normal
operation*, with the honest correction recorded on 17 September 2026: its rows
are `deleted_on_subject_erasure: true`, so "append-only" is not absolute.

**The de-duplication consequence, which is easy to get wrong.** A duplicate
`email_key` returns before *any* create. So A5 produces no Gardens row, **no
Status log row and no Consent proof row**. A second expression of consent by
the same address therefore leaves no second proof. That is the current design;
record it as observed behaviour, do not treat it as a defect in G5.

---

## 7 · THE COMPLETE ERASURE TEST

**First, the thing to know before planning anything else: there is no erasure
route in the Worker.** It exposes exactly two paths —
`/v1/garden-register/garden` and `/v1/garden-register/grower`. There is no
`DELETE`, no manage-token route, no withdrawal endpoint. Erasure in V1 is a
**manual operation performed by Colin in the Airtable UI**, triggered by an
email to the published address. G5 proves the *procedure*, not an automated
capability, and the evidence must say so in those words.

### 7A · The procedure, per erased subject

1. Locate the Gardens/Growers row by `email_key`.
2. **Record its record id** (`rec` + 14) before deleting anything — it is the
   only link to the Status log rows, and deleting the row first makes them
   unreachable.
3. Delete the Status log rows matching **both** `record_ref` = that id **and**
   `table` = `Gardens`/`Growers`. The schema is explicit that erasure filters
   on both, and that no email, hash, name or free text is part of the subject
   reference.
4. Delete the Gardens/Growers row.
5. On the matching Consent proofs row — matched by `email_hash`, recomputed
   from the address — stamp `erased_at`. Leave `email_hash`,
   `privacy_version`, `consent_text_hash` and `given_at` untouched. Stamp
   `withdrawn_at` as well if the subject's request was a withdrawal of consent
   rather than only a deletion request.

### 7B · What is deleted, what survives

| artefact | after erasure |
|---|---|
| Gardens / Growers row — `first_name`, `email`, `district`, `garden_note`, every inherited answer | **deleted** |
| Status log rows for that record | **deleted** |
| Consent proofs row | **survives**, with `erased_at` stamped |
| Incidents | untouched (empty in G5) |

### 7C · How the surviving proof is de-identified

It was never identified. `email_hash` is SHA-256 of the lower-cased address and
nothing in the row reverses it. Prove this at erasure time by direct
inspection: the surviving row contains **no** `first_name`, **no** `email`,
**no** `district`, **no** free text — the Consent proofs table has only seven
fields and none of them can hold an address.

Hashing is not anonymisation in the strong sense: an address that is already
guessed can be confirmed by recomputing the hash. The honest claim, and the one
the evidence should make, is that the surviving proof **cannot be read back to
an address** and holds nothing else about the person. It exists to prove
consent was given and honoured, which is the only reason to keep anything.

### 7D · Minimum erasure coverage

Erase **A2** (the richest row: permission tick, free-text note, inherited
answers) and **A6** (to prove the grower side and the `table` discriminator).
Then re-verify: those two rows gone, their status-log rows gone, their two
consent proofs present with `erased_at` set, and **the other three records
completely untouched** — the last check is what proves erasure is surgical
rather than broad.

---

## 8 · RETURNING ALL FIVE TABLES TO THE REQUIRED POST-TEST STATE

The target is the state every prior proof has recorded: **five tables × 0
records**, reconfirmed by direct read, not inferred.

| table | action |
|---|---|
| Gardens | delete the remaining rows (A1, A3, A4) |
| Growers | delete anything left |
| Status log | delete the remaining rows, by `record_ref` + `table` |
| Consent proofs | **see the conflict below** |
| Incidents | confirm 0; it should never have been written |

**A conflict the founder must settle, not me.** §7 requires the consent proof
to *survive* erasure. §8 requires every table at zero. Both cannot hold for the
same row. The two coherent resolutions:

- **(i) Return to five × zero.** After capturing the erasure evidence
  (screenshots or JSON of the surviving proofs with `erased_at` stamped),
  delete the five synthetic consent proofs too. Justification: they are
  *synthetic* — there is no data subject whose consent they evidence, so
  keeping them proves nothing about a real person and keeping the base clean
  before G6 is worth more. **Recommended.**
- **(ii) Keep the five proofs, with `erased_at` stamped.** The base then enters
  G6 with Consent proofs ≠ 0 and the `consent_id` autoNumber already advanced,
  which every later count must allow for, and every future "tables at zero"
  check must be restated.

Either way the evidence pack must carry the surviving-proof state **before**
any deletion, or the erasure proof is destroyed by the clean-up.

Note that `consent_id` is an `autoNumber`: it does **not** reset when rows are
deleted. After G5 the first genuine homeowner's consent proof will be
`consent_id` 6 or higher. That is expected and must not later be read as a lost
record.

---

## 9 · WHICH G2 NEGATIVE CONTROLS MUST BE RERUN WITH WRITES ENABLED

**`prove-deployed.mjs` must NOT be rerun unchanged while writes are on.**

Its own header claims it "cannot create a record even if the Worker were wide
open … it sends no valid consent text for a write it expects to succeed."
**That comment is false**, and this matters:

```js
const GARDEN_CONSENT = "I'm over 18, and I'd like PlotNua to keep this and
                        tell me if someone nearby is looking for growing space.";
const gardenBody = { first_name: 'Deploy', email: 'deployprobe@example.com',
  district: 'raheny', water: 'outside_tap', size_note: 'small',
  timing: 'flexible', inherited_tenure: 'own', over_18: true,
  consent_text: GARDEN_CONSENT };
```

Both consent strings are **byte-identical** to `CONSENT_TEXT.garden` and
`CONSENT_TEXT.grower` in the Worker, and both bodies are complete and valid. D1
and D2 are valid writes that happen to be stopped by the switch. With
`WRITES_ENABLED = "true"`, running that file would create **two Gardens/Growers
rows, two Status log rows and two Consent proofs** under
`deployprobe@example.com` and `deployprobe2@example.com` — and would report
them as FAILURES, because it asserts `503 not_open`.

| control | with writes on | handling |
|---|---|---|
| **D1** garden route `not_open` | **inverts** — becomes `200 received`, and writes | Do not run as-is. Fold into §1 step 3 as the deliberate "the switch really flipped" check, and count its row |
| **D2** grower route `not_open` | **inverts** — becomes `200 received`, and writes | Same. Either treat its row as A6, or expect seven submissions rather than six |
| D3 `GET` garden → 405 | unchanged | rerun |
| D4 `GET` grower → 405 | unchanged | rerun |
| D5 `GET` root refused | unchanged | rerun |
| D6 no Origin → 403, no CORS header | unchanged | rerun — **required** |
| D7 lookalike origin → 403 | unchanged | rerun — **required** |
| D8 `sec-fetch-site: same-origin` → 400 | unchanged | rerun — **required** |
| D9 `navigate` mode → 400 (raw socket) | unchanged | rerun — **required** |
| D10 preflight 204, echoes only the allowed origin | unchanged | rerun |
| D11 preflight 403 for anyone else | unchanged | rerun |
| D12 no reply mentions mail, token, confirm or verify | unchanged | rerun — **required**, and it means more with writes on |
| D13 unknown path → 404 | unchanged | rerun |

**Recommendation:** before G5, split `prove-deployed.mjs` into the eleven
switch-independent controls (D3–D13) and the two switch-dependent ones (D1, D2),
and **correct the false header comment**. That is a test-suite change, not a
product change, and it is the only code edit this plan would ask for — proposed
here, not performed.

Also rerun with writes on, unchanged in meaning: `prove-g3-deployed.mjs`
(10/0) — but note it submits `g3probe@plotnua.invalid`, so **with writes on it
creates a row**. Either count it as a seventh record or run it last, before the
clean-up.

Unaffected and rerun as pure regression: `prove-g3.mjs` (166/0),
`prove-g3-mutations.mjs` (25/25), `prove-guards.mjs` (65/0),
`prove-g3-review-harness.mjs` (46/0) — all local, none touches the network.

---

## 10 · RETURNING `WRITES_ENABLED` TO FALSE

1. Set `WRITES_ENABLED = "false"` in `wrangler.toml`.
2. `wrangler deploy`.
3. Confirm the deployed Worker sha256 is still `4c5a4783…` — the source must
   not have changed, only a var.
4. **Observe a refusal**, do not assume one: one valid garden POST and one
   valid grower POST must each return `503 {ok:false,state:'not_open'}`.
5. Confirm the five tables are in their agreed post-test state (§8) **after**
   those two POSTs, proving the refusal wrote nothing.
6. Record the new Worker version id alongside the pre-G5 one
   (`ed9d2dc6-69a0-4c88-91f3-9418a0954bc7` was the G3 freeze version).

Leave the secrets in place. They are a precondition, not a switch, and removing
them would make the next flip harder to reason about.

---

## 11 · THE FROZEN-GOVERNANCE / CODE DISCREPANCY — NOT RESOLVED HERE

**G1B §5, verbatim:**

| `inherited_tenure` | storable | may reach introduction | condition |
|---|---|---|---|
| `own` | yes | **yes** | Ordinary confirmation only |
| `rent` | yes | **only with explicit permission** | `permission_confirmed` **and** the homeowner's own words in `garden_note` |
| `buying` | yes | **no** | Stored, kept warm, never promoted. One clarifying question permitted |
| unconfirmed / absent | yes | **no** | As `buying` |

> "Unconfirmed tenure is a reason not to introduce, never a reason to discard a
> willing homeowner."

**The current Worker, verbatim:**

```js
if (!tenure) return REFUSED(cors, 'inherited_tenure');
...
if (tenure !== 'own') {
  if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
  if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
}
```

The shipped page mirrors it: `if (answers.tenure && answers.tenure !== 'own')`
requires both the tick and a 20-character note.

### Two divergences, of different weight

**(a) `buying` is treated as `rent`.** G1B makes storage unconditional for
`buying` and requires no permission; the code refuses a `buying` submission
that lacks a permission tick and a ≥20-character note. The code is **stricter
than the contract**, in the direction of refusing a willing homeowner — which
is the specific outcome G1B's closing sentence forbids.

**(b) Absent tenure is refused.** G1B says storable, never promoted. The code
refuses outright. **But it is unreachable from the page**: `decide()` only runs
once every question is answered, so tenure is always `own`/`rent`/`buying` when
the panel exists. Absent tenure can only arrive by hand-written POST. This is
a real divergence of **contract from code**, with **no reachable homeowner
consequence**.

### Does it prevent a faithful G5 proof?

**For (b): no.** Nothing a homeowner can do reaches it. Record it as a known,
unreachable divergence and move on.

**For (a): yes, partially, and only for case A4.** G5 cannot faithfully prove
what the contract specifies for `buying`, because the only `buying` submission
the system accepts is one that carries permission evidence the contract does
not ask for. Concretely, A4 can be run in exactly one of two ways:

- **as the code behaves** — supply tick and note, get a row, and record that
  the row carries `permission_confirmed = true` on a `buying` record, which the
  contract neither requires nor expects; or
- **as the contract specifies** — supply neither, and record `400 refused ·
  permission_confirmed` as the *expected* outcome under current code and a
  *divergence* from G1B §5.

Either is honest. Neither is the proof that `buying` is "storable, never
promoted". **The recommendation is to run A4 the second way** — submit without
the tick, record the refusal as the measured divergence, and let the founder
decide. It produces evidence of the gap rather than evidence that papers over
it. Under that choice Gardens holds **3** rows, not 4, and the §4D arithmetic
adjusts accordingly.

### The founder decision required before writes are enabled

**D-G5-1.** Which is authoritative for `buying`?

| option | consequence |
|---|---|
| **(1) The contract.** Relax page and Worker so `buying` needs no permission tick and no note | A code change to the frozen G3 page **and** the Worker, each needing its own bounded builder, guard-capability proof and full re-proof. G3's freeze is reopened. Not a small change |
| **(2) The code.** Amend G1B §5 so `buying` requires permission evidence, as `rent` does | Amends a **FROZEN** contract that was closed on 7 October 2026 with "no residual items". Governance-only; no code moves; nothing re-proved |
| **(3) Neither yet.** Record the divergence, run A4 as a measured refusal, carry it as an open item into G6 | No change to anything. G5 proceeds. The gap is documented rather than resolved, and a `buying` homeowner is refused until it is settled |

**My recommendation is (3) for G5 and a deliberate choice between (1) and (2)
before G6**, because G6 is where a real person who is mid-purchase gets turned
away. `buying` is not a rare answer among people who have just bought a house
with a garden they are not yet using — which is close to the register's best
candidate. That makes this worth settling properly, not quickly.

**It is not mine to settle, and this plan does not settle it.**

---

## 12 · EVIDENCE REQUIRED TO DECLARE G5 PASS

All fourteen. Any one missing and the verdict is WITHHELD, not PASS.

| # | evidence |
|---|---|
| 1 | Pre-flight: five tables × 0, deployed Worker sha256 `4c5a4783…`, live page sha256 `bd08ce67…`, local suites 166/0 · 25/25 · 65/0 · 46/0 |
| 2 | Both secrets confirmed present; the flag flip observed to change a `503 not_open` into a `200 received` |
| 3 | `INTEREST_PUBLIC` confirmed still `false` in the live page source, and an ordinary (no query string) visit confirmed to contain **no** `#bgInterest` in the DOM |
| 4 | Each accepted case recorded field by field, from a direct Airtable read, against the §4A list |
| 5 | Exact row counts in all five tables, matching §4D as adjusted by the A4 decision |
| 6 | A5 proven to write **nothing** in any of the three tables, while still replying `received` |
| 7 | Each of R1–R6 returning the exact `state` and `field`, with table counts unchanged before and after |
| 8 | The switch-independent front-door controls green (D3–D13 equivalents) |
| 9 | `email_hash` proven to be SHA-256 of the lower-cased address by recomputation, and proven to be the only address-derived value stored in Consent proofs |
| 10 | Prohibited-field sweep: none of the 29 names present on any written row |
| 11 | Erasure of A2 and A6: rows gone, status-log rows gone, consent proofs surviving with `erased_at` stamped, and the untouched records proven untouched |
| 12 | The agreed post-test table state (§8) confirmed by direct read, after the final two refusal POSTs |
| 13 | `WRITES_ENABLED` back to `"false"`, deployed, and a refusal **observed** on both routes |
| 14 | The §11 divergence recorded as measured, with the founder decision D-G5-1 either taken or explicitly carried forward |

Written up as a `G5-PROOF-RECORD.md` beside the G3 freeze record, with the
before/after hashes and the Worker version ids on both sides of the flip.

### 12A · Founder decisions needed BEFORE G5 is executed

| # | decision | recommendation |
|---|---|---|
| **D-G5-1** | `buying` — contract, code, or carry forward (§11) | **(3) carry forward**, run A4 as a measured refusal |
| **D-G5-2** | Consent proofs at the end — return to five × zero, or keep with `erased_at` (§8) | **(i) return to zero**, after capturing the surviving-proof evidence |
| **D-G5-3** | Whether to split and correct `prove-deployed.mjs` first (§9) | **yes** — it is a test-only change and the alternative is two unplanned records and two false FAILs |

---

## EXACT STOP CONDITIONS

Stop immediately, flip `WRITES_ENABLED` back to `"false"`, and report, on **any**
of these:

1. **Any row appears that Colin did not submit.** This is the one that means a
   stranger found the preview URL. Stop, record, do not delete it without
   deciding whether it is a genuine person owed a reply.
2. **A5 creates a Gardens row.** The idempotency guard has failed and duplicate
   submissions are accumulating.
3. **Any prohibited field appears** on any written row.
4. **A Consent proofs row contains an address**, or `email_hash` fails to match
   the recomputed SHA-256.
5. **A write partially succeeds** — a Gardens row with no Status log row, or no
   Consent proof. `writeRecord` has no transaction; a mid-sequence Airtable
   failure leaves exactly this state, and it must not be left in the base.
6. **Any refusal (R1–R6) writes anything.**
7. **`typecast` behaviour differs from expectation** — an option that does not
   exist being silently created rather than rejected.
8. **Any reply mentions mail, token, confirm or verify** (D12's assertion).
   There is no mail adapter; such a reply would mean the deployed Worker is not
   the source that was read.
9. **The deployed Worker sha256 is not `4c5a4783…`** at any check.
10. **`INTEREST_PUBLIC` is found to be anything but `false`** in the live page.
11. **An `unavailable` reply** on a valid submission — Airtable is refusing, and
    the reason must be understood before another write is attempted.
12. **Anything that would require a code change** to continue. G5 is a proof,
    not a build. A code change means stopping, reporting, and a separate
    authorisation.

### STANDING CONSTRAINTS FOR THE WHOLE OF G5

- **No genuine homeowner data.** Colin-controlled synthetic identities only.
- **No acquisition traffic.** No posting, no sharing, no linking of the preview
  URL anywhere.
- **No outreach.** Nobody is contacted about anything.
- **No G4.** Not started, not prepared.
- **No G7 and no email work.** There is no mail adapter; `EMAIL_ENABLED` stays
  `"false"` and flipping it would not enable email.
- **PS-3 does not block G5 or G6.** The insurer question gates the first real
  introduction and nothing earlier. The frozen gate model must not be restated.
- **`INTEREST_PUBLIC` is not opened**, as part of this plan or its execution.
- **PS-1 is CLOSED** and the footer is not reopened.

---

**PLAN ONLY.** No switch changed. No Airtable write. No deployment. No code
edited. The only file written today is this one.
