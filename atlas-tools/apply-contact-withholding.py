#!/usr/bin/env python3
"""Apply .github/scripts/contact_redaction.py to the published research data files, in place (27 Nov 2026), exactly as
the generators now write them: every string that quotes a telephone number or email address keeps its sentence with
the detail replaced by "[phone number withheld]" / "[email address withheld]". Formatting elsewhere is unchanged, and
each file must parse to exactly redact_tree(original) or nothing is written. --check reports only."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, '.github', 'scripts'))
from contact_redaction import redact, redact_tree, found  # noqa: E402
FILES = ['garden-room-recommendation-universe-v1.json', 'garden-room-detail-evidence-v1.json', 'garden-room-detail-suppliers-v1.json',
         'garden-room-detail-considerations-v1.json', 'garden-room-detail-planningconsiderations-v1.json', 'garden-room-detail-sources-v1.json',
         'additional-home-universe-v1.json', 'recommendation-universe-v1.json']
apply, total = '--apply' in sys.argv, 0
for f in FILES:
    p = os.path.join(ROOT, f); s = open(p, encoding='utf-8').read(); n = [0]
    def lit(m):
        raw = m.group(0); v = json.loads(raw)
        if not found(v): return raw
        n[0] += 1
        return json.dumps(redact(v), ensure_ascii='\\u' in raw)
    out = re.sub(r'"(?:[^"\\]|\\.)*"', lit, s)
    if json.loads(out) != redact_tree(json.loads(s)):
        sys.exit('REFUSED %s: the in-place edit is not exactly the declared change' % f)
    total += n[0]; print('%-50s %d string(s)' % (f, n[0]))
    if apply and out != s: open(p, 'w', encoding='utf-8').write(out)
print('CONTACT WITHHOLDING · %d string(s) %s' % (total, 'withheld' if apply else 'to withhold'))
