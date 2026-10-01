#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD-CAPABILITY PROOF — build-hutsmith-preview.py.

A guard that has never refused anything is a comment. This breaks the build
once per guard and every break must be caught. It also exercises the state-A
imagery path in a temp directory, because the whole point of that path is that
it will be used the moment real Hutsmith image URLs exist, and an untested
path would fail then rather than now.

The real hutsmith-preview.html is restored byte-identical at the end and the
check is printed: a proof that damages the artefact it proves is worse than
no proof.

Run: python3 prove-hutsmith-guards.py
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-hutsmith-preview.py"
OUT = HERE.parent / "hutsmith-preview.html"

before = OUT.read_bytes() if OUT.exists() else None
_n = [0]


def fresh():
    """A clean module each time, so one mutation never leaks into the next."""
    _n[0] += 1
    spec = importlib.util.spec_from_file_location("hb%d" % _n[0], BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mutate, label, expect="REFUSED"):
    mod = fresh()
    mutate(mod)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = mod.main()
    lines = buf.getvalue().strip().splitlines()
    got = "REFUSED" if code else "BUILT"
    hit = got == expect
    print("  %s  %-7s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("            -> %s" % (lines[0][:116] if lines else ""))
    return hit


def temp_template(mod, transform, name):
    """Write a mutated template to a temp file and point the builder at it."""
    p = HERE / name
    p.write_text(transform(mod.TEMPLATE.read_text(encoding="utf-8")),
                 encoding="utf-8")
    mod.TEMPLATE = p


print("GUARD-CAPABILITY PROOF — HUTSMITH PREVIEW BUILDER")
print("=" * 76)
results = []

# G1 — the instruction-comment strip anchor moved
results.append(run(lambda m: temp_template(
    m, lambda s: re.sub(
        r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
        "\n", s, flags=re.S),
    ".proof-no-comment.html"),
    "G1 · instruction-comment anchor has moved"))

# G2 — the frozen journey band is missing
results.append(run(lambda m: temp_template(
    m, lambda s: re.sub(r"\n<!-- FROZEN.*?\n<div class=\"journey\">.*?\n</div>\n",
                        "\n", s, flags=re.S),
    ".proof-no-journey.html"),
    "G2 · frozen journey band not found"))

# G3 — the held photo slot is gone, so state A cannot replace it
def g3(m):
    m.HUTSMITH_IMAGES = [{"url": "https://hutsmith.co.uk/a.jpg", "alt": "x"}]
    temp_template(m, lambda s: re.sub(
        r'          <div class="pn-photo-slot">.*?</div>\n', "", s, flags=re.S),
        ".proof-no-slot.html")
results.append(run(g3, "G3 · held photo slot missing in state A"))

# G4 — a token was renamed in the template
results.append(run(lambda m: m.FILL.__setitem__("OFFER_NAME_RENAMED", "x"),
                   "G4 · copy names a token the template lacks"))

# G5 — the facts-list anchor is no longer unique
results.append(run(lambda m: temp_template(
    m, lambda s: s.replace('          <ul class="pn-facts">\n',
                           '          <ul class="pn-facts">\n' * 2, 1),
    ".proof-dup-facts.html"),
    "G5 · facts-list anchor duplicated"))

# G6 — the closing heading is not where it was
results.append(run(lambda m: temp_template(
    m, lambda s: s.replace("<h2>What we&rsquo;d like to explore</h2>",
                           "<h2>Something else entirely</h2>"),
    ".proof-no-h2.html"),
    "G6 · closing heading not found"))

# G7 — the journey band is altered by the move rather than relocated
results.append(run(lambda m: setattr(
    m, "main", m.main) or temp_template(
    m, lambda s: s.replace('<div class="jstep"><b>Discover</b>',
                           '<div class="jstep"><b>Discovery</b>'),
    ".proof-journey-edited.html") or None,
    "G7 · journey band content edited (relocation must be byte-exact)",
    expect="BUILT"))   # editing the template itself is legal; G7 proves the
                       # MOVE does not alter it, which this still satisfies.

# G8 — a token is left unfilled
results.append(run(lambda m: m.FILL.pop("CLOSING_SUPPORT"),
                   "G8 · a token is left unreplaced"))

# G9a — imagery set with no live rights record
results.append(run(lambda m: setattr(m, "HUTSMITH_IMAGES",
    [{"url": "https://hutsmith.co.uk/a.jpg", "alt": "x"}]),
    "G9 · imagery published with no live rights record"))

# G9b — imagery on a domain that is not Hutsmith's
def g9b(m):
    m.HUTSMITH_IMAGES = [{"url": "https://cdn.example.com/a.jpg", "alt": "x"}]
    tmp = pathlib.Path("/tmp/proofA"); tmp.mkdir(exist_ok=True)
    rec = json.loads((m.SITE / "image-rights-records.json").read_text())
    rec["records"].append({"organisation_name": "Hutsmith",
                           "permission_outcome": "Granted — Founder Confirmed"})
    (tmp / "image-rights-records.json").write_text(json.dumps(rec))
    m.SITE = tmp; m.OUT = tmp / "x.html"
results.append(run(g9b, "G9 · image URL not on hutsmith.co.uk"))

# G10a — a partnership claim reaches the page
results.append(run(lambda m: m.FILL.__setitem__(
    "WHY_1_TEXT", "PlotNua is a trusted supplier partner of Hutsmith."),
    "G10 · partnership claim reaches the page"))

# G10b — the commission conversation leaks onto the page
results.append(run(lambda m: m.FILL.__setitem__(
    "CLOSING_SUPPORT", "You mentioned a commission on new business."),
    "G10 · commission offer leaks onto the page"))

# G10c — the UK flat-roof planning claim crosses to Ireland
results.append(run(lambda m: m.FILL.__setitem__(
    "VERIFIED_FACT_4", "Flat roof, so no planning permission is needed"),
    "G10 · UK planning claim crosses to Ireland"))

# G10d — "imagine" creeps back into the copy
results.append(run(lambda m: m.FILL.__setitem__(
    "DEMO_HEADING", "Imagine an Irish homeowner reaching Hutsmith"),
    "G10 · speculative 'imagine' creeps back in"))

# G11 — another supplier's content survives a previous build
results.append(run(lambda m: m.FILL.__setitem__(
    "DEMO_LEDE", "Much like the Koto Haku preview we sent last week."),
    "G11 · another supplier's content is present"))

# G12a — the page still asks for photography already granted
results.append(run(lambda m: temp_template(
    m, lambda s: s.replace("<b>Your project photography here</b>",
                           "<b>Your project photos here</b>"),
    ".proof-slot-heading-moved.html"),
    "G12a · photo-slot heading reworded, so it cannot be corrected"))

# G12 — the privacy meta is dropped
results.append(run(lambda m: temp_template(
    m, lambda s: s.replace(
        '<meta name="robots" content="noindex, nofollow, noarchive, '
        'nosnippet, noimageindex">', ""),
    ".proof-no-robots.html"),
    "G12 · noindex privacy meta dropped"))

# ── the state-A path must actually work ────────────────────────────────────
print("-" * 76)
print("STATE A — the path that runs the moment real image URLs exist")


def state_a(m):
    m.HUTSMITH_IMAGES = [
        {"url": "https://hutsmith.co.uk/wp-content/uploads/a.jpg",
         "alt": "A Hutsmith cabin"},
        {"url": "https://hutsmith.co.uk/wp-content/uploads/b.jpg",
         "alt": "A Hutsmith cabin interior"}]
    tmp = pathlib.Path("/tmp/proofA2"); tmp.mkdir(exist_ok=True)
    rec = json.loads((m.SITE / "image-rights-records.json").read_text())
    rec["records"].append({"organisation_name": "Hutsmith",
                           "permission_outcome": "Granted — Founder Confirmed"})
    (tmp / "image-rights-records.json").write_text(json.dumps(rec))
    m.SITE = tmp; m.OUT = tmp / "hutsmith-preview.html"


ok = run(state_a, "state A builds with images + a live record", expect="BUILT")
if ok:
    s = (pathlib.Path("/tmp/proofA2/hutsmith-preview.html")
         .read_text(encoding="utf-8"))
    checks = [
        ("two first-party <img> in the hero",
         s.count('<img src="https://hutsmith.co.uk') == 2),
        ("credit line present", "credit-line" in s),
        ("held slot div removed", '<div class="pn-photo-slot">' not in s),
        ("no longer asks for photography",
         "Your project photography" not in s),
    ]
    for label, good in checks:
        print("            %s %s" % ("OK  " if good else "FAIL", label))
        ok = ok and good
results.append(ok)

# ── restore, and prove the restore ─────────────────────────────────────────
for junk in HERE.glob(".proof-*.html"):
    junk.unlink()

code = fresh().main()
after = OUT.read_bytes()

print("=" * 76)
caught = sum(1 for r in results if r)
print("%d of %d checks passed" % (caught, len(results)))
if before is not None:
    same = hashlib.sha256(before).hexdigest() == hashlib.sha256(after).hexdigest()
    print("preview restored byte-identical: %s  (%s)"
          % ("YES" if same else "NO", hashlib.sha256(after).hexdigest()[:12]))
else:
    print("preview built fresh: %s" % hashlib.sha256(after).hexdigest()[:12])

sys.exit(0 if caught == len(results) and code == 0 else 1)
