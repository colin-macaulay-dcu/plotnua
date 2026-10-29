"""PlotArt artist galleries · shared rules (Phase 1, 29 Oct 2026; founder decision PN-FDR-2026-10-29-PLOTART-STUDIO).

Two steps, kept apart on purpose:

  1. INGEST  (atlas-tools/plotart-gallery-ingest.py)
     A gallery EXPORT (what PlotArt Studio will hand over on Publish: gallery.json + the
     artist's ORIGINAL photographs) becomes a public gallery PACKAGE:
       * every photograph checked (format by signature, size, decode, resolution, pixels);
       * camera rotation applied, colour converted to sRGB, ALL metadata removed (GPS!);
       * never cropped or upscaled: the whole artwork is preserved;
       * WebP derivatives at 600 / 1200 / 2000 px on the long edge;
       * exact (SHA-256) and near (perceptual) duplicates detected across every gallery;
       * a provenance record per published image (class ARTIST_SUPPLIED_ARTWORK);
       * a check report: BLOCK (cannot publish) and WARN (founder judgement).
     Originals never enter a package. A package holds public fields only.

  2. BUILD   (atlas-tools/build-plotart.py --galleries DIR)
     Packages become the artist gallery page, one page per artwork and a Virtual Gallery card.
     A package is PUBLISHED only when every publication safeguard passes (publication_blocks()).
     --private-preview renders unapproved packages too, outside the repository, ribboned and
     noindex, nofollow, with the check report shown on the page.
"""
import hashlib, io, json, os, re

SCHEMA = "plotnua.plotart.gallery.v1"
PACKAGE_SCHEMA = "plotnua.plotart.gallery-package.v1"
LICENCE_VERSIONS = ("PA-GPIL-2026-10-29",)          # Gallery Publication and Image Licence, r4
SIZES = (600, 1200, 2000)
MIN_LONG_EDGE = 2000          # BLOCK below this (artworks)
MIN_PORTRAIT_EDGE = 800       # portraits are shown small (PlotArt Studio, Phase 2)
GOOD_LONG_EDGE = 3000         # WARN below this
MAX_BYTES = 30 * 1024 * 1024
MAX_PIXELS = 60_000_000
MAX_SIDE = 12000
MAX_RATIO = 4.0               # WARN beyond 4:1
FOUNDING_MIN_WORKS = 10       # founder decision 29 Oct 2026: a minimum, never a maximum
WEBP_QUALITY = 84
AVAILABILITY = ("available", "reserved", "sold", "not_for_sale", "archived")
SHOWN = ("available", "reserved", "sold", "not_for_sale")
AI = ("none", "assisted", "generated")
PHOTOGRAPHER = ("self", "other_with_permission")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,6}$")
MEDIA = ("painting", "drawing", "works_on_paper", "printmaking", "photography", "sculpture",
         "ceramics_craft", "textiles", "mixed_media", "digital_new_media", "other")

# The ONLY keys a gallery export may carry. Anything else (an email, a phone number, an address,
# an application reference, review notes ...) is refused: the repository is public.
ARTIST_KEYS = {"slug", "display_name", "founding", "practice", "medium", "county", "county_public",
               "statement", "bio", "website", "instagram", "portrait"}
WORK_KEYS = {"id", "slug", "title", "year", "medium", "materials", "h_cm", "w_cm", "d_cm", "price_eur",
             "price_on_request", "availability", "description", "order", "ai_involvement", "ai_note",
             "ai_founder_decision", "images"}
IMAGE_KEYS = {"file", "role", "alt", "photographer", "photo_credit"}
PUB_KEYS = {"state", "version", "approved_by", "approved_at", "licence_version", "licence_accepted_at",
            "permission_ref", "test_note"}
TOP_KEYS = {"schema", "artist", "works", "publication"}
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]")
_EIRCODE = re.compile(r"\b[ACDEFHKNPRTVWXY]\d[0-9W]\s?[0-9ACDEFHKNPRTVWXY]{4}\b")      # upper case only
_DIGITRUN = re.compile(r"\+?\d[\d \-().]{6,}\d")


class _PrivateHint:
    """Email address, Eircode, or a run holding 9+ digits (a phone number; '2019 - 2026' is 8)."""
    @staticmethod
    def search(s):
        return (_EMAIL.search(s) or _EIRCODE.search(s) or re.search(r"(?i)\beircode\b", s)
                or any(sum(ch.isdigit() for ch in m.group()) >= 9 for m in _DIGITRUN.finditer(s)))


