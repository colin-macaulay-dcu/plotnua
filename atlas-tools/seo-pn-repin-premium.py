#!/usr/bin/env python3
"""SEO and analytics package, PlotNua half (founder approval, 26 Nov 2026): re-pin the Premium Discovery
snapshots for the DECLARED changes of that package, and nothing else.

Same method as SEO-GR2 (atlas-tools/premium-discovery/SEO-GR2-REPIN.md) and the Cookiebot id change
(atlas-tools/cookiebot-id-repin-premium-hashes.py). The declared transforms are:

  A  ANALYTICS, every page: atlas-tools/seo_pn_analytics.transform() -- the Consent Mode v2 default and the
     click listener inserted immediately before <script id="Cookiebot" ...>, and { content_group: 'PlotNua' } on
     the GA4 config call. Head only.
  T  TITLES AND DESCRIPTIONS, three pinned heads only (package section 3.2), exactly these strings:
       living-garden   <title> and meta description
       garden-retreat  <title> and meta description
       home-exchange   <title> (its description is kept)
  (Body additions -- the section 3.5 links -- are NOT snapshot changes: they are declared in the guards'
   own *-added.json / ADDED_LINKS, where every earlier addition is declared.)

Pinned TEXT snapshots (the head stored as text): for each, the tool proves the BASE page (the branch base,
BASE_COMMIT) passes its guard against the stored snapshot; builds the new snapshot as exactly A (+ T where
listed) applied to the stored head; edits the JSON text in place (formatting unchanged) and refuses unless it
parses to exactly that semantic change; then proves the working page passes its guard against the new snapshot.

Pinned HASH snapshots (driveway-income, hidden-bins, hidden-cars, parcel-house, power-station): proves every
stored hash equals the BASE page's; applies A to the BASE page and recomputes; refuses unless the working page
equals that result and only hash facts change; writes the new hashes in place.

Not re-pinned (fingerprinted to historical commits): a-home-for-art-base.json and garden-room-prices-ireland-
base.json. A Home for Art's guard compares head script sources only, so A leaves it passing unchanged; the price
guide's guard declares T for its own title (SEO_PN_HEAD) and the new description wording in G1.

  python3 atlas-tools/seo-pn-repin-premium.py           re-pin (idempotent)
  python3 atlas-tools/seo-pn-repin-premium.py --check   prove only; exit 1 if anything is left to re-pin
"""
import importlib.util, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "atlas-tools"))
import seo_pn_analytics as S   # noqa: E402

BASE_COMMIT = "5225aae771a0f95cf9c8d9327e098b23b58c4b56"   # production main + the Cookiebot id fix (branch base)

TEXT_GUARDS = ["living-garden", "natural-swimming", "garden-retreat", "above-and-beyond", "your-home-on-screen",
               "home-exchange", "borrowed-garden"]
HASH_GUARDS = ["driveway-income", "hidden-bins", "hidden-cars", "parcel-house", "power-station"]

T = {
    "living-garden": [
        ("<title>Garden Rooms in Ireland: Compare Makers &amp; Prices | PlotNua</title>",
         "<title>Garden Rooms in Ireland: Makers, Prices &amp; Rules | PlotNua</title>"),
        ('<meta name="description" content="Compare garden rooms and garden offices in Ireland. Explore researched makers, '
         'understand advertised prices, and check installation, specifications and planning.">',
         '<meta name="description" content="Garden rooms, garden offices and garden homes in Ireland: researched makers, '
         'what advertised prices cover, and the 2026 planning exemptions explained.">'),
    ],
    "garden-retreat": [
        ("<title>Garden Saunas, Hot Tubs &amp; Cold Plunges in Ireland | PlotNua</title>",
         "<title>Hot Tubs, Cold Plunges &amp; Saunas for Irish Gardens | PlotNua</title>"),
        ('<meta name="description" content="Garden saunas, hot tubs and cold plunges in Ireland: real published prices, the '
         'space each needs, and how the 30 m&sup2; and 25 m&sup2; limits apply.">',
         '<meta name="description" content="A wood-fired hot tub, cold plunge or garden sauna: published Irish prices from '
         '&euro;1,699, the space each needs, running costs and the 30 m&sup2; planning limit.">'),
    ],
    "home-exchange": [
        ("<title>Home Exchange in Ireland: How House Swapping Works | PlotNua</title>",
         "<title>House Swap Ireland: How Home Exchange Works | PlotNua</title>"),
    ],
}


def load(g):
    p = os.path.join(ROOT, "atlas-tools", "prove-premium-discovery-%s.py" % g)
    spec = importlib.util.spec_from_file_location("g_" + g.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def git_show(path):
    return subprocess.check_output(["git", "show", "%s:%s" % (BASE_COMMIT, path)], cwd=ROOT).decode("utf-8")


def enc(s):
    return json.dumps(s, ensure_ascii=False)[1:-1]


def declared_head(g, head):
    out = S.transform(head)
    if out == head and S.BLOCK not in head:
        sys.exit("REFUSED %s: the stored head carries no Cookiebot tag to transform" % g)
    for old, new in T.get(g, []):
        if out.count(old) != 1 and out.count(new) != 1:
            sys.exit("REFUSED %s: declared head string not found exactly once: %s" % (g, old[:60]))
        out = out.replace(old, new)
    return out


def repin_text(g, check_only):
    m = load(g)
    raw = open(m.BASE, encoding="utf-8").read(); base = json.loads(raw)
    strip = getattr(m, "strip_journey_cta", lambda h: h)   # as the guard's own main() reads the page
    prod = strip(git_show(m.PAGE))
    want_head = declared_head(g, base["head"])
    if base["head"] != want_head:   # not yet re-pinned: the stored head must be production's
        # (the guard's H checks only: its body checks now include this package's declared body additions)
        hb = [b for b in m.check(prod, base) if b.startswith("H ")]
        if hb:
            sys.exit("REFUSED %s: the BASE page's head does not match the stored snapshot: %s" % (g, hb[:2]))
    new = dict(base); new["head"] = want_head
    out = raw
    if base["head"] != want_head:
        out = S.json_transform(out)
        for old, nw in T.get(g, []):
            if out.count(enc(old)) != 1: sys.exit("REFUSED %s: %s not unique in the snapshot text" % (g, old[:60]))
            out = out.replace(enc(old), enc(nw))
        if json.loads(out) != new:
            sys.exit("REFUSED %s: the in-place edit is not exactly the declared change" % g)
    cur = strip(open(os.path.join(ROOT, m.PAGE), encoding="utf-8").read())
    bad = m.check(cur, new)
    if bad:
        sys.exit("REFUSED %s: the working page fails its guard against the re-pinned snapshot: %s" % (g, bad[:3]))
    changed = out != raw
    if changed and not check_only:
        open(m.BASE, "w", encoding="utf-8").write(out)
    print("%-20s text snapshot  %s" % (g, ("head %s (A%s)" % ("to re-pin" if check_only else "re-pinned", "+T" if g in T else "")) if changed else "up to date"))
    return changed


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
        sys.exit("REFUSED %s: the working page is not the BASE page + the declared analytics transform" % g)
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


def main():
    check_only = "--check" in sys.argv
    pending = 0
    for g in TEXT_GUARDS: pending += repin_text(g, check_only)
    for g in HASH_GUARDS: pending += repin_hash(g, check_only)
    if check_only:
        print("CHECK · %d snapshot(s) %s" % (pending, "left to re-pin" if pending else "re-pinned; every guard passes"))
        sys.exit(1 if pending else 0)
    print("REPIN · %d snapshot(s) re-pinned" % pending)


if __name__ == "__main__":
    main()
