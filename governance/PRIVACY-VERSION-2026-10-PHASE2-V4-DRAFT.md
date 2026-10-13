# PRIVACY NOTICE · VERSION 2026-10-PHASE2-V4 · DRAFT — NOT PUBLISHED

**Status:** DRAFT for founder approval and legal review. `privacy.html` is **not changed**. The live notice remains **2026-10-PHASE2-V3**.
**Purpose:** add a dedicated Art Space Register section (DISC-024 Open Your Home to Art, now part of the A Home for Art Discovery), kept separate in data, purpose and consent from the Garden Owner Register (Section 7).
**Prepared:** 13 October 2026, with the Art Space Register build (`governance/ART-SPACE-REGISTER-BUILD-2026-10-13.md`).
**Revised:** 13 October 2026, activation preparation. Changes in this revision:
- deletion-note retention of 12 months added (provisional);
- third-party sentence added;
- "artists' finished work" list punctuated with a colon, not a dash;
- the Garden Worker stays on V3.

**Builder:** `atlas-tools/build-privacy-v4.py`. Guard V1 refuses to build unless every sentence below appears in this file, so this draft and the builder cannot drift apart.

## Gate

The register cannot open until three things hold. The opening guard (R2 in `atlas-tools/build-art-space-register.py`) refuses until:
- `privacy.html` carries exactly the Section 8 below, as rendered by the V4 builder;
- the Art Worker's `PRIVACY_VERSION` is `2026-10-PHASE2-V4`;
- `OPEN_APPROVAL` records the founder's approval, the legal review and the dry run.

The V4 builder itself refuses to write `privacy.html` until its `APPROVAL` records the founder's approval, the legal review and the "Last updated" label.

## Changes from V3

1. **New Section 8, "The Art Space Register"** (text below). It goes after Section 7, "The Garden Owner Register", whose wording is unchanged.
2. **Renumbering.** Current Sections 8–17 become 9–18 (Cookies → 9 … Contact → 18).
3. **"Third-Party Services and Links"** (currently 9, becomes 10) gains one sentence after the Garden Owner Register sentence:
   *"The Art Space Register described in Section 8 also runs on a PlotNua service hosted on infrastructure provided by Cloudflare, and its records are stored in Airtable in a database kept separate from the Garden Owner Register."*
4. **"How Long We Keep Information"** (currently 11, becomes 12) gains one line:
   *"Art Space Register records are kept for a maximum of 24 months, as described in Section 8."*
5. **"Last updated"** changes to the publication month.
6. **No other change.** Legal basis, rights, complaints and processors are unchanged.

**On publication only, two Garden proof expectations follow the renumbering.** `atlas-tools/prove-g6-owner-register.py` currently expects sections 1–17 and uses a "9. Third-Party" heading as a mutation anchor. The builder updates those two lines in the same act. The Garden Worker, its consent, its database and its registration experience are not touched. The Garden Worker keeps privacy version **2026-10-PHASE2-V3** (founder decision, 13 Oct 2026), because Section 7's text does not change.

## Retention (provisional until privacy and legal review)

- **Homeowner registrations:** a maximum of **24 months**.
- **Minimal deletion records** (consent proofs: an email fingerprint, the notice version, the consent-text fingerprint and the dates): **12 months after the deletion is completed**, then deleted.
  - This applies whether the deletion followed a withdrawal or the 24-month limit. The founder's instruction named withdrawals; extending it to 24-month erasures is flagged for confirmation.

If the review changes either figure, change all four of these together:
- this draft;
- the builder's `SECTION8`;
- the register's on-page notice (`NOTICE` in `build-art-space-register.py`);
- the Airtable formula fields in `worker/art-space-register/airtable-schema.json`.

Guard V4 keeps the first three consistent.

## Proposed Section 8 — exact text

> ### 8. The Art Space Register
>
> The Open Your Home to Art Property Check is private: answering its questions does not send PlotNua your details. After seeing your result, you can choose to join the Art Space Register. It is a list, kept privately by PlotNua, of homeowners in Ireland who might be willing to offer space for artists' finished work: storing it, displaying it, opening a space to visitors by arrangement, or helping it find a buyer. Joining is voluntary. PlotNua is not introducing homeowners to artists, there is no matching or booking service, no payment is offered, and joining the register does not arrange anything.
>
> This register is separate from the Garden Owner Register described in Section 7. It is kept in a separate database, and your details are not shared between the two.
>
> What we collect when you join:
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
> We use this information to contact you about the Open Your Home to Art pilot, for example to ask a few questions about what you would consider, or to let you know if the pilot develops. We rely on your consent, which you give by ticking the box when you join. You can withdraw it at any time.
>
> Your record is private to PlotNua. It is not published, and there is no public listing, map, profile or directory. Records are reviewed by a person at PlotNua. No artist or other person sees your record. Your email address would only be shared with another person if you agreed to a specific arrangement, and no such arrangements are available.
>
> The form sends your details to a PlotNua service hosted on infrastructure provided by Cloudflare, which records them in the register. The register is stored in Airtable, a database service. Cloudflare and Airtable are both based in the United States, so your information may be processed outside the European Economic Area. Cloudflare states that it relies on the EU Standard Contractual Clauses, and on its certification under the EU-U.S. Data Privacy Framework, for such transfers. Airtable's Data Processing Addendum states that the EU Standard Contractual Clauses apply to personal data transferred from the European Economic Area. Visitors should refer to Cloudflare's and Airtable's own privacy policies for more about how they process personal information.
>
> We keep your record for a maximum of 24 months. You can ask us to delete it at any time, and we may delete it sooner if it is no longer needed.
>
> To leave the register or ask us to delete your record, email hello@plotnua.ie. There is nothing to cancel and no notice period. When we delete your record we keep a separate note that you gave permission and that we honoured your request. That note holds a one-way digital fingerprint made from your email address, not the address itself, so that we can show we did what you asked. We keep that note for 12 months after the deletion is completed, and then delete it.

## For legal review

1. **Consent as the legal basis**, with an over-18 self-declaration in the consent sentence.
2. **The email fingerprint is pseudonymised personal data, not anonymous data.** Anyone who already knows an address can recompute it. Check whether the 12-month retention and the wording "one-way digital fingerprint … not the address itself" are adequate.
3. **The Cloudflare and Airtable transfer statements**, which are the same wording as Section 7.
4. **Whether a record of processing entry is needed** for the register.

## Consistency already enforced

- **On-page notice:** the register's own notice states the same fields, purpose, retention and deletion-note terms (guard V4).
- **Fields:** the collected fields match the Worker's allowed keys (guard V4).
- **Version:** the Worker records `privacy_version = 2026-10-PHASE2-V4` (`worker/art-space-register/wrangler.toml`), and the register cannot open until this notice is published (guard R2).
