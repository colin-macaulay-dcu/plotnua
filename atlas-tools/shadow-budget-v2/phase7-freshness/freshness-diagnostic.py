#!/usr/bin/env python3
"""PHASE 7 — FRESHNESS DIAGNOSTIC. READ-ONLY. OBSERVES, DECIDES NOTHING.

Answers two questions about the genuine run-#38 573-product candidate:

  A  How old is the Last Price Check behind each governed price?
  B  Is each product's first-party URL still alive?

It writes NOTHING to Atlas, does not touch your-plot.html, the generator, CI,
or any generated production artefact, and writes its own output only inside
this directory. No freshness threshold is applied or proposed: age is reported,
never judged. Nothing is marked unsafe because it is old.

Atlas access reuses the established pattern -- atlas_common.fetch_all() with
AIRTABLE_TOKEN from the environment. No second credentials mechanism.

    export AIRTABLE_TOKEN=...            # same token the CI workflow uses
    python3 freshness-diagnostic.py                 # both diagnostics
    python3 freshness-diagnostic.py --no-network    # A only, no HTTP at all
    python3 freshness-diagnostic.py --urls-only     # B only, no Atlas read
"""
import argparse, collections, datetime, json, os, ssl, statistics, sys, time
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CANDIDATE = REPO / "atlas-tools/shadow-budget-v2/phase6d/postfix/garden-room-recommendation-universe-v1.json"
sys.path.insert(0, str(REPO / ".github/scripts"))

AS_OF = datetime.date(2026, 10, 6)
UA = "PlotNua-Atlas-Diagnostic/1.0 (+https://plotnua.ie; read-only link check)"
TIMEOUT = 15
RETRIES = 2
PAUSE = 0.4           # polite per-request pause; we are a guest on these sites

# ---------------------------------------------------------------- guards ----
def refuse(msg):
    print("REFUSING TO RUN: " + msg)
    sys.exit(2)

if not CANDIDATE.exists():
    refuse("the genuine #38 candidate is not at %s" % CANDIDATE)
if HERE.name != "phase7-freshness":
    refuse("this script must live in phase7-freshness/, not %s" % HERE.name)


