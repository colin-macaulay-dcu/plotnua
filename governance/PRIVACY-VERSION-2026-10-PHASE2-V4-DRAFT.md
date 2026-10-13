# PRIVACY NOTICE · VERSION 2026-10-PHASE2-V4 · DRAFT — NOT PUBLISHED

**Status:** DRAFT for founder approval and legal review. `privacy.html` is **not changed**. The live notice remains **2026-10-PHASE2-V3**.
**Purpose:** add a dedicated Art Space Register section (DISC-024 Open Your Home to Art), kept separate in data, purpose and consent from the Garden Owner Register (Section 7).
**Prepared:** 13 October 2026, with the Art Space Register build (`governance/ART-SPACE-REGISTER-BUILD-2026-10-13.md`).

## Gate

The register builder (`atlas-tools/build-art-space-register.py`, guard R2) **refuses to open the register** unless `privacy.html` carries a section with `id="art-space-register"`. This draft must be approved, legally reviewed and published before that can happen.

## Changes from V3

1. **New Section 8, "The Art Space Register"** (text below). It goes after Section 7, "The Garden Owner Register", whose wording is unchanged.
2. **Renumbering.** Current Sections 8–17 become 9–18 (Cookies → 9 … Contact → 18).
3. **"How Long We Keep Information"** (currently 11, becomes 12) gains one line: *"Art Space Register records are kept for a maximum of 24 months, as described in Section 8."*
4. **"Last updated"** changes to the publication date.
5. **No other change.** Legal basis, rights, complaints and processors are unchanged.

## Retention

The 24-month maximum is carried as a **policy that must be reviewed before opening** (founder instruction, 13 Oct 2026). If the review changes it, change this draft, the on-page notice (`NOTICE` in the builder) and the weekly-review procedure together.

## Proposed Section 8 — exact text

> ### 8. The Art Space Register
>
> The Open Your Home to Art Property Check is private: answering its questions does not send PlotNua your details. After seeing your result, you can choose to join the Art Space Register. It is a list, kept privately by PlotNua, of homeowners in Ireland who might be willing to offer space for artists' finished work — storing it, displaying it, opening a space to visitors by arrangement, or helping it find a buyer. Joining is voluntary. PlotNua is not introducing homeowners to artists, there is no matching or booking service, no payment is offered, and joining the register does not arrange anything.
>
> This register is separate from the Garden Owner Register described in Section 7. It is kept in a separate database, and your details are not shared between the two.
>
> **What we collect when you join:**
>
> - your first name;
> - your email address;
> - your county;
> - which of storing, displaying, opening to visitors or helping to sell you would consider;
> - if you choose to tell us: the kind of space, whether money is part of it for you, and anything you add in the note; and
> - a record that you gave your consent, which version of this notice applied, and when you joined.
>
> We do not collect your address, your Eircode, your town, your phone number, your surname, your age, photographs of your home, or anything about the value of what is in it. The form starts with three of your Property Check answers filled in, and only what is in the form when you submit it is sent. Your other Property Check answers and your Property Check result are not sent to the register.
>
> **Why we use it.** We use this information to contact you about the Open Your Home to Art pilot — for example, to ask a few questions about what you would consider, or to let you know if the pilot develops. We rely on your consent, which you give by ticking the box when you join. You can withdraw it at any time.
>
> **Your record is private to PlotNua.** It is not published, and there is no public listing, map, profile or directory. Records are reviewed by a person at PlotNua. No artist or other person sees your record. Your email address would only be shared with another person if you agreed to a specific arrangement, and no such arrangements are available.
>
> **Where it is processed.** The form sends your details to a PlotNua service hosted on infrastructure provided by Cloudflare, which records them in the register. The register is stored in Airtable, a database service. Cloudflare and Airtable are both based in the United States, so your information may be processed outside the European Economic Area. Cloudflare states that it relies on the EU Standard Contractual Clauses, and on its certification under the EU-U.S. Data Privacy Framework, for such transfers. Airtable's Data Processing Addendum states that the EU Standard Contractual Clauses apply to personal data transferred from the European Economic Area. Visitors should refer to Cloudflare's and Airtable's own privacy policies for more about how they process personal information.
>
> **How long we keep it.** We keep your record for a maximum of 24 months. You can ask us to delete it at any time, and we may delete it sooner if it is no longer needed.
>
> **Leaving.** To leave the register or ask us to delete your record, email hello@plotnua.ie. There is nothing to cancel and no notice period. When we delete your record we keep a separate note that you gave permission and that we honoured your request. That note holds a one-way digital fingerprint made from your email address, not the address itself, so that we can show we did what you asked.

## HTML placement (when approved)

`<section … id="art-space-register">`, using the same markup pattern as Section 7, immediately after Section 7's closing tag. Build it with a bounded builder that changes only Sections 8–18 headings, the new section, the retention line and the date. Prove the result against the text above.

## Consistency already enforced

- The on-page notice in the register (builder `NOTICE`) states the same fields, purpose, retention and deletion-fingerprint terms.
- The Worker records `privacy_version = 2026-10-PHASE2-V4` (`worker/art-space-register/wrangler.toml`), so no record can be written until this notice is the published one. That is an activation-sequence check, and writes are off.

## Open point for the founder

When V4 is published, the **Garden Owner Register Worker still records `2026-10-PHASE2-V3`**. Section 7's text is unchanged, so V3 remains an accurate description of what a garden registrant agreed to. Decide whether to leave it at V3 or move it to V4 in the same release. Either way, it's a separate, approved change to `worker/garden-register/wrangler.toml`, which this work did not touch.
