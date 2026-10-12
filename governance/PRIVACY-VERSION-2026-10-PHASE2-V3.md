# PRIVACY VERSION 2026-10-PHASE2-V3

**Status:** FROZEN on commit — the homeowner-facing privacy terms for the Garden Owner Register
**Date:** 12 October 2026
**Authority:** founder decision D2 option (ii), 12 October 2026
**Supersedes:** [`PRIVACY-VERSION-2026-10-PHASE2-V2.md`](PRIVACY-VERSION-2026-10-PHASE2-V2.md) (left historically accurate, not edited)
**Applied by:** `atlas-tools/build-g6-owner-register.py`

---

## 1 · Why V3 exists

V2 (8 October) disclosed that the register stored four Property Check answers and the Property Check result (`inherited_result_key`). On 12 October the founder chose **data minimisation**: transmit tenure only, because it is the input to the G1B §5 renter-permission safeguard, and stop transmitting the other answers and the result. The notice must describe what is actually sent, so the version advances.

No real homeowner record exists under V1 or V2. The five tables were returned to zero after G5 and nothing has been opened since.

## 2 · The consent sentence — UNCHANGED

> I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.

SHA-256 `85c436084349e841017171ef12e2c0d5e28fa24a82d99f4c2beaca8f6eee9b9c` — **byte-identical to V1 and V2**. No change was genuinely required: the sentence names no field, so narrowing the field set does not alter what is consented to. The standing rule from the V2 amendment holds: a privacy-version increment never, by itself, changes the consent sentence.

## 3 · The one notice paragraph that changed

**V2**

> **What we keep about you and your garden.** Your first name, your email address, the district you chose, and what you told the Property Check about your garden — its size band, water, how someone would get in, and whether you own the property — and the result the Property Check produced from those answers. We also keep the administrative records needed to manage your registration, your consent and its status.

**V3**

> **What we keep about you and your garden.** Your first name, your email address, the district you chose, and what you tell us here about the space — roughly how big it is, whether there is water, roughly when, and anything you add in the note. From your Property Check we keep one answer only: whether you own the home, rent it or are buying it, because if you rent, the owner would have to agree before anything could happen. Your other Property Check answers and its result are not sent to us. We also keep the administrative records needed to manage your registration, your consent and its status.

V2 was also inaccurate in a smaller way that V3 corrects: size band and water are asked **on the register form**, not by the Property Check.

The other nine notice paragraphs are byte-identical.

## 4 · What the page now sends

| key | V2 | V3 |
|---|---|---|
| `first_name` `email` `district` `water` `size_note` `timing` `over_18` `consent_text` `source` | sent | sent |
| `garden_note` | when entered | when entered |
| `permission_confirmed` | `rent` only | `rent` only |
| `inherited_tenure` | sent | **sent — on every submission** |
| `inherited_spare_corner` | sent | **not sent** |
| `inherited_way_in` | sent | **not sent** |
| `inherited_your_own_use` | sent | **not sent** |
| `inherited_result_key` | sent | **not sent** |

**Why tenure goes on every submission, not only for renters.** The deployed Worker refuses a garden submission with no `inherited_tenure` (`REFUSED field: inherited_tenure`), and an owner's `own` is precisely what tells it that no permission is required. Sending it only for renters would require a Worker change, which Route A excludes. This is the narrowest reading of "only where required for the existing renter-permission safeguard" that the existing architecture supports.

## 5 · The Worker — UNCHANGED, with one consequence recorded

`worker/garden-register/src/index.js` sha256 `66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79`, identical to the G5-certified source.

`wrangler.toml` changes one line: `PRIVACY_VERSION = "2026-10-PHASE2-V3"`. It takes effect **only when the Worker is next deployed**. `WRITES_ENABLED` and `EMAIL_ENABLED` remain `"false"`.

**Recorded, not fixed (founder decision required):** the Worker still *accepts* the four dropped keys as optional fields. The minimisation is enforced by the page. A hand-crafted request that bypassed the page could still store them. Closing that would be a Worker change (ignore those keys), followed by a fresh controlled-write proof.

## 6 · Published privacy policy

`privacy.html` gains Section 7, "The Garden Owner Register", plus Airtable in the third-party list, Cloudflare hosting of the register, and a retention line. Sections 7–16 become 8–17. Last updated: October 2026.

**Before publishing that page:** Airtable's Data Processing Addendum is **not binding until executed** ("This DPA will not become binding and enforceable unless and until it has been validly executed by the Parties", airtable.com/dpa). Section 7 describes what that DPA says about transfers. It should not go live until PlotNua has executed it (airtable.com/dpaform). Cloudflare's DPA, by contrast, is incorporated by reference for self-serve customers with no action required (cloudflare.com/trust-hub/gdpr).

## 7 · Version identity

| | |
|---|---|
| privacy_version | `2026-10-PHASE2-V3` |
| consent sentence SHA-256 | `85c43608…6eee9b9c` (unchanged) |
| journey page | `1083f0563c0f2094…` |
| privacy.html | `49e347398345a42f…` |
| wrangler.toml | `c5411f23b9f4dcf4…` |
| Worker source | `66ee90e2d94968ee…` (unchanged) |
