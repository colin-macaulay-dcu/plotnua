#!/usr/bin/env python3
"""Apply the founder-signed H6 provenance declaration to image-provenance-records.json.

    python3 atlas-tools/declare-h6-provenance.py SIGNED.json            # dry run: says what would change
    python3 atlas-tools/declare-h6-provenance.py SIGNED.json --write    # writes the register

SIGNED.json is governance/H6-PROVENANCE-DECLARATION-DRAFT-2026-10-26.json after the founder has:
  * filled every record's human_review.reviewer and human_review.date, and replaced the word DRAFT in
    each resemblance_review.verdict and "FOUNDER TO CONFIRM" in each reference_disclosure.statement
    with his own confirmed wording;
  * answered the open confirmations in a top-level "answers" object:
        "answers": {"C1": "no" | "not-recorded", "C2": "accept", "C3": "ILLUSTRATION_VERIFIED_NOT_AI", "signed_by": "...", "date": "YYYY-MM-DD"}
    C1 "no": no supplier photograph was supplied to the image generator. C1 "not-recorded": what was in
    the generation conversation is not known, and every record must then say so (reference_disclosure
    status UNCERTAIN, no reference_inputs), as the founder-attested form requires. Anything else, or a
    resemblance review that is not accepted (C2), is refused: no script can decide those.
    (Founder decision 26 Oct 2026, PN-FDR-2026-10-26-H6-HOME: C1 not-recorded, C2 accept, C3 ILLUSTRATION_VERIFIED_NOT_AI.)

What it does (and nothing else):
  1. adds the 18 H6 AI_ILLUSTRATION records and the 4 lettering records, each hashed from disk;
  2. retires the 13 records of the withdrawn Possibility Reveal component (P9: a withdrawn image's
     record goes with it; the files stay in git history), and the derivatives made from them (P12);
  3. moves the TimberIN licensed composite (possibility-reveal-L6) to staged_composites, unchanged
     except that it no longer names an asset, so its licences, the containment proofs and a future
     restore keep working.
It never writes a classification on its own: every record comes from the signed declaration, and
the validator's own rules (P1-P14) decide whether the result is publishable. The code changes the
declaration relies on (the H6 decision and ILLUSTRATION_VERIFIED_NOT_AI in validate-image-provenance.js,
and the H6 gate step) are applied separately and were approved with it.
"""
import json, hashlib, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, 'image-provenance-records.json')


def die(msg):
    sys.exit('REFUSED: ' + msg)


def sha(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), 'rb').read()).hexdigest()


