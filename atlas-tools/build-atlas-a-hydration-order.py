#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER: the hydration bootstrap must not depend on parse order.

THE BUG, EXACTLY AS THE FOUNDER DIAGNOSED IT.

The bootstrap is a classic inline <script>, so it executes synchronously the
moment the parser reaches it. Its first two statements were:

    var tpl = document.getElementById("pn-atlas-a-template");
    if (!tpl) return;

and <template id="pn-atlas-a-template"> appears AFTER that script in the
document. So at execution time the template did not exist yet, tpl was null,
the IIFE returned on its second line, and:

    * window.pnAtlasHydrate was NEVER assigned
    * the DOMContentLoaded listener was NEVER registered
    * every local `if (window.pnAtlasHydrate) window.pnAtlasHydrate(x)` call
      silently did nothing, because the guard was false

The result is total: not one hydrated Atlas mark has ever rendered. Not the
60x54 masthead lockup, not the 20px "What Atlas Knows" heading, not either 24px
popover mark. Only the 16px evidence-row signature appeared, because it is a
plain <img> and never touches this code at all. That is exactly what the founder
reported seeing, and it was never cache and never CSS.

WHY EVERY GUARD MISSED IT. The proof read the page as TEXT. It verified that the
bootstrap existed, that it cloned the template, that it stripped the ids, that it
tagged the fields, that the CSS was right. Every one of those was true. Not one
of them executed the code, so not one could see that the function exits before it
installs anything. A proof that only reads source cannot catch an ordering bug;
this change ships with a proof that RUNS the bootstrap.

THE FIX, option B: resolve the template AT HYDRATION TIME, never at install
time.

    * window.pnAtlasHydrate is installed unconditionally, first.
    * fill() looks the template up when it actually needs it.
    * if the template is not parsed yet, fill() returns WITHOUT marking the slot
      done, so the next hydration pass retries it. Nothing is permanently lost.
    * the DOMContentLoaded path is unchanged in shape, but now it is always
      registered -- by then the template is certainly parsed.
    * the local aaRenderAssessment() call still works, including after the lazy
      detail repaint, because it resolves the template on each call.

So script order can no longer silently disable Atlas: the bootstrap could sit
before the template, after it, or in the <head>, and hydration still happens.

NOTHING ELSE CHANGES. Not the geometry, the 60x54 box, the masthead layout, the
9s/11s ambient drift, the motion bounds, the fixed house, the responsive stack,
the evidence gating, or any other placement. This is the bootstrap's control flow
and nothing else.

ONE NOTE ON THE COMMENT WORDING. The new comment deliberately says "the\npn-atlas-a-template element" rather than writing the id= form, because this\nbuilder also asserts that the page still holds exactly ONE occurrence of that\nid string. Writing it in prose would make the count 2 and the builder would\nrefuse itself -- which it did, on the first run.\n\nAnchored. One edit, which must match exactly once or the builder refuses.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE.parent / "your-plot.html"


def die(msg):
    sys.stderr.write("REFUSED: " + msg + "\n")
    raise SystemExit(2)


OLD = """(function(){
  var tpl = document.getElementById("pn-atlas-a-template");
  if (!tpl) return;
  var DELAYS = { "atlas-dark-field": 90, "atlas-sage-field": 240 };
  function fill(slot){
    if (!slot || slot.getAttribute("data-atlas-done")) return;
"""

NEW = """(function(){
  /* THE TEMPLATE IS RESOLVED AT HYDRATION TIME, NEVER AT INSTALL TIME.

     This function used to begin by capturing the template and returning if it
     was absent. Because the pn-atlas-a-template element sits AFTER this
     script in the document, it was always absent at execution time: the IIFE
     returned on its second line, window.pnAtlasHydrate was never assigned, the
     DOMContentLoaded listener was never registered, and every
     `if (window.pnAtlasHydrate)` call elsewhere silently did nothing. No
     hydrated Atlas mark rendered at all.

     So nothing here may depend on parse order. pnAtlasHydrate is installed
     unconditionally; fill() looks the template up when it needs it; and if the
     template is not parsed yet, fill() returns WITHOUT marking the slot done,
     so the next pass retries it. This script could sit before the template,
     after it, or in the head, and hydration still happens. */
  var DELAYS = { "atlas-dark-field": 90, "atlas-sage-field": 240 };
  function template(){
    var t = document.getElementById("pn-atlas-a-template");
    return (t && t.content && t.content.firstElementChild) ? t : null;
  }
  function fill(slot){
    if (!slot || slot.getAttribute("data-atlas-done")) return;
    var tpl = template();
    /* Not parsed yet. Leave the slot UNMARKED so a later pass fills it. */
    if (!tpl) return;
"""


