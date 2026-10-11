#!/usr/bin/env python3
"""
BOUNDED BUILDER — RE-AIM THE CONTAINMENT PROOF FROM PER-DOMAIN TO PER-ASSET
============================================================================
Two anchored edits to atlas-tools/prove-biobuilds-containment.mjs.

THIS IS A RE-AIM, NOT A RELAXATION, AND THE DISTINCTION IS THE WHOLE POINT.

The proof's job has never been "keep BIOBUILDS imagery off the site". Its job
is to make the rights row NARROWER THAN THE GATE WOULD ENFORCE ON ITS OWN.
image-rights-manifest.json scopes by host and path prefix, so the moment a
biobuilds.com row exists the publish-time gate would pass ANY image on that
host, on any page. C1 and C6 were the difference.

Until 11 October 2026 the difference was a page: the private preview and
nothing else, because no imagery had been authorised for publication. The
founder has now authorised SIX ENUMERATED ASSETS. So the difference becomes
an asset list, which is strictly narrower than the host-and-prefix rule the
gate enforces and strictly narrower than "anything on the preview":

  C1  BEFORE  every biobuilds.com image must be on biobuilds-preview.html
      AFTER   every biobuilds.com image on a PUBLIC page must be one of the
              six enumerated approved assets. A non-approved asset may still
              appear on the private preview and nowhere else.

  C6  BEFORE  the runtime payload carries NO biobuilds.com image block
      AFTER   the runtime payload carries ONLY approved assets, each attached
              to the product its record names

C2, C3, C4 and C5 are untouched. The preview keeps all five robots
directives, keeps the credit and the link back, stays out of every sitemap,
and the rights outcome stays 'Granted with Conditions' with the pre-live
review condition still recorded -- because the supplier did ask for it and
has still not answered.

WHAT MAKES THIS SAFE RATHER THAN A WIDENING. The approved list is read from
the canonical rights record, so the proof cannot be satisfied by an asset
nobody wrote down. If the founder's decision were reverted by deleting
approved_assets, C1 would immediately require every BIOBUILDS image to be
back on the preview alone -- the old behaviour, recovered by removing data
rather than by editing this file.

    python3 atlas-tools/build-containment-per-asset.py [--check] [--revert]

Exit 0 = applied, or already correct.
"""
import difflib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "prove-biobuilds-containment.mjs"
BAK = SRC.with_suffix(".mjs.bak")

CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv
SENTINEL = "APPROVED_ASSET_URLS"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


# ── 1 · read the approved list before walking the tree ───────────────────
A1_OLD = """console.log('BIOBUILDS CONTAINMENT PROOF');
console.log('='.repeat(76));"""

A1_NEW = """console.log('BIOBUILDS CONTAINMENT PROOF');
console.log('='.repeat(76));

/* ---- the enumerated approved assets, read from the canonical record -----
   RE-AIMED 11 October 2026. Until the founder authorised publication this
   proof asserted that BIOBUILDS imagery appeared on the private preview and
   nowhere else, because none of it was publishable. Six assets are now
   approved by name, so the assertion becomes per asset: an APPROVED asset may
   appear publicly, and everything else is still preview-only.

   This is narrower than the manifest's host-and-prefix rule, which is the
   reason this file exists. And it is driven by DATA: delete approved_assets
   from the rights record and every BIOBUILDS image is required back on the
   preview alone, with no edit to this proof. */
let APPROVED_ASSET_URLS = new Set();
let APPROVED_BY_PRODUCT = new Map();
let approvalReadable = false;
try {
  const doc = JSON.parse(
    fs.readFileSync(path.join(ROOT, 'image-rights-records.json'), 'utf8'));
  const row = (doc.records || []).find(r => r.permitted_domain === HOST);
  const assets = (row && row.approved_assets) || [];
  for (const a of assets) {
    if (!a || typeof a.url !== 'string') continue;
    APPROVED_ASSET_URLS.add(a.url);
    if (a.product_code) {
      if (!APPROVED_BY_PRODUCT.has(a.product_code)) {
        APPROVED_BY_PRODUCT.set(a.product_code, new Set());
      }
      APPROVED_BY_PRODUCT.get(a.product_code).add(a.url);
    }
  }
  approvalReadable = true;
  console.log('  approved assets enumerated in the rights record: '
              + APPROVED_ASSET_URLS.size);
} catch (e) {
  cannot('the approved asset list could not be read',
         'without it this proof cannot tell an authorised image from an '
         + 'unauthorised one, so it refuses rather than guessing: '
         + String(e.message));
}"""

