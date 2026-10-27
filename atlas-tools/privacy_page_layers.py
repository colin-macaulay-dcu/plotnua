"""PlotNua · privacy.html page layers since Privacy V6 (verification repair, 27 Oct 2026).

WHY THIS EXISTS
  The privacy verifiers (build-privacy-v4.py, build-privacy-v5.py,
  build-art-space-register.py, and the proofs that drive them) compare
  privacy.html with the exact pages they govern. Two kinds of later change made
  them refuse from 20 October 2026, although no governed sentence changed:

  1. SITE SHELL (not notice text), each made by its own governed builder:
       2026-10-20  4f15bc9  shared identity layer (build-identity-stage1.py)
       2026-10-20  a63b7a2  theme colour            (build-identity-stage1.py)
       2026-10-22  b2da366  Architectural Anthracite theme (build-identity-stage1.py)
       2026-10-23  d9db752  global header v2         (build-global-header.py / pn_header.py)
     (the 19-20 Oct search-rail label change already has search_rail_layer.py)
     These are removed with those builders' own strip() functions, which their
     guards (prove-identity-stage1, prove-global-header, both release checks)
     keep exact. GUARD G1 below proves that removing the shell never touches a
     single byte of the notice itself (from its opening sentence to </main>).

  2. ONE WORDING ADDITION: the "WhatsApp enquiries" subsection under Section 5
     (656528b, 21 Oct 2026). It is NOT treated as approved here. The verifiers
     read the page without it, so they keep verifying every governed V3-V6
     sentence byte for byte, and WHATSAPP_CONFIRMATION records its status
     separately. While it is None:
       - prove-privacy-whatsapp.py reports it as UNCONFIRMED (and fails if the
         text has drifted from the exact block below);
       - build-privacy-v7.py (PlotArt) refuses to publish any further privacy
         change.
     The founder's confirmation, if given, is recorded in WHATSAPP_CONFIRMATION.

read_governed(text): privacy.html as the V3-V6 verifiers govern it. Exact and
narrow: the WhatsApp block must be present exactly once, in Section 5, or be
absent; anything else raises ValueError, so nothing can hide behind the layer.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

WHATSAPP_BLOCK = (
    '    <h3>WhatsApp enquiries</h3>\n'
    '    <p>You can also choose to contact PlotNua through WhatsApp Business on <a href="https://wa.me/353834036695" target="_blank" rel="noopener noreferrer">+353 83 403 6695</a>. The website link opens WhatsApp; it does not send a message automatically or include your property information. When you send us a message, we receive its contents, any attachments you choose to send, and the contact or profile information WhatsApp makes available to us, which may include your phone number and profile name.</p>\n'
    '    <p>We use this information to respond to your enquiry and handle related follow-up, relying on our legitimate interests in answering enquiries or, where applicable, taking steps at your request before entering into an arrangement. Messaging us does not join you to a register or opt you into marketing. WhatsApp enquiries follow the contact-enquiry retention arrangements in Section 12. You can ask about or request deletion of your information by messaging us or emailing <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>.</p>\n'
    '    <p>WhatsApp also processes information under its own <a href="https://www.whatsapp.com/legal/privacy-policy-eea" target="_blank" rel="noopener noreferrer">Privacy Policy</a>. Email and the website contact form remain available if you prefer not to use WhatsApp.</p>\n'
    '    <h3>Website forms</h3>\n'
)
WHATSAPP_ANCHOR = '    <h2>5. Contact Forms</h2>\n'
WHATSAPP_COMMIT = "656528b (21 Oct 2026), integrated from bb4cad0"

# None = NOT confirmed by the founder. Never fill this in without his explicit,
# dated confirmation of the exact block above.
WHATSAPP_CONFIRMATION = None

NOTICE_START = '<p class="lede">This Privacy Policy explains'
NOTICE_END = '</main>'


def without_whatsapp(text: str) -> str:
    n = text.count(WHATSAPP_BLOCK)
    if n == 0:
        if "WhatsApp enquiries" in text:
            raise ValueError("privacy.html carries a WhatsApp subsection that differs from the exact recorded block")
        return text
    if n != 1 or text.count(WHATSAPP_ANCHOR + WHATSAPP_BLOCK) != 1:
        raise ValueError("the WhatsApp block is not present exactly once, directly under Section 5")
    out = text.replace(WHATSAPP_ANCHOR + WHATSAPP_BLOCK, WHATSAPP_ANCHOR, 1)
    if "WhatsApp enquiries" in out:
        raise ValueError("WhatsApp wording remains outside the recorded block")
    return out


_IDS = None


def _identity():
    global _IDS
    if _IDS is None:
        spec = importlib.util.spec_from_file_location("pn_identity_stage1", ROOT / "atlas-tools" / "build-identity-stage1.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<meta name="theme-color" content="([^"]+)">', home)
        mod.HOME_THEME = m.group(1) if m else None
        _IDS = mod
    return _IDS


def _notice(text: str) -> str:
    if text.count(NOTICE_START) != 1 or text.count(NOTICE_END) != 1:
        raise ValueError("privacy.html: the notice boundaries are not present exactly once")
    return text[text.index(NOTICE_START):text.index(NOTICE_END)]


def without_site_shell(text: str, notice: bool = True) -> str:
    """Remove the identity layer, theme colour and global header with their own
    builders' strip(). GUARD G1 (privacy.html): the notice text is byte-identical
    before and after. For another page built from the privacy shell (the Artist
    Register page), notice=False and G1 checks that page's <main> instead."""
    out = _identity().strip(text)
    if notice:
        if _notice(out) != _notice(text):
            raise ValueError("G1 removing the site shell changed the notice text")
    else:
        main = lambda s: s[s.index("<main"):s.index("</main>")]
        if main(out) != main(text):
            raise ValueError("G1 removing the site shell changed the page's main content")
    return out


def read_governed(text: str) -> str:
    return without_whatsapp(without_site_shell(text))
