import numpy as np, cv2, json
B=cv2.imread('in/hero-before-master.png'); P=cv2.imread('in/hero-possible-master.png')
print(B.shape,P.shape)
# Compare row content near top and bottom to decide how the 1px differs
gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY).astype(np.float32); gP=cv2.cvtColor(P,cv2.COLOR_BGR2GRAY).astype(np.float32)
# Tile phase correlation on regions
res=[]
for (name,x0,y0,x1,y1) in [('sky-left',760,20,1000,180),('sky-right',1150,20,1450,150),('house',360,230,560,330),('house2',560,230,760,300),('chimney',680,140,740,220),('patio',560,360,760,440),('neigh-right',1250,160,1550,250),('path-low',320,700,480,930),('foxglove',0,520,300,900),('tree-trunk',20,250,120,520),('hedge-mid',830,240,1000,330),('purple-tree',870,200,1010,280),('lawn-mid',480,480,700,600)]:
    a=gB[y0:y1,x0:x1]; b=gP[y0:y1,x0:x1]
    win=cv2.createHanningWindow((x1-x0,y1-y0),cv2.CV_32F)
    (dx,dy),r=cv2.phaseCorrelate(a,b,win)
    res.append((name,round(dx,2),round(dy,2),round(r,3), round(float(np.abs(a-b).mean()),1)))
for r in res: print(r)
