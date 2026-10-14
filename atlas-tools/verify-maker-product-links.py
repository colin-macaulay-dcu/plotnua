#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAKER PRODUCT-LINK VERIFICATION — writes atlas-tools/maker-product-links-v1.json

Founder brief "Garden Retreat — controlled text-only publication expansion",
14 Oct 2026, item 3: "Allow verified HTTPS links to the maker's own public
product pages where supported by the product evidence. Do not require an
invented supplier permission state for an ordinary link. Do not allow
arbitrary external domains." Validate destination domain, product URL, HTTPS,
redirect behaviour, link safety and correct product association.

WHAT THIS DOES. For every wellness product the published universe makes
public (and every candidate the public-information register would add), it
fetches the Atlas Product URL once, records what happened, and decides:

  VERIFIED   https; final address on the maker's own declared domain; no
             credentials, port, query string or fragment; status 200; any
             redirect stays on the same host and only normalises the path
             (trailing slash, case); the page names the product.
  REFUSED    anything else, with the reason.

The file is evidence, not a permission. The maker explorer may link a product
ONLY when its entry here is VERIFIED and still matches the record's own URL;
the public-information gate holds a product whose page is not VERIFIED.

The network is read once, here, by a person running this script. Nothing that
builds the site fetches anything.

  python3 atlas-tools/verify-maker-product-links.py            fetch and write
  python3 atlas-tools/verify-maker-product-links.py --check    re-validate the file offline
"""
import html
import json
import pathlib
import re
import sys
import time
import unicodedata
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "atlas-tools" / "maker-product-links-v1.json"
REGISTER = ROOT / "atlas-tools" / "public-information-listings.json"
CHECK = "--check" in sys.argv
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# The maker's own domains. A product link may land on these and nowhere else.
# Each entry says where the association comes from.
MAKER_DOMAINS = {
    "OGNYX": (["www.ognyx.com"], "Atlas Organisation Website https://www.ognyx.com/"),
    "Tanktribe": (["www.tanktribe.ie"], "Atlas Organisation Website https://www.tanktribe.ie/"),
    "Irish Sauna Company": (["irishsaunacompany.com"], "Atlas Organisation Website https://irishsaunacompany.com/"),
    "Pineca Ireland": (["www.pineca.ie"], "Atlas Organisation Website https://www.pineca.ie/"),
    "Polaris Sauna": (["polaris-sauna.ie"], "Atlas Organisation Website https://polaris-sauna.ie/"),
    "TimberIN": (["www.woodenhottubsale.co.uk"], "Atlas Organisation Website https://www.woodenhottubsale.co.uk/"),
    "Hansa24 Group": (["summerhouse24.ie"],
                      "summerhouse24.ie describes itself as \"Summerhouse24 Ireland (Hansa24 Group)\" "
                      "with organisation @id https://hansa24.com/#organization (read 14 Oct 2026); "
                      "Atlas Organisation Website https://hansa24.com/"),
}

STOP = {"the", "and", "with", "for", "of", "a", "in", "x", "cm", "mm", "m", "m2", "m²",
        "outdoor", "sauna", "saunas", "hot", "tub", "tubs", "cold", "plunge", "garden",
        "wooden", "wood", "fired", "woodfired", "person", "persons", "people", "seats",
        "seat", "modern"}
# The maker's own name is not evidence that a page is about THIS product.
MAKER_TOKENS = {"ognyx", "tanktribe", "irish", "company", "pineca", "ireland", "polaris",
                "timberin", "hansa24", "group", "summerhouse24"}


def norm(s):
    s = html.unescape(s or "")
    s = re.sub(r"[\u2122\u00ae\u00a9]", " ", s)          # ™ ® © are marks, not words
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"(\d)[.,](\d)", r"\1d\2", s)              # 1.8 -> 1d8, so 1.8 m == 1.8m
    s = re.sub(r"(\d)\s*[x\u00d7]\s*(?=\d)", r"\1 ", s)      # 2 x 2 m == 2x2 m
    s = re.sub(r"(\d)\s+(m|cm|mm|kw)\b", r"\1\2", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def distinctive(name):
    """The tokens that tell this product apart: model names and numbers.
    A parenthesis in an Atlas product name is PlotNua's own annotation (a
    supplier G-code, "supplied by", "configurable", a type gloss), never the
    supplier's product title, so it is not required on the page. Generic
    category words and the maker's own name are not evidence of association."""
    bare = re.sub(r"\([^)]*\)", " ", name or "")
    return [t for t in norm(bare).split()
            if t not in STOP and t not in MAKER_TOKENS and len(t) > 1]


def associated(name, page_text):
    toks = distinctive(name)
    if not toks:
        return False, []
    hay = " " + norm(page_text) + " "
    found = [t for t in toks if (" " + t + " ") in hay]
    # Every distinctive token must appear on the page: a partial match is how a
    # link silently lands on a sibling model.
    return len(found) == len(toks), [t for t in toks if t not in found]


def candidates():
    W = json.loads((ROOT / "wellness-universe-v1.json").read_text(encoding="utf-8"))
    reg = json.loads(REGISTER.read_text(encoding="utf-8")) if REGISTER.exists() else {"organisations": []}
    listed = {o["name"] for o in reg.get("organisations", [])}
    snap_urls = {}
    snap = pathlib.Path(sys.argv[sys.argv.index("--snapshot") + 1]) if "--snapshot" in sys.argv else None
    if snap:
        S = json.loads(snap.read_text(encoding="utf-8"))
        snap_urls = {p["id"]: p["fields"].get("Product URL") for p in S["products"]}
    out = []
    for r in W["products"]:
        if r["qualification"]["state"] != "ELIGIBLE":
            continue
        if r["publicVisibility"] == "PUBLISHABLE" or r["organisation"] in listed:
            url = r.get("productUrl") or snap_urls.get(r["id"])
            out.append((r["id"], r["organisation"], r["productName"], url))
    return out


