#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PREVIEW-IDENTITY-001 — refresh both certified templates from the committed
production Results identity/gallery amendment (bcc904e).

WHAT WAS WRONG WITH THE PREVIEW.

  1. THE PRODUCT'S IDENTITY WAS STILL IN THE RIGHT-HAND COLUMN. The name,
     the supplier and the price sat inside .results-hero-body beside the
     photograph, which is exactly the composition production stopped using.
     A supplier opening their preview saw a layout PlotNua no longer ships.

  2. THE THUMBNAILS WERE DEAD. Both templates carry ZERO <script> tags, so
     the strip the builder emits has never had a click handler. Clicking a
     thumbnail did nothing. That is a static picture of a gallery, not a
     gallery, and it must not go to a supplier.

WHAT THIS WRITES, INTO BOTH TEMPLATES.

    .results-hero-inner
      .rh-identity        name, then "Supplier . price"
      .rh-split
        .pn-media-col     .results-hero-media (+ .pn-gal-strip)
        .results-hero-body   the decision column

  plus the production CSS block, LIFTED VERBATIM from your-plot.html and
  re-scoped from #screen-match-results to .pn-stage. The numbers are not
  retyped here: 58 / 64 / 4:3 arrive by extraction, so the preview cannot
  drift from production by a transcription error.

  plus ONE generic gallery handler, driven by data- attributes on the
  thumbs, so every preview built from these templates gets a working
  gallery rather than Hutsmith getting a special case.

WHAT THIS DOES NOT TOUCH.

  your-plot.html, Resolve, the rights records, the pricing logic, My Plot
  and the enquiry behaviour. This builder reads production and writes only
  the two templates.

A NOTE ON refresh-ui-kit.py. That tool is the intended way to regenerate
these templates and it is BROKEN: it slices production by hard-coded line
numbers, was last updated at 08de5f0, and your-plot.html has changed in 30
commits since. It aborts on its second block. It is left alone here because
it is out of scope for this pass, but it is why the templates drift, and it
should be re-anchored before the next refresh.

Run:  python3 build-preview-identity-band.py --check
      python3 build-preview-identity-band.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
PROD = REPO / "your-plot.html"
TEMPLATES = {
    "provider": HERE / "template-provider-led.html",
    "product": HERE / "template-product-led.html",
}
NAME_TOKEN = {"provider": "{{OFFER_NAME}}", "product": "{{PRODUCT_NAME}}"}

CHECK = "--check" in sys.argv


def die(msg):
    print("ABORT: " + msg)
    sys.exit(1)


# ===========================================================================
# 1 . LIFT THE PRODUCTION BLOCK. Not retyped -- extracted.
# ===========================================================================

prod = PROD.read_text(encoding="utf-8")
if "RESULTS-IDENTITY-001" not in prod:
    die("P01 production has no RESULTS-IDENTITY-001 block; is bcc904e checked out?")

# Bounded with die(), not index(). The proof caught this raising a bare
# ValueError when the block could not be found: a builder that crashes has
# not refused, it has merely failed, and the two must not look alike.
if "RESULTS-IDENTITY-001 · IDENTITY FIRST" not in prod:
    die("P01 production's identity banner is not where the lift expects it")
_i = prod.index("RESULTS-IDENTITY-001 · IDENTITY FIRST")
_i = prod.rindex("/*", 0, _i)
if "@media (max-width:719px){" not in prod[_i:]:
    die("P01 the identity block's mobile tail is missing; cannot bound the lift")
_j = prod.index("@media (max-width:719px){", _i)
_d, _k = 0, prod.index("{", _j)
while True:
    if prod[_k] == "{":
        _d += 1
    elif prod[_k] == "}":
        _d -= 1
        if _d == 0:
            break
    _k += 1
BLOCK = prod[_i:_k + 1]

