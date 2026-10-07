# G1B CONTRACT — DISC-025 BORROWED GARDEN MATCH PILOT

**Status:** FROZEN · 7 October 2026
**Founder approval:** given in full, with three copy corrections applied exactly as issued.
**privacy_version:** `2026-10-PHASE2-V1`
**Supersedes:** `2026-09-PHASE2-DRAFT` (never published, never used for a real submission)

This document is the governance source of truth for the Borrowed Garden match
pilot. It does not restate the data model: the certified
`disc025-register-contract.json` and `airtable-register-schema.json` remain
authoritative for fields, vocabularies and prohibitions, and nothing here
amends them.

---

## 1 · WHAT IS FROZEN

| item | state |
|---|---|
| privacy_version | `2026-10-PHASE2-V1` — APPROVED |
| Homeowner submission notice | APPROVED (corrections 1, 2, 3 applied) |
| Gardener submission notice | APPROVED (corrections 2, 3 applied) |
| Retention | 24-month maximum — APPROVED |
| R5 safety protocol | APPROVED |
| Tenure rule | APPROVED |
| Introduction consent emails (both sides) | APPROVED |
| Joint introduction email | APPROVED |
| D1 insurance | **PRE-G7 GATE** — gates introduction, not engineering, not registration |

### Deferred by founder ruling

**R4 — reconfirmation rate.** V1 creates no 12-month reconfirmation process.
R4 is therefore recorded as **DEFERRED / UNAVAILABLE**. Functionality must not
be added solely to produce the metric. The readiness criteria in the DISC-025
founder decision report stand, with R4 unmeasurable in V1 and that fact stated
rather than worked around.

---

## 2 · HOMEOWNER SUBMISSION NOTICE (garden side)

> **Before you join the register**
>
> **What we keep about you and your garden.** Your first name, your email
> address, the district you chose, and what you told the Property Check about
> your garden — its size band, water, how someone would get in, and whether you
> own the property. We also keep the administrative records needed to manage
> your registration, your consent and its status.
>
> **What we never ask for.** Your address, your Eircode, your phone number,
> your surname, your age, photographs of your garden, or anything about your
> health. We don't collect them, so we can't hold them or lose them.
>
> **Why we keep it.** So that we can tell you if someone nearby is looking for
> growing space.
>
> **Joining the register does not share your details with anyone.** No other
> person sees your record. There is no public listing, no public map, no profile
> page, and no directory. Your record is private to PlotNua.
>
> **If we think there's a possible fit, we'll email you and ask.** We'll
> describe the other person in general terms only — a district, how much space
> they're looking for, roughly when. No name, no email, no contact details.
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

**Consent control, canonical and frozen:**

> ☐ I'm over 18, and I'd like PlotNua to keep this and tell me if someone
> nearby is looking for growing space.

The UI may lay the checkbox out however it likes. What is hashed is the
sentence above, not the markup.

---

## 3 · GARDENER SUBMISSION NOTICE (grower side)

Identical to §2, with these three substitutions:

> **What we keep.** Your first name, your email address, the district you chose,
> how far you'd travel, how much space you're looking for, roughly when, and
> anything you choose to tell us in the notes box. We also keep the
> administrative records needed to manage your registration, your consent and
> its status.
>
> **Why we keep it.** So that we can tell you if someone near you has growing
> space they'd consider sharing.
>
> **What "registered" means.** "Registered grower" means only this: the person
> asked PlotNua to tell them about potential growing space, and confirmed
> control of the email address they gave.

*(`registered_means` reused verbatim from the certified contract.)*

**Consent control, canonical and frozen:**

> ☐ I'm over 18, and I'd like PlotNua to keep this and tell me about possible
> growing space nearby.

---

## 4 · R5 SAFETY PROTOCOL

This is the `PN-NONCLAIMS` region. The twelve prohibited words appear here only
as denials, which is the single place the certified contract permits.

