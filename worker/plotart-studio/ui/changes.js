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
    // A paragraph break added or removed is only white space: name it, or the change would be invisible. Same rule as the
    // gallery: a blank line, or a line break after the end of a sentence, starts a paragraph; any other break is joined.
    const before = n => { while (--n >= 0) if (o[n][0] === 'eq') return o[n][1]; return ''; };
    const space = t => !t.trim();
    const para = (t, n) => /\n/.test(t) && space(t) && (/\n\s*\n/.test(t) || /[.!?…:;"”’')\]]$/.test(before(n)));
    // white space replaced by white space: only a paragraph starting or ending is shown (a joined line break, or a
    // paragraph break re-typed, changes nothing on the page)
    const pair = n => { const [k, t] = o[n], m = k === 'del' ? n + 1 : n - 1, x = o[m];
      return space(t) && x && x[0] === (k === 'del' ? 'ins' : 'del') && space(x[1]) ? para(x[1], m) : null; };
    return o.map(([k, t], n) => {
      const p = pair(n), mine = para(t, n);
      if (k === 'del') return p !== null ? (mine && !p ? '<del class="st-brk">paragraph break</del>' : '') : mine ? '<del class="st-brk">paragraph break</del>' : `<del>${E(t)}</del>`;
      if (k === 'ins') return p !== null ? (mine && !p ? '<ins class="st-brk">new paragraph</ins>' : ' ') : mine ? '<ins class="st-brk">new paragraph</ins>' : `<ins>${E(t)}</ins>`;
      return trim(t, n === 0 ? 'before' : n === o.length - 1 ? 'after' : 'between'); }).join('');
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
