#!/usr/bin/env python3
"""
PROOF · the Discovery Library card labels can only say what is true (1 Nov 2026).

Copies the files the label builder reads into a scratch tree, plants one fault at a time, and requires
atlas-tools/build-library-card-labels.py to refuse it (build) or report it (--check). A positive control (the
untouched tree) must pass. Nothing in the real tree is written.

  python3 atlas-tools/prove-library-card-labels.py
"""
import json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILDER = "atlas-tools/build-library-card-labels.py"
MAPF = "atlas-tools/discovery-library-labels.json"


def files():
    out = {"discoveries.html", BUILDER, MAPF, "image-provenance-records.json"}
    m = json.loads((ROOT / MAPF).read_text(encoding="utf-8"))
    for href in m["cards"]:
        out.add(href)
        out.update(re.findall(r'href="(disc\d{3}-[a-z0-9-]+\.html)', (ROOT / href).read_text(encoding="utf-8")))
    return sorted(f for f in out if (ROOT / f).exists())


def run(tree, *args):
    p = subprocess.run([sys.executable, str(tree / BUILDER), *args], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1:] or [""]


def edit(tree, rel, fn):
    p = tree / rel
    p.write_text(fn(p.read_text(encoding="utf-8")), encoding="utf-8")


def mapping(tree, fn):
    p = tree / MAPF
    m = json.loads(p.read_text(encoding="utf-8")); fn(m); p.write_text(json.dumps(m), encoding="utf-8")


def register(tree, fn):
    p = tree / "image-provenance-records.json"
    r = json.loads(p.read_text(encoding="utf-8")); fn(r); p.write_text(json.dumps(r), encoding="utf-8")


FAULTS = [
    ("a label claims a check that does not exist (Natural Swimming Garden)", "build",
     lambda t: mapping(t, lambda m: m["cards"].__setitem__("discovery-natural-swimming-garden.html", "property-check"))),
    ("a check page has gone (Hidden Cars)", "build",
     lambda t: (t / "disc022-hidden-cars-check.html").unlink()),
    ("a check page says it is being prepared (Hidden Bins)", "build",
     lambda t: edit(t, "disc029-hidden-bins-check.html", lambda s: s.replace("</body>", "<p>This check is being prepared.</p></body>", 1))),
    ("a check page has become a redirect (Driveway Income)", "build",
     lambda t: edit(t, "disc014-driveway-income.html", lambda s: s.replace("<head>", '<head><meta http-equiv="refresh" content="0;url=index.html">', 1))),
    ("a label word outside the closed vocabulary", "build",
     lambda t: mapping(t, lambda m: m["cards"].__setitem__("discovery-hidden-cars.html", "book-now"))),
    ("a live check left without its label (Hidden Cars set to none)", "build",
     lambda t: mapping(t, lambda m: m["cards"].__setitem__("discovery-hidden-cars.html", None))),
    ("'Meet the makers' without the maker gallery (Garden Retreat)", "build",
     lambda t: edit(t, "discovery-garden-retreat.html", lambda s: s.replace("data-pn-supplier-gallery", "data-x-gallery"))),
    ("'Find what fits' without the brief (Above and Beyond)", "build",
     lambda t: edit(t, "discovery-above-and-beyond.html", lambda s: s.replace("Show me what fits", "Show me"))),
    ("'Garden room journey' without the journey link", "build",
     lambda t: edit(t, "discovery-living-in-the-garden.html", lambda s: s.replace('href="your-plot.html?discovery=garden-room"', 'href="your-plot.html"'))),
    ("'Journey coming soon' put back on a card", "check",
     lambda t: edit(t, "discoveries.html", lambda s: s.replace('<span class="lib-cat">Income</span>', '<span class="lib-cat">Income</span>\n          <span class="lib-soon">Journey coming soon</span>', 1))),
    ("'live' put back into a label", "check",
     lambda t: edit(t, "discoveries.html", lambda s: s.replace('<span class="lib-act">Property check</span>', '<span class="lib-act">Property check live</span>', 1))),
    ("the AI chip removed from a declared image", "check",
     lambda t: edit(t, "discoveries.html", lambda s: s.replace('<span class="lib-aichip">AI-generated illustration</span>', "", 1))),
    ("an AI chip added to a legacy (undeclared) image", "check",
     lambda t: edit(t, "discoveries.html", lambda s: s.replace('alt="A woman', 'alt="A woman', 1).replace(
         '</picture></span>', '</picture><span class="lib-aichip">AI-generated illustration</span></span>', 1))),
    ("the AI chip reworded", "check",
     lambda t: edit(t, "discoveries.html", lambda s: s.replace('<span class="lib-aichip">AI-generated illustration</span>', '<span class="lib-aichip">AI image</span>', 1))),
    ("a declared record withdrawn from the register while its chip stays", "check",
     lambda t: register(t, lambda r: [x.__setitem__("class", "WITHDRAWN") for x in r["records"] if x["asset"] == "assets/disc031/img/DISC-031-experience-960.jpg"])),
    ("an action label added by hand to a card with no tool (Supper Club)", "check",
     lambda t: edit(t, "discoveries.html", lambda s: s.replace(
         "someone else&rsquo;s favourite restaurant?</span>", "someone else&rsquo;s favourite restaurant?</span>\n        <span class=\"lib-act\">Property check</span>", 1))),
]


def main():
    fl = files()
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d) / "base"
        for f in fl:
            (base / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / f, base / f)
        tree = pathlib.Path(d) / "t"
        shutil.copytree(base, tree)
        rc, out = run(tree, "--check")
        if rc != 0:
            print("PROOF FAILED · the untouched tree does not pass: %s" % out[0]); sys.exit(1)
        print("  OK      POSITIVE CONTROL: the untouched tree passes")
        missed = []
        for name, mode, fault in FAULTS:
            shutil.rmtree(tree); shutil.copytree(base, tree)
            fault(tree)
            before = (tree / "discoveries.html").read_bytes()
            rc, out = run(tree, *(["--check"] if mode == "check" else []))
            unchanged = (tree / "discoveries.html").read_bytes() == before
            caught = rc != 0 and (mode == "check" or unchanged)
            print("  %s  %s  (%s)" % ("CAUGHT " if caught else "MISSED ", name, out[0][:110]))
            if not caught: missed.append(name)
    if missed:
        print("PROOF FAILED · not caught: " + "; ".join(missed)); sys.exit(1)
    print("LIBRARY CARD LABELS PROOF · OK — %d planted faults, all caught; positive control passes" % len(FAULTS))


if __name__ == "__main__":
    main()
