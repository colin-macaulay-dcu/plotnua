#!/usr/bin/env python3
"""VERIFY THE POSSIBILITY REVEAL LOCK CHAIN AGAINST THIS REPOSITORY'S RECORD.

H2, 20 Oct 2026. The locked Reveal images are far too large to live in the
site repository, and nothing in the published tree may carry them. So the
lock repository (possibility-reveal-locks, bundles in the LOCKED folders on
the founder's Mac) holds the pixels, and image-provenance-records.json holds
the AUTHORITATIVE record of which locks are active:
possibility_reveal_lock_chain. The provenance guard (P13) checks that record's
internal consistency on every CI run. This script is the bridge, run OFFLINE
whenever a lock changes or before any Reveal image is built:

  1. the repository's possibility_reveal_lock_chain is identical, field for
     field, to ACTIVE-LOCKS.json in the lock repository (active_master, chain,
     active_layers, superseded) -- so neither can drift silently;
  2. the lock repository's own verifier (verify_locks.py) passes: every hash,
     a pixel-identical rebuild L5 master -> + L3 v2.1c -> + L6, and refusal of
     the superseded L3 v2;
  3. the lock repository is at the commit the record names (when it has .git).

Usage:
  python3 atlas-tools/verify-possibility-reveal-locks.py --locks PATH [--check-image IMG ...]
Exit 0 = the chain is authoritative and reproduces. 1 = it does not.
2 = the lock repository could not be found or read.
"""
import json, pathlib, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
args = sys.argv[1:]
if "--locks" not in args:
    print(__doc__); sys.exit(2)
LOCKS = pathlib.Path(args[args.index("--locks") + 1]).expanduser().resolve()
extra = args[args.index("--check-image"):] if "--check-image" in args else []

def out(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    return ok

reg = json.loads((REPO / "image-provenance-records.json").read_text(encoding="utf-8"))
mine = reg.get("possibility_reveal_lock_chain")
if not mine:
    print("INSTRUMENT UNAVAILABLE: the register carries no possibility_reveal_lock_chain"); sys.exit(2)
active = LOCKS / "ACTIVE-LOCKS.json"
verifier = LOCKS / "verify_locks.py"
if not active.exists() or not verifier.exists():
    print("INSTRUMENT UNAVAILABLE: %s is not a lock repository (no ACTIVE-LOCKS.json / verify_locks.py)" % LOCKS)
    sys.exit(2)
theirs = json.loads(active.read_text(encoding="utf-8"))

good = True
for k in ("active_master", "chain", "active_layers", "superseded"):
    good &= out(mine.get(k) == theirs.get(k), "repository record matches ACTIVE-LOCKS.json: " + k)

if (LOCKS / ".git").exists():
    head = subprocess.run(["git", "-C", str(LOCKS), "rev-parse", "--short=7", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    want = (mine.get("lock_commits") or {}).get("L6")
    good &= out(bool(want) and head.startswith(want), "lock repository HEAD %s is the recorded L6 lock %s" % (head, want))

print("-- the lock repository's verifier --")
r = subprocess.run([sys.executable, str(verifier)] + extra, cwd=str(LOCKS), capture_output=True, text=True)
print(r.stdout.rstrip())
if r.stderr.strip():
    print(r.stderr.rstrip())
good &= out(r.returncode == 0, "verify_locks.py: pixel-identical rebuild and no superseded L3")

print("\nAUTHORITATIVE LOCK CHAIN OK" if good else "\nLOCK CHAIN NOT AUTHORITATIVE")
sys.exit(0 if good else 1)
