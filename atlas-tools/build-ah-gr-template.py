#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-ah-gr-template.py

THE ADDITIONAL HOME RESULT, REBUILT ON THE GARDEN ROOM TEMPLATE.

Measured in the browser at 1280 (panel 910px), the Garden Room hero is:

    .results-hero-inner
      .rh-identity        h2.results-hero-name 66.56px, then a one-line
                          .rh-identity-meta (org, separator, price)
      .rh-split           flex ROW, 26px gap
        .pn-media-col     582px — the large visual
        .results-hero-body 302px — ONE editorial sentence (48px), the
                          actions, then .hero-secondary. 192px in total.

Every figure and every finding lives ONCE, below, in the Atlas Assessment
dossier. The Additional Home hero had become 810px of figures, a pull
quote and a confirmed-findings list that the dossier then repeated. This
build makes it the Garden Room composition.

WHAT CHANGES

 T1  The hero media column carries the AUTHORISED BIOBUILDS Wanderlust
     exterior image, resolved through pnAuthorisedImage() — the governed
     reader — from the Wanderlust candidate already in the result set.
     No URL is hardcoded: if the rights gate refuses the asset, no media
     column is appended and the hero keeps the shipped is-fieldonly
     treatment. The caption is the founder's exact wording, the credit is
     attached by the shipped pnAttachImageCredit(), and the required link
     back to biobuilds.com is rendered beside it.

     THE MEDIUM IS NOT CLAIMED. The BIOBUILDS grant records that Atlas
     does not know whether the model imagery is photographic or a
     visualisation, and forbids PlotNua describing it as either. The
     caption therefore says neither, and the builder REFUSES if the words
     photograph/photo/render/visualisation appear in the block it adds.

     IT IS NOT A RECOMMENDATION. The caption says so in terms, and the
     builder refuses if best/strongest/preferred/recommended/top-ranked
     appear in the added block.

 T2  The hero stops carrying evidence. The figures row, the second
     detail paragraph and the confirmed-findings tick list leave the
     hero; they are already rendered by the dossier. The planning
     boundary stays: it is a condition on the headline, not evidence, and
     it appears nowhere else.

 T3  The dossier masthead uses the EXACT Garden Room Atlas mark — the
     same asset, the same 60x60 dimensions, the same pn-atlas-still
     markup and the same pnAtlasHydrate() call — in place of the
     alternative template clone that rendered it oversized and wrapped
     the wordmark.

 T4  The withdrawn Cesium hero mount goes, with the commentary that
     recorded it. It is obsolete: the media column now has a subject.

Usage: python3 atlas-tools/build-ah-gr-template.py [--check|--revert]
"""

import hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
BAK = PAGE + ".bak-grtemplate"
BASELINE = "852a3ca0b5a6ea4e"

# ----------------------------------------------------------------- T1 + T2 + T4
# The whole media/body construction is replaced in one anchored block, from
# the start of the withdrawn-Cesium commentary to the end of the trust call.

T1_FIND = """    /* THE HERO'S VISUAL IS THE HOMEOWNER'S OWN PROPERTY.

       Garden Room fills this column with the product's photograph. The
       Additional Home result is not a product, and a supplier's building
       must never stand in for someone's garden — so the column carries the
       one visual that genuinely IS the subject: the Cesium view of their
       property, which this page already builds for Sun & Light.

       NO SECOND 3D SYSTEM. #resultsMapViewport is MOVED, not cloned, and
       activateResultsMapViewport() is the same initialiser Sun & Light
       calls. The panel below keeps its season and time controls and drives
       the same viewport.

       THE FALLBACK IS THE SHIPPED ONE. If the viewport is absent, or the
       property was never geocoded, no media column is appended at all and
       the hero stays is-fieldonly — the exact treatment the product hero
       uses when Atlas holds no photograph it may publish. Nothing half-built
       is ever shown. */
