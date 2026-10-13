#!/usr/bin/env python3
"""GUARD-CAPABILITY PROOF · privacy notice V4 builder (atlas-tools/build-privacy-v4.py).

Part A · each case breaks ONE input in a real file, runs the builder's --check
         (or the refused action) and asserts a REFUSED. Every touched file is
         restored and hashed before and after.
Part B · PUBLICATION REHEARSAL in a throwaway clone (never in this tree):
         fill APPROVAL, run --apply, then run what publication must keep
         passing: the Garden Owner Register privacy proof, the Garden open-gate
         proof, the register builder (still CLOSED), the V4 builder's own
         published check, the landmarks proof and the first-lead proof.
         Nothing from the rehearsal is kept.

Exit 0 = every break caught, the rehearsal passes, this tree byte-identical.
Run: python3 atlas-tools/prove-privacy-v4.py
"""
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PB = ROOT / "atlas-tools" / "build-privacy-v4.py"
DRAFT = ROOT / "governance" / "PRIVACY-VERSION-2026-10-PHASE2-V4-DRAFT.md"
PRIVACY = ROOT / "privacy.html"
PAGE = ROOT / "disc024-open-your-home-to-art.html"
ART_WR = ROOT / "worker" / "art-space-register" / "wrangler.toml"
GARDEN_WR = ROOT / "worker" / "garden-register" / "wrangler.toml"
G6 = ROOT / "atlas-tools" / "prove-g6-owner-register.py"
FILES = [PB, DRAFT, PRIVACY, PAGE, ART_WR, GARDEN_WR, G6]

h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
BEFORE = {str(p): h(p) for p in FILES}
results = []


def run(args, cwd=ROOT):
    return subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=str(cwd))


def case(label, path, old, new, args=None, expect="REFUSED"):
    orig = path.read_bytes()
    try:
        t = orig.decode("utf-8")
        if old not in t:
            results.append((label, False, "mutation anchor not found")); return
        path.write_bytes(t.replace(old, new, 1).encode("utf-8"))
        r = run([str(PB)] + (args or ["--check"]))
        line = (r.stdout.strip().splitlines() or [""])[-1]
        results.append((label, r.returncode != 0 and expect in r.stdout, line[:104]))
    finally:
        path.write_bytes(orig)


def action(label, args, expect="REFUSED"):
    r = run([str(PB)] + args)
    line = (r.stdout.strip().splitlines() or [""])[-1]
    results.append((label, r.returncode != 0 and expect in r.stdout, line[:104]))


ctl0 = run([str(PB), "--check"]).returncode == 0

# ---- Part A
case("V1 builder Section 8 drifts from the draft", PB, "no payment is offered", "no payment is offered yet")
case("V1 draft drifts from the builder", DRAFT, "We keep that note for 12 months after the deletion is completed, and then delete it.",
     "We keep that note for as long as needed.")
case("V3 the no-matching statement removed", PB, "there is no matching or booking service, ", "")
case("V3 deletion-note retention removed", PB, " We keep that note for 12 months after the deletion is completed, and then delete it.", "")
case("V4 on-page notice retention differs", PAGE, "We keep that note for 12 months after the deletion is",
     "We keep that note for 18 months after the deletion is")
case("V4 Art Worker not on V4", ART_WR, 'PRIVACY_VERSION = "2026-10-PHASE2-V4"', 'PRIVACY_VERSION = "2026-10-PHASE2-V3"')
case("V4 Garden Worker moved off V3", GARDEN_WR, 'PRIVACY_VERSION = "2026-10-PHASE2-V3"', 'PRIVACY_VERSION = "2026-10-PHASE2-V4"')
case("V5 an invented legal assurance", PB, "Records are reviewed by a person at PlotNua.",
     "PlotNua is fully compliant with GDPR. Records are reviewed by a person at PlotNua.")
case("V6 the builder slips in an undeclared change", PB,
     "    out = out.replace(g7, g7 + \"\\n\" + section8_html().rstrip(\"\\n\") + \"\\n\", 1)\n",
     "    out = out.replace(g7, g7 + \"\\n\" + section8_html().rstrip(\"\\n\") + \"\\n\", 1)\n"
     "    out = out.replace(\"Google Analytics;\", \"Google Analytics (anonymised);\", 1)\n")
