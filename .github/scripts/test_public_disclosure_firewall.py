#!/usr/bin/env python3
"""
PlotNua — PUBLIC DISCLOSURE FIREWALL.

Every file at the repository root is served from a GitHub Pages site with a
CNAME, so it is publicly fetchable. Publication is a disclosure decision, not
only an engineering one.

This suite checks the PUBLICLY SERVED evidence artefacts for content that is
internal by nature. It is deliberately PATTERN-based, not string-based: the
point is that this class of leak cannot silently return in a new artefact or
a new claim, not that three particular sentences stay deleted.

Read-only. Writes nothing, contacts nothing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Publicly served evidence artefacts governed by this firewall.
PUBLIC_ARTEFACTS = [
    "parking-platform-evidence.json",
    "supplier-export-evidence.json",
    "PLATFORM-EVIDENCE-GOVERNANCE.md",
]

PASS = FAIL = 0


def ck(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"    ok   {name}")
    else:
        FAIL += 1
        print(f"    *** FAIL *** {name}  {detail}")


# ── patterns ────────────────────────────────────────────────────────────────
AIRTABLE_ID = re.compile(r"\b(?:rec|tbl|fld|app|sel)[A-Za-z0-9]{14}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")
SECRET = re.compile(
    r"(?:api[_-]?key|secret|password|bearer\s+[A-Za-z0-9]|authorization:|"
    r"-----BEGIN|\bpat[A-Za-z0-9]{14}\b|\bkey[A-Za-z0-9]{14}\b)", re.I)

# Negotiation / relationship-status vocabulary. A family, not a list of the
# specific sentences removed on 2026-09-22.
RELATIONSHIP_STATUS = re.compile(
    r"(awaiting (?:contact|reply|response)"
    r"|escalated(?: internally)?"
    r"|positive response"
    r"|head of partnerships"
    r"|partnerships (?:contact|team|lead)"
    r"|our outreach|outreach record|outreach status"
    r"|in negotiation|negotiating position"
    r"|commercial conversation|commercial discussion"
    r"|declined to (?:participate|engage)"
    r"|not interested in participating"
    r"|expected to contact (?:us|plotnua))", re.I)

# Claim-level provenance that must never appear in a published artefact.
FORBIDDEN_PROVENANCE = {"COMMERCIAL_CORRESPONDENCE"}
FORBIDDEN_SOURCE_TYPE = {"OUTREACH_RECORD"}
FORBIDDEN_METHOD = {"CORRESPONDENCE"}


def iter_claims(doc):
    for key in ("claims", "records"):
        for c in (doc.get(key) or []):
            if isinstance(c, dict):
                yield c


def main() -> int:
    print("\nPUBLIC DISCLOSURE FIREWALL\n")
    present = [f for f in PUBLIC_ARTEFACTS if (ROOT / f).exists()]
    ck("the governed public artefacts exist", len(present) == len(PUBLIC_ARTEFACTS),
       str(sorted(set(PUBLIC_ARTEFACTS) - set(present))))

    for name in present:
        p = ROOT / name
        raw = p.read_text(encoding="utf-8")
        print(f"\n--- {name} ({len(raw)//1024}KB) ---")

        ck("no internal Airtable/base identifier",
           not AIRTABLE_ID.search(raw),
           str(sorted(set(AIRTABLE_ID.findall(raw)))[:3]))
        ck("no email address", not EMAIL.search(raw),
           str(sorted(set(EMAIL.findall(raw)))[:3]))
        ck("no credential or secret pattern", not SECRET.search(raw),
           str(sorted({m.group(0)[:24] for m in SECRET.finditer(raw)})[:3]))
        hits = sorted({m.group(0) for m in RELATIONSHIP_STATUS.finditer(raw)})
        # The governance file may DESCRIBE the prohibition; it must not RECORD
        # a status. It is allowed to use the vocabulary inside the rule text.
        if name.endswith(".md"):
            ck("governance file states the rule without recording a status",
               "MUST NOT CONTAIN PRIVATE COMMERCIAL" in raw.upper())
        else:
            ck("no relationship or negotiation status vocabulary",
               not hits, str(hits[:4]))

        if name.endswith(".json"):
            doc = json.loads(raw)
            claims = list(iter_claims(doc))
            ck("artefact parses and carries claims", bool(claims), str(len(claims)))
            bad_prov = [c.get("claim_key") for c in claims
                        if c.get("provenance") in FORBIDDEN_PROVENANCE]
            ck("no claim carries COMMERCIAL_CORRESPONDENCE provenance",
               not bad_prov, str(bad_prov[:3]))
            bad_src = [c.get("claim_key") for c in claims
                       if c.get("source_type") in FORBIDDEN_SOURCE_TYPE]
            ck("no claim cites a private outreach record as its source",
               not bad_src, str(bad_src[:3]))
            bad_meth = [c.get("claim_key") for c in claims
                        if c.get("verification_method") in FORBIDDEN_METHOD]
            ck("no claim is verified by correspondence",
               not bad_meth, str(bad_meth[:3]))
            # Every published claim must cite something a reader can check,
            # except where the claim IS a recorded absence.
            unsourced = [c.get("claim_key") for c in claims
                         if not c.get("source_url")
                         and c.get("evidence_type") != "ABSENCE_OF_RECORD"]
            ck("every published claim cites a checkable source",
               not unsourced, str(unsourced[:3]))

    # The MODEL must survive sanitation: removing the private instance must not
    # remove the ability to distinguish provenance if a fact arrives later.
    print("\n--- the provenance model remains intact ---")
    for gen in ("generate_parking_platform_evidence.py",
                "generate_supplier_export_evidence.py"):
        src = (ROOT / ".github" / "scripts" / gen).read_text(encoding="utf-8")
        ck(f"{gen} still defines SUPPLIER_PROVIDED", "SUPPLIER_PROVIDED" in src)
        ck(f"{gen} still defines COMMERCIAL_CORRESPONDENCE",
           "COMMERCIAL_CORRESPONDENCE" in src)

    print("\n" + "=" * 74)
    print(f"  {PASS} passed, {FAIL} failed")
    print("=" * 74)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
