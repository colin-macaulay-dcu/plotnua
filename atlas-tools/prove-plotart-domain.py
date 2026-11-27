#!/usr/bin/env python3
"""Live checks for the PlotArt domain migration (R1, prepared 26 Nov 2026). Read-only: GET/HEAD and DNS lookups only.

  site      every PlotArt page and file of plotart/ answers 200 at <base>/<path>; pages carry the plotart.ie canonical;
            --indexing noindex|index checks the X-Robots-Tag header (testing vs after cutover)
  redirects every https://plotnua.ie/plotart/<path> answers 301 with Location https://plotart.ie/<path>, query kept
  plotnua   PlotNua itself is unaffected: its own pages answer 200 from https://plotnua.ie (not redirected)
  dns       plotnua.ie mail and verification records still match the inventory taken on 26 Nov 2026

Usage: python3 atlas-tools/prove-plotart-domain.py <repo-root> site --base https://plotart-site.colin-a41.workers.dev --indexing noindex
Exit status 1 on any failure; prints one line per failure and a summary.
"""
import argparse, concurrent.futures as cf, json, os, re, sys, urllib.error, urllib.request

UA = {"User-Agent": "PlotArt-domain-check/1"}
INVENTORY = {   # plotnua.ie, public DNS, 26 Nov 2026 (dns.google). Must survive the nameserver move unchanged.
    ("plotnua.ie", "MX"): ["1 smtp.google.com."],
    ("plotnua.ie", "TXT"): ["v=spf1 include:_spf.google.com ~all",
                            "google-site-verification=F60i8FgB6hqKHjPYaNx8eIbbFziRC1Ro3omIcUm2LsE",
                            "pinterest-site-verification=43734d093eca5e544e28b40564868371"],
    ("_dmarc.plotnua.ie", "TXT"): ["v=DMARC1; p=none; rua=mailto:hello@plotnua.ie; fo=1"],
    ("google._domainkey.plotnua.ie", "TXT"): ["v=DKIM1;k=rsa;p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyMZASa42wLEp1dfJimOzoguB3Z9NNWEU6SwOCocr/BoLeadq8+c+KUb5sBLXrmBZ2jus+0zXEpMJzlBaGdzGbmMxwMIEN1Ji9wcLZhsjQBwNikQ9XQaAyzHXGJxPI1zIXdxInoRhuCqyBHbV7PAcNZsdSNG8bupyf5+1awTtH9bfyWVnEiRfUKh+UuGNmf2hd9k2meAzChXdffuke8jZZ/DeHzAukxh/USENKN11mpkj924mNsBImha/obukzVn3jLyAumKXNXZM6jwQQhWij1OLBeQASG2/16W/cQerNUu6HLGjs698ULSW8wufoLVIA0pgrHIfEOLGeY+N/wz+YQIDAQAB"],
    ("www.plotnua.ie", "CNAME"): ["colin-macaulay-dcu.github.io."],
}
PLOTNUA_PAGES = ["", "discoveries.html", "privacy.html", "terms.html", "contact.html", "about.html",
                 "cookie-policy.html", "discovery-a-home-for-art.html", "sitemap.xml", "robots.txt"]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPEN = urllib.request.build_opener(NoRedirect)


def fetch(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers=UA)
    try:
        with OPEN.open(req, timeout=30) as r:
            return r.status, dict(r.headers), r.read() if method == "GET" else b""
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), b""
    except Exception as e:                              # network failure counts as a failure, with its reason
        return 0, {"error": str(e)}, b""


def paths(root):
    out = []
    src = os.path.join(root, "plotart")
    for d, _, names in os.walk(src):
        for n in names:
            rel = os.path.relpath(os.path.join(d, n), src).replace(os.sep, "/")
            out.append(rel[: -len("index.html")] if rel.endswith("index.html") else rel)
    return sorted(out)


def run(jobs):
    with cf.ThreadPoolExecutor(12) as ex:
        return [f for f in ex.map(lambda j: j(), jobs) if f]


