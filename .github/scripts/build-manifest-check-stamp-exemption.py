#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER: make the manifest drift check mean what it says.

THE DEFECT. generate_image_rights_manifest.py --check regenerates the manifest
in memory and byte-compares it against the committed file. The regenerated text
carries ("generated", datetime.date.today().isoformat()). So the comparison
includes TODAY'S DATE, and the check can only pass on the single calendar day
the manifest was last regenerated and committed. On every later day it reports
"manifest is up to date: NO -- regenerate" and exits 1, whatever the rights
records say.

That is what failed the publish of 2026-10-04. The manifest was stamped
2026-10-03. Nothing about the rights had changed: 12 records, 11 live grants,
and the row payload byte-identical. The gate refused a manifest that was
correct, for being a day old.

A gate that cries wolf daily is worse than no gate. The team learns to
regenerate reflexively to make CI green, which is exactly the habit that would
wave through a real rights change.

THE FIX, and its limits. --check lifts the COMMITTED manifest's own generated
stamp, re-serialises the fresh manifest with that stamp in place, and then
byte-compares the whole text as before. Everything else stays byte-strict:
key order, indentation, every row, every field, the reality_note and its
supplier list. Only the date is exempt, and only in --check. A real
regeneration still stamps today.

Freshness is NOT lost, because the date check was never where freshness lived.
atlas-tools/validate-image-rights.js reads perms.generated and refuses a
manifest older than --max-age-days (30 in CI). That rule is untouched. The
stamp still has to be real: --check refuses a committed stamp that is missing,
malformed, or dated in the future, because a manifest that lies about its own
age would defeat the staleness rule.

WHAT THIS DOES NOT DO. It does not touch image-rights-records.json,
image-rights-manifest.json, any rights row, any permission outcome, the gate
itself, or anything Atlas. It edits one file: this generator's --check path.

Anchored. Every edit must match exactly once or the builder refuses and writes
nothing.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE / "generate_image_rights_manifest.py"


def die(msg):
    sys.stderr.write("REFUSED: " + msg + "\n")
    raise SystemExit(2)


def anchored(src, old, new, label):
    n = src.count(old)
    if n != 1:
        die("%s: anchor matched %d times, expected exactly 1. The target has "
            "changed since this builder was written; read it before editing."
            % (label, n))
    return src.replace(old, new)


# ---------------------------------------------------------------- edit 1 of 3
# Document the exemption where the next person will read it: in the module
# docstring, beside the other statements of what the generator does and does
# not do.

DOC_OLD = """Run:  python3 .github/scripts/generate_image_rights_manifest.py
      python3 .github/scripts/generate_image_rights_manifest.py --check
\"\"\""""

DOC_NEW = """THE DATE STAMP IS NOT DRIFT. The manifest carries a 'generated' date, and a
regeneration stamps today. --check therefore compares the committed manifest
against a fresh one re-serialised with the COMMITTED stamp, so a manifest whose
rights are correct does not fail for being a day old. Everything else is still
compared byte for byte -- key order, indentation, every row and field. The
stamp must still be real: a missing, malformed or future-dated stamp is
refused, because freshness is enforced from that date by
atlas-tools/validate-image-rights.js (--max-age-days 30), and a manifest that
lied about its own age would defeat it.

Run:  python3 .github/scripts/generate_image_rights_manifest.py
      python3 .github/scripts/generate_image_rights_manifest.py --check
\"\"\""""

# ---------------------------------------------------------------- edit 2 of 3
# The check itself.

CHECK_OLD = """    text = json.dumps(out, indent=2, ensure_ascii=False) + "\\n"
    if CHECK_ONLY:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        same = current == text
        print("VALIDATED %d record(s), %d live grant(s)" % (len(records), len(live)))
        print("manifest is up to date: " + ("YES" if same else "NO — regenerate"))
        return 0 if same else 1
"""

CHECK_NEW = """    text = json.dumps(out, indent=2, ensure_ascii=False) + "\\n"
    if CHECK_ONLY:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        print("VALIDATED %d record(s), %d live grant(s)" % (len(records), len(live)))

        # Compare against the committed manifest re-stamped with ITS OWN date,
        # so a correct manifest does not fail merely for being a day old. The
        # stamp is the ONLY exemption, and it must be a real past date: see
        # stamp_of() for why.
        stamp, why = stamp_of(current)
        if stamp is None:
            print("manifest is up to date: NO — regenerate (" + why + ")")
            return 1
        out["generated"] = stamp
        expected = json.dumps(out, indent=2, ensure_ascii=False) + "\\n"

        same = current == expected
        print("manifest generated " + stamp
              + "; freshness is enforced by validate-image-rights.js"
              + " --max-age-days")
        print("manifest is up to date: " + ("YES" if same else "NO — regenerate"))
        return 0 if same else 1
"""

# ---------------------------------------------------------------- edit 3 of 3
# The helper. Placed immediately before main() so it reads in order.

HELPER_OLD = """def main():"""

HELPER_NEW = """def stamp_of(current):
    \"\"\"The committed manifest's own 'generated' date, or (None, reason).

    The date is exempt from the drift comparison, so it has to be checked on
    its own terms instead. A stamp that is missing, malformed, or dated in the
    future would defeat the staleness rule in validate-image-rights.js, which
    computes the manifest's age FROM THIS FIELD -- a manifest stamped next year
    would read as perpetually fresh. Each of those is refused here, where the
    message can say what to do, rather than in CI.
    \"\"\"
    if not current.strip():
        return None, "no committed manifest to compare against"
    try:
        stamp = json.loads(current).get("generated")
    except ValueError:
        return None, "the committed manifest is not readable JSON"
    if not isinstance(stamp, str) or not stamp:
        return None, "the committed manifest has no generated date"
    try:
        when = datetime.date.fromisoformat(stamp)
    except ValueError:
        return None, "the generated date is not a plain ISO date: " + stamp
    if when > datetime.date.today():
        return None, ("the generated date is in the future: " + stamp
                      + ". A manifest cannot be stamped ahead of itself; that "
                      + "would read as perpetually fresh.")
    return stamp, None


def main():"""


def build():
    if not TARGET.exists():
        die("target not found: " + str(TARGET))

    before = TARGET.read_text(encoding="utf-8")

    # Refuse to run twice. Idempotence by refusal, not by silent no-op: a
    # builder that quietly does nothing is indistinguishable from one that
    # worked.
    if "def stamp_of(" in before:
        die("the target already carries stamp_of(); this builder has already "
            "been applied. Nothing written.")

    src = before
    src = anchored(src, DOC_OLD, DOC_NEW, "edit 1/3 docstring")
    src = anchored(src, CHECK_OLD, CHECK_NEW, "edit 2/3 --check comparison")
    src = anchored(src, HELPER_OLD, HELPER_NEW, "edit 3/3 stamp_of helper")

    if src == before:
        die("no change produced; refusing to claim a build")

    TARGET.write_text(src, encoding="utf-8")
    print("WROTE " + str(TARGET))
    print("  %d bytes -> %d bytes" % (len(before.encode()), len(src.encode())))
    print("  3 anchored edits, each matched exactly once")


if __name__ == "__main__":
    build()
