#!/usr/bin/env python3
"""GUARD-CAPABILITY PROOF for the House as Power Station Provider Explorer.

A guard that has never been seen to refuse is a comment. This breaks each
guard once — in a temporary copy of its input — runs the builder, asserts the
break is REFUSED, and restores. A clean CONTROL runs before and after, and
every touched file is hashed before and after the whole run.

Exit 0 = every break caught and every file byte-identical. Exit 1 otherwise.
Run: python3 atlas-tools/prove-power-station-provider-guards.py
"""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = ROOT / "atlas-tools"
UB = T / "build-power-station-provider-universe.py"
PB = T / "build-power-station-provider-explorer.py"
TEXT = T / "power-station-provider-text-v1.json"
SRCS = T / "power-station-provider-sources-v1.json"
SNAP = T / "power-station-provider-atlas-snapshot.json"
PAGE = ROOT / "discovery-house-as-power-station.html"
JS = ROOT / "provider-explorer.js"
FILES = [TEXT, SRCS, SNAP, PAGE, JS, ROOT / "power-station-provider-universe-v1.json"]


def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


BEFORE = {p.name: h(p) for p in FILES}
results = []


def run(builder, *args):
    return subprocess.run([sys.executable, str(builder), "--check", *args], capture_output=True, text=True)


def case(label, path, mutate, builder=UB, args=(), expect_code=2):
    orig = path.read_bytes()
    try:
        path.write_bytes(mutate(orig.decode("utf-8")).encode("utf-8"))
        r = run(builder, *args)
        caught = r.returncode == expect_code and ("REFUSED" in r.stdout or "CHECK FAILED" in r.stdout)
        why = (r.stdout.strip().splitlines() or [""])[-1][:110]
    finally:
        path.write_bytes(orig)
    results.append((label, caught, why))


def jedit(fn):
    def m(s):
        d = json.loads(s)
        fn(d)
        return json.dumps(d, ensure_ascii=False, indent=1)
    return m


def first_how(d, org):
    return d["organisations"][org]["how"][0]


ctl0 = run(UB).returncode == 0 and run(PB).returncode == 0

case("W3 a rate in visitor text", TEXT, jedit(lambda d: first_how(d, "ORG-ESUP-EI").update(t="It pays 19.5c per kWh.")))
case("W3 earnings wording", TEXT, jedit(lambda d: first_how(d, "ORG-ESUP-EI").update(t="Households could earn from export.")))
case("W3 a euro sign", TEXT, jedit(lambda d: first_how(d, "ORG-ESUP-FLOGAS").update(t="Credits worth € to the account.")))
case("W1 ranking vocabulary", TEXT, jedit(lambda d: first_how(d, "ORG-ESUP-BGE").update(t="It is the best supplier for export.")))
case("W2 a web address", TEXT, jedit(lambda d: first_how(d, "ORG-ESUP-ENERGIA").update(t="See energia.ie for details.")))
case("U4 sentence cites another supplier's page", TEXT, jedit(lambda d: first_how(d, "ORG-ESUP-EI").update(s=["SRC-PS-BGE"])))
case("U4 sentence names a quote its source lacks", TEXT, jedit(lambda d: first_how(d, "ORG-ESUP-EI").update(q=["nonexistent"])))
case("U4 sentence with no quote", TEXT, jedit(lambda d: first_how(d, "ORG-ESUP-EI").update(q=[])))
case("U5 supplier in no tab", TEXT, jedit(lambda d: d["tabs"][0]["orgs"].remove("ORG-ESUP-FLOGAS")))
case("U3 partner status present", SNAP, jedit(lambda d: d["organisations"][0].update(partnerStatus="Active Partner")))
case("U1 supplier missing from Atlas read-back", SNAP, jedit(lambda d: d["organisations"].pop()))
case("U2 name differs from the DISC-026 pilot", SNAP, jedit(lambda d: d["organisations"][1].update(name="Electric Ireland Ltd")))
case("REFRESH evidence older than 90 days", SRCS, lambda s: s, args=("--as-of", "2027-01-20"))
case("P1 universe stale vs inputs", TEXT, jedit(lambda d: d["tabs"][0].update(note="Changed note.")), builder=PB)
case("P2 shared script changed (pin)", JS, lambda s: s + "\n", builder=PB)
case("P7/P9 page hand-edited inside the explorer", PAGE,
     lambda s: s.replace("Explore how suppliers pay for export", "Explore the best export suppliers"), builder=PB, expect_code=1)
case("P9 page hand-edited outside the explorer", PAGE,
     lambda s: s.replace("The energy anatomy of your property</h2>", "The energy anatomy of your house</h2>"), builder=PB)
case("P9/P10 computing caveat removed", PAGE,
     lambda s: s.replace("A proposition, not a service an Irish household can buy.", ""), builder=PB)

ctl1 = run(UB).returncode == 0 and run(PB).returncode == 0
AFTER = {p.name: h(p) for p in FILES}

print("=" * 74)
print("  CONTROL before   %s" % ("PASS" if ctl0 else "FAIL"))
for label, caught, why in results:
    print("  %-46s %s  %s" % (label, "CAUGHT" if caught else "*** MISSED ***", why))
print("  CONTROL after    %s" % ("PASS" if ctl1 else "FAIL"))
same = BEFORE == AFTER
print("  every touched file byte-identical after the proof: %s" % ("YES" if same else "NO"))
ok = ctl0 and ctl1 and same and all(c for _, c, _ in results)
print("  %d/%d guards caught their break — %s" % (sum(c for _, c, _ in results), len(results), "PROVEN" if ok else "NOT PROVEN"))
sys.exit(0 if ok else 1)
