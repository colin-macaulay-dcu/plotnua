#!/usr/bin/env python3
"""Declare AI illustrations from their own verifiable metadata (Governance 2.0, Rule 2, 30 Oct 2026).

    python3 atlas-tools/declare-ai-from-metadata.py ASSET [ASSET ...]           dry run
    python3 atlas-tools/declare-ai-from-metadata.py --write ASSET [ASSET ...]   writes the register

For each asset (a LEGACY_UNDECLARED entry in image-provenance-records.json) this reads the file's own
embedded C2PA manifest (c2pa-python) and declares the picture an AI_ILLUSTRATION ONLY if the manifest
says so: a c2pa.created action with digital source type trainedAlgorithmicMedia. It records what the
credential says and nothing else:
  * tool and date from the signed manifest (issuer, claim generator, signing time);
  * prompt_status UNAVAILABLE (a credential never carries the prompt);
  * reference_disclosure: CREDENTIALED when every recorded input image carries its own credential,
    otherwise UNCERTAIN, with the ingredients described exactly (an unidentified input is said to be one);
  * permitted_surfaces from the pages that show the picture (discovery pages -> "discovery").
No founder signature is needed (Rule 2). A file without such a credential is refused: provenance is
never inferred from appearance or invented. validate-image-provenance.js re-checks the credential in the
bytes (P5) and that every page showing a declared picture carries the AI label (P8).
"""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "image-provenance-records.json")


def die(m): sys.exit("REFUSED: " + m)


def read_c2pa(path):
    import c2pa
    j = json.loads(c2pa.Reader(path).json())
    am = j["manifests"][j["active_manifest"]]
    acts = [a for x in am.get("assertions", []) if "actions" in x["label"] for a in x["data"]["actions"]]
    created = [a for a in acts if a.get("action") == "c2pa.created"]
    ai = any("trainedAlgorithmicMedia" in str(a.get("digitalSourceType", "")) for a in created)
    gen = am.get("claim_generator") or ", ".join(g.get("name", "") for g in am.get("claim_generator_info", []))
    sig = am.get("signature_info", {})
    ings = am.get("ingredients", [])
    linked = []
    for i in ings:
        m = i.get("active_manifest")
        if m and m in j["manifests"]:
            linked.append(m)
    return dict(ai=ai, created=[a.get("description") for a in created], issuer=sig.get("issuer"),
                time=sig.get("time"), generator=gen, ingredients=len(ings), credentialed=len(linked),
                validation=j.get("validation_state"))


def main():
    write = "--write" in sys.argv
    assets = [a for a in sys.argv[1:] if not a.startswith("--")]
    reg = json.load(open(REG, encoding="utf-8"))
    legacy = {e["asset"]: e for e in reg["legacy_undeclared"]}
    pages = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
    new = []
    for a in assets:
        if a not in legacy: die("%s is not a LEGACY_UNDECLARED entry" % a)
        p = os.path.join(ROOT, a); data = open(p, "rb").read()
        if hashlib.sha256(data).hexdigest() != legacy[a]["sha256"]: die("%s: bytes differ from the register" % a)
        if b"jumdc2pa" not in data: die("%s: no embedded content credential; nothing is declared" % a)
        c = read_c2pa(p)
        if not c["ai"]: die("%s: the credential does not record an AI generation" % a)
        shown = [f for f in pages if a in open(os.path.join(ROOT, f), encoding="utf-8").read()]
        if not shown or any(not f.startswith("discovery-") for f in shown):
            die("%s: shown on %s; this script declares discovery-page pictures only (label those pages first)" % (a, shown))
        if c["ingredients"] == 0:
            status, stmt = "UNCERTAIN", "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out."
        elif c["credentialed"] == c["ingredients"]:
            status, stmt = "CREDENTIALED", "The credential records %d input image(s), each carrying its own signed credential." % c["ingredients"]
        else:
            status, stmt = "UNCERTAIN", "The credential records %d input image(s), %d without any credential, title or hash: not identifiable from the file." % (c["ingredients"], c["ingredients"] - c["credentialed"])
        ev = "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s, generator %s; actions: %s; digital source type trainedAlgorithmicMedia; validation %s." % (
            c["issuer"], c["time"], c["generator"], "; ".join(x for x in c["created"] if x), c["validation"])
        old = legacy[a]
        new.append({
            "asset": a, "sha256": old["sha256"], "bytes": old["bytes"], "pixels": old["pixels"],
            "class": "AI_ILLUSTRATION",
            "what": "Discovery illustration (%s)" % ", ".join(shown),
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED", "evidence": ev, "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI, per the file's own signed C2PA credential" % (c["issuer"] or "unknown issuer"), "date": (c["time"] or "")[:10]},
            "prompt_status": "UNAVAILABLE",
            "reference_disclosure": {"status": status, "statement": stmt},
            "permitted_surfaces": ["discovery"],
            "content_credentials": {"embeds_c2pa": True},
            "introduced": old.get("introduced"), "recovered_evidence": old.get("recovered_evidence"),
        })
        print("%s: AI generation verified (%s, %s); references %s" % (a, c["issuer"], (c["time"] or "")[:10], status))
    if not write: return
    names = {r["asset"] for r in new}
    reg["legacy_undeclared"] = [e for e in reg["legacy_undeclared"] if e["asset"] not in names]
    reg["records"] = reg["records"] + new
    open(REG, "w", encoding="utf-8").write(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    print("written: %d records" % len(new))


if __name__ == "__main__":
    main()
