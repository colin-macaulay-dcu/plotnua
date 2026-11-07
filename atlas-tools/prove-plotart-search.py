#!/usr/bin/env python3
"""Prove search eligibility and the narrow publishing boundary without network or artist changes."""
import copy
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import plotart_seo as SEO
import plotart_gallery_pages as P
import plotart_shell as S

ROOT = Path(__file__).resolve().parent.parent
launch = SEO.switches()
packages = SEO.public_packages(ROOT)
checks = []


def check(label, condition):
    checks.append(bool(condition))
    print(("PASS " if condition else "FAIL ") + label)


class Head(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.robots, self.canonicals = [], []
        self.feed(text.split("</head>")[0])

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("name", "").lower() in ("robots", "googlebot"):
            self.robots.append(a.get("content"))
        if tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a.get("href"))


for path in SEO.sitemap_paths(packages, launch) + ["mobile-gallery/index.html"]:
    doc = (ROOT / "plotart" / path).read_text()
    h = Head(doc)
    check("public index/canonical: " + path,
          h.robots == ["index, follow"] and h.canonicals == [SEO.canonical(path)])
for path in ("invitation.html", "founding-25.html", "living-gallery.html", "mobile-gallery/gallery.html"):
    h = Head((ROOT / "plotart" / path).read_text())
    check("private or future page stays excluded: " + path,
          h.robots == ["noindex, follow"] and not h.canonicals)

xml = (ROOT / "sitemap.xml").read_text()
ET.fromstring(xml)
check("sitemap generation is idempotent", SEO.update_sitemap(xml, packages, launch) == xml)
check("sitemap is an exact set with no duplicate URLs",
      len(re.findall(r"<loc>", xml)) == len(set(re.findall(r"<loc>(.*?)</loc>", xml))))
check("public A-Z names have real gallery links",
      all('href="../artists/%s/"' % p["artist"]["slug"] in P.artist_index(packages) for p in packages))

future = copy.deepcopy(packages[0])
future["artist"].update(slug="future-test", display_name="Future Test")
future["works"] = future["works"][:1]
pages = P.gallery_pages(future, S.artist_page)
check("a future approved artist inherits indexability and their own canonical",
      all(Head(doc).canonicals == [SEO.canonical(path)] and Head(doc).robots == ["index, follow"]
          for path, doc in pages))
closed = dict(launch, artist_pages_indexable=False)
check("switch off is fail-closed for artist pages",
      SEO.head("artists/future-test/index.html", "Test", "Test", closed) == '<meta name="robots" content="noindex, follow">')
check("a draft export cannot enter the sitemap", not any(p.startswith("artists/future-test/") for p in SEO.sitemap_paths(packages, launch)))
draft = copy.deepcopy(future)
draft["publication"]["state"] = "draft"
try:
    SEO.sitemap_paths([draft], launch)
    check("unapproved input is refused", False)
except ValueError:
    check("unapproved input is refused", True)
archived = copy.deepcopy(future)
archived["works"][0]["availability"] = "archived"
check("archived artwork leaves sitemap", len(SEO.sitemap_paths([archived], launch)) == len(SEO.sitemap_paths([], launch)) + 1)
check("removal leaves no artist or artwork URL", all("/artists/" not in u for u in re.findall(r"<loc>(.*?)</loc>", SEO.sitemap_block([], launch))))

# Exercise the actual content boundary against commits, including unrelated sitemap tampering.
with tempfile.TemporaryDirectory(prefix="pa-search-boundary-") as d:
    site = Path(d)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=site, stderr=subprocess.DEVNULL, text=True).strip()

    def write(path, text):
        dest = site / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)

    def commit():
        git("add", ".")
        git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Test fixture")
        return git("rev-parse", "HEAD")

    def boundary(base, sha, instant=False):
        r = subprocess.run([sys.executable, str(ROOT / "atlas-tools/release/plotart-content-boundary.py"),
                            base, sha] + (["--instant"] if instant else []), cwd=site, capture_output=True, text=True)
        return r.returncode

    git("init", "-q")
    write("atlas-tools/release/plotart-launch-switches.json", json.dumps(launch))
    skeleton = '<urlset><url><loc>https://plotnua.ie/</loc></url>' + SEO.sitemap_block([], launch) + '</urlset>'
    write("sitemap.xml", skeleton)
    base = commit()
    write("plotart/artists/future-test/gallery.json", json.dumps(future))
    write("sitemap.xml", SEO.update_sitemap(skeleton, [future], launch))
    published = commit()
    check("boundary accepts only the generated publish sitemap update", boundary(base, published) == 0)
    write("sitemap.xml", SEO.update_sitemap(skeleton, [future], launch).replace("https://plotnua.ie/</loc>", "https://other.invalid/</loc>"))
    poisoned = commit()
    check("boundary refuses unrelated sitemap changes", boundary(published, poisoned) != 0)
    write("sitemap.xml", SEO.update_sitemap(skeleton, [future], launch).replace(SEO.END, '<url><loc>https://plotnua.ie/plotart/invitation.html</loc></url>' + SEO.END))
    injected = commit()
    check("boundary refuses a private URL injected inside its region", boundary(published, injected) != 0)
    write("sitemap.xml", SEO.update_sitemap(skeleton, [future], launch))
    (site / "plotart/artists/future-test/gallery.json").unlink()
    write("sitemap.xml", SEO.update_sitemap(skeleton, [], launch))
    removed = commit()
    check("boundary accepts removal and exact URL cleanup", boundary(published, removed, instant=True) == 0)

print("PLOTART SEARCH · %d checks, %d passed, %d failed" % (len(checks), sum(checks), len(checks) - sum(checks)))
sys.exit(0 if all(checks) else 1)
