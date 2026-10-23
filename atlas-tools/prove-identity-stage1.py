#!/usr/bin/env python3
"""
CAPABILITY PROOF · shared identity layer, Phase 5 Stage 1

    python3 atlas-tools/prove-identity-stage1.py [--base <git-ref>]

Part A (only with --base): against the given commit, proves that removing the
identity insertions from each Stage 1 page gives back that commit's file
byte-for-byte, and lists every file that differs from it.

Part B: copies the site to a scratch folder and plants one fault at a time.
build-identity-stage1.py --check must REFUSE every one. A guard that cannot
fail proves nothing. The real repository is never written.
"""
import os, re, shutil, subprocess, sys, tempfile, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "atlas-tools" / "build-identity-stage1.py"
spec = importlib.util.spec_from_file_location("bid", B); bid = importlib.util.module_from_spec(spec); spec.loader.exec_module(bid)
_t = re.findall(r'<meta name="theme-color" content="(#[0-9A-Fa-f]{6})">', (ROOT / "index.html").read_text(encoding="utf-8"))
bid.HOME_THEME = _t[0] if len(_t) == 1 else None   # strip() reverses change T using the homepage's value
fails = 0
def ok(m): print("  [PASS] " + m)
def bad(m):
    global fails; fails += 1; print("  [FAIL] " + m)

