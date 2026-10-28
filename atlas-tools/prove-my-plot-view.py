#!/usr/bin/env python3
"""GUARD · My Plot and the Eircode journey are separate experiences (founder decision 28 Oct 2026).

    python3 atlas-tools/prove-my-plot-view.py            the guard (read-only)
    python3 atlas-tools/prove-my-plot-view.py --prove    plus planted-fault capability

your-plot.html holds two experiences: the Eircode / property journey (the plain URL and
its journey parameters) and My Plot, the homeowner's saved collection (?myplot=1, "the
My Plot view"). Prints "MY PLOT VIEW · OK" only when:

  M1  the view is decided before first paint: a script in <head>, exempt from Cookiebot's
      automatic blocking (data-cookieconsent="ignore"), marks ?myplot=1, titles the page
      "My Plot | PlotNua" and hides the Eircode screen while My Plot opens
  M2  My Plot ALWAYS opens in the view, whether or not anything is saved (no condition
      on restored items)
  M3  history: the view's first entry is My Plot, so Back never lands on the Eircode screen
  M4  Close, when My Plot is where the visit started, leaves to a PlotNua page that is not
      your-plot.html, or the Discovery Library; the journey's "Back to results" control
      is hidden in the view
  M5  the empty dashboard: exactly "Your ideas, all in one place.", the approved sentence,
      and "Explore Discoveries" linking to discoveries.html
  M6  the Eircode journey is unchanged: its title and heading stay "Your Plot", the
      Eircode form and its button are present, and the journey keeps its own empty message
  M7  the in-page count is saved products + added links (the header's count)
  M8  every link labelled "My Plot" anywhere on the site opens your-plot.html?myplot=1;
      footer "Your Plot" links still open the Eircode journey (plain your-plot.html)
"""
import glob, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMPTY_TITLE = "Your ideas, all in one place."
EMPTY_TEXT = ("You haven\\u2019t saved anything yet. Explore the Discovery Library and save the "
              "possibilities, products and ideas that interest you.")


def check(root):
    bad = []
    need = lambda ok, m: ok or bad.append(m)
    t = open(os.path.join(root, "your-plot.html"), encoding="utf-8").read()
    head = t[:t.index("</head>")]
    # M1
    m = re.search(r'<script data-cookieconsent="ignore">\(function\(\)\{try\{if\(new URLSearchParams\(location\.search\)\.get\(\'myplot\'\)===\'1\'\)\{'
                  r"var h=document\.documentElement;h\.classList\.add\('pn-myplot-view'\);document\.title='My Plot \| PlotNua';", head)
    need(m is not None, "M1 the My Plot view script is missing from <head> or not exempt from consent blocking")
    need("html.pn-myplot-view:not(.pn-myplot-open) #screen-entry{opacity:0 !important;pointer-events:none !important}" in head,
         "M1 the Eircode screen is not hidden while My Plot opens")
    need(head.index("pn-myplot-view") < head.index("<title>") if "pn-myplot-view" in head and "<title>" in head else False,
         "M1 the view script must come before the stylesheet and title")
    # M2
    need("      if (MYPLOT_VIEW) {\n        openMyPlot();" in t, "M2 My Plot does not always open in the view")
    need("restored > 0 && new URLSearchParams(location.search).get('myplot')" not in t, "M2 opening still depends on restored items")
    need("const MYPLOT_VIEW = document.documentElement.classList.contains('pn-myplot-view');" in t, "M2 the view flag is missing")
    # M3
    need("} else if (MYPLOT_VIEW) {\n    history.replaceState({ pnScreen: 'myplot' }, '');" in t, "M3 the view's first history entry is not My Plot")
    # M4
    need("if (MYPLOT_VIEW && !myPlotHasReturn) { leaveMyPlotView(); return; }" in t, "M4 Close is not guarded in the view")
    lv = re.search(r"function leaveMyPlotView\(\)\{.*?\n  \}", t, re.S)
    need(lv is not None and "location.assign(back || 'discoveries.html')" in lv.group(0) and "your-plot\\.html$" in lv.group(0)
         and "showScreen" not in lv.group(0), "M4 Close must leave to a PlotNua page that is not your-plot.html, or the Discovery Library")
    need("html.pn-myplot-view:not(.pn-myplot-journey) #pnReturn{display:none !important}" in head, "M4 the journey's return control shows in the view")
    # M5
    need(EMPTY_TITLE in t and EMPTY_TEXT in t and "<a class=\"btn-primary small\" href=\"discoveries.html\">Explore Discoveries</a>" in t,
         "M5 the empty dashboard is not the approved wording and link")
    need("viewEmpty = MYPLOT_VIEW && !ids.length && !addedItems.length" in t, "M5 the empty dashboard must show only in the view, when nothing is saved")
    # M6
    need("<title>Your Plot | PlotNua</title>" in head and '<h1 class="pn-page-title">Your Plot</h1>' in t, "M6 the Eircode journey's title or heading changed")
    need('<form id="entryForm" novalidate>' in t and 'id="eircodeInput"' in t and '>Find My Plot →</button>' in t, "M6 the Eircode form changed")
    need("Nothing saved yet. Save an option from your recommendations" in t, "M6 the journey's own empty message is gone")
    # M7
    need("const count = savedProductIds.size + addedCount;" in t, "M7 the in-page count is not saved + added")
    # M8
    wrong, footers = [], 0
    for f in glob.glob(os.path.join(root, "*.html")):
        s = open(f, encoding="utf-8", errors="ignore").read()
        for m2 in re.finditer(r'<a\b([^>]*)href="(/?your-plot\.html[^"]*)"([^>]*)>(.*?)</a>', s, re.S):
            label = re.sub(r"<[^>]+>", " ", m2.group(4))
            label = re.sub(r"\s+", " ", label).strip()
            aria = re.search(r'aria-label="([^"]*)"', m2.group(1) + m2.group(3))
            name = label or (aria.group(1) if aria else "")
            if re.search(r"\bMy Plot\b", name) and not m2.group(2).lstrip("/").startswith("your-plot.html?myplot=1"):
                wrong.append("%s %s (%s)" % (os.path.basename(f), m2.group(2), name))
            if name == "Your Plot":
                footers += 1
                if m2.group(2).lstrip("/") != "your-plot.html":
                    wrong.append("%s footer Your Plot -> %s" % (os.path.basename(f), m2.group(2)))
    need(not wrong, "M8 links labelled My Plot that do not open My Plot: %s" % wrong[:5])
    need(footers > 0, "M8 no footer 'Your Plot' link to the Eircode journey was found")
    return bad, footers


