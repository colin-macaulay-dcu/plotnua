#!/usr/bin/env python3
"""GUARD-CAPABILITY PROOF · Art Space Register builder (R1-R13) and art
cross-link builder (X1-X4).

Each case breaks ONE thing in a real file (the page, a builder, the Worker or
a protected Garden file), runs the builder's --check, asserts the break is
REFUSED, and restores the file. A clean control runs before and after, and
every touched file is hashed before and after the whole run.

Exit 0 = every break caught, controls pass, every file byte-identical.
Run: python3 atlas-tools/prove-art-space-register.py
"""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RB = ROOT / "atlas-tools" / "build-art-space-register.py"
XB = ROOT / "atlas-tools" / "build-art-cross-links.py"
PAGE = ROOT / "disc024-open-your-home-to-art.html"
WORKER = ROOT / "worker" / "art-space-register" / "src" / "index.js"
GARDEN = ROOT / "disc025-borrowed-garden-check.html"
OY = ROOT / "discovery-open-your-home-to-art.html"
HA = ROOT / "discovery-a-home-for-art.html"
FILES = [RB, XB, PAGE, WORKER, GARDEN, OY, HA]

h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
BEFORE = {p.name: h(p) for p in FILES}
results = []


def run(builder):
    return subprocess.run([sys.executable, str(builder), "--check"], capture_output=True, text=True, cwd=str(ROOT))


def case(label, path, old, new, builder=RB, expect="REFUSED"):
    orig = path.read_bytes()
    text = orig.decode("utf-8")
    try:
        if old not in text:
            results.append((label, False, "mutation anchor not found")); return
        path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
        r = run(builder)
        line = (r.stdout.strip().splitlines() or [""])[-1]
        caught = r.returncode != 0 and expect in r.stdout
        results.append((label, caught, line[:110]))
    finally:
        path.write_bytes(orig)


ctl0 = run(RB).returncode == 0 and run(XB).returncode == 0

case("R1 page edited outside the register", PAGE,
     "How far would you actually want this to go?", "How far would you go?")
case("R1 a Property Check question changed", PAGE,
     "q:'What could you actually offer?'", "q:'What space could you offer?'")
case("R1 a save key changed", PAGE,
     "journeyId: 'disc024-open-your-home-to-art'", "journeyId: 'disc024-art'")
case("R2 builder set to open the register", RB,
     "INTEREST_PUBLIC = False", "INTEREST_PUBLIC = True")
case("R3 Worker consent sentence drifts", WORKER,
     "withdraw my consent at any time.\";", "withdraw at any time.\";")
case("R3 page consent sentence drifts", RB,
     "the Open Your Home to Art pilot. I understand", "the art pilot. I understand")
case("R4 Worker gains a county the page lacks", WORKER, "'wicklow']", "'wicklow', 'antrim']")
case("R4 Worker gains a way the page lacks", WORKER,
     "ways: ['store', 'display', 'open', 'help_sell']", "ways: ['store', 'display', 'open', 'help_sell', 'studio']")
case("R5 Worker would accept an Eircode", WORKER, "'over_18', 'consent_text', 'source'",
     "'over_18', 'consent_text', 'source', 'eircode'")
case("R5 page would send the honeypot", RB, "      source: 'property_check'\n    };",
     "      source: 'property_check',\n      website: $('asrWebsite').value\n    };")
case("R6 an Eircode field is added", RB,
     '<select id="asrCounty" name="county" required></select>',
     '<select id="asrCounty" name="county" required></select><input type="text" name="eircode">')
case("R6 a phone (tel) input is added", RB,
     '<select id="asrCounty" name="county" required></select>',
     '<select id="asrCounty" name="county" required></select><input type="tel" name="contact">')
case("R7 approved invitation sentence removed", RB,
     '    "Would you be interested in hearing more?",\n', "")
case("R7 assurance removed", RB, "no commitment, no payment and no matching service",
     "no commitment and no matching service")
case("R7 income promise added", RB, "Would you be interested in hearing more?",
     "Would you be interested in hearing more? You could earn from your wall.")
case("R7 'guaranteed' added to the confirmation", RB, "If the pilot develops, we will email you.",
     "An introduction is guaranteed.")
case("R8 scope widened to studios", RB, "['open', 'Opening the space to visitors, by arrangement']",
     "['open', 'Opening the space to visitors, or as a studio']")
case("R9 honeypot made visible to assistive tech", RB,
     '<div class="asr-hp" aria-hidden="true">', '<div class="asr-hp">')
case("R10 tenure question added", RB, "Leave this field empty", "Do you own or rent the home? Leave this field empty")
case("R11 mount passes the whole answer set", RB,
     "mount({ space: answers.space, level: answers.level, money: answers.money })",
     "mount({ space: answers.space, level: answers.level, money: answers.money, access: answers.access })")
case("R12 register script reads localStorage", RB, "  function previewRequested() {",
     "  function previewRequested() {\n    localStorage.getItem('x');")
case("R12 register script calls the garden Worker", RB,
     'ENDPOINT = "https://plotnua-art-space-register.colin-a41.workers.dev/v1/art-space-register/host"',
     'ENDPOINT = "https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/garden"')
case("R13 Garden Owner Register page touched", GARDEN,
     "This is a register, not a match.</p>", "This is a register.</p>")
case("CHECK page hand-edited inside the register", PAGE,
     "Could your home become a home for art?</h2>", "Could your home host art?</h2>", expect="CHECK FAILED")
case("X1 Discovery edited outside the cross-link", OY,
     "Nothing has to happen twice.", "Nothing needs to happen twice.", builder=XB)
case("X2 cross-link pointed at a missing page", XB,
     '"target": "discovery-a-home-for-art.html"', '"target": "discovery-art.html"', builder=XB)
case("X3 a Property Check link changed", HA,
     'href="disc023-buy-original-irish-art.html"', 'href="disc023-buy-original-irish-art.html?x=1"', builder=XB)

ctl1 = run(RB).returncode == 0 and run(XB).returncode == 0
same = BEFORE == {p.name: h(p) for p in FILES}

print("=" * 76)
print("  CONTROL before   %s" % ("PASS" if ctl0 else "FAIL"))
for label, caught, why in results:
    print("  %-46s %s  %s" % (label, "CAUGHT" if caught else "*** MISSED ***", why))
print("  CONTROL after    %s" % ("PASS" if ctl1 else "FAIL"))
print("  every touched file byte-identical after the proof: %s" % ("YES" if same else "NO"))
ok = ctl0 and ctl1 and same and all(c for _, c, _ in results)
print("  %d/%d breaks caught — %s" % (sum(c for _, c, _ in results), len(results), "PROVEN" if ok else "NOT PROVEN"))
sys.exit(0 if ok else 1)
