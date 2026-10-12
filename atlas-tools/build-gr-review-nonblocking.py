#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-gr-review-nonblocking.py

REVIEW HARNESS ONLY. enterResultsReviewMode() awaits initCesium() and then
flyToLocation() before it calls computeAndShowResults(). Measured in the
browser: Google Photorealistic 3D Tiles answer 403 Forbidden from a
localhost origin, the fly-to promise does not settle, and the review
Results page therefore never renders — it sits on the entry screen.

The viewer is raised BESIDE the review rather than in front of it: the
same four functions, in the same order, against the same fixture, moved
into a non-awaited promise chain with its own catch. computeAndShowResults
then runs immediately, as it does for a real homeowner.

STRICTLY BOUNDED. The only function touched is enterResultsReviewMode(),
which is reachable only via ?review=… on localhost. Production behaviour,
the Results design, the assessment calculations, the product data and the
image permissions are not in this function and are not touched — the
builder refuses if the edit lands anywhere else, if any of the four viewer
calls is dropped, or if computeAndShowResults stops being called.

Usage: python3 atlas-tools/build-gr-review-nonblocking.py [--check|--revert]
"""

import hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-grreview"
BASELINE = "e742e2f1ec0210a2"

FIND = """    const ok = await initCesium();
    if (ok) {
      const flightResult = await flyToLocation(geocodedResult.lat, geocodedResult.lon, true);
      lastResolvedTarget = flightResult.resolvedC;
      if (tilesetLoaded && flightResult.resolvedC) showLocationMarker(flightResult.resolvedC);
      enableShadowsForSunLight();
      await moveCloserForPlotIntelligence();
    }
"""

REPL = """    /* THE REVIEW MUST NOT DEPEND ON THE PROPERTY VIEW LOADING.

       Measured, 12 October 2026: Google Photorealistic 3D Tiles answer
       403 Forbidden from a localhost origin. Awaited here, the fly-to
       promise never settled and computeAndShowResults() below was never
       reached, so the review Results page sat on the entry screen and
       could not be inspected at all.

       SAME FOUR FUNCTIONS, SAME ORDER, SAME FIXTURE. Nothing about the
       viewer changes; it is simply no longer in front of the render. The
       chain has its own catch, so a refused tile request is reported and
       ignored rather than stalling the page. REVIEW MODE ONLY — this
       function is reachable only through ?review=… and is not on any
       homeowner's path. */
    (function raiseReviewPropertyView(){
      Promise.resolve()
        .then(function(){ return initCesium(); })
        .then(function(ok){
          if (!ok) return null;
          return flyToLocation(geocodedResult.lat, geocodedResult.lon, true)
            .then(function(flightResult){
              lastResolvedTarget = flightResult.resolvedC;
              if (tilesetLoaded && flightResult.resolvedC)
                showLocationMarker(flightResult.resolvedC);
              enableShadowsForSunLight();
              return moveCloserForPlotIntelligence();
            });
        })
        .catch(function(e){
          console.warn('[REVIEW] property view unavailable', e);
        });
    })();
"""

# The four viewer calls that must survive, and the render that must follow.
KEEP = ["initCesium()", "flyToLocation(geocodedResult.lat, geocodedResult.lon, true)",
        "showLocationMarker(flightResult.resolvedC)", "enableShadowsForSunLight()",
        "moveCloserForPlotIntelligence()", "computeAndShowResults(true)"]

# Nothing outside the review function may move.
FORBIDDEN_NEIGHBOURS = ["rankArtistStudioCandidates", "scoreCandidate",
                        "pnAuthorisedImage", "pnAttachImageCredit",
                        "buildResultsGalleryCard", "buildResultsHero"]


def sha16(s): return hashlib.sha256(s.encode()).hexdigest()[:16]


def review_fn(src):
    a = src.index("async function enterResultsReviewMode(){")
    b = src.index("// PB035 — internal inspection surface", a)
    return src[a:b]


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

    if src.count(FIND) != 1:
        raise SystemExit("REFUSED: anchor matched %d" % src.count(FIND))

    # G1 — the anchor must lie inside enterResultsReviewMode().
    fn_before = review_fn(src)
    if FIND not in fn_before:
        raise SystemExit("REFUSED: the anchor is not inside "
                         "enterResultsReviewMode(); refusing to edit elsewhere")

    out = src.replace(FIND, REPL, 1)

    # G2 — the change is confined to that one function.
    if src.replace(fn_before, "") != out.replace(review_fn(out), ""):
        raise SystemExit("REFUSED: something outside enterResultsReviewMode() "
                         "changed")

    # G3 — every viewer call and the render survive.
    fn_after = review_fn(out)
    for k in KEEP:
        if k not in fn_after:
            raise SystemExit("REFUSED: the review harness lost %s" % k)

    # G4 — the render is no longer behind an await of the viewer.
    head = fn_after[:fn_after.index("computeAndShowResults(true)")]
    if re.search(r"await\s+(initCesium|flyToLocation|moveCloserForPlotIntelligence)",
                 head):
        raise SystemExit("REFUSED: the render still waits on the property view")

    # G5 — the ranking, imagery and card renderers are untouched everywhere.
    for t in FORBIDDEN_NEIGHBOURS:
        if out.count(t) != src.count(t):
            raise SystemExit("REFUSED: %s reference count changed" % t)

    # G6 — syntax, before anything is written.
    for i, b in enumerate(re.findall(
            r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", out, re.S)):
        if not b.strip(): continue
        tmp = os.path.join(ROOT, ".pn-gr-%d.mjs" % i)
        open(tmp, "w", encoding="utf-8").write(b)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            raise SystemExit("REFUSED: script %d does not parse, nothing "
                             "written:\n%s" % (i, r.stderr[:400]))

    if mode == "--check":
        print("CHECK ONLY. %s -> %s, %+d lines, 6 guards pass"
              % (base, sha16(out), out.count("\n") - src.count("\n")))
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied. %s -> %s" % (base, sha16(out)))


if __name__ == "__main__":
    main()
