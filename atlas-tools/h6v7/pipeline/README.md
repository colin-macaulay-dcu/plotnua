# H6 v7 asset pipeline (daylight BEFORE/POSSIBLE pair)
Run from a work folder containing `in/hero-before-master.png` and `in/hero-possible-master.png` (the handover masters,
sha256 373b6805… and 8af0550f…, kept on the founder's Mac, not in this repo):
`align.py` → `podpatch.py` → `reflection.py` → `layers.py` → `fixpatch.py` (9 Nov) → `devices.py` → `export.py`; `sky.py` for the cloud band.
Then `python3 atlas-tools/build-h6-homepage.py --mount && --check`. Snippet edits: `../migrate-snippet.py` (8 Nov), `../devices-snippet.py` (9 Nov).