def build():
    if not PAGE.exists():
        die("your-plot.html not found at " + str(PAGE))

    before = PAGE.read_text(encoding="utf-8")

    if "function template(){" in before:
        die("the bootstrap already resolves the template lazily; this builder "
            "has already been applied. Nothing written.")

    n = before.count(OLD)
    if n != 1:
        die("anchor matched %d times, expected exactly 1. Nothing written." % n)

    src = before.replace(OLD, NEW)

    # THE BUG MUST BE GONE. No install-time capture may survive.
    boot = src[src.index("/* ATLAS A HYDRATION"):src.index('<template id="pn-atlas-a-template"')]
    if 'var tpl = document.getElementById("pn-atlas-a-template");\n  if (!tpl) return;' in boot:
        die("the install-time template capture survives. Nothing written.")
    # And pnAtlasHydrate must be assigned unconditionally: no `return` may
    # precede its assignment at the IIFE's own statement level.
    head = boot.split("window.pnAtlasHydrate = function")[0]
    stripped = __import__("re").sub(r"/\*[\s\S]*?\*/", "", head)
    for line in stripped.splitlines():
        s = line.strip()
        if s.startswith("return") and not line.startswith("    "):
            die("a top-level return still precedes the pnAtlasHydrate "
                "assignment: %r. Nothing written." % s)

    # EVERYTHING ELSE UNTOUCHED.
    for keep, what in [
        ("mastMark.setAttribute('data-atlas-size', '60')", 'the 60px masthead placement'),
        ("mastMark.setAttribute('data-atlas-height', '54')", 'the aspect-correct height'),
        ('.pn-atlas-mark--60{ width:60px; height:54px; }', 'the 60x54 box'),
        ('animation-duration:620ms, 9s;', 'the 9s dark drift'),
        ('animation-duration:620ms, 11s;', 'the 11s sage drift'),
        ('@keyframes pn-atlas-a-drift-dark{', 'the dark keyframes'),
        ('@keyframes pn-atlas-a-drift-sage{', 'the sage keyframes'),
        ('@media (max-width:360px){', 'the responsive stack'),
        ("if (row.state === 'established' && !row.scope && !row.conflict){", 'the evidence gate'),
        ("am.src = 'assets/brand/atlas-mark-micro.svg'", 'the gated micro signature'),
        ('<span class="pn-atlas-slot" data-atlas-size="24"></span>', 'the popover slots'),
        ("akMark.setAttribute('data-atlas-size', '20')", 'the panel slot'),
        ('id="pn-atlas-a-template"', 'the single template'),
        ('viewBox="0 0 1157 1038"', 'the supplied viewBox'),
        ('g.classList.add(id === "atlas-dark-field" ? "pn-am-dark" : "pn-am-sage")',
         'the field-distinguishing classes'),
        ('h.removeAttribute("id")', 'the house id strip'),
    ]:
        if src.count(keep) != before.count(keep):
            die("something unrelated changed: " + what + ". Nothing written.")

    if src == before:
        die("no change produced; refusing to claim a build")

    PAGE.write_text(src, encoding="utf-8")
    print("WROTE " + str(PAGE))
    print("  %d bytes -> %d bytes (+%d)"
          % (len(before.encode()), len(src.encode()),
             len(src.encode()) - len(before.encode())))
    print("  1 anchored edit; template now resolved at hydration time")
    print("  pnAtlasHydrate installed unconditionally; everything else verified unchanged")


if __name__ == "__main__":
    build()
