#!/usr/bin/env python3
"""
PlotNua — Garden Room recommendation universe: PRODUCTION VALIDATION GATE.

Stands between a freshly generated candidate and the file the homeowner's
browser actually loads. Nothing reaches production without passing here.

    validate_garden_room_universe.py --candidate CAND [--production PROD]
                                     [--summary-out FILE] [--github-output]
                                     [--min-retained-fraction F]

    exit 0  candidate is valid           exit 1  candidate is REJECTED

WHAT THIS DELIBERATELY DOES NOT DO.

  It does not check that the universe still holds 490 products, or 228 prices,
  or 141 High Confidence records. Those were MEASUREMENTS taken on 3 September
  2026, not laws. Atlas is meant to grow, and a validator that freezes last
  week's counts would block every genuine improvement while catching nothing
  that is actually wrong.

  What it checks instead is that the file is STRUCTURALLY SOUND and
  TRUTHFUL: every record identifiable, every contract field present, every
  value in a vocabulary the runtime understands, and no unknown quietly
  converted into a fact.

  UNKNOWN != FALSE, in both directions. A null price must stay null. An
  unconfirmed Irish availability must not arrive as a confirmation.

THE ONE RELATIVE GUARD, AND WHY IT IS NOT A FROZEN COUNT.

  A candidate holding three perfectly-formed products would pass every
  structural rule above and destroy the homeowner experience. So there is one
  proportional cliff-guard: reject if the candidate retains less than
  --min-retained-fraction of whatever production currently holds (default 0.5).

  It is relative, so it moves as Atlas grows and never needs revising. It
  cannot block growth — only a collapse. If Atlas ever legitimately halves,
  this refuses and asks for a human, which is the correct outcome for a change
  that large. FOUNDER: this threshold is my judgement, not your instruction.
"""
import argparse, gzip, json, math, os, re, sys
from collections import Counter
from pathlib import Path

ATLAS_ID = re.compile(r"^rec[A-Za-z0-9]{14}$")

# Every field the runtime reads. The KEY must be present on every record;
# the VALUE may legitimately be null — that is what "unknown" looks like.
CONTRACT = [
    "id", "name", "organisation", "price", "currency", "priceBasis",
    "floorAreaM2", "glazing", "insulation", "manufactureCountry",
    "designLanguage", "irishAvailability", "irishAvailabilityConfirmationState",
    "availabilityStatus", "noPublishedIrishRoute", "qualificationTier",
    "qualificationCaveats",
]
NEVER_NULL = ("id", "name")

TIERS = {"HIGH_CONFIDENCE", "WITH_CAVEAT", "LIMITED_EVIDENCE"}
CONFIRMATION_STATES = {"Yes", "No", None}
# Declared totals that must agree with the records actually present. This is a
# self-consistency test, not a threshold: it catches a truncated or partially
# written file without caring what the numbers are.
DECLARED = {
    "eligibleCount": lambda ps: len(ps),
    "highConfidenceCount": lambda ps: sum(1 for p in ps if p.get("qualificationTier") == "HIGH_CONFIDENCE"),
    "withCaveatCount": lambda ps: sum(1 for p in ps if p.get("qualificationTier") == "WITH_CAVEAT"),
    "limitedEvidenceCount": lambda ps: sum(1 for p in ps if p.get("qualificationTier") == "LIMITED_EVIDENCE"),
    "noPublishedIrishRouteCount": lambda ps: sum(1 for p in ps if p.get("noPublishedIrishRoute") is True),
}
# Metadata that changes on every run regardless of the data. Excluded from the
# comparison that decides whether to commit — see materially_same().
VOLATILE = ("generated",)


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def load(path, label, errors):
    try:
        raw = Path(path).read_bytes()
    except Exception as e:
        errors.append(f"{label}: cannot be read ({e})")
        return None, None
    if not raw.strip():
        errors.append(f"{label}: file is empty")
        return None, None
    try:
        return json.loads(raw.decode("utf-8")), raw
    except Exception as e:
        # A truncated or half-written file lands here, which is the point.
        errors.append(f"{label}: not valid JSON — {e}")
        return None, raw


