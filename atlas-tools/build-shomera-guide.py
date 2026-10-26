#!/usr/bin/env python3
"""One bounded Shomera guide, using the existing maker renderer.

Default builds the noindex review draft. --check is read-only. Production
publication requires its own approved register and source state; the original
two-guide approval is never expanded. No network, Atlas or permission writes.
"""
import datetime as dt
import importlib.util
import json
import re
import subprocess
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'atlas-tools/maker-pages'
PAGE = 'shomera-garden-rooms.html'
PROFILE = {
    'template': 'shomera.html',
    'title': 'Shomera Garden Rooms: Classic & Contemporary Compared | PlotNua',
    'h1': 'Shomera garden rooms',
    'description': 'Compare Shomera Classic and Contemporary garden studios: six published starting prices, installation scope, VAT questions and what to confirm for your garden.',
    'lead': 'Classic and Contemporary compared: published prices, installation scope and questions for your quotation.',
    'about': 'Shomera Classic and Contemporary garden studios',
}
MODELS = ('12', '21', '25', '14', '18', '23')


def build():
    if set(sys.argv[1:]) - {'--check'}:
        raise ValueError('only --check is supported')
    ev = json.loads((DATA / 'shomera-evidence.json').read_text())
    reg = json.loads((DATA / 'shomera-publication.json').read_text())
    if ev['schema'] != 'plotnua.shomera-editorial-evidence.v1' or reg['schema'] != 'plotnua.shomera-editorial-publication.v1':
        raise ValueError('wrong evidence or publication schema')
    if ev['supplier_permission_asserted'] is not False or ev['imagery'] != 'none':
        raise ValueError('text-only public information; no supplier permission asserted')
    age = (dt.date.today() - dt.date.fromisoformat(ev['checked'])).days
    if not 0 <= age <= 30:
        raise ValueError('recheck sources: evidence is future-dated or older than 30 days')
    decision = reg['decision']
    if decision['scope'] != 'Garden Rooms' or decision['pages'] != [PAGE] or [o['name'] for o in reg['organisations']] != ['Shomera']:
        raise ValueError('publication scope must be exactly this Shomera guide')
    published = decision['state'] == 'APPROVED'
    if published:
        if decision['authorised_by'] != 'Colin MacAulay' or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', decision.get('decision_date') or '') or ev['publication_status'] != 'PUBLISHED':
            raise ValueError('publication requires the founder decision and matching source state')
        js = """import fs from 'node:fs';
import {derivePublicInformationListing} from './atlas-tools/publication-gate.mjs';
const reg=JSON.parse(fs.readFileSync(0,'utf8'));
const rows=JSON.parse(fs.readFileSync('image-rights-records.json','utf8')).records;
console.log(JSON.stringify(derivePublicInformationListing('Shomera',rows,reg,'Garden Rooms')));"""
        result = subprocess.run(['node','--input-type=module','-e',js], cwd=ROOT, input=json.dumps(reg), text=True, capture_output=True, check=True)
        gate = json.loads(result.stdout)
        if gate['visibility'] != 'PUBLISHABLE' or gate['basis'] != 'PUBLIC_INFORMATION':
            raise ValueError('rights-first publication gate refused this editorial basis')
    elif decision['state'] != 'PENDING' or decision['authorised_by'] is not None or decision['decision_date'] is not None or ev['publication_status'] != 'DRAFT':
        raise ValueError('draft must preserve pending approval without inventing a decision')
    src = {s['url']: s for s in ev['sources']}
    prefix = 'https://www.shomera.ie/garden-rooms'
    urls = {prefix, prefix+'/classic-range', prefix+'/contemporary-range'}
    rows = []
    if len(ev['models']) != 6:
        raise ValueError('exactly six reviewed models required')
    for m, number in zip(ev['models'], MODELS):
        group = 'classic-range' if number in MODELS[:3] else 'contemporary-range'
        url = prefix+'/'+group+'/shomera-'+number
        urls.add(url)
        if (m['model'] != 'Shomera '+number or m['source_url'] != url or m['checked'] != ev['checked']
                or m['range'] != ('Classic' if group == 'classic-range' else 'Contemporary')
                or m['vat'] != 'not established on reviewed pages'
                or m['build_and_installation'] != 'explicitly included in product headline'
                or not isinstance(m['starting_price_eur'], (int,float)) or m['starting_price_eur'] <= 0):
            raise ValueError('model identity, price scope or VAT limitation changed')
        rows.append('<tr><th scope="row">'+escape(m['range'])+'</th><td><a href="'+url+'">'+escape(m['model'])+'</a></td><td>'+escape(m['published_dimensions'])+'</td><td class="mp-price">From €'+format(m['starting_price_eur'], ',')+'</td></tr>')
        if m['source_sha256'] != src[url]['sha256']:
            raise ValueError('model evidence hash differs from its source')
    if set(src) != urls or len(ev['sources']) != 9:
        raise ValueError('exactly the nine reviewed primary URLs required')
    for url, s in src.items():
        if s['final_url'] != url or s['http_status'] != 200 or s['checked'] != ev['checked'] or not re.fullmatch(r'[0-9a-f]{64}',s['sha256']):
            raise ValueError('primary-source verification differs')
    surfaces = [(ROOT/p).read_text() for p in ['sitemap.xml','search-index-v1.json','discovery-living-in-the-garden.html']]
    if not published and any(PAGE in s for s in surfaces):
        raise ValueError('unapproved draft appears on a public discovery surface')
    if published and '--check' in sys.argv:
        records = [r for r in json.loads(surfaces[1])['records'] if r.get('route') == PAGE]
        if surfaces[0].count('<loc>https://plotnua.ie/'+PAGE+'</loc>') != 1 or surfaces[2].count('href="'+PAGE+'"') != 1 or len(records) != 1 or records[0]['type'] != 'possibility':
            raise ValueError('published guide needs one sitemap, parent and informational Search entry')
    spec = importlib.util.spec_from_file_location('shared_maker_renderer',ROOT/'atlas-tools/build-garden-maker-pages.py')
    maker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(maker)
    # The shared wrapper uses the existing pilot substitutions. They are unused
    # in this template; Shomera's factual table comes only from its own evidence.
    wrapper = json.loads((DATA/'source-evidence.json').read_text())
    wrapper['checked'] = ev['checked']
    text = maker.render(PAGE, PROFILE, wrapper, maker.load_identity(), published, {'model_rows': ''.join(rows)})
    required = [
        'reviewed pages do not clearly establish whether VAT is included',
        'These are starting prices, not quotations for your address',
        'Model numbers are names',
        'external landscaping remains the customer',
        'not a supplier endorsement, site assessment or offer',
    ]
    visible = re.sub(r'<[^>]+>', ' ', text)
    if any(phrase not in visible for phrase in required) or '<img' in text.split('<main',1)[1].split('</main>',1)[0]:
        raise ValueError('a required scope limitation is missing or supplier imagery was introduced')
    if '--check' in sys.argv:
        if not (ROOT/PAGE).exists() or (ROOT/PAGE).read_text() != text:
            raise ValueError('generated Shomera page differs')
    else:
        (ROOT/PAGE).write_text(text)
    print('SHOMERA GUIDE · '+('CHECK OK' if '--check' in sys.argv else 'BUILT')+' · '+('published' if published else 'noindex draft; founder approval pending'))


if __name__ == '__main__':
    try:
        build()
    except (ValueError,KeyError,subprocess.CalledProcessError) as exc:
        print('REFUSED: '+str(exc))
        sys.exit(1)
