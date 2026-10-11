#!/usr/bin/env python3
"""
BOUNDED BUILDER — AUTHORISED IMAGERY ON THE ADDITIONAL HOME PATHWAY
====================================================================
Two anchored edits: one to the Additional Home generator, one to the runtime
bridge in your-plot.html.

THE SMALLEST GOVERNED EXTENSION, and it is small because the architecture
already exists.

your-plot.html already carries a complete governed imagery layer, built for
the Garden Room pathway and used by six of its 573 products:

    pnImageRightsOk(im)      refuses an image missing url, credit, supplier,
                             rightsRecord or permittedPrefix, refuses any URL
                             that does not start with that prefix, and refuses
                             anything not https
    pnAuthorisedImage(p)     the primary, re-checked
    pnAuthorisedImages(p)    the whole authorised set, primary forced first
    the shared gallery       Results and Resolve both draw from it, so they
                             cannot disagree about what a product looks like
    presentationTier         the existing tiering

So NOTHING new is written to display an image. The Additional Home payload
gains an `imagery` block in exactly the shape that layer already reads, the
bridge passes it through, and Results, Compare, the hero, the cards and the
gallery all work without being touched. The Garden Room architecture is not
altered, which is the instruction.

WHAT THE GENERATOR WILL AND WILL NOT WRITE

It writes an imagery block ONLY for an asset enumerated in
`approved_assets` on that organisation's rights record, matched to the
product by productCode. Three consequences, each deliberate:

  * an asset on the supplier's domain that is not enumerated produces
    nothing. Approval is by name, not by host.
  * an approved asset whose product_code does not match produces nothing for
    that product. An image cannot drift onto the wrong building.
  * a supplier with no approved_assets produces nothing at all, which is
    every supplier other than BIOBUILDS today.

AND IT NEVER WRITES AN IMAGE FOR A HELD PRODUCT. publicVisibility is computed
first; a product on HOLD gets no imagery block, so the gate and the imagery
cannot disagree.

    python3 atlas-tools/build-additional-home-imagery.py [--check] [--revert]

Exit 0 = applied, or already correct.
"""
import difflib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GEN = ROOT / ".github" / "scripts" / "generate_additional_home_universe.py"
PLOT = ROOT / "your-plot.html"
GEN_BAK = GEN.with_suffix(".py.bak2")
PLOT_BAK = PLOT.with_suffix(".html.bak2")

CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv
SENTINEL = "_approved_imagery"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


# ── GENERATOR · the imagery index, beside the gate it already reads ──────
G_OLD = '''_GATE = None


def publication_hold(org_name):'''

G_NEW = '''# ── AUTHORISED IMAGERY, BY ENUMERATION ────────────────────────────────────
#
# Reads the same canonical rights records the gate above reads. An asset
# reaches a homeowner only by being named in approved_assets AND matching the
# product by productCode. Being served from the supplier's own domain is not
# enough and never was: the manifest scopes by host and prefix, which would
# pass any image on that host, and this is the layer that makes the row
# narrower than the gate would enforce.
#
# The emitted shape is the one your-plot.html's existing governed imagery
# layer already reads for the Garden Room pathway -- url, alt, credit,
# supplier, rightsRecord, permittedPrefix, linkBack, presentationTier -- so
# no display code is written anywhere for this.
_IMAGERY = None


def _imagery_index():
    """productCode -> {primary, set} of authorised images, or {} when none."""
    try:
        doc = json.loads(RIGHTS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        fail("the imagery index could not read image-rights-records.json "
             "(%s). Refusing to generate rather than publish ungoverned "
             "imagery." % e)
    rows = doc if isinstance(doc, list) else next(
        (v for v in doc.values() if isinstance(v, list) and v and
         isinstance(v[0], dict)), [])
    idx = {}
    for r in rows:
        assets = r.get("approved_assets")
        if not isinstance(assets, list) or not assets:
            continue
        org = (r.get("organisation_name") or "").strip()
        prefix = r.get("permitted_domain") or ""
        ref = r.get("atlas_permission_ref") or r.get("organisation_code")
        caption = ((r.get("asset_approval") or {}).get("conditions_on_every_use")
                   or [])
        credit = r.get("required_credit")
        if not (org and ref and credit):
            # A record missing the attribution conditions cannot authorise a
            # public image, whatever its asset list says.
            continue
        for a in assets:
            url = a.get("url") or ""
            code = a.get("product_code")
            alt = a.get("alt")
            if not (url.startswith("https://") and code and alt):
                continue
            # The narrow prefix the asset list itself was built from, not the
            # bare domain: a shared host is never enough to identify one
            # supplier's files.
            media = url[:url.rfind("/") + 1]
            im = {
                "url": url,
                "alt": alt,
                "credit": credit,
                "supplier": org,
                "rightsRecord": ref,
                "permittedPrefix": media,
                "linkBack": "https://www." + prefix.lstrip("www.") + "/"
                            if prefix else None,
                "presentationTier": "A",
                "caption": "BIOBUILDS model imagery" if org == "BIOBUILDS"
                           else None,
            }
            slot = idx.setdefault(code, {"primary": None, "set": []})
            slot["set"].append(im)
            if a.get("primary") and slot["primary"] is None:
                slot["primary"] = im
    # Primary first, always: the hero and the gallery's first frame are then
    # the same picture by construction.
    for code, slot in idx.items():
        if slot["primary"] is None and slot["set"]:
            slot["primary"] = slot["set"][0]
        p = slot["primary"]
        slot["set"] = [p] + [i for i in slot["set"] if i["url"] != p["url"]]
    return idx


def _approved_imagery(product_code, held):
    """The imagery block for this product, or (None, None).

    A HELD product gets nothing. The gate and the imagery cannot be allowed
    to disagree about whether a supplier is public."""
    if held:
        return (None, None)
    global _IMAGERY
    if _IMAGERY is None:
        _IMAGERY = _imagery_index()
    slot = _IMAGERY.get(product_code)
    if not slot:
        return (None, None)
    return (slot["primary"], slot["set"])


_GATE = None


def publication_hold(org_name):'''

