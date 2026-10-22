#!/usr/bin/env python3
"""
POSSIBILITY REVEAL · GARDEN LAYER TILES (H3, 20 Oct 2026)
===========================================================================
Makes the lazily loaded overlay tiles that let the homepage Reveal switch the
locked garden layers on and off, one by one, over the unchanged live picture
(L1 + L2A), and records exactly how.

  python3 atlas-tools/build-possibility-reveal-layers.py --check
        verify every tile against the record (CI; no images needed)
  python3 atlas-tools/build-possibility-reveal-layers.py --build --locks LOCKREPO \
        --base L1-plus-L2A.png --l4 L4-layer-RGBA.png --l6-solo L6-solo-without-L3-RGBA.png
        build from the authoritative lock chain (and --check --locks ... re-builds
        in memory and proves the committed tiles are reproducible)

THE LOCK CHAIN IS THE SOURCE. Every input is identified by hash and refused if
it differs:
  base     L1 + L2A (pixels 5dd29abe...), the picture the live site already paints
  L3       the active L3 layer (ACTIVE-LOCKS active_layers.L3; H5C4 since 22 Oct 2026;
           every superseded L3 -- v2, v2.1c -- is refused by hash)
  L4       L4 layer        (L4 lock manifest)
  L5       L5 layer        (ACTIVE-LOCKS active_layers.L5)
  L6       L6 layer        (ACTIVE-LOCKS active_layers.L6)
Before anything is written, base + L3 + L4 + L5 + L6 must rebuild the ACTIVE
MASTER pixel-for-pixel (26fb6507...a0f01). A tile set that cannot reproduce
the approved image is not built.

INDEPENDENCE. L3, L4 and L5 share no pixel, so each is exact on its own. L6
shares 13,383 pixels with L3: the chimney (opaque, identical either way) and
the approved smoke drifting over the pavilion. With the pavilion switched off,
that smoke must lie over the garden, not over a ghost of the pavilion. So L6 is
one SPRITE with two states, stacked vertically in one file:
  top     the locked L6 layer exactly as approved (shown with L3 on)
  bottom  the same L6 with the approved smoke step re-run, with identical
          settings, over the L1 + L2A garden where the pavilion would be
          (--l6-solo; shown with L3 off). Outside those pixels it is
          identical to the locked layer, and the smoke matte is identical.

WHAT A TILE IS. The layer's own pixels, cropped to its bounding box (even
coordinates, so the half-size tile maps exactly), binary alpha, encoded as WebP
(lossy colour, lossless alpha) at full size and half size. No editing.
"""
import hashlib, io, json, pathlib, sys
try:
    import numpy as np
    from PIL import Image, __version__ as PIL_VERSION, features
except ImportError:  # pragma: no cover
    np = Image = features = None; PIL_VERSION = "n/a"

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/possibility-reveal/layers"
RECORD = OUT / "layers.json"
REG = ROOT / "image-provenance-records.json"
W, H = 2752, 1536
WEBP = {"quality": 90, "method": 6, "alpha_quality": 100, "exact": False}

BASE_PIXEL_SHA = "5dd29abea1a7cd9aba4f0b1db05a562a46d555f888a922f721a44e03ec0988a0"
L4_SHA = "e421c1c3c8c2741c5a2a0c806d4f39f806bcd729b6cb17ac60daf4fe14c50d28"

LAYERS = [   # id, file stem, what it is
    ("L3", "garden-L3-pavilion", "L3 H5C4 · a generic mirrored garden pavilion at 85 %, moved towards the house (Grow a garden room)"),
    ("L4", "garden-L4-kitchen-garden", "L4 · a generic kitchen garden (Borrow a garden)"),
    ("L5", "garden-L5-pod", "L5 · a generic elevated timber pod (Hold a treehouse)"),
    ("L6", "garden-L6-retreat", "L6 H5C4-S · garden retreat: the TimberIN hot tub with its smoke and the TimberIN Nordic Cube sauna, charcoal terrace with a cold plunge, stepping stones, planting, Japanese maple and garden lights (Become a retreat); two-state sprite"),
]

