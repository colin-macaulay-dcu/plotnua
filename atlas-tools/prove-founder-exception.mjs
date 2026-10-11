/**
 * PROVE THE FOUNDER-AUTHORISED PUBLICATION EXCEPTION · FX1–FX17
 * =============================================================
 * BIOBUILDS is published on a founder's decision taken before the supplier
 * confirmed the corrected preview. That is a legitimate decision for a
 * founder to take and own. These are the assertions that it was recorded
 * honestly and that it did not loosen the gate for anybody else.
 *
 * THE FOUR THINGS THAT MUST HOLD, in the founder's own words:
 *
 *   "Preserve the original supplier permission and correspondence records
 *    accurately."                                            FX1, FX2, FX3
 *   "Record the founder's explicit decision to proceed."      FX4, FX5, FX6
 *   "Do not falsely record Mateus as having confirmed."       FX7, FX8, FX9
 *   "Without weakening the general publication gate for other
 *    suppliers."                                     FX10–FX14, FX15, FX16
 *
 * THE ASSERTION THAT MATTERS MOST IS FX15: every record in the tree that
 * carries NO exception must derive exactly what it derived before the
 * mechanism existed. It is checked against the pre-change derivation lifted
 * from the .bak sidecar, over all 13 real records and a 160-case synthetic
 * matrix, rather than by reading the diff and feeling reassured.
 *
 *   node atlas-tools/prove-founder-exception.mjs [--records PATH]
 *
 * Exit 0 = all pass. Exit 2 = the instrument could not run.
 */
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { derivePublicVisibility, gateIntegrityProblems,
         founderExceptionProblems, NEVER_WAIVABLE,
         WAIVABLE_HOLD_REASONS, PERMISSION_STATES,
         REVIEW_STATES, ASSET_STATES } from './publication-gate.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const arg = (n, d) => {
  const i = process.argv.indexOf('--' + n);
  return i === -1 ? d : process.argv[i + 1];
};
const RECORDS = arg('records', join(ROOT, 'image-rights-records.json'));

let pass = 0, fail = 0;
const ok  = (n, d) => { pass++; console.log(`  PASS  ${n}${d ? '  [' + d + ']' : ''}`); };
const bad = (n, d) => { fail++; console.log(`  FAIL  ${n}${d ? '  [' + d + ']' : ''}`); };
function refuse(why) {
  console.log('\nFOUNDER EXCEPTION');
  console.log('='.repeat(74));
  console.log('  INSTRUMENT UNAVAILABLE: ' + why);
  console.log('  Nothing was measured. This is not a pass.');
  process.exit(2);
}

let doc;
try { doc = JSON.parse(readFileSync(RECORDS, 'utf8')); }
catch (e) { refuse('the rights records could not be read: ' + e.message); }
const rows = Array.isArray(doc) ? doc
  : (Object.values(doc).find(v => Array.isArray(v) && v[0] && typeof v[0] === 'object') || null);
if (!rows) refuse('the rights records hold no recognisable row list');

const BB = rows.find(r => r.organisation_code === 'ORG-000153');
if (!BB) refuse('no BIOBUILDS row (ORG-000153) in ' + RECORDS);

console.log('\nFOUNDER EXCEPTION · FX1–FX17');
console.log('='.repeat(74));

/* ── 1 · THE ORIGINAL PERMISSION AND CORRESPONDENCE SURVIVE ───────────── */
{
  const p = BB.permission || {};
  (p.state === 'GRANTED' && p.date === '2026-10-02' &&
   p.ref === 'C2-GRANT-BIOBUILDS-20261002' &&
   (p.scope || []).includes('feature') && (p.scope || []).includes('imagery'))
    ? ok('FX1 the 2 October grant is intact: GRANTED, both scopes, same ref',
         `${p.state} ${p.date} ${p.ref}`)
    : bad('FX1 the 2 October grant is intact', JSON.stringify(p));
}
{
  /* The supplier's own words. This is the single most important string in
     the record and the one an edit is most likely to lose. */
  const ev = String(BB.evidence || '');
  const quoted = ev.includes('happy for PlotNua to feature BioBuilds')
    && ev.includes('with credit and a link back')
    && ev.includes('Please send us the listing before it goes live');
  quoted
    ? ok('FX2 Mateus’s words survive verbatim, including the review request')
    : bad('FX2 Mateus’s words survive verbatim', ev.slice(0, 120));
}
{
  const c = (BB.conditions || []).join(' | ');
  (/credit/i.test(c) && /link back/i.test(c) && /PRE-LIVE REVIEW/i.test(c)
   && /change or removal/i.test(c))
    ? ok('FX3 every original condition survives, including pre-live review',
         `${(BB.conditions || []).length} conditions`)
    : bad('FX3 every original condition survives', c.slice(0, 160));
}

