#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUARD-CAPABILITY PROOF — refresh-ui-kit.py v2 (27 Oct 2026).

Each case patches the kit's own source (or what it reads) once and runs it in
--check mode, so neither template is ever written. Every case must REFUSE.

Run: python3 supplier-preview-system/prove-refresh-ui-kit.py
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE / "refresh-ui-kit.py"
TPL = [HERE / "template-provider-led.html", HERE / "template-product-led.html"]
BEFORE = [hashlib.sha256(p.read_bytes()).hexdigest() for p in TPL]

CASES = [
    ("the image position gains rights-process copy",
     '<div class="pn-photo-slot"><b>Your image here</b></div>',
     '<div class="pn-photo-slot"><b>Your image here</b><span>stay yours until you say</span></div>', "HERO"),
    ("the old light shell comes back",
     '</head>\n<body class="pn-id pn-id--dark pn-sp">', '</head>\n<body>', "KIT"),
    ("the demo leaves production\'s Results chain",
     '<div class="results-hero" id="matchPrimary">', '<div class="results-hero">', "KIT"),
    ("the v1 demo ending is restored (slicing builders would break silently)",
     "    </div><!-- /pn-stage -->", "    </div>", "KIT"),
    ("a builder anchor moves",
     '\n  <div class="screen">\n    <div class="screen-chrome">', '\n  <div class="screen frame">\n    <div class="screen-chrome">', "KIT"),
    ("commercial wording enters the template",
     "<h2>Why this could be useful</h2>", "<h2>Why our referral partners like this</h2>", "KIT"),
    ("the illustrative label is repeated",
     "<p>{{DEMO_LEDE}}</p>", "<p>{{DEMO_LEDE}} Illustrative only.</p>", "KIT"),
    ("a supplier remnant reaches the template",
     "Prepared for {{SUPPLIER_NAME}}", "Prepared for {{SUPPLIER_NAME}} (as with Modulux)", "KIT"),
    ("the robots directive is weakened",
     "noindex, nofollow, noarchive, nosnippet, noimageindex", "noindex, nofollow", "KIT"),
    ("the provider template gains an image",
     '<div class="pn-photo-slot"><b>Your image here</b></div>',
     '<div class="pn-photo-slot"><b>Your image here</b></div><img src="x.jpg" alt="">', "HERO"),
    ("the skin scope is not re-scoped",
     "css = re.sub(r'/\\*.*?\\*/', '', css, flags=re.S)" , "", "NOOP"),
    ("an html-scoped skin selector survives",
     "    return W_SKIN + rest\n", "    return 'html[data-pn-skin=\"your-plot\"]' + rest\n", "KIT"),
]


def run(old, new, where):
    src = KIT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as d:
        kitdir = pathlib.Path(d) / "kit"
        kitdir.mkdir()
        for f in (HERE / "kit").iterdir():
            text = f.read_text(encoding="utf-8")
            if where == "HERO" and f.name == "hero-provider.html":
                if old not in text:
                    return "ANCHOR MISSING"
                text = text.replace(old, new, 1)
            (kitdir / f.name).write_text(text, encoding="utf-8")
        if where == "KIT":
            if old not in src:
                return "ANCHOR MISSING"
            src = src.replace(old, new, 1)
        src = src.replace("KIT = os.path.join(HERE, 'kit')", "KIT = %r" % str(kitdir))
        src = src.replace("    if not CHECK:\n        open(path, 'w', encoding='utf-8').write(h)\n", "    pass\n")
        tmp = pathlib.Path(d) / "kit_under_test.py"
        tmp.write_text(src.replace("HERE = os.path.join(REPO, 'supplier-preview-system')",
                                   "HERE = %r" % str(HERE)).replace(
            "REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
            "REPO = %r" % str(HERE.parent)), encoding="utf-8")
        r = subprocess.run([sys.executable, str(tmp), "--check"], capture_output=True, text=True)
        return (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else ""


caught = n = 0
print("GUARD-CAPABILITY PROOF — refresh-ui-kit.py v2")
print("=" * 78)
base = run("", "", "NONE")
ok_base = "GUARD FAILED" not in base
print(("  OK      " if ok_base else "  MISSED  ") + "the unmodified kit passes  -> " + base[:70])
for name, old, new, where in CASES:
    if where == "NOOP":
        continue
    n += 1
    out = run(old, new, where)
    hit = out.startswith("GUARD FAILED")
    caught += hit
    print(("  CAUGHT  " if hit else "  MISSED  ") + name + "\n           -> " + out[:110])
print("=" * 78)
print("%d of %d planted faults caught; unmodified kit %s" % (caught, n, "passes" if ok_base else "FAILS"))
after = [hashlib.sha256(p.read_bytes()).hexdigest() for p in TPL]
print("templates untouched by this proof: %s" % ("YES" if after == BEFORE else "NO"))
sys.exit(0 if (caught == n and ok_base and after == BEFORE) else 1)
