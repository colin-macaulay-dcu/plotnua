#!/usr/bin/env python3
"""Build borrowed-garden-provider-universe-v1.json — the ONLY data the Borrowed
Garden Provider Explorer may show.

Founder approval: 13 October 2026 (Provider Explorer evidence pack, approved
with conditions).

INPUTS (both in atlas-tools/, both reviewed)
  borrowed-garden-provider-atlas-snapshot.json   read-back of the Atlas records
  borrowed-garden-provider-text-v1.json          founder-approved public wording

The page never reads Atlas, and this builder never calls Airtable. An
organisation is eligible only when ALL hold:
  U1  it has an Atlas Organisation record in the snapshot
  U2  that record is linked to the DISC-025 Discovery record, and the
      Discovery links back to it
  U3  it carries no Products and no Partner records
  U4  every public sentence cites at least one Atlas Source belonging to THAT
      organisation, and none cites a background-only source
  U5  it appears in the founder-approved text file

PARTNER LABEL. Never shown in v1. Partner Status is a relationship state only;
"Active Partner" would additionally need a founder-approved public partner
label, and no such approval exists. Any Active Partner in the snapshot stops
the build (U6). Strategic Hold (Homegrown.ie) is an outreach stop: display is
permitted, contact is not, and nothing here contacts anyone.

EVIDENCE REFRESH (founder conditions, 13 Oct 2026)
  * 90-day review threshold, measured from each Source's Last Verified date.
  * A TIME-SENSITIVE sentence is WITHHELD once any of its sources is older
    than 90 days.
  * A non-time-sensitive sentence MAY REMAIN past 90 days only while its
    continued accuracy is supportable; this builder allows that up to 180 days,
    always FLAGGED for review, and withholds it beyond that.
  * Nothing is deleted from Atlas, and the Explorer is never removed silently:
    if an organisation would lose its "What it offers" text, or a tab would be
    left empty, the build STOPS with a review list instead of shipping.
  Every flag and every withheld sentence is printed and recorded in the
  universe's "review" list.

Usage:
  python3 atlas-tools/build-borrowed-garden-provider-universe.py            # write
  python3 atlas-tools/build-borrowed-garden-provider-universe.py --check    # verify only
  ... --as-of 2027-01-20     # evaluate staleness as of another date (dry checks)
"""
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "atlas-tools" / "borrowed-garden-provider-atlas-snapshot.json"
TEXT = ROOT / "atlas-tools" / "borrowed-garden-provider-text-v1.json"
OUT = ROOT / "borrowed-garden-provider-universe-v1.json"

REVIEW_DAYS = 90
GRACE_DAYS = 180
FIELDS = ("offers", "where", "how")
BANNED = re.compile(r"\b(recommended|recommend|best|top-rated|trusted|featured|"
                    r"verified partner|official partner|endorsed|Ireland's first|"
                    r"Ireland’s first)\b", re.I)
