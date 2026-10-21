"""PlotNua · The House as a Power Station · SEO Approach A layer (REVISED, Option 1b).

Founder approval, 20 Oct 2026 ("Home Energy SEO Editorial Strategy Review",
Approach A), revised by the founder review of the same evening, Decision 1 =
Option 1b: keep the approved title and meta description and the section
anchors; do NOT prepend category labels to any heading. The seven expressive
editorial headings stay exactly as they are, and prove-disc026-discovery.mjs
G18 ("a label is an orientation aid, not a heading") is preserved unchanged.
Orientation stays with the existing position kickers ("1 · Roof · Solar
energy" ...), which this layer does not touch.

The ONE definition of the change, shared by:
  * atlas-tools/build-disc026-seo-a.py      (applies and checks it),
  * atlas-tools/build-disc026-facts-oct2026.py (reads through it), and
  * atlas-tools/build-disc026-look-again.py (L2 reads the page through
    without_seo_a(), so its frozen V3 baseline keeps verifying every other
    byte of the article exactly).

What changes, and nothing else:
  E1  <title>                      -> computing-led: data centre waste heat and home energy
  E2  <meta name="description">    -> founder-approved wording
  E3-E6  stable anchors on the four positions that had none
         (#anat-air, #anat-ground, #anat-garden, #anat-driveway), matching the
         existing #anat-roof / #anat-battery / #anat-grid

with_seo_a(text): base -> approved state. Every anchor must occur exactly once.
without_seo_a(text): exact inverse. Text carrying none of the new strings is
returned untouched; a partial or duplicated state raises ValueError, so nothing
else can hide behind the layer.
"""
from __future__ import annotations

TITLE_OLD = "<title>Can Data Centre Waste Heat Warm a Home in Ireland? | PlotNua</title>"
# Founder decision 21 Oct 2026 (Discovery-led strategy, Stage 1): computing-led
# title; supersedes the solar-and-battery-led title approved on 20 Oct.
TITLE_NEW = "<title>Data Centre Waste Heat &amp; Home Energy in Ireland | PlotNua</title>"
DESC_OLD = ('<meta name="description" content="Could computing heat help warm an Irish home? '
            'Explore how waste-heat systems work, existing examples and what is realistically '
            'available today.">')
DESC_NEW = ('<meta name="description" content="Discover what your Irish home could do with solar '
            'panels, batteries, SEAI grants and electricity exports &mdash; and explore the future '
            'of computing-powered heat.">')

# The seven editorial position headings and their kickers. NOT edited: the
# builder asserts each heading is present exactly once as a bare <h3>.
HEADINGS = [
    "The one position almost every house already has.",
    "A battery doesn&rsquo;t make electricity. It moves it through time.",
    "There is usable heat in Irish air, even in February.",
    "The ground can do more than heat a house.",
    "You can put up a wind turbine in Ireland without planning permission.",
    "A car is a battery that happens to have wheels.",
    "The position nobody thinks of as part of the house.",
]
KICKERS = [
    "1 &middot; Roof &middot; Solar energy",
    "2 &middot; Utility room, garage or wall space &middot; Battery storage",
    "3 &middot; The air beside the house &middot; Air-source heat",
    "4 &middot; The ground beneath the garden &middot; Ground-source energy",
    "5 &middot; The open garden &middot; Small wind",
    "6 &middot; The driveway &middot; EV energy",
    "7 &middot; The grid connection &middot; Export and flexibility",
]

ANCHORS = [
    ("anat-air", "3 &middot; The air beside the house"),
    ("anat-ground", "4 &middot; The ground beneath the garden"),
    ("anat-garden", "5 &middot; The open garden"),
    ("anat-driveway", "6 &middot; The driveway"),
]
POS_PREFIX = '<div class="pos">\n        <span class="pos-where">'


def edits():
    out = [(TITLE_OLD, TITLE_NEW), (DESC_OLD, DESC_NEW)]
    for aid, where in ANCHORS:
        out.append((POS_PREFIX + where,
                    POS_PREFIX.replace('<div class="pos">', '<div class="pos" id="%s">' % aid) + where))
    return out


def with_seo_a(text: str) -> str:
    out = text
    for old, new in edits():
        if out.count(old) != 1 or new in out:
            raise ValueError("SEO-A layer: anchor not found exactly once in the base state: " + old[:70])
        out = out.replace(old, new, 1)
    return out


def without_seo_a(text: str) -> str:
    pairs = edits()
    present = [new in text for _, new in pairs]
    if not any(present):
        return text
    if not all(present):
        raise ValueError("SEO-A layer: the page carries only part of the governed change")
    out = text
    for old, new in pairs:
        if out.count(new) != 1 or old in out:
            raise ValueError("SEO-A layer: a governed string is duplicated or mixed with its original: " + new[:70])
        out = out.replace(new, old, 1)
    if with_seo_a(out) != text:
        raise ValueError("SEO-A layer is not an exact, reversible edit")
    return out
