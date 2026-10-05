#!/usr/bin/env python3
"""
GUARD-CAPABILITY PROOF FOR prove-disc026-discovery.mjs
===========================================================================
A guard that has never been seen to refuse is a comment. This breaks each
check in the DISC-026 Discovery proof exactly once, against the REAL page,
and asserts that each break is CAUGHT.

It also runs a CONTROL before and after. A clean page must pass; if the
control fails at the end, the restore did not work and the result is void.
Every mutation is reverted in a finally block, and the file is hashed before
and after the whole run: a proof that edits what it proves has proved nothing.

Exit 0 = every guard caught its break and the page is byte-identical.
Exit 1 = a break was MISSED, or the file changed.
Exit 2 = the proof could not run.

Run: python3 atlas-tools/prove-disc026-discovery-capability.py
"""

import hashlib
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PAGE = ROOT / "discovery-house-as-power-station.html"
PROOF = HERE / "prove-disc026-discovery.mjs"

for f in (PAGE, PROOF):
    if not f.exists():
        print("missing: " + str(f))
        sys.exit(2)

ORIGINAL = PAGE.read_bytes()
BEFORE = hashlib.sha256(ORIGINAL).hexdigest()
text = ORIGINAL.decode("utf-8")


def verdict():
    p = subprocess.run(["node", str(PROOF)], capture_output=True, text=True,
                       cwd=str(ROOT))
    v = {0: "GOVERNED", 1: "DIVERGED"}.get(p.returncode, "NOT ESTABLISHED")
    detail = ""
    for line in p.stdout.splitlines():
        t = line.strip()
        if t.startswith("FAIL") or t.startswith("ERROR"):
            detail = t
            break
    return v, detail


results = []


