# DISC-032 · The Supper Club at Home · build record

**27 October 2026 · Phase 2 consolidated production preparation (founder authorisation, 27 Oct 2026)**

## Status

| | |
|---|---|
| **Release candidate** | Branch `feature/disc032-supper-club-at-home`, on `origin/main` `5cbcc4e` (reconciled with DISC-033; first prepared on `7f8f964`). The page is `noindex, follow`, is not in the sitemap, the Discovery Library or the search index, and no other page links to it |
| **Launch** | Branch `launch/disc032-supper-club-at-home`, one commit on top of the release candidate: Library card, sitemap, search index, `index, follow`. **Held: needs its own founder approval** |
| **Pushed / merged / deployed** | Nothing |

## What the founder approved (27 Oct 2026)

- **Phase 1:**
  - C1 v3 is the BEFORE master and C2 the POSSIBLE master.
  - The corrected pair is approved.
  - The 0.2 px architectural-median tolerance exception is approved.
  - The visible guests and chef are approved.
  - The glassware is approved, without implying that alcohol sales are authorised.
  - The provenance chain is approved.
  - The pn-compare component is the reference design for future Discoveries.
  - Refinements A–C are approved; the hero designs are final.
- **Phase 2:** complete all production preparation in one pass.
  - Stay on a local feature branch, with no push, merge or deployment.
  - Keep the page `noindex` until launch approval.
  - Keep the card and sitemap changes isolated.
  - No registration, introductions, bookings, payments or supplier contact.
  - No changes to live Discoveries.
- **Standing (Stage 2, refinements A–E):**
  - There is no verified Irish example of Model 2.
  - No earnings figures.
  - Excluding alcohol from the ticket does not resolve licensing.
  - Regulatory questions stay open.
  - Registration stays inactive.
  - Never imply that ticketed home dining is exempt from planning, food-safety, fire-safety or insurance requirements.

## What was built

| Piece | Files |
|---|---|
| **Shared component** | `assets/identity/pn-compare.css`, `assets/identity/pn-compare.js` (the approved Phase 1 build, byte for byte) |
| **Shared editorial layer** | `assets/identity/pn-discovery-editorial.css`: DISC-031's inline ns-* blocks that DISC-032 needs, rule for rule, as de-*. **DISC-031 itself is unchanged** and keeps its inline layer until its migration is approved. Equivalence was proved by computed styles: 1,371 elements × 35 properties × 3 viewports, 0 differences against the approved preview |
| **Page** | `discovery-supper-club-at-home.html`: the approved preview with a production head (consent banner and analytics as on every Discovery, SEO metadata, JSON-LD WebPage + BreadcrumbList). The preview flag and the placeholders are removed. Real supper clubs are not named (see below) |
| **Images** | The eight approved preview encodings, unchanged (hash-verified), plus `DISC-032-og-1200x630.jpg` from the C2 master |
| **Provenance** | `governance/DISC-032-PROVENANCE-DECLARATION-2026-10-27.json` → `atlas-tools/declare-disc032-provenance.py` → 9 records in `image-provenance-records.json`. Pinned as `FOUNDER_ATTESTED_DISC032` in `validate-image-provenance.js` |
| **Registries** | Identity, header and Premium (29 identity pages, 31 header pages, after DISC-033's 28 / 30). The two standard release checks were updated to those counts |
| **Proof** | `atlas-tools/prove-disc032-page.py` (S1–S11; `--prove`: 19 planted faults in release-candidate mode, 18 in launch mode) |

## Editorial decisions taken in this pass (routine; recorded)

- **Real supper clubs are not named.** The preview's three named profiles were placeholders pending each club's written agreement, and two of those clubs are among the six pending enquiries. Section 02 instead describes the one example reported by The Irish Times (19 Nov 2025), without names. It says Irish home supper clubs will be profiled only with each club's agreement.
- **Sources:**
  - The businesses' own websites were removed with their names.
  - The allergen source now points to the FSAI page on non-prepacked food. It states the written-allergen requirement and that S.I. 489 of 2014 was updated by S.I. 656 of 2024.
  - The Irish Statute Book link could not be re-verified from the build session.
- **"Take part" wording:** "Nothing is set up yet: we don't arrange introductions, take bookings or sell tickets." Registration stays closed on both cards.

## Provenance in one paragraph

- **Origin:** ChatGPT image generation (gpt-image), per the OpenAI C2PA credentials of C2 and C1 v2.
- **C1 v3:** a deterministic geometric correction of v2 (24.68% of pixels moved, none generated). It carries **no** OpenAI credentials. Its delivered file carries only an Anthropic "Claude provided this file" manifest, and its pixels equal the pre-delivery output.
- **Prompts:** not supplied, so `prompt_status` is UNAVAILABLE. They have never been reconstructed.
- **Reference inputs:** UNCERTAIN; the credentials do not record conversation inputs, and no founder statement on third-party references has been recorded.
- **Resemblance review:** recorded.
- **Surfaces:** discovery and library-card only.

## Isolation: how the launch cannot become public by accident

1. The release candidate carries no card, sitemap entry or search-index entry. The search index allows only sitemap URLs.
2. The release candidate's release check (`prove-disc032-page.py`, S7) **refuses** if the page is in the sitemap, the Library or the search index, if it is linked from any other page, or if its robots meta says `index`.
3. The launch is a separate branch and a separate bundle, with no deploy script. Releasing it needs its own release folder, built only after the founder approves the launch, and its check is `--launch`.

## Tests (summary; full results in the release report)

- **Image Rights Gate, run locally step by step:** 26/26 on the release candidate and on the launch.
- **Standard production checks:** 37/37, plus 2 release-specific (39/39).
- **Provenance guard:** 15/15.
- **Browser tests:** axe-core 0 violations on desktop and mobile; mouse, touch, keyboard, reduced-motion and no-JS behaviour as approved; layout shift 0 on mobile and 0.028 on desktop (web-font swap).
- **Hero:** pixel-identical to the approved Phase 1 screenshots.
- **Existing pages:**
  - No existing HTML page changed in the release candidate.
  - DISC-031, the Library, A Home for Art, Power Station and Search render pixel-identical to production.
  - The homepage and Living in the Garden animate, so they differ between two renders of production itself.

## Recorded, not fixed (pre-existing)

- Running `build-search-rail.py` in write mode moves the rail stub above the header bar on every page, and the identity and header builders then move it back. Its baseline also predates two guides now in the sitemap. The launch adds only its own baseline entry, as DISC-031 did.
- The search index envelope's `sourceAdditionalHomeSha256` refreshes whenever the index is rebuilt (the additional-home universe changed upstream on 27 Oct).

## Reconciliation with DISC-033 (27 Oct 2026, evening)

DISC-033 The Hidden Flood Barrier was deployed first (`5cbcc4e`). The release candidate was rebased onto it, and nothing of DISC-033 changed:

- **Registries:** both pages are listed in the identity, header and Premium registries. The counts are now 29 identity pages and 31 header pages, and the release-check strings were updated to match. DISC-033's own page proof stays in the standard checks.
- **Provenance:** the DISC-033 records and pin are untouched. The nine DISC-032 records were re-applied, after validation, on top of the 57 production records, and both pins are listed.
- **Launch (held):** 28 public pages in the search rail; the Library card sits beside DISC-033's; the sitemap entry, search-index record and baseline entry are rebuilt on the new base.
- **DISC-032 itself:** the page, images, component, editorial layer, declaration and proofs are byte-identical to the approved candidate.
