#!/usr/bin/env python3
"""PLOTNUA SEARCH · SUPPLIER RECOGNITION ALIASES (SEARCH-V1 amendment A6)
===========================================================================

Writes atlas-tools/search-supplier-aliases.json: the governed input from which
build-search-index.py derives the index's `aliases` block, so that a homeowner
who types or pastes a supplier's web address ("https://www.sproutpod.ie/",
"sproutpod.ie") or its trading name written as one word ("SproutPod") reaches
the records PlotNua already publishes for that supplier.

WHAT THIS FILE MAY CONTAIN, AND NOTHING ELSE (founder approval, 12 Nov 2026)
  * Atlas Organisations.Website, copied verbatim.
  * Image Permission Outreach "Permitted Domain" values, ONLY on rows whose
    Permission Outcome is founder-confirmed and granted. A permission row that is
    Unknown, Declined or Withdrawn contributes nothing.
  * Two small hand sections, each line carrying its evidence:
      tradingNames   a trading name Atlas evidence supports but the record name
                     does not spell (e.g. "GardenRooms.ie");
      excludedNames  a word in an Atlas record name that is a description, not a
                     trading name (e.g. "(Garden Rooms)" in Elm Landscaping's
                     record), resolved here after build-search-index.py's A6b
                     duplicate guard refused it.
  Retail-channel aliases (one brand's domain pointing at another organisation's
  records) are DEFERRED by founder decision, 12 Nov 2026, and are refused.

WHAT IT NEVER DOES
  No Atlas write, no network call except the optional read-only --fetch, no
  decision about publication. Whether an alias is EMITTED is decided by the index
  builder from the published corpus alone: an organisation with no published
  record gets no alias, whatever this file says.

USAGE
  python3 atlas-tools/build-search-aliases.py --from-export EXPORT.json
        full regeneration from a read-only Atlas export (Organisations + Image
        Permission Outreach, Atlas REST shape)
  python3 atlas-tools/build-search-aliases.py --fetch
        the same, reading Atlas directly with AIRTABLE_TOKEN (read-only)
  python3 atlas-tools/build-search-aliases.py --merge-snapshot SNAP --organisation recXXXX
        targeted update: refresh ONE organisation's name and Website from a
        publish-targeted-update.py snapshot; every other entry is left untouched
  python3 atlas-tools/build-search-aliases.py --check
        validate the committed file; writes nothing
"""
import argparse
import datetime as _dt
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "atlas-tools" / "search-supplier-aliases.json"
SCHEMA = "plotnua.search.aliases"
BASE = "appoLZFWesvoPhZGR"
T_ORGS = "tblngwmviAcWxFKsW"
T_IPO = "tblDnEVrH26beMy1B"

# A Permission Outcome that counts as a founder-confirmed grant. Everything else
# (Unknown, Declined, Withdrawn, Superseded, anything new) contributes nothing.
GRANTED = re.compile(r"^Granted( with Conditions)? — Founder Confirmed$")
# Records that are not suppliers, or are retired duplicates of another record.
NOT_A_SUPPLIER = re.compile(r"TEST|NOT a supplier|RETIRED DUPLICATE|DO NOT CONTACT", re.I)
HOST = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,24}$")

# Hand sections. Each entry is founder-approved and carries its evidence.
TRADING_NAMES = [
    {"organisation": "Garden Rooms", "name": "GardenRooms.ie",
     "evidence": "ORG-000001 Website https://www.gardenrooms.ie/; the supplier trades as GardenRooms.ie "
                 "(garden-room supplier audit, 12 Nov 2026)"},
]
EXCLUDED_NAMES = [
    {"organisation": "Elm Landscaping (Garden Rooms)", "name": "Garden Rooms",
     "reason": "A product-category description inside the Atlas record name, not a trading name. "
               "It collides with GardenRooms.ie (ORG-000001); refused by A6b on 12 Nov 2026."},
]


def die(msg):
    sys.stderr.write("REFUSED: %s\n" % msg)
    sys.exit(1)


