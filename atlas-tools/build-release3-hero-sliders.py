#!/usr/bin/env python3
"""
PASS 2 · RELEASE 3 · Before / Possible hero sliders (founder approval, 30 Oct 2026:
"PRIVATE PREVIEW DEVELOPMENT ONLY") for three Discoveries:

  DISC-029 The Hidden Bins            9805382f (bins out)  ->  31b49fb6 (bins gone)
  DISC-026 The House as a Power Station fec77c3f (bare roof) -> ce9da2e5 (solar, battery, charger)
  DISC-016 Above and Beyond           b53d75f9 (garden)    ->  aecece07 (two pods), mark-removed
                                                                copies (build-disc016-hero-mark-removal.py)

Each pair is the audit's measured 0 px pair (one framing; masked edits). The hero becomes
the shared pn-compare component (v1.2, hero standard, as The Natural Swimming Garden): opens
at 35, Before / Possible, phones get the compact title band, a 4:5 image, the jump bar and
the hero copy below. Hero copy (eyebrow, H1, subtitle, intro) is carried over byte for byte.

  * Hidden Bins: the frozen hero annotation is removed from the hero (founder instruction);
    the hero is no longer a plate, which also fixes the thin phone hero.
  * Power Station: the Potential Asset annotation stays, unchanged in geometry and wording,
    now inside the BEFORE layer, so it labels the bare roof and is wiped away with it.
    It is drawn with xMidYMid slice and the layer's focus is 50% 50%, so it stays on the
    roof at every crop. Freeze record V8 records this as the only article change.
  * Above and Beyond: the slider uses the mark-removed copies; the sources are untouched.

Nothing else on the pages changes. Page CSS goes in its own <style> just before </head>
(no builder anchor is touched); the pn-compare stylesheet link follows the generated
identity HEAD block, as on the Release 2 pages.

  python3 atlas-tools/build-release3-hero-sliders.py          build
  python3 atlas-tools/build-release3-hero-sliders.py --check  verify, write nothing
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv
LINK = '<link rel="stylesheet" href="assets/identity/pn-compare.css?v=1.2">\n'
SCRIPT = '<script src="assets/identity/pn-compare.js?v=1.2" defer></script>\n'
HEAD_END = "<!-- PLOTNUA IDENTITY v1 · HEAD · END -->\n"
SIZES = "(max-width:1024px) and (orientation:portrait) 150vw, max(100vw, 132svh)"


def picture(webps, jpg, w, h, alt, possible):
    src = ""
    if webps:
        src = '          <source type="image/webp" srcset="%s" sizes="%s">\n' % (", ".join("%s %dw" % x for x in webps), SIZES)
    attrs = ' fetchpriority="high"' if possible else ""
    idattr = ' id="dHeroImg" class="on"' if possible else ""
    return ("        <picture>\n%s          <img%s src=\"%s\" width=\"%d\" height=\"%d\"%s decoding=\"async\" alt=\"%s\">\n"
            "        </picture>\n") % (src, idattr, jpg, w, h, attrs, alt)


def figure(p):
    extra = p.get("before_extra", "")
    return f'''  <figure class="pn-compare pn-compare--hero" id="{p['fid']}" data-start="35" data-subject="{p['subject']}" data-line-fade-under="#dHeroCopy" style="--pnc-focus:{p['focus']}">
    <div class="pn-compare__stage">
      <div class="pn-compare__possible">
{picture(p['pos_webp'], p['pos_jpg'], 1408, 768, p['pos_alt'], True)}      </div>
      <div class="pn-compare__before">
{picture(p['bef_webp'], p['bef_jpg'], 1408, 768, p['bef_alt'], False)}{extra}      </div>
      <span class="pn-compare__line" aria-hidden="true"></span>
      <span class="pn-compare__knob" aria-hidden="true"></span>
      <p class="pn-compare__tag is-before" aria-hidden="true">Before</p>
      <p class="pn-compare__tag is-possible" aria-hidden="true">Possible</p>
      <input class="pn-compare__range" type="range" min="0" max="100" step="1" value="35" aria-describedby="{p['fid']}Keys"
             aria-label="{p['aria']}"
             aria-valuetext="Mostly {p['subject']} as it could be, divider at 35 per cent">
    </div>
    <div class="pn-compare__bar">
      <p class="pn-compare__help"><span class="pn-compare__help-touch" aria-hidden="true">Slide to discover what&rsquo;s possible.</span><span class="pn-compare__help-pointer" aria-hidden="true">Drag the handle, or use the arrow keys, to compare.</span><span class="pn-compare__sr" id="{p['fid']}Keys">Use the left and right arrow keys to move the divider. Home shows {p['subject']} as it could be; End shows {p['subject']} before.</span></p>
      <div class="pn-compare__jump" role="group" aria-label="Show">
        <button type="button" data-to="100" aria-pressed="false">Before</button>
        <button type="button" data-to="0" aria-pressed="false">Possible</button>
      </div>
    </div>
  </figure>
'''


def page_css(cls):
    return f'''<style>
/* ---- Pass 2 Release 3 (30 Oct 2026): the hero is the shared pn-compare component (hero standard),
   as on the Release 2 pages. These rules only give the frame back to the component where this
   page's own .d-hero rules would otherwise win; the hero copy and its typography are unchanged. ---- */
body.pn-id.pn-pd .d-hero.{cls}.pn-hero-compare{{ height:92vh; height:92svh; min-height:560px; }}
body:has(> .pn-return) .d-hero.{cls}.pn-hero-compare{{ height:min(92svh, calc(100svh - var(--pnc-hdr,69px) - var(--pn-dock,0px))); }}
body.pn-id.pn-pd .{cls}.pn-hero-compare .d-hero-scrim{{ pointer-events:none; z-index:1; }}
body.pn-id.pn-pd .{cls}.pn-hero-compare .d-hero-copy{{ z-index:2; }}
body.pn-id.pn-pd .{cls}.pn-hero-compare :is(.pn-compare__possible,.pn-compare__before) picture{{ height:100%; }}
body.pn-id.pn-pd .{cls}.pn-hero-compare .pn-compare__before .pa-annot{{ position:absolute; inset:0; z-index:1; pointer-events:none; }}
body.pn-id.pn-pd .{cls}.pn-hero-compare .pn-compare__before .pa-annot svg{{ display:block; width:100%; height:100%; }}
@media (max-width:1024px) and (orientation:portrait), (max-width:719px){{
  body.pn-id.pn-pd .d-hero.{cls}.pn-hero-compare,
  body:has(> .pn-return) .d-hero.{cls}.pn-hero-compare{{ height:auto; min-height:0; }}
  body.pn-id.pn-pd .{cls}.pn-hero-compare .d-hero-copy{{ padding:24px 22px 28px; }}
  body.pn-id.pn-pd .{cls}.pn-hero-compare .d-hero-copy :is(h1,.subtitle,.intro){{ text-align:left; margin-left:0; margin-right:0; }}
  /* stacked layouts crop the frame to 1:1 / 4:5, where the divider's opening position would cut
     the annotation's label in two: it is shown only where it can sit clear of the opening divider */
  body.pn-id.pn-pd .{cls}.pn-hero-compare .pn-compare__before .pa-annot{{ display:none; }}
}}
</style>
'''


PAGES = {
    "discovery-hidden-bins.html": dict(
        cls="hb-hero", name="The Hidden Bins", fid="hbHeroCompare", subject="the frontage", focus="60% 50%",
        aria="Compare the frontage with its bins out and with the bins hidden away. Higher values show more of the frontage before.",
        bef_jpg="assets/img/9805382f8164228a.jpg",
        bef_webp=[("assets/img/9805382f8164228a-960w.webp", 960), ("assets/img/9805382f8164228a.webp", 1408)],
        bef_alt="Before: three ordinary wheelie bins standing exposed on the paved frontage of a new Irish home.",
        pos_jpg="assets/img/31b49fb60732073b.jpg", pos_webp=[],
        pos_alt="The frontage as it could be: the three wheelie bins gone and the paving running unbroken across the ground they stood on.",
        preload_old='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/9805382f8164228a-960w.webp 960w, assets/img/9805382f8164228a.webp 1408w" imagesizes="100vw" fetchpriority="high">\n',
        preload_new='<link rel="preload" as="image" href="assets/img/31b49fb60732073b.jpg" fetchpriority="high">\n',
        comment="""  <!-- Pass 2 Release 3 (founder approval, 30 Oct 2026): the shared Before -> Possible component
       pn-compare v1.2, hero standard. Same frontage, one framing (0 px): the bins out, then gone.
       The frozen hero annotation is removed from the hero by founder instruction; the photographs
       are unchanged. The POSSIBLE source's credential records an unidentified input, so it gets
       no derivative here and is served as its original JPEG (no lineage claim is made). -->
