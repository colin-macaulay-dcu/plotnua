#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD-CAPABILITY PROOF — build-hutsmith-preview.py.

A guard that has never refused anything is a comment. This breaks the build
eight ways, once per guard, and every break must be caught. The real
hutsmith-preview.html is restored byte-identical at the end and the check is
printed, because a proof that damages the artefact it is proving is worse than
no proof.

Run: python3 prove-hutsmith-guards.py
"""
import hashlib
import importlib.util
import io
import contextlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-hutsmith-preview.py"
OUT = HERE.parent / "hutsmith-preview.html"

before = OUT.read_bytes() if OUT.exists() else None


def fresh():
    """A clean module each time, so one mutation never leaks into the next."""
    spec = importlib.util.spec_from_file_location("hb%d" % len(sys.modules), BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mutate, label):
    """Apply a mutation, run main(), and report whether it refused."""
    mod = fresh()
    mutate(mod)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = mod.main()
    out = buf.getvalue().strip().splitlines()
    reason = next((l for l in out if l.startswith("REFUSED")), "")
    if code == 0:
        print("  MISSED   %-52s <-- THE GUARD DID NOT FIRE" % label)
        return False
    print("  CAUGHT   %s" % label)
    print("           -> %s" % reason[:140])
    return True


print("GUARD-CAPABILITY PROOF — HUTSMITH PREVIEW BUILDER")
print("=" * 74)

results = []
_t1 = HERE / ".proof-template-no-comment.html"


# G1 — the instruction-comment strip anchor
def g1(m):
    src = m.TEMPLATE.read_text(encoding="utf-8")
    # Remove the instruction block so the strip anchor cannot be found.
    import re
    src = re.sub(r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
                 "\n", src, flags=re.S)
    _t1.write_text(src, encoding="utf-8")
    m.TEMPLATE = _t1

results.append(run(g1, "G1 · the instruction-comment anchor has moved"))

# G2 — a token was renamed in the template
def g2(m):
    m.FILL = dict(m.FILL)
    m.FILL["OFFER_NAME_RENAMED"] = "anything"
results.append(run(g2, "G2 · the copy names a token the template lacks"))

# G3 — the facts-list anchor is no longer unique
def g3(m):
    t = HERE / ".proof-template-dup-facts.html"
    src = m.TEMPLATE.read_text(encoding="utf-8")
    src = src.replace('          <ul class="pn-facts">\n',
                      '          <ul class="pn-facts">\n' * 2, 1)
    t.write_text(src, encoding="utf-8")
    m.TEMPLATE = t
results.append(run(g3, "G3 · the facts-list anchor is duplicated"))

# G4 — a token is left unfilled
def g4(m):
    m.FILL = {k: v for k, v in m.FILL.items() if k != "CLOSING_SUPPORT"}
results.append(run(g4, "G4 · a token is left unreplaced"))

# G5a — a partnership claim reaches the page
def g5a(m):
    m.FILL = dict(m.FILL)
    m.FILL["WHY_1_TEXT"] = "PlotNua is a trusted supplier partner of Hutsmith."
results.append(run(g5a, "G5 · a partnership claim reaches the page"))

# G5b — the commission conversation leaks onto the page
def g5b(m):
    m.FILL = dict(m.FILL)
    m.FILL["CLOSING_SUPPORT"] = "You mentioned a commission on new business."
results.append(run(g5b, "G5 · the commission offer leaks onto the page"))

# G5c — the UK flat-roof planning claim crosses to Ireland
def g5c(m):
    m.FILL = dict(m.FILL)
    m.FILL["VERIFIED_FACT_4"] = "Flat roof, so no planning permission is needed"
results.append(run(g5c, "G5 · a UK planning claim crosses to Ireland"))

# G6 — another supplier's content survives from a previous build
def g6(m):
    m.FILL = dict(m.FILL)
    m.FILL["DEMO_LEDE"] = "Much like the Koto Haku preview we sent last week."
results.append(run(g6, "G6 · another supplier's content is present"))

# G7 — an unauthorised image is referenced
def g7(m):
    m.FILL = dict(m.FILL)
    m.FILL["PHOTO_SLOT_LINE"] = ('<img src="https://hutsmith.co.uk/'
                                 'wp-content/uploads/cabin.jpg" alt="">')
results.append(run(g7, "G7 · an image is referenced with no manifest grant"))

# G8 — the privacy meta is dropped
def g8(m):
    t = HERE / ".proof-template-no-robots.html"
    src = m.TEMPLATE.read_text(encoding="utf-8")
    src = src.replace(
        '<meta name="robots" content="noindex, nofollow, noarchive, '
        'nosnippet, noimageindex">', "")
    t.write_text(src, encoding="utf-8")
    m.TEMPLATE = t
results.append(run(g8, "G8 · the noindex privacy meta is dropped"))

# ── restore, and prove the restore ─────────────────────────────────────────
for junk in HERE.glob(".proof-template-*.html"):
    junk.unlink()

code = fresh().main()
after = OUT.read_bytes()

print("=" * 74)
caught = sum(1 for r in results if r)
print("%d mutations caught, %d missed" % (caught, len(results) - caught))
if before is not None:
    same = hashlib.sha256(before).hexdigest() == hashlib.sha256(after).hexdigest()
    print("preview restored byte-identical: %s  (%s)"
          % ("YES" if same else "NO", hashlib.sha256(after).hexdigest()[:12]))
else:
    print("preview built fresh: %s" % hashlib.sha256(after).hexdigest()[:12])

sys.exit(0 if caught == len(results) and code == 0 else 1)
