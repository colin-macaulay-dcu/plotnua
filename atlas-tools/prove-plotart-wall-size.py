#!/usr/bin/env python3
"""Reviewed static shell, search boundary and privacy for the public size tool."""
import json,runpy,re,sys
from pathlib import Path
from html.parser import HTMLParser
import plotart_seo as S
ROOT=Path(__file__).resolve().parent.parent
B=runpy.run_path(str(ROOT/'atlas-tools/build-plotart-wall-size.py'))
checks=[]
def check(name,ok):
 checks.append(ok);print(('PASS ' if ok else 'FAIL ')+name)
class Page(HTMLParser):
 def __init__(self,doc):super().__init__();self.ids=[];self.links=[];self.inputs=[];self.h1=0;self.forms=0;self.feed(doc)
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if a.get('href'):self.links.append(a['href'])
  if t=='input':self.inputs.append(a)
  self.h1+=t=='h1';self.forms+=t=='form'
doc=(ROOT/'plotart'/B['PATH']).read_text();page=Page(doc)
check('exact reviewed tool shell',doc==B['render']())
check('one H1 and unique IDs',page.h1==1 and len(page.ids)==len(set(page.ids)))
check('every local link and anchor resolves',all((ref[1:] in page.ids if ref.startswith('#') else (ROOT/'plotart'/ref.split('#')[0]/('index.html' if ref.endswith('/') else '')).exists()) for ref in page.links if not ref.startswith(('http','mailto:','/'))))
check('indexable with correct canonical',S.head(B['PATH'],'t','d').splitlines()[0]=='<meta name="robots" content="index, follow">' and 'href="'+S.canonical(B['PATH'])+'"' in doc)
check('tool is excluded when switch is off',not S.indexable(B['PATH'],dict(S.switches(),wall_size_indexable=False)))
check('tool enters generated sitemap exactly once',S.sitemap_paths(S.public_packages(ROOT),S.switches()).count(B['PATH'])==1)
check('no artist data copied into tool','Leah Hewson' not in doc and '/artists/' not in doc)
check('no upload, email collection or form',not page.forms and all(a.get('type') in ('number','text') for a in page.inputs) and not any(a.get('type')=='text' and 'readonly' not in a for a in page.inputs))
check('all size controls have visible labels',all('for="'+a['id']+'"' in doc for a in page.inputs if a.get('type')=='number'))
check('no-JavaScript advice is included','<noscript>' in doc and '133–150 cm' in doc and 'guide below' in doc)
check('source and limits are stated','saatchiart.com/pages/art-for-the-living-room' in doc and 'including any frame' in doc and '75 cm high' in doc)
check('live result and SVG have accessible descriptions','aria-live="polite"' in doc and 'aria-labelledby="size-svg-title size-svg-desc"' in doc)
js=(ROOT/'plotart/assets/plotart-wall-size.js').read_text()
check('calculator has no network, cookie, storage, upload or external scripts',not re.search(r'\bfetch\s*\(|XMLHttpRequest|localStorage|sessionStorage|document\.cookie|sendBeacon|https?://',js))
check('DOM updates use text, not HTML insertion','innerHTML' not in js and 'outerHTML' not in js and 'insertAdjacentHTML' not in js)
check('shared dimensions stay in URL fragment',"return '#'+params.toString()" in js and 'location.origin+location.pathname+encode(lastValid)' in js)
check('tool is linked from homepage and buyer guide',all('href="art-size-calculator.html"' in (ROOT/'plotart'/p).read_text() for p in ['index.html','buy-original-art-ireland.html']))
print('WALL SIZE PAGE · %d/%d passed'%(sum(checks),len(checks)));sys.exit(0 if all(checks) else 1)
