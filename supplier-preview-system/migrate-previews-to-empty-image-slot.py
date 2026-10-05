#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ONE-SHOT MIGRATION — bring the remaining provider-led builders onto the
certified template of 5 October 2026, in which the image position carries no
copy and {{PHOTO_SLOT_LINE}} no longer exists.

WHAT THIS DOES NOT DO: it does not regenerate a single supplier page. It edits
BUILDERS only. Every already-built *-preview.html is left byte-for-byte alone,
and the caller proves that with a hash comparison afterwards. A supplier's
page changes when that supplier is deliberately reopened, not because a
template moved underneath them.

FOUR EDITS, each applied only where that builder actually needs it:

  E1  the state-A slot regex is widened from `pn-photo-slot">` to
      `pn-photo-slot"[^>]*>`, because the slot now carries aria-hidden and the
      old pattern would silently stop matching. This is the dangerous one: a
      regex that no longer matches does not raise, it just fails to replace,
      and the builder would emit an empty panel where an AUTHORISED image
      should be. Widening it keeps state A working for the four builders that
      carry granted imagery.

  E2  the G3 relabel block is removed. It rewrote the slot heading into a
      sentence about photography; under the certified rule there is no
      heading and no sentence.

  E3  the PHOTO_SLOT_LINE fill entry and any assignment to it are removed, so
      the builder stops supplying a token the template no longer has. Any
      FILL.pop("PHOTO_SLOT_LINE", None) is LEFT IN PLACE on purpose: with the
      key gone it is a harmless no-op, and deleting it would be churn in a
      file whose page is frozen.

  E4  the "Where your imagery would go" subsection and the process-heavy
      three-question intro are removed where present, and the intro is
      replaced with the certified wording.

EVERY EDIT ASSERTS ITS ANCHOR MATCHES EXACTLY ONCE. If a file does not look
the way this script expects, that file is REFUSED and left untouched, and the
run reports it rather than guessing. Partial migration of a known file is
better than silent corruption of an unknown one.

Run: python3 supplier-preview-system/migrate-previews-to-empty-image-slot.py
     [--check]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
CHECK = "--check" in sys.argv

TARGETS = [
    "build-biobuilds-preview.py",
    "build-cosy-cabins-preview.py",
    "build-hutsmith-preview.py",
    "build-irish-sauna-company-preview.py",
    "build-modulux-preview.py",
    "build-ognyx-preview.py",
    "build-tanktribe-preview.py",
]

NEW_INTRO = ("  <p>These are the three things we&rsquo;d like to check with "
             "you before the\n     page goes live.</p>\n")

SLOT_NOTE = (
    "    # G3 · THE IMAGE POSITION CARRIES NO COPY (certified, 5 Oct\n"
    "    # 2026). The relabel that stood here rewrote the slot heading into a\n"
    "    # sentence about photography. There is no heading and no sentence\n"
    "    # now; the rights gate is unchanged and still fails closed.\n")

report = []


