#!/usr/bin/env python3
"""Every Discovery hero slider opens on the complete BEFORE image (founder directive, 30 Oct 2026).

    python3 atlas-tools/build-hero-start-before.py          apply
    python3 atlas-tools/build-hero-start-before.py --check  verify, write nothing

For every published page with a pn-compare HERO (figure.pn-compare--hero):
  * data-start="100" and the range input value="100" (100 = the whole frame shows BEFORE);
  * the static aria-valuetext reads as the script will at 100 ("Showing <subject> before", or
    "Showing <say-before>" where the page sets data-say-before);
  * loading priority moves to what is seen first: fetchpriority="high" on the BEFORE <img>, none on
    POSSIBLE, and the page's hero image preload(s) point at the BEFORE files instead (same types, media,
    srcset widths and sizes), so the opening image is not delayed and POSSIBLE is never the first paint;
  * the pn-compare stylesheet and script links move to ?v=1.3 (v1.3 shows BEFORE from the first paint
    and keeps the handle inside the frame at the edges).
Nothing else on any page changes. Without JavaScript the POSSIBLE picture (with its alt text) remains the
static image, as before. Inline comparisons (pn-compare--inline) are not hero sliders and are untouched.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv


def picture(fig, layer):
    m = re.search(r'<div class="pn-compare__%s">\s*<picture>([\s\S]*?)</picture>' % layer, fig)
    return m.group(1)


def urls(pic):
    out = []
    for s in re.findall(r'<source\b[^>]*>', pic):
        out += [u.strip().split(" ")[0] for u in re.search(r'srcset="([^"]+)"', s).group(1).split(",")]
    out.append(re.search(r'<img\b[^>]*\bsrc="([^"]+)"', pic).group(1))
    return out


def transform(t, name):
    fm = re.search(r'<figure class="pn-compare pn-compare--hero"[^>]*>[\s\S]*?</figure>', t)
    if not fm:
        return t
    fig = fm.group(0)
    pos, bef = picture(fig, "possible"), picture(fig, "before")
    pu, bu = urls(pos), urls(bef)
    # same <source> structure: map file for file; otherwise (a JPEG-only layer, e.g. a held source) map
    # only the fallback <img>, and the JPEG preload below is rebuilt from the BEFORE's WebP set
    swap = dict(zip(pu, bu)) if len(pu) == len(bu) else {pu[-1]: bu[-1]}
    subject = (re.search(r'data-subject="([^"]+)"', fig) or [None, "the property"])[1]
    sb = re.search(r'data-say-before="([^"]+)"', fig)
    vt = "Showing " + (sb.group(1) if sb else subject + " before")
    new = fig.replace('data-start="35"', 'data-start="100"', 1)
    new = re.sub(r'(<input class="pn-compare__range"[^>]*?)value="35"', r'\1value="100"', new, count=1)
    new = re.sub(r'aria-valuetext="[^"]*"', 'aria-valuetext="%s"' % vt, new, count=1)
    if 'aria-valuetext=' not in new:
        new = re.sub(r'(<input class="pn-compare__range"[^>]*?)>', r'\1 aria-valuetext="%s">' % vt, new, count=1)
    # priority: BEFORE high, POSSIBLE default
    p_old, b_old = picture(new, "possible"), picture(new, "before")
    p_new = p_old.replace(' fetchpriority="high"', '', 1)
    b_new = re.sub(r'(<img\b)(?![^>]*fetchpriority)', r'\1 fetchpriority="high"', b_old, count=1)
    new = new.replace(p_old, p_new, 1).replace(b_old, b_new, 1)
    t = t.replace(fig, new, 1)
    # hero preloads: point at the BEFORE files
    def pre(m):
        tag = m.group(0)
        hit = [u for u in swap if u in tag]
        if not hit:
            return tag
        for u in sorted(hit, key=len, reverse=True):
            tag = tag.replace(u, swap[u])
        return tag
    t = re.sub(r'<link rel="preload" as="image"[^>]*>', pre, t)
    # a jpg preload of a POSSIBLE that the BEFORE layer serves as WebP: preload the BEFORE's WebP set
    b_src = re.search(r'<source type="image/webp" srcset="([^"]+)" sizes="([^"]+)">', b_new)
    for jp in re.findall(r'<link rel="preload" as="image" href="([^"]+)" fetchpriority="high">', t):
        if jp == bu[-1] and b_src:
            t = t.replace('<link rel="preload" as="image" href="%s" fetchpriority="high">' % jp,
                          '<link rel="preload" as="image" type="image/webp" imagesrcset="%s" imagesizes="%s" fetchpriority="high">'
                          % (b_src.group(1), b_src.group(2)), 1)
    # v1.3 at least (v1.4, 31 Oct 2026, adds the opt-in disclosure beneath the comparison; a later version is kept)
    t = re.sub(r'href="assets/identity/pn-compare\.css(\?v=([0-9.]+))?"',
               lambda m: m.group(0) if m.group(2) and tuple(map(int, m.group(2).split("."))) >= (1, 3)
               else 'href="assets/identity/pn-compare.css?v=1.3"', t)
    t = re.sub(r'src="assets/identity/pn-compare\.js(\?v=[0-9.]+)?"', 'src="assets/identity/pn-compare.js?v=1.3"', t)
    return t


def main():
    pages = sorted(p for p in ROOT.glob("*.html") if 'pn-compare--hero' in p.read_text(encoding="utf-8"))
    bad = []
    for p in pages:
        t = p.read_text(encoding="utf-8")
        n = transform(t, p.name)
        if CHECK:
            if n != t or 'data-start="100"' not in t:
                bad.append(p.name)
            continue
        if n != t:
            p.write_text(n, encoding="utf-8"); print("updated:", p.name)
    if CHECK:
        print("HERO START BEFORE · " + ("OK on %d pages" % len(pages) if not bad else "NOT APPLIED: %s" % bad))
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
