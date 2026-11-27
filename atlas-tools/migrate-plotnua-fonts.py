#!/usr/bin/env python3
"""Apply the PlotNua self-hosted fonts change (seo_pn_fonts.py) once: every public PlotNua page, the two stylesheets
that @import Google Fonts, and the JSON-escaped pinned snapshots. --check reports only. Refuses on any unexpected shape."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_pn_fonts as F
ROOT = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()
apply = '--apply' in sys.argv
ls = lambda pat: subprocess.run(['git', 'ls-files', pat], capture_output=True, text=True, cwd=ROOT).stdout.splitlines()
changed, refused = [], []
SKIP = ('atlas-tools/', 'governance/', 'supplier-preview-system/', 'commercial/', 'worker/', '.github/')
for f in [x for x in ls('*.html') + ls('*.css') if not x.startswith(SKIP)] + ls('atlas-tools/premium-discovery/*.json'):
    p = os.path.join(ROOT, f); t = open(p, encoding='utf-8').read()
    if 'fonts.googleapis.com' not in t and 'fonts.gstatic.com' not in t:
        continue
    try:
        n = F.transform(t) if f.endswith('.html') else F.css_transform(t) if f.endswith('.css') else F.json_transform(t)
    except ValueError as e:
        refused.append(f'{f}: {e}'); continue
    if n != t:
        changed.append(f)
        if apply: open(p, 'w', encoding='utf-8').write(n)
print(json.dumps({'mode': 'apply' if apply else 'check', 'changed': len(changed), 'by_type': {e: sum(x.endswith(e) for x in changed) for e in ('.html', '.css', '.json')}, 'refused': refused}, indent=1))
sys.exit(1 if refused else 0)
