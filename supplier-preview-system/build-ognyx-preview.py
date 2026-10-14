#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE OGNYX PRIVATE SUPPLIER PREVIEW, ONBOARDING EDITION.

TEMPLATE: supplier-preview-system/template-provider-led.html (variant B).

WHAT CHANGED, AND WHY THE SENT PAGE WAS NOT LEFT FROZEN.
The first edition of this page (commit b7cddb8, 2 October 2026) was sent to
Fabian at OGNYX and is preserved in git. On 13 October 2026 he replied to the
12 October follow-up -- "We have reviewed your offer and can confirm we would
be happy to proceed with this" -- and on 14 October the founder decided to
onboard OGNYX as a participating supplier. That reply is the "genuine reason"
SUPPLIER-PREVIEW-SYSTEM-V1 §10.1 requires before a sent preview is edited:
the page now has to show what OGNYX will look like once their full range is in
Atlas, not the three-product sketch they were first shown. Nothing here is
sent; the §10.1 send gate still applies.

THE STRUCTURE. One production Results card, filled three times -- cold plunge,
sauna, hot tub -- and switched by a row of category names above the frame, so
the frozen seven-part structure is unchanged. Below the frame: the whole
OGNYX range now in Atlas (41 products, text only, each linked to its own
ognyx.com page) and the one PlotNua Discovery it belongs to, DISC-001 Garden
Retreat.

IMAGERY — STILL THE SAME FOUR, STILL PREVIEW-SCOPED.
Fabian's 2 October reply invited "any example imagery ... you propose to use"
for this preview, and the 12 October ask that he said yes to named "the
selected product images shown there". That is the four images below and no
others. On 14 October 2026 the founder confirmed that the 13 October reply
covers those four images, within this approved context and no wider (Atlas
WELLNESS-FIRST-OGNYX-20261002: "Granted with Conditions — Founder
Confirmed"). The preview-only containment in
atlas-tools/preview-only-suppliers.json stays in force, so the four images
appear on this page only and no other OGNYX image is used anywhere. The other 38 products are text-only.

PHOTOGRAPH VERSUS VISUALISATION. Unchanged from the first edition: two of the
four are renders and the page says so wherever they appear.

EVIDENCE, read live 14 October 2026 from ognyx.com: product pages and the
store's own product data; Terms (OGNYX LIMITED, CRO 800095, 134A Herbert Park,
Bray, Co. Wicklow); Shipping & Delivery Policy, last updated 2 September 2026.

