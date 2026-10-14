#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD-CAPABILITY PROOF — build-garden-retreat-maker-imagery.py (V1-V9).

Each case loads a fresh copy of the builder, breaks ONE thing in memory (a
constant, the generated markup, or the data it reads), runs build() and
guards(), and must be REFUSED. Nothing is written; the real files are hashed
before and after.

Run: python3 atlas-tools/prove-garden-retreat-maker-imagery.py
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
B = HERE / "build-garden-retreat-maker-imagery.py"
FILES = [ROOT / "discovery-garden-retreat.html", ROOT / "image-rights-records.json",
         ROOT / "wellness-universe-v1.json", B]
before = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in FILES}
_n = [0]
results = []


def fresh():
    _n[0] += 1
    spec = importlib.util.spec_from_file_location("gmi%d" % _n[0], B)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(label, mutate=None, post=None, expect="REFUSED"):
    m = fresh()
    A = copy.deepcopy(m.assets())
    if mutate:
        mutate(m, A)
    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf):
        try:
            out = m.build(m.PAGE.read_text(encoding="utf-8"), A)
            if post:
                out = post(out)
            m.guards(out, A)
        except SystemExit as e:
            code = e.code
    got = "REFUSED" if code else "BUILT"
    hit = got == expect
    line = (buf.getvalue().strip().splitlines() or [""])[-1]
    print("  %s %-8s %s\n           -> %s" % ("CAUGHT " if hit else "MISSED ", got, label, line[:100]))
    results.append(hit)


def held_code(m, A):
    W = json.loads(m.WELLNESS.read_text(encoding="utf-8"))
    held = [p for p in W["products"] if p["qualification"]["state"] == "HELD"][0]
    A[2]["product_code"] = held["productCode"]


print("GUARD-CAPABILITY PROOF — GARDEN RETREAT MAKER IMAGERY")
print("=" * 78)
run("CONTROL the real build", expect="BUILT")
run("V1 a fifth OGNYX image appears on the page",
    post=lambda o: o.replace("</main>", '<img src="https://www.ognyx.com/cdn/shop/files/x.png" alt="x"></main>', 1))
run("V1 an image src no longer matches the record",
    post=lambda o: o.replace("width=1024", "width=2048", 1))
run("V2 a figure loses its linked credit",
    post=lambda o: o.replace('rel="noopener noreferrer">© OGNYX</a></figcaption>',
                             'rel="noopener noreferrer">OGNYX</a></figcaption>', 1))
run("V3 a visualisation is captioned as a photograph",
    mutate=lambda m, A: m.KIND_LABEL.__setitem__("visualisation", "Photograph"))
run("V4 the images are cropped with object-fit:cover",
    mutate=lambda m, A: setattr(m, "CSS", m.CSS.replace("height:auto;", "height:240px; object-fit:cover;")))
run("V4 a filter is applied", mutate=lambda m, A: setattr(m, "CSS", m.CSS.replace(
    "background:var(--cream); }", "background:var(--cream); filter:saturate(1.3); }")))
run("V5 Irish delivery implied",
    post=lambda o: o.replace("PlotNua has not established delivery", "Free delivery across Ireland; PlotNua has not established delivery", 1))
run("V5 endorsement wording", post=lambda o: o.replace(
    "Three of the listed products", "Three recommended products", 1))
run("V6 an image shows a held product", mutate=held_code)
run("V7 the section is moved below the explorer", post=lambda o: (lambda s, e: o[:s] + o[e:].replace(
    '  <section class="article-section reveal" id="where-this-comes-from">',
    o[s:e] + '  <section class="article-section reveal" id="where-this-comes-from">', 1))(
    o.index("  <!-- PLOTNUA-GR-MAKER-IMAGERY-BEGIN"),
    o.index("  <!-- PLOTNUA-GR-MAKER-IMAGERY-END -->\n") + len("  <!-- PLOTNUA-GR-MAKER-IMAGERY-END -->\n")))
run("V8 the page is edited outside the section",
    post=lambda o: o.replace("Where this comes from", "Where all this comes from", 1))
run("V9 the credit link opens without rel=noopener",
    post=lambda o: o.replace('target="_blank" rel="noopener noreferrer">© OGNYX',
                             'target="_blank">© OGNYX', 1))
after = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in FILES}
print("-" * 78)
print("%d of %d caught" % (sum(results), len(results)))
print("every file byte-identical after the proof: %s" % ("YES" if before == after else "NO"))
sys.exit(0 if all(results) and before == after else 1)
