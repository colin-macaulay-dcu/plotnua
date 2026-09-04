#!/usr/bin/env python3
"""
ISSUE 005 PIECE D4b — VALIDATOR FOR THE LONG-FORM DETAIL EVIDENCE ARTEFACT.

A SEPARATE SCRIPT, DELIBERATELY. The core validator guards the file that decides
what a homeowner is shown and how it ranks; it is not weakened, extended or
re-pointed here. This one guards a second, additive artefact with a different
shape and a different failure consequence, and it is gated the same way: exit
non-zero and nothing publishes.

WHAT IT REFUSES
    invalid JSON · a top-level shape that is not the agreed contract ·
    a products map that is not an object · a canonical product id that is not
    rec + 14 alphanumerics · a DUPLICATE product id in the raw text (which
    json.load would silently collapse) · a category outside the declared set ·
    a category value that is not an object · a value with no usable text and no
    records · a records[] entry that is not an object · a records[] that
    disagrees with its own primary · header counts that disagree with the data
    (internal generator corruption) · any Match field leaking into the file.

WHAT IT DOES NOT REFUSE
    A product with no Considerations. Only products Atlas holds long-form
    evidence for appear, and absence is the normal case for the rest — 465
    records against 490 products. Refusing on absence would fail every run.

CHANGE DETECTION ignores `generated`, which moves every run by definition, so an
unchanged Atlas produces no commit. Same rule as the core validator.
"""
import argparse, gzip, json, os, re, sys
from pathlib import Path

ID_RE = re.compile(r"^rec[A-Za-z0-9]{14}$")

# The only categories this artefact may carry today. Adding one here is the
# deliberate act that lets a new long-form category through; a category that
# appears in the data without appearing here is a generator fault, not a warning.
#
# ISSUE 005 PIECE E2 — the remaining Decision Intelligence layer, plus
# provenance. Every one is CARRIED and validated; whether a homeowner is SHOWN
# it is a separate decision made in the page. Strengths in particular is carried
# and deliberately not presented — 429 of its 465 records have no extractable
# homeowner segment — and the validator's job is to guarantee the evidence
# survives intact, not to guess what is displayed.
# ISSUE 005 PIECE E2a — the supplier partition's own contract.
SUPPLIER_CATEGORY = "suppliers"
SUPPLIER_ALLOWED_KEYS = {
    "contractingEntity", "installationModel", "irishPresence", "deliveryCoverage",
    "manufacturingLocation", "jurisdiction", "evidenceTier", "evidenceScope",
    "sources",
}
# Frozen for E3. marketEligibility() branches on these and getEligibleAtlasPool()
# filters the pool on the result, so one of them appearing here would silently
# move products in and out of Results.
SUPPLIER_FORBIDDEN_KEYS = {
    "irish", "excludedProductIds", "excludedRanges", "excludesIreland",
    "deliveryConfirmed", "installationConfirmed",
}
# ATLAS 487 BATCH 1 · JOB B — the EXACT governed Organisation Type vocabulary.
# Proved against all 61 resolved Garden Room organisations before this list was
# written: 42 Manufacturer, 7 Bespoke Builder, 5 Modular Builder, 6 Supplier,
# 1 Installer = 61/61, and no other value occurs. A closed set here is what
# stops a future free-text or renamed value reaching a homeowner unreviewed,
# and what stops anything being INFERRED into the field.
SUPPLIER_ORG_TYPES = {
    "Manufacturer", "Bespoke Builder", "Modular Builder", "Supplier", "Installer",
}
SUPPLIER_PERSONAL = re.compile(
    r"[A-Za-z0-9._%%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"      # email
    r"|(?:\+\d[\d ()-]{7,})"                                # international phone
)


