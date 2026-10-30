#!/usr/bin/env python3
"""Proof for Privacy V7 (build-privacy-v7.py + privacy_v7_layer.py). Read-only.

Works before V7 is applied (it applies V7 to the live V6 page in memory) and after
(it takes V7 off the live page first). Never writes privacy.html.

  python3 atlas-tools/prove-privacy-v7.py
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import privacy_v7_layer as L  # noqa: E402
import privacy_page_layers as PPL  # noqa: E402

ok = bad = 0
def check(name, cond, detail=""):
    global ok, bad
    ok += bool(cond); bad += (not cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ("" if cond else f"   {detail}"))

spec = importlib.util.spec_from_file_location("b7", HERE / "build-privacy-v7.py")
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

live = (ROOT / "privacy.html").read_text(encoding="utf-8")
applied = L.MARKER in live
base = L.without_v7(live)
from privacy_v8_layer import without_v8          # V8 sits on top of V7 (29 Oct 2026): the V7 checks read the page beneath it
v7 = without_v8(live) if applied else B.apply(base)
F = L.F25_SUB
def sec(t, n):
    return t[t.index("<h2>%d." % n):t.index("<h2>%d." % (n + 1))]

check("V1 V7 applies to the published V6 notice", L.MARKER in v7 and F in v7)
check("V2 without_v7 is the exact inverse", L.without_v7(v7) == base)
check("V3 a page without V7 passes through untouched", L.without_v7(base) == base)
olds = [o.strip() for o, _ in L.PAIRS]
declared = lambda p: any(p in o or o in p for o in olds)
changed = [p for p in re.findall(r"<(?:p|li|h2|h3)[^>]*>.*?</(?:p|li|h2|h3)>", base, re.S) if v7.count(p) < base.count(p)]
check("V4 only the declared replacements change (%d paragraphs/headings, all declared)" % len(changed),
      all(declared(p) for p in changed) and len(changed) <= len(L.PAIRS) + 1)
check("V4b every other paragraph, item and heading survives",
      all(v7.count(p) >= base.count(p) or declared(p) for p in re.findall(r"<(?:p|li|h2|h3)[^>]*>.*?</(?:p|li|h2|h3)>", base, re.S)))
check("V5 the earlier markers V3-V6 are untouched", all(base.count(m) == v7.count(m) for m in
      ["PHASE2-V3", "PHASE2-V4", "PHASE2-V5", "PHASE2-V6", "PLOTNUA-ART-PRIVACY-V4", "PLOTNUA-ARTIST-PRIVACY-V5", "PLOTNUA-GROWER-PRIVACY-V6"]))
s8 = sec(v7, 8)
check("V6 the Founding 25 sub-section sits inside Section 8, after the Artist Register",
      s8.index("Founding 25 applications (artists)") > s8.index("The Artist Register (artists)"))
check("V7 lawful bases: a step before an agreement and legitimate interests for applying; consent ONLY for the waiting list; no permission to publish",
      "as a step before any agreement" in F and "legitimate interest" in F and "does not give us permission to publish" in F
      and [m.start() for m in re.finditer("consent", F, re.I)] and
      all("waiting list" in s for s in re.findall(r"<p>[^<]*consent[^<]*", F, re.I)))
check("V8 curated selection, not first-come; a person decides; no automated decision-making",
      "not on a first-come, first-served basis" in F and "read and decided by a person" in F and "automated decision-making" in F)
check("V9 data minimisation stated, and the biography hint", "do not ask for your home address, your phone number, your date of birth or images" in F
      and "health or other sensitive personal details" in F)
check("V10 retention for every outcome, the 30-day offer and the waiting list",
      all(x in F for x in ["not selected, is withdrawn, or a place offered is not taken up", "has not been decided", "Founding Artist, we keep",
                           "30 days to accept", "waiting list"]))
check("V11 no commission rate, percentage or commercial promise in the sub-section", not re.search(r"\d+\s?%|per ?cent|commission", F, re.I))
check("V12 C1 required-details sentence", "The details marked as required are needed for us to consider your application." in F)
check("V13 C2 Google Workspace: named, with its transfer safeguards (Data Privacy Framework and SCCs)",
      "runs on Google Workspace" in F and "Data Privacy Framework" in F and "standard contractual clauses" in F
      and "provided by Google Workspace" in sec(v7, 10))
check("V14 island of Ireland, not 'in Ireland'", "island of Ireland" in F and "based or working in Ireland" not in F)
check("V15 spam wording is accurate: no claim of Turnstile or cookies", "Turnstile" not in F and "do not use cookies" in F)
s1 = sec(v7, 1)
check("V16 Section 1: certificate spelling, Business Name Registration No. 794392, not a company, PlotArt an initiative, Legal information link; no home address",
      "Colin MacAulay (registered as Colin Macaulay), who is the data controller" in s1 and "Business Name Registration No. 794392" in s1 and "it is not a company" in s1
      and "PlotArt is an initiative of PlotNua" in s1 and "terms.html#legal-information" in s1 and "Allen Park" not in v7)
check("V17 Sections 14 and 15 are firm (no 'may have'), with the DPC's address",
      "may have rights" not in sec(v7, 14) and "Visitors have the following rights" in sec(v7, 14)
      and "They also have the right to lodge a complaint" in sec(v7, 15) and "www.dataprotection.ie" in sec(v7, 15))
foot = v7[v7.index("<footer"):]
check("V18 footer: heading 'PlotNua' (no 'Company') and a Legal information link", "<h2>PlotNua</h2>" in foot and "<h2>Company</h2>" not in foot
      and 'href="terms.html#legal-information">Legal information' in foot)
check("V19 Sections 2, 10 and 12 each gain the Founding 25 line once",
      all(v7.count(x) == 1 for x in ["If you apply to the PlotArt Founding 25", "PlotArt Founding 25 applications described in Section 8 use",
                                     "PlotArt Founding 25 applications are kept for the periods described in Section 8."]))
check("V20 the WhatsApp subsection is unchanged by V7 (C4 deferred)", v7.count(PPL.WHATSAPP_BLOCK) == base.count(PPL.WHATSAPP_BLOCK) == 1)
check("V21 the governed V3-V6 reading of the V7 page equals the V6 page (read_governed composes)",
      PPL.read_governed(v7) == PPL.read_governed(base))
for label, mut in [("a word changed inside the sub-section", lambda t: t.replace("for 12 months after that decision;", "for 24 months after that decision;", 1)),
                   ("the Section 12 line removed", lambda t: t.replace(L.S12_NEW, L.S12_OLD)),
                   ("the footer heading reverted", lambda t: t.replace("<h2>PlotNua</h2>\n        <ul>\n          <li><a href=\"about.html\">", "<h2>Company</h2>\n        <ul>\n          <li><a href=\"about.html\">", 1)),
                   ("the registration number altered", lambda t: t.replace("No. 794392", "No. 794393", 1))]:
    try:
        L.without_v7(mut(v7)); res = False
    except ValueError:
        res = True
    check(f"V22 a drifted V7 cannot hide behind the layer: {label}", res)
if not applied:
    r = subprocess.run([sys.executable, str(HERE / "build-privacy-v7.py")], capture_output=True, text=True)
    check("V23 the builder refuses to write without the founder's approval (P0)", r.returncode == 2 and ("P0" in r.stderr or "P5" in r.stderr))
    check("V24 privacy.html is unchanged (V7 not applied)", L.MARKER not in live)
else:
    r = subprocess.run([sys.executable, str(HERE / "build-privacy-v7.py"), "--check"], capture_output=True, text=True)
    check("V23 applied: build-privacy-v7 --check", r.returncode == 0 and "privacy V7 present" in r.stdout)
    import privacy_v8_layer as V8   # V8 (29 Oct 2026) may sit on top: V7 is checked beneath it
    check("V24 applied: the live page is exactly V7 over V6 (beneath V8 when present)", B.apply(base) == V8.without_v8(live))
print(f"\n  {ok} passed, {bad} failed · V7 {'APPLIED' if applied else 'NOT APPLIED (prepared)'}")
sys.exit(1 if bad else 0)
