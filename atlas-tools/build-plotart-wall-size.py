#!/usr/bin/env python3
"""Build the reviewed PlotArt wall-size tool. No artist data, uploads or backend."""
import html
import re
import sys
from pathlib import Path
import plotart_seo as SEO
ROOT = Path(__file__).resolve().parent.parent
PATH = 'art-size-calculator.html'
TITLE = 'Art Size Calculator | What Size Art Fits My Wall? | PlotArt'
DESC = 'Compare artwork sizes above a sofa or on a clear wall. A free visual art size calculator in centimetres, with practical advice for choosing art for your home.'
BODY = '''
<section class="pa-guide-hero"><div class="pa-wrap">
<p class="pa-eyebrow">PlotArt · Make room for art</p>
<h1>What size art<br>fits your wall?</h1>
<p class="pa-lede">A small work can feel intimate. A large one can change a room. Try a few proportions before you decide.</p>
<p class="pa-guide-note">Free to use. No account, photograph or email address needed.</p>
<a class="pa-btn pa-btn--solid pa-size-start" href="#size-tool">Try your dimensions ↓</a>
</div></section>
<section class="pa-size-section" id="size-tool" aria-labelledby="toolH"><div class="pa-wrap">
<div class="pa-size-heading"><div><p class="pa-eyebrow">See the relationship</p><h2 id="toolH">Your space. Your scale.</h2></div><p>All measurements are in centimetres. Enter the <strong>outer size, including any frame</strong>, to compare the space it will occupy.</p></div>
<noscript><div class="pa-guide-callout"><p>The interactive comparison needs JavaScript. For a sofa 200 cm wide, two-thirds to three-quarters suggests an artwork or group about 133–150 cm wide. This is a starting point: check the wall, frame and clear height. Read the practical guide below.</p></div></noscript>
<div class="pa-size-app" data-size-app hidden>
<div class="pa-size-controls">
<fieldset><legend>01 · Measure your space</legend>
<label for="size-mode">Where will the art hang?</label><select id="size-mode"><option value="furniture">Above a sofa or console</option><option value="wall">On a clear wall</option></select>
<label for="size-reference" id="size-reference-label">Furniture width (cm)</label><input id="size-reference" type="number" min="30" max="1000" step="1" value="200" inputmode="decimal" aria-describedby="size-reference-help">
<p class="pa-size-help" id="size-reference-help">Measure the furniture from one outer edge to the other.</p>
<label for="size-room">Room height (cm)</label><input id="size-room" type="number" min="100" max="600" step="1" value="260" inputmode="decimal">
</fieldset>
<fieldset><legend>02 · Try an artwork size</legend>
<div class="pa-size-pair"><div><label for="size-width">Outer width (cm)</label><input id="size-width" type="number" min="5" max="1000" step="1" value="140" inputmode="decimal"></div><div><label for="size-height">Outer height (cm)</label><input id="size-height" type="number" min="5" max="600" step="1" value="90" inputmode="decimal"></div></div>
<p class="pa-size-help">Already found a work you love? Enter its dimensions and include the frame if one will be added.</p>
<div class="pa-size-presets" aria-label="Compare artwork widths"><button type="button" data-size-ratio="0.5">Half the width</button><button type="button" data-size-ratio="0.6666666666666666">Two-thirds</button><button type="button" data-size-ratio="0.8">Four-fifths</button></div>
<p class="pa-size-help">Width comparisons keep your entered height. They are suggestions to explore, rather than available products.</p>
</fieldset>
<fieldset><legend>03 · Change the mood</legend><div class="pa-size-themes" aria-label="Illustrated wall colour"><button type="button" data-size-theme="chalk" aria-pressed="true"><span class="pa-size-dot pa-size-dot--chalk" aria-hidden="true"></span>Chalk</button><button type="button" data-size-theme="green" aria-pressed="false"><span class="pa-size-dot pa-size-dot--green" aria-hidden="true"></span>Deep green</button><button type="button" data-size-theme="clay" aria-pressed="false"><span class="pa-size-dot pa-size-dot--clay" aria-hidden="true"></span>Soft clay</button></div></fieldset>
<p id="size-error" class="pa-size-error" role="status" hidden></p>
</div>
<div class="pa-size-preview-column">
<div class="pa-size-preview" data-size-scene data-theme="chalk">
<div class="pa-size-scene-head"><span>Illustrated scale comparison</span><strong id="size-dimensions">140 × 90 cm</strong></div>
<svg id="size-scene" viewBox="-20 -20 340 300" role="img" aria-labelledby="size-svg-title size-svg-desc"><title id="size-svg-title">Artwork size comparison</title><desc id="size-svg-desc">An outline of an artwork above furniture, using your entered dimensions.</desc><defs><pattern id="size-paper" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6L6 0" stroke="#b6a897" stroke-opacity=".1" stroke-width=".4"/></pattern></defs><rect id="size-wall" x="0" y="0" width="300" height="260" class="pa-size-wall"/><path id="size-floor" d="M0 250H300" class="pa-size-floor"/><g id="size-furniture"><rect id="size-sofa" x="50" y="185" width="200" height="65" rx="5" class="pa-size-sofa"/><path id="size-sofa-detail" d="M55 218H245 M150 190V218" class="pa-size-sofa-detail"/><text id="size-furniture-caption" x="150" y="240" text-anchor="middle" class="pa-size-furniture-caption">Furniture · 200 cm</text></g><g id="size-frame"><rect id="size-frame-outer" x="80" y="75" width="140" height="90" class="pa-size-frame"/><rect id="size-frame-paper" x="83" y="78" width="134" height="84" fill="url(#size-paper)"/><text id="size-frame-caption" x="150" y="120" text-anchor="middle" dominant-baseline="middle" class="pa-size-frame-caption">140 × 90 cm</text></g></svg>
<p class="pa-size-scene-note">The outline shows the outer artwork dimensions you entered.</p>
</div>
<div class="pa-size-result" aria-live="polite" aria-atomic="true"><p class="pa-eyebrow">A starting point</p><h3 id="size-range">Try 133–150 cm wide</h3><p id="size-explanation">For furniture 200 cm wide, two-thirds to three-quarters gives a useful range to compare.</p><p id="size-warning" class="pa-size-error" hidden></p></div>
<p class="pa-size-help" id="size-assumptions">The furniture is illustrated at 75 cm high with a 20 cm gap below the artwork. Check the actual furniture, clear wall space, ceiling and fixings before choosing or hanging a work.</p>
<div class="pa-size-share"><button class="pa-btn pa-btn--ghost" id="size-share" type="button">Copy this comparison ↗</button><button class="pa-size-reset" id="size-reset" type="button">Reset</button></div><p id="size-share-status" role="status" class="pa-size-help"></p><input id="size-share-link" type="text" readonly aria-label="Comparison link" hidden>
<p class="pa-size-help">The share link contains only these measurements and the wall-colour choice. The calculator uses your browser; it does not upload a room photograph or save a profile.</p>
</div></div></div></section>
<section class="pa-guide-section"><div class="pa-wrap pa-guide-reading"><p class="pa-eyebrow">Room to make your own decision</p><h2>What size art should go above a sofa?</h2><p>One useful starting point is a work or group spanning about two-thirds to three-quarters of the furniture width. A 200 cm sofa therefore suggests roughly 133–150 cm across. Smaller and larger choices can work too: the surrounding space, the work itself and the effect you want matter.</p><p>This proportion is a common guideline, also described in <a href="https://www.saatchiart.com/pages/art-for-the-living-room">Saatchi Art’s living-room art guide</a>. It is a styling suggestion, not a fitting or installation specification.</p><h3>For a clear wall</h3><p>Measure the usable space between corners, doors, windows, shelves and other obstructions. In clear-wall mode, the tool compares the entered artwork width with that usable width. It does not prescribe a particular proportion.</p><h3>For several artworks together</h3><p>Use the total outer width and height of the arrangement, including gaps between the frames. The outline then represents the whole group rather than a single work.</p><h3>Check the frame and the real wall</h3><p>Artists may list the artwork size without a frame. Confirm the outer dimensions before buying. Mark the outline with removable paper to judge the scale in your actual space. Ask about suitable fixings and professional installation where needed.</p></div></section>
<section class="pa-guide-section"><div class="pa-wrap pa-guide-reading"><h2>Find a work you want to live with.</h2><p>Once you have a sense of scale, explore the artists and their work. Read the medium, dimensions and availability on each artwork page, and ask the artist about framing and viewing.</p><div class="pa-guide-actions"><a class="pa-btn pa-btn--solid" href="gallery/">Explore the artist galleries →</a><a class="pa-btn pa-btn--ghost" href="buy-original-art-ireland.html">Buying original art &amp; prices →</a><a class="pa-btn pa-btn--ghost" href="large-artworks/">Large artworks →</a></div></div></section>
'''

