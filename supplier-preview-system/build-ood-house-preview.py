#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER — THE ÖÖD HOUSE PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
VARIANT:  B, provider-led

WHY PROVIDER-LED, with seven products in Atlas. ÖÖD publish a range of
houses and saunas, not one product, so SUPPLIER-PREVIEW-SYSTEM-V1 §1 puts it
in variant B. The demonstration is still ONE production Results card; the
seven Atlas houses are seven fillings of that same card, switched by a row of
model names above the frame, so ÖÖD see each of their own houses as a
homeowner would and the frozen seven-part structure is unchanged.

FIRST-PARTY EVIDENCE, read 14 October 2026:
    https://oodhouse.com/en-gb/products/houses/*   dimensions, inclusions
    https://oodhouse.com/en/products/houses/*      euro prices
    https://oodhouse.com/en/products/saunas/*      euro prices, saunas
    https://oodhouse.com/en-gb/faq                 transport, permits, utilities
    https://oodhouse.com/en-gb/terms-of-service    "All prices ... are indicative"

    The en-gb Mobile House page returns 404; Mobile House is read from the
    euro site only. UK sterling prices are NOT used anywhere on this page
    (guard G12), because a UK price is not an Irish price.

ATLAS (all seven ELIGIBLE — WITH CAVEAT, Irish availability unconfirmed):
    ORG-000149   ÖÖD House             rec2URqKyVwlhHSBw
    PROD-000510  Signature House       recoQZlqmpfv3T5bz   €84,900   21.1 m²
    PROD-000509  Glämping House        recyc7vNON16NzYFD   €29,700    9 m²
    PROD-000512  Extended House        recGGCVFmV7lY1zkj   €94,900   26.3 m²
    PROD-000511  Mobile House          reczasgBzBbqP1lBg   €89,900   21.1 m²
    PROD-000514  Glääzy House          recl9ITOz7WlqPPBn   €139,900  26.7 m²
    PROD-000515  Möön House            reciFE98KRWuAhBwP   €139,900  26.7 m²
    PROD-000513  The Big Monolith      recPWKdUbLnAvXxmU   €149,900  40.9 m²

    The three saunas are NOT Atlas products and no PlotNua surface lists
    sauna makers today, so they are shown below the frame as "also in your
    range", never inside the Results card.

IMAGERY — STATE A, AUTHORISED.
    Gertrud Ots, Head of Marketing, gertrud@oodhouse.com, Gmail thread
    1a088713c8eccf73, message 1a139105565814d0, 14 October 2026 06:18 UTC,
    supplied ÖÖD's photo library organised by product in reply to PlotNua's
    permission request. Atlas IPO-007 (recqvHdcTwNdBRszM). Rights record in
    image-rights-records.json, scoped PER FILE on lh3.googleusercontent.com
    (/d/<Drive file id>=), never a bare host. Every image here is hot-linked
    unmodified from ÖÖD's own Drive files; nothing is downloaded or rehosted.
    Each image is used only for the model named by ÖÖD's own folder. The
    "Medium Office" folder holds Glämping House images and is not used.