def die(m):
    print("REFUSED: " + m + " -- nothing written"); sys.exit(1)
def sha(b): return hashlib.sha256(b).hexdigest()
def fsha(p): return sha(pathlib.Path(p).read_bytes())
def psha(a): return sha(np.ascontiguousarray(a).tobytes())
def arg(n):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None

def chain():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    c = reg.get("possibility_reveal_lock_chain")
    if not c: die("the provenance register carries no possibility_reveal_lock_chain")
    return c

def superseded_l3(c):
    return {k: v["sha256"] for k, v in (c.get("superseded") or {}).items()
            if k.startswith("L3_v") and isinstance(v, dict) and len(str(v.get("sha256", ""))) == 64}
def l3_problems(c):
    act = c["active_layers"]["L3"]; sup = superseded_l3(c); out = []
    if not act.get("version") or len(str(act.get("sha256", ""))) != 64: out.append("the chain does not name the active L3 by version and hash")
    if "L3_v2" not in sup: out.append("the superseded L3 v2 is not recorded")
    if act.get("sha256") in sup.values(): out.append("a superseded L3 is the active L3")
    if not any(v.get("replaced_by") == act.get("version") for k, v in c["superseded"].items() if k in sup): out.append("no superseded L3 records replaced_by " + str(act.get("version")))
    steps = c.get("chain") or []
    if not any(s.get("layer_sha256") == act.get("sha256") for s in steps): out.append("the chain does not apply the active L3")
    if any(s.get("layer_sha256") in sup.values() for s in steps): out.append("the chain applies a superseded L3")
    return out
def step_path(c, sha_):
    for s in c.get("chain") or []:
        if s.get("layer_sha256") == sha_: return s["layer"]
    die("the chain has no step applying layer " + sha_[:12])

