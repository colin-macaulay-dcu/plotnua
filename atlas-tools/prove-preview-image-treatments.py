#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROOF — SUPPLIER PREVIEW IMAGE TREATMENTS (standard v1.1, §3 and §9).

Founder-approved 18 October 2026. Runs in the image-rights CI gate.

PART 1 · THE TREE. Every *-preview.html at the repository root is classified
by the treatment of its image position (T1 authorised photography, T2 generic
illustration, T3 image-free typographic). Every page that carries a generic
illustration anywhere is held to the shared T2 rules in
supplier-preview-system/preview_image_treatment.py:
  · pure inline vector -- no <image>, href, external url() or foreignObject;
  · a visible label saying the drawings are generic and not the supplier's
    products;
  · no accessible label presenting a drawing as the supplier's product;
  · no rights-process narration (§10.2).
T1 is not re-judged here: the publish-time image-rights gate and the
preview-only containment proof already hold every supplier image to its
grant, and both run in the same workflow.

PART 2 · CAPABILITY. The same rules are run against deliberately broken
copies of a real T2 page, held in memory only. Each break must be refused and
the unbroken page must pass. A rule that has never been seen to refuse is a
comment. Nothing is written to disk.

Exit 0 only if both parts pass.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "supplier-preview-system"))
import preview_image_treatment as pit  # noqa: E402


def supplier_of(src):
    m = re.search(r"Prepared for ([^<&·]+?)\s*(?:<|&middot;|·)", src)
    return m.group(1).strip() if m else None


def main():
    pages = sorted(ROOT.glob("*-preview.html"))
    counts = {"T1": 0, "T2": 0, "T3": 0, None: 0}
    failures = []
    t2_pages = []
    print("SUPPLIER PREVIEW IMAGE TREATMENTS · standard v1.1")
    print("=" * 76)
    for p in pages:
        src = p.read_text(encoding="utf-8", errors="replace")
        t = pit.slot_treatment(src)
        counts[t] = counts.get(t, 0) + 1
        figs = pit.illustrations(src)
        if t == "T2" or figs:
            sup = supplier_of(src)
            if not sup:
                failures.append("%s: carries illustrations but names no supplier"
                                % p.name)
                continue
            probs = pit.t2_problems(src, sup)
            t2_pages.append((p, sup))
            if probs:
                failures.append("%s: %s" % (p.name, "; ".join(probs)))
            else:
                print("  PASS   %-44s T2 · %d illustrations, labelled generic"
                      % (p.name, len(figs)))
        if t == "T2" and not figs:
            failures.append("%s: T2 slot without a marked illustration" % p.name)
    print("  ----   %d previews: T1 %d · T2 %d · T3 %d · no slot %d"
          % (len(pages), counts["T1"], counts["T2"], counts["T3"], counts[None]))

    # ── PART 2 · CAPABILITY ────────────────────────────────────────────────
    print("-" * 76)
    if not t2_pages:
        failures.append("no T2 page exists to drive the capability proof")
    else:
        base_path, sup = t2_pages[0]
        base = base_path.read_text(encoding="utf-8")
        marker = pit.ILLUSTRATION_ATTR + ">"
        cases = [
            ("an embedded raster image",
             lambda s: s.replace(marker, marker + '<image href="x.jpg"/>', 1)),
            ("an external url() in a drawing",
             lambda s: s.replace(marker, marker + '<path fill="url(https://x/y)"/>', 1)),
            ("a foreignObject in a drawing",
             lambda s: s.replace(marker, marker + "<foreignObject></foreignObject>", 1)),
            ("the generic label removed",
             lambda s: re.sub(r"generic forms?,", "forms,", s)),
            ("a drawing named as the supplier's product",
             lambda s: s.replace('role="img" ', 'role="img" aria-label="The %s Barrel Sauna" ' % sup, 1)
             if 'role="img" ' in s else s + '<div aria-label="%s product"></div>' % sup),
            ("rights-process narration",
             lambda s: s.replace("</footer>", "<p>Your images stay yours until you tell us otherwise.</p></footer>", 1)),
        ]
        if pit.t2_problems(base, sup):
            failures.append("capability: the unbroken page does not pass")
        else:
            print("  ok     unbroken %s passes" % base_path.name)
        for label, broke in cases:
            s = broke(base)
            if s == base:
                failures.append("capability: could not apply break %r" % label)
                print("  BROKEN %s" % label)
                continue
            caught = bool(pit.t2_problems(s, sup))
            print("  %s %s" % ("caught" if caught else "MISSED", label))
            if not caught:
                failures.append("capability: %s was not refused" % label)

    print("=" * 76)
    if failures:
        for f in failures:
            print("  FAIL   " + f)
        print("REFUSED — %d problem(s)." % len(failures))
        return 1
    print("PASS — every generic illustration is pure vector and labelled; "
          "every rule refuses its break.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
