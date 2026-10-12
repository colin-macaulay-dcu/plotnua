#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-ah-review-locate.py

INSTRUMENT ONLY. Brings the Additional Home review harness to parity with
the Garden Room one, so the 3D property hero can actually be reviewed.

WHAT WAS WRONG. The harness already set `geocodedResult` to the SAME
Dundrum fixture coordinates the Garden Room review mode uses, but it never
brought Cesium up and never wrote the locality into #propConfirmPlace. So
the hero's `pnLocated` guard correctly refused to show a 3D view of a
property that, as far as the page was concerned, had never been located —
and fell back to is-fieldonly. The fallback was right; the harness was
incomplete.

WHAT THIS CHANGES — INSIDE THE ALREADY FAIL-CLOSED LOCAL BLOCK ONLY.
It calls initCesium(), flyToLocation(), enableShadowsForSunLight() and
moveCloserForPlotIntelligence() — the exact four functions
enterResultsReviewMode() calls, unchanged — and sets the locality label.
No coordinate reaches production behaviour: every line added sits inside
the block gated on localhost + http: + ?review=additional-home +
intendedUse === 'residential', and the red banner names the measurements
AND the location as fixtures.

Usage: python3 atlas-tools/build-ah-review-locate.py [--check|--revert]
"""

import hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-reviewlocate"
BASELINE = "17de53c242c314ae"

L1_FIND = """    geocodedResult = {
      lat: 53.2905, lon: -6.2413,
      formattedAddress: 'Dundrum, Co. Dublin (LOCAL DEV REVIEW — not a real customer address)',
      locationType: 'ROOFTOP', placeId: null, isRooftop: true
    };

      var all = [];
"""
L1_REPL = """    geocodedResult = {
      lat: 53.2905, lon: -6.2413,
      formattedAddress: 'Dundrum, Co. Dublin (LOCAL DEV REVIEW — not a real customer address)',
      locationType: 'ROOFTOP', placeId: null, isRooftop: true
    };

      /* THE PROPERTY IS LOCATED, SO THE PROPERTY VIEW CAN BE REVIEWED.

         The harness set the coordinates but never brought the viewer up or
         wrote the locality, so the hero's located-property guard refused —
         correctly — to show a 3D view of a property the page had no
         position for, and fell back to the shipped field-only treatment.

         These are the SAME FOUR FUNCTIONS enterResultsReviewMode() calls,
         in the same order, unchanged, against the SAME fixture coordinates
         already declared three lines above. No new camera code, no second
         viewer, and nothing here can run outside the four gates at the top
         of this block. */
      try {
        if (els.localityLabel)
          els.localityLabel.textContent = 'Dundrum, Co. Dublin (review mode)';
        var pcp = document.getElementById('propConfirmPlace');
        if (pcp) pcp.textContent = 'Dundrum, Co. Dublin';
        var pc = document.getElementById('propConfirm');
        if (pc) pc.hidden = false;
      } catch (e) {}
      try {
        var cesOk = await initCesium();
        if (cesOk) {
          var fr = await flyToLocation(geocodedResult.lat, geocodedResult.lon, true);
          lastResolvedTarget = fr.resolvedC;
          if (tilesetLoaded && fr.resolvedC) showLocationMarker(fr.resolvedC);
          enableShadowsForSunLight();
          await moveCloserForPlotIntelligence();
        }
      } catch (e) { console.warn('[REVIEW] property view unavailable', e); }

      var all = [];
"""

# The banner must name the location as a fixture too.
L2_FIND = ("        + n + ' real Additional Home candidate(s) · '\n"
           "        + 'THE PROPERTY ASSESSMENT ABOVE IS A FIXTURE. THE PRODUCT DATA IS REAL.';\n")
L2_REPL = ("        + n + ' real Additional Home candidate(s) · '\n"
           "        + 'THE PROPERTY MEASUREMENTS AND LOCATION ARE FIXTURES. "
           "THE PRODUCT DATA IS REAL.';\n")

# The harness callback must be async to await the four viewer functions,
# exactly as enterResultsReviewMode() is.
L0_FIND = "    additionalHomePoolReady.then(function () {\n"
L0_REPL = "    additionalHomePoolReady.then(async function () {\n"

EDITS = [("L0  the harness callback awaits the viewer", L0_FIND, L0_REPL),
         ("L1  locate the fixture property and raise the viewer", L1_FIND, L1_REPL),
         ("L2  the banner names the location as a fixture", L2_FIND, L2_REPL)]

GATES = ["if (!isLocal) return;", "if (location.protocol !== 'http:') return;",
         "if (qs.get('review') !== 'additional-home') return;",
         "if (intendedUse !== 'residential') return;"]


def sha16(s): return hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if mode == "--revert":
        if not os.path.exists(BAK): raise SystemExit("no backup")
        open(PAGE, "w", encoding="utf-8").write(open(BAK, encoding="utf-8").read())
        print("reverted."); return

    src = open(PAGE, encoding="utf-8").read()
    base = sha16(src)
    if base != BASELINE and not os.path.exists(BAK):
        raise SystemExit("REFUSED: baseline %s, expected %s" % (base, BASELINE))

    out = src
    for name, find, repl in EDITS:
        if out.count(find) != 1:
            raise SystemExit("REFUSED: anchor %s matched %d" % (name, out.count(find)))
        out = out.replace(find, repl, 1)

    for g in GATES:
        if g not in out:
            raise SystemExit("REFUSED: harness gate lost: %s" % g)
    # No coordinate may appear outside the harness block.
    body = out[out.index("if (qs.get('review') !== 'additional-home') return;"):]
    harness_end = body.index("  // SPRINT 1.5")
    outside = out.replace(body[:harness_end], "")
    extra = outside.count("53.2905") - src.count("53.2905") + 0
    if "53.2905" in outside and src.count("53.2905") < 2:
        pass  # the Garden Room fixture legitimately holds one
    if out.count("53.2905") != src.count("53.2905"):
        raise SystemExit("REFUSED: a coordinate was added; the harness must "
                         "reuse the one already declared")

    if mode == "--check":
        print("CHECK ONLY. baseline %s -> %s, +%d lines, gates intact, "
              "no coordinate added"
              % (base, sha16(out), out.count("\n") - src.count("\n")))
        return

    blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", out, re.S)
    for i, b in enumerate(blocks):
        if not b.strip(): continue
        tmp = os.path.join(ROOT, ".pn-rl-%d.mjs" % i)
        open(tmp, "w", encoding="utf-8").write(b)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            raise SystemExit("REFUSED: script %d does not parse, nothing "
                             "written:\n%s" % (i, r.stderr[:300]))
    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied. %s -> %s" % (base, sha16(out)))


if __name__ == "__main__":
    main()
