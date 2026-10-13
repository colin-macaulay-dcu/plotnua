#!/usr/bin/env python3
"""Build power-station-provider-universe-v1.json — the ONLY data the House as
Power Station Provider Explorer may show.

Founder instruction: 13 October 2026 ("Resume the electricity-export Provider
Explorer"; verified, current official evidence; no rankings, no supplier
recommendations, no unsupported rates or earnings claims, no implied
partnerships; the Property Check stays the primary homeowner journey).

INPUTS (all in atlas-tools/, all reviewed)
  power-station-provider-atlas-snapshot.json   read-back of the Atlas records
  power-station-provider-sources-v1.json       official pages re-read 13 Oct 2026,
                                               verbatim quotes
  power-station-provider-text-v1.json          public wording
and, for membership only, the published pilot supplier-export-evidence.json.

The page never reads Atlas, and this builder never calls Airtable or the web.
A supplier is eligible only when ALL hold:
  U1  it has an Atlas Organisation record in the snapshot, under the same name
  U2  it is one of the DISC-026 pilot suppliers in supplier-export-evidence.json
      under the same Atlas organisation code
  U3  it carries no Products and no Partner records, and no partner status
  U4  every public sentence cites at least one source belonging to THAT
      supplier, and names the verbatim quote(s) on that source it rests on
  U5  it appears in the public wording file, in exactly one tab

WORDING GUARDS over everything a visitor can read
  W1  no endorsement or ranking vocabulary
  W2  no link, web address or email
  W3  NO MONEY: no currency, no cent, no per-kWh figure, no earnings or savings
      wording; and no numerals at all apart from "NC6" (rates and estimates
      appear on every supplier page and must never be carried across)
  W4  no partner label: partner:false everywhere, partnersCount 0

EVIDENCE REFRESH (the rule already approved for the Borrowed Garden Explorer)
  * 90-day review threshold from each source's lastVerified date.
  * A time-sensitive sentence is WITHHELD once its evidence is older than 90
    days. Every sentence here is time-sensitive: supplier terms change.
  * If a supplier would lose its "What it offers" text, the build STOPS for
    review rather than shipping with a supplier silently missing.

Usage:
  python3 atlas-tools/build-power-station-provider-universe.py            # write
  python3 atlas-tools/build-power-station-provider-universe.py --check    # verify only
  ... --as-of 2027-01-20     # evaluate staleness as of another date (dry checks)
"""
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "atlas-tools" / "power-station-provider-atlas-snapshot.json"
SRCS = ROOT / "atlas-tools" / "power-station-provider-sources-v1.json"
TEXT = ROOT / "atlas-tools" / "power-station-provider-text-v1.json"
PILOT = ROOT / "supplier-export-evidence.json"
OUT = ROOT / "power-station-provider-universe-v1.json"

REVIEW_DAYS = 90
GRACE_DAYS = 180
FIELDS = ("offers", "where", "how")
BANNED = re.compile(r"\b(recommended|recommend|best|cheapest|top-rated|trusted|featured|"
                    r"verified partner|official partner|endorsed|leading|preferred|"
                    r"better|highest|lowest|great value)\b", re.I)
MONEY = re.compile(r"€|£|\$|\bcent\b|c/kWh|per kWh|\bkWh\b|\beuro|\bearn|\bincome|\bsaving|\bsave\b|"
                   r"\bprofit|\bworth\b|\breturn\b", re.I)
DIGIT = re.compile(r"\d")


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


