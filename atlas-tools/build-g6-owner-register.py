#!/usr/bin/env python3
"""
G6 PREPARATION · GARDEN OWNER REGISTER — BOUNDED BUILDER
===============================================================================
Founder decisions of 12 October 2026 (Route A; D2 option ii; D3; D4; D5).

Applies, and only applies:
  disc025-borrowed-garden-check.html
    P1  the G3 offer re-worded (heading, four statements, out-of-area line, CTA)
    P2  the inline notice's "What we keep" paragraph -> privacy V3 (D2)
    P3  intPayload() trimmed to tenure only (D2)
    P4  a page-only honeypot field (D4), HTML + CSS + submit check
    P5  the out-of-pilot confirmation line re-worded (D3)
    P6  one stale comment naming privacy V2
  privacy.html
    Q1-Q6  the Garden Owner Register section, Airtable / Cloudflare, retention,
           renumbering, last-updated
  worker/garden-register/wrangler.toml
    W1  PRIVACY_VERSION -> 2026-10-PHASE2-V3   (takes effect only on deploy)

It does NOT touch: INTEREST_PUBLIC, WRITES_ENABLED, EMAIL_ENABLED, the consent
sentence, the Worker source, the engine, the questions or the result copy.
Every replacement is an exact anchor asserted to occur exactly once, and the
post-gates prove the switches, the consent sentence, and that every changed
byte of the journey page lies inside the three G3 marker regions.

  python3 atlas-tools/build-g6-owner-register.py --check   # dry run
  python3 atlas-tools/build-g6-owner-register.py --apply
"""
import hashlib, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "disc025-borrowed-garden-check.html"
PRIVACY = ROOT / "privacy.html"
WRANGLER = ROOT / "worker" / "garden-register" / "wrangler.toml"
MARK = "PLOTNUA-G6-PREP-2026-10-12"

CONSENT_LINE = ('    "I\'m over 18, and I\'d like PlotNua to keep this and tell me if '
                'someone nearby is looking for growing space.";')


def refuse(msg):
    print("REFUSED: " + msg)
    sys.exit(2)


def sub(src, old, new, label):
    n = src.count(old)
    if n != 1:
        refuse(f"{label}: anchor expected once, found {n}")
    return src.replace(old, new)


# ------------------------------------------------------------------ page ---
P1_OLD = """      <h2 class="bg-int-h" id="bgIntH">If somebody nearby needed a corner, would you
        want to know?</h2>

      <div id="bgIntOffer">
        <p class="bg-int-p">Tell us about the part you have in mind. If somebody
          nearby is looking for growing space, we&rsquo;ll email you and ask first.</p>
        <p class="bg-int-p">Nobody else sees your details. There is no public listing,
          no map and no profile page. Nothing is shared with anybody until you say yes
          to one specific introduction.</p>
        <p class="bg-int-cta">
          <button class="pc-cta" type="button" id="bgIntOpen">Yes &mdash; let me know</button>
        </p>
        <p class="bg-int-caveat">This is a register, not a match.
          We may never find anybody near you.</p>
      </div>"""

P1_NEW = """      <h2 class="bg-int-h" id="bgIntH">Could you see yourself sharing part of
        your garden?</h2>

      <!-- """ + MARK + """ · D3 offer wording, founder-approved 12 October 2026.
           Every proposition the G6 guards protect is still stated: not a
           match, may never find anybody, no public listing, nothing shared
           until a yes. -->
      <div id="bgIntOffer">
        <p class="bg-int-p">PlotNua is exploring a small pilot that would introduce
          homeowners with a spare corner to people nearby who&rsquo;d like somewhere
          to grow. We&rsquo;re starting in Raheny, Killester, Donnycarney and Artane.</p>
        <ul class="bg-int-list">
          <li><strong>Matching isn&rsquo;t live yet.</strong> Joining the register
            doesn&rsquo;t arrange anything.</li>
          <li><strong>There&rsquo;s no obligation.</strong> Registering interest
            commits you to nothing, and you can come off the register at any time.</li>
          <li><strong>We can&rsquo;t promise an introduction.</strong> We may never
            find anybody near you.</li>
          <li><strong>You stay in control.</strong> Nobody else sees your details.
            There is no public listing, no map and no profile page. Nothing is shared
            with anybody until you say yes to one specific introduction.</li>
        </ul>
        <p class="bg-int-p">If you live somewhere else, you&rsquo;re still welcome to
          tell us. Your interest goes on the register, but we aren&rsquo;t looking for
          anyone to introduce outside those four areas.</p>
        <p class="bg-int-cta">
          <button class="pc-cta" type="button" id="bgIntOpen">I&rsquo;m interested in offering garden space</button>
        </p>
        <p class="bg-int-caveat">This is a register, not a match.</p>
      </div>"""

