#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-switch-electrical-preview.py.

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught.

THE BUILDER RUNS IN --stage MODE THROUGHOUT, so the deployed tree is never
written. The staged artefact is hashed before and after and the hash is
printed: a proof that damages what it proves is worse than no proof.

GUARD-ORDERING HAZARD, handled. A break that an EARLIER guard catches proves
nothing about the guard it was aimed at. Each sabotage is chosen so only its
target can catch it, and the printed refusal is the evidence of which fired.

TWO SABOTAGES MUTATE THE GUARD'S OWN NEEDLE rather than the copy, and they say
so where they appear. "survey" and "seai" each occur five or six times across
the fill set, so deleting every occurrence would be a test of my patience with
find-and-replace rather than of the guard. Mutating the needle asks the only
question that matters of a presence check: when the required statement is not
there, does the builder refuse? The third positive guard, the 2021 eligibility
condition, occurs exactly once and is deleted for real.

Run: python3 supplier-preview-system/prove-switch-electrical-guards.py
"""

import contextlib
import hashlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-switch-electrical-preview.py"
STAGED = pathlib.Path("/tmp/plotnua-stage/switch-electrical-preview.html")

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


print("GUARD-CAPABILITY PROOF — SWITCH ELECTRICAL PRIVATE PREVIEW")
print("=" * 78)
r = results.append

# ---- G0 . the whole point of this build ------------------------------------
r(run("G0 . supplier imagery is added while permission is unknown",
      [("SWITCH_IMAGES = []",
        'SWITCH_IMAGES = [{"url": "https://switchelectrical.ie/gallery/clean/'
        'roof-dublin-black-panels.jpg", "alt": "panels"}]')]))

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
r(run("G3c . the footer anchor for the attribution line cannot be found",
      [('foot = "<footer>\\n"', 'foot = "<footer >\\n"')]))

# ---- G3b . the closing heading --------------------------------------------
r(run("G3b . the closing heading anchor no longer matches the template",
      [('old_head = "<h2>What we&rsquo;d like to explore</h2>"',
        'old_head = "<h2>What we would like to explore</h2>"')]))

# ---- G4 . tokens ----------------------------------------------------------
r(run("G4 . a token is dropped from the fill set",
      [('"OFFER_NAME": "Solar PV, battery storage and EV charging",', "")]))

# ---- G5 . privacy ---------------------------------------------------------
r(run("G5 . the noimageindex robots directive is dropped",
      [('for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex"):',
        'for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex_MISSING"):')]))

# ---- G6 . another supplier -------------------------------------------------
# Sigenergy is deliberately NOT in G6's list, so the sabotage uses a supplier
# that is. A break using "Sigenergy" would prove the opposite of what is wanted.
r(run("G6 . another supplier's name reaches the page",
      [('"DEMO_HEADING": "How an Irish homeowner could reach Switch '
        'Electrical",',
        '"DEMO_HEADING": "How an Irish homeowner could reach Cosy Cabins",')]))

# ---- G7 . the frozen band must travel byte-for-byte ------------------------
r(run("G7 . the frozen journey band is edited in transit, not relocated",
      [('OPEN_QUESTIONS + "\\n" + journey.strip("\\n")',
        'OPEN_QUESTIONS + "\\n" + journey.strip("\\n").replace('
        '"journey", "journey-v2")')]))

# ---- G8 . the claims this supplier invites --------------------------------
# Four breaks, four different failure modes: a saving, a payback, a service
# area and a suitability claim. Each is what a careless writer would actually
# say about a solar installer, and the first two are the reason this builder
# exists in the shape it does.
r(run("G8 . the page promises the homeowner a saving",
      [('"WHY_1_LABEL": "THE GRANT, UNDERSTOOD BEFORE THE CALL",',
        '"WHY_1_LABEL": "WE WILL SAVE YOU MONEY",')]))

r(run("G8 . the page claims the system pays for itself",
      [('"VERIFIED_FACT_5": "Battery, inverter and EV charging on one '
        'Sigenergy "',
        '"VERIFIED_FACT_5": "Pays for itself. Battery, inverter and EV '
        'charging on one Sigenergy "')]))

r(run("G8 . the service area is widened past the five published counties",
      [('"VERIFIED_FACT_2_VALUE": "Based in Dublin. Dublin, Louth, Meath, '
        'Kildare "',
        '"VERIFIED_FACT_2_VALUE": "Nationwide. Dublin, Louth, Meath, '
        'Kildare "')]))

r(run("G8 . the page declares the work suitable for a house nobody has seen",
      [('"VERIFIED_FACT_1_LABEL": "What they fit",',
        '"VERIFIED_FACT_1_LABEL": "Suitable for your home",')]))

# ---- G8b . the statements that must be PRESENT ----------------------------
# NEEDLE MUTATION, and deliberately. "survey" appears six times and "seai"
# five, across the price basis, the facts, the honest line, the personalisation
# note and the open questions. Deleting every occurrence would test the copy;
# mutating the needle asks the guard the only question that matters — when the
# required statement is absent, does it refuse?
r(run("G8b . the survey requirement is absent from the page (needle mutated)",
      [('if "survey" not in low:', 'if "site visit" not in low:')]))

r(run("G8b . SEAI is never named, so the grant reads as the installer's "
      "offer (needle mutated)",
      [('if "seai" not in low:', 'if "sustainable energy authority" not in low:')]))

# The third positive guard needs no mutation: the condition occurs once.
r(run("G8b . the grant is stated without its published eligibility conditions",
      [('"home must have been built and occupied before 2021, "', '""')]))

# ---- G9 . no imagery on the artefact, and a real link back ---------------
# Aimed past G0: the list stays empty, so only the output check can catch an
# image that arrives through the markup.
r(run("G9 . an external image arrives through the markup, not the image list",
      [('  <h2>Three things we would ask before publishing</h2>',
        '  <h2>Three things we would ask before publishing</h2>\\n'
        '  <img src="https://switchelectrical.ie/gallery/clean/x.jpg" alt="">')]))

r(run("G9 . every link back to the supplier's site is reduced to prose",
      [('\'<a href="%s" rel="noopener">your services page</a>, \'\n'
        '        \'<a href="%s" rel="noopener">your SEAI grant page</a> and \'\n'
        '        \'<a href="%s" rel="noopener">switchelectrical.ie</a> on %s. \'',
        '\'%s your services page, \'\n'
        '        \'%s your SEAI grant page and \'\n'
        '        \'%s switchelectrical.ie on %s. \'')]))

# ---- G10 . no commercial implication --------------------------------------
r(run("G10 . the page implies an agreed relationship",
      [('"WHY_2_LABEL": "ONE TRADE, THREE JOBS",',
        '"WHY_2_LABEL": "APPROVED SUPPLIER",')]))

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