# ── GENERATOR · emit it on the product record ────────────────────────────
G2_OLD = '''            "class3a": c3,                       # technical, untouched'''

G2_NEW = '''            "class3a": c3,                       # technical, untouched'''

G3_OLD = '''            "publicVisibility": "HOLD" if hold else "PUBLISHABLE",
            "holdReason": hold,'''

G3_NEW = '''            "publicVisibility": "HOLD" if hold else "PUBLISHABLE",
            "holdReason": hold,
            # Written only for an enumerated approved asset matched to this
            # product code, and never for a held supplier.
            "imagery": _approved_imagery(
                txt(cell(p, "Product Code")) or None, bool(hold))[0],
            "imagerySet": _approved_imagery(
                txt(cell(p, "Product Code")) or None, bool(hold))[1],'''

# ── RUNTIME · the bridge carries it into the existing layer ──────────────
P_OLD = '''      /* Irish availability, in the shape pnIrishConfirmed already reads. */
      irishAvailability: !!(p.irish && p.irish.state === 'CONFIRMED'),'''

P_NEW = '''      /* AUTHORISED IMAGERY, STRAIGHT INTO THE EXISTING GOVERNED LAYER.
         pnImageRightsOk(), pnAuthorisedImage(), pnAuthorisedImages() and the
         shared gallery already refuse an image missing its url, credit,
         supplier, rightsRecord or permittedPrefix, refuse any URL that does
         not begin with that prefix, and refuse anything not https. Passing
         the generator's block through means Results, Compare, the hero, the
         cards and the gallery all work with no new display code, and the
         Garden Room architecture is untouched.
         A product with no authorised asset passes undefined and every
         surface takes its existing no-image path. */
      imagery: p.imagery || undefined,
      imagerySet: (Object.prototype.toString.call(p.imagerySet) === '[object Array]'
                   && p.imagerySet.length) ? p.imagerySet : undefined,
      /* Irish availability, in the shape pnIrishConfirmed already reads. */
      irishAvailability: !!(p.irish && p.irish.state === 'CONFIRMED'),'''


