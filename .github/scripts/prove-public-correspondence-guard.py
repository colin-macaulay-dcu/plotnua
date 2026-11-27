#!/usr/bin/env python3
"""Proves the public-correspondence guard refuses what it exists to refuse, and passes legitimate public supplier
information. Each case builds a small temporary git tree (the real rights records and allowlist plus planted files),
runs check_public_correspondence.py on it and compares the outcome. A guard that has never been seen to refuse is a
comment, not a safeguard."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GUARD = REPO / ".github/scripts/check_public_correspondence.py"
RECORDS = json.loads((REPO / "image-rights-records.json").read_text(encoding="utf-8"))
ALLOW = json.loads((REPO / "governance/public-contact-allowlist.json").read_text(encoding="utf-8"))
MID = "1" + "a2b3c4d5e6f7a8b9"[:15]                       # a 16-hex mail id, assembled so this file holds none
G = "g" + "mail"
AT = "@"                                         # planted addresses are assembled, so this file holds none


def tree(files, records=None, allow=None):
    d = Path(tempfile.mkdtemp(prefix="pcg-"))
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    (d / "governance").mkdir()
    a = allow if allow is not None else {**ALLOW, "contacts": [c for c in ALLOW["contacts"]
                                                               if c["address"] == "movingart@mauriceward.com"]}
    (d / "governance/public-contact-allowlist.json").write_text(json.dumps(a), encoding="utf-8")
    (d / "image-rights-records.json").write_text(json.dumps(records if records is not None else RECORDS),
                                                 encoding="utf-8")
    base = {"plotart/services.html": '<a href="mailto:movingart@mauriceward.com">Email</a>'}
    for rel, text in {**base, **files}.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    subprocess.run(["git", "-C", str(d), "add", "-A"], check=True)
    return d


def run(d):
    r = subprocess.run([sys.executable, str(GUARD), str(d)], capture_output=True, text=True)
    shutil.rmtree(d, ignore_errors=True)
    return r.returncode, r.stdout + r.stderr


def no_policy():
    r = json.loads(json.dumps(RECORDS))
    r.pop("correspondence_policy", None)
    return r


def no_flag():
    r = json.loads(json.dumps(RECORDS))
    for rec in r["records"]:
        if isinstance(rec.get("permission"), dict):
            rec["permission"].pop("pre_live_review_requested", None)
            break
    return r


CASES = [
    ("clean tree with legitimate public supplier information", True, "OK", dict(files={
        "suppliers/x.html": '<p>Our website <a href="https://www.example-maker.ie/">example-maker.ie</a>; the maker\'s '
                            'own page says "built to order in Ireland" (read 1 Nov 2026).</p>',
        "supplier-preview-system/showcases/x/showcase.json": json.dumps(
            {"basis": "Granted by email, 1 Nov 2026. Wording held privately (PN-EVID-RIGHTS-ORG-000001-20261101)."}),
        "worker/t/test/prove.mjs": "const e = 'artist@example.com';"})),
    ("a mail message identifier in a governance note", False, "C1", dict(files={
        "governance/NOTE.md": f"Granted in {G.capitalize()} {MID}."})),
    ("a thread identifier in source code", False, "C1", dict(files={
        "atlas-tools/x.py": f"# see thread {MID}"})),
    ("a link into a mailbox", False, "C1", dict(files={
        "governance/NOTE.md": "https://mail." + "google.com/" + "mail/u/0/#inbox/abc"})),
    ("a personal webmail address in a test fixture", False, "C2", dict(files={
        "worker/t/test/prove.mjs": f"const e = 'somebody@{G}.com';"})),
    ("an unreviewed business address", False, "C3", dict(files={
        "atlas-tools/x.json": '{"contact": "jane.doe' + AT + 'some-maker.ie"}'})),
    ("a personal webmail address on the allowlist", False, "can never be allowlisted", dict(files={
        "atlas-tools/x.txt": f"someone@{G}.com"}, allow={"contacts": [
            {"address": f"someone@{G}.com", "kind": "public-business-contact", "published_on": "x", "reason": "x"},
            {"address": "movingart@mauriceward.com", "kind": "public-business-contact", "published_on": "x",
             "reason": "x"}]})),
    ("a mailbox reference in a supplier showcase", False, "C4", dict(files={
        "supplier-preview-system/showcases/x/showcase.json": json.dumps({"basis": f"Granted ({G.capitalize()})."})})),
    ("a quotation attributed to an email in a supplied-image register", False, "C4", dict(files={
        "atlas-tools/plotart-services/images/x/image-copies.json": json.dumps(
            {"what": '"Please use these photos on your website" (Owner, email, 1 Nov 2026)'})})),
    ("a verbatim-correspondence marker in an Atlas snapshot", False, "C4", dict(files={
        "atlas-tools/targeted-updates/x.json": json.dumps({"Notes": "Recorded verbatim from the reply."})})),
    ("the correspondence policy removed from the rights records", False, "C5", dict(files={}, records=no_policy())),
    ("a structured permission without its pre-live review flag", False, "C5", dict(files={}, records=no_flag())),
    ("an allowlisted address that is no longer used", False, "no longer appears", dict(files={}, allow={"contacts": [
        {"address": "movingart@mauriceward.com", "kind": "public-business-contact", "published_on": "x",
         "reason": "x"},
        {"address": "info" + AT + "gone-maker.ie", "kind": "public-business-contact", "published_on": "x", "reason": "x"}]})),
]


def main():
    bad = 0
    for name, should_pass, expect, kw in CASES:
        code, out = run(tree(**kw))
        ok = (code == 0) == should_pass and expect in out
        bad += not ok
        print(("PASS" if ok else "FAIL"), name, "" if ok else "\n" + out)
    if bad:
        print(f"PUBLIC CORRESPONDENCE GUARD PROOF · {bad} case(s) did not behave")
        return 1
    print(f"PUBLIC CORRESPONDENCE GUARD PROOF · OK · {len(CASES)} cases "
          f"({sum(1 for c in CASES if not c[1])} refusals, {sum(1 for c in CASES if c[1])} legitimate pass)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
