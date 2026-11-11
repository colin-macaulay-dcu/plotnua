#!/usr/bin/env python3
"""PROVE · Art for Hire release preparation (Stage 3B-6, development 10 Nov 2026). Local only: temporary copies of the
repository. Nothing is committed to the repository, pushed or published.

    python3 atlas-tools/prove-plotart-hire-release.py

  D  the committed state, and disabled until authorised: the enquiry form switch stays off and the page switch matches
     what is published; the launch guard passes on the real site. On the last tree where Art for Hire was off (HEAD
     itself until the founder switched the page on, 11 Nov 2026; found from the switches' git history) the guard
     passes with Art for Hire off and refuses a planted hire page or tab; the page builder and the navigation tool
     refuse to write without the switch, and a preview can never be written into the repository.
  C  the release candidate: switches on, tab added, page built (empty state), manifest re-pinned: the guard passes (L1-L17)
     and refuses a visible card, an enquiry form without its switch, a contact address, an indexable page, a page
     missing the tab or a changed pinned file.
  P  the gallery pipeline writes the tab exactly as the navigation tool does once the switch is on, and not before.
  B  the publishing boundary: a gallery release can never touch the hire page; the --hire boundary accepts only the
     catalogue region, and --removals-only accepts withdrawals and refuses additions."""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok or not detail else "  [%s]" % str(detail)[-500:]))


