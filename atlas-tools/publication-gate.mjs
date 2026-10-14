/* THE PUBLICATION GATE — ONE DERIVATION, IMPORTED EVERYWHERE.
   =========================================================================
   Whether a supplier may appear in public Results is DERIVED from three
   independent dimensions and is never written down by hand. This file is the
   only place the derivation exists, so there cannot be a second answer.

   WHY A GATE AT ALL, when BIOBUILDS is already invisible today.

   It is invisible by ACCIDENT, not by intent. Two unrelated conditions happen
   to hold it back: its governed assets are still 'Reference Only — Not
   Published', and its area.number is null so class_3a() returns
   NOT_A_CANDIDATE with reason no-usable-area. Neither was designed as a
   review gate. The second is the dangerous one: correcting Wanderlust's area
   to its true 35.54 m2 -- an ordinary data-quality fix, and one the supplier
   asked for -- lands inside the 32-45 m2 band and would publish the product
   as a side effect, while the supplier is still reviewing the listing.

   A hold that works by accident is not a hold. This gate reads permission and
   review state ONLY. area.number is not an input to it, which is the whole
   point, and PG6 asserts exactly that.

   THE THREE DIMENSIONS, AND WHY THEY MUST NOT COLLAPSE INTO ONE.

   BIOBUILDS GRANTED permission on 2 October 2026 and separately asked to see
   the listing before it goes live. Those are different facts. Recording them
   as a single "not approved" flag -- which an earlier draft of PlotNua's own
   audit did -- misrepresents a supplier who said yes, and would have had us
   asking for permission we already had.                                    */

export const PERMISSION_STATES = ["GRANTED", "CONDITIONAL", "DECLINED", "NONE"];
export const REVIEW_STATES = ["NOT_REQUIRED", "AWAITING_CONFIRMATION",
                              "CONFIRMED", "CHANGES_REQUESTED"];
export const ASSET_STATES = ["APPROVED", "REFERENCE_ONLY", "WITHDRAWN"];

/* A grant whose own words ask to see the listing first cannot be recorded as
   needing no review. Without this, the easiest way to publish early is a
   typo in one enum. */
export const PRE_LIVE_REVIEW_LANGUAGE =
  /before it goes live|check it first|send us the listing|see the listing|review (?:it|the listing) (?:first|before)/i;

/* ── THE FOUNDER-AUTHORISED EXCEPTION ──────────────────────────────────────
   A founder may decide to publish a supplier before one of the gate's
   conditions is satisfied, and own that decision. What a founder may NOT do
   is make the record say the condition was met.

   So an exception does not edit a condition, remove it, or relax it for
   anyone else. It sits on ONE supplier's record, names the EXACT hold reasons
   it accepts the risk of, and travels in the derivation's output so no
   surface can later report a waived hold as a satisfied one.

   THE LINE THAT CANNOT MOVE. A permission that was never given, was declined,
   or was withdrawn cannot be waived by anybody. The gate exists so PlotNua
   does not publish a supplier's material without the supplier's permission; a
   founder can accept the risk of publishing early against a grant PlotNua
   HOLDS, and cannot conjure a grant that was never made. Without this list
   the mechanism would be a master key. */
export const NEVER_WAIVABLE = [
  "permission-declined",
  "no-permission",
  "permission-conditional-unresolved",
  "permission-state-missing",
  /* FAIL-CLOSED CORRECTION, 14 October 2026. A permission that does not
     cover featuring the supplier's products (OGNYX: four images on one
     private preview) is not a permission to list them, and an organisation
     with no rights record at all has no grant for anybody to accept the risk
     of. Neither is waivable: there is no grant behind either to proceed on. */
  "permission-scope-excludes-listing",
  "publication-record-missing"
];

/* Everything else is waivable ON AN EXPLICIT, NAMED DECISION -- enumerated
   rather than derived as "whatever is not forbidden", so adding a new hold
   reason does not silently make it waivable. */
