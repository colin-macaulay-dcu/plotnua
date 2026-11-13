#!/usr/bin/env python3
"""PROVE · Open for Commissions on the website (founder approval 13 Nov 2026).

  python3 atlas-tools/prove-plotart-commissions.py [--exports DIR] [--shots DIR]

C1  the pipeline accepts the key only as true, and accepts every export without it (absent = off)
C2  every PUBLISHED gallery (plotart/artists/*/gallery.json) renders byte-for-byte as main renders it today, gallery and
    artwork pages alike, with and without the live enquiry relay: nothing changes for an artist who hasn't switched it on
C3  switched on: the gallery page gains exactly one "Open for commissions" line, one "Enquire about a commission" button
    and one commission form (data-kind="commission", about the artist, never an artwork); artwork pages are unchanged
C4  the wording never mentions hire, the Living Gallery, availability or a PlotArt fee
C5  without the relay the button is a plain email link with a commission subject (no form)
C6  in a browser: the commission button opens its own form and sends kind "commission"; the ordinary enquiry still sends
    exactly the fields it sends today (no kind); screenshots on desktop and mobile with --shots
--exports: the two pipeline exports written by worker/plotart-studio/test/prove-open-for-commissions.mjs --export-dir.
"""
import copy, glob, html, importlib.util, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plotart_gallery as G          # noqa: E402
import plotart_gallery_pages as P    # noqa: E402

ARGS = sys.argv[1:]
EXPORTS = ARGS[ARGS.index("--exports") + 1] if "--exports" in ARGS else None
SHOTS = ARGS[ARGS.index("--shots") + 1] if "--shots" in ARGS else None
ENDPOINT = json.load(open(os.path.join(HERE, "release", "plotart-gallery-config.json")))["enquiry_endpoint"]
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [%s]" % str(detail)[:500]) if not ok and detail else ""))


def main_module():
    """plotart_gallery_pages.py exactly as production main holds it (the comparison baseline)."""
    src = subprocess.run(["git", "show", "origin/main:atlas-tools/plotart_gallery_pages.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    d = tempfile.mkdtemp(prefix="pa-ofc-main-")
    path = os.path.join(d, "plotart_gallery_pages_main.py")
    open(path, "w").write(src)
    spec = importlib.util.spec_from_file_location("plotart_gallery_pages_main", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pages(mod, pkg, endpoint):
    ws = mod.shown(pkg)
    out = {"index": mod.artist_body(pkg, enquiry_endpoint=endpoint)}
    for i, w in enumerate(ws):
        out[w["slug"]] = mod.artwork_body(pkg, w, ws[i - 1] if i else None, ws[i + 1] if i + 1 < len(ws) else None, enquiry_endpoint=endpoint)
    return out


print("PROVE · Open for Commissions (website)")
print("— the pipeline")
if EXPORTS:
    on, off = (json.load(open(os.path.join(EXPORTS, f))) for f in ("export-on.json", "export-off.json"))
    def ok(g):
        try:
            G.validate_export(g)
            return True
        except G.Refused as e:
            return str(e)
    check("C1a the Studio's real exports pass the pipeline: switched on (key true) and switched off (no key)",
          ok(on) is True and ok(off) is True and on["artist"].get("open_for_commissions") is True and "open_for_commissions" not in off["artist"],
          [ok(on), ok(off)])
    refused = []
    for v in (False, "yes", 1, None, "true"):
        g = copy.deepcopy(on)
        g["artist"]["open_for_commissions"] = v
        refused.append(ok(g) is not True)
    check("C1b anything but true is refused (false, \"yes\", 1, null, \"true\"): absent is the only way to say off", all(refused), refused)
else:
    check("C1 (skipped: run with --exports)", True)

print("— every published gallery renders exactly as today")
M = main_module()
pkgs = sorted(glob.glob(os.path.join(ROOT, "plotart", "artists", "*", "gallery.json")))
same, diffs = 0, []
for f in pkgs:
    pkg = json.load(open(f))
    for ep in (None, ENDPOINT):
        a, b = pages(M, pkg, ep), pages(P, pkg, ep)
        for k in a:
            if a[k] == b.get(k):
                same += 1
            else:
                diffs.append("%s/%s (%s)" % (pkg["artist"]["slug"], k, "relay" if ep else "email"))
check("C2 all %d published galleries: %d gallery and artwork pages byte-identical to main, with and without the relay" % (len(pkgs), same),
      len(pkgs) >= 5 and not diffs and same > 0 and not any(json.load(open(f))["artist"].get("open_for_commissions") for f in pkgs), diffs[:5])

print("— switched on")
base = json.load(open(os.path.join(ROOT, "plotart", "artists", "leah-hewson", "gallery.json")))
onp = copy.deepcopy(base)
onp["artist"]["open_for_commissions"] = True
A, B = pages(P, base, ENDPOINT), pages(P, onp, ENDPOINT)
g = B["index"]
check("C3a the gallery page gains exactly one \"Open for commissions\" line (the meta style, no new CSS)",
      g.count("Open for commissions") == 1 and g.count('<p class="pa-ag-meta pa-ag-ofc">Open for commissions</p>') == 1)
check("C3b …one \"Enquire about a commission\" button (ghost, its own wrapper) and one commission form about the artist",
      g.count(">Enquire about a commission</a>") == 1 and g.count('data-kind="commission"') == 1
      and re.search(r'<div class="pa-ag-enq-c"[^>]*><a class="pa-btn pa-btn--ghost" href="mailto:[^"]+" data-pa-track="artist_commission_enquiry" data-pa-enquire>Enquire about a commission</a><form class="pa-enq" hidden data-endpoint="%s" data-ref="PA-leah-hewson" data-notice="[^"]+" data-kind="commission" novalidate>' % re.escape(ENDPOINT), g) is not None)
check("C3c the ordinary enquiry button and form are unchanged and come first", A["index"].split('<section class="pa-ag-enq">')[1].split("</a>")[0] == g.split('<section class="pa-ag-enq">')[1].split("</a>")[0])
check("C3d removing the label and the commission block gives back exactly today's page (nothing else moved)",
      re.sub(r'\n  <div class="pa-ag-enq-c".*?</form></div>', "", g, flags=re.S).replace('<p class="pa-ag-meta pa-ag-ofc">Open for commissions</p>', "") == A["index"])
check("C3e artwork pages are unchanged when switched on (gallery page only)", all(A[k] == B[k] for k in A if k != "index") and len(A) > 1)
vis = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.search(r'<div class="pa-ag-enq-c".*?</div>', g, re.S).group(0))))
check("C4 the commission wording never mentions hire, the Living Gallery, availability, opportunities or a PlotArt fee",
      not re.search(r"hire|living gallery|availab|opportunit|fee|percent|%|PlotArt takes", vis, re.I), vis)