PRIVATE_HINT = _PrivateHint()
COUNTIES = ("Antrim", "Armagh", "Carlow", "Cavan", "Clare", "Cork", "Derry", "Donegal", "Down", "Dublin",
            "Fermanagh", "Galway", "Kerry", "Kildare", "Kilkenny", "Laois", "Leitrim", "Limerick", "Longford",
            "Louth", "Mayo", "Meath", "Monaghan", "Offaly", "Roscommon", "Sligo", "Tipperary", "Tyrone",
            "Waterford", "Westmeath", "Wexford", "Wicklow")


class Refused(Exception):
    pass


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ export validation (always blocking)
def _text(v, lo, hi, what):
    if not isinstance(v, str) or not (lo <= len(v.strip()) <= hi):
        raise Refused("%s must be text of %d-%d characters" % (what, lo, hi))
    if "<" in v or ">" in v:
        raise Refused("%s must not contain markup" % what)
    if PRIVATE_HINT.search(v):
        raise Refused("%s looks as if it contains an email address, phone number or Eircode" % what)
    return v.strip()


def validate_export(g):
    """Structural and privacy checks. Raises Refused: these never depend on founder judgement."""
    if not isinstance(g, dict) or g.get("schema") != SCHEMA:
        raise Refused("not a %s export" % SCHEMA)
    for k in g:
        if k not in TOP_KEYS:
            raise Refused("unexpected field %r (exports carry public fields only)" % k)
    a = g.get("artist") or {}
    for k in a:
        if k not in ARTIST_KEYS:
            raise Refused("unexpected artist field %r (exports carry public fields only)" % k)
    if not SLUG.match(a.get("slug", "")):
        raise Refused("artist slug must be lower-case words joined by hyphens")
    _text(a.get("display_name"), 2, 80, "artist name")
    _text(a.get("bio"), 40, 2400, "biography")
    if a.get("statement") is not None:
        _text(a["statement"], 10, 400, "statement")
    if a.get("practice") is not None:
        _text(a["practice"], 2, 60, "practice")
    if a.get("medium") not in MEDIA:
        raise Refused("artist medium must be one of the application's media")
    if a.get("county") is not None and a["county"] not in COUNTIES:
        raise Refused("county must be one of the 32 counties")
    if not isinstance(a.get("founding"), bool) or not isinstance(a.get("county_public"), bool):
        raise Refused("founding and county_public must be true or false")
    for k in ("website",):
        if a.get(k) is not None and not re.match(r"^https://[^\s<>\"']{4,200}$", a[k]):
            raise Refused("website must be an https link")
    if a.get("instagram") is not None and not re.match(r"^[A-Za-z0-9._]{1,30}$", a["instagram"]):
        raise Refused("instagram must be a handle without @")
    if a.get("portrait") is not None:
        _image_entry(a["portrait"], "portrait")
    works = g.get("works")
    if not isinstance(works, list) or not works:
        raise Refused("a gallery needs at least one artwork")
    ids, slugs = set(), set()
    for w in works:
        for k in w:
            if k not in WORK_KEYS:
                raise Refused("unexpected artwork field %r" % k)
        if not re.match(r"^w[0-9a-z]{2,24}$", str(w.get("id", ""))) or w["id"] in ids:
            raise Refused("artwork ids must be unique (w + letters/digits)")
        if not SLUG.match(w.get("slug", "")) or w["slug"] in slugs or w["slug"] == "index":
            raise Refused("artwork slugs must be unique lower-case words joined by hyphens")
        ids.add(w["id"]); slugs.add(w["slug"])
        _text(w.get("title"), 1, 120, "artwork title")
        _text(w.get("medium"), 2, 120, "artwork medium")
        if w.get("materials") is not None:
            _text(w["materials"], 2, 160, "materials")
        if w.get("description") is not None:
            _text(w["description"], 10, 1200, "artwork description")
        for d in ("h_cm", "w_cm"):
            if not isinstance(w.get(d), (int, float)) or not (1 <= w[d] <= 2000):
                raise Refused("%s %s must be 1-2000 cm" % (w["slug"], d))
        if w.get("d_cm") is not None and not (isinstance(w["d_cm"], (int, float)) and 0.1 <= w["d_cm"] <= 2000):
            raise Refused("%s depth must be 0.1-2000 cm" % w["slug"])
        if w.get("year") is not None and not (isinstance(w["year"], int) and 1900 <= w["year"] <= 2100):
            raise Refused("%s year must be a four-digit year" % w["slug"])
        if w.get("availability") not in AVAILABILITY:
            raise Refused("%s availability must be one of %s" % (w["slug"], ", ".join(AVAILABILITY)))
        p = w.get("price_eur")
        if p is not None and not (isinstance(p, int) and 1 <= p <= 1_000_000):
            raise Refused("%s price must be whole euros, 1-1,000,000" % w["slug"])
        if w.get("ai_involvement") not in AI:
            raise Refused("%s needs an AI declaration (none, assisted or generated)" % w["slug"])
        if w["ai_involvement"] != "none":
            _text(w.get("ai_note"), 10, 400, "%s AI disclosure" % w["slug"])
        if w.get("ai_founder_decision") not in (None, "approved", "declined"):
            raise Refused("%s ai_founder_decision must be approved or declined" % w["slug"])
        imgs = w.get("images")
        if not isinstance(imgs, list) or not imgs:
            raise Refused("%s needs at least one image" % w["slug"])
        if sum(1 for i in imgs if i.get("role") == "main") != 1:
            raise Refused("%s needs exactly one main image" % w["slug"])
        for i in imgs:
            _image_entry(i, w["slug"])
    pub = g.get("publication") or {}
    for k in pub:
        if k not in PUB_KEYS:
            raise Refused("unexpected publication field %r" % k)
    if pub.get("state") not in ("private_preview", "approved"):
        raise Refused("publication state must be private_preview or approved")
    return g