/* ── 2 · THE DECISION IS RECORDED, NAMED AND DATED ───────────────────── */
{
  const ex = BB.founder_exception;
  const problems = ex ? founderExceptionProblems(BB) : ['absent'];
  (!problems.length)
    ? ok('FX4 the founder exception is present and well-formed',
         `${ex.decision_ref} · ${ex.authorised_by} · ${ex.decision_date}`)
    : bad('FX4 the founder exception is present and well-formed',
          problems.join('; '));
}
{
  const d = derivePublicVisibility(BB);
  (d.visibility === 'PUBLISHABLE' && d.holdReason === null &&
   d.waived.length === 2 &&
   d.waived.includes('listing-review-awaiting-confirmation') &&
   d.waived.includes('assets-not-approved'))
    ? ok('FX5 BIOBUILDS derives PUBLISHABLE, and says what was waived',
         d.waived.join(', '))
    : bad('FX5 BIOBUILDS derives PUBLISHABLE with its waivers named',
          JSON.stringify(d));
}
{
  /* The record must carry the waiver, not just the derivation — a reader of
     the file should never have to run code to find out why a supplier with
     an outstanding review is live. */
  const w = BB.waived_conditions;
  (Array.isArray(w) && w.length === 2 && BB.public_visibility === 'PUBLISHABLE'
   && BB.hold_reason === null)
    ? ok('FX6 the written record carries the visibility and the waivers',
         JSON.stringify(w))
    : bad('FX6 the written record carries the visibility and the waivers',
          `${BB.public_visibility} / ${BB.hold_reason} / ${JSON.stringify(w)}`);
}

/* ── 3 · NO FABRICATED SUPPLIER CONFIRMATION ─────────────────────────── */
{
  /* THE FOUNDER'S RULE 3, AND THE WHOLE REASON THIS MECHANISM EXISTS
     RATHER THAN A ONE-WORD EDIT TO THE REVIEW STATE. */
  const lr = BB.listing_review || {};
  (lr.state === 'AWAITING_CONFIRMATION' && lr.confirmed_at === null)
    ? ok('FX7 the listing review still says AWAITING_CONFIRMATION, '
         + 'confirmed_at null')
    : bad('FX7 the listing review still says AWAITING_CONFIRMATION',
          `${lr.state} / confirmed_at=${JSON.stringify(lr.confirmed_at)}`);
}
{
  const ex = BB.founder_exception || {};
  (ex.supplier_confirmation_received === false)
    ? ok('FX8 the exception states in its own right that no confirmation '
         + 'was received')
    : bad('FX8 the exception states that no confirmation was received',
          String(ex.supplier_confirmation_received));
}
{
  /* And the integrity checks must REFUSE a record that tries to claim both.
     This is the drift this guard exists to catch: somebody tidying the file
     later and "completing" the review state to match the live listing. */
  /* TWO BRANCHES, TESTED SEPARATELY. An earlier version of this check forged
     a record that tripped BOTH the CONFIRMED-state branch and the
     confirmed_at branch, so removing either one left it passing on the other.
     The capability proof reported it VACUOUS. Each is now isolated. */
  const forgeState = JSON.parse(JSON.stringify(BB));
  forgeState.listing_review.state = 'CONFIRMED';
  const pState = gateIntegrityProblems(forgeState)
    .filter(p => /CONFIRMED/.test(p));
  pState.length
    ? ok('FX9 a forged CONFIRMED review state is refused on its own')
    : bad('FX9 a forged CONFIRMED review state is refused',
          JSON.stringify(gateIntegrityProblems(forgeState)));

  const forgeAt = JSON.parse(JSON.stringify(BB));
  forgeAt.listing_review.confirmed_at = '2026-10-12T09:00:00Z';
  const pAt = gateIntegrityProblems(forgeAt)
    .filter(p => /confirmed_at/.test(p));
  pAt.length
    ? ok('FX9b an invented confirmed_at timestamp is refused on its own')
    : bad('FX9b an invented confirmed_at timestamp is refused',
          JSON.stringify(gateIntegrityProblems(forgeAt)));
}

