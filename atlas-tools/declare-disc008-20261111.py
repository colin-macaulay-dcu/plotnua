"""Declare founder-approved DISC-008 imagery from this generation session."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = {
    'POSSIBLE': 'Create one highly photorealistic architectural editorial photograph, wide landscape 16:9, for an Irish contemporary garden room website hero. Real suburban South Dublin back garden, generous but believable 11m wide x 22m deep, viewed from the rear patio of the main home at human eye level 1.5m, looking towards the end of the garden. Hero subject at rear centre-right is a beautifully designed single-storey modest contemporary garden living studio about 6m wide, low flat roof, dark charcoal vertical timber cladding, slim anthracite aluminium full-height sliding glass, softly warm interior showing a comfortable low modern grey sofa, one olive armchair, books and an understated floor lamp. No people. Studio is about 35 percent of frame width and clearly visible, architectural quality without being a mansion. A small weathered limestone terrace immediately outside studio, simple stepping stone route across natural slightly uneven lawn. Authentic mature Irish planting, ferns grasses hydrangeas, one airy multistem tree on left, established hedges above modest rendered boundary walls, slight glimpse of real neighbouring Irish rooflines. Soft late afternoon daylight after rain, pale textured overcast sky, no orange sunset. Restrained palette anthracite warm oak green. Lived in, relaxed, aspirational but ordinary enough to believe, no staged symmetry, no excessive decor, no fairy lights. Accurate construction, straight glazing, subtle glass reflections, believable textures and imperfections, natural camera optics 35mm, no CGI smoothness, no illustration, no text, no logo. Leave foreground lawn sufficiently open so this exact scene can subsequently be edited to remove only the garden room and its immediate terrace to create a matching before photograph.',
    'BEFORE': 'Edit this exact image to create the BEFORE member of a before-and-after website slider. Keep exact canvas dimensions, camera, crop, perspective, lighting, sky, trees, neighbouring rooflines, left and right boundary walls and all visible foreground lawn, stepping stones, patio furniture and planting absolutely unchanged. Remove ONLY the dark garden room building at the rear and its immediate small terrace and pots. Replace its footprint with ordinary natural lawn continuing the existing grass and reveal a believable plain weathered grey rendered rear boundary wall with an established green hedge behind, continuous with side boundaries. This is the identical real-looking Irish garden before any garden room was built. Do not redesign anything, do not shift objects, do not change colour grade or weather. Preserve all pixels outside the immediate removed-building region as closely as possible. No text no labels.'
}
def measure(asset):
    p = ROOT / asset
    return dict(asset=asset, sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size, pixels=list(Image.open(p).size))

path = ROOT / 'image-provenance-records.json'
data = json.loads(path.read_text())
for kind in ('POSSIBLE', 'BEFORE'):
    asset = f'assets/disc008/img/DISC-008-{kind}-20261111.webp'
    row = measure(asset)
    row.update({
        'class': 'AI_ILLUSTRATION',
        'what': f'Generic Irish garden {"with a contemporary charcoal-timber garden room" if kind == "POSSIBLE" else "before the garden room is added"}.',
        'generated': {'tool': 'OpenAI image_gen built-in image generation tool', 'date': '2026-11-11'},
        'prompt': PROMPTS[kind],
        'reference_inputs': [] if kind == 'POSSIBLE' else [{'asset': 'assets/disc008/img/DISC-008-POSSIBLE-20261111.webp', 'description': 'The generation original PNG of the POSSIBLE image was the sole edit target; this WebP is its whole-frame delivery master.'}],
        'depicts_named_product': False, 'depicts_named_organisation': False,
        'human_review': {'reviewer': 'Colin Macaulay (founder)', 'date': '2026-11-11', 'attests': 'Reviewed the two new generated images in this conversation and approved: yes much better - continue and publish.'},
        'permitted_surfaces': ['discovery', 'library-card'],
        'label_on_page': 'AI-generated illustration',
        'processing': 'Original generated PNG converted to RGB WebP quality 93 without cropping or retouching; 1672 x 941 pixels retained.'
    })
    data['records'] = [r for r in data['records'] if r['asset'] != asset] + [row]
    for width in ([480, 960] if kind == 'POSSIBLE' else [960]):
        derivative = measure(f'assets/disc008/img/DISC-008-{kind}-{width}w-20261111.webp')
        derivative.update({'derived_from': {'asset': asset, 'sha256': row['sha256']}, 'method': 'webp-resize', 'encoder': 'Pillow, WebP quality 88, whole-frame proportional resize from generation PNG', 'made': '2026-11-11'})
        data['derivatives'] = [r for r in data['derivatives'] if r['asset'] != derivative['asset']] + [derivative]
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
