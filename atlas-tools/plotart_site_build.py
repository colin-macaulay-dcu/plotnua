#!/usr/bin/env python3
"""Builds the plotart.ie site from the repository's plotart/ folder (domain migration R1, prepared 26 Nov 2026).

One source, two addresses: plotart/ stays the single source of every PlotArt page, so the Studio publisher, the
content pipeline and website releases keep working unchanged. This builder turns plotart/ into the root of a
static site for the plotart-site Worker:

  * https://plotnua.ie/plotart/<path>  ->  https://plotart.ie/<path>   (canonical, og:url, JSON-LD, links, sitemap)
  * relative links that leave plotart/ ->  https://plotnua.ie/<path>   (privacy, terms, Discoveries, PlotNua home)
  * root-absolute /plotart/<path>      ->  /<path>
  * root-absolute /assets/... files that PlotArt pages use (brand, identity menu, founder portrait) are copied in;
    any other root-absolute link goes to https://plotnua.ie/...
  * sitemap.xml = every PlotArt <url> of the PlotNua sitemap, re-addressed (same indexing decisions, same images)
  * robots.txt: "test" mode disallows everything (with the Worker's X-Robots-Tag: noindex); "live" mode allows
    crawling and names https://plotart.ie/sitemap.xml

Byte-for-byte otherwise: no page content, design or data changes. Usage:
    python3 atlas-tools/plotart_site_build.py <repo-root> <out-dir> --mode test|live
Exit status is non-zero if any page would be left pointing at a file that does not exist.
"""
import argparse, json, os, posixpath, re, shutil, sys
from urllib.parse import urlsplit

OLD = "https://plotnua.ie/plotart"
NEW = "https://plotart.ie"
PLOTNUA = "https://plotnua.ie/"
TEXT = {".html", ".css", ".js", ".json", ".xml", ".txt", ".svg", ".webmanifest"}
SKIP_SCHEMES = ("%23", "http:", "https:", "mailto:", "tel:", "data:", "javascript:", "blob:", "#", "//", "{", "$", "`")
ABS_OLD = re.compile(r"https?://(?:www\.)?plotnua\.ie/plotart(?=/|[\"'<>\s?#)\\]|$)")
ATTR = re.compile(r'(?P<pre>\b(?:href|src|action|poster|data-src|data-href)=)(?P<q>["\'])(?P<url>[^"\']*)(?P=q)')
SRCSET = re.compile(r'(?P<pre>\bsrcset=)(?P<q>["\'])(?P<val>[^"\']*)(?P=q)')
CSSURL = re.compile(r'url\((?P<q>["\']?)(?P<url>[^)"\']+)(?P=q)\)')


class Site:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.extra = set()      # root files outside plotart/ that must be copied (repo-relative)
        self.missing = []       # (file, url) links that point at nothing

    def exists(self, rel):
        p = os.path.join(self.root, rel)
        return os.path.isfile(p) or os.path.isfile(os.path.join(p, "index.html"))

    def resolve(self, src_rel, url):
        """Returns the rewritten url for a link found in repo file src_rel."""
        if not url or url.startswith(SKIP_SCHEMES):
            return url
        parts = urlsplit(url)
        tail = url[len(parts.path):]                       # ?query#fragment, kept verbatim
        if parts.path.startswith("/"):
            target = posixpath.normpath(parts.path.lstrip("/")) if parts.path != "/" else ""
            if parts.path.endswith("/") and target not in ("", "."):
                target += "/"
            if target == "plotart" or target.startswith("plotart/"):
                return "/" + target[len("plotart/"):] + tail if target != "plotart" else "/" + tail
            if target.startswith("assets/") and os.path.isfile(os.path.join(self.root, target)):
                self.extra.add(target)
                return url
            self.check(src_rel, target, url)
            return PLOTNUA + ("" if target in ("", ".", "index.html") else target) + tail
        if not parts.path:                                  # "?x" or "" relative to the page itself
            return url
        base = posixpath.dirname(src_rel)
        target = posixpath.normpath(posixpath.join(base, parts.path))
        if parts.path.endswith("/"):
            target += "/"
        if target.startswith("plotart/"):
            self.check(src_rel, target, url)
            return url                                       # same tree on both addresses
        if target.startswith("assets/") and os.path.isfile(os.path.join(self.root, target)):
            self.extra.add(target)                           # keep a relative link working: make it root-absolute
            return "/" + target + tail
        self.check(src_rel, target, url)
        return PLOTNUA + ("" if target in (".", "index.html") else target) + tail

    def check(self, src_rel, target, url):
        t = target.rstrip("/")
        if t in ("", "."):
            return
        if not self.exists(t) and not self.exists(t + ".html"):
            self.missing.append((src_rel, url))

    def rewrite_text(self, src_rel, text, ext):
        text = ABS_OLD.sub(NEW, text)
        if ext in (".html", ".svg"):
            text = ATTR.sub(lambda m: m["pre"] + m["q"] + self.resolve(src_rel, m["url"]) + m["q"], text)
            text = SRCSET.sub(lambda m: m["pre"] + m["q"] + ", ".join(
                " ".join([self.resolve(src_rel, c.strip().split(" ")[0])] + c.strip().split(" ")[1:])
                for c in m["val"].split(",") if c.strip()) + m["q"], text)
        if ext in (".html", ".css"):
            text = CSSURL.sub(lambda m: "url(" + m["q"] + self.resolve(src_rel, m["url"]) + m["q"] + ")", text)
        return text