def validate(doc, raw, production_count, min_fraction):
    """Returns (errors, warnings, stats). Empty errors means the candidate may ship."""
    errors, warnings = [], []

    if not isinstance(doc, dict):
        return ["top level is not a JSON object"], warnings, {}
    products = doc.get("products")
    if not isinstance(products, list):
        return ["top level has no 'products' array"], warnings, {}
    if not products:
        return ["'products' is empty — a universe with nothing in it is never shippable"], warnings, {}

    for key in ("schema", "qualificationRuleVersion"):
        if not isinstance(doc.get(key), str) or not doc[key].strip():
            errors.append(f"top-level '{key}' is missing or not a string")

    ids, bad_id, dupes = [], [], []
    seen = set()
    for i, p in enumerate(products):
        if not isinstance(p, dict):
            errors.append(f"record {i} is not an object")
            continue
        pid = p.get("id")

        if not isinstance(pid, str) or not ATLAS_ID.match(pid):
            bad_id.append((i, repr(pid)[:40]))
        else:
            if pid in seen:
                dupes.append(pid)
            seen.add(pid)
            ids.append(pid)

        where = pid if isinstance(pid, str) else f"record {i}"

        for f in CONTRACT:
            if f not in p:
                errors.append(f"{where}: contract field '{f}' is absent")
        for f in NEVER_NULL:
            v = p.get(f)
            if not isinstance(v, str) or not v.strip():
                errors.append(f"{where}: '{f}' must be a non-empty string")

        price = p.get("price")
        if price is not None and not is_num(price):
            # A string price, a bool, NaN or Infinity are all coercion damage.
            errors.append(f"{where}: price is neither null nor a finite number ({type(price).__name__}: {repr(price)[:24]})")

        area = p.get("floorAreaM2")
        if area is not None and not is_num(area):
            errors.append(f"{where}: floorAreaM2 is neither null nor a finite number")

        if p.get("noPublishedIrishRoute") is not True and p.get("noPublishedIrishRoute") is not False:
            errors.append(f"{where}: noPublishedIrishRoute must be boolean, got {repr(p.get('noPublishedIrishRoute'))[:24]}")

        tier = p.get("qualificationTier")
        if tier not in TIERS:
            errors.append(f"{where}: qualificationTier '{tier}' is outside the supported vocabulary")

        cs = p.get("irishAvailabilityConfirmationState")
        if cs not in CONFIRMATION_STATES:
            errors.append(f"{where}: irishAvailabilityConfirmationState '{cs}' is not a recognised state")

        ia = p.get("irishAvailability")
        if ia not in (True, False, None):
            errors.append(f"{where}: irishAvailability must be true, false or null")

        # UNKNOWN must not have become a confirmation on the way out.
        if ia is not True and cs == "Yes":
            errors.append(f"{where}: confirmed Irish availability without confirming evidence")

        if not isinstance(p.get("qualificationCaveats"), list):
            errors.append(f"{where}: qualificationCaveats must be a list")

        for f in ("currency", "priceBasis", "manufactureCountry", "designLanguage",
                  "glazing", "insulation", "organisation", "availabilityStatus"):
            v = p.get(f)
            if v is not None and not isinstance(v, (str, list)):
                errors.append(f"{where}: '{f}' should be a string, a list or null")

    if bad_id:
        errors.append(f"{len(bad_id)} record(s) carry no valid canonical Airtable id "
                      f"(first: index {bad_id[0][0]} = {bad_id[0][1]}). "
                      "Synthetic or name-derived identities are never acceptable.")
    if dupes:
        errors.append(f"{len(set(dupes))} duplicate canonical id(s), e.g. {sorted(set(dupes))[:3]}")

    # Self-consistency: the header must describe the body it is attached to.
    for key, fn in DECLARED.items():
        if key in doc:
            actual = fn(products)
            if doc[key] != actual:
                errors.append(f"header '{key}' says {doc[key]} but the records give {actual} "
                              "— the file is internally inconsistent, which is what a truncated write looks like")

    # The one relative guard. Proportional, so it never needs revising.
    if production_count:
        frac = len(products) / production_count
        if frac < min_fraction:
            errors.append(f"candidate retains {len(products)} of production's {production_count} "
                          f"products ({frac:.0%}), below the {min_fraction:.0%} floor. "
                          "A drop this large is not published without a human looking at it.")
        elif frac < 0.9:
            warnings.append(f"candidate holds {len(products)} vs production's {production_count} "
                            f"({frac:.0%}) — a notable fall, allowed but worth a look")

    tiers = Counter(p.get("qualificationTier") for p in products if isinstance(p, dict))
    stats = {
        "products": len(products),
        "uniqueCanonicalIds": len(set(ids)),
        "numericPrices": sum(1 for p in products if isinstance(p, dict) and is_num(p.get("price"))),
        "unknownPrices": sum(1 for p in products if isinstance(p, dict) and p.get("price") is None),
        "irishAvailabilityConfirmed": sum(1 for p in products if isinstance(p, dict) and p.get("irishAvailability") is True),
        "irishAvailabilityUnknown": sum(1 for p in products if isinstance(p, dict) and p.get("irishAvailability") is None),
        "noPublishedIrishRoute": sum(1 for p in products if isinstance(p, dict) and p.get("noPublishedIrishRoute") is True),
        "highConfidence": tiers.get("HIGH_CONFIDENCE", 0),
        "withCaveat": tiers.get("WITH_CAVEAT", 0),
        "limitedEvidence": tiers.get("LIMITED_EVIDENCE", 0),
        "rawBytes": len(raw) if raw else 0,
        "gzipBytes": len(gzip.compress(raw, 9)) if raw else 0,
    }
    return errors, warnings, stats


