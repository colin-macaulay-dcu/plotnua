#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-cosy-cabins-preview.py.

A guard that has never refused anything is a comment. This breaks the
builder once per guard and every break must be caught.

THE BUILDER RUNS IN --stage MODE THROUGHOUT, so the deployed tree is never
written. The staged artefact is hashed before and after and the hash is
printed: a proof that damages what it proves is worse than no proof.

GUARD-ORDERING HAZARD, handled. A break that an EARLIER guard catches
proves nothing about the guard it was aimed at. Each sabotage below is
chosen so that only its target can catch it, and the printed refusal line
is the evidence of which guard fired.

Run: python3 supplier-preview-system/prove-cosy-cabins-guards.py
"""

import contextlib
import hashlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-cosy-cabins-preview.py"
STAGED = pathlib.Path("/tmp/plotnua-stage/cosy-cabins-preview.html")

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
    print("          -> %s" % (out[0][:110] if out else "(no refusal printed)"))
    return hit


print("GUARD-CAPABILITY PROOF — COSY CABINS PRIVATE PREVIEW")
print("=" * 78)
r = results.append

# ---- G0 . the whole point of this build ------------------------------------
# Imagery added while the Atlas permission outcome is still unknown. This is
# the mistake that would turn PREVIEW into GRANTED.
r(run("G0 . supplier imagery is added while permission is unknown",
      [("COSY_CABINS_IMAGES = []",
        'COSY_CABINS_IMAGES = [{"url": "https://static.wixstatic.com/media/'
        '9ba815_x.jpg", "alt": "a garden room"}]')]))

# ---- G1 / G1b / G2 . the template anchors ---------------------------------
r(run("G1 . the instruction-comment anchor no longer matches",
      [("PROVIDER-LED.*?", "PROVIDER-LEDGER.*?")]))

r(run("G1b . the matched hero block no longer carries the headline tokens",
      [('if "{{PROPOSITION}}" not in hero.group(0)',
        'if "{{PROPOSITION_MOVED}}" not in hero.group(0)')]))

r(run("G2 . the frozen journey band anchor no longer matches",
      [('r"\\n<!-- FROZEN.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"',
        'r"\\n<!-- THAWED.*?\\n<div class=\\"journey\\">.*?\\n</div>\\n"')]))

# ---- G3 . the held imagery panel ------------------------------------------
r(run("G3 . the held photo-slot heading cannot be found",
      [('ask = "<b>Your project photography here</b>"',
        'ask = "<b>Your project photographs here</b>"')]))

# ---- G3c . attribution ----------------------------------------------------
# NOTE ON A SABOTAGE THAT DID NOT WORK. The first attempt here shortened the
# anchor to "<footer", which still matches exactly once, so the builder
# BUILT and the proof correctly reported MISSED. The fault was the sabotage,
# not the guard: a uniqueness check is only exercised by an anchor that
# matches zero times or twice.
r(run("G3c . the footer anchor for the attribution line cannot be found",
      [('foot = "<footer>\\n"', 'foot = "<footer >\\n"')]))

# ---- G3b . the closing heading --------------------------------------------
r(run("G3b . the closing heading anchor no longer matches the template",
      [('old_head = "<h2>What we&rsquo;d like to explore</h2>"',
        'old_head = "<h2>What we would like to explore</h2>"')]))

# ---- G4 . tokens ----------------------------------------------------------
r(run("G4 . a token is dropped from the fill set",
      [('"OFFER_NAME": "Sauna 2m",', "")]))

# ---- G5 . privacy ---------------------------------------------------------
r(run("G5 . the noimageindex robots directive is dropped",
      [('for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex"):',
        'for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex_MISSING"):')]))

# ---- G6 . another supplier -------------------------------------------------
r(run("G6 . another supplier's name reaches the page",
      [('"DEMO_HEADING": "How an Irish homeowner could reach Cosy Cabins",',
        '"DEMO_HEADING": "How an Irish homeowner could reach Hutsmith",')]))

# ---- G7 . the frozen band must travel byte-for-byte ------------------------
r(run("G7 . the frozen journey band is edited in transit, not relocated",
      [('SECOND_POSSIBILITY + "\\n" + journey.strip("\\n")',
        'SECOND_POSSIBILITY + "\\n" + journey.strip("\\n").replace('
        '"journey", "journey-v2")')]))

# ---- G8 . unevidenced claims ----------------------------------------------
# Two separate breaks, because the two claims fail for different reasons:
# insulation is contradicted by the supplier's own itemised spec, and
# nationwide coverage is contradicted by their published delivery terms.
r(run("G8 . the page calls the framed example fully insulated",
      [('"VERIFIED_FACT_3": "Electric Harvia 9kW stove',
        '"VERIFIED_FACT_3": "Fully insulated. Electric Harvia 9kW stove')]))

r(run("G8 . the page claims nationwide installation",
      [('"WHY_3_LABEL": "MORE THAN ONE WAY IN",',
        '"WHY_3_LABEL": "NATIONWIDE REACH",')]))

r(run("G8 . the page borrows the supplier's year-round-use marketing line",
      [('"VERIFIED_FACT_5": "Assembly by Cosy Cabins is included',
        '"VERIFIED_FACT_5": "Designed for year-round use. Assembly included')]))

# ---- G9 . no imagery on the artefact, not merely absent from the list -----
# Aimed past G0: the list stays empty, so only the output check can catch an
# image that arrives through the markup.
r(run("G9 . an external image arrives through the markup, not the image list",
      [('  <h2>Another way Cosy Cabins could appear</h2>',
        '  <h2>Another way Cosy Cabins could appear</h2>\n'
        '  <img src="https://static.wixstatic.com/media/9ba815_x.jpg" alt="">')]))

# ALL THREE links are stripped, with the %s arity preserved. Removing only
# one proves nothing: the check needs a single href to be satisfied, and a
# sabotage that leaves two behind is not a sabotage. Preserving the arity
# matters too -- a format-string mismatch would make the builder CRASH, and
# a crash is not a refusal.
r(run("G9 . every link back to the supplier's site is reduced to prose",
      [('\'<a href="%sgarden-rooms/athlone-garden-room-4.5m-x-2.5m" \'\n'
        '        \'rel="noopener">their Athlone garden room page</a> and \'\n'
        '        \'<a href="%ssaunas/sauna-2m" rel="noopener">their Sauna 2m page</a> \'\n'
        '        \'on %s. No Cosy Cabins imagery is used anywhere on this page. \'\n'
        '        \'%s &middot; <a href="%s" rel="noopener">cosycabins.ie</a></p>\\n\'',
        '\'%sgarden-rooms/athlone-garden-room-4.5m-x-2.5m \'\n'
        '        \'their Athlone garden room page and \'\n'
        '        \'%ssaunas/sauna-2m their Sauna 2m page \'\n'
        '        \'on %s. No Cosy Cabins imagery is used anywhere on this page. \'\n'
        '        \'%s &middot; %s cosycabins.ie</p>\\n\'')]))

# ---- G10 . no commercial implication --------------------------------------
r(run("G10 . the page implies an agreed relationship",
      [('"WHY_1_LABEL": "THEY ARRIVE HAVING THOUGHT ABOUT IT",',
        '"WHY_1_LABEL": "APPROVED SUPPLIER",')]))

# ---- G11 . the page must say what it is -----------------------------------
# THE MARKER LIVES IN THE TEMPLATE, not in the copy. The first attempt here
# removed the phrase from DEMO_LEDE and the builder BUILT, which was correct:
# template-provider-led.html carries its own <span class="illus-tag">
# Illustrative preview</span> beside the heading. Two satisfying sources meant
# the sabotage proved nothing, so the copy no longer repeats the words and
# this sabotage strips the real one.
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
