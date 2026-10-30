#!/usr/bin/env python3
"""Apply the Release 3 hero AI declaration (PN-FDR-2026-10-30-R3HERO) once the founder has signed it.

    python3 atlas-tools/declare-r3-hero-provenance.py           # dry run: validates, writes nothing
    python3 atlas-tools/declare-r3-hero-provenance.py --write   # applies (only when signed)

Reads governance/R3-HERO-AI-DECLARATION-2026-10-30.json. Founder instruction, 30 Oct 2026: "Review the
embedded content credentials. Register verified AI-generated images accurately and display the existing AI
illustration label where required. Do not invent provenance for undeclared images."

What it does, and nothing more:
  * refuses unless the declaration is signed (signature.signed_by and signature.date);
  * for exactly three pictures whose own signed C2PA credentials state "Created by Google Generative AI"
    (9805382f, 31b49fb6 on The Hidden Bins; fec77c3f on The House as a Power Station): re-hashes each file,
    requires it to be the LEGACY_UNDECLARED entry of the same sha256, and moves it to `records` as an
    AI_ILLUSTRATION in the founder-attested form (prompt_status UNAVAILABLE, reference_disclosure
    UNCERTAIN, resemblance review, named human review = the signature), surfaces exactly ["discovery"];
  * adds the existing approved label ("AI-generated illustration", .pn-compare__ai) inside the two hero
    comparisons that show them, as on The Natural Swimming Garden.
No prompt or reference input is stated (none is known); nothing is inferred from appearance; every other
picture, including ce9da2e5 and the two Above and Beyond sources, is left exactly as it is.
validate-image-provenance.js then decides (pin FOUNDER_ATTESTED_R3HERO, P1-P14).
"""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "image-provenance-records.json")
DEC = os.path.join(ROOT, "governance", "R3-HERO-AI-DECLARATION-2026-10-30.json")
DECISION = "PN-FDR-2026-10-30-R3HERO"
ASSETS = {"assets/img/9805382f8164228a.jpg", "assets/img/31b49fb60732073b.jpg", "assets/img/fec77c3f0bae107a.jpg"}
LABEL = '      <p class="pn-compare__ai">AI-generated illustration</p>\n'
PAGES = {"discovery-hidden-bins.html": 'id="hbHeroCompare"', "discovery-house-as-power-station.html": 'id="psHeroCompare"'}
ANCHOR = '      <p class="pn-compare__tag is-possible" aria-hidden="true">Possible</p>\n'


def die(m): sys.exit("REFUSED: " + m)


def main():
    write = "--write" in sys.argv
    dec = json.load(open(DEC, encoding="utf-8"))
    if dec.get("decision") != DECISION: die("not %s" % DECISION)
    sig = dec.get("signature") or {}
    signed = bool(str(sig.get("signed_by") or "").strip() and str(sig.get("date") or "").strip())
    reg = json.load(open(REG, encoding="utf-8"))
    legacy = {e["asset"]: e for e in reg["legacy_undeclared"]}
    have = {r["asset"] for r in reg["records"]}
    rows = dec["records"]
    if {r["asset"] for r in rows} != ASSETS: die("the declaration must cover exactly the three credential-verified pictures")
    rr = dec["resemblance_review"]
    new = []
    for r in rows:
        a = r["asset"]
        data = open(os.path.join(ROOT, a), "rb").read()
        if hashlib.sha256(data).hexdigest() != r["sha256"] or len(data) != r["bytes"]: die("%s: bytes differ from the declaration" % a)
        if b"jumdc2pa" not in data: die("%s: no embedded credential" % a)
        if a in have: die("%s: already a record" % a)
        if a not in legacy or legacy[a]["sha256"] != r["sha256"]: die("%s: not the legacy entry of the same bytes" % a)
        new.append({
            "asset": a, "sha256": r["sha256"], "bytes": r["bytes"], "pixels": r["pixels"],
            "class": "AI_ILLUSTRATION", "what": r["what"],
            "depicts_named_product": False, "depicts_named_organisation": False,
            "generated": r["generated"],
            "prompt_status": "UNAVAILABLE",
            "reference_disclosure": {"status": "UNCERTAIN", "statement": r["reference_statement"] +
                                     " Content credentials do not record conversation context, so other inputs cannot be ruled out from the file.",
                                     "evidence": r["generated"]["c2pa_evidence"]},
            "resemblance_review": rr,
            "human_review": {"reviewer": sig.get("signed_by") or "", "date": sig.get("date") or "",
                             "attests": dec["signature"]["statement_to_sign"]},
            "permitted_surfaces": list(dec["surfaces"]),
            "decision_ref": DECISION + " (founder-attested form; credential-verified Google generations on the Release 3 hero sliders; discovery surface only)",
            "content_credentials": {"embeds_c2pa": True, "note": "The deployed file carries Google's signed C2PA credential (see generated.c2pa_evidence). Its WebP derivatives, where they exist, carry none."},
            "introduced": legacy[a].get("introduced"), "recovered_evidence": legacy[a].get("recovered_evidence"),
        })
    print("%d records validated for %s; signed: %s" % (len(new), DECISION, "yes (%s, %s)" % (sig["signed_by"], sig["date"]) if signed else "NO"))
    if not write: return
    if not signed: die("the declaration is not signed by the founder; nothing written")
    reg["legacy_undeclared"] = [e for e in reg["legacy_undeclared"] if e["asset"] not in ASSETS]
    reg["records"] = reg["records"] + new
    open(REG, "w", encoding="utf-8").write(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    for page, fid in PAGES.items():
        p = os.path.join(ROOT, page); t = open(p, encoding="utf-8").read()
        i = t.index(fid); j = t.index(ANCHOR, i)
        if 'class="pn-compare__ai"' in t[i:t.index("</figure>", i)]: continue
        t = t[:j + len(ANCHOR)] + LABEL + t[j + len(ANCHOR):]
        open(p, "w", encoding="utf-8").write(t)
    # Freeze record V8 (same-commit rule, GL12): the label is a hero change, so V8 is refreshed in place
    # (it is unreleased); the hash and size lines change and the label is recorded in its section 2.
    v8 = os.path.join(ROOT, "governance", "disc-026-house-as-power-station-FREEZE-RECORD-V8.md")
    art = open(os.path.join(ROOT, "discovery-house-as-power-station.html"), "rb").read()
    h = hashlib.sha256(art).hexdigest(); t = open(v8, encoding="utf-8").read()
    import re
    t = re.sub(r"\| \*\*SHA-256\*\* \| \*\*`[0-9a-f]{64}`\*\* \|", "| **SHA-256** | **`%s`** |" % h, t, count=1)
    t = re.sub(r"\| SHA-256 \(16\) \| `[0-9a-f]{16}` \|", "| SHA-256 (16) | `%s` |" % h[:16], t, count=1)
    t = re.sub(r"\| \*\*Byte size\*\* \| \*\*[0-9,]+ bytes\*\* \|", "| **Byte size** | **{:,} bytes** |".format(len(art)), t, count=1)
    note = "- **AI label** (declaration PN-FDR-2026-10-30-R3HERO, applied with the founder's signature): the approved 'AI-generated illustration' label inside the hero comparison, as on The Natural Swimming Garden.\n"
    if note not in t: t = t.replace("**Nothing else in the article changed.**", note + "\n**Nothing else in the article changed.**", 1)
    open(v8, "w", encoding="utf-8").write(t)
    print("written: register (+%d records, -%d legacy) and the label on %s" % (len(new), len(new), ", ".join(PAGES)))


if __name__ == "__main__":
    main()
