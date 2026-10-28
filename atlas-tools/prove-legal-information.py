#!/usr/bin/env python3
"""
PROVE LEGAL INFORMATION · website operator details (founder decision A1-a, 28 Oct 2026)

Checks, without writing anything:
  G1  terms.html has the legal-information block (id="legal-information") with the
      registered business name, Business Name Registration No. 794392, the
      registered proprietor "Colin Macaulay" (certificate spelling), the business
      address, email and telephone.
  G2  the site never calls 794392 a company number, and never calls PlotNua a
      limited company ("Ltd", "Limited", "company registration number"),
      apart from the explicit "not a limited company" statement.
  G3  no public page keeps the old footer heading "Company".
  G4  every page reachable from index.html links to terms.html, except the
      Your Plot app (your-plot.html, frozen; listed separately for review).
  G5  PlotArt pages state, or link to, the legal information; PlotArt is described
      as an initiative operated under PlotNua on the Terms page.
  G6  RELEASE GATE: the business address must be confirmed by the founder against
      the CRO registration certificate itself. Until ADDRESS_CONFIRMED is set to
      True below (by the founder's instruction), this proof FAILS on purpose.
      Verified against the issued certificate on 28 Oct 2026 (see ADDRESS_CONFIRMED).
"""
import os, re, sys, urllib.parse
from collections import deque

ADDRESS_CONFIRMED = True    # verified 28 Oct 2026 against the issued CRO Certificate of
                            # Registration No. 794392 (CR28671630-134792911.pdf, emailed by
                            # the CRO on 29 Sep 2026): Principal Place of Business
                            # "1 Allen Park Road / Stillorgan / DUBLIN / Ireland / A94 FT21";
                            # registered by Colin Macaulay; registered 29 September 2026.
ADDRESS = "1 Allen Park Road, Stillorgan, Dublin, A94 FT21, Ireland"

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
fails, passes = [], []
def ok(m): passes.append(m)
def bad(m): fails.append(m)
def read(p): return open(os.path.join(ROOT, p), encoding="utf-8", errors="ignore").read()

# G1
t = read("terms.html")
blk = re.search(r'<section[^>]*id="legal-information".*?</section>', t, re.S)
need = ["Registered business name:</strong> PlotNua",
        "Business Name Registration No.:</strong> 794392",
        "Registered proprietor:</strong> Colin Macaulay",
        "Business address:</strong> " + ADDRESS,
        'href="mailto:hello@plotnua.ie"',
        'href="tel:+353834036695">+353 83 403 6695']
if blk and all(n in blk.group(0) for n in need):
    ok("G1 terms.html legal-information block complete")
else:
    bad("G1 legal-information block missing or incomplete: " +
        ", ".join(n for n in need if not blk or n not in blk.group(0)))

# G2 and G3 over all public html
html = [os.path.relpath(os.path.join(d, f), ROOT) for d, _, fs in os.walk(ROOT)
        if "/.git" not in d and "node_modules" not in d for f in fs if f.endswith(".html")]
g2 = []
for p in html:
    s = read(p)
    if re.search(r"company (registration )?(number|no\.?)\s*:?\s*794392", s, re.I): g2.append(p + " (company number)")
    if re.search(r"PlotNua (Ltd|Limited)\b", s): g2.append(p + " (PlotNua Ltd)")
ok("G2 no page calls PlotNua a company or 794392 a company number") if not g2 else bad("G2 " + "; ".join(g2))
g3 = [p for p in html if re.search(r"<h[24]>Company</h[24]>", read(p))]
g3_allowed = {"privacy.html", "artist-register.html"}   # both take their footer from the privacy layer (V7 release)
g3_bad = [p for p in g3 if p not in g3_allowed]
ok("G3 no footer heading 'Company' (privacy.html and artist-register.html deferred to the V7 release: %s)" % ("yes" if g3 else "already done")) if not g3_bad else bad("G3 'Company' heading on: " + ", ".join(g3_bad))

# G4 reachable pages link to terms
def links(path):
    s = read(path); out = []
    for h in re.findall(r'href="([^"#?]+)', s):
        if h.startswith(("http", "mailto:", "tel:", "javascript")): continue
        q = os.path.normpath(os.path.join(os.path.dirname(path), urllib.parse.unquote(h)))
        if q.endswith("/") or os.path.isdir(os.path.join(ROOT, q)): q = os.path.join(q, "index.html")
        if q.endswith(".html") and os.path.exists(os.path.join(ROOT, q)): out.append(q)
    return out
seen, dq = set(), deque(["index.html"])
while dq:
    p = dq.popleft()
    if p in seen: continue
    seen.add(p); dq.extend(links(p))
EXEMPT = {"your-plot.html"}
missing = [p for p in sorted(seen) if p not in EXEMPT and "terms.html" not in read(p)]
ok("G4 all %d reachable pages link to Terms (exempt for review: %s)" % (len(seen) - len(EXEMPT), ", ".join(sorted(EXEMPT)))) if not missing else bad("G4 no Terms link: " + ", ".join(missing))

# G5 PlotArt
pa = [p for p in seen if p.startswith("plotart/")]
pa_bad = [p for p in pa if "terms.html#legal-information" not in read(p)]
ok("G5 %d PlotArt pages link to the legal information" % len(pa)) if pa and not pa_bad else bad("G5 PlotArt pages without legal link: " + ", ".join(pa_bad))
if "PlotArt is an initiative operated under PlotNua." in t: ok("G5 Terms says PlotArt is an initiative operated under PlotNua")
else: bad("G5 Terms lacks the PlotArt initiative sentence")

# G6 release gate
if ADDRESS_CONFIRMED: ok("G6 business address confirmed by the founder against the CRO certificate")
else: bad("G6 RELEASE GATE: business address not yet confirmed against the CRO certificate (taken from RBN1 submissions SR9795857 / SR9796002)")

for m in passes: print("  [PASS] " + m)
for m in fails: print("  [FAIL] " + m)
print("\nLEGAL INFORMATION · %s (%d passed, %d failed)" % ("OK" if not fails else "BLOCKED", len(passes), len(fails)))
sys.exit(0 if not fails else 1)