def main():
    bad, footers = check(ROOT)
    if bad:
        print("MY PLOT VIEW · FAILED (%d)" % len(bad))
        for b in bad:
            print("  " + b)
        return 1
    if "--prove" in sys.argv:
        Y = "your-plot.html"
        F = [
            ("view script loses its consent exemption", Y, '<script data-cookieconsent="ignore">(function(){try{if(new URLSearchParams(location.search).get(\'myplot\')', '<script>(function(){try{if(new URLSearchParams(location.search).get(\'myplot\')'),
            ("Eircode screen no longer hidden while opening", Y, "#screen-entry{opacity:0 !important;", "#screen-entry{opacity:1 !important;"),
            ("empty My Plot sends people to the journey again", Y, "      if (MYPLOT_VIEW) {\n        openMyPlot();", "      if (restored > 0 && MYPLOT_VIEW) {\n        openMyPlot();"),
            ("Back lands on the Eircode screen", Y, "history.replaceState({ pnScreen: 'myplot' }, '');", "history.replaceState({ pnScreen: 'landing' }, '');"),
            ("Close falls back to Results", Y, "if (MYPLOT_VIEW && !myPlotHasReturn) { leaveMyPlotView(); return; }", ""),
            ("Close leads into the journey", Y, "location.assign(back || 'discoveries.html')", "location.assign(back || 'your-plot.html')"),
            ("Back to results shown in the view", Y, "#pnReturn{display:none !important}", "#pnReturn{display:block}"),
            ("empty wording changed", Y, "Your ideas, all in one place.", "Your ideas, in one place."),
            ("CTA points elsewhere", Y, 'href="discoveries.html">Explore Discoveries</a>', 'href="your-plot.html">Explore Discoveries</a>'),
            ("journey renamed", Y, "<title>Your Plot | PlotNua</title>", "<title>My Plot | PlotNua</title>"),
            ("in-page count drops added links", Y, "const count = savedProductIds.size + addedCount;", "const count = savedProductIds.size;"),
            ("journey exit My Plot link restarts the journey", "disc014-driveway-income.html", 'class="pnx-go" href="your-plot.html?myplot=1">My Plot<', 'class="pnx-go" href="your-plot.html">My Plot<'),
            ("header My Plot link restarts the journey", "about.html", 'href="your-plot.html?myplot=1" data-myplot', 'href="your-plot.html" data-myplot'),
        ]
        missed = 0
        with tempfile.TemporaryDirectory() as d:
            for f in glob.glob(os.path.join(ROOT, "*.html")):
                shutil.copy2(f, d)
            for name, rel, a, b in F:
                p = os.path.join(d, rel)
                orig = open(p, encoding="utf-8").read()
                if orig.count(a) < 1:
                    print("SETUP  %s: anchor not found" % name); missed += 1; continue
                open(p, "w", encoding="utf-8").write(orig.replace(a, b, 1))
                got, _ = check(d)
                ok = bool(got)
                missed += not ok
                print("%s  %-48s %s" % ("caught" if ok else "MISSED", name, got[0][:70] if got else ""))
                open(p, "w", encoding="utf-8").write(orig)
        if missed:
            print("MY PLOT VIEW · CAPABILITY FAILED — %d of %d not caught" % (missed, len(F)))
            return 1
        print("MY PLOT VIEW · CAPABILITY OK — %d planted faults, 0 not caught" % len(F))
    print("MY PLOT VIEW · OK — M1-M8 · My Plot always opens its own view; the Eircode journey is unchanged; "
          "every My Plot link opens the view; %d footer Your Plot links still open the journey" % footers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