P2_OLD = """            <p><strong>What we keep about you and your garden.</strong> Your first
              name, your email address, the district you chose, and what you told the
              Property Check about your garden &mdash; its size band, water, how
              someone would get in, and whether you own the property &mdash; and the
              result the Property Check produced from those answers. We also keep
              the administrative records needed to manage your registration, your
              consent and its status.</p>"""

P2_NEW = """            <p><strong>What we keep about you and your garden.</strong> Your first
              name, your email address, the district you chose, and what you tell us
              here about the space &mdash; roughly how big it is, whether there is
              water, roughly when, and anything you add in the note. From your
              Property Check we keep one answer only: whether you own the home, rent
              it or are buying it, because if you rent, the owner would have to agree
              before anything could happen. Your other Property Check answers and its
              result are not sent to us. We also keep the administrative records
              needed to manage your registration, your consent and its status.</p>"""

P3_OLD = """      /* INHERITED FROM THE PROPERTY CHECK, not re-asked. These are the four
         answers the homeowner already gave this page. inherited_tenure is the
         one the Worker requires; the other three are context the register is
         allowed to hold. */
      inherited_tenure: answers.tenure || '',
      inherited_spare_corner: answers.spare_corner || '',
      inherited_way_in: answers.way_in || '',
      inherited_your_own_use: answers.your_own_use || ''
    };
    var note = $('bgIntNote').value;
    if (note) body.garden_note = note;
    if (answers.tenure === 'rent') {
      body.permission_confirmed = $('bgIntPerm').checked === true;
    }
    /* The result KEY, never the result prose — the same rule the save
       component applies, and for the same reason: a stored paragraph would
       keep asserting something PlotNua may have stopped standing over. */
    if (lastEval) {
      var k = (lastEval.kind === 'early_exit')
        ? lastEval.exit.headline
        : (lastEval.results && lastEval.results[0] ? lastEval.results[0].key : '');
      if (k) body.inherited_result_key = k;
    }
    return body;"""

P3_NEW = """      /* D2 · DATA MINIMISATION, founder decision 12 October 2026, option (ii).
         ONE answer is inherited from the Property Check: tenure. It is the
         input to the G1B §5 renter-permission safeguard, and the deployed
         Worker refuses a garden submission without it, so it is sent on every
         submission — an owner's 'own' is what tells the Worker no permission
         is needed. The other Property Check answers and the result key are
         NOT sent. The Worker still accepts them as optional fields; the page
         simply never supplies them. Privacy notice 2026-10-PHASE2-V3. */
      inherited_tenure: answers.tenure || ''
    };
    var note = $('bgIntNote').value;
    if (note) body.garden_note = note;
    if (answers.tenure === 'rent') {
      body.permission_confirmed = $('bgIntPerm').checked === true;
    }
    return body;"""

P4_HTML_OLD = "        <!-- The canonical consent control. ONE tick."
P4_HTML_NEW = """        <!-- D4 · PAGE-ONLY HONEYPOT. Off-screen, out of the tab order and
             hidden from assistive technology. A person never sees it. If it
             arrives filled, the page sends NOTHING and shows the truthful
             'didn't go through' state — never a false 'you're on the
             register'. Never part of the payload. -->
        <div class="bg-int-hp" aria-hidden="true">
          <label for="bgIntWebsite">Leave this field empty</label>
          <input type="text" id="bgIntWebsite" name="website" tabindex="-1"
                 autocomplete="off" value="">
        </div>

        <!-- The canonical consent control. ONE tick."""