"""

T1_REPL = """    /* THE HERO'S VISUAL — AN AUTHORISED EXAMPLE, NOT THE RESULT.

       Garden Room fills this column with the recommended building's
       picture. The Additional Home result is a PROPERTY VERDICT, and no
       building has been established as better than the others, so nothing
       here may read as a recommendation.

       What this column carries is an illustrative example of what an
       additional home in this range looks like: the one asset PlotNua
       holds written permission to show. It is resolved through
       pnAuthorisedImage(), the governed reader every other surface uses,
       from the candidate already in this result set — so the rights gate
       decides, not this function. No URL is written here.

       THE MEDIUM IS NOT CLAIMED. The BIOBUILDS grant records that Atlas
       does not know whether the model imagery is photographic or a
       visualisation, and that until BIOBUILDS answer, no PlotNua surface
       may describe it as either. The caption says neither.

       THE GRANT'S CONDITIONS ARE RENDERED WITH IT. The credit is attached
       by the shipped pnAttachImageCredit(); the required link back to the
       supplier sits beside the caption. If the reader refuses the asset,
       no media column is appended and the hero keeps the shipped
       is-fieldonly treatment. Nothing half-built is ever shown. */
"""

T2_FIND = """    const PN_HERO_3D_ENABLED = false;
    const pnVp = PN_HERO_3D_ENABLED && document.getElementById('resultsMapViewport');
    const pnLocated = !!(window.pnLastGeocode || document.getElementById('propConfirmPlace')
      && document.getElementById('propConfirmPlace').textContent.trim());
    if (pnVp && pnLocated) {
      const mediaCol = document.createElement('div');
      mediaCol.className = 'pn-media-col';
      const frame = document.createElement('div');
      frame.className = 'results-hero-media';
      frame.appendChild(pnVp);
      mediaCol.appendChild(frame);
      split.appendChild(mediaCol);
      wrap.classList.remove('is-fieldonly');
      try { if (typeof activateResultsMapViewport === 'function')
              activateResultsMapViewport(); } catch (e) {}
    }

    const body = document.createElement('div');
    body.className = 'results-hero-body';
    const factsRow = pnVerdictFactsRow(fit && fit.verdictFacts);
    if (factsRow) body.appendChild(factsRow);
    if (parts[1]) {
      const ed = document.createElement('p');
      ed.className = 'results-hero-editorial';
      ed.textContent = parts[1];
      body.appendChild(ed);
    }
    if (parts[2]) {
      const detail = document.createElement('p');
      detail.className = 'hm-calm';
      detail.textContent = parts[2];
      body.appendChild(detail);
    }
    const trust = pnVerdictTrust(fit && fit.verdictKnown,
                                 (fit && fit.verdictOpenCount) || 0);
    if (trust) body.appendChild(trust);
"""

T2_REPL = """    const pnEx = pnVerdictExampleImage(results);
    if (pnEx) {
      const mediaCol = document.createElement('div');
      mediaCol.className = 'pn-media-col';
      const frame = document.createElement('div');
      frame.className = 'results-hero-media';
      const img = document.createElement('img');
      img.src = pnEx.im.url;
      img.alt = pnEx.im.alt || '';
      img.loading = 'lazy';
      img.decoding = 'async';
      frame.appendChild(img);
      pnAttachImageCredit(frame, pnEx.im);
      mediaCol.appendChild(frame);
      /* THE CAPTION. Names the building and the courtesy, claims no medium,
         and says in terms that it is not a recommendation. */
      const cap = document.createElement('p');
      cap.className = 'pn-hero-example-note';
      const capName = document.createElement('span');
      capName.className = 'pn-hero-example-name';
      capName.textContent = pnEx.label + ' \\u00b7 Image courtesy of ' + pnEx.im.supplier;
      cap.appendChild(capName);
      const capRole = document.createElement('span');
      capRole.className = 'pn-hero-example-role';
      capRole.textContent = 'An example of an additional home in this range. '
        + 'Atlas has not placed it ahead of the other options.';
      cap.appendChild(capRole);
      if (pnEx.site) {
        const capLink = document.createElement('a');
        capLink.className = 'pn-hero-example-link';
        capLink.href = pnEx.site;
        capLink.target = '_blank';
        capLink.rel = 'noopener noreferrer';
        capLink.textContent = pnEx.im.supplier + ' \\u2192';
        cap.appendChild(capLink);
      }
      mediaCol.appendChild(cap);
      split.appendChild(mediaCol);
      wrap.classList.remove('is-fieldonly');
    }

    /* THE BODY IS ONE SENTENCE, AS GARDEN ROOM'S IS.

       The figures, the confirmed findings and the outstanding checks used
       to be rendered here AND again in the dossier below. They belong to
       the dossier: it is the page's single authoritative account of what
       Atlas found. The hero introduces the verdict and points at it. */
    const body = document.createElement('div');
    body.className = 'results-hero-body';
    if (parts[1]) {
      const ed = document.createElement('p');
      ed.className = 'results-hero-editorial';
      ed.textContent = parts[1];
      body.appendChild(ed);
    }
