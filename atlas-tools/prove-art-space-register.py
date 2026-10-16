#!/usr/bin/env python3
"""GUARD-CAPABILITY PROOF · Art Space Register builder (R1-R13).
(The art cross-link builder, X1-X4, was retired on 13 Oct 2026 when the two
art Discoveries merged into A Home for Art.)

Each case breaks ONE thing in a real file (the page, a builder, the Worker or
a protected Garden file), runs the builder's --check, asserts the break is
REFUSED, and restores the file. A clean control runs before and after, and
every touched file is hashed before and after the whole run.

Exit 0 = every break caught, controls pass, every file byte-identical.
Run: python3 atlas-tools/prove-art-space-register.py
"""
import sys as _sys_v6
_sys_v6.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from privacy_v6_layer import without_v6 as _without_v6  # V6 layer
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RB = ROOT / "atlas-tools" / "build-art-space-register.py"
PAGE = ROOT / "disc024-open-your-home-to-art.html"
WORKER = ROOT / "worker" / "art-space-register" / "src" / "index.js"
GARDEN = ROOT / "disc025-borrowed-garden-check.html"
PRIVACY = ROOT / "privacy.html"
ART_WRANGLER = ROOT / "worker" / "art-space-register" / "wrangler.toml"
SCHEMA = ROOT / "worker" / "art-space-register" / "airtable-schema.json"
PAGE23 = ROOT / "disc023-buy-original-irish-art.html"
DISCOVERY = ROOT / "discovery-a-home-for-art.html"
FILES = [RB, PAGE, WORKER, GARDEN, PRIVACY, ART_WRANGLER, SCHEMA, PAGE23, DISCOVERY]

import importlib.util
_spec = importlib.util.spec_from_file_location("pv4", ROOT / "atlas-tools" / "build-privacy-v4.py")
PV4 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(PV4)
_LIVE = _without_v6(PRIVACY.read_text(encoding="utf-8"))  # V6 layer: this proof governs V3-V5
# Privacy V4 was published on 13 Oct 2026 (founder approval, notice only). The
# proof works on either state: V3_PAGE and V4_PAGE are built in memory and
# written only inside a case.
# Privacy V5 (14 Oct 2026) is built over V4. Once it is live, V4_PAGE is the
# notice in force (the V5 page) and V3_PAGE is still derived from the V4 page
# inside it; the Art Worker then records V5 (CUR_VERSION).
V5_LIVE = PV4.v5_live(_LIVE)
_L4 = PV4.as_v4(_LIVE)
PUBLISHED = PV4.MARK in _L4
V3_PAGE = PV4.untransform(_L4) if PUBLISHED else _L4
V4_PAGE = _LIVE if PUBLISHED else PV4.transform(_LIVE)
CUR_VERSION = 'PRIVACY_VERSION = "%s"' % ("2026-10-PHASE2-V5" if V5_LIVE else "2026-10-PHASE2-V4")
COOKIES_H2 = "<h2>9. Cookies</h2>" if PUBLISHED else "<h2>8. Cookies</h2>"
APPROVED = ('OPEN_APPROVAL = {"founder_approval": "proof", "self_assessment": "proof", '
            '"risks_resolved": "proof", "dry_run": "proof"}')

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


def multi(label, edits, expect="REFUSED", positive=False):
    """Several coordinated edits (path, old, new) or (path, None, whole_text)."""
    saved = {p: p.read_bytes() for p, _, _ in edits}
    try:
        for path, old, new in edits:
            text = path.read_text(encoding="utf-8")
            if old is None:
                text = new
            else:
                if old not in text:
                    results.append((label, False, "mutation anchor not found")); return
                text = text.replace(old, new, 1)
            path.write_text(text, encoding="utf-8")
        r = run(RB)
        line = (r.stdout.strip().splitlines() or [""])[-1]
        if positive:
            caught = "REFUSED" not in r.stdout and "out of date" in r.stdout
        else:
            caught = r.returncode != 0 and expect in r.stdout
        results.append((label, caught, line[:110]))
    finally:
        for path, b in saved.items():
            path.write_bytes(b)


