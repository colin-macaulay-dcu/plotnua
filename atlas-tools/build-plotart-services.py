#!/usr/bin/env python3
"""Build/check the PlotArt "Art Services & Providers" page (plotart/services.html, founder brief 19 Nov 2026).

A plain, restrained listing of independent providers who have explicitly agreed to be listed on PlotArt. They are not
partners, PlotArt does not arrange, supervise or guarantee their work, and customers arrange quotations, services and
insurance directly with them. No logos or provider photographs (no image permissions held). Details are as supplied by
each provider (founder brief); the prices are the provider's own and are the only prices this page may show.

  python3 atlas-tools/build-plotart-services.py            build plotart/services.html
  python3 atlas-tools/build-plotart-services.py --check    write nothing; refuse if the page differs

PAUSED 19 Nov 2026 (founder: both providers asked for changes to their listings). The page is built only while the launch
switch services_page is on. Off: the page and its stylesheet must be absent from plotart/ (--check refuses otherwise),
and the build writes nothing. The source stays here: this script and atlas-tools/plotart-services/ (the stylesheet, and
the unpublished photograph-and-logo card design in preview/, whose images await the providers' permission).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import json                 # noqa: E402
import shutil               # noqa: E402
import plotart_shell as S   # noqa: E402

_SW = json.load(open(ROOT / "atlas-tools" / "release" / "plotart-launch-switches.json", encoding="utf-8"))
HIRE = _SW.get("art_for_hire_page") is True
ON = _SW.get("services_page") is True        # paused 19 Nov 2026 (off)
CSS_SRC = ROOT / "atlas-tools" / "plotart-services" / "plotart-services.css"
CSS_OUT = ROOT / "plotart" / "assets" / "plotart-services.css"

PATH = "services.html"
TITLE = "Art Services & Providers | PlotArt"
DESC = ("Independent art handling and picture hanging providers in Ireland: specialist art transport, delivery and "
        "installation, and professional artwork hanging. Contact each provider directly.")

# Providers, in page order. "publish": False keeps a provider's listing in the source but off the page (Maurice Ward,
# 19 Nov 2026: amendments outstanding). No prices appear on this page (Hang-It asked for its pricing to be removed,
# 19 Nov 2026); the launch guard refuses any euro price here.
IMG = ROOT / "atlas-tools" / "plotart-services" / "images"
PROVIDERS = [
    {"key": "mw", "publish": False, "name": "Maurice Ward Art Handling",
     "what": "Specialist art transport, delivery, unpacking and installation.",
     "facts": [("Quotations", "Each job is quoted individually."),
               ("Insurance", "Transit insurance is arranged separately, by you.")],
     "links": [("https://mauriceward-arthandling.com/", "Website", "services_mauriceward_web", True),
               ("mailto:movingart@mauriceward.com", "Email movingart@mauriceward.com", "services_mauriceward_email", False)]},
    {"key": "hi", "publish": True, "name": "Hang-It",
     "what": "Professional artwork and picture hanging and installation.",
     # images: Hang-It's written permission, 19 Nov 2026 (image-rights-records.json ORG-HANGIT / IPO-HANGIT-20261119)
     "photo": {"dir": "hang-it", "stem": "hang-it-hung-wall", "w": 1600, "h": 900, "credit": "Photo: Hang-It",
               "alt": "A row of framed photographs hung level along a living-room wall"},
     "logo": {"dir": "hang-it", "file": "hang-it-logo.png", "w": 474, "h": 130, "alt": "Hang-It, The Hanging Specialists",
              "plaque": "dark"},
     "accent": "#EDEBE7",
     "facts": [("Area", "Mainly Dublin. Other areas may be possible by arrangement."),
               ("Quotations", "Contact Hang-It directly for a quotation."),
               ("Insurance", "Fully insured, according to Hang-It."),
               ("Please note", "Hang-It doesn’t transport artwork.")],
     "links": [("https://www.hangit.ie/", "Website", "services_hangit_web", True),
               ("https://wa.me/353876634458", "WhatsApp 087 663 4458", "services_hangit_whatsapp", "wa")]},
]


def assets():
    """(source, published path) for every image a published provider shows."""
    out = []
    for p in PROVIDERS:
        if not p["publish"]:
            continue
        if "photo" in p:
            ph = p["photo"]
            for suf in ("-1600.jpg", "-1600.webp", "-800.webp"):
                out.append((IMG / ph["dir"] / (ph["stem"] + suf), "assets/services/" + ph["stem"] + suf))
        if "logo" in p:
            out.append((IMG / p["logo"]["dir"] / p["logo"]["file"], "assets/services/" + p["logo"]["file"]))
    return out


def card(p):
    e = lambda t: t.replace("&", "&amp;")
    hid = "sv" + p["key"].upper()
    media = ""
    if "photo" in p:
        ph = p["photo"]; base = "assets/services/" + ph["stem"]
        media = ('\n    <figure class="pa-sv-media"><picture>'
                 '<source type="image/webp" srcset="%(b)s-800.webp 800w, %(b)s-1600.webp 1600w" sizes="(max-width:900px) 100vw, 46vw">'
                 '<img src="%(b)s-1600.jpg" width="%(w)d" height="%(h)d" alt="%(alt)s" data-kind="Photograph" loading="lazy" decoding="async"></picture>'
                 '<figcaption>%(credit)s</figcaption></figure>') % dict(b=base, w=ph["w"], h=ph["h"], alt=ph["alt"], credit=ph["credit"])
    logo = ""
    if "logo" in p:
        lg = p["logo"]
        logo = ('\n    <span class="pa-sv-logo pa-sv-logo--%s"><img src="assets/services/%s" width="%d" height="%d" alt="%s logo" data-kind="Logo"></span>'
                % (lg["plaque"], lg["file"], lg["w"], lg["h"], lg["alt"]))
    facts = "\n".join('      <dt>%s</dt><dd>%s</dd>' % (e(k), e(v)) for k, v in p["facts"])
    links = []
    for href, label, track, ext in p["links"]:
        attrs = ' rel="noopener" target="_blank"' if ext else ""
        sr = '<span class="pa-sr"> (opens WhatsApp)</span>' if ext == "wa" else ('<span class="pa-sr"> (opens in a new tab)</span>' if ext else "")
        arrow = ' <span aria-hidden="true">↗</span>' if ext is True else ""
        links.append('      <a class="pa-btn pa-btn--ghost" href="%s"%s data-pa-track="%s">%s%s%s</a>' % (href, attrs, track, label, arrow, sr))
    cls = "pa-sv-card pa-sv-card--%s%s" % (p["key"], " pa-sv-card--media" if media else "")
    style = ' style="--sv-accent:%s"' % p["accent"] if p.get("accent") else ""
    return ('  <article class="%s"%s aria-labelledby="%s">%s\n    <div class="pa-sv-body">%s\n    <h2 id="%s">%s</h2>\n'
            '    <p class="pa-sv-what">%s</p>\n    <dl class="pa-sv-facts">\n%s\n    </dl>\n    <p class="pa-sv-contact">\n%s\n    </p>\n    </div>\n  </article>'
            % (cls, style, hid, media, logo, hid, e(p["name"]), e(p["what"]), facts, "\n".join(links)))


LISTED = [p for p in PROVIDERS if p["publish"]]
BODY = """
<section class="pa-sec pa-sec--deep pa-sv-hero" aria-labelledby="svH"><div class="pa-wrap">
  <p class="pa-eyebrow">PlotArt · Services</p>
  <h1 id="svH">Art Services &amp; Providers</h1>
  <p class="pa-lede">Independent specialists who can help once you’ve chosen a work: moving it safely, and hanging it well.</p>
  <p class="pa-sv-note">These independent providers have agreed to be listed on PlotArt. Please contact them directly to discuss services, quotations and insurance. PlotArt does not arrange or guarantee their work.</p>