export const WAIVABLE_HOLD_REASONS = [
  "listing-review-awaiting-confirmation",
  "listing-review-changes-requested",
  "listing-review-state-missing",
  "assets-not-approved"
];

/**
 * Is this record's founder_exception usable? Returns an array of problems;
 * empty means usable. A malformed exception waives NOTHING -- it does not
 * half-work, and it does not fail open.
 */
export function founderExceptionProblems(record) {
  const ex = record && record.founder_exception;
  if (!ex) return ["no founder_exception on this record"];
  const out = [];
  if (!ex.authorised_by || typeof ex.authorised_by !== "string") {
    out.push("authorised_by must name the person who decided");
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(ex.decision_date || ""))) {
    out.push("decision_date must be an ISO date");
  }
  if (!Array.isArray(ex.waives) || !ex.waives.length) {
    out.push("waives must list the exact hold reasons being accepted");
  } else {
    for (const r of ex.waives) {
      if (NEVER_WAIVABLE.includes(r)) {
        out.push(`${r} can never be waived by anyone`);
      } else if (!WAIVABLE_HOLD_REASONS.includes(r)) {
        out.push(`${r} is not a recognised waivable hold reason`);
      }
    }
  }
  /* The decision's whole character is that the supplier has NOT come back.
     Recording that explicitly, as a boolean on the exception itself, is what
     stops the file drifting into implying confirmation. It must be present
     and it must be false -- an exception is not the place to record a
     confirmation that arrived. */
  if (ex.supplier_confirmation_received !== false) {
    out.push("supplier_confirmation_received must be present and false: an "
             + "exception records proceeding WITHOUT confirmation");
  }
  if (!ex.basis || String(ex.basis).trim().length < 20) {
    out.push("basis must say why the decision was taken");
  }
  return out;
}

/**
 * Derive public visibility. Returns { visibility, holdReason, waived }.
 *
 * holdReason names the FIRST unsatisfied condition in a fixed order, so the
 * reason is stable and testable rather than dependent on evaluation order.
 * `waived` lists any conditions that were unsatisfied and explicitly accepted
 * by a well-formed founder exception; it is an empty array otherwise.
 *
 * The conditions below are the SAME conditions, in the SAME order, with the
 * SAME vocabulary as before the exception mechanism existed. A record with no
 * founder_exception derives exactly what it derived before, which
 * prove-founder-exception.mjs asserts over every real record and a synthetic
 * matrix rather than leaving it to inspection.
 */
export function derivePublicVisibility(record) {
  const permission = (record && record.permission) || {};
  const review = (record && record.listing_review) || {};
  const perm = permission.state;
  const rev = review.state;
  const assets = record && record.asset_approval_state;

  /* Every condition, in order. The first unsatisfied one decides, exactly as
     the chain of early returns did. */
  const conditions = [
    [!PERMISSION_STATES.includes(perm), "permission-state-missing"],
    [!REVIEW_STATES.includes(rev), "listing-review-state-missing"],
    [perm === "DECLINED", "permission-declined"],
    [perm === "NONE", "no-permission"],
    [perm === "CONDITIONAL", "permission-conditional-unresolved"],
    // perm === GRANTED from here. A grant must SAY it covers featuring the
    // products; a scope that is missing, or names imagery or a preview only,
    // fails closed (14 Oct 2026).
    [!(Array.isArray(permission.scope) && permission.scope.includes("feature")),
     "permission-scope-excludes-listing"],
    [rev === "AWAITING_CONFIRMATION", "listing-review-awaiting-confirmation"],
    [rev === "CHANGES_REQUESTED", "listing-review-changes-requested"],
    // The pre-existing Atlas gate, kept as a condition rather than replaced.
    [!!assets && assets !== "APPROVED", "assets-not-approved"]
  ];

  /* An exception is consulted ONLY if it is well-formed, and waives ONLY the
     reasons it names. A malformed one waives nothing. */
  const ex = record && record.founder_exception;
  const exUsable = ex && founderExceptionProblems(record).length === 0;
  const accepted = exUsable ? ex.waives.slice() : [];

  const waived = [];
  for (const [unsatisfied, reason] of conditions) {
    if (!unsatisfied) continue;
    if (accepted.includes(reason) && !NEVER_WAIVABLE.includes(reason)) {
      waived.push(reason);
      continue;
    }
    return { visibility: "HOLD", holdReason: reason, waived: waived };
  }

  return { visibility: "PUBLISHABLE", holdReason: null, waived: waived };
}