OPENED = "INTEREST_PUBLIC = True " in RB.read_text(encoding="utf-8")   # opened 14 Oct 2026
OPEN = (RB, "INTEREST_PUBLIC = False", "INTEREST_PUBLIC = True")
APPROVE = (RB, "OPEN_APPROVAL = None", APPROVED)
V4 = (PRIVACY, None, V4_PAGE)
V3 = (PRIVACY, None, V3_PAGE)

ctl0 = run(RB).returncode == 0

case("R1 page edited outside the register", PAGE,
     "Could your home hold an artist&rsquo;s work?", "Could your home hold art?")
case("R1 a Property Check question changed", PAGE,
     "q:'What could you actually offer?'", "q:'What space could you offer?'")
case("R1 a save key changed", PAGE,
     "journeyId: 'disc024-open-your-home-to-art'", "journeyId: 'disc024-art'")
if not OPENED:
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
# ---- the opening gate (activation preparation, 13 Oct 2026)
if OPENED:
    # The register is OPEN (founder approval, 14 Oct 2026). Every condition of the gate must keep holding.
    WOFF = (ART_WRANGLER, 'WRITES_ENABLED  = "true"', 'WRITES_ENABLED  = "false"')
    CLOSE = (RB, "INTEREST_PUBLIC = True ", "INTEREST_PUBLIC = False ")
    multi("R2 open, but OPEN_APPROVAL withdrawn", [(RB, "OPEN_APPROVAL = {", "OPEN_APPROVAL = None\n_WITHDRAWN = {")],
          expect="REFUSED: R2")
    multi("R2 open, but OPEN_APPROVAL lacks the dry run", [(RB, '"dry_run": "14 October', '"dry_run_x": "14 October')], expect="REFUSED: R2")
    multi("R2 open, but OPEN_APPROVAL lacks the risk resolution", [(RB, '    "risks_resolved": "Privacy',
          '    "risks_x": "Privacy')], expect="REFUSED: R2")
    multi("R2 open, but privacy back to V3", [V3], expect="REFUSED: R2")
    multi("R2 open, but Art Worker not on the published version",
          [(ART_WRANGLER, CUR_VERSION, 'PRIVACY_VERSION = "2026-10-PHASE2-V3"')], expect="REFUSED: R2")
    assert V4_PAGE.count("We keep your record for no longer than 12 months") == 1
    multi("R2 open, but published Section 8 differs (36-month retention)",
          [(PRIVACY, None, V4_PAGE.replace("We keep your record for no longer than 12 months",
                                           "We keep your record for no longer than 36 months", 1))], expect="REFUSED: R2")
    multi("R2 page closed while the Worker would still take writes", [CLOSE], expect="REFUSED: R2")
    multi("R2 WRITES_ENABLED neither true nor false", [(ART_WRANGLER, 'WRITES_ENABLED  = "true"', 'WRITES_ENABLED  = "yes"')],
          expect="REFUSED: R2")
    multi("R2 builder keeps the private-preview label on the public page",
          [(RB, "('' if INTEREST_PUBLIC else", "('' if False else")], expect="REFUSED: R2")
    multi("CHECK private-preview label hand-added to the public page",
          [(PAGE, '<section class="asr" id="asrSection" hidden aria-labelledby="asrH">\n',
            '<section class="asr" id="asrSection" hidden aria-labelledby="asrH">\n      <p class="asr-prev" id="asrPrev" hidden>Private preview</p>\n')],
          expect="CHECK FAILED")
    multi("R13 open, but privacy.html alters Garden Section 7",
          [(PRIVACY, "your phone number, your surname, your age, photographs of your garden",
            "your phone number, your age, photographs of your garden")],
          # Once V5 is live, R2's exact V5-over-V4 verification refuses this first.
          expect="REFUSED: R2" if V5_LIVE else "REFUSED: R13")
    multi("R7 send button relabelled back to the CTA", [(RB, 'SEND_LABEL = "Submit my registration"', 'SEND_LABEL = "Register my interest"')],
          expect="REFUSED: R7")
    multi("POSITIVE closing (page and Worker together) is allowed", [CLOSE, WOFF], positive=True)
    multi("CONTROL open register passes", [], positive=False, expect="CHECK OK")
    results[-1] = (results[-1][0], not results[-1][1] and "CHECK OK" in results[-1][2], results[-1][2])