Run: python3 build-ood-house-preview.py [--stage]
"""
import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/ood-house-preview.html") if STAGE
       else SITE / "ood-house-preview.html")

SUPPLIER = "ÖÖD House"
SUPPLIER_SHORT = "ÖÖD"
DATE = "14 October 2026"
PERMISSION_DATE = "14 October 2026"
CREDIT = "ÖÖD House"                    # required_credit in the rights record
IMG_HOST = "https://lh3.googleusercontent.com/d/"
DRIVE_ID = re.compile(r"^[A-Za-z0-9_-]{25,44}$")
LOCALITY = "Co. Wicklow"


def img(fid, alt, photo=None, place=None):
    return {"id": fid, "alt": alt, "photo": photo, "place": place}


# Price basis, identical for every house: what the figure is and, just as
# important, what it is not. No VAT claim -- ÖÖD do not state it.
PRICE_BASIS = ("As published on ÖÖD&rsquo;s euro site, for the house itself. "
               "Transport, foundations and service connections are arranged "
               "separately, and VAT isn&rsquo;t stated.")
IRISH_FACT = "Delivery to the Republic of Ireland: still to be confirmed by ÖÖD"
CHECK_COMMON = ("transport, groundworks and connections are arranged by the "
                "buyer, so the cost delivered and connected in Ireland will be "
                "higher than the published price; and the planning position "
                "depends on its size and how it&rsquo;s used.")

HOUSES = [
    {"key": "signature", "name": "Signature House", "price": "&euro;84,900",
     "url": "https://oodhouse.com/en-gb/products/houses/signature-house",
     "area": "21.1 m&sup2;", "size": "6.40 &times; 3.40 m, 3.35 m high",
     "f3": "Full steel frame with 200 mm insulation and argon-filled mirror "
           "glass; electric floor heating",
     "f4": "Kitchenette and a bathroom with Villeroy &amp; Boch and Grohe "
           "fittings; plug-and-play power, water and sewage connections",
     "check": CHECK_COMMON,
     "images": [
        img("1zfB24bun-dr7Smh0ZeFSX_OaNVDh6DMX", "Signature House among "
            "lupins and trees, its mirrored walls reflecting the sky",
            "Katherine Berke", "Vermont Glass House, USA"),
        img("1Bz95Xl1AzKeEI84zBbMBpGW_xDOwT9y0", "Signature House on a timber "
            "deck with loungers, mirrored glass reflecting pine trees",
            "Valmarifoto", "Pilguse, Estonia"),
        img("1vmuC_8SoSGh569AfqkKwdffpoSoFQ6-i", "Signature House at sunset "
            "on open grassland beside a small timber sauna", None,
            "Roosisaare, Estonia"),
        img("1DgirwuCSVsqIVR-Gjh2vsLshp_KiIZkG", "Inside a Signature House: "
            "bed, kitchenette and floor-to-ceiling glass onto trees",
            "Ragnar Hartvig", "Furu, Norway"),
     ]},
    {"key": "glamping", "name": "Glämping House", "price": "&euro;29,700",
     "url": "https://oodhouse.com/en-gb/products/houses/glamping-house",
     "area": "9 m&sup2;", "size": "3.90 &times; 2.40 m, 2.75 m high",
     "f3": "Steel frame, aluminium facade, reflective glass and thermo ash "
           "cladding",
     "f4": "A bedroom with floor heating; ÖÖD publish no kitchen or "
           "bathroom for this model",
     "check": "ÖÖD publish it as a glamping cabin, so how it would be used "
              "matters for planning; transport, groundworks and connections "
              "are arranged by the buyer, so the cost delivered in Ireland "
              "will be higher than the published price.",
     "images": [
        img("1yfaBudGFv1m7K98RfozvxlZzV-g1Ksio", "Glämping House on a timber "
            "deck in high desert at sunrise, with a telescope outside",
            "Marcario Photo", "Starry Nights Glamping, Arizona, USA"),
        img("1ob8p3n_CpDwJXh4SNSgImKA_h-kWF0xJ", "Glämping House under a "
            "starry sky on a timber deck with two chairs", None,
            "Starry Nights Glamping, Arizona, USA"),
        img("1o0i2YfvE8Kc9tLH_mZwGADXbiXzJuHB_", "Glämping House lit from "
            "within at night, the bedroom visible through the glass", None,
            "Starry Nights Glamping, Arizona, USA"),
        img("1GvCJ4OCDAn9NgQ6W4jwjlyfIpyV9ZwKv", "Glämping House seen from a "
            "distance across open scrubland, showing its scale",
            "Marcario Photo", "Starry Nights Glamping, Arizona, USA"),
     ]},
    {"key": "extended", "name": "Extended House", "price": "&euro;94,900",
     "url": "https://oodhouse.com/en-gb/products/houses/extended-house",
     "area": "26.3 m&sup2;", "size": "7.95 &times; 3.40 m, 3.35 m high",
     "f3": "The Signature House stretched by one full glass panel, with a "
           "3.4 m&sup2; bathroom",
     "f4": "Steel frame, aluminium facade, reflective glass and thermo ash "
           "cladding; about 12 tonnes",
     "check": CHECK_COMMON,
     "images": [
        img("1LNGkuROBSI4edwkw0FM9S6EJieOrsZg5", "Extended House with its "
            "long mirrored side reflecting dark hills and cloud"),
        img("1uCwtWOKNIG_xXoEy7yMPgbRKNPXCfNGa", "A timber-clad Extended "
            "House on a boardwalk in an open volcanic landscape"),
        img("1ZF7sYK4WvnXQD_7gUzruD6eT6O1vEzZI", "Extended House on a "
            "boardwalk among lava fields, with a mountain behind", None,
            "Hekla Horizon, Iceland"),
        img("10XNiu4r28DOUPflIOknPDNmM3wJOPx7Y", "Inside an Extended House: "
            "a long room with a table, kitchen and glass along one side"),
     ]},
    {"key": "mobile", "name": "Mobile House", "price": "&euro;89,900",
     "url": "https://oodhouse.com/en/products/houses/mobile-house",
     "area": "21.1 m&sup2;", "size": "6.40 &times; 3.40 m, 3.35 m high",
     "f3": "The Signature House on a wheeled chassis, which ÖÖD say can let "
           "it be classed as a mobile dwelling in some places",
     "f4": "Rests on prepared supports such as concrete pads or screw piles "
           "rather than a poured slab",
     "check": "how Irish rules would treat a house on a chassis needs "
              "checking for the particular site; transport, groundworks and "
              "connections are arranged by the buyer, so the cost delivered "
              "in Ireland will be higher than the published price.",
     "images": [
        img("1RekoPNxkpfEus5BoFLXNHGhDvAkwz0ar", "Mobile House among pine "
            "trees beside a timber deck with red chairs"),
        img("1-s3JU-5MhvXYPrKEWYlW2Qhhhwe3RXIM", "The mirrored end of a "
            "Mobile House beyond its deck, reflecting the woodland"),
        img("1NxvKE77I0ENDH75o3kki2Bs7J0z-Yfmh", "Inside a Mobile House: a "
            "bed and table beside full-height glass onto the trees"),
     ]},
    {"key": "glaazy", "name": "Glääzy House", "price": "&euro;139,900",
     "url": "https://oodhouse.com/en-gb/products/houses/glaazy-house",
     "area": "26.7 m&sup2;", "size": "7.95 &times; 3.54 m, 3.85 m high",
     "f3": "A glass roof and three walls of floor-to-ceiling glass",
     "f4": "Part of ÖÖD&rsquo;s custom collection, produced in the EU; "
           "about 13.5 tonnes",
     "check": CHECK_COMMON,
     "images": [
        img("1XIBfJ7rSHrjjFLlvpmTyWLo99A33bnlq", "Glääzy House with its "
            "pitched glass end among low trees and heather"),
        img("1ejJG2ntzGHxim7ht-NtypqpBJ06ydomW", "Glääzy House from a lower "
            "angle, dark cladding and mirrored glass in scrubland"),
        img("1mOp5MeibJ5j6fCUivqfj_3wlCZsjpG1F", "Glääzy House lit from "
            "within at dusk in a snowy landscape", None, "Norway"),
        img("1WZrrO7P28dYuSZhGfM_MDotq_-0q6J20", "Looking up from the bed in "
            "a Glääzy House through its glass roof and gable",
            "Even Tryggstrand", "WonderInn Arctic, Norway"),
     ]},
    {"key": "moon", "name": "Möön House", "price": "&euro;139,900",
     "url": "https://oodhouse.com/en-gb/products/houses/moon-house",
     "area": "26.7 m&sup2;", "size": "7.95 &times; 3.54 m, 3.85 m high",
     "f3": "An extended glass facade for more light and views of the sky",
     "f4": "Part of ÖÖD&rsquo;s custom collection, produced in the EU; "
           "about 13.5 tonnes",
     "check": CHECK_COMMON,
     "images": [
        img("1V0G-aX7veOinUIDuqn4poqjmMTO2GgzF", "Möön House with a "
            "full-height glass corner, curtains drawn back, on open moorland"),
        img("1PmSreci2uYbdaBxpwUnzz9EdynTUWJGk", "Möön House from above on "
            "a dark deck in green moorland"),
        img("1OrRzUbCQ02bhxDk5--mPR6KDFUIrIzy2", "Möön House and a small "
            "sauna seen from above beside a gravel track"),
        img("14OqokuAczh_R0finpF-szBWogsOrVd48", "Möön House under a cloudy "
            "sky, glass on two sides and dark cladding"),
        img("1Du2PTFM9Ggb_QU9iWZcxOb0uxy-AEBPx", "Inside a Möön House: a "
            "glass corner looking out across open landscape"),
     ]},
    {"key": "monolith", "name": "The Big Monolith", "price": "&euro;149,900",
     "url": "https://oodhouse.com/en-gb/products/houses/the-big-monolith",
     "area": "40.9 m&sup2;", "size": "11.10 &times; 3.70 m, 3.40 m high",
     "f3": "One or two bedrooms; ÖÖD describe it as a guest home, pool "
           "house, creative space or short-term rental",
     "f4": "Steel frame, aluminium facade, reflective glass and thermo ash "
           "cladding; about 19 tonnes",
     "check": CHECK_COMMON,
     "images": [
        img("1FZqxVCAG_jNbx5bpOzAcG58o1hV2NAW0", "The Big Monolith on mossy "
            "ground, its long mirrored side reflecting cloud and hills"),
        img("17Odd2cNOaEQoEjI584ut6cqI8qFqNVJS", "The Big Monolith in snow, "
            "its glass reflecting a mountain"),
        img("1V7_11MkyiQ-8doHTyyIi2ywM2wu00FkK", "The Big Monolith and a "
            "smaller unit in a wide snowy landscape, showing its length"),
        img("1CKxn4Aw9mWNQUoq_QHsuixi7tiiewQ7s", "Inside The Big Monolith: a "
            "bedroom with glass walls onto the landscape",
            "Ingibergur Thor", "Hekla Horizon, Iceland"),
     ]},
]

SAUNAS = [
    {"name": "Mini Sauna", "price": "&euro;23,900", "area": "5.5 m&sup2;",
     "url": "https://oodhouse.com/en-gb/products/saunas/mini-sauna",
     "image": img("19wfqQGI8YTnaGoKndiJc-F_m1Xv-GgRB", "Mini Sauna in a pine "
                  "forest with a timber walkway to the door",
                  "Oliver Soostar", "Rooslepa, Estonia")},
    {"name": "Medium Sauna", "price": "&euro;33,700", "area": "9.5 m&sup2;",
     "url": "https://oodhouse.com/en-gb/products/saunas/medium-sauna",
     "image": img("1exBx3pdtmh0AhYacPVMkK5kllB9qGnh5", "Medium Sauna with "
                  "timber cladding and a mirrored end on a lawn by water",
                  "Ammon Cluff")},
    {"name": "Large Sauna", "price": "&euro;84,900", "area": "21.1 m&sup2;",
     "url": "https://oodhouse.com/en-gb/products/saunas/large-sauna",
     "image": img("1cOZjC0XjnmPlAGcAp_2fTpfhISOMncB7", "Large Sauna with "
                  "mirrored walls on a pier over open water")},
]

FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "DEMO_HEADING": "How an Irish homeowner would meet ÖÖD",
    # The certified lede, word for word as on every Variant B preview.
    "DEMO_LEDE": "This is a shortened example of the Results "
                 "experience &mdash; a homeowner would see additional "
                 "property-specific checks, comparison information and "
                 "supporting detail as they continue through PlotNua.",
    "WHY_1_LABEL": "MORE CONTEXT",
    "WHY_1_TEXT": "By the time someone reaches you they&rsquo;ve already "
                  "looked at what would fit their garden, the planning "
                  "question and roughly what they can spend.",
    "WHY_2_LABEL": "CLEARER INTENT",
    "WHY_2_TEXT": "A house from &euro;29,700 to &euro;149,900, before "
                  "transport and groundworks, is a considered purchase. "
                  "We&rsquo;d rather send you a few people who&rsquo;ve "
                  "thought it through than lots who haven&rsquo;t.",
    "WHY_3_LABEL": "A BETTER STARTING POINT",
    "WHY_3_TEXT": "Your sizes and published prices are already in front of "
                  "them, so the first conversation can be about their site "
                  "and getting the house there.",
    "CLOSING_PROPOSITION": "Could ÖÖD houses be delivered and installed in "
                           "the Republic of Ireland?",
    "CLOSING_SUPPORT": "It&rsquo;s the one thing we can&rsquo;t yet tell "
                       "Irish homeowners. Once we know how delivery, "
                       "groundworks and connections would work here, we can "
                       "set out plainly what to expect beyond the published "
                       "price.",
    "DATE": DATE,
}

OTHER_SUPPLIERS = ("Hutsmith", "Yard Box", "Power Sheds", "Powersheds", "TRIQ",
                   "Superior Pergola", "BIOBUILDS", "Iglucraft", "Modulux",
                   "Dudley", "Cormac", "Tanktribe", "OGNYX")
RELATIONSHIP_WORDS = ("partner", "approved supplier", "recommended", "trusted "
                      "supplier", "preferred supplier", "endorsed",
                      "testimonial", "official stockist")
IRISH_OVERCLAIMS = ("delivers to ireland", "available in ireland",
                    "installed in ireland", "irish installation",
                    "irish installer", "delivery to ireland confirmed",
                    "lough neagh", "northern ireland")


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def src_url(fid, width):
    return "%s%s=w%d" % (IMG_HOST, fid, width)


def credit_of(i):
    """The required credit always leads; a named photographer follows."""
    c = CREDIT
    if i.get("photo"):
        c += " · Photo: " + i["photo"]
    return c


def alt_of(house_name, i):
    a = i["alt"]
    if i.get("place"):
        a += " (" + i["place"] + ")"
    return html.escape(a, quote=True)


def gallery(house):
    every = house["images"]
    hero = every[0]
    out = ['        <div class="results-hero-media has-pn-gallery">',
           '          <img src="%s" alt="%s" loading="lazy" decoding="async">'
           % (src_url(hero["id"], 1600), alt_of(house["name"], hero)),
           '          <span class="pn-image-credit">%s</span>'
           % html.escape(credit_of(hero)),
           '        </div>',
           '        <div class="pn-gal-strip">']
    for n, i in enumerate(every):
        out.append('          <button type="button" class="pn-gal-thumb%s" '
                   'aria-pressed="%s" aria-label="View image %d of %d" '
                   'data-full="%s" data-alt="%s" data-credit="%s">'
                   '<img src="%s" alt="" loading="lazy" decoding="async">'
                   '</button>'
                   % (" is-on" if n == 0 else "",
                      "true" if n == 0 else "false", n + 1, len(every),
                      src_url(i["id"], 1600), alt_of(house["name"], i),
                      html.escape(credit_of(i), quote=True),
                      src_url(i["id"], 480)))
    out.append('        </div>')
    return "\n".join(out)


def panel(inner, house, n):
    """One production Results card, filled for one house."""
    p = inner
    slot = re.search(r'        <div class="results-hero-media">\n'
                     r'          <div class="pn-photo-slot"[^>]*>.*?</div>\n'
                     r'        </div>\n', p, re.S)
    if not slot:
        die("the held media wrapper was not found in the Results card.")
    p = p.replace(slot.group(0), gallery(house) + "\n")
    # clipPath ids must stay unique across seven cards.
    if p.count("pnMarkClipSave") != 2:
        die("the Save mark clipPath id is not where the template had it.")
    p = p.replace("pnMarkClipSave", "pnMarkClipSave%d" % n)
    # The secondary link goes to the official product page -- the link back
    # ÖÖD were promised -- rather than the template's dead "#".
    old_link = ('<a class="hero-secondary-link" href="#">Explore with '
                '{{SUPPLIER_SHORT}} &rarr;</a>')
    if p.count(old_link) != 1:
        die("the 'Explore with' link is not in the Results card exactly once.")
    p = p.replace(old_link, '<a class="hero-secondary-link" href="%s" '
                  'target="_blank" rel="noopener">See it on oodhouse.com '
                  '&rarr;</a>' % house["url"])
    fills = {
        "OFFER_NAME": house["name"],
        "SUPPLIER_NAME": SUPPLIER,
        "VERIFIED_PRICE": house["price"],
        "VERIFIED_PRICE_BASIS": PRICE_BASIS,
        "HOMEOWNER_LOCALITY": LOCALITY,
        "PERSONALISATION": "Shown for a homeowner in %s, from the location "
                           "they gave us." % LOCALITY,
        "VERIFIED_FACT_1_LABEL": "Floor area",
        "VERIFIED_FACT_1_VALUE": house["area"],
        "VERIFIED_FACT_2_LABEL": "Outside size",
        "VERIFIED_FACT_2_VALUE": house["size"],
        "VERIFIED_FACT_3": house["f3"],
        "VERIFIED_FACT_4": house["f4"],
        "VERIFIED_FACT_5": IRISH_FACT,
        "THINGS_TO_CHECK": house["check"],
    }
    for k, v in fills.items():
        needle = "{{%s}}" % k
        if needle not in p:
            die("token %s is not in the Results card." % needle)
        p = p.replace(needle, v)
    left = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", p)))
    if left:
        die("unfilled tokens in the %s card: %s" % (house["name"], left))
    open_tag = '      <div class="results-hero-inner">'
    if not p.startswith(open_tag):
        die("the Results card does not open where expected.")
    p = ('      <div class="results-hero-inner ood-panel" id="ood-%s" '
         'role="tabpanel" aria-label="%s"%s>' % (house["key"], house["name"],
                                                 "" if n == 0 else " hidden")
         + p[len(open_tag):])
    return p


TABS_CSS = """
/* ── ÖÖD PREVIEW · model switcher and range strip ─────────────────── */
.ood-tabs{ display:flex; flex-wrap:wrap; gap:8px; margin:0 0 var(--pn-sm); }
.ood-tab{ font:inherit; font-size:var(--pn-w-body-sm); color:var(--pn-voice);
  background:transparent; border:1px solid var(--pn-edge); border-radius:999px;
  padding:7px 14px; cursor:pointer; line-height:1.2; }
