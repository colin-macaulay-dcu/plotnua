#!/usr/bin/env python3
"""POSSIBILITY REVEAL · HOMEPAGE COMPONENT (Phase 4 D2, 19 Oct 2026)

Package the approved L2B Prototype v2 as an isolated homepage component.

MECHANICAL TRANSFORM ONLY. Input: the unmodified prototype (index.html, assets/*).
Output: assets/possibility-reveal/{reveal.css,reveal.js,reveal-data.js} and a markup
snippet for #heroStage. Behaviour, sequencing, timings, camera values, beacon coordinates,
copy, drawings and data are copied byte-for-byte except for these isolation changes:
  1. every CSS rule is scoped under the component root (.pr); :root/html/body -> .pr
  2. @keyframes are renamed pr-* (and their animation references)
  3. every DOM id is namespaced pr-* (markup, CSS, JS, SVG url(#) references)
  4. JS looks up elements inside the component root, not the whole document;
     document-level click/keydown listeners ignore events from outside the component
  5. the prototype's <h1> becomes an <h2> (class pr-title): the page keeps one H1
  6. stage height, top safe inset and two grounds become CSS variables whose
     defaults are the prototype's own values (100svh / 0 / its greens)
  7. image paths point to assets/possibility-reveal/img/
  9. the mounted snippet is kept as stage-snippet.part, not .html, so it is never served
     as a stand-alone page showing the illustration without its label (P8, standard 3)
  8. ONE founder-approved wording change (19 Oct 2026, PN-FDR-2026-10-19-01, standard 3):
     the legend note "...not part of the photograph." reads "...not part of the picture."
     The scene is an AI-generated illustration, so it is not called a photograph.
  10. H3 GARDEN LAYERS (founder-approved H3, 20 Oct 2026), applied by h3_extend() below as
     anchored, counted edits after the mechanical transform:
       - the "Grow a garden room / Borrow a garden / Hold a treehouse / Become a retreat" chips
         become switches (aria-pressed); "Be renewed" and "Make its own energy" are unchanged;
       - the four locked garden layers (L3 v2.1c, L4, L5, L6) are mounted as <template>s, so
         nothing is downloaded until a layer is switched on (first paint and LCP unchanged);
       - the TimberIN credit and the founder-approved accessible disclosure sit beside L6;
       - reveal.js gains ONE hook, PN_REVEAL_API.frame(view), so a layer can be framed through
         the Reveal's own camera (beacons, lens, resize and Close keep working);
       - behaviour for the layers lives in garden.js / garden.css, hash-bound in the record.
     The tile files are made by build-possibility-reveal-layers.py from the lock chain.
Images are NOT made here: see build-possibility-reveal-images.py.

  python3 atlas-tools/build-possibility-reveal-component.py --source PROTOTYPE_DIR   build + mount
  python3 atlas-tools/build-possibility-reveal-component.py --check                  guard (no source needed)
  python3 atlas-tools/build-possibility-reveal-component.py --check --source DIR     guard + fresh-transform match

The guard refuses if: a generated file differs from its record; the snippet is not
mounted verbatim in index.html#heroStage; any component CSS rule is unscoped; the
component carries an <h1>, an un-prefixed id or a reserved homepage id; the script
looks anything up outside its root; or commerce is enabled / an offer is active."""
import re, sys, os, hashlib, json
IDS = ['pn','stage','cam','photo','hidden','sc-ground','sc-wind','sc-compute','lens','lensGrip','beacons','lensLabel',
       'layers','paths','bar','pathName','dots','btnReplay','btnHome','caption','more','introTitle','capTitle','moreTitle',
       'irisClip','cylClip','soil','soilEdge','warm']
KF = ['flow','spin','blink','ping','rise']
P = 'pr-'
def rd(p): return open(os.path.join(SRC, p), encoding='utf-8').read()

# ---------------- H3 · garden layers (L3–L6) ----------------
GARDEN = [('L3', 'Grow a garden room'), ('L4', 'Borrow a garden'), ('L5', 'Hold a treehouse'), ('L6', 'Become a retreat')]
CREDIT = 'Hot tub: TimberIN \u00b7 Sauna: TimberIN'   # 22 Oct 2026: the two TimberIN grants' exact credits (hot tub 20 Oct; Nordic Cube sauna 22 Oct), one link
CREDIT_LINK = 'https://www.timberin.com/'
VISIBLE_CAPTION = 'AI-generated illustration \u00b7 Hot tub: TimberIN \u00b7 Sauna: TimberIN'   # H5C4 (founder-approved one-line attribution, 21 Oct 2026)
DISCLOSURE = 'This garden scene combines AI-generated illustration with adapted photography of a TimberIN hot tub and sauna.'
def layers_record():
    return json.load(open(os.path.join(ROOTDIR, 'assets/possibility-reveal/layers/layers.json'), encoding='utf-8'))
def h3_tpl(rec, lid):
    L = rec['layers'][lid]; x, y, w, h = L['bbox_2752']
    names = list(L['files']); full = [n for n in names if not n.endswith('-half.webp')][0]; half = [n for n in names if n.endswith('-half.webp')][0]
    fw = L['files'][full]['pixels']; hw = L['files'][half]['pixels']
    d = 'assets/possibility-reveal/layers/'
    sprite = ' g-sprite' if lid == 'L6' else ''
    return ('<template data-layer="%s"><div class="g-layer%s" data-layer="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">'
            '<img src="%s%s" srcset="%s%s %dw, %s%s %dw" sizes="%dpx" width="%d" height="%d" alt="" decoding="async"></div></template>'
            % (lid, sprite, lid, x, y, w, h, d, full, d, half, hw[0], d, full, fw[0], w, fw[0], fw[1]))
