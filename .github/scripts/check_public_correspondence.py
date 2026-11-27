#!/usr/bin/env python3
"""PUBLIC-CORRESPONDENCE GUARD (M8C Stage 2 refresh, 27 Nov 2026).

This repository is public. Supplier correspondence and personal contact details never belong in it: they are held in
Atlas (Image Permission Outreach), the Supplier CRM and the private repository plotnua-infrastructure
(confidential-records/), and the public records cite them only by an evidence reference (PN-EVID-RIGHTS-...).

Every tracked text file is checked for:
  C1  a mail or message identifier (a Gmail message/thread id, a link into a mailbox or a private message thread);
  C2  a personal webmail address (gmail.com, outlook.com, icloud.com and the like), anywhere, including tests:
      test fixtures use reserved domains (example.com, *.test, *.invalid);
  C3  any other email address that is not PlotNua's own, not on a reserved test domain and not reviewed in
      governance/public-contact-allowlist.json. The allowlist holds the legitimate PUBLIC business contacts a
      supplier publishes or asked PlotNua to publish (for example a listing's own enquiry address); a new address
      fails until someone adds it there with where it is published and why.
The governed supplier records (rights records and manifest, provenance records, supplier showcases, supplied-image
registers, Atlas snapshots and proposed Atlas updates, public-information listings) are also checked for:
  C4  a mailbox reference ("Gmail"), a quotation attributed to an email/message/reply, or a "recorded/quoted
      verbatim" marker: correspondence is summarised neutrally and cites its evidence reference instead;
and the rights records themselves for:
  C5  the correspondence policy, and a boolean permission.pre_live_review_requested on every record that carries a
      structured permission, so the
      supplier's request to review a listing survives the removal of the wording that asked for it.

Usage: check_public_correspondence.py [ROOT]   (default: the repository containing this script)
Exit 0 clean, 1 findings. Legitimate public supplier information (websites, published business contacts on the
allowlist, the supplier's own published words quoted from its website) is not affected.
"""
import json
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
ALLOWLIST = "governance/public-contact-allowlist.json"
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf", ".zip", ".woff", ".woff2", ".ttf", ".otf",
               ".mp4", ".webm", ".mov", ".glb", ".avif", ".heic")
SKIP_FILES = {"package-lock.json"}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
MAIL_ID = re.compile(r"(?i)\b(?:gmail|mail|message|msg|thread)\b(?:\s+(?:id|message|thread))?\s*[:#=]?\s*\(?\s*1[0-9a-f]{15}\b")
MAILBOX_LINK = re.compile(r"(?i)mail\.google\.com/mail|instagram\.com/direct/t/|outlook\.(?:live|office)\.com/mail/")
WEBMAIL = re.compile(r"(?i)^(?:gmail\.com|googlemail\.com|hotmail\.[a-z.]+|outlook\.[a-z.]+|live\.[a-z.]+|msn\.com|"
                     r"yahoo\.[a-z.]+|ymail\.com|icloud\.com|me\.com|mac\.com|aol\.com|eircom\.net|proton\.me|"
                     r"protonmail\.com|gmx\.[a-z.]+|mail\.com)$")
OWN = re.compile(r"(?i)(?:^|\.)(?:plotnua\.ie|plotart\.ie)$")
RESERVED = re.compile(r"(?i)(?:^|\.)(?:test|invalid|example|localhost)$|^example\.(?:com|org|net|ie|co\.uk)$|"
                      r"(?:^|\.)example\.(?:com|org|net|ie|co\.uk|test|invalid)$|^users\.noreply\.github\.com$")

GOVERNED = ["image-rights-records.json", "image-rights-manifest.json", "image-provenance-records.json",
            "supplier-preview-system/showcases/*/*.json", "*/image-copies.json", "atlas-tools/targeted-updates/*.json",
            "atlas-tools/targeted-updates/*/*.json", "atlas-tools/proposed-atlas-updates/*.json",
            "atlas-tools/public-information-listings.json", "atlas-tools/maker-product-notes.json"]
