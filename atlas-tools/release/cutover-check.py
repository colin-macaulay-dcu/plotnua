#!/usr/bin/env python3
"""PlotNua · nameserver cutover checks (hosting migration A3, prepared 27 Nov 2026). READ-ONLY: it sends no email,
submits no form, takes no payment and uses no secret.

    python3 atlas-tools/release/cutover-check.py baseline --dist <plotnua build dir> --out baseline.json
    python3 atlas-tools/release/cutover-check.py compare  --dist <plotnua build dir> --baseline baseline.json [--out after.json]

`baseline` is run before the nameserver change, `compare` after it, and again later. A3 moves DNS only: every record stays
DNS only and keeps pointing at GitHub Pages, so apart from which nameservers answer, NOTHING a visitor or mail server
sees may change. `compare` therefore fails on any difference except the expected ones (the delegation, and TLS
certificate renewal dates), and on any absolute check that fails in either run.

Sections (each line is one check):
  D   DNS: every record of the zone, answered through two public resolvers, equals the reconciled inventory
      (Google Workspace MX/SPF/DKIM/DMARC, Resend DKIM + send + rsend, GitHub Pages A/www, verification TXT);
      which nameservers answer is recorded (informational: it is what A3 changes).
  W   PlotNua website: every file of the publication build answers on https://plotnua.ie with the same status and the
      same bytes as before (all existing URLs, pages and assets). A file that changed is accepted only when it is now
      byte-identical to the current build (--dist built from main at compare time), i.e. a release published meanwhile.
TLS observations are only meaningful from an unproxied network: run it from GitHub Actions (cutover-check.yml).
  R   TLS and redirects: valid certificates for plotnua.ie, www.plotnua.ie, plotart.ie, www.plotart.ie (issuer and
      names recorded; dates informational); http -> https and www -> apex redirects unchanged.
  S   SEO and indexing: robots.txt and sitemap.xml unchanged; no noindex header or meta on PlotNua pages; canonicals of
      key pages unchanged; plotart.ie keeps its approved indexing state (robots, X-Robots-Tag).
  P   PlotArt and Studio: plotart.ie key pages answer and are unchanged; Studio and its pipeline still sit behind
      Cloudflare Access; the existing site health checks (atlas-tools/release/site-health.py) pass.
  F   Forms, checkout and integrations: every Worker endpoint the pages call (enquiry relay, checkout, basket, Studio,
      registers, geocode, permission, ideas) answers without a server error and with the same status as before.
  M   Maps: the Google Maps key and the Cesium token on Your Plot are unchanged; the Maps JavaScript API serves the key
      for plotnua.ie; Cesium ion accepts the token.
Email DELIVERY is not sent from here: the founder's two test messages (hello@ in and out) and one Resend relay test
are listed in the A3 runbook (worker/CUTOVER-SEQUENCE.md) and checked by hand.
"""
import concurrent.futures as cf, hashlib, json, os, re, ssl, socket, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZONE = "plotnua.ie"
UA = {"User-Agent": "PlotNua-cutover-check/1.0 (+https://plotnua.ie)"}
EXPECT_DNS = {   # the reconciled inventory (Blacknight zone, 27 Nov 2026; identical in the pending Cloudflare zone)
    ("plotnua.ie", "A"): ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"],
    ("plotnua.ie", "MX"): ["1 smtp.google.com."],
    ("plotnua.ie", "TXT"): ["google-site-verification=F60i8FgB6hqKHjPYaNx8eIbbFziRC1Ro3omIcUm2LsE",
                            "pinterest-site-verification=43734d093eca5e544e28b40564868371",
                            "v=spf1 include:_spf.google.com ~all"],
    ("_dmarc.plotnua.ie", "TXT"): ["v=DMARC1; p=none; rua=mailto:hello@plotnua.ie; fo=1"],
    ("google._domainkey.plotnua.ie", "TXT"): ["v=DKIM1;k=rsa;p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyMZASa42wLEp1dfJimOzoguB3Z9NNWEU6SwOCocr/BoLeadq8+c+KUb5sBLXrmBZ2jus+0zXEpMJzlBaGdzGbmMxwMIEN1Ji9wcLZhsjQBwNikQ9XQaAyzHXGJxPI1zIXdxInoRhuCqyBHbV7PAcNZsdSNG8bupyf5+1awTtH9bfyWVnEiRfUKh+UuGNmf2hd9k2meAzChXdffuke8jZZ/DeHzAukxh/USENKN11mpkj924mNsBImha/obukzVn3jLyAumKXNXZM6jwQQhWij1OLBeQASG2/16W/cQerNUu6HLGjs698ULSW8wufoLVIA0pgrHIfEOLGeY+N/wz+YQIDAQAB"],
    ("resend._domainkey.plotnua.ie", "TXT"): ["p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCqy4niKGHDMp6yeXTa7PU/GcOyJUqO1XwfotJxjGOQnIxQyJ//yZ046jp1xWhAPTroWfvtV6MAFdz/FMSQHY9eHxKQClbmSCR6D1giGjG5sbgvzZiHOwVuMkxJKi47LWn+GoH2NpM41w+Wx0EsO59C77r9r3HvWYuzVK/btxysSQIDAQAB"],
    ("www.plotnua.ie", "CNAME"): ["colin-macaulay-dcu.github.io."],
    ("send.plotnua.ie", "CNAME"): ["send.forge.rmta.net."],
    ("rsend.plotnua.ie", "CNAME"): ["rsend-euw1.forge.rmta.net."],
}
RESOLVERS = {"google": "https://dns.google/resolve", "cloudflare": "https://cloudflare-dns.com/dns-query"}
TYPE_NO = {"A": 1, "NS": 2, "CNAME": 5, "MX": 15, "TXT": 16}
WORKERS = ["https://plotart-studio.colin-a41.workers.dev/", "https://plotart-enquiry.colin-a41.workers.dev/v1",
           "https://plotart-checkout.colin-a41.workers.dev/", "https://plotart-checkout.colin-a41.workers.dev/basket",
           "https://plotnua-art-space-register.colin-a41.workers.dev/v1", "https://plotnua-geocode.colin-a41.workers.dev/geocode",
           "https://plotnua-garden-register.colin-a41.workers.dev/v1", "https://plotnua-permission.colin-a41.workers.dev/v1",
           "https://plotnua-ideas.colin-a41.workers.dev/v1/ideas", "https://plotnua-garden-lead.colin-a41.workers.dev/v1",
           "https://plotnua-garden-board.colin-a41.workers.dev/v1"]