def write_out(name, text_or_obj):
    """Every write goes here, and only here."""
    p = (HERE / name).resolve()
    if HERE.resolve() not in p.parents:
        refuse("attempted write outside phase7-freshness: %s" % p)
    if isinstance(text_or_obj, str):
        p.write_text(text_or_obj, encoding="utf-8")
    else:
        p.write_text(json.dumps(text_or_obj, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def org(p):
    o = p.get("organisation") or {}
    return (o.get("name") if isinstance(o, dict) else o) or "(unknown)"


def safe_eur(p):
    pe = p.get("priceEvidence") or {}
    return (p.get("priceSafeForMatching") is True
            and pe.get("currency") == "EUR"
            and isinstance(p.get("price"), (int, float)))


# ------------------------------------------------- DIAGNOSTIC A: age --------
def diagnostic_a(products):
    try:
        import atlas_common as AC
    except ImportError:
        refuse("cannot import atlas_common from .github/scripts — run from the repo")
    token = os.environ.get("AIRTABLE_TOKEN")
    if not token:
        refuse("AIRTABLE_TOKEN is not set. Export the same token the refresh "
               "workflow uses. This script only READS.")

    print("  reading Product Pricing (Last Price Check, Status) ...")
    rows = AC.fetch_all(token, AC.T_PRICING, ["Last Price Check", "Status"])
    by_id = {}
    for r in rows:
        f = r.get("fields", r)
        by_id[r["id"]] = {"lastPriceCheck": AC.cell(r, "Last Price Check"),
                          "status": AC.cell(r, "Status")}
    print("  %d pricing records read" % len(by_id))

    out = []
    for p in products:
        ids = p.get("priceRecordIds") or []
        dates = []
        for rid in ids:
            d = (by_id.get(rid) or {}).get("lastPriceCheck")
            if d:
                dates.append(str(d)[:10])
        newest = max(dates) if dates else None
        age = None
        if newest:
            try:
                age = (AS_OF - datetime.date.fromisoformat(newest)).days
            except ValueError:
                newest, age = None, None
        out.append({
            "id": p["id"], "supplier": org(p), "product": p.get("name"),
            "priceRecordIds": ids, "priceStatus": p.get("priceStatus"),
            "priceSafeForMatching": p.get("priceSafeForMatching"),
            "lastPriceCheck": newest, "ageDays": age, "missingDate": newest is None,
            "price": p.get("price"), "safeEur": safe_eur(p),
            "productUrl": p.get("productUrl"),
        })
    return out


def age_report(rows, lines):
    sub = [r for r in rows if r["priceStatus"] == "Verified" and r["priceSafeForMatching"] is True]
    lines.append("\n=== A · LAST PRICE CHECK — Verified AND priceSafeForMatching=true ===")
    lines.append("  total in subset                 %d" % len(sub))
    dated = [r for r in sub if r["ageDays"] is not None]
    missing = [r for r in sub if r["ageDays"] is None]
    lines.append("  missing Last Price Check        %d" % len(missing))
    if dated:
        ages = sorted(r["ageDays"] for r in dated)
        lines.append("  newest                          %s  (%d days)"
                     % (max(r["lastPriceCheck"] for r in dated), min(ages)))
        lines.append("  oldest                          %s  (%d days)"
                     % (min(r["lastPriceCheck"] for r in dated), max(ages)))
        lines.append("  median age                      %d days" % int(statistics.median(ages)))
        B = [("0-30", 0, 30), ("31-90", 31, 90), ("91-180", 91, 180),
             ("181-365", 181, 365), (">365", 366, 10**9)]
        lines.append("  age buckets:")
        for lbl, lo, hi in B:
            n = sum(1 for a in ages if lo <= a <= hi)
            lines.append("    %-10s %4d" % (lbl, n))
        lines.append("    %-10s %4d" % ("missing", len(missing)))
        for lbl, pred in ((">180 days", lambda r: r["ageDays"] and r["ageDays"] > 180),
                          (">365 days", lambda r: r["ageDays"] and r["ageDays"] > 365),
                          ("missing date", lambda r: r["ageDays"] is None)):
            grp = collections.Counter(r["supplier"] for r in sub if pred(r))
            if grp:
                lines.append("  supplier concentration, %s:" % lbl)
                for n, c in grp.most_common(10):
                    lines.append("    %4d  %s" % (c, n))
    lines.append("  NOTE: age is diagnostic only. No expiry threshold is applied or implied.")
    return sub


# ------------------------------------------- DIAGNOSTIC B: URL health -------
GENERIC_HINTS = ("/", "/home", "/index", "/products", "/shop", "/range",
                 "/garden-rooms", "/solutions", "/designs", "/pricing")


def classify(original, final, status, title, err):
    if err == "timeout":
        return "TIMEOUT"
    if err == "blocked":
        return "BLOCKED"
    if err == "malformed":
        return "MALFORMED"
    if err:
        return "UNCHECKABLE"
    if status in (404, 410):
        return "DEAD_404_410"
    if status and status >= 400:
        return "OTHER_HTTP"
    if status and 200 <= status < 300:
        op = urllib.parse.urlparse(original).path.rstrip("/")
        fp = urllib.parse.urlparse(final).path.rstrip("/")
        # A soft 404: 200 status on a page that is really an error page.
        if title and ("page not found" in title.lower() or "404" in title.lower()):
            return "DEAD_404_410"
        if fp == op:
            return "LIVE_PRODUCT"
        if fp in GENERIC_HINTS or fp == "" or len(fp.split("/")) < len(op.split("/")):
            return "REDIRECT_GENERIC"
        return "REDIRECT_LIVE_PRODUCT"
    return "UNCHECKABLE"


def check_url(u):
    if not u or not u.lower().startswith(("http://", "https://")):
        return {"status": None, "final": None, "title": None, "err": "malformed"}
    ctx = ssl.create_default_context()
    last = None
    for attempt in range(RETRIES + 1):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA,
                                                     "Accept": "text/html,*/*"})
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
                body = r.read(60000).decode("utf-8", "replace")
                t = ""
                if "<title" in body.lower():
                    s = body.lower().index("<title")
                    s = body.index(">", s) + 1
                    t = body[s:body.lower().index("</title>", s)].strip()[:120]
                return {"status": r.status, "final": r.url, "title": t, "err": None}
        except urllib.error.HTTPError as e:
            return {"status": e.code, "final": u, "title": None,
                    "err": "blocked" if e.code in (401, 403, 429) else None}
        except Exception as e:  # timeouts, DNS, TLS
            last = "timeout" if "timed out" in str(e).lower() else "uncheckable"
            time.sleep(0.8 * (attempt + 1))
    return {"status": None, "final": None, "title": None, "err": last or "uncheckable"}


def diagnostic_b(rows):
    todo = [r for r in rows if r.get("productUrl")]
    cache = {}
    print("  checking %d product URLs (%d distinct) ..."
          % (len(todo), len({r["productUrl"] for r in todo})))
    for i, r in enumerate(todo, 1):
        u = r["productUrl"]
        if u not in cache:
            cache[u] = check_url(u)
            time.sleep(PAUSE)
        c = cache[u]
        r["httpStatus"] = c["status"]
        r["finalUrl"] = c["final"]
        r["pageTitle"] = c["title"]
        r["urlOutcome"] = classify(u, c["final"] or u, c["status"], c["title"], c["err"])
        if i % 25 == 0:
            print("    %d/%d" % (i, len(todo)))
    for r in rows:
        if not r.get("productUrl"):
            r["urlOutcome"] = "NO_PRODUCT_URL"
    return rows