def h3_extend(js, body):
    rec = layers_record()
    def one(t, a, b):
        assert t.count(a) == 1, ('h3 anchor', t.count(a), a[:80]); return t.replace(a, b)
    # JS: one camera hook, and the entry view may be re-framed by a garden layer
    js = one(js, '  var ENTRY_VIEW = { d: [1376, 820, 1], m: [1000, 800, 1] };\n',
             '  var ENTRY_VIEW = { d: [1376, 820, 1], m: [1000, 800, 1] };\n'
             '  var FRAME = null;   /* H3: a garden layer may re-frame the entry view (PN_REVEAL_API.frame) */\n'
             '  var entryView = function () { return FRAME || ENTRY_VIEW; };\n')
    js = one(js, '    camera(pick(ENTRY_VIEW)); placeBeacons(); setActive(null); restLens(); showPaths();',
             '    camera(pick(entryView())); placeBeacons(); setActive(null); restLens(); showPaths();')
    js = one(js, '      if (state.mode === "entry") { camera(pick(ENTRY_VIEW), true); placeBeacons(); setLens(lensPos.x, lensPos.y); }',
             '      if (state.mode === "entry") { camera(pick(entryView()), true); placeBeacons(); setLens(lensPos.x, lensPos.y); }')
    # H3 final review (21 Oct 2026): a frame may name where the lens rests while it is active
    # (`lens`, picture px); without it the lens rests on the ground beacon exactly as before
    js = one(js, '  var entryView = function () { return FRAME || ENTRY_VIEW; };\n',
             '  var entryView = function () { return FRAME || ENTRY_VIEW; };\n'
             '  var restAt = function () { return (FRAME && FRAME.lens) || BEACON.ground; };   /* H3: where the lens rests */\n')
    js = one(js, '  function restLens() { setLens.apply(null, toScreen(pick(BEACON.ground))); }',
             '  function restLens() { setLens.apply(null, toScreen(pick(restAt()))); }')
    js = one(js, '    var p = toScreen(pick(BEACON.ground)); easeLensTo(p[0], p[1], 600);',
             '    var p = toScreen(pick(restAt())); easeLensTo(p[0], p[1], 600);')
    js = one(js, '  window.PN_REVEAL_API = { play: play, home: home, state: state };   // for automated checks only',
             '  /* H3: frame a garden layer through this camera; null returns to the whole property.\n'
             '     If the frame names its own lens resting place, the lens goes there, and when that\n'
             '     ends it returns exactly to where it was before; otherwise it stays where it is. */\n'
             '  var lensHome = null;\n'
             '  function frame(v, instant) {\n'
             '    var own0 = !!(FRAME && FRAME.lens);\n'
             '    FRAME = v || null;\n'
             '    if (state.mode !== "entry") return;\n'
             '    stopGlide(); showPaths();\n'
             '    camera(pick(entryView()), instant); placeBeacons();\n'
             '    var own1 = !!(FRAME && FRAME.lens);\n'
             '    if (own1 && !dragging) { if (!own0) lensHome = [lensPos.x, lensPos.y]; restLens(); }\n'
             '    else if (own0 && !own1 && lensHome && !dragging) { setLens(lensHome[0], lensHome[1]); lensHome = null; }\n'
             '    else setLens(lensPos.x, lensPos.y);\n'
             '  }\n'
             '  window.PN_REVEAL_API = { play: play, home: home, state: state, frame: frame };   // play/home/state: automated checks; frame: garden.js')
    # markup: the four garden chips become switches
    nav_old = body[body.index('<nav class="layers" id="pr-layers"'):body.index('</nav>') + len('</nav>')]
    for lid, label in GARDEN: assert nav_old.count('<span class="lay">%s</span>' % label) == 1, ('chip', label)
    nav = nav_old.replace(' tabindex="0" aria-label="Other possibilities for this property (other layers are not part of this prototype)"',
                          ' aria-label="Possibilities for this property: switch a garden layer on or off"')
    assert nav != nav_old
    for lid, label in GARDEN:
        extra = ' aria-describedby="pr-gardenNote"' if lid == 'L6' else ''
        nav = nav.replace('<span class="lay">%s</span>' % label,
                          '<button type="button" class="lay lay-btn" data-layer="%s" aria-pressed="false"%s>%s</button>' % (lid, extra, label))
    body = one(body, nav_old, nav)
    # L3, L4, L5 sit directly on the picture; L6 last in the camera, beside its credit
    pic_end = '      </picture>\n'
    body = one(body, pic_end, pic_end + '\n      <!-- H3 · GARDEN LAYERS: locked L3–L5, nothing is fetched until switched on -->\n'
               + ''.join('      %s\n' % h3_tpl(rec, lid) for lid in ('L3', 'L4', 'L5')))
    cam_end = '    </div>\n\n    <div class="veil" aria-hidden="true"></div>'
    credit = ('    <p class="garden-credit" id="pr-gardenCredit" hidden>Garden possibilities illustrated. '
              '<a href="%s">%s</a>.<span class="sr-only" id="pr-gardenNote"> %s</span></p>\n'
              '    <p class="sr-only" id="pr-gardenStatus" aria-live="polite"></p>\n' % (CREDIT_LINK, CREDIT, DISCLOSURE))
    body = one(body, cam_end, '      <!-- H5C4 · GARDEN LAYER L6: locked L6 H5C4 (garden retreat: hot tub and smoke from licensed photography; terrace, cold plunge, planting), fetched only when switched on -->\n'
               '      %s\n' % h3_tpl(rec, 'L6') + '    </div>\n' + credit + '\n    <div class="veil" aria-hidden="true"></div>')
    return js, body

