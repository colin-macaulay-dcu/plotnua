#!/usr/bin/env python3
"""PROVE · Virtual Gallery collection, Direction C2 "The Curated Collection" (founder approval 5 Nov 2026). Read-only:
works on temporary copies and never touches the repository, the live site or any artist record.

    python3 atlas-tools/prove-plotart-vg-collection.py

V1-V8   the builder: the four position states from the founder's Gallery order, equal treatment, no unpublished name
P1-P3   the content pipeline accepts the order's optional "assigned" flag (true/false, never who) and nothing else
G1-G12  the PlotArt launch guard refuses every planted fault in a copy of the real Virtual Gallery page
"""
import copy, json, os, re, shutil, subprocess, sys, tempfile, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plotart_gallery_pages as P  # noqa: E402

results = []
def check(label, ok, detail=""):
    results.append(bool(ok)); print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok or not detail else "  [%s]" % str(detail)[:300]))

real = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(ROOT, "plotart", "artists", "*", "gallery.json")))]
check("V0 the real published galleries load (%d)" % len(real), len(real) >= 1)
base = real[0]

def synth(slug, name):
    """A synthetic published gallery shaped like a real one (test only; never written anywhere)."""
    p = copy.deepcopy(base); p["artist"] = dict(p["artist"], slug=slug, display_name=name, practice="Test practice")
    return p

pk = [synth("ann-test", "Ann Test"), synth("bea-test", "Bea Test"), synth("cal-test", "Cal Test")]
lay = {"positions": [{"position": 1, "slug": "bea-test", "reserved": False}, {"position": 2, "slug": None, "reserved": True},
                     {"position": 3, "slug": "secret-unpublished", "reserved": False}, {"position": 4, "slug": None, "reserved": False, "assigned": True},
                     {"position": 6, "slug": "ann-test", "reserved": False}, {"position": 7, "slug": "hidden-two", "reserved": True}],
       "extra": ["cal-test"]}
pos, extra = P.vg_positions(pk, layout=lay)
st = [s for _, s, _ in pos]
check("V1 position 01 is the published artist placed there; 02 reserved; 06 published", st[0] == "pub" and pos[0][2]["artist"]["slug"] == "bea-test" and st[1] == "res" and st[5] == "pub", st[:7])
check("V2 a placed artist whose gallery is not published is 'in preparation' (03), as is the bare 'assigned' flag (04)", st[2] == "prep" and st[3] == "prep", st[:5])
check("V3 reserved wins over a placed artist (07); every other position is available", st[6] == "res" and all(s == "av" for s in st[7:]) and st[4] == "av", st)
check("V4 a published gallery without a position follows the 25, without a number", [p["artist"]["slug"] for p in extra] == ["cal-test"])
h = P.vg_collection(pk, layout=lay)
check("V5 no unpublished gallery address or name ever reaches the page", "secret-unpublished" not in h and "hidden-two" not in h)
labels = re.findall(r'<div class="pa-vgc-label">.*?</div></div>', h, re.S)
shape = {re.sub(r"\d\d|[a-z]+-test|[A-Z][a-z]+ Test", "#", l) for l in labels[:2]}
check("V6 equal treatment: numbered open galleries share one identical label structure; the unplaced one only lacks the numeral",
      len(labels) == 3 and len(shape) == 1 and '<span class="pa-vgc-n" aria-hidden="true"></span>' in labels[2], labels)
check("V7 the count, the occupancy line and the summary agree", '<p class="pa-vgc-count">3 of 25 galleries open</p>' in h and
      "<b>2</b> published" in h and "<b>2</b> reserved" in h and "<b>2</b> in preparation" in h and "<b>19</b> available" in h and h.count('<li class="is-') == 25)
h0, h25 = P.vg_collection([], layout=None), P.vg_collection([synth("t%02d-test" % i, "T%02d Test" % i) for i in range(1, 26)], layout=None)
check("V8 0 and 25 open galleries: no wall and 25 available; 25 numbered works and 25 named positions",
      "pa-vgc-hang" not in h0 and h0.count('class="pa-vgc-pos is-av"') == 25 and h25.count('<li class="pa-vgc-work">') == 25 and h25.count('class="pa-vgc-pos is-pub"') == 25 and 'n-3"' in h25)

# P · the pipeline's view of the order (layout()): accepts "assigned" true/false only, refuses any other field
src = open(os.path.join(HERE, "plotart-gallery-publish.py"), encoding="utf-8").read()
fn = src[src.index("def layout():"):src.index("def regrid(")]
def run_layout(feed):
    ns = {"urllib": __import__("urllib.error"), "call": lambda *a, **k: feed}
    import urllib.error; ns["urllib"] = urllib
    exec(fn, ns)
    try:
        return ns["layout"](), None
    except RuntimeError as e:
        return None, str(e)
