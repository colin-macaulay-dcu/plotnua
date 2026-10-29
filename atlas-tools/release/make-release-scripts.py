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
    ("python3 atlas-tools/build-global-header.py --check", "CHECK OK — 2 pages", "global header builder"),
    # 27 since DISC-031 The Natural Swimming Garden (26 Oct 2026); production had 26 after the maker guides.
    # 28 since the DISC-033 The Hidden Flood Barrier release candidate (27 Oct 2026).
    # 29 since DISC-032 The Supper Club at Home (founder Phase 2 authorisation, 27 Oct 2026).
    ("python3 atlas-tools/build-identity-stage1.py --check", "CHECK OK — 29 pages", "identity layer"),
    ("python3 atlas-tools/prove-disc033-page.py", "DISC-033 PAGE · OK", "DISC-033 page proof F1-F10"),
    ("python3 atlas-tools/prove-global-header.py", "GLOBAL HEADER · OK", "global header guard G1-G9"),
    # 33 since the My Plot pill and Direction C (28 Oct 2026): the link to your-plot.html?myplot=1, the read-only
    # script (G6, G10) and the Discovery Library compass.
    ("python3 atlas-tools/prove-global-header-capability.py", "CAPABILITY · OK — 33 planted faults, 0 not caught", "global header capability 33/33"),
    # My Plot and the Eircode journey are separate experiences (founder decision 28 Oct 2026).
    ("python3 atlas-tools/prove-my-plot-view.py --prove", "MY PLOT VIEW · CAPABILITY OK — 13 planted faults, 0 not caught", "My Plot view M1-M8, capability 13/13"),
    ("python3 atlas-tools/prove-identity-stage1.py", "PROOF OK · 27 planted faults, 0 not caught", "identity proof 27/27"),
    ("python3 atlas-tools/prove-premium-discovery-a-home-for-art.py", "PREMIUM-HFA · OK", "Premium content guard"),
    ("python3 atlas-tools/prove-premium-discovery-capability.py", "PROOF OK · 20 planted faults, 0 not caught", "Premium capability 20/20"),
    ("python3 atlas-tools/release/prove-gate-result.py", "GATE-RESULT PROOF · OK", "gate reader proof"),
    ("python3 atlas-tools/prove-premium-locks.py", "PREMIUM LOCKS · OK", "Premium builder locks"),
    ("python3 atlas-tools/prove-premium-garden-room-prices.py", "PREMIUM-GRP · OK", "Garden Room Prices content guard"),
    ("python3 atlas-tools/prove-premium-garden-room-prices-capability.py", "0 not caught", "Garden Room Prices guard capability"),
    ("python3 atlas-tools/build-search-rail.py --check", "nothing written", "search rail unchanged"),
    ("node atlas-tools/prove-landmarks.mjs", "133 passed, 0 failed", "landmarks 133/133"),
    ("python3 atlas-tools/prove-landmarks-capability.py", "24 caught / 0 vacuous / 0 BLIND / 0 MISATTRIBUTED", "landmark capability 24/24"),
    ("node atlas-tools/validate-image-provenance.js", "16 checks, 16 passed, 0 failed", "provenance guard 16/16 (P5c founder original artwork, 29 Oct 2026)"),
    ("node atlas-tools/prove-timberin-containment.mjs", "real tree: contained · 25 mutations, 25 proved, 0 not proved", "TimberIN containment 25/25"),
    ("node atlas-tools/prove-cluster2-garden-retreat.mjs", "16 checks, 16 passed, 0 failed", "Garden Retreat claim guards 16/16"),
    ("env -u PN_PREVIEW_OFFERS python3 atlas-tools/build-maker-explorer.py --check", "CHECK OK — G1-G14", "maker directory G1-G14"),
    ("python3 atlas-tools/build-h6-homepage.py --check", "H6 COMPONENT CHECK OK", "H6 garden component (replaced the Possibility Reveal, 26 Oct 2026)"),
    ("node atlas-tools/prove-price-presentation-unchanged.mjs", "710 price comparisons", "price presentation 710/710 unchanged"),
    ("node atlas-tools/prove-discovery-library-images.mjs", "GOVERNED", "Discovery Library images"),
    ("python3 atlas-tools/prove-search-page-runtime.py", "16 passed, 0 failed", "search runtime 16/16"),
    # SEO phase 1 builder retired as a release check (26 Oct 2026): since the garden-room landing
    # release (bac3ab8) removed its In Brief block, the historical builder refuses on production main
    # itself (recorded in governance/GARDEN-ROOMS-IRELAND-SEARCH-FOCUS-2026-10-26.md). Page-level SEO
    # is proved by each release's own --check (for DISC-031: atlas-tools/prove-disc031-page.py).
    ("python3 .github/scripts/check_atlas_figures.py", "index.html agrees with atlas-stats.json", "Atlas figures"),
    ("node atlas-tools/validate-journey-contract.js", "HELD", "journey contract"),
    # PRIVACY NOTICE VERIFICATION (repair approved 27 Oct 2026). Until then none of the
    # privacy checks ran at release time, so they drifted unnoticed from 20 Oct 2026.
    # privacy_page_layers.py sets aside only site-shell changes (each made and guarded by
    # its own builder) and the separately tracked WhatsApp block; every governed V3-V6
    # sentence is still verified byte for byte.
    ("python3 atlas-tools/build-privacy-v4.py --check", "V4 PUBLISHED", "privacy V4 governed text"),
    ("python3 atlas-tools/build-privacy-v5.py --check", "V5 PUBLISHED", "privacy V5 governed text"),
    ("python3 atlas-tools/build-privacy-v6.py --check", "privacy V6 present", "privacy V6 present"),
    ("python3 atlas-tools/prove-privacy-v4.py", "20/20 breaks caught · rehearsal 9/9 — PROVEN", "privacy V4 proof 20/20, rehearsal 9/9"),
    ("python3 atlas-tools/prove-privacy-v5.py", "24/24 breaks caught · rehearsal 16/16 — PROVEN", "privacy V5 proof 24/24, rehearsal 16/16"),
    ("python3 atlas-tools/prove-privacy-v6.py", "10 passed, 0 failed", "privacy V6 proof 10/10"),
    ("python3 atlas-tools/prove-privacy-page-layers.py", "16 passed, 0 failed", "privacy page layers 16/16"),
    # Privacy V7 (prepared 28 Oct 2026): exact, reversible replacements over V6; the proof works before and after application.
    ("python3 atlas-tools/prove-privacy-v7.py", "0 failed", "privacy V7 proof"),
    ("python3 atlas-tools/prove-legal-information.py", "LEGAL INFORMATION · OK", "legal information G1-G6"),
    # PlotArt limited launch (27 Oct 2026): the published pages are exactly the verified
    # build (manifest), noindex, follow, and applications are not open. Changing the state is a new release.
    # Virtual Gallery (28 Oct 2026): a fourth page, plotart/gallery/, published empty (guard L11).
    ("python3 atlas-tools/prove-plotart-launch.py . --switches atlas-tools/release/plotart-launch-switches.json --manifest atlas-tools/release/plotart-launch-manifest.json",
     "PLOTART LAUNCH · OK — L1-L13 on 4 pages · applications open", "PlotArt launch L1-L13: Virtual Gallery empty; three-pill navigation, no banner; Founding 25 and Living Gallery separate (applications open, founder activation 28 Oct 2026)"),
    # PlotArt in the PlotNua navigation and the A Home for Art links (proposed 27 Oct 2026)
    # 31 header pages since DISC-032 The Supper Club at Home joined the header registry (27 Oct 2026; 30 after DISC-033).
    ("python3 atlas-tools/prove-plotart-integration.py", "PLOTART INTEGRATION · OK — N1-N4 · 31 header pages", "PlotArt navigation and A Home for Art links N1-N4"),
    ("python3 atlas-tools/prove-privacy-whatsapp.py", "PRIVACY WHATSAPP · OK", "privacy WhatsApp block exact (status printed)"),
    ("python3 atlas-tools/build-art-space-register.py --check", "CHECK OK — R1-R14 pass", "Art Space Register R1-R14"),
    ("python3 atlas-tools/build-artist-register.py --check", "CHECK OK — A1-A13 pass", "Artist Register A1-A13"),
    ("python3 atlas-tools/prove-g6-owner-register.py", "43 passed, 0 failed", "Garden Owner Register privacy proof 43/43"),
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
