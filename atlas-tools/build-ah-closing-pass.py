#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-ah-closing-pass.py

THE FINAL VISUAL PASS. Three measured faults, three corrections, no new
components and no new grid.

F1  THE ORPHAN. Measured at 1280: the four plates are 599px each in a
    two-column grid, and "Found something yourself? / Check with Atlas"
    is 263px, so it lands alone on a third row and reads as something
    appended after the set. It now spans both columns, closing the
    composition as a full-width final row of the SAME grid. No building
    is removed, none is promoted, and the grid is the shipped one.

F2  THE ABRUPT ENDING. #resultsDecide and #bydClose are revealed on the
    residential path, but renderResultsDecide() takes a PRODUCT and
    hides the section when there is none — so Additional Home showed no
    "Three things to know before you decide" and no closing panel at
    all. pnRenderResidentialDecide() builds the SAME .byd-point
    articles, through the SAME bydEl() helper, in the SAME .byd-points
    host, with the same number / category / question / body / action
    shape. No markup and no CSS is recreated.

    Point 02 names the outstanding conditions ATLAS ALREADY RECORDED
    (fit.verdictCheck) and invents no planning rule. Point 03 describes
    exclusions as POSSIBILITIES and states no total — the builder
    refuses on any currency figure in the added strings.

F3  THE BLANK PLATES. The three no-image frames were flat 329px fields.
    They keep the frame and the honest caption but gain the page's own
    hairline inset and a centred Atlas-less rule, so they read as a
    considered absence rather than an empty box. Existing tokens only.

