import numpy as np, cv2, json
B=cv2.imread('in/hero-before-master.png'); P=cv2.imread('in/hero-possible-master.png')
H,W=B.shape[:2]
# pad P to BEFORE canvas (bottom row replicated) -- no stretching
Pp=cv2.copyMakeBorder(P,0,H-P.shape[0],0,0,cv2.BORDER_REPLICATE)
gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY).astype(np.float32)/255; gP=cv2.cvtColor(Pp,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
# permanent-scenery mask: house, sky, roofs, left path/border; exclude feature zones
m=np.zeros((H,W),np.uint8)
for (x0,y0,x1,y1) in [(700,0,1670,200),(340,220,760,450),(1240,150,1560,240),(300,480,480,940),(0,600,300,940),(830,200,1050,300)]:
    m[y0:y1,x0:x1]=255
for (x0,y0,x1,y1) in [(400,150,660,215),(0,0,420,540)]: m[y0:y1,x0:x1]=0   # PV, treehouse/tree region
best={}
for mode,name in [(cv2.MOTION_TRANSLATION,'translation'),(cv2.MOTION_AFFINE,'affine')]:
    warp=np.eye(2,3,dtype=np.float32)
    cc,warp=cv2.findTransformECC(gB,gP,warp,mode,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-7),m,5)
    best[name]=(cc,warp.tolist()); print(name,cc,warp)
json.dump(best,open('out/alignment.json','w'),indent=1)
warp=np.array(best['translation'][1],np.float32)
A=cv2.warpAffine(Pp,warp,(W,H),flags=cv2.INTER_LANCZOS4|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite('out/possible-aligned.png',A)
# verify residual
gA=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float32)
for (name,x0,y0,x1,y1) in [('sky',760,20,1000,180),('house',360,230,560,330),('chimney',680,140,740,220),('neigh',1250,160,1550,250),('path',320,700,480,930),('purple',870,200,1010,280)]:
    a=gB[y0:y1,x0:x1]*255; b=gA[y0:y1,x0:x1]
    (dx,dy),r=cv2.phaseCorrelate(a,b,cv2.createHanningWindow((x1-x0,y1-y0),cv2.CV_32F)); print('residual',name,round(dx,2),round(dy,2))