for need in ("width:58%; min-width:0; max-width:58%; flex:0 0 58%;",
             "width:64%; max-width:64%; flex:0 0 64%;",
             "aspect-ratio:4/3;", "gap:clamp(32px,3.4vw,48px);", "gap:26px;",
             ".rh-identity", ".rh-split", ".rh-identity-meta", "min-height:26px"):
    if need not in BLOCK:
        die("P02 the lifted production block is missing %r" % need)

# Re-scope production -> preview. The preview's own scope is .pn-stage.
PORTED = (BLOCK
          .replace("#screen-match-results ", ".pn-stage ")
          .replace("  .results-hero-inner:has(.rh-identity){",
                   "  .pn-stage .results-hero-inner:has(.rh-identity){")
          .replace("RESULTS-IDENTITY-001 · IDENTITY FIRST",
                   "PREVIEW-IDENTITY-001 · IDENTITY FIRST (lifted from production)"))

if "#screen-match-results" in PORTED:
    die("P03 a production-only scope survived the re-scope")
# Selector LINES only -- one per line, ending in "{". A regex across the
# whole block reads declaration text as a selector and refuses a correct
# port; the production builder's R06 had the same bug and the same fix.
for line in PORTED.splitlines():
    r = line.strip()
    if not r.endswith("{") or r.startswith("@") or r.startswith("/*"):
        continue
    r = r[:-1].strip()
    if r.startswith(".pn-stage") or ":has(.rh-identity)" in r or ":has(.rh-split)" in r:
        continue
    die("P03 a ported rule is not preview-scoped: %r" % r)

# ===========================================================================
# 2 . THE GALLERY HANDLER. One, generic, data-driven.
# ===========================================================================

GALLERY_JS = """
<!-- PREVIEW-IDENTITY-001 — THE GALLERY ACTUALLY WORKS NOW.
     Both templates previously carried no script at all, so the thumbnail
     strip was decorative: clicking it did nothing. This is the whole
     behaviour, in one place, for every preview built from these templates.

     It is deliberately NOT a copy of pnGovernedGallery(). On Results that
     function re-checks the rights gate before every paint, because Results
     paints from live Atlas data. A preview is a STATIC artefact whose
     images already passed the gate at build time -- the builder refuses to
     emit an unauthorised image at all -- so there is nothing left to
     re-check at click time and pretending otherwise would be theatre. What
     must still hold is that the credit never parts company with the
     picture, so the credit is swapped in the same statement as the src. -->
<script>
(function(){
  var strip = document.querySelector('.pn-gal-strip');
  if (!strip) return;
  var media  = document.querySelector('.results-hero-media');
  var main   = media && media.querySelector('img');
  var credit = media && media.querySelector('.pn-image-credit');
  if (!main) return;
  var thumbs = strip.querySelectorAll('.pn-gal-thumb');

  function show(btn, i){
    var full = btn.getAttribute('data-full');
    if (!full) return;                       /* nothing to show, do nothing */
    main.src = full;
    main.alt = btn.getAttribute('data-alt') || '';
    /* THE CREDIT TRAVELS WITH THE PICTURE. Same statement, no gap. */
    if (credit) credit.textContent = btn.getAttribute('data-credit') || '';
    for (var k = 0; k < thumbs.length; k++){
      var on = (k === i);
      thumbs[k].classList.toggle('is-on', on);
      thumbs[k].setAttribute('aria-pressed', on ? 'true' : 'false');
    }
  }

  for (var i = 0; i < thumbs.length; i++){
    (function(btn, idx){
      btn.addEventListener('click', function(e){
        e.preventDefault();                  /* never reload the page */
        show(btn, idx);
      });
    })(thumbs[i], i);
  }
})();
</script>
"""

# ===========================================================================
# 3 . THE EDITS
# ===========================================================================

REPORT = []