GOV_MAILBOX = re.compile(r"(?i)\bgmail\b")
GOV_VERBATIM = re.compile(r"(?i)\b(?:recorded|quoted)\s+verbatim\b|\bverbatim\s+from\s+the\s+supplier'?s?\s+(?:e-?mail|message|reply)")
GOV_ATTRIBUTED = re.compile(r"[\"“][^\"“”]{20,}[\"”]\s*\([^()]{0,80}\b(?:e-?mail|message|reply|replied|WhatsApp|DM)\b",
                            re.I)


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def load_allowlist():
    p = ROOT / ALLOWLIST
    data = json.loads(p.read_text(encoding="utf-8"))
    allowed = {}
    for e in data["contacts"]:
        for k in ("address", "kind", "published_on", "reason"):
            if not e.get(k):
                raise SystemExit(f"{ALLOWLIST}: entry {e!r} is missing '{k}'")
        if e["kind"] not in ("public-business-contact", "test-fixture", "service-identity"):
            raise SystemExit(f"{ALLOWLIST}: unknown kind {e['kind']!r}")
        dom = e["address"].rsplit("@", 1)[-1]
        if WEBMAIL.match(dom):
            raise SystemExit(f"{ALLOWLIST}: a personal webmail address can never be allowlisted ({e['address']})")
        allowed[e["address"].lower()] = e
    return allowed


def json_strings(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from json_strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from json_strings(v)
    elif isinstance(x, str):
        yield x


def main():
    allowed = load_allowlist()
    findings, used = [], set()
    files = tracked()
    for rel in files:
        if rel in SKIP_FILES or rel == ALLOWLIST or rel.lower().endswith(SKIP_SUFFIX):
            continue          # the allowlist is validated by load_allowlist(), not scanned as a use of itself
        path = ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if MAIL_ID.search(line) or MAILBOX_LINK.search(line):
                findings.append(f"{rel}:{n}: C1 a mail/message identifier or a link into a mailbox")
            for m in EMAIL.finditer(line):
                addr = m.group(0)
                dom = addr.rsplit("@", 1)[1]
                if WEBMAIL.match(dom):
                    findings.append(f"{rel}:{n}: C2 a personal webmail address ({addr.split('@')[0][:2]}…@{dom})")
                elif OWN.search(dom) or RESERVED.search(dom):
                    continue
                elif addr.lower() in allowed:
                    used.add(addr.lower())
                else:
                    findings.append(f"{rel}:{n}: C3 an email address not on {ALLOWLIST} ({addr})")
        if any(fnmatch(rel, g) for g in GOVERNED):
            try:
                strings = list(json_strings(json.loads(text)))
            except ValueError:
                strings = [text]
            for s in strings:
                for code, rx, what in (("C4", GOV_MAILBOX, "a mailbox reference"),
                                       ("C4", GOV_VERBATIM, "a verbatim-correspondence marker"),
                                       ("C4", GOV_ATTRIBUTED, "a quotation attributed to correspondence")):
                    m = rx.search(s)
                    if m:
                        findings.append(f"{rel}: {code} {what}: …{s[max(0, m.start() - 40):m.end() + 20]}…")
    # C5 - the rights records carry the policy and the structured review flag.
    rec = json.loads((ROOT / "image-rights-records.json").read_text(encoding="utf-8"))
    if "PUBLIC REPOSITORY" not in str(rec.get("correspondence_policy", "")):
        findings.append("image-rights-records.json: C5 correspondence_policy is missing")
    for r in rec.get("records", []):
        p = r.get("permission")
        if p is None:          # earlier schema (permission_outcome only): no structured grant to flag
            continue
        if not isinstance(p, dict) or not isinstance(p.get("pre_live_review_requested"), bool):
            findings.append(f"image-rights-records.json: C5 {r.get('organisation_name')}: "
                            "permission.pre_live_review_requested must be true or false")
    stale = sorted(set(allowed) - used)
    for a in stale:
        findings.append(f"{ALLOWLIST}: allowlisted address no longer appears in any tracked file ({a}); remove it")
    if findings:
        for f in findings:
            print("FAIL", f)
        print(f"PUBLIC CORRESPONDENCE GUARD · {len(findings)} finding(s). Correspondence and personal contact "
              "details stay in the private records; cite the evidence reference instead.")
        return 1
    print(f"PUBLIC CORRESPONDENCE GUARD · OK · {len(files)} tracked files, {len(allowed)} reviewed public contacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