Usage: python3 atlas-tools/build-ah-closing-pass.py [--check|--revert]
"""

import hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-closingpass"
BASELINE = "0a9246016b12713d"

SCOPE = "#screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults"

# --------------------------------------------------------------- F2 renderer
D1_FIND = "  function renderResultsDecide(product){\n"

D1_REPL = """  /* ===== THE RESIDENTIAL CLOSING EXPERIENCE ===========================

     THE SAME COMPONENTS, A DIFFERENT SUBJECT. renderResultsDecide() is
     bound to a product and hides itself without one, which is why the
     Additional Home page stopped after the options. This builds the
     identical .byd-point articles — bydEl(), .byd-head, .byd-num,
     .byd-cat, .byd-q, .byd-body, .byd-act — into the identical
     #bydPoints host, and then lets the shipped #bydClose panel stand.

     EVERY CLAIM IS THE ASSESSMENT'S OWN. Point 02 lists the conditions
     Atlas has already recorded as outstanding; where it has recorded
     none, the card says so rather than inventing one. Point 03 names
     what a published building price may not include, as possibilities,
     and states no figure. */
  function pnResidentialDecidePoints(fit){
    /* The recorded conditions are full sentences. Joining them raw gave
       "yet.;" and "it..", so each is trimmed of its terminal stop and the
       list is joined with a semicolon. Wording is untouched. */
    const open = ((fit && fit.verdictCheck) || []).map(function(t){
      return String(t).trim().replace(/\.+$/, '');
    }).filter(Boolean);
    const pts = [];

    pts.push({
      key: 'property',
      category: 'Your property',
      question: 'Where could an additional home actually go?',
      body: 'The assessment measures what the regulations allow. Where a '
          + 'building could physically sit is a separate question: how you '
          + 'reach the far end of the garden, what the boundaries do, which '
          + 'way the space faces, and what is already in the way. The 3D '
          + 'view of your property is the quickest way to think it through.',
      actionLabel: 'Open the 3D view \\u2192',
      action: function(){
        const t = document.getElementById('yourProperty');
        if (!t) return;
        try { if (t.tagName === 'DETAILS') t.open = true; } catch (e) {}
        t.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });

    pts.push({
      key: 'planning',
      category: 'Planning',
      question: 'What still needs to be confirmed?',
      body: (open.length
        ? ('This is an assessment against the published conditions, not a '
           + 'planning decision and not a guarantee of eligibility. Atlas '
           + 'has ' + (open.length === 1 ? 'one condition' : open.length
           + ' conditions') + ' still open on your answers: '
           + open.join('; ') + '. Your local authority is the only body '
           + 'that can settle any of it.')
        : ('This is an assessment against the published conditions, not a '
           + 'planning decision and not a guarantee of eligibility. Atlas '
           + 'has recorded no outstanding condition on what you told us, '
           + 'which is not the same as approval. Your local authority is '
           + 'the only body that can settle that.')),
      actionLabel: 'See what Atlas checked \\u2192',
      action: function(){
        const t = document.getElementById('aboutSupplier');
        if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });

    pts.push({
      key: 'truecost',
      category: 'True cost',
      question: 'What would an additional home actually cost?',
      body: 'A published building price is the building. Depending on the '
          + 'supplier and the site it may not include foundations, site '
          + 'preparation, water, drainage or electrical connections, '
          + 'delivery, craning, installation or finishing. Atlas does not '
          + 'hold a confirmed scope for every option here, so treat each '
          + 'of those as a question to put to the supplier rather than a '
          + 'cost that is already counted.'
    });

    return pts;
  }

  function pnRenderResidentialDecide(fit){
    const sec = els.resultsDecide;
    if (!sec || !els.bydPoints) return 0;
    const points = pnResidentialDecidePoints(fit);
    if (!points.length) return 0;
    sec.removeAttribute('data-byd-product');
    /* OWNERSHIP. renderResultsDecide(null) runs later on this journey and
       hides the section and empties the host — measured: the points
       rendered and were then cleared. The marker tells it this section
       belongs to the property result, not to an absent product. */
    sec.setAttribute('data-pn-residential-decide', '1');
    els.bydPoints.innerHTML = '';
    points.forEach(function(p, i){
      const art = bydEl('article', 'byd-point');
      art.setAttribute('data-key', p.key);
      const head = bydEl('div', 'byd-head');
      head.appendChild(bydEl('span', 'byd-num', ('0' + (i + 1)).slice(-2)));
      head.appendChild(bydEl('span', 'byd-cat', p.category));
      art.appendChild(head);
      art.appendChild(bydEl('h3', 'byd-q', p.question));
      art.appendChild(bydEl('p', 'byd-body', p.body));
      if (p.actionLabel && p.action) {
        const b = bydEl('button', 'byd-act', p.actionLabel);
        b.type = 'button';
        b.addEventListener('click', p.action);
        art.appendChild(b);
      }
      els.bydPoints.appendChild(art);
    });
    sec.hidden = false;
    /* THE CLOSING BEAT, ADAPTED. The panel, the heading and the Ask
       control are the shipped nodes; only the one supporting sentence
       changes, because this journey narrowed a PROPERTY question. */
    const cb = document.querySelector('#bydClose .byd-close-body');
    if (cb) cb.textContent = 'Atlas has taken your property as far as a '
      + 'published assessment can. If there is still something you want to '
      + 'understand before you go further, ask us.';
    const cl = document.getElementById('bydClose');
    if (cl) cl.hidden = false;
    try { if (typeof bydRehomeAsk === 'function') bydRehomeAsk(); } catch (e) {}
    return points.length;
  }

  function renderResultsDecide(product){
"""

# --------------------------------------------------------- F2 call site
D2_FIND = "      if (pnVerdictShown) pnRenderPropertyAssessment(fit);\n"
D2_REPL = """      if (pnVerdictShown) pnRenderPropertyAssessment(fit);
      /* THE CLOSING EXPERIENCE. Same section, same components, the
         property's own three topics. Rendered after the product branch,
         which hides the section when there is no product. */
      if (pnVerdictShown) pnRenderResidentialDecide(fit);
"""

# ------------------------------------------------------------- F1 + F3 CSS
D3_FIND = """  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media:has(img.pn-image-fallback)::after{
    content:'No image Atlas may publish';
    position:absolute; inset:auto 0 0 0; padding:0 12px 10px;
    font-size:var(--pn-w-meta); letter-spacing:.06em;
    text-transform:uppercase; color:var(--pn-stone);
  }
"""

D3_REPL = """  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media:has(img.pn-image-fallback)::after{
    content:'No image Atlas may publish';
    position:absolute; inset:auto 0 0 0; padding:0 12px 10px;
    font-size:var(--pn-w-meta); letter-spacing:.06em;
    text-transform:uppercase; color:var(--pn-stone);
  }
  /* F3 - THE ABSENCE, COMPOSED. A flat field read as an unfinished box.
     The frame keeps an inset hairline and a short centred rule in the
     page's own hair tone, so the plate reads as a considered absence.
     Existing tokens only: no artwork, no mark, no supplier imagery. */
  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media:has(img.pn-image-fallback){
    box-shadow:inset 0 0 0 1px var(--pn-hair);
    background:linear-gradient(180deg,
      color-mix(in srgb, var(--pn-hair) 55%, transparent) 0%,
      var(--pn-hair) 100%);
  }
  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .results-gallery-media:has(img.pn-image-fallback)::before{
    content:''; position:absolute; left:50%; top:50%;
    width:48px; height:1px; margin-left:-24px;
    background:var(--pn-stone); opacity:.35;
  }
  /* F1 - CHECK WITH ATLAS CLOSES THE COMPOSITION. Measured at 1280: the
     four plates are 599px in two columns and this card is 263px, so it
     sat alone on a third row looking appended. It spans both columns and
     becomes the grid's closing row. The grid itself is unchanged, all
     four buildings stay, and none is promoted or demoted. */
  #screen-match-results #matchPrimary[data-pn-verdict] ~ #altResults
    .match-bring-your-own{ grid-column:1 / -1; }
"""


D4_FIND = "    if (!product) { sec.hidden = true; els.bydPoints.innerHTML = ''; return 0; }\n"
D4_REPL = """    /* THE PROPERTY RESULT OWNS THIS SECTION WHEN IT RENDERED IT. Absent a
       product this cleared the section unconditionally, which erased the
       Additional Home closing experience a moment after it was built. A
       Garden Room render is unaffected: it never sets the marker. */
    if (!product) {
      if (sec.getAttribute('data-pn-residential-decide') === '1') return 0;
      sec.hidden = true; els.bydPoints.innerHTML = ''; return 0;
    }
"""

EDITS = [
    ("D1  the residential closing renderer", D1_FIND, D1_REPL),
    ("D2  the call site", D2_FIND, D2_REPL),
    ("D3  the no-image plate and the closing grid row", D3_FIND, D3_REPL),
    ("D4  the null branch respects residential ownership", D4_FIND, D4_REPL),
]

# Shipped components that must still be referenced.
FLOOR = ["bydEl(", "byd-point", "byd-num", "byd-cat", "byd-q", "byd-body",
         "byd-act", "bydClose", "bydPoints", "renderResultsDecide(",
         "pnAuthorisedImage(", "pn-image-fallback"]

# Homeowner-visible text may not invent money, approval or a medium.
FORBIDDEN = ["€", "approved", "permission granted", "guarantees",
             "photograph", "render", "visualisation", "total cost of"]


def sha16(s): return hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if mode == "--revert":
        if not os.path.exists(BAK): raise SystemExit("no backup")
        open(PAGE, "w", encoding="utf-8").write(open(BAK, encoding="utf-8").read())
        print("reverted."); return

    src = open(PAGE, encoding="utf-8").read()
    base = sha16(src)
    if base != BASELINE and not os.path.exists(BAK):
        raise SystemExit("REFUSED: baseline %s, expected %s" % (base, BASELINE))

    out = src
    for name, find, repl in EDITS:
        n = out.count(find)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matched %d" % (name, n))
        out = out.replace(find, repl, 1)

    added = "\n".join(e[2] for e in EDITS)
    added_code = re.sub(r"/\*.*?\*/", " ", added, flags=re.S)
    literals = " ".join(re.findall(r"'((?:[^'\\]|\\.)*)'", added_code)).lower()

    # G1 — no invented money, approval or medium in homeowner-visible text.
    for w in FORBIDDEN:
        if w.lower() in literals:
            raise SystemExit("REFUSED: homeowner-visible text contains %r" % w)
    if re.search(r"\d[\d,]*\s*(euro|eur)\b", literals):
        raise SystemExit("REFUSED: a cost figure was written into the copy")

    # G2 — the planning point must be driven by recorded evidence.
    if "fit.verdictCheck" not in added_code:
        raise SystemExit("REFUSED: the planning point does not read the "
                         "conditions Atlas recorded")

    # G3 — shipped components still referenced, never fewer.
    for t in FLOOR:
        if out.count(t) < src.count(t):
            raise SystemExit("REFUSED: a shipped reference was lost: %s" % t)

    # G4 — no new component class is introduced.
    for cls in re.findall(r"bydEl\('[a-z0-9]+',\s*'([a-z0-9 -]+)'", added_code):
        for one in cls.split():
            if one not in src:
                raise SystemExit("REFUSED: %r is not an existing class" % one)

    # G5 — every added CSS rule is scoped to the residential grid.
    css = D3_REPL
    for rule in re.split(r"\}\s*", re.sub(r"/\*.*?\*/", " ", css, flags=re.S)):
        flat = re.sub(r"\s+", " ", rule).strip()
        if not flat or "{" not in flat: continue
        if SCOPE not in flat:
            raise SystemExit("REFUSED: unscoped rule added:\n%s" % flat[:140])

    # G6 — re-pointed. renderResultsDecide() now gains ONE guard on its
    #      no-product branch; everything the Garden Room path executes must
    #      be byte-identical, so the product branch is compared directly.
    def product_branch(t):
        a = t.index("function renderResultsDecide(product){")
        a = t.index("sec.setAttribute('data-byd-product'", a)
        return t[a:t.index("function bydRehomeAsk(")]
    if product_branch(src) != product_branch(out):
        raise SystemExit("REFUSED: the Garden Room product branch changed")
    #      The marker must be BOTH set by the residential renderer AND read
    #      by the null branch; reading one it never sets protects nothing.
    if "setAttribute('data-pn-residential-decide', '1')" not in out:
        raise SystemExit("REFUSED: the ownership marker is never set")
    if "getAttribute('data-pn-residential-decide')" not in out:
        raise SystemExit("REFUSED: the ownership marker is never read")

    # G7 — syntax, before anything is written.
    for i, blk in enumerate(re.findall(
            r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", out, re.S)):
        if not blk.strip(): continue
        tmp = os.path.join(ROOT, ".pn-cp-%d.mjs" % i)
        open(tmp, "w", encoding="utf-8").write(blk)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            raise SystemExit("REFUSED: script %d does not parse, nothing "
                             "written:\n%s" % (i, r.stderr[:400]))

    if mode == "--check":
        print("CHECK ONLY. %s -> %s, %+d lines, 7 guards pass"
              % (base, sha16(out), out.count("\n") - src.count("\n")))
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied. %s -> %s" % (base, sha16(out)))


if __name__ == "__main__":
    main()