COUNCIL_SHARING = re.compile(r"garden[- ]shar|\bpair|\bmatch|introduc", re.I)
COUNCIL_ALLOWED = "This is not garden-sharing."


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
    text = json.loads(TEXT.read_text(encoding="utf-8"))
    disc = snap["discovery"]
    if disc["code"] != "DISC-025":
        die("U2 snapshot Discovery is not DISC-025")
    if disc.get("products") or disc.get("partners"):
        die("U3 the DISC-025 Discovery carries Products or Partners")
    orgs = {o["code"]: o for o in snap["organisations"]}
    srcs = {s["code"]: s for s in snap["sources"]}
    labels = text["sourceLabels"]

    review, tabs_out, partners = [], [], 0
    approved_codes = [c for t in text["tabs"] for c in t["orgs"]]
    if sorted(approved_codes) != sorted(text["organisations"]):
        die("U5 tab membership and approved organisations disagree")
    if len(set(approved_codes)) != len(approved_codes):
        die("U5 an organisation appears in more than one tab")

    for tab in text["tabs"]:
        rows = []
        for code in tab["orgs"]:
            o = orgs.get(code)
            if not o:
                die("U1 %s has no Atlas Organisation record in the snapshot" % code)
            if disc["record"] not in o["discoveries"] or o["record"] not in disc["linkedOrganisations"]:
                die("U2 %s is not linked both ways to DISC-025" % code)
            if o.get("products") or o.get("partners"):
                die("U3 %s carries Products or Partner records" % code)
            if o["partnerStatus"] == "Active Partner":
                die("U6 %s is an Active Partner; no partner label is approved for public display" % code)
            spec = text["organisations"][code]
            row = {"code": code, "name": o["name"], "kind": spec["kind"], "subtitle": spec["subtitle"],
                   "partner": False, "relationship": spec["relationship"]}
            used = {}
            for field in FIELDS:
                kept = []
                for sen in spec[field]:
                    if not sen["s"]:
                        die("U4 %s %s: a sentence cites no source" % (code, field))
                    ages = []
                    for sc in sen["s"]:
                        s = srcs.get(sc)
                        if not s:
                            die("U4 %s cites %s, which is not in the snapshot" % (code, sc))
                        if s["org"] != code:
                            die("U4 %s cites %s, which belongs to %s" % (code, sc, s["org"]))
                        if s.get("backgroundOnly"):
                            die("U4 %s cites background-only source %s" % (code, sc))
                        if sc not in labels:
                            die("U4 %s has no public label" % sc)
                        ages.append((as_of - dt.date.fromisoformat(s["lastVerified"])).days)
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
                                       "why": "evidence %d days old (> %d); kept while continued accuracy is supportable, up to %d days" % (oldest, REVIEW_DAYS, GRACE_DAYS),
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
                die("STALE REVIEW REQUIRED: %s would lose its 'What it offers' text. Refresh its evidence in Atlas; "
                    "the Explorer is never shipped with an organisation silently missing" % code)
            by_date = {}
            for sc, d in used.items():
                by_date.setdefault(d, []).append(labels[sc])
            parts = []
            for d in sorted(by_date, reverse=True):
                names = sorted(set(by_date[d]), key=lambda n: (n.lower()))
                parts.append(" and ".join(names) + ", checked " + fmt_date(d))
            row["evidence"] = "; ".join(parts)
            row["evidenceOldest"] = min(used.values())
            rows.append(row)
        if not rows:
            die("STALE REVIEW REQUIRED: tab '%s' would be empty" % tab["key"])
        rows.sort(key=lambda r: r["name"].lower())
        tabs_out.append({"key": tab["key"], "label": tab["label"], "note": tab["note"], "orgs": rows})

    # wording guards over everything a visitor can read
    for tab in tabs_out:
        for r in tab["orgs"]:
            blob = " ".join([r["name"], r["kind"], r["subtitle"], r["offers"], r["where"], r["how"], r["relationship"]])
            if BANNED.search(blob):
                die("W1 banned endorsement wording in %s: %r" % (r["code"], BANNED.search(blob).group(0)))
            if re.search(r"https?://|www\.|@", blob.replace("Homegrown.ie", "")):
                die("W2 a link, web address or email appears in %s" % r["code"])
            if tab["key"] == "other":
                if COUNCIL_ALLOWED not in r["offers"]:
                    die("W3 council %s does not say it is not garden-sharing" % r["code"])
                if COUNCIL_SHARING.search(blob.replace(COUNCIL_ALLOWED, "")):
                    die("W3 council %s uses garden-sharing / matching wording" % r["code"])

    universe = {
        "_about": "Published, founder-approved data for the Borrowed Garden Provider Explorer. Generated by atlas-tools/build-borrowed-garden-provider-universe.py from the Atlas read-back and the approved wording. Do not hand-edit.",
        "universe": "borrowed-garden-provider-universe-v1",
        "discovery": {"code": "DISC-025", "page": "discovery-the-borrowed-garden.html"},
        "statusLabel": "Independently researched by PlotNua",
        "partnersCount": partners,
        "reviewThresholdDays": REVIEW_DAYS,
        "tabs": tabs_out,
        "review": review,
    }
    body = json.dumps(universe, ensure_ascii=False, indent=1) + "\n"

    print("  as of %s · threshold %d days · grace %d days" % (as_of, REVIEW_DAYS, GRACE_DAYS))
    for t in tabs_out:
        print("  tab %-6s %d organisations: %s" % (t["key"], len(t["orgs"]), ", ".join(r["name"] for r in t["orgs"])))
    for r in review:
        print("  REVIEW  %(org)s %(field)s %(action)s - %(why)s" % r)
    nxt = min(dt.date.fromisoformat(s["lastVerified"]) for s in snap["sources"] if not s.get("backgroundOnly"))
    print("  next evidence review due: %s (oldest public source + %d days)" % (nxt + dt.timedelta(days=REVIEW_DAYS), REVIEW_DAYS))
    if check:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != body:
            print("CHECK FAILED: %s is out of date with its inputs" % OUT.name)
            sys.exit(1)
        print("CHECK OK — U1-U6, W1-W3 pass; universe up to date")
        return
    OUT.write_text(body, encoding="utf-8")
    print("WROTE %s — U1-U6, W1-W3 pass" % OUT.name)


if __name__ == "__main__":
    main(sys.argv[1:])