Run: python3 build-ognyx-preview.py [--stage]
"""

import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/ognyx-preview.html") if STAGE
       else SITE / "ognyx-preview.html")

SUPPLIER = "OGNYX"
EVIDENCE_DATE = "14 October 2026"
PERMISSION_DATE = "2 October 2026"
SUPPLIER_SITE = "https://www.ognyx.com/"
PRODUCT_BASE = "https://www.ognyx.com/products/"
CREDIT = "© OGNYX"
PERMITTED_PREFIX = "https://www.ognyx.com/cdn/shop/files/"
LOCALITY = "Co. Wicklow"

# ── THE FOUR IMAGES, EACH ONE LOOKED AT (first edition, re-checked live) ──
IMG = {
    "plunge1": {"url": PERMITTED_PREFIX + "Screenshot2025-08-13at21.01.07.png"
                       "?v=1755111942&width=1024",
                "kind": "photograph",
                "alt": "Photograph of the OGNYX stainless steel cold plunge "
                       "tub, clad in vertical timber staves with two steel "
                       "hoops and a stainless inner rim, standing on gravel "
                       "with a timber step stool beside it"},
    "plunge2": {"url": PERMITTED_PREFIX + "Screenshot2025-08-13at21.01.20.png"
                       "?v=1755111942&width=1024",
                "kind": "photograph",
                "alt": "Photograph looking down into the same empty cold "
                       "plunge tub, showing the stainless steel interior, the "
                       "timber staves and the two steel hoops, on gravel"},
    "sauna": {"url": PERMITTED_PREFIX + "Screenshot2025-08-11at18.27.16"
                     "_33889bd3-cb18-4369-83b3-b0be9a8d8586.png"
                     "?v=1754936822&width=1024",
              "kind": "visualisation",
              "alt": "Visualisation of the OGNYX 1.6m outdoor barrel sauna on "
                     "a timber deck in a garden, with a glass door, a dark "
                     "shingled roof and garden furniture beside it"},
    "tub": {"url": PERMITTED_PREFIX + "Screenshot2025-08-12at19.20.47.png"
                   "?v=1755025372&width=1024",
            "kind": "visualisation",
            "alt": "Visualisation of the OGNYX round hot tub, clad in timber "
                   "with a stainless chimney rising from the integrated stove "
                   "inside it and a timber step stool alongside, beside a "
                   "swimming pool. The image carries OGNYX's own caption bar "
                   "reading Ø 2M FOR 5 PERS"},
}

PRICE_BASIS = ("Basic-set price as published on ognyx.com; options chosen in "
               "the configurator add to it. The page doesn&rsquo;t say "
               "whether VAT is in the figure, and delivery is priced at "
               "checkout.")
CHECK = ("delivery to the homeowner&rsquo;s address is priced at checkout, "
         "assembly or installation is quoted separately, and production "
         "time depends on the configuration chosen.")

PANELS = [
    {"key": "plunge", "tab": "Cold plunge",
     "name": "Stainless Steel Cold Plunge Tub for One", "price": "&euro;2,310",
     "handle": "stainless-steel-cold-plunge-tub-for-one",
     "images": ["plunge1", "plunge2"],
     "f1": ("Size", "86 cm across, 105 cm high"),
     "f2": ("Capacity", "400 litres, for one person"),
     "f3": "Stainless steel interior inside an 18 mm thermowood exterior",
     "f4": "Basic set: the tub, waterproof plywood flooring, two stainless "
           "hoops, a thermowood bench and a drain",
     "f5": "Options include a cooler, a cover, stairs and an electric chiller "
           "that both cools and heats"},
    {"key": "sauna", "tab": "Sauna",
     "name": "1.6m Outdoor Sauna for 3 people", "price": "&euro;2,850",
     "handle": "1-6m-outdoor-sauna-for-3-persons",
     "images": ["sauna"],
     "f1": ("Size", "160 &times; 200 &times; 210 cm assembled"),
     "f2": ("Steam room", "4.2 m&sup3;, about two to three people"),
     "f3": "40 mm spruce body, thermowood benches, tempered glass door and a "
           "bitumen shingle roof",
     "f4": "Supplied flat-packed or fully assembled",
     "f5": "The configurator covers the electric stove, a glass or mirror "
           "front wall and lighting"},
    {"key": "tub", "tab": "Hot tub",
     "name": "Round Hot Tub with integrated wood-fired stove for 5 people",
     "price": "&euro;2,440",
     "handle": "round-hot-tub-with-integrated-wood-fired-stove-for-5-people",
     "images": ["tub"],
     "f1": ("Capacity", "4&ndash;6 people, 1,100 litres"),
     "f2": ("Size", "2.0 m round, 1.1 m high, 0.83 m deep"),
     "f3": "Fibreglass bath planked in 18 mm thermowood, with a 30 kW "
           "stainless steel stove inside the tub",
     "f4": "Chimney guard, waterproof plywood flooring and a drain valve in "
           "the basic set",
     "f5": "Options include bubble and hydro massage, LED lighting, an "
           "electric heater and a filter"},
]

# ── THE WHOLE RANGE NOW IN ATLAS (PROD-001217 to PROD-001257) ─────────────
# Titles exactly as OGNYX publish them; basic-set prices in euro.
RANGE = [
    ("plunge", "Stainless Steel Cold Plunge Tub for One", 2310, "stainless-steel-cold-plunge-tub-for-one"),
    ("plunge", "Cold Plunge Tub from fiberglass for 2 people", 2080, "cold-plunge-tub-from-fiberglass-for-2-persons"),
    ("plunge", "Fiberglass Cold Plunge Tub for One", 1690, "fiberglass-cold-plunge-tub-for-one"),
    ("tub", "Wooden Hot Tub without Heater", 1160, "wooden-hot-tub-without-heater"),
    ("tub", "Wooden Hot Tub with an Inside Heater for 3-10 people", 2050, "for-3-10-persons-wooden-hot-tub-with-an-inside-heater"),
    ("tub", "Wooden Hot Tub with an Outside Heater for 2 people", 1890, "for-2-persons-wooden-hot-tub-with-an-outside-heater"),
    ("tub", "Stainless Steel Wooden Hot Tub with a Wood-Fired Heater", 3460, "stainless-steel-wooden-hot-tub-with-a-wood-fired-heater"),
    ("tub", "Wooden Hot Tub with an Outside Heater for 4-12 people", 2050, "for-4-12-persons-wooden-hot-tub-with-an-outside-heater"),
    ("tub", "Wood-fired Hot Tub from Fiberglass for 2 people", 2490, "for-2-persons-wood-fired-hot-tub-from-fiberglass"),
    ("tub", "Wood-fired Hot Tub with an Inside Heater for 3 people", 2600, "for-3-persons-wood-fired-hot-tub-with-an-inside-heater"),
    ("tub", "Wood-fired Hot Tub with an Outside Heater for 4 people", 2570, "for-4-persons-wood-fired-hot-tub-with-an-outside-heater"),
    ("tub", "Wood-fired Hot Tub “Octa” from Fiberglass for 6 people", 2850, "for-6-persons-wood-fired-hot-tub-octa-from-fiberglass"),
    ("tub", "Wood-fired Hot Tub “Octa” from Fiberglass for 7 people", 2940, "for-7-persons-wood-fired-hot-tub-octa-from-fiberglass"),
    ("tub", "Wood-fired Hot Tub “Octa” from Fiberglass for 9 people", 3130, "for-9-persons-wood-fired-hot-tub-octa-from-fiberglass"),
    ("tub", "Wood-fired Hot Tub “Quattro” from Fiberglass for 8 people", 3250, "for-8-persons-wood-fired-hot-tub-quattro-from-fiberglass"),
    ("tub", "Round Hot Tub with integrated wood-fired stove for 5 people", 2440, "round-hot-tub-with-integrated-wood-fired-stove-for-5-people"),
    ("sauna", "Vertical Outdoor Sauna for 2 people", 3950, "vertical-outdoor-sauna-for-2-persons"),
    ("sauna", "Big Oval Outdoor Sauna for 6 people", 9970, "big-oval-outdoor-sauna-for-6-persons"),
    ("sauna", "Oval Outdoor Sauna for 6 people", 6780, "oval-outdoor-sauna-for-6-persons"),
    ("sauna", "Oval Outdoor Sauna for 4 people", 6680, "oval-outdoor-sauna-for-4-persons"),
    ("sauna", "3m Mirrored Sauna for 6 people", 5140, "3m-for-6-persons-mirrored-sauna"),
    ("sauna", "3m Mirrored Cube Barrel Sauna for 6 people", 5340, "3m-for-6-persons-mirrored-cube-barrel-sauna"),
    ("sauna", "2/2.3m Mirrored Cube Barrel Sauna for 4 people", 4810, "2-2-3m-for-4-persons-mirrored-cube-barrel-sauna"),
    ("sauna", "2-2.3m Mirrored Sauna for 4 people", 4580, "2-2-3m-for-4-persons-mirrored-sauna"),
    ("sauna", "4m Cube Barrel Sauna with dressing room and outside seats for 4 people", 5270, "4m-for-4-persons-cube-barrel-sauna-with-dressing-room-and-outside-seats"),
    ("sauna", "3m Cube Barrel Sauna for 6 people", 4340, "3m-for-6-persons-cube-barrel-sauna"),
    ("sauna", "3m Cube Barrel Sauna with dressing room for 4 people", 4610, "3m-for-4-persons-cube-barrel-sauna-with-dressing-room"),
    ("sauna", "2.4m Cube Barrel Sauna with outside seats for 4 people", 3880, "2-4m-for-4-persons-cube-barrel-sauna-with-outside-seats"),
    ("sauna", "2/2.3m Cube Barrel Sauna for 3 people", 3810, "2-2-3m-for-4-persons-cube-barrel-sauna"),
    ("sauna", "1.7m Cube Barrel Sauna for 3 people", 3160, "1-7m-for-3-persons-cube-barrel-sauna"),
    ("sauna", "5m Outdoor Sauna with seats or bed for 6 people", 6820, "5m-outdoor-sauna-for-6-persons-with-seats-or-bed"),
    ("sauna", "4m Outdoor Sauna with Dressing Room for 8 people", 4870, "4m-for-8-persons-outdoor-sauna-with-dressing-room"),
    ("sauna", "4m Two-room Outdoor Sauna for 4-6 people", 4960, "4m-for-4-6-persons-two-room-outdoor-sauna"),
    ("sauna", "4m Outdoor Sauna with Dressing Room and Outside Seats for 4 people", 4920, "4m-for-4-persons-outdoor-sauna-with-dressing-room-and-outside-seats"),
    ("sauna", "3.6m Outdoor Sauna with Outside Seats for 6 people", 4290, "3-6m-for-6-persons-outdoor-sauna-with-outside-seats"),
    ("sauna", "3m Outdoor Sauna for 6 people", 4140, "3m-for-6-persons-outdoor-sauna"),
    ("sauna", "3m Outdoor Sauna with Dressing Room for 4 people", 4360, "3m-for-4-persons-outdoor-sauna-with-dressing-room"),
    ("sauna", "2.8m Outdoor Sauna with Outside Seats for 4 people", 3860, "2-8m-for-4-persons-outdoor-sauna-with-outside-seats"),
    ("sauna", "2.4m Outdoor Sauna with Outside Seats for 4 people", 3660, "2-4m-for-4-persons-outdoor-sauna-with-outside-seats"),
    ("sauna", "2-2.3m Outdoor Sauna for 4 people", 3580, "2-2-3m-for-4-persons-outdoor-sauna"),
    ("sauna", "1,6m Outdoor Sauna for 3 people", 2850, "1-6m-outdoor-sauna-for-3-persons"),
]
FAMILY = {"plunge": "Cold plunges", "tub": "Hot tubs", "sauna": "Saunas"}

# The OGNYX pages that contradict themselves. Put to OGNYX, never resolved by
# PlotNua choosing one of the two figures.
CONTRADICTIONS = [
    "The <b>4m Outdoor Sauna with Dressing Room</b> is titled for 8 people "
    "but its specification gives a steam room for about 4;",
    "the <b>2.8m Outdoor Sauna with Outside Seats</b> is titled for 4 people "
    "but its specification says about 6;",
    "the <b>2/2.3m Cube Barrel Sauna</b> is titled for 3 people, but its "
    "web address and specification say 4.",
]

BANNED_CLAIM_PHRASES = [
    "health benefit", "therapeutic", "improves recovery", "boosts",
    "reduces inflammation", "immune", "detox", "cures", "treats ",
    "inc. vat", "including vat", "vat included", "ex. vat", "plus vat",
    "free delivery", "delivery is free", "delivery included",
    "installation included", "we install", "fully installed",
    "assembled on site", "warranty included", "guaranteed",
    "in stock", "next day", "ships in", "lead time of",
    "planning exempt", "no planning permission",
]
AI_ASSET_TOKENS = ["chatgpt", "midjourney", "ai-generated", "ai generated",
                   "dall-e", "stable diffusion"]
OTHER_SUPPLIERS = ("Cosy Cabins", "Irish Sauna Company", "Hutsmith",
                   "Yard Box", "Power Sheds", "TRIQ", "BIOBUILDS",
                   "Superior Pergola", "Honka", "MyCabin", "Harvia",
                   "Tanktribe", "TANKKD", "ÖÖD", "Polaris", "Pineca")
RELATIONSHIP_WORDS = ("partner", "approved supplier", "recommended",
                      "trusted supplier", "preferred supplier", "endorsed",
                      "commission", "exclusive")

FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "DEMO_HEADING": "How OGNYX would appear within PlotNua",
    "DEMO_LEDE": "This is a shortened example of the Results "
                 "experience &mdash; a homeowner would see additional "
                 "property-specific checks, comparison information and "
                 "supporting detail as they continue through PlotNua.",
    "WHY_1_LABEL": "THREE ROUTES, ONE SUPPLIER",
    "WHY_1_TEXT": "A homeowner looking at a garden retreat doesn&rsquo;t "
                  "arrive knowing whether they want a sauna, a hot tub or "
                  "cold water. OGNYX cover all three, so you stay relevant "
                  "whichever way their thinking goes.",
    "WHY_2_LABEL": "AN IRISH COMPANY",
    "WHY_2_TEXT": "OGNYX LIMITED is registered in Ireland, in Bray, Co. "
                  "Wicklow. For someone comparing outdoor wellness options, "
                  "that&rsquo;s a real difference from ordering from abroad.",
    "WHY_3_LABEL": "REACHED THROUGH WELLNESS",
    "WHY_3_TEXT": "People arrive here having decided they want a garden "
                  "retreat, not having typed your name into a search box. "
                  "That&rsquo;s a different kind of enquiry from a directory "
                  "click.",
    "CLOSING_PROPOSITION": "Is everything here right before Irish "
                           "homeowners see it?",
    "CLOSING_SUPPORT": "Your 41 products are now in our catalogue, each linked to "
                       "its own page on ognyx.com. Three things we&rsquo;d "
                       "like to check with you before the range goes live: "
                       "</p>\n  <ul class=\"og-questions\">\n"
                       "    <li><b>VAT.</b> Is the price on the product page "
                       "the full price for an Irish buyer, or does VAT change "
                       "it at checkout?</li>\n"
                       "    <li><b>Delivery and timing.</b> What would you "
                       "tell someone in Ireland to expect for delivery cost "
                       "and time from order, for a standard sauna, hot tub "
                       "or plunge?</li>\n"
                       "    <li><b>Three capacities.</b> " + " ".join(CONTRADICTIONS)
                       + " Which figure should we use?</li>\n"
                       "  </ul>\n  <p>",
    "DATE": EVIDENCE_DATE,
}

CSS = """
/* ── OGNYX PREVIEW · category switcher, range and discovery ───────── */
.og-tabs{ display:flex; flex-wrap:wrap; gap:8px; margin:0 0 var(--pn-sm); }
.og-tab{ font:inherit; font-size:var(--pn-w-body-sm); color:var(--pn-voice);
  background:transparent; border:1px solid var(--pn-edge); border-radius:999px;
  padding:7px 16px; cursor:pointer; line-height:1.2; }
