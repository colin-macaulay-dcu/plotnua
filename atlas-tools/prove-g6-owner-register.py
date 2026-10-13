#!/usr/bin/env python3
"""
G6 PREPARATION · GARDEN OWNER REGISTER — PRIVACY GUARDS + CAPABILITY PROOF
===============================================================================
Part A  PRIVACY GUARDS. Asserts the published privacy.html says what the
        founder approved on 12 October 2026, and does not say what it must
        not (no stored result, no legal-assurance language, no match claim).
Part B  PRIVACY GUARD CAPABILITY. Breaks privacy.html one way at a time in a
        temporary copy; the OWNING guard must fail.
Part C  BUILDER CAPABILITY. Breaks one precondition of
        build-g6-owner-register.py at a time against the PRE-BUILD files read
        from git; the builder must REFUSE and write nothing.
Verdicts: CAPABLE / BLIND / VACUOUS (mutation did not apply) / MISATTRIBUTED.

  python3 atlas-tools/prove-g6-owner-register.py
"""
import html as htmlmod, importlib.util, io, pathlib, re, shutil, subprocess, sys, tempfile
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
# Re-pinned 12 October 2026 (Commit A) from 9a0c517, a commit that existed
# only on the founder's machine, to c64e63a, which is on GitHub main. The
# three input files are byte-identical at both (same git blob ids:
# disc025 1665871d, privacy.html 80b04149, wrangler.toml 9de56898), so the
# proof is unchanged in meaning and now runs in any clean clone.
PRE_REF = "c64e63a"

PASS = FAIL = 0


def say(ok, label, detail=""):
    global PASS, FAIL
    PASS += ok; FAIL += (not ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"   {detail}" if detail and not ok else ""))


def text_of(section_html):
    t = re.sub(r"<[^>]+>", " ", section_html)
    return re.sub(r"\s+", " ", htmlmod.unescape(t)).strip()


def section7(src):
    m = re.search(r"<h2>7\. The Garden Owner Register</h2>(.*?)</section>", src, re.S)
    return text_of(m.group(1)) if m else ""


# ------------------------------------------------------------ the guards --
def guards(src):
    """Returns {id: bool}. Each id OWNS one proposition."""
    s7 = section7(src)
    whole = text_of(src)
    g = {}
    g["PV1"] = bool(s7) and len(s7) > 400                       # section exists, non-trivial
    g["PV2"] = "Matching is not live" in s7 and "does not arrange an introduction" in s7
    g["PV3"] = all(x in s7 for x in ("your first name;", "your email address;",
                                      "the area you choose from a short list;"))
    g["PV4"] = ("whether you own the home, rent it or are buying it, carried over from your "
                "Property Check answer") in s7
    g["PV5"] = ("Your other Property Check answers and your Property Check result are not "
                "sent to the register.") in s7 and "result the Property Check produced" not in whole
    g["PV6"] = ("We do not collect your address, your Eircode, your phone number, your surname, "
                "your age, photographs of your garden, or anything about your health.") in s7
    g["PV7"] = "We rely on your consent" in s7 and "withdraw it at any time" in s7
    g["PV8"] = "Records are reviewed by a person at PlotNua." in s7 and "no public listing" in s7
    g["PV9"] = ("Cloudflare" in s7 and "Airtable" in s7 and "outside the European Economic Area" in s7
                and "Standard Contractual Clauses" in s7)
    g["PV10"] = "maximum of 24 months" in s7
    # Strengthened after its capability case came back BLIND: the email
    # address alone also appears elsewhere, so removing the deletion
    # instruction left the old check passing. It now owns the instruction.
    g["PV11"] = ("To leave the register or ask us to delete your record, email hello@plotnua.ie" in s7
                 and "one-way digital fingerprint" in s7)
    g["PV12"] = ("Airtable, a database service that holds records kept by PlotNua's own services, "
                 "including the Garden Owner Register;") in whole
    g["PV13"] = "Garden Owner Register records are kept for a maximum of 24 months" in whole
    g["PV14"] = [int(n) for n in re.findall(r"<h2>(\d+)\. ", src)] == list(range(1, 19))  # 18 since privacy V4
    # no invented legal assurance and no match promise, ranged over the WHOLE page
    # AFFIRMATIVE forms only. The first version matched any "guarantee", and
    # the unmutated control failed on the pre-existing Section 12 disclaimer
    # "can be guaranteed to be completely secure" — a negation, not an
    # assurance. Narrowed to what would actually be an invented assurance.
    g["PV15"] = not re.search(r"\b(fully compliant|GDPR[- ]compliant|we guarantee|guaranteed match|"
                              r"we will match|you will be matched|certified secure)\b", whole, re.I)
    g["PV16"] = "to understand where garden space might be available" not in whole
    return g


