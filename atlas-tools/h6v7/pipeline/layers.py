"""PlotNua hero: feature layers from the aligned BEFORE/POSSIBLE pair.
Layer = source pixels (POSSIBLE, or a reconstructed patch where another feature's foliage hid it) + alpha matte,
composited over the unchanged BEFORE master in Z order. Checks: ALL == POSSIBLE inside every feature, CLEAR == BEFORE."""
import numpy as np, cv2, json
B=cv2.imread('in/hero-before-master.png').astype(np.float32); A=cv2.imread('out/possible-aligned.png').astype(np.float32)
PODFREE=cv2.imread('out/pod-reedfree.png').astype(np.float32); REED=np.load('out/pod-reedmask.npy')
H,W=B.shape[:2]; D=np.load('out/diff.npy')
def poly(pts):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[np.array(pts,np.int32)],255); return m>0
c=(D>16).astype(np.uint8); c=cv2.morphologyEx(c,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)); CH=cv2.morphologyEx(c,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))>0
hsv=cv2.cvtColor(A.astype(np.uint8),cv2.COLOR_BGR2HSV).astype(np.float32)
veg=((hsv[...,0]>28)&(hsv[...,0]<90)&(hsv[...,1]>70)&(hsv[...,2]>45))

# Retreat / pool boundary: the reed line in front of the gravel (pool owns everything below it)
L_RP=[(1336,498),(1420,500),(1486,505),(1490,557),(1670,560)]
F={}
F['treehouse']=dict(z=0,
  zone=poly([(38,88),(335,80),(345,235),(412,320),(424,512),(412,532),(296,532),(268,500),(150,500),(112,470),(104,228),(38,228)]),
  core=poly([(46,96),(322,92),(322,190),(398,300),(410,520),(300,520),(240,490),(176,500),(176,360),(112,352),(108,232),(96,190)]))
F['borrowed-garden']=dict(z=1,
  zone=poly([(0,372),(146,372),(150,468),(318,468),(326,560),(318,700),(250,724),(90,726),(0,706)]),
  core=poly([(92,478),(306,478),(312,690),(96,690)]))
F['garden-room']=dict(z=2,
  zone=poly([(864,288),(1342,286),(1342,497),(1200,497),(1045,494),(864,500)]),
  core=poly([(918,296),(1334,296),(1334,494),(918,494)]))
F['garden-retreat']=dict(z=3,
  zone=poly([(1336,276),(1670,276)]+L_RP[::-1][:0]+[(1670,560)]+L_RP[::-1][1:]),
  core=poly([(1344,282),(1670,282)]+[(1670,556),(1492,553),(1482,500),(1344,494)]))
F['natural-swimming-pool']=dict(z=4,
  zone=poly([(668,560),(1040,530),(1046,446),(1336,446)]+L_RP+[(1670,942),(980,942),(1080,890)]),
  core=poly([(676,566),(1042,540),(1336,540)]+[(1336,505),(1488,509),(1492,562),(1670,564)]+[(1670,942),(1000,942),(1090,895)]))
F['power-station']=dict(z=5,
  zone=poly([(408,146),(658,146),(662,220),(408,220)]),
  core=poly([(414,152),(648,152),(650,212),(414,212)]))
SRC={k:A for k in F}
SRC['natural-swimming-pool']=cv2.imread('out/pool-noreflection.png').astype(np.float32)

def matte(f, feather=2.2):
    a=(f['core'] | (f['zone'] & CH)).astype(np.float32)
    a=cv2.GaussianBlur(a,(0,0),feather)
    a*=cv2.GaussianBlur(f['zone'].astype(np.float32),(0,0),1.2)
    return np.clip(a,0,1)
M={k:matte(f) for k,f in F.items()}
# ---- the band between the pod / retreat and the pool: explicit ownership of every pixel
yy,xx=np.mgrid[0:H,0:W]
C=[(668,560),(1040,532),(1150,538),(1340,560),(1490,561),(1670,566)]            # far coping line (hidden under reeds on the right)
belowC=poly(C+[(1670,942),(668,942)])
band=(poly([(1046,440),(1336,440),(1336,560),(1040,532)]) | poly([(1336,474),(1484,480),(1486,538),(1610,541),(1626,553),(1670,555),(1670,566),(1490,561),(1340,560)]))&~belowC
reedish=veg|REED|((hsv[...,0]>=22)&(hsv[...,0]<=40)&(hsv[...,1]>110)&(hsv[...,2]>110))
reedish=cv2.morphologyEx(reedish.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((2,2),np.uint8))>0
podzone=F['garden-room']['zone']
left=band&(xx<1336); right=band&(xx>=1336)
strict=veg|((hsv[...,0]>=22)&(hsv[...,0]<=40)&(hsv[...,1]>110)&(hsv[...,2]>110))
glaz=(xx>=1040)&(xx<1196)&(yy<467)
deckrows=(xx>=1040)&(xx<1200)&(yy>=466)&(yy<=493)
strict=strict&~(deckrows&(hsv[...,0]<26))&~((xx>=1132)&(xx<1182)&(yy<470))
pd=np.abs(A-PODFREE).max(2)
own_pool_band=band&((strict&~glaz)|(strict&REED&glaz)|(REED&(pd>40)&(hsv[...,2]>60)&(hsv[...,1]>45)&~glaz)) | (left&(yy>510)) | (left&~podzone&(yy>497)&~((yy<=510)&(xx>=918)))
own_pool_band&=~(deckrows&(hsv[...,0]<27)&(hsv[...,1]>40))
own_pod_shadow=left&~podzone&(yy>494)&(yy<=510)&(xx>=918)&~reedish
own_retreat_band=right&~reedish&(yy>=470)
def feath(m,s=0.8): return np.clip(cv2.GaussianBlur(m.astype(np.float32),(0,0),s),0,1)
SRC['garden-room']=np.where(REED[...,None],PODFREE,A)
M['natural-swimming-pool']=np.where(band, feath(own_pool_band), M['natural-swimming-pool'])
M['garden-room']=np.maximum(M['garden-room'], feath(own_pod_shadow))
M['garden-retreat']=np.where(right, feath(own_retreat_band), M['garden-retreat'])
# treehouse / beds share a narrow band: the beds' foliage stays with the beds
ov=(M['treehouse']>0)&(M['borrowed-garden']>0)
fol=cv2.GaussianBlur((veg&ov).astype(np.float32),(0,0),0.7)
M['treehouse']=np.where(ov, M['treehouse']*(1-fol), M['treehouse'])

order=sorted(F,key=lambda k:F[k]['z'])
def comp(keys):
    out=B.copy()
    for k in order:
        if k in keys: a=M[k][...,None]; out=out*(1-a)+SRC[k]*a
    return out
allc=comp(order); u=np.zeros((H,W),bool)
for k in order: u|=M[k]>0.98
err=np.abs(allc-A).max(2)
rep={'all_vs_possible_inside_features':{'mean':round(float(err[u].mean()),3),'p99':round(float(np.percentile(err[u],99)),2),'max':round(float(err[u].max()),2)}}
print(rep)
np.savez_compressed('out/mattes.npz',**{k.replace('-','_'):M[k] for k in order})
np.save('out/src-garden-room.npy',SRC['garden-room'].astype(np.uint8))
cv2.imwrite('out/comp-all.png',allc.astype(np.uint8))
for k in order: cv2.imwrite('out/comp-%s.png'%k,comp([k]).astype(np.uint8))
json.dump({'order':order,'checks':rep},open('out/layers-report.json','w'),indent=1)
