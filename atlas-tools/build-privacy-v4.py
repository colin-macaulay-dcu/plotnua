#!/usr/bin/env python3
"""PRIVACY NOTICE V4 · bounded builder for the Art Space Register section.

Founder direction, 13 October 2026 ("Art Space Register · activation
preparation approved"): implement the V4 privacy-page builder from the
existing draft, and keep the section unpublished until founder approval.

PUBLICATION APPROVED, 13 October 2026 (23:50): the founder approved the Art
Space Register GDPR Self-Assessment dated 13 October 2026 and authorised
publication of Privacy Notice V4, dated October 2026 (APPROVAL below). The
approval covers the privacy notice ONLY: the Art Space Register stays CLOSED
(OPEN_APPROVAL in build-art-space-register.py remains None).
  --check            (default) before publication: build V4 in memory from the
                     live V3 privacy.html, run every guard, write nothing.
                     After publication: verify the published page. It
                     rebuilds V3 from it, checks Section 7 against its pin,
                     rebuilds V4 and runs guards V1-V6 again.
  --preview PATH     write the V4 page to PATH for review. PATH must be
                     OUTSIDE the repository: every file in the repository is
                     served by GitHub Pages, so a preview inside it would be a
                     publication.
  --apply            write privacy.html (and the Garden proof co-edits, see
                     CO-EDITS). REFUSED while APPROVAL is None or incomplete,
                     or while BACKUP_PERIOD is None. Setting APPROVAL is a
                     committed, founder-authorised change recording the
                     founder's approval, the dated GDPR self-assessment, the
                     documented resolution of material risks and the
                     "Last updated" label (founder decision, 13 Oct 2026:
                     no external legal review by default).

THE CHANGE, AND NOTHING ELSE (guard V6 proves it)
  1. Sections 8-17 renumbered 9-18.
  2. New Section 8, "The Art Space Register" (SECTION8 below), immediately
     after Section 7, carrying the marker MARK and the version label.
  3. Third-party section: one sentence naming the Art Space Register's
     Cloudflare service and its separate Airtable database.
  4. Retention section: one line for Art Space Register records.
  5. "Last updated" label, from APPROVAL, only if it differs.
  6. Section 2 ("Information We Collect"): one sentence pointing to Section 8,
     after the existing Garden Owner Register sentence (founder approval,
     13 Oct 2026, 22:00).
Section 7 (the Garden Owner Register) is byte-identical. The Garden Worker
keeps privacy version 2026-10-PHASE2-V3 (founder decision, 13 Oct 2026).

CO-EDITS ON --apply ONLY. atlas-tools/prove-g6-owner-register.py pins the V3
page's section count (1..17), uses one section heading as a mutation anchor,
and requires each mutation anchor to occur once on the whole page, which six
no longer do once Section 8 repeats Section 7's legal sentences. Three bounded
co-edits follow (G6_CO_EDITS), rehearsed by atlas-tools/prove-privacy-v4.py;
nothing else in the Garden proof changes. The
Garden Worker, its consent, its database and its registration experience are
not touched.

GUARDS
  V1 SECTION8 is the governed text: every paragraph appears verbatim in
     governance/PRIVACY-VERSION-2026-10-PHASE2-V4-DRAFT.md, and so do the
     third-party and retention sentences
  V2 numbering 1..18; Section 7 is the Garden Owner Register, byte-identical;
     Section 8 is the Art Space Register
  V3 Section 8 states: no matching, no booking, no payment; separate from the
     Garden register; every collected field; the never-collected list;
     consent and withdrawal; 24 months; the 12-month deletion note; the
     deletion route; the transfer facts
  V4 consistency: the collected fields match the Worker's ALLOWED_KEYS; the
     retention figures match the register's on-page notice; the Art Worker's
     PRIVACY_VERSION is the version this section carries; the Garden Worker
     stays on V3
  V5 no invented legal assurance or match promise anywhere on the page
  V6 removing exactly the six declared changes from the output gives back
     the input, byte for byte

Usage:
  python3 atlas-tools/build-privacy-v4.py --check
  python3 atlas-tools/build-privacy-v4.py --preview /tmp/privacy-v4-preview.html
"""
import sys as _sys_v6
_sys_v6.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from privacy_v6_layer import without_v6 as _without_v6  # V6 layer: verify V3-V5 text unchanged beneath it
import hashlib
import html as htmlmod
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIVACY = ROOT / "privacy.html"
DRAFT = ROOT / "governance" / "PRIVACY-VERSION-2026-10-PHASE2-V4-DRAFT.md"
ART_WRANGLER = ROOT / "worker" / "art-space-register" / "wrangler.toml"
ART_WORKER = ROOT / "worker" / "art-space-register" / "src" / "index.js"
GARDEN_WRANGLER = ROOT / "worker" / "garden-register" / "wrangler.toml"
REGISTER_BUILDER = ROOT / "atlas-tools" / "build-art-space-register.py"
G6_PROOF = ROOT / "atlas-tools" / "prove-g6-owner-register.py"

