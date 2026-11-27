#!/usr/bin/env python3
"""Consent migration (prepared 27 Nov 2026, NOT released): re-pin the snapshots that fingerprint the head scripts, for
the DECLARED change in atlas-tools/seo_pn_consent.py and nothing else. Same method as seo-pn-repin-premium.py.

  * Pinned HASH snapshots (driveway-income, hidden-bins, hidden-cars, parcel-house, power-station): proves every stored
    hash equals the BASE page's (production main); applies the consent transform to the BASE page and recomputes;
    refuses unless the working page equals that result and only hash facts change; writes the new hashes in place.
  * H6 homepage record (assets/h6/h6-record.json, homepage_baseline): proves the stored baseline is production's,
    and that the working homepage is production's homepage + the consent transform; re-records the two analytics
    and consent values only.
  * Pinned TEXT snapshots were updated by migrate-plotnua-consent.py (seo_pn_consent.json_transform); their guards pass.

  python3 atlas-tools/consent-repin-premium.py           re-pin (idempotent)
  python3 atlas-tools/consent-repin-premium.py --check   prove only; exit 1 if anything is left to re-pin
"""
import importlib.util, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "atlas-tools"))
import seo_pn_consent as S   # noqa: E402  (S.transform: the declared consent transform)

BASE_COMMIT = "33e4b3cc490b9b4e410c733089a15f2ed93e9548"   # production main when the migration was prepared
HASH_GUARDS = ["driveway-income", "hidden-bins", "hidden-cars", "parcel-house", "power-station"]


def load(g):
    p = os.path.join(ROOT, "atlas-tools", "prove-premium-discovery-%s.py" % g)
    spec = importlib.util.spec_from_file_location("g_" + g.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def git_show(path):
    return subprocess.check_output(["git", "show", "%s:%s" % (BASE_COMMIT, path)], cwd=ROOT).decode("utf-8")


def facts(m, html):
    strip = getattr(m, "strip_journey_cta", None)
    return m.facts(strip(html) if strip else html)


def repin_hash(g, check_only):
    m = load(g)
    prod = git_show(m.PAGE)
    raw = open(m.BASE, encoding="utf-8").read(); base = json.loads(raw)
    f_old, f_new = facts(m, prod), facts(m, S.transform(prod))
    live = facts(m, open(os.path.join(ROOT, m.PAGE), encoding="utf-8").read())
    if f_new != {k: live[k] for k in f_new}:
        sys.exit("REFUSED %s: the working page is not the BASE page + the declared consent transform" % g)
    diff = [k for k in f_old if f_old[k] != f_new[k]]
    for k in diff:
        if not isinstance(f_old[k], str) or len(f_old[k]) != 64:
            sys.exit("REFUSED %s: non-hash fact %s changed" % (g, k))
    out = raw; n = 0
    for k in diff:
        if base.get(k) == f_new[k]: continue
        if base.get(k) != f_old[k]: sys.exit("REFUSED %s: stored %s is not the BASE page's" % (g, k))
        if out.count(f_old[k]) != 1: sys.exit("REFUSED %s: hash for %s not unique in the snapshot" % (g, k))
        out = out.replace(f_old[k], f_new[k]); n += 1
        print("%-20s hash snapshot  %-10s %s -> %s" % (g, k, f_old[k][:12], f_new[k][:12]))
    if n == 0: print("%-20s hash snapshot  up to date" % g)
    if out != raw and not check_only:
        open(m.BASE, "w", encoding="utf-8").write(out)
    return out != raw


def repin_h6(check_only):
    h6 = load_h6()
    path = os.path.join(ROOT, "assets", "h6", "h6-record.json")
    raw = open(path, encoding="utf-8").read(); rec = json.loads(raw)
    prod = git_show("index.html")
    old, new = h6.baseline_parts(prod), h6.baseline_parts(S.transform(prod))
    live = h6.baseline_parts(open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())
    if live != new:
        sys.exit("REFUSED h6: the working homepage is not production's homepage + the declared consent transform")
    if old["atlas_figures_block"] != new["atlas_figures_block"]:
        sys.exit("REFUSED h6: the transform touched the Atlas figures block")
    base = rec["homepage_baseline"]
    if base == new:
        print("%-20s h6 record      up to date" % "h6"); return False
    if base != old:
        sys.exit("REFUSED h6: the stored homepage baseline is not production's")
    out = raw
    for k in ("analytics_and_consent", "analytics_and_consent_count"):
        o, n = json.dumps(base[k]), json.dumps(new[k])
        key = '"%s": %s' % (k, o)
        if out.count(key) != 1: sys.exit("REFUSED h6: %s not unique in the record" % k)
        out = out.replace(key, '"%s": %s' % (k, n))
    want = dict(rec); want["homepage_baseline"] = new
    if json.loads(out) != want: sys.exit("REFUSED h6: the in-place edit is not exactly the declared change")
    if not check_only: open(path, "w", encoding="utf-8").write(out)
    print("%-20s h6 record      analytics and consent baseline %s" % ("h6", "to re-pin" if check_only else "re-pinned"))
    return True


def load_h6():
    p = os.path.join(ROOT, "atlas-tools", "build-h6-homepage.py")
    spec = importlib.util.spec_from_file_location("h6b", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def main():
    check_only = "--check" in sys.argv
    pending = sum(repin_hash(g, check_only) for g in HASH_GUARDS) + repin_h6(check_only)
    if check_only:
        print("CHECK · %d snapshot(s) %s" % (pending, "left to re-pin" if pending else "re-pinned; every guard passes"))
        sys.exit(1 if pending else 0)
    print("REPIN · %d snapshot(s) re-pinned" % pending)


if __name__ == "__main__":
    main()
