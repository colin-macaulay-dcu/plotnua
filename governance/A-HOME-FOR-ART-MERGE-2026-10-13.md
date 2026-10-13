# A HOME FOR ART · DISC-024 CONSOLIDATED INTO DISC-023 (DISCOVERY PAGE ONLY)

**Date:** 13 October 2026 · **Authority:** founder decision "A Home for Art · merged Discovery · approved for build" (supersedes the same day's keep-separate decision) · **Baseline:** `460c97a` · **Status:** committed locally, not pushed.

## Decision recorded

- **DISC-024 (Open Your Home to Art) is consolidated into DISC-023 (A Home for Art) at the Discovery-page level only.**
- **Not retired:**
  - the DISC-024 Property Check (`disc024-open-your-home-to-art.html`), its engine, questions and outcomes;
  - its journey ID `disc024-open-your-home-to-art` and every saved My Plot record;
  - the closed Art Space Register attached to it.
- No Atlas Discovery record was created.

## The merged Discovery

**URL:** `discovery-a-home-for-art.html`, unchanged. **H1:** *A Home for Art.*

**Hero** (founder wording):
- Subtitle: "Your home could be more than somewhere to hang art."
- Intro: "Three possibilities. One home. And you decide how far to go."
- The middle paragraph opens the article.

**Three branches**, each anchored and introduced by a chooser:

| Branch | Anchor | Content (verbatim from the two source pages unless noted) | Check |
|---|---|---|---|
| 1 · Discover & own | `#discover-and-own` | Original/print/edition · "Does it have to be expensive?" · four routes · commissioning · four things to settle in writing | **Check your wall** → DISC-023 |
| 2 · Live with art | `#live-with-art` | Founder's Branch 2 wording, verbatim · the Display tile · "the artist is the seller" · pointer to the custody, insurance and money questions | **Check how far you'd go** → DISC-024 |
| 3 · Open your home to art | `#open-your-home-to-art` | "What you have / what they don't" · the four-way ladder (Store, Display, Open, Help sell) · the commercial-direction note | **Check how far you'd go** → DISC-024 |

**Shared sections:**
- "Most regrets are size regrets" (the wall);
- "Three things to settle first" (`#before-anything-arrives`): custody, home insurance, money, the agreement checklist, insurance detail, and money/selling/planning;
- "Three people are better off";
- FAQ;
- "Where this could go": the PlotArt sentence unchanged, plus "Finding each other" with "This matching service is not live yet."

**Closing panel:** two independent checks, side by side.

**Imagery:** only images already published on the two source pages, plus one existing related-card thumbnail of Your Home on Screen. No new asset.

## URL migration

- **`discovery-open-your-home-to-art.html` is now a redirect page, not a Discovery.**
  - Canonical: `https://plotnua.ie/discovery-a-home-for-art.html`.
  - A script sends visitors to `discovery-a-home-for-art.html` + the original query string + `#open-your-home-to-art`, or to a known branch hash if one was given.
  - A `<noscript>` meta refresh is the fallback (the query string is not kept without script).
  - A visible link is included.
  - The page has no analytics and is not in the sitemap.
- **PN-SOC-017** (Facebook, Mon 19 Oct 2026) links the old URL. It lands on the hosting branch with `fbclid` and any other query parameters preserved. Its call to action, "Discover Open Your Home to Art on PlotNua", remains true, because that's the branch's name.

## Consolidation (bounded, one-for-one, guard M9)

- **Homepage, Discovery Library, 404:** one art card, "A Home for Art".
- **Discovery Library image map:** row removed and title renamed.
- **Living in the Garden:** its duplicate related card removed.
- **Your Home on Screen:** its related card now points to `#open-your-home-to-art`.
- **My Plot:**
  - the Hidden Potential list has one entry;
  - `MYPLOT_JOURNEY_DISCOVERY['disc024-…']` → `discovery-a-home-for-art.html#open-your-home-to-art`;
  - saved records, journey keys and "Reopen this check" destinations are unchanged.
- **DISC-024 check:** only its "Back to the story" link changed, now pointing to the hosting branch. The DISC-023 check is byte-identical.
- **Sitemap:** old URL removed; merged page `lastmod` 2026-10-13.
- **Search** (through its builder):
  - `poss-open-your-home-to-art` retired;
  - `jrn-disc024-…` now belongs to `poss-a-home-for-art`;
  - 13 possibilities;
  - the merged title and description carry "A Home for Art" and "open your home to art".
- **Proof inventories updated deliberately:**
  - `prove-landmarks.mjs`: 13 → 12 public Discoveries;
  - `build-search-rail.py`: `EXPECTED_PAGES` 22 → 21;
  - `prove-discovery-library-capability.py`: card title.
- **Retired:** `atlas-tools/build-art-cross-links.py`. Its two links are now anchors within one page, and its cases were removed from `prove-art-space-register.py`.

## Builder and guards

`atlas-tools/build-a-home-for-art-merge.py`. Sources are read from git at `460c97a`.

| Guard | What it enforces |
|---|---|
| M1 | Every visible text block is verbatim from the sources or declared in `NEW_TEXT` (founder wording and interface labels) |
| M2 | Anchors are present |
| M3 | Both checks are linked from their branches and from the panel; no link to the old URL |
| M4 | No service claim |
| M5 | Only published imagery |
| M6 | All cautions present: Allianz, Rent-a-Room, Section 5, Artists' Exemption, copyright, insurance caps, "not live yet", PlotArt, no price guides, no valuation, and the founder's Branch 2 text |
| M7 | The governed redirect |
| M8 | DISC-024 changes by its back-link only; DISC-023 unchanged |
| M9 | Consolidation applied; no live page links to the old URL |

## Tests (13 Oct 2026)

| Suite | Result |
|---|---|
| Merge builder `--check` | M1–M9 pass |
| Browser (desktop 1440, mobile 390) | **56 / 56**: hero; chooser to all three anchors; Branch 2 wording; check routing and labels; redirect with query string, branch hash, no query and no-JS; DISC-023 and DISC-024 completed and saved; My Plot reopen and Discovery links; Search for four queries; one art card on the Library, homepage and 404; 11 other Discoveries load clean with no stale link |
| axe WCAG 2.1 A/AA | 0 violations on new elements. Two pre-existing template contrast findings (`.quiet-section > .kicker`, `.related-head > .kicker`) are identical on the baseline page and other Discoveries. Out of scope here and recorded for a site-wide fix. |
| Art Space Register | builder R1–R13 pass · capability **24 / 24** (cross-link cases retired) · Worker **64 / 64** · register absent when closed |
| `prove-landmarks.mjs` | 133 / 133 (7 fewer than before because the redirect page is no longer a Discovery) |
| Search index and rail · library images and capability · image provenance 11 / 11 · image-rights manifest up to date | pass |
| House as Power Station and Borrowed Garden Explorers · G6 privacy 43 / 43 · Garden Worker 74 / 74 · disclosure firewall 27 / 27 · journey-exit mutations 19 caught | pass |

## Addendum: visual and narrative priority correction (founder, 13 Oct 2026, 20:34)

The merged page was approved in principle, but it led with buying. It now leads with **Open Your Home to Art**, told in that Discovery's own pictures:

1. **Hero:** A Home for Art, unchanged. The spark is the hosting Discovery's own: *"What if a room you rarely use could give local art somewhere to be seen?"*
2. **The overlooked opportunity.** New heading: *"You may already have something an artist needs."* Underneath: *"Making the work is rarely an artist's hardest problem…"* and the **Space ↔ Space** board, verbatim.
3. **Before and after, in pictures:**
   - the empty wall annotated as a potential asset ("A wall, a floor, and a door that opens.");
   - the artist among finished work ("The work exists already. What it lacks is a room.");
   - the same room hung with art. This was the hosting Discovery's hero. New caption: *"The same room, once the work has somewhere to be seen."*
4. **Three possibilities**, in the founder's order:
   - **Open your home to art** (the four-way ladder; "Check how far you'd go"), followed by the outcome plate ("A work leaves with somebody who saw it in a real room.");
   - **Live with art**, followed by the evening plate;
   - **Discover & own** (why a blank wall matters, what you are buying, sizing, where to look, commissioning, before you buy; "Check your wall").
5. **Shared guidance:** before anything arrives, three people are better off, the FAQ, and where this could go.
6. **Both checks**, hosting first.

**Other changes:**
- **Title and description** reordered: Host, Live With or Buy. Search rebuilt through its builder.
- **Two buyer-side plates dropped** because they repeated the empty-wall and artist concepts: `5dc201…` (annotated fireplace wall) and `5d43b14…` (artist at easel).
- **Unpublished image not used:** the original DISC-024 "empty room" master (`933e80…`) is not published and not declared, so it was not introduced.
- **Unchanged:** both checks, the My Plot keys, the redirect, every caution, the closed register and imagery permissions.
- **New guard M10** enforces this order.
- **Browser validation:** 58 / 58.
