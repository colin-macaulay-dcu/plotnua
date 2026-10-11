# IMAGE PROVENANCE · LOADER COVERAGE

Founder final action 1: *"Confirm the provenance guard covers all locally
hosted images used on published pages, including relevant CSS backgrounds,
picture/source elements and other image loading mechanisms."*

**Confirmed — but not as it stood.** The audit found four image-loading
mechanisms in live use that the guard had never read, and eight tracked
images outside the inventory. Both are closed. No published page, caption or
image was altered.

---

## 1 · WHAT THE GUARD COULD NOT SEE

Measured against the repository, not assumed.

| mechanism | in use | was scanned |
|---|---|---|
| `<link rel="*icon" href>` | **122 references** | no |
| `twitter:image` | **23 references** | no |
| `site.webmanifest` icons | **2 images** | no — not an HTML file |
| pages below the repository root | **12 HTML pages** | no — `readdirSync(ROOT)` only |
| `<img src>`, `<source srcset>`, `url()`, `og:image` | yes | yes |

The fourth is the one that mattered most in principle: the guard read the
root directory, while the image-**rights** gate sitting beside it already
walked recursively. Two guards over the same tree disagreed about what the
tree was.

### And eight images that were in no register at all

`favicon.ico` · `favicon-16x16.png` · `favicon-32x32.png` ·
`favicon-48x48.png` · `apple-touch-icon.png` ·
`android-chrome-192x192.png` · `android-chrome-512x512.png` ·
`404-hidden-discovery.png`

**Seven of the eight are referenced from published pages.** They sat outside
the inventory because the recovery tool scanned `assets/` and the register
was built from what it found. An inventory derived from a scanner inherits
the scanner's blind spots.

This is the second time this inventory has grown for that reason — 85 → 101
when the guard caught three brand SVGs, and now 101 → 110. The fix is
structural: the recovery tool now walks from the repository root with an
explicit `SKIP_DIRS`, so a new directory is **in** scope by default rather
than out of it.

---

## 2 · THE 101 ENTRIES ARE PRESERVED, AND NINE WERE ADDED

Founder final action 3 said preserve the 101-entry inventory. Verified
mechanically against `git show HEAD:image-provenance-records.json`:

```
committed entries        101
dropped                    0
hashes changed             0
added                      9
now                      110
records: []                     ← still nothing declared
```

A preservation guard in `build-image-provenance-register.py` now makes that
non-optional — it refuses to write a register that loses an asset or changes
a committed hash:

```python
lost  = [a for a in old_rows if a not in new_rows]
moved = [a for a, h in old_rows.items()
         if a in new_rows and new_rows[a] != h]
if lost or moved:
    die("the existing backlog would not be preserved: ...")
```

The ninth addition is `atlas-visual-references/atlas-a-sketch-visual-authority.jpg`,
tracked and outside `assets/`.

**Nothing was declared.** Founder final action 4: no provenance was invented.
The legacy backlog is 110 and the count still only goes down.

---

## 3 · WHAT THE GUARD NOW READS

Recursive from the root (`SKIP_DIRS`: `.git`, `node_modules`, `outputs`,
`.github`, `__pycache__`, `atlas-tools`), including `.webmanifest`, with
`.ico` a recognised image extension and `https://plotnua.ie/` normalised as
a self-origin so an absolute URL to our own host is treated as local.

**In use, now covered:** `<img src>` · `<source srcset>` · CSS `url()` ·
`og:image` · `twitter:image` · `msapplication-TileImage` ·
`<link rel=*icon href>` (both attribute orders) · webmanifest `"src"` ·
JS `.src =`

**Not yet in use, covered pre-emptively** so the next one does not need
another audit: `<img srcset>` · `imagesrcset` · `image-set()` ·
`<video poster>` · `<input type=image>` · `<object data>` · `<embed src>` ·
`(xlink:)href` to an image extension · `data-src|bg|image|background`

Result: **163 pages scanned, 70 local images referenced, 11/11 passing.**

---

## 4 · THIRTEEN NEW CAPABILITY CASES — AND A CONTROL THAT FAILED THREE TIMES