# --------------------------------------------------------------- Part A ---
print("\n  G6 PREP · PRIVACY GUARDS\n")
LIVE = (ROOT / "privacy.html").read_text(encoding="utf-8")
for k, v in guards(LIVE).items():
    say(v, f"{k} holds on privacy.html")

# --------------------------------------------------------------- Part B ---
print("\n  G6 PREP · PRIVACY GUARD CAPABILITY\n")
MUTS = [
    ("PV2", "matching claimed to be live", "Matching is not live, and", "Matching is live, and"),
    ("PV4", "tenure disclosure dropped", ", carried over from your Property Check answer", ""),
    ("PV5", "the result said to be stored",
     "Your other Property Check answers and your Property Check result are not sent to the register.",
     "We also keep the result the Property Check produced from those answers."),
    ("PV6", "Eircode removed from the never-collect list", "your address, your Eircode, your phone",
     "your address, your phone"),
    ("PV7", "legal basis removed", "We rely on your consent", "We process this"),
    ("PV9", "transfer sentence removed", "so your information may be processed outside the European Economic Area",
     "so your information stays in Ireland"),
    ("PV10", "retention lengthened", "We keep your record for a maximum of 24 months.",
     "We keep your record for a maximum of 36 months."),
    ("PV11", "deletion route removed", "To leave the register or ask us to delete your record, email",
     "To leave the register, write to"),
    ("PV12", "Airtable dropped from the third-party list",
     "      <li>Airtable, a database service that holds records kept by PlotNua's own services, including the Garden Owner Register;</li>\n", ""),
    ("PV14", "a section number left stale", "<h2>10. Third-Party Services and Links</h2>",
     "<h2>9. Third-Party Services and Links</h2>"),
    ("PV15", "a legal assurance invented", "Visitors should refer to Cloudflare's",
     "PlotNua is fully compliant with GDPR. Visitors should refer to Cloudflare's"),
    ("PV16", "an un-consented research purpose added", "looking for growing space. We rely",
     "looking for growing space, and to understand where garden space might be available. We rely"),
]
base = guards(LIVE)
if not all(base.values()):
    print("  [ABORT] privacy guards do not pass unmutated"); sys.exit(1)
for gid, name, old, new in MUTS:
    g7 = re.search(r"<h2>7\. The Garden Owner Register</h2>[\s\S]*?</section>", LIVE).group(0)
    if g7.count(old) == 1:   # since privacy V4, Section 8 repeats some Section 7 sentences
        mutated = LIVE.replace(g7, g7.replace(old, new), 1)
    else:
        n = LIVE.count(old)
        if n != 1:
            say(False, f"[VACUOUS] {gid} {name}", f"anchor found {n} times"); continue
        mutated = LIVE.replace(old, new)
    got = guards(mutated)
    failed = [k for k, v in got.items() if not v]
    if not failed:
        say(False, f"[BLIND] {gid} {name}")
    elif gid not in failed:
        say(False, f"[MISATTRIBUTED] {gid} {name}", ",".join(failed))
    else:
        extra = [f for f in failed if f != gid]
        say(True, f"[CAPABLE] {gid} {name}" + (f"  (also {','.join(extra)})" if extra else ""))

# --------------------------------------------------------------- Part C ---
print("\n  G6 PREP · BUILDER CAPABILITY (against the pre-build files from git)\n")


def git_show(rel):
    return subprocess.run(["git", "show", f"{PRE_REF}:{rel}"], cwd=ROOT, check=True,
                          capture_output=True).stdout.decode("utf-8")


PRE = {"page": git_show("disc025-borrowed-garden-check.html"),
       "privacy": git_show("privacy.html"),
       "wrangler": git_show("worker/garden-register/wrangler.toml")}


