"""PlotNua — atlas_common.py

Shared Atlas access and governance primitives. EXTRACTED VERBATIM from
generate_garden_room_universe.py; not one character of logic was rewritten.

WHY THIS EXISTS, AND WHY IT IS SMALL.
  The Additional Home builder needs to read Atlas and to apply two pieces of
  GOVERNANCE that must never exist in two versions: the Irish-availability
  vocabulary, and the export-hygiene sanitiser that keeps internal prose out
  of a published artefact. Duplicating either would mean PlotNua could answer
  the same question two ways.

WHAT IS DELIBERATELY NOT HERE.
  Garden Room qualification, its tiers, its category adjudication, its price
  adjudication, its detail partitions and its supplier segmentation all stay
  in the Garden Room generator. Additional Home qualification is required to
  be independent of them, so sharing them would defeat the requirement rather
  than serve it. This module is a floor, not a framework: nothing is added to
  it on the grounds that it might be reused one day.

PROVEN BY: the Gate S1 differential — the Garden Room generator produces
byte-identical output before and after this extraction, from a frozen Atlas
snapshot under a pinned clock.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_ID = "appoLZFWesvoPhZGR"                 # PlotNua Atlas Core

T_PRODUCTS   = "tblMiUcO4OT9ia2aE"

T_PRICING    = "tblqsjmkTrwSct7gv"

T_AVAIL      = "tblP1d5lgKxxhkBkj"

T_FEATVALS   = "tbl7wGyTgJ2mzjdOh"

T_FEATURES   = "tblH2EpBiV9bt1rdD"

T_ORGS       = "tblngwmviAcWxFKsW"

API = "https://api.airtable.com/v0"

PAGE_SIZE = 100

RETRIES = 4

IE_CONFIRMED = (
    "AVAILABLE ACROSS IRELAND",
    "AVAILABLE IN IRELAND",
    "AVAILABLE IN THE REPUBLIC OF IRELAND",
    # FIX 1. Atlas writes this WITHOUT the definite article, and the original
    # vocabulary carried it with. "AVAILABLE IN IRELAND" does not rescue the
    # case either: after "AVAILABLE IN " comes REPUBLIC, not IRELAND. One
    # missing word was resolving ~160 explicitly-positive products to UNKNOWN.
    "AVAILABLE IN REPUBLIC OF IRELAND",
    "REPUBLIC OF IRELAND CONFIRMED",
    "IRISH AVAILABILITY CONFIRMED",
    "SUPPLIES IRELAND",
)

IE_UNAVAILABLE = (
    "NOT AVAILABLE IN IRELAND",
    "NOT AVAILABLE IN THE REPUBLIC OF IRELAND",
    "DOES NOT SUPPLY IRELAND",
    "DOES NOT DELIVER TO IRELAND",
    "REPUBLIC OF IRELAND EXCLUDED",
    "NO IRISH AVAILABILITY",
)

IE_UNKNOWN = (
    "AVAILABILITY UNKNOWN",
    "REPUBLIC OF IRELAND UNCONFIRMED",
    "IRISH AVAILABILITY UNKNOWN",
    "UNCONFIRMED",
)

IE_NO_PUBLISHED_ROUTE = (
    "UK ONLY",
    "UNITED KINGDOM ONLY",
    "GB ONLY",
    "MAINLAND UK ONLY",
)

_REC_ID_RE = re.compile(r"\brec[A-Za-z0-9]{14}\b")

INTERNAL_LEAD_PHRASES = (
    "integrity:", "integrity issue", "integrity note", "do not rank",
    "do not use", "supplier status", "repair:", "gap:", "limitation:",
    "unresolved,", "recorded as standing technical debt",
    "standing technical debt", "attribution caution", "scope note",
    "domain note", "duplicate-organisation note", "related-entity finding",
    "registration cluster", "co-location note", "recency note",
    "candidates tested and rejected", "dissolved-registration finding",
    "note, recorded not acted upon", "recorded once and not collapsed",
)

def redact(msg) -> str:
    """Defence in depth on the one path a credential could conceivably travel.

    The token is only ever placed in an Authorization header, so no message
    built by this script contains it. But error text is assembled from
    exceptions raised by urllib, and an exception is somebody else's string.
    Anything that looks like a bearer token or an Airtable PAT is removed
    before it can reach a log, a workflow transcript or an artefact."""
    s = str(msg)
    s = re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", s)
    s = re.sub(r"\bpat[A-Za-z0-9._-]{10,}", "[REDACTED]", s)
    s = re.sub(r"\bkey[A-Za-z0-9]{14,}", "[REDACTED]", s)
    return s

def fail(msg):
    print(f"::error::{redact(msg)}", file=sys.stderr)
    print("Nothing was written.", file=sys.stderr)
    sys.exit(1)

def fetch_all(token: str, table: str, fields: list) -> list:
    """Every record in one table, carrying the named fields. Raises on failure.

    Pagination is checked for stability: Airtable returns an offset until the
    set is exhausted, and a page that comes back empty while still offering an
    offset means the read is not to be trusted."""
    out, offset, pages = [], None, 0
    while True:
        q = [("pageSize", str(PAGE_SIZE))] + [("fields[]", f) for f in fields]
        if offset:
            q.append(("offset", offset))
        url = f"{API}/{BASE_ID}/{table}?{urllib.parse.urlencode(q)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

        for attempt in range(RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(redact(f"{table}: HTTP {e.code} {e.reason}")) from e
            except Exception as e:
                if attempt < RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(redact(f"{table}: {e}")) from e

        page = payload.get("records", [])
        offset = payload.get("offset")
        pages += 1
        if not page and offset:
            raise RuntimeError(f"{table}: empty page {pages} while still paginating")
        out.extend(page)
        if not offset:
            return out
        if pages > 500:
            raise RuntimeError(f"{table}: pagination did not terminate")
        time.sleep(0.25)

def cell(rec, field):
    v = rec.get("fields", {}).get(field)
    if isinstance(v, dict):
        return v.get("name")
    return v

def links(rec, field) -> list:
    v = rec.get("fields", {}).get(field) or []
    return [x.get("id") if isinstance(x, dict) else x for x in v]

def txt(v) -> str:
    return (v or "").strip() if isinstance(v, str) else ""

def homeowner_text(s: str):
    """QUALIFICATION v2 — EXPORT HYGIENE.

    Atlas evidence text is written for two readers at once: the homeowner and
    the next researcher. The researcher's half — integrity notes, governance
    directives, technical-debt commentary and raw Airtable record IDs — was
    reaching the published artefact verbatim. A homeowner has no use for
    'DO NOT RANK on any basis' or 'recUhAgdKiDdJ3fLz', and an instruction
    written into a data field was never a control anyway.

    Sentence-level, and deliberately conservative: a sentence is dropped only
    when it OPENS with a known internal lead phrase. Ordinary evidence keeps
    every word. Record IDs are stripped wherever they survive, because they are
    never homeowner-facing in prose. Structural id fields are untouched — this
    function is applied to rendered text only.

    Returns None when nothing publishable remains, so the caller omits the key
    rather than emitting an empty string.
    """
    s = txt(s)
    if not s:
        return None
    # Directives written INSIDE a sentence, e.g. "…nothing estimated. DO NOT
    # RANK on internal area. PLANNING — MATERIAL: …". Remove the clause, keep
    # the evidence either side of it.
    s = re.sub(r"(?:^|(?<=[.!?]))\s*DO NOT (?:RANK|USE)\b[^.!?]*[.!?]", " ", s,
               flags=re.IGNORECASE)
    # Internal LABELS attached to genuinely useful evidence. The label goes;
    # the sentence stays. "CATEGORY INTEGRITY: Auroom supplies wellness
    # cabins…" is real homeowner information wearing a researcher's badge, and
    # deleting the sentence would throw away the best evidence in the record.
    s = re.sub(r"\b(?:[A-Z][A-Z \-]{0,24}\s)?INTEGRITY(?:\s+ISSUE)?\s*[:—-]\s*",
               "", s)
    s = re.sub(r"\bflagged as an integrity issue\b", "flagged", s,
               flags=re.IGNORECASE)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", s)
    kept = []
    for part in parts:
        probe = part.strip().lstrip("—-• ").lower()
        if any(probe.startswith(p) for p in INTERNAL_LEAD_PHRASES):
            continue
        kept.append(part.strip())
    out = " ".join(p for p in kept if p)
    out = _REC_ID_RE.sub("", out)
    out = re.sub(r"\(\s*[,;]?\s*\)", "", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" ,;—-")
    return out or None

def classify_irish_availability(feat_rows: list) -> tuple:
    """(state, basis, scope, classified, no_route) for Irish availability.

    state is confirmed | unknown | unavailable. `no_route` marks the
    no-published-irish-route case, which is a kind of UNKNOWN, never a kind of
    unavailable. `classified` is False when a lead phrase was present but
    matched no vocabulary — that product still resolves to UNKNOWN, and the
    caller counts it so the parser's blind spots stay visible.

    ORDER OF EVIDENCE, AND WHY IT CHANGED.

    The first version read Confirmation State first and returned immediately
    on a legacy `No`. That produced the incoherence the diagnostic found: six
    products hard-excluded on a legacy checkbox while ~48 carrying the same
    UK-ONLY prose stayed eligible, because their checkbox was blank.

    A legacy `No` is now a CANDIDATE for unavailable, not a verdict. It is
    honoured only when the accompanying text explicitly establishes that the
    Republic cannot be served. Where the text says only that coverage is UK
    ONLY, the product is UNKNOWN + no-published-irish-route. Where there is no
    text at all, a bare legacy `No` is not explicit evidence of anything and
    resolves to UNKNOWN.

    UNAVAILABLE is reserved for evidence that says so in terms.
    """
    best = ("unknown", "no irish-availability evidence recorded", None)
    classified = True
    no_route = False
    legacy_no = None                      # a bare `No`, pending corroboration

    for row in feat_rows:
        scope = cell(row, "Evidence Scope")
        conf = txt(cell(row, "Confirmation State"))
        body = txt(cell(row, "Value Text"))
        head = body.upper()

        # A positive Confirmation State is still decisive: it is an explicit
        # statement, and nothing in the ruling weakens it.
        if conf and conf.lower().startswith("yes"):
            return ("confirmed", f"Confirmation State: {conf}", scope, True, False)

        # Text is now read before a negative Confirmation State is honoured.
        if body:
            if any(head.startswith(p) for p in IE_UNAVAILABLE):
                return ("unavailable", body[:200], scope, True, False)
            if any(head.startswith(p) for p in IE_CONFIRMED):
                return ("confirmed", body[:200], scope, True, False)
            if any(head.startswith(p) for p in IE_NO_PUBLISHED_ROUTE):
                no_route = True
                best = ("unknown", body[:200], scope)
                continue
            if any(head.startswith(p) for p in IE_UNKNOWN):
                best = ("unknown", body[:200], scope)
                continue
            classified = False
            best = ("unknown", body[:200], scope)
            continue

        if conf:
            c = conf.lower()
            if c == "no":
                legacy_no = (f"Confirmation State: {conf} (no accompanying evidence text)", scope)
            elif c == "unknown":
                best = ("unknown", f"Confirmation State: {conf}", scope)

    # A legacy `No` that nothing corroborates is not explicit evidence of
    # unavailability. It lowers nothing and excludes nothing.
    if legacy_no and best[1] == "no irish-availability evidence recorded":
        best = ("unknown", legacy_no[0], legacy_no[1])

    return best + (classified, no_route)