def _image_entry(i, where):
    for k in i:
        if k not in IMAGE_KEYS:
            raise Refused("unexpected image field %r (%s)" % (k, where))
    f = i.get("file", "")
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$", f) or ".." in f:
        raise Refused("image file names must be plain names inside the export (%s)" % where)
    if i.get("role") not in ("main", "view", "detail", "portrait"):
        raise Refused("image role must be main, view, detail or portrait (%s)" % where)
    _text(i.get("alt"), 5, 300, "image description (alt text, %s)" % where)
    if i.get("photographer") not in PHOTOGRAPHER:
        raise Refused("who took the photograph must be declared (%s)" % where)
    if i["photographer"] == "other_with_permission":
        _text(i.get("photo_credit"), 2, 80, "photo credit (%s)" % where)


# ------------------------------------------------------------------ image processing
def _dhash(im, n=8):
    g = im.convert("L").resize((n + 1, n))
    px = list(g.getdata())
    bits = 0
    for r in range(n):
        for c in range(n):
            bits = (bits << 1) | (px[r * (n + 1) + c] > px[r * (n + 1) + c + 1])
    return "%016x" % bits


def hamming(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def process_image(src_path, out_dir, stem, min_long_edge=MIN_LONG_EDGE):
    """Check one original and write its derivatives. Returns (record, blocks, warns)."""
    from PIL import Image, ImageCms, ImageOps
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS          # decompression-bomb guard
    blocks, warns = [], []
    raw = open(src_path, "rb").read()
    n = len(raw)
    sig = ("jpeg" if raw[:3] == b"\xff\xd8\xff" else "png" if raw[:8] == b"\x89PNG\r\n\x1a\n"
           else "webp" if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP" else None)
    rec = {"source_sha256": sha256_bytes(raw), "source_bytes": n, "source_format": sig}
    if sig is None:
        return rec, ["not a JPEG, PNG or WebP file (checked by its content, not its name)"], warns
    if n > MAX_BYTES:
        return rec, ["file is %.1f MB; the limit is 30 MB" % (n / 1048576)], warns
    try:
        im = Image.open(io.BytesIO(raw))
        w0, h0 = im.size
        if w0 * h0 > MAX_PIXELS or max(w0, h0) > MAX_SIDE:
            return rec, ["image is %d x %d px; the limit is 60 megapixels and 12,000 px a side" % (w0, h0)], warns
        im.load()                                   # full decode: truncated or corrupt files fail here
    except Exception as e:                          # noqa: BLE001 - any decoder failure is a refusal
        return rec, ["the file could not be read as an image (%s)" % type(e).__name__], warns
    exif_orient = im.getexif().get(274, 1)
    icc = im.info.get("icc_profile")
    im = ImageOps.exif_transpose(im)               # camera rotation applied, never guessed
    colour = "sRGB (no embedded profile; treated as sRGB)"
    if icc and im.mode in ("RGB", "RGBA", "CMYK", "L"):
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            name = ImageCms.getProfileDescription(src).strip()
            if im.mode == "RGBA":
                im = im.convert("RGB")
            # Every embedded profile is converted (Display P3, Adobe RGB, CMYK ...); converting an sRGB-equivalent
            # profile is a no-op in effect, and the published file then carries no profile at all.
            im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), renderingIntent=0, outputMode="RGB")
            colour = "converted to sRGB from the embedded profile (%s)" % name
        except Exception:                           # noqa: BLE001
            warns.append("the embedded colour profile could not be read; colours were kept as they are")
            colour = "embedded profile unreadable; kept as-is"
    elif icc:
        warns.append("an unusual image mode (%s); colours converted without its profile" % im.mode)
    if im.mode in ("P", "LA", "PA", "RGBA"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (36, 34, 31))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    long_edge = max(w, h)
    rec.update({"pixels": [w, h], "exif_orientation": exif_orient, "colour": colour, "dhash": _dhash(im)})
    if long_edge < min_long_edge:
        blocks.append("the photograph is %d px on its long edge; at least %d px is needed" % (long_edge, min_long_edge))
    elif min_long_edge == MIN_LONG_EDGE and long_edge < GOOD_LONG_EDGE:
        warns.append("%d px on the long edge: acceptable, but %d px or more looks better on large screens" % (long_edge, GOOD_LONG_EDGE))
    ratio = max(w, h) / min(w, h)
    if ratio > MAX_RATIO:
        warns.append("a very long format (%.1f:1); check it reads well as a thumbnail" % ratio)
    if n / (w0 * h0) < 0.06 and sig == "jpeg":
        warns.append("strong JPEG compression; a less-compressed export would look better")
    outs = []
    os.makedirs(out_dir, exist_ok=True)
    for s in SIZES:
        target = min(s, long_edge)                  # never upscaled
        if outs and target == outs[-1]["long_edge"]:
            continue
        k = target / long_edge
        dim = (max(1, round(w * k)), max(1, round(h * k)))
        d = im if dim == (w, h) else im.resize(dim, Image.LANCZOS)
        buf = io.BytesIO()
        d.save(buf, "WEBP", quality=WEBP_QUALITY, method=6)   # no exif=, no icc_profile=: nothing carried over
        b = buf.getvalue()
        name = "%s-%d.webp" % (stem, target)
        open(os.path.join(out_dir, name), "wb").write(b)
        outs.append({"file": name, "long_edge": target, "pixels": list(dim), "sha256": sha256_bytes(b), "bytes": len(b)})
    rec["derivatives"] = outs
    rec["aspect"] = round(w / h, 5)
    return rec, blocks, warns


