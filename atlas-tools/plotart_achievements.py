"""PlotArt · Exhibitions & Achievements: the publisher's twin of worker/plotart-studio/src/achievements.js (Phase C,
development 25 Nov 2026). The artist's free-form, optional section: headings ("## "), list items ("- ") and paragraphs, as
the Studio stores it. check() refuses anything the Studio would not have stored; to_html() writes exactly what the Studio's
toHtml() writes. Everything is escaped: the artist's text is never HTML."""
import html
import re

MAX, MAX_HEADING, MAX_ITEM, MAX_PARA, MAX_HEADINGS, MAX_ITEMS = 6000, 80, 400, 1200, 24, 200
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class Refused(ValueError):
    pass


def blocks(text):
    out, para, lst = [], None, None

    def end():
        nonlocal para, lst
        if para:
            out.append({"p": " ".join(para)})
        if lst:
            out.append({"ul": lst})
        para = lst = None

    for line in (text or "").split("\n"):
        if not line:
            end()
            continue
        if line.startswith("## "):
            end()
            out.append({"h": line[3:]})
            continue
        if line.startswith("- "):
            if para:
                end()
            lst = (lst or []) + [line[2:]]
            continue
        if lst:
            end()
        para = (para or []) + [line]
    end()
    return out


_HEAD = re.compile(r"^#{1,3}\s+")
_ITEM = re.compile(r"^[-*\u2022]\s+")
_WS = re.compile(r"\s+")


def normalise(v):
    """Exactly the Studio's normalise() (src/achievements.js): the stored text, or None when empty."""
    if v is None:
        return None
    if not isinstance(v, str) or _CTRL.search(v):
        raise Refused("achievements must be plain text")
    out = []
    for raw in v.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = _WS.sub(" ", raw).strip()
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        if _HEAD.match(line):
            t = re.sub(r"#+$", "", _HEAD.sub("", line, count=1)).strip()
            if t:
                if out and out[-1] != "":
                    out.append("")
                out += ["## " + t, ""]
            continue
        if _ITEM.match(line):
            t = _ITEM.sub("", line, count=1).strip()
            if t:
                out.append("- " + t)
            continue
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    text = "\n".join(out)
    if not text:
        return None
    bl = blocks(text)
    if (len(text) > MAX or sum(1 for b in bl if "h" in b) > MAX_HEADINGS or any("h" in b and len(b["h"]) > MAX_HEADING for b in bl)
            or sum(len(b["ul"]) for b in bl if "ul" in b) > MAX_ITEMS or any(len(i) > MAX_ITEM for b in bl if "ul" in b for i in b["ul"])
            or any("p" in b and len(b["p"]) > MAX_PARA for b in bl)):
        raise Refused("achievements exceeds the Studio's limits")
    return text


def check(text):
    """The publisher accepts only the Studio's stored form: text that normalise() leaves exactly as it is."""
    if not isinstance(text, str) or normalise(text) != text:
        raise Refused("achievements is not in the Studio's stored form")
    return text


def _esc(s):
    return html.escape(s, quote=True)


def to_html(text):
    parts = []
    for b in blocks(text):
        if "h" in b:
            parts.append("<h3>%s</h3>" % _esc(b["h"]))
        elif "p" in b:
            parts.append("<p>%s</p>" % _esc(b["p"]))
        else:
            parts.append("<ul>%s</ul>" % "".join("<li>%s</li>" % _esc(i) for i in b["ul"]))
    return "\n".join(parts)
