#!/usr/bin/env python3
"""Proof of the Premium Discovery safety lock in build-a-home-for-art-merge.py
(founder condition, 23 Oct 2026). Runs the builder in throwaway git worktrees,
never in this checkout, and needs the repository history (local runs).

  T1  L1  target is the approved Premium Discovery page (this branch's HEAD):
          --apply and --check refuse with L1; every file in the tree is
          byte-for-byte unchanged. Control: the ORIGINAL builder on the same
          input replaces the page while printing "nothing written"
  T2  L2  incompatible source, ordinary target (production 0cb456d, where the
          consolidation edits no longer apply): --apply refuses with M9 and the
          tree is byte-for-byte unchanged
  T3  L3  refusal after the writes (a guard fault planted where only the
          post-write guards can see it): every touched file restored
          byte-for-byte, the whole tree identical to before the run
  T4      compatible input (f20fa3e, the builder's own last state, with the
          page perturbed and the redirect removed): the locked builder and the
          original builder produce byte-identical trees and identical output;
          --check output identical on the unperturbed input

  python3 atlas-tools/prove-a-home-for-art-merge-lock.py
"""
import hashlib, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B = "atlas-tools/build-a-home-for-art-merge.py"
NEW = (ROOT / B).read_bytes()
ORIG = subprocess.run(["git", "-C", str(ROOT), "show", "f20fa3e:" + B], capture_output=True, check=True).stdout
PROD = "0cb456d9b0263e54cdcbbf9363fa4b9dc39ce576"
COMPAT = "f20fa3e"
fails = 0
work = Path(tempfile.mkdtemp(prefix="pnlock-"))

def ok(c, m):
    global fails
    if not c: fails += 1
    print("  [%s] %s" % ("PASS" if c else "FAIL", m))

def tree(ref, builder):
    d = work / ("wt%d" % len(list(work.iterdir())))
    subprocess.run(["git", "-C", str(ROOT), "worktree", "add", "--detach", str(d), ref], capture_output=True, check=True)
    (d / B).write_bytes(builder)
    return d

def snap(d):
    out = {}
    for p in sorted(d.rglob("*")):
        if p.is_file() and ".git" not in p.relative_to(d).parts and "__pycache__" not in p.parts:
            out[str(p.relative_to(d))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

def run(d, *args):
    p = subprocess.run([sys.executable, B, *args], cwd=d, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()

def drop(d):
    subprocess.run(["git", "-C", str(ROOT), "worktree", "remove", "--force", str(d)], capture_output=True)

def edit(d, f, a, b):
    t = (d / f).read_text(encoding="utf-8")
    if a not in t: raise SystemExit("proof setup: %r not in %s" % (a[:50], f))
    (d / f).write_text(t.replace(a, b, 1), encoding="utf-8")

try:
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    print("\n  T1 · target is the approved Premium Discovery page (HEAD %s)\n" % head[:7])
    d = tree("HEAD", NEW); s0 = snap(d)
    rc, out = run(d, "--apply")
    ok(rc == 2 and "REFUSED: L1" in out, "--apply refuses with L1: %s" % out.splitlines()[-1][:110])
    ok(snap(d) == s0, "every file byte-for-byte unchanged after --apply (%d files)" % len(s0))
    rc, out = run(d, "--check")
    ok(rc == 2 and "REFUSED: L1" in out and snap(d) == s0, "--check refuses with L1, tree unchanged")
    drop(d)
    d = tree("HEAD", ORIG); s0 = snap(d); rc, out = run(d, "--apply"); s1 = snap(d)
    changed = sorted(k for k in set(s0) | set(s1) if s0.get(k) != s1.get(k))
    ok(rc == 2 and "nothing written" in out and "discovery-a-home-for-art.html" in changed,
       "control: the ORIGINAL builder prints 'nothing written' yet has replaced %s (the defect fixed here)" % ", ".join(changed))
    drop(d)

    print("\n  T2 · incompatible source, ordinary target (production %s)\n" % PROD[:7])
    d = tree(PROD, NEW); s0 = snap(d)
    rc, out = run(d, "--apply")
    ok(rc == 2 and "REFUSED: M9" in out, "--apply refuses with M9 before writing: %s" % out.splitlines()[-1][:100])
    changed = sorted(k for k in set(s0) | set(snap(d)) if s0.get(k) != snap(d).get(k))
    ok(not changed, "every file byte-for-byte unchanged%s" % ("" if not changed else ": " + ", ".join(changed[:5])))
    drop(d)

    print("\n  T3 · refusal after the writes: transactional restore (%s)\n" % COMPAT)
    d = tree(COMPAT, NEW)
    edit(d, "discovery-a-home-for-art.html", "Three people are better off.", "Three people are better off!")   # forces a rewrite
    (d / "discovery-open-your-home-to-art.html").unlink()                                                     # forces a write
    edit(d, "sitemap.xml", "</urlset>", "  <url><loc>https://plotnua.ie/discovery-open-your-home-to-art.html</loc></url>\n</urlset>")  # M7 sees it only after writing
    s0 = snap(d)
    rc, out = run(d, "--apply")
    ok(rc == 2 and "L3 every file restored" in out and "REFUSED: M7" in out, "post-write guard refuses and restores: %s" % " | ".join(out.splitlines()[-2:])[:130])
    s1 = snap(d); changed = sorted(k for k in set(s0) | set(s1) if s0.get(k) != s1.get(k))
    ok(not changed, "whole tree byte-for-byte as before the run, including the absent redirect%s" % ("" if not changed else ": " + ", ".join(changed[:5])))
    drop(d)

    print("\n  T4 · compatible input: identical behaviour to the original builder (%s)\n" % COMPAT)
    a, b = tree(COMPAT, ORIG), tree(COMPAT, NEW)
    ra, rb = run(a, "--check"), run(b, "--check")
    ok(ra == rb and ra[0] == 0, "--check identical: %s" % rb[1].splitlines()[-1][:100])
    for d in (a, b):
        edit(d, "discovery-a-home-for-art.html", "Three people are better off.", "Three people are better off!")
        (d / "discovery-open-your-home-to-art.html").unlink()
    ra, rb = run(a, "--apply"), run(b, "--apply")
    ok(ra == rb and ra[0] == 0, "--apply identical exit and output: %s" % rb[1].splitlines()[-1][:100])
    sa, sb = snap(a), snap(b); sa.pop(B); sb.pop(B)
    ok(sa == sb, "--apply trees byte-identical apart from the builder itself (%d files)" % len(sa))
    ok(subprocess.run(["git", "-C", str(b), "status", "--porcelain", "--", ".", ":!" + B], capture_output=True, text=True).stdout.strip() == "",
       "the regenerated page and redirect equal the committed %s files" % COMPAT)
    drop(a); drop(b)
finally:
    shutil.rmtree(work, ignore_errors=True)
    subprocess.run(["git", "-C", str(ROOT), "worktree", "prune"], capture_output=True)

print("\n  %s · %d check(s) failed\n" % ("PROOF OK" if not fails else "PROOF FAILED", fails))
sys.exit(1 if fails else 0)
