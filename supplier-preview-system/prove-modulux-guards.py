#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-modulux-preview.py.

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught.

THE BUILDER RUNS IN --stage MODE THROUGHOUT, so the deployed tree is never
written. The staged artefact is hashed before and after and the hash is
printed: a proof that damages what it proves is worse than no proof.

GUARD-ORDERING HAZARD, handled. A break that an EARLIER guard catches proves
nothing about the guard it was aimed at. Each sabotage is chosen so only its
target can catch it, and the printed refusal is the evidence of which fired.

THE TWO BREAKS THAT MATTER MOST ON THIS SUPPLIER are G8b and G8c, and they
are the inverse of every other guard in this system. Everywhere else the
danger is a claim appearing. Here the danger is a true and useful statement
DISAPPEARING: Modulux publishes the planning distinction better than anyone
else in the Irish market, and publishes no price at all. A page that quietly
drops either would read perfectly well and be worse than no page. So those
two breaks delete rather than add.

Run: python3 supplier-preview-system/prove-modulux-guards.py
"""

import contextlib
import hashlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-modulux-preview.py"
STAGED = pathlib.Path("/tmp/plotnua-stage/modulux-preview.html")

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


print("GUARD-CAPABILITY PROOF — MODULUX PRIVATE PREVIEW")
print("=" * 78)
r = results.append

# ---- G0 . the whole point of this build ------------------------------------
# Modulux has never been contacted. Their gallery is real and tempting.
r(run("G0 . supplier imagery is added while permission is unknown",
      [("MODULUX_IMAGES = []",
        'MODULUX_IMAGES = [{"url": "https://www.modulux.ie/images/'
        'hero-main.jpg", "alt": "a garden room"}]')]))

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
      [('"OFFER_NAME": "Garden apartment &mdash; one or two bedrooms",', "")]))

# ---- G5 . privacy ---------------------------------------------------------
# Doubly load-bearing here: the supplier does not yet know the page exists.
r(run("G5 . the noimageindex robots directive is dropped",
      [('for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex"):',
        'for directive in ("noindex", "nofollow", "noarchive", "nosnippet",\n'
        '                      "noimageindex_MISSING"):')]))

# ---- G6 . another supplier -------------------------------------------------
r(run("G6 . another supplier's name reaches the page",
      [('"DEMO_HEADING": "How an Irish homeowner could reach Modulux",',
        '"DEMO_HEADING": "How an Irish homeowner could reach Cosy Cabins",')]))

# ---- G7 . the frozen band must travel byte-for-byte ------------------------
r(run("G7 . the frozen journey band is edited in transit, not relocated",
      [('LADDER + "\\n" + journey.strip("\\n")',
        'LADDER + "\\n" + journey.strip("\\n").replace('
        '"journey", "journey-v2")')]))

# ---- G8 . unevidenced claims ----------------------------------------------
# Five separate breaks, because they fail for five different reasons: money,
# dimension, product, planning and time. Each is the claim a careless writer
# would actually make about THIS supplier, whose site publishes a process in
# detail and almost no numbers at all.
r(run("G8 . a price is invented for a supplier who publishes none",
      [('"VERIFIED_PRICE": "Quoted per project",',
        '"VERIFIED_PRICE": "From &euro;65,000",')]))

r(run("G8 . a floor area is invented",
      [('"VERIFIED_FACT_2_VALUE": "One or two bedrooms.',
        '"VERIFIED_FACT_2_VALUE": "Typically 40 sq m. One or two bedrooms.')]))

r(run("G8 . a catalogue of models is implied",
      [('"VERIFIED_FACT_3": "Built to the current building regulations',
        '"VERIFIED_FACT_3": "Choose from our models. Built to the current '
        'building regulations')]))

r(run("G8 . the garden apartment is called planning exempt",
      [('"VERIFIED_FACT_4": "Foundations, heating, lighting, painting',
        '"VERIFIED_FACT_4": "Planning exempt. Foundations, heating, lighting, '
        'painting')]))

r(run("G8 . a lead time is invented",
      [('"VERIFIED_FACT_5": "Design, building regulations',
        '"VERIFIED_FACT_5": "Typical lead time of ten weeks. Design, building '
        'regulations')]))

r(run("G8 . a warranty is invented",
      [('"WHY_1_TEXT": "You offer several different responses',
        '"WHY_1_TEXT": "Every build carries a ten year warranty. You offer '
        'several different responses')]))

# ---- G12 . TONE. Founder correction, 5 October 2026. -----------------------
# Three breaks, because this failure has three shapes and each would read as
# ordinary, confident marketing copy while doing the damage.
r(run("G12 . the homeowner is made to sound as though they choose wrongly",
      [('"WHY_1_TEXT": "You offer several different responses to the need for '
        'more "',
        '"WHY_1_TEXT": "A homeowner who has not thought it through will ask '
        'for the wrong one. You offer several different responses to the need '
        'for more "')]))

r(run("G12 . the homeowner is described as wasting the supplier's time",
      [('"WHY_3_TEXT": "By the time a homeowner reaches you through PlotNua, they "',
        '"WHY_3_TEXT": "We filter out the ones who would waste your time. "')]))

# ---- G12b . THE INVERSE. Deleting the framing is not correcting it. --------
r(run("G12b . the approved ladder heading is deleted rather than corrected",
      [("  <h2>Different possibilities for different needs</h2>\n", "")]))

# ---- G8b . THE INVERSE GUARD. The planning position must SURVIVE. ----------
# Both halves, separately, because a page could keep one and lose the other
# and the loss of either is the specific failure this supplier invites.
r(run("G8b . the 'normally needs planning permission' half is softened away",
      [("it will normally need planning permission. Modulux "
        '"\n                       "handle that application as part of the '
        'project, and ',
        "planning is handled for you. Modulux "
        '"\n                       "handle that application as part of the '
        'project, and ')]))

r(run("G8b . the 'local authority decides' half is dropped",
      [('"say plainly that your local authority is the only "\n'
        '                       "body that can confirm what is required on '
        'your site.",',
        '"say so plainly.",')]))

# ---- G8c . THE INVERSE GUARD. The absence of a price must stay visible. ----
# TWO substitutions in ONE case, and the first version of this proof needed
# them. "no price list" is stated twice -- in the price basis and again in the
# honest line -- so removing it from one place left the other and the break
# built cleanly. That was the sabotage being wrong, not the guard: a guard
# that passes while the statement survives SOMEWHERE is behaving correctly.
# The break now removes it from both, which is what a careless edit tidying
# "repetition" would actually do.
r(run("G8c . the explicit 'no price list' statement is dropped everywhere",
      [('"VERIFIED_PRICE_BASIS": "Modulux publish no price list. The visit and "',
        '"VERIFIED_PRICE_BASIS": "The visit and "'),
       ('"there is no figure on this page because Modulux "\n'
        '                       "publish no price list &mdash; work is quoted '
        'per "\n                       "project after the visit and the design '
        'stage. And "',
        '"work is quoted after the design stage. And "')]))

# ---- G9 . no imagery, proven on the OUTPUT ---------------------------------
# G0 reads the input list, so this break bypasses the list entirely and puts
# an external image straight into the emitted page. Only G9 can catch it.
r(run("G9 . an external image is injected into the output, bypassing the list",
      [('"PHOTO_SLOT_LINE": "No Modulux photography is used on this page. "',
        '"PHOTO_SLOT_LINE": "<img src=\\"https://www.modulux.ie/images/'
        'hero-main.jpg\\" alt=\\"\\">No Modulux photography on this page. "')]))

# The first version of this break edited SUPPLIER_SITE, which BUILT -- and
# correctly, because the guard and the link are both derived from that one
# constant, so changing it moves them together. The real failure mode is the
# attribution losing its anchor while the constant stays, which is what a
# tidy-up of the credit line would actually do.
r(run("G9 . the attribution stops LINKING back, keeping only the words",
      [('\'<a href="%s" rel="noopener">modulux.ie</a> on %s. \'',
        "'modulux.ie on %s. '"),
       ('% (SUPPLIER, APARTMENT_URL, HOMES_URL, SUPPLIER_SITE, EVIDENCE_DATE,',
        '% (SUPPLIER, APARTMENT_URL, HOMES_URL, EVIDENCE_DATE,')]))

# ---- G10 . no partnership implication --------------------------------------
r(run("G10 . the page implies a partnership",
      [('"WHY_3_LABEL": "ARRIVING WITH A DEVELOPED IDEA",',
        '"WHY_3_LABEL": "A PARTNER WORTH HAVING",')]))

# ---- G11 . the preview must say what it is ---------------------------------
r(run("G11 . the pre-publication review ask is removed from the page",
      [('src = src.replace(old_head, "<h2>Before anything goes live</h2>")',
        'src = src.replace(old_head, "<h2>Next steps</h2>")')]))

# ---- CONTROL . the unmutated builder must still build ----------------------
r(run("CONTROL . the unmutated builder builds cleanly", (), expect="BUILT"))

after = hashlib.sha256(STAGED.read_bytes()).hexdigest()
print("-" * 78)
print("%d of %d checks passed" % (sum(results), len(results)))
print("staged artefact untouched by this proof: %s  (%s)"
      % ("YES" if after == before else "NO", before[:12]))
if after != before:
    print("VOID — the proof altered the artefact it was proving.")
    sys.exit(1)
sys.exit(0 if all(results) else 1)