VERSION = "2026-10-PHASE2-V4"
MARK = "<!-- PLOTNUA-ART-PRIVACY-V4 · Art Space Register, privacy notice %s -->" % VERSION

# None = NOT APPROVED. Publication requires a committed change that fills all
# four, e.g. {"founder_approval": "Colin MacAulay, <date>",
#             "self_assessment": "Art Space Register GDPR Self-Assessment, <date>, v<n>",
#             "risks_resolved": "<where the resolution of each material risk is documented>",
#             "last_updated": "November 2026"}
# Founder decision, 13 Oct 2026 22:18: a completed, dated GDPR self-assessment,
# documented resolution of material risks and explicit founder approval replace
# the mandatory external legal review. Paid advice is not required by default.
# Every technical guard below still applies.
APPROVAL = {
    "founder_approval": "Colin MacAulay, founder, 13 October 2026 (23:50): publication of PlotNua Privacy Notice V4, "
                        "dated October 2026, is authorised. The approval covers the privacy notice ONLY; the Art "
                        "Space Register remains CLOSED.",
    "self_assessment": "Art Space Register GDPR Self-Assessment, dated 13 October 2026, approved by the founder on "
                       "13 October 2026, with its documented limitations and remaining risks accepted subject to "
                       "the safeguards and opening conditions it records.",
    "risks_resolved": "governance/ART-SPACE-REGISTER-BUILD-2026-10-13.md sections 11.10-11.15 and the self-assessment, "
                      "Section B: each material risk is resolved, or gated before opening (fully executed Airtable "
                      "DPA, the six database views, a recorded dry run, OPEN_APPROVAL).",
    "last_updated": "October 2026",
}
APPROVAL_KEYS = ("founder_approval", "self_assessment", "risks_resolved", "last_updated")

# Airtable keeps automatic base snapshots for a period set by the plan (2 weeks
# on Free, 1 year on Team, longer above). None = not yet confirmed: the notice
# then says "for a limited period" and --apply is REFUSED until the founder
# records the plan's period here, e.g. "for up to 2 weeks".
BACKUP_PERIOD = "up to 1 year"   # Airtable Team plan, confirmed by the founder 13 Oct 2026 (22:51)

