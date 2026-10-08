#!/usr/bin/env python3
"""
G3 REVIEW HARNESS BUILDER — FOUNDER VISUAL REVIEW ONLY
===============================================================================
This builds the files Colin opens to look at the G3 panel. It is NOT part of
the product, touches no production file, and changes no switch. It reads
disc025-borrowed-garden-check.html and writes only into the outputs folder.

-------------------------------------------------------------------------------
WHY THE PREVIOUS HARNESS FAILED — ROOT CAUSE, MEASURED
-------------------------------------------------------------------------------
The first harness put the page into `<iframe srcdoc="...">`. A srcdoc frame's
document URL is `about:srcdoc`, which has NO QUERY STRING. The shipped page
tests preview mode like this, and only like this:

    function intPreviewRequested() {
      try { return /(?:^|[?&])interest=preview(?:&|$)/.test(location.search); }
      catch (e) { return false; }
    }
    function intGatesPass() {
      if (!INTEREST_PUBLIC && !intPreviewRequested()) return false;
      ...

With `location.search` empty and `INTEREST_PUBLIC` false, gate 1 failed, so
`interestOffer()` took its correct branch and REMOVED #bgInterest from the DOM.
That produced all three reported symptoms from one cause:

    state 1  -> "section absent"                        (the section was gone)
    state 2  -> Cannot read properties of null ('click') (bgIntOpen was null)
    state 3  -> Cannot read properties of null ('click') (same)

The null clicks were consequential, exactly as the founder judged. Measured in
jsdom: a srcdoc frame reports `location.search === ""`.

THE SHIPPED PAGE BEHAVED CORRECTLY THROUGHOUT. The defect was mine, introduced
when I replaced a `src="page.html?interest=preview"` frame with srcdoc to dodge
file:// origin problems.

-------------------------------------------------------------------------------
THE REPAIR, AND WHY THIS SHAPE
-------------------------------------------------------------------------------
Each state is a STANDALONE PAGE COPY that drives itself, loaded by `src` with a
real `?interest=preview` query string. Consequences:

  * The page's OWN gate mechanism is used, exactly as written. No flag is
    flipped, no constant is substituted, nothing is faked. If the real gate
    ever stopped working, this harness would fail rather than hide it.
  * The parent review files contain NO SCRIPT AT ALL and never touch
    contentWindow, so file:// opaque origins are irrelevant.
  * Each state file is an ordinary page plus one driver script, so it can be
    tested headlessly in jsdom — which srcdoc cannot.

Two rejected alternatives, recorded so they are not retried:
  * srcdoc + flipping INTEREST_PUBLIC to true in the copy. Works, but tests a
    different code path from the one the founder is reviewing, and suppresses
    the "Private preview" ribbon (the page shows it only when the flag is
    false). Rejected: a review harness must not alter what it is reviewing.
  * srcdoc + history.replaceState to invent a query string. Unverifiable here
    (no browser in this environment) and likely to throw on about:srcdoc.

-------------------------------------------------------------------------------
FAIL CLOSED
-------------------------------------------------------------------------------
The driver never calls .click() on an unchecked element. Every prerequisite is
polled for and asserted; on any absence it paints a specific HARNESS FAILURE
banner, sets the document title to a failure marker, and stops. Nothing leaves
the browser: `fetch` is replaced before the form can be submitted.
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "disc025-borrowed-garden-check.html"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = pathlib.Path(ARGS[0]) if ARGS else None

# TENURE, 8 October 2026. Added for the PRE-G5 correction: the founder must see
# the BUYING state, which did not exist before the correction (a buying
# homeowner was shown the permission block and could not submit without it).
# `own` remains the default, so every existing invocation and the 46/0 suite
# behave exactly as before.
TENURE = "own"
for _a in sys.argv[1:]:
    if _a.startswith("--tenure="):
        TENURE = _a.split("=", 1)[1]
if TENURE not in ("own", "rent", "buying"):
    print("REFUSED: --tenure must be own, rent or buying (got %r)" % TENURE)
    sys.exit(1)

# Representative Property Check answers: a clear corner, side access, still
# using it. Chosen because it is the ordinary workable case and does NOT trip
# the founder-Q1 no_garden suppression. Only the tenure varies.
ANSWERS = ("{tenure:'%s',spare_corner:'yes_a_clear_corner',"
           "way_in:'side_or_rear_access',your_own_use:'now_and_then'}" % TENURE)

# The exact closed-state heading the founder approved. Asserted, not assumed.
CLOSED_HEADING = "The register isn’t open yet"

STATES = [
    ("1-invitation", "invitation", "1 · the invitation"),
    ("2-form",       "form",       "2 · the expanded form, filled"),
    ("3-closed",     "closed",     "3 · the closed state (503 not_open)"),
]

# Loaders that cannot resolve with no network. Removed from the REVIEW COPIES
# only; the production file is never written. Each must match, or the build
# refuses — a silent miss would leave a hanging frame.
STRIP = [
    (r'<script id="Cookiebot"[^>]*></script>\n?', "Cookiebot", 1),
    (r'<script async src="https://www\.googletagmanager\.com[^>]*></script>\n?',
     "gtag loader", 1),
    (r'<link href="https://fonts\.googleapis\.com[^>]*>\n?', "Google Fonts", 1),
    (r'<link rel="preconnect"[^>]*>\n?', "preconnect", 2),
]

DRIVER = """
<!-- ===================================================================
     G3 REVIEW DRIVER — harness only, appended to a COPY of the page.
     Drives this page to ONE state and asserts every prerequisite before
     touching it. Never clicks an unchecked element.
     =================================================================== -->