if not OPENED:
  multi("R2 opening approved but privacy still V3", [OPEN, APPROVE, V3], expect="REFUSED: R2")
  multi("R2 privacy V4 live but no OPEN_APPROVAL", [OPEN, V4])
  multi("R2 OPEN_APPROVAL lacks the dry run", [OPEN, V4, (RB, "OPEN_APPROVAL = None",
        'OPEN_APPROVAL = {"founder_approval": "proof", "self_assessment": "proof", "risks_resolved": "proof", "dry_run": " "}')])
  multi("R2 OPEN_APPROVAL lacks the risk resolution", [OPEN, V4, (RB, "OPEN_APPROVAL = None",
        'OPEN_APPROVAL = {"founder_approval": "proof", "self_assessment": "proof", "dry_run": "proof"}')])
  multi("R2 Art Worker not on the published version", [OPEN, V4, APPROVE,
        (ART_WRANGLER, CUR_VERSION, 'PRIVACY_VERSION = "2026-10-PHASE2-V3"')])
  assert V4_PAGE.count("We keep your record for no longer than 12 months") == 1
  multi("R2 published Section 8 differs (36-month retention)", [OPEN, APPROVE,
        (PRIVACY, None, V4_PAGE.replace("We keep your record for no longer than 12 months",
                                        "We keep your record for no longer than 36 months", 1))],
        expect="REFUSED: R2")
  multi("R13 the V4 page also alters Garden Section 7", [OPEN, V4, APPROVE,
        (PRIVACY, "your phone number, your surname, your age, photographs of your garden",
         "your phone number, your age, photographs of your garden")], expect="REFUSED: R13")
  multi("POSITIVE all three conditions met: gate opens", [OPEN, V4, APPROVE], positive=True)
  multi("CONTROL privacy V4 staged, register closed: passes", [V4], positive=False, expect="CHECK OK")
  results[-1] = (results[-1][0], not results[-1][1] and "CHECK OK" in results[-1][2], results[-1][2])
# ---- R7b, R13, R14
case("R7b commitment statement weakened", RB, "PlotNua is simply exploring whether homeowners",
     "PlotNua is exploring whether homeowners")
case("R7b commitment statement dropped from the form", RB,
     "        '        <p class=\"asr-p\" id=\"asrCommit\">%s</p>\\n' % COMMITMENT +\n", "")
multi("R13 privacy.html hand-edited, not by the V4 builder", [(PRIVACY, COOKIES_H2, COOKIES_H2.replace("Cookies", "Cookie use"))])
import json as _json


def schema_with(fn):
    """A whole-file schema mutation made on the parsed JSON, so file formatting cannot blind a case."""
    d = _json.loads(SCHEMA.read_text(encoding="utf-8"))
    fn(d)
    return (SCHEMA, None, _json.dumps(d, indent=2, ensure_ascii=False) + "\n")


def _hosts(d):
    return [t for t in d["tables"] if t["name"] == "Hosts"][0]["fields"]


def _drop_field(d, name):
    t = [t for t in d["tables"] if t["name"] == "Hosts"][0]
    t["fields"] = [f for f in t["fields"] if f["name"] != name]


multi("R14 schema lacks a field the Worker writes", [schema_with(lambda d: _drop_field(d, "consent_text_hash"))])
multi("R14 schema county options drift", [schema_with(lambda d: [f for f in _hosts(d) if f["name"] == "county"][0]["options"].append("antrim"))])
multi("R14 schema gives status a second option", [schema_with(lambda d: [f for f in _hosts(d) if f["name"] == "status"][0]["options"].append("introduced"))])
multi("R14 Status log table missing", [(SCHEMA, '"name": "Status log"', '"name": "Log"')])
case("CHECK page hand-edited inside the register", PAGE,
     "Could your home become a home for art?</h2>", "Could your home host art?</h2>", expect="CHECK FAILED")

# ---- E0-E7 · A Home for Art two-option entry (founder approval 14 Oct 2026)
case("E0 DISC-023 Start button hand-edited", PAGE23,
     '<button class="pc-cta" id="arStart">Start the check', '<button class="pc-cta" id="arStart">Begin',
     expect="REFUSED: E0")