HOSTS = "Art Space Register"
SECTION8 = [
    ("p", "The Open Your Home to Art Property Check is private: answering its questions does not send PlotNua your details. After seeing your result, you can choose to join the Art Space Register. It is a list, kept privately by PlotNua, of homeowners in Ireland who might be willing to offer space for artists' finished work: storing it, displaying it, opening a space to visitors by arrangement, or helping it find a buyer. Joining is voluntary. PlotNua is not introducing homeowners to artists, there is no matching or booking service, no payment is offered, and joining the register does not arrange anything."),
    ("p", "This register is separate from the Garden Owner Register described in Section 7. It is kept in a separate database, and your details are not shared between the two."),
    ("p", "What we collect when you join:"),
    ("ul", ["your first name;",
            "your email address;",
            "your county;",
            "which of storing, displaying, opening to visitors or helping to sell you would consider;",
            "if you choose to tell us: the kind of space, whether money is part of it for you, and anything you add in the note; and",
            "a record that you gave your consent, which version of this notice applied, and when you joined."]),
    ("p", "We do not collect your address, your Eircode, your town, your phone number, your surname, your age, photographs of your home, or anything about the value of what is in it. The form starts with three of your Property Check answers filled in, and only what is in the form when you submit it is sent. Your other Property Check answers and your Property Check result are not sent to the register."),
    ("p", "We use this information to contact you about the Open Your Home to Art pilot, for example to ask a few questions about what you would consider, or to let you know if the pilot develops. We rely on your consent, which you give by ticking the box when you join. You can withdraw it at any time."),
    ("p", "Your record is private to PlotNua. It is not published, and there is no public listing, map, profile or directory. Records are reviewed by a person at PlotNua. Registration details are accessible only to authorised people managing the register and to service providers where necessary to operate it. They are not shared with artists or made publicly available. Your email address would only be shared with another person if you agreed to a specific arrangement, and no such arrangements are available."),
    ("p", "The form sends your details to a PlotNua service hosted on infrastructure provided by Cloudflare, which records them in the register. The register is stored in Airtable, a database service. Cloudflare and Airtable are both based in the United States, so your information may be processed outside the European Economic Area. Cloudflare states that it relies on the EU Standard Contractual Clauses, and on its certification under the EU-U.S. Data Privacy Framework, for such transfers. Airtable's Data Processing Addendum states that the EU Standard Contractual Clauses apply to personal data transferred from the European Economic Area. Visitors should refer to Cloudflare's and Airtable's own privacy policies for more about how they process personal information."),
    ("p", "The services that carry the form, such as Cloudflare, process technical information such as your IP address so that your request can be delivered securely. PlotNua does not record it in the register."),
    ("p", "We keep your record for no longer than 12 months, and we delete it sooner if the pilot ends or no longer needs it. You can ask us to delete it at any time. This is how long PlotNua keeps your record; the recovery copies kept by our database provider are described below."),
    ("p", "To leave the register or ask us to delete your record, email <a href=\"mailto:hello@plotnua.ie\">hello@plotnua.ie</a>. There is nothing to cancel and no notice period. When we delete your record, we delete everything the register holds about you, including the record of your consent. A deleted record can be restored from our database provider's trash for 7 days. Separately, the provider keeps its own automatic recovery copies of the database for %s, and these may still contain a deleted record until they expire. Those copies are managed by the provider, not used by PlotNua, and we never restore deleted registration records from them. We keep only an anonymous entry in our deletion log, recording when a deletion was requested or became due, when it was completed and why, so that we can show deletions are carried out. That entry contains nothing that identifies you." % (BACKUP_PERIOD or "a limited period")),
]
THIRD_ANCHOR = ("    <p>The Garden Owner Register described in Section 7 also runs on a PlotNua service hosted on "
                "infrastructure provided by Cloudflare.</p>\n")
THIRD_NEW = ("    <p>The Art Space Register described in Section 8 also runs on a PlotNua service hosted on "
             "infrastructure provided by Cloudflare, and its records are stored in Airtable in a database kept "
             "separate from the Garden Owner Register.</p>\n")
RET_ANCHOR = "    <p>Garden Owner Register records are kept for a maximum of 24 months, as described in Section 7.</p>\n"
RET_NEW = "    <p>Art Space Register records are kept for a maximum of 12 months, as described in Section 8.</p>\n"
SEC2_ANCHOR = "    <p>If you choose to join the Garden Owner Register, we also collect the information described in Section 7.</p>\n"
SEC2_NEW = "    <p>If you choose to join the Art Space Register, we also collect the information described in Section 8.</p>\n"
UPDATED_RE = re.compile(r'<p class="policy-updated">Last updated: ([^<]+)</p>')

# Section 7 as approved and published in V3 (Garden Owner Register). Pinned so
# a V4 page can never be built over an altered Garden section (guard V2).
GARDEN7_SHA256 = "fb90a58b549f4aff353004f10efa003d43e76cee20da3ef2f9586686825648cc"

# After publication: the V3 page that V4 was built from, pinned so that no
# sentence outside the declared V4 changes can be edited without a deliberate,
# reviewed update of this pin (set at publication, 13 Oct 2026).
PUBLISHED_V3_SHA256 = "49e347398345a42f83147a1e92b09f6b8afd7077298135c4dd6243376832f588"

