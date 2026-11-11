#!/usr/bin/env python3
"""Rebuild founder-approved daylight hero pair (11 November 2026).

The generation originals are retained in ChatGPT as Contemporary Irish Home and Garden
Before.png and Hidden garden shelter entrance.png. The two DAYLIGHT-MASTER.webp files
are quality-95 WebP encodings at original dimensions, without crop or retouching.
This builder performs only identical crops/resizes/encoding for the paired delivery files.
The earlier sunset masters remain archived with their existing provenance records.
"""
import hashlib, io, json, pathlib, sys
from PIL import Image, __version__ as PIL_VERSION
ROOT=pathlib.Path(__file__).resolve().parent.parent
D='assets/disc038/img/'
REG=ROOT/'image-provenance-records.json'
DATE='2026-11-11'
CHECK='--check' in sys.argv
MASTERS={
 'BEFORE': D+'DISC-038-BEFORE-DAYLIGHT-MASTER.webp',
 'POSSIBLE': D+'DISC-038-POSSIBLE-DAYLIGHT-MASTER.webp',
}
PROMPTS={
 'BEFORE': "Create ONE landscape 3:2 photorealistic architectural editorial photograph, BEFORE view for a precise before/possible comparison slider. A very contemporary architect-designed Irish family house and modest stylish suburban back garden in soft bright natural daylight, mild early summer, neutral colours. Not twilight. House occupies left third: white mineral render, large slim anthracite sliding glass doors, a clean contemporary flat-roof single-storey rear extension, partial two-storey upper volume, oak flooring and understated modern furniture glimpsed inside. Garden is inviting and believable, not a CGI mansion: rectangular fresh lawn, restrained beds of grasses and leafy perennials, pale large-format limestone patio foreground, tall privacy hedging at rear, one mature tree near rear left, a little neighbouring roof barely visible. Edge of a cool modern dark outdoor dining table and two slim chairs cropped at far left foreground, no lanterns or styled props. Crucial future edit zone: right foreground-to-middle of garden next to patio is a clear broad strip of flat lawn approximately 1.5 metres wide and 3 metres long, with planting along its right edge; this is where a discreet stair entrance will later appear. For THIS BEFORE image this strip is just normal lawn with no hatch, no hole, no stairs, no shelter visible. Camera at standing eye level from patio looking diagonally towards rear boundary, 35mm architectural lens, straight verticals, wide enough to retain house at left and entrance zone at right in same shot. Contemporary, modern, cool and inviting, clear airy day without harsh sun or grey gloom. Real photograph aesthetic: material variation, naturally irregular foliage, credible glazing reflections, gentle soft shadows, subtle camera grain, no HDR or glossy render surfaces. Premium but lived in, immaculate enough to be appealing without sterile perfection. No people, no text or lettering, no logos, no borders, no diagrams, no sunset, no garden uplighting, no orange light, no fantasy cutaway. Output a full standalone photograph only.",
 'POSSIBLE': "Edit this exact photograph to make its POSSIBLE comparison-slider counterpart. Preserve the original photograph, exact camera position, lens, crop, canvas dimensions, house, every glazing mullion, trees, sky, hedge, furniture, lawn edges, patio joints, lighting and colour grading. Change ONLY the right-hand lawn immediately beside the patio to reveal a discreet contemporary underground shelter stair entrance. It must be a plausible modest scale engineered stairwell approximately 1.1 metres clear width, 2.8 metres long, aligned away from viewer towards rear hedge, on the right side just inside the planting border. The near end starts at the lawn/patio edge, walking entry from patio. A slim low concrete curb around sides and rear, realistic smooth light architectural concrete walls and seven or eight narrow descending concrete treads, one slim anthracite handrail fixed internally. A single flat anthracite steel hatch lid hinged across the FAR end of the rectangular opening, raised backwards to roughly 80 degrees, held by two realistic compact gas struts outside the clear stair passage. Hatch exactly sized to close the opening. The stair descends under the garden to a real small landing and a modest open doorway; glimpse only a tiny section of an understated contemporary underground living space in shadow beyond, soft neutral practical light, no bright orange glow. No impossible full-size room visible through the stairs, no cutaway view, no huge cavern. Opening and stairs clear and legible at normal website size, elegantly integrated but recognisably functional, not science fiction. The garden remains the dominant scene. Add physically credible local shadows on the stairwell and lid matching the original daylight. Keep all surrounding lawn, planting, patio, architecture, reflections and trees unchanged. Same 3:2 landscape dimensions. Maintain the natural real-camera photographic texture of the source, no render finish or cinematic grading, no people, no text, no labels, no border. This is the same shot with only the shelter entrance introduced.",
}
def sha(b): return hashlib.sha256(b).hexdigest()
def facts(a,b): return {'asset':a,'sha256':sha(b),'bytes':len(b),'pixels':list(Image.open(io.BytesIO(b)).size)}
def encode(im,fmt):
 out=io.BytesIO()
 if fmt=='webp': im.save(out,'WEBP',quality=82,method=6)
 else: im.save(out,'JPEG',quality=86,optimize=True,progressive=True)
 return out.getvalue()