case("V2 input already altered in Section 7", PRIVACY, "photographs of your garden", "photos of your garden")
action("--preview inside the repository", ["--preview", str(ROOT / "privacy-v4-preview.html")])
action("--apply while APPROVAL is None", ["--apply"])
case("--apply with an incomplete APPROVAL", PB, "APPROVAL = None",
     'APPROVAL = {"founder_approval": "x", "legal_review": "", "last_updated": "November 2026"}', args=["--apply"])

# ---- Part B · publication rehearsal in a throwaway clone
rehearsal = []
tmp = pathlib.Path(tempfile.mkdtemp(prefix="pv4-rehearsal-"))
try:
    clone = tmp / "repo"
    subprocess.run(["git", "clone", "-q", "--shared", str(ROOT), str(clone)], check=True)
    shutil.copytree(ROOT, clone, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "node_modules", ".wrangler", "__pycache__"))
    cb = clone / "atlas-tools" / "build-privacy-v4.py"
    cb.write_text(cb.read_text(encoding="utf-8").replace(
        "APPROVAL = None",
        'APPROVAL = {"founder_approval": "rehearsal", "legal_review": "rehearsal", "last_updated": "October 2026"}', 1),
        encoding="utf-8")
    steps = [
        ("V4 --apply in the clone", [str(cb), "--apply"], "APPLIED"),
        ("V4 builder verifies the published page", [str(cb), "--check"], "PUBLISHED"),
        ("Garden privacy proof passes on V4", [str(clone / "atlas-tools" / "prove-g6-owner-register.py")], "0 failed"),
        ("Garden open-gate proof passes on V4", [str(clone / "atlas-tools" / "prove-g6-open-register.py")], ""),
        ("register builder: still CLOSED, R1-R14 pass", [str(clone / "atlas-tools" / "build-art-space-register.py"), "--check"], "CLOSED"),
    ]
    for label, args, need in steps:
        r = run(args, cwd=clone)
        ok = r.returncode == 0 and need in r.stdout
        rehearsal.append((label, ok, (r.stdout.strip().splitlines() or [""])[-1][:96]))
    for label, script in (("landmarks proof passes on V4", "prove-landmarks.mjs"),
                          ("first-lead privacy proof passes on V4", "prove-first-lead.mjs")):
        r = subprocess.run(["node", str(clone / "atlas-tools" / script)], capture_output=True, text=True, cwd=str(clone))
        rehearsal.append((label, r.returncode == 0, (r.stdout.strip().splitlines() or [""])[-1][:96]))
    import importlib.util
    spec = importlib.util.spec_from_file_location("pv4", PB)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    expected = G6.read_text(encoding="utf-8")
    for a, b in mod.G6_CO_EDITS:
        expected = expected.replace(a, b, 1)
    got = (clone / "atlas-tools" / "prove-g6-owner-register.py").read_text(encoding="utf-8")
    rehearsal.append(("Garden proof: only the %d declared co-edits" % len(mod.G6_CO_EDITS),
                      got == expected and got != G6.read_text(encoding="utf-8"), ""))
    for label, rel in (("Garden Worker untouched by publication", "worker/garden-register"),
                       ("Garden check page untouched by publication", "disc025-borrowed-garden-check.html")):
        d = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=str(clone))
        rehearsal.append((label, d.returncode == 0, ""))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

ctl1 = run([str(PB), "--check"]).returncode == 0
same = BEFORE == {str(p): h(p) for p in FILES}

print("=" * 76)
print("  CONTROL before   %s" % ("PASS" if ctl0 else "FAIL"))
for label, ok, why in results:
    print("  %-46s %s  %s" % (label, "CAUGHT" if ok else "*** MISSED ***", why))
print("  ---- publication rehearsal (throwaway clone)")
for label, ok, why in rehearsal:
    print("  %-46s %s  %s" % (label, "PASS" if ok else "*** FAIL ***", why))
print("  CONTROL after    %s" % ("PASS" if ctl1 else "FAIL"))
print("  every touched file byte-identical after the proof: %s" % ("YES" if same else "NO"))
ok = ctl0 and ctl1 and same and all(c for _, c, _ in results) and all(c for _, c, _ in rehearsal)
print("  %d/%d breaks caught · rehearsal %d/%d — %s" % (sum(c for _, c, _ in results), len(results),
      sum(c for _, c, _ in rehearsal), len(rehearsal), "PROVEN" if ok else "NOT PROVEN"))
sys.exit(0 if ok else 1)
