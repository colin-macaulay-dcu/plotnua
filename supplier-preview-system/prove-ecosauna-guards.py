#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPABILITY PROOF — THE ECOSAUNA BUILDER'S GUARDS CATCH WHAT THEY ARE FOR.
v2, 18 October 2026: rewritten for the premium redesign of the builder.

Each case copies build-ecosauna-preview.py and the provider-led template into
a throwaway directory, makes ONE deliberate break, runs the copy with
--stage and requires it to REFUSE. A final clean run must PASS. The real
builder, template and page are never written.

Run: python3 prove-ecosauna-guards.py
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-ecosauna-preview.py"
TEMPLATE = HERE / "template-provider-led.html"

CASES = [
    ("G0  supplier imagery added with no live grant",
     "ECO_IMAGES = []",
     'ECO_IMAGES = [{"url": "https://mapleapplehost.com/wp-content/uploads/x.jpg", "alt": "x"}]'),
    ("G10b a commercial mechanism switched on",
     'CONNECT_MODE = "none"', 'CONNECT_MODE = "qualified-lead"'),
    ("G3b an illustration given an external image",
     '\'<path d="M22 46v-12a6 6 0 0 1 12 0v12" class="ev-acc"/>\'',
     '\'<image href="https://mapleapplehost.com/a.jpg"/>\''),
    ("G3d rights-process copy in the image position",
     'ILLUS_CAPTION = "Illustration &middot; a generic form, not an EcoSauna product"',
     'ILLUS_CAPTION = "Your image here"'),
    ("G3  hero illustration no longer labelled generic",
     "<figcaption>Illustration &middot; generic forms, not EcoSauna products</figcaption>",
     "<figcaption>EcoSauna in the garden</figcaption>"),
    ("G8  planning-exemption claim",
     '"line": "The classic cylindrical garden sauna, in six sizes."',
     '"line": "The classic cylindrical garden sauna; planning exempt."'),
    ("G8  testimonial wording",
     '("Reached through garden wellness",', '("Highly recommended by customers",'),
    ("G8  origin claim",
     '"line": "A square sauna with more headroom, in seven sizes."',
     '"line": "A square sauna, made in Ireland."'),
    ("G8  VAT basis asserted without evidence",
     '"VERIFIED_PRICE": "From &euro;3,300"', '"VERIFIED_PRICE": "From &euro;3,300 inc. VAT"'),
    ("G8  health claim",
     '"line": "A herbal steam cabin you sit in, 130cm tall."',
     '"line": "A herbal steam cabin with real healing power."'),
    ("G8b nationwide delivery unattributed",
     '"confirmed on contact. EcoSauna say they deliver "',
     '"confirmed on contact. Nationwide delivery "'),
    ("G8c planning firewall removed",
     '"of ours rather than yours: the local authority is the "\n                       "only body that can confirm',
     '"of ours rather than yours: the council can "\n                       "tell you'),
    ("G8e a qualification hidden in a collapsed panel",
     "top; VAT is not stated.</p></div>", "top.</p></div>"),
    ("G9b a dead '#' link",
     '<a class="ev-btn ev-btn-light" href="#products">',
     '<a class="ev-btn ev-btn-light" href="#">'),
    ("G9b an unexpected outbound link",
     '<a class="ev-btn ev-btn-dark" href="%(site)s" rel="noopener">',
     '<a class="ev-btn ev-btn-dark" href="https://example.com/offer" rel="noopener">'),
    ("G10 partnership wording",
     '<h2 id="c-h">Does this represent EcoSauna accurately',
     '<h2 id="c-h">As a PlotNua partner, does this represent EcoSauna accurately'),
    ("G10 commission wording",
     '("Your configurator, understood first",', '("Referral commission on every sale",'),
    ("G10 a lead form",
     '<p class="ev-swipe" aria-hidden="true">',
     '<form><input name="email"></form><p class="ev-swipe" aria-hidden="true">'),
    ("G11 a product renamed",
     '{"name": "Phytosauna", "key": "phyto"', '{"name": "Steam Cabin", "key": "phyto"'),
    ("G11 an unpublished installation value invented",
     '"extras": ["No priced extras are listed in the configurator"],\n     "install": None},\n    {"name": "Phytosauna"',
     '"extras": ["No priced extras are listed in the configurator"],\n     "install": "&euro;300"},\n    {"name": "Phytosauna"'),
    ("G11 a starting price changed",
     '"from_eur": 3300,', '"from_eur": 2800,'),
    ("G6  another supplier's content",
     '"OFFER_NAME": "Barrel Sauna"', '"OFFER_NAME": "Barrel Sauna (as Sauna Experts)"'),
    ("G7  a journey step dropped",
     '    ("Decide", "An informed choice, made in their own time."),\n', ''),
]


def run(src_text, workdir):
    (workdir / "build.py").write_text(src_text, encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", str(workdir / "build.py"),
                        "--stage"], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:]


def main():
    original = BUILDER.read_text(encoding="utf-8")
    before = {p: p.read_bytes() for p in (BUILDER, TEMPLATE)}
    failures = 0
    with tempfile.TemporaryDirectory() as d:
        wd = pathlib.Path(d) / "supplier-preview-system"
        wd.mkdir()
        shutil.copy(TEMPLATE, wd / TEMPLATE.name)
        print("ECOSAUNA BUILDER v2 — GUARD CAPABILITY PROOF")
        print("=" * 74)
        for label, old, new in CASES:
            if original.count(old) != 1:
                print("  BROKEN  %s — anchor not found exactly once" % label)
                failures += 1
                continue
            code, last = run(original.replace(old, new), wd)
            refused = code != 0 and last and last[0].startswith("REFUSED")
            print("  %s  %s" % ("caught" if refused else "MISSED", label))
            if not refused:
                failures += 1
                print("          last line: %r" % (last,))
        code, last = run(original, wd)
        clean = code == 0
        print("  %s  clean build passes" % ("ok    " if clean else "FAILED"))
        if not clean:
            failures += 1
            print("          last line: %r" % (last,))
    same = all(p.read_bytes() == b for p, b in before.items())
    print("-" * 74)
    print("%d of %d checks passed" % (len(CASES) + 1 - failures, len(CASES) + 1))
    print("builder and template byte-identical after the proof: %s"
          % ("YES" if same else "NO"))
    return 0 if failures == 0 and same else 1


if __name__ == "__main__":
    sys.exit(main())