case("E2 Discovery loses #discover-and-own", DISCOVERY,
     'id="discover-and-own"', 'id="discover-own"', expect="REFUSED: E2")
case("E5 Discovery links to a check without ?start=1", DISCOVERY,
     'href="disc023-buy-original-irish-art.html?start=1"', 'href="disc023-buy-original-irish-art.html"',
     expect="REFUSED: E5")
case("E6 DISC-023 edited outside the entry", PAGE23,
     "What will your wall actually take?", "What will your wall take?", expect="REFUSED: E6")


def guard_case(label, path, old, new, expect):
    """A page as a broken build would emit it, given straight to entry_guards():
    the E0 anchors cannot mask the guard under test. Nothing is written."""
    import contextlib, importlib.util, io
    spec = importlib.util.spec_from_file_location("asr_proof", RB)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        results.append((label, False, "mutation anchor not found exactly once")); return
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            mod.entry_guards(path.name, text.replace(old, new))
            code = 0
        except SystemExit as e:
            code = e.code
    out = buf.getvalue().strip()
    results.append((label, bool(code) and expect in out, (out.splitlines() or [""])[-1][:110]))


guard_case("E1 Discover button sent to the wrong section", PAGE23,
           'href="discovery-a-home-for-art.html#discover-and-own">Discover A Home for Art',
           'href="discovery-a-home-for-art.html#live-with-art">Discover A Home for Art', "REFUSED: E1")
guard_case("E1 Discover relabelled", PAGE,
           '">Discover A Home for Art\n', '">Learn more\n', "REFUSED: E1")
guard_case("E1 Discover placed before Start", PAGE23,
           '    <button class="pc-cta" id="arStart">Start the check\n'
           '      <span class="pc-arrow" aria-hidden="true">&rarr;</span></button>\n'
           '    <a class="pc-ghost" id="arDiscover" href="discovery-a-home-for-art.html#discover-and-own">Discover A Home for Art\n'
           '      <span class="pc-arrow" aria-hidden="true">&rarr;</span></a>\n',
           '    <a class="pc-ghost" id="arDiscover" href="discovery-a-home-for-art.html#discover-and-own">Discover A Home for Art\n'
           '      <span class="pc-arrow" aria-hidden="true">&rarr;</span></a>\n'
           '    <button class="pc-cta" id="arStart">Start the check\n'
           '      <span class="pc-arrow" aria-hidden="true">&rarr;</span></button>\n', "REFUSED: E1")
guard_case("E7 Discover opens a new tab", PAGE,
           'id="hoDiscover" href="discovery-a-home-for-art.html#open-your-home-to-art">',
           'id="hoDiscover" href="discovery-a-home-for-art.html#open-your-home-to-art" target="_blank">', "REFUSED: E")
guard_case("E3 ?start=1 does more than advance()", PAGE,
           "  if (/(?:^|[?&])start=1(?:&|$)/.test(location.search.replace(/^\\?/, '?'))) {\n    advance();",
           "  if (/(?:^|[?&])start=1(?:&|$)/.test(location.search.replace(/^\\?/, '?'))) {\n    advance(); show('hoQ');",
           "REFUSED: E3")
guard_case("E3 ?start=1 handler removed", PAGE23,
           "/(?:^|[?&])start=1(?:&|$)/.test(", "/(?:^|[?&])begin=1(?:&|$)/.test(", "REFUSED: E3")
guard_case("E4 DISC-023 header link loses its section", PAGE23,
           '<a class="ar-back" href="discovery-a-home-for-art.html#discover-and-own">',
           '<a class="ar-back" href="discovery-a-home-for-art.html">', "REFUSED: E4")
guard_case("E4 DISC-024 header label reverted", PAGE,
           '<span class="ho-back-x" id="hoBackX">Explore A Home for Art <span aria-hidden="true">&rarr;</span>',
           '<span class="ho-back-x" id="hoBackX">Back to the story', "REFUSED: E4")
case("E6 DISC-024 question edited outside the entry", PAGE,
     "Could your home hold an artist&rsquo;s work?", "Could your home hold art?", expect="REFUSED: R1")

ctl1 = run(RB).returncode == 0
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
