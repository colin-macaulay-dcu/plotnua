# Privacy notice · WhatsApp enquiries subsection · provisional founder confirmation

**27 October 2026 · Provisional founder confirmation. NOT legal approval.**

## The text

The "WhatsApp enquiries" subsection under "5. Contact Forms" of `privacy.html`
(introduced in `656528b`, 21 Oct 2026, integrated from `bb4cad0`, released with
the H5 homepage). Its exact HTML is `WHATSAPP_BLOCK` in
`atlas-tools/privacy_page_layers.py`.

## The founder's decision

From "PlotArt limited launch · founder approval: privacy verification repair"
(27 Oct 2026):

- Retain the existing WhatsApp subsection.
- Its wording is provisionally accepted as an accurate description of the
  intended contact process, subject to legal and privacy review.
- Record this as provisional founder confirmation, not legal approval.
- Do not publish V7 yet.

## How it is recorded

- `WHATSAPP_PROVISIONAL` in `privacy_page_layers.py` holds this confirmation.
- `WHATSAPP_CONFIRMATION` stays `None` until the legal and privacy review is
  complete and the founder confirms the exact text. Until then:
  - `prove-privacy-whatsapp.py` reports **PROVISIONAL … NOT legal approval**;
  - `build-privacy-v7.py` refuses to publish V7 (guard P5).
- The exact text is still enforced: any change to the block, a duplicate, a move
  or extra WhatsApp wording fails the release checks.

## Open

- Legal and privacy review of the subsection (with V7).
- The notice carries no version change for this subsection; whether one is
  needed is part of that review.
