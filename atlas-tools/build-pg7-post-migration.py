#!/usr/bin/env python3
"""PlotNua — build-pg7-post-migration.py

A BOUNDED BUILDER. Two changes, one root cause: the VAT-basis migration
finished when the founder regenerated the universe, and two things still
assume it had not.

THE FAILURE, 11 October 2026.

    prove-supplier-publication-gate-capability.mjs
    CONTROL: 14 passed, 0 failed
    14 mutations: 13 caught, 1 BLIND
    BLIND C-PG7  NOT CAUGHT (owner PG7)
      "one priced product gains a basis and the rest do not"

MEASURED AGAINST THE FOUNDER'S REGENERATED ARTEFACT (read-only):

    priced products                 125
    of those WITHOUT basis            0
    PG7 verdict, unmutated         ok   125 priced products
    C-PG7 applied as written       ->  artefact changed at all? FALSE
    PG7 verdict, mutated           ok   125 priced products

C-PG7 SETS `basis = 'INCLUDES_VAT'` on the first priced product. Before the
regeneration no priced product had a basis, so that broke the uniformity the
migration branch excused and PG7 reported it — which is what the mutation's
name describes. After the regeneration every priced product ALREADY has
exactly that value, so the mutation is a literal no-op. A mutation that
changes nothing cannot be caught by anything. That is the BLIND, and it is a
defect in the MUTATION, not in the safeguard.

THE SAFEGUARD'S MAIN PATH IS SOUND. Measured on the same artefact:

    delete ONE basis   ->  bad   1 of 125 missing        correctly caught
    delete ALL bases   ->  ok    NOT YET REGENERATED     <-- the hole

So there is a second, worse problem, and it is the reason the old mutation had
to be written sideways in the first place. PG7 carries a migration-era branch
that PASSES when EVERY priced product lacks a basis. That branch was honest
while the migration was pending. Now that it has completed, it excuses exactly
the condition PG7 exists to forbid: a generator regression that stripped VAT
basis from all 125 priced products would be reported as "ok, not yet
regenerated".

THE FIX, both halves of one root cause:

  1. RETIRE the migration branch. Uniform absence now FAILS. This STRENGTHENS
     PG7 — it removes an excuse, it does not add one. With no special case
     left, "one missing" and "all missing" are the same code path, so the
     single-product mutation below proves both.

  2. RE-AIM C-PG7 at the post-migration defect: delete one basis. Same intent
     as the original mutation — prove PG7 detects an amount with no basis —
     with the mechanism the current world requires. This follows the file's
     own precedent; C-PG6 and C-PG11 carry "RE-AIMED 11 October 2026" notes
     for the same reason.

WHAT THIS IS NOT. The mutation is not being altered to manufacture a pass. The
old one asserts nothing on any artefact that has been regenerated, and the new
one fails against a PG7 with the migration branch still in place — which is
the test that the fix is real, and is run as part of the proof.

IT DOES NOT TOUCH additional-home-universe-v1.json. The founder's regenerated
artefact is read, never written. Price basis, configuration and publication
safeguards are unchanged.

IDEMPOTENT. Run twice and the second run reports nothing to do.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / "atlas-tools" / "prove-supplier-publication-gate.mjs"
PROOF = ROOT / "atlas-tools" / "prove-supplier-publication-gate-capability.mjs"
ARTEFACT = ROOT / "additional-home-universe-v1.json"

# ── 1 · the guard: the completed migration stops being an excuse ────────────
G_OLD = '''  const missing = priced.filter(p => !(p.price || {}).basis);
  // The universe has not been regenerated yet, so today every priced product
  // legitimately lacks `basis`. The guard states which world it is in rather
  // than passing silently in either.
  if (!priced.length) {
    bad('PG7 VAT basis present wherever an amount exists', 'no priced product found — vacuous');
  } else if (missing.length === priced.length) {
    ok('PG7 VAT basis — NOT YET REGENERATED, all ' + priced.length +
       ' priced products predate the field; re-run after regeneration',
       'pre-migration state, recorded not hidden');
  } else if (missing.length) {'''

G_NEW = '''  const missing = priced.filter(p => !(p.price || {}).basis);
  // THE MIGRATION BRANCH IS GONE, RETIRED 11 October 2026.
  //
  // This guard used to PASS when EVERY priced product lacked `basis`, on the
  // grounds that the universe had not been regenerated yet and a uniform
  // absence was the honest pre-migration state. That was true while it was
  // true. The founder regenerated on 11 October and all 125 priced products
  // now carry a basis, so the branch became unreachable in normal operation
  // and dangerous in abnormal operation: a generator regression that stripped
  // the field from every priced product would have been reported as "ok, not
  // yet regenerated" — the guard excusing precisely what it exists to forbid.
  //
  // Uniform absence now fails like any other absence. With no special case
  // left, one missing basis and all missing bases are the same code path,
  // which is why C-PG7 can prove both by removing one.
  if (!priced.length) {
    bad('PG7 VAT basis present wherever an amount exists', 'no priced product found — vacuous');
  } else if (missing.length) {'''

# ── 2 · the mutation: aim it at the defect that exists now ─────────────────
M_OLD = '''  ['C-PG7', 'PG7', 'one priced product gains a basis and the rest do not',
    t => t.universe(d => {
      const p = d.products.find(x => (x.price || {}).amount != null);
      p.price.basis = 'INCLUDES_VAT';
    })],'''

M_NEW = '''  /* RE-AIMED 11 October 2026, and the reason is the whole point of running
     this proof. The old mutation SET basis = 'INCLUDES_VAT' on the first
     priced product. Before the regeneration no priced product had a basis, so
     that broke the uniformity PG7's migration branch excused and PG7 reported
     it. After the regeneration every priced product already holds exactly
     that value, so the mutation changed nothing at all — measured: the
     artefact was byte-identical afterwards — and the proof correctly called
     it BLIND. A mutation that cannot alter the artefact cannot test anything.

     Aimed instead at the condition PG7's own headline asserts: an amount with
     no basis. One product, not all of them, because one is the sensitive case
     — a guard that only noticed a universal absence would pass this. */
  ['C-PG7', 'PG7', 'one priced product loses its VAT basis',
    t => t.universe(d => {
      const p = d.products.find(x => (x.price || {}).amount != null);
      delete p.price.basis;
    })],'''


def die(msg: str) -> None:
    print(f"REFUSING: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    for p in (GUARD, PROOF):
        if not p.exists():
            die(f"{p} does not exist.")
    gsrc, psrc = GUARD.read_text(encoding="utf-8"), PROOF.read_text(encoding="utf-8")
    gbak = GUARD.with_suffix(GUARD.suffix + ".bak-pg7")
    pbak = PROOF.with_suffix(PROOF.suffix + ".bak-pg7")

    # THE ARTEFACT IS READ-ONLY HERE. Recorded before and after so the claim
    # is measured rather than asserted.
    before = hashlib.sha256(ARTEFACT.read_bytes()).hexdigest() if ARTEFACT.exists() else None

    if args.revert:
        if not (gbak.exists() and pbak.exists()):
            die("a sidecar is missing; refusing a partial revert.")
        shutil.copyfile(gbak, GUARD)
        shutil.copyfile(pbak, PROOF)
        print("reverted both files.")
        return

    if "RETIRED 11 October 2026" in gsrc:
        print("already applied — nothing to do.")
        return

    for label, src, anchor in (("the PG7 branch", gsrc, G_OLD),
                               ("the C-PG7 mutation", psrc, M_OLD)):
        n = src.count(anchor)
        if n != 1:
            die(f"the {label} anchor appears {n} times, expected exactly 1. "
                "The source has changed; re-read it before editing.")

    gout = gsrc.replace(G_OLD, G_NEW)
    pout = psrc.replace(M_OLD, M_NEW)

    # PG7 MUST STILL REFUSE, AND THE OTHER GUARDS MUST BE UNTOUCHED. The
    # headline assertion, the vacuous arm and the pass arm all stay; only the
    # migration excuse goes.
    if gout.count("bad('PG7") != 2:
        die("PG7 no longer has exactly two refusal arms. Refusing.")
    if "else if (missing.length === priced.length)" in gout:
        die("the migration branch is still present. Refusing.")
    for token in ("PG1", "PG2", "PG3", "PG4", "PG5", "PG6",
                  "PG8", "PG9", "PG10", "PG11", "PG12"):
        if gout.count(f"'{token} ") != gsrc.count(f"'{token} "):
            die(f"{token} changed. Refusing.")
    # Every mutation except C-PG7 must be byte-identical.
    for token in ("C-PG1", "C-PG2", "C-PG3", "C-PG4", "C-PG5", "C-PG6",
                  "C-PG8", "C-PG9", "C-PG10", "C-PG11", "C-PG12"):
        if pout.count(f"['{token}'") != psrc.count(f"['{token}'"):
            die(f"{token} changed. Refusing.")
    if pout.count("['C-PG") != psrc.count("['C-PG"):
        die("the mutation count changed. Refusing.")

    for name, path, out in (("the guard", GUARD, gout), ("the proof", PROOF, pout)):
        if args.check:
            continue
        if not path.with_suffix(path.suffix + ".bak-pg7").exists():
            shutil.copyfile(path, path.with_suffix(path.suffix + ".bak-pg7"))
        path.write_text(out, encoding="utf-8")

    if args.check:
        print(f"--check: guard {len(gout.splitlines()) - len(gsrc.splitlines()):+d} lines, "
              f"proof {len(pout.splitlines()) - len(psrc.splitlines()):+d} lines, "
              f"{pout.count(chr(91) + chr(39) + 'C-PG')} mutations unchanged in number.")
        return

    for path in (GUARD, PROOF):
        r = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if r.returncode != 0:
            die(f"{path.name} does not parse: {r.stderr.strip()}")

    if gout.replace(G_NEW, G_OLD) != gsrc or pout.replace(M_NEW, M_OLD) != psrc:
        die("the edit is not reversible byte for byte.")

    after = hashlib.sha256(ARTEFACT.read_bytes()).hexdigest() if ARTEFACT.exists() else None
    if before != after:
        die("additional-home-universe-v1.json CHANGED. That must never happen "
            "here. Investigate before doing anything else.")

    print("applied.")
    print(f"  {GUARD.name:52} sha256 {hashlib.sha256(GUARD.read_bytes()).hexdigest()[:16]}")
    print(f"  {PROOF.name:52} sha256 {hashlib.sha256(PROOF.read_bytes()).hexdigest()[:16]}")
    print(f"  artefact untouched, sha256 still {(after or '')[:16]}")


if __name__ == "__main__":
    main()
