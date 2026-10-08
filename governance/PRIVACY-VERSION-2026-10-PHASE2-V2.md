# PRIVACY VERSION 2026-10-PHASE2-V2

**Status:** FROZEN — immutable record of the homeowner-facing privacy terms
**Applies to:** every register row stamped `privacy_version = 2026-10-PHASE2-V2`
**Approved:** 8 October 2026, founder decision
**Supersedes:** `2026-10-PHASE2-V1` (approved 7 October 2026 at the G1B freeze; never published for real use, never used for a genuine submission — all five register tables at 0 at the time of supersession)
**Scope:** PlotNua Gardener Register, Airtable base `appUie3wPmPITfMW7`
**Amendment record:** [`G1B-V2-AMENDMENT-2026-10-08.md`](G1B-V2-AMENDMENT-2026-10-08.md)

This file exists so that the `privacy_version` stamped on a stored row points at
something that cannot change. The live page can be edited; this cannot. If the
homeowner wording changes again, a NEW version file is created and the Worker's
`PRIVACY_VERSION` is incremented. This file is never edited after any row
carries its version.

The wording below is captured verbatim from the built page. It has not been
rewritten, shortened, corrected or improved beyond the single founder-approved
amendment recorded in §10.

---

## 1 · The consent sentence

Presented beside a single checkbox. The sentence carries the over-18 statement
itself; there is no second box.

**Garden (homeowner) route — the sentence shown on the interest form:**

> I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is
> looking for growing space.

**Grower route — recorded here because this privacy version governs both:**

> I'm over 18, and I'd like PlotNua to keep this and tell me about possible
> growing space nearby.

Source: `disc025-borrowed-garden-check.html` lines 2496–2498, rendered to the
label at line 2827. Canonical copy: `worker/garden-register/src/index.js`
lines 108–111. The two are **byte-identical**.

| | SHA-256 |
|---|---|
| Garden | `85c436084349e841017171ef12e2c0d5e28fa24a82d99f4c2beaca8f6eee9b9c` |
| Grower | `32ba8b3ec621ed6e15edf0cc4c4fe95bec7b386d9c95179737fe9179990148f1` |

**Both values are UNCHANGED from V1.** The amendment that produced V2 touched
the privacy notice only. The consent sentence and the privacy notice are
separate artefacts with separate lifecycles: the Worker hashes the consent
sentence and never hashes the notice, and the privacy version is a label
stamped on rows, not an input to the hash.

**Standing rule: a privacy-version increment never, by itself, changes the
consent sentence.** If a future amendment does change the consent wording, the
hash changes, the Worker's constant must change in the same commit, and every
previously stored row keeps its old hash and its old version.

Both hashes were written to live `Consent proofs` rows during G5 under V1 and
verified by recomputation (G5 §7). They remain valid.

### How the hash is enforced

The page sends the consent string it actually rendered. The Worker hashes what
arrives and compares it to its own constant (`src/index.js` line 347 garden,
409 grower). A mismatch returns
`400 {ok:false, state:'refused', field:'consent_text'}` and **writes nothing**.

A page whose wording drifts from this file therefore **stops working** rather
than silently storing consent to text nobody approved. Proven by G5 case R2:
the sentence altered by one character returned `400 refused · consent_text`.

---

## 2 · The privacy notice shown beside the interest form

Source: `disc025-borrowed-garden-check.html` lines 1118–1159,
`<details class="bg-int-notice" id="bgIntNotice">`, 3,103 bytes,
sha256 `f67b4ae7166ecca27f1e6106c7fec92cf35181feace3d50c7b76c0241aee31c7`.

Presented as a disclosure the homeowner opens. Summary line:

> Before you join the register — what we keep, and what we never ask for

Body, verbatim:

> **What we keep about you and your garden.** Your first name, your email
> address, the district you chose, and what you told the Property Check about
> your garden — its size band, water, how someone would get in, and whether you
> own the property — and the result the Property Check produced from those
> answers. We also keep the administrative records needed to manage your
> registration, your consent and its status.
>
> **What we never ask for.** Your address, your Eircode, your phone number, your
> surname, your age, photographs of your garden, or anything about your health.
> We don't collect them, so we can't hold them or lose them.
>
> **Why we keep it.** So that we can tell you if someone nearby is looking for
> growing space.
>
> **Joining the register does not share your details with anyone.** No other
> person sees your record. There is no public listing, no public map, no profile
> page, and no directory. Your record is private to PlotNua.
>
> **If we think there's a possible fit, we'll email you and ask.** We'll describe
> the other person in general terms only — a district, how much space they're
> looking for, roughly when. No name, no email, no contact details.
>
> **Nothing is shared until you say yes.** Your email address only reaches
> another person after you have said yes to that specific introduction. Saying
> yes once is yes to that one introduction and nothing more. If you don't reply,
> nothing happens.
>
> **We never sell your information**, and we never pass it to anyone for
> advertising.
>
> **Leaving.** Email hello@plotnua.ie and we will delete your record. There's
> nothing to cancel and no notice period.
>
> **How long we keep it.** We keep your record for a maximum of 24 months. You
> can ask us to delete it at any time, and we may delete it sooner if it is no
> longer needed.
>
> **One thing we keep after deletion.** When we delete your record we keep a
> separate note recording that you gave permission and that we honoured your
> request to remove it. That note holds a one-way digital fingerprint made from
> your email address, not the email address itself. It exists so we can prove we
> did what you asked.

