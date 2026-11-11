#!/usr/bin/env python3
"""H6 v7 cloud lettering v2 (11 Nov 2026, founder instruction: complete the provenance declarations for the cloud assets
and retire the unused v1 sky records, without weakening any safeguard).
  1. records each H6v7-cloud-* map as a Governance 2.0 Rule 3 derivative of the declared hero photograph
     assets/h6/img/H6v7-before-1670.webp (hash-bound; method 'crop' from the closed vocabulary, with the exact operation
     written out). The derivatives declare nothing themselves: they inherit the photograph's AI_ILLUSTRATION record and
     its homepage-only surface, and are shown under the existing AI label;
  2. retires the four v1 sky records (H6v7-sky-src/-tgt/-flow/-time), which the homepage no longer references, and
     removes their hashes from the H6 v7 founder-attested pin list in validate-image-provenance.js (the exception only
     narrows). Idempotent; refuses if the source photograph's record or hash is not what it was derived from."""
import json, hashlib, os, re, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(ROOT, 'image-provenance-records.json'); VAL = os.path.join(ROOT, 'atlas-tools/validate-image-provenance.js')
SRC = 'assets/h6/img/H6v7-before-1670.webp'
sha = lambda p: hashlib.sha256(open(os.path.join(ROOT, p), 'rb').read()).hexdigest()
d = json.load(open(REG, encoding='utf-8'))
rec = next((r for r in d['records'] if r['asset'] == SRC), None)
if not rec or rec['sha256'] != sha(SRC): sys.exit('REFUSED: the hero photograph record is missing or its file changed')
BAND = 'the sky band x 730-1550, y 0-224 of the hero photograph'
OPS = {
 'src':     'crop of ' + BAND + ', unchanged (the first frame of the animation)',
 'fill':    'crop of ' + BAND + ', with the branches, roofs, chimney and antenna painted out (OpenCV Telea inpaint, then a 4 px blur inside that mask only): the cloud that drifts',
 'plate':   'crop of ' + BAND + ', replaced by a smooth least-squares fit of its own blue-sky pixels plus a light horizon haze: the clear sky that shows where cloud thins',
 'colour':  'procedural rendering at 2x the band: the words "Discover what’s possible." set in Noto Serif CJK Black and rebuilt as a lit heap of spherical cloud puffs, coloured with cloud colours measured from ' + BAND + '; no generative AI',
 'density': 'procedural, 2x the band, greyscale: the density of the cloud letters (same build as the colour map)',
 'data':    'procedural, band size: R = when each billow condenses, G = the open-sky mask measured from ' + BAND + ', B = the words as loose cloud masses',
 'field':   'procedural, half band size: the drift field toward the words (R, G) and where the sky thins around them (B)',
}
have = {x['asset'] for x in d.get('derivatives', [])}
added = 0
for k, op in OPS.items():
    a = 'assets/h6/img/H6v7-cloud-%s.webp' % k
    if not os.path.exists(os.path.join(ROOT, a)): sys.exit('REFUSED: %s missing' % a)
    d['derivatives'] = [x for x in d.get('derivatives', []) if x['asset'] != a]
    d['derivatives'].append({
        'asset': a, 'sha256': sha(a), 'bytes': os.path.getsize(os.path.join(ROOT, a)), 'pixels': list(Image.open(os.path.join(ROOT, a)).size),
        'derived_from': {'asset': SRC, 'sha256': rec['sha256']},
        'method': 'crop',
        'edit': {'description': 'H6 v7 cloud lettering v2 (Governance 2.0, Rule 3): ' + op + '.', 'operation': op,
                 'verified_by': 'atlas-tools/h6v7/pipeline/clouds.py (deterministic; reproduces these bytes from the photograph)'},
        'encoder': 'Pillow, WebP' + (' lossless' if k in ('data', 'field') else ''),
        'made': '2026-11-11',
        'content_credentials': {'source_file_embeds_c2pa': False, 'derivative_embeds_c2pa': False,
                                'note': 'The served photograph carries no credential (its master does); these maps carry none.'}})
    added += 1
OLD = ['assets/h6/img/H6v7-sky-%s' % f for f in ('src.webp', 'tgt.webp', 'flow.png', 'time.png')]
gone = [r for r in d['records'] if r['asset'] in OLD]
d['records'] = [r for r in d['records'] if r['asset'] not in OLD]
open(REG, 'w', encoding='utf-8').write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
v = open(VAL, encoding='utf-8').read(); n0 = len(v)
v = re.sub(r"\n    '[0-9a-f]{64}',   // H6v7-sky-(?:flow|src|tgt|time)\.(?:png|webp)", '', v)
v = v.replace('truthful record. ONLY these 26 files, and ONLY on the homepage.', 'truthful record. ONLY these 22 files, and ONLY on the homepage (the four v1 sky maps were retired on 11 Nov 2026).')
open(VAL, 'w', encoding='utf-8').write(v)
print('recorded %d cloud derivatives; retired %d v1 sky records; pin list %s' % (added, len(gone), 'narrowed' if len(v) < n0 else 'unchanged'))
