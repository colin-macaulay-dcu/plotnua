#!/bin/bash
# Builds the two launch patches from the closed Grower Register commits.
#   make-grower-launch-kit.sh "<founder V6 approval text>" "<founder launch approval text>" OUT_DIR
# 1-release.patch    = everything since 84453f1, plus Privacy V6 applied (approved)
# 2-activation.patch = Grower panel public + Discovery two routes + grower writes on V6
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; V6A="$1"; OPENA="$2"; OUT="$3"
WT="$(mktemp -d)/kit"; git -C "$ROOT" worktree add -q --detach "$WT" HEAD
trap 'git -C "$ROOT" worktree remove --force "$WT"' EXIT
cd "$WT"
python3 - "$V6A" <<'PY'
import sys,re; p='atlas-tools/build-privacy-v6.py'; s=open(p).read()
s=re.sub(r'^APPROVAL = None.*$', 'APPROVAL = %r' % sys.argv[1], s, count=1, flags=re.M); open(p,'w').write(s)
PY
python3 atlas-tools/build-privacy-v6.py && python3 atlas-tools/build-privacy-v6.py --check
python3 atlas-tools/build-grower-register.py --check
git add -A && git -c user.name="Colin MacAulay" -c user.email="kolin.macaulay@gmail.com" commit -qm "Privacy V6: Grower Register added to Section 7 (founder-approved)

$V6A"
python3 - "$OPENA" "$V6A" <<'PY'
import sys,re; p='atlas-tools/build-grower-register.py'; s=open(p).read()
s=s.replace('"privacy_v6_wording_approved": None', '"privacy_v6_wording_approved": %r' % sys.argv[2])
s=s.replace('"launch_approved": None', '"launch_approved": %r' % sys.argv[1])
s=re.sub(r'^GROWER_PUBLIC = False', 'GROWER_PUBLIC = True', s, count=1, flags=re.M); open(p,'w').write(s)
p='worker/garden-register/wrangler.toml'; s=open(p).read()
s=s.replace('GROWER_WRITES_ENABLED  = "false"','GROWER_WRITES_ENABLED  = "true"').replace('GROWER_PRIVACY_VERSION = ""','GROWER_PRIVACY_VERSION = "2026-10-PHASE2-V6"'); open(p,'w').write(s)
PY
python3 atlas-tools/build-grower-register.py && python3 atlas-tools/build-grower-register.py --check
git add -A && git -c user.name="Colin MacAulay" -c user.email="kolin.macaulay@gmail.com" commit -qm "Grower Register: open, with two routes on The Borrowed Garden

$OPENA"
mkdir -p "$OUT"
git format-patch -q --stdout 84453f1..HEAD~1 > "$OUT/1-release.patch"
git format-patch -q --stdout HEAD~1..HEAD > "$OUT/2-activation.patch"
echo "kit: $(grep -c '^From [0-9a-f]\{40\}' "$OUT/1-release.patch") release commits + 1 activation commit -> $OUT"