# ---------------- H5 · homepage simplification (H5 Phase C preview, 21 Oct 2026) ----------------
# The homepage hero becomes the garden photograph and its four transformations, nothing else:
# no lens, no tour, no Discovery markers, no Power Station headline or paths on the hero (the
# Discovery scenes, data and the Power Station Discovery itself are untouched and stay in the
# component, dormant); one invitation (the page's H1) and four prominent ON/OFF switches below the
# photograph; the AI disclosure and the TimberIN credit in a strip directly beneath the photograph,
# so nothing covers the retreat; a private smoke-animation prototype (h5c-smoke.js, procedural, no
# image pixels, founder-approved for publication 21 Oct 2026). The picture is the approved, LOCKED L1 + L2A
# (production encodings in img/, unchanged): Path A, founder decision 21 Oct 2026. The L2A-H5 heat-pump
# candidate is not part of this release.
H5_FILES = ['assets/possibility-reveal/h5.css', 'assets/possibility-reveal/h5c-smoke.js']
H5_PS_JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'possibility-reveal-h5-ps.js.part'), encoding='utf-8').read()
H5_SWITCHES = [('L3', 'Garden Room'), ('L4', 'Borrowed Garden'), ('L5', 'Treehouse'), ('L6', 'Garden Retreat')]
H5_INVITE = 'Discover What\u2019s Possible.'   # H5C4 founder-approved heading
def h5_extend(js, body):
    def one(t, a, b):
        assert t.count(a) == 1, ('h5 anchor', t.count(a), a[:90]); return t.replace(a, b)
    # ---- JS: the lens never appears; nothing chases the pointer; the tour never starts
    js = one(js, '    ground:  { view: { d: [1700, 1080, 1.12], m: [1760, 1060, 1.0] },',
             '    ground:  { view: { d: [1520, 1080, 1.12], m: [1356, 1170, 1.0] },')   # H5C4: framed on the square ground-heat cut-away
    js = one(js, '  var mqReduce = window.matchMedia("(prefers-reduced-motion: reduce)");\n',
             '  var mqReduce = window.matchMedia("(prefers-reduced-motion: reduce)");\n'
             '  var H5 = true, PS = false;   /* H5 Phase C: the Power Station experience (lens, tour, markers, scenes) runs only while its switch is on */\n')
    js = one(js, '  var entryView = function () { return FRAME || ENTRY_VIEW; };\n',
             '  var PS_VIEW = { d: [1376, 640, 1], m: [1000, 800, 1] };   /* H5: with Power Station on, phones frame the original view (wind, house, lawn) */\n'
             '  /* H5 Phase C (framing fix, 21 Oct 2026): on wider screens the photograph is shown full width, so it\n'
             '     shows only part of the picture\'s height. The camera now keeps EVERYTHING that is switched on in view\n'
             '     (each garden layer\'s own area, and with Power Station the roof marker and the whole lens over the lawn),\n'
             '     centred when it fits and, when it cannot all fit, favouring the lower garden (hot tub, beds, lawn).\n'
             '     Phones keep their approved close framing of the last layer switched on.\n'
             '     H5C4: Power Station no longer has a lens to keep in view; and on wider screens the house and its\n'
             '     roofline stay in the frame too whenever everything switched on still fits with them. */\n'
             '  var HOUSE = [150, 640];   /* picture rows: the chimney top to the patio */\n'
             '  var ZONES = { L3: [526, 1118], L4: [832, 1420], L5: [394, 724], L6: [606, 1462] };\n'
             '  var entryView = function () {\n'
             '    var base = FRAME || ENTRY_VIEW;\n'
             '    if (mob()) return base;\n'
             '    var on = (pn.getAttribute("data-garden") || "").split(" ").filter(function (x) { return ZONES[x]; });\n'
             '    if (!on.length) return base;\n'
             '    var W = stage.clientWidth, H = stage.clientHeight, k = Math.max(W / 2752, H / 1536), R = H / k, a = 1e9, b = -1e9, low = false;\n'
             '    on.forEach(function (id) { a = Math.min(a, ZONES[id][0]); b = Math.max(b, ZONES[id][1]); if (id === "L6" || id === "L4") low = true; });\n'
             '    if (b - Math.min(a, HOUSE[0]) <= R) a = Math.min(a, HOUSE[0]);   /* keep the whole house when it fits */\n'
             '    var top = (b - a <= R) ? a - (R - (b - a)) / 2 : (low ? b - R : a);\n'
             '    top = Math.max(0, Math.min(1536 - R, top));\n'
             '    return { d: [base.d[0], top + 0.46 * R, 1], m: base.m, lens: base.lens };\n'
             '  };\n')
    js = one(js, '  var ENTRY_VIEW = { d: [1376, 820, 1], m: [1000, 800, 1] };\n',
             '  var ENTRY_VIEW = { d: [1376, 640, 1], m: [1250, 800, 1] };   /* H5: the sky kept in view; phones see the house and the extension */\n')
    js = one(js, '    var R = r == null ? lensRadius() : r, c = clampLens(x, y, Math.max(R, 1));',
             '    var R = H5 ? 0 : (r == null ? lensRadius() : r), c = clampLens(x, y, Math.max(R, 1));')
    js = one(js, '    if (mob()) {   /* on phones', '    if (mob() && $(".lede")) {   /* on phones')
    js = one(js, '    if (dragging || e.pointerType === "mouse") {\n',
             '    if (H5) return;\n    if (dragging || e.pointerType === "mouse") {\n')
    js = one(js, '    if (state.mode !== "entry" || dragging || e.pointerType !== "mouse") return;\n',
             '    if (H5 || state.mode !== "entry" || dragging || e.pointerType !== "mouse") return;\n')
    js = one(js, '  grip.addEventListener("pointerdown", function (e) { dragging = true;',
             '  grip.addEventListener("pointerdown", function (e) { if (H5) return; dragging = true;')
    js = one(js, '  /* ---------- start ---------- */\n', H5_PS_JS + '\n  /* ---------- start ---------- */\n')
    # H5C4: on phones the wind scene is framed a little further left, so the whole turbine and its wind lines are in view
    js = one(js, 'wind:    { view: { d: [900, 330, 1.7],    m: [860, 330, 1.35] }', 'wind:    { view: { d: [900, 330, 1.7],    m: [720, 330, 1.35] }')
    js = one(js, 'state: state, frame: frame };', 'state: state, frame: frame, ps: setPS, psOn: function () { return PS; } };')
    js = one(js, '    [".intro", "#pr-beacons", "#pr-layers"].forEach(function (s) { $(s).inert = scene; });',
             '    [".intro", "#pr-beacons"].forEach(function (s) { var e = $(s); if (e) e.inert = scene; });   /* H5C4: the switches beneath the photograph stay usable during a scene */')
    js = one(js, '    timers.push(setTimeout(function () { beaconsEl.classList.add("ready"); glide(); }, 650));',
             '    if (!H5) timers.push(setTimeout(function () { beaconsEl.classList.add("ready"); glide(); }, 650));')
    # ---- markup
    body = one(body, '<div class="pr pn" id="pr-pn" data-mode="entry" data-pr-root>', '<div class="pr pn h5 h5c" id="pr-pn" data-mode="entry" data-pr-root>')
    # H5C4 (22 Oct 2026): the ground-heat scene redrawn as a near-square cut-away of the central lawn
    _ga = body.index('      <svg class="scene" id="pr-sc-ground"'); _gb = body.index('</svg>', _ga) + len('</svg>')
    body = body[:_ga] + open(os.path.join(ROOTDIR, 'atlas-tools/possibility-reveal-h5c4-ground.svg.part'), encoding='utf-8').read() + body[_gb:]
    # FINAL HOMEPAGE RELEASE (22 Oct 2026, founder): the computer-heat scene is marked "Emerging possibility",
    # with one plain line saying it is not available to Irish homeowners (no commercial availability implied)
    body = one(body, '<text class="stamp s-fade s1 only-d" x="1190" y="338" text-anchor="middle">ILLUSTRATION \u00b7 NOT IN IRISH HOMES</text>',
               '<text class="stamp s-fade s1 only-d" x="1190" y="338" text-anchor="middle">ILLUSTRATION \u00b7 EMERGING POSSIBILITY</text>')
    body = one(body, '<text class="stamp s-fade s1 only-m" x="1190" y="338" text-anchor="middle">NOT IN IRISH HOMES</text>',
               '<text class="stamp s-fade s1 only-m" x="1190" y="338" text-anchor="middle">EMERGING POSSIBILITY</text>')
    body = one(body, '<text class="label s-fade s4 only-m" x="1190" y="1070" text-anchor="middle">abroad: computer \u2192 heat \u2192 hot water</text>',
               '<text class="label s-fade s4 only-m" x="1190" y="1070" text-anchor="middle">abroad: computer \u2192 heat \u2192 hot water</text>\n'
               '        <text class="label s-fade s4 only-d" x="1190" y="1118" text-anchor="middle">tried in homes abroad \u00b7 not available to Irish homeowners today</text>\n'
               '        <text class="label s-fade s4 only-m" x="1190" y="1130" text-anchor="middle">not available to Irish homeowners</text>')
    body = one(body, '<a class="skip" href="#pr-paths">Skip to the discovery paths</a>', '<a class="skip" href="#pr-layers">Skip to the garden transformations</a>')
    # the Power Station headline, lede and paths leave the hero (paths kept, empty and hidden: the script builds into it)
    a = body.index('    <section class="intro" aria-labelledby="pr-introTitle">'); b = body.index('    </section>\n', a) + len('    </section>\n')
    intro = body[a:b]; body = body[:a] + body[b:]
    ps_title = re.search(r'      <h2 class="pr-title" id="pr-introTitle">.*?</h2>\n', intro).group(0)
    ps_lede = re.search(r'      <p class="lede">.*?</p>\n', intro).group(0)
    # the old chip row leaves the photograph
    a = body.index('    <nav class="layers" id="pr-layers"'); b = body.index('</nav>', a) + len('</nav>\n')
    body = body[:a] + body[b:]
    # the TimberIN credit and status line move out of the photograph into the strip beneath it
    credit_a = body.index('    <p class="garden-credit" id="pr-gardenCredit" hidden>')
    credit_b = body.index('    <p class="sr-only" id="pr-gardenStatus" aria-live="polite"></p>\n') + len('    <p class="sr-only" id="pr-gardenStatus" aria-live="polite"></p>\n')
    credit = body[credit_a:credit_b]; body = body[:credit_a] + body[credit_b:]
    # H5C4: one visible line, "AI-generated illustration · Hot tub: TimberIN" (the credit joins the label while
    # Garden Retreat is on); the full disclosure stays in the page for screen readers
    credit = ('<span class="garden-credit" id="pr-gardenCredit" hidden> \u00b7 <a href="%s">%s</a>'
              '<span class="sr-only" id="pr-gardenNote"> %s</span></span>' % (CREDIT_LINK, CREDIT, DISCLOSURE))
    # the stage's own overlays (all positioned with explicit z-index, so their stacking does not
    # depend on order) move ahead of the camera, so the strip with the TimberIN credit follows the
    # L6 layer directly in the markup, as the provenance guard's licensed-credit window requires
    va = body.index('    <div class="veil" aria-hidden="true"></div>\n')
    vb = body.index('</aside>\n', va) + len('</aside>\n')
    over = body[va:vb]; body = body[:va] + body[vb:]
    body = one(body, '  <div class="stage" id="pr-stage">\n', '  <div class="stage" id="pr-stage">\n' + over)
    sw = []
    for lid, label in H5_SWITCHES:
        extra = ' aria-describedby="pr-gardenNote"' if lid == 'L6' else ''
        sw.append('      <button type="button" class="lay lay-btn h5c-sw" data-layer="%s" aria-pressed="false"%s>'
                  '<span class="h5c-knob" aria-hidden="true"></span><span class="h5c-lb">%s</span>'
                  '<span class="h5c-st" aria-hidden="true"></span></button>\n' % (lid, extra, label))
    ps_sw = ('      <button type="button" class="h5c-sw h5c-sw-ps" id="pr-psSwitch" aria-pressed="false" aria-controls="pr-psPanel">'
             '<span class="h5c-knob" aria-hidden="true"></span><span class="h5c-lb">Power Station</span><span class="h5c-st" aria-hidden="true"></span></button>\n')
    la = body.index('  <p class="legend" aria-label="How possibilities are marked">'); lb = body.index('  </p>\n', la) + len('  </p>\n')
    legend = body[la:lb]; body = body[:la] + '<!--H5LEGEND-->' + body[lb:]
    deck = ('  <!-- H5 Phase C · directly beneath the photograph: the disclosure strip, then the invitation and the five switches -->\n'
            '  <div class="h5c-strip" id="pr-strip">\n'
            '    <p class="h5c-ai" id="pr-aiNote"><b>AI-generated illustration</b>' + credit + '</p>\n'
            '    <p class="sr-only" id="pr-gardenStatus" aria-live="polite"></p>\n'
            '  </div>\n'
            '  <div class="h5c-deck" id="pr-deck">\n'
            '    <div class="layers h5c-switches" id="pr-layers" role="group" aria-labelledby="pr-invite">\n'
            '     <div class="h5c-group h5c-group-g" role="group" aria-labelledby="pr-gLab"><h1 class="h5c-invite" id="pr-invite">' + H5_INVITE + '</h1><p class="h5c-glab" id="pr-gLab">Garden transformations</p><div class="h5c-row">\n'
            + ''.join(sw) +
            '     </div></div>\n'
            '     <div class="h5c-group h5c-group-ps" role="group" aria-labelledby="pr-hLab"><p class="h5c-glab" id="pr-hLab">Hidden possibilities</p><div class="h5c-row">\n'
            + ps_sw +
            '     </div></div>\n'
            '    </div>\n'
            '    <!-- H5C4 Power Station panel, shown only while Power Station is on: the three approved scenes play in the\n'
            '         photograph (no lens); these buttons replay any one; the scene question (approved wording); a link to the Discovery -->\n'
            '    <div class="h5c-ps" id="pr-psPanel" hidden>\n'
            '      <p class="h5c-ps-line" id="pr-psLine" aria-live="polite"></p>\n'
            '      <div class="h5c-steps" role="group" aria-label="Power Station scenes">'
            '<button type="button" class="h5c-step" data-ps="wind" aria-pressed="false">Wind</button>'
            '<button type="button" class="h5c-step" data-ps="compute" aria-pressed="false">Computer Heat</button>'
            '<button type="button" class="h5c-step" data-ps="ground" aria-pressed="false">Ground Heat</button></div>\n'
            '      <a class="h5c-ps-link" href="discovery-house-as-power-station.html">The House as a Power Station <span aria-hidden="true">\u2192</span></a>\n'
            '      <div class="paths" id="pr-paths" hidden></div>\n'
            '    </div>\n'
            '  </div>\n')
    body = one(body, '<!--H5LEGEND-->', deck)
    body = one(body, '<p class="noscript">This interactive view needs JavaScript. <a href="https://plotnua.ie/discovery-house-as-power-station.html">Read The House as a Power Station</a>.</p>',
               '<p class="noscript">Switching the garden transformations on and off needs JavaScript. <a href="https://plotnua.ie/discoveries.html">Explore the Discovery Library</a>.</p>')
    return js, body

