# THE BORROWED GARDEN · GROWER REGISTER · BUILD RECORD (16 October 2026)

**Founder instruction:** "PlotNua — Community Roots Gardener Register development", 16 Oct 2026.

**State: BUILT AND CLOSED.**
- Local commits only: not pushed, Worker not deployed.
- No email sent. No host registration read or changed.

**Naming:** "Community Roots" is an independent garden-sharing organisation (Atlas ORG-000202, Researching, not a partner), listed in the Borrowed Garden Provider Explorer. This register is therefore named for PlotNua's own Discovery:
- **Garden Owner Register:** hosts, live since 12 Oct.
- **Grower Register:** gardeners, this build.

A different public name is a text change in `build-grower-register.py`. Guard G11 only refuses the third party's name.

## 1 · What already existed (reused, not rebuilt)

| Piece | Existing since | Used as |
|---|---|---|
| Worker route `/v1/garden-register/grower` with validation, duplicate handling, status ceiling and consent proof | G2, 7 Oct | The gardener route, now with its own switches |
| Frozen G1B §3 gardener notice and consent sentence | 7 Oct | Verbatim on the page |
| `Growers` table in base `appUie3wPmPITfMW7` (vocabularies identical to the Worker) | Phase 2 V1 | Gardener records; **no schema change needed to register** |
| `Status log` (`table = Growers`) and `Consent proofs` (separated by consent hash) | Phase 2 V1 | Unchanged |
| R5 safety protocol and introduction-consent rules | G1B §4, §6, §7 | Summarised on the page; unchanged |
| Artist Register page pattern (closed by default, preview flag, states, honeypot) | 14 Oct | Page structure and styling |

## 2 · What was built

| File | What |
|---|---|
| `worker/garden-register/src/index.js` | The grower route gets its own two stops: `GROWER_WRITES_ENABLED` and `GROWER_PRIVACY_VERSION`. Strict 10-key allow-list. Grower records carry the grower notice version. **The garden handler is byte-identical** (builder guard G8). |
| `worker/garden-register/wrangler.toml` | `GROWER_WRITES_ENABLED = "false"`, `GROWER_PRIVACY_VERSION = ""`. The garden settings are unchanged. |
| `worker/garden-register/test/prove-grower-route.mjs` | 54 checks, plus 5 mutations caught |
| `borrowed-garden-grower-register.html` | The gardener journey, generated |
| `atlas-tools/build-grower-register.py` | Bounded builder, guards G1–G11 |
| `atlas-tools/prove-grower-register-builder.py` | Guard capability proof: 16/16 |
| `atlas-tools/prove-grower-register-page.py` | Chromium proof with a stubbed endpoint: 37/37 |
| `atlas-tools/borrowed-garden-pair-shortlist.py` and `prove-…` | Founder-only, offline possible-pair shortlist: 13/13 on synthetic data |
| `governance/PRIVACY-VERSION-2026-10-PHASE2-V6-DRAFT.md` | Privacy wording for growers, **draft** |

### Finding in the live system (needs a founder decision)

The Worker currently deployed has `WRITES_ENABLED = "true"` (the Garden Owner Register is open). In that code, the same switch also opens the grower route.

- **The exposure:** a request sent directly to the grower endpoint would be written to `Growers` under notice V3, which does not describe growers.
- **What limits it:** no page sends to that route, and the Origin check blocks browsers on other sites. A script could still forge the header.
- **The fix:** deploy this commit's Worker (`npx wrangler deploy` from `worker/garden-register/`), which closes the grower route. Proof M5 shows the old behaviour and that this change closes it.
- **What it doesn't change:** the garden route behaves identically.

## 3 · The gardener journey

