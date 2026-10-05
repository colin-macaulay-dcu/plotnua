#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-sauna-experts-preview.py.

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught.

THE BUILDER RUNS IN --stage MODE THROUGHOUT, so the deployed tree is never
written. The staged artefact is hashed before and after and the hash is
printed: a proof that damages what it proves is worse than no proof.

GUARD-ORDERING HAZARD, handled. A break that an EARLIER guard catches proves
nothing about the guard it was aimed at. Each sabotage is chosen so only its
target can catch it, and the printed refusal is the evidence of which fired.

THE TWO SABOTAGES THAT MATTER MOST on this supplier are the borrowed
superlative and the unattributed origin claim, because both are sentences a
careful writer could produce in good faith from the supplier's own homepage.
They are the reason G8 carries marketing language alongside unevidenced facts,
and the reason G8b checks for a form of words rather than against one.

Run: python3 supplier-preview-system/prove-sauna-experts-guards.py
"""

import contextlib
import hashlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-sauna-experts-preview.py"
STAGED = pathlib.Path("/tmp/plotnua-stage/sauna-experts-preview.html")

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


print("GUARD-CAPABILITY PROOF — SAUNA EXPERTS PRIVATE PREVIEW")
print("=" * 78)
r = results.append

# ---- G0 . the whole point of this build ------------------------------------
r(run("G0 . supplier imagery is added while permission is unknown",
      [("SE_IMAGES = []",
        'SE_IMAGES = [{"url": "https://saunaexperts.ie/wp-content/uploads/'
        'x.jpeg", "alt": "a sauna"}]')]))

# ---- G1 / G1b / G2 . the template anchors ---------------------------------
r(run("G1 . the instruction-comment anchor no longer matches",
      [("PROVIDER-LED.*?", "PROVIDER-LEDGER.*?")]))

r(run("G1b . the matched hero block no longer carries the headline tokens",
      [('if "{{PROPOSITION}}" not in hero.group(0)',
        'if "{{PROPOSITION_MOVED}}" not in hero.group(0)')]))

r(run("G2 . the frozen journey band anchor no longer matches",
      [('r"\\n<!-- FROZEN.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"',
        'r"\\n<!-- THAWED.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"')]))

# ---- G3 / G3d . the image position and the rights-process copy ------------
# BOTH SABOTAGES RE-POINTED, 5 Oct 2026. The old G3 renamed a heading the
# builder then rewrote; under the certified rule the slot carries no copy at
# all, so the guard runs the other way and the sabotage has to PUT copy in
# rather than rename it. G3d is new and gets its own break, because a rule
# with no failing test is a comment.
r(run("G3 . rights copy is added beside the placeholder label",
      [('    PLACEHOLDER = "<b>Your image here</b>"',
        '    src = src.replace(\'<div class="pn-photo-slot"><b>Your image '
        'here</b></div>\', \'<div class="pn-photo-slot"><b>Your image here'
        '</b><span>No photography is used on this page.</span></div>\')\n'
        '    PLACEHOLDER = "<b>Your image here</b>"')]))

r(run("G3 . the placeholder label is stripped out entirely",
      [('    PLACEHOLDER = "<b>Your image here</b>"',
        '    src = src.replace(\'<div class="pn-photo-slot"><b>Your image '
        'here</b></div>\', \'<div class="pn-photo-slot"></div>\')\n'
        '    PLACEHOLDER = "<b>Your image here</b>"')]))

r(run("G3d . the page explains the image-rights process to the supplier",
      [('  <p>These are the three things we&rsquo;d like to check with you '
        'before the\n     page goes live.</p>',
        '  <p>Where your imagery would go: the space beside the result is '
        'where your\n     photography would sit.</p>')]))

# ---- G3c . attribution ----------------------------------------------------
r(run("G3c . the footer anchor for the attribution line cannot be found",
      [('foot = "<footer>\\n"', 'foot = "<footer >\\n"')]))

# ---- G3b . the closing heading --------------------------------------------
r(run("G3b . the closing heading anchor no longer matches the template",
      [('old_head = "<h2>What we&rsquo;d like to explore</h2>"',
        'old_head = "<h2>What we would like to explore</h2>"')]))

# ---- G4 . tokens ----------------------------------------------------------
r(run("G4 . a token is dropped from the fill set",
      [('"OFFER_NAME": "Outdoor Sauna Chill &mdash; Woodburner",', "")]))

# ---- G5 . privacy ---------------------------------------------------------
r(run("G5 . the noimageindex robots directive is dropped",
      [('for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex"):',
        'for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex_MISSING"):')]))

# ---- G6 . another supplier -------------------------------------------------
# Harvia is deliberately NOT in G6's list — it is the stove on this product's
# own specification — so the sabotage uses a supplier that is.
r(run("G6 . another supplier's name reaches the page",
      [('"DEMO_HEADING": "How an Irish homeowner could reach Sauna Experts",',
        '"DEMO_HEADING": "How an Irish homeowner could reach Cosy Cabins",')]))

# ---- G7 . the frozen band must travel byte-for-byte ------------------------
r(run("G7 . the frozen journey band is edited in transit, not relocated",
      [('OPEN_QUESTIONS + "\\n" + journey.strip("\\n")',
        'OPEN_QUESTIONS + "\\n" + journey.strip("\\n").replace('
        '"journey", "journey-v2")')]))

# ---- G8 . the claims and the marketing ------------------------------------
# Four breaks. The first two are the dangerous ones: they are the supplier's
# own words, true to their site and false in PlotNua's voice.
r(run("G8 . the supplier's ranking claim is repeated as PlotNua's",
      [('"WHY_1_LABEL": "YOUR SPECIFICATION, NOT OUR SUMMARY",',
        '"WHY_1_LABEL": "IRELAND\'S NUMBER ONE SAUNA SHOP",')]))

r(run("G8 . the contradictory experience figure is used anyway",
      # ANCHOR RE-POINTED after the price-basis line was given its own
      # subject. The sabotage is unchanged in kind -- it injects the banned
      # "20 years of experience" figure into the same field -- only the
      # string it attaches to moved.
      [('"VERIFIED_PRICE_BASIS": "The &euro;25,000 is exactly as published '
        'on the "',
        '"VERIFIED_PRICE_BASIS": "Built by a team with over 20 years of '
        'experience. The &euro;25,000 is exactly as published on the "')]))

r(run("G8 . the page asserts a warranty nobody published",
      [('"VERIFIED_FACT_3": "Harvia woodburning stove with sauna stones, "',
        '"VERIFIED_FACT_3": "Warranty included. Harvia woodburning stove '
        'with sauna stones, "')]))

r(run("G8 . the page decides the planning question the supplier never raised",
      [('"VERIFIED_FACT_4": "Fully insulated with a vapour barrier; Thermo '
        'Aspen "',
        '"VERIFIED_FACT_4": "Planning exempt. Fully insulated with a vapour '
        'barrier; Thermo Aspen "')]))

# ---- G8b . Irish manufacture must be ATTRIBUTED, not asserted -------------
# The attribution occurs exactly once, so this sabotage is real rather than a
# needle mutation: the claim survives in the copy, the attribution does not.
r(run("G8b . Irish manufacture is stated without saying whose claim it is",
      # ANCHOR RE-POINTED. The relocated specification detail now follows
      # the attribution in the same string, so the anchor had to grow to
      # match. The sabotage is unchanged in kind: it still strips "Sauna
      # Experts say" and asserts Irish manufacture as PlotNua's own finding,
      # which is the single thing G8b exists to catch.
      [('"say their saunas are designed and manufactured "\n'
        '                            "in Ireland. The published specification '
        'also "',
        '"design and manufacture in Ireland. The published specification '
        'also "')]))

# ---- G8c . the planning firewall must be present --------------------------
r(run("G8c . the planning firewall is dropped from the honest line",
      [('"your site addresses planning, and the local authority "\n'
        '                       "is the only body that can confirm what a '
        'particular "\n'
        '                       "site requires.",', '"",')]))

# ---- G9 . no imagery on the artefact, and a real link back ---------------
# Aimed past G0: the list stays empty, so only the output check can catch an
# image that arrives through the markup.
r(run("G9 . an external image arrives through the markup, not the image list",
      [('  <h2>Three things we would ask before publishing</h2>',
        '  <h2>Three things we would ask before publishing</h2>\\n'
        '  <img src="https://saunaexperts.ie/wp-content/uploads/x.jpeg" alt="">')]))

r(run("G9 . every link back to the supplier's site is reduced to prose",
      [('\'<a href="%s" rel="noopener">your Outdoor Sauna Chill page</a>, \'\n'
        '        \'<a href="%s" rel="noopener">your custom sauna units</a> and \'\n'
        '        \'<a href="%s" rel="noopener">saunaexperts.ie</a> on %s. \'',
        '\'%s your Outdoor Sauna Chill page, \'\n'
        '        \'%s your custom sauna units and \'\n'
        '        \'%s saunaexperts.ie on %s. \'')]))

# ---- G10 . no commercial implication --------------------------------------
# This is also the guard that keeps the supplier's own Harvia partnership
# banner off the page, which is why the sabotage uses that exact wording.
r(run("G10 . the supplier's Harvia partnership banner is reproduced",
      [('"WHY_2_LABEL": "THE PRICE, WITH WHAT SITS AROUND IT",',
        '"WHY_2_LABEL": "AN OFFICIAL HARVIA PARTNER",')]))

# ---- G11 . the page must say what it is -----------------------------------
r(run("G11 . the template's illustrative-preview tag is stripped out",
      [("    # G4 · Fill every token",
        '    src = src.replace(\'<span class="illus-tag">Illustrative '
        'preview</span>\', "")\n\n    # G4 · Fill every token")')]))

r(run("G11 . the pre-publication review ask is removed from the page",
      [('src = src.replace(old_head, "<h2>Before anything goes live</h2>")',
        'src = src.replace(old_head, "<h2>Next steps</h2>")')]))

# ---- and the unmutated builder must still pass ----------------------------
print("-" * 78)
r(run("the unmutated builder passes every guard", expect="BUILT"))

after = hashlib.sha256(STAGED.read_bytes()).hexdigest()
print("=" * 78)
print("%d of %d checks passed" % (sum(1 for x in results if x), len(results)))
print("the staged page is byte-identical after the proof: %s  (%s)"
      % ("YES" if before == after else "NO", after[:12]))
sys.exit(0 if all(results) and before == after else 1)