> **What PlotNua does and does not do**
>
> **PlotNua introduces people. That is all it does.**
>
> PlotNua does not verify anybody's identity, has not met them, has not seen
> identification, has not Garda vetted them, has not checked references, has not
> assessed their experience or competence, has not assessed whether they are
> safe, does not endorse or recommend them, and has not confirmed anything they
> told us, including where they live.
>
> **We have not checked who owns the garden.** The person offering it told us
> what they told us. We have not seen a deed, a lease or a letter.
>
> **PlotNua provides no insurance of any kind** — not for injury, not for damage
> to property, not for loss of tools or crops. Neither party is covered by
> anything PlotNua holds. If either of you wants cover, that's between you and
> your own insurer.
>
> **Meeting for the first time**
>
> - Meet at the garden, in **daylight**, before anything is agreed
> - **Tell somebody else** where you're going and when you expect to be back
> - Bring somebody with you if you'd prefer. Nobody will think it odd
> - Nobody has to decide anything at the first meeting, and nobody should be
>   asked to
>
> **Children.** A garden may be a family garden. If children are in or around
> the garden, that is for the householder to manage, and the two of you should
> talk about it plainly before anything starts. PlotNua has not vetted anyone
> and nothing here is a substitute for a parent's own judgement.
>
> **Getting in.** Agree how the gardener gets to the garden before they start —
> times, which gate, whether anyone needs to be home. **If you are thinking
> about giving someone a key, think carefully.** Many arrangements work
> perfectly well with the householder present, or with access only to an outside
> gate. A key is not required for this to work.
>
> **Tools and equipment.** Agree whose tools get used and where they're kept.
> PlotNua does not supply, insure or replace anything.
>
> **If something goes wrong.** Injury, damage, or a dispute is between the two
> of you and your own insurers. PlotNua is not a party to your arrangement and
> cannot resolve it for you.
>
> **Money.** PlotNua does not handle money, does not take a fee, does not take a
> commission, and holds no payment information of any kind. Whatever you agree
> about costs — or agree that there are none — is between you, and PlotNua keeps
> no record of it.
>
> **Stopping.** Either of you can stop at any time, for any reason or none,
> without notice and without explaining. That applies before you meet, after you
> meet, and at any point afterwards. A tidy ending is a courtesy, not an
> obligation.
>
> **Telling us something is wrong.** Email **hello@plotnua.ie**. If either of
> you raises a safety concern, PlotNua will: suspend both records from any
> further introduction immediately, before investigating anything; record what
> you told us; and not propose either of you to anyone else while it is open.
> **PlotNua cannot investigate a crime, and will not pretend to. If you are in
> danger, contact An Garda Síochána on 999 or 112.**

Consistent with the Incidents table rule: *any open incident suspends matching
for both records before it is investigated.*

---

## 5 · TENURE RULE

| `inherited_tenure` | storable | may reach introduction | condition |
|---|---|---|---|
| `own` | yes | **yes** | Ordinary confirmation only. No document. PlotNua has not verified ownership and says so |
| `rent` | yes | **only with explicit permission** | `permission_confirmed` ticked **and** the homeowner states in their own words in `garden_note` that their landlord or owner knows and has agreed. No tick, or a tick with no supporting statement → not matchable |
| `buying` | yes | **no** | Stored, kept warm, never promoted. One clarifying question permitted; the answer re-routes it |
| unconfirmed / absent | yes | **no** | As `buying` |

Unconfirmed tenure is a reason not to introduce, never a reason to discard a
willing homeowner. PlotNua never asks for or stores a deed, lease, landlord name
or landlord contact detail. The homeowner's own sentence is evidence of what
they said, not of the fact.

---

## 6 · INTRODUCTION CONSENT

Two emails, sent separately, only after `human_review_by` / `human_review_at`
are stamped. Full approved text held in the G1B package.

Three rules these emails encode:

1. **No reply is never consent.** Stated to both. Logged as a declined pair
   after 7 days.
2. **A yes is scoped to that one introduction** and nothing else.
3. **Neither email reveals a name, an email address, an address, or a district
   narrower than the register holds.**

---

## 7 · JOINT INTRODUCTION EMAIL

Sent only after two independent yeses. Introduces first names, shares the two
email addresses at that point and not before, restates the non-claims paragraph
in full, carries the first-meeting guidance, states that the participants decide
and that either may stop, and gives the incident and withdrawal route.

---

## 8 · GATE STATE

| stage | state |
|---|---|
| **G2** — bounded Worker, `WRITES_ENABLED=false`, `EMAIL_ENABLED=false` | **UNBLOCKED** |
| **G5** — flip writes, Colin-controlled test records, then erasure | **UNBLOCKED** |
| **G6** — real expressions of interest and registrations | **UNBLOCKED** |
| **G7** — first real introduction | **BLOCKED** until the insurer / broker question is resolved |

**G6 constraint, founder-set:** registration material must not promise or imply
that joining the register guarantees a match or an introduction.

---

## 9 · RESOLVED — 7 October 2026

**G1B IS FULLY FROZEN. No residual items.**

The homeowner consent control in the original §2 draft read *"…tell me about
possible growing space nearby."* That is the gardener's sentence; a homeowner is
offering space, not seeking it. It was held at `null` in the Worker — refusing
every garden submission by construction, regardless of the write switch — rather
than corrected on anyone's authority but the founder's.

**Approved verbatim, 7 October 2026:**

> I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby
> is looking for growing space.

Now set as the canonical garden consent string in §2 and in the Worker. The
`if (!CONSENT_TEXT.garden) return NOT_OPEN(cors)` stop is **retained** rather
than removed: a future edit that blanks the canonical sentence must close the
route instead of recording a consent to nothing.

---

## 10 · CONSENT HASHING

`consent_text_hash` is the SHA-256 of the exact rendered consent control text.
The page sends the string it actually rendered; the Worker hashes it and
compares against its own canonical constant for `2026-10-PHASE2-V1`. A mismatch
is a rejected submission, not a silent write. A page that drifts from the
approved wording therefore stops working rather than recording a consent to
text nobody approved.