| Stage | On the page |
|---|---|
| **Discover** | Hero: "Somewhere to grow, closer than you think." Free, private, non-binding; beginners welcome. |
| **Explore** | Four steps (two registers, a separate email to each person, nothing shared until both say yes). Honest status: no garden available today; four pilot areas; no promises. A link to the Provider Explorer for growing sooner elsewhere. |
| **Check your interest** | Six questions answered in the browser: area, travel, space, timing, experience, working style. **Nothing is sent.** A tailored, honest result; the four kept answers pre-fill the form. |
| **Join the register** | First name, email, area, travel, space, timing, optional note (with a prompt for interests, experience, working style and days). Frozen consent tick. "What we keep" notice. |
| **Confirmation** | "You're on the Grower Register": a register, not a match; we'll email and ask first; we may never find a garden; an out-of-area line; how to leave. Plus truthful not-open, refused and failed states. |
| **Potential future match** | Founder-only shortlist, then the G1B two-email consent route. **Introductions stay blocked at G7** (insurance question). |

## 4 · Registration fields

**Kept:**
- first_name, email, district, travel_radius, space_wanted, timing;
- growing_note (optional);
- over_18 and the consent hash;
- source = grower_register.

**Asked but not kept:** experience and working style. They only shape the check's advice; a person can repeat them in the note if they want us to know.

**Not collected:** surname, address, Eircode, phone, age, health, and a newsletter tick (which the Worker now refuses).

**Your list, mapped:**

| You asked for | Covered by |
|---|---|
| Name, email, general location | first_name, email, district |
| Areas willing to travel to | travel_radius |
| Typical availability | timing (roughly when); days go in the note |
| Growing interests, experience, independent or collaborative | In the check (not stored) and invited in the note |
| Consent | The frozen sentence |

**Possible V2:** structured `experience` and `working_style` fields. They would need:
- two Airtable fields;
- two Worker vocabularies;
- a privacy amendment.

Not done, because the frozen contract and minimisation favour the note for the pilot.

## 5 · Atlas / data integration

**One base, one Worker, separate tables and switches:**
- **Base:** `appUie3wPmPITfMW7`, the same one the Garden Owner Register uses.
- **Hosts:** `Gardens`.
- **Gardeners:** `Growers`.
- **Status log:** shared, with `table` naming the register.
- **Consent proofs:** shared. The consent hash differs per register, so the register can be told apart with no new field.

**Founder steps in the Airtable UI (about 10 minutes, any time; registering does not need them):**

1. **`Growers`:** add `record_ref` (formula `RECORD_ID()`), `human_review_by` (single line text) and `human_review_at` (date and time). This gives parity with `Gardens` and lets the shortlist tool name pairs without personal data.
2. **`Gardens`:** add `record_ref` (formula `RECORD_ID()`).
3. **Views on `Growers`:**
   - **New this week:** submitted_at within the past week, newest first.
   - **Notes to screen:** growing_note is not empty.
   - **Erasure due:** submitted_at is before 24 months ago.
4. **Optional, `Possible pairs` table, founder-only.** Fields:
   - garden_ref, grower_ref (text);
   - proposed_at;
   - reason (long text, no personal data);
   - garden_asked_at, garden_answer;
   - grower_asked_at, grower_answer;
   - introduced_at;
   - outcome.

   Every row is entered by hand.
5. **Weekly review:** add `Growers` to the existing G6 procedure. Same screening rules (junk, over-sharing in notes). **Do not change `status`.**

**Contact history:** stays in Gmail plus the `Status log`. No supplier CRM is involved: registrants are members of the public, not suppliers.

## 6 · Matching framework (v1, founder-controlled)

**Gates:**
- Neither side is paused or withdrawn.
- Both sides are in a pilot district.
- Garden tenure follows G1B §5:
  - own: ok;
  - rent: only with the tick plus a statement of 20+ characters;
  - buying or absent: never put forward.

**Fit:**
- **Distance:** the approximate district distance is within the grower's travel radius.
- **Space:** the garden's band is at least what the grower wants.
- **Timing:** compatible.

**Flags (prompt a conversation):** no water or not sure; size not sure; either note present.

**Output:** record references, a score and the reasons only. Every row reads "founder review; nobody contacted".

