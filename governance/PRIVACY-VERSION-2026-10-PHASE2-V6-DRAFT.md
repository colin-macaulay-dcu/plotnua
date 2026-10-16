# PRIVACY NOTICE · VERSION 2026-10-PHASE2-V6 · DRAFT FOR FOUNDER APPROVAL

**Status:** DRAFT. Not approved and not published. `privacy.html` is unchanged and still carries V5.
**Why:** the Grower Register (`borrowed-garden-grower-register.html`) would collect gardeners' details. The notice in force describes the Garden Owner Register only. The Worker's grower route stays closed (`GROWER_PRIVACY_VERSION` empty) until this notice is approved and published.
**Scope of change:** Section 7 only. Its heading changes, and one subsection is added for growers. The Garden Owner Register text is unchanged, word for word. No other section changes, apart from two one-line cross-references (Sections 2 and 12).

---

## Section 7 · proposed text

**Heading (was "7. The Garden Owner Register"):**

> **7. The Garden Owner Register and the Grower Register**

**Lead sentence, added before the existing text:**

> PlotNua keeps two registers for The Borrowed Garden pilot: the Garden Owner Register, for homeowners who might share part of their garden, and the Grower Register, for people who would like somewhere to grow. They are separate lists with separate forms and separate consent. Joining one does not add you to the other, and nobody on one register can see the other.

**Existing Garden Owner Register text:** unchanged, under a sub-heading *"The Garden Owner Register (homeowners)"*.

**New sub-heading and text:**

> **The Grower Register (growers)**
>
> The Grower Register is a list, kept privately by PlotNua, of people who would like somewhere to grow and who might be introduced to a homeowner nearby. PlotNua is exploring this as a small pilot. Joining is voluntary and free. Matching is not live, and joining the register does not arrange an introduction or mean that a garden is available.
>
> The six quick questions on the Grower Register page are answered in your browser. Your answers are not sent to PlotNua. If you choose, four of them can fill in the registration form, where you can see and change them before you submit.
>
> What we collect when you join:
> - your first name;
> - your email address;
> - the area you choose from a short list;
> - how far you would travel, how much space you are looking for, and roughly when;
> - anything you choose to add in the note; and
> - a record that you gave your consent, which version of this notice applied, and when you joined.
>
> We do not collect your address, your Eircode, your phone number, your surname, your age, or anything about your health.
>
> We use this information so that we can tell you if someone near you has growing space they would consider sharing. We rely on your consent, which you give by ticking the box when you join. You can withdraw it at any time.
>
> Your record is private to PlotNua. It is not published, and there is no public listing, map, profile or directory. Records are reviewed by a person at PlotNua. If we think there might be a fit, we will email you first and describe the homeowner in general terms only. Your email address would only be shared with another person if you said yes to one specific introduction, and introductions are not yet available.
>
> Grower Register records are kept in the same database as the Garden Owner Register, in a separate table, and are sent and stored by the same service providers, in the same way, as described above.
>
> We keep your record for a maximum of 24 months. You can ask us to delete it at any time, and we may delete it sooner if it is no longer needed.
>
> To leave the register or ask us to delete your record, email hello@plotnua.ie. There is nothing to cancel and no notice period. When we delete your record we keep a separate note that you gave permission and that we honoured your request. That note holds a one-way digital fingerprint made from your email address, not the address itself, so that we can show we did what you asked.

## Cross-references (one line each)

- **Section 2**, after "If you choose to join the Garden Owner Register…": *"…or the Grower Register, we also collect the information described in Section 7."*
- **Section 12:** *"Garden Owner Register and Grower Register records are kept for a maximum of 24 months, as described in Section 7."*

## Consistency with what is built

| Notice says | Built as |
|---|---|
| Six questions not sent | Page: check answers are never read by `payload()` (guard G7, browser check P6c) |
| Four may fill the form, visible and changeable | Page pre-fills district, travel, space and timing only (P5d) |
| First name, email, area, travel, space, timing, note | Worker `GROWER_ALLOWED_KEYS` (10 keys; anything else refused, R4) |
| No address, Eircode, phone, surname, age, health | No such field (G5); Worker refuses those keys (R4) |
| Same database, separate table | `Growers` table in base `appUie3wPmPITfMW7` |
| Consent record with notice version | Consent proofs row carries `GROWER_PRIVACY_VERSION` (R5i) |
| 24 months; fingerprint kept after deletion | Same procedure as the Garden Owner Register (G1B, G6 runbook) |
| Consent sentence | Frozen G1B §3: "I'm over 18, and I'd like PlotNua to keep this and tell me about possible growing space nearby." |

## For the founder to decide

1. Approve this wording, or amend it.
2. Optionally, a short review by someone qualified in Irish data protection (as recommended for V3, R9).
3. Once approved: a bounded builder applies it to `privacy.html` with the marker `PLOTNUA-GROWER-PRIVACY-V6`. Guard G9 of the page builder checks for that marker.
