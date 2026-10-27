#!/usr/bin/env python3
"""PlotNua · the WhatsApp subsection in privacy.html: exactness and status. Read-only.

    python3 atlas-tools/prove-privacy-whatsapp.py

The subsection (656528b, 21 Oct 2026) is NOT treated as approved by this proof.
It checks that the published text is exactly the recorded block (so it cannot
change unnoticed) and prints its confirmation status. It passes while the text
is exact; the status line says whether the founder has confirmed it.
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import privacy_page_layers as L

text = (HERE.parent / "privacy.html").read_text(encoding="utf-8")
ok = True
try:
    stripped = L.without_whatsapp(text)
    present = stripped != text
except ValueError as e:
    print("PRIVACY WHATSAPP · FAILED — " + str(e)); sys.exit(1)
status = ("CONFIRMED · " + L.WHATSAPP_CONFIRMATION) if L.WHATSAPP_CONFIRMATION else "UNCONFIRMED · awaiting the founder's confirmation"
if present:
    print("PRIVACY WHATSAPP · OK — exact recorded text present (%s) · %s" % (L.WHATSAPP_COMMIT, status))
else:
    print("PRIVACY WHATSAPP · OK — subsection not present · %s" % status)