**The first paragraph is the only one that differs from V1.** The other nine are
byte-identical, proven by builder guard P7.

---

## 3 · What PlotNua stores — the actual field set

The notice above is the promise. This is the implementation, read from
`src/index.js` lines 354–380 (garden route). Recorded so the two can be
compared without reading code.

**Gardens — always written**

`first_name` · `email` · `email_key` (the address lower-cased) · `district` ·
`water` · `size_note` · `timing` · `over_18` (always `true`; a `false` is never
stored) · `status` · `inherited_tenure` · `submitted_at` ·
`privacy_version` · `consent_text_hash` · `source`

**Gardens — written only when present**

`permission_confirmed` · `garden_note` (free text, max 600 chars) ·
`inherited_spare_corner` · `inherited_way_in` · `inherited_your_own_use` ·
`inherited_result_key` · `check_saved_at`

**`inherited_result_key` — the field this version exists to disclose.**
It holds the result the Property Check produced, stored **as a key, never as
prose**. A stored sentence would freeze a position PlotNua may stop standing
over; a key is re-read against today's copy. This is the same discipline the
saved Property Checks use. It is now explicitly covered by the notice's first
paragraph. The field is **unchanged** by this amendment — kept, not removed, and
not altered in shape.

**Status log — one row per accepted submission**

`from_status` · `to_status` · `actor` (`system`) · `reason`
(`submission_accepted`) · `record_ref` · `table`

**Consent proofs — four fields only** (`src/index.js` lines 289–294)

`email_hash` (SHA-256 of the lower-cased address) · `privacy_version` ·
`consent_text_hash` · `given_at`

Plus `erased_at`, stamped on erasure.

The Consent proofs table **cannot hold an address, a name, a district or any
free text** — the fields do not exist. Verified in G5 §7.

**No stored field was added, removed or altered by this amendment.**

---

## 4 · What PlotNua does not ask for

No address · no Eircode · no coordinates · no phone number · no surname · no
age (only the over-18 statement) · no photographs · no health information · no
payment details.

Enforced structurally, not by policy: the register's closed vocabularies have no
field for any of these, and Airtable runs with `typecast: false`, so an
unexpected field is rejected rather than coerced. The coarsest location PlotNua
holds is a district from a closed list of six.

---

## 5 · Purpose

To tell a registered homeowner if someone nearby is looking for growing space,
and to ask them before anything is shared.

Not for advertising. Not sold. Not passed to third parties. No public listing,
map, profile or directory exists, and no code to produce one exists.

---

## 6 · Retention — 24 months, and how it is enforced

The notice states a maximum of 24 months.

**This is a MANUAL OPERATIONAL COMMITMENT. It is NOT enforced in code.** The
Worker contains no retention, expiry or TTL logic — searched and confirmed at
this commit. There is no scheduled job. Honouring the 24-month ceiling is an
operational responsibility of the founder, and a future version of this register
should either automate it or record the manual review date that discharges it.

**No retention automation was built as part of this amendment, by founder
decision.** The retention rule itself is unchanged from V1.

Stated plainly here because a retention promise with no mechanism behind it is
exactly the kind of claim that quietly becomes untrue.

---

## 7 · Erasure and contact route

`hello@plotnua.ie`, published three times in homeowner-visible copy: in the
notice ("Leaving"), in the accepted end state, and in the failure end state.

**There is no erasure route in the Worker.** It exposes two POST paths and
nothing else. Erasure is a manual Airtable operation, performed in the order
proven by G5 §8:

1. record the subject row id
2. delete Status log rows matching **both** `record_ref` and `table`
3. delete the subject row
4. stamp `erased_at` on the Consent proofs row matched by recomputed `email_hash`

Proven surgical in G5: two subjects erased, three untouched subjects verified
field-by-field as untouched.

