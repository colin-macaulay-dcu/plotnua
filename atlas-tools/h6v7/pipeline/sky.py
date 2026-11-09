"""Cloud lettering target + transport field for 'Discover what’s possible.' made from the photograph's own clouds.
Outputs (band = BX..BX+BW, BY..BY+BH in master pixels):
  sky-src  : the BEFORE pixels of the band (what the visitor sees first)
  sky-tgt  : the same sky after the clouds have gathered into the words
  sky-flow : R,G = where each target pixel's cloud came from (offset +128, px), B = where the morph applies (0-255)
Every letter is a translated piece of a real cloud from this sky (no stretching, no generated texture)."""
import numpy as np, cv2, json
from PIL import Image, ImageDraw, ImageFont
B=cv2.imread('in/hero-before-master.png'); H,W=B.shape[:2]
BX,BY,BW,BH=870,0,640,196
S=B[BY:BY+BH,BX:BX+BW].copy()
lab=cv2.cvtColor(S,cv2.COLOR_BGR2LAB).astype(np.float32); L,a,b=lab[...,0],lab[...,1]-128,lab[...,2]-128
hsv=cv2.cvtColor(S,cv2.COLOR_BGR2HSV).astype(np.float32)
yy,xx=np.mgrid[0:BH,0:BW].astype(np.float32)
# ---- sky vs foreground (branches, roofs, trees, antennas)
fg=((hsv[...,0]>25)&(hsv[...,0]<95)&(hsv[...,1]>45)) | (L<105) | ((hsv[...,0]<22)&(hsv[...,1]>60))
fg=cv2.morphologyEx(fg.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
fg=cv2.dilate(fg,np.ones((7,7),np.uint8))
sky=(1-fg).astype(np.float32)
# ---- clear-sky plate: fit the blue pixels with a smooth surface
blue=(b<-14)&(sky>0)
A_=np.stack([np.ones_like(xx),xx/BW,yy/BH,(xx/BW)**2,(yy/BH)**2,(xx*yy)/(BW*BH)],-1)
plate=np.zeros_like(lab); wb=cv2.GaussianBlur(blue.astype(np.float32),(0,0),45)
mean=lab[blue].mean(0); t=yy/BH
fallback=np.dstack([mean[0]+9*t, np.full_like(t,mean[1]), 128+(mean[2]-128)*(1-0.22*t)])
for c in range(3):
    nc=cv2.GaussianBlur(lab[...,c]*blue,(0,0),45)/np.maximum(wb,1e-4)
    k=np.clip(wb*6,0,1); plate[...,c]=nc*k+fallback[...,c]*(1-k)
pa,pb=plate[...,1]-128,plate[...,2]-128
# ---- cloud matte from blueness; de-matted cloud colour
alpha=np.clip((b-pb)/np.maximum(-pb-2.0,4),0,1)*sky
alpha=cv2.GaussianBlur(alpha,(0,0),0.6)
cc=np.where(alpha[...,None]>0.05,(lab-plate*(1-alpha[...,None]))/np.maximum(alpha[...,None],0.05),lab)
cc[...,0]=np.clip(cc[...,0],60,255)
# ---- the words: heavy serif, two lines, billowy edges
SS=4; font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc',63*SS,index=0)
cv=Image.new('L',(BW*SS,BH*SS),0); d=ImageDraw.Draw(cv)
lines=['Discover','what’s possible.']; cx=BW*SS*0.5
for t,y in zip(lines,[8*SS,82*SS]):
    w=d.textlength(t,font=font); d.text((cx-w/2,y),t,font=font,fill=255)
txt=np.array(cv.resize((BW,BH),Image.LANCZOS)).astype(np.float32)/255
inside=(txt>0.5).astype(np.uint8)
dist=cv2.distanceTransform(inside,cv2.DIST_L2,5)-cv2.distanceTransform(1-inside,cv2.DIST_L2,5)
rng=np.random.default_rng(7)
def fbm(oct=4,base=10.0):
    n=np.zeros((BH,BW),np.float32); amp=1.0
    for o in range(oct):
        s=base/(2**o); g=rng.standard_normal((int(BH/s)+3,int(BW/s)+3)).astype(np.float32)
        n+=amp*cv2.resize(g,(BW+int(3*s),BH+int(3*s)),interpolation=cv2.INTER_CUBIC)[:BH,:BW]; amp*=0.55
    return n/1.6
billow=np.abs(fbm(4,7.0))*2.4+fbm(2,2.5)*0.7
la=np.clip((dist+1.6+billow-0.9)/2.4,0,1); la=la*la*(3-2*la)
la*=np.clip(0.86+0.14*fbm(3,6.0),0.7,1.0)
la=cv2.GaussianBlur(la,(0,0),0.55)
# ---- each letter = a translated piece of real cloud (pick the densest nearby cloud for it)
n,lbl=cv2.connectedComponents(cv2.dilate((la>0.2).astype(np.uint8),np.ones((3,3),np.uint8)))
dens=cv2.GaussianBlur(alpha*np.clip((cc[...,0]-150)/70,0,1),(0,0),2)
O=np.zeros((BH,BW,2),np.float32); offs={}
for i in range(1,n):
    m=lbl==i; ys,xs=np.where(m)
    best=(-1,0,0)
    for dy in range(-24,25,4):
        for dx in range(-72,73,4):
            y2,x2=ys+dy,xs+dx
            ok=(y2>=0)&(y2<BH)&(x2>=0)&(x2<BW)
            if ok.mean()<0.999: continue
            sc=dens[y2,x2].mean()-0.0022*np.hypot(dx,dy*1.5)
            if sc>best[0]: best=(sc,dx,dy)
    O[m]=(best[1],best[2]); offs[i]=best
# smooth the field outward so the neighbourhood moves with each letter
wgt=cv2.GaussianBlur((lbl>0).astype(np.float32),(0,0),14)
Of=np.dstack([cv2.GaussianBlur(O[...,k],(0,0),14) for k in range(2)])/np.maximum(wgt[...,None],1e-3)
Of=Of*np.clip(wgt*3,0,1)[...,None]
Of=np.dstack([cv2.GaussianBlur(Of[...,k],(0,0),3.0) for k in range(2)])   # one smooth field: no tearing between letters
mx=(xx+Of[...,0]).astype(np.float32); my=(yy+Of[...,1]).astype(np.float32)
src_cc=np.dstack([cv2.remap(cc[...,c],mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT) for c in range(3)])
# lighting: the photograph is lit from above; tops of strokes a touch brighter, undersides greyer
gy=cv2.Sobel(cv2.GaussianBlur(la,(0,0),2.2),cv2.CV_32F,0,1,ksize=3)
core=cv2.GaussianBlur(np.clip(dist/4,0,1),(0,0),1.0)
src_cc[...,0]=np.clip(src_cc[...,0]+np.clip(gy*45,-16,9)-4*(1-core)*np.clip(-gy*20,0,1),60,255)
# ---- target: thin veil of the original cloud + the dense letters
near=cv2.GaussianBlur((la>0.3).astype(np.float32),(0,0),17)
bgA=alpha*np.clip(1-near*2.4,0.10,1.0)
A_t=la+bgA*(1-la)
col=(src_cc*la[...,None]+cc*(bgA*(1-la))[...,None])/np.maximum(A_t[...,None],1e-3)
tgt=plate*(1-A_t[...,None])+col*A_t[...,None]
# where the morph applies: sky only, fading out towards the band's edges
edge=np.minimum.reduce([xx/60,(BW-1-xx)/60,(BH-1-yy)/22,np.ones_like(xx)])
region=np.clip(edge,0,1)*cv2.GaussianBlur(sky,(0,0),1.5)
region=region*region*(3-2*region)
T=cv2.cvtColor(np.clip(tgt,0,255).astype(np.uint8),cv2.COLOR_LAB2BGR)
T=(T*region[...,None]+S*(1-region[...,None])).astype(np.uint8)
cv2.imwrite('out/sky-src.png',S); cv2.imwrite('out/sky-tgt.png',T)
flow=np.dstack([np.clip(Of[...,0]+128,0,255),np.clip(Of[...,1]+128,0,255),region*255]).astype(np.uint8)
Image.fromarray(flow,'RGB').save('out/sky-flow.png')
# when each pixel condenses (letters, cores first) or thins (the surrounding cloud): 0..0.55 of the morph
nz=(fbm(3,8.0)-fbm(3,8.0).min()); nz/=nz.max()
tau_l=0.30*(1-np.clip(dist/6,0,1))+0.14*nz
tau_b=0.12+0.30*nz
tau=np.clip(np.where(la>0.05,tau_l*la+tau_b*(1-la),tau_b),0,0.55)
tau=cv2.GaussianBlur(tau,(0,0),1.2)
t8=(tau/0.55*255).astype(np.uint8); Image.fromarray(np.dstack([t8,t8,t8]),'RGB').save('out/sky-time.png')
json.dump({'band':[BX,BY,BW,BH],'offsets':{int(k):[float(v[1]),float(v[2])] for k,v in offs.items()}},open('out/sky.json','w'),indent=1)
cv2.imwrite('out/sky-compare.png',cv2.resize(np.vstack([S,T]),None,fx=2,fy=2,interpolation=cv2.INTER_LANCZOS4))
print(n-1,'letter pieces')