"""

# The renderer needs the result set to find the authorised example.
T3_FIND = "  function pnRenderVerdictHero(parts, fit){\n"
T3_REPL = """  /* THE ONE AUTHORISED EXAMPLE IN THIS RESULT SET.

     Walks the candidates and returns the first whose imagery the governed
     reader allows. The gate is pnAuthorisedImage(), unchanged: it checks
     credit, supplier, rights record, the supplier's own permitted prefix
     and https. A supplier whose grant does not enumerate the asset is
     refused here exactly as it is refused on a card. */
  function pnVerdictExampleImage(results){
    if (!results || !results.length) return null;
    for (let i = 0; i < results.length; i++) {
      const p = results[i] && (results[i].product || results[i]);
      if (!p) continue;
      const im = pnAuthorisedImage(p);
      if (!im) continue;
      return { im: im, label: p.name || im.supplier,
               site: (im.permittedPrefix && /^https:\\/\\/[^\\/]+/.exec(im.permittedPrefix)
                      || [null])[0] };
    }
    return null;
  }

  function pnRenderVerdictHero(parts, fit, results){
"""

# The call site passes the result set through.
T4_FIND = "        && pnRenderVerdictHero(fit && fit.verdictParts, fit);\n"
T4_REPL = "        && pnRenderVerdictHero(fit && fit.verdictParts, fit, results);\n"

# ----------------------------------------------------------------------- T5
# The dossier masthead uses the exact Garden Room mark.

T5_FIND = """    const lead = aaEl('span', 'aa-mast-lead');
    try {
      const tpl = document.getElementById('pn-atlas-a-template');
      if (tpl && tpl.content) lead.appendChild(tpl.content.cloneNode(true));
    } catch (e) {}
    lead.appendChild(aaEl('span', 'aa-mast-l', 'Atlas assessment'));
"""

T5_REPL = """    const lead = aaEl('span', 'aa-mast-lead');
    /* THE EXACT GARDEN ROOM ATLAS MARK.

       This previously cloned #pn-atlas-a-template, a different asset with
       no intrinsic size, which rendered the symbol oversized and pushed
       the wordmark onto a second line. These are the same six lines the
       Garden Room masthead uses, against the same approved asset, at the
       same 60x60, with the same hydration call — not an approximation of
       them. */
    const mastMark = aaEl('span', 'pn-atlas-still');
    const mastImg = document.createElement('img');
    mastImg.className = 'pn-atlas-still-img';
    mastImg.src = 'assets/brand/atlas-final-static-approved-transparent.png';
    mastImg.alt = '';
    mastImg.width = 60; mastImg.height = 60;
    mastImg.decoding = 'async';
    mastImg.setAttribute('aria-hidden', 'true');
    mastMark.appendChild(mastImg);
    lead.appendChild(mastMark);
    lead.appendChild(aaEl('span', 'aa-mast-l', 'Atlas assessment'));
    if (window.pnAtlasHydrate) window.pnAtlasHydrate(lead);
"""

# ----------------------------------------------------------------------- T6
# The caption's own spacing. Scoped to the residential verdict hero.

T6_FIND = "  #screen-match-results #altResults > *{ height:100%; }\n"
T6_REPL = """  #screen-match-results #altResults > *{ height:100%; }
  /* THE EXAMPLE CAPTION. Three stacked lines under the hero visual, in the
     page's existing meta and caption sizes. Scoped to the residential
     verdict hero, so the Garden Room hero cannot inherit it. */
  #screen-match-results #matchPrimary[data-pn-verdict] .pn-hero-example-note{
    display:flex; flex-direction:column; gap:4px;
    margin:10px 0 0; padding:0;
  }
  #screen-match-results #matchPrimary[data-pn-verdict] .pn-hero-example-name{
    font-size:var(--pn-w-caption); letter-spacing:.06em; color:var(--pn-ink);
  }
  #screen-match-results #matchPrimary[data-pn-verdict] .pn-hero-example-role{
    font-size:var(--pn-w-meta); color:var(--pn-stone); line-height:1.5;
  }
  #screen-match-results #matchPrimary[data-pn-verdict] .pn-hero-example-link{
    font-size:var(--pn-w-meta); color:var(--pn-stone);
  }