def build():
 files={}
 for role,a in MASTERS.items():
  im=Image.open(ROOT/a).convert('RGB');assert im.size==(1536,1024)
  for w in (768,1024,1376,1536):
   files[D+f'DISC-038-{role}-{w}.webp']=(encode(im.resize((w,round(w*2/3)),Image.Resampling.LANCZOS),'webp'),role,f'Whole frame, Lanczos resize to {w} pixels wide')
  files[D+f'DISC-038-{role}-1024.jpg']=(encode(im.resize((1024,683),Image.Resampling.LANCZOS),'jpg'),role,'Whole frame, Lanczos resize to 1024 x 683')
  files[D+f'DISC-038-{role}-M-819.webp']=(encode(im.crop((717,0,1536,1024)),'webp'),role,'Identical 819 x 1024 phone window x 717-1536, full height; entrance remains visible')
  if role=='POSSIBLE': files[D+'DISC-038-og-1200x630.jpg']=(encode(im.resize((1200,800),Image.Resampling.LANCZOS).crop((0,85,1200,715)),'jpg'),role,'Resize whole frame to 1200 x 800; crop y 85-715 for social card')
 return files
reg=json.loads(REG.read_text());files=build()
if CHECK:
 records={r['asset']:r for r in reg['records']};ders={d['asset']:d for d in reg['derivatives']}
 for a in MASTERS.values(): assert records[a]['sha256']==sha((ROOT/a).read_bytes()),a
 for a,(b,*_) in files.items(): assert (ROOT/a).read_bytes()==b and ders[a]['sha256']==sha(b),a
 print('DISC-038 IMAGES: two daylight masters and 13 reproducible delivery files verified');sys.exit(0)
old={D+'DISC-038-01-BEFORE-MASTER.png',D+'DISC-038-02-POSSIBLE-MASTER.png'}
for row in reg['records']:
 if row['asset'] in old:
  archived=dict(row);archived['superseded']='Replaced by founder-approved daylight pair, 11 November 2026; not published.'
  reg.setdefault('superseded_records',[]).append(archived)
reg['records']=[row for row in reg['records'] if row['asset'] not in old]
for role,a in MASTERS.items():
 b=(ROOT/a).read_bytes();r=facts(a,b);r.update({'class':'AI_ILLUSTRATION','what': 'Generic contemporary Irish house and garden in daylight'+(' with an open underground shelter entrance.' if role=='POSSIBLE' else ' before the shelter entrance is introduced.'),'generated':{'tool':'OpenAI image_gen built-in image generation tool','date':DATE},'prompt':PROMPTS[role],'reference_inputs':[] if role=='BEFORE' else [{'asset':MASTERS['BEFORE'],'description':'The BEFORE generation original PNG was supplied to image_gen as the sole edit target; this WebP is its whole-frame delivery master.'}],'depicts_named_product':False,'depicts_named_organisation':False,'human_review':{'reviewer':'Colin Macaulay (founder)','date':DATE,'attests':'Reviewed both generated images in this conversation and instructed: great now implement and publish.'},'permitted_surfaces':['discovery','library-card'],'label_on_page':'AI-generated illustration','processing':'Generation original encoded as quality-95 WebP, original dimensions retained, no crop or retouching. Original retained in ChatGPT.'})
 reg['records']=[v for v in reg['records'] if v['asset']!=a]+[r]
for a,(b,role,op) in files.items():
 (ROOT/a).write_bytes(b);src=MASTERS[role];r=facts(a,b);r.update({'derived_from':{'asset':src,'sha256':sha((ROOT/src).read_bytes())},'method':'crop' if 'window' in op or 'crop' in op else 'optimise','edit':{'description':op,'operation':op,'verified_by':'atlas-tools/build-disc038-images.py --check'},'encoder':f'Pillow {PIL_VERSION}, WebP quality 82 method 6 or JPEG quality 86 progressive','made':DATE,'content_credentials':{'source_file_embeds_c2pa':False,'derivative_embeds_c2pa':False,'note':'WebP master and delivery copies carry no signed credential; AI origin is explicitly declared from this generation session.'}})
 reg['derivatives']=[v for v in reg['derivatives'] if v['asset']!=a]+[r]
REG.write_text(json.dumps(reg,indent=2,ensure_ascii=False)+'\n')
print('Built two approved daylight masters and 13 delivery files')
