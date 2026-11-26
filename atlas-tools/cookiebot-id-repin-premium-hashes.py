#!/usr/bin/env python3
"""Analytics restore (26 Nov 2026): re-pin the hashed Premium Discovery snapshots for ONE declared change,
the Cookiebot domain group id 8a5219c1… (suspended trial account) -> b8abbc45… (active account).

Same method as SEO-GR2 (atlas-tools/premium-discovery/SEO-GR2-REPIN.md). For each hashed guard it:
  1. proves every stored hash equals the production page at origin/main (so nothing else had drifted);
  2. applies ONLY the id replacement to that production page and recomputes the facts;
  3. refuses unless the only facts that change are hashes of regions containing the id;
  4. writes the new hashes into the snapshot JSON text in place (formatting unchanged).
    python3 atlas-tools/cookiebot-id-repin-premium-hashes.py [--check]
"""
import importlib.util, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD, NEW = "8a5219c1-0f84-4a7e-9c17-d22fab76adc1", "b8abbc45-15b0-4d27-8f95-83ebd240a305"
GUARDS = ["driveway-income", "hidden-bins", "hidden-cars", "parcel-house", "power-station"]

def load(g):
    p = os.path.join(ROOT, "atlas-tools", "prove-premium-discovery-%s.py" % g)
    spec = importlib.util.spec_from_file_location("g_" + g.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def facts(m, html):
    strip = getattr(m, "strip_journey_cta", None)
    return m.facts(strip(html) if strip else html)

def main():
    check_only = "--check" in sys.argv; changed = 0
    for g in GUARDS:
        m = load(g)
        prod = subprocess.check_output(["git", "show", "origin/main:" + m.PAGE], cwd=ROOT).decode("utf-8")
        if OLD not in prod and NEW in prod: prod = prod.replace(NEW, OLD)   # already released: reconstruct the pre-change page
        raw = open(m.BASE, encoding="utf-8").read(); base = json.loads(raw)
        f_old, f_new = facts(m, prod), facts(m, prod.replace(OLD, NEW))
        live = facts(m, open(os.path.join(ROOT, m.PAGE), encoding="utf-8").read())
        if f_new != {k: live[k] for k in f_new}: sys.exit("REFUSED %s: the working page is not production + the id change only" % g)
        diff = [k for k in f_old if f_old[k] != f_new[k]]
        for k in diff:
            if not isinstance(f_old[k], str) or len(f_old[k]) != 64: sys.exit("REFUSED %s: non-hash fact %s changed" % (g, k))
        out = raw
        for k in diff:
            if base.get(k) == f_new[k]: continue                     # already re-pinned
            if base.get(k) != f_old[k]: sys.exit("REFUSED %s: stored %s is not production's" % (g, k))
            if out.count(f_old[k]) != 1: sys.exit("REFUSED %s: hash for %s not unique in the snapshot" % (g, k))
            out = out.replace(f_old[k], f_new[k]); changed += 1
            print("%-16s %-10s %s -> %s" % (g, k, f_old[k][:12], f_new[k][:12]))
        if out != raw and not check_only:
            open(m.BASE, "w", encoding="utf-8").write(out)
    print("%s · %d hash(es) %s" % ("CHECK" if check_only else "REPIN", changed, "to re-pin" if check_only else "re-pinned"))

if __name__ == "__main__":
    main()
