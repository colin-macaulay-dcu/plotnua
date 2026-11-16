"""PlotArt · artist opportunity lists (development 16 Nov 2026; founder approval of the architecture and destinations).

Every opportunity an artist can choose in PlotArt Studio has a public list of the PUBLISHED artists who chose to show it,
each name linking to that artist's existing gallery. The ONLY input is the set of approved public gallery packages
(plotart/artists/<slug>/gallery.json), written by the content pipeline from founder-approved Studio exports:
  - an artist appears only while their gallery is published (no package, no listing);
  - an artist appears under an opportunity only while their package carries it in "open_to" (the artist's own choice,
    published as an instant update), or, for Commissions, while their existing "Open for commissions" setting is on;
  - nothing else about an artist's Opportunities answers ever reaches the website (the Studio never exports it).

Destinations (founder approval, 16 Nov 2026):
  Living Gallery        plotart/living-gallery.html          (its own page)
  Art for Hire          plotart/art-for-hire/index.html      (its own page, below and separate from the works approved for hire)
  Mobile Gallery        plotart/mobile-gallery/index.html    (its own page)
  all seven             plotart/opportunities/index.html     (new page, outside the main navigation; noindex until the SEO
                                                              workstream decides)
Each page holds ONE generated region (BEGIN ... END). Everything outside it is fixed by the code release and pinned in the
launch manifest; the content pipeline may change only the region, and only to exactly what update() produces from the
published packages (atlas-tools/release/plotart-content-boundary.py checks that).
"""
import html
import re
from pathlib import Path

E = lambda s: html.escape(str(s), quote=True)
BEGIN, END = "<!-- pa-opportunity-artists:begin -->", "<!-- pa-opportunity-artists:end -->"
REGION = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
HUB = "opportunities/index.html"

# key: (short label, list heading, what the artists said, programme page or None, anchor on the opportunities page)
OPPORTUNITIES = {
    "exhibitions": ("Exhibitions", "Artists open to exhibitions",
                    "These artists have said they’d welcome conversations about showing their work in physical gallery exhibitions.", None, "exhibitions"),
    "living_gallery": ("Living Gallery", "Artists open to the Living Gallery",
                       "These artists have said they’d welcome conversations about showing their work in someone’s home.", "living-gallery.html", "living-gallery"),
    "art_for_hire": ("Art for Hire", "Artists open to Art for Hire",
                     "These artists have said they’d welcome conversations about hiring out their work. Only the works shown under “Available to hire” have been approved for hire; being listed here doesn’t mean a particular work is available.",
                     "art-for-hire/", "art-for-hire"),
    "mobile_gallery": ("Mobile Gallery", "Artists open to home viewings",
                       "These artists have said they’d welcome conversations about home viewings arranged through participating galleries. No gallery’s participation has been confirmed yet.",
                       "mobile-gallery/", "mobile-gallery"),
    "venues": ("Hotels and workplaces", "Artists open to hotel and workplace displays",
               "These artists have said they’d welcome conversations about showing their work in hotels, offices and other workplaces.", None, "hotels-and-workplaces"),
    "commissions": ("Commissions", "Artists open to commissions",
                    "These artists have said they’d welcome enquiries about a new, commissioned work. Any commission is agreed directly between the artist and the client.", None, "commissions"),
    "talks": ("Talks and events", "Artists open to talks and events",
              "These artists have said they’d welcome conversations about artist talks and events.", None, "talks-and-events"),
}
KEYS = tuple(OPPORTUNITIES)
NOTE = "Every opportunity is discussed and agreed individually with the artist. Being listed is not a booking, and nothing is confirmed until it’s agreed."
# Which list each page carries (plotart/<path>): the three programme pages carry their own; the opportunities page all seven.
PAGES = {"living-gallery.html": ("living_gallery",), "art-for-hire/index.html": ("art_for_hire",),
         "mobile-gallery/index.html": ("mobile_gallery",), HUB: KEYS}
MEDIUM = {"painting": "Painting", "drawing": "Drawing", "works_on_paper": "Works on paper", "printmaking": "Printmaking", "photography": "Photography",
          "sculpture": "Sculpture", "ceramics_craft": "Ceramics and craft", "textiles": "Textiles", "mixed_media": "Mixed media",
          "digital_new_media": "Digital and new media", "other": ""}


class Refused(ValueError):
    pass


def check_open_to(v):
    """The gallery export's optional open_to: a non-empty list of known opportunity keys, no repeats, in the fixed order."""
    if not isinstance(v, list) or not v or any(not isinstance(k, str) or k not in OPPORTUNITIES for k in v) or len(set(v)) != len(v) \
            or v != [k for k in KEYS if k in v]:
        raise Refused("open_to must be a non-empty list of known opportunities, in the fixed order, without repeats")
    return v


