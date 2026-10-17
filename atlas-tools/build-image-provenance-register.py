#!/usr/bin/env python3
"""
BOUNDED BUILDER — THE IMAGE PROVENANCE REGISTER
================================================
Writes image-provenance-records.json from MEASUREMENT: the recovery tool's
findings plus a SHA-256 of every byte on disk.

WHY A SEPARATE FILE FROM image-rights-records.json

Four reasons, and the first is the founder's instruction.

  1. AI illustrations stay out of supplier image-permission records.
  2. That file's source_of_record is "Atlas Core · Image Permission
     Outreach". An AI illustration has no outreach record and never will;
     putting it there would make the file's own declaration false.
  3. The two files answer different questions. Rights records answer MAY WE
     PUBLISH SOMEONE ELSE'S IMAGE. This answers WHAT IS THIS IMAGE.
  4. image-rights-manifest.json is generated from the rights records and
     compared byte-for-byte in CI, with an eleven-sabotage capability proof
     guarding the comparison. Widening that schema to carry a fact that does
     not belong in it would be a large change for no gain.

A SUPPLIER_IMAGE row here carries a POINTER (rights_ref) to the organisation
row that authorises it, and duplicates no permission data. One source of
record; this file never grants anything.

WHAT THE BUILDER REFUSES TO DO

It will not write a classification. Not one. `records` is created empty and
stays empty until a person declares an image from real knowledge, because
after searching the metadata, the git history, the master library and the
masters' own metadata, NOTHING in the published tree carries evidence of what
made it. Writing AI_ILLUSTRATION against 85 garden scenes because they look
generated is exactly the inference the founder forbade, and it is also the
inference that would make this register worthless.

So every asset starts in legacy_undeclared, carrying what WAS recovered --
the master it came from, the Discovery it served, the commit that introduced
it -- so declaring them later is clerical rather than archaeological.

    python3 atlas-tools/build-image-provenance-register.py [--check]
                                                           [--library PATH]

Exit 0 = written, or already correct. Exit 2 = could not measure.
"""
import argparse
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TARGET = ROOT / "image-provenance-records.json"

