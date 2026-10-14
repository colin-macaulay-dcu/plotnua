#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD-CAPABILITY PROOF — product navigation in build-maker-explorer.py.

Founder brief "Garden Retreat — final pre-launch corrections", 14 Oct 2026:
the explorer may now link a product to its maker's own page and show
authorised images. Those are the two ways it could publish something nobody
permitted, so each guard that stops it is broken once here, in memory, and
must refuse. Nothing is written; every touched file is hashed before and
after.

The script side (one fragment read, no URL writes) is held by G4 AND by the
sha256 pin (G11): any edit to maker-explorer.js refuses before G4 is reached.

Run: python3 atlas-tools/prove-maker-explorer-navigation.py
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
B = HERE / "build-maker-explorer.py"
PAGE = "discovery-garden-retreat.html"
FILES = [ROOT / PAGE, ROOT / "image-rights-records.json", ROOT / "wellness-universe-v1.json",
         ROOT / "maker-explorer.js", B]
before = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in FILES}
_n = [0]
results = []


def fresh():
    _n[0] += 1
    spec = importlib.util.spec_from_file_location("mxn%d" % _n[0], B)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(label, mutate=None, expect="REFUSED"):
    m = fresh()
    if mutate:
        mutate(m)
    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf):
        try:
            m.build(PAGE, m.PAGES[PAGE], (ROOT / PAGE).read_text(encoding="utf-8"))
        except SystemExit as e:
            code = e.code
    got = "REFUSED" if code else "BUILT"
    hit = got == expect
    line = (buf.getvalue().strip().splitlines() or [""])[-1]
    print("  %s %-8s %s\n           -> %s" % ("CAUGHT " if hit else "MISSED ", got, label, line[:110]))
    results.append(hit)


def rights(m, org, fn):
    """Load the real rights rows, then change one in memory."""
    m.rights_row(org)
    row = copy.deepcopy(m._RIGHTS[org])
    fn(row)
    m._RIGHTS[org] = row


def nav_patch(m, fn):
    real = m.product_nav
    def patched(q):
        out = real(q)
        return fn(q, out) or out
    m.product_nav = patched


def first_href(q, out, new):
    if out.get("href") and not getattr(first_href, "done", False):
        out["href"] = new
        first_href.done = True


print("GUARD-CAPABILITY PROOF — MAKER EXPLORER PRODUCT NAVIGATION")
print("=" * 78)
run("CONTROL the real Garden Retreat build", expect="BUILT")
run("a product link pointed at another domain",
    lambda m: nav_patch(m, lambda q, o: o.update(href="https://example.com/x") if o.get("href") else None))
run("a product link carrying a query string",
    lambda m: nav_patch(m, lambda q, o: o.update(href=o["href"] + "?ref=plotnua") if o.get("href") else None))
run("a maker whose grant has no link-back condition",
    lambda m: rights(m, "Tanktribe", lambda r: r["permission"].__setitem__(
        "conditions", [c for c in r["permission"]["conditions"] if c != "link-back"])) or
    nav_patch(m, lambda q, o: o.update(href=q.get("productUrl"), site="tanktribe.ie")
              if q.get("organisation") == "Tanktribe" else None))
run("a maker whose rights record is not PUBLISHABLE",
    lambda m: rights(m, "Irish Sauna Company", lambda r: r.__setitem__("public_visibility", "HOLD")) or
    nav_patch(m, lambda q, o: o.update(href=q.get("productUrl"), site="irishsaunacompany.com")
              if q.get("organisation") == "Irish Sauna Company" else None))
run("an image that is not among the maker's approved assets",
    lambda m: nav_patch(m, lambda q, o: [im.__setitem__("src", "https://www.ognyx.com/cdn/shop/files/other.png")
                                         for im in o.get("img", [])] and None))
run("a visualisation labelled as a photograph",
    lambda m: nav_patch(m, lambda q, o: [im.update(alt="Photograph of a hot tub")
                                         for im in o.get("img", []) if im["kind"] == "Visualisation"] and None))
run("an image without the required credit",
    lambda m: nav_patch(m, lambda q, o: [im.__setitem__("credit", "OGNYX") for im in o.get("img", [])] and None))
run("an unexpected navigation field (a tracking parameter)",
    lambda m: nav_patch(m, lambda q, o: o.__setitem__("utm", "x") if o.get("href") else None))
run("an external link in the static block that is not an image credit",
    lambda m: m.PAGES[PAGE].__setitem__("intro", m.PAGES[PAGE]["intro"] +
                                         ' <a href="https://example.com/">more</a>'))
run("the shared script edited (any edit, e.g. a URL write) refuses at the pin",
    lambda m: m.PINS.__setitem__(m.SHARED_JS, "0" * 64))

after = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in FILES}
print("-" * 78)
print("%d of %d correct" % (sum(results), len(results)))
print("every file byte-identical after the proof: %s" % ("YES" if before == after else "NO"))
sys.exit(0 if all(results) and before == after else 1)