def case(label, mutate, expect="DIVERGED"):
    """Apply MUTATE to the page text, run the proof, restore, record."""
    try:
        new = mutate(text)
        if new == text:
            print("  BROKEN  the mutation %r changed nothing, so this case "
                  "would prove nothing" % label)
            results.append((False, label, "mutation was a no-op"))
            return
        PAGE.write_text(new, encoding="utf-8")
        got, detail = verdict()
    finally:
        PAGE.write_bytes(ORIGINAL)
    hit = (got == expect)
    print("  %s %-16s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("          -> %s" % (detail[:104] if detail else "(nothing reported)"))
    results.append((hit, label, detail))


print("DISC-026 DISCOVERY GUARD-CAPABILITY PROOF")
print("=" * 74)

# ---- CONTROL, before -------------------------------------------------------
v, d = verdict()
print("  CONTROL (clean page)      %s" % v)
if v != "GOVERNED":
    print("  The clean page does not pass its own proof, so nothing below "
          "would mean anything. %s" % d)
    sys.exit(2)
print("")

# ---- G1 . the withdrawn wind characterisation returns ----------------------
case("G1  the withdrawn 'worst air' claim is put back",
     lambda t: t.replace(
         "What is not settled is whether it would be worth building at your",
         "The envelope places the rotor in the worst air on most sites, and "
         "what is not settled is whether it would be worth building at your",
         1))

# ---- G2 . the hero loses its potential-asset marker ------------------------
case("G2  the hero plate's potential-asset marker is removed",
     lambda t: t.replace(
         "the roof annotated by PlotNua as a potential asset.",
         "the roof seen from the garden.", 1))

# ---- G3 . the governed Library image gains a before-state description -----
case("G3  the Library image is re-described as a before state",
     lambda t: t.replace(
         'alt="An Irish family outside their home at dusk: solar panels',
         'alt="The roof standing completely empty before anything is planted: '
         'an Irish family outside their home at dusk, solar panels', 1))

# ---- G3b . the governed Library image is dropped altogether ---------------
case("G3b the governed Library image is removed from the page",
     lambda t: t.replace("assets/img/ce9da2e51c945693.jpg",
                         "assets/img/f0e99db16cefc470.jpg", 1))

# ---- G4 . the battery boundary is converted without authorisation ---------
case("G4  the battery grant is converted to the present tense",
     lambda t: t.replace(
         "From 6 October 2026 SEAI is to pay a flat\n            &euro;600",
         "There&rsquo;s an SEAI grant of\n            &euro;600", 1))

# ---- G4b . the boundary markers are stripped ------------------------------
case("G4b the battery boundary markers are stripped",
     lambda t: t.replace("PN-DISC026-BATTERY-BOUNDARY-BEGIN", "battery grant", 1))

# ---- G5 . a supplier photograph is hotlinked -------------------------------
case("G5  an un-granted supplier photograph is hotlinked",
     lambda t: t.replace(
         '<img src="assets/img/f0e99db16cefc470.jpg"',
         '<img src="https://example-installer.ie/photos/real-install.jpg"', 1))

# ---- G6 . a withdrawn claim comes back ------------------------------------
case("G6  a withdrawn claim (Hestiia) is reinstated",
     lambda t: t.replace(
         "<span class=\"dq-adv-label\">Germany &middot; specified</span>",
         "<span class=\"dq-adv-label\">Hestiia, France</span>", 1))

# ---- G7 . the honesty break is moved below the energy anatomy -------------
def move_seam_below(t):
    a = t.index('<section class="seam reveal">')
    b = t.index("</section>", t.index("</div>\n</section>", a)) + len("</section>")
    band = t[a:b]
    rest = t[:a] + t[b:]
    k = rest.index('<section class="closing-line reveal">')
    return rest[:k] + band + "\n\n" + rest[k:]


case("G7  the honesty break is moved BELOW the energy anatomy",
     move_seam_below)

# ---- G8 . an unconditional finding is softened ----------------------------
case("G8  an unconditional RCR finding is softened",
     lambda t: t.replace(
         "Distributed residential computing is not currently commercially",
         "Distributed residential computing is not yet widely", 1))

# ---- G9 . a position is dropped from the anatomy --------------------------
case("G9  the ground position is dropped from the anatomy",
     lambda t: t.replace("4 &middot; The ground beneath the garden",
                         "The ground beneath the garden", 1))

# ---- G9b . two positions are swapped out of order -------------------------
case("G9b anatomy positions are renumbered",
     lambda t: t.replace("1 &middot; Roof", "9 &middot; Roof", 1)
                .replace("7 &middot; The grid connection",
                         "1 &middot; The grid connection", 1))

# ---- G10 . the Wind Atlas is presented as usable --------------------------
case("G10 the SEAI Wind Atlas is presented as able to answer",
     lambda t: t.replace(
         "The SEAI Wind Atlas is the obvious place to\n            look and "
         "<strong>it cannot answer this question</strong>: its lowest\n"
         "            height is 50&nbsp;m, and the tallest exempt domestic "
         "turbine is\n            13&nbsp;m.",
         "The SEAI Wind Atlas is the obvious place to\n            look, and it "
         "will give you a mean wind speed for your area.", 1))

# ---- G11 . an ungoverned money figure appears ------------------------------
case("G11 an ungoverned grant amount is added",
     lambda t: t.replace(
         "<p>Charging at home needs somewhere off-street",
         "<p>There is a grant of &euro;300 towards a home charger. Charging at "
         "home needs somewhere off-street", 1))

# ---- G13 . implementation language leaks back into homeowner copy ----------
case("G13 internal machinery language leaks into homeowner copy",
     lambda t: t.replace(
         "<strong>It will not give you a score.</strong>",
         "<strong>It gives three states and no score.</strong> A build gate stops "
         "a number reaching the page.", 1))

# ---- G13b . the honesty is deleted rather than reworded -------------------
case("G13b the no-score limitation is deleted instead of reworded",
     lambda t: t.replace(
         "<strong>It will not give you a score.</strong> We can&rsquo;t give a "
         "property\n      a meaningful percentage yet, because nobody has "
         "established what a fully\n      &ldquo;compute-ready&rdquo; home would "
         "actually require. And",
         "And", 1))

# ---- G14 . the page speaks for every Irish operator again -----------------
case("G14 the page generalises from Tandem to all Irish operators",
     lambda t: t.replace(
         "PlotNua has not found an equivalent "
         "Irish residential offering, and Tandem has confirmed that individual "
         "homes are not part of its current pipeline.",
         "Not available in Ireland, and not on any Irish operator&rsquo;s "
         "pipeline for homes today.", 1))

# ---- G15 . the detail is deleted rather than demoted ----------------------
case("G15 a demoted fact is deleted rather than moved to the drawer",
     lambda t: t.replace("43&nbsp;dB(A) or less", "quiet enough", 1))

# ---- G15b . a position loses its leading idea -----------------------------
case("G15b a position loses its leading idea",
     lambda t: t.replace(
         '<span class="pos-eq">Battery <i>&rarr;</i> stored electricity</span>\n',
         '', 1))

# ---- G16 . the ground-source revelation is suppressed again ---------------
case("G16 the ground-source cooling concept is suppressed again",
     lambda t: t.replace(
         "<p>Some systems can also use that same ground connection for cooling. "
         "Whether\n          that works for a particular Irish home depends on the "
         "system, the ground\n          conditions and the design.</p>\n", "", 1))

# ---- G16b . cooling is overclaimed ---------------------------------------
case("G16b ground-source cooling is overclaimed",
     lambda t: t.replace(
         "Some systems can also use that same ground connection for cooling.",
         "A ground-source system also provides passive cooling in summer.", 1))

# ---- G17 . the permission workflow is told to the homeowner again ---------
case("G17 the permission workflow is put back in homeowner copy",
     lambda t: t.replace(
         '<span class="imgnote">Real installation photography will be added when '
         'publication rights are confirmed.</span>',
         '<div class="rights">PlotNua has asked heata for permission and has not '
         'had an answer.</div>', 1))

# ---- G12 . the ending stops returning to the flagship ---------------------
case("G12 the closing line no longer returns to the flagship",
     lambda t: t.replace(
         "Could your house one day\n    do some of the work of a data centre "
         "&mdash; and use the heat it creates?",
         "PlotNua will keep watching.", 1))

# ---- structure . an unbalanced tag -----------------------------------------
case("STR a section is left unclosed",
     lambda t: t.replace('<section class="closing-line reveal">',
                         '<section class="closing-line reveal"><section>', 1))

# ---- G18 . a technology category reverts to a story label -----------------
case("G18 a technology category reverts to a story label",
     lambda t: t.replace(
         '<div class="kicker">Data centres &middot; useful heat</div>',
         '<div class="kicker">And in Ireland</div>', 1))

# ---- G18b . a position loses its technology -------------------------------
case("G18b an anatomy position loses its technology",
     lambda t: t.replace("&middot; Ground-source energy</span>", "</span>", 1))

# ---- G18c . a category is promoted to a heading ---------------------------
case("G18c a category is promoted to a heading",
     lambda t: t.replace(
         "<h3>The ground can do more than heat a house.</h3>",
         "<h3>Ground-source energy</h3>", 1))

# ---- G19 . every headline goes back to proof scale -------------------------
case("G19 section headlines go back to proof scale",
     lambda t: t.replace(
         ".article-section h2{ font-size:clamp(23px,2.6vw,31px)",
         ".article-section h2{ font-size:clamp(26px,3.4vw,40px)", 1))

# ---- G19b . a second headline claims proof scale --------------------------
case("G19b a second headline claims proof scale",
     lambda t: t.replace(
         "<h2>This is already being built in Ireland.</h2>",
         '<h2 class="is-proof">This is already being built in Ireland.</h2>', 1))

# ---- G19c . the transition reclaims a viewport ----------------------------
case("G19c the transition reclaims most of a viewport",
     lambda t: t.replace(".spark{ padding:7vh 7vw; }",
                         ".spark{ padding:12vh 7vw; }", 1))

# ---- G20 . the wind envelope stops being to scale -------------------------
case("G20 a wind envelope dimension stops being to scale",
     lambda t: t.replace('d="M424 88 V232 M418 88 H430 M418 232 H430"',
                         'd="M424 88 V210 M418 88 H430 M418 210 H430"', 1))

# ---- G20b . a sixth drawing appears without a decision --------------------
case("G20b an undecided sixth drawing appears",
     lambda t: t.replace(
         '<section class="closing-line reveal">',
         '<section class="closing-line reveal">\n<svg viewBox="0 0 10 10">'
         '<rect x="1" y="1" width="8" height="8"/></svg>', 1))

# ---- G20c . the "nothing to photograph" sentence comes back ---------------
case("G20c the 'nothing to photograph' sentence comes back",
     lambda t: t.replace(
         "Centralised heating is a\n        precondition of that model, not a detail.",
         "There is no photograph here because there is nothing to photograph.", 1))

# ---- G21 . a reader instruction returns -----------------------------------
case("G21 an instruction about reading the evidence returns",
     lambda t: t.replace(
         "<p style=\"margin-top:38px\">Every one of those figures is British",
         "<p style=\"margin-top:38px\"><strong>Read those figures carefully.</strong> "
         "Every one of those figures is British", 1))

# ---- G22 . the planning jargon reverts on the homeowner surface ------------
case("G22 the drawer summary reverts to planning jargon",
     lambda t: t.replace("<h3>The planning limits, at a glance</h3>",
                         "<h3>The exempt envelope, in full</h3>", 1))

# ---- G22b . and in the caption -------------------------------------------
case("G22b the caption reverts to planning jargon",
     lambda t: t.replace(
         '<p class="anat-cap">The planning limits, drawn to scale.</p>',
         '<p class="anat-cap">The exempt envelope, drawn to scale.</p>', 1))

# ---- G22c . and where only a screen-reader user would meet it -------------
case("G22c the jargon survives only in the aria-label",
     lambda t: t.replace(
         'aria-label="The planning limits for a domestic wind turbine',
         'aria-label="The exempt envelope for a domestic wind turbine', 1))

# ---- G22d . plainer words cost the homeowner a governed dimension ---------
case("G22d a governed dimension loses its label on the drawing",
     lambda t: t.replace(">3 m MINIMUM CLEARANCE<", ">CLEARANCE<", 1))

# ---- CONTROL, after --------------------------------------------------------
print("")
v, d = verdict()
print("  CONTROL (restored page)   %s" % v)
after = hashlib.sha256(PAGE.read_bytes()).hexdigest()

print("")
print("=" * 74)
missed = [lab for hit, lab, _ in results if not hit]
print("  file sha256 before  %s" % BEFORE)
print("  file sha256 after   %s" % after)
print("  cases %d . caught %d . missed %d"
      % (len(results), len(results) - len(missed), len(missed)))

if after != BEFORE:
    print("VOID -- the page was not restored byte-identically.")
    sys.exit(1)
if v != "GOVERNED":
    print("VOID -- the restored page does not pass its own proof.")
    sys.exit(1)
if missed:
    print("INSUFFICIENT -- these breaks were NOT caught:")
    for m in missed:
        print("    " + m)
    sys.exit(1)
print("CAPABLE -- every break was caught, the control passed before and "
      "after, and the page is byte-identical.")
sys.exit(0)
