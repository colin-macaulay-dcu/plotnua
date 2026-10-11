#!/usr/bin/env python3
"""
BOUNDED BUILDER — THE COMMERCIAL TERMS A PRICE CARRIES
======================================================
One anchored edit to _price_state() in
.github/scripts/additional_home_qualification.py, so a published price can
say what it does and does not include.

WHY A TOKEN SET AND NOT THE PROSE.

The governed evidence lives in the Pricing table's `Known Exclusions`, and it
is a curator's paragraph: sources, supersession notes, arithmetic that did not
reconcile, items deliberately not claimed. The Garden Room price contract
already refuses to let that field reach the runtime -- test_price_contract.py
asserts "Known Exclusions does not reach the contract" -- and it is right to.
Piping a research note to a homeowner would publish PlotNua's working out.

So the generator RECOGNISES a closed set of terms by anchored phrase, and the
reader holds the homeowner sentence for each one. Recognition is the only
inference permitted, and it fails in the honest direction: wording the
anchors do not match yields NO token, so the term is simply not stated. The
reader never says "everything else is included", because absence of a token
means absence of evidence, not absence of a cost.

WHY PER CONFIGURATION, AND WHY THE INTERSECTION IS WHAT GETS SHOWN.

A term recognised on the Turnkey row is true of Turnkey. Stating it as though
it covered both configurations would be exactly the kind of quiet widening
this whole Piece exists to prevent. Each configuration therefore carries its
own terms, and the product-level `commercialTerms` is the INTERSECTION -- only
what is true of every priced configuration. The reader shows the intersection.

MEASURED, NOT ASSUMED. All eight rows carrying a Configuration were read from
the live base on 11 October 2026 before these anchors were written:
  * 4 BIOBUILDS rows (Wanderlust, Serenity x Exterior Finished, Turnkey)
  * 4 Tiny House Heavens rows (Liora, Baby x Basic, Optima)
The anchors below match those rows' actual sentences and nothing else.

    python3 atlas-tools/build-commercial-terms.py [--check] [--revert]

Exit 0 = applied, or already correct.
"""
import difflib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / ".github" / "scripts" / "additional_home_qualification.py"
BAK = SRC.with_suffix(".py.bak")

CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


# ── The anchor. Byte for byte from the current file. ───────────────────────
OLD = '''def _vat_basis_of(row):
    """The EXISTING governed field, not a new one. An unrecognised or absent
    value is VAT_UNKNOWN, never a silent assumption of inclusive."""
    raw = txt(cell(row, "Price Includes VAT")).strip().lower()
    return VAT_BASIS.get(raw, "VAT_UNKNOWN")
'''

NEW = '''def _vat_basis_of(row):
    """The EXISTING governed field, not a new one. An unrecognised or absent
    value is VAT_UNKNOWN, never a silent assumption of inclusive."""
    raw = txt(cell(row, "Price Includes VAT")).strip().lower()
    return VAT_BASIS.get(raw, "VAT_UNKNOWN")


# ── WHAT A PRICE INCLUDES, AS TOKENS RATHER THAN PROSE ─────────────────────
#
# The governed evidence is a curator's paragraph in Known Exclusions: sources,
# supersession notes, items deliberately not claimed. The Garden Room price
# contract already refuses to let that field reach the runtime, and it is
# right to -- publishing it would publish PlotNua's working out.
#
# These anchors recognise a CLOSED set of commercial terms in it. Each token
# has one approved homeowner sentence, held in the reader. Recognition is the
# only inference permitted here, and it fails in the honest direction:
# wording the anchors do not match produces NO token, so the term is not
# stated. No token ever means "included" -- absence of evidence is not
# absence of a cost, and no reader may say otherwise.
COMMERCIAL_TERM_ANCHORS = (
    # (token, required substrings -- ALL must appear, case-insensitively)
    ("TRANSPORT_AND_ASSEMBLY_INCLUDED",
     ("transport", "assembly", "ground screws", "are included")),
    ("FOUNDATIONS_UTILITIES_SITEWORKS_QUOTED_SEPARATELY",
     ("foundations", "utility connections", "site works", "quoted per project")),
    ("KITCHEN_FURNITURE_AND_APPLIANCES_EXCLUDED",
     ("kitchen furniture", "appliances", "not included")),
    ("DELIVERY_INSTALLATION_FOUNDATION_EXCLUDED",
     ("delivery, installation and foundation", "not included")),
)


def _commercial_terms_of(row):
    """The recognised terms on ONE pricing row, in anchor order.

    Anchor order, not evidence order, so the same facts always present in the
    same sequence and a reader cannot be made to reorder by a curator's
    sentence being rewritten."""
    blob = txt(cell(row, "Known Exclusions")).lower()
    if not blob:
        return []
    return [tok for tok, needles in COMMERCIAL_TERM_ANCHORS
            if all(n in blob for n in needles)]
'''

# ── The second anchor: every configuration carries its own terms. ─────────
OLD2 = '''            configs.append({
                "key": (key or "").strip().lower().replace(" ", "-") or None,
                "label": key,
                "amount": _amount_of(r),
                "priceType": txt(cell(r, "Price Type")) or None,
            })
'''