"""),
    "discovery-house-as-power-station.html": dict(
        cls="ps-hero", name="The House as a Power Station", fid="psHeroCompare", subject="the house", focus="50% 50%",
        aria="Compare the house with a bare roof and with solar panels, a battery and a charger. Higher values show more of the house before.",
        bef_jpg="assets/img/fec77c3f0bae107a.jpg",
        bef_webp=[("assets/img/fec77c3f0bae107a-960w.webp", 960), ("assets/img/fec77c3f0bae107a.webp", 1408)],
        bef_alt="Before: the same house and garden at dusk with a bare tiled roof, no panels and no battery, the roof annotated by PlotNua as a potential asset.",
        pos_jpg="assets/img/ce9da2e51c945693.jpg",
        pos_webp=[("assets/img/ce9da2e51c945693-960w.webp", 960), ("assets/img/ce9da2e51c945693.webp", 1408)],
        pos_alt="The house as it could be: solar panels across the roof, a battery unit in the open garage, a charger on the wall and an electric car in the driveway.",
        preload_old=None,
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/ce9da2e51c945693-960w.webp 960w, assets/img/ce9da2e51c945693.webp 1408w" imagesizes="%s" fetchpriority="high">\n' % SIZES,
        comment="""  <!-- Pass 2 Release 3 (founder approval, 30 Oct 2026; freeze record V8): the shared Before ->
       Possible component pn-compare v1.2, hero standard. Same house, one framing (0 px): the bare
       roof, then the S8 picture (solar, battery, charger). The Potential Asset annotation is
       unchanged in geometry and wording and now sits inside the BEFORE layer, so it labels the
       bare roof and is wiped away with it (xMidYMid slice, layer focus 50% 50%). -->