P4_CSS_OLD = """  @media(max-width:560px){ .bg-int{padding:26px 20px;} }
  /* PLOTNUA-G3-CSS-END */"""
P4_CSS_NEW = """  /* G6 prep · the four offer statements, and the honeypot (never visible). */
  .bg-int-list{margin:2px 0 14px;padding:0 0 0 1.15em;}
  .bg-int-list li{margin:0 0 8px;font-size:15px;line-height:1.6;color:var(--body);
    max-width:68ch;}  /* the offer's existing measure, as #bgIntOffer .bg-int-p */
  .bg-int-list strong{font-weight:600;color:var(--ink);}
  .bg-int-hp{position:absolute !important;left:-10000px;top:auto;width:1px;
    height:1px;overflow:hidden;}
  @media(max-width:560px){ .bg-int{padding:26px 20px;} }
  /* PLOTNUA-G3-CSS-END */"""

P4_JS_OLD = """    intMsg('', null);
    intShow('sending');
"""
P4_JS_NEW = """    intMsg('', null);

    /* D4 honeypot. Checked after the local field checks, so a person whose
       browser somehow filled it still meets ordinary validation first. */
    var hp = $('bgIntWebsite');
    if (hp && hp.value !== '') { intUnavailable(); return; }

    intShow('sending');
"""

P5_OLD = """      out.push('We are starting in a small part of Dublin 5, so it may be a ' +
               'while before there is anybody near you at all. You are on the ' +
               'register either way.');"""
P5_NEW = """      out.push('We are starting in Raheny, Killester, Donnycarney and ' +
               'Artane, and we are not looking for anybody to introduce ' +
               'outside those areas. You are on the register either way.');"""

P6_OLD = "   * own constant for privacy_version 2026-10-PHASE2-V2. If this page ever"
P6_NEW = "   * own constant (unchanged since V1; privacy notice now V3). If this page ever"

# --------------------------------------------------------------- privacy ---
Q1_OLD = "    <p>We do not ask for unnecessary personal information.</p>"
Q1_NEW = ("    <p>If you choose to join the Garden Owner Register, we also collect the "
          "information described in Section 7.</p>\n" + Q1_OLD)

Q2_OLD = """    <p>Your name, email address and location are not saved to My Plot and are not stored in your browser.</p>
  </section>
"""
Q2_NEW = Q2_OLD + """
  <!-- """ + MARK + """ · Garden Owner Register, privacy notice 2026-10-PHASE2-V3 -->
  <section class="article-section reveal">
    <h2>7. The Garden Owner Register</h2>
    <p>The Borrowed Garden Property Check is private: answering its questions does not send PlotNua your details. After seeing your result, you can choose to join the Garden Owner Register. It is a list, kept privately by PlotNua, of homeowners who might be willing to share part of their garden with someone nearby who would like somewhere to grow. PlotNua is exploring this as a small pilot. Joining is voluntary. Matching is not live, and joining the register does not arrange an introduction.</p>
    <p>What we collect when you join:</p>
    <ul>
      <li>your first name;</li>
      <li>your email address;</li>
      <li>the area you choose from a short list;</li>
      <li>what you tell us about the space: roughly how big it is, whether there is water, and roughly when;</li>
      <li>anything you choose to add in the note;</li>
      <li>whether you own the home, rent it or are buying it, carried over from your Property Check answer. We keep this one answer because, if you rent, the owner would have to agree before any introduction could happen; and</li>
      <li>a record that you gave your consent, which version of this notice applied, and when you joined.</li>
    </ul>
    <p>We do not collect your address, your Eircode, your phone number, your surname, your age, photographs of your garden, or anything about your health. Your other Property Check answers and your Property Check result are not sent to the register.</p>
    <p>We use this information so that we can tell you if someone nearby is looking for growing space. We rely on your consent, which you give by ticking the box when you join. You can withdraw it at any time.</p>
    <p>Your record is private to PlotNua. It is not published, and there is no public listing, map, profile or directory. Records are reviewed by a person at PlotNua. Your email address would only be shared with another person if you said yes to one specific introduction, and introductions are not yet available.</p>
    <p>The form sends your details to a PlotNua service hosted on infrastructure provided by Cloudflare, which records them in the register. The register is stored in Airtable, a database service. Cloudflare and Airtable are both based in the United States, so your information may be processed outside the European Economic Area. Cloudflare states that it relies on the EU Standard Contractual Clauses, and on its certification under the EU-U.S. Data Privacy Framework, for such transfers. Airtable's Data Processing Addendum states that the EU Standard Contractual Clauses apply to personal data transferred from the European Economic Area. Visitors should refer to Cloudflare's and Airtable's own privacy policies for more about how they process personal information.</p>
    <p>We keep your record for a maximum of 24 months. You can ask us to delete it at any time, and we may delete it sooner if it is no longer needed.</p>
    <p>To leave the register or ask us to delete your record, email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>. There is nothing to cancel and no notice period. When we delete your record we keep a separate note that you gave permission and that we honoured your request. That note holds a one-way digital fingerprint made from your email address, not the address itself, so that we can show we did what you asked.</p>
  </section>
"""

