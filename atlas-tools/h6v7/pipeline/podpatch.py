import numpy as np, cv2
A=cv2.imread('out/possible-aligned.png'); H,W=A.shape[:2]
hsv=cv2.cvtColor(A,cv2.COLOR_BGR2HSV).astype(np.int32)
h,s,v=hsv[...,0],hsv[...,1],hsv[...,2]
x0,x1,y0,y1=1040,1342,440,500
reg=np.zeros((H,W),bool); reg[y0:y1,x0:x1]=True
# reeds: green/yellow-green blades and yellow flowers; not the warm timber (hue<20) nor near-black body
reed=reg&(((h>=22)&(h<=95)&(s>60)&(v>58)))
yy,xx=np.mgrid[0:H,0:W]
glaz=reg&(yy<467)&(xx<1196)
reed&=~glaz | ((h>=24)&(h<=48)&(s>110)&(yy>=454))          # behind the glass only clear yellow-green blades
body=reg&(xx>=1196)
reed|=body&((v>78)|(s>70))&(yy>=446)&~((h<=22)&(s>60)&(xx<1212))                       # anything on the near-black body that is not dark cladding
reed|=reg&(s<55)&(v>95)&(xx>=1150)&(xx<1262)&(yy>=478)          # pool-edge boulder tops in front of the deck
reed=cv2.dilate(reed.astype(np.uint8),np.ones((3,3),np.uint8))>0
reed&=reg
P=A.copy()
# deck: horizontal grain -> nearest clean pixel in the row (left first)
for y in range(466,494):
    for x in range(1040,1200):
        if reed[y,x]:
            for d in range(1,160):
                if x-d>=900 and not reed[y,x-d]: P[y,x]=P[y,x-d]; break
# body: vertical seams -> nearest clean pixel above in the column
for x in range(1196,1331):
    for y in range(440,500):
        if reed[y,x]:
            for d in range(1,60):
                if not reed[y-d,x]: P[y,x]=(P[y-d,x].astype(np.float32)*max(0.82,1-0.004*(y-440))).astype(np.uint8); break
# glazing/interior band: Telea inpaint
g=np.zeros((H,W),np.uint8); g[440:467,1040:1200]=reed[440:467,1040:1200]
P=cv2.inpaint(P,g,5,cv2.INPAINT_TELEA)
sm=cv2.GaussianBlur(P,(0,0),0.8); P=np.where(reed[...,None],sm,P)
cv2.imwrite('out/pod-reedfree.png',P); np.save('out/pod-reedmask.npy',reed)
c=np.vstack([A[430:505,1030:1345],P[430:505,1030:1345]]); cv2.imwrite('out/podpatch-view.png',cv2.resize(c,None,fx=2.5,fy=2.5,interpolation=cv2.INTER_NEAREST))
