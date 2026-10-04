"""
ATLAS -- GUARD-CAPABILITY PROOF FOR THE APPROVED STATIC MARK.

A proof that passes tells you nothing until you know it can fail. This breaks
the shipped page and the shipped asset one change at a time and requires the
Atlas proofs to catch every one, with a clean control before and after.

It earned two of its cases the hard way. Swapping createElement('img') for
createElement('video') was MISSED on the first run, because the retirement
check searched for the string "<video" and the retired implementation built its
player in JS -- so the JS route is now a case of its own. And re-pointing the
masthead at the opaque asset is a case because that is the exact defect the
founder reported after the first static build shipped.

Run from anywhere:  python3 atlas-tools/prove-atlas-static-capability.py
"""
import pathlib, shutil, subprocess, tempfile, os, sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
src=(ROOT/'your-plot.html').read_text()
BREAKS=[
 ('A','remove the approved static asset reference',
  "mastImg.src = 'assets/brand/atlas-final-static-approved-transparent.png';",
  "mastImg.src = 'assets/brand/other.png';",1),
 ('A','revert to the opaque asset',
  "mastImg.src = 'assets/brand/atlas-final-static-approved-transparent.png';",
  "mastImg.src = 'assets/brand/atlas-final-static-approved.png';",1),
 ('A','animate the static mark',
  "  .pn-atlas-still{\n    display:inline-block;",
  "  .pn-atlas-still{\n    animation:spin 2s linear infinite;\n    display:inline-block;",1),
 ('A','blend the static mark',
  "  .pn-atlas-still-img{\n    display:block;",
  "  .pn-atlas-still-img{\n    mix-blend-mode:multiply;\n    display:block;",1),
 ('A','bring the video element back',
  "const mastImg = document.createElement('img');",
  "const mastImg = document.createElement('video');",1),
 ('A','shrink the 60px box',
  "    width:60px; height:60px;\n  }",
  "    width:44px; height:44px;\n  }",1),
 ('A','change the narrow-width box',
  ".pn-atlas-still{ width:48px; height:48px; }",
  ".pn-atlas-still{ width:52px; height:52px; }",1),
 ('A','drop aria-hidden from the static image',
  "mastImg.setAttribute('aria-hidden', 'true');",
  "mastImg.setAttribute('data-x', 'true');",1),
 ('A','drop the 1:1 intrinsic ratio',
  "aspect-ratio:1 / 1; object-fit:contain;",
  "object-fit:contain;",1),
 ('A','revive the retired 60px class',
  "  .pn-atlas-still{",
  "  .pn-atlas-mark--60{ width:60px; height:54px; }\n  .pn-atlas-still{",1),
 ('H','reintroduce an ambient drift rule',
  "  .pn-atlas-still{",
  "  .pn-atlas-mark--60 .pn-am-dark{ animation-name:pn-atlas-a-drift-dark; }\n  .pn-atlas-still{",1),
 ('H','animate a ribbon field again',
  "  .pn-atlas-still{",
  "  .pn-atlas-a .pn-am-sage{ animation-name:wobble; }\n  .pn-atlas-still{",1),
 ('H','remove EVERY shipped slot',
  '<span class="pn-atlas-slot" data-atlas-size="24"></span>',
  '<span class="pn-atlas-x" data-atlas-size="24"></span>',0),
]
PROOF={'A':'atlas-tools/prove-atlas-a.mjs',
       'H':'atlas-tools/prove-atlas-hydration-order.mjs',
       'T':'atlas-tools/prove-atlas-transparency.mjs'}

# BREAKS THAT ATTACK THE ASSET ITSELF, not the page. Each rewrites the shipped
# PNG in the copied tree; prove-atlas-transparency.mjs has to notice.
def _asset_breaks(d):
    import numpy as np
    from PIL import Image
    P=os.path.join(d,'assets/brand/atlas-final-static-approved-transparent.png')
    orig=Image.open(P).copy()
    def flatten():      # the whole ground painted back in -- the pale rectangle returns
        a=np.asarray(orig).copy(); a[:,:,3]=255
        Image.fromarray(a,'RGBA').save(P)
        return 'repaint the opaque ground onto the asset'
    def fill_centre():  # the open centre closed up
        a=np.asarray(orig).copy(); h,w=a.shape[:2]
        a[h//2-60:h//2+60, w//2-60:w//2+60, 3]=255
        Image.fromarray(a,'RGBA').save(P)
        return 'close the open centre'
    def redraw():       # clean matte, but the artwork recoloured -- a redraw
        a=np.asarray(orig).copy()
        m=a[:,:,3]==255
        a[:,:,0]=np.where(m, np.clip(a[:,:,0].astype(int)+6,0,255), a[:,:,0])
        Image.fromarray(a,'RGBA').save(P)
        return 'recolour the knot by 6 levels (a redraw with a clean matte)'
    def strip_alpha():  # RGB, no alpha channel at all
        orig.convert('RGB').save(P)
        return 'strip the alpha channel entirely'
    def eat_rim():      # hard-edged matte, anti-aliasing destroyed
        a=np.asarray(orig).copy()
        a[:,:,3]=np.where(a[:,:,3]>=128,255,0).astype('uint8')
        Image.fromarray(a,'RGBA').save(P)
        return 'threshold the rim away (no anti-aliasing left)'
    return orig,P,[flatten,fill_centre,redraw,strip_alpha,eat_rim]
def run(d,proof): return subprocess.run(['node',proof],cwd=d,capture_output=True,text=True)
fails=0
with tempfile.TemporaryDirectory() as t:
    d=os.path.join(t,'repo')
    shutil.copytree(ROOT,d,symlinks=True,ignore=shutil.ignore_patterns('node_modules'))
    for k,pf in sorted(PROOF.items()):
        r=run(d,pf)
        print(f"CONTROL  {pf.split('/')[-1]:36s} exit={r.returncode} {'OK' if r.returncode==0 else 'UNEXPECTED FAIL'}")
        if r.returncode!=0: fails+=1; print(r.stdout[-900:])
    print()
    p=pathlib.Path(d)/'your-plot.html'
    for i,(k,name,old,new,n) in enumerate(BREAKS,1):
        c=src.count(old)
        if c<1:
            print(f"BREAK {i:2d}  MUTATION DID NOT APPLY ({name})"); fails+=1; continue
        mutated = src.replace(old,new,n) if n else src.replace(old,new)
        assert mutated!=src
        p.write_text(mutated)
        r=run(d,PROOF[k]); caught=r.returncode!=0
        print(f"BREAK {i:2d}  {name:40s} [{c} site(s)] -> {PROOF[k].split('/')[-1][6:-4]:26s} {'CAUGHT' if caught else '*** MISSED ***'}")
        if not caught: fails+=1
        p.write_text(src)
    # ---- and now the asset itself
    print()
    orig,P,breaks=_asset_breaks(d)
    for j,mk in enumerate(breaks, len(BREAKS)+1):
        name=mk()
        r=run(d,PROOF['T']); caught=r.returncode!=0
        print(f"BREAK {j:2d}  {name:40s} [the asset] -> {'atlas-transparency':26s} {'CAUGHT' if caught else '*** MISSED ***'}")
        if not caught: fails+=1
        orig.save(P)

    for k,pf in PROOF.items():
        r=run(d,pf)
        if r.returncode!=0: fails+=1; print(f"POST-RESTORE {pf} UNEXPECTED FAIL")
print('\n'+('CAPABILITY PROOF PASSED — every break caught, controls clean'
            if fails==0 else f'CAPABILITY PROOF FAILED — {fails} problem(s)'))
sys.exit(1 if fails else 0)