def host_of(url):
    """Registrable host of an Atlas Website value: scheme, www., path, query and
    port removed. None when the value is not a web address."""
    m = re.match(r"^\s*(?:[a-z][a-z0-9+.-]*://)?(?:www\.)?([^/?#:\s]+)", (url or "").strip().lower())
    h = m.group(1).rstrip(".") if m else None
    return h if h and HOST.match(h) else None


def entries_from(orgs, ipo):
    by_id = {}
    for r in orgs:
        f = r.get("fields") or {}
        name = (f.get("Organisation Name") or "").strip()
        if not name or NOT_A_SUPPLIER.search(name):
            continue
        by_id[r["id"]] = {"atlasRecord": r["id"], "atlasCode": f.get("Organisation Code") or "",
                          "name": name, "website": (f.get("Website") or "").strip(),
                          "permittedDomains": []}
    for r in ipo:
        f = r.get("fields") or {}
        outcome = f.get("Permission Outcome")
        outcome = outcome.get("name") if isinstance(outcome, dict) else outcome
        dom = (f.get("Permitted Domain") or "").strip().lower()
        if not dom or not GRANTED.match(outcome or ""):
            continue
        for oid in f.get("Organisation") or []:
            oid = oid.get("id") if isinstance(oid, dict) else oid
            if oid in by_id:
                by_id[oid]["permittedDomains"].append(
                    {"domain": dom, "ref": f.get("Outreach Ref") or r["id"], "outcome": outcome})
    for e in by_id.values():
        e["permittedDomains"].sort(key=lambda d: (d["domain"], d["ref"]))
    return sorted(by_id.values(), key=lambda e: (e["name"].lower(), e["atlasRecord"]))


def document(entries, source):
    return {
        "schema": SCHEMA, "version": "1",
        "generated": _dt.date.today().isoformat(),
        "source": source,
        "rule": ("Hosts come only from Organisations.Website and from founder-confirmed granted "
                 "Image Permission Outreach Permitted Domains. build-search-index.py emits an alias "
                 "only for an organisation that already has published records. Retail-channel "
                 "aliases are deferred (founder decision, 12 Nov 2026)."),
        "organisations": entries,
        "tradingNames": TRADING_NAMES,
        "excludedNames": EXCLUDED_NAMES,
    }


def validate(doc):
    if doc.get("schema") != SCHEMA:
        die("not a %s file" % SCHEMA)
    if doc.get("channels"):
        die("retail-channel aliases are deferred by founder decision (12 Nov 2026)")
    seen = set()
    for e in doc["organisations"]:
        for k in ("atlasRecord", "name", "website", "permittedDomains"):
            if k not in e:
                die("organisation entry %r lacks %r" % (e.get("name"), k))
        if e["atlasRecord"] in seen:
            die("organisation %s appears twice" % e["atlasRecord"])
        seen.add(e["atlasRecord"])
        for d in e["permittedDomains"]:
            if not GRANTED.match(d.get("outcome") or ""):
                die("%r: permitted domain %r is not a founder-confirmed grant" % (e["name"], d.get("domain")))
            if not HOST.match(d.get("domain") or ""):
                die("%r: permitted domain %r is not a hostname" % (e["name"], d.get("domain")))
    names = {e["name"] for e in doc["organisations"]}
    for t in doc.get("tradingNames", []):
        if t.get("organisation") not in names or not t.get("evidence"):
            die("trading name %r must name an Atlas organisation and carry evidence" % t.get("name"))
    for x in doc.get("excludedNames", []):
        if x.get("organisation") not in names or not x.get("reason"):
            die("excluded name %r must name an Atlas organisation and carry a reason" % x.get("name"))