def main():
    if len(sys.argv) < 2:
        die('usage: declare-h6-provenance.py SIGNED.json [--write]')
    write = '--write' in sys.argv[2:]
    dec = json.load(open(sys.argv[1]))
    ans = dec.get('answers') or {}
    if not ans.get('signed_by') or not ans.get('date'):
        die('the declaration is not signed (answers.signed_by, answers.date)')
    c1 = str(ans.get('C1', '')).lower()
    if c1 not in ('no', 'not-recorded'):
        die('C1 must be "no" or "not-recorded"')
    if c1 == 'not-recorded':
        for r in dec['records']:
            rd = r.get('reference_disclosure') or {}
            if rd.get('status') != 'UNCERTAIN' or 'reference_inputs' in r:
                die(f"{r['asset']}: C1 is not-recorded, so the record must disclose the uncertainty and claim no reference_inputs")
    if str(ans.get('C2', '')).lower() != 'accept':
        die('C2 is not "accept": the resemblance review has not been accepted')
    if ans.get('C3') not in ('ILLUSTRATION_VERIFIED_NOT_AI', 'SVG_TEXT'):
        die('C3 is unanswered (ILLUSTRATION_VERIFIED_NOT_AI, or SVG_TEXT if the lettering is redrawn as live text)')

    reg = json.load(open(REG))
    have = {r['asset'] for r in reg['records']}
    new = []
    for r in dec['records']:
        hr = r.get('human_review') or {}
        if not hr.get('reviewer') or not hr.get('date'):
            die(f"{r['asset']}: human_review is not signed")
        if 'DRAFT' in json.dumps(r.get('resemblance_review')) or 'FOUNDER TO CONFIRM' in json.dumps(r.get('reference_disclosure')):
            die(f"{r['asset']}: the resemblance review or reference disclosure still carries draft wording")
        if sha(r['asset']) != r['sha256']:
            die(f"{r['asset']}: the file on disk is not the file the founder signed")
        if r['asset'] in have:
            die(f"{r['asset']}: already declared")
        rec = {k: v for k, v in r.items() if k not in ('group', 'what')}
        rec['what'] = r['what']
        new.append(rec)
    if ans['C3'] == 'ILLUSTRATION_VERIFIED_NOT_AI':
        for l in dec['lettering']:
            if sha(l['asset']) != l['sha256']:
                die(f"{l['asset']}: the file on disk is not the file the founder signed")
            new.append({'asset': l['asset'], 'sha256': l['sha256'], 'bytes': os.path.getsize(os.path.join(ROOT, l['asset'])),
                        'class': 'ILLUSTRATION_VERIFIED_NOT_AI', 'what': l['what'],
                        'generated': {'tool': 'Blender 5.2 (Cycles), scripted 3D render of typeset lettering (Playfair Display ExtraBold, SIL Open Font Licence); no generative model', 'date': '2026-10-25',
                                      'method': 'PlotNua project documents claude/h6-floating-lettering-proof-2026-10-25.md and claude/h6-status-and-typography-refinement-2026-10-25.md (Version B, approved 25 Oct 2026)',
                                      'layout_reference': "Size and placement were fitted by eye to the founder's ChatGPT mock-up PlotNua-H6-Floating-Text-Reference.png; none of its pixels are used"},
                        'human_review': {'reviewer': ans['signed_by'], 'date': ans['date'],
                                         'attests': 'Founder approved this lettering (Version B, 25 Oct 2026) and its release (26 Oct 2026). It is a 3D render of typeset lettering made in Blender without any generative AI model.'},
                        'permitted_surfaces': ['homepage']})
    else:
        print('C3 = SVG_TEXT: no lettering records; the lettering images must be gone from the page before the guard will pass.')

    retire = set(dec['retire']['records'])
    gone = [r for r in reg['records'] if r['asset'] in retire]
    if len(gone) != len(retire):
        die(f'expected {len(retire)} Possibility Reveal records to retire, found {len(gone)}')
    l6 = [r for r in gone if r.get('composite_id') == 'possibility-reveal-L6']
    if len(l6) != 1:
        die('the TimberIN composite record possibility-reveal-L6 was not found exactly once')
    staged = dict(l6[0]); staged.pop('asset'); staged.pop('sha256', None); staged.pop('bytes', None)
    staged['retired_from_homepage'] = {'date': ans['date'], 'by': ans['signed_by'],
                                       'why': 'The Possibility Reveal component was replaced by H6. Kept staged so its TimberIN licences, containment proofs and a restore stay intact.',
                                       'was_asset': l6[0]['asset'], 'was_sha256': l6[0]['sha256']}
    reg['records'] = [r for r in reg['records'] if r['asset'] not in retire] + new
    # P12: a derivative is accounted for only through its source, so derivatives of a retired source go too.
    dgone = [x for x in reg.get('derivatives', []) if (x.get('derived_from') or {}).get('asset') in retire]
    reg['derivatives'] = [x for x in reg.get('derivatives', []) if x not in dgone]
    reg.setdefault('staged_composites', []).append(staged)

    print(f"+ {len(new)} records ({sum(r['class'] == 'AI_ILLUSTRATION' for r in new)} AI_ILLUSTRATION, {sum(r['class'] != 'AI_ILLUSTRATION' for r in new)} lettering)")
    print(f"- {len(gone)} Possibility Reveal records retired, and {len(dgone)} derivatives of them")
    print("~ possibility-reveal-L6 (TimberIN licensed composite) moved to staged_composites")
    if write:
        # The register is hand-formatted in places; this rewrite normalises it to indent=2 (content unchanged
        # apart from the records above, as the validator and `git diff --word-diff` will show).
        open(REG, 'w').write(json.dumps(reg, indent=2) + '\n')
        print('written: ' + REG + '  (now run: node atlas-tools/validate-image-provenance.js)')
    else:
        print('dry run: nothing written (add --write)')


if __name__ == '__main__':
    main()
