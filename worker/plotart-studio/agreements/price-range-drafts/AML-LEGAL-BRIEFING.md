# Legal briefing · Anti-money-laundering position of PlotArt for artworks of EUR 10,000 or more

**Prepared 23 Nov 2026 for review with a professional adviser. This is a briefing to frame questions, not legal advice and
not a conclusion that PlotArt is or is not a designated person.**

## 1. Why this matters now

PlotArt wants to support artwork sales at any price. Today every online route stops below EUR 10,000:
- a EUR 9,999.99 per-artwork ceiling (code, database and the four issued texts); and
- a EUR 10,000 linked-purchase safeguard (same buyer, any artist, twelve months), refused before any payment.

The code comment that introduced the safeguard says it applies "until PlotArt has professional advice and, if required, the
procedures of a designated person". The safeguard stays in production until that advice is in hand.

## 2. How PlotArt works (facts for the adviser)

- **Seller.** The artist is the seller of the artwork and the buyer contracts with the artist (PA-BBT, PA-BPT). PlotArt
  never owns the artwork.
- **Introduction and marketing.** PlotArt publishes the artist's gallery and artwork pages on plotnua.ie, receives
  enquiries and passes them to the artist.
- **Checkout.** PlotArt operates the online checkout:
  - single-artwork quotes issued by PlotArt from an enquiry, approved by the artist;
  - a multi-artist basket on PlotArt's own pages.
- **Payment.** Payment is a Stripe Connect **direct charge** on the artist's own Stripe account. The buyer's card is saved
  on PlotArt's Stripe account and cloned to each artist's account. Funds settle to the artist; PlotArt does not hold them.
- **Commission.** PlotArt's commission (15% for Gallery Artists; 0% for Founding 25 sales, where the artist bears Stripe's
  fees) is taken as a Stripe application fee from the artist's charge. Commission is never charged on delivery.
- **Records.** PlotArt sets the delivery and insurance rules, approves each artist's delivery offer, and keeps the order,
  quote and payment records. It also handles refunds and disputes through Stripe on the artist's account.
- **Scale.** Today: up to 16 active artists. The highest listed price is EUR 20,000, and 17 available works are priced
  above EUR 9,999.99.

## 3. Confirmed (from the legislation as published on irishstatutebook.ie)

1. **Art market participants are designated persons, but only above a threshold.** The Criminal Justice (Money Laundering
   and Terrorist Financing) (Amendment) Act 2021 (No. 3 of 2021), section 5, amends section 25(1) of the Criminal Justice
   (Money Laundering and Terrorist Financing) Act 2010. It adds, as a designated person:

   > "(ib) a person trading or acting as an intermediary in the trade of works of art (including when carried out by an art
   > gallery or an auction house) but only in respect of transactions of a total value of at least €10,000 (whether in one
   > transaction or in a series of transactions that are or appear to be linked to each other)".

2. **Below EUR 10,000 they are not designated persons.** The status applies only to transactions, alone or linked, of at
   least EUR 10,000. Below that, the 2010 Act's obligations do not attach to a person by virtue of paragraph (ib).
3. **It comes from EU law.** The 2021 Act gives effect to Directive (EU) 2018/843 (the "fifth anti-money-laundering
   directive"), which the Act itself cites.
4. **It took effect by ministerial order.** Section 30(2) of the 2021 Act provides that the Act comes into operation on the
   day or days appointed by the Minister by order. *(Whether and when section 5 was commenced is listed under section 4: we
   have not verified the commencement order.)*

## 4. Requiring professional interpretation

**Role (the decisive questions)**
1. Is PlotArt "acting as an intermediary in the trade of works of art" within paragraph (ib)? It markets the work,
   introduces the buyer, runs the checkout, issues quotes, sets the terms of sale and takes a commission, while the artist
   is the seller and PlotArt never holds title or funds. Does the gallery-like commission model alone bring it within (ib)?
2. Does the payment structure change the answer? The payment is a Stripe Connect direct charge on the artist's account, and
   Stripe, a regulated payment institution, has its own AML obligations. Does that affect PlotArt's position as
   intermediary, or only the payment leg?
3. Is the artist, selling their own original work, "a person trading in works of art" and so a designated person in their
   own right for sales of EUR 10,000 or more? If so, what does that mean for artists selling through PlotArt? Should PlotArt
   tell them, and does PA-PAY or PA-BAA need to say so?
4. Do the Founding 25 sales (0% commission, artist bears Stripe's fees) change PlotArt's role for those transactions?

**Threshold and linking**
5. What is the "value of the transaction": the artwork price alone, or the price plus delivery (and installation)? Is
   PlotArt's commission relevant?
6. What counts as "linked" for PlotArt? Possibilities include:
   - the same buyer across different artists;
   - the same artist across buyers;
   - a basket of several artists' works;
   - a household or business.

   Over what period? The current twelve-month window is a pilot rule, not a legal definition.
7. Is the threshold measured per buyer-intermediary relationship, or per artwork sale?

**If PlotArt is a designated person for those transactions**
8. Which customer due-diligence measures apply to a buyer, and when? Before the buyer commits, before the card is charged,
   or before funds are captured? The basket authorises every payment before capturing any; would verification between
   authorisation and capture be enough?
9. Who is the "customer" for PlotArt's due diligence: the buyer, the artist, or both?
10. Which other obligations would follow, and in what form for a business of PlotArt's size?
    - risk assessment;
    - policies and procedures;
    - training;
    - checks for politically exposed persons and sanctions;
    - record keeping, and for how long;
    - reporting suspicious transactions (to whom).
11. **Registration and supervision.** Is there a registration requirement for art market participants, and who is the
    competent authority (for example the Department of Justice's Anti-Money Laundering Compliance Unit)? We have not found a
    registration provision for paragraph (ib) persons in the 2021 Act and make **no assumption** that registration is
    required.
12. Can PlotArt limit its obligations by keeping all online sales below EUR 10,000 and handling larger sales through a
    separate, checked route (for example quotes issued only after verification)?

**Related points**
13. **Commencement.** Confirm that section 5 of the 2021 Act is in force, and from when.
14. **Data protection.** If identity documents are collected: lawful basis, retention period, and the changes the Privacy
    Notice needs (a V19).
15. **Terms.** Confirm which of the two drafted variants (`PRICE-RANGE-TEXT-CHANGES-DRAFT.md`) is appropriate, and any
    wording the adviser requires.

## 5. Practical points outside AML (for awareness, not legal questions)

- **Stripe.** A single charge can be up to EUR 999,999.99; the code refuses anything larger. The buyer's card issuer may
  still decline a large payment. Stripe may ask for more verification of a connected account that receives large payments.
- **Insurance.** Every fixed-price delivery offer already needs transit insurance for at least the artwork price, and that
  stays. Artists must be able to obtain cover at EUR 14,000, EUR 30,000 and above.
- **Disputes and refunds.** The refund and commission maths are unaffected by price (tested at EUR 4,500, 14,000 and
  30,000). A refund may have to be funded from the artist's Stripe balance; at high values, artists need to understand
  this.

## 6. What happens after the advice

- **Not a designated person.** Issue the new texts without the limits, apply migration 0023, and lift the switches
  (`PRICE_RANGE=open`, `AML_LINKED_LIMIT_CENTS=none`) through a reviewed change.
- **Designated person.** Put the required procedures in place first. Keep online sales below the threshold, and complete
  larger sales through a verified route. Issue the matching texts (Variant 2) and Privacy Notice V19.
