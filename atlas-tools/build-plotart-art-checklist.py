#!/usr/bin/env python3
"""Build a deterministic one-page printable checklist. No email capture or inventory."""
from pathlib import Path
import reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'plotart/downloads/plotart-art-buying-checklist.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
fonts=Path(reportlab.__file__).parent/'fonts'
pdfmetrics.registerFont(TTFont('PASans',str(fonts/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('PASansBold',str(fonts/'VeraBd.ttf')))
c=canvas.Canvas(str(OUT),pagesize=(595.28,841.89),invariant=1)
c.setTitle('PlotArt - Art-buying checklist')
c.setAuthor('PlotArt')
cream=HexColor('#F8F5EC');green=HexColor('#1F3B2E');clay=HexColor('#A9563D')
c.setFillColor(cream);c.rect(0,0,595.28,841.89,fill=1,stroke=0)
c.setFillColor(green);c.setFont('PASansBold',12);c.drawString(44,793,'PlotArt / PART OF PLOTNUA')
c.setFont('PASansBold',29);c.drawString(44,747,'Before you buy art.')
c.setFont('PASans',12);c.drawString(44,724,'Eight checks to take to a viewing or an artist enquiry.')
items=[
('Know the work','Confirm artist, title, medium and whether it is a unique work, original print or reproduction.'),
('Measure the outer size','Include the frame. Width: __________ cm    Height: __________ cm'),
('Try it in your room','Check scale and position from the doorway and your usual seat. Leave comfortable headroom above furniture.'),
('Ask about condition','Confirm marks, damage, repairs or details not clear in the photographs.'),
('Check care and display','Ask about light, heat and handling for the materials. Confirm weight and suitable wall fixings with the artist, framer or installer.'),
('Agree the total cost','Ask what is included: frame, any applicable tax, delivery and installation. Total agreed: __________________'),
('Agree the arrangements','Confirm payment, collection or delivery, timing and any viewing or return arrangements with the artist.'),
('Keep the details','Save the agreed description and ask what receipt or documentation accompanies the artwork.')]
y=679
for title,body in items:
 c.setStrokeColor(clay);c.setLineWidth(1);c.rect(45,y-1,12,12,fill=0)
 c.setFillColor(green);c.setFont('PASansBold',12);c.drawString(69,y,title)
 c.setFont('PASans',11)
 for line in simpleSplit(body,'PASans',11,478):
  y-=16;c.drawString(69,y,line)
 y-=25
c.setFont('PASans',10);c.drawString(44,208,'Questions for the artist:')
c.setStrokeColor(HexColor('#C5C3B7'));c.line(44,190,551,190);c.line(44,171,551,171);c.line(44,152,551,152)
c.setFillColor(green);c.setFont('PASans',11)
c.drawString(44,133,'Artist / artwork: ___________________________________________________')
c.drawString(44,110,'Notes: ___________________________________________________________')
c.setFont('PASans',9)
c.drawString(44,79,'Explore the guide and free size calculator at plotnua.ie/plotart/')
c.linkURL('https://plotnua.ie/plotart/choose-art-for-living-room.html',(44,73,551,91),relative=0)
c.drawString(44,62,'PlotArt passes enquiries to artists. Any sale is arranged directly with the artist.')
c.drawString(44,45,'8 November 2026 | General buying guidance; confirm the details of the particular work.')
c.showPage();c.save();print(OUT)
