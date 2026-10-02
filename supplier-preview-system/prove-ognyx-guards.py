#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-ognyx-preview.py.

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught.

THE BUILDER RUNS IN --stage MODE THROUGHOUT, so the deployed tree is never
written. The staged artefact is hashed before and after and the hash is
printed: a proof that damages what it proves is worse than no proof.

GUARD-ORDERING HAZARD, handled. A break that an EARLIER guard catches proves
nothing about the guard it was aimed at. Each sabotage is chosen so only its
target can catch it, and the printed refusal is the evidence of which fired.

Run: python3 supplier-preview-system/prove-ognyx-guards.py
"""

import contextlib
import hashlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-ognyx-preview.py"
STAGED = pathlib.Path("/tmp/plotnua-stage/ognyx-preview.html")

if not STAGED.exists():
    print("run the builder with --stage once before proving it")
    sys.exit(2)

before = hashlib.sha256(STAGED.read_bytes()).hexdigest()
results = []


def run(label, subs=(), expect="REFUSED"):
    code = BUILDER.read_text(encoding="utf-8")
    for old, new in subs:
        if old not in code:
            raise AssertionError("builder anchor absent: %r" % old[:70])
        code = code.replace(old, new, 1)
    argv, buf, rc = sys.argv, io.StringIO(), 0
    sys.argv = [str(BUILDER), "--stage"]
    try:
        with contextlib.redirect_stdout(buf):
            g = {"__name__": "__main__", "__file__": str(BUILDER)}
            exec(compile(code, str(BUILDER), "exec"), g)
    except SystemExit as e:
        rc = e.code or 0
    finally:
        sys.argv = argv
    out = [l for l in buf.getvalue().strip().splitlines()
           if l.startswith("REFUSED")]
    got = "REFUSED" if rc else "BUILT"
    hit = got == expect
    print("  %s %-7s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("          -> %s" % (out[0][:108] if out else "(no refusal printed)"))
    return hit


print("GUARD-CAPABILITY PROOF — OGNYX PRIVATE PREVIEW")
print("=" * 78)
r = results.append

# ---- G0 . the permitted scope -------------------------------------------
# OGNYX serve from their own domain, so the dangerous case is not a
# neighbouring CDN tenant but an image from somewhere else entirely arriving
# under their credit.
r(run("G0 . an image from another domain is added",
      [('PERMITTED_PREFIX + "Screenshot2025-08-13at21.01.20.png"',
        '"https://images.example.com/not-ognyx.png"')]))

# The count guard: the list of four is what says every one was looked at.
r(run("G0a . the four inspected assets become three",
      [('''    {"url": PERMITTED_PREFIX + "Screenshot2025-08-12at19.20.47.png"
            "?v=1755025372&width=1024",
     "kind": "visualisation",
     "alt": "Visualisation of the OGNYX round hot tub, clad in timber with a "
            "stainless chimney rising from the integrated stove inside it "
            "and a timber step stool alongside, beside a swimming pool. The "
            "image carries OGNYX\'s own caption bar reading \u00d8 2M FOR 5 PERS"},
''', "")]))

r(run("G0 . an asset is left unclassified",
      [('"kind": "photograph",\n     "alt": "Photograph looking down into',
        '"kind": "",\n     "alt": "Photograph looking down into')]))

# ---- G0b . the AI exclusion ----------------------------------------------
r(run("G0b . an AI-named asset reaches the image list",
      [('"alt": "Photograph looking down into the same empty cold plunge tub, "',
        '"alt": "ChatGPT Image looking down into the empty cold plunge tub, "')]))

# ---- G0c . photograph versus visualisation -------------------------------
# THE GUARD THIS BUILD EXISTS FOR. Two of the four images are renders. A
# render described as a photograph is the misrepresentation the whole
# classification is there to stop, so it is broken in both directions.
r(run("G0c . a visualisation's alt text calls it a photograph",
      [('"alt": "Visualisation of the OGNYX 1.6m outdoor barrel sauna on a "',
        '"alt": "Photograph of the OGNYX 1.6m outdoor barrel sauna on a "')]))

r(run("G0c . a photograph's alt text stops saying so",
      [('"alt": "Photograph of the OGNYX stainless steel cold plunge tub, clad "',
        '"alt": "The OGNYX stainless steel cold plunge tub, clad "')]))

# ---- G1 / G1b / G2 . the template anchors --------------------------------
r(run("G1 . the instruction-comment anchor no longer matches",
      [("PROVIDER-LED.*?", "PROVIDER-LEDGER.*?")]))
r(run("G1b . the matched hero block no longer carries the headline tokens",
      [('if "{{PROPOSITION}}" not in hero.group(0)',
        'if "{{PROPOSITION_MOVED}}" not in hero.group(0)')]))
r(run("G2 . the frozen journey band anchor no longer matches",
      [('r"\\n<!-- FROZEN.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"',
        'r"\\n<!-- THAWED.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"')]))
r(run("G3 . the held media wrapper the imagery replaces cannot be found",
      [("r'        <div class=\"results-hero-media\">\\n'",
        "r'        <div class=\"results-hero-MEDIA\">\\n'")]))
r(run("G3c . the footer anchor for the credit line cannot be found",
      [('foot = "<footer>\\n"', 'foot = "<footer >\\n"')]))
r(run("G3b . the closing heading anchor no longer matches",
      [('old_head = "<h2>What we&rsquo;d like to explore</h2>"',
        'old_head = "<h2>What we would like to explore</h2>"')]))
r(run("G4 . a token is dropped from the fill set",
      [('"OFFER_NAME": "Stainless Steel Cold Plunge Tub for One",', "")]))
r(run("G5 . the noimageindex robots directive is dropped",
      [('for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex"):',
        'for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex_MISSING"):')]))
r(run("G6 . another supplier's name reaches the page",
      [('"DEMO_HEADING": "How OGNYX could appear within PlotNua",',
        '"DEMO_HEADING": "How Cosy Cabins could appear within PlotNua",')]))
r(run("G7 . the frozen journey band is edited in transit",
      [('OTHER_CATEGORIES + "\\n" + OPEN_QUESTIONS + "\\n"\n'
        '                      + journey.strip("\\n")',
        'OTHER_CATEGORIES + "\\n" + OPEN_QUESTIONS + "\\n"\n'
        '                      + journey.strip("\\n").replace("journey", "journey-v2")')]))

# ---- G8 . the claims this supplier's own policies leave conditional -------
# Four breaks, four different reasons: health, money, logistics, time. Each
# is the claim a careless writer would actually make here, and three of them
# are claims OGNYX's own pages come close to making.
r(run("G8 . the page repeats OGNYX's own health claim",
      [('"VERIFIED_FACT_5": "Designed for one person",',
        '"VERIFIED_FACT_5": "Designed for one person. Health benefit backed",')]))
r(run("G8 . the page states a VAT basis nobody published",
      [('"VERIFIED_FACT_1_VALUE": "86 cm diameter, 105 cm high, 400-litre capacity",',
        '"VERIFIED_FACT_1_VALUE": "86 cm diameter, price inc. VAT",')]))
r(run("G8 . the page promises free delivery",
      [('"VERIFIED_FACT_3": "The basic set includes the tub with thermowood "',
        '"VERIFIED_FACT_3": "Free delivery. The basic set includes the tub "')]))
r(run("G8 . the page asserts a lead time nobody published",
      [('"VERIFIED_FACT_4": "A cooler, a cover, stairs and an electric chiller are "',
        '"VERIFIED_FACT_4": "In stock. A cooler, a cover and stairs are "')]))

# ---- G8b . the label must reach the reader, not just the image list ------
# Aimed past G0c: the alt text stays honest, so only the on-page check can
# catch a page that never shows the word.
r(run("G8b . the word 'visualisation' never reaches the visible page",
      [('    vis = sum(1 for i in OGNYX_IMAGES if i["kind"] == "visualisation")',
        '    low = low.replace("visualisation", "image")\n'
        '    vis = sum(1 for i in OGNYX_IMAGES if i["kind"] == "visualisation")')]))

# ---- G9 . the credit and the link back -----------------------------------
# THE VACUOUS-GUARD CASE. src.count("") returns the page length, so a
# count-only guard would pass an uncredited page.
r(run("G9 . the required credit constant is emptied",
      [('CREDIT = "\u00a9 OGNYX"', 'CREDIT = ""')]))
r(run("G9 . the credit is written as the &copy; entity",
      [('\'          <span class="pn-image-credit">%s</span>\' % CREDIT,',
        '\'          <span class="pn-image-credit">&copy; OGNYX</span>\',')]))
r(run("G9 . every link back to ognyx.com is reduced to prose",
      [('\'served from <a href="%s" rel="noopener">ognyx.com</a>, with \'',
        '\'served from %s ognyx.com, with \''),
       ('  <p><a href="%s" rel="noopener">See the sauna on ognyx.com</a></p>',
        '  <p>See the sauna on %s ognyx.com</p>'),
       ('  <p><a href="%s" rel="noopener">See the hot tub on ognyx.com</a></p>',
        '  <p>See the hot tub on %s ognyx.com</p>')]))

# ---- G10 / G11 -----------------------------------------------------------
r(run("G10 . the page implies an agreed relationship",
      [('"WHY_3_LABEL": "REACHED THROUGH WELLNESS",',
        '"WHY_3_LABEL": "APPROVED SUPPLIER",')]))
r(run("G11 . the template's illustrative-preview tag is stripped out",
      [("    # G4 · Fill every token",
        '    src = src.replace(\'<span class="illus-tag">Illustrative '
        'preview</span>\', "")\n\n    # G4 · Fill every token")')]))
r(run("G11 . the pre-publication review ask is removed",
      [('src = src.replace(old_head, "<h2>Before anything goes live</h2>")',
        'src = src.replace(old_head, "<h2>Next steps</h2>")')]))

print("-" * 78)
r(run("the unmutated builder passes every guard", expect="BUILT"))

after = hashlib.sha256(STAGED.read_bytes()).hexdigest()
print("=" * 78)
print("%d of %d checks passed" % (sum(1 for x in results if x), len(results)))
print("the staged page is byte-identical after the proof: %s  (%s)"
      % ("YES" if before == after else "NO", after[:12]))
sys.exit(0 if all(results) and before == after else 1)
