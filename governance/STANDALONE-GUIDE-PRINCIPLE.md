# Standalone guide principle

**Founder decision, 17 Oct 2026** (SEO strategy approval, phase 1). This applies to every standalone SEO guide PlotNua publishes.

## When a standalone guide exists

A standalone guide exists only where the search evidence shows a distinct intent that its parent Discovery cannot serve as well. It keeps its own dedicated, indexable URL wherever the evidence supports one. The guide's title, H1 and opening target the guide's own intent, not the parent's.

## The guide's connection to its parent Discovery

Every guide is a child of exactly one parent Discovery, and must make that obvious to a visitor who arrives directly from Google:

1. **Parent link near the top.** The hero carries a visible link, `← Explore <Parent Discovery>`, before or beside the H1.
2. **A "Part of" line in the hero.** The hero states that the guide is part of the parent Discovery.
3. **An invitation further down.** A prominent block invites the reader into the parent Discovery and its relevant makers or providers, for example its Explorer anchor.
4. **Links from the parent.** The parent Discovery links to the guide early on the page, not only once in the middle.
5. **Not footer links or breadcrumbs alone.** Breadcrumb JSON-LD and footer links stay, but they never replace points 1 to 4.
6. **The rule is enforced in the build.** A guide's builder refuses a page that:
   - lacks the parent link;
   - places it beyond the top of the page;
   - hides it with CSS;
   - omits the "Part of" line;
   - lacks the invitation block or its links.

## First implementation

**Garden Room Prices in Ireland** (`garden-room-prices-ireland.html`):
- Parent Discovery: Living in the Garden.
- Enforced by guard G-PARENT in `atlas-tools/build-garden-room-prices.py`.
