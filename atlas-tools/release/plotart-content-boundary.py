#!/usr/bin/env python3
"""PLOTART CONTENT-ONLY BOUNDARY (founder approval in principle, 29 Oct 2026)

    python3 atlas-tools/release/plotart-content-boundary.py BASE REL [--instant]

Decides whether the commits BASE..REL are a CONTENT-ONLY gallery release: the only kind the founder's
admin "Publish" button (or, with --instant, the automatic availability/removal path) may push. Prints
"CONTENT BOUNDARY · OK" and exits 0 only when EVERY changed path is one of:

  plotart/artists/<slug>/index.html | <artwork>.html | img/<name>-<size>.webp   (added, changed or removed)
  plotart/gallery/index.html            only inside the generated collection region
                                        (<!-- pa-vg-collection:begin --> ... <!-- pa-vg-collection:end -->)
  plotart/<buyer guide or artworks/index.html>   only inside its generated collection region, and exactly the
                                        region the approved public exports produce (plotart_search_content)
  image-provenance-records.json         only ARTIST_SUPPLIED_ARTWORK records; every other record and
                                        every other top-level field byte-for-byte unchanged

--instant additionally refuses any new or changed image and any change to an artwork's title, medium,
size, description or price: an instant release may only change availability, remove or reorder.

Anything else (code, styles, templates, other pages, the Worker, privacy wording, launch switches,
the manifest) is a CODE release: it needs the founder's full seven-step approval and is refused here.

Art for Hire (Stage 3B-6). The gallery release above can NEVER touch plotart/art-for-hire/ (refused by name). The hire
page has its own, narrower boundary:

    python3 atlas-tools/release/plotart-content-boundary.py BASE REL --hire [--removals-only]

  --hire           every changed path must be plotart/art-for-hire/index.html, modified (never added or removed), and
                   only inside its generated catalogue region (<!-- pa-hire-catalogue:begin --> ... :end -->). Nothing
                   else at all: no gallery, artist page, record, style, script or switch. Adding the page, its assets
                   or the navigation tab is a CODE release.
  --removals-only  (automatic runs, founder decision D2: withdrawals publish without approval, additions never do) the
                   new region may only drop works: every card left must be byte-identical to a card already there.
Exit codes: 0 content-only; 1 refused; 2 usage or git error.
"""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plotart_seo as SEO
import plotart_search_content as C

ART = re.compile(r"^plotart/artists/([a-z0-9]+(?:-[a-z0-9]+){0,6})/(?:[a-z0-9]+(?:-[a-z0-9]+){0,6}\.html|gallery\.json|img/[a-z0-9-]+-\d{2,5}\.webp)$")
# the generated collection region (Direction C2, 5 Nov 2026): the open galleries and the twenty-five positions
GRID = re.compile(rb'<!-- pa-vg-collection:begin -->.*?<!-- pa-vg-collection:end -->', re.S)
HIRE_PAGE = "plotart/art-for-hire/index.html"
HIRE = re.compile(rb'<!-- pa-hire-catalogue:begin -->.*?<!-- pa-hire-catalogue:end -->', re.S)
HIRE_CARD = re.compile(rb'<li class="pa-hire-card" data-hire-work="[^"]+".*?</li>', re.S)
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


def hire_main(base, rel, removals_only):
    """The Art for Hire catalogue region, and nothing else."""
    git("merge-base", "--is-ancestor", base, rel)
    refused = []
    rows = [l.split("\t") for l in git("diff", "--no-renames", "--name-status", base, rel).splitlines() if l]
    if not rows:
        refused.append("nothing changed")
    for row in rows:
        st, path = row[0], row[-1]
        if path != HIRE_PAGE or st != "M":
            refused.append("%s (%s): outside the Art for Hire boundary (only the hire page's catalogue region may change)" % (path, st))
            continue
        a, b = show(base, path), show(rel, path)
        if len(HIRE.findall(a)) != 1 or len(HIRE.findall(b)) != 1:
            refused.append("%s: the catalogue region markers are missing or repeated" % path)
            continue
        if HIRE.sub(b"<region/>", a) != HIRE.sub(b"<region/>", b):
            refused.append("%s: changed outside the catalogue region" % path)
        if removals_only:
            old, new = HIRE_CARD.findall(HIRE.search(a).group(0)), HIRE_CARD.findall(HIRE.search(b).group(0))
            if any(c not in old for c in new):
                refused.append("%s: a work was added or changed; only withdrawals publish automatically (additions need the founder)" % path)
    if refused:
        print("HIRE BOUNDARY · REFUSED (%d)" % len(refused))
        for x in refused:
            print("  " + x)
        return 1
    print("HIRE BOUNDARY · OK — the Art for Hire catalogue region only%s" % (" (withdrawals only)" if removals_only else ""))
    return 0


def main(base, rel, instant):
    git("merge-base", "--is-ancestor", base, rel)
    refused = []
    rows = [l.split("\t") for l in git("diff", "--no-renames", "--name-status", base, rel).splitlines() if l]
    if not rows:
        refused.append("nothing changed")
    for row in rows:
        st, path = row[0], row[-1]
        if path.startswith("plotart/art-for-hire/"):          # Art for Hire: never through the gallery release (3B-6)
            refused.append("%s (%s): the Art for Hire page is never published by a gallery release (use --hire)" % (path, st))
            continue
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
                refused.append("%s: changed outside the collection region" % path)
            continue
        if path in {"plotart/" + p for p in SEO.GENERATED_PATHS} and st == "M":
            try:
                a, b = show(base, path).decode(), show(rel, path).decode()
                names = git("ls-tree", "-r", "--name-only", rel, "plotart/artists").splitlines()
                packages = [json.loads(show(rel, n)) for n in names if re.fullmatch(r"plotart/artists/[a-z0-9-]+/gallery.json", n)]
                if b != C.update(a, path.removeprefix("plotart/"), packages):
                    refused.append(path + ": differs from the exact public collection update")
            except (ValueError, TypeError) as e:
                refused.append(path + ": " + str(e))
            continue
        if path == "sitemap.xml" and st == "M":
            a, b = show(base, path).decode(), show(rel, path).decode()
            try:
                launch = json.loads(show(rel, "atlas-tools/release/plotart-launch-switches.json"))
                names = git("ls-tree", "-r", "--name-only", rel, "plotart/artists").splitlines()
                packages = [json.loads(show(rel, n)) for n in names if re.fullmatch(r"plotart/artists/[a-z0-9-]+/gallery.json", n)]
                if b != SEO.update_sitemap(a, packages, launch):
                    refused.append("sitemap.xml: differs from the exact generated PlotArt region")
            except (ValueError, TypeError) as e:
                refused.append("sitemap.xml: " + str(e))
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
    if "--hire" in sys.argv:
        sys.exit(hire_main(args[0], args[1], "--removals-only" in sys.argv))
    sys.exit(main(args[0], args[1], "--instant" in sys.argv))
