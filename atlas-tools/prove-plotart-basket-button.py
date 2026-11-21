"""PROVE · multi-artist basket entry point on published artwork pages (21 Nov 2026).
Without basket_origin (the default and today's configuration) every page is byte-for-byte what it was; with it, only
AVAILABLE artworks gain a hidden basket block and the pa-basket.js script.  python3 atlas-tools/prove-plotart-basket-button.py"""
import json, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plotart_gallery_pages as P  # noqa: E402
ok = []
def check(n, c):
    ok.append(bool(c)); print(("  PASS  " if c else "  FAIL  ") + n)
pkgs = []
for f in sorted(glob.glob(os.path.join(ROOT, "plotart", "artists", "*", "gallery.json")))[:6]:
    pkgs.append(json.load(open(f, encoding="utf-8")))
page = lambda path, title, desc, body, scripts: (path, "<html><head><title>%s</title></head><body>%s<script>%s</script></body></html>" % (title, body, ",".join(scripts)))
before = [P.gallery_pages(p, page, enquiry_endpoint="https://plotart-enquiry.example.workers.dev/v1/enquiry") for p in pkgs]
same = [P.gallery_pages(p, page, enquiry_endpoint="https://plotart-enquiry.example.workers.dev/v1/enquiry", basket_origin=None) for p in pkgs]
check("B1 basket_origin unset: every artist and artwork page is identical to today's", before == same and len(pkgs) > 0)
on = [P.gallery_pages(p, page, enquiry_endpoint="https://plotart-enquiry.example.workers.dev/v1/enquiry", basket_origin="https://plotart-checkout.example.workers.dev") for p in pkgs]
avail = blocks = other = 0
for pk, pages in zip(pkgs, on):
    ws = {w["slug"]: w for w in P.shown(pk)}
    for path, doc in pages:
        slug = path.rsplit("/", 1)[-1][:-5]
        if slug in ws:
            has = 'class="pa-basket"' in doc
            if ws[slug]["availability"] == "available":
                avail += 1; blocks += has and 'hidden>' in doc and "pa-basket.js" in doc and 'data-pa-artwork="%s"' % ws[slug]["id"] in doc
            else:
                other += has
        else:
            other += 'class="pa-basket"' in doc
check("B2 basket_origin set: every AVAILABLE artwork gains the hidden basket block and pa-basket.js (%d of %d)" % (blocks, avail), avail > 0 and blocks == avail)
check("B3 sold, reserved and not-for-sale works and artist pages never show a basket block", other == 0)
js = open(os.path.join(ROOT, "plotart", "assets", "pa-basket.js"), encoding="utf-8").read()
check("B4 pa-basket.js reveals the button only when the checkout Worker confirms the work can be bought online; omits cookies", "box.hidden = false" in js and "j.items[0].ok" in js and "credentials: 'omit'" in js)
print("\nBASKET ENTRY POINT · %d checks, %d passed, %d failed" % (len(ok), sum(ok), len(ok) - sum(ok)))
sys.exit(0 if all(ok) else 1)
