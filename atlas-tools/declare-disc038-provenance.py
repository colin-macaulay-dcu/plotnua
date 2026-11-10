#!/usr/bin/env python3
"""DISC-038 · declare the chapter 02 section illustration in image-provenance-records.json (Stage 4, 8 Nov 2026).

The hero pair is declared by atlas-tools/build-disc038-images.py (from C2PA). This script declares the other DISC-038 image:
the vector section drawing written as code by Claude (atlas-tools/build-disc038-section-illustration.py), the Stage 3
interim hero, kept in chapter 02 on the founder's instruction. It is classed AI_ILLUSTRATION, following the GridNua
precedent. It also withdraws the Stage 3 records for the two drawing masters that are no longer on the page
(DISC-038-BEFORE-MASTER.png, DISC-038-POSSIBLE-MASTER.png) and every derivative of them.

HUMAN REVIEW: the founder's own confirmation, Stage 5 private-preview approval (10 Nov 2026), quoted verbatim, given after
he saw the drawing in the Stage 3 and Stage 4 screenshots. It supersedes the Stage 4 placeholder that quoted his "retain it"
instruction.

  python3 atlas-tools/declare-disc038-provenance.py
"""
import hashlib, json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, 'image-provenance-records.json')
D = 'assets/disc038/img/'
TODAY = '2026-11-08'
VERIFY = 'atlas-tools/build-disc038-section-illustration.py (deterministic rebuild)'
OLD = {D + 'DISC-038-BEFORE-MASTER.png', D + 'DISC-038-POSSIBLE-MASTER.png'}
M = D + 'DISC-038-SECTION-MASTER.png'


def facts(rel):
    p = os.path.join(ROOT, rel)
    b = open(p, 'rb').read()
    return hashlib.sha256(b).hexdigest(), len(b), list(Image.open(p).size)


reg = json.load(open(REG))
reg['records'] = [r for r in reg['records'] if r['asset'] not in OLD and r['asset'] != M]
reg['derivatives'] = [d for d in reg['derivatives'] if d['derived_from']['asset'] not in OLD and d['derived_from']['asset'] != M]

sha, n, px = facts(M)
reg['records'].append({
    'asset': M, 'sha256': sha, 'bytes': n, 'pixels': px,
    'class': 'AI_ILLUSTRATION',
    'what': 'DISC-038 chapter 02 section illustration: a vector section through a generic two-storey Irish house and back garden at dusk, '
            'with a generic family shelter under the lawn (entrance stair, living and kitchen, bunks, shower and WC, plant room with filter, '
            'batteries and tanks, air intake, escape hatch), labelled. Not to scale; no real product or installation.',
    'generated': {
        'tool': 'Claude (Anthropic), in a PlotNua Claude session: the SVG was written as code by the model '
                '(atlas-tools/build-disc038-section-illustration.py) and rasterised with rsvg-convert. No image-generation service, no raster model.',
        'date': TODAY,
    },
    'prompt': ('Founder brief, Stage 3, 8 Nov 2026 (hero, verbatim extract): "BEFORE is an ordinary contemporary Irish home and garden. '
               'POSSIBLE is the same view with a discreet, engineered underground shelter entrance, open, giving a glimpse of a spacious modern '
               'underground living environment." The drawing is a section through a generic house and garden with a generic shelter under the lawn. '
               'No image-generation service and no reference images: every shape is drawn by the script.'),
    'reference_inputs': [],
    'depicts_named_product': False,
    'depicts_named_organisation': False,
    'human_review': {
        'reviewer': 'Colin MacAulay (founder)',
        'date': '2026-11-10',
        'attests': ('Founder Stage 5 private-preview approval, 10 Nov 2026, after reviewing the drawing in the Stage 3 and Stage 4 screenshots, '
                    'verbatim: "Record the founder\'s confirmation that the Chapter 02 section drawing is illustrative and does not depict a '
                    'verified real product or installation." Private preview only; publication awaits the founder\'s release approval.'),
    },
    'label_on_page': 'Caption: AI-generated illustration (vector drawing made with Claude). Not to scale; not a specific product or installation.',
    'permitted_surfaces': ['discovery'],
    'status_note': 'DISC-038 private preview only (branch dev/disc038-hidden-shelter). Stage 3 interim hero; chapter 02 illustration since Stage 4.',
})
outs = [(f'DISC-038-SECTION-{w}.webp', 'optimise', f'Lanczos resize to {w} px wide (whole image, aspect kept)', 'Pillow, WebP quality 86, method 6') for w in (768, 1024, 1376, 1536)]
outs.append(('DISC-038-SECTION-1024.jpg', 'optimise', 'Lanczos resize to 1024 px wide (whole image, aspect kept)', 'Pillow, JPEG quality 86, progressive'))
for fn, method, op, enc in outs:
    rel = D + fn
    dsha, dn, dpx = facts(rel)
    reg['derivatives'] = [d for d in reg['derivatives'] if d['asset'] != rel]
    reg['derivatives'].append({
        'asset': rel, 'sha256': dsha, 'bytes': dn, 'pixels': dpx,
        'derived_from': {'asset': M, 'sha256': sha},
        'method': method,
        'edit': {'description': f'DISC-038 web copy (Governance 2.0, Rule 3): {op}.', 'operation': op, 'verified_by': VERIFY},
        'encoder': enc, 'made': TODAY,
        'content_credentials': {'source_file_embeds_c2pa': False, 'derivative_embeds_c2pa': False,
                                'note': 'Neither the master nor this copy carries a C2PA credential: the drawing was made as code, not by an image-generation service. Its record carries the AI classification.'},
    })

with open(REG, 'w') as f:
    json.dump(reg, f, indent=2, ensure_ascii=False)
    f.write('\n')
print('declared the section illustration (1 record, %d derivatives); withdrew the Stage 3 drawing masters' % len(outs))