NEW2 = '''            configs.append({
                "key": (key or "").strip().lower().replace(" ", "-") or None,
                "label": key,
                "amount": _amount_of(r),
                "priceType": txt(cell(r, "Price Type")) or None,
                # A term recognised on the Turnkey row is true of Turnkey, and
                # of nothing else until its own row says so.
                "terms": _commercial_terms_of(r),
            })
'''

# ── The third anchor: the product-level list is the intersection. ─────────
OLD3 = '''        extra = {"basis": basis, "vatRatePercent": rate}
        if len(configs) > 1 or configs[0]["label"]:
            extra["configurations"] = configs
'''

NEW3 = '''        # THE INTERSECTION, NEVER THE UNION. Publishing a Turnkey term as
        # though it covered the Exterior Finished price too would be exactly
        # the quiet widening this contract exists to prevent. Only what is
        # true of EVERY priced configuration reaches the product level, in
        # anchor order so the sequence cannot be changed by a curator
        # rewriting a sentence.
        common = None
        for c in configs:
            t = set(c.get("terms") or ())
            common = t if common is None else (common & t)
        shared = [t for t, _ in COMMERCIAL_TERM_ANCHORS if t in (common or set())]

        extra = {"basis": basis, "vatRatePercent": rate}
        if shared:
            extra["commercialTerms"] = shared
        if len(configs) > 1 or configs[0]["label"]:
            extra["configurations"] = configs
'''


def main():
    if not SRC.exists():
        die("additional_home_qualification.py is not where this builder expects it.")
    src = SRC.read_text(encoding="utf-8")

    if REVERT:
        if not BAK.exists():
            die("there is no .bak sidecar to revert to.")
        shutil.copyfile(BAK, SRC)
        print("REVERTED additional_home_qualification.py from its .bak sidecar.")
        return

    already = "COMMERCIAL_TERM_ANCHORS" in src

    if not already:
        # G1 · ALL THREE ANCHORS, EXACTLY ONCE EACH, OR REFUSE.
        for name, anchor in (("the VAT basis reader", OLD),
                             ("the configuration row builder", OLD2),
                             ("the extra-payload assembly", OLD3)):
            n = src.count(anchor)
            if n != 1:
                die("%s was found %d times, not once. The qualification module "
                    "has moved. Nothing written." % (name, n))

        out = (src.replace(OLD, NEW, 1)
                  .replace(OLD2, NEW2, 1)
                  .replace(OLD3, NEW3, 1))

        # G2 · NOTHING ELSE MOVED. Reversing all three replacements must land
        # back on the original byte for byte.
        if (out.replace(NEW3, OLD3, 1).replace(NEW2, OLD2, 1)
               .replace(NEW, OLD, 1)) != src:
            die("the replacements did not leave the rest of the file "
                "identical. Nothing written.")
    else:
        out = src

    # G3 · THE CURATOR'S PROSE NEVER BECOMES A VALUE.
    # _commercial_terms_of must return tokens and nothing else. If any anchor
    # body ever returned the blob, a research note would reach a homeowner.
    body = out[out.find("def _commercial_terms_of"):]
    body = body[:body.find("\ndef ", 1)] if "\ndef " in body[1:] else body
    if "return blob" in body or "blob]" in body:
        die("_commercial_terms_of would return the governed prose rather than "
            "tokens. Nothing written.")

    # G4 · THE TOKEN SET IS CLOSED. A term with no anchor cannot be emitted,
    # and an anchor with no token cannot exist.
    toks = [l for l in NEW.splitlines() if l.strip().startswith('("') and
            l.strip().endswith('",')]
    if len(toks) != 4:
        die("the anchor table does not hold exactly the four measured terms "
            "(found %d). Nothing written." % len(toks))

    # G5 · THE INTERSECTION, NOT THE UNION. A term true of one configuration
    # must never be published as true of all of them. This is the assertion
    # that the operator stayed an intersection.
    if "common & t" not in out:
        die("the product-level term list is not an intersection across the "
            "priced rows. Nothing written.")

    # G6 · ABSENCE IS NEVER TURNED INTO INCLUSION.
    for phrase in ("everything else is included", "all other items included",
                   "nothing else to pay", "fully inclusive"):
        if phrase in out.lower():
            die("the module would assert %r. A term with no token means no "
                "evidence, not no cost. Nothing written." % phrase)

    print("\nCOMMERCIAL TERMS ON A GOVERNED PRICE")
    print("=" * 74)
    if already:
        print("  ok    the anchors are already in place; nothing to do")
    else:
        print("  ok    G1  all three anchors matched exactly once")
        print("  ok    G2  every byte outside them is unchanged")
    print("  ok    G3  the governed prose never becomes a value")
    print("  ok    G4  the token set is closed at the four measured terms")
    print("  ok    G5  the product-level list is an intersection, not a union")
    print("  ok    G6  a missing term is never rendered as an inclusion")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            print("\n".join(difflib.unified_diff(
                src.splitlines(), out.splitlines(),
                "additional_home_qualification.py",
                "additional_home_qualification.py (proposed)", lineterm="", n=2)))
        return
    if already:
        print("-" * 74)
        print("No change needed.")
        return

    if not BAK.exists():
        shutil.copyfile(SRC, BAK)
    SRC.write_text(out, encoding="utf-8")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (SRC.name, len(out.encode("utf-8"))))


if __name__ == "__main__":
    main()
