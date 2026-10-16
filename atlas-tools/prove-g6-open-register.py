#!/usr/bin/env python3
"""
GUARD-CAPABILITY PROOF for build-g6-open-register.py
===============================================================================
The pre-opening input is derived from the tree itself: the current page with
its one switch line set back to false. No git reference is needed, so this
runs in any clone. Each case breaks one precondition; the builder must REFUSE
and write nothing. A control proves the derived input applies, and that the
builder's output is byte-identical to the page on disk.

  python3 atlas-tools/prove-g6-open-register.py
"""
import sys as _sys_v6
_sys_v6.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from privacy_v6_layer import without_v6 as _without_v6  # V6 layer
import importlib.util, io, pathlib, shutil, sys, tempfile
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
ON, OFF = "  var INTEREST_PUBLIC = true;", "  var INTEREST_PUBLIC = false;"
LIVE = {
    "page": (ROOT / "disc025-borrowed-garden-check.html").read_text(encoding="utf-8"),
    "privacy": _without_v6((ROOT / "privacy.html").read_text(encoding="utf-8")),
    "worker": (ROOT / "worker/garden-register/src/index.js").read_text(encoding="utf-8"),
    "wrangler": (ROOT / "worker/garden-register/wrangler.toml").read_text(encoding="utf-8"),
}
assert LIVE["page"].count(ON) == 1 and OFF not in LIVE["page"], "page on disk is not the opened page"
PRE = dict(LIVE, page=LIVE["page"].replace(ON, OFF))
PASS = FAIL = 0


def builder():
    spec = importlib.util.spec_from_file_location("g6o", HERE / "build-g6-open-register.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def case(label, mutate=None, control=False):
    global PASS, FAIL
    d = pathlib.Path(tempfile.mkdtemp(prefix="g6o-"))
    try:
        files = dict(PRE)
        if mutate:
            files = mutate(files)
            if files is None:
                FAIL += 1; print(f"  [VACUOUS ] {label}"); return
        paths = {k: d / k for k in files}
        for k, p in paths.items(): p.write_text(files[k], encoding="utf-8")
        m = builder()
        m.PAGE, m.PRIVACY, m.WORKER, m.WRANGLER = paths["page"], paths["privacy"], paths["worker"], paths["wrangler"]
        before = {k: p.read_bytes() for k, p in paths.items()}
        buf, code, old = io.StringIO(), 0, sys.argv
        sys.argv = ["b", "--apply"]
        try:
            with redirect_stdout(buf): m.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        except Exception as e:
            code = -1; buf.write(f"CRASH {type(e).__name__}: {e}")
        finally:
            sys.argv = old
        out = buf.getvalue().strip()
        if control:
            ok = code == 0 and paths["page"].read_text(encoding="utf-8") == LIVE["page"]
            tag = "CONTROL"
        else:
            ok = code == 2 and "REFUSED" in out and all(paths[k].read_bytes() == before[k] for k in paths)
            tag = "CAPABLE" if ok else "BLIND"
        PASS += ok; FAIL += (not ok)
        print(f"  [{tag:8}] {label}" + ("" if ok else f"   -> {out.splitlines()[-1] if out else code}"))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def edit(key, old, new):
    def f(files):
        if files[key].count(old) != 1: return None
        return dict(files, **{key: files[key].replace(old, new)})
    return f


print("\n  G6 OPENING · BUILDER CAPABILITY\n")
case("O0 control: the closed page opens, and the result equals the page on disk", control=True)
case("O1 already open", lambda f: dict(f, page=f["page"].replace(OFF, ON)))
case("O2 the switch line duplicated", edit("page", OFF, OFF + "\n" + OFF))
case("O3 G6 offer wording absent (pre-G6 page)", edit("page", "<strong>Matching isn&rsquo;t live yet.</strong>", "<strong>Soon.</strong>"))
case("O4 payload not tenure-only", edit("page", "      inherited_tenure: answers.tenure || ''\n    };",
                                        "      inherited_tenure: answers.tenure || '',\n      inherited_way_in: answers.way_in || ''\n    };"))
case("O5 honeypot absent", edit("page", 'id="bgIntWebsite" name="website" tabindex="-1"', 'id="bgIntWebsite" name="website"'))
case("O6 consent sentence altered", edit("page", "tell me if someone nearby is looking for growing space.\";", "tell me about growing space.\";"))
case("O7 pre-PS-1 footer", edit("page", "you can choose to join the register.", "nothing on this page sends your details anywhere."))
case("O8 no_garden suppression removed", edit("page", "if (answers.spare_corner === 'no_garden') return false;", "if (false) return false;"))
case("O9 privacy Section 7 absent", edit("privacy", "<h2>7. The Garden Owner Register</h2>", "<h2>7. Cookies</h2>"))
case("O10 Worker without the deprecated-key refusal", edit("worker", "if (deprecated) return REFUSED(cors, deprecated);", "/* gone */"))
case("O11 Worker status ceiling raised", edit("worker", "const SUBMIT_STATUS = 'interest_submitted';", "const SUBMIT_STATUS = 'contact_confirmed';"))
case("O12 wrangler.toml still on privacy V2", edit("wrangler", '"2026-10-PHASE2-V3"', '"2026-10-PHASE2-V2"'))


# O13 · the builder's OWN replacement widened to two lines: its post-gate
# (exactly one changed line, and it is the switch) must refuse.
print()
spec_case = "O13 a rewrite that changes more than the switch line"
d = pathlib.Path(tempfile.mkdtemp(prefix="g6o-"))
try:
    m = builder()
    m.ON = "  var INTEREST_PUBLIC = true;\n  var EXTRA = 1;"
    try:
        m.build(PRE["page"], PRE["privacy"], PRE["worker"], PRE["wrangler"]); ok = False; msg = "applied"
    except SystemExit as e:
        ok = e.code == 2; msg = ""
    PASS += ok; FAIL += (not ok)
    print(f"  [{'CAPABLE' if ok else 'BLIND':8}] {spec_case}" + ("" if ok else "   -> " + msg))
finally:
    shutil.rmtree(d, ignore_errors=True)

print(f"\n  {PASS} passed, {FAIL} failed\n")
sys.exit(1 if FAIL else 0)