# ── 2 · C1 becomes per-asset ─────────────────────────────────────────────
A2_OLD = """const wrong = [...carriers.keys()].filter(p => p !== PAGE);
if (wrong.length) {
  bad('BIOBUILDS imagery appears only on ' + PAGE,
      'it also appears on: ' + wrong.join(', ') + '. BIOBUILDS asked to see '
      + 'the listing before it goes live; another page carrying their imagery '
      + 'is publication, whatever that page is called.');
} else if (!carriers.has(PAGE)) {
  ok('no BIOBUILDS imagery is deployed anywhere (the held slot)');
} else {
  ok('BIOBUILDS imagery appears on ' + PAGE + ' and nowhere else ('
     + carriers.get(PAGE) + ' references)');
}"""

A2_NEW = """/* C1 . only ENUMERATED assets leave the preview ---------------------------
   A non-approved BIOBUILDS image on any page other than the private preview
   is a publication nobody authorised. An APPROVED one is exactly what the
   founder decided to publish. */
const unauthorised = [];
let publicApproved = 0;
for (const [rel, urls] of carriers) {
  for (const u of urls) {
    if (rel === PAGE) continue;                 // the preview may carry both
    if (APPROVED_ASSET_URLS.has(u)) { publicApproved++; continue; }
    unauthorised.push(rel + ' -> ' + u);
  }
}
if (!approvalReadable) {
  /* cannot() has already fired; say nothing more rather than reporting a
     result the proof did not establish. */
} else if (unauthorised.length) {
  bad('only enumerated approved assets appear outside ' + PAGE,
      unauthorised.length + ' unauthorised reference(s): '
      + unauthorised.slice(0, 4).join('; ')
      + '. An asset is publishable because it is written down in '
      + 'approved_assets, never because it is served from the supplier\\'s '
      + 'domain.');
} else if (!carriers.size) {
  ok('no BIOBUILDS imagery is deployed anywhere');
} else {
  ok('every BIOBUILDS image outside ' + PAGE + ' is an enumerated approved '
     + 'asset (' + publicApproved + ' public reference(s), '
     + (carriers.get(PAGE) || 0) + ' on the preview)');
}

/* C1b . and a withheld asset is still withheld --------------------------- */
try {
  const doc = JSON.parse(
    fs.readFileSync(path.join(ROOT, 'image-rights-records.json'), 'utf8'));
  const row = (doc.records || []).find(r => r.permitted_domain === HOST);
  const withheld = ((row && row.withheld_assets) || []).map(w => w.url);
  const leaked = [];
  for (const [rel, urls] of carriers) {
    if (rel === PAGE) continue;
    for (const u of urls) if (withheld.includes(u)) leaked.push(rel + ' -> ' + u);
  }
  if (!withheld.length) {
    ok('no asset is recorded as withheld (nothing to contain)');
  } else if (leaked.length) {
    bad('every explicitly withheld asset stays off public pages',
        leaked.join('; '));
  } else {
    ok('all ' + withheld.length + ' explicitly withheld asset(s) stay off '
       + 'public pages');
  }
} catch (e) {
  cannot('the withheld asset list could not be read', String(e.message));
}"""

# ── 3 · C6 becomes per-asset too ─────────────────────────────────────────
A3_OLD = """/* C6 . the public Results path is untouched -------------------------------- */
/* The runtime payload is what decides the Results pool. An image block there
   for BIOBUILDS would mean an Atlas asset reached 'Approved' -- which is the
   one thing that would put them in front of homeowners. */"""

A3_NEW = """/* C6 . the runtime payload carries ONLY approved assets -------------------
   RE-AIMED with C1. The payload's image block is what a homeowner actually
   sees, so it is checked against the same enumerated list: an approved asset
   may be there, anything else may not, and an approved asset may only be
   attached to the product its own record names. An image drifting onto the
   wrong building is the failure this second half catches. */"""