def materially_same(a, b):
    """Same universe, ignoring metadata that moves on every run.

    The generator stamps 'generated' with the run time, so two runs over
    identical Atlas data are never byte-identical. Comparing raw bytes would
    commit a new file every single day with nothing in it but a new timestamp
    — precisely the churn a change gate exists to prevent. Comparing the
    meaningful content also leaves production's 'generated' reading as the
    moment the DATA last changed, which is the more truthful of the two.
    """
    if a is None or b is None:
        return False
    sa = {k: v for k, v in a.items() if k not in VOLATILE}
    sb = {k: v for k, v in b.items() if k not in VOLATILE}
    return json.dumps(sa, sort_keys=True) == json.dumps(sb, sort_keys=True)


def diff_summary(cand, prod):
    """High-level distribution movement, for the log. Never a pass/fail gate."""
    if not prod:
        return []
    cp = {p["id"]: p for p in cand.get("products", []) if isinstance(p, dict) and isinstance(p.get("id"), str)}
    pp = {p["id"]: p for p in prod.get("products", []) if isinstance(p, dict) and isinstance(p.get("id"), str)}
    added, removed = set(cp) - set(pp), set(pp) - set(cp)
    changed = [i for i in (set(cp) & set(pp)) if cp[i] != pp[i]]
    out = [f"products added   {len(added)}", f"products removed {len(removed)}",
           f"records changed  {len(changed)}"]
    # The fault class this programme exists to stop, reported explicitly.
    coerced = [i for i in (set(cp) & set(pp))
               if pp[i].get("price") is None and cp[i].get("price") == 0]
    if coerced:
        out.append(f"*** {len(coerced)} null price(s) became 0 — inspect before shipping ***")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--production", default=None)
    ap.add_argument("--summary-out", default=None)
    ap.add_argument("--github-output", action="store_true",
                    help="Append changed=true/false to $GITHUB_OUTPUT.")
    ap.add_argument("--min-retained-fraction", type=float, default=0.5)
    args = ap.parse_args()

    errors = []
    cand, cand_raw = load(args.candidate, "candidate", errors)
    prod, prod_raw = (None, None)
    prod_count = 0
    if args.production and Path(args.production).exists():
        perr = []
        prod, prod_raw = load(args.production, "production", perr)
        # A damaged PRODUCTION file must not be able to fail the candidate; it
        # only means we cannot compare. Report it and carry on.
        if perr:
            print("NOTE: production artefact could not be parsed for comparison: " + "; ".join(perr))
        elif isinstance(prod, dict) and isinstance(prod.get("products"), list):
            prod_count = len(prod["products"])

    stats, warnings = {}, []
    if cand is not None and not errors:
        errors, warnings, stats = validate(cand, cand_raw, prod_count, args.min_retained_fraction)

    lines = ["GARDEN ROOM RECOMMENDATION UNIVERSE — VALIDATION", ""]
    if stats:
        for k in ("products", "uniqueCanonicalIds", "numericPrices", "unknownPrices",
                  "irishAvailabilityConfirmed", "irishAvailabilityUnknown",
                  "noPublishedIrishRoute", "highConfidence", "withCaveat",
                  "limitedEvidence", "rawBytes", "gzipBytes"):
            lines.append(f"  {k:<28}{stats[k]:>12,}")
    for w in warnings:
        lines.append(f"  WARNING  {w}")

    changed = True
    if not errors and prod is not None:
        same = materially_same(cand, prod)
        changed = not same
        lines.append("")
        if same:
            lines.append("  NO CHANGE — production universe already current")
            lines.append("  (compared on content; 'generated' is excluded because it moves every run)")
        else:
            lines.append("  CHANGED — production universe will be replaced")
            for d in diff_summary(cand, prod):
                lines.append(f"    {d}")
    elif not errors:
        lines.append("")
        lines.append("  No production artefact to compare against — treating as CHANGED.")

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
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if (changed and not errors) else 'false'}\n")
            fh.write(f"valid={'true' if not errors else 'false'}\n")
            for k, v in stats.items():
                fh.write(f"{k}={v}\n")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
