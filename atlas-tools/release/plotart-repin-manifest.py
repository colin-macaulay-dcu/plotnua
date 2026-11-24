#!/usr/bin/env python3
"""Re-pin atlas-tools/release/plotart-launch-manifest.json from the files under ROOT/plotart (three galleries Phase A,
24 Nov 2026). Uses exactly the fingerprints prove-plotart-launch.py L3 checks:

  files                       SHA-256 of every published PlotArt file except artist gallery files (L14 verifies those)
  outside_grid                gallery/index.html with its collection AND Featured Artists regions blanked
  outside_search_content      each generated guide/collection page outside its generated region
  outside_hire_catalogue      the Art for Hire page outside its catalogue
  outside_opportunity_lists   each opportunity-list page outside its lists (and, for Art for Hire, outside its catalogue)

Only the keys a section already pins are re-pinned (no pin is added to or dropped from a section silently); "files" is
re-derived from disk, so a new page must have passed L1 (its allow-list) before it can be pinned.

  python3 atlas-tools/release/plotart-repin-manifest.py ROOT "note to append"            write
  python3 atlas-tools/release/plotart-repin-manifest.py ROOT --check                     list what would change"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import plotart_featured as FEAT  # noqa: E402
import plotart_opportunities as OPP  # noqa: E402
import plotart_search_content as C  # noqa: E402
import plotart_seo as SEO  # noqa: E402

ART_FILE = re.compile(r"^artists/([a-z0-9]+(?:-[a-z0-9]+){0,6})/(?:[a-z0-9]+(?:-[a-z0-9]+){0,6}\.html|gallery\.json|img/[a-z0-9-]+-\d{2,5}\.webp)$")
VG_BEGIN, VG_END = b"<!-- pa-vg-collection:begin -->", b"<!-- pa-vg-collection:end -->"
HIRE_BEGIN, HIRE_END = b"<!-- pa-hire-catalogue:begin -->", b"<!-- pa-hire-catalogue:end -->"
HIRE_PAGE = "art-for-hire/index.html"
sha = lambda b: hashlib.sha256(b).hexdigest()


def outside_hire(raw):
    a, b = raw.find(HIRE_BEGIN), raw.find(HIRE_END)
    if raw.count(HIRE_BEGIN) != 1 or raw.count(HIRE_END) != 1 or not 0 <= a < b:
        raise ValueError("Art for Hire catalogue markers")
    return raw[:a] + HIRE_BEGIN + b"<!-- catalogue -->" + raw[b:]


def outside_grid(raw):
    a, b = raw.find(VG_BEGIN), raw.find(VG_END)
    if raw.count(VG_BEGIN) != 1 or raw.count(VG_END) != 1 or not 0 <= a < b:
        raise ValueError("collection markers")
    raw = raw[:a] + VG_BEGIN + b"<!-- collection -->" + raw[b:]
    return FEAT.outside(raw.decode()).encode()


def main(root, note=None, check=False):
    pa = os.path.join(root, "plotart")
    mp = os.path.join(HERE, "plotart-launch-manifest.json")
    man = json.load(open(mp, encoding="utf-8"))
    files = {}
    for d, _, fs in os.walk(pa):
        for f in fs:
            rel = os.path.relpath(os.path.join(d, f), pa).replace(os.sep, "/")
            if not ART_FILE.match(rel):
                files[rel] = sha(open(os.path.join(d, f), "rb").read())
    new = dict(man)
    new["files"] = dict(sorted(files.items()))
    raw = lambda rel: open(os.path.join(pa, rel), "rb").read()
    new["outside_grid"] = {rel: sha(outside_grid(raw(rel))) for rel in man.get("outside_grid", {})}
    new["outside_search_content"] = {rel: sha(C.outside(raw(rel).decode()).encode()) for rel in man.get("outside_search_content", {})}
    new["outside_hire_catalogue"] = {rel: sha(outside_hire(raw(rel))) for rel in man.get("outside_hire_catalogue", {})}
    oo = {}
    for rel in man.get("outside_opportunity_lists", {}):
        blank = OPP.outside(raw(rel).decode()).encode()
        oo[rel] = sha(outside_hire(blank) if rel == HIRE_PAGE else blank)
    new["outside_opportunity_lists"] = oo
    changed = sorted({k for sec in ("files", "outside_grid", "outside_search_content", "outside_hire_catalogue", "outside_opportunity_lists")
                      for k in set(man.get(sec, {})) | set(new[sec]) if man.get(sec, {}).get(k) != new[sec].get(k)})
    if check:
        print("%d pins would change: %s" % (len(changed), ", ".join(changed)))
        return 1 if changed else 0
    if note:
        new["note"] = man["note"].rstrip() + " " + note
    open(mp, "w", encoding="utf-8").write(json.dumps(new, indent=2, ensure_ascii=False) + "\n")
    print("manifest re-pinned: %d pins changed" % len(changed))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], None if sys.argv[2] == "--check" else sys.argv[2], sys.argv[2] == "--check"))
