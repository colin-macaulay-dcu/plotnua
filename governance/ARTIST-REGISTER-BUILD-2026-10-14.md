# PLOTART · ARTIST REGISTER · BUILD NOTE (14 October 2026)

**Founder approval:** build approved on 14 October 2026 ("PlotNua × PlotArt · Artist Register · founder build approval").

**State: BUILT AND CLOSED.**
- Artist writes are off: `ARTIST_WRITES_ENABLED = "false"`.
- The page is `noindex`. Its form is removed from the DOM unless the URL carries `?register=preview`.
- Nothing links to the page. The sitemap and Search do not list it.
- Privacy Notice V5 is a draft and is not published.

**What it is not:** an expression-of-interest register only. There is no matching, no public artist profile, no booking, no commission, no payment and no guaranteed introduction.

## 1 · Architecture (reuses the Art Space Register)

| Element | Artist Register | Homeowner register (unchanged) |
|---|---|---|
| Page | `artist-register.html`, built by `atlas-tools/build-artist-register.py` from the site shell | `disc024-open-your-home-to-art.html` |
| Worker | Same `plotnua-art-space-register` Worker, route `/v1/art-space-register/artist` | Route `/v1/art-space-register/host` |
| Switch | `ARTIST_WRITES_ENABLED` (shipped `"false"`) | `WRITES_ENABLED` (open since 14 Oct) |
| Privacy version | `ARTIST_PRIVACY_VERSION = "2026-10-PHASE2-V5"` | `PRIVACY_VERSION = "2026-10-PHASE2-V4"` |
| Allow-list and consent | `ARTIST_ALLOWED_KEYS`, `ARTIST_CONSENT_TEXT` | `ALLOWED_KEYS`, `CONSENT_TEXT` |
| Duplicate check and daily cap | `Artists` table only, 25 a day | `Hosts` table only, 25 a day |
| Base | "PlotNua Art Space Register" (`appS4gWOxuZqJyWvU`), new `Artists` table | `Hosts` |
| Consent proofs, status log | Shared tables, rows marked `register = artist` | Rows unchanged (`register` left blank) |
| Deletion | The same human procedure | The same |

Both routes share the protections the Worker already had: the origin allow-list, the fetch-metadata check, the 4 KB body limit, the per-isolate burst limit, `typecast:false` on every write, the one-status ceiling (`interest_submitted`), no logging, no mail adapter and no read surface. The token and base stay as Cloudflare secrets and never reach the browser.

Artist registrations are **never** written to the "PlotArt — Artist Evidence (E1)" research base.

## 2 · Exact Airtable changes (founder, in the Airtable UI; about 15 minutes)

All changes are in base **"PlotNua Art Space Register"**. The Worker token has no schema scope, by design, so the founder makes them. The definitive spec is `worker/art-space-register/airtable-schema.json`.

The Worker uses `typecast:false`, so option names must match exactly: lower case, with underscores.

### A. Create the `Artists` table

Create a new table named **`Artists`**, with these fields:

| Field | Type | Options / notes |
|---|---|---|
| `artist_name` | Single line text (**primary field**) | |
| `email` | Email | |
| `email_key` | Single line text | |
| `based_in` | Single select | antrim, armagh, carlow, cavan, clare, cork, derry, donegal, down, dublin, fermanagh, galway, kerry, kildare, kilkenny, laois, leitrim, limerick, longford, louth, mayo, meath, monaghan, offaly, roscommon, sligo, tipperary, tyrone, waterford, westmeath, wexford, wicklow, outside_ireland |
| `reach` | Single select | local_area, particular_places, anywhere_ireland |
| `reach_places` | Single line text | |
| `disciplines` | Multiple select | painting, drawing_print, photography, sculpture, ceramics_craft, textiles, installation_mixed, digital_video, other |
| `interests` | Multiple select | display, show_visitors, installation, store, reach_buyers |
| `needs` | Multiple select | wall, floor_room, outdoor, dry_storage, not_sure |
| `portfolio` | URL | |
| `statement` | Long text | Plain text, not rich text |
| `over_18` | Checkbox | |
| `status` | Single select | interest_submitted (the **only** option) |
| `submitted_at` | Date | Include time, 24-hour, ISO, the same time zone as the other tables |
| `privacy_version` | Single line text | |
| `consent_text_hash` | Single line text | |
| `human_review_by` | Single line text | Reserved; leave blank |
| `human_review_at` | Date with time | Reserved; leave blank |
| `erase_after` | Formula | `DATEADD({submitted_at}, 12, 'months')`, ISO date format |