for kind, path in TEMPLATES.items():
    t = path.read_text(encoding="utf-8")
    orig = t
    edits = []

    def edit(tag, old, new, why):
        global t
        n = t.count(old)
        if n != 1:
            die("%s/%s anchor matched %d times, expected 1: %s"
                % (kind, tag, n, old.strip().splitlines()[0][:90]))
        t = t.replace(old, new, 1)
        edits.append((tag, why))

    if "rh-identity" in t:
        die("T00/%s the identity band is already in this template" % kind)

    NAME = NAME_TOKEN[kind]

    # ---- T01 . the identity band, and .rh-split opens --------------------
    OLD_OPEN = '      <div class="results-hero-inner">\n'
    NEW_OPEN = ('      <div class="results-hero-inner">\n'
                '        <!-- PREVIEW-IDENTITY-001 — THE PRODUCT IS NAMED ACROSS THE\n'
                '             TOP, as it is on production Results. The band carries the\n'
                '             name and "Supplier · price" and nothing else; the price\n'
                '             BASIS and every other explanation belong to the decision,\n'
                '             so they stay in the column below. -->\n'
                '        <div class="rh-identity">\n'
                '          <h2 class="results-hero-name">%s</h2>\n'
                '          <div class="rh-identity-meta">\n'
                '            <span class="results-hero-org">{{SUPPLIER_NAME}}</span>\n'
                '            <span class="rh-identity-sep" aria-hidden="true">·</span>\n'
                '            <span class="results-hero-price">{{VERIFIED_PRICE}}</span>\n'
                '          </div>\n'
                '        </div>\n'
                '        <div class="rh-split">\n' % NAME)
    edit("T01", OLD_OPEN, NEW_OPEN, "identity band added, .rh-split opened")

    # ---- T02 . the media block moves into .pn-media-col ------------------
    if kind == "provider":
        OLD_MEDIA = """        <div class="results-hero-media">
          <div class="pn-photo-slot">
            <b>Your project photography here</b>
            <span>{{PHOTO_SLOT_LINE}}</span>
          </div>
        </div>
"""
        NEW_MEDIA = """        <div class="pn-media-col">
        <div class="results-hero-media">
          <div class="pn-photo-slot">
            <b>Your project photography here</b>
            <span>{{PHOTO_SLOT_LINE}}</span>
          </div>
        </div>
        </div>
"""
    else:
        OLD_MEDIA = """        <div class="results-hero-media">
          <img src="{{IMAGE_URL}}" alt="{{IMAGE_ALT}}" loading="lazy">
        </div>
"""
        NEW_MEDIA = """        <div class="pn-media-col">
        <div class="results-hero-media">
          <img src="{{IMAGE_URL}}" alt="{{IMAGE_ALT}}" loading="lazy">
        </div>
        </div>
"""
    edit("T02", OLD_MEDIA, NEW_MEDIA, "media wrapped in .pn-media-col")

    # ---- T03 . name/org/price leave the decision column ------------------
    OLD_HEAD = """        <div class="results-hero-body">
          <h2 class="results-hero-name">%s</h2>
          <div class="results-hero-org">{{SUPPLIER_NAME}}</div>

          <div class="results-hero-price-row">
            <span class="results-hero-price">{{VERIFIED_PRICE}}</span>
            <span class="results-hero-area">{{VERIFIED_PRICE_BASIS}}</span>
          </div>
""" % NAME
    NEW_HEAD = """        <div class="results-hero-body">
          <!-- The name, the supplier and the price are in the band above.
               What stays here is the price BASIS, which explains the figure
               rather than stating it, and therefore belongs to the decision. -->
          <div class="results-hero-price-row">
            <span class="results-hero-area">{{VERIFIED_PRICE_BASIS}}</span>
          </div>
"""
    edit("T03", OLD_HEAD, NEW_HEAD, "name/supplier/price removed from the column")

    # ---- T04 . .rh-split closes ------------------------------------------
    OLD_CLOSE = """            <a class="hero-secondary-link" href="#">Explore with {{SUPPLIER_SHORT}} &rarr;</a>
          </div>
        </div>
      </div>
"""
    NEW_CLOSE = """            <a class="hero-secondary-link" href="#">Explore with {{SUPPLIER_SHORT}} &rarr;</a>
          </div>
        </div>
        </div>
      </div>
"""
    edit("T04", OLD_CLOSE, NEW_CLOSE, ".rh-split closed around media + body")

    # ---- T05 . the ported production CSS ----------------------------------
    # Anchored on the media-column rule PREVIEW-PARITY-001 added: unique in
    # both templates, and the right neighbourhood for the ported block.
    CSS_ANCHOR = ".pn-stage .pn-media-col{ display:flex; flex-direction:column; min-width:0; }"
    if t.count(CSS_ANCHOR) != 1:
        die("T05/%s the preview CSS anchor is not unique" % kind)
    _p = t.rindex("\n", 0, t.index(CSS_ANCHOR))
    t = t[:_p] + "\n\n" + PORTED + "\n" + t[_p:]
    edits.append(("T05", "production identity/split CSS ported, re-scoped"))

    # ---- T06 . the gallery handler ----------------------------------------
    if "</body>" not in t:
        die("T06/%s no </body> to attach the gallery handler to" % kind)
    t = t.replace("</body>", GALLERY_JS + "</body>", 1)
    edits.append(("T06", "generic data-driven gallery handler added"))

    # ---- guards -----------------------------------------------------------
    body = t[t.index('<div class="results-hero-body">'):]
    body = body[:body.index('<div class="rh-split">')] if '<div class="rh-split">' in body else body
    if "results-hero-name" in body:
        die("G1/%s the product name is still inside the decision column" % kind)
    if '<div class="results-hero-org">' in body:
        die("G1/%s the supplier is still a block in the decision column" % kind)

    ident = t[t.index('<div class="rh-identity">'):t.index('<div class="rh-split">')]
    for banned in ("VERIFIED_PRICE_BASIS", "PERSONALISATION", "pn-facts",
                   "THINGS_TO_CHECK", "prop-confirm"):
        if banned in ident:
            die("G2/%s the identity band carries more than name + supplier + "
                "price (%s)" % (kind, banned))
    if ident.count("results-hero-name") != 1 or ident.count("results-hero-price") != 1:
        die("G2/%s the band does not carry exactly one name and one price" % kind)

    if t.count('<div class="rh-split">') != 1 or t.count('<div class="pn-media-col">') != 1:
        die("G3/%s split or media column is not emitted exactly once" % kind)

    if "addEventListener('click'" not in t or "data-full" not in t:
        die("G4/%s the gallery handler is missing or not data-driven" % kind)
    if "e.preventDefault()" not in t:
        die("G4/%s the gallery handler can reload the page" % kind)
    if "data-credit" not in t:
        die("G4/%s the credit does not travel with the picture" % kind)

    if re.search(r"(width|max-width|flex:0 0)\s*:?\s*60%", PORTED):
        die("G5/%s a 60%% width reached the preview" % kind)
    if "noindex" not in t:
        die("G6/%s the privacy meta was disturbed" % kind)

    # tag balance: every edit added exactly the divs it opened
    for tag in ("rh-identity", "rh-split", "pn-media-col"):
        if t.count('class="%s"' % tag) != 1:
            die("G7/%s %s appears %d times" % (kind, tag, t.count('class="%s"' % tag)))
    opens = t.count("<div") + t.count("<section")
    closes = t.count("</div>") + t.count("</section>")
    if opens != closes:
        die("G7/%s unbalanced block tags: %d open, %d close" % (kind, opens, closes))

    REPORT.append((kind, path.name, edits, len(t) - len(orig), t))

print("build-preview-identity-band: 2 templates, %d edits each, 7 guards each"
      % len(REPORT[0][2]))
for kind, name, edits, delta, _ in REPORT:
    print("\n  %s  (%s)  %+d bytes" % (name, kind, delta))
    for tag, why in edits:
        print("     %-4s %s" % (tag, why))

if CHECK:
    print("\n--check: nothing written")
    sys.exit(0)

for kind, name, edits, delta, text in REPORT:
    TEMPLATES[kind].write_text(text, encoding="utf-8")
print("\nwritten: %s" % ", ".join(n for _, n, _, _, _ in REPORT))
