#!/usr/bin/env python3
"""SEO-GR2 (founder approval 8 Nov 2026): carry the two declared SEO-GR2 changes into the pinned
Premium Discovery base snapshots (atlas-tools/premium-discovery/*-base.json), and nothing else.

The Premium Discovery content guards compare each page's head, header and post-journey regions with
a pinned snapshot. SEO-GR2 changes those regions in exactly two declared ways:
  1. homepage links: an href that resolves to the root /index.html becomes "/" (query/fragment kept),
     using the SAME resolver as atlas-tools/seo-gr2-home-links.py;
  2. Living in the Garden only: WebPage dateModified 2026-10-26 -> 2026-11-07 (its last content
     change, commit 0351c89), matching sitemap.xml.
This tool applies those two transforms to every string in each snapshot and refuses if anything else
would change. Run once; --check reports whether the snapshots already carry the transforms.
Record: atlas-tools/premium-discovery/SEO-GR2-REPIN.md
"""
import importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("homelinks", ROOT / "atlas-tools" / "seo-gr2-home-links.py")
HL = importlib.util.module_from_spec(spec); spec.loader.exec_module(HL)

BASES = {  # snapshot -> the page it pins (from each guard's PAGE constant)
    # a-home-for-art-base.json is NOT re-pinned: it is fingerprinted and must equal git 0cb456d's page (P0);
    # its guard compares the live page through its own declared-change rules instead.
    "above-and-beyond-base.json": "discovery-above-and-beyond.html",
    "the-borrowed-garden-base.json": "discovery-the-borrowed-garden.html",
    "driveway-income-base.json": "discovery-driveway-income.html",
    "garden-retreat-base.json": "discovery-garden-retreat.html",
    "hidden-bins-base.json": "discovery-hidden-bins.html",
    "hidden-cars-base.json": "discovery-hidden-cars.html",
    "home-exchange-base.json": "discovery-home-exchange.html",
    "living-garden-base.json": "discovery-living-in-the-garden.html",
    "natural-swimming-base.json": "discovery-natural-swimming-garden.html",
    "parcel-house-base.json": "discovery-neighbourhood-parcel-house.html",
    "power-station-base.json": "discovery-house-as-power-station.html",
    "your-home-on-screen-base.json": "discovery-your-home-on-screen.html",
    # garden-room-prices-ireland-base.json is NOT re-pinned: it is fingerprinted (G0); its guard declares the
    # SEO-GR2 homepage-link mapping in its link comparison instead.
}
DATE_FROM, DATE_TO = '"dateModified": "2026-10-26"', '"dateModified": "2026-11-07"'
HREF = re.compile(r'href="([^"]*)"')
FORMATS = [dict(ensure_ascii=ea, indent=ind, separators=sep) for ea in (False, True) for ind in (None, 1, 2, 4)
           for sep in (None, (",", ":"), (", ", ": "))]


def transform(page, value, counts):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            nk = HL.to_root_home(page, k) if re.fullmatch(r"[^\s<>\"]+", k) else None
            if nk is not None:
                counts["href"] += 1
            out[nk or k] = transform(page, v, counts)
        return out
    if isinstance(value, list):
        return [transform(page, v, counts) for v in value]
    if not isinstance(value, str):
        return value
    whole = HL.to_root_home(page, value) if re.fullmatch(r"[^\s<>\"]+", value) else None
    if whole is not None:                      # a bare href in a links list
        counts["href"] += 1
        return whole

    def sub(m):
        new = HL.to_root_home(page, m.group(1))
        if new is None:
            return m.group(0)
        counts["href"] += 1
        return f'href="{new}"'
    out = HREF.sub(sub, value)
    if page == "discovery-living-in-the-garden.html" and DATE_FROM in out:
        out = out.replace(DATE_FROM, DATE_TO); counts["date"] += 1
    return out