A widened scanner that cannot fail is worse than a narrow one, because it
looks like coverage. Each new mechanism got a mutation proving the guard
refuses an undeclared image loaded that way:

`C-LOAD-icon` · `C-LOAD-apple-touch` · `C-LOAD-twitter-image` ·
`C-LOAD-webmanifest` · `C-LOAD-subdir-page` · `C-LOAD-css-url` ·
`C-LOAD-img-srcset` · `C-LOAD-video-poster` · `C-LOAD-image-set` ·
`C-LOAD-js-src` · `C-LOAD-svg-image-href` · `C-LOAD-data-src`

Plus `C-LOAD-control`, which asserts the opposite: a **declared** image via
`<link rel="icon">` is *accepted*. Without it, a guard that refused
everything would have scored 12/12.

**The control went VACUOUS three times**, and each time the guard was right
and the test was wrong:

1. P8 refused — the declared AI row owed its approved label.
2. P9 refused — a declared record may not describe an unreferenced asset, and
   the control had not put it on the page.
3. P2 refused — the legacy asset was recorded but its bytes were not in the
   disposable tree.

Fixed by building an honest control rather than loosening the guard: both
assets on the page, the label present, and the legacy bytes copied in.

**Final: 33 mutations, 33 proved capable, 0 not proved.** Real tree
hash-verified untouched.

---

## 5 · GUARDS RUN (founder final action 8)

| suite | result |
|---|---|
| `validate-image-provenance.js` | **11/11** · 163 pages, 70 local images, 110 backlog |
| `prove-image-provenance-capability.mjs` | **33 mutations, 33 proved capable** |
| `prove-image-rights-gate-capability.mjs` | **5/5** |
| `validate-image-rights.js --scan-html` / `--self-test` | pass / pass |
| `generate_image_rights_manifest.py --check` | manifest matches its records |
| `prove-manifest-check-capability.py` | pass |
| `prove-biobuilds-imagery.mjs` | **14/14** |
| `prove-biobuilds-imagery-capability.mjs` | **15/15** |
| `prove-biobuilds-containment.mjs` + capability | pass · **11/11** |
| `prove-supplier-publication-gate.mjs` + capability | **14/14** · **14/14** |
| `prove-founder-exception.mjs` + capability | **18/18** · **20/20** |
| `prove-preview-only-containment.mjs` | pass |
| `prove-powersheds-grant.mjs` · `prove-superior-pergola-grant.mjs` | pass · pass |
| `prove-results-configurations.mjs` · `prove-price-configurations.py` | **19/19** · **28/28** |
| `prove-price-presentation-unchanged.mjs` | 619 products unmoved |
| `prove-landmarks.mjs` | **140/140** |

---

## 6 · PRESERVED (founder final actions 5, 6, 7)

- **No published image or caption changed.** No HTML file was modified.
- **The 39 unreferenced assets are retirement candidates, not deletions.**
  The founder's note said 37; it is now 39, and the two additions are
  measured, not estimated: of the nine newly-inventoried assets, seven are
  referenced from published pages and **two are not** —
  `404-hidden-discovery.png` and
  `atlas-visual-references/atlas-a-sketch-visual-authority.jpg`. No asset
  moved in the other direction. Nothing was deleted.
- **Supplier permissions untouched** — `image-rights-records.json` was not
  modified by this work.
- **The BIOBUILDS publication decision untouched** — `FX-BIOBUILDS-PUBLISH-20261011`,
  its six approved and two withheld assets, and
  `listing_review.state: AWAITING_CONFIRMATION` with `confirmed_at: null`
  all stand. Mateus is still not recorded as having confirmed anything.
- Atlas pricing, Results, Compare, the publication gates and Cluster 1 are
  byte-identical.

---

## 7 · STILL OPEN

**The first-party photograph taxonomy gap.** Nine of the 110 legacy assets
carry iOS EXIF — they are first-party photographs, and
`SUPPLIER_IMAGE` / `AI_ILLUSTRATION` / `NO_IMAGE` has no class for them.
None is published. One founder decision closes it; inventing a class was not
mine to do.
