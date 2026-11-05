# Direction C · design previews (NOT PRODUCTION)
Design exploration only (founder brief, 5 Nov 2026). This folder lives on branch `design/plotart-vg-direction-c` and must never be merged or released.
- `build-previews.py` copies the live `plotart/gallery/index.html` and swaps only its collection section for C1, C2 or Direction A, at 1, 5, 15 and 25 open galleries.
- Leah Hewson's name, practice, position, artwork and link are read unchanged from the live page and her gallery.json.
- Every other artist is a labelled MOCK placeholder (`mock/`); reserved and in-preparation positions are illustrative.
- View locally: `python3 -m http.server` from the repository root, then open `/plotart/gallery-design-c/c1-5.html` etc.
