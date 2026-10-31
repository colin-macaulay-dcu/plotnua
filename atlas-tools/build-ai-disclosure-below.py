#!/usr/bin/env python3
"""
AI disclosure beneath the comparison (founder approval, 31 Oct 2026: "No disclosure badge should obscure the
imagery"). Applies the treatment approved on DISC-016 Above and Beyond to every Discovery hero slider that
carried the overlay badge:

  DESKTOP          .pn-hero-note: a discreet line immediately beneath the hero, aligned with the hero content
  MOBILE / TABLET  .pn-compare__note: immediately beneath the Before/Possible controls, in the comparison panel
  (pn-compare.css v1.4: exactly one is displayed per viewport; both are visible without JavaScript)

Wording (register labels.AI_ILLUSTRATION_VARIANTS):
  "Illustrative AI-generated visualisation. Not an actual installation."      (installation Discoveries)
  "Illustrative AI-generated visualisation. Not an actual home or event."     (Supper Club at Home)

The hero imagery, slider markup and behaviour are untouched: only the badge <p class="pn-compare__ai"> leaves
the figure, the note is added after the comparison bar, the line after the hero header, and the stylesheet
link moves to ?v=1.4. Discoveries without AI imagery are not in the list.

  python3 atlas-tools/build-ai-disclosure-below.py          apply
  python3 atlas-tools/build-ai-disclosure-below.py --check  verify, write nothing
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv
INSTALL = "Illustrative AI-generated visualisation. Not an actual installation."
EVENT = "Illustrative AI-generated visualisation. Not an actual home or event."
PROPERTY = "Illustrative AI-generated visualisation. Not an actual property."
FILM = "Illustrative AI-generated visualisation. Not an actual film production."
PAGES = {
    "discovery-above-and-beyond.html": INSTALL,
    "discovery-garden-retreat.html": INSTALL,
    "discovery-hidden-bins.html": INSTALL,
    "discovery-house-as-power-station.html": INSTALL,
    "discovery-hidden-flood-barrier.html": INSTALL,
    "discovery-natural-swimming-garden.html": INSTALL,
    "discovery-supper-club-at-home.html": EVENT,
    # Release 5 (founder approval, 31 Oct 2026): page-specific approved wordings
    "discovery-driveway-income.html": PROPERTY,
    "discovery-your-home-on-screen.html": FILM,
}
# the desktop line aligns with each hero's own copy: the 1240 px content column (default), the copy's viewport
# inset (Hidden Flood Barrier 4vw, Supper Club 5vw), or centred under centred copy (Natural Swimming Garden)
ALIGN = {
    "discovery-hidden-flood-barrier.html": ' class="pn-hero-note pn-hero-note--inset" style="--pnn-inset:4vw"',
    "discovery-supper-club-at-home.html": ' class="pn-hero-note pn-hero-note--inset" style="--pnn-inset:5vw"',
    "discovery-natural-swimming-garden.html": ' class="pn-hero-note pn-hero-note--centre"',
}
FIG = re.compile(r'<figure class="pn-compare pn-compare--hero"[\s\S]*?</figure>')


def apply(t, note, attrs=' class="pn-hero-note"'):
    fig = FIG.search(t).group(0)
    nf = re.sub(r'\n[ \t]*<p class="pn-compare__ai"[^>]*>[^<]*</p>', '', fig)
    if '<p class="pn-compare__note">' not in nf:
        i = nf.rindex("</figure>")
        nf = nf[:i].rstrip(" ") + '    <p class="pn-compare__note">%s</p>\n  </figure>' % note + nf[i + len("</figure>"):]
    t = t.replace(fig, nf, 1)
    if 'class="pn-hero-note' not in t:
        end = t.index("</header>", t.index("pn-compare--hero"))
        t = t[:end] + '</header>\n<p%s>%s</p>' % (attrs, note) + t[end + len("</header>"):]
    else:
        t = re.sub(r'<p class="pn-hero-note[^"]*"(?: style="[^"]*")?>', '<p%s>' % attrs, t, count=1)
    return re.sub(r'pn-compare\.css\?v=1\.[0-3]"', 'pn-compare.css?v=1.4"', t)


def ok(t, note):
    fig = FIG.search(t).group(0)
    return ("pn-compare__ai" not in fig and fig.count('<p class="pn-compare__note">%s</p>' % note) == 1
            and len(re.findall(r'<p class="pn-hero-note[^>]*>%s</p>' % re.escape(note), t)) == 1 and "pn-compare.css?v=1.4" in t)


def main():
    bad = []
    for name, note in PAGES.items():
        p = ROOT / name
        t = p.read_text(encoding="utf-8")
        if CHECK:
            if not ok(t, note) or apply(t, note, ALIGN.get(name, ' class="pn-hero-note"')) != t: bad.append(name)
            continue
        n = apply(t, note, ALIGN.get(name, ' class="pn-hero-note"'))
        if n != t:
            p.write_text(n, encoding="utf-8"); print("updated: " + name)
    if CHECK:
        print("AI DISCLOSURE BELOW · " + ("OK on %d pages" % len(PAGES) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
