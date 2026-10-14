#!/usr/bin/env python3
"""PRIVACY NOTICE V5 · bounded builder for the Artist Register.

Founder approval to IMPLEMENT, 14 October 2026 (19:29): prepare V5 for
publication, generate the proposed page for review, and do NOT publish it.
APPROVAL is None: --apply is refused until the founder approves the exact
wording in governance/PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md.

  --check            before publication: build V5 in memory from the live V4
                     privacy.html, run W1-W7, write nothing. After
                     publication: verify the published page (it rebuilds V4
                     from it, checks V4 with the V4 builder's own published
                     check, rebuilds V5 and runs W1-W7 again).
  --preview PATH     write the proposed V5 page to PATH for review. PATH must
                     be OUTSIDE the repository: every file in the repository is
                     served by GitHub Pages, so a preview inside it would be a
                     publication.
  --apply            REFUSED while APPROVAL is None or incomplete. Once
                     approved, it writes privacy.html AND moves the homeowner
                     Worker's PRIVACY_VERSION from V4 to V5 in wrangler.toml,
                     in the same commit, so new homeowner registrations record
                     the notice in force. That takes effect only when the
                     founder deploys the Worker, which the sequence below
                     places AFTER the V5 page is live. Existing V4 consent
                     records in Airtable are never touched.

THE CHANGE, AND NOTHING ELSE (guard W7 proves it)
  1. Section 8 heading: "8. The Art Space Register" becomes
     "8. The Art Space Register and the Artist Register".
  2. Section 8: the V5 marker, an introduction distinguishing the two
     registers and a "(homeowners)" sub-heading, BEFORE the V4 text, which
     is unchanged word for word.
  3. Section 8: the Artist Register sub-section, AFTER the V4 text.
  4. Section 2: one sentence, after the Art Space Register sentence.
  4a. Section 10 (Third-Party Services and Links): one sentence after the
      Art Space Register sentence: the same Cloudflare service and Airtable
      database, separate records (founder correction, 14 Oct 2026, 19:39).
  5. Section 12: one line, after the Art Space Register line.
  6. One scoped style rule for the two sub-headings (.pv5-sub).
  7. "Last updated" label, from APPROVAL, only if it differs.
No renumbering. Section 7 (Garden Owner Register) is byte-identical. The
Garden Worker stays on V3.

GUARDS
  W1 governed text, both ways: every piece of text this builder adds is a
     governed "> " line of the V5 draft, and every governed line is on the page
  W2 the V4 notice is intact inside V5: removing the V5 changes gives back the
     input byte for byte, and the V4 builder's FULL published verification
     (pinned V3 base, pinned Section 7, governed V4 transform) passes on it
  W3 the founder's nine requirements are each stated in the artist sub-section
  W4 consistency: the consent sentence is identical in the Worker, the artist
     page builder and the draft; the fields described match the Worker's
     ARTIST_ALLOWED_KEYS; ARTIST_PRIVACY_VERSION is V5; the artist route is
     still CLOSED; the Garden Worker stays on V3
  W5 no invented assurance or promise; the no-guarantee wording is present
  W6 numbering 1..18; Section 7 byte-identical; Section 8 is both registers
  W7 nothing but the declared changes differs (see W2)

Usage:
  python3 atlas-tools/build-privacy-v5.py --check
  python3 atlas-tools/build-privacy-v5.py --amend-s8     (one-sentence Section 8 amendment, 14 Oct 2026)
  python3 atlas-tools/build-privacy-v5.py --preview /tmp/privacy-v5-preview.html
"""
import html as htmlmod
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIVACY = ROOT / "privacy.html"
DRAFT = ROOT / "governance" / "PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md"
ART_WRANGLER = ROOT / "worker" / "art-space-register" / "wrangler.toml"
ART_WORKER = ROOT / "worker" / "art-space-register" / "src" / "index.js"
GARDEN_WRANGLER = ROOT / "worker" / "garden-register" / "wrangler.toml"
ARTIST_BUILDER = ROOT / "atlas-tools" / "build-artist-register.py"

VERSION = "2026-10-PHASE2-V5"
V4_VERSION = "2026-10-PHASE2-V4"
MARK = "  <!-- PLOTNUA-ARTIST-PRIVACY-V5 · Art Space Register and Artist Register, privacy notice %s -->\n" % VERSION

