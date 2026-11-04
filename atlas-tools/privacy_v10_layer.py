"""PlotNua · Privacy Notice V10 layer (2026-11-GARDEN-NOTICEBOARD-V10): The Borrowed Garden noticeboard.

PREPARED IN THE NOTICEBOARD RELEASE CANDIDATE (4 Nov 2026). Published only with that release, which is the founder's
approval of this wording. Like V7-V9, V10 is a set of EXACT, REVERSIBLE additions on top of the published page:
  S2   Section 2: one line pointing to the noticeboard sub-section.
  S7a  Section 7: a short note that new registrations to both registers are paused (founder decision 4 Nov 2026), and
       that existing records are kept privately as described.
  S7b  Section 7: a new sub-section "The Borrowed Garden noticeboard" (id="borrowed-garden-noticeboard", linked from
       the noticeboard's form).
  S10  Section 10: one line on the hosting of the noticeboard.
  S12  Section 12: one line on noticeboard retention.
  The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V10.
without_v10() returns the exact page beneath V10, so every earlier verifier keeps reading the text it governs
(privacy_v9_layer.without_v9 takes V10 off first).

    python3 atlas-tools/privacy_v10_layer.py --apply     write V10 into privacy.html
"""
from __future__ import annotations

MARKER = "PLOTNUA-GARDEN-NOTICEBOARD-PRIVACY-V10"
VERSION = "2026-11-GARDEN-NOTICEBOARD-V10"

PAUSED = ("    <p><strong>New registrations are paused.</strong> Since 4 November 2026 neither register accepts new entries. "
          "Existing records are kept privately, as described below, and you can still ask us to delete yours at any time.</p>\n")

BOARD_SUB = f"""  <!-- {MARKER} · The Borrowed Garden noticeboard, privacy notice {VERSION} -->
    <h3 class="pv5-sub" id="borrowed-garden-noticeboard">The Borrowed Garden noticeboard</h3>
    <p>The Borrowed Garden noticeboard is a free board where people with garden space they could share, and people looking for somewhere to grow, can post a short listing. It is separate from the two registers above.</p>
    <p>If you post a listing, we collect: whether you have space or want space; your county; a general area, such as a town or neighbourhood; the type of space; roughly when; a short description; your email address; and the date you sent it and that you agreed to how your listing is shown. We give you a reference number.</p>
    <p><strong>What is public, and what is private.</strong> If we approve your listing, the noticeboard shows the side, county, general area, type of space and timing you chose, the description as approved, the reference number, the date it was posted and the date it comes down. Your email address is never shown and is not shared with anyone; we use it only to contact you about your listing. We do not ask for your name, telephone number, address or Eircode, and the form refuses descriptions that contain contact details, a web address or an address. We do not store your IP address, and the form does not use cookies.</p>
    <p><strong>Moderation.</strong> Every listing is read by PlotNua before anything is published. We may decline a listing, or tidy its wording or general area to remove identifying details, but we do not change its meaning. We may remove a published listing at any time.</p>
    <p><strong>Expiry and removal.</strong> A published listing comes down 90 days after it is approved. To ask us to remove or delete your listing at any time, email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a> with your reference number; we will take it down and delete it.</p>
    <p><strong>What the noticeboard does not do.</strong> PlotNua does not check, visit or verify any garden or person, does not match anyone, and does not arrange garden-sharing agreements. Contact between people through the noticeboard is not available yet, so nobody can contact you through it and your email address is not passed to anyone.</p>
    <p><strong>If that changes.</strong> If we later offer a way to reply to a listing, we will update this notice before it starts and explain how it works.</p>
    <p>We rely on your consent, which you give by ticking the box when you post a listing. You can withdraw it at any time by asking us to remove your listing.</p>
"""
S2_OLD = "    <p>If you add an idea to the Idea Board, we collect the information described in Section 5.</p>\n"
S2_NEW = S2_OLD + "    <p>If you post a listing on The Borrowed Garden noticeboard, we collect the information described in Section 7.</p>\n"
S7A_OLD = '    <h3 class="pv5-sub">The Garden Owner Register (homeowners)</h3>\n'
S7A_NEW = PAUSED + S7A_OLD
S7B_OLD = "  </section>\n\n  <!-- PLOTNUA-ART-PRIVACY-V4"
S7B_NEW = BOARD_SUB + S7B_OLD
S10_OLD = "    <p>The Idea Board described in Section 5 runs on a PlotNua service hosted on infrastructure provided by Cloudflare.</p>\n"
S10_NEW = S10_OLD + "    <p>The Borrowed Garden noticeboard described in Section 7 runs on the same kind of PlotNua service, hosted on infrastructure provided by Cloudflare.</p>\n"
S12_OLD = ("    <p>Idea Board ideas waiting for review are kept for up to 90 days; ideas we do not publish, or remove from the board, "
           "are deleted 30 days after that decision; published ideas are kept while they are on the board, as described in Section 5.</p>\n")
S12_NEW = S12_OLD + ("    <p>Noticeboard listings waiting for review are kept for up to 90 days; listings we decline, remove or that have come "
                     "down after 90 days are deleted 30 days after that, as described in Section 7.</p>\n")
PAIRS = [(S2_OLD, S2_NEW), (S7A_OLD, S7A_NEW), (S7B_OLD, S7B_NEW), (S10_OLD, S10_NEW), (S12_OLD, S12_NEW)]


def apply_v10(text: str) -> str:
    if MARKER in text:
        raise ValueError("V10 already applied")
    if "PLOTNUA-IDEA-BOARD-PRIVACY-V9" not in text:
        raise ValueError("V10 applies on top of V9 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V10 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v10(text: str) -> str:
    """The exact page beneath V10. A page without V10 passes through untouched; a page that carries the V10 marker but
    not exactly the governed V10 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V10 marker but not exactly the governed V10 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v10(out) != text:
        raise ValueError("privacy.html V10 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v10(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V10 (The Borrowed Garden noticeboard) applied")
