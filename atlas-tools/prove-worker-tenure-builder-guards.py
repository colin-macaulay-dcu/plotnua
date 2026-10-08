#!/usr/bin/env python3
"""
GUARD-CAPABILITY PROOF · build-worker-tenure-alignment.py
===============================================================================
A guard that has never been seen to fail is not a proven guard. This driver
builds a disposable copy of the repository layout, breaks ONE thing per case,
runs the builder in --check mode against the copy, and asserts the builder
REFUSES with the expected guard.

Two kinds of sabotage, both legitimate and each labelled in the output:

  INPUT    the Worker source handed to the builder is corrupted. Proves the
           guard catches a bad target.
  BUILDER  the builder's own OLD/NEW constants or patch step are corrupted.
           Proves the guard catches a builder that would do the wrong thing —
           which is the failure mode that actually ships bad code.

Nothing here touches the real Worker, the real page, Airtable or any switch.

    python3 prove-worker-tenure-builder-guards.py
"""

import hashlib
import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILDER = ROOT / "atlas-tools" / "build-worker-tenure-alignment.py"
WORKER = ROOT / "worker" / "garden-register" / "src" / "index.js"

# THE PRE-CORRECTION SOURCE, read from git, not from disk. Once the builder
# has run, the file on disk already contains `tenure === 'rent'`, so guard 3
# (not re-runnable) fires for every case and the proof becomes unrunnable —
# which would make it a one-shot script rather than reproducible evidence.
# Reading the committed base keeps this proof runnable for good.
_BASE_REF = "057bb81:worker/garden-register/src/index.js"
try:
    SRC = subprocess.run(["git", "show", _BASE_REF], cwd=ROOT, check=True,
                         capture_output=True, text=True).stdout
except Exception as e:                                    # noqa: BLE001
    raise SystemExit("cannot read the pre-correction Worker from git (%s): %s"
                     % (_BASE_REF, e))
assert hashlib.sha256(SRC.encode("utf-8")).hexdigest() == \
    "4c5a47831ec85178f083f4535f1bbb732ee9c4542af43f28ef8b88105897a3ba", \
    "the committed base Worker is not 4c5a4783..."
BUILDER_SRC = BUILDER.read_text(encoding="utf-8")

PRESERVED = "  if (!tenure) return REFUSED(cors, 'inherited_tenure');"
NEW_RE = re.compile(r'(?s)^NEW = """.*?"""', re.M)
OLD_RE = re.compile(r'(?s)^OLD = """(.*?)"""', re.M)

# The anchor the builder actually looks for, lifted from the builder itself
# rather than retyped here. A retyped copy was the first version of this file
# and it silently failed to match, which made C2 read as blind when the guard
# was fine: the prover was duplicating a FRAGMENT of the anchor, not the anchor.
# Imported, not retyped and not regex-unescaped. The first version of this
# file retyped the anchor and silently failed to match, which made C2 read as
# blind when the guard was fine; the second tried unicode_escape and mangled
# the em dash. Importing the builder is the only way to get the exact object.
_spec = importlib.util.spec_from_file_location("_b", BUILDER)
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)
ANCHOR = _b.OLD
assert ANCHOR in SRC, "the builder's OLD anchor is not present in the Worker"

passed = failed = 0


# The comment half of the builder's NEW constant, preserved verbatim by every
# sabotage below. An earlier version of new_block() replaced the WHOLE constant,
# which stripped the landlord denial and made guard 16 fire for every case —
# masking G11 and G15 and reporting them blind. A sabotage must break exactly
# one thing.
_NEW_COMMENT = _b.NEW.split("  const permission_confirmed")[0]


def new_block(body):
    """Replace only the CODE half of the builder's NEW constant."""
    return 'NEW = """' + _NEW_COMMENT + body + '"""'


def run_case(label, kind, guard, worker_mut=None, builder_mut=None,
             refresh_base=True):
    """Apply one sabotage, run the builder, require a refusal naming `guard`."""
    global passed, failed
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="guardproof-"))
    try:
        (tmp / "atlas-tools").mkdir()
        (tmp / "worker" / "garden-register" / "src").mkdir(parents=True)

        src = worker_mut(SRC) if worker_mut else SRC
        (tmp / "worker" / "garden-register" / "src" / "index.js").write_text(
            src, encoding="utf-8")

        b = builder_mut(BUILDER_SRC) if builder_mut else BUILDER_SRC
        if refresh_base:
            # So the case under test is the one that fires, not the base-hash
            # guard. The base-hash guard has its own case (C1).
            b = re.sub(r'BASE_SHA = "[0-9a-f]{64}"',
                       'BASE_SHA = "%s"' % hashlib.sha256(
                           src.encode("utf-8")).hexdigest(), b)
        (tmp / "atlas-tools" / "b.py").write_text(b, encoding="utf-8")

        r = subprocess.run([sys.executable, str(tmp / "atlas-tools" / "b.py"),
                            "--check"], capture_output=True, text=True)
        out = r.stdout + r.stderr
        refused = r.returncode == 1 and "REFUSED:" in out
        named = guard in out
        ok = refused and named
        if ok:
            passed += 1
            why = out.split("REFUSED:")[1].strip().split("\n")[0]
            print("  [CAPABLE ] %-44s %-8s %s" % (label, kind, why[:72]))
        else:
            failed += 1
            print("  [*** BLIND] %-44s %-8s rc=%s" % (label, kind, r.returncode))
            print("              expected a refusal naming %r" % guard)
            print("              got: %s" % out.strip().replace("\n", " | ")[:300])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