# ----------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-network", action="store_true", help="Diagnostic A only.")
    ap.add_argument("--urls-only", action="store_true", help="Diagnostic B only.")
    a = ap.parse_args()

    products = json.loads(CANDIDATE.read_text())["products"]
    print("candidate: %d products" % len(products))

    if a.urls_only:
        rows = [{"id": p["id"], "supplier": org(p), "product": p.get("name"),
                 "priceStatus": p.get("priceStatus"),
                 "priceSafeForMatching": p.get("priceSafeForMatching"),
                 "price": p.get("price"), "safeEur": safe_eur(p),
                 "productUrl": p.get("productUrl"),
                 "lastPriceCheck": None, "ageDays": None, "missingDate": True,
                 "priceRecordIds": p.get("priceRecordIds") or []} for p in products]
    else:
        rows = diagnostic_a(products)

    L = ["PHASE 7 FRESHNESS DIAGNOSTIC — read-only, observational",
         "candidate: run #38 / ba5b5a7, %d products   as of %s" % (len(products), AS_OF)]

    if not a.urls_only:
        sub = age_report(rows, L)

    if not a.no_network:
        rows = diagnostic_b(rows)
        L.append("\n=== B · FIRST-PARTY URL HEALTH ===")
        withurl = [r for r in rows if r.get("productUrl")]
        L.append("  products with a Product URL     %d of %d" % (len(withurl), len(rows)))
        L.append("  products with NO Product URL    %d" % (len(rows) - len(withurl)))
        L.append("  outcome counts (all products):")
        for k, c in collections.Counter(r["urlOutcome"] for r in rows).most_common():
            L.append("    %-24s %4d" % (k, c))
        se = [r for r in rows if r["safeEur"]]
        L.append("  outcome counts (safe EUR prices, n=%d):" % len(se))
        for k, c in collections.Counter(r["urlOutcome"] for r in se).most_common():
            L.append("    %-24s %4d" % (k, c))

        dead_safe = [r for r in rows if r["safeEur"] and r["urlOutcome"] == "DEAD_404_410"]
        L.append("\n=== HIGH-RISK · priceSafeForMatching=true AND DEAD_404_410 ===")
        L.append("  count %d" % len(dead_safe))
        for r in sorted(dead_safe, key=lambda x: -(x["price"] or 0)):
            L.append("    EUR%-9s %-24s %-34s age=%s"
                     % (format(int(r["price"]), ","), r["supplier"][:24],
                        str(r["product"])[:34], r["ageDays"]))
        if dead_safe:
            L.append("  supplier clustering:")
            for n, c in collections.Counter(r["supplier"] for r in dead_safe).most_common():
                L.append("    %4d  %s" % (c, n))

        nourl = [r for r in rows if r["safeEur"] and not r.get("productUrl")]
        L.append("\n=== URL-LESS SAFE PRICES (not failures — classified separately) ===")
        L.append("  count %d across %d suppliers" % (len(nourl), len({r["supplier"] for r in nourl})))
        for n, c in collections.Counter(r["supplier"] for r in nourl).most_common(12):
            L.append("    %4d  %s" % (c, n))
        da = [r["ageDays"] for r in nourl if r["ageDays"] is not None]
        L.append("  with a Last Price Check: %d   missing: %d"
                 % (len(da), len(nourl) - len(da)))
        if da:
            L.append("  age median %d days, range %d-%d"
                     % (int(statistics.median(da)), min(da), max(da)))

    if not a.urls_only:
        ranked = sorted([r for r in rows if r["safeEur"] and r["ageDays"] is not None],
                        key=lambda x: -x["ageDays"])[:25]
        L.append("\n=== OLDEST SAFE PRICES (age-ranked; old is NOT declared unsafe) ===")
        for r in ranked:
            L.append("    %5d days  EUR%-9s %-22s %s"
                     % (r["ageDays"], format(int(r["price"]), ","),
                        r["supplier"][:22], str(r["product"])[:34]))

    txt = "\n".join(L)
    print("\n" + txt)
    write_out("freshness-summary.txt", txt + "\n")
    write_out("freshness-results.json",
              {"schema": "plotnua.phase7.freshness-diagnostic",
               "asOf": str(AS_OF), "candidate": "run-38/ba5b5a7",
               "productCount": len(products), "rows": rows})
    print("\nwritten: %s/freshness-summary.txt and freshness-results.json" % HERE.name)
    print("NOTHING was written to Atlas. No threshold was applied.")


if __name__ == "__main__":
    main()
