#!/usr/bin/env python3
"""Apply the PlotNua consent migration (seo_pn_consent.py) to the repository, once. Prepared 27 Nov 2026, NOT released.

  python3 atlas-tools/migrate-plotnua-consent.py --check   # report what would change, change nothing
  python3 atlas-tools/migrate-plotnua-consent.py --apply

Covers: every PlotNua page carrying the Cookiebot block (root, suppliers/, gridnua/), every PlotArt page on plotnua.ie
(plotart_shell.ANALYTICS_HEAD -> PLOTART_HEAD), the JSON-escaped pinned snapshots, thanks.html's generate_lead trigger,
and the Cookiebot cookie declaration on cookie-policy.html (replaced by a static declaration, see the policy draft).
Refuses (exit 1) on any page whose analytics block is not the declared shape, so nothing is changed by guesswork.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_pn_analytics as A
import seo_pn_consent as C
import plotart_shell as S

ROOT = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()
apply = '--apply' in sys.argv
OLD_PA_HEAD = S.ANALYTICS_HEAD if 'consent.cookiebot.com' in S.ANALYTICS_HEAD else None

LEAD_OLD = ("if(sent||typeof gtag!=='function'||!(window.Cookiebot&&Cookiebot.consent&&Cookiebot.consent.statistics))return;")
LEAD_NEW = ("if(sent||typeof gtag!=='function'||!(window.siteConsent&&siteConsent.statistics))return;")
LEAD_EVT_OLD = ("  window.addEventListener('CookiebotOnConsentReady',lead);\n  window.addEventListener('CookiebotOnAccept',lead);\n")
LEAD_EVT_NEW = ("  window.addEventListener('site-consent',lead);\n  lead();\n")


def files(pattern):
    return subprocess.run(['git', 'ls-files', pattern], capture_output=True, text=True, cwd=ROOT).stdout.splitlines()


changed, refused = [], []
for f in files('*.html'):
    p = os.path.join(ROOT, f)
    t = open(p, encoding='utf-8').read()
    n = t
    try:
        if f.startswith('plotart/'):
            if OLD_PA_HEAD and OLD_PA_HEAD in n:
                n = n.replace(OLD_PA_HEAD, C.PLOTART_HEAD)
        elif A.COOKIEBOT in n:
            n = C.transform(n)
        if f == 'thanks.html':
            if LEAD_OLD in n:
                n = n.replace(LEAD_OLD, LEAD_NEW)
            if LEAD_EVT_OLD in n:
                n = n.replace(LEAD_EVT_OLD, LEAD_EVT_NEW)
    except ValueError as e:
        refused.append(f'{f}: {e}')
        continue
    if n != t:
        changed.append(f)
        if apply:
            open(p, 'w', encoding='utf-8').write(n)
for f in files('*.json'):
    p = os.path.join(ROOT, f)
    t = open(p, encoding='utf-8').read()
    enc = lambda x: json.dumps(x, ensure_ascii=False)[1:-1]
    if enc(A.COOKIEBOT) not in t:
        continue
    try:
        n = C.json_transform(t)
        json.loads(n)
    except Exception as e:
        refused.append(f'{f}: {e}')
        continue
    if n != t:
        changed.append(f)
        if apply:
            open(p, 'w', encoding='utf-8').write(n)

# what is left anywhere public that still mentions Cookiebot in code (comments and policy text are reported, not refused)
left = []
for f in files('*.html') + files('*.js'):
    if f.startswith(('atlas-tools/', 'worker/', 'governance/', 'commercial/', 'supplier-preview-system/', '.github/')):
        continue
    t = open(os.path.join(ROOT, f), encoding='utf-8', errors='ignore').read()
    if apply and f in changed:
        pass
    for m in re.finditer(r'consent\.cookiebot\.com|Cookiebot\.consent|CookiebotOn[A-Za-z]+', t):
        left.append(f'{f}: {m.group(0)}')
print(json.dumps({'mode': 'apply' if apply else 'check', 'files_changed': len(changed),
                  'html': sum(1 for f in changed if f.endswith('.html')), 'json': sum(1 for f in changed if f.endswith('.json')),
                  'refused': refused, 'cookiebot_code_left': left[:40]}, indent=1))
sys.exit(1 if refused else 0)