# None = NOT APPROVED. Publication requires a committed change filling all four:
# {"founder_approval": "Colin MacAulay, <date>: approval of the exact V5 wording",
#  "self_assessment": "Artist Register addendum to the Art Space Register GDPR self-assessment, <date>",
#  "risks_resolved": "<where each material risk's resolution is documented>",
#  "last_updated": "<Month YYYY>"}
APPROVAL = {
    "founder_approval": "Colin MacAulay, founder, 14 October 2026 (19:45): approves publication of PlotNua Privacy "
                        "Notice V5, dated October 2026, in the reviewed wording of "
                        "governance/PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md including both corrections of 19:39. "
                        "The approval covers the privacy notice ONLY; the Artist Register remains CLOSED.",
    "self_assessment": "Artist Register addendum to the Art Space Register GDPR self-assessment, dated 14 October "
                       "2026, approved by the founder on 14 October 2026 (19:45).",
    "risks_resolved": "governance/PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md, 'Risks and resolution' (six risks, "
                      "each resolved), and governance/ARTIST-REGISTER-BUILD-2026-10-14.md (opening conditions).",
    "last_updated": "October 2026",
}
APPROVAL_KEYS = ("founder_approval", "self_assessment", "risks_resolved", "last_updated")

# EDITORIAL AMENDMENT TO PUBLISHED V5 (founder decision, 14 October 2026, 20:33).
# One sentence in Section 8, so the notice stays true whether the Artist Register
# is open or paused. The version stays 2026-10-PHASE2-V5 and the Last updated
# label stays as approved; every other privacy commitment is unchanged. Applied
# once with --amend-s8, which replaces exactly this sentence and nothing else.
OLD_S8_SENTENCE = "When registrations open, artists will be able to join through PlotArt's Artist Register page."
NEW_S8_SENTENCE = "Artists can join through PlotArt's Artist Register page while registrations are open."
AMENDMENT = {
    "s8_open_wording": "Colin MacAulay, founder, 14 October 2026 (20:33): approves the Section 8 amendment "
                       "\"Artists can join through PlotArt's Artist Register page while registrations are open.\" "
                       "V5 retained; editorial amendment only; all existing privacy commitments preserved.",
}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pv4():
    return _load("build_privacy_v4", ROOT / "atlas-tools" / "build-privacy-v4.py")


