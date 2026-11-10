#!/usr/bin/env python3
"""PlotArt · Art for Hire RELEASE CANDIDATE (Stage 3B-6, development 10 Nov 2026). Builds; never commits, pushes or publishes.

    python3 atlas-tools/release/plotart-hire-release-candidate.py OUT [--catalogue FILE] [--rev REV]

Exports REV (default HEAD) of this repository into the empty folder OUT and prepares there, exactly as the founder's
release step would, the site with Art for Hire switched on:
  1. plotart-launch-switches.json: art_for_hire_page = true (art_for_hire_enquiry_form stays false);
  2. atlas-tools/plotart-hire-nav.py adds the fourth gallery tab to every PlotArt page, plus the scoped style block;
  3. atlas-tools/plotart-hire-page.py builds plotart/art-for-hire/ from the catalogue (default: none listed: the
     empty state) using the approved relay in plotart-gallery-config.json;
  4. the launch manifest is re-pinned for exactly the files this changed, and the three new files are added (the page
     pinned outside its generated catalogue region, as the Artists' Gallery grid is);
  5. the launch guard (L1-L17) runs on OUT with the new switches and manifest and must print PLOTART LAUNCH · OK.
It prints which files changed. The founder reviews OUT; only an approved release copies it to main."""
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "atlas-tools"))
import plotart_search_content as C  # noqa: E402

BEGIN, END = b"<!-- pa-hire-catalogue:begin -->", b"<!-- pa-hire-catalogue:end -->"
VG_BEGIN, VG_END = b"<!-- pa-vg-collection:begin -->", b"<!-- pa-vg-collection:end -->"
sha = lambda b: hashlib.sha256(b).hexdigest()


def blank(raw, a_m, b_m, fill):
    a, b = raw.find(a_m), raw.find(b_m)
    return raw[:a] + a_m + fill + raw[b:]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    out = os.path.abspath(args[0])
    if out == REPO or out.startswith(REPO + os.sep):
        sys.exit("REFUSED: the candidate is built outside the repository")
    if os.path.exists(out) and os.listdir(out):
        sys.exit("REFUSED: %s is not empty" % out)
    os.makedirs(out, exist_ok=True)
    rev = sys.argv[sys.argv.index("--rev") + 1] if "--rev" in sys.argv else "HEAD"
    cat = sys.argv[sys.argv.index("--catalogue") + 1] if "--catalogue" in sys.argv else None
    tar = subprocess.run(["git", "-C", REPO, "archive", rev], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", out], input=tar, check=True)
    rel_dir = os.path.join(out, "atlas-tools", "release")
    sw_p, man_p = os.path.join(rel_dir, "plotart-launch-switches.json"), os.path.join(rel_dir, "plotart-launch-manifest.json")
    pa = os.path.join(out, "plotart")
    before = {}
    for d, _, fs in os.walk(pa):
        for f in fs:
            p = os.path.join(d, f)
            before[os.path.relpath(p, pa)] = sha(open(p, "rb").read())
    sw = json.load(open(sw_p, encoding="utf-8"))
    sw["art_for_hire_page"], sw["art_for_hire_enquiry_form"] = True, False
    json.dump(sw, open(sw_p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(sw_p, "a").write("\n")
    run = lambda *c: subprocess.run([sys.executable] + list(c), capture_output=True, text=True)
    r = run(os.path.join(out, "atlas-tools", "plotart-hire-nav.py"), out)
    if r.returncode:
        sys.exit("navigation step refused:\n" + r.stdout + r.stderr)
    cpath = os.path.join(out, "catalogue.candidate.json")
    json.dump(json.load(open(cat)) if cat else {"generated_at": None, "items": []}, open(cpath, "w"))
    r = run(os.path.join(out, "atlas-tools", "plotart-hire-page.py"), out, "--catalogue", cpath)
    os.remove(cpath)
    if r.returncode:
        sys.exit("page step refused:\n" + r.stdout + r.stderr)
    print(r.stdout.strip())
    man = json.load(open(man_p, encoding="utf-8"))
    changed = []
    for d, _, fs in os.walk(pa):
        for f in fs:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, pa).replace(os.sep, "/")
            raw = open(p, "rb").read()
            if before.get(rel) != sha(raw):
                changed.append(rel)
            if rel in man["files"] or rel.startswith("art-for-hire/"):
                man["files"][rel] = sha(raw)
            if rel in man.get("outside_grid", {}):
                man["outside_grid"][rel] = sha(blank(raw, VG_BEGIN, VG_END, b"<!-- collection -->"))
            if rel in man.get("outside_search_content", {}):
                man["outside_search_content"][rel] = sha(C.outside(raw.decode()).encode())
            if rel == "art-for-hire/index.html":
                man.setdefault("outside_hire_catalogue", {})[rel] = sha(blank(raw, BEGIN, END, b"<!-- catalogue -->"))
    man["note"] += (" Art for Hire release candidate (Stage 3B-6): fourth gallery tab on every PlotArt page, the six-pill style block, "
                    "and plotart/art-for-hire/ (page pinned outside its catalogue region, its stylesheet and script); all other pins retained.")
    json.dump(man, open(man_p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(man_p, "a").write("\n")
    g = subprocess.run([sys.executable, os.path.join(out, "atlas-tools", "prove-plotart-launch.py"), out, "--switches", sw_p, "--manifest", man_p],
                       capture_output=True, text=True)
    print("changed PlotArt files: %d (%s)" % (len(changed), ", ".join(sorted(changed))))
    print((g.stdout + g.stderr).strip().splitlines()[-1] if (g.stdout + g.stderr).strip() else "no guard output")
    if g.returncode or "PLOTART LAUNCH · OK" not in g.stdout:
        print(g.stdout[-3000:])
        sys.exit(1)
    print("RELEASE CANDIDATE · OK — %s" % out)


if __name__ == "__main__":
    main()