def write(doc):
    validate(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = len(doc["organisations"])
    w = sum(1 for e in doc["organisations"] if host_of(e["website"]))
    p = sum(len(e["permittedDomains"]) for e in doc["organisations"])
    print("WROTE %s: %d organisations, %d with a usable Website, %d founder-confirmed permitted "
          "domain(s)" % (OUT.relative_to(ROOT), n, w, p))


def fetch():
    token = os.environ.get("AIRTABLE_TOKEN")
    if not token:
        die("--fetch needs AIRTABLE_TOKEN in the environment; or pass --from-export")

    def get(table, fields):
        out, offset = [], None
        while True:
            q = [("pageSize", "100")] + [("fields[]", f) for f in fields]
            if offset:
                q.append(("offset", offset))
            url = "https://api.airtable.com/v0/%s/%s?%s" % (BASE, table, urllib.parse.urlencode(q))
            req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
            for attempt in range(5):
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        d = json.loads(r.read())
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 429 and attempt < 4:
                        time.sleep(30 if attempt else 1)
                        continue
                    die("Atlas read failed: HTTP %d" % e.code)
            out += d.get("records", [])
            offset = d.get("offset")
            if not offset:
                return out
    orgs = get(T_ORGS, ["Organisation Name", "Organisation Code", "Website"])
    ipo = [r for r in get(T_IPO, ["Outreach Ref", "Organisation", "Permitted Domain", "Permission Outcome"])
           if (r.get("fields") or {}).get("Permitted Domain")]
    return orgs, ipo


def merge_snapshot(snap_path, org_id):
    """Targeted update: refresh ONE organisation's name and Website from the
    publish-targeted-update.py snapshot. Its permitted domains, and every other
    entry, are left exactly as they are."""
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    snap = json.loads(pathlib.Path(snap_path).read_text(encoding="utf-8"))
    rows = [o for o in snap.get("organisations", []) if o.get("id") == org_id]
    if len(rows) != 1:
        die("the snapshot holds no organisation %s" % org_id)
    f = rows[0].get("fields") or {}
    name = (f.get("Organisation Name") or "").strip()
    if not name or NOT_A_SUPPLIER.search(name):
        die("organisation %s is not a supplier record" % org_id)
    entry = {"atlasRecord": org_id, "atlasCode": f.get("Organisation Code") or "", "name": name,
             "website": (f.get("Website") or "").strip(), "permittedDomains": []}
    others = [e for e in doc["organisations"] if e["atlasRecord"] != org_id]
    old = [e for e in doc["organisations"] if e["atlasRecord"] == org_id]
    if old:
        entry["permittedDomains"] = old[0]["permittedDomains"]
        if old[0]["name"] != name:
            for sect, key in (("tradingNames", "organisation"), ("excludedNames", "organisation")):
                for t in doc.get(sect, []):
                    if t[key] == old[0]["name"]:
                        die("%s names %r, which Atlas now calls %r; update the hand section first"
                            % (sect, old[0]["name"], name))
    doc["organisations"] = sorted(others + [entry], key=lambda e: (e["name"].lower(), e["atlasRecord"]))
    if old and old[0] == entry:
        print("aliases: %s unchanged" % name)
        return
    write(doc)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--from-export")
    g.add_argument("--fetch", action="store_true")
    g.add_argument("--merge-snapshot")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--organisation")
    a = ap.parse_args(argv)
    if a.check:
        validate(json.loads(OUT.read_text(encoding="utf-8")))
        print("search-supplier-aliases.json: valid")
        return 0
    if a.merge_snapshot:
        if not a.organisation:
            die("--merge-snapshot needs --organisation recXXXX")
        merge_snapshot(a.merge_snapshot, a.organisation)
        return 0
    if a.fetch:
        orgs, ipo = fetch()
        source = "Atlas Core read-only read with AIRTABLE_TOKEN, %s" % _dt.date.today().isoformat()
    else:
        exp = json.loads(pathlib.Path(a.from_export).read_text(encoding="utf-8"))
        orgs, ipo = exp["organisations"], exp.get("imagePermissionOutreach", [])
        source = exp.get("source") or "Atlas export %s" % pathlib.Path(a.from_export).name
    write(document(entries_from(orgs, ipo), source))
    return 0


if __name__ == "__main__":
    sys.exit(main())
