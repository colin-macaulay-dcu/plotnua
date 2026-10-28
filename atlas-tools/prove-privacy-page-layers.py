#!/usr/bin/env python3
"""Capability proof for privacy_page_layers.py (verification repair, 27 Oct 2026). Read-only.

    python3 atlas-tools/prove-privacy-page-layers.py

Shows that the repaired verifiers still catch every change to governed notice
text, that the WhatsApp block is held exactly (never silently absorbed), and
that only genuine site-shell changes are set aside.
"""
import importlib.util, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import privacy_page_layers as L
import search_rail_layer as R

ok = bad = 0
def check(name, cond):
    global ok, bad
    ok += bool(cond); bad += (not cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name)

def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / name)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

B4, B5 = load("build-privacy-v4.py"), load("build-privacy-v5.py")
live = (ROOT / "privacy.html").read_text(encoding="utf-8")
gov = lambda t: B4._without_v6(t)
v5ok = lambda t: B5.published_ok(B5._without_v6(t))

def raises(f):
    try:
        f(); return False
    except (ValueError, SystemExit):
        return True

# control
check("C0 control: the live page passes V4 exact and V5", B4.published_exact(gov(live)) and v5ok(live))
v6rel = subprocess.run(["git", "-C", str(ROOT), "show", "25f7e61:privacy.html"], capture_output=True, text=True).stdout
check("C1 the governed reading of today's page equals the V6 release page exactly (rail-normalised)",
      bool(v6rel) and R.without_ask_label(L.read_governed(live)) == R.without_ask_label(v6rel))

# notice text changes must still be caught
for label, old, new in [
    ("a Section 8 Artist Register sentence", "Joining is voluntary and free, and it does not commit you to anything.", "Joining is voluntary."),
    ("Section 12 retention line", "Artist Register records are kept for a maximum of 12 months", "Artist Register records are kept for a maximum of 36 months"),
    ("Section 7 Garden Owner wording", "Records are reviewed by a person at PlotNua.", "Records are reviewed by PlotNua."),
    ("Section 1 controller sentence", "who is the data controller", "who controls"),
    ("Section 9 heading", "<h2>9. Cookies</h2>", "<h2>9. Cookie use</h2>"),
    ("the intro sentence", "This Privacy Policy explains how PlotNua handles", "This Privacy Policy describes how PlotNua handles"),
]:
    if live.count(old) < 1:
        check("M %s: anchor present" % label, False); continue
    mut = live.replace(old, new, 1)
    caught = raises(lambda: gov(mut)) or not (B4.published_exact(gov(mut)) and v5ok(mut))
    check("M notice change caught: " + label, caught)

# WhatsApp block held exactly, never absorbed
wa = L.WHATSAPP_BLOCK
check("W1 a changed word inside the WhatsApp block is refused",
      raises(lambda: L.without_whatsapp(live.replace("profile name.", "profile name and location.", 1))))
check("W2 a duplicated WhatsApp block is refused", raises(lambda: L.without_whatsapp(live.replace(wa, wa + wa, 1))))
check("W3 the WhatsApp block moved out of Section 5 is refused",
      raises(lambda: L.without_whatsapp(live.replace(L.WHATSAPP_ANCHOR + wa, L.WHATSAPP_ANCHOR, 1).replace("<h2>9. Cookies</h2>\n", "<h2>9. Cookies</h2>\n" + wa, 1))))
check("W4 extra WhatsApp wording elsewhere is refused",
      raises(lambda: L.without_whatsapp(live.replace("<h2>9. Cookies</h2>", "<h2>9. Cookies</h2><p>WhatsApp enquiries are also logged.</p>", 1))))
import re as _re_w5
check("W5 status is not silently approved: WHATSAPP_CONFIRMATION is None, or a dated founder confirmation (\"founder, YYYY-MM-DD: ...\")",
      L.WHATSAPP_CONFIRMATION is None or bool(_re_w5.match(r"founder, 20\d\d-\d\d-\d\d: .{20,}", str(L.WHATSAPP_CONFIRMATION))))
check("W6 the founder's provisional confirmation is recorded as provisional, not legal approval",
      "provisional" in L.WHATSAPP_PROVISIONAL.lower() and "not legal approval" in L.WHATSAPP_PROVISIONAL)

# shell changes are set aside, but never at the notice's expense
hdr_i = live.find(">Discovery Library<")
check("S1 a site-shell edit (the header's nav label, governed by the header builder) does not change the governed notice reading",
      0 < hdr_i < live.index("<main") and L.read_governed(live) == L.read_governed(live[:hdr_i] + ">Ideas Library<" + live[hdr_i + len(">Discovery Library<"):]))
inj = "<!-- PLOTNUA IDENTITY v1 · SKIP · BEGIN --><p>Hidden notice text</p><!-- PLOTNUA IDENTITY v1 · SKIP · END -->"
mut_s2 = live.replace("<h2>9. Cookies</h2>", inj + "<h2>9. Cookies</h2>", 1)
check("S2 text hidden inside a shell-style marker within the notice is caught (by G1, or by the notice verifiers)",
      raises(lambda: L.without_site_shell(mut_s2)) or not (B4.published_exact(gov(mut_s2)) and v5ok(mut_s2)))

print(f"\n  {ok} passed, {bad} failed")
sys.exit(1 if bad else 0)