def migrate(path):
    """Return (changed_text, list_of_edits) or raise ValueError to refuse."""
    src = path.read_text(encoding="utf-8")
    original = src
    edits = []

    # ---- E1 . widen the state-A slot regex --------------------------------
    OLD_RE = r"""          <div class="pn-photo-slot">.*?</div>\n"""
    NEW_RE = r"""          <div class="pn-photo-slot"[^>]*>.*?</div>\n"""
    n = src.count(OLD_RE)
    if n:
        if n != 1:
            raise ValueError("state-A slot regex appears %d times, expected 1"
                             % n)
        src = src.replace(OLD_RE, NEW_RE, 1)
        edits.append("E1 state-A slot regex widened for aria-hidden")

    # ---- E2 . remove the G3 relabel block ---------------------------------
    blk = re.compile(
        r'\n[ ]*ask = "<b>Your project photography here</b>"\n'
        r'.*?src = src\.replace\(ask, "[^"]*"\)\n', re.S)
    found = blk.findall(src)
    if found:
        if len(found) != 1:
            raise ValueError("G3 relabel block appears %d times, expected 1"
                             % len(found))
        if len(found[0]) > 900:
            raise ValueError("G3 relabel block is %d chars, far larger than "
                             "expected; refusing to delete that much"
                             % len(found[0]))
        src = blk.sub("\n" + SLOT_NOTE, src, count=1)
        edits.append("E2 G3 relabel block removed")

    # ---- E3 . remove the PHOTO_SLOT_LINE fill entry and assignments -------
    lines = src.split("\n")
    out, i, removed = [], 0, 0
    while i < len(lines):
        ln = lines[i]
        if '"PHOTO_SLOT_LINE":' in ln:
            # Consume this logical entry. THE FIRST VERSION OF THIS LOOP HAD A
            # REAL BUG AND IT DID DAMAGE: it consumed forward until a line
            # ending in `",`, which is right for the multi-line paragraph form
            # but catastrophically wrong for the one-line form
            #     "PHOTO_SLOT_LINE": "",   # set by imagery state
            # whose line ends in a COMMENT, not in `",`. On four builders it
            # ran on and swallowed the following fill entries -- OFFER_NAME
            # among them -- and they refused to build with an unfilled token.
            # The entries were restored from HEAD and the rule is now: strip
            # any trailing comment first, then decide.
            def code_of(s):
                return s.split("#")[0].rstrip()

            if code_of(ln).endswith('",') or code_of(ln).endswith('"",'):
                i += 1                       # one-line entry: drop just it
            else:
                start = i
                while i < len(lines) and not code_of(lines[i]).endswith('",'):
                    i += 1
                    if i - start > 15:
                        raise ValueError(
                            "the PHOTO_SLOT_LINE entry did not close within "
                            "15 lines; refusing to consume further")
                i += 1
            removed += 1
            continue
        if re.match(r'\s*FILL\["PHOTO_SLOT_LINE"\]\s*=', ln):
            i += 1
            removed += 1
            continue
        out.append(ln)
        i += 1
    if removed:
        src = "\n".join(out)
        edits.append("E3 %d PHOTO_SLOT_LINE fill line(s)/assignment(s) removed"
                     % removed)

    # ---- E4 . the imagery subsection and the old intro --------------------
    sect = re.compile(r"\n  <h3>Where your imagery would go</h3>\n"
                      r"  <p>.*?</p>\n", re.S)
    if sect.search(src):
        if len(sect.findall(src)) != 1:
            raise ValueError("imagery subsection appears more than once")
        src = sect.sub("\n", src, count=1)
        edits.append("E4a 'Where your imagery would go' subsection removed")

    intro = re.compile(r"  <p>Everything above comes from your own.*?</p>\n",
                       re.S)
    if intro.search(src):
        if len(intro.findall(src)) != 1:
            raise ValueError("old three-question intro appears more than once")
        src = intro.sub(NEW_INTRO, src, count=1)
        edits.append("E4b three-question intro replaced with the certified "
                     "wording")

    # ---- post-conditions --------------------------------------------------
    if "PHOTO_SLOT_LINE" in src and 'FILL.pop("PHOTO_SLOT_LINE"' not in src:
        raise ValueError("PHOTO_SLOT_LINE still referenced outside a pop()")
    if "Where your imagery would go" in src:
        raise ValueError("the imagery subsection survived the edit")
    if "Everything above comes from your own" in src:
        raise ValueError("the old intro survived the edit")
    if '"<b>Your project photography here</b>"' in src:
        raise ValueError("the photo-slot heading is still referenced")
    if src == original:
        edits.append("no change needed")
    return src, edits


ok, refused = 0, 0
for name in TARGETS:
    p = HERE / name
    if not p.exists():
        report.append("%-40s MISSING" % name)
        refused += 1
        continue
    try:
        new, edits = migrate(p)
    except ValueError as e:
        report.append("%-40s REFUSED: %s" % (name, e))
        refused += 1
        continue
    if not CHECK and new != p.read_text(encoding="utf-8"):
        p.write_text(new, encoding="utf-8")
    ok += 1
    report.append("%-40s %s" % (name, "; ".join(edits)))

print("PROVIDER-LED BUILDER MIGRATION" + ("  (--check, nothing written)"
                                          if CHECK else ""))
print("=" * 78)
for line in report:
    print("  " + line)
print("=" * 78)
print("%d migrated, %d refused" % (ok, refused))
sys.exit(1 if refused else 0)
