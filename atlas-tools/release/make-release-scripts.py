#!/usr/bin/env python3
"""PLOTNUA RELEASE · build a release folder's guarded scripts and bundle.

  python3 atlas-tools/release/make-release-scripts.py --name <slug> --title "<what it is>" \
      --base <production sha> --rel <release sha> --out <folder> [--check "<cmd>|<expected text>|<label>"]...

Writes into --out:
  plotnua-<slug>.bundle      the release commits (base..rel) on branch release/<slug>
  deploy-<slug>.sh           --stage / --status / --release, from deploy-template.sh
  rollback-<slug>.sh         revert-commit rollback, from rollback-template.sh

Every release gets the standard production checks below; --check adds release-specific
ones. Each check runs in a clean checkout of the release commit and must print its
expected text. The scripts read the Image Rights Gate for the exact release commit
(gate-result.py); they never start it and never deploy without the founder's typed
confirmation. See RELEASE-PROCESS.md.
"""
import datetime, hashlib, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

STANDARD = [
    ("python3 atlas-tools/build-global-header.py --check", "CHECK OK — 7 pages", "global header builder"),
    ("python3 atlas-tools/build-identity-stage1.py --check", "CHECK OK — 18 pages", "identity layer"),
    ("python3 atlas-tools/prove-global-header.py", "GLOBAL HEADER · OK", "global header guard G1-G9"),
    ("python3 atlas-tools/prove-global-header-capability.py", "CAPABILITY · OK — 25 planted faults, 0 not caught", "global header capability 25/25"),
    ("python3 atlas-tools/prove-identity-stage1.py", "PROOF OK · 27 planted faults, 0 not caught", "identity proof 27/27"),
    ("python3 atlas-tools/prove-premium-discovery-a-home-for-art.py", "PREMIUM-HFA · OK", "Premium content guard"),
    ("python3 atlas-tools/prove-premium-discovery-capability.py", "PROOF OK · 20 planted faults, 0 not caught", "Premium capability 20/20"),
    ("python3 atlas-tools/release/prove-gate-result.py", "GATE-RESULT PROOF · OK", "gate reader proof"),
    ("python3 atlas-tools/build-search-rail.py --check", "nothing written", "search rail unchanged"),
    ("node atlas-tools/prove-landmarks.mjs", "133 passed, 0 failed", "landmarks 133/133"),
    ("python3 atlas-tools/prove-landmarks-capability.py", "24 caught / 0 vacuous / 0 BLIND / 0 MISATTRIBUTED", "landmark capability 24/24"),
    ("node atlas-tools/validate-image-provenance.js", "14 checks, 14 passed, 0 failed", "provenance guard 14/14"),
    ("node atlas-tools/prove-timberin-containment.mjs", "real tree: contained · 25 mutations, 25 proved, 0 not proved", "TimberIN containment 25/25"),
    ("node atlas-tools/prove-cluster2-garden-retreat.mjs", "16 checks, 16 passed, 0 failed", "Garden Retreat claim guards 16/16"),
    ("env -u PN_PREVIEW_OFFERS python3 atlas-tools/build-maker-explorer.py --check", "CHECK OK — G1-G14", "maker directory G1-G14"),
    ("python3 atlas-tools/build-possibility-reveal-component.py --check", "CHECK OK", "Reveal component"),
    ("python3 atlas-tools/build-possibility-reveal-layers.py --check", "CHECK OK", "Reveal tiles"),
    ("node atlas-tools/prove-price-presentation-unchanged.mjs", "710 price comparisons", "price presentation 710/710 unchanged"),
    ("node atlas-tools/prove-discovery-library-images.mjs", "GOVERNED", "Discovery Library images"),
    ("python3 atlas-tools/prove-search-page-runtime.py", "16 passed, 0 failed", "search runtime 16/16"),
    ("python3 atlas-tools/build-seo-phase1.py --check", "CHECK OK", "SEO phase 1"),
    ("python3 .github/scripts/check_atlas_figures.py", "index.html agrees with atlas-stats.json", "Atlas figures"),
    ("node atlas-tools/validate-journey-contract.js", "HELD", "journey contract"),
]


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def arg(n):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None


def sh_quote(s):
    return "'" + s.replace("'", "'\\''") + "'"


def main():
    name, title, base, rel, out = (arg(x) for x in ("--name", "--title", "--base", "--rel", "--out"))
    if not all((name, title, base, rel, out)) or not re.fullmatch(r"[a-z0-9-]+", name):
        sys.exit(__doc__)
    base, rel = git("rev-parse", base), git("rev-parse", rel)
    extra = [tuple(c.split("|", 2)) for i, c in enumerate(sys.argv) if sys.argv[i - 1] == "--check"]
    if subprocess.run(["git", "merge-base", "--is-ancestor", base, rel], cwd=ROOT).returncode:
        sys.exit("REFUSED: %s is not built on %s" % (rel[:7], base[:7]))
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    br = "release/" + name
    git("branch", "-f", br, rel)
    bundle = out / ("plotnua-%s.bundle" % name)
    git("bundle", "create", str(bundle), br, "^" + base)
    checks = []
    for cmd, expect, label in STANDARD + extra:
        checks.append('  %s 2>&1 | grep -qF -- %s && echo %s &&' % (cmd, sh_quote(expect), sh_quote("OK   " + label)))
    sub = {
        "@@TITLE@@": title, "@@DATE@@": datetime.date.today().isoformat(), "@@SCRIPT@@": "deploy-%s.sh" % name,
        "@@BUNDLE@@": bundle.name, "@@BUNDLE_SHA@@": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "@@BRANCH@@": br, "@@MAIN@@": base, "@@MAIN_SHORT@@": base[:7], "@@REL@@": rel,
        "@@TREE@@": git("rev-parse", rel + "^{tree}"), "@@N@@": git("rev-list", "--count", "%s..%s" % (base, rel)),
        "@@WANT@@": " ".join(sorted(git("diff", "--name-only", base, rel).split("\n"))) + " ",
        "@@CHECKS@@": "\n".join(checks),
    }
    for tpl, dst in (("deploy-template.sh", "deploy-%s.sh" % name), ("rollback-template.sh", "rollback-%s.sh" % name)):
        s = (HERE / tpl).read_text(encoding="utf-8")
        for k, v in sub.items():
            s = s.replace(k, v)
        if "@@" in s:
            sys.exit("REFUSED: unfilled placeholder in %s" % tpl)
        (out / dst).write_text(s, encoding="utf-8"); (out / dst).chmod(0o755)
    print("RELEASE SCRIPTS · %s · %s on %s · %s commit(s) · %d checks · bundle %s"
          % (br, rel[:7], base[:7], sub["@@N@@"], len(checks), sub["@@BUNDLE_SHA@@"][:12]))


if __name__ == "__main__":
    main()
