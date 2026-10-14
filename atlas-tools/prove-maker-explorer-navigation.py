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
         ROOT / "maker-explorer.js", B, HERE / "maker-product-links-v1.json",
         HERE / "public-information-listings.json"]
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


def links(m, fn):
    """Load the real link evidence, then change it in memory."""
    D = copy.deepcopy(m.links_doc())
    fn(D)
    m._LINKS = D


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
# 14 Oct 2026 (controlled text-only publication expansion): a link now rests
# on VERIFIED page evidence rather than a grant's link-back condition, so the
# cases below break THAT evidence, and the image cases break the rights record
# that still alone governs images.
run("a product link whose page was never verified",
    lambda m: links(m, lambda D: D["links"].pop(next(i for i, e in D["links"].items()
                                                     if e["organisation"] == "Pineca Ireland"))) or
    nav_patch(m, lambda q, o: o.update(href=q.get("productUrl"), site="pineca.ie")
              if q.get("organisation") == "Pineca Ireland" and not o.get("href") else None))
run("a product link whose evidence was REFUSED",
    lambda m: links(m, lambda D: [e.__setitem__("state", "REFUSED") for e in D["links"].values()
                                  if e["organisation"] == "Polaris Sauna"]) or
    nav_patch(m, lambda q, o: o.update(href=q.get("productUrl"), site="polaris-sauna.ie")
              if q.get("organisation") == "Polaris Sauna" else None))
run("a VERIFIED entry pointing at another maker's domain",
    lambda m: links(m, lambda D: [e.update(url="https://www.ognyx.com/products/x", final="https://www.ognyx.com/products/x")
                                  for e in D["links"].values() if e["organisation"] == "TimberIN"]) or
    nav_patch(m, lambda q, o: o.update(href="https://www.ognyx.com/products/x", site="ognyx.com")
              if q.get("organisation") == "TimberIN" else None))
run("a public-information maker given an image",
    lambda m: nav_patch(m, lambda q, o: o.__setitem__("img", [{"src": "https://www.pineca.ie/x.jpg", "alt": "Photograph",
                                                               "kind": "Photograph", "w": 1, "h": 1,
                                                               "credit": "Pineca", "creditHref": "https://www.pineca.ie/"}])
                        if q.get("organisation") == "Pineca Ireland" else None))
def held_ognyx_with_image(m):
    real = m.rights_row("OGNYX")
    a = real["approved_assets"][0]
    im = {"src": a["url"], "alt": a["alt"], "kind": a["kind"].capitalize(), "w": 1, "h": 1,
          "credit": real["required_credit"], "creditHref": "https://www.ognyx.com/"}
    rights(m, "OGNYX", lambda r: r.__setitem__("public_visibility", "HOLD"))
    nav_patch(m, lambda q, o: o.__setitem__("img", [im]) if q.get("productCode") == a["product_code"] else None)


run("images for a maker whose rights record is not PUBLISHABLE (held after the nav was drawn)",
    held_ognyx_with_image)
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