PLOTART = ["", "gallery/", "artworks/", "art-for-hire/", "mobile-gallery/", "services.html", "robots.txt", "sitemap.xml"]
CANONICAL_PAGES = ["", "discoveries.html", "garden-room-prices-ireland.html", "discovery-living-in-the-garden.html",
                   "your-plot.html", "plotart/", "privacy.html"]

out, fails = {}, []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def fetch(url, follow=True, headers=None, method="GET"):
    req = urllib.request.Request(url, method=method, headers={**UA, **(headers or {})})
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    for attempt in range(3):
        try:
            with opener.open(req, timeout=30) as r:
                return r.status, r.read(), {k.lower(): v for k, v in r.headers.items()}
        except urllib.error.HTTPError as e:
            return e.code, e.read(), {k.lower(): v for k, v in e.headers.items()}
        except Exception:                                   # noqa: BLE001 - retry, then report as 0
            time.sleep(3 * (attempt + 1))
    return 0, b"", {}


def rec(key, value, hard=None):
    """Record one observation. hard=False marks an absolute failure in this run."""
    out[key] = value
    if hard is False:
        fails.append(key)
        print("  FAIL ", key, "·", str(value)[:160])


def doh(resolver, name, typ):
    url = RESOLVERS[resolver] + "?" + urllib.parse.urlencode({"name": name, "type": typ})
    s, body, _ = fetch(url, headers={"accept": "application/dns-json"})
    if s != 200:
        return None
    d = json.loads(body)
    vals = [a["data"] for a in d.get("Answer", []) if a.get("type") == TYPE_NO[typ] and a["name"].rstrip(".") == name]
    norm = sorted(re.sub(r'"\s*"', "", v).strip('"') if typ == "TXT" else (v if v.endswith(".") or typ != "CNAME" else v + ".") for v in vals)
    return norm


