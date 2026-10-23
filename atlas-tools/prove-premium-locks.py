#!/usr/bin/env python3
"""PLOTNUA · proof that no legacy layout builder can overwrite a Premium page.

For every locked builder, the page it rewrites is added to the Premium registry for
one run (PN_PREMIUM_EXTRA), and the builder is started in every mode it has. Each run
must exit 2 with "REFUSED: PREMIUM", and every page, data file and evidence file must
be byte-identical afterwards. Then, with nothing added, the registry must agree with
the identity builder's Premium layer.

Usage: python3 atlas-tools/prove-premium-locks.py
"""
import hashlib, os, subprocess, sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import premium_pages  # noqa: E402

LOCKED = {
    "build-cluster1-garden-authority.py": "discovery-living-in-the-garden.html",
    "build-discovery-makers-section.py": "discovery-living-in-the-garden.html",
    "build-triq-cube-public.py": "triq-cube.html",
    "build-garden-retreat-restructure.py": "discovery-garden-retreat.html",
    "build-cluster2-garden-retreat.py": "discovery-garden-retreat.html",
}
MODES = ([], ["--apply"])          # writing modes (a builder's default may write): must refuse
READ_ONLY = (["--check"],)          # reads and reports only: allowed, and must write nothing


def tree():
    files = sorted(list(ROOT.glob("*.html")) + list(ROOT.glob("*.json")) + list(ROOT.glob("sitemap.xml"))
                   + list((ROOT / "atlas-tools").glob("*.json")))
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}


def main():
    bad = 0
    before = tree()
    for b, page in LOCKED.items():
        src = (TOOLS / b).read_text(encoding="utf-8")
        if "premium_pages" not in src or "refuse_if_premium" not in src:
            print("MISSING  %s carries no Premium lock" % b); bad += 1; continue
        for m in MODES:
            r = subprocess.run([sys.executable, str(TOOLS / b)] + m, cwd=ROOT, capture_output=True, text=True,
                               env={**os.environ, "PN_PREMIUM_EXTRA": page}, timeout=300)
            out = (r.stdout + r.stderr).strip()
            ok = r.returncode == 2 and "REFUSED: PREMIUM" in out
            bad += not ok
            print("%s  %-38s %-10s %s" % ("refused " if ok else "NOT REFUSED", b, " ".join(m) or "(default)",
                                          "" if ok else out[-160:]))
        for m in READ_ONLY:   # allowed to run its content guards; the tree check below proves it wrote nothing
            r = subprocess.run([sys.executable, str(TOOLS / b)] + m, cwd=ROOT, capture_output=True, text=True,
                               env={**os.environ, "PN_PREMIUM_EXTRA": page}, timeout=300)
            out = (r.stdout + r.stderr).strip()
            ok = "REFUSED: PREMIUM" not in out
            bad += not ok
            print("%s  %-38s %-10s %s" % ("read-only" if ok else "REFUSED --check", b, " ".join(m), ""))
    after = tree()
    changed = sorted(k for k in before if before[k] != after.get(k))
    if changed:
        print("WROTE  files changed during the proof: %s" % changed[:6]); bad += 1
    # registry = the identity builder's Premium layer
    ib = (TOOLS / "build-identity-stage1.py").read_text(encoding="utf-8")
    if "premium_pages.PREMIUM_PAGES" not in ib:
        print("SPLIT  build-identity-stage1.py does not take its Premium set from the registry"); bad += 1
    if os.environ.get("PN_PREMIUM_EXTRA"):
        print("ENV  PN_PREMIUM_EXTRA is set in the environment; unset it"); bad += 1
    if bad:
        print("PREMIUM LOCKS · FAILED — %d problem(s)" % bad); return 2
    print("PREMIUM LOCKS · OK — %d legacy layout builders x %d modes refuse before writing on a Premium page; "
          "no file changed; registry (%d pages) drives the identity layer"
          % (len(LOCKED), len(MODES), len(premium_pages.PREMIUM_PAGES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
