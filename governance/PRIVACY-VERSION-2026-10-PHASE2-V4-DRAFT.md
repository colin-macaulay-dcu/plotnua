# PRIVACY NOTICE · VERSION 2026-10-PHASE2-V4 · DRAFT — NOT PUBLISHED

**Status:** DRAFT. `privacy.html` is **not changed**; the live notice remains **2026-10-PHASE2-V3**.
**Purpose:** add a dedicated Art Space Register section (DISC-024 Open Your Home to Art, part of the A Home for Art Discovery), kept separate in data, purpose and consent from the Garden Owner Register (Section 7).
**Builder:** `atlas-tools/build-privacy-v4.py`. Guard V1 refuses to build unless every sentence below appears in this file, so this draft and the builder cannot drift apart.

## Founder decisions, 13 October 2026 (22:18)

- **R1, retention:** a maximum of **12 months** for registrations, deleted sooner when no longer needed.
- **R2, deletion evidence, Option A:**
  - no email fingerprint is kept after deletion;
  - the person's record, consent proof and status-log entries are deleted together;
  - only an anonymous administrative deletion log is kept (§ Retention).
- **R3, technical data:** the clarification is adopted.
  - Hosting is verified: plotnua.ie is served by GitHub Pages; the form service runs on Cloudflare.
  - The Worker's request logging is to be switched off explicitly.
  - Airtable's 7-day trash and its automatic snapshots are disclosed.
- **R4, access:** the founder's access wording is adopted.
- **Publication gate:** the external legal-review requirement is replaced. Publication now needs a completed, dated GDPR self-assessment, documented resolution of material risks, and explicit founder approval. All technical safeguards remain. Paid advice is not required by default.

## Gate

The register cannot open until all of these hold. The opening guard (R2 in `atlas-tools/build-art-space-register.py`) refuses until:
- `privacy.html` carries exactly the Section 8 below, as rendered by the V4 builder;
- the Art Worker's `PRIVACY_VERSION` is `2026-10-PHASE2-V4`;
- `OPEN_APPROVAL` records the founder's approval, the self-assessment, the resolution of material risks and the dry run.

The V4 builder refuses to write `privacy.html` until:
- `APPROVAL` records the founder's approval, the self-assessment, the resolution of material risks and the "Last updated" label;
- `BACKUP_PERIOD` records the Airtable plan's snapshot retention.

## Changes from V3

1. **New Section 8, "The Art Space Register"** (text below), after Section 7, whose wording is unchanged.
2. **Renumbering:** Sections 8–17 become 9–18.
3. **Section 2:** one sentence: *"If you choose to join the Art Space Register, we also collect the information described in Section 8."*
4. **Third-Party Services and Links** (becomes Section 10): one sentence: *"The Art Space Register described in Section 8 also runs on a PlotNua service hosted on infrastructure provided by Cloudflare, and its records are stored in Airtable in a database kept separate from the Garden Owner Register."*
5. **How Long We Keep Information** (becomes Section 12): one line: *"Art Space Register records are kept for a maximum of 12 months, as described in Section 8."*
6. **"Last updated"** set to the publication month.
7. **No other change.**

**On publication only:** `atlas-tools/prove-g6-owner-register.py` receives three bounded co-edits (the section count, one heading anchor, and mutation anchors scoped to Section 7). The Garden Worker keeps privacy version V3. Its Worker, consent, database and registration experience are untouched.

## Retention and deletion

- **Registrations:** a maximum of 12 months, deleted sooner if the pilot ends or no longer needs them. The Airtable formula `erase_after` flags each record at 12 months. **The formula only flags: a person deletes.**
- **At deletion:** the Hosts record, its Consent proofs row and its Status log rows are all deleted together. No email, email fingerprint, name or record identifier survives.
- **Anonymous deletion log** (Airtable table `Deletion log`), one row per deletion:
  - the date it was requested or became due;
  - the date it was completed;
  - the reason: withdrawal, retention limit, pilot ended or other.

  It holds no name, email, email hash, county or record identifier, and it is kept for the life of the pilot.
- **Limitation, accepted by the founder:** an anonymous log proves that deletions are carried out. It **cannot prove** that a particular person's record was deleted. For a voluntary, unpaid pilot interest register, that is judged proportionate (see the GDPR self-assessment).
- **Provider recovery:**
  - Airtable keeps deleted records in its trash for 7 days.
  - Airtable also keeps automatic base snapshots for a period set by the plan: 2 weeks on Free, 1 year on Team, longer on higher plans.
  - PlotNua never restores deleted registration records.
  - `BACKUP_PERIOD` must hold the plan's actual figure before publication.

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
> Your record is private to PlotNua. It is not published, and there is no public listing, map, profile or directory. Records are reviewed by a person at PlotNua. Registration details are accessible only to authorised people managing the register and to service providers where necessary to operate it. They are not shared with artists or made publicly available. Your email address would only be shared with another person if you agreed to a specific arrangement, and no such arrangements are available.
>
> The form sends your details to a PlotNua service hosted on infrastructure provided by Cloudflare, which records them in the register. The register is stored in Airtable, a database service. Cloudflare and Airtable are both based in the United States, so your information may be processed outside the European Economic Area. Cloudflare states that it relies on the EU Standard Contractual Clauses, and on its certification under the EU-U.S. Data Privacy Framework, for such transfers. Airtable's Data Processing Addendum states that the EU Standard Contractual Clauses apply to personal data transferred from the European Economic Area. Visitors should refer to Cloudflare's and Airtable's own privacy policies for more about how they process personal information.
>
> The services that carry the form, such as Cloudflare, process technical information such as your IP address so that your request can be delivered securely. PlotNua does not record it in the register.
>
> We keep your record for no longer than 12 months, and we delete it sooner if the pilot ends or no longer needs it. You can ask us to delete it at any time.
>
> To leave the register or ask us to delete your record, email hello@plotnua.ie. There is nothing to cancel and no notice period. When we delete your record, we delete everything the register holds about you, including the record of your consent. A deleted record can be restored from our database provider's trash for 7 days, and it remains in that provider's automatic backups for a limited period, until those backups expire. We do not restore deleted registration records. We keep only an anonymous entry in our deletion log, recording when a deletion was requested or became due, when it was completed and why, so that we can show deletions are carried out. That entry contains nothing that identifies you.

## Consistency enforced

- **On-page notice:** the register's short notice states the same retention, access and deletion terms, and contains no fingerprint wording (guard V4).
- **Fields:** the collected fields match the Worker's allowed keys (guard V4).
- **Version:** the Worker records `privacy_version = 2026-10-PHASE2-V4`. The register cannot open until this notice is published (guard R2).

## Superseded

The earlier deletion-note proposal (email fingerprint kept for 12 months, "Option B") and its legal-basis question were withdrawn on 13 October 2026, when the founder adopted Option A.
