"""PlotNua · Privacy Notice V9 layer (2026-11-IDEA-BOARD-V9): the PlotNua Idea Board.

PREPARED FOR FOUNDER REVIEW (1 Nov 2026). NOT PUBLISHED until the founder approves the exact wording and the public
launch of the Idea Board. Like V7 and V8, V9 is a set of EXACT, REVERSIBLE additions on top of the published page:
  S2   Section 2: one line pointing to the Idea Board sub-section.
  S5   Section 5: a new sub-section "The Idea Board" (id="idea-board", linked from ideas.html).
  S10  Section 10: one line on the hosting of the Idea Board.
  S12  Section 12: one line on Idea Board retention.
  The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V9.
without_v9() returns the exact page beneath V9, so every earlier verifier keeps reading the text it governs
(privacy_v8_layer.without_v8 takes V9 off first).

    python3 atlas-tools/privacy_v9_layer.py --apply     write V9 into privacy.html (only with the founder's approval)
"""
from __future__ import annotations

MARKER = "PLOTNUA-IDEA-BOARD-PRIVACY-V9"
VERSION = "2026-11-IDEA-BOARD-V9"

IDEA_SUB = f"""  <!-- {MARKER} · the Idea Board, privacy notice {VERSION} -->
    <h3 class="pv5-sub" id="idea-board">The Idea Board</h3>
    <p>If you add an idea to the PlotNua Idea Board, we collect the idea you write (up to 160 characters), the area and the county you choose to add, if any, whether you allow your county to be shown, and the date you sent it. We give you a reference number so that you can contact us about your idea later.</p>
    <p>Ideas are anonymous. We do not ask for your name, email address or any other contact details, and the form refuses ideas that contain an email address, a telephone number or a web address. We do not store your IP address, and the form does not use cookies. Please don't include names, addresses or anything else that could identify you or another person.</p>
    <p>Every idea is read by PlotNua before anything is published. If we approve an idea, it appears on the Idea Board and, for the three most recent ideas, in the Discovery Library, without any name or reference number. We may shorten or tidy the wording, or correct the area, but we do not change its meaning. Your county is shown only if you ticked "Show my county", and we may still choose not to show it. We show the month and year an idea was published, never the exact date or time.</p>
    <p>We use ideas to show visitors what other homeowners are thinking about and to help decide what PlotNua researches next. An idea may lead PlotNua to research and publish a Discovery on the same subject; where that happens, we may mark the idea "Now a PlotNua Discovery". Sharing an idea creates no payment, credit or ownership. We rely on our legitimate interests in running and improving PlotNua for this; you can object, as described in Section 14.</p>
    <p>A hidden form field, a check on how quickly the form is sent, and limits on repeated ideas keep the board free of spam. These limits are held briefly in memory and are not stored.</p>
    <p>Ideas waiting for review are deleted 90 days after they arrive if we have not decided on them. Ideas we decide not to publish, and ideas we remove from the board, are deleted 30 days after that decision. Published ideas stay on the board until we remove them. To ask us to remove or delete your idea at any time, email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a> with your reference number; we will take it off the board and delete it.</p>
"""
S2_OLD = "    <p>If you apply to the PlotArt Founding 25, we also collect the information described in Section 8.</p>\n"
S2_NEW = S2_OLD + "    <p>If you add an idea to the Idea Board, we collect the information described in Section 5.</p>\n"
S5_OLD = ("Visitors should refer to Formspree's own Privacy Policy for further information about how it processes personal information.</p>\n"
          "  </section>")
S5_NEW = S5_OLD.replace("  </section>", IDEA_SUB + "  </section>")
S10_OLD = "    <p>These providers operate under their own privacy policies and terms."
S10_NEW = ("    <p>The Idea Board described in Section 5 runs on a PlotNua service hosted on infrastructure provided by Cloudflare.</p>\n"
           + S10_OLD)
S12_OLD = "    <p>Information will be deleted or anonymised when it is no longer reasonably required"
S12_NEW = ("    <p>Idea Board ideas waiting for review are kept for up to 90 days; ideas we do not publish, or remove from the board, "
           "are deleted 30 days after that decision; published ideas are kept while they are on the board, as described in Section 5.</p>\n"
           + S12_OLD)
PAIRS = [(S2_OLD, S2_NEW), (S5_OLD, S5_NEW), (S10_OLD, S10_NEW), (S12_OLD, S12_NEW)]


def apply_v9(text: str) -> str:
    if MARKER in text:
        raise ValueError("V9 already applied")
    if "PLOTNUA-PLOTART-PRIVACY-V8" not in text:
        raise ValueError("V9 applies on top of V8 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V9 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v9(text: str) -> str:
    """The exact page beneath V9. A page without V9 passes through untouched; a page that carries the V9 marker but not
    exactly the governed V9 text raises."""
    from privacy_v10_layer import without_v10       # V10 (The Borrowed Garden noticeboard, 4 Nov 2026) sits on top of V9: take it off first
    text = without_v10(text)
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V9 marker but not exactly the governed V9 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v9(out) != text:
        raise ValueError("privacy.html V9 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v9(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V9 (Idea Board) applied")