# ------------------------------------------------------------------ publication safeguards
def publication_blocks(pkg):
    """Everything that stops a package being PUBLISHED. Empty list = publishable."""
    out = list(pkg.get("checks", {}).get("blocks", []))
    pub = pkg.get("publication", {})
    a = pkg["artist"]
    if pub.get("state") != "approved":
        out.append("not approved for publication by the founder (state: %s)" % pub.get("state"))
    else:
        for k in ("version", "approved_by", "approved_at", "permission_ref"):
            if not pub.get(k):
                out.append("publication record is missing %s" % k)
        if pub.get("approved_by") not in (None, "founder"):
            out.append("only the founder can approve publication")
    if pub.get("licence_version") not in LICENCE_VERSIONS or not pub.get("licence_accepted_at"):
        out.append("the artist has not accepted the current Gallery Publication and Image Licence")
    shown = [w for w in pkg["works"] if w["availability"] in SHOWN]
    if not shown:
        out.append("no artworks to show")
    # The Founding minimum is enforced when the gallery FIRST opens (v1, or an unversioned preview). Afterwards a sale or
    # removal must never be blocked: the artist is asked to top up within 30 days (Founding Artist Agreement 3.3(c)).
    if a.get("founding") and len(shown) < FOUNDING_MIN_WORKS and pub.get("version") in (None, "v1"):
        out.append("Founding Artist galleries show at least %d artworks; this one has %d" % (FOUNDING_MIN_WORKS, len(shown)))
    for w in pkg["works"]:
        if w["ai_involvement"] == "generated" and w.get("ai_founder_decision") != "approved":
            out.append("%s: entirely prompt-generated work needs the founder's eligibility decision" % w["slug"])
    return out