"""),
    "discovery-above-and-beyond.html": dict(
        cls="ab-hero", name="Above and Beyond", fid="abHeroCompare", subject="the garden", focus="65% 50%",
        aria="Compare the garden as it is and with raised timber pods above the lawn. Higher values show more of the garden before.",
        bef_jpg="assets/disc016/img/DISC-016-HERO-BEFORE-MR.jpg",
        bef_webp=[("assets/disc016/img/DISC-016-HERO-BEFORE-MR-960.webp", 960), ("assets/disc016/img/DISC-016-HERO-BEFORE-MR-1408.webp", 1408)],
        bef_alt="Before: an ordinary Irish back garden seen from the house: a mown striped lawn with a football on it, a paved patio outside sliding doors, a silver birch and a mature oak, with clipped hedges and neighbouring rooftops beyond.",
        pos_jpg="assets/disc016/img/DISC-016-HERO-POSSIBLE-MR.jpg",
        pos_webp=[("assets/disc016/img/DISC-016-HERO-POSSIBLE-MR-960.webp", 960), ("assets/disc016/img/DISC-016-HERO-POSSIBLE-MR-1408.webp", 1408)],
        pos_alt="The garden as it could be: two timber pods raised above the lawn, joined in the air by a rope bridge, with a climbing net up to one and a curved slide down from the other.",
        preload_old=None,
        preload_new='<link rel="preload" as="image" type="image/webp" imagesrcset="assets/disc016/img/DISC-016-HERO-POSSIBLE-MR-960.webp 960w, assets/disc016/img/DISC-016-HERO-POSSIBLE-MR-1408.webp 1408w" imagesizes="%s" fetchpriority="high">\n' % SIZES,
        comment="""  <!-- Pass 2 Release 3 (founder approval, 30 Oct 2026): the shared Before -> Possible component
       pn-compare v1.2, hero standard. Same garden, one framing (0 px): as it is, then two pods.
       The slider uses copies of the two legacy pictures with the faint visible mark removed
       (atlas-tools/build-disc016-hero-mark-removal.py; draft provenance for founder review in
       governance/DISC-016-HERO-MARK-REMOVAL-REVIEW-DRAFT-2026-10-30.json). The sources and
       their other uses on this page are unchanged. -->
