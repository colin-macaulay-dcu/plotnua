#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-tanktribe-preview.py.

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught.

THE BUILDER RUNS IN --stage MODE THROUGHOUT, so the deployed tree is never
written. The staged artefact is hashed before and after and the hash is
printed: a proof that damages what it proves is worse than no proof.

GUARD-ORDERING HAZARD, handled. A break that an EARLIER guard catches proves
nothing about the guard it was aimed at. Each sabotage is chosen so only its
target can catch it, and the printed refusal is the evidence of which fired.

Run: python3 supplier-preview-system/prove-tanktribe-guards.py
"""

import contextlib
import hashlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-tanktribe-preview.py"
STAGED = pathlib.Path("/tmp/plotnua-stage/tanktribe-preview.html")

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


print("GUARD-CAPABILITY PROOF — TANKTRIBE PRIVATE PREVIEW")
print("=" * 78)
r = results.append
P = "https://images.squarespace-cdn.com/content/v1/67ac8d737a7c665f57f5babe/"

# ---- G0 . the granted scope is a NAMESPACE on a shared CDN ----------------
# The whole point: images.squarespace-cdn.com hosts every Squarespace site in
# the world, so an image from a neighbouring namespace is somebody else's
# photography arriving under Tanktribe's grant.
r(run("G0 . an image from a neighbouring Squarespace namespace is added",
      [('PERMITTED_PREFIX + "b9e11038-bd53-49c8-984b-65ed12892e43/"\n            "IMG_2580%2B3.JPG"',
        '"https://images.squarespace-cdn.com/content/v1/'
        '0000000000000000000000/x/IMG_2580.JPG"')]))

r(run("G0 . the governed six becomes five",
      [('    {"url": PERMITTED_PREFIX + "33335f39-c5fe-48af-9c3a-f6f6cc4e8c8e/"\n'
        '            "IMG_2518.JPG",\n'
        '     "alt": "Close-up of the Tanktribe WILD TUB wood-fired heating coil "\n'
        '            "burning on a paving slab"},\n',
        '')]))

# ---- the WILD TUB section's supporting image must BE the coil -------------
# The secondary section states in words that the photograph shows the
# wood-fired coil. A reorder that leaves a cold-plunge tank at index 4 would
# make the page say one thing and show another.
r(run("the WILD TUB section's supporting image is no longer the coil",
      [("WILD_TUB_COIL = TANKTRIBE_IMAGES[4]",
        "WILD_TUB_COIL = TANKTRIBE_IMAGES[0]")]))

# ---- G0b . the AI-asset exclusion ----------------------------------------
# The condition that constrains PlotNua rather than the supplier, and so the
# one most likely to be quietly dropped.
r(run("G0b . a ChatGPT-named asset reaches the image list",
      [('"alt": "Four galvanised stock tanks lined up on grass beside water, "',
        '"alt": "ChatGPT Image of four stock tanks beside water, "')]))

# ---- template anchors ----------------------------------------------------
r(run("G1 . the instruction-comment anchor no longer matches",
      [("PROVIDER-LED.*?", "PROVIDER-LEDGER.*?")]))
r(run("G1b . the matched hero block no longer carries the headline tokens",
      [('if "{{PROPOSITION}}" not in hero.group(0)',
        'if "{{PROPOSITION_MOVED}}" not in hero.group(0)')]))
r(run("G2 . the frozen journey band anchor no longer matches",
      [('r"\\n<!-- FROZEN.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"',
        'r"\\n<!-- THAWED.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"')]))
r(run("G3 . the held media wrapper state A replaces cannot be found",
      [("r'        <div class=\"results-hero-media\">\\n'",
        "r'        <div class=\"results-hero-MEDIA\">\\n'")]))
r(run("G3c . the footer anchor for the credit line cannot be found",
      [('foot = "<footer>\\n"', 'foot = "<footer >\\n"')]))
r(run("G3b . the closing heading anchor no longer matches",
      [('old_head = "<h2>What we&rsquo;d like to explore</h2>"',
        'old_head = "<h2>What we would like to explore</h2>"')]))
r(run("G4 . a token is dropped from the fill set",
      [('"OFFER_NAME": "CORE",', "")]))
r(run("G5 . the noimageindex robots directive is dropped",
      [('for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex"):',
        'for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex_MISSING"):')]))
r(run("G6 . another supplier's name reaches the page",
      [('"DEMO_HEADING": "How an Irish homeowner could reach Tanktribe",',
        '"DEMO_HEADING": "How an Irish homeowner could reach Cosy Cabins",')]))
r(run("G7 . the frozen journey band is edited in transit",
      [('OPEN_QUESTIONS + "\\n" + journey.strip("\\n")',
        'OPEN_QUESTIONS + "\\n" + journey.strip("\\n").replace('
        '"journey", "journey-v2")')]))

# ---- G8 . the claims a cold-water product attracts ------------------------
r(run("G8 . the page makes a health claim",
      [('"VERIFIED_FACT_3": "The simplest configuration in the range, and the one "',
        '"VERIFIED_FACT_3": "Improves recovery after training, and the one "')]))
r(run("G8 . the page states a VAT basis nobody published",
      [('"VERIFIED_FACT_4": "FLOW adds filtration from &euro;850 and ACTIVE adds "',
        '"VERIFIED_FACT_4": "Price is inc. VAT. FLOW adds filtration, and ACTIVE adds "')]))

# ---- G9 . the credit and the link back -----------------------------------
# THE VACUOUS-GUARD CASE. src.count("") returns the page length, so a
# count-only guard would pass an uncredited page. That mistake was made once
# on the BIOBUILDS builder; this proves it cannot be made here.
r(run("G9 . the required credit constant is emptied",
      [('CREDIT = "\u00a9 Tanktribe"', 'CREDIT = ""')]))
# The %s AND its format operator both go: dropping only the placeholder makes
# the builder CRASH on a format-arity error, and a crash is not a refusal.
r(run("G9 . the credit is written as the &copy; entity",
      [('\'          <span class="pn-image-credit">%s</span>\' % CREDIT,',
        '\'          <span class="pn-image-credit">&copy; Tanktribe</span>\',')]))
r(run("G9 . the link back is reduced to prose",
      [('<a href="%s" rel="noopener">tanktribe.ie</a>. If Tanktribe ask for ',
        '%s tanktribe.ie. If Tanktribe ask for ')]))

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
