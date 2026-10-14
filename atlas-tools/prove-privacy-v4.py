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

AFTER PUBLICATION (founder approval, 13 Oct 2026, 23:50; notice only, the
register stays closed): Part A keeps every content case, which --check now
runs against the published page, and replaces the pre-publication approval
cases with their published-state equivalents. Part B becomes a post-publication
verification in a throwaway clone: the same downstream proofs, the register
still CLOSED, and the Garden proof carrying exactly the declared co-edits.

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
PUBLISHED = "PLOTNUA-ART-PRIVACY-V4" in PRIVACY.read_text(encoding="utf-8")

# ---- Part A
case("V1 builder Section 8 drifts from the draft", PB, "no payment is offered", "no payment is offered yet")
case("V1 draft drifts from the builder", DRAFT, "That entry contains nothing that identifies you.",
     "That entry contains very little.")
case("V3 the no-matching statement removed", PB, "there is no matching or booking service, ", "")
case("V3 anonymous-log assurance removed", PB, " That entry contains nothing that identifies you.", "", )
case("V3 retention lengthened to 24 months", PB, "We keep your record for no longer than 12 months", "We keep your record for no longer than 24 months")
case("V4 on-page notice retention differs", PAGE, "A maximum of 12 months, and less",
     "A maximum of 18 months, and less")
case("V4 on-page notice reintroduces a fingerprint", PAGE, "We keep only an anonymous log entry",
     "We keep a fingerprint and an anonymous log entry")
# Once privacy V5 is live the Art Worker records V5, the notice in force.
V5_LIVE = "PLOTNUA-ARTIST-PRIVACY-V5" in PRIVACY.read_text(encoding="utf-8")
CUR_VERSION = 'PRIVACY_VERSION = "%s"' % ("2026-10-PHASE2-V5" if V5_LIVE else "2026-10-PHASE2-V4")
case("V4 Art Worker not on the notice in force", ART_WR, CUR_VERSION, 'PRIVACY_VERSION = "2026-10-PHASE2-V3"')
case("V4 Garden Worker moved off V3", GARDEN_WR, 'PRIVACY_VERSION = "2026-10-PHASE2-V3"', 'PRIVACY_VERSION = "2026-10-PHASE2-V4"')
case("V5 an invented legal assurance", PB, "Records are reviewed by a person at PlotNua.",
     "PlotNua is fully compliant with GDPR. Records are reviewed by a person at PlotNua.")
case("V6 the builder slips in an undeclared change", PB,
     "    out = out.replace(g7, g7 + \"\\n\" + section8_html().rstrip(\"\\n\") + \"\\n\", 1)\n",
     "    out = out.replace(g7, g7 + \"\\n\" + section8_html().rstrip(\"\\n\") + \"\\n\", 1)\n"
     "    out = out.replace(\"Google Analytics;\", \"Google Analytics (anonymised);\", 1)\n")
case("V2 Section 2 pointer to Section 8 dropped", PB,
     '((SEC2_ANCHOR, SEC2_NEW, "Section 2 anchor"), (THIRD_ANCHOR', '((THIRD_ANCHOR')
case("V1 Section 2 sentence drifts from the draft", PB,
     'SEC2_NEW = "    <p>If you choose to join the Art Space Register, we also collect',
     'SEC2_NEW = "    <p>If you join the Art Space Register, we also collect')
case("V2 input already altered in Section 7", PRIVACY, "photographs of your garden", "photos of your garden")
action("--preview inside the repository", ["--preview", str(ROOT / "privacy-v4-preview.html")])
if not PUBLISHED:
    action("--apply while APPROVAL is None", ["--apply"])
    case("--apply with an incomplete APPROVAL", PB, "APPROVAL = None",
         'APPROVAL = {"founder_approval": "x", "self_assessment": "x", "risks_resolved": "", "last_updated": "November 2026"}', args=["--apply"])
    # SAFETY: this case must never reach a real write. It unsets BACKUP_PERIOD on the same line that fills APPROVAL,
    # so APPROVAL is complete but the period is not, and --apply must refuse.
    case("--apply approved but BACKUP_PERIOD unconfirmed", PB, 'BACKUP_PERIOD = "up to 1 year"',
         'BACKUP_PERIOD = None\nAPPROVAL = {"founder_approval": "x", "self_assessment": "x", "risks_resolved": "x", "last_updated": "November 2026"}', args=["--apply"])
else:
    # Published state. --apply can never write again: the page already carries Section 8.
    action("--apply again on the published page", ["--apply"])
    case("published V4 with APPROVAL removed", PB, "APPROVAL = {", "APPROVAL = None\n_WITHDRAWN = {")
    case("published V4 with an incomplete APPROVAL", PB, '"risks_resolved": "governance/', '"risks_unrecorded": "governance/')
    if not V5_LIVE:   # once V5 is live, the label is V5's; prove-privacy-v5.py proves it
        case("published Last updated label not the approved one", PRIVACY,
             "Last updated: October 2026", "Last updated: November 2026")
    else:
        case("published V5 page altered inside the V4 text", PRIVACY,
             "Records are reviewed by a person at PlotNua.", "Records are reviewed by PlotNua.")
    case("published page altered outside Section 8", PRIVACY, "<h2>9. Cookies</h2>", "<h2>9. Cookie use</h2>")

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
        'APPROVAL = {"founder_approval": "rehearsal", "self_assessment": "rehearsal", "risks_resolved": "rehearsal", '
        '"last_updated": "October 2026"}', 1),
        encoding="utf-8")
    steps = [] if PUBLISHED else [("V4 --apply in the clone", [str(cb), "--apply"], "APPLIED")]
    steps += [
        ("V4 builder verifies the published page", [str(cb), "--check"], "PUBLISHED"),
        ("Garden privacy proof passes on V4", [str(clone / "atlas-tools" / "prove-g6-owner-register.py")], "0 failed"),
        ("Garden open-gate proof passes on V4", [str(clone / "atlas-tools" / "prove-g6-open-register.py")], ""),
        ("register builder: R1-R14 pass (open since 14 Oct 2026)", [str(clone / "atlas-tools" / "build-art-space-register.py"), "--check"], "CHECK OK"),
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
    got = (clone / "atlas-tools" / "prove-g6-owner-register.py").read_text(encoding="utf-8")
    if PUBLISHED:
        # Undo the declared co-edits: what remains must be the V3-era Garden proof, i.e. no
        # V3 anchor survives and each declared replacement occurs exactly once.
        ok_co = all(got.count(b) == 1 and a not in got for a, b in mod.G6_CO_EDITS)
        rehearsal.append(("Garden proof: exactly the %d declared co-edits" % len(mod.G6_CO_EDITS), ok_co, ""))
    else:
        expected = G6.read_text(encoding="utf-8")
        for a, b in mod.G6_CO_EDITS:
            expected = expected.replace(a, b, 1)
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
