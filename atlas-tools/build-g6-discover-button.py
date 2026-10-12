#!/usr/bin/env python3
"""
G6 · DISCOVER BUTTON — BOUNDED BUILDER (12 October 2026)
Founder instruction: the plain-text Discovery link beneath "Start the check"
is too subtle. Replace it with a secondary outlined pill:
  "Discover The Borrowed Garden →"  -> discovery-the-borrowed-garden.html
Primary pill unchanged; header link unchanged; one page only.
Gates: each anchor exactly once; switches, consent, engine, register
untouched; #bgStart unchanged; destination href count unchanged; every
changed line is one of the anchors' replacements.
  python3 atlas-tools/build-g6-discover-button.py --check | --apply
"""
import pathlib, sys, difflib
ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "disc025-borrowed-garden-check.html"
DEST = "discovery-the-borrowed-garden.html"
MARK = "PLOTNUA-G6-DISCOVER-BUTTON"

def refuse(m): print("REFUSED: " + m); sys.exit(2)

H_OLD = '''    <button class="pc-cta" id="bgStart">Start the check
      <span class="pc-arrow" aria-hidden="true">&rarr;</span></button>
    <!-- PLOTNUA-G6-ENTRY-LINKS · for first-time visitors arriving from social -->
    <p class="pc-discover"><a href="discovery-the-borrowed-garden.html"><span aria-hidden="true">&#127807;</span> New to The Borrowed Garden? Discover how it works <span aria-hidden="true">&rarr;</span></a></p>
  </section>'''
H_NEW = '''    <div class="pc-actions">
    <button class="pc-cta" id="bgStart">Start the check
      <span class="pc-arrow" aria-hidden="true">&rarr;</span></button>
    <!-- PLOTNUA-G6-ENTRY-LINKS · ''' + MARK + ''' · for first-time visitors arriving from social -->
    <a class="pc-ghost" href="discovery-the-borrowed-garden.html">Discover The Borrowed Garden
      <span class="pc-arrow" aria-hidden="true">&rarr;</span></a>
    </div>
  </section>'''
C_OLD = '''  /* G6 entry link: secondary to the pill - text weight, no fill. */
  .pc-discover{margin:22px 0 0;font-size:15px;line-height:1.5;}
  .pc-discover a{display:inline-block;padding:8px 0;color:var(--ink);
    text-decoration:none;}
  .pc-discover a:hover,.pc-discover a:focus-visible{text-decoration:underline;
    text-underline-offset:4px;}
'''
C_NEW = '''  /* G6 discover button: the outlined twin of the primary pill. Same type,
     radius and height; no fill, no shadow, so Start stays the action. */
  .pc-actions{display:flex;flex-wrap:wrap;align-items:center;gap:14px 16px;
    align-self:flex-start;max-width:100%;}
  .pc-ghost{display:inline-flex;align-items:center;justify-content:center;
    gap:11px;background:transparent;color:var(--ink);
    border:1.5px solid var(--ink);font-family:'Work Sans',sans-serif;
    padding:15px 26.5px;font-size:13.5px;letter-spacing:.09em;
    text-transform:uppercase;border-radius:32px;cursor:pointer;
    text-decoration:none;text-align:center;line-height:normal;
    transition:transform .22s cubic-bezier(.2,.85,.32,1.1),
      background .22s ease;}
  .pc-ghost:hover{background:var(--cream);transform:translateY(-2px);}
  .pc-ghost:active{transform:translateY(0);}
  .pc-ghost .pc-arrow{font-size:16px;line-height:1;transition:transform .22s ease;}
  .pc-ghost:hover .pc-arrow{transform:translateX(3px);}
  .pc-actions .pc-cta:focus-visible,.pc-ghost:focus-visible{
    outline:2px solid var(--accent);outline-offset:3px;}
  @media (max-width:780px){
    /* Phones: stacked, equal width, capped so neither reads as a banner.
       The outlined label may wrap on the narrowest phones; it wraps as
       centred text with the arrow kept on the last line. */
    .pc-actions{display:flex;flex-direction:column;align-items:stretch;
      gap:12px;max-width:340px;}
    .pc-actions .pc-cta{align-self:stretch;justify-content:center;}
    .pc-ghost{display:block;padding:14px 20px;letter-spacing:.07em;}
    .pc-ghost .pc-arrow{display:inline-block;margin-left:4px;}
  }
'''

KEEP = ["var INTEREST_PUBLIC = true;",
        "\"I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.\";",
        "'https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/garden'",
        "inherited_tenure: answers.tenure || ''",
        "$('bgStart').addEventListener('click', function () { advance(); });",
        '<a class="bg-back" href="discovery-the-borrowed-garden.html">Explore The Borrowed Garden']

def build(src):
    if MARK in src: refuse("already applied")
    out = src
    for o, n, lab in ((H_OLD, H_NEW, "HTML"), (C_OLD, C_NEW, "CSS")):
        if out.count(o) != 1: refuse(f"{lab}: anchor found {out.count(o)} times")
        out = out.replace(o, n)
    for k in KEEP:
        if out.count(k) != src.count(k) or out.count(k) < 1: refuse(f"GATE: protected text changed: {k[:50]}")
    changed = [l for l in difflib.unified_diff(src.splitlines(), out.splitlines(), lineterm="", n=0)
               if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    allowed = set(H_OLD.splitlines() + H_NEW.splitlines() + C_OLD.splitlines() + C_NEW.splitlines())
    stray = [l for l in changed if l[1:] not in allowed]
    if stray: refuse(f"GATE: unexpected changed lines: {stray[:3]}")
    if out.count(f'href="{DEST}"') != src.count(f'href="{DEST}"'): refuse("GATE: destination count")
    if "pc-discover" in out: refuse("GATE: old text link still present")
    return out

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    src = PAGE.read_text(encoding="utf-8"); out = build(src)
    if mode == "--apply": PAGE.write_text(out, encoding="utf-8"); print("APPLIED")
    else: print("CHECK OK")

if __name__ == "__main__": main()