/**
 * Integrity checks on a single record, independent of the derivation.
 * Returns an array of problem strings; empty means consistent.
 */
export function gateIntegrityProblems(record) {
  const out = [];
  const permission = (record && record.permission) || {};
  const review = (record && record.listing_review) || {};
  const derived = derivePublicVisibility(record);

  // PG1 · derived, never literal.
  if (record.public_visibility !== undefined &&
      record.public_visibility !== derived.visibility) {
    out.push(`public_visibility is ${JSON.stringify(record.public_visibility)} ` +
             `but derives to ${derived.visibility}`);
  }
  if (record.hold_reason !== undefined &&
      record.hold_reason !== derived.holdReason) {
    out.push(`hold_reason is ${JSON.stringify(record.hold_reason)} but ` +
             `derives to ${JSON.stringify(derived.holdReason)}`);
  }

  // PG4 · a grant that asked for pre-live review cannot say NOT_REQUIRED.
  const evidence = String(record.evidence || "");
  if (PRE_LIVE_REVIEW_LANGUAGE.test(evidence) &&
      review.state === "NOT_REQUIRED") {
    out.push("the grant's own words ask for pre-live review, but " +
             "listing_review.state is NOT_REQUIRED");
  }

  // PG5 · never call a granted supplier unpermitted.
  if (permission.state === "GRANTED" && derived.holdReason === "no-permission") {
    out.push("holdReason says no-permission for a supplier whose permission " +
             "state is GRANTED");
  }

  /* PG14 · AN EXCEPTION IS NOT A CONFIRMATION, AND MUST NEVER BECOME ONE.
     The failure mode this exists for: somebody tidies the record later,
     notices the supplier is published, and "completes" the review state to
     match. That would turn a founder's accepted risk into a supplier's
     endorsement, in writing, on PlotNua's own file. */
  const ex = record && record.founder_exception;
  if (ex) {
    const problems = founderExceptionProblems(record);
    if (problems.length) {
      out.push("founder_exception is malformed and therefore waives nothing: "
               + problems.join("; "));
    }
    if (ex.supplier_confirmation_received === false &&
        review.state === "CONFIRMED") {
      out.push("the record says the supplier has NOT confirmed and also sets "
               + "listing_review.state to CONFIRMED");
    }
    if (ex.supplier_confirmation_received === false && review.confirmed_at) {
      out.push("the record says the supplier has NOT confirmed and also "
               + "carries a confirmed_at timestamp");
    }
    /* An exception that waives nothing real is a note pretending to be a
       decision; it should be removed rather than left to rot. */
    if (!problems.length && !derived.waived.length) {
      out.push("founder_exception waives " + JSON.stringify(ex.waives) +
               " but no such condition is unsatisfied; the exception is "
               + "inert and should be removed");
    }
  }

  return out;
}

/* ── THE ORGANISATION-LEVEL DERIVATION · FAIL-CLOSED CORRECTION ─────────────
   14 October 2026. derivePublicVisibility() above was always fail-closed for
   a record: missing states derive permission-state-missing. The hole was one
   level up, in how a generator FOUND the record:

     * a rights row with neither state was skipped as "pre-gate, holds nobody";
     * an organisation with no rights row at all was treated as publishable;
     * names were matched case-insensitively but otherwise exactly, so
       "Yardbox" never found "Yard Box".

   Each of those turned ABSENT evidence into PUBLISHABLE. This function is the
   one answer for an organisation by name, and the generator mirrors it.

   EXISTING PUBLICATION IS PRESERVED, NOT APPROVED. The organisations already
   public in Results with no rights record are listed by name in
   atlas-tools/publication-gate-legacy-baseline.json. They stay publishable
   so nothing live changes, they are reported for manual review, and the list
   can only shrink: anybody not on it, and every NEW organisation, needs a
   rights record that derives PUBLISHABLE. */