def py(*a, cwd=None):
    r = subprocess.run([sys.executable] + list(a), capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout + r.stderr


def guard(root, switches=None, manifest=None):
    rel = os.path.join(root, "atlas-tools", "release")
    return py(os.path.join(root, "atlas-tools", "prove-plotart-launch.py"), root, "--switches", switches or os.path.join(rel, "plotart-launch-switches.json"),
              "--manifest", manifest or os.path.join(rel, "plotart-launch-manifest.json"))


def export(dest, rev="HEAD"):
    os.makedirs(dest)
    tar = subprocess.run(["git", "-C", REPO, "archive", rev], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", dest], input=tar, check=True)
    return dest


T = tempfile.mkdtemp(prefix="pa-hire-rel-")
try:
    print("PROVE · Art for Hire release preparation\n— D · disabled until authorised")
    SWP = "atlas-tools/release/plotart-launch-switches.json"
    sw = json.load(open(os.path.join(REPO, SWP), encoding="utf-8"))
    ON = sw.get("art_for_hire_page") is True
    published = os.path.exists(os.path.join(REPO, "plotart/art-for-hire/index.html"))
    tabbed = "nav_art_for_hire" in open(os.path.join(REPO, "plotart/index.html"), encoding="utf-8").read()
    check("D1 the enquiry form switch is OFF, and the page switch matches what is published (%s)" % ("on: page and tab present" if ON else "off: no page, no tab"),
          sw.get("art_for_hire_enquiry_form") is False and isinstance(sw.get("art_for_hire_page"), bool) and published == ON and tabbed == ON)
    c, o = guard(REPO)
    check("D2 the launch guard passes on the real site with the committed switches (Art for Hire %s, L1-L17)" % ("ON" if ON else "off"),
          c == 0 and ("Art for Hire ON" if ON else "Art for Hire off") in o, o)
    # the last tree where Art for Hire was off: HEAD itself, or the newest commit of the switches file with the page off
    off_rev = "HEAD"
    if ON:
        revs = subprocess.run(["git", "-C", REPO, "rev-list", "HEAD", "--", SWP], capture_output=True, text=True, check=True).stdout.split()
        off_rev = next((r for r in revs if json.loads(subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (r, SWP)], capture_output=True, text=True,
                        check=True).stdout).get("art_for_hire_page") is not True), None)
    off = export(os.path.join(T, "off"), off_rev) if off_rev else None
    c, o = guard(off) if off else (1, "no commit with Art for Hire off was found")
    check("D2b on the last tree with Art for Hire off (%s) the launch guard passes with Art for Hire off" % (off_rev[:7] if off_rev else "none"),
          c == 0 and "Art for Hire off" in o, o)
    os.makedirs(os.path.join(off, "plotart/art-for-hire"))
    open(os.path.join(off, "plotart/art-for-hire/index.html"), "w").write("<p>planted</p>")
    c, o = guard(off)
    check("D3 a hire page planted while the switch is off is refused (L1)", c == 1 and "L1" in o and "art-for-hire/index.html" in o, o)
    shutil.rmtree(os.path.join(off, "plotart/art-for-hire"))
    lg = os.path.join(off, "plotart/living-gallery.html")
    raw = open(lg, encoding="utf-8").read()
    open(lg, "w", encoding="utf-8").write(raw.replace('Living Gallery</a><a class="pa-pill pa-pill--out"', 'Living Gallery</a><a class="pa-pill" href="art-for-hire/" data-pa-track="nav_art_for_hire">Art for Hire</a><a class="pa-pill pa-pill--out"', 1))
    c, o = guard(off)
    check("D4 the tab planted on one page while the switch is off is refused (L11, L17)", c == 1 and "L17 living-gallery.html" in o, o)
    open(lg, "w", encoding="utf-8").write(raw)
    c1, o1 = py(os.path.join(REPO, "atlas-tools/plotart-hire-page.py"), off, "--catalogue", os.path.join(REPO, "atlas-tools/release/plotart-launch-switches.json"))
    c2, o2 = py(os.path.join(REPO, "atlas-tools/plotart-hire-nav.py"), off)
    c3, o3 = py(os.path.join(REPO, "atlas-tools/plotart-hire-page.py"), REPO, "--catalogue", "x.json", "--preview")
    c4, o4 = py(os.path.join(REPO, "atlas-tools/plotart-hire-nav.py"), REPO, "--preview")
    check("D5 without the switch the page builder and the navigation tool write nothing; a preview is never written into the repository",
          c1 == 1 and "not switched on" in o1 and c2 == 2 and "not switched on" in o2 and c3 == 1 and "never writes into the repository" in o3 and c4 == 2
          and not os.path.exists(os.path.join(off, "plotart/art-for-hire")) and "nav_art_for_hire" not in open(os.path.join(off, "plotart/index.html"), encoding="utf-8").read(),
          "\n".join([o1, o2, o3, o4]))

    print("— C · the release candidate (switches on, built outside the repository)")
    rc = os.path.join(T, "rc")
    c, o = py(os.path.join(REPO, "atlas-tools/release/plotart-hire-release-candidate.py"), rc)
    check("C1 the candidate builds and the guard passes with Art for Hire ON (tab on every page, page, assets, re-pinned manifest)",
          c == 0 and "RELEASE CANDIDATE · OK" in o and "Art for Hire ON" in o, o)
    pages = [p for p in glob.glob(os.path.join(rc, "plotart/**/*.html"), recursive=True) if 'class="pa-pills' in open(p, encoding="utf-8").read()]
    check("C2 every PlotArt page with the gallery navigation carries the tab (%d pages)" % len(pages),
          pages and all('data-pa-track="nav_art_for_hire"' in open(p, encoding="utf-8").read() for p in pages))
    hp = os.path.join(rc, "plotart/art-for-hire/index.html")
    page = open(hp, encoding="utf-8").read()
    check("C3 the built page is the empty state today (no listed works), noindex, enquiry form OFF, approved relay",
          'class="pa-hire-card"' not in page and "No works are available for hire just now." in page and 'content="noindex, follow"' in page
          and 'data-enquiries="off"' in page and 'data-api="https://plotart-enquiry.colin-a41.workers.dev"' in page)
    man = os.path.join(rc, "atlas-tools/release/plotart-launch-manifest.json")

    def mutate(desc, fn, want):
        bak = page
        open(hp, "w", encoding="utf-8").write(fn(page))
        c, o = guard(rc)
        open(hp, "w", encoding="utf-8").write(bak)
        return c == 1 and want in o, o

    card = ('<ul class="pa-hire-grid"><li class="pa-hire-card" data-hire-work="wzz1" data-hire-ref="PA-leah-hewson-wzz1" data-hire-title="x" data-hire-artist="x">'
            '<figure class="pa-hire-art"><img src="../artists/leah-hewson/img/missing-600.webp" alt="x"></figure></li></ul>')
    tests = [
        ("C4 a card that is not hidden, or is not an available published work", lambda s: s.replace("<!-- pa-hire-catalogue:begin -->", "<!-- pa-hire-catalogue:begin -->" + card), "L17 every card must ship hidden"),
        ("C5 an enquiry form without its switch", lambda s: s.replace('data-enquiries="off"', 'data-enquiries="on"'), "L17 the enquiry form state"),
        ("C6 a contact address on the page", lambda s: s.replace("Price on request.", "Price on request. artist@example.com"), "L17 the Art for Hire page exposes an address"),
        ("C7 the page made indexable", lambda s: s.replace('content="noindex, follow"', 'content="index, follow"'), "noindex"),
        ("C8 a change outside the catalogue region (pinned)", lambda s: s.replace("Simple, direct,", "Simple, quick,"), "L3 art-for-hire/index.html differs from the verified build"),
        ("C9 another relay address", lambda s: s.replace("plotart-enquiry.colin-a41", "evil.example"), "L17 the Art for Hire page must use the approved enquiry relay"),
    ]
    for name, fn, want in tests:
        ok, o = mutate(name, fn, want)
        check(name + " → refused", ok, o)
    au = os.path.join(rc, "plotart/about.html")
    a0 = open(au, encoding="utf-8").read()
    open(au, "w", encoding="utf-8").write(a0.replace('<a class="pa-pill" href="art-for-hire/" data-pa-track="nav_art_for_hire">Art for Hire</a>', "", 1))
    c, o = guard(rc)
    open(au, "w", encoding="utf-8").write(a0)
    check("C10 a page missing the tab while the switch is on → refused", c == 1 and ("L11 about.html" in o or "L17 about.html" in o), o)
    swoff = os.path.join(T, "switches-off.json")
    json.dump(dict(sw, art_for_hire_page=False, art_for_hire_enquiry_form=False), open(swoff, "w"))
    c, o = guard(rc, switches=swoff)
    check("C11 the candidate site with the switch OFF → refused (the page and tab must not exist)", c == 1 and "L17" in o, o)

    print("— P · the gallery pipeline and the tab")
    import plotart_shell as S
    import plotart_gallery_pages as P
    ep = json.load(open(os.path.join(REPO, "atlas-tools/release/plotart-gallery-config.json")))["enquiry_endpoint"]

    def regen(root, flag):
        S.HIRE_NAV = flag
        same, total = 0, 0
        base = set()
        for gp in sorted(glob.glob(os.path.join(root, "plotart/artists/*/gallery.json"))):
            for path, doc in P.gallery_pages(json.load(open(gp)), S.artist_page, enquiry_endpoint=ep):
                total += 1
                if open(os.path.join(root, "plotart", path), encoding="utf-8").read() == doc:
                    same += 1
                    base.add(path)
        return same, total, base
    s0, t0, b0 = regen(REPO, ON)          # the real site as committed (tab on every page once the switch is on)
    s1, t1, b1 = regen(rc, True)
    S.HIRE_NAV = False
    check("P1 with the switch on, the pipeline writes artist pages identical to the tool-patched candidate (%d of %d; the rest differ identically with the switch off, from older SEO metadata)" % (s1, t1),
          s1 == s0 and b1 == b0 and s1 > 0, (s0, t0, s1, t1))
    src = open(os.path.join(REPO, "atlas-tools/plotart-gallery-publish.py"), encoding="utf-8").read()
    check("P2 the pipeline takes the tab from the launch switch, and nothing in it writes plotart/art-for-hire/",
          'S.HIRE_NAV = json.load(open(os.path.join(HERE, "release", "plotart-launch-switches.json"), encoding="utf-8")).get("art_for_hire_page") is True' in src
          and "art-for-hire" not in src.replace("Art for Hire", ""))

    print("— B · the publishing boundary")
    g = os.path.join(T, "git")
    shutil.copytree(rc, g)
    sh = lambda *a: subprocess.run(a, cwd=g, capture_output=True, text=True, check=True).stdout.strip()
    sh("git", "init", "-q"); sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"); sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
    base = sh("git", "rev-parse", "HEAD")
    BOUND = os.path.join(REPO, "atlas-tools/release/plotart-content-boundary.py")

    def commit(edit):
        sh("git", "checkout", "-q", base)
        edit()
        sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "x")
        return sh("git", "rev-parse", "HEAD")
    gp = os.path.join(g, "plotart/art-for-hire/index.html")
    p0 = open(gp, encoding="utf-8").read()
    CARD = lambda w: '<li class="pa-hire-card" data-hire-work="%s" data-hire-ref="PA-a-%s" hidden>x</li>' % (w, w)
    reg = lambda cards: re.sub(r"<!-- pa-hire-catalogue:begin -->.*?<!-- pa-hire-catalogue:end -->",
                               "<!-- pa-hire-catalogue:begin -->" + "".join(CARD(w) for w in cards) + "<!-- pa-hire-catalogue:end -->", p0, flags=re.S)
    two = commit(lambda: open(gp, "w", encoding="utf-8").write(reg(["wa1", "wa2"])))
    # a base with two works, then: one withdrawn / one added / text outside the region / another file
    sh("git", "checkout", "-q", two)
    base = two
    one = commit(lambda: open(gp, "w", encoding="utf-8").write(reg(["wa1"])))
    three = commit(lambda: open(gp, "w", encoding="utf-8").write(reg(["wa1", "wa2", "wa3"])))
    outside = commit(lambda: open(gp, "w", encoding="utf-8").write(reg(["wa1", "wa2"]).replace("Simple, direct,", "Simple, quick,")))
    other = commit(lambda: open(os.path.join(g, "plotart/assets/plotart.css"), "a").write("/* x */\n"))
    bd = lambda rel, *f: py(BOUND, base, rel, *f, cwd=g)
    r = [bd(one, "--hire", "--removals-only"), bd(three, "--hire", "--removals-only"), bd(three, "--hire"), bd(outside, "--hire"), bd(other, "--hire"), bd(one)]
    check("B1 --hire --removals-only: a withdrawal publishes (catalogue region only)", r[0][0] == 0 and "HIRE BOUNDARY · OK" in r[0][1], r[0][1])
    check("B2 --removals-only refuses an addition (additions need the founder); plain --hire accepts it for a founder-approved run", r[1][0] == 1 and "only withdrawals" in r[1][1] and r[2][0] == 0, r[1][1] + r[2][1])
    check("B3 --hire refuses any change outside the catalogue region, and any other file", r[3][0] == 1 and "outside the catalogue region" in r[3][1] and r[4][0] == 1 and "outside the Art for Hire boundary" in r[4][1], r[3][1] + r[4][1])
    check("B4 a gallery (content-only) release that touches the hire page is refused by name", r[5][0] == 1 and "never published by a gallery release" in r[5][1], r[5][1])
    cat = os.path.join(T, "cat.json"); json.dump({"items": []}, open(cat, "w"))
    sh("git", "checkout", "-q", two)
    c, o = py(os.path.join(g, "atlas-tools/plotart-hire-page.py"), g, "--catalogue", cat, "--update")
    sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "update")
    upd = sh("git", "rev-parse", "HEAD")
    c2, o2 = py(BOUND, two, upd, "--hire", "--removals-only", cwd=g)
    check("B5 the builder's --update rewrites only the catalogue region: the result passes --hire --removals-only (all works withdrawn → empty state)",
          c == 0 and "catalogue region updated" in o and c2 == 0 and "No works are available" in open(gp, encoding="utf-8").read(), o + o2)
finally:
    shutil.rmtree(T, ignore_errors=True)
n = sum(results)
print("\nART FOR HIRE RELEASE · %d checks, %d passed, %d failed" % (len(results), n, len(results) - n))
sys.exit(0 if n == len(results) else 1)
