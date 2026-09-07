#!/usr/bin/env python3
"""ISSUE 007 — build supplier-operations-evidence-v1.json from adjudications.

CONFIRMED values are entered by hand below, each with the page whose visible
content supports the claim at organisation scope and the date it was read.
Everything else is DERIVED mechanically, never invented:

  STATED_NOT_CERTIFIED  Atlas prose asserts something the page did not support
  UNKNOWN               Atlas asserts nothing either — a finding, not a negative

Only organisations whose pages were actually read appear at all. An absent
organisation has no typed evidence; that is not a negative claim about it.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CHECKED = "2026-09-07"

# ---- CONFIRMED, adjudicated from the quoted page content ------------------
INSTALL = {
    # org id: (installationType, page URL)
    "recw124UIanKV5Ath": ("SUPPLIER_INSTALLS", "https://www.shomera.ie/garden-rooms/"),
    "rec0E8ongSL0hZnZR": ("SUPPLY_ONLY",       "https://www.lasita.com/installation-support"),
    "recFQ1GyK0fq2fK4I": ("SUPPLIER_INSTALLS", "https://sproutpod.ie/"),
    "rec7q7WitcIuY3phT": ("SUPPLIER_INSTALLS", "https://allinonecabins.ie/"),
    "recefOJGKHPwabRhV": ("SUPPLIER_INSTALLS", "https://www.loghouse.ie/"),
    "rec0zLenIbn3nsvjh": ("SUPPLIER_INSTALLS", "https://gardenofficesolutions.ie/"),
    "reccM9Gg66ZuZC0m3": ("SUPPLIER_INSTALLS", "https://allaboutoutdoors.ie/"),
    "reczankduIWGWwXKR": ("SUPPLIER_INSTALLS", "https://liveingardenpods.ie/"),
    "recnvHCjmfim16w3q": ("SUPPLIER_INSTALLS", "https://bigmantinyhomes.ie/"),
    "recIFIi1fxjwc1g1C": ("SUPPLIER_INSTALLS", "https://raycomodularhomes.ie/"),
    "recZsdhQM53LBVyyg": ("SUPPLIER_INSTALLS", "https://www.totalgardenrooms.com/"),
    "recyfWvDVODL06P8l": ("SUPPLIER_INSTALLS", "https://www.yardbox.co.uk/"),
    # ---- the final 19, certified 2026-09-07 under founder domain authorisation
    "rec17SIbblmee8Vs3": ("SUPPLY_ONLY",       "https://sips-house.com/"),
    "reclCNqekU666UWJA": ("SUPPLIER_INSTALLS", "https://boothsgardenstudios.co.uk/"),
    "recontC2BSomwggsc": ("SUPPLIER_INSTALLS", "https://www.cabinmaster.co.uk/"),
    "recKazlmd4FCnanxR": ("SUPPLIER_INSTALLS", "https://www.sanctumgardenstudios.com/"),
    "recuCWhMIEWD1X1yE": ("SUPPLIER_INSTALLS", "https://gardenofficebuildings.co.uk/"),
    "recmBdXALBPGk5wSI": ("SUPPLIER_INSTALLS", "https://nookprefab.com/"),
    "rec8j9KTIVfQAVMzg": ("SUPPLIER_INSTALLS", "https://www.oecogardenrooms.co.uk/"),
    "recEMNNtEYy59gmbt": ("SUPPLIER_INSTALLS", "https://koto.co.uk/"),
}
# org id: (roiDelivery, roiInstallCoverage, page URL)
DELIVERY = {
    "reclA5R4kPCCwc8Pc": ("CONFIRMED", "UNKNOWN",    "https://gardenhouse24.ie/"),
    "recFQ1GyK0fq2fK4I": ("CONFIRMED", "NATIONWIDE", "https://sproutpod.ie/"),
    "rec7q7WitcIuY3phT": ("CONFIRMED", "UNKNOWN",    "https://allinonecabins.ie/"),
    "rec4VIYIbk68JihtK": ("CONFIRMED", "UNKNOWN",    "https://timberliving.ie/"),
    "recIFIi1fxjwc1g1C": ("CONFIRMED", "UNKNOWN",    "https://raycomodularhomes.ie/"),
    "recP4lqMNuNceOyNh": ("CONFIRMED", "UNKNOWN",    "https://www.woodenhottubsale.co.uk/"),
    "recExaEx7i1hqG6CD": ("CONFIRMED", "UNKNOWN",
                          "https://mcdgardensheds.ie/delivery-cancellations-returns/"),
    "recefOJGKHPwabRhV": ("UNKNOWN",   "NATIONWIDE", "https://www.loghouse.ie/"),
}

# Organisations whose first-party pages were actually read in this pass.
READ = [
    "recw124UIanKV5Ath", "rec0E8ongSL0hZnZR", "reclA5R4kPCCwc8Pc",   # pilot
    "receufKmrd8c4QgMv", "recUnzSlV4tszVzg6", "recFQ1GyK0fq2fK4I",
    "recLQOPHHfSrfs3xA", "recn9B3Qn43VUXxAg", "rec7q7WitcIuY3phT",
    "recJwB6aXMbElG2Fm", "recOjnbeotdf0jnqH", "recefOJGKHPwabRhV",
    "recfV4V49BHoMsYBA", "rechco59Sn6wp3Aiq", "recZcfloN72CBES6I",
    "rec0zLenIbn3nsvjh", "recExaEx7i1hqG6CD", "reccM9Gg66ZuZC0m3",
    "reczankduIWGWwXKR", "rectRQUdpY3t4ukdP", "rec4VIYIbk68JihtK",
    "recv6T9JI9T8aqcRO", "recnvHCjmfim16w3q", "reczne3oE3EHQyp7L",
    "rec7dG4sHJtzstIHo", "recDRvQusj5KgRU2s", "recmW0HlJFr9GvLEj",
    "recIFIi1fxjwc1g1C", "recePJOyXsH8LXtwf", "recaVJQjZD9UV8JSs",
    "recfpcUL7s03Es3lV", "recZsdhQM53LBVyyg", "rectTyBhqejHG4GQG",
    "recyfWvDVODL06P8l", "recP4lqMNuNceOyNh", "recAbCMI3LkwWO3Z6",
    "recxdr0chc5ljRqfR", "rec66sNzKArqeOU23", "recrtMY2s1Tabf06e",
    "recdkZXPh12FyiCRr", "reczIVnJujZd8a2CK", "recZVKy9FPReF7I9H",
    # ---- the final 19
    "recsDmxfYLRJiaFmG", "recSDXX7gK0FT7g8G", "rec5Dwr8vYDDkHEeW",
    "rec17SIbblmee8Vs3", "rec2URqKyVwlhHSBw", "reclCNqekU666UWJA",
    "recontC2BSomwggsc", "recKazlmd4FCnanxR", "recXGziDNcDnpz0iN",
    "recbZVOTUMCmMphuj", "recJJ4jFPAMxw6IkY", "recuCWhMIEWD1X1yE",
    "rec7wp2vzUC3dxcYr", "recmBdXALBPGk5wSI", "rec8j9KTIVfQAVMzg",
    "recEMNNtEYy59gmbt", "recgsaDsSVCCad0q4", "rechsPFUooApigybT",
    "reczQn59haPghHYmT",
]

# Prose that asserts nothing. Anything else counts as an Atlas claim.
NO_CLAIM = re.compile(r"^\s*(none|not stated|no |unknown|not published)", re.I)

part = json.loads((ROOT / "garden-room-detail-suppliers-v1.json").read_text())["products"]
out = {}
for oid in READ:
    loc = part[oid]["locality"]
    rec = {"name": part[oid]["name"]}

    t, url = INSTALL.get(oid, (None, None))
    if t:
        rec.update(installationType=t, installationStatus="CONFIRMED",
                   installationSourceUrl=url, installationCheckedAt=CHECKED)
    else:
        prose = loc.get("installationModel", "")
        rec.update(installationType="UNKNOWN",
                   installationStatus="STATED_NOT_CERTIFIED"
                   if prose and not NO_CLAIM.match(prose) else "UNKNOWN")

    d = DELIVERY.get(oid)
    if d:
        roi, cov, durl = d
        rec.update(roiDelivery=roi, roiInstallCoverage=cov,
                   deliveryStatus="CONFIRMED",
                   deliverySourceUrl=durl, deliveryCheckedAt=CHECKED)
    else:
        prose = loc.get("deliveryCoverage", "")
        rec.update(roiDelivery="UNKNOWN", roiInstallCoverage="UNKNOWN",
                   deliveryStatus="STATED_NOT_CERTIFIED"
                   if prose and not NO_CLAIM.match(prose) else "UNKNOWN")
    out[oid] = rec

doc = {
    "schema": "plotnua.supplier-operations-evidence",
    "version": "1.0.0-scale",
    "note": ("GENERATOR INPUT, NEVER PUBLISHED. Typed Supplier Operations Evidence keyed by "
             "canonical Airtable organisation id. Every CONFIRMED value names the page whose "
             "visible content supports the claim and the date it was read. STATED_NOT_CERTIFIED "
             "means Atlas prose asserts something no read page supported. UNKNOWN asserts "
             "nothing. Organisations absent from this file were not read and carry no typed "
             "evidence — which is a finding, not a negative. Nothing here is read by "
             "marketEligibility(), getEligibleAtlasPool(), qualification, ranking or "
             "recommendation selection."),
    "checkedAt": CHECKED,
    "organisationsRead": len(READ),
    "organisations": out,
}
(HERE / "supplier-operations-evidence-v1.json").write_text(
    json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("wrote", len(out), "organisations")