</div></section>

<section class="pa-sec pa-sv-sec" aria-label="Providers"><div class="pa-wrap pa-sv-list%s">

%s

</div></section>

<section class="pa-sec pa-sv-sec pa-sv-foot"><div class="pa-wrap">
  <p>Details are as supplied by each provider and may change, so please confirm them directly. Listing a provider isn’t a recommendation for any particular job, and other providers may be listed in future.</p>
</div></section>
""" % (" pa-sv-list--one" if len(LISTED) == 1 else "", "\n\n".join(card(p) for p in LISTED))


FINE = ("Artworks in PlotArt galleries are offered by their artists: PlotArt introduces buyers; the artist is the seller. "
        "Providers listed on this page are independent businesses, not PlotArt partners, and PlotArt doesn't guarantee their services.")


def render():
    return S.artist_page(PATH, TITLE, DESC, BODY, current="services", hire_nav=HIRE, fine=FINE, styles=("assets/plotart-services.css",), services_nav=True)[1]


def write_site(base):
    """Write the page, its stylesheet and its provider images into the site at `base` (a checkout or a preview copy)."""
    (base / "plotart" / PATH).write_text(render(), encoding="utf-8")
    shutil.copyfile(CSS_SRC, base / "plotart" / "assets" / "plotart-services.css")
    (base / "plotart" / "assets" / "services").mkdir(parents=True, exist_ok=True)
    for src, rel in assets():
        shutil.copyfile(src, base / "plotart" / rel)


def main():
    page = ROOT / "plotart" / PATH
    imgdir = ROOT / "plotart" / "assets" / "services"
    if "--preview" in sys.argv:              # a review copy of the site, never the checkout; ignores the switch
        dest = Path(sys.argv[sys.argv.index("--preview") + 1]).resolve()
        if dest == ROOT or ROOT in dest.parents:
            raise SystemExit("SERVICES · --preview must write outside the repository")
        write_site(dest)
        print("SERVICES · preview written to %s (not the public site)" % dest)
        return
    if not ON:
        if page.exists() or CSS_OUT.exists() or imgdir.exists():
            raise SystemExit("SERVICES · paused (services_page off), but plotart/%s, its stylesheet or its images are still in the public site" % PATH)
        print("SERVICES · paused (services_page off): page, stylesheet and images absent from plotart/; nothing written")
        return
    want = render()
    if "--check" in sys.argv:
        if not CSS_OUT.exists() or CSS_OUT.read_bytes() != CSS_SRC.read_bytes():
            raise SystemExit("SERVICES · plotart/assets/plotart-services.css differs from its source")
        for src, rel in assets():
            if not (ROOT / "plotart" / rel).exists() or (ROOT / "plotart" / rel).read_bytes() != src.read_bytes():
                raise SystemExit("SERVICES · plotart/%s differs from its source copy" % rel)
        extra = sorted(set(f.name for f in imgdir.iterdir()) - set(Path(r).name for _, r in assets())) if imgdir.exists() else []
        if extra:
            raise SystemExit("SERVICES · images no listing uses: %s" % ", ".join(extra))
        if not page.exists() or page.read_text(encoding="utf-8") != want:
            raise SystemExit("SERVICES · plotart/%s differs from its reviewed source (rebuild and review)" % PATH)
        print("SERVICES · OK — plotart/%s matches its source; nothing written" % PATH)
        return
    write_site(ROOT)
    print("SERVICES · built plotart/%s" % PATH)


if __name__ == "__main__":
    main()