.og-tab:hover{ border-color:var(--pn-voice); }
.og-tab[aria-selected="true"]{ background:var(--pn-voice); color:var(--pn-on-dark);
  border-color:var(--pn-voice); }
.og-tab:focus-visible{ outline:2px solid var(--pn-voice); outline-offset:2px; }
.og-panel[hidden]{ display:none !important; }
.og-block{ margin-top:var(--pn-lg); }
.og-block.is-last{ margin-bottom:var(--pn-xl); }
.og-block h3{ font-size:var(--pn-s-quote); margin:0 0 6px; }
.og-block > p{ font-size:var(--pn-w-body-sm); margin:0 0 var(--pn-sm); }
.og-where{ display:block; text-decoration:none; color:inherit; border:1px solid var(--pn-hair);
  border-radius:5px; padding:16px 18px; background:var(--pn-ground); max-width:640px; }
.og-where:hover{ border-color:var(--pn-voice); }
.og-where b{ display:block; font-family:'Fraunces',Georgia,serif; font-weight:400;
  font-size:19px; color:var(--pn-voice); margin-bottom:2px; }
.og-where span{ font-size:var(--pn-w-body-sm); }
.og-range{ display:grid; grid-template-columns:1fr 1fr 2fr; gap:16px; align-items:start; }
.og-fam{ background:var(--pn-paper); border:1px solid var(--pn-hair); border-radius:5px;
  padding:14px 16px 10px; }
