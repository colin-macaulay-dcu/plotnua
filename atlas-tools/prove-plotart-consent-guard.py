#!/usr/bin/env python3
"""Proof that launch-guard rule L23 protects the consent architecture of 27 Nov 2026 (self-hosted consent module, no
Cookiebot), rather than accepting whatever the current files say.

Each fault is planted in an isolated copy of the site. Where a fault changes pages, the copy's manifest is re-pinned to the
faulty pages first, so the manifest rule (L3) cannot be what refuses it: the guard must refuse it under L23. Faults that
change the shared head constant are applied to every page as well, so only the fixed expectations of L23 can catch them.

  python3 atlas-tools/prove-plotart-consent-guard.py [ROOT]"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("" if ok else "  [" + detail[-300:] + "]"))


def copy_site(tmp):
    site = os.path.join(tmp, "site")
    os.mkdir(site)
    for name in os.listdir(ROOT):
        if name in (".git", ".openai"):
            continue
        src = os.path.join(ROOT, name)
        if name in ("plotart", "atlas-tools"):
            shutil.copytree(src, os.path.join(site, name), symlinks=True)
        elif name == "assets":
            os.mkdir(os.path.join(site, "assets"))
            for a in os.listdir(src):
                (shutil.copytree if a == "consent" else os.symlink)(os.path.join(src, a), os.path.join(site, "assets", a))
        else:
            os.symlink(src, os.path.join(site, name))
    return site


def pages(site):
    for d, _, fs in os.walk(os.path.join(site, "plotart")):
        for f in fs:
            if f.endswith(".html"):
                yield os.path.join(d, f)


def edit(path, old, new, count=1):
    s = open(path, encoding="utf-8").read()
    if old not in s:
        raise SystemExit("fixture text not found in %s: %r" % (path, old[:80]))
    open(path, "w", encoding="utf-8").write(s.replace(old, new, count))


def edit_all_pages(site, old, new):
    n = 0
    for p in pages(site):
        s = open(p, encoding="utf-8").read()
        if old in s:
            open(p, "w", encoding="utf-8").write(s.replace(old, new)); n += 1
    return n


def guard(site, repin):
    if repin:
        subprocess.run([sys.executable, os.path.join(site, "atlas-tools/release/plotart-repin-manifest.py"), site, "consent guard proof"],
                       capture_output=True, text=True, check=True)
    r = subprocess.run([sys.executable, os.path.join(site, "atlas-tools/prove-plotart-launch.py"), site,
                        "--switches", os.path.join(site, "atlas-tools/release/plotart-launch-switches.json"),
                        "--manifest", os.path.join(site, "atlas-tools/release/plotart-launch-manifest.json")], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


CONSENT_PY = "atlas-tools/seo_pn_analytics.py"
MOD = "assets/consent/site-consent.js"
GALLERY = "plotart/gallery/index.html"
COOKIEBOT = '<script id="Cookiebot" src="https://consent.cookiebot.com/uc.js" data-cbid="b8abbc45-15b0-4d27-8f95-83ebd240a305" data-blockingmode="auto"></script>\n'
GTAG = '<script async src="https://www.googletagmanager.com/gtag/js?id=G-PKKJ0RK6N8"></script>'


def fault_page_cookiebot(site):
    edit(os.path.join(site, GALLERY), "</head>", COOKIEBOT + "</head>")
def fault_page_gtag(site):
    edit(os.path.join(site, GALLERY), "</main>", GTAG + "</main>")
def fault_page_no_block(site):
    edit(os.path.join(site, GALLERY), '<script src="/assets/consent/site-consent.js', '<script data-x src="/assets/consent/site-consent.js')
def fault_defaults_granted(site):
    edit(os.path.join(site, CONSENT_PY), "analytics_storage: 'denied'", "analytics_storage: 'granted'")
    edit_all_pages(site, "analytics_storage: 'denied', functionality_storage", "analytics_storage: 'granted', functionality_storage")
def fault_wrong_property(site):
    edit(os.path.join(site, "atlas-tools/seo_pn_consent.py"), 'data-ga="G-PKKJ0RK6N8"', 'data-ga="G-ATTACKER01"')
    edit_all_pages(site, 'data-ga="G-PKKJ0RK6N8"', 'data-ga="G-ATTACKER01"')
def fault_cookiebot_restored(site):
    edit(os.path.join(site, "atlas-tools/seo_pn_consent.py"), "MODULE = ('", "MODULE = ('" + COOKIEBOT.replace("\n", "\\n").replace("'", "\\'") + "' + '")
    edit_all_pages(site, '<link rel="stylesheet" href="/assets/consent/site-consent.css', COOKIEBOT + '<link rel="stylesheet" href="/assets/consent/site-consent.css')
def fault_module_loads_at_start(site):
    edit(os.path.join(site, MOD), "apply(choice ? choice.statistics : null);", "apply(choice ? choice.statistics : null); loadAnalytics();")
def fault_module_ad_signals(site):
    edit(os.path.join(site, MOD), "w.gtag('consent', 'update', { analytics_storage: 'granted' });", "w.gtag('consent', 'update', { analytics_storage: 'granted', ad_storage: 'granted' });")
def fault_module_google_signals(site):
    edit(os.path.join(site, MOD), "allow_google_signals: false", "allow_google_signals: true")
def fault_module_keeps_cookies(site):
    edit(os.path.join(site, MOD), "if (!choice) stopAnalytics();", "")
def fault_module_second_google_script(site):
    edit(os.path.join(site, MOD), "  function stopAnalytics() {", "  var t = d.createElement('script'); t.src = 'https://www.googletagmanager.com/gtm.js?id=GTM-X'; d.head.appendChild(t);\n  function stopAnalytics() {")


FAULTS = [
    ("a Cookiebot script added to one page", fault_page_cookiebot, True, "must carry exactly the approved consent"),
    ("a Google tag script added to one page's body", fault_page_gtag, True, "must carry exactly the approved consent"),
    ("the consent block altered on one page", fault_page_no_block, True, "must carry exactly the approved consent"),
    ("analytics granted by default (constant and every page)", fault_defaults_granted, True, "L23 the consent defaults must come first"),
    ("a different Google Analytics property (constant and every page)", fault_wrong_property, True, "L23 the analytics block must be the approved one"),
    ("Cookiebot restored in the shared block (constant and every page)", fault_cookiebot_restored, True, "L23 the analytics block must be the approved one"),
    ("the module loads Google Analytics before any choice", fault_module_loads_at_start, False, "L23 the consent module"),
    ("the module grants an advertising signal on Accept", fault_module_ad_signals, False, "L23 the consent module"),
    ("the module turns Google signals on", fault_module_google_signals, False, "L23 the consent module"),
    ("the module stops clearing analytics cookies without consent", fault_module_keeps_cookies, False, "L23 the consent module"),
    ("the module loads a second Google script", fault_module_second_google_script, False, "L23 the consent module"),
]

print("PROVE · L23 consent guard against planted faults")
with tempfile.TemporaryDirectory(prefix="pa-consent-guard-") as tmp:
    site = copy_site(os.path.join(tmp))
    code, out = guard(site, False)
    check("control: the untouched copy passes the launch guard", code == 0, out)
for label, fault, repin, want in FAULTS:
    with tempfile.TemporaryDirectory(prefix="pa-consent-guard-") as tmp:
        site = copy_site(tmp)
        fault(site)
        code, out = guard(site, repin)
        l3 = [l for l in out.splitlines() if l.strip().startswith("L3 ")]
        check("refused under L23: " + label, code != 0 and want in out and not l3, out)
print("PLOTART CONSENT GUARD · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
