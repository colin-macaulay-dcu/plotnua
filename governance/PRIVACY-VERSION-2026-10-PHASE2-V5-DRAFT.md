# PRIVACY NOTICE · VERSION 2026-10-PHASE2-V5 · DRAFT FOR FOUNDER APPROVAL

**Status:** DRAFT, 14 October 2026. **Not published.** `privacy.html` is unchanged (it carries V4).

**Purpose:** extend the privacy notice to cover the PlotArt **Artist Register** (`artist-register.html`). Artist registrations are stored in the existing Art Space Register base, in a separate `Artists` table. They are sent through the existing Worker, on a separate closed route.

**Approval needed:** the founder approves the final wording below and the self-assessment addendum, both dated. Only then is the V5 builder written and run, and the notice published. The Artist Register stays **CLOSED** until the separate opening approval (`ARTIST_OPEN_APPROVAL` in `atlas-tools/build-artist-register.py`).

**Governed text:** every line below that begins `> ` is governed text. Guard A2 in `atlas-tools/build-artist-register.py` refuses to open the register unless `privacy.html` carries every one of these lines (after tags are stripped and whitespace is normalised), together with the marker `PLOTNUA-ARTIST-PRIVACY-V5`. Any wording change approved by the founder is made **in this file**, and the page then follows it.

## Changes from V4

1. **Section 8** gains an artist sub-section, placed after its existing text. The existing homeowner text is unchanged, word for word.
   - Proposed heading change: **"8. The Art Space Register and the Artist Register"**.
   - This change has publication-time co-edits in the proofs that anchor on the Section 8 heading (`prove-privacy-v4.py`, `prove-art-space-register.py`). These co-edits are made by the V5 builder, not by hand.
2. **Section 2:** one added sentence (below).
3. **How Long We Keep Information** (Section 12): one added line (below).
4. **"Last updated":** set to the publication month.
5. **No other change.** In particular:
   - no renumbering;
   - the Garden Owner Register section (Section 7) is unchanged;
   - the homeowner Art Space Register text is unchanged.

## Proposed V5 text

### Section 8 · new sub-section

> The Artist Register

> Artists can also choose to join the Artist Register from PlotArt's Artist Register page. It is a list, kept privately by PlotNua, of artists who might be interested in displaying, showing, installing or storing their work in homes and gardens in Ireland, or in reaching potential buyers through a home setting. Joining is voluntary and free. PlotNua is not introducing artists to homeowners, there is no matching, exhibition, booking or sales service, no payment is offered, and joining the register does not arrange anything.

> What we collect when an artist joins:

The following is published as a list. Each item is governed.

> the name you work under;

> your email address;

> the county where you are based, or that you are based outside Ireland;

> where you would consider opportunities and, if you choose to tell us, which counties or regions;

> what you make and which opportunities interest you;

> if you choose to tell us: the space your work needs, a link to your website or portfolio, and a short statement about your work; and

> a record that you gave your consent, which version of this notice applied, and when you joined.

> We do not collect your home address, your phone number, your date of birth, photographs of your work, prices or details of your sales.

> We use this information to contact you about the A Home for Art pilot and the development of PlotArt, for example to ask what would be useful to you, or to let you know if the idea develops. We rely on your consent, which you give by ticking the box when you join. You can withdraw it at any time.

> Your record is private to PlotNua. It is not published, and there is no public profile, listing, map or directory of artists. Registration details are accessible only to authorised people managing the register and to service providers where necessary to operate it. They are not shared with homeowners or made publicly available. Your details would only be shared with another person if you agreed to a specific arrangement, and no such arrangements are available.

> Artist registrations are kept in the same database as the Art Space Register, in a separate table, and are sent and stored in the same way and by the same service providers, as described above for the Art Space Register.

> Artist Register records are kept for no longer than 12 months, deleted sooner if no longer needed, and can be deleted at any time on request, in the same way and with the same deletion arrangements as the Art Space Register.

### Section 2 · one sentence

> If you choose to join the Artist Register, we also collect the information described in Section 8.

### Section 12 · one line

> Artist Register records are kept for a maximum of 12 months, as described in Section 8.

## Consent sentence (artist form)

This is the proposed wording, as implemented in the Worker (`ARTIST_CONSENT_TEXT`) and on the page.

- The Worker hashes the sentence the page sends and compares it with its own copy.
- Any change to the wording must be made in both places in one commit.
- Guard A3 refuses a mismatch.

*"I'm over 18 and agree that PlotNua may keep my registration details and contact me about the A Home for Art pilot and the development of PlotArt. I understand I can withdraw my consent at any time."*

(Not a `> ` line: the consent sentence lives on the form, not in the notice.)

## GDPR self-assessment · artist addendum (for founder approval, dated)

This addendum extends the Art Space Register self-assessment approved on 13 October 2026. It records only what is new for artists.

| Area | Position |
|---|---|
| Controller | PlotNua, as for the Art Space Register. |
| Purpose | Learning whether artists are interested, and contacting them about the A Home for Art pilot and PlotArt's development. No matching, introductions, bookings, sales or commission. |
| Lawful basis | Consent: a separate tick box, with a separate verified consent sentence and a separate consent proof marked `register = artist`. |
| Data | Name worked under, email, where based (county or outside Ireland), reach, disciplines, interests. Optional: space needs, an `https` portfolio link, a statement of up to 400 characters. No address, phone number, date of birth, photographs, prices or sales. |
| Minimisation | The Worker refuses any field outside its artist allow-list before the write switch is checked. |
| Visibility | Private. No public profile, listing or directory. Not shared with homeowners. |
| Processors | Cloudflare (the Worker; request logging off) and Airtable (same base and DPA, Team plan). No new processor. |
| Transfers | As in V4 (Standard Contractual Clauses; Cloudflare also relies on the EU-U.S. Data Privacy Framework). |
| Retention | 12 months maximum; `erase_after` flags each record; a person deletes it. |
| Deletion | Delete the Artists record, then its Consent proofs and Status log rows (`register = artist`, same timestamp), then add one anonymous Deletion log row with `register = artist`. |
| Abuse | 25 artist records a day; the cap is stored in Airtable, so it survives restarts. A burst limit, a hidden spam field, origin and fetch-metadata checks. |
| Age | 18+ confirmation. |

**Risks and resolution**

1. **A statement or portfolio link might reveal more than intended**, for example a third party's details or a personal address.
   - *Resolution:* the hint under the statement field asks for none of this, and an Airtable view, `Statements to screen`, supports the weekly review.
   - A portfolio link is stored, never published.
2. **The name an artist works under is often their real name.**
   - *Resolution:* it is treated as personal data throughout, and it is never published.
3. **Artists based in Northern Ireland or abroad.**
   - *Resolution:* PlotNua's notice applies equally to them. There is no change to transfers.
4. **Confusion with the Art Space Register.**
   - *Resolution:* separate page, consent sentence, table and switch, and a separate notice sub-section.
5. **Expectation of opportunities.**
   - *Resolution:* the developmental disclaimer appears on the page, in the success message and in the notice.
   - Guard A7 refuses promise wording.

No material risk is left unresolved. Paid advice is not required under the founder's gate.

## Publication steps (after the founder's approval of this text)

1. Record the approval date in this file.
2. Write `atlas-tools/build-privacy-v5.py`, modelled on `build-privacy-v4.py`. It:
   - applies exactly the changes above, with the `PLOTNUA-ARTIST-PRIVACY-V5` marker;
   - carries the proof co-edits;
   - refuses to build unless every governed line is present.
3. Run it, then check `privacy.html` against the governed lines.
4. Commit locally. The founder pushes.
