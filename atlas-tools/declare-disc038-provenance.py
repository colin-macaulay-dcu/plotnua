#!/usr/bin/env python3
"""DISC-038 · declare the interim hero drawing in image-provenance-records.json (private preview, 8 Nov 2026).

Two AI_ILLUSTRATION records (the BEFORE and POSSIBLE masters, written as code by Claude, the GridNua precedent) and
hash-bound derivatives for every web copy the page shows. Idempotent: removes any earlier DISC-038 entries first.

HUMAN REVIEW IS LEFT PENDING ON PURPOSE. The guard (P5) requires a named human review; no human has reviewed these
images yet, and the build session will not write one on the founder's behalf. Until the founder reviews them, P5
fails for these two records, by design: that failure is the stop-and-report.

  python3 atlas-tools/declare-disc038-provenance.py
"""
import hashlib, json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, 'image-provenance-records.json')
D = 'assets/disc038/img/'
TODAY = '2026-11-08'
VERIFY = 'atlas-tools/build-disc038-hero-illustration.py (deterministic rebuild)'


def facts(rel):
    p = os.path.join(ROOT, rel)
    b = open(p, 'rb').read()
    w, h = Image.open(p).size
    return hashlib.sha256(b).hexdigest(), len(b), [w, h]


BRIEF = ('Founder brief, Stage 3, 8 Nov 2026 (hero, verbatim extract): "BEFORE is an ordinary contemporary Irish home and '
         'garden. POSSIBLE is the same view with a discreet, engineered underground shelter entrance, open, giving a glimpse '
         'of a spacious modern underground living environment." Interim drawing: a section through a generic two-storey '
         'house and garden at dusk; POSSIBLE adds a generic shelter shell with stair and entry, living and kitchen, bunks, '
         'shower and WC, a plant room, an open entrance hatch, an air intake and an escape hatch, with labels. No image '
         'generation service and no reference images: every shape is drawn by the script.')

WHAT = {
    'BEFORE': 'DISC-038 hero, BEFORE side of the slider: a vector section drawing of a generic contemporary two-storey Irish house and back garden at dusk, with plain ground below the lawn.',
    'POSSIBLE': 'DISC-038 hero, POSSIBLE side of the slider: the same drawing and frame with a generic family shelter under the lawn (entrance stair, living and kitchen, bunks, shower and WC, plant room, air intake, escape hatch), labelled. Not to scale; no real product or installation.',
}

reg = json.load(open(REG))
reg['records'] = [r for r in reg['records'] if not r['asset'].startswith(D)]
reg['derivatives'] = [r for r in reg['derivatives'] if not r['asset'].startswith(D)]

for name in ('BEFORE', 'POSSIBLE'):
    m = D + f'DISC-038-{name}-MASTER.png'
    sha, n, px = facts(m)
    reg['records'].append({
        'asset': m, 'sha256': sha, 'bytes': n, 'pixels': px,
        'class': 'AI_ILLUSTRATION',
        'what': WHAT[name],
        'generated': {
            'tool': 'Claude (Anthropic), in a PlotNua Claude session: the SVG was written as code by the model '
                    '(atlas-tools/build-disc038-hero-illustration.py) and rasterised with rsvg-convert. No image-generation '
                    'service, no raster model.',
            'date': TODAY,
        },
        'prompt': BRIEF,
        'reference_inputs': [],
        'depicts_named_product': False,
        'depicts_named_organisation': False,
        'human_review': {
            'reviewer': None,
            'date': None,
            'attests': None,
            'status': 'PENDING FOUNDER REVIEW. Not reviewed by a human. The build session checked the drawing visually '
                      'for alignment and legibility only; that is not a human review and is not recorded as one.',
        },
        'label_on_page': 'Illustrative AI-generated visualisation. Not an actual installation. A vector drawing made with '
                         'Claude for PlotNua; not to scale and not a specific product.',
        'permitted_surfaces': ['discovery'],
        'status_note': 'DISC-038 private preview only (branch dev/disc038-hidden-shelter). Interim drawing; to be replaced '
                       'if the founder supplies a photographic AI hero pair.',
    })
    msha = sha
    outs = [(f'DISC-038-{name}-{w}.webp', 'optimise', f'Lanczos resize to {w} px wide (whole image, aspect kept)', 'Pillow, WebP quality 86, method 6') for w in (768, 1024, 1376, 1536)]
    outs.append((f'DISC-038-{name}-1024.jpg', 'optimise', 'Lanczos resize to 1024 px wide (whole image, aspect kept)', 'Pillow, JPEG quality 86, progressive'))
    outs.append((f'DISC-038-{name}-M-819.webp', 'crop', '4:5 phone window: crop x 1380-3018 of the 3072 master (x 690-1509 of the 1536 frame), full height, Lanczos resize to 819 x 1024; the same window for both views', 'Pillow, WebP quality 86, method 6'))
    if name == 'POSSIBLE':
        outs.append(('DISC-038-og-1200x630.jpg', 'crop', 'Lanczos resize to 1200 x 800, crop y 85-715 to 1200 x 630 (social card from the hero POSSIBLE)', 'Pillow, JPEG quality 86'))
    for fn, method, op, enc in outs:
        rel = D + fn
        sha, n, px = facts(rel)
        reg['derivatives'].append({
            'asset': rel, 'sha256': sha, 'bytes': n, 'pixels': px,
            'derived_from': {'asset': m, 'sha256': msha},
            'method': method,
            'edit': {'description': f'DISC-038 web copy (Governance 2.0, Rule 3): {op}.', 'operation': op, 'verified_by': VERIFY},
            'encoder': enc,
            'made': TODAY,
            'content_credentials': {'source_file_embeds_c2pa': False, 'derivative_embeds_c2pa': False,
                                    'note': 'Neither the master nor this copy carries a C2PA credential: the drawing was made as code, not by an image-generation service. Its record carries the AI classification.'},
        })

with open(REG, 'w') as f:
    json.dump(reg, f, indent=2, ensure_ascii=False)
    f.write('\n')
print('declared 2 records and', sum(1 for r in reg['derivatives'] if r['asset'].startswith(D)), 'derivatives')
