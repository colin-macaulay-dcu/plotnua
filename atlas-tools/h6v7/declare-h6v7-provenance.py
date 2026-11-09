#!/usr/bin/env python3
"""Apply founder decision PN-FDR-2026-11-09-H6V7-HOME (provenance Option A) to image-provenance-records.json:
  1. add one founder-attested AI_ILLUSTRATION record per H6 v7 file served by the homepage hero (hashed from disk);
  2. retire the 22 records of the evening H6 image set the homepage no longer references (P9).
Refuses if a file's hash is not pinned in validate-image-provenance.js, or if already applied."""
import json, hashlib, os, sys, re
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(ROOT, 'image-provenance-records.json')
VAL = open(os.path.join(ROOT, 'atlas-tools/validate-image-provenance.js'), encoding='utf-8').read()
DEC = 'PN-FDR-2026-11-09-H6V7-HOME'
d = json.load(open(REG, encoding='utf-8'))
if any(DEC in json.dumps(r) for r in d['records']): sys.exit('REFUSED: already applied')
pinned = set(re.findall(r"'([0-9a-f]{64})',\s*// H6v7-", VAL))
img = os.path.join(ROOT, 'assets/h6/img')
files = sorted(f for f in os.listdir(img) if f.startswith('H6v7-'))
WHAT = {
 'before': 'H6 v7 BEFORE: a cream two-storey Irish house with a patio, one open lawn, a stone path through foxgloves and ferns, a mature tree and clipped hedges under a cloudy daylight sky (the hero photograph)',
 'layer': 'H6 v7 discovery layer: POSSIBLE pixels with a transparency matte over the BEFORE master',
 'sky': 'H6 v7 sky band: the BEFORE sky, its clouds rearranged into the words, and the two data maps that drive the cloud animation',
 'water': 'H6 v7 water texture: the POSSIBLE pool or hot-tub water, cropped for the ripple canvas',
 'device': 'H6 v7 Power Station heat-pump unit: pixels from the approved H6 evening base (PN-FDR-2026-10-26-H6-HOME), re-graded to daylight',
}
new = []
for f in files:
    p = os.path.join(img, f); b = open(p, 'rb').read(); h = hashlib.sha256(b).hexdigest()
    if h not in pinned: sys.exit('REFUSED: %s (%s) is not pinned under %s' % (f, h[:12], DEC))
    kind = f.split('-')[1]
    try: px = list(Image.open(p).size)
    except Exception: px = None
    what = WHAT.get(kind, WHAT['layer'])
    if kind == 'layer': what += ' (' + f[len('H6v7-layer-'):].rsplit('-', 1)[0].replace('-', ' ') + ')'
    new.append({
        'asset': 'assets/h6/img/' + f, 'sha256': h, 'bytes': len(b), 'pixels': px, 'class': 'AI_ILLUSTRATION', 'what': what,
        'depicts_named_product': False, 'depicts_named_organisation': False,
        'generated': {'tool': 'OpenAI ChatGPT image generation (gpt-image), per the masters\' own signed C2PA credentials; then PlotNua deterministic build tools (atlas-tools/h6v7/pipeline), no generative fill',
                      'date': '2026-11-08',
                      'source_masters': [{'role': 'BEFORE', 'sha256': '373b6805b127067454422bcd3140fdb7242a4403ac8f6403ca132a2df91d23b3', 'pixels': [1670, 942], 'c2pa_created': '2026-11-08T20:10:23Z'},
                                         {'role': 'POSSIBLE', 'sha256': '8af0550f814df72ef78bd4bbc94df27e1648843e0158701250e81f772c642e7e', 'pixels': [1670, 941], 'c2pa_created': '2026-11-08T20:04:37Z'}]},
        'decision_ref': DEC + ' (governance/PN-FDR-2026-11-09-H6V7-HOME.md)',
        'prompt_status': 'UNAVAILABLE',
        'reference_disclosure': {'status': 'UNCERTAIN',
            'statement': 'The masters\' credentials record no input image; the ChatGPT conversation context is not recorded, so inputs cannot be ruled out. reference_inputs is therefore not recorded.',
            'evidence': 'Embedded C2PA manifests of the two masters (read from the file bytes, 9 Nov 2026); governance/H6V7-PROVENANCE-DECLARATION-DRAFT-2026-11-09.json'},
        'resemblance_review': {'date': '2026-11-09', 'reviewed_by': 'PlotNua build session (full-resolution review of every state)',
            'compared_against': 'the two masters and the approved H6 evening set',
            'verdict': 'Accepted by the founder: generic garden structures (treehouse, curved garden pod, sauna, wood-fired hot tub, natural swimming pool, rooftop PV); no supplier product, logo or organisation is identifiable or named.',
            'findings': ['No brand marks, logos or text on any structure.', 'No supplier credit is shown or implied; no licensed supplier photograph is used in v7.']},
        'human_review': {'reviewer': 'Colin MacAulay (founder)', 'date': '2026-11-09',
            'attests': 'Founder approved the H6 v7 daylight homepage hero for production on 9 Nov 2026 under provenance Option A. AI-generated illustration, labelled as such; not presented as a photograph of a real property or any supplier\'s product. Prompts unavailable; recorded without inventing facts.'},
        'permitted_surfaces': ['homepage'],
        'content_credentials': {'embeds_c2pa': False, 'note': 'The PNG masters carry OpenAI C2PA credentials; masking and web re-encoding remove them.'},
        'introduced': {'date': '2026-11-09', 'subject': 'H6 v7 daylight homepage hero (founder production approval)'}})
old = [r for r in d['records'] if r['asset'].startswith('assets/h6/img/H6-')]
if len(old) != 22: sys.exit('REFUSED: expected 22 evening H6 records, found %d' % len(old))
d['records'] = [r for r in d['records'] if not r['asset'].startswith('assets/h6/img/H6-')] + new
open(REG, 'w', encoding='utf-8').write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
print('added %d H6 v7 records, retired %d evening H6 records' % (len(new), len(old)))