<script>
(function () {
  var STATE = '__STATE__';
  var ANS   = __ANSWERS__;
  var CLOSED_HEADING = '__CLOSED_HEADING__';

  /* Nothing leaves the browser. Installed before any submit is possible. */
  window.fetch = function () {
    return Promise.resolve({
      status: 503,
      json: function () { return Promise.resolve({ state: 'not_open' }); }
    });
  };

  var $ = function (id) { return document.getElementById(id); };

  function banner(ok, text) {
    var b = document.createElement('div');
    b.setAttribute('data-g3-marker', ok ? 'OK' : 'FAIL');
    b.style.cssText =
      'position:relative;z-index:9999;margin:0;padding:10px 14px;' +
      'font:500 12px/1.45 -apple-system,BlinkMacSystemFont,sans-serif;' +
      'letter-spacing:.04em;color:#fff;background:' +
      (ok ? '#1F3B2E' : '#8A2E20') + ';';
    b.textContent = text;
    document.body.insertBefore(b, document.body.firstChild);
    document.title = (ok ? 'G3-OK ' : 'G3-FAIL ') + text;
    window.__g3marker = (ok ? 'OK' : 'FAIL') + ':' + text;
  }

  function fail(why) { banner(false, 'HARNESS FAILURE \\u2014 ' + why); }

  /* Poll instead of guessing a timeout. Resolves true as soon as the
     condition holds, false once the budget is spent. */
  function until(test, budgetMs, done) {
    var waited = 0, step = 25;
    (function tick() {
      var ok = false;
      try { ok = !!test(); } catch (e) { ok = false; }
      if (ok) return done(true);
      waited += step;
      if (waited >= budgetMs) return done(false);
      setTimeout(tick, step);
    })();
  }

  /* CORRECTION 2 · POSITION ON THE COMPONENT THE FOUNDER IS REVIEWING.
     The first harness scrolled #bgInterest to the top, so the closed state sat
     below the ribbon, eyebrow and headline and did not appear in the capture.
     This scrolls to the element that MATTERS for the state, keeping a small
     amount of context above it, and records where it went so the proof can
     assert the target rather than assume it. Positioning only — the page's own
     copy and layout are untouched. */
  function show(el, context) {
    try {
      var top = el.getBoundingClientRect().top + (window.scrollY || 0)
                - (context === undefined ? 24 : context);
      window.scrollTo(0, top < 0 ? 0 : top);
      window.__g3scroll = { target: el.id, top: top };
    } catch (e) {
      try { el.scrollIntoView({ block: 'start' }); } catch (e2) {}
      window.__g3scroll = { target: el.id, top: null };
    }
  }

  /* ---- step 1 · the page's own journey must have booted ---------------- */
  if (!window.__disc025 || typeof window.__disc025.answer !== 'function') {
    return fail('the page journey did not boot: window.__disc025 is absent');
  }

  /* ---- step 2 · preview mode must be established THE PAGE'S OWN WAY ---- */
  if (!/(?:^|[?&])interest=preview(?:&|$)/.test(location.search)) {
    return fail('this copy was opened without ?interest=preview, so the ' +
                'page correctly withholds the section (location.search = ' +
                JSON.stringify(location.search) + ')');
  }

  /* ---- step 3 · drive the representative answers ---------------------- */
  try { window.__disc025.answer(ANS); }
  catch (e) { return fail('driving the Property Check threw: ' + e.message); }

  /* ---- step 4 · WAIT for the invitation to genuinely exist ------------- */
  until(function () { return $('bgInterest') && $('bgIntOpen'); }, 3000,
  function (ok) {
    if (!ok) {
      return fail('#bgInterest or #bgIntOpen never appeared after the ' +
                  'Property Check resolved');
    }
    /* ---- step 5 · assert the invitation --------------------------------- */
    var sec = $('bgInterest');
    if (sec.hidden) return fail('#bgInterest exists but is hidden');
    if ($('bgIntOffer').hidden) return fail('the invitation block is hidden');
    show(sec);

    if (STATE === 'invitation') {
      return banner(true, 'OK-INVITATION \\u2014 #bgInterest and the ' +
                          'invitation control are present');
    }

    /* ---- step 6 · ONLY NOW open the form ------------------------------- */
    try { $('bgIntOpen').click(); }
    catch (e) { return fail('clicking the invitation threw: ' + e.message); }

    /* ---- step 7 · assert every control before touching it -------------- */
    var NEED = ['bgIntName', 'bgIntEmail', 'bgIntDistrict', 'bgIntWater',
                'bgIntSize', 'bgIntTiming', 'bgIntNote', 'bgIntConsent',
                'bgIntSend', 'bgIntCancel', 'bgIntForm'];
    until(function () {
      if ($('bgIntForm').hidden) return false;
      for (var i = 0; i < NEED.length; i++) { if (!$(NEED[i])) return false; }
      return true;
    }, 3000, function (ok2) {
      if (!ok2) {
        var missing = NEED.filter(function (id) { return !$(id); });
        return fail('the form did not open, or controls are missing: ' +
                    (missing.length ? missing.join(', ') : '#bgIntForm hidden'));
      }
      var v = function (id, x) { $(id).value = x; };
      v('bgIntName', 'Aoife');
      v('bgIntEmail', 'aoife@example.ie');
      v('bgIntDistrict', 'raheny');
      v('bgIntWater', 'outside_tap');
      v('bgIntSize', 'small');
      v('bgIntTiming', 'flexible');
      $('bgIntConsent').checked = true;
      show($('bgInterest'));

      if (STATE === 'form') {
        return banner(true, 'OK-FORM \\u2014 all 11 controls present and the ' +
                            'form is filled');
      }

      /* ---- step 8 · ONLY NOW simulate the 503 ------------------------- */
      try {
        $('bgIntForm').dispatchEvent(
          new Event('submit', { cancelable: true, bubbles: true }));
      } catch (e) { return fail('submitting threw: ' + e.message); }

      /* ---- step 9 · assert the EXACT closed-state heading ------------- */
      until(function () {
        return !$('bgIntDone').hidden &&
               $('bgIntDoneH').textContent.trim() === CLOSED_HEADING &&
               $('bgIntDoneBody').querySelectorAll('p').length >= 2;
      }, 3000, function (ok3) {
        if (!ok3) {
          return fail('the closed state did not render as approved. ' +
                      'done hidden=' + $('bgIntDone').hidden +
                      ' heading=' + JSON.stringify(
                        $('bgIntDoneH').textContent.trim()) +
                      ' paragraphs=' +
                      $('bgIntDoneBody').querySelectorAll('p').length);
        }
        if (!$('bgIntForm').hidden || !$('bgIntOffer').hidden) {
          return fail('the closed state rendered but the form or invitation ' +
                      'is still visible');
        }
        /* CORRECTION 2: position on #bgIntDone, the closed response, so the
           heading and both paragraphs are what the capture actually shows. */
        show($('bgIntDone'), 56);
        banner(true, 'OK-CLOSED \\u2014 heading and both paragraphs match the ' +
                     'approved wording');
      });
    });
  });
})();
</script>
"""

PARENT = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>G3 visual review &mdash; %(label)s</title><style>
 body{margin:0;background:#232825;color:#e9e5d9;
   font:13px/1.55 -apple-system,BlinkMacSystemFont,sans-serif;}
 header{padding:16px 14px 12px;}
 h1{font-size:14px;letter-spacing:.14em;text-transform:uppercase;margin:0 0 7px;
   font-weight:500;}
 .note{margin:0;color:#a7aea9;font-size:11.5px;max-width:54em;}
 .note b{color:#d9cfb8;font-weight:500;}
 .cap{margin:0 0 22px;}
 .cap h2{font-size:11px;letter-spacing:.12em;text-transform:uppercase;
   color:#cbb79a;margin:0 0 7px 14px;font-weight:500;}
 .hold{margin-left:14px;overflow:hidden;
   background:#F8F5EC;border:1px solid #4a514c;}
 iframe{width:%(w)dpx;border:0;display:block;
   transform:scale(%(s)s);transform-origin:top left;}
</style></head><body>
<header><h1>%(label)s</h1>
<p class="note">The <b>real shipped page</b>, one copy per state, each loaded
 with its own <b>?interest=preview</b> query string &mdash; so the page's own
 gate decides whether to show the panel. Each frame is exactly <b>%(w)dpx</b>
 wide.%(scalenote)s <code>fetch</code> is replaced inside every copy, so
 <b>nothing leaves the browser</b>.</p>
<p class="note" style="margin-top:7px">A <b>dark green banner</b> at the top of a
 frame means the state was reached and asserted. A <b>dark red banner</b> is a
 harness failure and names the missing prerequisite. Cookiebot, gtag and Google
 Fonts are stripped from these copies only (they cannot resolve offline), so
 type falls back to the system sans-serif; spacing, colour and layout are true.</p>
</header>
%(frames)s
</body></html>"""


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def main():
    if OUT is None:
        die("usage: build-g3-review-harness.py <output-directory>")
    if not PAGE.exists():
        die("production page not found: %s" % PAGE)

    src = PAGE.read_text(encoding="utf-8")
    page_sha = hashlib.sha256(src.encode("utf-8")).hexdigest()
    print("  SOURCE  %s" % PAGE.name)
    print("  bytes   %d" % len(src.encode("utf-8")))
    print("  sha256  %s" % page_sha)
    print()

    # The harness must be building the G3 page, not something else.
    for marker in ("PLOTNUA-G3-INTEREST-BEGIN", "bgInterest", "bgIntOpen",
                   "intPreviewRequested", "__disc025"):
        if marker not in src:
            die("source does not contain %s — wrong file?" % marker)
    if "var INTEREST_PUBLIC = false;" not in src:
        die("source does not ship with INTEREST_PUBLIC = false")
    if CLOSED_HEADING not in src:
        die("source does not contain the approved closed-state heading")

    # Build the review copy: strip only the offline-unresolvable loaders.
    copy = src
    print("  STRIPPED FROM THE REVIEW COPIES ONLY")
    for pat, what, expect in STRIP:
        copy, n = re.subn(pat, "", copy)
        print("    %-14s removed %d (expected %d)" % (what, n, expect))
        if n != expect:
            die("%s matched %d times, expected %d" % (what, n, expect))

    # Nothing else may change. Prove it: the copy must still carry the shipped
    # flag and the whole G3 region untouched.
    if "var INTEREST_PUBLIC = false;" not in copy:
        die("the review copy lost INTEREST_PUBLIC = false — it must NOT be "
            "flipped; the query string is what opens the gate")
    a, b = "/* PLOTNUA-G3-INTEREST-BEGIN", "/* PLOTNUA-G3-INTEREST-END */"
    if src[src.index(a):src.index(b)] != copy[copy.index(a):copy.index(b)]:
        die("the G3 region differs between source and review copy")
    print("    G3 region      IDENTICAL to source")
    print("    INTEREST_PUBLIC still false in the copy")
    print()

    OUT.mkdir(parents=True, exist_ok=True)
    tail = "</body>\n</html>"
    if copy.count(tail) != 1:
        die("cannot find a unique document tail to append the driver before")

    print("  WRITTEN")
    for fname, state, _label in STATES:
        drv = (DRIVER.replace("__STATE__", state)
                     .replace("__ANSWERS__", ANSWERS)
                     .replace("__CLOSED_HEADING__", CLOSED_HEADING))
        doc = copy.replace(tail, drv + "\n" + tail, 1)
        p = OUT / ("state-%s.html" % fname)
        p.write_text(doc, encoding="utf-8")
        print("    %-28s %8d bytes" % (p.name, len(doc.encode("utf-8"))))

    for fname, w, s, label in [("review-390.html", 390, 1.0, "390px · phone"),
                               ("review-1440.html", 1440, 0.33,
                                "1440px · desktop")]:
        # CORRECTION 2: per-state frame heights. The closed response is short,
        # so a 1500px frame buried it in whitespace. Each state gets a height
        # that suits what it has to show.
        HEIGHTS = {'1-invitation': 1150, '2-form': 1800, '3-closed': 620}
        frames = []
        for sf, _st, flabel in STATES:
            fh = HEIGHTS[sf]
            frames.append(
                '<div class="cap"><h2>%s</h2>'
                '<div class="hold" style="width:%dpx;height:%dpx">'
                '<iframe src="state-%s.html?interest=preview" title="%s" '
                'style="height:%dpx"></iframe></div></div>'
                % (flabel, int(w * s), int(fh * s), sf, flabel, fh))
        scalenote = ("" if s == 1.0 else
                     " Shown at %d%% so it fits on screen." % round(s * 100))
        doc = PARENT % {"label": label, "w": w, "s": s,
                        "frames": "\n".join(frames), "scalenote": scalenote}
        p = OUT / fname
        p.write_text(doc, encoding="utf-8")
        print("    %-28s %8d bytes   (no script; %d frames)"
              % (p.name, len(doc.encode("utf-8")), len(STATES)))

    print()
    print("  PRODUCTION PAGE UNCHANGED  sha256 %s"
          % hashlib.sha256(PAGE.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
