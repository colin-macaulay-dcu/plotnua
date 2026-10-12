#!/usr/bin/env python3
"""
GUARD-CAPABILITY PROOF for build-g6-worker-deprecated-fields.py
===============================================================================
Runs the builder against the PRE-BUILD Worker source read from git (c64e63a),
breaking one precondition at a time. The builder must REFUSE and write nothing.
A control proves the unmutated source applies.

  python3 atlas-tools/prove-g6-worker-builder.py
"""
import importlib.util, io, pathlib, shutil, subprocess, sys, tempfile
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
# Re-pinned 12 October 2026 (Commit A) from 9287489 (local-only) to c64e63a
# (on GitHub main). worker/garden-register/src/index.js is byte-identical at
# both: git blob 171b73af. The proof's meaning is unchanged.
PRE = subprocess.run(["git", "show", "c64e63a:worker/garden-register/src/index.js"],
                     cwd=ROOT, check=True, capture_output=True).stdout.decode()
PASS = FAIL = 0


def builder():
    spec = importlib.util.spec_from_file_location("g6w", HERE / "build-g6-worker-deprecated-fields.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def case(label, src_mut=None, mod_mut=None, control=False):
    global PASS, FAIL
    d = pathlib.Path(tempfile.mkdtemp(prefix="g6w-"))
    try:
        src = PRE
        if src_mut:
            src = src_mut(src)
            if src is None:
                FAIL += 1; print(f"  [VACUOUS ] {label}"); return
        t = d / "index.js"; t.write_text(src, encoding="utf-8")
        m = builder(); m.TARGET = t
        if mod_mut and mod_mut(m) is False:
            FAIL += 1; print(f"  [VACUOUS ] {label}"); return
        before = t.read_bytes(); buf = io.StringIO(); code = 0; old = sys.argv
        sys.argv = ["b", "--apply"]
        try:
            with redirect_stdout(buf): m.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        except Exception as e:                       # a crash is not a refusal
            code = -1; buf.write(f"CRASH {type(e).__name__}: {e}")
        finally:
            sys.argv = old
        out = buf.getvalue().strip()
        if control:
            ok = code == 0 and "APPLIED" in out
            tag = "CONTROL"
        else:
            ok = code == 2 and "REFUSED" in out and t.read_bytes() == before
            tag = "CAPABLE" if ok else "BLIND"
        PASS += ok; FAIL += (not ok)
        print(f"  [{tag:8}] {label}" + ("" if ok else f"   -> {out.splitlines()[-1] if out else code}"))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def edit(old, new):
    return lambda s: s.replace(old, new) if s.count(old) == 1 else None


def modset(attr, old, new):
    def f(m):
        v = getattr(m, attr)
        if v.count(old) != 1: return False
        setattr(m, attr, v.replace(old, new))
    return f


print("\n  G6 R3 · WORKER BUILDER CAPABILITY\n")
case("B0 control: the pre-build Worker applies cleanly", control=True)
case("B1 already applied (marker present)", edit("/* PlotNua — BORROWED", "/* G6-R3-DEPRECATED-FIELDS */\n/* PlotNua — BORROWED"))
case("B2 handler anchor missing", edit("async function handleGarden(env, body, now, cors) {", "async function handleGarden(env, body, nowT, cors) {"))
case("B3 write-path anchor missing", edit("  if (wayIn) fields.inherited_way_in = wayIn;\n", "  if (wayIn) { fields.inherited_way_in = wayIn; }\n"))
case("B4 a protection already absent in the input (tenure not required)",
     edit("  if (!tenure) return REFUSED(cors, 'inherited_tenure');", "  /* gone */"))
case("B5 the rewrite would leave a deprecated key in executable code",
     mod_mut=modset("W2B_NEW", "  if (note) fields.garden_note = note;\n",
                    "  if (note) fields.garden_note = note;\n  if (body.inherited_result_key) fields.inherited_result_key = 1;\n"))
case("B6 the rewrite would drop a key from the deprecated list",
     mod_mut=modset("W1_NEW", "'inherited_your_own_use', 'inherited_result_key'", "'inherited_your_own_use'"))
case("B7 the rewrite would omit the refusal itself",
     mod_mut=modset("W1B_NEW", "  if (deprecated) return REFUSED(cors, deprecated);\n", ""))
case("B8 the rewrite would raise the status ceiling",
     mod_mut=modset("W2B_NEW", "  if (note) fields.garden_note = note;\n",
                    "  if (note) fields.garden_note = note;\n  fields.status = 'qualified_garden_opportunity';\n") )
case("B9 the rewrite would disturb typecast:false",
     src_mut=edit("{ records: [{ fields }], typecast: false }", "{ records: [{ fields }], typecast: true }"))
print(f"\n  {PASS} passed, {FAIL} failed\n")
sys.exit(1 if FAIL else 0)
