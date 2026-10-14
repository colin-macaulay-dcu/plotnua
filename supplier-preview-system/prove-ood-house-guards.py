#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD-CAPABILITY PROOF — build-ood-house-preview.py.

A guard that has never refused anything is a comment. This breaks the build
once per guard and every break must be caught. Every run writes to a
throwaway path, never to ood-house-preview.html, and the clean build is
checked byte-identical to the committed page, so the proof cannot damage the
artefact it proves.

Run: python3 prove-ood-house-guards.py [--stage]
     --stage  skip the byte-identical comparison (the page is staged, not
              committed at the repo root)
"""
import contextlib
import importlib.util
import io
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-ood-house-preview.py"
REAL = HERE.parent / "ood-house-preview.html"
TMP = pathlib.Path(tempfile.mkdtemp(prefix="ood-proof-"))
_n = [0]


def fresh():
    _n[0] += 1
    spec = importlib.util.spec_from_file_location("ood%d" % _n[0], BUILDER)
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


def house(mod, key):
    return [h for h in mod.HOUSES if h["key"] == key][0]


print("GUARD-CAPABILITY PROOF — ÖÖD HOUSE PREVIEW BUILDER")
print("=" * 76)
R = []

ok, clean = run(lambda m: None, "baseline · the real build", expect="BUILT")
R.append(ok)
if "--stage" not in sys.argv:
    same = REAL.exists() and clean.OUT.read_bytes() == REAL.read_bytes()
    print("  %s  committed ood-house-preview.html is byte-identical to a fresh "
          "build" % ("CAUGHT " if same else "MISSED "))
    R.append(same)

R.append(run(lambda m: house(m, "signature")["images"][0].update(
    id="../../etc/passwd"), "G0 · an image that is not a Drive file id")[0])
R.append(run(lambda m: house(m, "glamping")["images"].append(
    dict(house(m, "signature")["images"][0])),
    "G0 · the same image used for two models")[0])
R.append(run(lambda m: house(m, "mobile").update(
    images=house(m, "mobile")["images"][:2]), "G0 · fewer than 3 images")[0])
R.append(run(lambda m: tpl(m, "PROVIDER-LED", "PROVIDER LED"),
             "G1 · instruction-comment anchor has moved")[0])
R.append(run(lambda m: tpl(
    m, 'content="noindex, nofollow, noarchive, nosnippet, noimageindex"',
    'content="index, follow"'), "G5 · robots directives removed")[0])
R.append(run(lambda m: m.FILL.update(WHY_1_TEXT="Like Hutsmith, ..."),
             "G6 · another supplier's name in the copy")[0])
R.append(run(lambda m: setattr(m, "IRISH_FACT", "ÖÖD delivers to Ireland"),
             "G8 · Irish delivery claimed as confirmed")[0])
R.append(run(lambda m: house(m, "signature").update(
    f4=house(m, "signature")["f4"] + "; as at Lough Neagh"),
    "G8 · Northern Ireland site used as Irish evidence")[0])
R.append(run(lambda m: setattr(m, "CREDIT", "ÖÖD"),
             "G9 · required credit wording changed")[0])
R.append(run(lambda m: m.FILL.update(WHY_3_TEXT="ÖÖD is our recommended "
                                     "maker."), "G10 · recommendation implied")[0])
R.append(run(lambda m: m.FILL.update(DEMO_LEDE="Illustrative preview."),
             "G11 · illustrative label repeated")[0])
R.append(run(lambda m: house(m, "extended").update(price="&pound;86,700"),
             "G12 · a UK sterling price")[0])
R.append(run(lambda m: setattr(m, "PRICE_BASIS", m.PRICE_BASIS) or
             house(m, "moon").update(f3=house(m, "moon")["f3"] +
                                     '<img src="https://example.com/x.jpg">'),
             "G13 · an image from outside ÖÖD's Drive files")[0])

print("-" * 76)
caught = sum(R)
print("%d of %d caught" % (caught, len(R)))
print("PROOF PASS" if caught == len(R) else "PROOF FAIL")
sys.exit(0 if caught == len(R) else 1)
