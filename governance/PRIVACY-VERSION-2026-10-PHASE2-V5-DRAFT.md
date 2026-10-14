# PRIVACY NOTICE · VERSION 2026-10-PHASE2-V5 · FINAL DRAFT FOR FOUNDER APPROVAL

**Status:** FINAL DRAFT, 14 October 2026 (after the founder decisions of 19:25). **Not published.**
- `privacy.html` is unchanged and still carries V4.
- The Artist Register stays **CLOSED**.
- Approval of this exact wording is required before anything is published. Opening the register is a separate approval (`ARTIST_OPEN_APPROVAL` in `atlas-tools/build-artist-register.py`).

**Governed text:** every line beginning `> ` is governed. Guard A2 in `atlas-tools/build-artist-register.py` refuses to open the register unless `privacy.html` carries every one of these lines (tags stripped, whitespace normalised), together with the marker `PLOTNUA-ARTIST-PRIVACY-V5`. Wording changes are made **here**, and the page follows.

## Founder decisions applied (14 October 2026, 19:25)

1. Section 8 is renamed **"The Art Space Register and the Artist Register"**.
2. Artist-register review trigger: **10 genuine artist registrations or 8 weeks after public opening, whichever comes first.** It triggers a review only, not matching or introductions.
3. Site-specific installations on the homeowner side remain a future improvement only.
4. The artist consent wording is the founder's (below). It is identical in the Worker (`ARTIST_CONSENT_TEXT`), the page builder (`CONSENT`) and this file. Guard A3 and the Worker tests C4 and C5 refuse any drift.

## Changes from V4

1. **Section 8 heading:** "8. The Art Space Register" becomes "8. The Art Space Register and the Artist Register".
2. **Section 8:** one new introductory sentence before the existing text, so that the two registers are distinguished from the first line.
   - The existing homeowner text follows unchanged, word for word, under the sub-heading "The Art Space Register (homeowners)".
   - The new artist text follows under "The Artist Register (artists)".
3. **Section 2:** one added sentence.
4. **Section 12** (How Long We Keep Information): one added line.
5. **"Last updated":** set to the publication month.
6. **No other change.** In particular:
   - no renumbering;
   - Section 7 (the Garden Owner Register) is unchanged;
   - every existing homeowner sentence in Section 8 is unchanged.

## Final V5 wording

### Section 8 · heading and introduction

> 8. The Art Space Register and the Artist Register

> PlotNua keeps two separate registers for the A Home for Art idea: the Art Space Register, for homeowners who might offer space for artists' finished work, and the Artist Register, for artists who might be interested in that kind of space. They are separate lists with separate forms and separate consent. Joining one does not add you to the other, and neither register is shared with the people on the other.

> The Art Space Register (homeowners)

*(The existing V4 Section 8 text follows here, unchanged.)*

> The Artist Register (artists)

> The Artist Register is a list, kept privately by PlotNua, of artists who might be interested in displaying, showing, installing or storing their work in homes and gardens in Ireland, or in reaching potential buyers through a home setting. You can join it from PlotArt's Artist Register page. Joining is voluntary and free, and it does not commit you to anything.

> PlotArt is in development. There is no matching service at present. PlotNua is not introducing artists to homeowners, there is no exhibition, booking or sales service, no payment is offered, and registering does not guarantee an opportunity of any kind.

> What we collect when you join:

The following is published as a list. Each item is governed.

> the name you work under;

> your email address;

> the county where you are based, or that you are based outside Ireland;

> where you would consider opportunities and, if you choose to tell us, which counties or regions;

> what you make and which opportunities interest you;

> if you choose to tell us: the space your work needs, a link to your website or portfolio, and a short statement about your work; and

> a record that you gave your consent, which version of this notice applied, and when you joined.

> We do not collect your home address, your phone number, your date of birth, photographs of your work, prices or details of your sales.

> We use this information to contact you about the development of PlotArt and about potential opportunities to connect with homeowners, for example to ask what would be useful to you or to let you know if the idea develops. We rely on your consent, which you give by ticking the box when you join.

> Your registration is stored privately. It is not published: there is no public artist profile, listing, map or directory. Registration details are accessible only to authorised people managing the register and to service providers where necessary to operate it. Your details are not shared with homeowners, automatically or otherwise. If a possible opportunity ever arose, we would contact you first, and your details would only be shared with a homeowner if you agreed to that specific arrangement. No such arrangements are available at present.

> Artist registrations are kept in the same database as the Art Space Register but in a separate table, and are sent and stored by the same service providers, in the same way, as described above for the Art Space Register.

> We keep your registration for no longer than 12 months, and we delete it sooner if it is no longer needed.

> You can withdraw your consent, or ask us to delete your registration, at any time by emailing hello@plotnua.ie. There is nothing to cancel and no notice period. When we delete your registration, we delete everything the Artist Register holds about you, including the record of your consent, and the same arrangements for our database provider's trash and recovery copies, and for our anonymous deletion log, apply as described above for the Art Space Register.

### Section 2 · one sentence

> If you choose to join the Artist Register, we also collect the information described in Section 8.

### Section 12 · one line

> Artist Register records are kept for a maximum of 12 months, as described in Section 8.

## Requirement coverage (founder brief, 19:25)

