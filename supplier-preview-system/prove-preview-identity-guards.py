#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD-CAPABILITY PROOF — build-preview-identity-band.py.

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught.

Two sabotage channels, for the same reason the production proof needed two:
  B(...)  patches the BUILDER's own source — the strings its edits install.
  S(...)  patches the SOURCE it reads — production your-plot.html, or a
          template — for the guards that assert something about material the
          builder does not itself write.

The builder runs in --check mode throughout, so neither template is written
by this proof. Both are hashed before and after and the hashes are printed.

Run: python3 prove-preview-identity-guards.py
"""
import contextlib
import hashlib
import importlib.util
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-preview-identity-band.py"
TPL = {"provider": HERE / "template-provider-led.html",
       "product": HERE / "template-product-led.html"}
PROD = HERE.parent / "your-plot.html"

BEFORE = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in TPL.items()}
_n = [0]

READ_PROD = 'prod = PROD.read_text(encoding="utf-8")'
READ_TPL = 't = path.read_text(encoding="utf-8")'


def _exec(builder_subs, prod_subs, tpl_subs):
    code = BUILDER.read_text(encoding="utf-8")
    for old, new in builder_subs:
        if old not in code:
            raise AssertionError("builder anchor absent: %r" % old[:70])
        code = code.replace(old, new, 1)
    if prod_subs:
        live = PROD.read_text(encoding="utf-8")
        for old, _ in prod_subs:
            if old not in live:
                raise AssertionError("production anchor absent: %r" % old[:70])
        code = code.replace(READ_PROD, READ_PROD + "\nfor _o,_nn in %r:\n"
                            "    prod = prod.replace(_o,_nn)" % (prod_subs,), 1)
    if tpl_subs:
        for old, _ in tpl_subs:
            if old not in TPL["provider"].read_text(encoding="utf-8"):
                raise AssertionError("template anchor absent: %r" % old[:70])
        code = code.replace(READ_TPL, READ_TPL + "\n    for _o,_nn in %r:\n"
                            "        t = t.replace(_o,_nn,1)" % (tpl_subs,), 1)
    _n[0] += 1
    spec = importlib.util.spec_from_file_location("pib%d" % _n[0], BUILDER)
    mod = importlib.util.module_from_spec(spec)
    exec(compile(code, str(BUILDER), "exec"), mod.__dict__)


def run(label, builder_subs=(), prod_subs=(), tpl_subs=(), expect="REFUSED"):
    argv, buf, rc = sys.argv, io.StringIO(), 0
    sys.argv = [str(BUILDER), "--check"]
    try:
        with contextlib.redirect_stdout(buf):
            _exec(list(builder_subs), list(prod_subs), list(tpl_subs))
    except SystemExit as e:
        rc = e.code or 0
    finally:
        sys.argv = argv
    out = buf.getvalue().strip().splitlines()
    got = "REFUSED" if rc else "BUILT"
    hit = got == expect
    print("  %s %-7s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("           -> %s" % (out[0][:116] if out else "(no output)"))
    return hit


print("GUARD-CAPABILITY PROOF -- SUPPLIER PREVIEW IDENTITY BAND")
print("=" * 78)
r = []

# ---- P01 . production must actually carry the committed block -------------
r.append(run("P01 . production has no RESULTS-IDENTITY-001 block",
             prod_subs=[("RESULTS-IDENTITY-001", "RESULTS-IDENTITY-XXX")]))

# ---- P02 . the lifted block must carry the authorised geometry ------------
r.append(run("P02 . the 58% media width is missing from the lift",
             prod_subs=[("width:58%; min-width:0; max-width:58%; flex:0 0 58%;",
                         "width:55%; min-width:0; max-width:55%; flex:0 0 55%;")]))

r.append(run("P02 . the identity meta loses its fixed minimum height",
             prod_subs=[("gap:0 10px; min-height:26px;", "gap:0 10px;")]))

# ---- P03 . nothing production-scoped may reach the preview ----------------
r.append(run("P03 . a production-only scope survives the re-scope",
             builder_subs=[('.replace("#screen-match-results ", ".pn-stage ")',
                            '.replace("#screen-match-results ", "#screen-match-results ")')]))

# ---- T00 . idempotence ----------------------------------------------------
r.append(run("T00 . refuses when the band is already in the template",
             tpl_subs=[('<div class="results-hero-inner">',
                        '<div class="results-hero-inner rh-identity-already">')]))

# ---- G1 . the name must leave the decision column -------------------------
r.append(run("G1 . the product name is left in the decision column",
             builder_subs=[('''    NEW_HEAD = """        <div class="results-hero-body">''',
                            '''    NEW_HEAD = """        <div class="results-hero-body">
          <h2 class="results-hero-name">LEFT BEHIND</h2>''')]))

# ---- G2 . the band carries nothing but name + supplier + price ------------
r.append(run("G2 . the price basis is dragged into the identity band",
             builder_subs=[("'            <span class=\"results-hero-price\">{{VERIFIED_PRICE}}</span>\\n'",
                            "'            <span class=\"results-hero-price\">{{VERIFIED_PRICE}}</span>\\n'\n                '            <span>{{VERIFIED_PRICE_BASIS}}</span>\\n'")]))

# ---- G3 . split and media column emitted exactly once ---------------------
r.append(run("G3 . the media column is emitted twice",
             builder_subs=[('NEW_MEDIA = """        <div class="pn-media-col">',
                            'NEW_MEDIA = """        <div class="pn-media-col"></div>\n        <div class="pn-media-col">')]))

# ---- G4 . the gallery must really work ------------------------------------
r.append(run("G4 . the gallery handler is removed entirely",
             builder_subs=[("""    t = t.replace("</body>", GALLERY_JS + "</body>", 1)""",
                            """    t = t.replace("</body>", "</body>", 1)""")]))

r.append(run("G4 . the handler stops being data-driven",
             builder_subs=[("var full = btn.getAttribute('data-full');",
                            "var full = btn.getAttribute('href');")]))

r.append(run("G4 . the click can reload the page",
             builder_subs=[("        e.preventDefault();                  /* never reload the page */\n",
                            "")]))

r.append(run("G4 . the credit stops travelling with the picture",
             builder_subs=[("""    if (credit) credit.textContent = btn.getAttribute('data-credit') || '';""",
                            """    /* credit dropped */""")]))

# ---- G6 . privacy ---------------------------------------------------------
r.append(run("G6 . the noindex privacy meta is dropped",
             tpl_subs=[("noindex", "index")]))

# ---- G7 . structural balance ---------------------------------------------
r.append(run("G7 . .rh-split is opened but never closed",
             builder_subs=[("""        </div>
        </div>
      </div>
\"\"\"""", """        </div>
      </div>
\"\"\"""")]))

# ---- the unmutated builder must still pass --------------------------------
print("-" * 78)
r.append(run("the unmutated builder passes for both templates", expect="BUILT"))

AFTER = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in TPL.items()}
print("=" * 78)
print("%d of %d checks passed" % (sum(1 for x in r if x), len(r)))
for k in TPL:
    same = BEFORE[k] == AFTER[k]
    print("%-10s untouched by this proof: %s  (%s)"
          % (k, "YES" if same else "NO", AFTER[k][:12]))
sys.exit(0 if all(r) and BEFORE == AFTER else 1)