RENUMBER = [(f"<h2>{a}. {t}</h2>", f"<h2>{a + 1}. {t}</h2>") for a, t in [
    (16, "Contact"), (15, "Changes to This Policy"), (14, "Children's Privacy"),
    (13, "Complaints"), (12, "Your Data Protection Rights"), (11, "Data Security"),
    (10, "How Long We Keep Information"), (9, "Legal Basis for Processing"),
    (8, "Third-Party Services and Links"), (7, "Cookies")]]

Q3_OLD = "      <li>Formspree;</li>\n"
Q3_NEW = ("      <li>Airtable, a database service that holds records kept by PlotNua's own "
          "services, including the Garden Owner Register;</li>\n" + Q3_OLD)

Q4_OLD = ("    <p>The Eircode lookup in Your Plot runs on PlotNua's own service, which is hosted "
          "on infrastructure provided by Cloudflare. Cloudflare is named here as the hosting "
          "provider rather than as a separate service of its own.</p>")
Q4_NEW = Q4_OLD + ("\n    <p>The Garden Owner Register described in Section 7 also runs on a "
                   "PlotNua service hosted on infrastructure provided by Cloudflare.</p>")

Q5_OLD = ("    <p>Supplier enquiries are retained for as long as needed to pass them on, answer "
          "any follow-up, and keep a record of what was sent on your behalf.</p>")
Q5_NEW = Q5_OLD + ("\n    <p>Garden Owner Register records are kept for a maximum of 24 months, "
                   "as described in Section 7.</p>")

Q6_OLD = '<p class="policy-updated">Last updated: September 2026</p>'
Q6_NEW = '<p class="policy-updated">Last updated: October 2026</p>'

W1_OLD = 'PRIVACY_VERSION = "2026-10-PHASE2-V2"'
W1_NEW = 'PRIVACY_VERSION = "2026-10-PHASE2-V3"'

# ------------------------------------------------------------------ gates --
REGIONS = [("PLOTNUA-G3-CSS-BEGIN", "PLOTNUA-G3-CSS-END"),
           ("PLOTNUA-G3-HTML-BEGIN", "PLOTNUA-G3-HTML-END"),
           ("PLOTNUA-G3-INTEREST-BEGIN", "PLOTNUA-G3-INTEREST-END")]


def mask(src):
    out = src
    for a, b in REGIONS:
        if out.count(a) != 1 or out.count(b) != 1:
            refuse(f"G3 region markers {a}/{b} not exactly once")
        i, j = out.index(a), out.index(b)
        if j < i:
            refuse(f"G3 region {a} ends before it begins")
        out = out[:i] + "<<" + a + ">>" + out[j:]
    return out


