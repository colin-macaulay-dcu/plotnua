#!/usr/bin/env python3
"""
PlotNua — homepage Atlas counters.

Reads three governed counts from the Atlas base and writes them into the
homepage as finished HTML. The homeowner's browser never talks to Airtable and
never fetches the generated JSON: the numbers are already in the page it is
served, so they survive with JavaScript disabled and cause no layout shift.

GOVERNED METRICS — do not substitute
  Garden Rooms    Products         where Product Category  = "Garden Rooms"
  Suppliers       Organisations    where Organisation Type = "Supplier"
  Verified Prices Product Pricing  where Status            = "Verified"

  Verified Prices is NOT the total Product Pricing count. The total is
  recorded alongside it for context and is never published.

SANITY GATES — any failure writes nothing and exits non-zero
  a count of zero                              FAIL
  a missing or non-integer count               FAIL
  a decrease of more than 20% on a count       FAIL
  an increase, of any size                     ALLOW, and log it
  the homepage anchors or labels have moved    FAIL

  Atlas is expanding, so a large rise is plausible. A large fall is far more
  likely to be a renamed choice, a changed field or a partial API response, and
  publishing it would replace good figures with wrong ones. On any failure the
  live homepage keeps the last known valid figures, because nothing is written.

Standard library only — no pip install step in the workflow.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ── Atlas addressing ─────────────────────────────────────────────────────────
# The base id is an identifier, not a credential: it is useless without a token,
# so it lives here in plain sight rather than as a second secret.
BASE_ID = "appoLZFWesvoPhZGR"          # PlotNua Atlas Core

METRICS = {
    "gardenRooms": {
        "table": "tblMiUcO4OT9ia2aE",   # Products
        "field": "Product Category",
        "value": "Garden Rooms",
        "label": "Garden Rooms",
    },
    "suppliers": {
        "table": "tblngwmviAcWxFKsW",   # Organisations
        "field": "Organisation Type",
        "value": "Supplier",
        "label": "Suppliers",
    },
    "verifiedPrices": {
        "table": "tblqsjmkTrwSct7gv",   # Product Pricing
        "field": "Status",
        "value": "Verified",
        "label": "Verified Prices",
    },
}

MAX_DECREASE = 0.20                     # 20%, per founder governance

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"
STATS = ROOT / "atlas-stats.json"

API = "https://api.airtable.com/v0"
PAGE_SIZE = 100
RETRIES = 4


def fail(msg: str) -> "NoReturn":                      # noqa: F821
    print(f"::error::{msg}", file=sys.stderr)
    print("Nothing was written. The live homepage keeps its last valid figures.",
          file=sys.stderr)
    sys.exit(1)


# ── Airtable ─────────────────────────────────────────────────────────────────
def fetch_all(token: str, table: str, field: str) -> list:
    """Every record in one table, carrying one field. Raises on any failure."""
    out, offset = [], None
    while True:
        q = {"pageSize": str(PAGE_SIZE), "fields[]": field}
        if offset:
            q["offset"] = offset
        url = f"{API}/{BASE_ID}/{table}?{urllib.parse.urlencode(q)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

        for attempt in range(RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                # 429 and 5xx are worth retrying; 401/403/404 are not.
                if e.code in (429, 500, 502, 503, 504) and attempt < RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"{table}: HTTP {e.code} {e.reason}") from e
            except Exception as e:                     # network, timeout, JSON
                if attempt < RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"{table}: {e}") from e

        out.extend(payload.get("records", []))
        offset = payload.get("offset")
        if not offset:
            return out
        time.sleep(0.25)                                # stay under 5 req/s


def cell(rec: dict, field: str):
    """A singleSelect comes back as a plain string from the REST API. Some
    clients return {"name": ...}; accept both rather than assume one."""
    v = rec.get("fields", {}).get(field)
    if isinstance(v, dict):
        return v.get("name")
    return v


def collect(token: str) -> dict:
    counts = {}
    for key, m in METRICS.items():
        records = fetch_all(token, m["table"], m["field"])
        total = len(records)
        matched = sum(1 for r in records if cell(r, m["field"]) == m["value"])
        counts[key] = {"count": matched, "tableTotal": total}
        print(f"  {m['label']:<16} {matched:>5}  of {total} records in the table")
    return counts


# ── sanity gates ─────────────────────────────────────────────────────────────
def previous() -> dict:
    if not STATS.exists():
        return {}
    try:
        return json.loads(STATS.read_text(encoding="utf-8")).get("counts", {})
    except Exception:
        return {}                                       # unreadable = no baseline


def gate(counts: dict, prev: dict) -> None:
    for key, m in METRICS.items():
        n = counts.get(key, {}).get("count")
        if not isinstance(n, int) or isinstance(n, bool):
            fail(f"{m['label']}: count is missing or not an integer ({n!r}).")
        if n == 0:
            fail(f"{m['label']}: count is 0. Treated as a failure, never as a result "
                 f"— most likely the '{m['value']}' choice or the '{m['field']}' "
                 f"field has been renamed.")
        was = prev.get(key, {}).get("count") if isinstance(prev.get(key), dict) else prev.get(key)
        if isinstance(was, int) and was > 0:
            if n < was * (1 - MAX_DECREASE):
                drop = 100 * (was - n) / was
                fail(f"{m['label']}: fell from {was} to {n}, a drop of {drop:.1f}% "
                     f"— more than the {MAX_DECREASE:.0%} allowed. A fall this size is "
                     f"more likely a filter, schema or API problem than a real change. "
                     f"Check Atlas, then re-run.")
            if n > was:
                print(f"::notice::{m['label']} rose from {was} to {n}.")
            elif n < was:
                print(f"  {m['label']} eased from {was} to {n}, within tolerance.")


# ── the homepage ─────────────────────────────────────────────────────────────
# Six numbers, three of them twice over. Each is found by an anchor that also
# asserts the public label, so the workflow can never change wording — only
# digits. If an anchor has moved, the script refuses to guess.
ATTRS = {"gardenRooms": "data-products",
         "suppliers": "data-suppliers",
         "verifiedPrices": "data-prices"}
DTS = {"gardenRooms": "atlasProducts",
       "suppliers": "atlasSuppliers",
       "verifiedPrices": "atlasPrices"}


def patch_homepage(html: str, counts: dict) -> tuple:
    """Returns (new_html, changed). Raises ValueError if an anchor has moved."""
    out, changed = html, False

    for key, m in METRICS.items():
        n = counts[key]["count"]

        attr = ATTRS[key]
        pat = re.compile(r'(' + re.escape(attr) + r'=")(\d+)(")')
        found = pat.findall(out)
        if len(found) != 1:
            raise ValueError(f"{attr}: expected exactly one occurrence, found {len(found)}")
        if found[0][1] != str(n):
            changed = True
        out = pat.sub(lambda mm: mm.group(1) + str(n) + mm.group(3), out, count=1)

        dt = DTS[key]
        pat = re.compile(r'(<dt id="' + re.escape(dt) + r'">)(\d+)(</dt><dd>)'
                         + re.escape(m["label"]) + r'(</dd>)')
        found = pat.findall(out)
        if len(found) != 1:
            raise ValueError(
                f'<dt id="{dt}"> with label "{m["label"]}": expected exactly one '
                f"occurrence, found {len(found)}. The markup or the public label has "
                f"moved — refusing to guess.")
        if found[0][1] != str(n):
            changed = True
        out = pat.sub(lambda mm: mm.group(1) + str(n) + mm.group(3) + m["label"] + mm.group(4),
                      out, count=1)

    return out, changed


def main() -> None:
    token = os.environ.get("AIRTABLE_TOKEN")
    if not token:
        fail("AIRTABLE_TOKEN is not set.")
    if not INDEX.exists():
        fail(f"index.html not found at {INDEX}")

    print("Reading Atlas…")
    try:
        counts = collect(token)
    except Exception as e:
        fail(f"Atlas read failed: {e}")

    gate(counts, previous())

    html = INDEX.read_text(encoding="utf-8")
    try:
        new_html, changed = patch_homepage(html, counts)
    except ValueError as e:
        fail(str(e))

    payload = {
        "source": "PlotNua Atlas Core",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts": {
            "gardenRooms": {"count": counts["gardenRooms"]["count"],
                            "definition": "Products where Product Category = Garden Rooms"},
            "suppliers": {"count": counts["suppliers"]["count"],
                          "definition": "Organisations where Organisation Type = Supplier"},
            "verifiedPrices": {"count": counts["verifiedPrices"]["count"],
                               "definition": "Product Pricing where Status = Verified",
                               "ofTotalPricingRecords": counts["verifiedPrices"]["tableTotal"]},
        },
        "note": ("Generated by .github/workflows/atlas-stats.yml. The homepage does not "
                 "read this file: the same figures are written into index.html so they "
                 "are present without JavaScript. This file is the audit record."),
    }
    new_stats = json.dumps(payload, indent=2) + "\n"

    old_stats = STATS.read_text(encoding="utf-8") if STATS.exists() else ""
    old_counts = previous()
    stats_changed = any(
        (old_counts.get(k, {}).get("count") if isinstance(old_counts.get(k), dict)
         else old_counts.get(k)) != counts[k]["count"] for k in METRICS)

    if not changed and not stats_changed and old_stats:
        print("No governed count changed. Nothing written, nothing to commit.")
        return

    INDEX.write_text(new_html, encoding="utf-8")
    STATS.write_text(new_stats, encoding="utf-8")
    print(f"Written: {INDEX.name}, {STATS.name}")
    for k, m in METRICS.items():
        print(f"  {m['label']}: {counts[k]['count']}")


if __name__ == "__main__":
    main()