"""

EDITS = [
    ("T1  the media column's account", T1_FIND, T1_REPL),
    ("T2  the authorised example replaces the withdrawn 3D mount", T2_FIND, T2_REPL),
    ("T3  the example resolver, and the renderer takes the result set", T3_FIND, T3_REPL),
    ("T4  the call site passes the result set", T4_FIND, T4_REPL),
    ("T5  the dossier masthead uses the exact Garden Room mark", T5_FIND, T5_REPL),
    ("T6  the caption's spacing", T6_FIND, T6_REPL),
]

# --------------------------------------------------------------------- GUARDS

# Words the grant forbids, and words that would make the example a ranking.
FORBIDDEN = ["photograph", "photo ", "photographic", "render", "rendering",
             "visualisation", "visualization", "best option", "strongest",
             "preferred", "highest-ranked", "top-ranked", "recommended building",
             "we'd start with"]

# Governed machinery that must still be referenced after the build.
FLOOR = ["pnAuthorisedImage(", "pnAttachImageCredit(", "pnRenderPropertyAssessment(",
         "pnLensRailAfterOptions(", "data-pn-verdict", "aaEl(", "aaFig(",
         "pnAtlasHydrate", "atlas-final-static-approved-transparent.png"]

# Must be GONE: the hero may no longer render the evidence.
MUST_VANISH_FROM_HERO = ["pnVerdictFactsRow(fit", "pnVerdictTrust(fit",
                         "PN_HERO_3D_ENABLED"]


def sha16(s): return hashlib.sha256(s.encode()).hexdigest()[:16]


def hero_block(src):
    a = src.index("function pnRenderVerdictHero(")
    b = src.index("function pnLensRailAfterOptions(")
    return src[a:b]


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

    # G1 — NOTHING THE HOMEOWNER READS may claim a medium or a ranking.
    #      Scanned on the STRING LITERALS of the added block, not its prose:
    #      a comment explaining why the medium cannot be claimed must be
    #      allowed to name the thing it is forbidding.
    added = "\n".join(l for e in EDITS for l in e[2].splitlines()
                      if l not in e[1].splitlines())
    added_code = re.sub(r"/\*.*?\*/", " ", added, flags=re.S)
    literals = " ".join(re.findall(r"'((?:[^'\\]|\\.)*)'", added_code)
                        + re.findall(r'"((?:[^"\\]|\\.)*)"', added_code)).lower()
    for w in FORBIDDEN:
        if w in literals:
            raise SystemExit("REFUSED: homeowner-visible text uses a forbidden "
                             "word: %r\nThe grant forbids claiming the medium, "
                             "and the example must not read as a "
                             "recommendation." % w)

    # G2 — no URL is hardcoded; the rights reader decides.
    if re.search(r"https://(?!www\.w3\.org)[\w.-]*biobuilds", added, re.I):
        raise SystemExit("REFUSED: a supplier URL was written into the page; "
                         "the asset must come from pnAuthorisedImage()")

    # G3 — the governed machinery must still be referenced.
    for t in FLOOR:
        if out.count(t) < src.count(t) or t not in out:
            raise SystemExit("REFUSED: a governed reference was lost: %s" % t)

    # G4 — the hero must no longer render the dossier's evidence.
    hb = hero_block(out)
    for t in MUST_VANISH_FROM_HERO:
        if t in hb:
            raise SystemExit("REFUSED: the hero still carries %s; the evidence "
                             "belongs to the dossier alone" % t)

    # G5 — the dossier must still carry it.
    db = out[out.index("function pnRenderPropertyAssessment("):
              out.index("window.__PN_RENDER_RESIDENTIAL__")]
    for t in ["verdictFacts", "verdictKnown", "verdictCalc", "verdictCheck"]:
        if t not in db:
            raise SystemExit("REFUSED: the dossier lost %s" % t)

    # G6 — the alternative Atlas template CLONE must be gone from the dossier.
    #      Matched on the lookup, not the name: the comment that records why
    #      the clone was wrong is entitled to name what it replaced.
    db_code = re.sub(r"/\*.*?\*/", " ", db, flags=re.S)
    if "pn-atlas-a-template" in db_code:
        raise SystemExit("REFUSED: the dossier still clones the alternative "
                         "Atlas template")
    #      and it must now use the Garden Room asset at the Garden Room size.
    for t in ["atlas-final-static-approved-transparent.png",
              "pn-atlas-still", "mastImg.width = 60", "pnAtlasHydrate"]:
        if t not in db_code:
            raise SystemExit("REFUSED: the dossier masthead is not the Garden "
                             "Room implementation; missing %s" % t)

    # G7 — Garden Room's own hero and masthead are untouched.
    gr = src[src.index("/* ---- (1) MASTHEAD"):]
    gr_out = out[out.index("/* ---- (1) MASTHEAD"):]
    if gr != gr_out:
        raise SystemExit("REFUSED: the Garden Room masthead region changed")

    # G8 — every added selector is scoped to the residential verdict hero.
    #      EVERY added line that opens a rule is checked, not only the ones
    #      that happen to begin with the screen id — an unscoped selector is
    #      exactly the line that would not begin with it.
    for line in added.splitlines():
        s = line.strip()
        if not s.endswith("{") or s.startswith(("/*", "*", "@")):
            continue
        if not s.startswith(("#", ".")):
            continue  # a JS block, not a CSS selector
        if "#screen-match-results" not in s or "[data-pn-verdict]" not in s:
            raise SystemExit("REFUSED: a selector was added that is not scoped "
                             "to the residential verdict hero: %s" % s)

    # G9 — syntax, before anything is written.
    blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", out, re.S)
    for i, b in enumerate(blocks):
        if not b.strip(): continue
        tmp = os.path.join(ROOT, ".pn-gt-%d.mjs" % i)
        open(tmp, "w", encoding="utf-8").write(b)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            raise SystemExit("REFUSED: script %d does not parse, nothing "
                             "written:\n%s" % (i, r.stderr[:400]))

    if mode == "--check":
        print("CHECK ONLY. %s -> %s, %+d lines, 9 guards pass"
              % (base, sha16(out), out.count("\n") - src.count("\n")))
        return

    if not os.path.exists(BAK):
        open(BAK, "w", encoding="utf-8").write(src)
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied. %s -> %s" % (base, sha16(out)))


if __name__ == "__main__":
    main()
