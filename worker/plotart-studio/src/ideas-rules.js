/* PlotNua · Idea Board shared rules (Phase 1, 1 Nov 2026): used by the public intake Worker (ideas.js) and by the
   founder's Ideas tab in PlotArt Studio (index.js), so an idea the founder edits is held to the same rules. */
export const AREAS = ['Space', 'Garden', 'Art', 'Energy', 'Frontage', 'Neighbourhood', 'Income'];
export const COUNTIES = ['Antrim', 'Armagh', 'Carlow', 'Cavan', 'Clare', 'Cork', 'Derry', 'Donegal', 'Down', 'Dublin', 'Fermanagh', 'Galway', 'Kerry',
  'Kildare', 'Kilkenny', 'Laois', 'Leitrim', 'Limerick', 'Longford', 'Louth', 'Mayo', 'Meath', 'Monaghan', 'Offaly', 'Roscommon', 'Sligo',
  'Tipperary', 'Tyrone', 'Waterford', 'Westmeath', 'Wexford', 'Wicklow'];
export const rules = {
  link: /(https?:\/\/|www\.|\b[a-z0-9-]{2,}\.(?:com|ie|net|org|co|uk|io|eu|info|biz|app|dev|ly|me)\b)/i,
  email: /[^\s@]+@[^\s@]+\.[^\s@]+/,
  phone: /\d(?:[\s().\-]?\d){6,}/,
  markup: /[<>]/,
};
export function clean(s) {
  return String(s ?? '').replace(/[\u200b-\u200f\u2060\ufeff]/g, '').replace(/[\u0000-\u001f\u007f\u2028\u2029]/g, ' ').replace(/\s+/g, ' ').trim();
}
export function problem(text) {
  if (text.length < 8) return 'Please write a little more: at least 8 characters.';
  if (text.length > 160) return 'Please keep your idea to 160 characters.';
  if (rules.email.test(text)) return 'Please leave out e-mail addresses: ideas are anonymous.';
  if (rules.link.test(text)) return 'Please leave out website addresses.';
  if (rules.phone.test(text)) return 'Please leave out telephone numbers: ideas are anonymous.';
  if (rules.markup.test(text)) return 'Please leave out the < and > characters.';
  return null;
}
