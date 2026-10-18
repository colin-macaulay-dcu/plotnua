#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPABILITY PROOF — THE ECOSAUNA BUILDER'S GUARDS CATCH WHAT THEY ARE FOR.

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
    ("G0 imagery added while permission is unknown",
     "ECO_IMAGES = []",
     'ECO_IMAGES = [{"url": "https://mapleapplehost.com/wp-content/uploads/x.jpg", "alt": "x"}]'),
    ("G8 planning-exemption claim",
     '"VERIFIED_FACT_3": "Firewood or electric stove"',
     '"VERIFIED_FACT_3": "Firewood or electric stove; planning exempt"'),
    ("G8 testimonial wording",
     '"WHY_3_LABEL": "REACHED THROUGH GARDEN WELLNESS"',
     '"WHY_3_LABEL": "HIGHLY RECOMMENDED BY CUSTOMERS"'),
    ("G8 origin claim",
     '"VERIFIED_FACT_4": "Spruce as standard; Thermowood from +&euro;450"',
     '"VERIFIED_FACT_4": "Made in Ireland in spruce"'),
    ("G8 VAT basis asserted without evidence",
     '"VERIFIED_PRICE": "From &euro;3,300"',
     '"VERIFIED_PRICE": "From &euro;3,300 inc. VAT"'),
    ("G8b nationwide delivery unattributed",
     '"contact. EcoSauna say they deliver to all 32 "',
     '"contact. Nationwide delivery to all 32 "'),
    ("G8c planning firewall removed",
     "the local authority is the \"\n                       \"only body that can confirm",
     "the council can \"\n                       \"tell you"),
    ("G10 partnership wording",
     '"CLOSING_PROPOSITION": "Does this represent EcoSauna accurately for an "',
     '"CLOSING_PROPOSITION": "As a PlotNua partner, does this represent EcoSauna accurately for an "'),
    ("G10 commission wording",
     '"WHY_1_LABEL": "YOUR CONFIGURATOR, UNDERSTOOD FIRST"',
     '"WHY_1_LABEL": "REFERRAL COMMISSION ON EVERY SALE"'),
    ("G11 a product dropped from the range",
     '    {"name": "Phytosauna",',
     '    {"name": "Steam Cabin",'),
    ("G11 an unpublished value invented",
     '"from": "&euro;1,100", "install": None},',
     '"from": "&euro;1,100", "install": "&euro;300"},'),
    ("G6 another supplier's content",
     '"OFFER_NAME": "Barrel Sauna"',
     '"OFFER_NAME": "Barrel Sauna (as Sauna Experts)"'),
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
        print("ECOSAUNA BUILDER — GUARD CAPABILITY PROOF")
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
        code, last = run(original, wd)
        clean = code == 0
        print("  %s  clean build passes" % ("ok    " if clean else "FAILED"))
        if not clean:
            failures += 1
    same = all(p.read_bytes() == b for p, b in before.items())
    print("-" * 74)
    print("%d of %d checks passed" % (len(CASES) + 1 - failures, len(CASES) + 1))
    print("builder and template byte-identical after the proof: %s"
          % ("YES" if same else "NO"))
    return 0 if failures == 0 and same else 1


if __name__ == "__main__":
    sys.exit(main())