G6_CO_EDITS = [
    ('g["PV14"] = [int(n) for n in re.findall(r"<h2>(\\d+)\\. ", src)] == list(range(1, 18))',
     'g["PV14"] = [int(n) for n in re.findall(r"<h2>(\\d+)\\. ", src)] == list(range(1, 19))  # 18 since privacy V4'),
    ('("PV14", "a section number left stale", "<h2>9. Third-Party Services and Links</h2>",\n'
     '     "<h2>8. Third-Party Services and Links</h2>"),',
     '("PV14", "a section number left stale", "<h2>10. Third-Party Services and Links</h2>",\n'
     '     "<h2>9. Third-Party Services and Links</h2>"),'),
    # Section 8 deliberately repeats six Section 7 sentences (consent basis,
    # transfers, retention, deletion route...). The Garden proof's mutation
    # anchors must occur exactly once, so on V4 they are taken inside Section 7
    # whenever they occur there. On a V3 page this is behaviour-identical.
    ('    n = LIVE.count(old)\n'
     '    if n != 1:\n'
     '        say(False, f"[VACUOUS] {gid} {name}", f"anchor found {n} times"); continue\n'
     '    got = guards(LIVE.replace(old, new))\n',
     '    g7 = re.search(r"<h2>7\\. The Garden Owner Register</h2>[\\s\\S]*?</section>", LIVE).group(0)\n'
     '    if g7.count(old) == 1:   # since privacy V4, Section 8 repeats some Section 7 sentences\n'
     '        mutated = LIVE.replace(g7, g7.replace(old, new), 1)\n'
     '    else:\n'
     '        n = LIVE.count(old)\n'
     '        if n != 1:\n'
     '            say(False, f"[VACUOUS] {gid} {name}", f"anchor found {n} times"); continue\n'
     '        mutated = LIVE.replace(old, new)\n'
     '    got = guards(mutated)\n'),
]


