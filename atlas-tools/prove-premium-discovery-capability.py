#!/usr/bin/env python3
"""Capability proof for prove-premium-discovery-a-home-for-art.py (Stage 2c).

Plants one fault at a time in a scratch copy of discovery-a-home-for-art.html and
requires the guard to refuse each; the unmodified copy must pass. Also refuses a
tampered BASE snapshot (P0). Nothing in the repository is written.

  python3 atlas-tools/prove-premium-discovery-capability.py
"""
import pathlib, shutil, subprocess, sys, tempfile

TOOLS = pathlib.Path(__file__).resolve().parent
ROOT = TOOLS.parent
GUARD = TOOLS / "prove-premium-discovery-a-home-for-art.py"
PAGE = "discovery-a-home-for-art.html"
fails = 0

def run(d, guard=GUARD):
    p = subprocess.run([sys.executable, str(guard), "--dir", str(d)], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()[0][:120]

def scratch():
    d = pathlib.Path(tempfile.mkdtemp(prefix="pnpd-")); shutil.copy2(ROOT / PAGE, d / PAGE); return d

def sub(d, a, b, count=1):
    t = (d / PAGE).read_text(encoding="utf-8")
    if a not in t: raise SystemExit("proof setup: %r not on the page" % a[:60])
    (d / PAGE).write_text(t.replace(a, b, count), encoding="utf-8")

def ok(c, m):
    global fails
    if not c: fails += 1
    print("  [%s] %s" % ("PASS" if c else "FAIL", m))

d = scratch(); rc, line = run(d); shutil.rmtree(d)
ok(rc == 0, "control: the unmodified page passes (%s)" % line[:70])

MUT = [
 ("P1 title edited", lambda d: sub(d, "<title>A Home for Art", "<title>A Home For Art")),
 ("P1 meta description edited", lambda d: sub(d, 'content="Open your home to an artist', 'content="Open your house to an artist')),
 ("P2 an alt text edited", lambda d: sub(d, 'alt="An artist working on a large canvas', 'alt="An artist painting a large canvas')),
 ("P2 a photograph swapped", lambda d: sub(d, 'src="assets/img/05cab54ac0af83d0.jpg"', 'src="assets/img/c0f5bf000000000.jpg"')),
 ("P3 an outbound reference link removed", lambda d: sub(d, '<a href="https://culturenight.ie/" target="_blank" rel="noopener">Culture Night</a>', "Culture Night")),
 ("P4 a governed anchor renamed", lambda d: sub(d, 'id="live-with-art"', 'id="live-with"')),
 ("P4 navigation reordered", lambda d: sub(d, '<li><a href="#before-anything-arrives">Practical guide</a></li>\n      <li><a href="#discover-your-property">Checks</a></li>',
                                            '<li><a href="#discover-your-property">Checks</a></li>\n      <li><a href="#before-anything-arrives">Practical guide</a></li>')),
 ("P5 TAKE-PART marker removed", lambda d: sub(d, "<!-- PLOTNUA-TAKE-PART", "<!-- TAKE-PART")),
 ("P5 a second artist-register link", lambda d: sub(d, 'href="discoveries.html">See all Discoveries', 'href="artist-register.html">See all Discoveries')),
 ("P5 a check entry without ?start=1", lambda d: sub(d, 'href="disc023-buy-original-irish-art.html?start=1">Explore art for my home', 'href="disc023-buy-original-irish-art.html">Explore art for my home')),
 ("P6 a BASE sentence deleted", lambda d: sub(d, " Mark it on the wall in masking tape before you commit.", "")),
 ("P6 an undeclared new sentence", lambda d: sub(d, "<p>Many artists sell from their own website or studio.", "<p>Most homeowners find this rewarding. Many artists sell from their own website or studio.")),
 ("P7 a caution moved into an expander", lambda d: (sub(d, "<p class=\"pd-small\" style=\"margin-top:16px\">This matching service is not live yet.</p>", ""), sub(d, "If both sides were interested, PlotNua could help make an introduction.</p>", "If both sides were interested, PlotNua could help make an introduction.</p><p>This matching service is not live yet.</p>"))),
 ("P7 the loans caution removed", lambda d: sub(d, "<strong>PlotNua does not currently arrange artwork loans, rentals or placements. Any arrangement would need to be agreed directly with the artist or gallery.</strong>", "<strong>Any arrangement would need to be agreed directly with the artist or gallery.</strong>")),
 ("P8 an earnings claim added", lambda d: sub(d, "Neither is a rate:", "Hosts typically earn up to €500 a season. Neither is a rate:")),
 ("P8 a guarantee added", lambda d: sub(d, "<p>Do not assume a home policy", "<p>PlotNua guarantees every arrangement. Do not assume a home policy")),
 ("P7 the on-view determination requirement removed", lambda d: sub(d, ", but only where Revenue has made a determination for that artist&rsquo;s work. It does not cover USC or PRSI.</p>", ". It does not cover USC or PRSI.</p>")),
 ("P9 determination dropped inside the practical-guide expander", lambda d: sub(d, "up to &euro;50,000 a year, but only where Revenue has made a determination for that artist&rsquo;s work. It does not cover USC or PRSI. It is the artist", "up to &euro;50,000 a year. It does not cover USC or PRSI. It is the artist")),
 ("P5 a form added", lambda d: sub(d, "</main>", "<form action=\"#\"><input name=\"e\"></form></main>")),
]
for name, f in MUT:
    d = scratch(); f(d); rc, line = run(d); shutil.rmtree(d)
    ok(rc != 0, "%s -> refused: %s" % (name, line))

# P0: a tampered snapshot is refused (run a copy of the guard beside a tampered snapshot)
t = pathlib.Path(tempfile.mkdtemp(prefix="pnpd-snap-")); (t / "premium-discovery").mkdir()
shutil.copy2(GUARD, t / GUARD.name)
snap = (TOOLS / "premium-discovery" / "a-home-for-art-base.json").read_text(encoding="utf-8")
(t / "premium-discovery" / "a-home-for-art-base.json").write_text(snap.replace("Three people are better off.", "Three people benefit."), encoding="utf-8")
d = scratch(); rc, line = run(d, t / GUARD.name); shutil.rmtree(d); shutil.rmtree(t)
ok(rc != 0, "P0 BASE snapshot tampered -> refused: %s" % line)

print("\n  %s · %d planted faults, %d not caught\n" % ("PROOF OK" if not fails else "PROOF FAILED", len(MUT) + 1, fails))
sys.exit(1 if fails else 0)
