const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, AlignmentType, Footer, Header, PageNumber, BorderStyle, ShadingType,
        Table, TableRow, TableCell, WidthType, LevelFormat, HeadingLevel } = require('docx');

const FONT = 'Arial', SERIF = 'Georgia', INK = '1B1C1E', MUTED = '5E5A55', TERRA = 'AE6245';
const W = 9026; // A4 text width at 1" margins (DXA)

function runs(text, base = {}) {            // **bold** inline markup
  const out = []; const parts = text.split(/(\*\*[^*]+\*\*)/);
  for (const p of parts) { if (!p) continue;
    if (p.startsWith('**')) out.push(new TextRun({ text: p.slice(2, -2), bold: true, font: FONT, size: 21, color: INK, ...base }));
    else out.push(new TextRun({ text: p, font: FONT, size: 21, color: INK, ...base })); }
  return out;
}
const P = (text, o = {}) => new Paragraph({ children: runs(text, o.run || {}), spacing: { after: 120, line: 288 }, ...o.para });
const H = (text, pb) => new Paragraph({ pageBreakBefore: !!pb, heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: SERIF, size: 26, color: INK })],
  spacing: { before: 300, after: 120 }, keepNext: true, keepLines: true });
const C = (num, text) => new Paragraph({ children: [new TextRun({ text: num + '\t', bold: true, font: FONT, size: 21, color: INK }), ...runs(text)],
  tabStops: [{ type: 'left', position: 620 }], indent: { left: 620, hanging: 620 }, spacing: { after: 110, line: 288 } });
const B = (text) => new Paragraph({ children: runs(text), numbering: { reference: 'bul', level: 0 }, spacing: { after: 60, line: 276 }, indent: { left: 980, hanging: 300 } });
const NOTE = (text) => new Paragraph({ children: [new TextRun({ text, font: FONT, size: 18, color: '7A3E26', bold: true })],
  shading: { type: ShadingType.CLEAR, fill: 'F6E9E1', color: 'auto' }, border: { left: { style: BorderStyle.SINGLE, size: 18, color: TERRA, space: 8 } },
  spacing: { before: 120, after: 240 }, indent: { left: 120 } });
const RULE = () => new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: 'C9C2B8', space: 1 } }, spacing: { after: 200 } });
function table(rows, widths) {
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ cantSplit: true, tableHeader: i === 0, children: r.map((c, j) => new TableCell({ width: { size: widths[j], type: WidthType.DXA },
      shading: i === 0 ? { type: ShadingType.CLEAR, fill: 'EFEBE5', color: 'auto' } : undefined,
      margins: { top: 80, bottom: 80, left: 110, right: 110 },
      children: [new Paragraph({ children: runs(c, i === 0 ? { bold: true, size: 19 } : { size: 19 }), spacing: { after: 0, line: 264 } })] })) })) });
}
function build(doc, file) {
  const body = [];
  body.push(new Paragraph({ children: [new TextRun({ text: 'PLOTART', font: FONT, size: 20, bold: true, color: TERRA, characterSpacing: 60 })], spacing: { after: 60 } }));
  body.push(new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun({ text: doc.title, font: SERIF, size: 44, color: INK })], spacing: { after: 80 } }));
  body.push(new Paragraph({ children: [new TextRun({ text: doc.sub, font: FONT, size: 19, color: MUTED })], spacing: { after: 60 } }));
  if (doc.status) body.push(NOTE(doc.status));
  for (const [kind, a, b] of doc.blocks) {
    if (kind === 'h') body.push(H(a)); else if (kind === 'hpb') body.push(H(a, true)); else if (kind === 'c') body.push(C(a, b)); else if (kind === 'p') body.push(P(a));
    else if (kind === 'b') body.push(B(a)); else if (kind === 'rule') body.push(RULE()); else if (kind === 't') { body.push(table(a, b)); body.push(P('')); }
    else if (kind === 'quote') body.push(new Paragraph({ children: runs(a, { italics: true }), indent: { left: 620, right: 400 },
      border: { left: { style: BorderStyle.SINGLE, size: 12, color: 'C9C2B8', space: 10 } }, spacing: { before: 80, after: 160, line: 288 } }));
  }
  const d = new Document({
    creator: 'PlotNua', title: doc.title + ' ' + doc.id, description: doc.sub,
    styles: { default: { document: { run: { font: FONT, size: 21 } } },
      paragraphStyles: [
        { id: 'Title', name: 'Title', basedOn: 'Normal', run: { font: SERIF, size: 44 }, paragraph: { spacing: { before: 0, after: 80 } } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: SERIF, size: 26 }, paragraph: { spacing: { before: 300, after: 120 }, keepNext: true, outlineLevel: 1 } }] },
    numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 980, hanging: 300 } } } }] }] },
    sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: doc.id, font: FONT, size: 16, color: MUTED })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: doc.footer + '  ·  Page ', font: FONT, size: 16, color: MUTED }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: MUTED }),
        new TextRun({ text: ' of ', font: FONT, size: 16, color: MUTED }), new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: MUTED })] })] }) },
      children: body }] });
  return Packer.toBuffer(d).then(buf => fs.writeFileSync(file, buf));
}
module.exports = { build };
