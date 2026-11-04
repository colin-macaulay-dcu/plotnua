#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD - SUPERIOR PERGOLA IRELAND SHOWCASE (suppliers/superior-pergola-ireland.html).

Checks the built page, then breaks the data file in memory and proves the builder refuses.

  SP1  the page is exactly what the builder makes from showcase.json (no hand edits)
  SP2  every photograph is inside the grant's scope (b3819663.assetcdn.net/2.0/3819663/) and shown once
  SP3  every photograph carries the required credit as a working link to superiorpergola.ie
  SP4  the only links to the supplier's site are those credits (no Visit / Shop / Buy button)
  CM1  no percentage anywhere on the page while the saving is off; no commission rate in the data file or builder
  CM4  switched on with its basis confirmed, the saving renders exactly the approved wording, once
  CM2  with the saving switched off, no saving markup exists at all (not hidden: absent)
  CM3  the referral fee is disclosed in words
  PD1  the page collects nothing: no form, no input, no script of its own beyond consent + analytics
  PD2  the consent promise is on the page: nothing reaches the supplier without asking first
  RF1  both help routes carry the attribution ref superior-pergola-ireland
  MUT  the builder refuses: a saving switched on before its basis is confirmed; saving wording that
       names another figure (the combined 8%) or PlotNua's commission; an image outside
       the account prefix; a changed credit; the same photograph twice; a product with no
       Atlas record; a photograph with no Atlas asset record; a review copy written into the repo

Run: python3 supplier-preview-system/prove-superior-pergola-showcase.py
"""
import copy, importlib.util, io, json, re, sys, contextlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "supplier-preview-system" / "build-superior-pergola-showcase.py"
DATAF = ROOT / "supplier-preview-system" / "showcases" / "superior-pergola-ireland" / "showcase.json"
PAGE = ROOT / "suppliers" / "superior-pergola-ireland.html"
PREFIX = "https://b3819663.assetcdn.net/2.0/3819663/"
CREDIT = "Image: Superior Pergola Ireland"

spec = importlib.util.spec_from_file_location("spb", BUILDER)
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
ORIG = copy.deepcopy(B.DATA)
page = PAGE.read_text(encoding="utf-8")
fails = []


def check(code, ok, what):
    print(f"  {'ok  ' if ok else 'FAIL'}  {code}  {what}")
    if not ok:
        fails.append(code)


print("SUPERIOR PERGOLA IRELAND SHOWCASE GUARD\n" + "=" * 74)
check("SP1", B.build() == page, "page matches the builder output")

imgs = re.findall(r'<img src="([^"]+)"', page)
check("SP2", bool(imgs) and all(u.startswith(PREFIX) for u in imgs) and len(imgs) == len(set(imgs)),
      f"{len(imgs)} photographs, all inside {PREFIX}, none repeated")

figs = re.findall(r'<figure class="sp-fig">.*?</figure>', page, re.S)
cred = all(re.search(r'<a href="https://www\.superiorpergola\.ie/[^"]*"[^>]*>' + re.escape(CREDIT) + "</a>", f) for f in figs)
check("SP3", len(figs) == len(imgs) and cred, "every photograph credited with a working link to superiorpergola.ie")

sup_links = re.findall(r'<a href="https://www\.superiorpergola\.ie[^"]*"[^>]*>([^<]*)</a>', page)
check("SP4", all(t in (CREDIT, "superiorpergola.ie") for t in sup_links)
      and not re.search(r">\s*(Visit|Shop|Buy)\b", page),
      f"{len(sup_links)} supplier links, all credits; no sales button")

text = re.sub(r"<style.*?</style>|<script.*?</script>", "", page, flags=re.S)
src = DATAF.read_text(encoding="utf-8") + BUILDER.read_text(encoding="utf-8")
check("CM1", "%" not in re.sub(r"<[^>]+>", " ", text)
      and not re.search(r"(?i)commission[^\n]{0,40}\d|\d\s*%[^\n]{0,30}commission|referral fee[^\n]{0,20}\d", src)
      and not ORIG["offer"]["enabled"],
      "no percentage on the page; no commission rate in the data file or the builder")
check("CM2", "data-pn-offer" not in page and "sp-offer\"" not in page and not ORIG["offer"]["enabled"],
      "saving switched off and absent from the markup")
check("CM3", "may receive a referral fee from Superior Pergola Ireland" in page, "referral fee disclosed in words")
check("PD1", "<form" not in page and "<input" not in page and "<textarea" not in page
      and len(re.findall(r"<script", page)) == 3, "no form, no input; only the consent and analytics scripts")
check("PD2", "never pass your name or contact details to a supplier without asking you first" in page,
      "consent promise present")
check("RF1", page.count("superior-pergola-ireland%29") == 2 or
      (("ref%20superior-pergola-ireland" in page) and page.count("superior-pergola-ireland") >= 4),
      "WhatsApp and email routes carry ref superior-pergola-ireland")


def refuses(label, mutate, argv=None):
    B.DATA = copy.deepcopy(ORIG)
    mutate(B.DATA)
    old = sys.argv
    sys.argv = argv or ["x"]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            if argv:
                B.main()
            else:
                B.build()
        ok = False
    except SystemExit as e:
        ok = bool(e.code) and str(e.code).startswith("FAIL")
    finally:
        sys.argv = old
        B.DATA = copy.deepcopy(ORIG)
    check("MUT", ok, "refuses: " + label)


def first_img(d): return d["images"][1]
refuses("saving switched on, basis unconfirmed", lambda d: d["offer"].update(enabled=True))
refuses("saving switched on with no percent", lambda d: d["offer"].update(enabled=True, basisConfirmed=True, percent=None))
refuses("saving wording naming the combined 8%", lambda d: d["offer"].update(wording="Save 8% on Superior Pergola installations"))
refuses("saving wording naming PlotNua's commission", lambda d: d["offer"].update(wording="4% off; PlotNua earns a commission"))
refuses("saving switched on with a different figure in its wording", lambda d: d["offer"].update(enabled=True, basisConfirmed=True, percent=3))
refuses("image from another assetcdn account", lambda d: first_img(d).update(origin=first_img(d)["origin"].replace("/3819663/", "/9999999/")))
refuses("image from the CDN outside the prefix", lambda d: first_img(d).update(origin="https://b3819663.assetcdn.net/other/x.jpg"))
refuses("credit changed", lambda d: d["supplier"].update(credit="Photo courtesy of Superior Pergola"))
refuses("credit link sent elsewhere", lambda d: d["supplier"].update(creditHref="https://example.com/"))
refuses("same photograph twice", lambda d: d["images"].append(dict(d["images"][2], id="dup")))
refuses("product without Atlas record", lambda d: d["products"][0].update(atlas=""))
refuses("photograph without Atlas asset", lambda d: first_img(d).update(asset=None))
refuses("review copy written inside the repository", lambda d: None,
        argv=["x", "--preview-offer", str(ROOT / "suppliers" / "offer-review.html")])

B.DATA = copy.deepcopy(ORIG); B.DATA["offer"].update(enabled=True, basisConfirmed=True)
try:
    on = B.build(); ok4 = on.count("data-pn-offer") == 1 and ORIG["offer"]["wording"] in on and "8%" not in on
except SystemExit:
    ok4 = False
B.DATA = copy.deepcopy(ORIG)
check("CM4", ok4, "switched on (basis confirmed), the saving renders the approved wording once and nothing else")

print("-" * 74)
print("GUARD PASSED" if not fails else "GUARD FAILED: " + ", ".join(fails))
sys.exit(1 if fails else 0)