/* ── 4 · THE GATE IS NOT WEAKENED FOR ANYBODY ELSE ───────────────────── */
{
  /* THE BRIGHT LINE. A founder can accept the risk of publishing early
     against a grant PlotNua HOLDS. A founder cannot conjure a grant. */
  const wants = ['permission-declined', 'no-permission',
                 'permission-conditional-unresolved', 'permission-state-missing'];
  const covered = wants.every(w => NEVER_WAIVABLE.includes(w));
  covered
    ? ok('FX10 all four permission reasons are in NEVER_WAIVABLE')
    : bad('FX10 all four permission reasons are in NEVER_WAIVABLE',
          JSON.stringify(NEVER_WAIVABLE));
}
{
  /* And the attempt must actually fail, not merely be forbidden on paper. */
  const results = [];
  for (const [perm, reason] of [['NONE', 'no-permission'],
                                ['DECLINED', 'permission-declined'],
                                ['CONDITIONAL', 'permission-conditional-unresolved'],
                                ['NOT_A_STATE', 'permission-state-missing']]) {
    const r = {
      permission: { state: perm },
      listing_review: { state: 'NOT_REQUIRED' },
      founder_exception: {
        authorised_by: 'Someone', decision_date: '2026-10-11',
        waives: [reason], supplier_confirmation_received: false,
        basis: 'An attempt to publish without a supplier permission at all.'
      }
    };
    const d = derivePublicVisibility(r);
    results.push(`${perm}:${d.visibility}/${d.holdReason}`);
    if (d.visibility !== 'HOLD' || d.holdReason !== reason) {
      results.push('LEAK');
    }
  }
  !results.includes('LEAK')
    ? ok('FX11 an exception naming a permission reason publishes nobody',
         results.join(' '))
    : bad('FX11 an exception naming a permission reason publishes nobody',
          results.join(' '));
}
{
  /* A malformed exception is not a half-exception. */
  const base = {
    permission: { state: 'GRANTED' },
    listing_review: { state: 'AWAITING_CONFIRMATION' }
  };
  const malformed = [
    { waives: ['listing-review-awaiting-confirmation'] },                 // no author
    { authorised_by: 'X', waives: ['listing-review-awaiting-confirmation'] }, // no date
    { authorised_by: 'X', decision_date: '2026-10-11', waives: [] },      // waives nothing
    { authorised_by: 'X', decision_date: '11/10/2026',
      waives: ['listing-review-awaiting-confirmation'],
      supplier_confirmation_received: false, basis: 'x'.repeat(30) },     // bad date
    { authorised_by: 'X', decision_date: '2026-10-11',
      waives: ['listing-review-awaiting-confirmation'],
      supplier_confirmation_received: true,
      basis: 'x'.repeat(30) },                                           // claims confirmed
    { authorised_by: 'X', decision_date: '2026-10-11',
      waives: ['listing-review-awaiting-confirmation'],
      supplier_confirmation_received: false, basis: 'too short' }         // no real basis
  ];
  const leaks = malformed.filter(ex =>
    derivePublicVisibility({ ...base, founder_exception: ex }).visibility
      !== 'HOLD');
  !leaks.length
    ? ok('FX12 six malformed exceptions each waive nothing',
         `${malformed.length} tested`)
    : bad('FX12 six malformed exceptions each waive nothing',
          `${leaks.length} leaked`);
}
{
  /* An exception waives ONLY what it names. */
  const r = {
    permission: { state: 'GRANTED' },
    listing_review: { state: 'AWAITING_CONFIRMATION' },
    asset_approval_state: 'REFERENCE_ONLY',
    founder_exception: {
      authorised_by: 'X', decision_date: '2026-10-11',
      waives: ['listing-review-awaiting-confirmation'],
      supplier_confirmation_received: false,
      basis: 'Waives the review only, deliberately not the assets.'
    }
  };
  const d = derivePublicVisibility(r);
  (d.visibility === 'HOLD' && d.holdReason === 'assets-not-approved' &&
   d.waived.length === 1)
    ? ok('FX13 a condition the decision did not name still holds',
         `${d.holdReason}, waived ${JSON.stringify(d.waived)}`)
    : bad('FX13 a condition the decision did not name still holds',
          JSON.stringify(d));
}
{
  /* Every OTHER row in the real tree. None carries an exception, so none may
     have moved, and none may have gained one. */
  const others = rows.filter(r => r.organisation_code !== 'ORG-000153');
  const withEx = others.filter(r => r.founder_exception);
  const published = others.filter(r =>
    derivePublicVisibility(r).visibility === 'PUBLISHABLE' &&
    derivePublicVisibility(r).waived.length);
  (!withEx.length && !published.length)
    ? ok('FX14 no other supplier has an exception or a waived condition',
         `${others.length} other record(s) checked`)
    : bad('FX14 no other supplier has an exception or a waived condition',
          `withException=${withEx.length} withWaiver=${published.length}`);
}