"""),
}


def build(name, p, t):
    hm = re.search(r'<header class="d-hero[^"]*">[\s\S]*?</header>\n', t)
    assert hm and t.count('<header class="d-hero') == 1, name + ": hero header not found once"
    hero = hm.group(0)
    copy = re.search(r'  <div class="d-hero-copy in" id="dHeroCopy">[\s\S]*?\n  </div>\n', hero)
    assert copy, name + ": hero copy not found"
    if name == "discovery-house-as-power-station.html":
        ann = re.search(r'  <!-- POTENTIAL ASSET ANNOTATION, ON THE HERO\.[\s\S]*?-->\n<div class="pa-annot" aria-hidden="true">\n[\s\S]*?\n  </div>\n', hero)
        assert ann, "Power Station: annotation not found"
        # the same comment and element, indented to sit inside the BEFORE layer;
        # geometry, classes and text unchanged
        p["before_extra"] = "".join(("      " + l) if l.strip() else l for l in ann.group(0).splitlines(True))
    mtitle = ('  <div class="pn-hero-compare__mtitle" aria-hidden="true"><span class="pn-hero-compare__mkicker">'
              'A PlotNua Discovery</span><span class="pn-hero-compare__mname">%s</span></div>\n' % p["name"])
    new_hero = ('<header class="d-hero %s pn-hero-compare pn-hero-compare--std">\n' % p["cls"] + mtitle + p["comment"]
                + figure(p) + '  <div class="d-hero-scrim"></div>\n' + copy.group(0) + "</header>\n")
    t = t.replace(hero, new_hero, 1)
    assert t.count(HEAD_END) == 1, name + ": identity HEAD end marker"
    t = t.replace(HEAD_END, HEAD_END + LINK, 1)
    if p["preload_old"]:
        assert t.count(p["preload_old"]) == 1, name + ": preload"
        t = t.replace(p["preload_old"], p["preload_new"], 1)
    else:
        t = t.replace(HEAD_END + LINK, HEAD_END + LINK + p["preload_new"], 1)
    assert t.count("</head>") == 1 and t.count("</body>") == 1
    t = t.replace("</head>", page_css(p["cls"]) + "</head>", 1)
    t = t.replace("</body>", SCRIPT + "</body>", 1)
    return t


def main():
    bad = []
    for name, p in PAGES.items():
        path = ROOT / name
        cur = path.read_text(encoding="utf-8")
        if CHECK:
            if 'class="pn-compare pn-compare--hero"' not in cur or LINK not in cur or SCRIPT not in cur:
                bad.append(name)
            continue
        if 'class="pn-compare pn-compare--hero"' in cur:
            print("already built: " + name); continue
        path.write_text(build(name, dict(p), cur), encoding="utf-8")
        print("built: " + name)
    if CHECK:
        print("RELEASE 3 HERO SLIDERS · " + ("OK" if not bad else "NOT BUILT: %s" % bad)); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