def intpayload(src):
    m = re.search(r"function intPayload\(\) \{.*?\n  \}\n", src, re.S)
    if not m:
        refuse("intPayload() not found")
    return m.group(0)


def build_page(src):
    if MARK in src:
        refuse("G6-prep marker already present; this builder is not re-runnable over its own output")
    if src.count("var INTEREST_PUBLIC = false;") != 1:
        refuse("INTEREST_PUBLIC is not exactly 'false' once before the build")
    out = src
    for old, new, lab in [(P1_OLD, P1_NEW, "P1 offer"), (P2_OLD, P2_NEW, "P2 notice"),
                          (P3_OLD, P3_NEW, "P3 payload"), (P4_HTML_OLD, P4_HTML_NEW, "P4 html"),
                          (P4_CSS_OLD, P4_CSS_NEW, "P4 css"), (P4_JS_OLD, P4_JS_NEW, "P4 js"),
                          (P5_OLD, P5_NEW, "P5 confirmation"), (P6_OLD, P6_NEW, "P6 comment")]:
        out = sub(out, old, new, lab)
    # post-gates
    if out.count("var INTEREST_PUBLIC = false;") != 1 or "INTEREST_PUBLIC = true" in out:
        refuse("GATE: INTEREST_PUBLIC must remain false")
    if out.count(CONSENT_LINE) != 1:
        refuse("GATE: canonical consent sentence changed or duplicated")
    if mask(out) != mask(src):
        refuse("GATE: a byte outside the three G3 regions changed")
    pay = intpayload(out)
    for k in ("inherited_spare_corner", "inherited_way_in",
              "inherited_your_own_use", "inherited_result_key", "lastEval"):
        if k in pay:
            refuse(f"GATE: intPayload still references {k}")
    if "inherited_tenure: answers.tenure" not in pay:
        refuse("GATE: intPayload no longer sends tenure (the Worker requires it)")
    if "website" in pay or "bgIntWebsite" in pay:
        refuse("GATE: the honeypot leaked into the payload")
    return out


def build_privacy(src):
    if MARK in src:
        refuse("privacy.html already carries the G6-prep marker")
    out = src
    for old, new in RENUMBER:
        out = sub(out, old, new, "renumber " + old)
    for old, new, lab in [(Q1_OLD, Q1_NEW, "Q1 collect"), (Q2_OLD, Q2_NEW, "Q2 section"),
                          (Q3_OLD, Q3_NEW, "Q3 airtable"), (Q4_OLD, Q4_NEW, "Q4 cloudflare"),
                          (Q5_OLD, Q5_NEW, "Q5 retention"), (Q6_OLD, Q6_NEW, "Q6 updated")]:
        out = sub(out, old, new, lab)
    nums = [int(n) for n in re.findall(r"<h2>(\d+)\. ", out)]
    if nums != list(range(1, 18)):
        refuse(f"GATE: privacy sections not numbered 1..17 in order: {nums}")
    return out


def build_wrangler(src):
    out = sub(src, W1_OLD, W1_NEW, "W1 privacy version")
    for line in ('WRITES_ENABLED  = "false"', 'EMAIL_ENABLED   = "false"'):
        if out.count(line) != 1:
            refuse(f"GATE: wrangler switch line changed: {line}")
    return out


def sha(b):
    return hashlib.sha256(b.encode()).hexdigest()[:16]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if mode not in ("--check", "--apply"):
        refuse("usage: --check | --apply")
    plan = []
    for path, fn in ((TARGET, build_page), (PRIVACY, build_privacy), (WRANGLER, build_wrangler)):
        src = path.read_text(encoding="utf-8")
        out = fn(src)
        plan.append((path, src, out))
        print(f"  {path.relative_to(ROOT)}  {sha(src)} -> {sha(out)}  "
              f"({len(src)} -> {len(out)} bytes)")
    if mode == "--apply":
        for path, _, out in plan:
            path.write_text(out, encoding="utf-8")
        print("APPLIED")
    else:
        print("CHECK OK (nothing written)")


if __name__ == "__main__":
    main()
