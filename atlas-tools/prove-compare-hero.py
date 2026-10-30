"""GUARD · pn-compare hero standard (Pass 2, founder approval D1, 30 Oct 2026). Read-only.

Checks every page that carries a pn-compare HERO (class pn-compare--hero):
  C1  the shared stylesheet and script are linked (pn-compare.css / pn-compare.js)
  C2  start position data-start="35" (35% Before / 65% Possible) and a range input valued 35
  C3  exactly two layers (POSSIBLE base, BEFORE overlay), each a <picture> with an <img> carrying alt text
  C4  both layers declare the same width and height (one framing, pixel alignment)
  C5  POSSIBLE is the priority image (fetchpriority="high"); BEFORE is not lazy-loaded
  C6  the AI-generated illustration label is inside the figure whenever a layer is a declared
      AI_ILLUSTRATION record (legacy-undeclared images are not labelled by this guard: no claim
      is made about what made them until they are declared)
  C7  both layers' image files exist and every encoding has a provenance record
  C8  BEFORE and POSSIBLE tags, keyboard help (aria-describedby) and the jump group are present
  C9  exactly one H1 on the page

--self-test plants a fault per check on an in-memory copy and requires every one to be caught.
Prints "COMPARE HERO · OK" only when all checks pass.
"""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAGES = ["discovery-supper-club-at-home.html", "discovery-natural-swimming-garden.html",
         # Pass 2 Release 2 (30 Oct 2026)
         "discovery-hidden-flood-barrier.html", "discovery-living-in-the-garden.html", "discovery-home-exchange.html",
         # Pass 2 Release 3 (30 Oct 2026, private preview)
         "discovery-hidden-bins.html", "discovery-house-as-power-station.html", "discovery-above-and-beyond.html"]


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


def declared_ai():
    try:
        d = json.loads(read("image-provenance-records.json"))
        return {r["asset"] for r in d.get("records", []) if r.get("class") == "AI_ILLUSTRATION"}
    except Exception:
        return set()


def provenance_assets():
    out = set()
    for f in ["image-provenance-records.json"] + [os.path.join("governance", g) for g in os.listdir(os.path.join(ROOT, "governance")) if g.endswith(".json") and "PROVENANCE" in g]:
        try:
            out |= set(re.findall(r'"asset"\s*:\s*"([^"]+)"', read(f)))
        except Exception:
            pass
    return out


PROV = provenance_assets()
AI = declared_ai()


def check(page, s, exists=lambda p: os.path.exists(os.path.join(ROOT, p))):
    f = []
    m = re.search(r'<figure class="pn-compare pn-compare--hero"[^>]*>[\s\S]*?</figure>', s)
    if not m:
        return ["C0 no pn-compare hero figure"]
    fig = m.group(0)
    if not re.search(r'href="assets/identity/pn-compare\.css', s) or not re.search(r'src="assets/identity/pn-compare\.js', s):
        f.append("C1 shared stylesheet/script not linked")
    if 'data-start="35"' not in fig or not re.search(r'class="pn-compare__range"[^>]*value="35"', fig):
        f.append("C2 start is not 35")
    layers = re.findall(r'<div class="pn-compare__(possible|before)">\s*<picture>([\s\S]*?)</picture>', fig)
    if [l[0] for l in layers] != ["possible", "before"]:
        f.append("C3 layers are not POSSIBLE then BEFORE")
    imgs = [re.search(r"<img\b[^>]*>", l[1]).group(0) for l in layers if re.search(r"<img\b[^>]*>", l[1])]
    if len(imgs) != 2 or not all(re.search(r'alt="[^"]{10,}"', i) for i in imgs):
        f.append("C3 a layer image is missing or lacks alt text")
    dims = [(re.search(r'width="(\d+)"', i).group(1), re.search(r'height="(\d+)"', i).group(1)) for i in imgs if re.search(r'width="(\d+)"', i) and re.search(r'height="(\d+)"', i)]
    if len(dims) != 2 or dims[0] != dims[1]:
        f.append("C4 layers declare different sizes: %s" % dims)
    if len(imgs) == 2 and ('fetchpriority="high"' not in imgs[0] or 'loading="lazy"' in imgs[1]):
        f.append("C5 POSSIBLE not priority, or BEFORE lazy-loaded")
    layer_imgs = set(re.findall(r'<img\b[^>]*src="([^"]+)"', fig))
    if (layer_imgs & AI) and "AI-generated illustration" not in fig:
        f.append("C6 AI-generated illustration label missing")
    refs = set(re.findall(r'(assets/[^"\s,]+\.(?:jpg|webp|avif))', fig))
    for r in sorted(refs):
        if not exists(r):
            f.append("C7 missing file " + r)
        elif r not in PROV:
            f.append("C7 no provenance record for " + r)
    if not ('is-before' in fig and 'is-possible' in fig and 'aria-describedby=' in fig and 'pn-compare__jump' in fig):
        f.append("C8 tags, keyboard help or jump group missing")
    if len(re.findall(r"<h1[\s>]", s)) != 1:
        f.append("C9 not exactly one H1")
    return f


def main():
    if "--self-test" in sys.argv:
        s = read("discovery-natural-swimming-garden.html")
        faults = {
            "C1": lambda t: t.replace('src="assets/identity/pn-compare.js', 'src="assets/identity/other.js'),
            "C2": lambda t: t.replace('data-start="35"', 'data-start="50"', 1),
            "C3": lambda t: t.replace('alt="Before: the same garden as it is, with a stone patio and a long open lawn."', 'alt=""', 1),
            "C4": lambda t: t.replace('before-1536.jpg" width="1536" height="1024"', 'before-1536.jpg" width="1536" height="1000"', 1),
            "C5": lambda t: t.replace('before-1536.jpg" width="1536" height="1024" decoding="async"', 'before-1536.jpg" width="1536" height="1024" loading="lazy" decoding="async"', 1),
            "C6": lambda t: t.replace('<p class="pn-compare__ai">AI-generated illustration</p>', '', 1),
            "C7": lambda t: t.replace('DISC-031-before-960.webp', 'DISC-031-before-961.webp', 1),
            "C8": lambda t: t.replace('aria-describedby="nsHeroCompareKeys"', '', 1),
            "C9": lambda t: t.replace('</main>', '<h1>x</h1></main>', 1),
        }
        caught = sum(1 for k, fn in faults.items() if any(x.startswith(k) for x in check("x", fn(s))))
        print("COMPARE HERO CAPABILITY · %d/%d planted faults caught" % (caught, len(faults)))
        sys.exit(0 if caught == len(faults) else 1)
    fails = []
    for p in PAGES:
        fails += ["%s: %s" % (p, x) for x in check(p, read(p))]
    for x in fails:
        print("FAIL", x)
    print("COMPARE HERO · OK — C1-C9 on %d pages" % len(PAGES) if not fails else "COMPARE HERO · %d FAILURE(S)" % len(fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