def transform():
    global css, js, data, snippet

    # ---------------- CSS ----------------
    def scope_sel(sel):
        sel = sel.strip()
        if not sel: return sel
        for i in IDS: sel = re.sub(r'#%s\b' % re.escape(i), '#' + P + i, sel)
        sel = sel.replace('.intro h1', '.intro .pr-title')
        if sel in (':root', 'html', 'body'): return '.pr'
        if sel == '*': return '.pr, .pr *'
        if sel.startswith('[data-mode') or sel.startswith('.lens-over-intro'): return '.pr' + sel   # root-state selectors: the class/attribute sits ON the root
        return '.pr ' + sel
    def scope_block(css):
        out = []; i = 0
        while i < len(css):
            j = css.find('{', i)
            if j < 0: out.append(css[i:]); break
            head = css[i:j]
            lm = re.match(r'(\s*(?:/\*.*?\*/\s*)*)', head, re.S); lead0 = lm.group(1); hs = head[len(lead0):].strip()
            if hs.startswith('@media') or hs.startswith('@supports'):
                depth = 1; k = j + 1
                while depth:
                    if css[k] == '{': depth += 1
                    elif css[k] == '}': depth -= 1
                    k += 1
                out.append(head + '{' + scope_block(css[j+1:k-1]) + '}'); i = k; continue
            if hs.startswith('@keyframes'):
                depth = 1; k = j + 1
                while depth:
                    if css[k] == '{': depth += 1
                    elif css[k] == '}': depth -= 1
                    k += 1
                name = head.strip().split()[1]
                out.append(head.replace(name, P + name) + css[j:k]); i = k; continue
            k = css.find('}', j)
            # keep leading comments/whitespace of the head
            m = re.match(r'(\s*(?:/\*.*?\*/\s*)*)(.*)$', head, re.S)
            lead, sels = m.group(1), m.group(2)
            out.append(lead + ','.join(scope_sel(s) for s in sels.split(',')) + css[j:k+1]); i = k + 1
        return ''.join(out)
    css = rd('assets/reveal.css')
    css = scope_block(css)
    css = re.sub(r'(animation(?:-name)?\s*:\s*)([a-z]+)', lambda m: m.group(1) + (P + m.group(2) if m.group(2) in KF else m.group(2)), css)
    # 6 · integration variables (defaults = the prototype's own values)
    rep = [
     ('.pr .stage{position:relative;width:100%;height:100vh;height:100svh;min-height:560px;max-height:1100px;overflow:hidden;background:#24331f;isolation:isolate}',
      '.pr .stage{position:relative;width:100%;height:var(--pr-stage-h,100vh);height:var(--pr-stage-h,100svh);min-height:var(--pr-stage-min,560px);max-height:var(--pr-stage-max,1100px);overflow:hidden;background:var(--pr-stage-bg,#24331f);isolation:isolate}'),
     ('.pr .layers{position:absolute;z-index:6;top:14px;', '.pr .layers{position:absolute;z-index:6;top:calc(14px + var(--pr-safe-top,0px));'),
     ('.pr .bar{position:absolute;z-index:7;top:14px;', '.pr .bar{position:absolute;z-index:7;top:calc(14px + var(--pr-safe-top,0px));'),
     ('.pr .caption.pos-tr{top:68px;', '.pr .caption.pos-tr{top:calc(68px + var(--pr-safe-top,0px));'),
     ('.pr .more{position:absolute;z-index:9;top:0;', '.pr .more{position:absolute;z-index:9;top:var(--pr-safe-top,0px);'),
     ('background:#0f1c15}', 'background:var(--pr-legend-bg,#0f1c15)}'),
     ('.pr{margin:0;background:#0f1c15;', '.pr{margin:0;background:var(--pr-legend-bg,#0f1c15);'),
     ('.pr .stage{min-height:600px;max-height:none}', '.pr .stage{min-height:var(--pr-stage-min-m,600px);max-height:none}'),
     ('.pr .intro{top:56px;', '.pr .intro{top:calc(56px + var(--pr-safe-top,0px));'),
     ('.pr .bar{top:10px;', '.pr .bar{top:calc(10px + var(--pr-safe-top,0px));'),
    ]
    for a, b in rep:
        n = css.count(a)
        assert n == 1, ('css anchor', n, a)
        css = css.replace(a, b)
    css = '/* PlotNua Possibility Reveal · L2B v2 · homepage component (generated by build_reveal_component.py; do not hand-edit) */\n' + css

    # ---------------- JS ----------------
    js = rd('assets/reveal.js')
    def jrep(a, b, n=1):
        global js
        c = js.count(a); assert c == n, ('js anchor', c, a); js = js.replace(a, b)
    jrep('  var $ = function (s, r) { return (r || document).querySelector(s); };',
         '  var ROOT = document.querySelector("[data-pr-root]");\n  if (!ROOT) return;\n  var $ = function (s, r) { return (r || ROOT).querySelector(s); };')
    jrep('document.querySelectorAll(".scene")', 'ROOT.querySelectorAll(".scene")', 2)
    jrep('document.querySelectorAll(".cam source, .cam img")', 'ROOT.querySelectorAll(".cam source, .cam img")')
    jrep('  document.addEventListener("click", function (e) {\n',
         '  document.addEventListener("click", function (e) {\n    if (!ROOT.contains(e.target)) return;\n')
    jrep('  document.addEventListener("keydown", function (e) {\n',
         '  document.addEventListener("keydown", function (e) {\n    if (e.target !== document.body && !ROOT.contains(e.target)) return;\n')
    for i in IDS:
        js = re.sub(r'(["\'])#%s\b' % re.escape(i), r'\1#' + P + i, js)
        js = re.sub(r'id=\\?"%s"' % re.escape(i), 'id="' + P + i + '"', js)
        js = js.replace('.id === "%s"' % i, '.id === "%s%s"' % (P, i))
    js = js.replace('"#sc-" +', '"#' + P + 'sc-" +')
    # the root is the component element itself (querySelector inside it cannot return it)
    assert js.count('var pn = $("#pr-pn")') == 1
    js = js.replace('var pn = $("#pr-pn")', 'var pn = ROOT')
    assert js.count('"#pr-sc-" +') == 1
    js = '/* PlotNua Possibility Reveal · L2B v2 · homepage component (generated; do not hand-edit) */\n' + js
    data = rd('assets/reveal-data.js')

    # ---------------- markup ----------------
    h = rd('index.html')
    body = h[h.index('<a class="skip"'):h.index('</noscript>') + len('</noscript>')]
    for i in IDS:
        body = re.sub(r'id="%s"' % re.escape(i), 'id="%s%s"' % (P, i), body)
        body = re.sub(r'url\(#%s\)' % re.escape(i), 'url(#%s%s)' % (P, i), body)
        body = re.sub(r'aria-(labelledby|controls)="%s"' % re.escape(i), r'aria-\1="%s%s"' % (P, i), body)
        body = body.replace('href="#%s"' % i, 'href="#%s%s"' % (P, i))
    body = body.replace('<main class="pn" id="pr-pn" data-mode="entry">', '<div class="pr pn" id="pr-pn" data-mode="entry" data-pr-root>')
    # the prototype's skip link sits before <main>; move it inside the component root so its scoped styles apply
    skip = re.search(r'<a class="skip" href="#pr-paths">[^<]*</a>\s*', body).group(0)
    body = body.replace(skip, '', 1).replace('data-pr-root>', 'data-pr-root>\n  ' + skip.strip(), 1)
    assert body.count('</main>') == 1; body = body.replace('</main>', '</div>')
    WORD_OLD = 'Drawings are illustrations, not part of the photograph.'
    WORD_NEW = 'Drawings are illustrations, not part of the picture.'
    assert body.count(WORD_OLD) == 1, 'founder wording change: anchor not found exactly once'
    body = body.replace(WORD_OLD, WORD_NEW)
    assert body.count('<h1 id="pr-introTitle">') == 1
    body = body.replace('<h1 id="pr-introTitle">', '<h2 class="pr-title" id="pr-introTitle">').replace('power station.</h1>', 'power station.</h2>')
    body = body.replace('img/house-L1-L2A', 'assets/possibility-reveal/img/house-L1-L2A')
    # the noscript sits inside the component root
    nos = body[body.index('<noscript>'):]; body = body[:body.index('<noscript>')].rstrip()
    assert body.endswith('</div>'); body = body[:-len('</div>')] + '  ' + nos + '\n</div>'
    js, body = h3_extend(js, body)
    js, body = h5_extend(js, body)
    snippet = '<!-- POSSIBILITY REVEAL · L2B v2 component (generated by build_reveal_component.py; do not hand-edit) -->\n' + body + '\n<!-- /POSSIBILITY REVEAL -->'

    return {'assets/possibility-reveal/reveal.css': css, 'assets/possibility-reveal/reveal.js': js,
            'assets/possibility-reveal/reveal-data.js': data, 'assets/possibility-reveal/stage-snippet.part': snippet}

ROOTDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORD = os.path.join(ROOTDIR, 'assets/possibility-reveal/component-record.json')
H3_FILES = ['assets/possibility-reveal/garden.css', 'assets/possibility-reveal/garden.js']
RESERVED = ['heroFrame','heroPhoto','heroCardsDock','heroCopy','heroWordmark','brandMark','atlasFigures','dCarousel',
            'pn-main','top','discover','research','libInfoBtn','libInfo','continuePanel','pnsOpen']
def sha(t): return hashlib.sha256(t.encode('utf-8') if isinstance(t, str) else t).hexdigest()
def die(m): print('REFUSED: ' + m); sys.exit(1)
def mount(index, snip):
    a = index.find('<!-- POSSIBILITY REVEAL · L2B v2 component'); b = index.find('<!-- /POSSIBILITY REVEAL -->')
    if a < 0 or b < 0: die('index.html has no POSSIBILITY REVEAL mount markers')
    return index[:a] + snip + index[b + len('<!-- /POSSIBILITY REVEAL -->'):]
def guard():
    bad = []
    rec = json.load(open(RECORD))
    files = {p: open(os.path.join(ROOTDIR, p), encoding='utf-8').read() for p in rec['outputs']}
    for p, t in files.items():
        if sha(t) != rec['outputs'][p]: bad.append(p + ' differs from its record (hand-edited?)')
    css_t, js_t, snip = files['assets/possibility-reveal/reveal.css'], files['assets/possibility-reveal/reveal.js'], files['assets/possibility-reveal/stage-snippet.part']
    data_t = files['assets/possibility-reveal/reveal-data.js']
    index = open(os.path.join(ROOTDIR, 'index.html'), encoding='utf-8').read()
    if snip not in index: bad.append('the snippet is not mounted verbatim in index.html')
    if index.count('<div class="hero-stage p4-stage" id="heroStage" data-hero="possibility-reveal">') != 1: bad.append('#heroStage is not the possibility-reveal slot')
    if len(re.findall(r'<h1\b', index)) != 1: bad.append('index.html must carry exactly one <h1>')
    if len(re.findall(r'<h1\b', snip)) > 1 or (re.search(r'<h1\b', snip) and '<h1 class="h5c-invite" id="pr-invite">' not in snip): bad.append('the component carries an <h1> other than the H5 invitation')   # H5 Phase C: the invitation is the page H1
    if '.pr .lens-over-intro' in css_t or '.pr.lens-over-intro' not in css_t: bad.append('the mobile headline fade-back rule is mis-scoped (the class is set on the component root itself)')
    if re.search(r'part of the photograph', snip): bad.append('the component calls the AI illustration a photograph (PN-FDR-2026-10-19-01, standard 3)')
    for i in re.findall(r'\bid="([^"]+)"', snip):
        if not i.startswith('pr-'): bad.append('un-prefixed id in the component: ' + i)
        if i in RESERVED: bad.append('reserved homepage id reused: ' + i)
    plain = re.sub(r'/\*.*?\*/', '', css_t, flags=re.S)
    def walk(t):
        i = 0
        while True:
            j = t.find('{', i)
            if j < 0: return
            head = t[i:j].strip()
            if head.startswith('@media') or head.startswith('@supports') or head.startswith('@keyframes'):
                d = 1; k = j + 1
                while d:
                    d += t[k] == '{'; d -= t[k] == '}'; k += 1
                if not head.startswith('@keyframes'): walk(t[j+1:k-1])
                elif not head.split()[1].startswith('pr-'): bad.append('unprefixed keyframes ' + head)
                i = k; continue
            for sel in head.split(','):
                if not sel.strip().startswith('.pr'): bad.append('unscoped CSS selector: ' + sel.strip()[:60])
            i = t.find('}', j) + 1
    walk(plain)
    if re.search(r'document\.(getElementById|querySelectorAll?)\((?!"\[data-pr-root\]")', js_t): bad.append('the script looks up elements outside its root')
    if 'commerceEnabled: false' not in data_t: bad.append('commerce is not hard-disabled')
    if re.search(r'status:\s*"active"', data_t): bad.append('an offer is active')
    bad += h3_guard(rec, snip, js_t, index)
    for p in H5_FILES + ['atlas-tools/possibility-reveal-h5-ps.js.part']:
        if sha(open(os.path.join(ROOTDIR, p), encoding='utf-8').read()) != (rec.get('h5_extension') or {}).get(p): bad.append(p + ' differs from its record')
    for p in H5_FILES:
        tag = ('<link rel="stylesheet" href="%s">' % p) if p.endswith('.css') else ('<script src="%s" defer></script>' % p)
        if index.count(tag) != 1: bad.append(p + ' is not loaded exactly once')
    return bad

