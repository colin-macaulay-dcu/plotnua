/* PlotArt Studio · how a change is shown (18 Nov 2026, after an artist's two-word biography correction read as "the old
   information" on Review and submit: the whole old biography was printed first, with the new one in brackets after it).
   Shared by the artist Studio and the founder Review Desk. A long text shows only what changed, words removed struck
   through and words added marked, with a little context either side; a short value reads "old → new". */
window.PAChanges = (() => {
  const E = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const tokens = s => String(s ?? '').split(/(\s+)/).filter(t => t !== '');
  function ops(a, b) {   // longest common subsequence over words and spaces
    const n = a.length, m = b.length;
    if (n * m > 4e6) return [['del', a.join('')], ['ins', b.join('')]];
    const L = new Uint32Array((n + 1) * (m + 1)), at = (i, j) => i * (m + 1) + j;
    for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--)
      L[at(i, j)] = a[i] === b[j] ? L[at(i + 1, j + 1)] + 1 : Math.max(L[at(i + 1, j)], L[at(i, j + 1)]);
    const out = [], push = (k, t) => { const l = out[out.length - 1]; if (l && l[0] === k) l[1] += t; else out.push([k, t]); };
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (a[i] === b[j]) { push('eq', a[i]); i++; j++; }
      else if (L[at(i + 1, j)] >= L[at(i, j + 1)]) push('del', a[i++]);
      else push('ins', b[j++]);
    }
    while (i < n) push('del', a[i++]);
    while (j < m) push('ins', b[j++]);
    return out;
  }
  function trim(t, side) {   // keep about eight words of context next to a change
    const w = t.split(/(\s+)/);
    if (w.length <= 17) return E(t);
    return side === 'before' ? '… ' + E(w.slice(-16).join('')) : side === 'after' ? E(w.slice(0, 16).join('')) + ' …'
      : E(w.slice(0, 16).join('')) + ' … ' + E(w.slice(-16).join(''));
  }
  function textDiff(from, to) {
    const o = ops(tokens(from), tokens(to));
    return o.map(([k, t], n) => k === 'del' ? `<del>${E(t)}</del>` : k === 'ins' ? `<ins>${E(t)}</ins>`
      : trim(t, n === 0 ? 'before' : n === o.length - 1 ? 'after' : 'between')).join('');
  }
  const long = v => typeof v === 'string' && (v.length > 60 || /\n/.test(v));
  const show = v => v === null || v === undefined || v === '' ? '—' : v === true ? 'yes' : v === false ? 'no' : String(v);
  /* the detail line for one change (empty when there is nothing to show, e.g. a new photograph) */
  function detail(c) {
    if (c.to === undefined || typeof c.to === 'object' && c.to !== null) return '';
    if (long(c.from) || long(c.to)) return `<span class="st-diff">${textDiff(c.from, c.to)}</span>`;
    return `<span class="st-diff st-diff--short"><del>${E(show(c.from))}</del> → <ins>${E(show(c.to))}</ins></span>`;
  }
  return { detail, textDiff };
})();
