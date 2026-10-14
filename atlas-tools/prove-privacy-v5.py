#!/usr/bin/env python3
"""GUARD-CAPABILITY PROOF · privacy notice V5 builder (atlas-tools/build-privacy-v5.py).

Part A · each case breaks ONE input in a real file, runs the V5 builder's
         --check (or the refused action) and asserts REFUSED. Every touched
         file is restored and hashed before and after.
Part B · PUBLICATION REHEARSAL in a throwaway clone (never in this tree):
         fill APPROVAL, run --apply, then run everything publication must keep
         passing: the V5 and V4 builders' published checks, the homeowner
         register builder (still OPEN) and its proof, the V4 proof, the artist
         register builder (still CLOSED), both Worker proofs, the Garden
         proofs, landmarks and first-lead. It also asserts that --apply moved
         the homeowner Worker to V5 and nothing else in it, that the artist
         route stays closed, and that the homeowner Worker code and the Garden
         register are untouched. Nothing from the rehearsal is kept.

Exit 0 = every break caught, the rehearsal passes, this tree byte-identical.
Run: python3 atlas-tools/prove-privacy-v5.py
"""
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PB = ROOT / "atlas-tools" / "build-privacy-v5.py"
DRAFT = ROOT / "governance" / "PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md"
PRIVACY = ROOT / "privacy.html"
ART_WR = ROOT / "worker" / "art-space-register" / "wrangler.toml"
ART_W = ROOT / "worker" / "art-space-register" / "src" / "index.js"
GARDEN_WR = ROOT / "worker" / "garden-register" / "wrangler.toml"
AB = ROOT / "atlas-tools" / "build-artist-register.py"
FILES = [PB, DRAFT, PRIVACY, ART_WR, ART_W, GARDEN_WR, AB]

h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
BEFORE = {str(p): h(p) for p in FILES}
results = []


def run(args, cwd=ROOT):
    return subprocess.run([sys.executable] + [str(a) for a in args], capture_output=True, text=True, cwd=str(cwd))


def case(label, path, old, new, args=None, expect="REFUSED"):
    orig = path.read_bytes()
    try:
        t = orig.decode("utf-8")
        if old not in t:
            results.append((label, False, "mutation anchor not found")); return
        path.write_bytes(t.replace(old, new, 1).encode("utf-8"))
        r = run([PB] + (args or ["--check"]))
        line = (r.stdout.strip().splitlines() or [""])[-1]
        results.append((label, r.returncode != 0 and expect in r.stdout, line[:100]))
    finally:
        path.write_bytes(orig)


ctl0 = run([PB, "--check"]).returncode == 0
LIVE = "PLOTNUA-ARTIST-PRIVACY-V5" in PRIVACY.read_text(encoding="utf-8")

# ---- Part A
case("W1 builder text drifts from the draft", PB, "no payment is offered, and registering",
     "no payment is offered yet, and registering")
case("W1 draft drifts from the builder", DRAFT, "> Your registration is stored privately.",
     "> Your registration is stored securely.")
case("W1 a governed draft line not on the page", DRAFT, "> We keep your registration for no longer than 12 months",
     "> We review every registration monthly.\n\n> We keep your registration for no longer than 12 months")
case("W3 no-automatic-sharing statement removed", PB, "Your details are not shared with homeowners, \"\n          \"automatically or otherwise. ", "\"\n          \"")
case("W6 the Section 10 infrastructure sentence dropped", PB,
     '(THIRD_ANCHOR, THIRD_NEW, "Section 10 anchor"),\n                             ', '')
case("W3 Section 8 says artists can already register", PB,
     '"potential buyers through a home setting. When registrations open, artists will be able to join through "\n'
     '          "PlotArt\'s Artist Register page. Joining is "',
     '"potential buyers through a home setting. You can join it from PlotArt\'s Artist Register page. Joining is "')
case("W3 retention lengthened", PB, "We keep your registration for no longer than 12 months",
     "We keep your registration for no longer than 24 months")
case("W4 consent drifts in the Worker only", ART_W, "does not guarantee an opportunity and that I can withdraw",
     "does not promise an opportunity and that I can withdraw")
