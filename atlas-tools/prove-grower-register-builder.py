#!/usr/bin/env python3
"""Capability proof for atlas-tools/build-grower-register.py.

Each case copies the repo's relevant files into a scratch tree, makes ONE
deliberate break, runs the builder there and requires it to REFUSE (exit 2)
naming the expected guard. A control case (no break) must build. A guard
never seen to refuse is not a proven guard.

  python3 atlas-tools/prove-grower-register-builder.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILDER = "atlas-tools/build-grower-register.py"
W = "worker/garden-register/src/index.js"


def edit(path, old, new):
    def f(tree: Path):
        p = tree / path
        s = p.read_text()
        assert s.count(old) >= 1, f"anchor missing in {path}: {old[:50]}"
        p.write_text(s.replace(old, new, 1))
    return f


def append(path, text):
    def f(tree: Path):
        p = tree / path
        p.write_text(p.read_text() + text)
    return f


CASES = [
    ("control", None, None),
    ("G1 Worker grower sentence edited", edit(W, "tell me about possible growing space nearby", "tell me about growing space"), "G1"),
    ("G2 Worker vocabulary gains a district", edit(W, "'elsewhere_in_dublin', 'elsewhere_in_ireland'],", "'elsewhere_in_dublin', 'elsewhere_in_ireland', 'cork'],"), "G2"),
    ("G3 Worker allow-list drops growing_note", edit(W, "'timing', 'growing_note', 'over_18'", "'timing', 'over_18'"), "G3"),
    ("G3b an extra key reaches the payload", edit(BUILDER, "consent_text: CONSENT_TEXT,\n      source:", "consent_text: CONSENT_TEXT,\n      experience: 'new',\n      source:"), "G3"),
    ("G4 another page links to the closed grower check", append("index.html", '\n<a href="disc025-borrowed-garden-grower-check.html">x</a>\n'), "G4"),
    ("G4b sitemap lists the closed grower check", edit("sitemap.xml", "</urlset>", "<url><loc>https://plotnua.ie/disc025-borrowed-garden-grower-check.html</loc></url></urlset>"), "G4"),
    ("G5 a phone field is added", edit(BUILDER, 'autocomplete="email" maxlength="120" required>', 'autocomplete="email" maxlength="120" required><input type="tel" name="phone">'), "G5"),
    ("G6 an honesty line is removed", edit(BUILDER, "We may never find a garden near you. Nothing is shared", "Nothing is shared"), "G6"),
    ("G6b a promise is added", edit(BUILDER, "Looking for somewhere to grow?</h1>", "Get matched with a garden this week.</h1>"), "G6"),
    ("G8 host Property Check edited", append("disc025-borrowed-garden-check.html", "\n<!-- edit -->\n"), "G8"),
    ("G8b privacy.html edited while closed", append("privacy.html", "\n<!-- edit -->\n"), "G8"),
    ("G8c host Worker handler edited", edit(W, "if (!size_note) return REFUSED(cors, 'size_note');", "if (!size_note) return REFUSED(cors, 'size');"), "G8"),
    ("G8d Discovery edited while closed", append("discovery-the-borrowed-garden.html", "\n<!-- edit -->\n"), "G8"),
    ("G9 launched without approvals", edit(BUILDER, "GROWER_PUBLIC = False", "GROWER_PUBLIC = True"), "G9"),
    ("G9b launched with approvals but no V6 notice", edit(BUILDER, "GROWER_PUBLIC = False\n", "GROWER_PUBLIC = True\n").__class__ and
        (lambda t: (edit(BUILDER, "GROWER_PUBLIC = False", "GROWER_PUBLIC = True")(t),
                    edit(BUILDER, '"privacy_v6_wording_approved": None', '"privacy_v6_wording_approved": "test"')(t),
                    edit(BUILDER, '"launch_approved": None', '"launch_approved": "test"')(t))), "G9"),
    ("G11 Community Roots used as the register name", edit(BUILDER, "Looking for somewhere to grow?</h1>", "The Community Roots Gardener Register</h1>"), "G11"),
    ("P0 privacy V6 applied without approval", "privacy", "P0"),
    ("P3 a Garden Owner sentence altered by the V6 edit", "privacy-p3", "P3"),
]


def main():
    caught = blind = 0
    for name, mut, guard in CASES:
        with tempfile.TemporaryDirectory() as d:
            tree = Path(d) / "repo"
            # a git worktree-free copy that still answers `git show 84453f1:...`
            subprocess.run(["git", "clone", "-q", "--shared", str(ROOT), str(tree)], check=True)
            for rel in [BUILDER, W]:
                shutil.copy(ROOT / rel, tree / rel)
            cmd = [sys.executable, BUILDER]
            if mut == "privacy":
                shutil.copy(ROOT / "atlas-tools/privacy_v6_layer.py", tree / "atlas-tools/privacy_v6_layer.py")
                cmd = [sys.executable, "atlas-tools/build-privacy-v6.py"]
                shutil.copy(ROOT / "atlas-tools/build-privacy-v6.py", tree / "atlas-tools/build-privacy-v6.py")
            elif mut == "privacy-p3":
                shutil.copy(ROOT / "atlas-tools/build-privacy-v6.py", tree / "atlas-tools/build-privacy-v6.py")
                edit("atlas-tools/build-privacy-v6.py", 'APPROVAL = None', 'APPROVAL = "test"')(tree)
                shutil.copy(ROOT / "atlas-tools/privacy_v6_layer.py", tree / "atlas-tools/privacy_v6_layer.py")
                edit("atlas-tools/privacy_v6_layer.py", "return out.replace(S2_OLD, S2_NEW)",
                     "return out.replace('Matching is not live, and joining the register does not arrange an introduction.</p>', 'Matching is live.</p>', 1).replace(S2_OLD, S2_NEW)")(tree)
                cmd = [sys.executable, "atlas-tools/build-privacy-v6.py"]
            elif mut:
                mut(tree)
            r = subprocess.run(cmd, cwd=tree, capture_output=True, text=True)
            if guard is None:
                ok = r.returncode == 0
                print(("  [PASS] " if ok else "  [FAIL] ") + "control builds" + ("" if ok else "  " + r.stderr.strip()))
                caught += ok; blind += (not ok)
            else:
                ok = r.returncode == 2 and f"REFUSED: {guard}" in r.stderr
                print(("  [CAUGHT] " if ok else "  [BLIND] ") + name + ("" if ok else f"  rc={r.returncode} {r.stderr.strip()[:160]}"))
                caught += ok; blind += (not ok)
    print(f"\n  {caught} correct, {blind} blind or wrong")
    sys.exit(1 if blind else 0)


if __name__ == "__main__":
    main()
