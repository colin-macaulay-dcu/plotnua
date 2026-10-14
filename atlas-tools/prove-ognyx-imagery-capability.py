#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPABILITY PROOF — atlas-tools/prove-ognyx-imagery-containment.mjs.

A guard that has never refused anything is a comment. Each case breaks the
tree once, in place, runs the containment proof, and restores every touched
file from memory in a finally block; a decoy page is always deleted. Every
touched file is hashed before and after.

Run: python3 atlas-tools/prove-ognyx-imagery-capability.py
"""
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
RECORDS = ROOT / "image-rights-records.json"
PREVIEW = ROOT / "ognyx-preview.html"
PROOF = HERE / "prove-ognyx-imagery-containment.mjs"
DECOY = ROOT / "zz-ognyx-capability-decoy.html"
WELLNESS = ROOT / "wellness-universe-v1.json"
TOUCHED = [RECORDS, PREVIEW, WELLNESS]
if DECOY.exists():
    print("refusing: decoy already on disk"); sys.exit(2)
before = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in TOUCHED}
results = []
OK_IMG = "https://www.ognyx.com/cdn/shop/files/Screenshot2025-08-13at21.01.07.png?v=1755111942&width=1024"
VIS = "https://www.ognyx.com/cdn/shop/files/Screenshot2025-08-12at19.20.47.png?v=1755025372&width=1024"


def proof():
    p = subprocess.run(["node", str(PROOF)], capture_output=True, text=True, cwd=str(ROOT))
    verdict = {0: "CONTAINED", 1: "BREACHED"}.get(p.returncode, "NOT ESTABLISHED")
    detail = next((l.strip() for l in p.stdout.splitlines()
                   if l.strip().startswith(("FAIL", "ERROR"))), "")
    return verdict, detail


def case(label, mutate, expect):
    saved = {f: f.read_bytes() for f in TOUCHED}
    try:
        mutate()
        got, detail = proof()
    finally:
        for f, b in saved.items():
            f.write_bytes(b)
        if DECOY.exists():
            DECOY.unlink()
    hit = got == expect
    print("  %s %-16s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("          -> %s" % (detail[:104] or "(nothing reported)"))
    results.append(hit)


def decoy(body):
    return lambda: DECOY.write_text("<!doctype html><html><body>" + body + "</body></html>",
                                    encoding="utf-8")


def record(fn):
    def go():
        d = json.loads(RECORDS.read_text(encoding="utf-8"))
        fn([r for r in d["records"] if r["organisation_name"] == "OGNYX"][0])
        RECORDS.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return go


print("CAPABILITY PROOF — OGNYX IMAGERY CONTAINMENT")
print("=" * 78)
case("a fifth, unenumerated OGNYX image on a page",
     decoy('<p>© OGNYX</p><a href="https://www.ognyx.com/">OGNYX</a>'
           '<img src="https://www.ognyx.com/cdn/shop/files/other.png" alt="x">'), "BREACHED")
case("an enumerated image without the credit",
     decoy('<a href="https://www.ognyx.com/">OGNYX</a><img src="' + OK_IMG + '" alt="Photograph"> '),
     "BREACHED")
case("an enumerated image without the link back",
     decoy('<p>© OGNYX</p><img src="' + OK_IMG + '" alt="Photograph">'), "BREACHED")
case("a visualisation presented as a photograph",
     decoy('<p>© OGNYX</p><a href="https://www.ognyx.com/">OGNYX</a>'
           '<img src="' + VIS + '" alt="Photograph of the round hot tub">'), "BREACHED")
case("the record loses an enumerated asset",
     record(lambda r: r["approved_assets"].pop()), "BREACHED")
case("the grant loses its featuring scope",
     record(lambda r: r["permission"].__setitem__("scope", ["imagery"])), "BREACHED")
case("the record disappears", lambda: RECORDS.write_text(
     json.dumps({**json.loads(RECORDS.read_text(encoding="utf-8")),
                 "records": [r for r in json.loads(RECORDS.read_text(encoding="utf-8"))["records"]
                             if r["organisation_name"] != "OGNYX"]}, indent=2, ensure_ascii=False) + "\n",
     encoding="utf-8"), "NOT ESTABLISHED")
def wellness(fn):
    def go():
        d = json.loads(WELLNESS.read_text(encoding="utf-8"))
        fn([p for p in d["products"] if p["organisation"] == "OGNYX"][0])
        WELLNESS.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return go


case("an OGNYX record in the wellness universe promises free delivery",
     wellness(lambda p: p.__setitem__("productType", "Sauna with free delivery")), "BREACHED")
case("an OGNYX record repeats a health claim",
     wellness(lambda p: p["price"].__setitem__("basis", "A therapeutic cold plunge")), "BREACHED")
case("CONTROL a properly credited, linked, enumerated use",
     decoy('<p>© OGNYX</p><a href="https://www.ognyx.com/">OGNYX</a>'
           '<img src="' + VIS + '" alt="Visualisation of the round hot tub">'), "CONTAINED")
print("-" * 78)
got, _ = proof()
results.append(got == "CONTAINED")
print("  %s %-16s the untouched tree is contained" % ("CAUGHT " if got == "CONTAINED" else "MISSED ", got))
after = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in TOUCHED}
intact = before == after and not DECOY.exists()
print("=" * 78)
print("%d of %d checks passed" % (sum(results), len(results)))
print("every touched file is byte-identical after the proof: %s" % ("YES" if intact else "NO"))
sys.exit(0 if all(results) and intact else 1)
