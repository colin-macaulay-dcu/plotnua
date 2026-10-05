#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED REGISTER EDIT — add Switch Electrical and Sauna Experts to
atlas-tools/preview-only-suppliers.json.

Adding a supplier here is not a permission. It is what puts their preview
UNDER CONTAINMENT: prove-preview-only-containment.mjs then checks, on every
run, that none of their imagery appears anywhere in the tree, that their
preview carries all five robots directives, links back and credits them, that
no sitemap lists it, that no rights record exists, that no runtime payload
reaches them, and that the page makes none of the claims on the list below.

BOTH ROWS ARE imagery_mode "none". Both suppliers replied asking to SEE the
page. Neither granted anything, so none of their imagery may appear on ANY
page including their own preview. The "preview-only" mode exists for a
supplier who invited imagery for the preview in writing; neither did, and the
two modes are checked by different code paths precisely so that a one-character
edit cannot promote one into the other.

THE FORBIDDEN LISTS ARE PER SUPPLIER and are not copies of each other. Switch
Electrical's is built around MONEY and SERVICE AREA, because the thing a solar
preview overclaims is a return and a county. Sauna Experts' is built around
BORROWED SUPERLATIVES, because their own site ranks itself four different ways
and PlotNua repeating any of it would read as an endorsement.

The edit is anchored: it matches the final row's closing fence exactly once or
it refuses, and the result must parse as JSON with exactly two more suppliers
than it started with.

Run: python3 supplier-preview-system/register-switch-and-sauna-previews.py
     [--check]
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REGISTER = HERE.parent / "atlas-tools" / "preview-only-suppliers.json"
CHECK = "--check" in sys.argv

NEW_ROWS = """    },
    {
      "name": "Switch Electrical",
      "imagery_mode": "none",
      "legal_name": "Switch Electrical Limited",
      "page": "switch-electrical-preview.html",
      "site_host": "switchelectrical.ie",
      "credit": "\\u00a9 Switch Electrical Ltd",
      "image_hosts": [
        { "host": "switchelectrical.ie", "path_prefix": "/gallery/",
          "why": "their completed-installation gallery, served from their own domain" },
        { "host": "switchelectrical.ie", "path_prefix": "/_astro/",
          "why": "the build-time image directory their site serves the hero and page imagery from" }
      ],
      "forbidden_claims": [
        "save you", "savings of", "guaranteed saving", "will save",
        "pay for itself", "pays for itself", "payback", "return on investment",
        "free electricity", "cut your bills", "lower your bills",
        "reduce your bills",
        "nationwide", "across ireland", "all of ireland", "anywhere in ireland",
        "suitable for your home", "suits your roof", "any roof", "every home",
        "cheapest", "best price", "number one",
        "planning exempt", "no planning permission",
        "warranty", "guaranteed for", "lead time of"
      ],
      "forbidden_claims_note": "MONEY AND SERVICE AREA, not product facts. Switch Electrical's own homepage says \\"cut your electricity bills\\" and carries three customer reviews mentioning bill reductions; that is their copy about their customers and would be an unevidenced claim about a stranger's house in PlotNua's voice. The service-area bans exist because the site names five counties and adds \\"across Leinster\\" -- a page that rounded that up to nationwide would send them enquiries they cannot serve. NOTE WHAT IS NOT BANNED: the words \\"free\\" and \\"guarantee\\". The free survey, the free quote and the free BER are all published, and the Clean Export Guarantee is the name of a real scheme.",
      "evidence": "Switch Electrical replied \\"Preview pls\\" on 5 October 2026 to outreach sent to sales@switchelectrical.ie, when the outreach offered both YES and PREVIEW. A request to see the page is not a grant.",
      "atlas_permission_ref": "NOT IN ATLAS — Switch Electrical Limited has no organisation record, no product record and no permission record. A full-tree search on 5 October 2026 returned nothing. There is no relationship to reflect and none is implied."
    },
    {
      "name": "Sauna Experts",
      "imagery_mode": "none",
      "legal_name": "Sauna Experts Limited",
      "page": "sauna-experts-preview.html",
      "site_host": "saunaexperts.ie",
      "credit": "\\u00a9 Sauna Experts",
      "image_hosts": [
        { "host": "saunaexperts.ie", "path_prefix": "/wp-content/uploads/",
          "why": "their WordPress media library on their own domain, which is where every product and gallery image is served from" }
      ],
      "forbidden_claims": [
        "number one", "highest rated", "best sauna", "ireland's top",
        "ireland's best", "most professional", "the leading", "top rated",
        "market leader", "cheapest", "best price",
        "20 years of experience", "16 years of experience",
        "warranty", "guaranteed for", "we guarantee",
        "lead time of", "free delivery", "delivery included",
        "planning exempt", "no planning permission",
        "cures", "treats", "proven to reduce"
      ],
      "forbidden_claims_note": "BORROWED SUPERLATIVES FIRST. Their own site calls them \\"Ireland's Number One Sauna Shop\\", \\"the highest rated sauna supplier in Ireland\\", \\"Ireland's Top Sauna Manufacturer\\" and \\"the most professional\\". Those are their marketing and nobody's verified fact; PlotNua repeating one would convert an unchecked claim into an apparent ranking on a page whose whole purpose is to show editorial independence. THE EXPERIENCE FIGURES ARE BANNED BECAUSE THEY CONTRADICT EACH OTHER: the homepage says \\"over 20 years of experience\\" of the custom saunas and, four paragraphs later, \\"over 16 years\\" of the founders. Both are first-party and they disagree, so neither is used. NOTE WHAT IS NOT BANNED: installation and nationwide delivery. Unlike the Irish Sauna Company case, this supplier publishes both on the product page itself -- \\"nationwide delivery, sauna installation, and comprehensive support with building advisory\\" -- so they are evidenced and may be reported, with the open question of what sits inside the price left open rather than answered.",
      "evidence": "Sauna Experts replied \\"PREVIEW\\" on 5 October 2026 to outreach sent to saunaexpertsltd@gmail.com, when the outreach offered both YES and PREVIEW. A request to see the page is not a grant.",
      "atlas_permission_ref": "NOT IN ATLAS — Sauna Experts Limited has no organisation record, no product record and no permission record. A full-tree search on 5 October 2026 returned nothing. There is no relationship to reflect and none is implied."
    }
  ]
}
"""