case("W4 consent drifts in the artist page builder only", AB, 'registering does not guarantee an opportunity and that "',
     'registering does not promise an opportunity and that "')
case("W4 the Worker collects a field the notice does not describe", ART_W, "'needs', 'portfolio', 'statement'",
     "'needs', 'portfolio', 'instagram', 'statement'")
case("W4 the artist privacy version is not V5", ART_WR, 'ARTIST_PRIVACY_VERSION = "2026-10-PHASE2-V5"',
     'ARTIST_PRIVACY_VERSION = "2026-10-PHASE2-V4"')
case("W4 the Garden Worker moved off V3", GARDEN_WR, 'PRIVACY_VERSION = "2026-10-PHASE2-V3"', 'PRIVACY_VERSION = "2026-10-PHASE2-V5"')
case("W5 an invented assurance", PB, "PlotArt is in development. ", "PlotArt is fully compliant with GDPR. ")
case("W5 the no-guarantee wording removed", PB, ", and registering \"\n          \"does not guarantee an opportunity of any kind", "\"\n          \"")
case("W7 the builder slips in an undeclared change", PB,
     "    out = out.replace(CSS_ANCHOR, CSS_NEW + CSS_ANCHOR, 1)\n",
     "    out = out.replace(CSS_ANCHOR, CSS_NEW + CSS_ANCHOR, 1)\n"
     "    out = out.replace(\"Google Analytics;\", \"Google Analytics (anonymised);\", 1)\n")
case("W2 the V4 homeowner text altered in the input", PRIVACY, "PlotNua is not introducing homeowners to artists",
     "PlotNua is not yet introducing homeowners to artists")
case("W6 Section 7 altered in the input", PRIVACY, "photographs of your garden", "photos of your garden")
if not LIVE:
    case("premature homeowner V5: Worker records V5 before V5 is live", ART_WR,
         'PRIVACY_VERSION = "2026-10-PHASE2-V4"', 'PRIVACY_VERSION = "2026-10-PHASE2-V5"')
    r = run([PB, "--apply"])
    results.append(("--apply while APPROVAL is None", r.returncode != 0 and "NOT APPROVED" in r.stdout, ""))
    case("--apply with an incomplete APPROVAL", PB, "APPROVAL = None",
         'APPROVAL = {"founder_approval": "x", "self_assessment": "x", "risks_resolved": "", "last_updated": "October 2026"}',
         args=["--apply"])
r = run([PB, "--preview", ROOT / "privacy-v5-preview.html"])
results.append(("--preview inside the repository", r.returncode != 0 and "inside the repository" in r.stdout, ""))

