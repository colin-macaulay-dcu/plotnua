# PlotArt Services: unpublished photo-and-logo card design (19 Nov 2026)

PRIVATE DEVELOPMENT MATERIAL: not part of the public site (nothing under `plotart/`), not in the image-rights manifest.

The Services page is **paused** (founder, 19 Nov 2026: both providers asked for changes to their listings). Its live
source is `atlas-tools/build-plotart-services.py` and `../plotart-services.css`; it is built only while the launch switch
`services_page` is on. To restore: update the provider details, switch `services_page` (and `services_indexable`) on,
run `python3 atlas-tools/build-plotart-services.py` and `python3 atlas-tools/plotart-services-nav.py .`, re-pin the
launch manifest, and release through the protected process.

`cards-preview.html` and `cards-preview.css` are the founder-reviewed redesign: a wide photograph, the provider's logo on
a small plaque, one short rule in the provider's colour (Maurice Ward `#68B0D8`; Hang-It off-white). The images are
**not stored here** and must not be published until each provider gives written permission (logo and photograph use,
resizing, credit wording; for Maurice Ward, consent of the identifiable staff). Sources:

| Provider | Asset | Source |
|---|---|---|
| Maurice Ward Art Handling | Logo (SVG, `#2E3126`) | https://mauriceward-arthandling.com/wp-content/uploads/2022/03/mwah-logo.svg |
| Maurice Ward Art Handling | Photo: two handlers carrying a gilt-framed painting (1180×786) | https://mauriceward-arthandling.com/wp-content/uploads/2022/03/homepage-img-1.jpg |
| Hang-It | Logo "HANG-IT · The Hanging Specialists" (PNG) | https://d2f0ora2gkri0g.cloudfront.net/68/0d/680d0588-5d3b-4ac9-a772-7753f3767293.png |
| Hang-It | Photo: framed photographs hung level in a living room (4032×2268) | https://d2f0ora2gkri0g.cloudfront.net/8b/b5/8bb5dc58-076f-466a-9b87-df0aae4fc3ba.jpg |

Alternatives: Maurice Ward `…/2022/03/services-img-1.jpg` (fleet), illustrations `service_transport.jpg`,
`service_installation.jpg`; Hang-It `…/79/5d/795dcc28-5faa-4432-a4bc-35f12b699c6d.jpeg` (laser levelling).
Preview paths in `cards-preview.html` (`_preview-providers/…`) point to local copies made for review only.

## Update 19 Nov 2026: Hang-It approved, pricing removed

- Hang-It (John) approved its listing with the logo and photograph, asking for all pricing to be removed. Recorded in
  Atlas (Organisations ORG-HANGIT rec6zbEPxUrcT2XVN; Image Permission Outreach IPO-HANGIT-20261119 rech5aeWWGcj0sZVM)
  and image-rights-records.json (Granted with Conditions — Founder Confirmed; scope feature, imagery, hosting).
- The builder now renders the cards from data: Hang-It with its photograph (credit "Photo: Hang-It") and logo, and
  "Contact Hang-It directly for a quotation." in place of prices; Maurice Ward kept unchanged but `publish: False`
  (amendments outstanding). Review copy: `python3 atlas-tools/build-plotart-services.py --preview DIR`.
- Image copies and source hashes: `../images/hang-it/` (image-copies.json). Provenance declarations for the three
  photograph copies are prepared in `../images/hang-it/provenance-pending.json`, to merge in the restoring release.
- OPEN: the logo cannot yet be declared in the provenance register (supplier labels are Photograph or Visualisation
  only). Publishing it needs a founder-approved register extension; otherwise restore with the photograph only.