def raw_transform(page, raw):
    """The same two transforms applied to the JSON text itself, so the file's formatting is untouched."""
    def esc_href(m):
        new = HL.to_root_home(page, m.group(1))
        return m.group(0) if new is None else 'href=\\"%s\\"' % new
    out = re.sub(r'href=\\"([^"\\]*)\\"', esc_href, raw)
    def bare(m):
        new = HL.to_root_home(page, m.group(1))
        return m.group(0) if new is None else '"%s"' % new
    out = re.sub(r'"([^"\\\s<>]*index\.html[^"\\\s<>]*)"', bare, out)
    if page == "discovery-living-in-the-garden.html":
        out = out.replace('\\"dateModified\\": \\"2026-10-26\\"', '\\"dateModified\\": \\"2026-11-07\\"')
    return out


HASHED = {  # editorial guards that pin SHA-256 hashes of page regions instead of text
    "driveway-income-base.json": "prove-premium-discovery-driveway-income.py",
    "hidden-bins-base.json": "prove-premium-discovery-hidden-bins.py",
    "hidden-cars-base.json": "prove-premium-discovery-hidden-cars.py",
    "parcel-house-base.json": "prove-premium-discovery-parcel-house.py",
    "power-station-base.json": "prove-premium-discovery-power-station.py",
}


def repin_hashed(name, guard, check):
    """Re-pin a hashed snapshot: prove the stored hashes are those of the page at git HEAD (production),
    apply the declared homepage-link transform to that page, and store the new region hashes. Every other
    pinned field must come out identical, or nothing is written."""
    import subprocess
    g_spec = importlib.util.spec_from_file_location("guard_" + name.replace("-", "_")[:-10], ROOT / "atlas-tools" / guard)
    G = importlib.util.module_from_spec(g_spec); g_spec.loader.exec_module(G)
    p = ROOT / "atlas-tools" / "premium-discovery" / name
    raw = p.read_text(encoding="utf-8"); base = json.loads(raw)
    head_page = subprocess.check_output(["git", "show", "HEAD:" + G.PAGE], cwd=ROOT).decode("utf-8")
    before = G.facts(head_page)
    hashed = [k for k in ("head", "pre_main", "post_main") if k in base]
    moved = HL.HREF.sub(lambda m: 'href="%s"' % (HL.to_root_home(G.PAGE, m.group(1)) or m.group(1)), head_page)
    after = G.facts(moved)
    for k in hashed:
        if base[k] not in (before[k], after[k]):
            sys.exit(f"REFUSED: {name}: {k} is neither HEAD's {G.PAGE} nor HEAD's page with the declared transform; nothing written")
    for k in base:
        if k in hashed or k in ("ref", "lag"):
            continue
        if json.loads(json.dumps(after.get(k))) != base[k] and json.loads(json.dumps(before.get(k))) == base[k]:
            sys.exit(f"REFUSED: {name}: the transform would change pinned field {k}; nothing written")
    changed = [k for k in hashed if after[k] != base[k]]
    print(f"{len(changed):3d}  {name}  (hashed regions re-pinned: {', '.join(changed) or 'none'})")
    if changed and not check:
        out = raw
        for k in changed:
            out = out.replace(base[k], after[k], 1)
        if json.loads(out) != {**base, **{k: after[k] for k in changed}}:
            sys.exit(f"REFUSED: {name}: text-level edit differs; nothing written")
        p.write_text(out, encoding="utf-8")
    return len(changed)


def main():
    check = "--check" in sys.argv
    total = 0
    for name, page in BASES.items():
        if name in HASHED:
            continue
        p = ROOT / "atlas-tools" / "premium-discovery" / name
        if not p.exists():
            sys.exit(f"REFUSED: {name} missing")
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
        counts = {"href": 0, "date": 0}
        new = transform(page, data, counts)
        n = counts["href"] + counts["date"]
        total += n
        print(f"{n:3d}  {name}  ({counts['href']} homepage href, {counts['date']} date)")
        if n and not check:
            out = raw_transform(page, raw)
            if json.loads(out) != new:
                sys.exit(f"REFUSED: {name}: the text-level edit does not equal the declared transform; nothing written")
            p.write_text(out, encoding="utf-8")
    for name, guard in HASHED.items():
        total += repin_hashed(name, guard, check)
    print(("PENDING " if check else "APPLIED ") + f"{total} change(s)")
    sys.exit(1 if (check and total) else 0)


if __name__ == "__main__":
    main()
