/* PlotArt · multi-artist basket · texts and founder decisions (21 Nov 2026). NOT DEPLOYED.

   TEXTS. The issued single-artwork texts (PA-PAY-2026-11, PA-BPT-2026-11) exclude orders of more than one artwork
   (PA-PAY 1.3), so a basket needs its own buyer terms and artist addendum. NONE has been approved: LIVE_BASKET_DOCS is
   empty, so no basket can be opened in live mode until the founder approves real texts and they are added here (with
   their fingerprints) in a reviewed change, and installed by an approved migration. In test mode only the labelled TEST
   placeholders below are accepted.

   DECISIONS. Founder decisions the basket depends on. Each value is what the code does today; nothing here invents or
   approves a commercial term. A value marked "test only" applies only in Stripe TEST mode. */
const sha = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('');

const BUYER_TEST = `<!DOCTYPE html><html lang="en-IE"><head><meta charset="utf-8"><title>TEST ONLY · PlotArt basket purchase terms (placeholder)</title></head><body>
<h1>TEST ONLY · Basket purchase terms (placeholder)</h1>
<p><strong>This is a labelled placeholder for Stripe TEST mode. It is not a PlotArt document and no real purchase can be made under it.</strong></p>
<p>Each artwork in your basket is sold to you by its artist, who is the seller. You make a separate contract with each artist. You enter your card once; each artist's payment is a separate card payment to that artist's own Stripe account, and each appears separately on your statement. PlotArt introduces you to the artists, provides the checkout and may receive a commission from an artist. PlotArt does not hold your payment; it is not escrow.</p>
<p>Your basket is paid only when every artist's payment has been confirmed. If any payment cannot be completed, no artwork in the basket is bought and every payment already authorised is cancelled.</p>
<p>Delivery: each artist's delivery charge, route, cover and return arrangements are shown before you pay and in your confirmation. Cancellation, returns and refunds are handled per artwork with that artist; PlotArt helps coordinate.</p>
</body></html>`;
const ARTIST_TEST = `<!DOCTYPE html><html lang="en-IE"><head><meta charset="utf-8"><title>TEST ONLY · PlotArt basket addendum (placeholder)</title></head><body>
<h1>TEST ONLY · Basket addendum (placeholder)</h1>
<p><strong>This is a labelled placeholder for Stripe TEST mode. It is not a PlotArt document.</strong></p>
<p>I agree that my available artworks with an approved delivery offer may be bought online, alone or in a basket with other artists' works. Each purchase is a direct payment to my own Stripe account; I remain the seller. PlotArt's commission (if any) applies only as my existing agreement provides and never to delivery. A basket payment is authorised first and captured only when every artist's payment in the basket is authorised.</p>
</body></html>`;

export const TEST_BASKET_DOCS = Object.freeze({
  'PA-BBT-TEST-01': { kind: 'buyer_basket_terms', title: 'Basket purchase terms (TEST placeholder)', html: BUYER_TEST },
  'PA-BAA-TEST-01': { kind: 'artist_basket_addendum', title: 'Basket addendum (TEST placeholder)', html: ARTIST_TEST },
});
/* LIVE texts: NONE approved. Add an entry ONLY with the founder's written approval of the exact text. */
export const LIVE_BASKET_DOCS = Object.freeze({});

export async function basketDoc(docId, live) {
  const d = (live ? LIVE_BASKET_DOCS : TEST_BASKET_DOCS)[docId];
  return d ? { ...d, doc_id: docId, html_sha256: await sha(d.html) } : null;
}
export const ARTIST_STATEMENT = docId => `I have read and accept the PlotArt Basket Addendum ${docId}. I understand that my artworks with an approved delivery offer may be bought online, alone or in a basket with other artists' works, that every payment is made to my own Stripe account and I remain the seller, and that I can stop at any time.`;

export const BASKET_DECISIONS = Object.freeze({
  /* Commission-free lines (Founding 25 and every Founding Enquiry). Fee Model B (17 Nov 2026) keeps commission-free orders
     on direct payment, because PlotArt cannot reimburse Stripe's processing fee through an application fee of zero.
     Options: 'direct_payment_only' (as Model B: such works are not offered in the basket; buyers enquire instead) or
     'with_processing_consent' (offered in the basket only when the artist has given the separate processing consent).
     LIVE: 'direct_payment_only' until the founder decides otherwise. TEST: set by BASKET_COMMISSION_FREE (test only). */
  commission_free_lines_live: 'direct_payment_only',
  /* Charges per basket: one direct charge per ARTWORK (each artwork is its own order, receipt, refund and dispute). Two
     works by one artist are two lines on the buyer's statement. A single charge per artist is possible later. */
  charge_granularity: 'per_artwork',
  /* Delivery: Republic of Ireland only, at the artist's approved standing offer for that artwork. */
  delivery_region: 'IE',
  /* How long the buyer has to complete an extra bank authentication for one artist's payment before every authorisation
     in the basket is cancelled. */
  action_minutes: 30,
});
