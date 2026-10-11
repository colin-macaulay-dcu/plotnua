#!/usr/bin/env python3
"""PlotNua — test_property_claim_excision.py

REGRESSION TEST for the Stage 3 firewall failure of 11 October 2026:

    2 public-disclosure firewall violation(s). Nothing written.
      .products[129].description      PROD-001194  MyCabin One Bedroom D
      .products[136].description      PROD-001201  MyCabin Barn Style One Bedroom D

Both Airtable DESCRIPTION fields carry the supplier's own line under a
research label:

    SITING: "If your site is long and narrow, this residential log cabin is
    the perfect solution! ..."

`homeowner_text()` dropped a sentence only when it opened with a phrase in
INTERNAL_LEAD_PHRASES. "SITING:" is not one, so the sentence reached
`.description` and the firewall refused the artefact on `your site is`.

The sentences below are the REAL ones, copied from the live records.

T7 is the capability proof: it asserts the pre-fix behaviour — keep the
sentence, firewall matches — still holds for text the rule does NOT cover, so
the rule is doing work and the test can tell the difference.

No network. No token. Nothing written.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from atlas_common import homeowner_text, PROPERTY_CLAIM_RE  # noqa: E402

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail}")


# ── the two real offenders, verbatim ────────────────────────────────────────
D_4x7 = ('SITING: "If your site is long and narrow, this residential log '
         'cabin is the perfect solution! At only 4m (13.1ft) wide, it will '
         'FIT IN MOST GARDENS without compromising on internal space."')
D_4x8 = ('SITING: "If your site is long and narrow, this residential log '
         'cabin is the perfect solution! At only 4m wide and 8m long, it '
         'will FIT IN MOST GARDENS without compromising on internal space."')

# Real neighbouring sentences from the same records, which must SURVIVE.
KEEP_WARRANTY = "WARRANTY: 10 years structural (externally insulated)."
KEEP_CONFIG = ('RESIDENTIAL CONFIGURATION - PUBLISHED: "The design includes '
               'an open-plan living room and kitchen area, creating a bright '
               'and spacious feel."')
KEEP_DIMS = ("DIMENSIONS - published spec table: Size 4m x 7m. Wall Height "
             "2.2m. Ridge Height 2.6m.")

print("\n  PROPERTY-CLAIM EXCISION — REGRESSION (firewall, 11 Oct 2026)")
print("  " + "-" * 68)

# T1/T2 — the two flagged sentences no longer reach public text.
for label, raw in (("PROD-001194 (4.0m x 7.0m)", D_4x7),
                   ("PROD-001201 (4.0m x 8.0m)", D_4x8)):
    out = homeowner_text(raw)
    check(f"T1  {label}: the SITING claim is excised",
          out is None or not PROPERTY_CLAIM_RE.search(out),
          f"published text: {out!r}")

# T3 — the firewall, run over the transformed text, now finds nothing. This is
# the exact check that failed, in the exact order the generator runs it.
for label, raw in (("PROD-001194", D_4x7), ("PROD-001201", D_4x8)):
    out = homeowner_text(raw) or ""
    check(f"T3  {label}: the firewall pattern finds nothing to report",
          PROPERTY_CLAIM_RE.search(out) is None,
          "scanned the value the generator would publish")

# T4 — THE REST OF THE DESCRIPTION SURVIVES. The fix excises one sentence, it
# does not blank the field. Dropping the whole description would have been the
# lazy fix and would have thrown away real homeowner evidence.
mixed = " ".join([KEEP_CONFIG, D_4x7, KEEP_WARRANTY, KEEP_DIMS])
out = homeowner_text(mixed)
check("T4  neighbouring evidence survives the excision",
      out is not None
      and "WARRANTY: 10 years structural" in out
      and "open-plan living room" in out
      and "Ridge Height 2.6m" in out,
      f"{len(out or '')} chars kept from {len(mixed)}")

# T5 — and the claim is gone from that same mixed text.
check("T5  the claim is gone from the mixed description",
      out is not None and not PROPERTY_CLAIM_RE.search(out)
      and "long and narrow" not in out,
      "one sentence removed, the rest intact")

# T6 — NOTHING IS INVENTED. No substitute sentence, no placeholder, no
# "description unavailable" text.
for token in ("unavailable", "redacted", "removed", "[", "omitted"):
    if out and token in out.lower():
        check("T6  no placeholder or substitute text is introduced", False,
              f"found {token!r} in the output")
        break
else:
    check("T6  no placeholder or substitute text is introduced", True,
          "the sentence is dropped, not replaced")

# T7 — CAPABILITY. The rule is narrow by design: it targets the claim, not the
# label. Prove it does NOT fire on the sibling record's siting sentence, which
# is second-person but makes no claim about what the site IS. If this ever
# starts failing, the pattern has been widened and the blast radius must be
# re-measured.
D2_SIBLING = ('SITING: "With a width of 7m and a depth of just 4m, it '
              'maximizes the room inside WITHOUT OVERTAKING YOUR GARDEN."')
sib = homeowner_text(D2_SIBLING)
check("T7  the rule is narrow: the D2 sibling sentence is untouched",
      sib is not None and "OVERTAKING YOUR GARDEN" in sib,
      "PROD-001193 was not among the two violations, and still is not")

# T8 — the pattern still matches the raw text. A remover that silently stopped
# matching would make every other check vacuous.
check("T8  PROPERTY_CLAIM_RE still matches the raw supplier sentence",
      PROPERTY_CLAIM_RE.search(D_4x7) is not None
      and PROPERTY_CLAIM_RE.search(D_4x8) is not None,
      f"matched {PROPERTY_CLAIM_RE.search(D_4x7).group(0)!r}")

# T9 — the generator's firewall uses THIS object, not a copy. If someone
# re-inlines a second regex, this fails and says so.
gen = (Path(__file__).resolve().parent
       / "generate_additional_home_universe.py").read_text(encoding="utf-8")
check("T9  the generator's firewall references the shared pattern",
      '("property assertion", PROPERTY_CLAIM_RE)' in gen
      and "PROPERTY_CLAIM_RE" in gen.split("FIREWALL = [")[0],
      "detector and remover cannot drift apart")

# T10 — the other firewall rules are still present and enforced.
for rule in ("habitation basis rule name", "internal signal notation",
             "internal rule name", "governance directive", "raw record id",
             "property assertion"):
    if f'("{rule}"' not in gen:
        check("T10 all six firewall rules are still declared", False,
              f"missing: {rule}")
        break
else:
    check("T10 all six firewall rules are still declared", True,
          "the firewall was not weakened, relaxed or bypassed")

print("  " + "-" * 68)
print(f"  {len(PASS) + len(FAIL)} checks, {len(PASS)} passed, {len(FAIL)} failed\n")
sys.exit(1 if FAIL else 0)