Then create three views:
- **New this week:** submitted_at is within the past week, newest first.
- **Statements to screen:** statement is not empty.
- **Erasure due:** erase_after is on or before today.

### B. Add a `register` field to three existing tables

- **`Status log`:** add `register`, Single select, options `host`, `artist`.
- **`Consent proofs`:** add `register`, Single select, options `host`, `artist`.
- **`Deletion log`:** add `register`, Single select, options `host`, `artist`. A person fills this in.

The homeowner route does not write `register`, so homeowner rows stay blank, and a blank value means homeowner. Existing rows need no change.

### C. Keep everything else as it is

- No forms, interfaces, automations, share links or syncs.
- The founder remains the only collaborator.
- The token is the same one; it is already scoped to this base.

## 3 · Cloudflare deployment requirements

1. Nothing new is needed in Cloudflare: no new secrets, bindings or Worker. `AIRTABLE_TOKEN` and `AIRTABLE_BASE` are already set as secrets.
2. Deploying this code with the committed `wrangler.toml` keeps the artist route **closed** and the homeowner route **open, exactly as now**:
   ```
   cd worker/art-space-register && npx wrangler deploy
   ```
3. **Order:** deploy only after the founder pushes the commit. Deploying before the Airtable changes is safe, because the artist route writes nothing while closed.
4. **Opening, later:** set `ARTIST_WRITES_ENABLED = "true"` in `wrangler.toml` (guard A2 refuses this while the page is closed), then run `npx wrangler deploy`.
5. **Closing fast:** set it back to `"false"` and deploy again. Revoking the token is the hard stop for both registers.

## 4 · Controlled test procedure (founder, before opening)

The founder runs this with their own details only. It mirrors the homeowner test of 14 Oct.

1. **Prerequisites:**
   - the Airtable changes in §2 are made;
   - Privacy V5 is approved and published;
   - the Worker is deployed with `ARTIST_WRITES_ENABLED = "true"` for the test window only. Guard A2 requires the open approval, so for a pre-opening test the switch is flipped by a deploy with `--var ARTIST_WRITES_ENABLED:true`, which lasts only for that deploy.
2. Open `https://plotnua.ie/artist-register.html?register=preview`.
3. **Field checks:**
   - Submit empty: each required field is named in turn, and nothing is sent.
   - Enter an `http://` portfolio link: it is refused locally.
4. **Valid registration:** submit with `based_in = outside_ireland`, `reach = particular_places`, two disciplines, two interests, one need, a portfolio link and a statement. Expect **"You're on the register"**.
5. **Airtable checks:**
   - **Artists:** one row, with every field as entered; `status` is interest_submitted, `privacy_version` is 2026-10-PHASE2-V5, and `erase_after` is 12 months on.
   - **Consent proofs:** one new row with `register = artist`, a 64-character hash and no `@`.
   - **Status log:** one new row with `register = artist`, `record_ref` equal to the Artists record id, and `at` identical to `submitted_at`.
   - **Hosts:** unchanged.
6. **Duplicate:** submit again with the same email. The reply is "received" again, and no new rows appear.
7. **Homeowner check:** run a homeowner registration on the Open Your Home to Art check with a second address of the founder's. It writes to Hosts only, with no `register` value, then delete it as usual.
8. **Deletion:**
   1. delete the Artists row, then its Consent proofs and Status log rows (matched by the shared timestamp and `register = artist`);
   2. add one anonymous Deletion log row: reason withdrawal, `register = artist`.
   Confirm nothing about the test artist remains.
9. Redeploy with the committed `wrangler.toml` (artist closed), unless opening is approved the same day.
10. Record the test date in `ARTIST_OPEN_APPROVAL["controlled_test"]`.

## 5 · Launch checklist (each item needs the founder's explicit approval)