def validate_supplier(doc, errors):
    """The supplier partition. A different shape, so a different checker."""
    if not isinstance(doc, dict):
        errors.append("supplier partition is not an object")
        return
    orgs = doc.get("products")
    if not isinstance(orgs, dict):
        errors.append("supplier partition: products is not an object")
        return
    for oid, rec in orgs.items():
        if not re.fullmatch(r"rec[A-Za-z0-9]{14}", str(oid)):
            errors.append(f"not a canonical Airtable organisation id: {oid!r}")
        if not isinstance(rec, dict):
            errors.append(f"{oid}: entry is not an object")
            continue
        for bad in SUPPLIER_FORBIDDEN_KEYS:
            if bad in rec:
                errors.append(f"{oid}: FROZEN eligibility key present: {bad!r}")
        # ATLAS 487 BATCH 1 — the two governed Organisation fields.
        # These GATES ARE ADDITIVE. Nothing existing is relaxed.
        if "organisationType" in rec:
            ot = rec["organisationType"]
            if not isinstance(ot, str) or ot not in SUPPLIER_ORG_TYPES:
                errors.append(
                    f"{oid}.organisationType: not a governed Organisation Type: {ot!r}")
        if "lastReviewed" in rec:
            lr = rec["lastReviewed"]
            if not isinstance(lr, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lr):
                errors.append(
                    f"{oid}.lastReviewed: not a governed ISO date: {lr!r}")
        loc = rec.get("locality")
        if not isinstance(loc, dict) or not loc:
            errors.append(f"{oid}: locality is not a non-empty object")
            continue
        for k, v in loc.items():
            if k in SUPPLIER_FORBIDDEN_KEYS:
                errors.append(f"{oid}.locality: FROZEN eligibility key: {k!r}")
            elif k not in SUPPLIER_ALLOWED_KEYS:
                errors.append(f"{oid}.locality: key not in contract: {k!r}")
            if not isinstance(v, str) or not v.strip():
                errors.append(f"{oid}.locality.{k}: not a non-empty string")
                continue
            hit = SUPPLIER_PERSONAL.search(v)
            if hit:
                errors.append(f"{oid}.locality.{k}: personal contact data: {hit.group(0)!r}")


ALLOWED_CATEGORIES = {
    "considerations",
    "planningConsiderations",
    "bestFor",
    "strengths",
    "typicalHomeowner",
    "alternatives",
    "sources",          # product-level provenance, text as Atlas holds it,
    # ISSUE 005 PIECE E2a — the supplier partition.
    "suppliers",
}

# Fields that belong to the Match universe and must never be duplicated here.
# The canonical product id is the join; anything else is a second copy of the
# product waiting to drift out of step with the first.
FORBIDDEN_FIELDS = {
    "price", "priceFrom", "turnkeyPrice", "qualification", "qualificationTier",
    "confidenceTier", "style", "styleTags", "availability", "availabilityStatus",
    "organisation", "organisationEvidence", "floorAreaM2", "floorArea",
    "irishAvailability", "productUrl", "imageUrl", "name",
}


def load(path, label, errors):
    p = Path(path)
    if not p.exists():
        errors.append(f"{label}: file not found: {path}")
        return None, None
    raw = p.read_bytes()
    try:
        return json.loads(raw.decode("utf-8")), raw
    except Exception as exc:
        errors.append(f"{label}: invalid JSON — {exc}")
        return None, raw


def duplicate_ids(raw):
    """json.loads keeps the LAST of two identical keys and reports nothing, so a
       duplicated product id would vanish silently. Count them in the text."""
    if not raw:
        return []
    seen, dupes = set(), []
    for m in re.finditer(rb'"(rec[A-Za-z0-9]{14})"\s*:', raw):
        k = m.group(1).decode()
        if k in seen and k not in dupes:
            dupes.append(k)
        seen.add(k)
    return dupes


