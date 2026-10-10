#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-irish-sauna-company-preview.py.

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught.

THE BUILDER RUNS IN --stage MODE THROUGHOUT, so the deployed tree is never
written. The staged artefact is hashed before and after and the hash is
printed: a proof that damages what it proves is worse than no proof.

GUARD-ORDERING HAZARD, handled. A break that an EARLIER guard catches proves
nothing about the guard it was aimed at. Each sabotage is chosen so only its
target can catch it, and the printed refusal is the evidence of which fired.

Run: python3 supplier-preview-system/prove-irish-sauna-company-guards.py
"""

import contextlib
import hashlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-irish-sauna-company-preview.py"
STAGED = pathlib.Path("/tmp/plotnua-stage/irish-sauna-company-preview.html")

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


print("GUARD-CAPABILITY PROOF — IRISH SAUNA COMPANY PRIVATE PREVIEW")
print("=" * 78)
r = results.append

# ---- G0 . the grant, read from the register and not from this file --------
# THIS GUARD CHANGED SIDES ON 10 OCTOBER 2026. It used to refuse imagery
# because permission was unknown; Brona granted it, so it now refuses imagery
# that is NOT covered by a live grant in the generated manifest. The three
# breaks are the three ways that cover can be lost.
r(run("G0 . the register is consulted at a path that does not exist",
      [('man = SITE / "image-rights-manifest.json"',
        'man = SITE / "image-rights-manifest-GONE.json"')]))

r(run("G0 . no live grant matches the supplier's domain",
      [('if (r.get("permitted_domain") == "irishsaunacompany.com"',
        'if (r.get("permitted_domain") == "irishsaunacompany.invalid"')]))

r(run("G0 . the printed credit drifts from the credit the grant requires",
      [('CREDIT = "\u00a9 Irish Sauna Company"',
        'CREDIT = "\u00a9 Irish Sauna Co."')]))

r(run("G0 . an image is taken from outside the permitted domain",
      [('{"url": "https://irishsaunacompany.com/cdn/shop/files/"\n'
        '            "HarviaLegendElectricOutdoorSauna1.png?v=1788467600&width=1200",',
        '{"url": "https://cdn.shopify.com/s/files/1/9999/9999/'
        'HarviaLegendElectricOutdoorSauna1.png",')]))

r(run("G0 . an image is listed with no alt text",
      [('"alt": "The Harvia Legend Electric outdoor sauna seen in a garden setting"',
        '"alt": "   "')]))

# ---- G1 / G1b / G2 . the template anchors ---------------------------------
r(run("G1 . the instruction-comment anchor no longer matches",
      [("PROVIDER-LED.*?", "PROVIDER-LEDGER.*?")]))

r(run("G1b . the matched hero block no longer carries the headline tokens",
      [('if "{{PROPOSITION}}" not in hero.group(0)',
        'if "{{PROPOSITION_MOVED}}" not in hero.group(0)')]))

r(run("G2 . the frozen journey band anchor no longer matches",
      [('r"\\n<!-- FROZEN.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"',
        'r"\\n<!-- THAWED.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"')]))

# ---- G3 . state A must actually replace the held media wrapper ------------
r(run("G3 . the held media wrapper anchor no longer matches the template",
      [('r\'          <div class="pn-photo-slot"[^>]*>.*?</div>\\n\'',
        'r\'          <div class="pn-photo-SLOTT"[^>]*>.*?</div>\\n\'')]))

# ---- G3c . attribution ----------------------------------------------------
r(run("G3c . the footer anchor for the attribution line cannot be found",
      [('foot = "<footer>\\n"', 'foot = "<footer >\\n"')]))

# ---- G3b . the closing heading --------------------------------------------
r(run("G3b . the closing heading anchor no longer matches the template",
      [('old_head = "<h2>What we&rsquo;d like to explore</h2>"',
        'old_head = "<h2>What we would like to explore</h2>"')]))

# ---- G4 . tokens ----------------------------------------------------------
r(run("G4 . a token is dropped from the fill set",
      [('"OFFER_NAME": "Harvia Legend Electric Outdoor Sauna",', "")]))

# ---- G5 . privacy ---------------------------------------------------------
r(run("G5 . the noimageindex robots directive is dropped",
      [('for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex"):',
        'for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex_MISSING"):')]))

# ---- G6 . another supplier -------------------------------------------------
# Harvia is deliberately NOT in G6's list, so the sabotage uses a supplier
# that is. A break using "Harvia" would prove the opposite of what is wanted.
r(run("G6 . another supplier's name reaches the page",
      [('"DEMO_HEADING": "How an Irish homeowner could reach Irish Sauna '
        'Company",',
        '"DEMO_HEADING": "How an Irish homeowner could reach Cosy Cabins",')]))

# ---- G7 . the frozen band must travel byte-for-byte ------------------------
r(run("G7 . the frozen journey band is edited in transit, not relocated",
      [('OPEN_QUESTIONS + "\\n" + journey.strip("\\n")',
        'OPEN_QUESTIONS + "\\n" + journey.strip("\\n").replace('
        '"journey", "journey-v2")')]))

# ---- G8 . unevidenced claims ----------------------------------------------
# Four separate breaks, because they fail for four different reasons: origin,
# service, money and time. Each is the claim a careless writer would actually
# make about this supplier.
r(run("G8 . the page calls the Harvia garden sauna Irish-built",
      [('"VERIFIED_FACT_4": "Insulated outdoor construction',
        '"VERIFIED_FACT_4": "Irish built. Insulated outdoor construction')]))

r(run("G8 . the page implies they install it",
      [('"WHY_1_LABEL": "YOUR SPECIFICATION, NOT OUR SUMMARY",',
        '"WHY_1_LABEL": "INSTALLATION INCLUDED",')]))

r(run("G8 . the page claims delivery is free",
      [('"VERIFIED_FACT_5": "12m&sup3; calculated sauna volume',
        '"VERIFIED_FACT_5": "Free delivery. 12m&sup3; calculated sauna volume')]))

r(run("G8 . the page asserts a warranty nobody published",
      [('"VERIFIED_FACT_3": "Harvia Legend Pro PO11 11kW electric heater',
        '"VERIFIED_FACT_3": "Warranty included. Harvia Legend Pro PO11 heater')]))

# ---- G8b . the origin must be STATED, not merely not-misstated ------------
# Two breaks, one per half of the origin. This is the guard that matters most
# on a page headed "Irish Sauna Company" showing a product somebody else
# makes, and a guard for an omission needs the omission actually made.
# BOTH SOURCES must go. The first attempt removed the origin only from
# VERIFIED_PRICE_BASIS and the builder BUILT -- correctly, because the
# attribution line also states it. Two satisfying sources meant the sabotage
# proved nothing about the guard, so it now strips both.
r(run("G8b . the page stops saying the Legend is manufactured by Harvia",
      [('"VERIFIED_PRICE_BASIS": "inc. VAT, exactly as published. '
        'Manufactured by "\n                            "Harvia and supplied '
        'in Ireland by Irish Sauna "\n                            "Company.",',
        '"VERIFIED_PRICE_BASIS": "inc. VAT, exactly as published.",'),
       ('\'The Legend is manufactured by Harvia and supplied in Ireland by %s. \'',
        '\'The Legend is supplied in Ireland by %s. \'')]))

r(run("G8b . the page keeps Harvia but drops who supplies it in Ireland",
      [('\'The Legend is manufactured by Harvia and supplied in Ireland by %s. \'',
        '\'The Legend is manufactured by Harvia. \''),
       ('"VERIFIED_PRICE_BASIS": "inc. VAT, exactly as published. '
        'Manufactured by "\n                            "Harvia and supplied '
        'in Ireland by Irish Sauna "\n                            "Company.",',
        '"VERIFIED_PRICE_BASIS": "inc. VAT, exactly as published. '
        'Manufactured by Harvia.",'),
       ('% (SUPPLIER, PRODUCT_URL, RANGE_URL, EVIDENCE_DATE, SUPPLIER,\n'
        '           SUPPLIER, PERMISSION_DATE, SUPPLIER, CREDIT, SUPPLIER_SITE))',
        '% (SUPPLIER, PRODUCT_URL, RANGE_URL, EVIDENCE_DATE,\n'
        '           SUPPLIER, PERMISSION_DATE, SUPPLIER, CREDIT, SUPPLIER_SITE))')]))

# ---- G9 . the imagery on the OUTPUT, and a real link back ----------------
# Aimed past G0: the image list stays legitimate, so only the output check can
# catch something that arrives through the markup instead of through the list.
r(run("G9 . an off-grant image arrives through the markup, not the image list",
      [('  <h2>Three things we would ask before publishing</h2>',
        '  <h2>Three things we would ask before publishing</h2>\\n'
        '  <img src="https://images.example.net/sauna.jpg" alt="">')]))

r(run("G9 . an og:image hands the supplier's image to link unfurlers",
      [('    # G5 \u00b7 PRIVACY.',
        '    src = src.replace("</head>", \'<meta property="og:image" \'\n'
        '        \'content="https://irishsaunacompany.com/cdn/shop/files/a.png">\'\n'
        '        \'</head>\')\n\n    # G5 \u00b7 PRIVACY.')]))

r(run("G9 . every link back to the supplier's site is reduced to prose",
      [('\'<a href="%s" rel="noopener">their Harvia Legend Electric page</a> \'\n'
        '        \'and <a href="%s" rel="noopener">their garden sauna range</a> on %s. \'',
        '\'%s their Harvia Legend Electric page \'\n'
        '        \'and %s their garden sauna range on %s. \''),
       ('\'%s &middot; <a href="%s" rel="noopener">irishsaunacompany.com</a>\'',
        '\'%s &middot; %s irishsaunacompany.com\'')]))

# ---- G10 . no commercial implication --------------------------------------
r(run("G10 . the page implies an agreed relationship",
      [('"WHY_3_LABEL": "REACHED THROUGH WELLNESS",',
        '"WHY_3_LABEL": "APPROVED SUPPLIER",')]))

# ---- G11 . the page must say what it is -----------------------------------
r(run("G11 . the template's illustrative-preview tag is stripped out",
      [("    # G4 · Fill every token",
        '    src = src.replace(\'<span class="illus-tag">Illustrative '
        'preview</span>\', "")\n\n    # G4 · Fill every token")')]))

r(run("G11 . the pre-publication review ask is removed from the page",
      [('src = src.replace(old_head, "<h2>Before anything goes live</h2>")',
        'src = src.replace(old_head, "<h2>Next steps</h2>")')]))

# ---- G12 . the medium may not be claimed ----------------------------------
# The one guard that exists because of what this supplier's own filenames
# show: they publish generated imagery. A page that calls a render a
# photograph is making a provenance claim nobody has checked.
r(run("G12 . the page calls the supplier's imagery a photograph",
      [('"WHY_1_LABEL": "YOUR SPECIFICATION, NOT OUR SUMMARY",',
        '"WHY_1_LABEL": "YOUR PHOTOGRAPHY, SHOWN AS PUBLISHED",')]))

r(run("G12 . the alt text describes the medium instead of the subject",
      [('"alt": "The Harvia Legend Electric outdoor sauna seen in a garden setting"',
        '"alt": "A photograph of the Harvia Legend Electric outdoor sauna"')]))

# ---- and the unmutated builder must still pass ----------------------------
print("-" * 78)
r(run("the unmutated builder passes every guard", expect="BUILT"))

after = hashlib.sha256(STAGED.read_bytes()).hexdigest()
print("=" * 78)
print("%d of %d checks passed" % (sum(1 for x in results if x), len(results)))
print("the staged page is byte-identical after the proof: %s  (%s)"
      % ("YES" if before == after else "NO", after[:12]))
sys.exit(0 if all(results) and before == after else 1)