# ---- Part B · publication rehearsal in a throwaway clone
rehearsal = []
tmp = pathlib.Path(tempfile.mkdtemp(prefix="pv5-rehearsal-"))
try:
    clone = tmp / "repo"
    subprocess.run(["git", "clone", "-q", "--shared", str(ROOT), str(clone)], check=True)
    shutil.copytree(ROOT, clone, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "node_modules", ".wrangler", "__pycache__"))
    subprocess.run(["git", "add", "-A"], cwd=clone, check=True)
    subprocess.run(["git", "-c", "user.name=r", "-c", "user.email=r@r", "commit", "-q", "--allow-empty", "-m",
                    "rehearsal base"], cwd=clone, check=True)
    (clone / "node_modules").symlink_to("/opt/npm-tools/node_modules") if pathlib.Path("/opt/npm-tools/node_modules").exists() else None
    cb = clone / "atlas-tools" / "build-privacy-v5.py"
    cb.write_text(cb.read_text(encoding="utf-8").replace(
        "APPROVAL = None",
        'APPROVAL = {"founder_approval": "rehearsal", "self_assessment": "rehearsal", "risks_resolved": "rehearsal", '
        '"last_updated": "October 2026"}', 1), encoding="utf-8")
    worker_before = (clone / "worker" / "art-space-register" / "src" / "index.js").read_bytes()
    wr_before = (clone / "worker" / "art-space-register" / "wrangler.toml").read_text(encoding="utf-8")
    at = lambda *p: clone.joinpath(*p)
    steps = [] if LIVE else [("V5 --apply in the clone", [cb, "--apply"], "APPLIED")]
    steps += [
        ("V5 builder verifies the published page", [cb, "--check"], "PUBLISHED"),
        ("V4 builder still verifies the V4 text inside V5", [at("atlas-tools", "build-privacy-v4.py"), "--check"], "PUBLISHED"),
        ("homeowner register builder: R1-R14 pass, still OPEN", [at("atlas-tools", "build-art-space-register.py"), "--check"], "OPEN · CHECK OK"),
        ("artist register builder: A1-A13 pass, still CLOSED", [at("atlas-tools", "build-artist-register.py"), "--check"], "CLOSED · CHECK OK"),
        ("homeowner register proof on V5", [at("atlas-tools", "prove-art-space-register.py")], "PROVEN"),
        ("V4 proof on V5", [at("atlas-tools", "prove-privacy-v4.py")], "PROVEN"),
        ("Garden privacy proof on V5", [at("atlas-tools", "prove-g6-owner-register.py")], "0 failed"),
        ("Garden open-gate proof on V5", [at("atlas-tools", "prove-g6-open-register.py")], ""),
    ]
    for label, args, need in steps:
        r = run(args, cwd=clone)
        ok = r.returncode == 0 and need in r.stdout
        rehearsal.append((label, ok, (r.stdout.strip().splitlines() or [""])[-1][:90]))
    for label, script in (("homeowner Worker proof", "worker/art-space-register/test/prove-art-worker.mjs"),
                          ("artist Worker proof", "worker/art-space-register/test/prove-artist-worker.mjs"),
                          ("landmarks proof on V5", "atlas-tools/prove-landmarks.mjs"),
                          ("first-lead privacy proof on V5", "atlas-tools/prove-first-lead.mjs")):
        r = subprocess.run(["node", str(clone / script)], capture_output=True, text=True, cwd=str(clone))
        rehearsal.append((label, r.returncode == 0, (r.stdout.strip().splitlines() or [""])[-1][:90]))
    wr_after = (clone / "worker" / "art-space-register" / "wrangler.toml").read_text(encoding="utf-8")
    rehearsal.append(("--apply moved ONLY the homeowner PRIVACY_VERSION to V5",
                      LIVE or wr_after == wr_before.replace('\nPRIVACY_VERSION = "2026-10-PHASE2-V4"',
                                                            '\nPRIVACY_VERSION = "2026-10-PHASE2-V5"', 1) != wr_before, ""))
    rehearsal.append(("artist route still closed after publication",
                      'ARTIST_WRITES_ENABLED = "false"' in wr_after, ""))
    rehearsal.append(("homeowner submission handling (Worker code) untouched",
                      (clone / "worker" / "art-space-register" / "src" / "index.js").read_bytes() == worker_before, ""))
    d = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=str(clone), capture_output=True, text=True).stdout.split()
    rehearsal.append(("publication changes exactly privacy.html, wrangler.toml (and the builder's approval)",
                      LIVE or sorted(d) == sorted(["atlas-tools/build-privacy-v5.py", "privacy.html",
                                                   "worker/art-space-register/wrangler.toml"]), " ".join(d)))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

ctl1 = run([PB, "--check"]).returncode == 0
same = BEFORE == {str(p): h(p) for p in FILES}

print("=" * 76)
print("  CONTROL before   %s" % ("PASS" if ctl0 else "FAIL"))
for label, ok, why in results:
    print("  %-58s %s  %s" % (label, "CAUGHT" if ok else "*** MISSED ***", why))
print("  ---- publication rehearsal (throwaway clone)")
for label, ok, why in rehearsal:
    print("  %-58s %s  %s" % (label, "PASS" if ok else "*** FAIL ***", why))
print("  CONTROL after    %s" % ("PASS" if ctl1 else "FAIL"))
print("  every touched file byte-identical after the proof: %s" % ("YES" if same else "NO"))
ok = ctl0 and ctl1 and same and all(c for _, c, _ in results) and all(c for _, c, _ in rehearsal)
print("  %d/%d breaks caught · rehearsal %d/%d — %s" % (sum(c for _, c, _ in results), len(results),
      sum(c for _, c, _ in rehearsal), len(rehearsal), "PROVEN" if ok else "NOT PROVEN"))
sys.exit(0 if ok else 1)
