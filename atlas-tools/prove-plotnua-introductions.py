#!/usr/bin/env python3
"""PROVE · Package N 'Request an introduction' block (pages side).
Each check is run against the real module, then against planted faults that it must catch.
  python3 atlas-tools/prove-plotnua-introductions.py
"""
import copy, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import plotnua_introductions as M

ROOT = M.ROOT
WORKER = (ROOT / "worker/garden-lead/src/introduction.js").read_text(encoding="utf-8")
cfg = M.load()
results = []


def check(i, what, ok, d=""):
    results.append(bool(ok))
    print("  %s  %s %s%s" % ("PASS" if ok else "FAIL", i, what, "" if ok or not d else "  [%s]" % str(d)[:300]))


def js_str(name):
    m = re.search(r"export const %s =\s*'((?:[^'\\]|\\.)*)'" % name, WORKER, re.S) or \
        re.search(r"export const %s =\s*\n\s*'((?:[^'\\]|\\.)*)'" % name, WORKER, re.S)
    return m.group(1) if m else None


def preview(p, sup=None):
    return M.apply((ROOT / p["page"]).read_text(encoding="utf-8"), p["page"], cfg, force=True, preview_suppliers=sup)


def blk(t):
    a, b = t.find(M.START), t.find(M.END)
    return t[a:b] if a >= 0 else ""


# ------------------------------------------------------------------ switch & bytes
check("P01", "the switch ships off and the config validates", cfg["public"] is False and not M.validate(cfg), M.validate(cfg))
unchanged = all(M.apply((ROOT / p["page"]).read_text(encoding="utf-8"), p["page"], cfg) == (ROOT / p["page"]).read_text(encoding="utf-8")
                for p in cfg["placements"])
check("P02", "switch off: every placement page is byte-for-byte unchanged, and none carries a block", unchanged and
      not any(M.START in (ROOT / p["page"]).read_text(encoding="utf-8") for p in cfg["placements"]))
check("P03", "no PlotArt page and not your-plot.html is a placement (PlotArt and the Journey Contract door untouched)",
      not any(p["page"].startswith("plotart/") or p["page"] == "your-plot.html" for p in cfg["placements"]))

# ------------------------------------------------------------------ agreement with the Worker
check("P04", "the general consent sentence is the founder-approved wording (26 Nov 2026) and identical to the Worker's",
      js_str("GENERAL_CONSENT") == M.GENERAL_CONSENT == ("I agree that PlotNua may use the information I provide to review my enquiry and contact "
      "me about my project. My contact details will not be shared with a supplier without my further permission."), js_str("GENERAL_CONSENT"))
check("P05", "the supplier consent template is identical to the Worker's (founder-approved wording)",
      js_str("SUPPLIER_CONSENT_TEMPLATE") == M.SUPPLIER_CONSENT_TEMPLATE ==
      "I agree that PlotNua may share my enquiry and contact details with [supplier name] so they can contact me about this project.")
wt = dict(re.findall(r"'([a-z0-9-]+)': '([^']+)'", WORKER[WORKER.find("TIMEFRAMES"):WORKER.find("});", WORKER.find("TIMEFRAMES"))]))
check("P06", "timeframe options and the county list match the Worker", wt == dict(M.TIMEFRAMES) and
      all("'%s'" % c in WORKER for c in M.COUNTIES) and WORKER.count("'Wicklow'") == 1)
wsup = re.search(r"export const INTRO_SUPPLIERS = Object\.freeze\((\{.*?\})\);", WORKER, re.S).group(1)
check("P07", "suppliers with a written agreement: the page config and the Worker allow-list agree (both empty today)",
      set(cfg["suppliers"]) == set(re.findall(r"'([a-z0-9-]+)':\s*\{", wsup)) and cfg["suppliers"] == {})

# ------------------------------------------------------------------ the block, switch forced on in memory
sup_p = [p for p in cfg["placements"] if p["page_type"] == "supplier"]
gen = {p["page"]: blk(preview(p)) for p in cfg["placements"]}
check("P08", "forced on, every placement gets exactly one block, before </main>, and removing it restores the page exactly",
      all(preview(p).count(M.START) == 1 and preview(p).find(M.END) < preview(p).find("</main>") and
          M.FENCE_RE.sub("", preview(p)) == (ROOT / p["page"]).read_text(encoding="utf-8") for p in cfg["placements"]))
check("P09", "with no agreement on file, supplier pages show the GENERAL form, never the named sentence",
      all('data-kind="general"' in gen[p["page"]] and "share my enquiry and contact details with" not in gen[p["page"]] for p in sup_p))
named = blk(preview(sup_p[0], {sup_p[0]["supplier"]: {"name": "NOOK Prefab", "agreement": "x"}}))
check("P10", "with an agreement, the supplier page shows the approved sentence naming that supplier, and kind=supplier",
      'data-kind="supplier"' in named and M.supplier_consent("NOOK Prefab") in named and 'data-supplier="nook-prefab"' in named)
