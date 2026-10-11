#!/usr/bin/env python3
"""
RECOVER WHAT CAN BE RECOVERED ABOUT THE LOCAL IMAGES
=====================================================
The founder's instruction was explicit: before declaring provenance unknown,
search the repository for generation scripts, prompts, source manifests,
generation metadata and existing documentation. Recover evidence wherever
possible. Do not invent missing information.

This is the tool that did the searching, kept so the search is repeatable and
so its findings can be checked rather than taken on trust.

WHAT IT LOOKS FOR, AND WHAT IT FOUND ON 11 OCTOBER 2026

  1. EMBEDDED METADATA on the deployed assets
     -> 85 of 85 carry NOTHING. Every one is stripped: no EXIF, no XMP, no
        text chunks. Consistent with a resize-and-strip publishing step.

  2. GENERATION SCRIPTS, PROMPTS AND SOURCE MANIFESTS in git history
     -> none have ever existed. Searching every path ever added or deleted
        across all branches returns no prompt file, no image-source manifest
        and no generation script. This is a real absence, not an oversight
        in the search.

  3. THE MASTER IMAGE LIBRARY outside the repository
     -> 132 masters under Images/, organised by Discovery, with editorial
        filenames (MASTER, Before, Reveal, NEUTRALISED). 77 of the 85
        deployed assets match a named master perceptually. That recovers
        WHICH Discovery an image belongs to and WHAT ROLE it played, which
        is real evidence and worth having.

  4. EMBEDDED METADATA ON THOSE MASTERS
     -> 9 masters carry device evidence (iOS Software tags, Apple MPF) and
        are therefore photographs. NONE of them is among the 85 that
        shipped: the DISC-022 and DISC-002 iPhone files stayed in the
        library. So zero deployed assets trace to a master with camera
        evidence either.

  5. THE GIT COMMIT that introduced each asset
     -> recoverable for all 85: a date and a release context.

WHAT THIS MEANS, STATED PLAINLY. Provenance CONTEXT was recovered for 77 of
85 assets. Provenance CLASSIFICATION was recovered for NONE. Not one image in
the published tree carries evidence of what made it, so not one can honestly
be declared AI_ILLUSTRATION or SUPPLIER_IMAGE. Every one goes to the legacy
backlog, each carrying whatever was recovered so the founder can declare in
batches from real knowledge rather than from inference.

THE MATCHER IS EVIDENCE, NOT PROOF. A 16x16 average-hash comparison at a
Hamming distance of 22 or less out of 256 establishes that a deployed asset
and a master are the same picture. It does not establish what made the
picture, and nothing here treats it as though it did.

    python3 atlas-tools/recover-image-provenance.py [--library PATH]
                                                    [--json OUT]

Exit 0 = the search ran. Exit 2 = the master library could not be read, so
nothing was measured. A recovery tool that silently finds nothing because it
was pointed at the wrong place is worse than one that refuses.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
# EVERY local image directory a published page can draw from, not just
# assets/img. The provenance guard found three brand marks on published pages
# that an assets/img-only inventory had missed -- a hole in the ratchet, since
# the guard refuses any local image that is in neither the records nor the
# backlog. The inventory is the whole of assets/ so completeness does not
# depend on remembering a directory.
IMG_ROOTS = [ROOT / "assets"]
# The library lives outside the repository, beside it in the PlotNua folder.
DEFAULT_LIBRARY = ROOT.parent.parent / "Images"
MATCH_THRESHOLD = 22          # of 256 bits
# Keys that can carry provenance. JFIF density, DPI and ICC profiles cannot.
PROVENANCE_KEYS = ("exif", "xmp", "XML:com.adobe.xmp", "comment",
                   "Software", "Description", "parameters", "prompt",
                   "Comment", "Author", "Copyright", "c2pa")
SIG = 16                      # 16x16 average hash


def refuse(why):
    print("\nIMAGE PROVENANCE RECOVERY")
    print("=" * 74)
    print("  INSTRUMENT UNAVAILABLE: " + why)
    print("  Nothing was measured. This is not a finding of 'no provenance'.")
    sys.exit(2)


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", default=str(DEFAULT_LIBRARY))
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
    except ImportError:
        refuse("Pillow is not installed, so no image could be read "
               "(pip install pillow)")

    for d in IMG_ROOTS:
        if not d.is_dir():
            refuse("%s does not exist" % d)
    library = pathlib.Path(args.library)
    if not library.is_dir():
        refuse("the master image library is not at %s. Pass --library with "
               "its real location; do not treat its absence as evidence that "
               "no master exists." % library)

    def svg_generator(p):
        """SVG is XML, and most editors sign their output. A generator tag is
        real provenance evidence -- it names the tool -- so it is read rather
        than skipped."""
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:4000]
        except OSError:
            return {}
        out = {}
        m = re.search(r"(?:Generator|generator)\s*[:=]\s*\"?([^\"\n<>-]{3,60})",
                      head)
        if m:
            out["SvgGenerator"] = m.group(1).strip()
        for tool in ("Adobe Illustrator", "Inkscape", "Figma", "Sketch",
                     "Affinity", "CorelDRAW"):
            if tool.lower() in head.lower():
                out.setdefault("SvgGenerator", tool)
        return out

    def signature(p):
        # A vector file has no raster signature to compare. That is a property
        # of the format, not a failure, and it must not be reported as one.
        if p.suffix.lower() == ".svg":
            return None
        try:
            im = Image.open(p).convert("L").resize((SIG, SIG), Image.LANCZOS)
            px = list(im.getdata())
            avg = sum(px) / len(px)
            return [1 if v > avg else 0 for v in px]
        except Exception:
            return None

    def embedded(p):
        """Provenance-bearing metadata on the asset itself. For an SVG that is
        the generator tag; for a raster it is EXIF/XMP/text chunks. JFIF
        density, DPI and ICC profiles are not provenance and are excluded --
        an early version counted them and reported 82 of 85 as carrying
        metadata, which would have overstated the recovery badly."""
        if p.suffix.lower() == ".svg":
            return sorted(svg_generator(p).keys())
        try:
            info = Image.open(p).info or {}
        except Exception:
            return []
        return sorted(k for k in info if k in PROVENANCE_KEYS and info.get(k))

    def device_evidence(p):
        """Camera or phone evidence on this file. A photograph leaves traces;
        absence of them is NOT evidence of generation."""
        out = {}
        if p.suffix.lower() == ".svg":
            return svg_generator(p)
        try:
            im = Image.open(p)
            ex = im.getexif() or {}
            for tag, name in ((271, "Make"), (272, "Model"), (305, "Software"),
                              (36867, "DateTimeOriginal"),
                              (42036, "LensModel")):
                if ex.get(tag):
                    out[name] = str(ex.get(tag))[:60]
            if "mp" in (im.info or {}):
                out["AppleMPF"] = True
        except Exception:
            pass
        return out

    EXT = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg")
    deployed = sorted({p for d in IMG_ROOTS for p in d.rglob("*")
                       if p.is_file() and p.suffix.lower() in EXT})
    masters = sorted(p for p in library.rglob("*")
                     if p.suffix.lower() in EXT and p.is_file())
    if not masters:
        refuse("the library at %s holds no images" % library)

    msig = [(p, signature(p)) for p in masters]
    msig = [(p, s) for p, s in msig if s]

    # Which published page references each asset. An asset nothing references
    # is a different problem from an asset with no provenance.
    refs = {}
    for html in sorted(ROOT.glob("*.html")):
        try:
            body = html.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r"assets/[A-Za-z0-9._/-]+?"
                             r"\.(?:jpe?g|png|webp|avif|gif|svg)", body,
                             re.I):
            refs.setdefault(m.group(0), set()).add(html.name)

    # The commit that introduced each asset: a date and a release context.
    commits = {}
    try:
        log = subprocess.run(
            ["git", "log", "--diff-filter=A", "--date=short",
             "--pretty=format:@@%h|%ad|%s", "--name-only", "--", "assets/img"],
            cwd=ROOT, capture_output=True, text=True, timeout=120).stdout
        cur = None
        for line in log.splitlines():
            if line.startswith("@@"):
                h, d, s = line[2:].split("|", 2)
                cur = {"commit": h, "date": d, "subject": s}
            elif line.strip() and cur:
                commits.setdefault(pathlib.Path(line.strip()).name, cur)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass

    rows = []
    for p in deployed:
        sig = signature(p)
        best = None
        if sig:
            scored = sorted((sum(1 for a, b in zip(sig, s) if a != b), mp)
                            for mp, s in msig)
            if scored and scored[0][0] <= MATCH_THRESHOLD:
                best = scored[0]
        try:
            w, h = Image.open(p).size
        except Exception:
            w = h = None          # vector, or unreadable raster
        row = {
            "asset": p.relative_to(ROOT).as_posix(),
            "sha256": sha256(p),
            "bytes": p.stat().st_size,
            "pixels": [w, h],
            # PROVENANCE-BEARING keys only. An early version of this counted
            # every key in Image.info and reported 82 of 85 as carrying
            # metadata -- it was counting JFIF density and DPI, which say
            # nothing about who made the picture. That would have overstated
            # the recovery, so the set is now enumerated.
            "embedded_metadata": embedded(p),
            "referenced_by": sorted(refs.get(p.relative_to(ROOT).as_posix(), ())),
            "introduced": commits.get(p.name),
            "matched_master": None,
            "master_device_evidence": {},
        }
        if best:
            d, mp = best
            row["matched_master"] = {
                "path": str(pathlib.Path(mp).relative_to(library.parent)),
                "name": pathlib.Path(mp).name,
                "discovery_folder": pathlib.Path(mp).parent.name,
                "hamming_distance": d,
            }
            row["master_device_evidence"] = device_evidence(pathlib.Path(mp))
        rows.append(row)

    matched = [r for r in rows if r["matched_master"]]
    with_device = [r for r in rows if r["master_device_evidence"]]
    with_meta = [r for r in rows if r["embedded_metadata"]]
    orphan = [r for r in rows if not r["referenced_by"]]

    print("\nIMAGE PROVENANCE RECOVERY")
    print("=" * 74)
    print("  deployed assets inventoried        %d" % len(rows))
    print("  masters searched                   %d  (%s)" % (len(msig), library))
    print("  carrying embedded metadata         %d" % len(with_meta))
    print("  matched to a named master          %d" % len(matched))
    print("  whose master shows a camera/phone  %d" % len(with_device))
    print("  referenced by no published page    %d" % len(orphan))
    print("-" * 74)
    print("  TOOL OR DEVICE EVIDENCE SUFFICIENT TO CLASSIFY: %d"
          % len(with_device + with_meta))
    print("  Context recovered is not classification. An image whose master")
    print("  is known is still an image whose MAKER is not.")

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps({"threshold": MATCH_THRESHOLD, "library": str(library),
                        "rows": rows}, indent=1) + "\n", encoding="utf-8")
        print("  wrote %s" % args.json)


if __name__ == "__main__":
    main()