print("\n  GUARD-CAPABILITY PROOF · build-worker-tenure-alignment.py\n")

# ---------------------------------------------------------------- INPUT cases
run_case("C1  G1 base hash: target is not the frozen Worker", "INPUT",
         "not the frozen deployed Worker",
         worker_mut=lambda s: s.replace("const V = {", "const V = { /* x */",
                                        1),
         refresh_base=False)

run_case("C2  G2 anchor: the tenure block occurs twice", "INPUT",
         "expected exactly 1",
         worker_mut=lambda s: s.replace(ANCHOR, ANCHOR + "\n" + ANCHOR, 1))

run_case("C3  G3 re-run: aligned condition already present", "INPUT",
         "not re-runnable",
         worker_mut=lambda s: s.replace(
             "  const permission_confirmed = body.permission_confirmed === true;",
             "  if (tenure === 'rent') { /* already done */ }\n"
             "  const permission_confirmed = body.permission_confirmed === true;",
             1))

run_case("C4  G9a preserved line absent before the patch", "INPUT",
         "not present exactly once before",
         worker_mut=lambda s: s.replace(PRESERVED + "\n", "", 1))

# -------------------------------------------------------------- BUILDER cases
run_case("C5  G9b patch deletes the preserved refusal", "BUILDER",
         "did not survive",
         builder_mut=lambda b: b.replace(
             "    out = src.replace(OLD, NEW, 1)",
             "    out = src.replace(OLD, NEW, 1).replace(PRESERVED + chr(10), '')")
         if "    out = src.replace(OLD, NEW, 1)" in b else
         b.replace("out = src.replace(OLD, NEW, 1)",
                   "out = src.replace(OLD, NEW, 1).replace(PRESERVED + chr(10), '')"))

run_case("C6  G10 rent branch loses the garden_note refusal", "BUILDER",
         "not present exactly once after",
         builder_mut=lambda b: NEW_RE.sub(new_block("""  const permission_confirmed = body.permission_confirmed === true;
  if (tenure === 'rent') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
  }"""), b))

run_case("C7  G10 rent refusals put out of order", "BUILDER",
         "out of order",
         builder_mut=lambda b: NEW_RE.sub(new_block("""  const permission_confirmed = body.permission_confirmed === true;
  if (tenure === 'rent') {
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
  }"""), b))

run_case("C8  G11 an extra statement smuggled in", "BUILDER",
         "somewhere other than the tenure condition",
         builder_mut=lambda b: NEW_RE.sub(new_block("""  const permission_confirmed = body.permission_confirmed === true;
  const extra = 1;
  if (tenure === 'rent') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }"""), b))

run_case("C9  G12 introduction logic added", "BUILDER",
         "promotion is a G7 decision",
         builder_mut=lambda b: NEW_RE.sub(new_block("""  const permission_confirmed = body.permission_confirmed === true;
  const introducible = tenure === 'own';
  if (tenure === 'rent') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }"""), b))

run_case("C10 G13 a second record status assigned", "BUILDER",
         "other than SUBMIT_STATUS",
         builder_mut=lambda b: NEW_RE.sub(new_block("""  const permission_confirmed = body.permission_confirmed === true;
  const pre = { status: 'paused' };
  if (tenure === 'rent') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }"""), b))

run_case("C11 G14 a new homeowner-visible literal added", "BUILDER",
         "string literals changed",
         builder_mut=lambda b: NEW_RE.sub(new_block("""  const permission_confirmed = body.permission_confirmed === true;
  const hint = 'Someone nearby may be looking for growing space';
  if (tenure === 'rent') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }"""), b))

run_case("C12 G15 the token bound to a local", "BUILDER",
         "neither inside a comment nor an env read",
         builder_mut=lambda b: NEW_RE.sub(new_block("""  const permission_confirmed = body.permission_confirmed === true;
  const tok = AIRTABLE_TOKEN;
  if (tenure === 'rent') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }"""), b))

run_case("C13 G14b condition changed to the wrong tenure", "BUILDER",
         "moved by",
         builder_mut=lambda b: NEW_RE.sub(new_block("""  const permission_confirmed = body.permission_confirmed === true;
  if (tenure !== 'buying') {
    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
  }"""), b))

run_case("C14 G16 the landlord denial is broken by rewrapping", "BUILDER",
         "unbroken on one line",
         # Anchored on text unique to NEW. A shorter anchor also matched OLD,
         # whose comment carries the same denial, and broke the builder's own
         # anchor instead of the guard under test.
         builder_mut=lambda b: b.replace(
             "a lease, or a landlord's details: the\n     homeowner's own sentence is evidence of",
             "a lease, or a\n     landlord's details: the homeowner's own sentence is evidence of"))

print()
print("  %d guards proven capable, %d blind" % (passed, failed))
print()
print("  ORDERING NOTE. G11 (\'executable text differs ONLY in that condition\')")
print("  is the catch-all and runs LAST, deliberately. An earlier draft ran it")
print("  first, which masked G12-G15 and G14b and reported five guards blind")
print("  that were in fact working. Specific diagnosis before generic.")
sys.exit(1 if failed else 0)