.og-fam h4{ font-family:'Fraunces',Georgia,serif; font-weight:400; font-size:18px;
  color:var(--pn-voice); margin:0 0 8px; }
.og-fam h4 small{ display:block; margin-top:3px; font-family:'Work Sans',system-ui,sans-serif; font-size:var(--pn-w-meta);
  letter-spacing:.14em; text-transform:uppercase; color:var(--pn-stone); }
.og-fam ul{ list-style:none; margin:0; padding:0; }
.og-fam.is-wide ul{ columns:2; column-gap:20px; }
.og-fam li{ break-inside:avoid; border-top:1px solid var(--pn-hair); padding:7px 0;
  font-size:var(--pn-w-body-sm); line-height:1.35; }
.og-fam li:first-child{ border-top:0; }
.og-fam li a{ color:var(--pn-fact); text-decoration:none; }
.og-fam li a:hover{ text-decoration:underline; }
.og-fam li span{ display:block; color:var(--pn-stone); font-size:12px; margin-top:1px; }
.og-questions{ margin:0 0 15px; padding-left:18px; max-width:62ch; }
.og-questions li{ margin-bottom:8px; }
@media (max-width:900px){
  .og-range{ grid-template-columns:1fr 1fr; }
  .og-fam.is-wide{ grid-column:1 / -1; }
}
@media (max-width:600px){
  .og-range{ grid-template-columns:1fr; }
  .og-fam.is-wide ul{ columns:1; }
}
"""

SCRIPT = """<script>
/* OGNYX PREVIEW — the template's gallery, per card, plus the category
   switcher. The credit is swapped in the same statement as the picture. */
