#!/usr/bin/env python3
"""PLOTART CONTENT-ONLY BOUNDARY (founder approval in principle, 29 Oct 2026)

    python3 atlas-tools/release/plotart-content-boundary.py BASE REL [--instant]

Decides whether the commits BASE..REL are a CONTENT-ONLY gallery release: the only kind the founder's
admin "Publish" button (or, with --instant, the automatic availability/removal path) may push. Prints
"CONTENT BOUNDARY · OK" and exits 0 only when EVERY changed path is one of:

  plotart/artists/<slug>/index.html | <artwork>.html | img/<name>-<size>.webp   (added, changed or removed)
  plotart/gallery/index.html            only inside the collection grid (<ol class="pa-vg2-grid">)
  image-provenance-records.json         only ARTIST_SUPPLIED_ARTWORK records; every other record and
                                        every other top-level field byte-for-byte unchanged

--instant additionally refuses any new or changed image and any change to an artwork's title, medium,
size, description or price: an instant release may only change availability, remove or reorder.

Anything else (code, styles, templates, other pages, the Worker, privacy wording, launch switches,
the manifest) is a CODE release: it needs the founder's full seven-step approval and is refused here.
Exit codes: 0 content-only; 1 refused; 2 usage or git error.
"""
import json, re, subprocess, sys

ART = re.compile(r"^plotart/artists/([a-z0-9]+(?:-[a-z0-9]+){0,6})/(?:[a-z0-9]+(?:-[a-z0-9]+){0,6}\.html|gallery\.json|img/[a-z0-9-]+-\d{2,5}\.webp)$")
GRID = re.compile(rb'<ol class="pa-vg2-grid"[^>]*>.*?</ol>', re.S)
DETAILS = re.compile(r'class="pa-ag-title">([^<]*)<|class="pa-ag-sub">([^<]*)<|<h1>([^<]*)</h1>|class="pa-aw-dl">(.*?)</dl>|class="pa-aw-desc">([^<]*)<|<img [^>]*src="(img/[^"]+)"', re.S)
PRICES = re.compile(r'class="pa-(?:ag-status|aw-price[^"]*)">(€[^<]*)<')


def instant_ok(a, b):
    """Only availability, removal or order may differ: every detail in the new page already existed, and
    no price changed from one amount to another (a price change is a light-review change)."""
    a, b = (a or b"").decode(), (b or b"").decode()
    old, new = [m.group(0) for m in DETAILS.finditer(a)], [m.group(0) for m in DETAILS.finditer(b)]
    if any(new.count(x) > old.count(x) for x in set(new)):
        return False
    return set(PRICES.findall(b)) <= set(PRICES.findall(a))


def git(*a, binary=False):
    r = subprocess.run(("git",) + a, capture_output=True)
    if r.returncode:
        raise SystemExit("REFUSED: git %s failed: %s" % (" ".join(a), r.stderr.decode(errors="replace").strip()))
    return r.stdout if binary else r.stdout.decode()


def show(rev, path):
    r = subprocess.run(("git", "show", "%s:%s" % (rev, path)), capture_output=True)
    return r.stdout if r.returncode == 0 else None


def main(base, rel, instant):
    git("merge-base", "--is-ancestor", base, rel)
    refused = []
    rows = [l.split("\t") for l in git("diff", "--no-renames", "--name-status", base, rel).splitlines() if l]
    if not rows:
        refused.append("nothing changed")
    for row in rows:
        st, path = row[0], row[-1]
        m = ART.match(path)
        if m:
            if instant and path.endswith(".webp") and st != "D":
                refused.append("%s: a new or changed image is not an instant change (needs review)" % path)
            if instant and path.endswith(".html") and st == "M":
                if not instant_ok(show(base, path), show(rel, path)):
                    refused.append("%s: artwork details changed; only availability, removal or order are instant" % path)
            if instant and path.endswith(".html") and st == "A":
                refused.append("%s: a new page is not an instant change (needs review)" % path)
            continue
        if path == "plotart/gallery/index.html" and st == "M":
            a, b = show(base, path), show(rel, path)
            if GRID.sub(b"<grid/>", a) != GRID.sub(b"<grid/>", b):
                refused.append("%s: changed outside the collection grid" % path)
            continue
        if path == "image-provenance-records.json" and st == "M":
            a, b = json.loads(show(base, path)), json.loads(show(rel, path))
            if {k: v for k, v in a.items() if k != "records"} != {k: v for k, v in b.items() if k != "records"}:
                refused.append("%s: a field other than records changed" % path)
            keep = lambda d: sorted((json.dumps(r, sort_keys=True) for r in d.get("records", []) if r.get("class") != "ARTIST_SUPPLIED_ARTWORK"))
            if keep(a) != keep(b):
                refused.append("%s: a record other than ARTIST_SUPPLIED_ARTWORK changed" % path)
            continue
        refused.append("%s (%s): outside the content-only boundary" % (path, st))
    if refused:
        print("CONTENT BOUNDARY · REFUSED (%d) — this is not a content-only release" % len(refused))
        for x in refused:
            print("  " + x)
        return 1
    print("CONTENT BOUNDARY · OK — %d path(s), content only%s" % (len(rows), " (instant)" if instant else ""))
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    sys.exit(main(args[0], args[1], "--instant" in sys.argv))