def main():
    for f in (GEN, PLOT):
        if not f.exists():
            die("%s is not where this builder expects it." % f.name)
    gsrc = GEN.read_text(encoding="utf-8")
    psrc = PLOT.read_text(encoding="utf-8")

    if REVERT:
        for bak, target in ((GEN_BAK, GEN), (PLOT_BAK, PLOT)):
            if bak.exists():
                shutil.copyfile(bak, target)
                print("reverted %s" % target.name)
        return

    already = SENTINEL in gsrc and "imagery: p.imagery || undefined" in psrc

    if already:
        gout, pout = gsrc, psrc
    else:
        for name, anchor, src in (("the generator gate tail", G_OLD, gsrc),
                                  ("the product visibility fields", G3_OLD, gsrc),
                                  ("the runtime bridge", P_OLD, psrc)):
            n = src.count(anchor)
            if n != 1:
                die("%s was found %d times, not once. Nothing written."
                    % (name, n))
        gout = gsrc.replace(G_OLD, G_NEW, 1).replace(G3_OLD, G3_NEW, 1)
        pout = psrc.replace(P_OLD, P_NEW, 1)
        if (gout.replace(G3_NEW, G3_OLD, 1).replace(G_NEW, G_OLD, 1) != gsrc
                or pout.replace(P_NEW, P_OLD, 1) != psrc):
            die("reversing the replacements did not reproduce the originals. "
                "Nothing written.")

    # G1 · APPROVAL IS BY ENUMERATION. The index must read approved_assets and
    # must key on the product code.
    if ('r.get("approved_assets")' not in gout
            or 'a.get("product_code")' not in gout):
        die("the imagery index does not read the enumerated approved_assets "
            "keyed by product code. Nothing written.")

    # G2 · A HELD PRODUCT GETS NO IMAGERY. The gate and the imagery must not
    # be able to disagree.
    fn = gout[gout.find("def _approved_imagery"):]
    fn = fn[:fn.find("\n\n\n")]
    if "if held:" not in fn or "return (None, None)" not in fn:
        die("_approved_imagery does not refuse a held product. Nothing "
            "written.")

    # G3 · THE ATTRIBUTION CONDITIONS ARE LOAD-BEARING, not decorative. An
    # organisation without a required_credit cannot authorise a public image.
    if "if not (org and ref and credit):" not in gout:
        die("the index would authorise an image for a record carrying no "
            "credit. Nothing written.")

    # G4 · THE PREFIX IS THE ASSET'S OWN MEDIA PATH, never the bare host.
    # pnImageRightsOk re-checks it at render time, so a widened prefix here
    # would widen what the runtime accepts.
    if 'media = url[:url.rfind("/") + 1]' not in gout:
        die("the permitted prefix is not derived from the asset's own media "
            "path. A bare host would authorise every file on it. Nothing "
            "written.")

    # G5 · NO DISPLAY CODE WAS WRITTEN. The whole point: the runtime change is
    # a pass-through into a layer that already exists.
    # A set, not a list scan: your-plot.html is 2 MB and ~40,000 lines, and
    # the list version of this check made the builder hang.
    before = set(psrc.splitlines())
    added = [l for l in pout.splitlines() if l not in before]
    for banned in ("createElement", "innerHTML", "appendChild", "<img"):
        if any(banned in l for l in added):
            die("the runtime edit writes display code (%r). The existing "
                "governed imagery layer is supposed to do that. Nothing "
                "written." % banned)

    # G6 · AND THE GARDEN ROOM LAYER IS UNTOUCHED.
    for fnname in ("function pnImageRightsOk", "function pnAuthorisedImage",
                   "function pnAuthorisedImages"):
        a = psrc[psrc.find(fnname):]
        a = a[:a.find("\n  }") + 4]
        b = pout[pout.find(fnname):]
        b = b[:b.find("\n  }") + 4]
        if a != b:
            die("%s changed. The Garden Room imagery architecture must not be "
                "altered. Nothing written." % fnname)

    print("\nADDITIONAL HOME AUTHORISED IMAGERY")
    print("=" * 74)
    if already:
        print("  ok    already in place; nothing to do")
    else:
        print("  ok    G0  all three anchors matched once; nothing else moved")
    print("  ok    G1  approval is by enumeration, keyed on product code")
    print("  ok    G2  a held product is given no imagery")
    print("  ok    G3  a record with no credit cannot authorise an image")
    print("  ok    G4  the permitted prefix is the asset's own media path")
    print("  ok    G5  no display code was written in the runtime")
    print("  ok    G6  pnImageRightsOk / pnAuthorisedImage(s) are byte-identical")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            print("\n".join(difflib.unified_diff(
                gsrc.splitlines(), gout.splitlines(),
                "generate_additional_home_universe.py",
                "(proposed)", lineterm="", n=1)))
        return
    if already:
        print("-" * 74)
        print("No change needed.")
        return

    if not GEN_BAK.exists():
        shutil.copyfile(GEN, GEN_BAK)
    if not PLOT_BAK.exists():
        shutil.copyfile(PLOT, PLOT_BAK)
    GEN.write_text(gout, encoding="utf-8")
    PLOT.write_text(pout, encoding="utf-8")
    print("-" * 74)
    print("wrote %s and %s" % (GEN.name, PLOT.name))


if __name__ == "__main__":
    main()