1. [x] (14 Oct 2026, 19:45) Privacy V5 wording and the self-assessment addendum approved and dated (`governance/PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md`).
2. [x] (14 Oct 2026, applied locally; live on the founder's push) `build-privacy-v5.py` written and run; `privacy.html` carries every governed line and the `PLOTNUA-ARTIST-PRIVACY-V5` marker; the founder pushes.
3. [x] (14 Oct 2026) Airtable `Artists` table and `register` fields created and verified against the schema file.
4. [x] (14 Oct 2026) Worker deployed (artist route closed). Current closed version: `33f42f08-0729-4cc3-b666-a69703ef4274`.
5. [x] (14 Oct 2026) Controlled test (§4) passed, and its date recorded (§8).
6. [ ] `ARTIST_OPEN_APPROVAL` completed (four of five recorded 14 Oct 2026; the founder's approval to open is still to come) in `build-artist-register.py`: founder approval, V5 approval, self-assessment, Airtable created, controlled test.
7. [ ] `ARTIST_PUBLIC = True`, rebuilt. This makes the page indexable, removes the preview label and shows the form.
8. [ ] `ARTIST_WRITES_ENABLED = "true"` in `wrangler.toml`; the founder deploys.
9. [ ] A Home for Art: apply the prepared `FUTURE_LINK` after `FUTURE_ANCHOR` (via `build-a-home-for-art-merge.py`), and add the page to `sitemap.xml`. Guard A10 refuses both while the register is closed.
10. [ ] The founder pushes.
11. [ ] Weekly review covers the `Artists` table and the "Statements to screen" view.
12. [x] Review trigger set by the founder (14 Oct 2026, 19:25): 10 genuine artist registrations or 8 weeks after public opening, whichever comes first. It triggers a review only.

## 6 · Guards and tests

- **`atlas-tools/build-artist-register.py`:** guards A1–A13 (see its docstring).
- **`worker/art-space-register/test/prove-artist-worker.mjs`:** 106 checks.
  - Routes and switches: closed by default; the switches are independent; origin, method and body checks; the separate allow-list.
  - Validation: required fields; invalid email, portfolio and vocabulary values; consent.
  - Writes: exactly what a write sends; consent proof and status-log marking; one shared timestamp.
  - Abuse and errors: duplicates without leaking whether someone is registered; the separate cap; Airtable failures; the burst limit.
  - The homeowner route is unchanged; the schema matches the Worker.
- **Unchanged and passing:**
  - `prove-art-worker.mjs`: 70 checks;
  - `prove-art-space-register.py`: 57 out of 57 breaks caught;
  - `build-art-space-register.py --check`: R1–R14.

## 6a · Founder decisions, 14 Oct 2026 (19:25)

The closed build at `9725254` was accepted. Registrations stay closed.

1. Privacy Section 8 is renamed "The Art Space Register and the Artist Register".
2. Review trigger: as in checklist item 12.
3. Homeowner site-specific installations: a future improvement only (see §7).
4. The artist consent wording is the founder's. It was applied in ONE commit to:
   - the Worker (`ARTIST_CONSENT_TEXT`);
   - the page builder (`CONSENT`) and the rebuilt page;
   - the Worker tests (C4 pins it exactly; C5 checks the V5 draft carries it);
   - the V5 draft.

   Guard A7 previously refused any page containing the word "guarantee". It now removes the pinned consent sentence before scanning, exactly as it already did for the disclaimer, so "does not guarantee" is allowed there and nowhere else.

## 7 · Recorded for later (not part of this build)

- **Homeowner site-specific installations:** artists can now say they are interested in creating a site-specific installation. The homeowner form has no matching option. Adding one to the homeowner register means a new `ways` value in the Worker, page and schema. It is a separate founder decision and build.
- **Homeowner form, message clearing:** in testing, the artist form showed that clearing a validation message on `change` can shift the Submit button out from under a click that has already started. The artist form keeps the message until the next submit. The homeowner form has the same pattern and was not changed here (the brief excluded it).

## 8 · Controlled live test: PASSED (14 October 2026)

The founder ran the test with their own details, using the `--var ARTIST_WRITES_ENABLED:true` deploy. That method was checked in advance by a dry run, which showed all six settings kept and only the artist switch changed.

| Check | Result |
|---|---|
| Valid artist registration | PASS |
| Airtable Artists record | PASS |
| Privacy V5 consent proof (`register = artist`) | PASS |
| Status log (`register = artist`) | PASS |
| Duplicate prevention | PASS |
| Homeowner isolation | PASS |
| Test-record deletion | PASS |
| Deletion log entry | PASS |

**Closing:** the artist route was closed again by a plain deploy from the committed `wrangler.toml`. The closed Worker version is `33f42f08-0729-4cc3-b666-a69703ef4274`. Homeowner registrations stayed open throughout.

**Final Airtable state:** verified read-only by Claude, 14 Oct 2026, about 20:25.
- Artists, Hosts, Consent proofs and Status log: 0 rows each.
- Deletion log: 2 rows, both anonymous. One is the homeowner test of 14 Oct, which predates the register field. The other is this test, with `register = artist`, reason "other" and dates of 14 Oct 2026.

## 9 · Remaining before public opening, and the smallest safe opening plan

### Still required

1. **The founder's dated approval to open.** This goes into `ARTIST_OPEN_APPROVAL["founder_approval"]`. Guard A2 refuses opening without it.
2. **Privacy Section 8 wording.** The live V5 text says "When registrations open, artists will be able to join through PlotArt's Artist Register page." That stops being accurate the moment the register opens.
   - Recommended replacement, true both before and after opening: "Artists can join through PlotArt's Artist Register page while registrations are open."
   - It is a one-sentence, editorial-only amendment: no change to data, purposes, retention or rights.
   - Proposed handling: a V5 amendment through the V5 builder, keeping version `2026-10-PHASE2-V5`.
   - This needs the founder's approval of the wording, and of keeping the version label.
3. **Two Airtable views before real registrations arrive:** "Statements to screen" (statement is not empty) and "Erasure due" (erase_after on or before today). They are part of the weekly review and retention procedure. "New this week" is optional.
4. **The weekly review** extends to the Artists table. The review trigger is 10 genuine artist registrations or 8 weeks after opening, whichever comes first.

### Smallest safe opening plan (one commit, one push, one deploy)

1. The founder approves opening and the Section 8 amendment, with a date.
2. Claude prepares, in one local commit:
   - the opening approval recorded and `ARTIST_PUBLIC = True`, with the page rebuilt (indexable, no preview label, form visible);
   - `ARTIST_WRITES_ENABLED = "true"` in `wrangler.toml` (guard A2 allows it only when everything above is in place);
   - the Section 8 amendment applied;
   - the prepared A Home for Art link applied, and the page added to `sitemap.xml`;
   - all checks run: privacy V4 and V5, both registers, both Worker proofs and a browser check.
3. The founder pushes, then confirms that `artist-register.html` shows the form and that the privacy notice carries the amended sentence.
4. The founder deploys the Worker immediately, with a plain `npx wrangler deploy`. The bindings must show `ARTIST_WRITES_ENABLED ("true")` and `WRITES_ENABLED ("true")`.
   - Between the push and the deploy, the page answers "isn't open yet". Nobody can register early.
5. No test submission is made against the open register. The controlled test already covered that path.

**Fast close (no commit):**
```
npx wrangler deploy --var ARTIST_WRITES_ENABLED:false
```
Then follow up with a committed close.

**Variant: soft opening.** Steps 2–4 can be done without the A Home for Art link and sitemap entry, so the page is reachable only from a shared link. The link is added in a later commit. It is safer, but nobody finds the page unprompted.


## 10 · Founder approval to open, and the opening commit (14 October 2026, 20:33)

**Approval.** Colin MacAulay, founder, 14 October 2026 (20:33): "I approve proceeding with the public opening of the PlotArt Artist Register and its integration into A Home for Art, subject to the final checks below." Recorded in `ARTIST_OPEN_APPROVAL["founder_approval"]`; the opening approval is now 5 of 5. Publication (push and Worker deploy) awaits the founder's separate confirmation.

### What the opening commit does

- **A Home for Art, "Take part".** One section in the PlotArt part of the page ("Where This Could Go"), directly after "This matching service is not live yet.", using the page's existing pathway cards (`.hfa-path`):
  - "I have a space for art" → `disc024-open-your-home-to-art.html?start=1` (the existing check; its result offers the existing Art Space Register);
  - "I'm an artist looking for space" → `artist-register.html`;
  - the shared line: "Both are expressions of interest only: free, private and non-binding. Nothing is matched or arranged, and PlotNua has not verified any space or artist."
  - Rendered by `build-a-home-for-art-merge.py` (every word declared for guard M1) only while `ARTIST_PUBLIC` is True; checked by guard A11. Two cards side by side on desktop, stacked on mobile.
- **Artist Register page open.** `ARTIST_PUBLIC = True`: indexable, no preview label, form visible.
- **Privacy Section 8.** "When registrations open, artists will be able to join through PlotArt's Artist Register page." → "Artists can join through PlotArt's Artist Register page while registrations are open." Applied with `build-privacy-v5.py --amend-s8`. Version stays `2026-10-PHASE2-V5`; Last updated label unchanged; nothing else in the notice changes (W1–W7 pass).
- **Sitemap.** `artist-register.html` added once, after A Home for Art (written by the artist builder; guard A10).
- **Worker configuration.** `ARTIST_WRITES_ENABLED = "true"` in `wrangler.toml`. Takes effect only on deploy.
- **Unchanged:** the homeowner check, its register form, the `/host` route and the Hosts table (guards R1–R14 and A12).

### Operations from opening day

**Weekly review (both registers).** Once a week, the founder opens both tables:
1. **Hosts** and **Artists**: read every new row. Screen free text (`host_note`; `statement` and `portfolio`) for third-party personal data, addresses, Eircodes or phone numbers, and remove or ask about anything that should not be held. Fill `human_review_by` and `human_review_at`.
2. **Spam:** delete obvious junk (then its Consent proofs and Status log rows, as below). The Worker caps each register at 25 registrations a day.
3. **Withdrawals:** act on every request to hello@plotnua.ie (below).
4. **Review trigger:** count genuine registrations in each table. The review is due at **10 genuine registrations or 8 weeks after opening, whichever comes first** (each register separately).

**Withdrawal and deletion (on request to hello@plotnua.ie, or for spam).**
1. Find the person's row in Hosts or Artists.
2. Delete that row, then its Consent proofs and Status log rows (matched by the shared timestamp; for artists also `register = artist`).
3. Add one anonymous Deletion log row: the reason (withdrawal, or other) and `register` (host or artist). No name or email.
4. Reply to confirm. Nothing about the person remains (Airtable's trash keeps a deleted row for 7 days, as the notice says).

**Retention.** Each row's `erase_after` is 12 months after `submitted_at`. The first can fall due in October 2027.

### Airtable views

The Airtable connector available to Claude can list views but cannot create them (checked 14 Oct 2026: Artists and Hosts each have only "Grid view"). **Manual setup, about two minutes:**

*"Statements to screen" (create before or on opening day):*
1. Open the base "PlotNua Art Space Register" → table **Artists**.
2. Views sidebar → **Create… → Grid** → name it `Statements to screen`.
3. **Filter → Add condition:** `statement` *is not empty*. Then **Add condition → Or**: `portfolio` *is not empty*.
4. **Add condition** group (And): `human_review_at` *is empty*. (A row leaves the view once it has been reviewed.)
5. **Sort:** `submitted_at`, oldest first.
6. Repeat in **Hosts** with the same name: filter `host_note` *is not empty* AND `human_review_at` *is empty*; sort by `submitted_at`.

*"Erasure due" (not needed until October 2027; does not delay opening):* in each table, a Grid view filtered `erase_after` *is on or before* *today*, sorted by `erase_after`.

### Publication sequence (founder, after confirming)

Order chosen so the public artist form is **never visible while the route is closed**: the Worker opens first, the page second.
1. Apply the patch on the Mac (the usual `git am` step) and check the tree hash.
2. **Deploy the Worker first**, from the committed configuration:
   `cd worker/art-space-register && npx wrangler@4.151.0 deploy`
   Check that the bindings show `ARTIST_WRITES_ENABLED ("true")`, `WRITES_ENABLED ("true")` and both privacy versions `2026-10-PHASE2-V5`.
   - Until the push, the live artist page is still closed (form removed), so nobody can reach the open route from the site.
3. **Push immediately:** `git push origin HEAD:main`.
4. When GitHub Pages has rebuilt (one to two minutes), check on plotnua.ie: the two cards on A Home for Art (desktop and phone); the artist form visible on `artist-register.html` with no preview label; the amended Section 8 sentence on `privacy.html`; `sitemap.xml` lists the artist page.
5. No live test submission.

### Rollback

- **Fast close (seconds, no commit):** `npx wrangler@4.151.0 deploy --var ARTIST_WRITES_ENABLED:false`. The page stays up; the route refuses new artist registrations. The homeowner route is unaffected.
- **Full rollback:** fast close first, then `git revert --no-edit <opening commit>` and push. The revert restores the closed page, removes the Take part section and the sitemap entry, restores the previous Section 8 sentence and sets the committed switch back to "false". Then a plain `npx wrangler@4.151.0 deploy` so the Worker matches the committed configuration.
- **Worker only, to the closed version:** `npx wrangler@4.151.0 rollback 33f42f08-0729-4cc3-b666-a69703ef4274 --message "close artist route"`.
- Registrations already received stay in Airtable under V5 consent; the rollback does not delete them.
