"""PlotArt · Art for Hire, Version 3 (founder approval, 11 Nov 2026): the three illustrated environments.

The settings are drawn here in SVG (no photographs, stock or AI imagery). The only image is the founder's own painting,
plotart/assets/hero/founder-01-abstract.webp (FOUNDER_ORIGINAL_ARTWORK, registered for the surface plotart-art-for-hire),
placed unaltered over each drawing. Every scene is labelled "Illustration" and carries the painting's credit.
"""

ART = "../assets/hero/founder-01-abstract.webp"
CREDIT = "Painting by Colin Macaulay, PlotArt’s founder. Not offered for hire."
HERO_ALT = "An abstract painting: looping yellow and violet forms over pink and blue lines on grey."

FILM_BACK='''
<rect width="1600" height="900" fill="#0f1012"/>
<rect x="250" y="70" width="1100" height="590" fill="url(#fw)"/>
<rect x="250" y="70" width="1100" height="590" fill="url(#key)"/>
<path d="M616 70V660M984 70V660" stroke="#000" stroke-opacity=".28" stroke-width="2"/>
<rect x="250" y="626" width="1100" height="34" fill="#4a453f"/>
<path d="M0 660H1600V900H0z" fill="url(#ff)"/>
<path d="M640 760h40M660 740v40M940 770h40M960 750v40" stroke="#c9a640" stroke-opacity=".55" stroke-width="4"/>
<polygon points="40,40 210,0 760,560 360,700" fill="url(#beam)" opacity=".55" filter="url(#soft)"/>
<g fill="#08090a"><path d="M1458 900l8-214h10l8 214zM1408 900l63-110 63 110z"/><rect x="1400" y="590" width="150" height="96" rx="10"/><path d="M1400 606l-58-22v108l58-22z"/><rect x="1336" y="572" width="22" height="132" rx="4"/><rect x="1430" y="552" width="70" height="38" rx="4"/><circle cx="1508" cy="560" r="30"/><circle cx="1448" cy="548" r="22"/></g>
<g fill="#0b0c0d"><path d="M158 900l6-292h8l6 292zM110 900l58-104 58 104z"/><path d="M118 498h104l18 58v40H100v-40z"/><rect x="132" y="470" width="76" height="30" rx="4"/><path d="M104 520l-44-26M236 520l44-26" stroke="#0b0c0d" stroke-width="8"/></g>
<ellipse cx="170" cy="584" rx="120" ry="70" fill="url(#lens)"/>
'''
FILM_DEFS='''
<linearGradient id="fw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5b554d"/><stop offset="1" stop-color="#3d3934"/></linearGradient>
<radialGradient id="key" cx=".3" cy=".25" r=".8"><stop offset="0" stop-color="#ffe9c7" stop-opacity=".55"/><stop offset=".55" stop-color="#ffe2b5" stop-opacity=".12"/><stop offset="1" stop-color="#000" stop-opacity=".45"/></radialGradient>
<linearGradient id="ff" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c1b1a"/><stop offset="1" stop-color="#070708"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff3dd" stop-opacity=".7"/><stop offset="1" stop-color="#fff3dd" stop-opacity="0"/></linearGradient>
<radialGradient id="lens"><stop offset="0" stop-color="#fff6e2" stop-opacity=".95"/><stop offset=".35" stop-color="#fff0d2" stop-opacity=".45"/><stop offset="1" stop-color="#fff0d2" stop-opacity="0"/></radialGradient>
<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="28"/></filter><filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>'''

ROOM_BACK='''
<rect width="1600" height="900" fill="url(#rw)"/>
<rect width="1600" height="900" fill="url(#lamp)"/>
<rect y="690" width="1600" height="10" fill="#1d201d"/>
<path d="M0 700H1600V900H0z" fill="url(#oak)"/>
<g stroke="#000" stroke-opacity=".22" stroke-width="2"><path d="M800 700L620 900M800 700L320 900M800 700L20 900M800 700L980 900M800 700L1280 900M800 700L1580 900"/></g>
<ellipse cx="800" cy="812" rx="560" ry="62" fill="#a39886" opacity=".28"/>
<g><path d="M470 560q0-30 30-30h600q30 0 30 30v150H470z" fill="#2b2620"/><path d="M450 610q0-24 24-24h48v140h-72zM1078 586h48q24 0 24 24v116h-72z" fill="#231f1a"/><path d="M500 560h290v70H500zM810 560h290v70H810z" fill="#38302a"/><rect x="470" y="700" width="660" height="26" fill="#1a1714"/><path d="M500 726v14M1100 726v14" stroke="#0e0c0b" stroke-width="8"/>
<path d="M500 560h290M810 560h290" stroke="#5a4c40" stroke-opacity=".7" stroke-width="3"/></g>
<g><path d="M250 640h120l-12 86h-96z" fill="#1c1b19"/><path d="M290 640q-6-60 10-120q4 50-2 120zM312 640q10-80 50-150q-24 80-36 150z" fill="#30352c"/></g>
<g><path d="M1340 760h70v10h-70z" fill="#121211"/><path d="M1374 760V330q0-120-150-150" fill="none" stroke="#121211" stroke-width="7"/><path d="M1170 150h110l26 62h-162z" fill="#191816"/><ellipse cx="1225" cy="214" rx="78" ry="12" fill="#ffd9a0" opacity=".9" filter="url(#glow2)"/></g>
'''
ROOM_DEFS='''
<linearGradient id="rw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2b302c"/><stop offset="1" stop-color="#3a403a"/></linearGradient>
<radialGradient id="lamp" cx=".76" cy=".3" r=".7"><stop offset="0" stop-color="#ffcf8a" stop-opacity=".42"/><stop offset=".45" stop-color="#ffc77a" stop-opacity=".12"/><stop offset="1" stop-color="#000" stop-opacity=".35"/></radialGradient>
<linearGradient id="oak" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5a4330"/><stop offset="1" stop-color="#2a1e15"/></linearGradient>
<filter id="glow2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>'''

