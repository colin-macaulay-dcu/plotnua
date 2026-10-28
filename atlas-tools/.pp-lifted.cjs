  function pnPresentationTier(product){
    /* THE ONLY DEFINITION OF TIER A, AND IT NAMES NO SUPPLIER.
       `imagery` is written exclusively by apply_authorised_imagery.py, which
       resolves it from the canonical rights manifest: live grant, scoped
       delivery host, product-linked Atlas asset, required credit attached.
       If any of those fail the block is absent and this returns 'B'.

       THE CREDIT IS PART OF THE TEST. An image whose attribution went missing
       is not an image PlotNua may publish, so it is not tier A either. */
    const im = product && product.imagery;
    if (im && im.url && im.credit) return 'A';
    return 'B';
  }

  function pnApplyPresentationPriority(rows){
    /* Stable partition, IN PLACE, from index 1 onward.

       IN PLACE because `rows` carries non-enumerable contracts (__scored,
       __eligible, and later views/originViewState) that several downstream
       consumers read. Building a new array would silently drop them.

       FROM INDEX 1 because rows[0] is Best Overall -- a match claim, not a
       presentation slot. Imagery must never decide it. */
    if (!Array.isArray(rows) || rows.length < 3) return rows;

    const head = rows[0];
    const tail = rows.slice(1);
    const withImage = tail.filter(r => pnPresentationTier(r.product) === 'A');
    if (!withImage.length || withImage.length === tail.length) return rows;
    const without = tail.filter(r => pnPresentationTier(r.product) !== 'A');

    const merged = [head].concat(withImage, without);
    for (let i = 0; i < rows.length; i++) rows[i] = merged[i];

    /* Internal only. It exists so that "why did that move up?" has a recorded
       answer rather than a re-derivation, and so the ledger can show that
       ordering changed while scoring did not. */
    try {
      Object.defineProperty(rows, '__presentationPriority', {
        value: { appliedFrom: 1, withAuthorisedImagery: withImage.length,
                 withoutImagery: without.length,
                 headUntouched: rows[0] === head },
        enumerable: false, configurable: true });
    } catch (e) { /* non-fatal: presentation trace only */ }
    return rows;
  }


module.exports={pnPresentationTier,pnApplyPresentationPriority};
