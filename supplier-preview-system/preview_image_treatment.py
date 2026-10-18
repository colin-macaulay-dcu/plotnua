# -*- coding: utf-8 -*-
"""
SHARED SAFEGUARDS — SUPPLIER PREVIEW IMAGE TREATMENTS (standard v1.1, §3).

Approved by the founder on 18 October 2026 with the v1.1 amendment to
SUPPLIER-PREVIEW-SYSTEM-V1.md. One place for the rules every preview builder
and the repository-wide proof apply, so a fix cannot reach one builder and
miss the next.

PERMISSION STATE decides what may be shown (A authorised, B PlotNua-owned,
C not yet authorised). TREATMENT decides how the image position is presented:

  T1  authorised supplier photography   -- state A only, read from the manifest
  T2  original, labelled generic illustration
  T3  deliberate image-free typographic presentation

Nothing here relaxes an existing rule. The publish-time image-rights gate,
the preview-only containment proof and the §10.1 send gate are unchanged;
these checks sit in front of them.

A T2 illustration is marked in the page as
    <svg ... data-pn-illustration="generic" ...>
so that this module, not a class name chosen by one builder, decides what is
an illustration and holds it to the rules.
"""

import json
import pathlib
import re

ILLUSTRATION_ATTR = 'data-pn-illustration="generic"'

LIVE_OUTCOMES = {
    "Granted — Founder Confirmed",
    "Granted with Conditions — Founder Confirmed",
    "Granted — Supplier Confirmed (one-click)",
}

# §10.2: the rights process is never narrated to the supplier.
RIGHTS_NARRATION = (
    "where they would sit", "where your imagery would go",
    "where your photography would", "stay yours until", "images stay yours",
    "imagery waits until", "until you tell us otherwise",
    "before anything is published, so your",
)


def visible_text(src):
    """Lower-cased visible text: comments, <style> and <script> removed,
    tags kept (so attribute text such as aria-label is still examined)."""
    v = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    v = re.sub(r"<style\b.*?</style>", " ", v, flags=re.S | re.I)
    v = re.sub(r"<script\b.*?</script>", " ", v, flags=re.S | re.I)
    return re.sub(r"\s+", " ", v).lower()


def live_grant(site_root, domain, credit):
    """T1 GATE. Returns the LIVE manifest row for `domain`, or None.
    Raises ValueError if a live row exists but requires a different credit:
    a grant whose credit the page does not print is not usable."""
    man = pathlib.Path(site_root) / "image-rights-manifest.json"
    if not man.exists():
        return None
    rows = json.loads(man.read_text(encoding="utf-8")).get("rows") or []
    for r in rows:
        pd = str(r.get("permitted_domain", "")).lower()
        if ((pd == domain or pd.endswith("." + domain))
                and r.get("permission_outcome") in LIVE_OUTCOMES
                and not r.get("withdrawal_effective_at")):
            if r.get("required_credit") != credit:
                raise ValueError("the live grant for %s requires the credit %r, "
                                 "not %r" % (domain, r.get("required_credit"),
                                             credit))
            return r
    return None


def illustrations(src):
    """Every inline SVG marked as a T2 generic illustration."""
    return [m.group(0) for m in re.finditer(r"<svg\b[^>]*>.*?</svg>", src, re.S)
            if ILLUSTRATION_ATTR in m.group(0).split(">", 1)[0]]


def slot_treatment(src):
    """Classify the Results image position: T1, T2 or T3 (or None)."""
    m = re.search(r'<div class="(?:results-hero-media[^"]*|pn-photo-slot)"[^>]*>'
                  r'(.*?)</div>', src, re.S)
    if not m:
        return None
    inner = m.group(1)
    if re.search(r"<img\b", inner, re.I):
        return "T1"
    if ILLUSTRATION_ATTR in inner:
        return "T2"
    return "T3"


def t2_problems(src, supplier):
    """Everything wrong with a page's T2 illustrations. Empty list = pass.

    1 · pure vector: no <image>, no external href, no url() other than an
        in-document #fragment, no <foreignObject>;
    2 · every page carrying an illustration says, in visible text, that it is
        a generic illustration and not the supplier's product;
    3 · nothing labels an illustration as the supplier's actual product: an
        aria-label or caption naming the supplier's product as depicted;
    4 · the rights process is not narrated (§10.2)."""
    problems = []
    figs = illustrations(src)
    if not figs:
        return problems
    for i, svg in enumerate(figs, 1):
        if re.search(r"<image\b|<foreignObject\b", svg, re.I):
            problems.append("illustration %d embeds an image or foreign object" % i)
        if re.search(r"\b(?:xlink:)?href\s*=", svg, re.I):
            problems.append("illustration %d carries an href" % i)
        if re.search(r"url\(\s*(?!#)", svg, re.I):
            problems.append("illustration %d references an external url()" % i)
    low = visible_text(src)
    sup = supplier.lower()
    label = re.search(r"illustration\s*(?:&middot;|·|-|—|:)\s*(?:a\s+)?generic\s+forms?,?"
                      r"\s+not\s+(?:an?\s+)?" + re.escape(sup), low)
    if not label:
        problems.append("no visible label saying the illustrations are generic "
                        "and not %s products" % supplier)
    # An accessible name or caption must never present a drawing AS the
    # supplier's product.
    for m in re.finditer(r'aria-label="([^"]*)"', src):
        al = m.group(1).lower()
        if sup in al and "generic" not in al:
            problems.append("an accessible label names %s without saying the "
                            "drawing is generic: %r" % (supplier, m.group(1)))
    for phrase in RIGHTS_NARRATION:
        if phrase in low:
            problems.append("the rights process is narrated: %r" % phrase)
    return problems