def validate(doc, raw):
    errors, warnings, stats = [], [], {}

    if not isinstance(doc, dict):
        return ["top level is not an object"], warnings, stats
    for key in ("schema", "version", "generated", "products", "categories"):
        if key not in doc:
            errors.append(f"missing required top-level key: {key}")
    if errors:
        return errors, warnings, stats

    if not str(doc.get("schema", "")).endswith(".detail"):
        errors.append(f"schema is not a detail schema: {doc.get('schema')!r}")

    declared = doc.get("categories")
    if not isinstance(declared, list) or not declared:
        errors.append("categories is not a non-empty list")
        declared = []
    for c in declared:
        if c not in ALLOWED_CATEGORIES:
            errors.append(f"category not permitted in this artefact: {c!r}")

    products = doc.get("products")
    if not isinstance(products, dict):
        return errors + ["products is not an object keyed by canonical product id"], warnings, stats

    for d in duplicate_ids(raw):
        errors.append(f"duplicate canonical product id in the file: {d}")

    seen_categories, record_total, value_total = set(), 0, 0
    for pid, rec in products.items():
        if not ID_RE.match(pid or ""):
            errors.append(f"not a canonical Airtable product id: {pid!r}")
            continue
        if not isinstance(rec, dict) or not rec:
            errors.append(f"{pid}: entry is not a non-empty object")
            continue
        for cat, val in rec.items():
            seen_categories.add(cat)
            if cat not in ALLOWED_CATEGORIES:
                errors.append(f"{pid}: unexpected category {cat!r}")
                continue
            if not isinstance(val, dict):
                errors.append(f"{pid}.{cat}: value is not an object")
                continue
            for bad in FORBIDDEN_FIELDS.intersection(val):
                errors.append(f"{pid}.{cat}: Match field must not appear here: {bad}")
            text = val.get("text")
            recs = val.get("records")
            if text is not None and not isinstance(text, str):
                errors.append(f"{pid}.{cat}: text is present but not a string")
            if not (isinstance(text, str) and text.strip()) and recs is None:
                errors.append(f"{pid}.{cat}: no usable text and no records[]")
            if recs is not None:
                if not isinstance(recs, list) or len(recs) < 2:
                    errors.append(f"{pid}.{cat}: records[] must be a list of 2 or more")
                else:
                    for i, one in enumerate(recs):
                        if not isinstance(one, dict):
                            errors.append(f"{pid}.{cat}.records[{i}]: not an object")
                            continue
                        if one.get("text") is not None and not isinstance(one["text"], str):
                            errors.append(f"{pid}.{cat}.records[{i}]: text is not a string")
                        for bad in FORBIDDEN_FIELDS.intersection(one):
                            errors.append(f"{pid}.{cat}.records[{i}]: Match field: {bad}")
                    # D2's rule: the primary is one OF the records, never a
                    # synthesis of them. If it is not among them, the generator
                    # has corrupted the set.
                    if isinstance(text, str) and not any(
                            isinstance(o, dict) and o.get("text") == text for o in recs):
                        errors.append(f"{pid}.{cat}: the primary text is not one of its own records[]")
                    record_total += len(recs)
            else:
                record_total += 1
            value_total += 1

    for c in sorted(seen_categories - set(declared)):
        errors.append(f"category present in the data but not declared: {c!r}")

    # Header counts must agree with the data, or the file is internally corrupt.
    if doc.get("productCount") != len(products):
        errors.append(f"productCount {doc.get('productCount')!r} disagrees with {len(products)} products")
    counts = doc.get("recordCounts")
    if not isinstance(counts, dict):
        errors.append("recordCounts is not an object")
    else:
        for cat in declared:
            got = sum(len(v[cat]["records"]) if isinstance(v.get(cat), dict) and
                      isinstance(v[cat].get("records"), list) else (1 if cat in v else 0)
                      for v in products.values() if isinstance(v, dict))
            if counts.get(cat) != got:
                errors.append(f"recordCounts[{cat}] {counts.get(cat)!r} disagrees with {got}")

    stats = {
        "products": len(products),
        "categoryValues": value_total,
        "evidenceRecords": record_total,
        "rawBytes": len(raw or b""),
        "gzipBytes": len(gzip.compress(raw or b"", 9)),
    }
    return errors, warnings, stats


def materially_same(a, b):
    """`generated` moves every run and is not a change. Nothing else is ignored."""
    def strip(d):
        c = dict(d)
        c.pop("generated", None)
        return c
    return json.dumps(strip(a), sort_keys=True) == json.dumps(strip(b), sort_keys=True)