STAGE_BACK='''
<rect width="1600" height="900" fill="url(#sw)"/>
<g filter="url(#sun)" fill="#fff8ea" opacity=".85"><polygon points="120,40 420,40 760,620 460,620"/><polygon points="470,40 640,40 980,620 810,620"/></g>
<rect x="1240" y="110" width="250" height="590" fill="url(#door)"/><path d="M1240 700V110h250V700" fill="none" stroke="#b9ad9c" stroke-width="12"/>
<rect y="690" width="1600" height="12" fill="#c7bba9"/>
<path d="M0 700H1600V900H0z" fill="url(#pale)"/>
<g stroke="#7d6750" stroke-opacity=".25" stroke-width="2"><path d="M800 700L600 900M800 700L300 900M800 700L0 900M800 700L1000 900M800 700L1300 900M800 700L1600 900"/></g>
<polygon points="560,700 900,700 1240,900 760,900" fill="#fff8ea" opacity=".35" filter="url(#sun)"/>
<g><rect x="520" y="568" width="560" height="18" fill="#b08d66"/><path d="M548 586l-10 110M1052 586l10 110M560 586l18 108M1040 586l-18 108" stroke="#2c2620" stroke-width="5"/>
<path d="M600 568q0-44 44-44t44 44z" fill="#e8e1d6"/><path d="M604 560q40 10 80 0" stroke="#cfc6b8" stroke-width="3" fill="none"/>
<rect x="900" y="548" width="120" height="10" fill="#4f5a52"/><rect x="908" y="538" width="104" height="10" fill="#a8664a"/><rect x="904" y="558" width="112" height="10" fill="#d9d1c3"/>
<path d="M736 568l6-44h20l6 44z" fill="#5f5a52"/><path d="M752 526q-26-30-54-40M752 526q14-34 44-46M752 526q-2-30 4-52" stroke="#55614f" stroke-width="4" fill="none"/></g>
<g filter="url(#leaf)" fill="#5d5245" opacity=".22"><ellipse cx="300" cy="300" rx="70" ry="22" transform="rotate(-30 300 300)"/><ellipse cx="370" cy="250" rx="60" ry="18" transform="rotate(20 370 250)"/><ellipse cx="250" cy="390" rx="80" ry="20" transform="rotate(10 250 390)"/></g>
'''
STAGE_DEFS='''
<linearGradient id="sw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d3cabd"/><stop offset="1" stop-color="#bfb5a6"/></linearGradient>
<linearGradient id="door" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ece6dc"/><stop offset="1" stop-color="#fbf8f2"/></linearGradient>
<linearGradient id="pale" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#bda283"/><stop offset="1" stop-color="#8f7457"/></linearGradient>
<filter id="sun" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter><filter id="leaf" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10"/></filter>'''

def _scene(kind, defs, back, art_box, title, text, extra='', hud=''):
    x,y,w = art_box   # in 1600x900 stage units
    return f'''<figure class="afh3-scene afh3-scene--{kind}">
    <div class="afh3-view"><div class="afh3-stage">
      <svg class="afh3-env" viewBox="0 0 1600 900" preserveAspectRatio="none" aria-hidden="true" focusable="false"><defs>{defs}</defs>{back}</svg>
      <div class="afh3-tex" aria-hidden="true"></div>
      <img class="afh3-art" src="{ART}" alt="" loading="lazy" decoding="async" width="1332" height="940" style="left:{x/16}%;top:{y/9}%;width:{w/16}%">
      {extra}
      <div class="afh3-grain" aria-hidden="true"></div>
    </div>{hud}</div>
    <figcaption><p class="afh3-tag">Illustration</p><h3>{title}</h3><p>{text}</p><p class="afh3-credit">{CREDIT}</p></figcaption>
  </figure>'''

HUD='''<div class="afh3-hud" aria-hidden="true"><span class="afh3-rec">REC</span><span class="afh3-tc">01:12:08:14</span><span class="afh3-cam">A CAM&nbsp;&nbsp;35mm&nbsp;&nbsp;T2.8</span><span class="afh3-asp">2.39:1</span><i class="afh3-c afh3-c1"></i><i class="afh3-c afh3-c2"></i><i class="afh3-c afh3-c3"></i><i class="afh3-c afh3-c4"></i></div>'''
SUNLIGHT='<div class="afh3-sunlight" aria-hidden="true"></div>'

SCENES = (
  _scene('film', FILM_DEFS, FILM_BACK, (540,150,520), 'Film and television',
        'A real original on the set wall, lit and framed for the shot. For production designers, set decorators and art departments.', '', HUD) +
  _scene('room', ROOM_DEFS, ROOM_BACK, (602,170,396), 'Contemporary interiors',
        'A single strong work can carry a room. For interior designers dressing a home, an office or a hotel suite, for a season or an event.') +
  _scene('stage', STAGE_DEFS, STAGE_BACK, (612,150,376), 'Property staging',
        'Art makes a staged home feel lived in, and photographs better. For property stagers preparing a home for viewings and listing photographs.', SUNLIGHT)
)
