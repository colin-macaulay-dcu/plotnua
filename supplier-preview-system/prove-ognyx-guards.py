#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-ognyx-preview.py (onboarding edition).

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught. Every run writes to a
throwaway path, never to ognyx-preview.html, and the clean build is checked
byte-identical to the committed page.

Run: python3 supplier-preview-system/prove-ognyx-guards.py [--stage]
     --stage  skip the byte-identical comparison with the committed page
"""
import contextlib
import importlib.util
import io
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-ognyx-preview.py"
REAL = HERE.parent / "ognyx-preview.html"
TMP = pathlib.Path(tempfile.mkdtemp(prefix="ognyx-proof-"))
_n = [0]


def fresh():
    _n[0] += 1
    spec = importlib.util.spec_from_file_location("og%d" % _n[0], BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.OUT = TMP / ("out%d.html" % _n[0])
    return mod


def run(mutate, label, expect="REFUSED"):
    mod = fresh()
    mutate(mod)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            code = mod.main()
        except SystemExit as e:
            code = e.code
    lines = buf.getvalue().strip().splitlines()
    got = "REFUSED" if code else "BUILT"
    hit = got == expect
    print("  %s  %-7s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("            -> %s" % (lines[0][:116] if lines else ""))
    return hit, mod


def tpl(mod, old, new):
    p = TMP / ("tpl%d.html" % _n[0])
    s = mod.TEMPLATE.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit("proof setup: %r not in the template" % old)
    p.write_text(s.replace(old, new), encoding="utf-8")
    mod.TEMPLATE = p


def panel(mod, key):
    return [p for p in mod.PANELS if p["key"] == key][0]


print("GUARD-CAPABILITY PROOF — OGNYX PREVIEW BUILDER (ONBOARDING EDITION)")
print("=" * 78)
R = []

ok, _ = run(lambda m: None, "baseline · the real build", expect="BUILT")
R.append(ok)
if "--stage" not in sys.argv:
    same = REAL.exists() and _.OUT.read_bytes() == REAL.read_bytes()
    print("  %s  committed ognyx-preview.html is byte-identical to a fresh "
          "build" % ("CAUGHT " if same else "MISSED "))
    R.append(same)

R.append(run(lambda m: m.IMG["plunge2"].update(
    url="https://images.example.com/not-ognyx.png"),
    "G0 · an image from another domain")[0])
R.append(run(lambda m: m.IMG.update(extra=dict(m.IMG["tub"])),
             "G0 · a fifth, uninspected image is added")[0])
R.append(run(lambda m: m.IMG["sauna"].update(kind=""),
             "G0 · an image is left unclassified")[0])
R.append(run(lambda m: panel(m, "tub").update(images=["tub", "sauna"]),
             "G0 · one image used for two products")[0])
R.append(run(lambda m: m.IMG["plunge2"].update(
    alt="ChatGPT image of the empty cold plunge tub, a photograph"),
    "G0b · an AI-named asset")[0])
R.append(run(lambda m: m.IMG["sauna"].update(
    alt="Photograph of the OGNYX 1.6m outdoor barrel sauna"),
    "G0c · a visualisation described as a photograph")[0])
R.append(run(lambda m: m.RANGE.pop(), "G0d · a product drops out of the range")[0])
R.append(run(lambda m: tpl(m, "PROVIDER-LED", "PROVIDER LED"),
             "G1 · instruction-comment anchor has moved")[0])
R.append(run(lambda m: tpl(
    m, 'content="noindex, nofollow, noarchive, nosnippet, noimageindex"',
    'content="index, follow"'), "G5 · robots directives removed")[0])
R.append(run(lambda m: m.FILL.update(WHY_3_TEXT="Like Tanktribe, ..."),
             "G6 · another supplier's name in the copy")[0])
R.append(run(lambda m: panel(m, "plunge").update(
    f5="Proven health benefits of cold immersion"),
    "G8 · OGNYX's own health claim repeated")[0])
R.append(run(lambda m: setattr(m, "PRICE_BASIS", "Price including VAT."),
             "G8 · a VAT basis nobody published")[0])
R.append(run(lambda m: setattr(m, "CHECK", "free delivery anywhere in Ireland."),
             "G8 · free delivery promised")[0])
R.append(run(lambda m: panel(m, "sauna").update(f4="In stock now"),
             "G8 · stock asserted")[0])
R.append(run(lambda m: setattr(m, "credit_for", lambda i: m.CREDIT),
             "G8b · a visualisation loses its on-image label")[0])
R.append(run(lambda m: setattr(m, "CREDIT", "OGNYX"),
             "G9 · required credit wording changed")[0])
R.append(run(lambda m: setattr(m, "PRODUCT_BASE", "https://example.com/p/"),
             "G9 · product links no longer point to ognyx.com")[0])
R.append(run(lambda m: m.FILL.update(WHY_1_TEXT="OGNYX is our recommended "
                                     "supplier."),
             "G10 · recommendation implied")[0])
R.append(run(lambda m: m.FILL.update(DEMO_LEDE="Illustrative preview."),
             "G11 · illustrative label repeated")[0])

print("-" * 78)
caught = sum(R)
print("%d of %d caught" % (caught, len(R)))
print("PROOF PASS" if caught == len(R) else "PROOF FAIL")
sys.exit(0 if caught == len(R) else 1)
