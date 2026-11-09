"""Pool water without the garden room's warm reflections (used by the pool layer), and those reflections as a
conditional layer shown only when both the Garden Room and the pool are on."""
import numpy as np, cv2
A=cv2.imread('out/possible-aligned.png'); H,W=A.shape[:2]
lab=cv2.cvtColor(A,cv2.COLOR_BGR2LAB).astype(np.float32)
m=np.zeros((H,W),np.float32)
cv2.ellipse(m,(946,602),(30,44),0,0,360,1,-1)
cv2.ellipse(m,(1160,646),(34,54),0,0,360,1,-1)
hard=m.copy(); m=cv2.GaussianBlur(m,(0,0),6)
w=(1-cv2.dilate(hard,np.ones((9,9),np.uint8)))
def nconv(x,s): return cv2.GaussianBlur(x*w,(0,0),s)/np.maximum(cv2.GaussianBlur(w,(0,0),s),1e-4)
lo=np.dstack([cv2.GaussianBlur(lab[...,c],(0,0),4) for c in range(3)])
sur=np.dstack([nconv(lo[...,c],22) for c in range(3)])
out=lab+(sur-lo)*m[...,None]
noref=cv2.cvtColor(np.clip(out,0,255).astype(np.uint8),cv2.COLOR_LAB2BGR)
cv2.imwrite('out/pool-noreflection.png',noref); np.save('out/reflection-alpha.npy',m)
v=np.vstack([A[540:720,880:1230],noref[540:720,880:1230]]); cv2.imwrite('out/reflection-view.png',cv2.resize(v,None,fx=2,fy=2))
