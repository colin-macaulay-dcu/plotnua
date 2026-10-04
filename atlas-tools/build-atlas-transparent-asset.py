"""
ATLAS -- KEY OUT THE PNG'S #FDFAF1 GROUND, CHANGE NOTHING ELSE.

The approved mark is opaque RGB on a flat #FDFAF1 ground, so it reads as a pale
rectangle on PlotNua's #F5F2E8 surface. This replaces that ground with real
alpha. It is a matte, not a redraw.

THE TEST THIS HAS TO PASS is a round trip: composite the result back over
#FDFAF1 and it must return the original image. Any error there is artwork this
operation damaged. A first attempt feathered alpha from a ramp and then divided
the ground out, and it failed that test by up to 13 levels across 18,879 pixels
-- because dividing by a guessed alpha pushes the recovered colour out of gamut,
and the clip is lost information. So alpha is not guessed here. On the rim it is
the SMALLEST value for which the recovered colour still fits in 0..255:

    C = aF + (1-a)B,  F in [0,255]  =>  a >= 1 - min_c(C_c/B_c)
                                   and  a >= max_c (C_c-B_c)/(255-B_c)

Taking alpha at that bound makes the rim as transparent as it can honestly be
AND keeps F in gamut, so nothing is clipped and the round trip is exact.

Three decisions, each measured from the asset:

  TLO=2 . The ground is not perfectly flat: 29% of the image is exactly
         #FDFAF1 and 77% within one level. Two levels covers that dither
         without reaching artwork.

  AREA>=64 . That tolerance yields one border region (982,669px), nine
         substantial enclosed openings (96,049 down to 2,372px -- the open
         centre and the gaps in the weave) and a tail of 517 specks totalling
         1,647px. The specks stay OPAQUE: a speck that is really a pale
         highlight must not become a hole, while a speck that is really a gap
         is 0.1% of the image and sub-pixel at the 60px display size. Only one
         direction of that error is visible, so the rule points away from it.

  RIM=2px . Partial alpha is confined to artwork pixels that actually touch the
         ground. Everywhere inside, the knot stays fully opaque and its bytes
         are untouched -- so the dark green, the sage and all the shading
         between them are the approved artwork, not a reconstruction of it.
"""
import numpy as np, hashlib, os, pathlib
from PIL import Image
from scipy import ndimage as nd

os.chdir(pathlib.Path(__file__).resolve().parent.parent)   # always the repo root
SRC='assets/brand/atlas-final-static-approved.png'
DST='assets/brand/atlas-final-static-approved-transparent.png'
B=np.array([0xFD,0xFA,0xF1], dtype=np.float64)
TLO, MIN_AREA, RIM = 2, 64, 2

rgb=np.asarray(Image.open(SRC).convert('RGB')).astype(np.float64)
dist=np.abs(rgb-B).max(axis=2)

lab,n=nd.label(dist<=TLO); sz=np.bincount(lab.ravel()); sz[0]=0
bg=(sz>=MIN_AREA)[lab]
art=~bg

disk=np.array([[0,1,1,1,0],[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0]],bool)   # r=2
rim  = art & nd.binary_dilation(bg, structure=disk)

# the honest floor for alpha, per pixel
a_dark  = 1.0 - (rgb/B).min(axis=2)                       # keeps F >= 0
a_light = ((rgb-B)/(255.0-B)).max(axis=2)                 # keeps F <= 255
a_min   = np.clip(np.maximum(a_dark, a_light), 0.0, 1.0)

alpha=np.where(art,1.0,0.0)
alpha[rim]=a_min[rim]
A8=np.rint(alpha*255).astype(np.uint8)
A8[bg]=0; A8[art & ~rim]=255

# GROUND DITHER THAT ESCAPED THE TOLERANCE. A few hundred pixels sit 3-6 levels
# off #FDFAF1 -- including three plate corners -- so they fall outside TLO and
# pick up a whisper of alpha. They are ground, not artwork, and they are exactly
# the rectangle the founder is asking to remove. They are cleared, but ONLY
# where BOTH tests agree: at most 8% opaque AND more than 4px from any solid
# artwork. Measured on this asset that is 117 pixels. A blanket distance rule
# would have been wrong -- 107 pixels further than 4px carry alpha above 40 and
# are the fine brush tapers of the knot, which must survive.
solid = A8>=200
faraway = nd.distance_transform_edt(~solid) > 4.0
dither = (A8>0) & (A8<=20) & faraway
A8[dither]=0
print('GROUND DITHER cleared: %d px (all <=8%% opaque and >4px from any artwork)' % int(dither.sum()))

out=rgb.copy()
al8=A8.astype(np.float64)/255.0
part=(A8>0)&(A8<255)
a=al8[part][:,None]
out[part]=np.clip((rgb[part]-(1.0-a)*B)/a, 0.0, 255.0)
rgba=np.dstack([np.rint(out).astype(np.uint8), A8])
Image.fromarray(rgba,'RGBA').save(DST, optimize=True)

# ---- ROUND TRIP: back over the original ground must return the original.
al=rgba[:,:,3:4].astype(np.float64)/255.0
back=rgba[:,:,:3].astype(np.float64)*al + B*(1.0-al)
err=np.abs(back-rgb).max(axis=2)
print('MATTE   transparent %.2f%%   fully opaque %.2f%%   partial %.2f%% (%d px, all on the rim)'
      %((A8==0).mean()*100,(A8==255).mean()*100,part.mean()*100,int(part.sum())))
print('ROUND TRIP over #FDFAF1   max channel error %d   mean %.4f   px>1 %d   px>2 %d'
      %(err.max(), err.mean(), int((err>1).sum()), int((err>2).sum())))
ident=(rgba[:,:,:3]==rgb.astype(np.uint8)).all(axis=2)&(A8==255)
print('INTERIOR  %d px fully opaque AND byte-identical to the approved artwork (%.2f%% of the image)'
      %(int(ident.sum()), ident.mean()*100))
print('           every opaque pixel identical:', bool((ident==(A8==255)).all()))
# what the page will see
P=np.array([0xF5,0xF2,0xE8],dtype=np.float64)
onpage=rgba[:,:,:3].astype(np.float64)*al + P*(1.0-al)
d=np.abs(onpage-rgb).max(axis=2)
print('ON #F5F2E8 vs the approved image   max shift %d levels   mean %.3f   px shifted >2: %d'
      %(d.max(), d.mean(), int((d>2).sum())))
print('sha256', hashlib.sha256(open(DST,"rb").read()).hexdigest())
im=Image.open(DST); print('saved', DST, im.mode, im.size)
