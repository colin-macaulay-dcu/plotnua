#!/usr/bin/env python3
"""PlotNua · supplier-independence disclosure guard (founder decision, 6 Nov 2026,
Stage 2 item 10: "Preserve the existing supplier-independence disclosure, and add a
validation guard against future contradictory commercial arrangements").

Two pages say PlotNua has no commercial arrangement with the suppliers they describe:

  garden-room-prices-ireland.html      "PlotNua has no commercial arrangement with any of them"
      them = every supplier in the page's price evidence (opaque supplierKey rows of
      atlas-tools/garden-room-price-page-evidence.json, all segments)
  discovery-living-in-the-garden.html  "PlotNua has no commercial arrangement with any maker listed"
      listed = every maker in the page's Maker Explorer config

The guard refuses when a disclosure is missing, or when any organisation it covers is in
atlas-tools/commercial-arrangements-register.json (ACTIVE arrangements, opaque keys).
At that point the founder must decide: change the disclosure, or the listing.

  python3 atlas-tools/check-commercial-disclosure.py           check
  python3 atlas-tools/check-commercial-disclosure.py --prove   mutation proof
"""
import hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTER = ROOT / "atlas-tools" / "commercial-arrangements-register.json"
EXTRACT = ROOT / "atlas-tools" / "garden-room-price-page-evidence.json"
PRICES = ROOT / "garden-room-prices-ireland.html"
LITG = ROOT / "discovery-living-in-the-garden.html"
PRICES_TEXT = "PlotNua has no commercial arrangement with any of them"
LITG_TEXT = "commercial arrangement with any maker listed"


def key(name):
    return hashlib.sha256(name.encode()).hexdigest()[:12]


def flat(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def problems(register, extract, prices_html, litg_html):
    out = []
    active = {a["key"] for a in register.get("active", [])}
    if not all(re.fullmatch(r"[0-9a-f]{12}", k) for k in active):
        out.append("register: every active entry must be a 12-hex key")
    if PRICES_TEXT not in flat(prices_html):
        out.append("price guide: the supplier-independence disclosure is missing")
    hit = sorted({r["supplierKey"] for r in extract["rows"]} & active)
    if hit:
        out.append("price guide: %d supplier(s) in the price evidence hold an ACTIVE commercial "
                   "arrangement (%s), contradicting '%s'" % (len(hit), ", ".join(hit), PRICES_TEXT))
    if LITG_TEXT not in flat(litg_html):
        out.append("Living in the Garden: the maker-independence disclosure is missing")
    m = re.search(r'id="mx-data">(.*?)</script>', litg_html, re.S)
    if not m:
        out.append("Living in the Garden: Maker Explorer config not found")
    else:
        makers = {x["m"] for tab in json.loads(m.group(1))["tabs"] for x in tab.get("makers", [])}
        hit = sorted(n for n in makers if key(n) in active)
        if hit:
            out.append("Living in the Garden: listed maker(s) hold an ACTIVE commercial arrangement "
                       "(%s), contradicting '...%s'" % (", ".join(key(n) for n in hit), LITG_TEXT))
    return out


def load():
    return (json.loads(REGISTER.read_text(encoding="utf-8")), json.loads(EXTRACT.read_text(encoding="utf-8")),
            PRICES.read_text(encoding="utf-8"), LITG.read_text(encoding="utf-8"))


def check():
    reg, ex, p, l = load()
    bad = problems(reg, ex, p, l)
    for b in bad:
        print("REFUSED: " + b)
    if not bad:
        print("COMMERCIAL DISCLOSURE · OK — %d active arrangement(s) on the register; none among the "
              "%d price-evidence suppliers or the Living in the Garden makers; both disclosures present"
              % (len(reg.get("active", [])), len({r["supplierKey"] for r in ex["rows"]})))
    return 1 if bad else 0


def prove():
    reg, ex, p, l = load()
    assert not problems(reg, ex, p, l), "the committed state must pass first"
    m = json.loads(re.search(r'id="mx-data">(.*?)</script>', l, re.S).group(1))
    a_maker = m["tabs"][0]["makers"][0]["m"]
    cases = {
        "a price-evidence supplier becomes active": (
            dict(reg, active=reg["active"] + [{"key": ex["rows"][0]["supplierKey"]}]), ex, p, l),
        "a listed maker becomes active": (dict(reg, active=reg["active"] + [{"key": key(a_maker)}]), ex, p, l),
        "price-guide disclosure removed": (reg, ex, p.replace("no commercial arrangement", "a commercial arrangement"), l),
        "Living in the Garden disclosure removed": (reg, ex, p, l.replace(LITG_TEXT, "arrangement")),
        "malformed register key": (dict(reg, active=[{"key": "TimberIN"}]), ex, p, l),
    }
    caught = 0
    for name, args in cases.items():
        ok = bool(problems(*args))
        caught += ok
        print("  %s %s" % ("CAUGHT" if ok else "MISSED", name))
    print("COMMERCIAL DISCLOSURE · PROOF %d/%d" % (caught, len(cases)))
    return 0 if caught == len(cases) else 1


if __name__ == "__main__":
    sys.exit(prove() if "--prove" in sys.argv else check())