**Receipt at `hello@plotnua.ie` is a separate founder gate (R0) and must PASS
before genuine registrations are accepted.** It is the entire mechanism by which
a homeowner can exercise the erasure right this notice promises.

---

## 8 · The hash-only consent proof that survives erasure

When a record is erased, the Consent proofs row survives with `erased_at`
stamped. `email_hash`, `privacy_version`, `consent_text_hash` and `given_at` are
left untouched.

It holds a one-way SHA-256 of the lower-cased email address and **never the
address**. It cannot be used to contact anyone, and it cannot be reversed. Its
only purpose is to evidence that consent was given under a stated privacy
version and that an erasure request was honoured.

Verified in G5 §8: Consent proofs 2 and 5 survived their subjects' deletion with
every other field intact.

### `consent_id` begins at 6

`consent_id` is an Airtable autoNumber. It reached 5 during G5's synthetic proof
under V1 and was deliberately not reset. **The first genuine homeowner's consent
proof will be numbered 6 or higher. This is expected and must never be read as
five lost records.**

---

## 9 · Version identity and frozen artefacts

| | |
|---|---|
| `privacy_version` | `2026-10-PHASE2-V2` |
| Set at | `worker/garden-register/wrangler.toml` line 24 |
| Stamped on | every Gardens row, every Growers row, every Consent proofs row |
| Garden consent hash | `85c436084349e841017171ef12e2c0d5e28fa24a82d99f4c2beaca8f6eee9b9c` (unchanged) |
| Grower consent hash | `32ba8b3ec621ed6e15edf0cc4c4fe95bec7b386d9c95179737fe9179990148f1` (unchanged) |

**Artefacts frozen at this version** (post-change, measured)

| File | SHA-256 |
|---|---|
| `disc025-borrowed-garden-check.html` | `b73ebdcbb44e04c79e8c824264bf5b9c10f107866fdb41ead164a9cd7d470090` |
| `atlas-tools/build-g3-garden-interest.py` | `fd399f7cffeb243f7acf0faae1c7e9b8c8652c62d4a10e85a6dbb238167a2c45` |
| `worker/garden-register/wrangler.toml` | `ad6778b1d20b81261409342db095f786d6a4cf5878fc41e3f7976de72cc92a39` |
| `worker/garden-register/src/index.js` | `66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79` (**UNCHANGED**) |

`src/index.js` reads `env.PRIVACY_VERSION` and never contains the version
string, so no Worker code changed. The `wrangler.toml` change still requires
`wrangler deploy` for the new value to take effect.

**State at freeze:** `WRITES_ENABLED = "false"` · `EMAIL_ENABLED = "false"` ·
`INTEREST_PUBLIC = false`. No real homeowner data exists. All five tables at 0.

---

## 10 · Amendment record — what changed and what did not

**Founder decision, 8 October 2026.** Before G6, a readiness audit found that
the register stores `inherited_result_key` — the result the Property Check
produced — while the V1 notice described only the answers the homeowner
supplied. One stored field therefore had no homeowner-facing disclosure.

**The founder decided to KEEP the field and amend the notice.**

**What changed**

- The "What we keep about you and your garden" paragraph now reads
  `… and whether you own the property — and the result the Property Check
  produced from those answers. We also keep …`
- `privacy_version` advanced from `2026-10-PHASE2-V1` to `2026-10-PHASE2-V2`
- A new guard, `G23f3`, asserts the disclosure so the sentence cannot silently
  drift. Its absence under V1 is how the omission survived a freeze.

**What did NOT change**

- Both consent sentences, byte-for-byte, and both SHA-256 values
- Every other paragraph of the privacy notice (nine paragraphs, guard P7)
- Every stored field, including `inherited_result_key` itself
- The 24-month retention rule, and its status as a manual commitment
- Any matching, promotion or introduction rule
- `worker/garden-register/src/index.js`
- `WRITES_ENABLED`, `EMAIL_ENABLED`, `INTEREST_PUBLIC` — all still false
- The historical G5 proof under V1, which remains untouched and accurate

**G7 remains BLOCKED** pending the insurer / broker prerequisite. Introduction
eligibility must continue to exclude `buying`, absent tenure and unconfirmed
tenure. This amendment does not touch G7 and does not authorise G6.

**Mechanism.** Applied by the bounded builder
`atlas-tools/build-g3-privacy-v2.py`, which asserted the substitution was
unique, that the consent hashes survived, that the byte delta was exactly `+84`
per file, that the other nine paragraphs were untouched, and that all three
switches remained false. Each of its eight guards was demonstrated capable of
failing against deliberately mutated copies before the real run.
