/* PlotArt Studio · Exhibitions & Achievements (Phase C, development 25 Nov 2026; following Dave King's feedback: "A separate
   section might be easier to access for visitors different to the statement of practice."). NOT DEPLOYED.
   One optional, free-form section the artist organises themselves: exhibitions, awards, collections, residencies,
   commissions, publications, or anything else, under their own headings. No structured record per item.
   The text format is deliberately plain (no HTML is ever accepted or produced from the artist's text):
     ## Heading            a heading (a line starting with "#" or "##")
     - item                a list item (a line starting with "-", "*" or "•"); consecutive items form one list
     any other line        a paragraph; consecutive lines join into one paragraph; a blank line starts a new block
   normalise() is the only way text is stored; blocks() is the only way it is read. The publisher's Python twin
   (atlas-tools/plotart_achievements.py) must give exactly the same result (test/prove-achievements.mjs checks both). */
import { Bad } from './lib.js';

export const MAX = 6000, MAX_HEADING = 80, MAX_ITEM = 400, MAX_PARA = 1200, MAX_HEADINGS = 24, MAX_ITEMS = 200;
const HEAD = /^#{1,3}\s+/, ITEM = /^[-*•]\s+/;
const CTRL = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/;

/* The stored text, or null when there is nothing (the section is then hidden). Throws Bad with a plain message. */
export function normalise(v) {
  if (v === undefined || v === null) return null;
  if (typeof v !== 'string') throw new Bad('Exhibitions & Achievements must be text');
  if (CTRL.test(v)) throw new Bad('Exhibitions & Achievements contains characters that can’t be shown');
  const lines = v.replace(/\r\n?/g, '\n').split('\n').map(l => l.replace(/\s+/g, ' ').trim());
  const out = [];
  for (const l of lines) {
    if (!l) { if (out.length && out[out.length - 1] !== '') out.push(''); continue; }
    if (HEAD.test(l)) { const t = l.replace(HEAD, '').replace(/#+$/, '').trim(); if (t) { if (out.length && out[out.length - 1] !== '') out.push(''); out.push('## ' + t); out.push(''); } continue; }
    if (ITEM.test(l)) { const t = l.replace(ITEM, '').trim(); if (t) out.push('- ' + t); continue; }
    out.push(l);
  }
  while (out.length && out[out.length - 1] === '') out.pop();
  const text = out.join('\n');
  if (!text) return null;
  if (text.length > MAX) throw new Bad(`Exhibitions & Achievements can be up to ${MAX.toLocaleString('en-IE')} characters`);
  const bl = blocks(text);
  if (bl.filter(b => b.h).length > MAX_HEADINGS) throw new Bad(`Use up to ${MAX_HEADINGS} headings`);
  if (bl.some(b => b.h && b.h.length > MAX_HEADING)) throw new Bad(`Keep each heading under ${MAX_HEADING} characters`);
  if (bl.reduce((n, b) => n + (b.ul ? b.ul.length : 0), 0) > MAX_ITEMS) throw new Bad(`Use up to ${MAX_ITEMS} list items`);
  if (bl.some(b => b.ul && b.ul.some(i => i.length > MAX_ITEM))) throw new Bad(`Keep each list item under ${MAX_ITEM} characters`);
  if (bl.some(b => b.p && b.p.length > MAX_PARA)) throw new Bad(`Keep each paragraph under ${MAX_PARA.toLocaleString('en-IE')} characters`);
  return text;
}

/* Stored text → blocks: { h } | { p } | { ul: [...] } */
export function blocks(text) {
  const out = [];
  let para = null, list = null;
  const end = () => { if (para) out.push({ p: para.join(' ') }); if (list) out.push({ ul: list }); para = list = null; };
  for (const l of String(text || '').split('\n')) {
    if (!l) { end(); continue; }
    if (l.startsWith('## ')) { end(); out.push({ h: l.slice(3) }); continue; }
    if (l.startsWith('- ')) { if (para) end(); (list ||= []).push(l.slice(2)); continue; }
    if (list) end();
    (para ||= []).push(l);
  }
  end();
  return out;
}

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
/* The section's inner HTML (the publisher writes the same). Everything is escaped: the artist's text is never HTML. */
export function toHtml(text) {
  return blocks(text).map(b => b.h ? `<h3>${esc(b.h)}</h3>` : b.p ? `<p>${esc(b.p)}</p>` : `<ul>${b.ul.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`).join('\n');
}