(function(){
  var panels = document.querySelectorAll('.og-panel');
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
  var tabs = document.querySelectorAll('.og-tab');
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


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def credit_for(i):
    return CREDIT + (" · Visualisation" if i["kind"] == "visualisation" else "")


def gallery(panel):
    imgs = [IMG[k] for k in panel["images"]]
    hero = imgs[0]
    out = ['        <div class="results-hero-media has-pn-gallery">',
           '          <img src="%s" alt="%s" loading="lazy">'
           % (hero["url"], html.escape(hero["alt"], quote=True)),
           '          <span class="pn-image-credit">%s</span>' % credit_for(hero),
           '        </div>']
    if len(imgs) > 1:
        out.append('        <div class="pn-gal-strip">')
        for n, i in enumerate(imgs):
            out.append('          <button type="button" class="pn-gal-thumb%s" '
                       'aria-pressed="%s" aria-label="View image %d of %d" '
                       'data-full="%s" data-alt="%s" data-credit="%s">'
                       '<img src="%s" alt=""></button>'
                       % (" is-on" if n == 0 else "",
                          "true" if n == 0 else "false", n + 1, len(imgs),
                          i["url"], html.escape(i["alt"], quote=True),
                          credit_for(i), i["url"]))
        out.append('        </div>')
    return "\n".join(out)


def panel_html(inner, p, n):
    s = inner
    slot = re.search(r'        <div class="results-hero-media">\n'
                     r'          <div class="pn-photo-slot"[^>]*>.*?</div>\n'
                     r'        </div>\n', s, re.S)
    if not slot:
        die("the held media wrapper was not found in the Results card.")
    s = s.replace(slot.group(0), gallery(p) + "\n")
    if s.count("pnMarkClipSave") != 2:
        die("the Save mark clipPath id is not where the template had it.")
    s = s.replace("pnMarkClipSave", "pnMarkClipSave%d" % n)
    old_link = ('<a class="hero-secondary-link" href="#">Explore with '
                '{{SUPPLIER_SHORT}} &rarr;</a>')
    if s.count(old_link) != 1:
        die("the 'Explore with' link is not in the Results card exactly once.")
    s = s.replace(old_link, '<a class="hero-secondary-link" href="%s%s" '
                  'target="_blank" rel="noopener">See it on ognyx.com &rarr;</a>'
                  % (PRODUCT_BASE, p["handle"]))
    fills = {
        "OFFER_NAME": p["name"], "SUPPLIER_NAME": SUPPLIER,
        "VERIFIED_PRICE": p["price"], "VERIFIED_PRICE_BASIS": PRICE_BASIS,
        "HOMEOWNER_LOCALITY": LOCALITY,
        "PERSONALISATION": "Shown for a homeowner in %s, from the location "
                           "they gave us." % LOCALITY,
        "VERIFIED_FACT_1_LABEL": p["f1"][0], "VERIFIED_FACT_1_VALUE": p["f1"][1],
        "VERIFIED_FACT_2_LABEL": p["f2"][0], "VERIFIED_FACT_2_VALUE": p["f2"][1],
        "VERIFIED_FACT_3": p["f3"], "VERIFIED_FACT_4": p["f4"],
        "VERIFIED_FACT_5": p["f5"], "THINGS_TO_CHECK": CHECK,
    }
    for k, v in fills.items():
        needle = "{{%s}}" % k
        if needle not in s:
            die("token %s is not in the Results card." % needle)
        s = s.replace(needle, v)
    left = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", s)))
    if left:
        die("unfilled tokens in the %s card: %s" % (p["tab"], left))
    open_tag = '      <div class="results-hero-inner">'
    if not s.startswith(open_tag):
        die("the Results card does not open where expected.")
    return ('      <div class="results-hero-inner og-panel" id="og-%s" '
            'role="tabpanel" aria-label="%s"%s>'
            % (p["key"], p["tab"], "" if n == 0 else " hidden")
            + s[len(open_tag):])


def tabs_html():
    out = ['  <div class="og-tabs" role="tablist" aria-label="OGNYX ranges">']
    for n, p in enumerate(PANELS):
        out.append('    <button type="button" class="og-tab" role="tab" '
                   'id="og-tab-%s" aria-controls="og-%s" aria-selected="%s"%s>'
                   '%s</button>' % (p["key"], p["key"],
                                    "true" if n == 0 else "false",
                                    "" if n == 0 else ' tabindex="-1"', p["tab"]))
    out.append('  </div>')
    return "\n".join(out) + "\n"


def range_html():
    fams = []
    for f in ("plunge", "tub", "sauna"):
        rows = [r for r in RANGE if r[0] == f]
        lo = min(r[2] for r in rows)
        items = "\n".join(
            '        <li><a href="%s%s" target="_blank" rel="noopener">%s</a>'
            '<span>&euro;%s</span></li>'
            % (PRODUCT_BASE, r[3], html.escape(r[1]), "{:,}".format(r[2]))
            for r in rows)
        fams.append(
            '    <div class="og-fam%s">\n'
            '      <h4>%s <small>%d &middot; from &euro;%s</small></h4>\n'
            '      <ul>\n%s\n      </ul>\n    </div>'
            % (" is-wide" if f == "sauna" else "", FAMILY[f], len(rows),
               "{:,}".format(lo), items))
    return (
        '\n  <div class="og-block">\n'
        '    <h3>Where OGNYX would sit on PlotNua</h3>\n'
        '    <a class="og-where" href="https://plotnua.ie/discovery-garden-retreat.html" '
        'target="_blank" rel="noopener"><b>Garden Retreat</b>'
        '<span>Saunas, hot tubs and cold plunges &mdash; all three of your '
        'ranges belong here.</span></a>\n'
        '  </div>\n'
        '\n  <div class="og-block is-last">\n'
        '    <h3>Your full range in PlotNua</h3>\n'
        '    <p>Every product as you publish it, with its basic-set price in '
        'euro and a link to its own page.</p>\n'
        '    <div class="og-range">\n' + "\n".join(fams) + '\n    </div>\n'
        '  </div>\n')


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · THE FOUR AUTHORISED IMAGES AND NOTHING ELSE, EACH CLASSIFIED.
    if len(IMG) != 4:
        die("expected the 4 inspected assets, found %d." % len(IMG))
    for k, i in IMG.items():
        if not i["url"].startswith(PERMITTED_PREFIX):
            die("image outside OGNYX's own file namespace: " + i["url"])
        if i["kind"] not in ("photograph", "visualisation"):
            die("image %s is neither a photograph nor a visualisation." % k)
    used = [k for p in PANELS for k in p["images"]]
    if sorted(used) != sorted(IMG):
        die("each of the four images must be used exactly once: %s" % used)
    # G0b · NO AI-LABELLED ASSET.
    for i in IMG.values():
        blob = (i["url"] + " " + i["alt"]).lower()
        for tok in AI_ASSET_TOKENS:
            if tok in blob:
                die("an AI-labelled asset reached the image list: " + tok)
    # G0c · A VISUALISATION SAYS SO IN ITS ALT TEXT, A PHOTOGRAPH LIKEWISE.
    for i in IMG.values():
        if i["kind"] not in i["alt"].lower():
            die("alt text does not state the medium (%s): %s"
                % (i["kind"], i["url"]))
    # G0d · THE RANGE IS THE 41 ATLAS PRODUCTS, EACH ON ITS OWN PAGE.
    if len(RANGE) != 41 or len({r[3] for r in RANGE}) != 41:
        die("the range must list the 41 Atlas products once each.")
    for r in RANGE:
        if not re.match(r"^[a-z0-9-]+$", r[3]) or r[0] not in FAMILY:
            die("malformed range row: %r" % (r,))
    for p in PANELS:
        if not any(r[3] == p["handle"] for r in RANGE):
            die("the %s card is not one of the range products." % p["tab"])

    # G1 · Strip the template's filling instructions.
    block = re.search(r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
                      src, re.S)
    if not block:
        die("the template's instruction comment was not found.")
    src = src.replace(block.group(0), "\n")

    # G1b · Remove the introductory hero.
    hero = re.search(r"\n<div class=\"wrap\">\n  <header class=\"hero\">.*?"
                     r"\n  </header>\n</div>\n", src, re.S)
    if not hero or "{{PROPOSITION}}" not in hero.group(0):
        die("the introductory hero block was not found.")
    src = src.replace(hero.group(0), "\n")

    # G2 · Relocate the frozen journey band, byte-for-byte.
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

    # G3 · Three fillings of the one production Results card.
    start_tag = '      <div class="results-hero-inner">'
    end_tag = '\n    </div>\n  </div>\n</section>'
    if src.count(start_tag) != 1 or src.count(end_tag) != 1:
        die("the Results card boundaries are not unique.")
    a, b = src.index(start_tag), src.index(end_tag)
    inner = src[a:b] + "\n"
    panels = "".join(panel_html(inner, p, n) for n, p in enumerate(PANELS))
    src = src[:a] + panels.rstrip("\n") + src[b:]

    # G3a · The switcher above the frame; Discovery and range below it.
    if src.count('  <div class="screen">') != 1:
        die("the screen frame is not unique.")
    src = src.replace('  <div class="screen">', tabs_html() + '  <div class="screen">')
    if src.count(end_tag) != 1:
        die("the demonstration section end is not unique.")
    src = src.replace(end_tag, "\n    </div>\n  </div>\n" + range_html()
                      + "</section>")

    # G3b · The closing heading becomes the pre-publication review ask.
    old_head = "<h2>What we&rsquo;d like to explore</h2>"
    if src.count(old_head) != 1:
        die("the closing heading was not found exactly once.")
    src = src.replace(old_head, "<h2>Before anything goes live</h2>")

    # G3c · Credit, link back and medium, in plain words.
    credit_line = (
        '<p class="credit-line">%s. The four images are OGNYX&rsquo;s own, '
        'used unmodified and served from <a href="%s" rel="noopener">'
        'ognyx.com</a> with permission given on %s for this preview. Two are '
        'visualisations and are labelled as such. If OGNYX ask for any image '
        'to be changed or removed, we change or remove it. Every figure on '
        'this page is published by OGNYX and was read on %s.</p>\n'
        % (CREDIT, SUPPLIER_SITE, PERMISSION_DATE, EVIDENCE_DATE))
    if src.count("<footer>\n") != 1:
        die("the footer anchor is not unique.")
    src = src.replace("<footer>\n", credit_line + "<footer>\n")

    # G3d · Per-card gallery script replaces the template's single-card one.
    sm = re.search(r"<script>\n\(function\(\)\{\n  var strip = "
                   r"document\.querySelector\('\.pn-gal-strip'\);.*?</script>",
                   src, re.S)
    if not sm:
        die("the template gallery script was not found.")
    src = src.replace(sm.group(0), SCRIPT)
    if "</style>\n</head>" not in src:
        die("no stylesheet to extend.")
    src = src.replace("</style>\n</head>", CSS + "</style>\n</head>", 1)

    # G4 · Fill the page-level tokens; refuse on anything left behind.
    for key, value in FILL.items():
        needle = "{{%s}}" % key
        if needle not in src:
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
    low = re.sub(r"\s+", " ", html.unescape(visible)).lower()

    # G6 · NO OTHER SUPPLIER'S CONTENT.
    for other in OTHER_SUPPLIERS:
        if other.lower() in low:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit.")

    # G8 · NO UNEVIDENCED CLAIM.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the evidence does not "
                "support: %r." % phrase)

    # G8b · EACH VISUALISATION IS LABELLED WHERE IT IS SHOWN.
    vis = sum(1 for i in IMG.values() if i["kind"] == "visualisation")
    if src.count('class="pn-image-credit">%s · Visualisation' % CREDIT) != vis:
        die("a visualisation is shown without its on-image label.")

    # G9 · CREDIT AND LINK BACK.
    if CREDIT != "© OGNYX":
        die("the required credit constant has changed: %r" % CREDIT)
    if "&copy;" in src:
        die("the credit is written as the &copy; entity.")
    if src.count('class="pn-image-credit">' + CREDIT) != len(PANELS):
        die("a Results card shows an image without the %s credit." % CREDIT)
    if 'href="%s"' % SUPPLIER_SITE not in src:
        die("the page does not link back to %s." % SUPPLIER_SITE)
    # The literal, not the constant: a guard that counts its own subject
    # passes whatever the subject is changed to.
    if src.count('href="https://www.ognyx.com/products/') < len(RANGE) + len(PANELS):
        die("a product is listed without a link to its own ognyx.com page.")
    imgs = re.findall(r'<img[^>]+src="(https?://[^"]+)"', src)
    stray = [u for u in imgs if not u.startswith(PERMITTED_PREFIX)]
    if stray:
        die("an image outside the permitted scope reached the page: " + stray[0])
    expected = len(PANELS) + sum(len(p["images"]) for p in PANELS
                                 if len(p["images"]) > 1)
    if len(imgs) != expected:   # one per card, plus a thumbnail per gallery image
        die("expected %d <img> tags, found %d." % (expected, len(imgs)))

    # G10 · NO RELATIONSHIP IMPLICATION.
    for w in RELATIONSHIP_WORDS:
        if w in low:
            die("the page implies a relationship that does not exist: " + w)

    # G11 · ILLUSTRATIVE LABEL ONCE, AND THE REVIEW ASK.
    if src.count("Illustrative preview") != 1:
        die("the illustrative label must appear exactly once.")
    if "before anything goes live" not in low:
        die("the pre-publication review ask is missing.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("OGNYX PRIVATE PREVIEW — ONBOARDING EDITION")
    print("=" * 74)
    print("  ok    guards G0-G11 passed")
    print("  ok    3 Results cards, %d range products, all linked to ognyx.com"
          % len(RANGE))
    print("  ok    4 authorised images (%d photograph, %d visualisation), "
          "each credited and labelled" % (len(IMG) - vis, vis))
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    no VAT, health, delivery, installation or lead-time claim")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched.")
    print("SEND GATE: §10.1 — hand it to the founder and STOP.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
