#!/usr/bin/env python3
"""Business rental publication checks and targeted guard mutation proof."""
import copy, hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"atlas-tools"))
import plotart_business_rental as B
import plotart_seo as SEO
checks=[]
def check(name,ok):
    checks.append(bool(ok));print(("PASS " if ok else "FAIL ")+name)
page=(ROOT/"plotart/art-for-hire/index.html").read_text()
outside=B.outside(page)
css_version=hashlib.sha256((ROOT/"plotart/art-for-hire/art-for-hire.css").read_bytes()).hexdigest()[:12]
check("stylesheet cache key matches the current CSS",'href="art-for-hire.css?v='+css_version+'"' in page)
check("one exact approved business section",page.count(B.BEGIN)==1 and page.count(B.END)==1)
check("business link independent of the live catalogue CTA",'href="#business-rentals">Business rentals' in page and 'href="#afh3-how" data-hire-cta' in page)
check("closed enquiry form unchanged",'data-enquiries="off"' in page and '<form' not in page)
check("no public artist rental inventory invented",'class="pa-hire-card"' not in page)
check("download is the verified template",B.verify_document(ROOT,ROOT))
pdf=ROOT/"plotart"/B.PDF
reader=PdfReader(pdf)
text="\n".join(p.extract_text() or "" for p in reader.pages)
for term in ("4%","3%","1%","75% / 25%","six calendar months","30 calendar days","seven calendar days","14 calendar days"):
    check("template contains "+term,term in text)
check("PDF contains no JavaScript or signature form",not reader.get_fields() and "/JavaScript" not in str(reader.trailer))
check("all template pages have readable text",len(reader.pages)>0 and all(len(p.extract_text() or "")>300 for p in reader.pages))
check("current page indexable through its explicit switch",SEO.indexable("art-for-hire/index.html",SEO.switches()))
check("switch off excludes rental page from search",not SEO.indexable("art-for-hire/index.html",dict(SEO.switches(),business_rental_information=False)))
check("disabled hire page cannot become indexable",not SEO.indexable("art-for-hire/index.html",dict(SEO.switches(),art_for_hire_page=False)))
check("sale priority and approval protect artist","Buying is the priority." in page and "Each artist approves" in page)
check("company costs and no artist advance are explicit","The renting business pays" in page and "Neither artist nor PlotArt" in page)
check("replacement fallback and refund are explicit","If none is agreed" in page and "refunded within 14 days" in page)
for price,total,owner,fee in [(100000,4000,3000,1000),(200000,8000,6000,2000),(500000,20000,15000,5000),(99999,4000,3000,1000)]:
    t=(price*4+50)//100;o=(price*3+50)//100
    check("fee arithmetic "+str(price),t==total and o==owner and t-o==fee)
# A changed pinned page must fail on the content rules even after an attacker
# re-pins that changed page. Use independent copies for the fixture and atomic file
# replacement so no source file can be modified by a fixture mutation.
manifest=json.loads((ROOT/"atlas-tools/release/plotart-launch-manifest.json").read_text())
sw=ROOT/"atlas-tools/release/plotart-launch-switches.json"
def atomic(path,raw):
    temp=path.with_suffix(path.suffix+".test-write")
    temp.write_bytes(raw);os.replace(temp,path)
with tempfile.TemporaryDirectory(prefix="plotart-rental-proof-") as tmp:
    site=Path(tmp)/"site";site.mkdir()
    for child in ROOT.iterdir():
        if child.name in (".git",".openai"):continue
        if child.name=="plotart":shutil.copytree(child,site/child.name,copy_function=shutil.copy2)
        else:(site/child.name).symlink_to(child,target_is_directory=child.is_dir())
    target=site/"plotart/art-for-hire/index.html"
    for label,mutate,wanted in [
        ("wrong customer rate",lambda x:x.replace("<strong>4%","<strong>5%",1),"L19"),
        ("wrong artist split",lambda x:x.replace("3% to the artist","2% to the artist",1),"L19"),
        ("duplicate terms",lambda x:x+B.REGION,"L19"),
        ("unapproved fee outside the bounded section",lambda x:x.replace("</main>","<p>Extra 9% fee</p></main>"),"L17"),
        ("new public enquiry form",lambda x:x.replace("</main>","<form></form></main>"),"L17"),
    ]:
        changed=mutate(page).encode();atomic(target,changed)
        m=copy.deepcopy(manifest)
        m["files"]["art-for-hire/index.html"]=hashlib.sha256(changed).hexdigest()
        a=changed.index(b"<!-- pa-hire-catalogue:begin -->");z=changed.index(b"<!-- pa-hire-catalogue:end -->")+len(b"<!-- pa-hire-catalogue:end -->")
        m["outside_hire_catalogue"]["art-for-hire/index.html"]=hashlib.sha256(changed[:a]+b"<!-- catalogue -->"+changed[z:]).hexdigest()
        mp=Path(tmp)/"manifest.json";mp.write_text(json.dumps(m))
        r=subprocess.run([sys.executable,str(ROOT/"atlas-tools/prove-plotart-launch.py"),str(site),"--switches",str(sw),"--manifest",str(mp)],capture_output=True,text=True)
        check("guard refuses "+label,r.returncode!=0 and wanted in r.stdout+r.stderr)
    atomic(target,page.encode())
    bad=site/"plotart"/B.PDF;atomic(bad,b"%PDF-corrupted")
    try:B.verify_document(site,ROOT);refused=False
    except ValueError:refused=True
    check("independent document record refuses a corrupted PDF",refused)
print("Business rental publication:",sum(checks),"/",len(checks),"passed")
sys.exit(0 if all(checks) else 1)