ANCHOR = """    }
  ]
}
"""


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


src = REGISTER.read_text(encoding="utf-8")
before = json.loads(src)
n_before = len(before["suppliers"])

if src.count(ANCHOR) != 1:
    die("the register's closing fence was not found exactly once (%d). The "
        "file's shape has changed and this edit will not guess at it."
        % src.count(ANCHOR))

out = src.replace(ANCHOR, NEW_ROWS, 1)

# ---- post-conditions, before anything is written -------------------------
try:
    after = json.loads(out)
except Exception as e:
    die("the result does not parse as JSON: %s" % e)

if len(after["suppliers"]) != n_before + 2:
    die("expected %d suppliers after the edit, got %d"
        % (n_before + 2, len(after["suppliers"])))

names = [s["name"] for s in after["suppliers"]]
for who in ("Switch Electrical", "Sauna Experts"):
    if names.count(who) != 1:
        die("%r appears %d times in the register" % (who, names.count(who)))

for s in after["suppliers"]:
    for field in ("name", "imagery_mode", "legal_name", "page", "site_host",
                  "credit", "image_hosts", "forbidden_claims", "evidence",
                  "atlas_permission_ref"):
        if field not in s:
            die("row %r is missing the required field %r" % (s["name"], field))
    if s["imagery_mode"] not in ("none", "preview-only"):
        die("row %r carries an unrecognised imagery_mode" % s["name"])

# THE ONE THAT MATTERS: neither new row may be permissive.
for s in after["suppliers"]:
    if s["name"] in ("Switch Electrical", "Sauna Experts"):
        if s["imagery_mode"] != "none":
            die("%r was registered with imagery_mode %r. Both of these "
                "suppliers asked to SEE the preview and granted nothing, so "
                "the only correct mode is 'none'." % (s["name"], s["imagery_mode"]))

if CHECK:
    print("--check: the edit applies cleanly and the result is valid. "
          "Nothing written.")
    sys.exit(0)

REGISTER.write_text(out, encoding="utf-8")
print("preview-only register: %d suppliers (was %d)"
      % (len(after["suppliers"]), n_before))
for s in after["suppliers"]:
    print("  %-22s %-13s %s" % (s["name"], s["imagery_mode"], s["page"]))