if "--base" in sys.argv:
    base = sys.argv[sys.argv.index("--base") + 1]
    print("\n  A · reversibility against %s\n" % base)
    for page in bid.PAGES:
        old = subprocess.run(["git", "show", "%s:%s" % (base, page)], cwd=ROOT, capture_output=True, text=True).stdout
        new = (ROOT / page).read_text(encoding="utf-8")
        if "PLOTNUA IDENTITY v1" in old:      # already carried the layer at the base: must be untouched
            (ok if new == old else bad)("%s: unchanged from %s (layer already present there)" % (page, base))
        else:
            (ok if bid.strip(new) == old and new != old else bad)("%s: insertions removed = %s byte-for-byte" % (page, base))
    for f in bid.PROTECTED:                 # I11 against the base commit
        old = subprocess.run(["git", "show", "%s:%s" % (base, f)], cwd=ROOT, capture_output=True).stdout
        (ok if (ROOT / f).read_bytes() == old else bad)("I11 %s byte-identical to %s" % (f, base))
    diff = subprocess.run(["git", "diff", "--name-only", base, "--"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    diff += subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    allowed = set(bid.PAGES) | {"assets/identity/pn-identity.css", "atlas-tools/build-identity-stage1.py",
                                "atlas-tools/prove-identity-stage1.py", ".github/workflows/image-rights-gate.yml",
                                "atlas-tools/build-triq-cube-public.py",
                                "assets/identity/pn-identity-discovery.css",
                                # Stage 2c Premium Discovery prototype (23 Oct 2026)
                                "assets/identity/pn-premium-discovery.css",
                                "atlas-tools/prove-premium-discovery-a-home-for-art.py",
                                "atlas-tools/prove-premium-discovery-capability.py",
                                "atlas-tools/premium-discovery/a-home-for-art-base.json"}
    extra = sorted(set(diff) - allowed)
    (ok if not extra else bad)("only Stage 1 files differ from %s%s" % (base, "" if not extra else ": " + ", ".join(extra)))
    print("  changed files: " + ", ".join(sorted(set(diff))))

print("\n  B · each guard refuses a planted fault\n")
NEEDED = list(bid.PAGES) + ["index.html", "assets/identity/pn-identity.css", "assets/identity/pn-identity-discovery.css", "assets/identity/pn-premium-discovery.css"] + [f for f in bid.PROTECTED if (ROOT / f).exists()]
def scratch():
    d = Path(tempfile.mkdtemp(prefix="pnid-"))
    for f in NEEDED:
        (d / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / f, d / f)
    for f in ROOT.glob("*.html"):
        if not (d / f.name).exists(): shutil.copy2(f, d / f.name)
    return d
def run(d):
    p = subprocess.run([sys.executable, str(B), "--check"], env=dict(os.environ, PN_ROOT=str(d)), capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1]
def sub(d, f, a, b_):
    t = (d / f).read_text(encoding="utf-8")
    if a not in t: raise SystemExit("proof setup: %r not in %s" % (a, f))
    (d / f).write_text(t.replace(a, b_, 1), encoding="utf-8")

d = scratch(); rc, line = run(d); shutil.rmtree(d)
(ok if rc == 0 else bad)("control: the unmodified copy passes (%s)" % line[:60])

MUT = [
 ("I2 nav link text edited by hand", lambda d: sub(d, "contact.html", ">Your Plot</a>", ">Your plot</a>")),
 ("I2 stylesheet link removed from a page", lambda d: sub(d, "privacy.html", '<link rel="stylesheet" href="assets/identity/pn-identity.css">\n', "")),
 ("I2 reading surface switched by hand", lambda d: sub(d, "terms.html", "pn-id--paper", "pn-id--dark")),
 ("I4 token drifts from the homepage", lambda d: sub(d, "assets/identity/pn-identity.css", "--p4-earth:#27282A", "--p4-earth:#28282A")),
 ("I4 homepage token changes, shared file not updated", lambda d: sub(d, "index.html", "--p4-terra-text:#CF8566", "--p4-terra-text:#CF8567")),
 ("I5 unscoped rule added", lambda d: sub(d, "assets/identity/pn-identity.css", "/* ---- 2 · base type", "h1{ color:red; }\n/* ---- 2 · base type")),
 ("I6 identity layer added to the homepage", lambda d: sub(d, "index.html", "</head>", '<link rel="stylesheet" href="assets/identity/pn-identity.css">\n</head>')),
 ("I7 markers on a page outside Stage 1", lambda d: sub(d, "discoveries.html", "</head>", "<!-- PLOTNUA IDENTITY v1 · HEAD · BEGIN -->\n</head>")),
 ("I9 theme colour edited by hand on one page", lambda d: sub(d, "privacy.html", 'content="#27282A"', 'content="#27282B"')),
 ("I9 homepage theme colour changes, pages not rebuilt", lambda d: sub(d, "index.html", '<meta name="theme-color" content="#27282A">', '<meta name="theme-color" content="#28282A">')),
 ("I9 a page left on the previous homepage theme colour", lambda d: sub(d, "terms.html", 'content="#27282A"', 'content="#2A2622"')),
 ("I9 a second theme-color meta added to a page", lambda d: sub(d, "contact.html", '<meta name="theme-color" content="#27282A">', '<meta name="theme-color" content="#27282A">\n<meta name="theme-color" content="#1F3B2E">')),
 ("I10 Discovery stylesheet linked from a page outside the pilot", lambda d: sub(d, "discovery-hidden-cars.html", "</head>", '<link rel="stylesheet" href="assets/identity/pn-identity-discovery.css">\n</head>')),
 ("I10 Discovery class removed from a pilot page", lambda d: sub(d, "discovery-hidden-bins.html", 'class="pn-id pn-id--dark pn-id--disc"', 'class="pn-id pn-id--dark"')),
 ("I10 Discovery stylesheet removed from a pilot page", lambda d: sub(d, "discoveries.html", '<link rel="stylesheet" href="assets/identity/pn-identity-discovery.css">\n', "")),
 ("I12 unscoped rule added to the Discovery layer", lambda d: sub(d, "assets/identity/pn-identity-discovery.css", "/* ---- 2 · hero", ".lib-card{ border-radius:40px; }\n/* ---- 2 · hero")),
 ("I12 rule scoped to Stage 1 only (body.pn-id) in the Discovery layer", lambda d: sub(d, "assets/identity/pn-identity-discovery.css", "/* ---- 2 · hero", "body.pn-id .footer-word{ color:red; }\n/* ---- 2 · hero")),
 ("I12 Discovery layer redefines a homepage token", lambda d: sub(d, "assets/identity/pn-identity-discovery.css", "/* ---- 2 · hero", "body.pn-id.pn-id--disc{ --p4-earth:#000000; }\n/* ---- 2 · hero")),
 ("I2 Discovery header edited by hand", lambda d: sub(d, "discovery-living-in-the-garden.html", '<div class="pn-id-header" role="region" aria-label="PlotNua site">', '<div class="pn-id-header">')),
 ("I13 Premium stylesheet linked from a page outside Stage 2c", lambda d: sub(d, "discovery-hidden-cars.html", "</head>", '<link rel="stylesheet" href="assets/identity/pn-premium-discovery.css">\n</head>')),
 ("I13 Premium class removed from the prototype page", lambda d: sub(d, "discovery-a-home-for-art.html", 'class="pn-id pn-id--dark pn-id--disc pn-pd"', 'class="pn-id pn-id--dark pn-id--disc"')),
 ("I13 Premium class added to a standard Discovery by hand", lambda d: sub(d, "discovery-hidden-cars.html", 'class="pn-id pn-id--dark pn-id--disc"', 'class="pn-id pn-id--dark pn-id--disc pn-pd"')),
 ("I13 Premium stylesheet removed from the prototype page", lambda d: sub(d, "discovery-a-home-for-art.html", '<link rel="stylesheet" href="assets/identity/pn-premium-discovery.css">\n', "")),
 ("I14 unscoped rule added to the Premium layer", lambda d: sub(d, "assets/identity/pn-premium-discovery.css", "/* ---- canvas, rhythm", ".pd-card{ border-radius:0; }\n/* ---- canvas, rhythm")),
 ("I14 Discovery-scoped (not Premium) rule in the Premium layer", lambda d: sub(d, "assets/identity/pn-premium-discovery.css", "/* ---- canvas, rhythm", "body.pn-id.pn-id--disc .related{ display:none; }\n/* ---- canvas, rhythm")),
 ("I14 Premium layer redefines a homepage token", lambda d: sub(d, "assets/identity/pn-premium-discovery.css", "/* ---- canvas, rhythm", "body.pn-id.pn-pd{ --p4-ivory:#FFFFFF; }\n/* ---- canvas, rhythm")),
 ("I8 skip link target removed", lambda d: sub(d, "about.html", '<span id="pn-id-content" tabindex="-1"></span>\n', "")),
]
for name, f in MUT:
    d = scratch(); f(d); rc, line = run(d); shutil.rmtree(d)
    (ok if rc != 0 else bad)("%s -> refused: %s" % (name, line[:110]))
print("\n  %s · %d planted faults, %d not caught\n" % ("PROOF OK" if not fails else "PROOF FAILED", len(MUT), fails))
sys.exit(1 if fails else 0)