def open_to(pkg):
    """The opportunities this published artist is listed under (Commissions also while "Open for commissions" is on)."""
    a = pkg["artist"]
    keys = set(a.get("open_to") or [])
    if a.get("open_for_commissions") is True:
        keys.add("commissions")
    return [k for k in KEYS if k in keys]


def href(key, base):
    """Where an opportunity is listed, relative to the PlotArt root through `base` ("" from plotart/, "../" one level down)."""
    label, head, said, page, anchor = OPPORTUNITIES[key]
    return base + (page + "#open-artists" if page else "opportunities/#" + anchor)


def _surname(pkg):
    n = pkg["artist"]["display_name"].strip()
    return (n.split()[-1].lower(), n.lower(), pkg["artist"]["slug"])


def listed(packages, key):
    """Published artists listed under `key`, by surname (neutral: never by position, fee or anything else)."""
    out = []
    for p in packages:
        if p.get("publication", {}).get("state") != "approved":
            raise Refused("an unapproved gallery package was offered to the opportunity lists")
        if key in open_to(p):
            out.append(p)
    return sorted(out, key=_surname)


def _rows(pkgs, base):
    def line(p):
        a = p["artist"]
        what = a.get("practice") or MEDIUM.get(a.get("medium"), "")
        return ('<li><a href="%sartists/%s/" data-pa-track="opportunity_artist">%s</a>%s</li>'
                % (base, E(a["slug"]), E(a["display_name"]), ('<span>%s</span>' % E(what)) if what else ""))
    return '<ul class="pa-opp-list">%s</ul>' % "".join(line(p) for p in pkgs)


def section(key, packages, base, hub):
    label, head, said, page, anchor = OPPORTUNITIES[key]
    pkgs = listed(packages, key)
    if not pkgs and not hub:
        return ""          # a programme page shows nothing until someone is listed (the region stays, empty)
    sid = anchor if hub else "open-artists"
    more = ('<p class="pa-opp-more"><a href="%s">About the %s →</a></p>' % (E(base + page), E(label))) if hub and page else \
           ('<p class="pa-opp-more"><a href="%sopportunities/">Every artist opportunity →</a></p>' % E(base)) if not hub else ""
    body = _rows(pkgs, base) if pkgs else '<p class="pa-opp-none">No artists are listed here yet.</p>'
    return ('<section class="pa-opp" id="%s" aria-labelledby="opp-%s-h"><div class="pa-wrap pa-opp-in">\n'
            '  <h2 id="opp-%s-h">%s</h2>\n  <p class="pa-opp-said">%s %s</p>\n  %s\n  %s\n</div></section>'
            % (sid, key, key, E(head), E(said), E(NOTE), body, more))


def content(path, packages):
    hub = path == HUB
    base = "../" * path.count("/")
    return "\n".join(s for s in (section(k, packages, base, hub) for k in PAGES[path]) if s)


def update(document, path, packages):
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise Refused("Missing or duplicate opportunity region in plotart/" + path)
    inner = content(path, packages)
    return REGION.sub(lambda m: BEGIN + ("\n" + inner + "\n" if inner else "") + END, document, count=1)


def outside(document):
    """The page with its opportunity region blanked out (what the launch manifest pins)."""
    if document.count(BEGIN) != 1 or document.count(END) != 1 or not REGION.search(document):
        raise Refused("Missing or duplicate opportunity region")
    return REGION.sub(BEGIN + "<!-- opportunity artists -->" + END, document, count=1)


def refresh(root, packages):
    """Rewrite every opportunity region from the published packages (the content pipeline, after each gallery change)."""
    for path in PAGES:
        dest = Path(root) / "plotart" / path
        if dest.exists():
            dest.write_text(update(dest.read_text(encoding="utf-8"), path, packages), encoding="utf-8")


def artist_line(pkg, base="../../"):
    """The artist's own gallery page: "Open to: …", each linking to its list. Commissions is left out when the existing
    "Open for commissions" line is already shown (never said twice). Empty when the artist shows nothing."""
    a = pkg["artist"]
    keys = [k for k in check_open_to(a["open_to"])] if a.get("open_to") else []
    if a.get("open_for_commissions") is True:
        keys = [k for k in keys if k != "commissions"]
    if not keys:
        return ""
    return '<p class="pa-ag-meta pa-ag-open">Open to: %s</p>' % " · ".join(
        '<a href="%s" data-pa-track="artist_opportunity_link">%s</a>' % (E(href(k, base)), E(OPPORTUNITIES[k][0])) for k in keys)