def section_dns():
    for (name, typ), want in EXPECT_DNS.items():
        for r in RESOLVERS:
            got = doh(r, name, typ)
            if typ == "MX" and got:
                got = sorted(g if g.endswith(".") else g + "." for g in got)
            ok = got == sorted(want)
            rec(f"D {name} {typ} via {r}", got, ok if not ok else None)
    for r in RESOLVERS:
        out[f"D-info nameservers via {r}"] = doh(r, ZONE, "NS")


def build_paths(dist):
    skip = {".build-report.json", ".assetsignore", "_headers"}
    paths = []
    for p in sorted(Path(dist).rglob("*")):
        if p.is_file():
            rel = p.relative_to(dist).as_posix()
            if rel not in skip:
                paths.append(rel)
    return paths


def section_website(dist):
    paths = build_paths(dist)
    def one(rel):
        url = "https://plotnua.ie/" + ("" if rel == "index.html" else urllib.parse.quote(rel))
        s, body, h = fetch(url)
        return rel, s, hashlib.sha256(body).hexdigest()
    bad = 0
    with cf.ThreadPoolExecutor(16) as ex:
        for rel, s, sha in ex.map(one, paths):
            out[f"W {rel}"] = [s, sha]
            if s != 200:
                bad += 1
                if bad <= 20:
                    print("  FAIL  W", rel, "HTTP", s)
    rec("W every published file answers 200", f"{len(paths) - bad}/{len(paths)}", bad == 0 if bad else None)


def cert(host):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=15) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                c = tls.getpeercert()
        issuer = dict(x[0] for x in c["issuer"]).get("organizationName", "")
        names = sorted(v for k, v in c.get("subjectAltName", []) if k == "DNS")
        return {"issuer": issuer, "names": names, "not_after": c["notAfter"]}
    except Exception as e:                                  # noqa: BLE001
        return {"error": type(e).__name__}


def section_tls():
    for host in ("plotnua.ie", "www.plotnua.ie", "plotart.ie", "www.plotart.ie"):
        c = cert(host)
        rec(f"R tls {host} issuer and names", {k: v for k, v in c.items() if k != "not_after"}, False if "error" in c else None)
        out[f"R-info tls {host} expires"] = c.get("not_after")
    for url in ("http://plotnua.ie/", "https://www.plotnua.ie/", "http://www.plotnua.ie/", "http://plotart.ie/",
                "https://www.plotart.ie/", "https://plotnua.ie/discoveries"):
        s, _, h = fetch(url, follow=False)
        rec(f"R redirect {url}", [s, h.get("location", "")])


def section_seo():
    for f in ("robots.txt", "sitemap.xml"):
        s, body, _ = fetch("https://plotnua.ie/" + f)
        rec(f"S plotnua.ie/{f}", [s, hashlib.sha256(body).hexdigest()], s == 200 if s != 200 else None)
    for p in CANONICAL_PAGES:
        s, body, h = fetch("https://plotnua.ie/" + p)
        txt = body.decode("utf-8", "replace")
        canon = re.findall(r'<link rel="canonical" href="([^"]+)"', txt)
        robots_meta = re.findall(r'<meta name="robots" content="([^"]+)"', txt)
        noindex = "noindex" in h.get("x-robots-tag", "") or any("noindex" in m for m in robots_meta)
        rec(f"S plotnua.ie/{p} canonical and robots", {"status": s, "canonical": canon, "robots": robots_meta,
                                                        "x-robots-tag": h.get("x-robots-tag", "")},
            False if (s != 200 or (noindex and p not in ("your-plot.html",))) else None)
    s, body, h = fetch("https://plotart.ie/robots.txt")
    rec("S plotart.ie robots.txt and X-Robots-Tag", [s, hashlib.sha256(body).hexdigest(), h.get("x-robots-tag", "")])