def build():
    """Returns {filename: bytes} and the record, built from the lock chain."""
    if np is None: die("Pillow and NumPy are needed to build")
    c = chain()
    locks = pathlib.Path(arg("--locks") or die("--locks LOCKREPO is required"))
    act = c["active_layers"]
    src = {
        "L3": locks / step_path(c, act["L3"]["sha256"]),
        "L5": locks / "l5lock/layer/L5-layer-RGBA.png",
        "L6": locks / step_path(c, act["L6"]["sha256"]),
        "L4": pathlib.Path(arg("--l4") or die("--l4 L4-layer-RGBA.png is required")),
    }
    want = {"L3": act["L3"]["sha256"], "L5": act["L5"]["sha256"], "L6": act["L6"]["sha256"], "L4": L4_SHA}
    bad3 = l3_problems(c)
    if bad3: die("; ".join(bad3))
    L6_SOLO_SHA = (c.get("l6_solo_without_L3") or {}).get("sha256") or die("the chain records no L6 solo (without L3) variant")
    for k, p in src.items():
        if not p.exists(): die("missing input " + str(p))
        if fsha(p) != want[k]: die(k + " layer " + str(p) + " is not the locked file (hash differs)")
    base = np.asarray(Image.open(arg("--base") or die("--base is required")).convert("RGB"))
    if psha(base) != BASE_PIXEL_SHA: die("--base is not the locked L1 + L2A picture")
    lay = {k: np.asarray(Image.open(p).convert("RGBA")) for k, p in src.items()}
    solo_p = pathlib.Path(arg("--l6-solo") or die("--l6-solo is required"))
    if fsha(solo_p) != L6_SOLO_SHA: die("--l6-solo is not the recorded L6-without-L3 derivation")
    solo = np.asarray(Image.open(solo_p).convert("RGBA"))

    m = {k: v[..., 3] > 0 for k, v in lay.items()}
    for k, v in lay.items():
        if set(np.unique(v[..., 3])) - {0, 255}: die(k + " alpha is not binary")
    for a, b in (("L3", "L4"), ("L3", "L5"), ("L4", "L5"), ("L4", "L6"), ("L5", "L6")):
        if (m[a] & m[b]).any(): die(a + " and " + b + " overlap; they would not be independent")
    full = base.copy()
    for k in ("L3", "L4", "L5", "L6"):
        full[m[k]] = lay[k][..., :3][m[k]]
    if psha(full) != c["active_master"]["pixel_sha256"]:
        die("base + L3 + L4 + L5 + L6 does not rebuild the active master")
    ov = m["L3"] & m["L6"]
    ms = solo[..., 3] > 0
    if not (m["L6"] <= ms).all() or (ms & ~m["L6"] & ~m["L3"]).any():
        die("the L6 solo variant reaches beyond L6 and the pavilion")
    if ((solo[..., :3] != lay["L6"][..., :3]).any(2) & m["L6"] & ~m["L3"]).any():
        die("the L6 solo variant differs from the locked L6 outside the pavilion")

    files, rec = {}, {}
    def bbox(mask):
        ys, xs = np.nonzero(mask)
        x0, y0 = int(xs.min()) & ~1, int(ys.min()) & ~1
        x1, y1 = min(W, (int(xs.max()) + 2) & ~1), min(H, (int(ys.max()) + 2) & ~1)
        return x0, y0, x1, y1
    def enc(rgba, name):
        im = Image.fromarray(rgba, "RGBA")
        b = io.BytesIO(); im.save(b, "WEBP", **WEBP); full_b = b.getvalue()
        half = im.convert("RGBa").resize((im.width // 2, im.height // 2), Image.LANCZOS).convert("RGBA")
        hb = io.BytesIO(); half.save(hb, "WEBP", **WEBP)
        files[name + ".webp"] = full_b
        files[name + "-half.webp"] = hb.getvalue()
        return full_b, hb.getvalue(), half.size
    for k, stem, what in LAYERS:
        if k != "L6":
            x0, y0, x1, y1 = bbox(m[k])
            t = lay[k][y0:y1, x0:x1].copy()
            fb, hb, hs = enc(t, stem)
            states = {"on": {"y_offset": 0}}
            exp = [(t, (x0, y0))]
        else:
            x0, y0, x1, y1 = bbox(m["L6"] | ms)
            a = lay["L6"][y0:y1, x0:x1]; b = solo[y0:y1, x0:x1]
            t = np.concatenate([a, b], 0)
            fb, hb, hs = enc(t, stem)
            states = {"with_L3": {"y_offset": 0}, "without_L3": {"y_offset": y1 - y0}}
            exp = [(a, (x0, y0)), (b, (x0, y0))]
        # fidelity: decode the full tile, paste on the exact base, compare with the exact layer pixels
        dec = np.asarray(Image.open(io.BytesIO(fb)).convert("RGBA")).astype(np.int16)
        tt = t.astype(np.int16)
        alpha_exact = bool((dec[..., 3] == tt[..., 3]).all())
        sel = tt[..., 3] > 0
        err = np.abs(dec[..., :3] - tt[..., :3])[sel]
        rec[k] = {
            "what": what,
            "files": {stem + ".webp": {"sha256": sha(fb), "bytes": len(fb), "pixels": [t.shape[1], t.shape[0]]},
                      stem + "-half.webp": {"sha256": sha(hb), "bytes": len(hb), "pixels": list(hs)}},
            "bbox_2752": [x0, y0, x1 - x0, y1 - y0],
            "states": states,
            "layer_px": int(m[k].sum()),
            "fidelity": {"alpha_lossless": alpha_exact, "mean_abs_error": round(float(err.mean()), 3),
                         "p99_abs_error": int(np.percentile(err, 99)), "max_abs_error": int(err.max())},
        }
    rec["L6"]["overlap_with_L3_px"] = int(ov.sum())
    rec["L6"]["solo_variant_extra_px"] = int((ms & ~m["L6"]).sum())
    record = {
        "schema": "plotnua.possibility-reveal.layers.v1",
        "what_this_is": "How the Reveal's lazily loaded garden-layer tiles were made from the authoritative lock chain. Not a provenance declaration and not a permission: see image-provenance-records.json and image-adaptation-licences.json.",
        "lock_chain": {"active_master_pixel_sha256": c["active_master"]["pixel_sha256"],
                       "L3": {"version": act["L3"]["version"], "sha256": want["L3"]}, "L4": {"sha256": L4_SHA},
                       "L5": {"sha256": want["L5"]}, "L6": {"sha256": want["L6"]},
                       "base_pixel_sha256": BASE_PIXEL_SHA, "rebuilds_active_master": True},
        "l6_solo_variant": {"sha256": L6_SOLO_SHA, "method": c["l6_solo_without_L3"]["method"]},
        "encoder": {"pillow": PIL_VERSION, "libwebp": features.version("webp"), "webp": WEBP,
                    "half": "premultiplied (RGBa) Lanczos to half size"},
        "layers": rec,
    }
    return files, record

def main():
    if "--check" in sys.argv and "--locks" not in sys.argv:
        rec = json.loads(RECORD.read_text(encoding="utf-8"))
        bad = []
        names = set()
        for k, v in rec["layers"].items():
            for f, d in v["files"].items():
                names.add(f)
                p = OUT / f
                if not p.exists(): bad.append(f + " missing"); continue
                if fsha(p) != d["sha256"]: bad.append(f + " differs from its record")
        extra = {p.name for p in OUT.glob("*.webp")} - names
        if extra: bad.append("unrecorded tiles: " + ", ".join(sorted(extra)))
        c = chain()
        lc = rec["lock_chain"]
        if lc["active_master_pixel_sha256"] != c["active_master"]["pixel_sha256"]: bad.append("tiles were not built from the active master")
        bad += l3_problems(c)
        if lc["L3"]["sha256"] != c["active_layers"]["L3"]["sha256"] or lc["L3"].get("version") != c["active_layers"]["L3"]["version"]: bad.append("tiles were not built from the active L3")
        if lc["L3"]["sha256"] in superseded_l3(c).values(): bad.append("tiles were built from a superseded L3")
        for k in ("L5", "L6"):
            if lc[k]["sha256"] != c["active_layers"][k]["sha256"]: bad.append(k + " tiles are not from the active " + k)
        if bad: die("CHECK: " + "; ".join(bad[:8]))
        print("POSSIBILITY REVEAL LAYERS · CHECK OK — %d tiles match their record, built from the active lock chain (L3 %s)" % (len(names), c["active_layers"]["L3"]["version"]))
        return
    files, record = build()
    if "--check" in sys.argv:
        rec = json.loads(RECORD.read_text(encoding="utf-8"))
        bad = [f for f, b in files.items() if not (OUT / f).exists() or fsha(OUT / f) != sha(b)]
        if json.dumps(rec, sort_keys=True) != json.dumps(record, sort_keys=True): bad.append("layers.json differs from a fresh build")
        if bad: die("CHECK (rebuild): " + "; ".join(bad))
        print("POSSIBILITY REVEAL LAYERS · REBUILD OK — every tile is reproduced byte-for-byte from the lock chain")
        return
    if "--build" not in sys.argv: die("pass --check, or --build with the lock inputs")
    OUT.mkdir(parents=True, exist_ok=True)
    for f, b in files.items(): (OUT / f).write_bytes(b)
    RECORD.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    for k, v in record["layers"].items():
        print(k, {f: d["bytes"] for f, d in v["files"].items()}, v["bbox_2752"], v["fidelity"])
    print("wrote", len(files), "tiles and", RECORD.relative_to(ROOT))

if __name__ == "__main__":
    main()