def validate_index(doc, base_dir, errors):
    """ISSUE 005 PIECE E2 — the partition index.

    The runtime reads this to learn which partitions exist, so it must never
    name a file that is not there, never omit one that is, and never claim a
    category a partition does not declare. Those three are the only ways a
    homeowner could end up fetching a 404 or reading the wrong evidence."""
    if not isinstance(doc, dict) or not str(doc.get("schema", "")).endswith(".detail.index"):
        return ["index: not a detail index document"]
    parts = doc.get("partitions")
    if not isinstance(parts, list) or not parts:
        return ["index: partitions is not a non-empty list"]
    seen = set()
    for p in parts:
        if not isinstance(p, dict):
            errors.append("index: a partition entry is not an object"); continue
        cat, name = p.get("category"), p.get("file")
        if cat not in ALLOWED_CATEGORIES:
            errors.append(f"index: category not permitted: {cat!r}")
        if cat in seen:
            errors.append(f"index: category listed twice: {cat!r}")
        seen.add(cat)
        if not isinstance(name, str) or not name.endswith(".json"):
            errors.append(f"index: partition file name is not a .json path: {name!r}"); continue
        f = Path(base_dir) / name
        if not f.exists():
            errors.append(f"index: names a partition that does not exist: {name}"); continue
        try:
            sub = json.loads(f.read_bytes().decode("utf-8"))
        except Exception as exc:
            errors.append(f"index: partition {name} is not valid JSON — {exc}"); continue
        if sub.get("categories") != [cat]:
            errors.append(f"index: {name} declares {sub.get('categories')!r}, index says {cat!r}")
        if sub.get("productCount") != p.get("productCount"):
            errors.append(f"index: {name} productCount disagrees with the index")
    # Every partition file present on disk must be listed. An unlisted file is
    # evidence the runtime would never fetch — a silent loss, not a saving.
    for f in sorted(Path(base_dir).glob("garden-room-detail-*-v1.json")):
        # Neither the D4b combined artefact nor the index itself is a partition,
        # and both match the same glob. Caught by this validator running against
        # the first generated set — the check was refusing the index for not
        # listing itself.
        if f.name in ("garden-room-detail-evidence-v1.json",
                      "garden-room-detail-index-v1.json"):
            continue
        if f.name not in {p.get("file") for p in parts if isinstance(p, dict)}:
            errors.append(f"index: a partition exists on disk but is not listed: {f.name}")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=None,
                    help="Validate a partition index and every partition it names.")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--production", default=None)
    ap.add_argument("--summary-out", default=None)
    ap.add_argument("--github-output", action="store_true")
    ap.add_argument("--output-prefix", default="detail_",
                    help="Prefix for $GITHUB_OUTPUT keys, so core and detail never collide.")
    args = ap.parse_args()

    errors = []
    cand, cand_raw = load(args.candidate, "candidate", errors)
    prod = None
    if args.production and Path(args.production).exists():
        perr = []
        prod, _ = load(args.production, "production", perr)
        if perr:
            # A damaged PRODUCTION file cannot fail the candidate. It only means
            # we cannot compare, so the candidate is treated as changed.
            print("NOTE: production detail artefact could not be parsed: " + "; ".join(perr))
            prod = None

    stats, warnings = {}, []
    if cand is not None and not errors:
        errors, warnings, stats = validate(cand, cand_raw)

    # ISSUE 005 PIECE E2 — when an index is supplied, every partition it names
    # is validated too, in the same run and under the same exit code. There is
    # no path on which a partition publishes without having been checked.
    if args.index and not errors:
        idx, _ = load(args.index, "index", errors)
        if idx is not None and not errors:
            errors = validate_index(idx, Path(args.index).parent, errors)
            for p in (idx.get("partitions") or []):
                if not isinstance(p, dict) or not isinstance(p.get("file"), str):
                    continue
                pf = Path(args.index).parent / p["file"]
                if not pf.exists():
                    continue
                sub, sub_raw = load(str(pf), f"partition {p['file']}", errors)
                if sub is None:
                    continue
                if sub.get('categories') == ['suppliers']:
                    perr = []
                    validate_supplier(sub, perr)
                    pstats = {'products': len(sub.get('products') or {})}
                else:
                    perr, _, pstats = validate(sub, sub_raw)
                errors += [f"{p['file']}: {e}" for e in perr]
                stats[f"partition_{p['category']}_products"] = pstats.get("products", 0)
                stats[f"partition_{p['category']}_gzipBytes"] = pstats.get("gzipBytes", 0)

    lines = ["GARDEN ROOM DETAIL EVIDENCE — VALIDATION", ""]
    for k in ("products", "categoryValues", "evidenceRecords", "rawBytes", "gzipBytes"):
        if k in stats:
            lines.append(f"  {k:<28}{stats[k]:>12,}")
    for w in warnings:
        lines.append(f"  WARNING  {w}")

    changed = True
    if not errors and prod is not None:
        same = materially_same(cand, prod)
        changed = not same
        lines.append("")
        lines.append("  NO CHANGE — production detail evidence already current"
                     if same else "  CHANGED — production detail evidence will be replaced")
        if same:
            lines.append("  (compared on content; 'generated' is excluded because it moves every run)")
    elif not errors:
        lines.append("")
        lines.append("  No production detail artefact to compare against — treating as CHANGED.")

    lines.append("")
    if errors:
        lines.append(f"  REJECTED — {len(errors)} problem(s). Production is NOT replaced.")
        for e in errors[:25]:
            lines.append(f"    - {e}")
        if len(errors) > 25:
            lines.append(f"    …and {len(errors) - 25} more")
    else:
        lines.append("  VALID — candidate is safe to publish.")

    report = "\n".join(lines)
    print(report)
    if args.summary_out:
        Path(args.summary_out).write_text(report + "\n", encoding="utf-8")

    if args.github_output and os.environ.get("GITHUB_OUTPUT"):
        p = args.output_prefix
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"{p}changed={'true' if (changed and not errors) else 'false'}\n")
            fh.write(f"{p}valid={'true' if not errors else 'false'}\n")
            for k, v in stats.items():
                fh.write(f"{p}{k}={v}\n")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
