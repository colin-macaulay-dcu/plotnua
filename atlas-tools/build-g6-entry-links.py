#!/usr/bin/env python3
"""
G6 · ENTRY LINKS FOR FIRST-TIME VISITORS — BOUNDED BUILDER (12 October 2026)
Founder instruction: two changes to disc025-borrowed-garden-check.html only.
  L1  top-right header link text: "Back to the story" -> "Explore The Borrowed Garden →"
  L2  a secondary link beneath "Start the check":
      "🌿 New to The Borrowed Garden? Discover how it works →"
Both link to the canonical Discovery page, discovery-the-borrowed-garden.html.
Gates: each anchor exactly once; switches, consent, engine, register untouched;
every changed line is one of the two links or their CSS.
  python3 atlas-tools/build-g6-entry-links.py --check | --apply
"""
import pathlib, sys, difflib
ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "disc025-borrowed-garden-check.html"
DEST = "discovery-the-borrowed-garden.html"
MARK = "PLOTNUA-G6-ENTRY-LINKS"

def refuse(m): print("REFUSED: " + m); sys.exit(2)

L1_OLD = '    <a class="bg-back" href="discovery-the-borrowed-garden.html">Back to the story</a>'
L1_NEW = ('    <a class="bg-back" href="discovery-the-borrowed-garden.html">Explore The Borrowed Garden '
          '<span aria-hidden="true">&rarr;</span></a>')
L2_OLD = '''    <button class="pc-cta" id="bgStart">Start the check
      <span class="pc-arrow" aria-hidden="true">&rarr;</span></button>
  </section>'''
L2_NEW = '''    <button class="pc-cta" id="bgStart">Start the check
      <span class="pc-arrow" aria-hidden="true">&rarr;</span></button>
    <!-- ''' + MARK + ''' · for first-time visitors arriving from social -->
    <p class="pc-discover"><a href="discovery-the-borrowed-garden.html"><span aria-hidden="true">&#127807;</span> New to The Borrowed Garden? Discover how it works <span aria-hidden="true">&rarr;</span></a></p>
  </section>'''
CSS_OLD = '''  .pc-cta .pc-arrow{font-size:16px;line-height:1;'''
CSS_NEW = '''  /* G6 entry link: secondary to the pill - text weight, no fill. */
  .pc-discover{margin:22px 0 0;font-size:15px;line-height:1.5;}
  .pc-discover a{display:inline-block;padding:8px 0;color:var(--ink);
    text-decoration:none;}
  .pc-discover a:hover,.pc-discover a:focus-visible{text-decoration:underline;
    text-underline-offset:4px;}
  .pc-cta .pc-arrow{font-size:16px;line-height:1;'''

KEEP = ["var INTEREST_PUBLIC = true;",
        "\"I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.\";",
        "'https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/garden'",
        "inherited_tenure: answers.tenure || ''"]

def build(src):
    if MARK in src: refuse("already applied")
    out = src
    for o, n, lab in ((L1_OLD, L1_NEW, "L1 header link"), (L2_OLD, L2_NEW, "L2 discover link"), (CSS_OLD, CSS_NEW, "CSS")):
        if out.count(o) != 1: refuse(f"{lab}: anchor found {out.count(o)} times")
        out = out.replace(o, n)
    for k in KEEP:
        if out.count(k) != src.count(k) or out.count(k) < 1: refuse(f"GATE: protected text changed: {k[:50]}")
    changed = [l for l in difflib.unified_diff(src.splitlines(), out.splitlines(), lineterm="", n=0)
               if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    allowed = set(L1_OLD.splitlines() + L1_NEW.splitlines() + L2_NEW.splitlines() + CSS_NEW.splitlines())
    stray = [l for l in changed if l[1:] not in allowed]
    if stray: refuse(f"GATE: unexpected changed lines: {stray[:3]}")
    if out.count(f'href="{DEST}"') != src.count(f'href="{DEST}"') + 1: refuse("GATE: destination count")
    return out

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    src = PAGE.read_text(encoding="utf-8"); out = build(src)
    if mode == "--apply": PAGE.write_text(out, encoding="utf-8"); print("APPLIED")
    else: print("CHECK OK")

if __name__ == "__main__": main()