def safe_shape(u):
    p = urlsplit(u or "")
    if p.scheme != "https":
        return "not https"
    if p.username or p.password or p.port:
        return "credentials or port in the address"
    if p.query or p.fragment:
        return "query string or fragment"
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+/[A-Za-z0-9._~/%+-]*", u):
        return "unexpected character in the address"
    return None


def same_path(a, b):
    na = urlsplit(a).path.rstrip("/").lower()
    nb = urlsplit(b).path.rstrip("/").lower()
    return na == nb


def fetch(url):
    import requests
    hops = []
    cur = url
    for _ in range(5):
        for wait in (0, 8, 20, 45):          # a 429 is the site asking us to slow down
            time.sleep(wait)
            r = requests.get(cur, headers={"User-Agent": UA, "Accept-Language": "en-IE,en;q=0.9"},
                             allow_redirects=False, timeout=25)
            if r.status_code != 429:
                break
        if r.status_code in (301, 302, 303, 307, 308):
            nxt = requests.compat.urljoin(cur, r.headers.get("Location", ""))
            hops.append({"status": r.status_code, "to": nxt})
            cur = nxt
            continue
        title = ""
        m = re.search(r"<title[^>]*>(.*?)</title>", r.text or "", re.S | re.I)
        if m:
            title = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
        h1 = " ".join(re.sub(r"<[^>]+>", " ", x) for x in
                      re.findall(r"<h1[^>]*>(.*?)</h1>", r.text or "", re.S | re.I))
        og = " ".join(re.findall(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', r.text or "", re.I)
                      + re.findall(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', r.text or "", re.I))
        return {"status": r.status_code, "final": cur, "hops": hops,
                "title": title[:200], "heading": re.sub(r"\s+", " ", html.unescape(h1)).strip()[:200],
                "og": html.unescape(og)[:400]}
    return {"status": "too-many-redirects", "final": cur, "hops": hops, "title": "", "heading": "", "og": ""}


def decide(org, name, url, got):
    doms, _ = MAKER_DOMAINS.get(org, ([], ""))
    why = safe_shape(url)
    if why:
        return "REFUSED", why
    if urlsplit(url).hostname not in doms:
        return "REFUSED", "the product URL is not on the maker's own domain"
    if got["status"] != 200:
        return "REFUSED", "the page answered %s" % got["status"]
    fin = got["final"]
    why = safe_shape(fin)
    if why:
        return "REFUSED", "after redirect: " + why
    if urlsplit(fin).hostname != urlsplit(url).hostname:
        return "REFUSED", "the page redirects to another host"
    if not same_path(url, fin):
        return "REFUSED", "the page redirects to a different path (%s)" % urlsplit(fin).path
    ok, missing = associated(name, " ".join((got["title"], got["heading"], got["og"])))
    if not ok:
        return "REFUSED", "the page's title, heading and description do not name the product (missing: %s)" % ", ".join(missing)
    return "VERIFIED", None


def check_file():
    D = json.loads(OUT.read_text(encoding="utf-8"))
    bad = []
    for pid, e in D["links"].items():
        doms, _ = MAKER_DOMAINS.get(e["organisation"], ([], ""))
        if e["state"] == "VERIFIED":
            if safe_shape(e["url"]) or urlsplit(e["url"]).hostname not in doms:
                bad.append(pid + " verified link off-domain or unsafe")
            if e["status"] != 200 or not same_path(e["url"], e["final"]):
                bad.append(pid + " verified link without a clean 200")
            if not associated(e["productName"], " ".join((e["title"], e["heading"], e["og"])))[0]:
                bad.append(pid + " verified link whose page does not name the product")
    if bad:
        print("CHECK FAILED:\n  " + "\n  ".join(bad))
        sys.exit(1)
    n = sum(1 for e in D["links"].values() if e["state"] == "VERIFIED")
    print("maker product links · CHECK OK — %d verified, %d refused, read %s"
          % (n, len(D["links"]) - n, D["checkedAt"]))


def main():
    if CHECK:
        return check_file()
    links = {}
    for pid, org, name, url in candidates():
        try:
            got = fetch(url) if url else {"status": "no-url", "final": "", "hops": [], "title": "", "heading": "", "og": ""}
        except Exception as e:     # a network failure is a refusal, never a pass
            got = {"status": "error: %s" % type(e).__name__, "final": "", "hops": [], "title": "", "heading": "", "og": ""}
        state, why = decide(org, name, url, got)
        links[pid] = {"organisation": org, "productName": name, "url": url, "state": state,
                      "reason": why, "status": got["status"], "final": got["final"],
                      "redirects": got["hops"], "title": got["title"], "heading": got["heading"],
                      "og": got["og"]}
        print("  %-8s %-20s %s%s" % (state, org[:20], name[:50], "" if not why else "  — " + why))
        time.sleep(1.5)
    doc = {
        "schema": "plotnua.maker-product-links.v1",
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rule": ("A product may link to the maker's own page only when its entry is VERIFIED: https, "
                 "on the maker's own domain, no query/fragment/credentials/port, HTTP 200, any redirect "
                 "same host and same path, and the page's title, heading or meta description names "
                 "every distinctive word of the product name (PlotNua's own parenthetical notes excepted). Evidence, not permission; no tracking is ever added."),
        "makerDomains": {k: {"domains": v[0], "basis": v[1]} for k, v in MAKER_DOMAINS.items()},
        "links": links,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = sum(1 for e in links.values() if e["state"] == "VERIFIED")
    print("wrote %s — %d verified, %d refused" % (OUT.name, n, len(links) - n))


if __name__ == "__main__":
    main()