export const NO_RECORD_HOLD = "publication-record-missing";

export function normaliseOrganisationName(name) {
  return String(name || "").toUpperCase().replace(/[^A-Z0-9]+/g, "");
}

/**
 * Derive visibility for an organisation by name. rows = the rights records;
 * legacy = the baseline's organisation names. Returns the record derivation
 * plus { matched: bool, legacy: bool }. Two records answering to one name is
 * a HOLD, never a choice between them.
 */
export function deriveOrganisationVisibility(name, rows, legacy = []) {
  const key = normaliseOrganisationName(name);
  if (!key) {
    return { visibility: "HOLD", holdReason: NO_RECORD_HOLD, waived: [],
             matched: false, legacy: false };
  }
  const hits = (rows || []).filter(r =>
    normaliseOrganisationName(r && r.organisation_name) === key);
  if (hits.length > 1) {
    return { visibility: "HOLD", holdReason: "permission-state-missing",
             waived: [], matched: true, legacy: false };
  }
  if (hits.length === 1) {
    return Object.assign(derivePublicVisibility(hits[0]),
                         { matched: true, legacy: false });
  }
  if ((legacy || []).some(n => normaliseOrganisationName(n) === key)) {
    return { visibility: "PUBLISHABLE", holdReason: null, waived: [],
             matched: false, legacy: true };
  }
  return { visibility: "HOLD", holdReason: NO_RECORD_HOLD, waived: [],
           matched: false, legacy: false };
}

/* ── THE PUBLIC-INFORMATION LISTING BASIS · 14 October 2026 ────────────────
   Founder decision, "Garden Retreat — controlled text-only publication
   expansion": a factual, text-only listing for a maker who has NOT given
   permission, read from its own public product pages. It is not a
   permission and is never recorded as one.

   The order is the whole rule: a rights record ALWAYS decides first, so a
   decline, a hold or a review request can never be overridden by the
   register; the legacy baseline is not consulted (wellness never had one);
   only an organisation with no record that the register names, in scope,
   with no objection, no permission claim and no imagery, may be listed --
   and then only as text. The wellness generator mirrors this in
   wellness_hold(); test_wellness_universe.py W10 exercises it. */
export const PUBLIC_INFORMATION = "PUBLIC_INFORMATION";

export function derivePublicInformationListing(name, rows, register, scope) {
  const key = normaliseOrganisationName(name);
  const hits = (rows || []).filter(r =>
    normaliseOrganisationName(r && r.organisation_name) === key);
  if (hits.length) {
    const d = deriveOrganisationVisibility(name, rows, []);
    return Object.assign(d, { basis: d.visibility === "PUBLISHABLE" ? "SUPPLIER_PERMISSION" : null });
  }
  const reg = register || {};
  if (((reg.decision || {}).scope) !== scope) {
    return { visibility: "HOLD", holdReason: NO_RECORD_HOLD, waived: [], basis: null };
  }
  const row = (reg.organisations || []).find(o => normaliseOrganisationName(o.name) === key);
  const wellFormed = row && row.basis === PUBLIC_INFORMATION && row.supplier_permission === false
    && row.imagery === "none" && row.objection === "none recorded";
  return wellFormed
    ? { visibility: "PUBLISHABLE", holdReason: null, waived: [], basis: PUBLIC_INFORMATION }
    : { visibility: "HOLD", holdReason: NO_RECORD_HOLD, waived: [], basis: null };
}