ok, err = run_layout({"positions": [{"position": 4, "slug": None, "reserved": False, "assigned": True}], "extra": []})
check("P1 the order may carry assigned: true (no name)", ok is not None and err is None, err)
ok, err = run_layout({"positions": [{"position": 4, "slug": None, "reserved": False, "assigned": "Nick"}], "extra": []})
check("P2 an 'assigned' value other than true/false is refused", ok is None and "true or false" in (err or ""), err)
ok, err = run_layout({"positions": [{"position": 4, "slug": None, "reserved": False, "name": "Someone"}], "extra": []})
check("P3 any other field (e.g. a name) is still refused", ok is None and "must not" in (err or ""), err)

# G · the launch guard against planted faults in a copy of the real page
def guard(site):
    r = subprocess.run([sys.executable, os.path.join(site, "atlas-tools", "prove-plotart-launch.py"), site, "--switches",
                        os.path.join(site, "atlas-tools/release/plotart-launch-switches.json"), "--manifest",
                        os.path.join(site, "atlas-tools/release/plotart-launch-manifest.json")], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr
tmp = tempfile.mkdtemp(prefix="pa-vgc-")
site = os.path.join(tmp, "site")
shutil.copytree(ROOT, site, symlinks=True, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))
vgp = os.path.join(site, "plotart", "gallery", "index.html")
orig = open(vgp, encoding="utf-8").read()
rc, out = guard(site)
check("G0 the unchanged copy passes the launch guard", rc == 0 and "PLOTART LAUNCH · OK" in out, out[-400:])
slug = base["artist"]["slug"]
FAULTS = [
    ("G1 a reserved position names someone", lambda s: s.replace("</span>Reserved</span>", "</span>Reserved for Jane</span>", 1), "L11"),
    ("G2 an available position links somewhere", lambda s: re.sub(r'(<li class="pa-vgc-pos is-av">)(<b>.*?Available</span>)(</li>)', r'\1<a href="../artists/x/">\2</a>\3', s, count=1), "L11"),
    ("G3 an unpublished artist's name in an 'in preparation' position", lambda s: re.sub(r'<li class="pa-vgc-pos is-av"><b><span class="pa-vgc-sr">Position </span>(\d\d)</b><span class="pa-vgc-st"><span class="pa-vgc-sr">: </span>Available</span>',
        r'<li class="pa-vgc-pos is-prep"><b><span class="pa-vgc-sr">Position </span>\1</b><span class="pa-vgc-st"><span class="pa-vgc-sr">: </span>Nick Example</span>', s, count=1), "L11"),
    ("G4 positions out of order", lambda s: s.replace("Position </span>05</b>", "Position </span>06</b>", 1), "L11"),
    ("G5 a 26th position", lambda s: s.replace("\n    </ol>\n  </div>", '\n      <li class="pa-vgc-pos is-av"><b><span class="pa-vgc-sr">Position </span>26</b><span class="pa-vgc-st"><span class="pa-vgc-sr">: </span>Available</span></li>\n    </ol>\n  </div>', 1), "L11"),
    ("G6 the wall's numeral disagrees with the index", lambda s: re.sub(r'(<span class="pa-vgc-n" aria-hidden="true">)01(</span>.*?Position )01(: )', r'\g<1>09\g<2>09\3', s, count=1, flags=re.S), "L11"),
    ("G7 an open gallery shows another artist's image in its srcset", lambda s: s.replace("../artists/%s/img/" % slug, "../artists/someone-else/img/", 2), "L11"),
    ("G8 the open-gallery count is wrong", lambda s: re.sub(r'<p class="pa-vgc-count">\d+ of 25', '<p class="pa-vgc-count">9 of 25', s), "L11"),
    ("G9 the summary is wrong", lambda s: re.sub(r"<b>(\d+)</b> available", "<b>99</b> available", s), "L11"),
    ("G10 the markers are removed", lambda s: s.replace(P.VG_BEGIN, "").replace(P.VG_END, ""), "L11"),
    ("G11 a change outside the generated region", lambda s: s.replace("The first twenty-five galleries.", "The first twenty-six galleries.", 1), "L"),
    ("G12 a mock placeholder image on the wall", lambda s: s.replace('src="../artists/%s/img/' % slug, 'src="../gallery-design-c/mock/', 1), "L11"),
]
for label, f, code in FAULTS:
    bad = f(orig)
    if bad == orig:
        check(label + " (fault could not be planted)", False); continue
    open(vgp, "w", encoding="utf-8").write(bad)
    rc, out = guard(site)
    check(label + " → refused", rc != 0 and code in out, out[-300:])
open(vgp, "w", encoding="utf-8").write(orig)
shutil.rmtree(tmp, ignore_errors=True)
ok = sum(results)
print("\nPLOTART VIRTUAL GALLERY C2 · %d checks, %d passed, %d failed" % (len(results), ok, len(results) - ok))
sys.exit(0 if ok == len(results) else 1)
