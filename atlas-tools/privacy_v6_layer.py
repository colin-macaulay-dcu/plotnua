"""PlotNua · Privacy Notice V6 layer: the ONE definition of the V6 blocks.

Shared by build-privacy-v6.py (which applies them) and by every earlier
privacy verifier (V4, V5, the Garden and Art register builders and proofs),
which read privacy.html through without_v6() so that their governed V3/V4/V5
checks keep verifying exactly the text they govern, unchanged.

without_v6(text): exact inverse of apply_v6(). Text without the V6 marker is
returned untouched. Text with the marker but not EXACTLY the governed V6
blocks raises ValueError (so a drifted V6 cannot hide behind the layering).
"""
from __future__ import annotations

MARKER = "PLOTNUA-GROWER-PRIVACY-V6"

H7_OLD = "    <h2>7. The Garden Owner Register</h2>\n"
H7_NEW = (f"  <!-- {MARKER} · Garden Owner Register and Grower Register, privacy notice 2026-10-PHASE2-V6 -->\n"
          "    <h2>7. The Garden Owner Register and the Grower Register</h2>\n"
          "    <p>PlotNua keeps two registers for The Borrowed Garden pilot: the Garden Owner Register, for homeowners who might share part of their garden, and the Grower Register, for people who would like somewhere to grow. They are separate lists with separate forms and separate consent. Joining one does not add you to the other, and nobody on one register can see the other.</p>\n"
          "    <h3 class=\"pv5-sub\">The Garden Owner Register (homeowners)</h3>\n")
GROWER_SUB = """    <h3 class="pv5-sub">The Grower Register (growers)</h3>
    <p>The Grower Register is a list, kept privately by PlotNua, of people who would like somewhere to grow and who might be introduced to a homeowner nearby. PlotNua is exploring this as a small pilot. Joining is voluntary and free. Matching is not live, and joining the register does not arrange an introduction or mean that a garden is available.</p>
    <p>The Borrowed Garden Grower Check is private: answering its questions does not send PlotNua your details. If you choose to join the register, your answers fill in the form, where you can see and change them before you submit.</p>
    <p>What we collect when you join:</p>
    <ul>
      <li>your first name;</li>
      <li>your email address;</li>
      <li>your county and the area you choose from a short list;</li>
      <li>how much space you are looking for and roughly when;</li>
      <li>if you choose to tell us, your town or general area and how far you would travel;</li>
      <li>anything you choose to add in the note; and</li>
      <li>a record that you gave your consent, which version of this notice applied, and when you joined.</li>
    </ul>
    <p>We do not collect your address, your Eircode, your phone number, your surname, your age, or anything about your health.</p>
    <p>We use this information so that we can tell you if someone near you has growing space they would consider sharing. We rely on your consent, which you give by ticking the box when you join. You can withdraw it at any time.</p>
    <p>Your record is private to PlotNua. It is not published, and there is no public listing, map, profile or directory. Records are reviewed by a person at PlotNua. If we think there might be a fit, we will email you first and describe the homeowner in general terms only. Your email address would only be shared with another person if you said yes to one specific introduction, and introductions are not yet available.</p>
    <p>Grower Register records are kept in the same database as the Garden Owner Register, in a separate table, and are sent and stored by the same service providers, in the same way, as described above.</p>
    <p>We keep your record for a maximum of 24 months. You can ask us to delete it at any time, and we may delete it sooner if it is no longer needed.</p>
    <p>To leave the register or ask us to delete your record, email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>. There is nothing to cancel and no notice period. When we delete your record we keep a separate note that you gave permission and that we honoured your request. That note holds a one-way digital fingerprint made from your email address, not the address itself, so that we can show we did what you asked.</p>
"""
S7_END_OLD = "so that we can show we did what you asked.</p>\n  </section>\n\n  <!-- PLOTNUA-ART-PRIVACY-V4"
S2_OLD = "    <p>If you choose to join the Garden Owner Register, we also collect the information described in Section 7.</p>\n"
S2_NEW = S2_OLD + "    <p>If you choose to join the Grower Register, we also collect the information described in Section 7.</p>\n"
S10_OLD = "    <p>The Garden Owner Register described in Section 7 also runs on a PlotNua service hosted on infrastructure provided by Cloudflare.</p>\n"
S10_NEW = "    <p>The Garden Owner Register and the Grower Register described in Section 7 also run on a PlotNua service hosted on infrastructure provided by Cloudflare.</p>\n"
S12_OLD = "    <p>Garden Owner Register records are kept for a maximum of 24 months, as described in Section 7.</p>\n"
S12_NEW = S12_OLD + "    <p>Grower Register records are kept for a maximum of 24 months, as described in Section 7.</p>\n"




def apply_v6(text: str) -> str:
    out = text.replace(H7_OLD, H7_NEW)
    out = out.replace(S7_END_OLD, S7_END_OLD.replace("</p>\n  </section>", "</p>\n" + GROWER_SUB + "  </section>", 1))
    return out.replace(S2_OLD, S2_NEW).replace(S10_OLD, S10_NEW).replace(S12_OLD, S12_NEW)


def without_v6(text: str) -> str:
    if MARKER not in text:
        return text
    for block in (H7_NEW, GROWER_SUB, S2_NEW, S10_NEW, S12_NEW):
        if text.count(block) != 1:
            raise ValueError("privacy.html carries the V6 marker but not exactly the governed V6 text")
    out = (text.replace(H7_NEW, H7_OLD).replace(GROWER_SUB, "").replace(S2_NEW, S2_OLD)
               .replace(S10_NEW, S10_OLD).replace(S12_NEW, S12_OLD))
    if MARKER in out or apply_v6(out) != text:
        raise ValueError("privacy.html V6 layer is not an exact, reversible edit")
    return out


def read_without_v6(path) -> str:
    return without_v6(path.read_text(encoding="utf-8"))