fields = lambda b: sorted(set(re.findall(r'name="([a-z_]+)"', b)))
check("P11", "fields: name, email, county, timeframe, optional description, consent, honeypot; no phone, Eircode or address",
      all(fields(b) == sorted(["name", "email", "county", "timeframe", "description", "consent", "company_website"]) for b in gen.values()) and
      not any(re.search(r"phone|tel\b|type=\"tel\"|eircode|address", b.split("<script")[0], re.I) for b in gen.values()),
      fields(next(iter(gen.values()))))
check("P12", "nothing is preselected: no checked or selected attribute, and the description is marked optional",
      all(not re.search(r"\schecked|\sselected", b) and "(optional)" in b and 'name="description" maxlength="1000"' in b and
          'textarea name="description" maxlength="1000" placeholder' in b and "required" not in b.split('name="description"')[1].split(">")[0] for b in gen.values()))
check("P13", "no bundled marketing permission: one consent box only, and no newsletter or marketing wording",
      all(b.count('type="checkbox"') == 1 and not re.search(r"newsletter|marketing|offers|updates from", b, re.I) for b in gen.values()))
check("P14", "the referral-fee disclosure appears verbatim beside every form, with the privacy link",
      all(M.DISCLOSURE in b and 'href="/privacy.html#introductions"' in b for b in gen.values()))
check("P15", "the primary action reads 'Request an introduction' and expands in place (no pop-up, dialog or new window)",
      all(">Request an introduction <span" in b and not re.search(r"<dialog|window\.open|alert\(|confirm\(|modal", b) for b in gen.values()))
check("P16", "no navigation is added: the block contains no <nav> and no link other than the privacy notice",
      all("<nav" not in b and re.findall(r'href="([^"]+)"', b) == ["/privacy.html#introductions"] for b in gen.values()))
js = M.JS
check("P17", "analytics: events fire only with Cookiebot statistics consent and carry kind, page type and supplier slug only",
      "Cookiebot.consent.statistics" in js and re.findall(r"p=\{([^}]*)\}", js) == ["intro_kind:kind,page_type:pt"] and
      "p.supplier=sup" in js and not re.search(r"gtag\([^)]*(email|name|county|description)", js))
payload = set(re.findall(r"([a-z_]+):", js[js.find("var body={"):js.find("};", js.find("var body={"))]))
allowed = set(re.findall(r"'([a-z_]+)'", WORKER[WORKER.find("const ALLOWED"):WORKER.find("];", WORKER.find("const ALLOWED"))]))
check("P18", "the page payload is a subset of the Worker's closed payload", payload and payload <= allowed, payload - allowed)
check("P19", "success is shown only for a reply carrying ok, state 'received' and a reference",
      "j.ok===true&&j.state==='received'&&j.reference" in js)
check("P20", "the failure message says nothing was recorded and keeps what the homeowner typed (no reset)",
      "nothing was recorded" in js and ".reset(" not in js)
check("P21", "apply() is idempotent", all(M.apply(preview(p), p["page"], cfg, force=True) == preview(p) for p in cfg["placements"]))
check("P22", "the three supplier builders route their output through apply() for their own page",
      all('_pni.apply(' in (ROOT / "supplier-preview-system" / f).read_text() and
          ('"suppliers/%s.html"' % f[6:-12]) in (ROOT / "supplier-preview-system" / f).read_text()
          for f in ("build-nook-prefab-showcase.py", "build-the-pod-factory-showcase.py", "build-arctic-wellness-showcase.py")))

# ------------------------------------------------------------------ planted faults
bad = copy.deepcopy(cfg); bad["suppliers"] = {"nook-prefab": {"name": "NOOK Prefab"}}
check("P23", "planted: a supplier added without a written-agreement reference is refused", any("agreement" in e for e in M.validate(bad)))
bad = copy.deepcopy(cfg); bad["endpoint"] = "http://x.example/v1/introduction"
check("P24", "planted: a non-https endpoint is refused", any("https" in e for e in M.validate(bad)))
b0 = gen[cfg["placements"][0]["page"]]
check("P25", "planted: a preselected consent box would be caught by P12's test",
      bool(re.search(r"\schecked", b0.replace('type="checkbox" name="consent"', 'type="checkbox" name="consent" checked'))))
check("P26", "planted: a phone field would be caught by P11's test",
      fields(b0.replace('<label>Email', '<label>Phone<input type="tel" name="phone"></label><label>Email')) != fields(b0))

fail = results.count(False)
print("\nINTRODUCTION PAGES · %d checks, %d passed, %d failed" % (len(results), len(results) - fail, fail))
sys.exit(1 if fail else 0)