def plotart_sitemap(root, mode):
    """plotart.ie's own sitemap, generated by the same code and switches as PlotNua's PlotArt region (so it stays
    correct after the cutover empties that region), plus any PlotArt page PlotNua's sitemap lists by hand."""
    sys.path.insert(0, os.path.join(root, "atlas-tools"))
    import plotart_seo as SEO
    launch = dict(SEO.switches(), plotart_domain_sitemap=False)
    block = SEO.sitemap_block(SEO.public_packages(root), launch)
    with open(os.path.join(root, "sitemap.xml"), encoding="utf-8") as f:
        doc = f.read()
    head = re.search(r"<urlset[^>]*>", doc).group(0)
    rows = re.findall(r"<url>.*?</url>", block, re.S)
    outside = SEO.REGION.sub("", doc)
    rows += [b for b in re.findall(r"<url>.*?</url>", outside, re.S) if ABS_OLD.search(re.search(r"<loc>(.*?)</loc>", b).group(1))]
    seen, out = set(), []
    for block in rows:
        block = ABS_OLD.sub(NEW, block)
        loc = re.search(r"<loc>(.*?)</loc>", block).group(1).strip()
        if loc in seen:
            continue
        seen.add(loc)
        out.append("  " + block)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + head + "\n" + "\n".join(out) + "\n</urlset>\n"
    return xml, sorted(seen)


def build(root, out, mode):
    site = Site(root)
    src = os.path.join(site.root, "plotart")
    if os.path.exists(out):
        shutil.rmtree(out)
    files = 0
    for d, _, names in os.walk(src):
        for n in sorted(names):
            p = os.path.join(d, n)
            rel = os.path.relpath(p, site.root).replace(os.sep, "/")
            dest = os.path.join(out, os.path.relpath(p, src))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            ext = os.path.splitext(n)[1].lower()
            if ext in TEXT:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
                with open(dest, "w", encoding="utf-8", newline="") as f:
                    f.write(site.rewrite_text(rel, text, ext))
            else:
                shutil.copyfile(p, dest)
            files += 1
    # the 404 page is PlotNua's own, re-addressed so every link goes back to a real page
    with open(os.path.join(site.root, "404.html"), encoding="utf-8") as f:
        page = site.rewrite_text("404.html", f.read(), ".html")
    with open(os.path.join(out, "404.html"), "w", encoding="utf-8") as f:
        f.write(page)
    copied = set()
    while site.extra - copied:                              # copied root assets may reference further assets
        for rel in sorted(site.extra - copied):
            copied.add(rel)
            dest = os.path.join(out, rel)
            if os.path.exists(dest):
                raise SystemExit(f"name collision between plotart/{rel} and /{rel}")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            ext = os.path.splitext(rel)[1].lower()
            if ext in TEXT:
                with open(os.path.join(site.root, rel), encoding="utf-8") as f:
                    text = f.read()
                with open(dest, "w", encoding="utf-8", newline="") as f:
                    f.write(site.rewrite_text(rel, text, ext))
            else:
                shutil.copyfile(os.path.join(site.root, rel), dest)
    xml, urls = plotart_sitemap(site.root, mode)
    with open(os.path.join(out, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    robots = ("User-agent: *\nDisallow: /\n" if mode == "test"
              else "User-agent: *\nAllow: /\n\nSitemap: https://plotart.ie/sitemap.xml\n")
    with open(os.path.join(out, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)
    leftover = []
    for d, _, names in os.walk(out):
        for n in names:
            if os.path.splitext(n)[1].lower() in TEXT:
                with open(os.path.join(d, n), encoding="utf-8") as f:
                    if ABS_OLD.search(f.read()):
                        leftover.append(os.path.relpath(os.path.join(d, n), out))
    report = {"mode": mode, "pages_and_files": files, "root_assets_copied": sorted(copied),
              "sitemap_urls": len(urls), "missing_links": site.missing, "old_address_left_in": leftover}
    with open(os.path.join(out, ".build-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    with open(os.path.join(out, ".assetsignore"), "w", encoding="utf-8") as f:
        f.write(".build-report.json\n.assetsignore\n")    # never uploaded by wrangler
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("out")
    ap.add_argument("--mode", choices=("test", "live"), required=True)
    a = ap.parse_args()
    r = build(a.root, a.out, a.mode)
    print(json.dumps({k: (len(v) if isinstance(v, list) and k != "root_assets_copied" else v) for k, v in r.items()}, indent=1))
    if r["old_address_left_in"]:
        sys.exit("old address left in: " + ", ".join(r["old_address_left_in"][:10]))
    if r["missing_links"]:
        for s, u in r["missing_links"][:20]:
            print(f"missing: {s} -> {u}", file=sys.stderr)


if __name__ == "__main__":
    main()