def builder():
    spec = importlib.util.spec_from_file_location("g6b", HERE / "build-g6-owner-register.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def run_case(label, mutate_files=None, mutate_mod=None, expect_refusal=True):
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="g6b-"))
    try:
        files = dict(PRE)
        if mutate_files:
            files = mutate_files(files)
            if files is None:
                say(False, f"[VACUOUS] {label}", "mutation did not apply"); return
        paths = {}
        for k, name in (("page", "page.html"), ("privacy", "privacy.html"), ("wrangler", "wrangler.toml")):
            paths[k] = tmpdir / name; paths[k].write_text(files[k], encoding="utf-8")
        m = builder()
        m.TARGET, m.PRIVACY, m.WRANGLER, m.ROOT = paths["page"], paths["privacy"], paths["wrangler"], tmpdir
        if mutate_mod:
            if mutate_mod(m) is False:
                say(False, f"[VACUOUS] {label}", "module mutation did not apply"); return
        before = {k: p.read_bytes() for k, p in paths.items()}
        buf = io.StringIO(); code = 0; old = sys.argv
        sys.argv = ["b", "--apply"]
        try:
            with redirect_stdout(buf): m.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        finally:
            sys.argv = old
        out = buf.getvalue()
        after = {k: p.read_bytes() for k, p in paths.items()}
        refused = code != 0 and "REFUSED" in out
        if expect_refusal:
            ok = refused and before == after
            say(ok, f"[{'CAPABLE' if ok else 'BLIND'}] {label}",
                out.strip().splitlines()[-1] if out.strip() else "")
        else:
            ok = code == 0 and "APPLIED" in out
            say(ok, f"[CONTROL] {label}", out.strip()[-160:])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def edit(key, old, new, count=1):
    def f(files):
        if files[key].count(old) != count: return None
        files = dict(files); files[key] = files[key].replace(old, new); return files
    return f


def modset(attr, old, new):
    def f(m):
        v = getattr(m, attr)
        if v.count(old) != 1: return False
        setattr(m, attr, v.replace(old, new))
    return f


run_case("C0 control: the unmutated pre-build files apply cleanly", expect_refusal=False)
run_case("C1 offer anchor missing", edit("page", "If somebody nearby needed a corner", "If somebody nearby wanted a corner"))
# C2 duplicates the WHOLE P1 anchor. The first version copied only its
# opening lines, so the full anchor still occurred once and the builder rightly
# applied — the harness was blind, not the builder.
run_case("C2 offer anchor duplicated",
         edit("page", "    <!-- PLOTNUA-G3-HTML-END -->",
              "    <!-- PLOTNUA-G3-HTML-END -->\n<!--\n" + builder().P1_OLD + "\n-->"))
run_case("C3 builder already applied (marker present)", edit("page", "<head>", "<head><!-- PLOTNUA-G6-PREP-2026-10-12 -->"))
run_case("C4 INTEREST_PUBLIC already true before the build",
         edit("page", "var INTEREST_PUBLIC = false;", "var INTEREST_PUBLIC = true;"))
run_case("C5 the payload rewrite would still send the result key",
         mutate_mod=modset("P3_NEW", "      inherited_tenure: answers.tenure || ''\n",
                           "      inherited_tenure: answers.tenure || '',\n      inherited_result_key: 'X'\n"))
run_case("C6 the payload rewrite would drop tenure",
         mutate_mod=modset("P3_NEW", "      inherited_tenure: answers.tenure || ''\n", ""))
run_case("C7 a replacement would flip INTEREST_PUBLIC",
         mutate_mod=modset("P6_NEW", "If this page ever", "If this page ever\n  var INTEREST_PUBLIC = true;"))
run_case("C8 a replacement would alter the consent sentence",
         mutate_mod=modset("P4_JS_NEW", "    intShow('sending');\n",
                           "    intShow('sending');\n    \"I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.\";\n"))
def escape_engine(m):
    """Repoint one replacement at a line of the frozen ENGINE, outside every
    G3 region. Only the region-mask gate can stop this."""
    eng = "  { id: 'tenure',       values: ['own', 'rent', 'buying'] },"
    if PRE["page"].count(eng) != 1: return False
    m.P6_OLD, m.P6_NEW = eng, eng.replace("'buying'", "'buying', 'other'")


run_case("C9 a change escapes the three G3 regions (engine touched)", mutate_mod=escape_engine)
run_case("C10 the honeypot leaks into the payload",
         mutate_mod=modset("P3_NEW", "      inherited_tenure: answers.tenure || ''\n",
                           "      inherited_tenure: answers.tenure || '',\n      website: $('bgIntWebsite').value\n"))
run_case("C11 privacy section anchor missing",
         edit("privacy", "<p>Your name, email address and location are not saved to My Plot", "<p>Your name and email address are not saved to My Plot"))
run_case("C12 privacy numbering would come out wrong",
         edit("privacy", "<h2>16. Contact</h2>", "<h2>16. Contact us</h2>"))
run_case("C13 a wrangler switch line differs",
         edit("wrangler", 'WRITES_ENABLED  = "false"', 'WRITES_ENABLED  = "true"'))
run_case("C14 privacy version already moved", edit("wrangler", '"2026-10-PHASE2-V2"', '"2026-10-PHASE2-V9"'))

print(f"\n  {PASS} passed, {FAIL} failed\n")
sys.exit(1 if FAIL else 0)