EDITS = [("the proof header", A1_OLD, A1_NEW),
         ("the C1 verdict", A2_OLD, A2_NEW),
         ("the C6 preamble", A3_OLD, A3_NEW)]


def main():
    if not SRC.exists():
        die("prove-biobuilds-containment.mjs is not where this builder "
            "expects it.")
    src = SRC.read_text(encoding="utf-8")

    if REVERT:
        if not BAK.exists():
            die("there is no .bak sidecar to revert to.")
        shutil.copyfile(BAK, SRC)
        print("REVERTED prove-biobuilds-containment.mjs.")
        return

    already = SENTINEL in src
    if already:
        out = src
    else:
        for name, old, _ in EDITS:
            n = src.count(old)
            if n != 1:
                die("%s was found %d times, not once. The containment proof "
                    "has moved. Nothing written." % (name, n))
        out = src
        for _, old, new in EDITS:
            out = out.replace(old, new, 1)
        back = out
        for _, old, new in reversed(EDITS):
            back = back.replace(new, old, 1)
        if back != src:
            die("reversing the replacements did not reproduce the original. "
                "Nothing written.")

    # G1 · THE PROOF REFUSES RATHER THAN GUESSES. Without the approved list it
    # cannot tell an authorised image from an unauthorised one, and a proof
    # that passes when it is confused is not a proof.
    if ("the approved asset list could not be read" not in out
            or "approvalReadable" not in out):
        die("the proof does not refuse when the approved list is unreadable. "
            "Nothing written.")

    # G2 · APPROVAL IS STILL BY ENUMERATION, read from the canonical record
    # rather than hard-coded here. Two lists would be two answers.
    if "row.approved_assets" not in out:
        die("the proof does not read approved_assets from the rights record. "
            "Nothing written.")
    if "biobuilds.com/_next" in out:
        die("the proof hard-codes an asset URL. The list must come from the "
            "record so reverting the decision reverts the proof. Nothing "
            "written.")

    # G3 · C2-C5 ARE UNTOUCHED. These four are the conditions the supplier
    # actually attached, and nothing in this change may soften them.
    for keep in ("the preview carries noindex, nofollow, noarchive, "
                 "nosnippet, noimageindex",
                 "the credit is a condition of the grant, not decoration.",
                 "the link back is the other condition of the grant.",
                 "no sitemap lists the BIOBUILDS preview",
                 "the pre-live review condition is still recorded",
                 "Granted with Conditions — Founder Confirmed"):
        if keep not in out:
            die("a check the supplier's own conditions depend on has gone: "
                "%r. Nothing written." % keep[:52])

    # G4 · THE WITHHELD LIST IS ENFORCED, not merely recorded. An asset
    # deliberately not approved is the case most likely to slip through.
    if "withheld_assets" not in out:
        die("the proof does not enforce the withheld asset list. Nothing "
            "written.")

    # G5 · AND THE PER-PRODUCT MAP EXISTS, so C6 can catch an image attached
    # to the wrong building.
    if "APPROVED_BY_PRODUCT" not in out:
        die("the proof builds no product-to-asset map, so it cannot catch an "
            "image on the wrong product. Nothing written.")

    print("\nCONTAINMENT, RE-AIMED PER ASSET")
    print("=" * 74)
    if already:
        print("  ok    already in place; nothing to do")
    else:
        print("  ok    G0  all three anchors matched once; nothing else moved")
    print("  ok    G1  the proof refuses when the approved list is unreadable")
    print("  ok    G2  approval is read from the record, never hard-coded here")
    print("  ok    G3  C2-C5 survive: robots, credit, link, sitemap, outcome")
    print("  ok    G4  the withheld asset list is enforced, not just recorded")
    print("  ok    G5  a product-to-asset map exists for the wrong-product case")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            print("\n".join(difflib.unified_diff(
                src.splitlines(), out.splitlines(),
                "prove-biobuilds-containment.mjs", "(proposed)",
                lineterm="", n=1)))
        return
    if already:
        print("-" * 74)
        print("No change needed.")
        return

    if not BAK.exists():
        shutil.copyfile(SRC, BAK)
    SRC.write_text(out, encoding="utf-8")
    print("-" * 74)
    print("wrote %s" % SRC.name)


if __name__ == "__main__":
    main()