def h3_guard(rec, snip, js_t, index):
    """H3 · the garden layers stay lazy, credited, scoped and on the lock chain."""
    bad = []
    ext = rec.get('h3_extension') or {}
    for p in H3_FILES:
        t = open(os.path.join(ROOTDIR, p), encoding='utf-8').read()
        if sha(t) != ext.get(p): bad.append(p + ' differs from its record (hand-edited?)')
    lj = open(os.path.join(ROOTDIR, 'assets/possibility-reveal/layers/layers.json'), encoding='utf-8').read()
    if sha(lj) != rec.get('h3_layers_record_sha256'): bad.append('the layer record changed without a component rebuild')
    lrec = json.loads(lj)
    for lid, label in GARDEN:
        if snip.count('<template data-layer="%s">' % lid) != 1: bad.append('garden layer %s is not mounted exactly once as a template' % lid)
        if snip.count('data-layer="%s" aria-pressed="false"' % lid) != 1: bad.append('the %s chip is not a switch' % label)
        for f in lrec['layers'][lid]['files']:
            if snip.count('assets/possibility-reveal/layers/' + f) < 1: bad.append(f + ' is not referenced')
    # every tile reference sits inside a <template>: nothing loads before a layer is switched on
    outside = re.sub(r'<template\b.*?</template>', '', snip, flags=re.S)
    if 'assets/possibility-reveal/layers/' in outside: bad.append('a garden tile is referenced outside a <template> (it would load with the page)')
    if 'href="assets/possibility-reveal/layers/' in index or 'rel="preload"' in snip: bad.append('a garden tile is preloaded')
    if re.search(r'<link[^>]+layers/garden-', index): bad.append('a garden tile is linked from the page head')
    # credit and disclosure, exact, beside L6 only
    if snip.count('<a href="%s">%s</a>' % (CREDIT_LINK, CREDIT)) != 1: bad.append('the TimberIN credit is not present exactly once, linked to timberin.com')
    plain = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', snip))
    if VISIBLE_CAPTION not in plain: bad.append('the approved visible caption is missing')
    if DISCLOSURE not in plain: bad.append('the approved accessible disclosure is missing')
    i6 = snip.index('<template data-layer="L6">'); ic = snip.index(CREDIT)
    strip = snip.find('<div class="h5c-strip" id="pr-strip">')
    if not (0 < ic - i6 < 1200 or (strip > i6 and 0 < ic - strip < 400)): bad.append('the credit does not sit beside the L6 layer or in the strip directly beneath the photograph')
    for lid in ('L3', 'L4', 'L5'):
        if abs(ic - snip.index('<template data-layer="%s">' % lid)) < 1500: bad.append('the TimberIN credit sits beside %s, which is not TimberIN imagery' % lid)
    if snip.replace(CREDIT, ' ').replace(DISCLOSURE, ' ').count('TimberIN') != 0: bad.append('TimberIN is named outside the credit and the disclosure')
    # the one camera hook, and nothing else changed in its place
    if js_t.count('window.PN_REVEAL_API = { play: play, home: home, state: state, frame: frame') != 1: bad.append('the camera hook is missing')   # H5 appends intro hooks
    css_g = open(os.path.join(ROOTDIR, 'assets/possibility-reveal/garden.css'), encoding='utf-8').read()
    plain_g = re.sub(r'/\*.*?\*/', '', css_g, flags=re.S)
    def walk_g(t):
        i = 0
        while True:
            j = t.find('{', i)
            if j < 0: return
            head = t[i:j].strip()
            if head.startswith('@media') or head.startswith('@supports'):
                d = 1; k = j + 1
                while d:
                    d += t[k] == '{'; d -= t[k] == '}'; k += 1
                walk_g(t[j+1:k-1]); i = k; continue
            for sel in head.split(','):
                if not sel.strip().startswith('.pr'): bad.append('unscoped garden CSS selector: ' + sel.strip()[:60])
            i = t.find('}', j) + 1
    walk_g(plain_g)
    js_g = open(os.path.join(ROOTDIR, 'assets/possibility-reveal/garden.js'), encoding='utf-8').read()
    if re.search(r'document\.(getElementById|querySelectorAll?)\((?!"\[data-pr-root\]")', js_g): bad.append('garden.js looks up elements outside the component root')
    for p in H3_FILES:
        tag = ('<link rel="stylesheet" href="%s">' % p) if p.endswith('.css') else ('<script src="%s" defer></script>' % p)
        if index.count(tag) != 1: bad.append(p + ' is not loaded exactly once by index.html')
    if index.find('<script src="assets/possibility-reveal/garden.js" defer></script>') < index.find('<script src="assets/possibility-reveal/reveal.js" defer></script>'):
        bad.append('garden.js must load after reveal.js')
    return bad