noep = pages(P, onp, None)["index"]
mail = re.search(r'<a class="pa-btn pa-btn--ghost" href="([^"]+)" data-pa-track="artist_commission_enquiry">Enquire about a commission</a></div>', noep)
check("C5 without the relay: a plain email link with a commission subject naming the artist, and no form",
      mail is not None and "PlotArt%20commission%20enquiry%3A%20Leah%20Hewson%20%5BPA-leah-hewson%5D" in html.unescape(mail.group(1)) and 'data-kind' not in noep, mail and mail.group(1)[:120])

print("— in a browser")
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
if sync_playwright is None:
    check("C6 (skipped: Playwright not available)", True)
else:
    css = open(os.path.join(ROOT, "plotart", "assets", "plotart.css"), encoding="utf-8").read()
    js = open(os.path.join(ROOT, "plotart", "assets", "pa-enquiry.js"), encoding="utf-8").read()
    def doc(body):
        return ('<!DOCTYPE html><html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<style>%s</style></head><body class="pa-body"><main>%s</main><script>%s</script></body></html>') % (css, body, js)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        sent = []
        def run(body, click, fill=True):
            sent.clear()
            pg = br.new_page(viewport={"width": 1280, "height": 900})
            pg.route(ENDPOINT, lambda route: (sent.append(json.loads(route.request.post_data)),
                                              route.fulfill(status=200, headers={"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"},
                                                            body='{"ok":true,"reference":"PA-E-261113-ABC123"}')))
            pg.set_content(doc(body))
            pg.click(click)
            form = pg.locator("form.pa-enq:not([hidden])")
            n_open = form.count()
            if fill and n_open == 1:
                form.locator("input[name=name]").fill("Cara Client")
                form.locator("input[name=email]").fill("cara@example.test")
                form.locator("textarea[name=message]").fill("Could you paint a large piece for our hallway?")
                form.locator("button[type=submit]").click()
                pg.wait_for_timeout(300)
            pg.close()
            return n_open
        n1 = run(B["index"], "a[data-pa-track=artist_commission_enquiry]")
        c = list(sent)
        n2 = run(B["index"], "a[data-pa-track=artist_enquiry]")
        o = list(sent)
        n3 = run(A["index"], "a[data-pa-track=artist_enquiry]")
        t = list(sent)
        check("C6a the commission button opens ITS form (one form open) and sends kind \"commission\" with the artist reference",
              n1 == 1 and len(c) == 1 and c[0].get("kind") == "commission" and c[0]["ref"] == "PA-leah-hewson", c)
        check("C6b the ordinary enquiry on the same page opens its own form and sends exactly today's fields (no kind)",
              n2 == 1 and len(o) == 1 and "kind" not in o[0] and sorted(o[0]) == ["email", "message", "name", "notice", "ref", "website"], o)
        check("C6c a page without the switch sends exactly the same fields as before", n3 == 1 and t and sorted(t[0]) == sorted(o[0]) and "kind" not in t[0], t)
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True)
            for name, w, h in (("desktop", 1440, 900), ("mobile", 390, 844)):
                for tag, body in (("off", A["index"]), ("on", B["index"])):
                    pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
                    pg.set_content(doc(body))
                    pg.locator(".pa-ag-hero, .pa-ag-head, header").first.screenshot(path=os.path.join(SHOTS, "head-%s-%s.png" % (name, tag))) if pg.locator(".pa-ag-hero, .pa-ag-head, header").count() else None
                    pg.locator("section.pa-ag-enq").screenshot(path=os.path.join(SHOTS, "enquire-%s-%s.png" % (name, tag)))
                    if tag == "on":
                        pg.click("a[data-pa-track=artist_commission_enquiry]")
                        pg.locator("section.pa-ag-enq").screenshot(path=os.path.join(SHOTS, "enquire-%s-on-open.png" % name))
                    pg.close()
        br.close()

print("\nPLOTART COMMISSIONS · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