| Requirement | Where it is covered |
|---|---|
| The Artist Register's purpose | The first "(artists)" paragraph, and "We use this information…" |
| Private storage of registrations | "Your registration is stored privately…" |
| No current matching service | "There is no matching service at present…" |
| No automatic sharing with homeowners | "…not shared with homeowners, automatically or otherwise…"; the Section 8 introduction |
| No public artist profiles | "…there is no public artist profile, listing, map or directory." |
| 12-month retention | "We keep your registration for no longer than 12 months…"; the Section 12 line |
| How to withdraw consent | "You can withdraw your consent… by emailing hello@plotnua.ie." |
| How to request deletion | The same paragraph, plus the deletion arrangements |
| The distinction between artist and homeowner registrations | The Section 8 introduction; the two sub-headings; the separate table |

## Consent sentence (artist form)

This is the founder's wording, verbatim and in ASCII only. It is identical in `worker/art-space-register/src/index.js` (`ARTIST_CONSENT_TEXT`) and `atlas-tools/build-artist-register.py` (`CONSENT`).

I confirm that I am 18 or over and consent to PlotNua storing my Artist Register details and contacting me about the development of PlotArt and potential opportunities to connect with homeowners. I understand that registering does not guarantee an opportunity and that I can withdraw my consent at any time.

**How the mechanism treats it**
- The page writes the sentence into the consent label with `textContent` and sends it as `consent_text`.
- The Worker hashes what it receives (after collapsing whitespace) and compares that hash with the hash of its own copy.
- On a mismatch the registration is refused (`consent_text`), so a page and a Worker that disagree record nothing.
- The hash of this sentence is stored on the Artists row and on the consent proof.
- If this sentence is ever changed, the old hash stays on existing records. That is correct: it proves what each person agreed to.

## GDPR self-assessment · artist addendum (for founder approval)

This addendum extends the Art Space Register self-assessment approved on 13 October 2026.

| Area | Position |
|---|---|
| Controller | PlotNua, as for the Art Space Register. |
| Purposes | (1) Contact about the development of PlotArt; (2) contact about potential opportunities to connect with homeowners. Both are named in the consent sentence and in the notice. No matching, introductions, bookings, sales or commission. |
| Lawful basis | Consent: a separate tick box and a separate verified sentence, with a consent proof marked `register = artist`. Withdrawal is as easy as joining (one email). |
| Data | Name worked under, email, where based (county or outside Ireland), reach, disciplines and interests. Optional: space needs, an `https` portfolio link, a statement of up to 400 characters. |
| Not collected | Home address, phone number, date of birth, photographs, prices, sales. The Worker refuses any field outside its allow-list. |
| Visibility | Private. No public profile, listing or directory. Not shared with homeowners, automatically or otherwise. |
| Processors and transfers | Cloudflare and Airtable, as in V4. No new processor. |
| Retention | 12 months maximum. `erase_after` flags each record; a person deletes it. |
| Deletion | Delete the Artists record, then its Consent proofs and Status log rows (`register = artist`, same timestamp), then add one anonymous Deletion log row with `register = artist`. |
| Abuse controls | 25 artist records a day (stored in Airtable, so it survives restarts), a burst limit, a hidden spam field, origin and fetch-metadata checks, and `typecast:false`. |
| Age | Confirmation of 18 or over, in the consent sentence. |
| Review | 10 genuine artist registrations or 8 weeks after public opening, whichever comes first. Review only. |

**Risks and resolution**

1. **Expectation of opportunities.** The purpose names "potential opportunities", which could be read as a promise.
   - *Resolution:* the consent itself says that registering "does not guarantee an opportunity".
   - The notice says there is no matching service at present.
   - The page carries a disclaimer, and guard A7 refuses promise wording anywhere else on the page.
2. **Two purposes under one tick box.** Both are contact purposes about the same initiative, and both are named.
   - Assessed as specific and informed. Splitting them into two boxes is possible, but is not required for this level of processing.
3. **A free-text statement or portfolio link may reveal more than intended.**
   - *Resolution:* the field hint asks for no address or third-party details, and the "Statements to screen" view supports the weekly review.
   - A portfolio link is stored, never published.
4. **The name an artist works under is often their real name.** It is treated as personal data throughout and is never published.
5. **Artists in Northern Ireland or outside Ireland.** The same notice and rights apply. There is no change to transfers.
6. **Confusing the two registers.** Separate page, sentence, table and switch; the Section 8 introduction explains the difference.

No material risk is left unresolved. Paid advice is not required under the founder's gate.

## Implementation notes for publication

These are made by the V5 builder, not by hand.

1. **The V4 dependency.**
   - `build-privacy-v4.py`'s `published_ok()` currently checks the V4 Section 8 exactly, heading included.
   - The homeowner register's opening guard (R2 in `build-art-space-register.py`) uses that check. The homeowner register is OPEN, so renaming the heading would make R2 refuse the homeowner build.
   - The V5 publication must therefore move R2 to accept V5 (the V4 homeowner text intact, inside the renamed section).
   - It must also update the affected cases in `prove-art-space-register.py` and `prove-privacy-v4.py`.
   - The homeowner Worker and page do not change.
2. **The homeowner Worker's `PRIVACY_VERSION`** is V4. After V5 is published, V5 is the notice in force for everyone, although the homeowner text is unchanged.
   - Recommended: change the homeowner Worker to V5 as part of the publication (a one-line `wrangler.toml` change and one deploy).
   - Otherwise, new homeowner records will keep recording V4.
3. **The artist page's notice summary** ("Before you register — what we keep…") is written in the same terms as this notice and is generated by the builder.
