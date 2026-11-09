"""Export the hero image set: BEFORE base, six feature layers, the conditional reflection layer, water textures."""
import numpy as np, cv2, json, hashlib, os
from PIL import Image
OUT='out/assets'; os.makedirs(OUT,exist_ok=True)
B=cv2.imread('in/hero-before-master.png'); A=cv2.imread('out/possible-aligned.png'); NOREF=cv2.imread('out/pool-noreflection.png')
H,W=B.shape[:2]; M=np.load('out/mattes.npz'); order=json.load(open('out/layers-report.json'))['order']
SRCPOD=np.load('out/src-garden-room.npy')
src={k:A for k in order}; src['garden-room']=SRCPOD; src['natural-swimming-pool']=NOREF; src['garden-retreat']=np.load('out/src-garden-retreat.npy')
WIDTHS=(960,1670); STEM='H6v7'
def rgba(bgr,alpha):
    a=np.clip(alpha*255+0.5,0,255).astype(np.uint8); rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
    rgb=np.where(a[...,None]==0,0,rgb)          # transparent pixels carry no colour (smaller files)
    return Image.fromarray(np.dstack([rgb,a]),'RGBA')
def save_set(img,stem,avif=False,q=86):
    files=[]
    for w in WIDTHS:
        im=img if w==W else img.resize((w,round(H*w/W)),Image.LANCZOS)
        p='%s/%s-%d.webp'%(OUT,stem,w); im.save(p,'WEBP',quality=q,method=6,exact=True) ; files.append(p)
        if avif: p='%s/%s-%d.avif'%(OUT,stem,w); im.save(p,'AVIF',quality=70); files.append(p)
    return files
files=[]
files+=save_set(Image.fromarray(cv2.cvtColor(B,cv2.COLOR_BGR2RGB)),STEM+'-before',avif=True,q=84)
DEV=json.load(open('out/devices.json'))
def with_devices(im):
    # the battery and EV charger belong to the Power Station layer, as in the approved evening layer
    for n in ('battery','charger'):
        d=DEV[n]; sp=Image.open('/home/claude/work/out/devices/'+os.path.basename(d['file'])).convert('RGBA')
        sp=sp.resize((round(d['w']),round(d['h'])),Image.LANCZOS); im.alpha_composite(sp,(round(d['x']),round(d['y'])))
    return im
for k in order:
    im=rgba(src[k],M[k.replace('-','_')])
    if k=='power-station': im=with_devices(im)
    files+=save_set(im,'%s-layer-%s'%(STEM,k))
# conditional: the garden room's reflection in the pool (only when both are on)
ra=np.load('out/reflection-alpha.npy')*M['natural_swimming_pool']
files+=save_set(rgba(A,ra),STEM+'-layer-garden-room-reflection')
# water textures for the ripple canvas (full-canvas coordinates; cropped bounding boxes recorded)
hsv=cv2.cvtColor(A,cv2.COLOR_BGR2HSV).astype(np.int32)
def polym(pts):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[np.array(pts,np.int32)],255); return m>0
veg=(hsv[...,0]>24)&(hsv[...,0]<62)&(hsv[...,1]>115)&(hsv[...,2]>105)
_yy,_xx=np.mgrid[0:H,0:W]
veg&=_yy<(575+(_xx-1040)*140/630)            # only the reeds standing at the far edge; reed reflections ripple with the water
stone=(hsv[...,1]<40)&(hsv[...,2]>135)
pool=polym([(712,575),(1040,558),(1180,577),(1330,612),(1500,662),(1670,702),(1670,794),(1226,877),(1150,858),(758,598)])&~cv2.dilate(veg.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
pool=cv2.morphologyEx(pool.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
tub=np.zeros((H,W),np.uint8); cv2.ellipse(tub,(1571,437),(76,8),0,0,360,1,-1); tub[:,1626:1646]=0
tex={}
for name,mask,img in [('pool',pool,NOREF),('pool-reflect',pool,A),('tub',tub,A)]:
    a=cv2.GaussianBlur(mask.astype(np.float32),(0,0),1.6)*(mask>0)
    ys,xs=np.where(mask>0); x0,x1,y0,y1=xs.min()-2,xs.max()+3,ys.min()-2,ys.max()+3
    im=rgba(img[y0:y1,x0:x1],a[y0:y1,x0:x1]); p='%s/%s-water-%s.webp'%(OUT,STEM,name); im.save(p,'WEBP',quality=88,method=6,exact=True); files.append(p)
    tex[name]=[int(x0),int(y0),int(x1-x0),int(y1-y0)]
json.dump({'canvas':[W,H],'water':tex},open(OUT+'/water-boxes.json','w'),indent=1)
for p in files: print('%-60s %8d'%(p,os.path.getsize(p)))
print(tex)
