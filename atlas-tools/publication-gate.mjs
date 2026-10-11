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

/**
 * Derive public visibility. Returns { visibility, holdReason }.
 * holdReason is null when PUBLISHABLE, and otherwise names the FIRST
 * unsatisfied condition in a fixed order, so the reason is stable and
 * testable rather than dependent on evaluation order.
 */
export function derivePublicVisibility(record) {
  const permission = (record && record.permission) || {};
  const review = (record && record.listing_review) || {};
  const perm = permission.state;
  const rev = review.state;
  const assets = record && record.asset_approval_state;

  if (!PERMISSION_STATES.includes(perm)) {
    return { visibility: "HOLD", holdReason: "permission-state-missing" };
  }
  if (!REVIEW_STATES.includes(rev)) {
    return { visibility: "HOLD", holdReason: "listing-review-state-missing" };
  }

  if (perm === "DECLINED") {
    return { visibility: "HOLD", holdReason: "permission-declined" };
  }
  if (perm === "NONE") {
    return { visibility: "HOLD", holdReason: "no-permission" };
  }
  if (perm === "CONDITIONAL") {
    return { visibility: "HOLD", holdReason: "permission-conditional-unresolved" };
  }

  // perm === GRANTED from here.
  if (rev === "AWAITING_CONFIRMATION") {
    return { visibility: "HOLD",
             holdReason: "listing-review-awaiting-confirmation" };
  }
  if (rev === "CHANGES_REQUESTED") {
    return { visibility: "HOLD", holdReason: "listing-review-changes-requested" };
  }

  // The pre-existing Atlas gate, kept as a condition rather than replaced.
  if (assets && assets !== "APPROVED") {
    return { visibility: "HOLD", holdReason: "assets-not-approved" };
  }

  return { visibility: "PUBLISHABLE", holdReason: null };
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

  return out;
}
