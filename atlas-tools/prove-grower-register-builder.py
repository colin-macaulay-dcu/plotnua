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
    ("G4 another page links to the closed register", append("index.html", '\n<a href="borrowed-garden-grower-register.html">x</a>\n'), "G4"),
    ("G4b sitemap lists the closed register", edit("sitemap.xml", "</urlset>", "<url><loc>https://plotnua.ie/borrowed-garden-grower-register.html</loc></url></urlset>"), "G4"),
    ("G5 a phone field is added", edit(BUILDER, 'autocomplete="email" maxlength="120" required></div>', 'autocomplete="email" maxlength="120" required><input type="tel" name="phone"></div>'), "G5"),
    ("G6 an honesty line is removed", edit(BUILDER, "We may never find a garden near you.</li>", "</li>"), "G6"),
    ("G6b a promise is added", edit(BUILDER, "Two registers, one careful introduction.", "Get matched with a garden this week."), "G6"),
    ("G7 experience reaches the payload", edit(BUILDER, "consent_text: CONSENT_TEXT,\n      source:", "consent_text: CONSENT_TEXT,\n      experience: checked('experience'),\n      source:"), "G7"),
    ("G8 host check page edited", append("disc025-borrowed-garden-check.html", "\n<!-- edit -->\n"), "G8"),
    ("G8b privacy.html edited while closed", append("privacy.html", "\n<!-- edit -->\n"), "G8"),
    ("G8c host Worker handler edited", edit(W, "if (!size_note) return REFUSED(cors, 'size_note');", "if (!size_note) return REFUSED(cors, 'size');"), "G8"),
    ("G9 opened without approvals", edit(BUILDER, "GROWER_PUBLIC = False", "GROWER_PUBLIC = True"), "G9"),
    ("G10 shell marker missing", edit("artist-register.html", "<!-- PLOTNUA SEARCH RAIL v1 · END -->", "<!-- rail end -->"), "G10"),
    ("G11 Community Roots used as the register name", edit(BUILDER, "<h1>Somewhere to grow, closer than you think.</h1>", "<h1>The Community Roots Gardener Register</h1>"), "G11"),
]


def main():
    caught = blind = 0
    for name, mut, guard in CASES:
        with tempfile.TemporaryDirectory() as d:
            tree = Path(d) / "repo"
            # a git worktree-free copy that still answers `git show 84453f1:...`
            subprocess.run(["git", "clone", "-q", "--shared", str(ROOT), str(tree)], check=True)
            for rel in [BUILDER, W, "artist-register.html"]:
                shutil.copy(ROOT / rel, tree / rel)
            if mut:
                mut(tree)
            r = subprocess.run([sys.executable, BUILDER], cwd=tree, capture_output=True, text=True)
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