.ood-tab:hover{ border-color:var(--pn-voice); }
.ood-tab[aria-selected="true"]{ background:var(--pn-voice); color:var(--pn-on-dark);
  border-color:var(--pn-voice); }
.ood-tab:focus-visible{ outline:2px solid var(--pn-voice); outline-offset:2px; }
.ood-panel[hidden]{ display:none !important; }
.ood-also{ margin-top:var(--pn-lg); }
.ood-also.is-last{ margin-bottom:var(--pn-xl); }
.ood-also h3{ font-size:var(--pn-s-quote); margin:0 0 6px; }
.ood-also > p{ font-size:var(--pn-w-body-sm); margin:0 0 var(--pn-sm); }
.ood-also > p a{ color:var(--pn-voice); }
.ood-range{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }
.ood-card{ background:var(--pn-paper); border:1px solid var(--pn-hair); border-radius:5px;
  overflow:hidden; display:flex; flex-direction:column; }
.ood-card figure{ margin:0; position:relative; aspect-ratio:4/3; background:var(--pn-panel); }
.ood-card figure img{ width:100%; height:100%; object-fit:cover; display:block; }
.ood-card figcaption{ position:absolute; left:0; right:0; bottom:0; padding:16px 10px 6px;
  font-size:10.5px; color:#fff; background:linear-gradient(transparent,rgba(0,0,0,.55)); }
.ood-card-body{ padding:12px 14px 14px; }
.ood-card-body b{ display:block; font-family:'Fraunces',Georgia,serif; font-weight:400;
  font-size:18px; color:var(--pn-voice); }
.ood-card-body span{ font-size:var(--pn-w-body-sm); color:var(--pn-fact); }
.ood-card-body a{ display:inline-block; margin-top:6px; font-size:var(--pn-w-body-sm);
  color:var(--pn-voice); }
.ood-where{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px;
  margin-top:var(--pn-md); }
.ood-where a{ display:block; text-decoration:none; color:inherit; border:1px solid var(--pn-hair);
  border-radius:5px; padding:14px 16px; background:var(--pn-ground); }
.ood-where a:hover{ border-color:var(--pn-voice); }
.ood-where b{ display:block; font-family:'Fraunces',Georgia,serif; font-weight:400;
  font-size:18px; color:var(--pn-voice); margin-bottom:2px; }
.ood-where span{ font-size:var(--pn-w-body-sm); }
@media (max-width:720px){
  .ood-range{ grid-template-columns:1fr; }
  .ood-where{ grid-template-columns:1fr; }
  .ood-tabs{ flex-wrap:nowrap; overflow-x:auto; padding-bottom:4px;
    -webkit-overflow-scrolling:touch; scrollbar-width:thin; }
  .ood-tab{ flex:0 0 auto; }
}
"""

SCRIPT = """<script>
/* ÖÖD PREVIEW — the template's gallery behaviour, per card, plus the model
   switcher. The credit is swapped in the same statement as the picture, so
   it can never part company with it. */
(function(){
  var panels = document.querySelectorAll('.ood-panel');
  Array.prototype.forEach.call(panels, function(panel){
    var strip = panel.querySelector('.pn-gal-strip');
    var media = panel.querySelector('.results-hero-media');
    var main = media && media.querySelector('img');
    var credit = media && media.querySelector('.pn-image-credit');
    if (!strip || !main) return;
    var thumbs = strip.querySelectorAll('.pn-gal-thumb');
    Array.prototype.forEach.call(thumbs, function(btn, idx){
      btn.addEventListener('click', function(e){
        e.preventDefault();
        var full = btn.getAttribute('data-full');
        if (!full) return;
        main.src = full;
        main.alt = btn.getAttribute('data-alt') || '';
        if (credit) credit.textContent = btn.getAttribute('data-credit') || '';
        for (var k = 0; k < thumbs.length; k++){
          thumbs[k].classList.toggle('is-on', k === idx);
          thumbs[k].setAttribute('aria-pressed', k === idx ? 'true' : 'false');
        }
      });
    });
  });
  var tabs = document.querySelectorAll('.ood-tab');
  Array.prototype.forEach.call(tabs, function(tab){
    tab.addEventListener('click', function(){
      var id = tab.getAttribute('aria-controls');
      for (var i = 0; i < tabs.length; i++){
        var on = tabs[i] === tab;
        tabs[i].setAttribute('aria-selected', on ? 'true' : 'false');
        tabs[i].tabIndex = on ? 0 : -1;
      }
      Array.prototype.forEach.call(panels, function(p){ p.hidden = (p.id !== id); });
    });
    tab.addEventListener('keydown', function(e){
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      var list = Array.prototype.slice.call(tabs);
      var i = list.indexOf(tab) + (e.key === 'ArrowRight' ? 1 : -1);
      var next = list[(i + list.length) % list.length];
      next.focus(); next.click(); e.preventDefault();
    });
  });
})();
</script>"""


def tabs_html():
    out = ['  <div class="ood-tabs" role="tablist" aria-label="ÖÖD houses">']
    for n, h in enumerate(HOUSES):
        out.append('    <button type="button" class="ood-tab" role="tab" '
                   'id="ood-tab-%s" aria-controls="ood-%s" aria-selected="%s"'
                   '%s>%s</button>'
                   % (h["key"], h["key"], "true" if n == 0 else "false",
                      "" if n == 0 else ' tabindex="-1"', h["name"]))
    out.append('  </div>')
    return "\n".join(out) + "\n"


def also_html():
    cards = []
    for s in SAUNAS:
        i = s["image"]
        cards.append(
            '    <article class="ood-card">\n'
            '      <figure><img src="%s" alt="%s" '
            'decoding="async"><figcaption>%s</figcaption></figure>\n'
            '      <div class="ood-card-body"><b>%s</b><span>%s &middot; %s'
            '</span><br><a href="%s" target="_blank" rel="noopener">See it on '
            'oodhouse.com &rarr;</a></div>\n'
            '    </article>'
            % (src_url(i["id"], 1200), alt_of(s["name"], i),
               html.escape(credit_of(i)), s["name"], s["price"], s["area"],
               s["url"]))
    return (
        '\n  <div class="ood-also">\n'
        '    <h3>Where ÖÖD would sit on PlotNua</h3>\n'
        '    <div class="ood-where">\n'
        '      <a href="https://plotnua.ie/discovery-living-in-the-garden.html#explore-makers" '
        'target="_blank" rel="noopener"><b>Living in the Garden</b>'
        '<span>Garden rooms and garden homes. Your seven houses are already '
        'listed with the garden-room makers here.</span></a>\n'
        '      <a href="https://plotnua.ie/discovery-garden-retreat.html" '
        'target="_blank" rel="noopener"><b>Garden Retreat</b>'
        '<span>Saunas, hot tubs and cold plunges. This is where your saunas '
        'would belong.</span></a>\n'
        '    </div>\n'
        '  </div>\n'
        '\n  <div class="ood-also is-last">\n'
        '    <h3>Also in your range</h3>\n'
        '    <p>Euro prices as published, for the sauna itself.</p>\n'
        '    <div class="ood-range">\n' + "\n".join(cards) + '\n'
        '    </div>\n'
        '  </div>\n')


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · EVERY IMAGE IS ONE ÖÖD DRIVE FILE, WELL-FORMED, NEVER REPEATED.
    seen = set()
    every = [i for h in HOUSES for i in h["images"]] + [s["image"] for s in SAUNAS]
    for i in every:
        if not DRIVE_ID.match(i["id"]):
            die("not a Drive file id: %r" % i["id"])
        if i["id"] in seen:
            die("the same image is used twice: " + i["id"])
        seen.add(i["id"])
    for h in HOUSES:
        if not 3 <= len(h["images"]) <= 5:
            die("%s carries %d images; the brief asks for 3-5."
                % (h["name"], len(h["images"])))

    # G1 · Strip the template's filling instructions.
    block = re.search(r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
                      src, re.S)
    if not block:
        die("the template's instruction comment was not found.")
    src = src.replace(block.group(0), "\n")

    # G1b · Remove the introductory hero, as on every current Variant B build.
    hero = re.search(r"\n<div class=\"wrap\">\n  <header class=\"hero\">.*?"
                     r"\n  </header>\n</div>\n", src, re.S)
    if not hero or "{{PROPOSITION}}" not in hero.group(0):
        die("the introductory hero block was not found.")
    src = src.replace(hero.group(0), "\n")

    # G2 · Move the frozen journey band below the demonstration, byte-for-byte.
    jm = re.search(r"\n<!-- FROZEN.*?\n<div class=\"journey\">.*?\n</div>\n",
                   src, re.S)
    if not jm:
        die("the frozen journey band was not found.")
    journey = jm.group(0)
    src = src.replace(journey, "\n")
    why_anchor = "<!-- WHY THIS COULD BE USEFUL"
    if src.count(why_anchor) != 1:
        die("the 'why' section anchor is not unique.")
    src = src.replace(why_anchor, journey.strip("\n") + "\n\n" + why_anchor)

    # G3 · Seven fillings of the one production Results card.
    start_tag = '      <div class="results-hero-inner">'
    end_tag = '\n    </div>\n  </div>\n</section>'
    if src.count(start_tag) != 1 or src.count(end_tag) != 1:
        die("the Results card boundaries are not unique.")
    a = src.index(start_tag)
    b = src.index(end_tag)
    inner = src[a:b] + "\n"
    if not inner.rstrip().endswith("</div>"):
        die("the Results card did not close where expected.")
    panels = "".join(panel(inner, h, n) for n, h in enumerate(HOUSES))
    src = src[:a] + panels.rstrip("\n") + src[b:]

    # G3a · The model switcher sits above the frame; the range and the
    # Discoveries sit below it, inside the same demonstration section.
    screen = '  <div class="screen">'
    if src.count(screen) != 1:
        die("the screen frame is not unique.")
    src = src.replace(screen, tabs_html() + screen)
    demo_end = "\n    </div>\n  </div>\n</section>"
    if src.count(demo_end) != 1:
        die("the demonstration section end is not unique.")
    src = src.replace(demo_end, "\n    </div>\n  </div>\n" + also_html()
                      + "</section>")

    # G3b · The rights line before the footer: who gave permission and when,
    # with the link back.
    credit = ('<p class="credit-line">Images: %s, supplied by Gertrud Ots, '
              'Head of Marketing, on %s for use on PlotNua, shown unmodified '
              'from ÖÖD&rsquo;s own library and each used only for the model '
              'it shows. Named photographers are credited on each image. More '
              'at <a href="https://oodhouse.com/en-gb" rel="noopener">'
              'oodhouse.com</a>. If ÖÖD ask for any image to be changed or '
              'removed, we change or remove it.</p>\n'
              % (CREDIT, PERMISSION_DATE))
    if src.count("<footer>\n") != 1:
        die("the footer anchor is not unique.")
    src = src.replace("<footer>\n", credit + "<footer>\n")

    # G3c · Replace the template's single-card gallery script with the
    # per-card version above.
    sm = re.search(r"<script>\n\(function\(\)\{\n  var strip = "
                   r"document\.querySelector\('\.pn-gal-strip'\);.*?</script>",
                   src, re.S)
    if not sm:
        die("the template gallery script was not found.")
    src = src.replace(sm.group(0), SCRIPT)

    if src.count("</style>") < 1:
        die("no stylesheet to extend.")
    src = src.replace("</style>\n</head>", TABS_CSS + "</style>\n</head>", 1)
    if TABS_CSS not in src:
        die("the preview styles were not attached.")

    # G4 · Fill the page-level tokens; refuse on anything left behind.
    FILL.setdefault("SUPPLIER_SHORT", SUPPLIER_SHORT)
    for key, value in FILL.items():
        needle = "{{%s}}" % key
        if needle not in src and key != "SUPPLIER_SHORT":
            die("token %s is not in the template." % needle)
        src = src.replace(needle, value)
    leftover = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", src)))
    if leftover:
        die("unfilled tokens remain: " + ", ".join(leftover))

    # G5 · PRIVACY.
    for d in ("noindex", "nofollow", "noarchive", "nosnippet", "noimageindex"):
        if d not in src:
            die("the robots directive '%s' is missing." % d)

    visible = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.S | re.I)
    visible = re.sub(r"<script\b.*?</script>", " ", visible, flags=re.S | re.I)
    low = html.unescape(visible).lower()

    # G6 · NO OTHER SUPPLIER'S CONTENT.
    for other in OTHER_SUPPLIERS:
        if other.lower() in low:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit.")

    # G8 · NO IRISH OVERCLAIM. ROI delivery and installation are unconfirmed,
    # and Northern Ireland is not the Republic.
    for w in IRISH_OVERCLAIMS:
        if w in low:
            die("the page claims more about Ireland than is established: " + w)
    if low.count("still to be confirmed") < len(HOUSES):
        die("a house card lost its unconfirmed-Ireland line.")

    # G9 · CREDIT ON EVERY IMAGE, AND THE LINK BACK.
    if CREDIT != "ÖÖD House":
        die("the required credit constant has changed: %r" % CREDIT)
    n_img = len(re.findall(r'<img\b[^>]*src="https://lh3', src))
    n_credit = src.count('class="pn-image-credit">ÖÖD House') + \
        src.count("<figcaption>ÖÖD House")
    if n_credit != len(HOUSES) + len(SAUNAS):
        die("not every displayed image carries the ÖÖD House credit.")
    if src.count('data-credit="ÖÖD House') != sum(len(h["images"]) for h in HOUSES):
        die("a gallery thumbnail would swap in an image without its credit.")
    if "oodhouse.com" not in src:
        die("no link back to oodhouse.com.")

    # G10 · NO RELATIONSHIP OR TESTIMONIAL IMPLICATION.
    for w in RELATIONSHIP_WORDS:
        if w in low:
            die("the page implies a relationship that does not exist: " + w)

    # G11 · ILLUSTRATIVE LABEL, ONCE.
    if src.count("Illustrative preview") != 1:
        die("the illustrative label must appear exactly once.")

    # G12 · NO UK PRICES, AND EVERY PRICE IN EURO WITH ITS BASIS.
    if "£" in src or "&pound;" in src:
        die("a sterling price reached the page; a UK price is not an Irish one.")
    if src.count(PRICE_BASIS) != len(HOUSES):
        die("a house price lost its basis.")

    # G13 · EVERY REMOTE IMAGE IS A SCOPED ÖÖD DRIVE FILE.
    for u in re.findall(r'(?:src|data-full)="(https?://[^"]+)"', src):
        if not u.startswith(IMG_HOST):
            die("an image outside ÖÖD's Drive files: " + u)
        fid = u[len(IMG_HOST):].split("=")[0]
        if fid not in seen:
            die("an image that is not on the selected list: " + fid)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("ÖÖD HOUSE PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    13 guards passed")
    print("  ok    %d houses, %d saunas, %d images (%d <img> tags), all scoped "
          "ÖÖD Drive files" % (len(HOUSES), len(SAUNAS), len(seen), n_img))
    print("  ok    credit %r on every image and in the rights line" % CREDIT)
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    euro prices with basis; no sterling; Ireland unconfirmed")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