def site(root, base, indexing):
    base = base.rstrip("/")

    def job(p):
        def check():
            method = "GET" if p == "" or p.endswith((".html", "/")) else "HEAD"
            s, h, body = fetch(f"{base}/{p}", method)
            if s != 200:
                return f"{s} {base}/{p}"
            tag = {k.lower(): v for k, v in h.items()}.get("x-robots-tag", "")
            if indexing == "noindex" and "noindex" not in tag:
                return f"not noindexed: /{p}"
            if indexing == "index" and "noindex" in tag:
                return f"still noindexed: /{p}"
            if method == "GET" and p.endswith((".html", "/")) or p == "":
                m = re.search(rb'<link rel="canonical" href="([^"]+)"', body)
                if m and not m.group(1).decode().startswith("https://plotart.ie/"):
                    return f"canonical not on plotart.ie: /{p} -> {m.group(1).decode()}"
                if b"plotnua.ie/plotart" in body:
                    return f"old address in page: /{p}"
        return check
    ps = paths(root)
    return ps, run([job(p) for p in ps])


def redirects(root):
    def job(p):
        def check():
            s, h, _ = fetch(f"https://plotnua.ie/plotart/{p}", "HEAD")
            loc = {k.lower(): v for k, v in h.items()}.get("location", "")
            if s != 301 or loc != f"https://plotart.ie/{p}":
                return f"{s} https://plotnua.ie/plotart/{p} -> {loc or '-'}"
        return check
    ps = paths(root)
    fails = run([job(p) for p in ps])
    s, h, _ = fetch("https://plotnua.ie/plotart/gallery/?utm_source=check", "HEAD")
    if {k.lower(): v for k, v in h.items()}.get("location") != "https://plotart.ie/gallery/?utm_source=check":
        fails.append("query string not kept by the redirect")
    s, h, _ = fetch("https://plotnua.ie/plotart", "HEAD")
    if s != 301 or {k.lower(): v for k, v in h.items()}.get("location") not in ("https://plotart.ie/", "https://plotart.ie"):
        fails.append(f"{s} https://plotnua.ie/plotart (no slash)")
    # www, and a query on a deep artwork page
    s, h, _ = fetch("https://www.plotnua.ie/plotart/artworks/?sort=new", "HEAD")
    loc = {k.lower(): v for k, v in h.items()}.get("location", "")
    if not (s == 301 and loc == "https://plotart.ie/artworks/?sort=new"):
        fails.append(f"www: {s} -> {loc or '-'}")
    # the rule must match ONLY /plotart and /plotart/...: PlotNua's own pages, and look-alike paths, are never redirected
    for path in ("", "discoveries.html", "discovery-a-home-for-art.html", "privacy.html", "plotart-x.html", "plotartist/", "plotart.html"):
        s, h, _ = fetch(f"https://plotnua.ie/{path}", "HEAD")
        loc = {k.lower(): v for k, v in h.items()}.get("location", "")
        if "plotart.ie" in loc:
            fails.append(f"unrelated path redirected: /{path} -> {loc}")
    return ps, fails


def plotnua():
    def job(p):
        def check():
            s, _, _ = fetch(f"https://plotnua.ie/{p}", "GET")
            return None if s == 200 else f"{s} https://plotnua.ie/{p}"
        return check
    return PLOTNUA_PAGES, run([job(p) for p in PLOTNUA_PAGES])


def dns():
    fails = []
    types = {"MX": 15, "TXT": 16, "CNAME": 5}
    for (name, t), want in INVENTORY.items():
        s, _, body = fetch(f"https://dns.google/resolve?name={name}&type={t}")
        try:
            got = sorted(a["data"].strip('"') for a in json.loads(body).get("Answer", []) if a["type"] == types[t])
        except Exception:
            got = []
        if t == "TXT":
            got = [g.replace('" "', "") for g in got]
        missing = [w for w in want if w not in got]
        if missing:
            fails.append(f"{name} {t}: missing {[m[:40] for m in missing]}")
    return list(INVENTORY), fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("check", choices=("site", "redirects", "plotnua", "dns"))
    ap.add_argument("--base", default="https://plotart.ie")
    ap.add_argument("--indexing", choices=("noindex", "index", "any"), default="any")
    a = ap.parse_args()
    if a.check == "site":
        items, fails = site(a.root, a.base, a.indexing)
    elif a.check == "redirects":
        items, fails = redirects(a.root)
    elif a.check == "plotnua":
        items, fails = plotnua()
    else:
        items, fails = dns()
    for f in fails[:200]:
        print("FAIL ", f)
    print(f"{a.check}: {len(items)} checked, {len(fails)} failed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
