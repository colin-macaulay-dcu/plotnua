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
DESC = ("Independent art service providers in Ireland: specialist art transport, artwork collection and delivery, "
        "installation, and professional artwork hanging. Contact each provider directly.")

# Providers, in page order. "publish": False keeps a provider's listing in the source but off the page. A provider shows
# its own photograph and logo only with written image permission ("photo"/"logo"); otherwise a plain panel ("placeholder").
# More providers: add an entry here; the grid takes any number (two across, one on narrow screens). No prices appear on this page (Hang-It asked for its pricing to be removed,
# 19 Nov 2026); the launch guard refuses any euro price here.
IMG = ROOT / "atlas-tools" / "plotart-services" / "images"
PROVIDERS = [
    # Maurice Ward, restored 22 Nov 2026 (founder brief): text-only. Listing agreed in writing 19 Nov 2026 (Nicola Carragher,
    # with the email address and website to use); the company declined the use of its photograph the same day, so no
    # Maurice Ward photograph or logo is used. "placeholder": a plain PlotArt panel in place of an image (no provider imagery).
    {"key": "mw", "publish": True, "name": "Maurice Ward Art Handling",
     "placeholder": "Art transport and installation",
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
    # FastLane Couriers, added 22 Nov 2026 (founder brief): the owner, Joseph Collins, agreed to be listed and supplied the
    # logo and the branded-van photograph for this listing (image-rights-records.json ORG-FASTLANE / IPO-FASTLANE-20261122).
    # Independent provider: no partner wording, no insurance, qualifications, guarantees or prices.
    {"key": "fl", "publish": True, "name": "FastLane Couriers",
     "what": "Same-day, express and scheduled collection and delivery.",
     # supplied photograph 1077 px wide: copies are never enlarged, so the large size is 1077 (not 1600)
     "photo": {"dir": "fastlane", "stem": "fastlane-van", "big": 1077, "w": 1077, "h": 718, "credit": "Photo: FastLane Couriers",
               "alt": "A white FastLane Couriers van with orange and navy branding parked on a Dublin street"},
     "logo": {"dir": "fastlane", "file": "fastlane-logo.png", "w": 588, "h": 130, "alt": "FastLane Couriers",
              "plaque": "white"},
     "accent": "#E8772E",
     "facts": [("Area", "Throughout Dublin. Nationwide deliveries by arrangement."),
               ("Enquiries", "Welcomes enquiries from artists, galleries and art buyers seeking flexible transport."),
               ("Quotations", "Contact FastLane Couriers directly for a quotation.")],
     # website button restored 23 Nov 2026 (founder): site operational again (withheld 22 Nov while it showed a holding page)
     "links": [("https://www.fastlanecouriers.com", "Visit Website / Request a Quote", "services_fastlane_web", True),
               ("mailto:info@fastlanecouriers.com", "Email info@fastlanecouriers.com", "services_fastlane_email", False),
               ("tel:+35319081167", "Call 01 908 1167", "services_fastlane_phone", False),
               ("https://wa.me/353851402487", "WhatsApp 085 140 2487", "services_fastlane_whatsapp", "wa")]},
    # DropBy, prepared 24 Nov 2026 (founder brief): an Irish delivery marketplace preparing to launch in Dublin; co-founder
    # Cristian confirmed interest in being listed. Text-only until DropBy supplies approved imagery (none requested from the web).
    # AT LAUNCH: delete "status", reword or drop the "Watch this space" fact, add contact/booking links, update "Area".
    # No partner wording, bookings, prices, insurance, qualifications, launch date or present-tense nationwide coverage.
    {"key": "db", "publish": True, "name": "DropBy",
     "status": "Launching Soon",
     # image (25 Nov 2026): DropBy's own promotional graphic, sent by Cristian "which you can use" (image-rights-records.json
     # ORG-DROPBY / IPO-DROPBY-20261125); hosted as a 16:9 band (logo, wordmark, strapline, tagline), declared as Logo
     "photo": {"dir": "dropby", "stem": "dropby-promo", "big": 1284, "w": 1284, "h": 722, "credit": "Image: DropBy", "kind": "Logo",
               "alt": "DropBy logo and wordmark with the strapline Same-Day and Next-Day Delivery"},
     "what": "A new Irish same-day and next-day delivery marketplace.",
     "about": "Connecting individuals and businesses with independent couriers using bicycles, cars and vans.",
     "facts": [("Area", "Launching initially in Dublin, with plans to expand across Ireland."),
               ("Artwork deliveries", "Same-day and next-day delivery options, subject to artwork dimensions, value, "
                                      "packaging and handling requirements."),
               ("Watch this space", "An exciting new Irish delivery marketplace preparing for its official launch.")],
     "links": [("https://www.dropbycouriers.com/", "Discover DropBy", "services_dropby_web", True)]},
    # N.I. Couriers, added 25 Nov 2026 (founder brief): Michael Murphy authorised the listing by email the same day
    # ("Fell free to add our details.") — Atlas Organisation ORG-NICOURIERS (recIy6hMan7ytOVz8). Text-only: no image
    # permission yet. Website, telephone, coverage and imagery requested; add them when supplied. Overnight parcel
    # services are discontinued — never advertise them. No insurance, art-handling experience, nationwide availability or prices.
    {"key": "ni", "publish": True, "name": "N.I. Couriers",
     "placeholder": "Dedicated same-day delivery",
     "what": "Dedicated same-day, direct-drive and time-critical delivery services.",
     "facts": [("Area", "Based in County Antrim, Northern Ireland. Contact N.I. Couriers directly to discuss delivery "
                        "destinations and geographical coverage."),
               ("Delivery services", "Dedicated same-day, direct-drive transport for time-critical deliveries."),
               ("Artwork deliveries", "Contact N.I. Couriers directly to discuss artwork transport and individual "
                                      "handling requirements."),
               ("Quotations", "Contact N.I. Couriers directly for a quotation.")],
     "links": [("mailto:michael@nicouriers.com", "Email michael@nicouriers.com", "services_nicouriers_email", False)]},
]


def assets():
    """(source, published path) for every image a published provider shows."""
    out = []
    for p in PROVIDERS:
        if not p["publish"]:
            continue
        if "photo" in p:
            ph = p["photo"]
            big = ph.get("big", 1600)
            for suf in ("-%d.jpg" % big, "-%d.webp" % big, "-800.webp"):
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
                 '<source type="image/webp" srcset="%(b)s-800.webp 800w, %(b)s-%(big)d.webp %(big)dw" sizes="(max-width:900px) 100vw, 46vw">'
                 '<img src="%(b)s-%(big)d.jpg" width="%(w)d" height="%(h)d" alt="%(alt)s" data-kind="%(kind)s" loading="lazy" decoding="async"></picture>'
                 '<figcaption>%(credit)s</figcaption></figure>') % dict(b=base, big=ph.get("big", 1600), w=ph["w"], h=ph["h"], alt=ph["alt"],
                                                                      credit=ph["credit"], kind=ph.get("kind", "Photograph"))
    elif "placeholder" in p:
        # a provider without image permission: a quiet anthracite panel with the kind of service in the PlotArt serif;
        # decorative (the provider's name is the card heading), never a photograph, logo or stock image
        media = ('\n    <div class="pa-sv-media pa-sv-media--plain" aria-hidden="true"><span>%s</span></div>' % p["placeholder"])
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
    # optional, for a provider not yet operating (24 Nov 2026, DropBy): a small status label above the name, and a short
    # description paragraph; both are omitted for every other provider, so their markup is unchanged
    status = '\n    <p class="pa-sv-status">%s</p>' % e(p["status"]) if p.get("status") else ""
    about = '\n    <p class="pa-sv-about">%s</p>' % e(p["about"]) if p.get("about") else ""
    return ('  <article class="%s"%s aria-labelledby="%s">%s\n    <div class="pa-sv-body">%s%s\n    <h2 id="%s">%s</h2>\n'
            '    <p class="pa-sv-what">%s</p>%s\n    <dl class="pa-sv-facts">\n%s\n    </dl>\n    <p class="pa-sv-contact">\n%s\n    </p>\n    </div>\n  </article>'
            % (cls, style, hid, media, logo, status, hid, e(p["name"]), e(p["what"]), about, facts, "\n".join(links)))


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