def section_plotart():
    for p in PLOTART:
        s, body, h = fetch("https://plotart.ie/" + p)
        rec(f"P plotart.ie/{p}", [s, hashlib.sha256(body).hexdigest()], s == 200 if s != 200 else None)
    r = subprocess.run([sys.executable, str(ROOT / "atlas-tools/release/site-health.py")], cwd=ROOT, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or [""])[-1]
    rec("P site health (H1-H6: pages, Studio behind Access, public Workers)", last, r.returncode == 0 if r.returncode else None)


def section_forms():
    for u in WORKERS:
        s, _, h = fetch(u, follow=False)
        rec(f"F {u}", s, (0 < s < 500) if not (0 < s < 500) else None)


def section_maps():
    s, body, _ = fetch("https://plotnua.ie/your-plot.html")
    txt = body.decode("utf-8", "replace")
    key = (re.findall(r'PLOTNUA_GOOGLE_MAPS_KEY\s*=\s*"([^"]+)"', txt) or [""])[0]
    tok = (re.findall(r"PLOTNUA_CESIUM_TOKEN\s*=\s*['\"]([^'\"]+)['\"]", txt) or [""])[0]
    rec("M Your Plot map credentials (fingerprints)", [hashlib.sha256(key.encode()).hexdigest()[:16],
                                                       hashlib.sha256(tok.encode()).hexdigest()[:16]],
        bool(key and tok) if not (key and tok) else None)
    s, body, _ = fetch("https://maps.googleapis.com/maps/api/js?key=" + key, headers={"Referer": "https://plotnua.ie/your-plot.html"})
    rec("M Google Maps JavaScript API serves the key for plotnua.ie", s, s == 200 if s != 200 else None)
    s, body, _ = fetch("https://api.cesium.com/v1/assets/2275207/endpoint?access_token=" + tok,   # Google Photorealistic 3D Tiles
                       headers={"Origin": "https://plotnua.ie", "Referer": "https://plotnua.ie/your-plot.html"})
    rec("M Cesium ion accepts the token", s, s == 200 if s != 200 else None)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("baseline", "compare"):
        sys.exit(__doc__)
    arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    dist = arg("--dist")
    if not dist or not Path(dist).is_dir():
        sys.exit("--dist <plotnua build dir> is required (python3 atlas-tools/plotnua_site_build.py . <dir> --mode live)")
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for name, fn in (("DNS", section_dns), ("TLS and redirects", section_tls), ("SEO", section_seo),
                     ("PlotArt and Studio", section_plotart), ("Forms, checkout and integrations", section_forms),
                     ("Maps", section_maps)):
        print("—", name)
        fn()
    print("— PlotNua website (every published file)")
    section_website(dist)
    out["_meta"] = {"mode": sys.argv[1], "started": started, "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    target = arg("--out")
    if target:
        Path(target).write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    diffs, released = [], []
    if sys.argv[1] == "compare":
        base = json.loads(Path(arg("--baseline")).read_text(encoding="utf-8"))
        for k in sorted(set(base) | set(out)):
            if k.startswith(("_", "D-info", "R-info")):
                continue
            if base.get(k) != out.get(k):
                if k.startswith("W ") and out.get(k) and out[k][0] == 200:
                    # a website file that changed is accepted only if it is now exactly the file of the current build
                    # (a legitimate release published during the window), never anything else
                    f = Path(dist) / k[2:]
                    if f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest() == out[k][1]:
                        released.append(k)
                        continue
                diffs.append(k)
                if len(diffs) <= 40:
                    print("  CHANGED", k, "·", str(base.get(k))[:90], "->", str(out.get(k))[:90])
        if released:
            print(f"  note: {len(released)} website file(s) changed to exactly the current build (a release in the window)")
        print("— delegation (expected to change at A3):",
              base.get("D-info nameservers via google"), "->", out.get("D-info nameservers via google"))
    n = len([k for k in out if not k.startswith("_")])
    print(f"CUTOVER CHECK · {sys.argv[1]} · {n} observations · {len(fails)} failed" +
          (f" · {len(diffs)} changed since the baseline" if sys.argv[1] == "compare" else ""))
    sys.exit(1 if fails or diffs else 0)


if __name__ == "__main__":
    main()