def refuse(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


# ------------------------------------------------------------ governed text
HEAD_OLD = "    <h2>8. The Art Space Register</h2>\n"
HEAD_NEW = "    <h2>8. The Art Space Register and the Artist Register</h2>\n"
INTRO = ("PlotNua keeps two separate registers for the A Home for Art idea: the Art Space Register, for homeowners "
         "who might offer space for artists' finished work, and the Artist Register, for artists who might be "
         "interested in that kind of space. They are separate lists with separate forms and separate consent. "
         "Joining one does not add you to the other, and neither register is shared with the people on the other.")
SUB_HOMES = "The Art Space Register (homeowners)"
SUB_ARTISTS = "The Artist Register (artists)"
ARTIST = [
    ("p", "The Artist Register is a list, kept privately by PlotNua, of artists who might be interested in "
          "displaying, showing, installing or storing their work in homes and gardens in Ireland, or in reaching "
          "potential buyers through a home setting. Artists can join through PlotArt's Artist Register page while "
          "registrations are open. Joining is "
          "voluntary and free, and it does not commit you to anything."),
    ("p", "PlotArt is in development. There is no matching service at present. PlotNua is not introducing artists "
          "to homeowners, there is no exhibition, booking or sales service, no payment is offered, and registering "
          "does not guarantee an opportunity of any kind."),
    ("p", "What we collect when you join:"),
    ("ul", ["the name you work under;",
            "your email address;",
            "the county where you are based, or that you are based outside Ireland;",
            "where you would consider opportunities and, if you choose to tell us, which counties or regions;",
            "what you make and which opportunities interest you;",
            "if you choose to tell us: the space your work needs, a link to your website or portfolio, and a short "
            "statement about your work; and",
            "a record that you gave your consent, which version of this notice applied, and when you joined."]),
    ("p", "We do not collect your home address, your phone number, your date of birth, photographs of your work, "
          "prices or details of your sales."),
    ("p", "We use this information to contact you about the development of PlotArt and about potential "
          "opportunities to connect with homeowners, for example to ask what would be useful to you or to let you "
          "know if the idea develops. We rely on your consent, which you give by ticking the box when you join."),
    ("p", "Your registration is stored privately. It is not published: there is no public artist profile, listing, "
          "map or directory. Registration details are accessible only to authorised people managing the register "
          "and to service providers where necessary to operate it. Your details are not shared with homeowners, "
          "automatically or otherwise. If a possible opportunity ever arose, we would contact you first, and your "
          "details would only be shared with a homeowner if you agreed to that specific arrangement. No such "
          "arrangements are available at present."),
    ("p", "Artist registrations are kept in the same database as the Art Space Register but in a separate table, "
          "and are sent and stored by the same service providers, in the same way, as described above for the Art "
          "Space Register."),
    ("p", "We keep your registration for no longer than 12 months, and we delete it sooner if it is no longer "
          "needed."),
    ("p", "You can withdraw your consent, or ask us to delete your registration, at any time by emailing "
          "<a href=\"mailto:hello@plotnua.ie\">hello@plotnua.ie</a>. There is nothing to cancel and no notice "
          "period. When we delete your registration, we delete everything the Artist Register holds about you, "
          "including the record of your consent, and the same arrangements for our database provider's trash and "
          "recovery copies, and for our anonymous deletion log, apply as described above for the Art Space "
          "Register."),
]
SEC2_ANCHOR = "    <p>If you choose to join the Art Space Register, we also collect the information described in Section 8.</p>\n"
SEC2_NEW = "    <p>If you choose to join the Artist Register, we also collect the information described in Section 8.</p>\n"
THIRD_ANCHOR = ("    <p>The Art Space Register described in Section 8 also runs on a PlotNua service hosted on "
                "infrastructure provided by Cloudflare, and its records are stored in Airtable in a database kept "
                "separate from the Garden Owner Register.</p>\n")
# Founder correction, 14 Oct 2026 (19:39): Section 10 names the shared infrastructure, with separate records.
THIRD_NEW = ("    <p>The Artist Register described in Section 8 uses the same PlotNua service on infrastructure "
             "provided by Cloudflare, and the same Airtable database, as the Art Space Register, with artist "
             "registrations kept as separate records in their own table.</p>\n")
RET_ANCHOR = "    <p>Art Space Register records are kept for a maximum of 12 months, as described in Section 8.</p>\n"
RET_NEW = "    <p>Artist Register records are kept for a maximum of 12 months, as described in Section 8.</p>\n"
CSS_ANCHOR = "</style>\n</head>"
CSS_NEW = ("/* PLOTNUA PRIVACY V5 · the two Section 8 sub-headings (generated by atlas-tools/build-privacy-v5.py) */\n"
           ".article-section h3.pv5-sub{ font-size:clamp(19px,2.2vw,23px); line-height:1.35; margin:44px 0 18px; }\n"
           ".article-section h2 + p + h3.pv5-sub{ margin-top:36px; }\n")
REQUIREMENTS = {   # W3: the founder's nine requirements, 14 Oct 2026 (19:25)
    "purpose": "of artists who might be interested in displaying, showing, installing or storing their work",
    "private storage": "Your registration is stored privately",
    "no current matching": "There is no matching service at present",
    "no automatic sharing": "Your details are not shared with homeowners, automatically or otherwise",
    "no public profiles": "there is no public artist profile, listing, map or directory",
    "12-month retention": "no longer than 12 months",
    "withdraw consent": "You can withdraw your consent",
    "request deletion": "ask us to delete your registration, at any time by emailing hello@plotnua.ie",
    "artist/homeowner distinction": "They are separate lists with separate forms and separate consent",
}


def plain(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s).replace("’", "'").replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip()


def sections(src):
    return [(int(n), t) for n, t in re.findall(r"<h2>(\d+)\. ([^<]+)</h2>", src)]


def intro_html():
    return (MARK + "    <p>%s</p>\n" % INTRO +
            '    <h3 class="pv5-sub">%s</h3>\n' % SUB_HOMES)


def artist_html():
    out = ['    <h3 class="pv5-sub">%s</h3>' % SUB_ARTISTS]
    for kind, body in ARTIST:
        if kind == "p":
            out.append("    <p>%s</p>" % body)
        else:
            out.append("    <ul>")
            out += ["      <li>%s</li>" % li for li in body]
            out.append("    </ul>")
    return "\n".join(out) + "\n"


def section8(src):
    m = re.search(r'  <section class="article-section reveal" id="art-space-register">\n[\s\S]*?\n  </section>\n', src)
    return m.group(0) if m else None


def transform(v4, last_updated=None):
    """Published V4 privacy.html -> V5. Pure: no file is read or written."""
    P4 = pv4()
    if "PLOTNUA-ARTIST-PRIVACY-V5" in v4:
        refuse("privacy.html already carries V5")
    if not P4.published_exact(v4):
        refuse("the input is not exactly the published V4 page (the V4 builder's full published check fails)")
    s8 = section8(v4)
    if not s8 or v4.count(s8) != 1 or s8.count(HEAD_OLD) != 1:
        refuse("V4 Section 8 not found exactly once")
    new8 = s8.replace(HEAD_OLD, HEAD_NEW + intro_html(), 1)
    new8 = new8[:-len("  </section>\n")] + artist_html() + "  </section>\n"
    out = v4.replace(s8, new8, 1)
    for anchor, new, lab in ((SEC2_ANCHOR, SEC2_NEW, "Section 2 anchor"), (THIRD_ANCHOR, THIRD_NEW, "Section 10 anchor"),
                             (RET_ANCHOR, RET_NEW, "retention anchor")):
        if out.count(anchor) != 1:
            refuse(lab + " not found exactly once")
        out = out.replace(anchor, anchor + new, 1)
    if out.count(CSS_ANCHOR) != 1:
        refuse("style anchor not found exactly once")
    out = out.replace(CSS_ANCHOR, CSS_NEW + CSS_ANCHOR, 1)
    if last_updated:
        m = P4.UPDATED_RE.search(out)
        if not m:
            refuse("the Last updated line is missing")
        out = out.replace(m.group(0), '<p class="policy-updated">Last updated: %s</p>' % last_updated, 1)
    return out


def untransform(v5):
    """Remove exactly the declared V5 changes (W7). The Last updated label is
    the caller's to restore."""
    s = v5.replace(HEAD_NEW + intro_html(), HEAD_OLD, 1)
    s = s.replace(artist_html() + "  </section>\n", "  </section>\n", 1)
    s = s.replace(SEC2_NEW, "", 1).replace(THIRD_NEW, "", 1).replace(RET_NEW, "", 1).replace(CSS_NEW, "", 1)
    return s


def published(text=None):
    text = PRIVACY.read_text(encoding="utf-8") if text is None else text
    return "PLOTNUA-ARTIST-PRIVACY-V5" in text


def published_ok(text=None):
    """True when the text carries exactly the governed V5 changes over a page
    the V4 builder accepts (used by the register guards once V5 is live)."""
    text = PRIVACY.read_text(encoding="utf-8") if text is None else text
    if text.count(MARK) != 1 or (HEAD_NEW + intro_html()) not in text or artist_html() not in text \
            or SEC2_NEW not in text or THIRD_NEW not in text or RET_NEW not in text:
        return False
    return pv4().published_exact(text)


def toml(key, path=ART_WRANGLER):
    m = re.search(r'^%s\s*=\s*"([^"]*)"' % key, path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def governed():
    return [plain(g) for g in re.findall(r"^> (.+)$", DRAFT.read_text(encoding="utf-8"), re.M)]


def guards(v4, v5):
    P4 = pv4()
    s8 = section8(v5)
    if not s8:
        refuse("W6 Section 8 missing")
    s8t, page = plain(s8), plain(v5)
    gov = governed()
    # W1 both ways
    pieces = [plain(HEAD_NEW), INTRO, SUB_HOMES, SUB_ARTISTS, plain(SEC2_NEW), plain(THIRD_NEW), plain(RET_NEW)]
    if v5.count(THIRD_NEW) != 1 or v5.index(THIRD_ANCHOR) > v5.index(THIRD_NEW) \
            or v5.index(THIRD_NEW) > v5.index("<h2>11. "):
        refuse("W6 Section 10 does not carry the Artist Register infrastructure sentence once, after the Art Space Register one")
    if "Artists can join through PlotArt's Artist Register page while registrations are open." not in s8t \
            or OLD_S8_SENTENCE in s8t:
        refuse("W3 Section 8 must say artists can join while registrations are open (founder amendment, 14 Oct 2026)")
    for kind, body in ARTIST:
        pieces += [plain(x) for x in ([body] if kind == "p" else body)]
    for p in pieces:
        if plain(p) not in gov:
            refuse("W1 builder text is not a governed line of the V5 draft: " + plain(p)[:70])
    for g in gov:
        if g not in page:
            refuse("W1 a governed V5 line is not on the page: " + g[:70])
    # W2 / W7
    back = untransform(v5)
    m4, mb = P4.UPDATED_RE.search(v4), P4.UPDATED_RE.search(back)
    if m4 and mb:
        back = back.replace(mb.group(0), m4.group(0), 1)
    if back != v4:
        refuse("W7 something other than the declared V5 changes differs")
    if not P4.published_exact(back):
        refuse("W2 the V4 notice inside V5 no longer passes the V4 builder's full published check")
    # W3
    for label, need in REQUIREMENTS.items():
        if plain(need) not in s8t:
            refuse("W3 requirement not stated: %s" % label)
    # W4
    src = ART_WORKER.read_text(encoding="utf-8")
    wc = re.search(r'const ARTIST_CONSENT_TEXT =\s*"([^"]*)";', src)
    ab = _load("build_artist_register", ARTIST_BUILDER)
    if not wc or wc.group(1) != ab.CONSENT or ab.CONSENT not in DRAFT.read_text(encoding="utf-8"):
        refuse("W4 the artist consent sentence differs between the Worker, the artist page builder and the V5 draft")
    keys = set(re.findall(r"'([a-z_0-9]+)'", re.search(r"const ARTIST_ALLOWED_KEYS = Object\.freeze\(\[([\s\S]*?)\]\)",
                                                         src).group(1)))
    described = {"artist_name", "email", "based_in", "reach", "reach_places", "disciplines", "interests", "needs",
                 "portfolio", "statement", "over_18", "consent_text"}
    if keys != described:
        refuse("W4 the Worker's ARTIST_ALLOWED_KEYS no longer match the fields this section describes: %r" % sorted(keys))
    if toml("ARTIST_PRIVACY_VERSION") != VERSION:
        refuse("W4 the Worker's ARTIST_PRIVACY_VERSION is not %s" % VERSION)
    if toml("ARTIST_WRITES_ENABLED") != "true" and getattr(ab, "ARTIST_PUBLIC", False):
        refuse("W4 the artist page is public but the artist route is closed")
    if toml("PRIVACY_VERSION", GARDEN_WRANGLER) != "2026-10-PHASE2-V3":
        refuse("W4 the Garden Worker must stay on 2026-10-PHASE2-V3")
    # W5
    if re.search(r"\b(fully compliant|GDPR[- ]compliant|we guarantee|guaranteed (match|opportunit\w+|exhibition)|"
                 r"we will match|you will be matched|certified secure|you will be paid|earn)\b", page, re.I):
        refuse("W5 an invented assurance or promise is on the page")
    if "registering does not guarantee an opportunity of any kind" not in s8t:
        refuse("W5 the no-guarantee wording is missing")
    # W6
    if [n for n, _ in sections(v5)] != list(range(1, 19)):
        refuse("W6 sections not numbered 1..18")
    titles = dict(sections(v5))
    if titles[7] != "The Garden Owner Register" or titles[8] != "The Art Space Register and the Artist Register":
        refuse("W6 Sections 7 and 8 are not Garden then both art registers")
    if P4.garden7(v5) != P4.garden7(v4):
        refuse("W6 Section 7 changed")
    if s8t.index(plain(SUB_HOMES)) > s8t.index("The Open Your Home to Art Property Check is private") or \
            s8t.index(plain(SUB_ARTISTS)) < s8t.index("That entry contains nothing that identifies you"):
        refuse("W6 Section 8 is not introduction, homeowner text, then artist text")


def approved():
    return isinstance(APPROVAL, dict) and all(isinstance(APPROVAL.get(k), str) and APPROVAL[k].strip()
                                              for k in APPROVAL_KEYS)


def main(argv):
    cur = PRIVACY.read_text(encoding="utf-8")
    if "--amend-s8" in argv:
        if not AMENDMENT.get("s8_open_wording", "").strip():
            refuse("the Section 8 amendment is not approved")
        if not published(cur):
            refuse("V5 is not published; there is nothing to amend")
        if cur.count(NEW_S8_SENTENCE) == 1 and OLD_S8_SENTENCE not in cur:
            print("privacy.html: Section 8 amendment already applied")
        elif cur.count(OLD_S8_SENTENCE) != 1 or NEW_S8_SENTENCE in cur:
            refuse("the Section 8 sentence to amend is not found exactly once")
        else:
            cur = cur.replace(OLD_S8_SENTENCE, NEW_S8_SENTENCE, 1)
            if not published_ok(cur):
                refuse("the amended page does not carry exactly the governed V5 text")
            PRIVACY.write_text(cur, encoding="utf-8")
            print("privacy.html: Section 8 amendment APPLIED (V5 retained)")
        argv = ["--check"]
    if "--apply" in argv:
        if not approved():
            refuse("V5 is NOT APPROVED for publication: APPROVAL must record the founder's approval of the exact "
                   "wording, the dated self-assessment addendum, the resolution of material risks and the Last "
                   "updated label")
        v5 = transform(cur, APPROVAL["last_updated"])
        guards(cur, v5)
        wr = ART_WRANGLER.read_text(encoding="utf-8")
        old = 'PRIVACY_VERSION = "%s"' % V4_VERSION
        if len(re.findall(r'^PRIVACY_VERSION\s*=\s*"%s"' % V4_VERSION, wr, re.M)) != 1:
            refuse("the homeowner Worker's PRIVACY_VERSION is not the single V4 line expected")
        wr = re.sub(r'^PRIVACY_VERSION\s*=\s*"%s"' % V4_VERSION, 'PRIVACY_VERSION = "%s"' % VERSION, wr, count=1, flags=re.M)
        PRIVACY.write_text(v5, encoding="utf-8")
        ART_WRANGLER.write_text(wr, encoding="utf-8")
        print("privacy.html: V5 APPLIED · homeowner Worker PRIVACY_VERSION -> %s (takes effect on deploy, AFTER "
              "the page is live)" % VERSION)
        return
    if published(cur):
        if "--preview" in argv:
            refuse("V5 is already published; there is nothing to preview")
        if not approved():
            refuse("privacy.html carries V5 but APPROVAL does not record its approval")
        if not published_ok(cur):
            refuse("the published V5 changes differ from the governed text")
        v4 = untransform(cur)
        m = pv4().UPDATED_RE.search(cur)
        if not m or m.group(1) != APPROVAL["last_updated"]:
            refuse("the published Last updated label is not the approved one")
        m4 = pv4().UPDATED_RE.search(v4)
        v4 = v4.replace(m4.group(0), '<p class="policy-updated">Last updated: %s</p>'
                        % pv4().APPROVAL["last_updated"], 1)
        if transform(v4, APPROVAL["last_updated"]) != cur:
            refuse("W7 the published page is not exactly the governed V5 transform of V4")
        guards(v4, cur)
        if toml("PRIVACY_VERSION") != VERSION:
            refuse("W4 V5 is published but the homeowner Worker still records %s" % toml("PRIVACY_VERSION"))
        print("privacy.html: V5 PUBLISHED · matches the governed text · W1-W7 pass")
        return
    v5 = transform(cur)
    guards(cur, v5)
    if toml("PRIVACY_VERSION") != V4_VERSION:
        refuse("W4 V5 is not published, so the homeowner Worker must still record %s" % V4_VERSION)
    if "--preview" in argv:
        i = argv.index("--preview")
        if i + 1 >= len(argv):
            refuse("--preview needs a path")
        out = pathlib.Path(argv[i + 1]).resolve()
        if ROOT in out.parents or out == ROOT:
            refuse("--preview path is inside the repository; every file there is published by GitHub Pages")
        out.write_text(v5, encoding="utf-8")
        print("privacy V5 preview written to %s (privacy.html unchanged)" % out)
        return
    print("privacy.html: V4 live · V5 UNPUBLISHED · dry run builds cleanly — W1-W7 pass · nothing written")


if __name__ == "__main__":
    main(sys.argv[1:])