def fmt_date(iso):
    d = dt.date.fromisoformat(iso)
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def main(argv):
    check = "--check" in argv
    as_of = dt.date.today()
    if "--as-of" in argv:
        as_of = dt.date.fromisoformat(argv[argv.index("--as-of") + 1])

    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    src = json.loads(SRCS.read_text(encoding="utf-8"))
    text = json.loads(TEXT.read_text(encoding="utf-8"))
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    if snap["discovery"]["code"] != "DISC-026":
        die("U1 snapshot Discovery is not DISC-026")
    orgs = {o["code"]: o for o in snap["organisations"]}
    srcs = {s["code"]: s for s in src["sources"]}
    pilot_codes = {v["atlas_organisation_code"]: v["supplier_name"] for v in pilot["suppliers"].values()}
    labels = text["sourceLabels"]

    approved = [c for t in text["tabs"] for c in t["orgs"]]
    if sorted(approved) != sorted(text["organisations"]):
        die("U5 tab membership and approved organisations disagree")
    if len(set(approved)) != len(approved):
        die("U5 an organisation appears in more than one tab")

    review, tabs_out = [], []
    for tab in text["tabs"]:
        rows = []
        for code in tab["orgs"]:
            o = orgs.get(code)
            if not o:
                die("U1 %s has no Atlas Organisation record in the snapshot" % code)
            if pilot_codes.get(code) != o["name"]:
                die("U2 %s is not a DISC-026 pilot supplier under the same name" % code)
            if o.get("products") or o.get("partners") or o.get("partnerStatus"):
                die("U3 %s carries Products, Partner records or a partner status" % code)
            spec = text["organisations"][code]
            row = {"code": code, "name": o["name"], "kind": spec["kind"], "subtitle": spec["subtitle"],
                   "partner": False, "relationship": spec["relationship"]}
            used = {}
            for field in FIELDS:
                kept = []
                for sen in spec[field]:
                    if not sen["s"] or not sen.get("q"):
                        die("U4 %s %s: a sentence cites no source or no quote" % (code, field))
                    ages = []
                    for sc in sen["s"]:
                        s = srcs.get(sc)
                        if not s:
                            die("U4 %s cites %s, which is not in the sources file" % (code, sc))
                        if s["org"] != code:
                            die("U4 %s cites %s, which belongs to %s" % (code, sc, s["org"]))
                        if sc not in labels:
                            die("U4 %s has no public label" % sc)
                        ages.append((as_of - dt.date.fromisoformat(s["lastVerified"])).days)
                    for qk in sen["q"]:
                        if not any(qk in srcs[sc]["quotes"] and srcs[sc]["quotes"][qk].strip() for sc in sen["s"]):
                            die("U4 %s cites quote %r, which none of its sources holds" % (code, qk))
                    oldest = max(ages)
                    if oldest <= REVIEW_DAYS:
                        kept.append(sen["t"])
                    elif sen["ts"]:
                        review.append({"org": code, "field": field, "action": "WITHHELD",
                                       "why": "time-sensitive; evidence %d days old (> %d)" % (oldest, REVIEW_DAYS),
                                       "sentence": sen["t"]})
                        continue
                    elif oldest <= GRACE_DAYS:
                        kept.append(sen["t"])
                        review.append({"org": code, "field": field, "action": "FLAGGED",
                                       "why": "evidence %d days old (> %d)" % (oldest, REVIEW_DAYS),
                                       "sentence": sen["t"]})
                    else:
                        review.append({"org": code, "field": field, "action": "WITHHELD",
                                       "why": "evidence %d days old (> %d grace)" % (oldest, GRACE_DAYS),
                                       "sentence": sen["t"]})
                        continue
                    for sc in sen["s"]:
                        used[sc] = srcs[sc]["lastVerified"]
                row[field] = " ".join(kept)
            if not row["offers"]:
                for r in review:
                    print("  REVIEW  %(org)s %(field)s %(action)s - %(why)s" % r)
                die("STALE REVIEW REQUIRED: %s would lose its 'What it offers' text. Re-read the supplier's "
                    "page; the Explorer is never shipped with a supplier silently missing" % code)
            by_date = {}
            for sc, d in used.items():
                by_date.setdefault(d, []).append(labels[sc])
            row["evidence"] = "; ".join(" and ".join(sorted(set(by_date[d]))) + ", checked " + fmt_date(d)
                                        for d in sorted(by_date, reverse=True))
            row["evidenceOldest"] = min(used.values())
            rows.append(row)
        if not rows:
            die("STALE REVIEW REQUIRED: tab '%s' would be empty" % tab["key"])
        rows.sort(key=lambda r: r["name"].lower())
        tabs_out.append({"key": tab["key"], "label": tab["label"], "note": tab["note"], "orgs": rows})

    for tab in tabs_out:
        for blob_src in [tab["label"], tab["note"]] + [
                " ".join([r["name"], r["kind"], r["subtitle"], r["offers"], r["where"], r["how"], r["relationship"]])
                for r in tab["orgs"]]:
            if BANNED.search(blob_src):
                die("W1 endorsement or ranking wording: %r" % BANNED.search(blob_src).group(0))
            if re.search(r"https?://|www\.|@|\.ie\b|\.com\b", blob_src):
                die("W2 a link, web address or email appears in: %r" % blob_src[:80])
            if MONEY.search(blob_src):
                die("W3 money, rate or earnings wording: %r" % MONEY.search(blob_src).group(0))
            if DIGIT.search(blob_src.replace("NC6", "")):
                die("W3 a numeral appears in visitor text: %r" % blob_src[:80])
        for r in tab["orgs"]:
            if r["partner"] is not False:
                die("W4 %s is not partner:false" % r["code"])

    universe = {
        "_about": "Published data for the House as Power Station Provider Explorer. Generated by atlas-tools/build-power-station-provider-universe.py from the Atlas read-back, the official supplier pages re-read on 13 October 2026, and the public wording. Not a ranking, not a recommendation and not a complete list of suppliers. No rates or earnings are carried. Do not hand-edit.",
        "universe": "power-station-provider-universe-v1",
        "discovery": {"code": "DISC-026", "page": "discovery-house-as-power-station.html"},
        "statusLabel": "Independently researched by PlotNua",
        "partnersCount": 0,
        "ratesShown": False,
        "reviewThresholdDays": REVIEW_DAYS,
        "tabs": tabs_out,
        "review": review,
    }
    body = json.dumps(universe, ensure_ascii=False, indent=1) + "\n"
    # W5 disclosure firewall patterns (as .github/scripts/test_public_disclosure_firewall.py)
    if re.search(r"\b(?:rec|tbl|fld|app|sel)[A-Za-z0-9]{14}\b", body):
        die("W5 an Airtable identifier would be published")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]{2,}", body):
        die("W5 an email address would be published")
    if re.search(r"api[_-]?key|secret|password|bearer\s+[A-Za-z0-9]|-----BEGIN", body, re.I):
        die("W5 secret-like content would be published")
    for f in (SNAP, SRCS, TEXT):
        if re.search(r"\b(?:rec|tbl|fld|app|sel)[A-Za-z0-9]{14}\b|[\w.+-]+@[\w-]+\.[\w.]{2,}", f.read_text(encoding="utf-8")):
            die("W5 %s (publicly served) holds an Airtable identifier or email" % f.name)

    print("  as of %s · threshold %d days" % (as_of, REVIEW_DAYS))
    for t in tabs_out:
        print("  tab %-9s %d organisations: %s" % (t["key"], len(t["orgs"]), ", ".join(r["name"] for r in t["orgs"])))
    for r in review:
        print("  REVIEW  %(org)s %(field)s %(action)s - %(why)s" % r)
    nxt = min(dt.date.fromisoformat(s["lastVerified"]) for s in src["sources"])
    print("  next evidence review due: %s (oldest source + %d days)" % (nxt + dt.timedelta(days=REVIEW_DAYS), REVIEW_DAYS))
    if check:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != body:
            print("CHECK FAILED: %s is out of date with its inputs" % OUT.name)
            sys.exit(1)
        print("CHECK OK — U1-U5, W1-W5 pass; universe up to date")
        return
    OUT.write_text(body, encoding="utf-8")
    print("WROTE %s — U1-U5, W1-W5 pass" % OUT.name)


if __name__ == "__main__":
    main(sys.argv[1:])