**Then (only after G7 is unblocked):**
1. The founder chooses a pair.
2. Separate G1B §6 consent emails go to each person, describing the other in general terms only.
3. After two yeses, the G1B §7 joint email.
4. No reply is never consent.

**Not built, by design:** automatic matching, ranking shown to anyone, profiles, or any stranger-to-stranger introduction.

## 7 · Discovery entry point (prepared, NOT applied)

The Borrowed Garden Discovery is not touched (guard G8). At opening, with approval, add a two-path "Take part" block after the Property Check section:
- "I have a garden" goes to the Property Check (the existing host journey).
- "I'd like to grow" goes to `borrowed-garden-grower-register.html`.

Guard G4 refuses any inbound link while the register is closed.

## 8 · Activation sequence (each step needs the founder)

1. Approve the page (preview: `…/borrowed-garden-grower-register.html?register=preview`).
2. Approve Privacy V6. Apply it with a bounded builder (marker `PLOTNUA-GROWER-PRIVACY-V6`).
3. **Deploy the Worker first** (grower route closed). This also closes the live exposure in §2. **Order matters:** until this deploy, the live Worker would WRITE a `?register=preview` submission made from plotnua.ie.
4. Push. The page is live but closed and noindex, and the form isn't rendered.
5. **Controlled test**, with your own details only:
   1. Deploy once with `--var GROWER_WRITES_ENABLED:true --var GROWER_PRIVACY_VERSION:2026-10-PHASE2-V6`.
   2. Submit from `?register=preview`.
   3. Check the `Growers`, `Status log` and `Consent proofs` rows.
   4. Resubmit the same address: expect no new row.
   5. Erase by the usual procedure.
   6. Redeploy closed.
6. **Open:**
   1. In `wrangler.toml`: `GROWER_WRITES_ENABLED = "true"` and `GROWER_PRIVACY_VERSION = "2026-10-PHASE2-V6"`; deploy.
   2. Fill in `OPEN_APPROVAL`, set `GROWER_PUBLIC = True` and rebuild.
   3. Add the Discovery entry point, the sitemap entry and Search; push.
7. Weekly review, with a target to agree. It's suggested to mirror the hosts: five genuine growers or eight weeks.

**Emergency close:** set `GROWER_WRITES_ENABLED = "false"` and deploy. The page then shows "isn't open yet" to anyone who submits.

## 9 · Tests run

| Suite | Result |
|---|---|
| `prove-grower-route.mjs` (new) | 54/54; 5/5 mutations caught |
| `prove-guards.mjs` (existing) | 74/74, unchanged |
| `prove-g6-deprecated-fields.mjs` | 72/72, unchanged |
| `prove-worker-mutations.mjs`, `prove-g6-worker-mutations.mjs` | 3/3, 10/10 |
| `prove-grower-register-builder.py` (new) | 16/16 (two guards were blind at first; fixed) |
| `prove-grower-register-page.py` (new, Chromium) | 37/37: desktop, 390px mobile, keyboard-only, validation, success, duplicate, not-open, refused, network failure, honeypot, axe WCAG 2.1 AA (no serious/critical findings) |
| `prove-borrowed-garden-pair-shortlist.py` (new) | 13/13, synthetic data |
| Host regression | See the report: host files byte-identical, plus the host suites |

**Host regression (16 Oct):**
- `disc025-borrowed-garden-check.html`, `discovery-the-borrowed-garden.html` and `privacy.html` are byte-identical to `84453f1`.
- `prove-g3.mjs`: 197/197.
- `prove-g6-open-register.py`: 14/14.
- `prove-g6-owner-register.py`: every case run passes, then it stops at `git show c64e63a`. `prove-tenure-invariance.mjs` likewise needs `057bb81`. Both are commits from the Mac line that are not on GitHub: pre-existing, and unrelated to this work.
- Image-rights manifest is up to date, and the image-rights gate passes.