SCHEMA = "plotnua.image-provenance.records.v1"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def load_recovery(library):
    """Run the recovery tool in-process so the register is built from a fresh
    measurement rather than from a stale side file."""
    spec = importlib.util.spec_from_file_location(
        "rec", HERE / "recover-image-provenance.py")
    mod = importlib.util.module_from_spec(spec)
    argv = sys.argv
    out = pathlib.Path("/tmp/pn-provenance-recovery.json")
    sys.argv = ["recover", "--json", str(out)]
    if library:
        sys.argv += ["--library", library]
    try:
        spec.loader.exec_module(mod)
        mod.main()
    except SystemExit as e:
        if e.code not in (0, None):
            print("the recovery tool exited %s; the register is not built "
                  "from a guess." % e.code)
            sys.exit(2)
    finally:
        sys.argv = argv
    return json.loads(out.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--library", default=None)
    args = ap.parse_args()

    data = load_recovery(args.library)
    rows = data["rows"]
    if not rows:
        die("the recovery found no deployed images at all. Nothing written.")

    # G7 · HASH-BOUND DERIVATIVES ARE CARRIED, NEVER CENSUSED (SEO Phase 1b,
    # 16 Oct 2026). A WebP re-encoding recorded in the existing register's
    # `derivatives` list is the same picture as its source, so it must not
    # enter legacy_undeclared (the ratchet only goes down). It is removed from
    # the census ONLY if its bytes still match the recorded hash; a file that
    # merely looks like a derivative is censused like any other new image.
    prev_derivs = []
    if TARGET.exists():
        try:
            prev_derivs = json.loads(TARGET.read_text(encoding="utf-8")).get("derivatives") or []
        except ValueError:
            prev_derivs = []
    by_hash = {d["asset"]: d["sha256"] for d in prev_derivs if isinstance(d, dict)}
    carried = [r for r in rows if by_hash.get(r["asset"]) == r["sha256"]]
    rows = [r for r in rows if by_hash.get(r["asset"]) != r["sha256"]]
    if len(carried) != len([d for d in prev_derivs if isinstance(d, dict)]):
        missing = sorted(set(by_hash) - {r["asset"] for r in carried})
        die("recorded derivative(s) missing on disk or changed: %s. Nothing written."
            % missing[:4])

    # G1 · NOT ONE ASSET MAY BE CLASSIFIED WITHOUT EVIDENCE.
    classifiable = [r for r in rows
                    if r["embedded_metadata"] or r["master_device_evidence"]]
    if classifiable:
        # If this ever fires it is GOOD NEWS: evidence was found. It is a
        # refusal because the builder must not decide what that evidence
        # means -- a person reads it and declares.
        die("%d asset(s) now carry tool or device evidence. That is a real "
            "finding and a person must read it and declare them, rather than "
            "this builder guessing what it means:\n    %s"
            % (len(classifiable),
               "\n    ".join("%s %s %s" % (r["asset"], r["embedded_metadata"],
                                           r["master_device_evidence"])
                             for r in classifiable[:10])))

    legacy = []
    for r in sorted(rows, key=lambda x: x["asset"]):
        entry = {
            "asset": r["asset"],
            "sha256": r["sha256"],
            "status": "LEGACY_UNDECLARED",
            "bytes": r["bytes"],
            "pixels": r["pixels"],
            "referenced_by": r["referenced_by"],
        }
        if r.get("introduced"):
            entry["introduced"] = r["introduced"]
        if r.get("matched_master"):
            m = r["matched_master"]
            entry["recovered_evidence"] = {
                "master_file": m["path"],
                "discovery_folder": m["discovery_folder"],
                "match": "perceptual, 16x16 average hash, Hamming %d of 256"
                         % m["hamming_distance"],
                "establishes": "which picture this is and which Discovery it "
                               "served",
                "does_not_establish": "what made the picture",
            }
        legacy.append(entry)

    doc = {
        "schema": SCHEMA,
        "what_this_is":
            "What every locally-hosted published image IS. This is NOT a "
            "rights file: image-rights-records.json governs whether PlotNua "
            "may publish someone else's image, and this governs what "
            "PlotNua's own published images are. A SUPPLIER_IMAGE row here "
            "carries a pointer (rights_ref) to that file and duplicates none "
            "of it. Nothing in this file grants any permission.",
        "generated_by": "atlas-tools/build-image-provenance-register.py",
        "guarded_by": "atlas-tools/validate-image-provenance.js",
        "asset_classes": {
            "SUPPLIER_IMAGE":
                "Actual supplier imagery, published under a documented "
                "permission or a valid licence. Carries rights_ref pointing "
                "at the authorising organisation row in "
                "image-rights-records.json.",
            "AI_ILLUSTRATION":
                "Independently generated generic imagery that reproduces no "
                "supplier photograph and no distinctive product design. "
                "Carries the tool, the date, the prompt, an explicit "
                "reference_inputs list and a named human review.",
        },
        "the_third_state": {
            "name": "NO_IMAGE",
            "note":
                "NO_IMAGE is the state of an image SLOT that has no asset. It "
                "is deliberately NOT a class in this register, because a "
                "register of assets cannot hold a record for an image that "
                "does not exist. It is recorded here so the distinction is "
                "explicit: every image slot on a published page resolves to "
                "exactly one of three states, two of which point at a record "
                "in this file and the third of which points at nothing. "
                "NO_IMAGE must stay as easy to choose as the other two -- if "
                "it is not a respectable answer, the pressure is always to "
                "fill the slot with something, and that pressure is how "
                "laundering starts.",
        },
        "rules": [
            "Never use AI to launder a copyrighted image.",
            "AI generation is never evidence of rights. No code path reads "
            "this file to answer a rights question.",
            "Never recreate a supplier photograph.",
            "Never imply an AI illustration depicts a named supplier's actual "
            "product.",
            "An absent term is never an inclusion: an asset with no record is "
            "undeclared, not cleared.",
            "AI illustrations do not appear on individual supplier product "
            "cards. product-card is not an available permitted surface.",
            "Provenance is never inferred from appearance.",
        ],
        "recovery": {
            "performed": "2026-10-11",
            "tool": "atlas-tools/recover-image-provenance.py",
            "instructed_by": "Founder policy implementation, 11 October 2026, "
                             "item 2: recover evidence wherever possible, do "
                             "not invent missing information.",
            "searched": [
                "embedded metadata on all %d deployed assets" % len(rows),
                "every path ever added or deleted across all git branches, "
                "for generation scripts, prompts and source manifests",
                "the master image library outside the repository",
                "embedded metadata on the matched masters",
                "the git commit that introduced each asset",
            ],
            "found": {
                "assets_with_embedded_metadata": 0,
                "generation_scripts_or_prompts_in_history": 0,
                "assets_matched_to_a_named_master": len(
                    [r for r in rows if r.get("matched_master")]),
                "assets_whose_master_shows_a_camera_or_phone": 0,
                "assets_with_evidence_sufficient_to_CLASSIFY": 0,
            },
            "conclusion":
                "Provenance CONTEXT was recovered for %d of %d assets: which "
                "picture each one is, which Discovery it served, and the "
                "commit and date that introduced it. Provenance "
                "CLASSIFICATION was recovered for NONE. No deployed image "
                "carries any evidence of what made it, so no image is "
                "declared. Nine masters in the library DO carry iOS device "
                "evidence and are therefore photographs, but not one of them "
                "is among the assets that shipped."
                % (len([r for r in rows if r.get("matched_master")]), len(rows)),
            "a_fourth_class_may_be_needed":
                "Those nine masters are photographs taken by PlotNua. They "
                "are neither a supplier's image nor an AI illustration, so "
                "the approved three-state taxonomy has no place for a "
                "first-party photograph. None of them is published today, so "
                "nothing is blocked -- but the first one to be published will "
                "need a founder decision rather than a guess. Recorded here "
                "rather than resolved, because inventing a class was not "
                "authorised.",
        },
        "how_to_declare_an_asset": [
            "1. Establish what made the image, from real knowledge. If that "
            "is not available, do not declare it.",
            "2. Move its entry from legacy_undeclared to records, keeping the "
            "asset path and recomputing sha256.",
            "3. For AI_ILLUSTRATION: record tool, date, prompt verbatim, an "
            "explicit reference_inputs array (empty is an assertion, absent "
            "is an unanswered question), depicts_named_product false, "
            "depicts_named_organisation false, a named human_review, and "
            "permitted_surfaces.",
            "4. For SUPPLIER_IMAGE: record rights_ref only. Copy no "
            "permission data.",
            "5. Run atlas-tools/validate-image-provenance.js.",
            "6. Only once records exist may the corresponding page captions "
            "be labelled.",
        ],
        "labels": {
            "AI_ILLUSTRATION": "AI-generated illustration",
            "ILLUSTRATION_VERIFIED_NOT_AI": "Illustration",
            "LEGACY_UNDECLARED": None,
        },
        "label_note":
            "An undeclared asset gets NO label. Inventing a classification to "
            "fill a caption is the error this register exists to prevent, and "
            "no published caption changes until the matching record exists.",
        "legacy_undeclared_note":
            "THE RATCHET. Every asset below is enumerated by path and "
            "sha256. The guard refuses any local image on a published page "
            "that is in neither records nor this list, so no NEW undeclared "
            "image can be added. The count is printed on every CI run and "
            "only ever goes down. A legacy entry is NOT a declaration, is NOT "
            "verified, is NOT authorised supplier imagery, and may not reach "
            "a product card or a supplier context.",
        "records": [],
        "legacy_undeclared": legacy,
    }

    if prev_derivs:
        prev_doc = json.loads(TARGET.read_text(encoding="utf-8"))
        doc["derivatives_note"] = prev_doc.get("derivatives_note")
        doc["derivatives"] = prev_derivs
        print("  ok    G7  %d hash-bound derivative(s) carried, not censused" % len(prev_derivs))

    # G2 · THE REGISTER NEVER GRANTS ANYTHING.
    blob = json.dumps(doc)
    for forbidden in ("permission_outcome", "permitted_domain",
                      "required_credit", "permitted_delivery_hosts"):
        if forbidden in blob:
            die("the register would carry the rights field %r. It must point "
                "at image-rights-records.json, never copy it. Nothing "
                "written." % forbidden)

    # G3 · NOT A SINGLE CLASSIFICATION IS WRITTEN.
    if doc["records"]:
        die("the builder produced %d classified record(s). It must not "
            "classify anything. Nothing written." % len(doc["records"]))

    # G4 · EVERY LEGACY ENTRY CARRIES A PATH AND A REAL HASH.
    for e in legacy:
        # A relative path inside the publish tree. The assets/ prefix is NOT
        # required: eight tracked images live at the repository root --
        # favicon.ico, the favicon sizes, apple-touch-icon, the two
        # android-chrome icons and 404-hidden-discovery -- and an
        # assets/-only assertion was what kept them out of the census.
        if e["asset"].startswith("/") or ".." in e["asset"]:
            die("a legacy entry has an unexpected path %r." % e["asset"])
        if len(e["sha256"]) != 64:
            die("a legacy entry has no usable sha256 (%s)." % e["asset"])

    # G6 · THE EXISTING BACKLOG IS PRESERVED, NOT REWRITTEN.
    # The founder's instruction was to preserve the 101-entry inventory.
    # Widening the census ADDS entries; it must not alter or drop one. Every
    # asset path already recorded must still be present with the same
    # SHA-256, or this refuses.
    if TARGET.exists():
        try:
            prev = json.loads(TARGET.read_text(encoding="utf-8"))
        except ValueError:
            prev = None
        if prev:
            old_rows = {e["asset"]: e.get("sha256")
                        for e in (prev.get("legacy_undeclared") or [])
                        if isinstance(e, dict) and e.get("asset")}
            new_rows = {e["asset"]: e.get("sha256") for e in legacy}
            lost = [a for a in old_rows if a not in new_rows]
            moved = [a for a, h in old_rows.items()
                     if a in new_rows and new_rows[a] != h]
            if lost or moved:
                die("the existing backlog would not be preserved: %d entr(y/ies) "
                    "dropped %s, %d hash(es) changed %s. Nothing written."
                    % (len(lost), lost[:4], len(moved), moved[:4]))
            print("  ok    G6  all %d existing entries preserved; %d added"
                  % (len(old_rows), len(new_rows) - len(old_rows)))

    # G5 · THE BACKLOG IS COMPLETE. Every deployed asset is accounted for
    # exactly once; a backlog with a gap is a hole in the ratchet.
    if len(legacy) != len(rows) or len({e["asset"] for e in legacy}) != len(rows):
        die("the backlog holds %d entries for %d assets. Nothing written."
            % (len(legacy), len(rows)))

    print("\nIMAGE PROVENANCE REGISTER")
    print("=" * 74)
    print("  ok    G1  no asset carries evidence that would permit a "
          "classification")
    print("  ok    G2  the register copies no rights field; it only points")
    print("  ok    G3  zero classifications written")
    print("  ok    G4  every legacy entry has a path and a real SHA-256")
    print("  ok    G5  the backlog accounts for all %d assets exactly once"
          % len(rows))
    print("-" * 74)
    print("  records              0")
    print("  legacy_undeclared    %d" % len(legacy))
    print("  with recovered master context  %d"
          % len([e for e in legacy if e.get("recovered_evidence")]))

    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        print("CHECK ONLY. Nothing written.")
        return
    TARGET.write_text(text, encoding="utf-8")
    print("  wrote %s (%d bytes)" % (TARGET.name, len(text.encode("utf-8"))))


if __name__ == "__main__":
    main()