def refuse(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


def section8_html():
    out = ["  " + MARK, '  <section class="article-section reveal" id="art-space-register">',
           "    <h2>8. The Art Space Register</h2>"]
    for kind, body in SECTION8:
        if kind == "p":
            out.append("    <p>%s</p>" % body)
        else:
            out.append("    <ul>")
            out += ["      <li>%s</li>" % li for li in body]
            out.append("    </ul>")
    out.append("  </section>")
    return "\n".join(out) + "\n\n"


def plain(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s).replace("’", "'").replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip()


def sections(src):
    return [(int(n), t) for n, t in re.findall(r"<h2>(\d+)\. ([^<]+)</h2>", src)]


def garden7(src):
    m = re.search(r"  <!-- PLOTNUA-G6-PREP[^\n]*\n  <section class=\"article-section reveal\">\n"
                  r"    <h2>7\. The Garden Owner Register</h2>[\s\S]*?  </section>\n", src)
    return m.group(0) if m else None


def transform(v3, last_updated=None):
    """V3 privacy.html -> V4. Pure: no file is read or written."""
    if MARK in v3 or 'id="art-space-register"' in v3:
        refuse("privacy.html already carries the Art Space Register section")
    if [n for n, _ in sections(v3)] != list(range(1, 18)):
        refuse("input is not the 17-section V3 page")
    g7 = garden7(v3)
    if not g7 or v3.count(g7) != 1:
        refuse("Section 7 (Garden Owner Register) not found exactly once")
    if hashlib.sha256(g7.encode("utf-8")).hexdigest() != GARDEN7_SHA256:
        refuse("V2 Section 7 is not the approved Garden Owner Register text")
    out = v3
    for n in range(17, 7, -1):                      # 17->18 ... 8->9, top down: no collisions
        old = re.search(r"<h2>%d\. ([^<]+)</h2>" % n, out)
        out = out.replace(old.group(0), "<h2>%d. %s</h2>" % (n + 1, old.group(1)), 1)
    out = out.replace(g7, g7 + "\n" + section8_html().rstrip("\n") + "\n", 1)
    for anchor, new, lab in ((SEC2_ANCHOR, SEC2_NEW, "Section 2 anchor"), (THIRD_ANCHOR, THIRD_NEW, "third-party anchor"),
                             (RET_ANCHOR, RET_NEW, "retention anchor")):
        if out.count(anchor) != 1:
            refuse(lab + " not found exactly once")
        out = out.replace(anchor, anchor + new, 1)
    if last_updated:
        m = UPDATED_RE.search(out)
        if not m:
            refuse("the Last updated line is missing")
        out = out.replace(m.group(0), '<p class="policy-updated">Last updated: %s</p>' % last_updated, 1)
    return out


def untransform(v4):
    """Remove exactly the declared changes (guard V6)."""
    s = v4.replace("\n" + section8_html().rstrip("\n") + "\n", "", 1)
    s = s.replace(SEC2_NEW, "", 1).replace(THIRD_NEW, "", 1).replace(RET_NEW, "", 1)
    for n in range(9, 19):
        old = re.search(r"<h2>%d\. ([^<]+)</h2>" % n, s)
        if old:
            s = s.replace(old.group(0), "<h2>%d. %s</h2>" % (n - 1, old.group(1)), 1)
    return s


def worker_allowed():
    m = re.search(r"const ALLOWED_KEYS = Object\.freeze\(\[([\s\S]*?)\]\)", ART_WORKER.read_text(encoding="utf-8"))
    return set(re.findall(r"'([a-z_0-9]+)'", m.group(1)))


def toml_version(path):
    m = re.search(r'^PRIVACY_VERSION\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def guards(v3, v4):
    s8 = re.search(r'<section class="article-section reveal" id="art-space-register">([\s\S]*?)</section>', v4)
    if not s8:
        refuse("V2 Section 8 missing")
    s8t = plain(s8.group(1))
    # V1
    draft = plain(DRAFT.read_text(encoding="utf-8").replace("**", "").replace("> ", " "))
    for kind, body in SECTION8:
        for piece in ([body] if kind == "p" else body):
            if plain(piece) not in draft:
                refuse("V1 Section 8 text is not in the V4 draft: " + plain(piece)[:70])
    for piece in (SEC2_NEW, THIRD_NEW, RET_NEW):
        if plain(piece) not in draft:
            refuse("V1 a declared change is not in the V4 draft: " + plain(piece)[:70])
    # V2
    if [n for n, _ in sections(v4)] != list(range(1, 19)):
        refuse("V2 sections not numbered 1..18")
    if v4.count(SEC2_NEW) != 1 or v4.index(SEC2_ANCHOR) > v4.index(SEC2_NEW) \
            or v4.index(SEC2_NEW) > v4.index("<h2>3. How We Use Your Information</h2>"):
        refuse("V2 Section 2 does not point to Section 8 once, after the Garden sentence")
    titles = dict(sections(v4))
    if titles[7] != "The Garden Owner Register" or titles[8] != "The Art Space Register":
        refuse("V2 Sections 7 and 8 are not Garden then Art")
    if garden7(v4) != garden7(v3):
        refuse("V2 Section 7 changed")
    if v4.count(MARK) != 1 or VERSION not in MARK:
        refuse("V2 version marker missing")
    # V3
    for need in ("there is no matching or booking service", "no payment is offered",
                 "does not arrange anything", "separate from the Garden Owner Register described in Section 7",
                 "your first name;", "your email address;", "your county;",
                 "which of storing, displaying, opening to visitors or helping to sell you would consider;",
                 "We do not collect your address, your Eircode, your town, your phone number, your surname",
                 "We rely on your consent", "You can withdraw it at any time",
                 "no longer than 12 months", "including the record of your consent",
                 "We keep only an anonymous entry in our deletion log", "That entry contains nothing that identifies you",
                 "trash for 7 days", "automatic recovery copies",
                 "This is how long PlotNua keeps your record",
                 "not shared with artists or made publicly available",
                 "process technical information such as your IP address",
                 "email hello@plotnua.ie", "outside the European Economic Area", "Standard Contractual Clauses",
                 "accessible only to authorised people managing the register"):
        if need not in s8t:
            refuse("V3 Section 8 lacks: " + need)
    # V4
    collected = {"first_name", "email", "county", "ways", "space", "money", "host_note", "over_18",
                 "consent_text", "source"}
    if worker_allowed() != collected:
        refuse("V4 the Worker's ALLOWED_KEYS no longer match the fields this section describes: %r"
               % sorted(worker_allowed()))
    reg = plain((ROOT / "disc024-open-your-home-to-art.html").read_text(encoding="utf-8"))
    if ("A maximum of 12 months" not in reg or "We keep only an anonymous log entry" not in reg
            or "They are not shared with artists or made publicly available." not in reg
            or "fingerprint" in reg
            or (BACKUP_PERIOD and ("recovery copies for " + BACKUP_PERIOD) not in reg)):
        refuse("V4 the register's on-page notice (as built on the DISC-024 check) does not carry the same retention figures")
    if toml_version(ART_WRANGLER) != art_version_expected():
        refuse("V4 the Art Worker's PRIVACY_VERSION is not %s (the notice in force)" % art_version_expected())
    if toml_version(GARDEN_WRANGLER) != "2026-10-PHASE2-V3":
        refuse("V4 the Garden Worker must stay on 2026-10-PHASE2-V3 (founder decision)")
    # V5
    if re.search(r"\b(fully compliant|GDPR[- ]compliant|we guarantee|guaranteed match|we will match|"
                 r"you will be matched|certified secure|you will be paid|earn)\b", plain(v4), re.I):
        refuse("V5 an invented assurance or promise is on the page")
    # V6
    back = untransform(v4)
    m3, m4 = UPDATED_RE.search(v3), UPDATED_RE.search(back)
    if m3 and m4:
        back = back.replace(m4.group(0), m3.group(0), 1)
    if back != v3:
        refuse("V6 something other than the six declared changes differs")


# ---- PRIVACY V5 AWARENESS (founder approval to implement V5, 14 Oct 2026) ----
# V5 (atlas-tools/build-privacy-v5.py) is built ON TOP of this V4 page: it
# renames the Section 8 heading and adds the Artist Register around the V4
# text, which stays word for word. Once V5 is live, every check here reads the
# page as the V4 page it was built from: exactly the declared V5 changes are
# removed and the V4 "Last updated" label restored. A page that is not exactly
# V5 over V4 does not reduce to the V4 page, so every V4 check still refuses
# it; the V5 builder checks the V5 additions themselves. Nothing is weakened.
V5_MARK_TEXT = "PLOTNUA-ARTIST-PRIVACY-V5"


def _pv5():
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("build_privacy_v5", ROOT / "atlas-tools" / "build-privacy-v5.py")
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def v5_live(text=None):
    text = _without_v6(PRIVACY.read_text(encoding="utf-8")) if text is None else text
    return V5_MARK_TEXT in text


def as_v4(text):
    if V5_MARK_TEXT not in text:
        return text
    v = _pv5().untransform(text)
    m = UPDATED_RE.search(v)
    if m and isinstance(APPROVAL, dict) and APPROVAL.get("last_updated"):
        v = v.replace(m.group(0), '<p class="policy-updated">Last updated: %s</p>' % APPROVAL["last_updated"], 1)
    return v


def art_version_expected():
    """The homeowner Worker records V4 while V4 is the notice in force, and V5 once V5 is live."""
    return _pv5().VERSION if v5_live() else VERSION


def published_ok(text=None):
    """True when privacy.html carries exactly the governed V4 Section 8 (used by the register's R2).
    Once V5 is live, the V4 page inside it must still carry it exactly."""
    text = _without_v6(PRIVACY.read_text(encoding="utf-8")) if text is None else text
    text = as_v4(text)
    if text.count(MARK) != 1 or (section8_html().rstrip("\n") + "\n") not in text:
        return False
    return [n for n, _ in sections(text)] == list(range(1, 19))


def published_exact(text=None):
    """The full published-state verification of --check, as a predicate: the
    page (or the V4 page inside a V5 page) is exactly the governed V4
    transform of the pinned V3 page, with the approved label and the pinned
    Section 7. Used by the V5 builder, so V5 can only be built over, and only
    verify against, an exact V4."""
    text = as_v4(_without_v6(PRIVACY.read_text(encoding="utf-8")) if text is None else text)
    try:
        if not published_ok(text) or not isinstance(APPROVAL, dict):
            return False
        m = UPDATED_RE.search(text)
        if not m or m.group(1) != APPROVAL.get("last_updated"):
            return False
        v3 = untransform(text)
        if hashlib.sha256(v3.encode("utf-8")).hexdigest() != PUBLISHED_V3_SHA256:
            return False
        g7 = garden7(v3)
        if not g7 or hashlib.sha256(g7.encode("utf-8")).hexdigest() != GARDEN7_SHA256:
            return False
        return transform(v3, APPROVAL["last_updated"]) == text
    except SystemExit:
        return False


def main(argv):
    cur = _without_v6(PRIVACY.read_text(encoding="utf-8"))
    if "--apply" in argv:
        if not (isinstance(APPROVAL, dict) and all(isinstance(APPROVAL.get(k), str) and APPROVAL[k].strip()
                                                     for k in APPROVAL_KEYS)):
            refuse("V4 is NOT APPROVED for publication: APPROVAL must record the founder's approval, the dated GDPR "
                   "self-assessment, the documented resolution of material risks and the Last updated label")
        if not (isinstance(BACKUP_PERIOD, str) and BACKUP_PERIOD.strip()):
            refuse("V4 may not be published until BACKUP_PERIOD records the Airtable plan's snapshot retention")
        v4 = transform(cur, APPROVAL["last_updated"])
        guards(cur, v4)
        g6 = G6_PROOF.read_text(encoding="utf-8")
        for old, new in G6_CO_EDITS:
            if g6.count(old) != 1:
                refuse("Garden proof co-edit anchor not found exactly once: " + old[:60])
            g6 = g6.replace(old, new)
        PRIVACY.write_text(v4, encoding="utf-8")
        G6_PROOF.write_text(g6, encoding="utf-8")
        print("privacy.html: V4 APPLIED (Section 8 · Art Space Register) and %d Garden proof co-edits" % len(G6_CO_EDITS))
        return
    if MARK in cur:
        cur = as_v4(cur)
        if "--preview" in argv:
            refuse("V4 is already published; there is nothing to preview")
        if not (isinstance(APPROVAL, dict) and all(isinstance(APPROVAL.get(k), str) and APPROVAL[k].strip()
                                                     for k in APPROVAL_KEYS)):
            refuse("privacy.html carries V4 but APPROVAL does not record its approval")
        if not published_ok(cur):
            refuse("the published Section 8 differs from the governed text")
        m = UPDATED_RE.search(cur)
        if not m or m.group(1) != APPROVAL["last_updated"]:
            refuse("the published Last updated label is not the approved one (%s)" % APPROVAL["last_updated"])
        v3 = untransform(cur)
        if hashlib.sha256(v3.encode("utf-8")).hexdigest() != PUBLISHED_V3_SHA256:
            refuse("V6 the published page differs from the pinned V3 base outside the declared V4 changes")
        g7 = garden7(v3)
        if not g7 or hashlib.sha256(g7.encode("utf-8")).hexdigest() != GARDEN7_SHA256:
            refuse("V2 the published Section 7 is not the approved Garden Owner Register text")
        if transform(v3, APPROVAL["last_updated"]) != cur:
            refuse("V6 the published page is not exactly the governed V4 transform of V3")
        guards(v3, cur)
        print("privacy.html: V4 PUBLISHED · Section 8 matches the governed text · V1-V6 pass")
        return
    v4 = transform(cur)
    guards(cur, v4)
    if "--preview" in argv:
        i = argv.index("--preview")
        if i + 1 >= len(argv):
            refuse("--preview needs a path")
        out = pathlib.Path(argv[i + 1]).resolve()
        if ROOT in out.parents or out == ROOT:
            refuse("--preview path is inside the repository; every file there is published by GitHub Pages")
        out.write_text(v4, encoding="utf-8")
        print("privacy V4 preview written to %s (privacy.html unchanged)" % out)
        return
    print("privacy.html: V3 live · V4 UNPUBLISHED · dry run builds cleanly — V1-V6 pass · nothing written")


if __name__ == "__main__":
    main(sys.argv[1:])