/* ── FX15 · THE EQUIVALENCE PROOF ────────────────────────────────────── */
{
  /* Lifted from the .bak sidecar: the derivation as it was BEFORE the
     exception mechanism existed. Every record without an exception must
     derive identically under both. Reading the diff is not this. */
  const bak = join(HERE, 'publication-gate.mjs.bak');
  if (!existsSync(bak)) {
    bad('FX15 (equivalence) the pre-change derivation could not be lifted',
        'no publication-gate.mjs.bak sidecar — run the builder, or pass a '
        + 'baseline');
  } else {
    const src = readFileSync(bak, 'utf8');
    let before;
    try {
      const mod = await import('data:text/javascript;base64,' +
        Buffer.from(src).toString('base64'));
      before = mod.derivePublicVisibility;
    } catch (e) {
      bad('FX15 (equivalence) the pre-change derivation would not evaluate',
          e.message);
    }
    if (before) {
      const cases = [];
      for (const p of [...PERMISSION_STATES, 'NOT_A_STATE', undefined]) {
        for (const rv of [...REVIEW_STATES, 'NOT_A_STATE', undefined]) {
          for (const a of [...ASSET_STATES, undefined]) {
            cases.push({ permission: { state: p },
                         listing_review: { state: rv },
                         asset_approval_state: a });
          }
        }
      }
      // Plus every real record, with any exception stripped.
      for (const r of rows) {
        const copy = JSON.parse(JSON.stringify(r));
        delete copy.founder_exception;
        cases.push(copy);
      }
      const moved = [];
      for (const c of cases) {
        const b = before(c), n = derivePublicVisibility(c);
        if (b.visibility !== n.visibility || b.holdReason !== n.holdReason) {
          moved.push(`${JSON.stringify([c.permission && c.permission.state,
            c.listing_review && c.listing_review.state,
            c.asset_approval_state])}: ${b.visibility}/${b.holdReason}`
            + ` → ${n.visibility}/${n.holdReason}`);
        }
        if (n.waived.length) moved.push('a no-exception case waived something');
      }
      !moved.length
        ? ok('FX15 (equivalence) every no-exception case derives exactly as '
             + 'before', `${cases.length} cases: ${cases.length - rows.length} `
             + `synthetic + ${rows.length} real`)
        : bad('FX15 (equivalence) every no-exception case derives as before',
              `${moved.length} moved, e.g. ${moved[0]}`);
    }
  }
}

/* ── FX16 · THE WAIVABLE LIST IS ENUMERATED, NOT INFERRED ────────────── */
{
  /* "Whatever is not forbidden" would mean a hold reason added next month
     became waivable the moment it was written. */
  const overlap = WAIVABLE_HOLD_REASONS.filter(r => NEVER_WAIVABLE.includes(r));
  /* TESTED AT THE VALIDATOR, NOT THE DERIVATION. Every condition the gate
     evaluates today sits in one of the two lists, so an unrecognised reason
     can never be the thing holding a supplier -- the derivation simply leaves
     the real hold in place and looks identical either way. The capability
     proof reported exactly that as VACUOUS. The validator CAN see it, and it
     is what protects the ninth condition somebody adds later from being
     waivable the moment it is written. */
  const unrecognised = founderExceptionProblems({
    founder_exception: {
      authorised_by: 'X', decision_date: '2026-10-11',
      waives: ['some-future-hold-reason'],
      supplier_confirmation_received: false,
      basis: 'Naming a reason that is not in the enumerated waivable list.'
    }
  });
  const rejected = unrecognised.some(p => /not a recognised waivable/.test(p));
  (!overlap.length && rejected)
    ? ok('FX16 an unrecognised reason is rejected by the validator; the two '
         + 'lists do not overlap', `${WAIVABLE_HOLD_REASONS.length} waivable`)
    : bad('FX16 an unrecognised reason is rejected by the validator',
          `overlap=${overlap.join(',')} problems=${JSON.stringify(unrecognised)}`);
}

/* ── FX17 · DEFENCE IN DEPTH, HONESTLY LABELLED ──────────────────────── */
{
  /* SOURCE ASSERTION, and it says so, because it cannot honestly be anything
     else. NEVER_WAIVABLE is checked twice: in founderExceptionProblems, which
     rejects the whole exception, and again in the waiver loop. The second is
     UNREACHABLE while the first works -- the capability proof demonstrated
     that removing it changes no behaviour -- so no behavioural test can
     distinguish it. It exists to survive a future edit to the validator, and
     the only truthful way to assert it is structurally. */
  const src = readFileSync(join(HERE, 'publication-gate.mjs'), 'utf8');
  const inValidator = /NEVER_WAIVABLE\.includes\(r\)/.test(src);
  const inLoop =
    /accepted\.includes\(reason\) && !NEVER_WAIVABLE\.includes\(reason\)/.test(src);
  (inValidator && inLoop)
    ? ok('FX17 (source) NEVER_WAIVABLE is enforced at BOTH the validator and '
         + 'the waiver itself')
    : bad('FX17 (source) NEVER_WAIVABLE is enforced at both layers',
          `validator=${inValidator} loop=${inLoop}`);
}

console.log('\n' + '='.repeat(74));
console.log(`${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