if __name__ == '__main__':
    SRC = sys.argv[sys.argv.index('--source') + 1] if '--source' in sys.argv else None
    CHECK = '--check' in sys.argv
    if CHECK:
        bad = guard()
        if SRC:
            fresh = transform()
            for p, t in fresh.items():
                if sha(t) != json.load(open(RECORD))['outputs'].get(p): bad.append(p + ' differs from a fresh transform of the prototype')
        if bad: die('CHECK: ' + '; '.join(bad[:8]))
        print('POSSIBILITY REVEAL COMPONENT · CHECK OK — outputs match their record, mounted verbatim, fully scoped, one H1, commerce off'
              + (', identical to a fresh transform' if SRC else ''))
        sys.exit(0)
    if not SRC: die('--source PROTOTYPE_DIR is required to build')
    outs = transform()
    for p, t in outs.items(): open(os.path.join(ROOTDIR, p), 'w', encoding='utf-8').write(t)
    proto = {f: hashlib.sha256(open(os.path.join(SRC, f), 'rb').read()).hexdigest() for f in ('index.html', 'assets/reveal.css', 'assets/reveal.js', 'assets/reveal-data.js')}
    json.dump({'schema': 'plotnua.possibility-reveal.component.v1', 'source': 'PlotNua Possibility Reveal L2B Prototype v2 (2026-10-18), unmodified except one founder-approved wording change (PN-FDR-2026-10-19-01) the H3 garden-layer stage (founder-approved H3, 20 Oct 2026; see h3_extend) and the H5 stage (H5 Phase C preview, 21 Oct 2026; see h5_extend)',
               'source_sha256': proto, 'outputs': {p: sha(t) for p, t in outs.items()},
               'h3_extension': {p: sha(open(os.path.join(ROOTDIR, p), encoding='utf-8').read()) for p in H3_FILES},
               'h5_extension': {p: sha(open(os.path.join(ROOTDIR, p), encoding='utf-8').read()) for p in H5_FILES + ['atlas-tools/possibility-reveal-h5-ps.js.part']},
               'h3_layers_record_sha256': sha(open(os.path.join(ROOTDIR, 'assets/possibility-reveal/layers/layers.json'), encoding='utf-8').read())}, open(RECORD, 'w'), indent=1)
    p = os.path.join(ROOTDIR, 'index.html'); idx = open(p, encoding='utf-8').read(); new = mount(idx, outs['assets/possibility-reveal/stage-snippet.part'])
    if new != idx: open(p, 'w', encoding='utf-8').write(new)
    print('POSSIBILITY REVEAL COMPONENT · built and mounted')
