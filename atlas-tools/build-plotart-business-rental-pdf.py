from pathlib import Path
import re,html,json,hashlib
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent.parent
source=ROOT/'atlas-tools/plotart-business-rental-terms.md'
target=ROOT/'plotart/downloads/plotart-business-rental-artist-guide-and-agreement.pdf'
font='/usr/share/fonts/truetype/open-sans/'
pdfmetrics.registerFont(TTFont('OpenSans',font+'OpenSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('OpenSansBold',font+'OpenSans-Bold.ttf'))
pdfmetrics.registerFontFamily('OpenSans',normal='OpenSans',bold='OpenSansBold',italic='OpenSans',boldItalic='OpenSansBold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='PA-Body',fontName='OpenSans',fontSize=10.2,leading=15,spaceAfter=9,textColor=colors.HexColor('#202124')))
styles.add(ParagraphStyle(name='PA-H1',fontName='OpenSansBold',fontSize=22,leading=28,spaceBefore=12,spaceAfter=16,keepWithNext=True))
styles.add(ParagraphStyle(name='PA-H2',fontName='OpenSansBold',fontSize=13,leading=18,spaceBefore=14,spaceAfter=8,keepWithNext=True))
styles.add(ParagraphStyle(name='PA-Small',fontName='OpenSans',fontSize=8.4,leading=12,spaceAfter=8,textColor=colors.HexColor('#454545')))
def inline(s):
 s=html.escape(s)
 return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
story=[]
doc=SimpleDocTemplate(str(target),pagesize=(595.28,841.89),rightMargin=48,leftMargin=48,topMargin=50,bottomMargin=48,title='PlotArt business rentals - Artist guide and agreement template',author='PlotArt',subject='Business rental information and blank placement agreements',pageCompression=1,invariant=1)
text=source.read_text()
text=re.sub(r"(^#{1,2} [^\n]+)\n(?!\n)", r"\1\n\n", text, flags=re.M)
for block in re.split(r'\n\s*\n',text):
 block=block.strip()
 if not block:continue
 if block=='# Agreement template' or block.startswith('# Separate PlotArt fee'):
  story.append(PageBreak())
 if block.startswith('# '):story.append(Paragraph(inline(block[2:].replace(' · ',' | ')),styles['PA-H1']))
 elif block.startswith('## '):story.append(Paragraph(inline(block[3:]),styles['PA-H2']))
 else:
  lines=block.splitlines()
  for line in lines:
   story.append(Paragraph(inline(line.replace(' · ',' | ')),styles['PA-Body']))
def footer(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#cccccc'));canvas.line(48,38,547,38)
 canvas.setFont('OpenSans',7.5);canvas.setFillColor(colors.HexColor('#555555'))
 canvas.drawString(48,26,'PlotArt | PA-BHR-2026-11 v1.0 | Template: complete and agree before signing')
 canvas.drawRightString(547,26,str(doc.page))
target.parent.mkdir(parents=True,exist_ok=True)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
record={'version':'PA-BHR-2026-11-v1.0','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
(ROOT/'atlas-tools/plotart-business-rental-document.json').write_text(json.dumps(record,indent=2)+'\n')
print(target)