def render():
    home = (ROOT/'plotart/index.html').read_text()
    header = re.search(r'<header class="pa-head.*?</header>', home, re.S).group(0).replace(' aria-current="page"','')
    footer = re.search(r'<footer class="pa-foot">.*?</footer>', home, re.S).group(0)
    head = home.split('<head>',1)[1].split('</head>',1)[0].replace('\n<link rel="stylesheet" href="assets/plotart-join.css">', '')  # the Join styles belong to the homepage invitation only (14 Nov 2026)
    head = re.sub(r'<title>.*?</title>','<title>'+html.escape(TITLE)+'</title>',head)
    for kind,key,value in [('name','description',DESC),('property','og:title',TITLE),('property','og:description',DESC),('name','twitter:title',TITLE),('name','twitter:description',DESC),('property','og:url',SEO.canonical(PATH))]:
        head = re.sub(r'<meta '+kind+'="'+key+'" content="[^"]*">','<meta '+kind+'="'+key+'" content="'+html.escape(value,quote=True)+'">',head)
    head = re.sub(r'<link rel="canonical" href="[^"]+">','<link rel="canonical" href="'+SEO.canonical(PATH)+'">',head)
    if not SEO.indexable(PATH,SEO.switches()):
        head=head.replace('<meta name="robots" content="index, follow">','<meta name="robots" content="noindex, follow">')
        head=re.sub(r'<link rel="canonical" href="[^"]+">\n?','',head)
    head += '<link rel="stylesheet" href="assets/plotart-guides.css">\n<link rel="stylesheet" href="assets/plotart-wall-size.css">\n'
    return '<!DOCTYPE html>\n<html lang="en-IE" class="no-js">\n<head>'+head+'</head>\n<body class="pa">\n<a class="pa-skip" href="#main">Skip to content</a>\n'+header+'\n<main id="main" class="pa-guide">'+BODY+'</main>\n'+footer+'\n<script src="assets/plotart.js" defer></script>\n<script src="assets/plotart-wall-size.js" defer></script>\n<script src="/assets/identity/pn-menu.js?v=1" defer></script>\n</body>\n</html>\n'
if __name__=='__main__':
    path=ROOT/'plotart'/PATH
    if '--check' in sys.argv:
        if not path.exists() or path.read_text()!=render():raise SystemExit('WALL SIZE · page differs from reviewed source')
        print('WALL SIZE · OK — exact reviewed page')
    else:path.write_text(render())
