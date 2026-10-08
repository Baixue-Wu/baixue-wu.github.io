"""Render the profile's animated SVGs from media/ and fonts/.

Every SVG is self-contained: frames are embedded as JPEG data, text is drawn as
outlines, and motion is CSS keyframes, which GitHub plays inside <img>. Viewers
who ask for reduced motion get a still page.
"""

import argparse
import base64
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from .text import Face, Fonts

BG = "#0b0b0d"
PANEL = "#121216"
LINE = "#26262c"
INK = "#ece6dc"
MUTED = "#8a8590"
DIM = "#4a4750"
CYAN = "#7ee0d2"
AMBER = "#f2a65a"
LIME = "#d2e679"

BASE_CSS = """
@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
.fb { transform-box: fill-box; transform-origin: center; }
"""

WORKS = {
    "jimo": ("寂寞花芳", "LONELY FLOWER"),
    "cyber": ("高空馄饨摊", "AI SHORT"),
    "dog": ("晒被子吃西瓜", "AI ANIMATION"),
    "sher": ("MoCoCo", "SHERLOCK JR."),
    "ootd": ("秋日穿搭", "AI FASHION"),
}


class Media:
    def __init__(self, folder: Path):
        self.folder = folder
        index = folder / "media.json"
        if not index.exists():
            raise FileNotFoundError(f"{index} missing; run profile-extract first")
        self.data = json.loads(index.read_text())

    def frame(self, key: str) -> dict:
        return self.data["frames"].get(key) or self.data["stills"][key]

    def uri(self, key: str) -> str:
        raw = (self.folder / self.frame(key)["file"]).read_bytes()
        return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def doc(w: int, h: int, label: str, css: str, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">'
            f"<title>{label}</title><style>{BASE_CSS}{css}</style>{body}</svg>")


def text(face: Face, s: str, size: float, x: float, y: float, fill: str,
         anchor: str = "start", tracking: float = 0, extra: str = "") -> str:
    return f'<path d="{face.path(s, size, x, y, anchor, tracking)}" fill="{fill}" {extra}/>'


def luminance(hex_: str) -> float:
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


def hsv(hex_: str) -> tuple[float, float, float]:
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = 60 * (((g - b) / d) % 6)
    elif mx == g:
        h = 60 * ((b - r) / d + 2)
    else:
        h = 60 * ((r - g) / d + 4)
    return h, (d / mx if mx else 0.0), mx


GRAIN = ('<filter id="grain" x="0" y="0" width="100%" height="100%">'
         '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>'
         '<feColorMatrix type="saturate" values="0"/>'
         '<feComponentTransfer><feFuncA type="linear" slope="0.07"/></feComponentTransfer></filter>')


def grain(w: int, h: int, rx: int) -> str:
    return (f'<rect class="grain" width="{w}" height="{h}" rx="{rx}" filter="url(#grain)"/>')


def card_frame(w: int, h: int, accent: str, kicker: str, title: str, lines: list[str],
               tags: str, f: Fonts) -> tuple[str, str]:
    """Background and caption block shared by every project card."""
    back = (f'<rect width="{w}" height="{h}" rx="16" fill="{PANEL}"/>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="15.5" fill="none" stroke="{LINE}"/>')
    y0 = h - 112
    front = text(f.mono, kicker, 11, 30, 30, accent, tracking=1.5)
    front += f'<rect x="30" y="{y0 - 34}" width="{w - 60}" height="1" fill="{LINE}"/>'
    front += text(f.serif_cjk if any(ord(c) > 127 for c in title) else f.serif,
                  title, 28 if any(ord(c) > 127 for c in title) else 34, 30, y0, INK)
    for i, ln in enumerate(lines):
        front += text(f.sans_cjk, ln, 14.5, 30, y0 + 28 + i * 22, MUTED if i else "#c9c3ba")
    front += text(f.mono, tags, 10.5, 30, h - 22, DIM, tracking=1.2)
    return back, front


# ------------------------------------------------------------------ hero

def hero(m: Media, f: Fonts) -> str:
    W, H = 1200, 640
    ids = [k for k in m.data["frames"] if k.split("-")[0] in WORKS and k.split("-")[1].isdigit()]
    slot, size, top = 200, 180, 112
    seq_w = slot * len(ids)
    scan = 600

    defs = GRAIN
    defs += (f'<clipPath id="filmSide"><rect x="{scan}" y="0" width="{W - scan}" height="{H}"/></clipPath>'
             f'<clipPath id="dataSide"><rect x="0" y="0" width="{scan}" height="{H}"/></clipPath>'
             f'<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>')
    defs += ('<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
             f'<stop offset="0.5" stop-color="#ffffff" stop-opacity="0.9"/>'
             f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>'
             '<radialGradient id="vignette" cx="0.5" cy="0.45" r="0.75">'
             '<stop offset="0.6" stop-color="#000" stop-opacity="0"/>'
             '<stop offset="1" stop-color="#000" stop-opacity="0.55"/></radialGradient>'
             '<filter id="glow" x="-50%" y="-10%" width="200%" height="120%">'
             '<feGaussianBlur stdDeviation="6"/></filter>')

    def edge(i: int, key: str) -> str:
        zh, en = WORKS[key.split("-")[0]]
        x = i * slot + 10
        return (text(f.mono, f"{i + 1:02d}", 9, x, top - 10, DIM, tracking=1) +
                text(f.sans_cjk, zh, 9.5, x + 20, top - 10, "#6d6873") +
                text(f.mono, en, 8, x + size, top - 10, DIM, "end", 1))

    sprockets = "".join(
        f'<rect x="{i * 25 + 5}" y="{y}" width="14" height="9" rx="2" fill="{BG}"/>'
        for i in range(seq_w // 25) for y in (92, top + size + 12))
    film_seq, data_seq, edges = "", "", ""
    for i, key in enumerate(ids):
        x = i * slot + 10
        defs += f'<image id="im{i}" width="{size}" height="{size}" xlink:href="{m.uri(key)}"/>'
        film_seq += f'<use xlink:href="#im{i}" x="{x}" y="{top}"/>'
        edges += edge(i, key)
        pal = sorted(m.frame(key)["palette"], key=lambda c: luminance(c["hex"]))
        cx = x
        bars = ""
        for c in pal:
            w = c["share"] * size
            bars += f'<rect x="{cx:.1f}" y="{top}" width="{w + 0.4:.1f}" height="{size}" fill="{c["hex"]}"/>'
            cx += w
        dom = max(pal, key=lambda c: c["share"])["hex"]
        h_, s_, v_ = hsv(dom)
        tone = "#111" if luminance(dom) > 0.55 else INK
        info = (text(f.mono_bold, dom.upper(), 11, x + 8, top + size - 26, tone, tracking=0.5) +
                text(f.mono, f"H{h_:03.0f} S{s_ * 100:02.0f} V{v_ * 100:02.0f}", 9, x + 8, top + size - 12, tone))
        data_seq += bars + info
    defs += (f'<g id="filmSeq">{film_seq}</g><g id="dataSeq">{data_seq}</g>'
             f'<g id="edgeSeq">{sprockets}{edges}</g>')

    def reel(seq: str) -> str:
        return (f'<g class="reel"><use xlink:href="#{seq}"/>'
                f'<use xlink:href="#{seq}" x="{seq_w}"/></g>')

    css = f"""
.reel {{ animation: reel {len(ids) * 4}s linear infinite; }}
@keyframes reel {{ to {{ transform: translateX(-{seq_w}px); }} }}
.beam {{ animation: flicker 2.6s ease-in-out infinite; }}
@keyframes flicker {{ 0%,100% {{ opacity: .85; }} 45% {{ opacity: 1; }} 50% {{ opacity: .55; }} 55% {{ opacity: 1; }} }}
.shine {{ animation: shine 6s ease-in-out infinite; }}
.shine.b {{ animation-delay: 3s; }}
@keyframes shine {{ 0% {{ transform: translateX(-320px); }} 60%,100% {{ transform: translateX(320px); }} }}
.measure {{ animation: measure 7s cubic-bezier(.6,0,.2,1) infinite; transform-origin: 0 0; }}
@keyframes measure {{ 0% {{ transform: scaleX(0); }} 55%,85% {{ transform: scaleX(1); }} 100% {{ transform: scaleX(0); opacity: 0; }} }}
.wave rect {{ animation: wave 1.4s ease-in-out infinite alternate; }}
@keyframes wave {{ from {{ transform: scaleY(.15); }} to {{ transform: scaleY(1); }} }}
.digits {{ animation: tick 10s steps(10) infinite; }}
.digits.tens {{ animation: tick6 60s steps(6) infinite; }}
@keyframes tick {{ to {{ transform: translateY(-160px); }} }}
@keyframes tick6 {{ to {{ transform: translateY(-96px); }} }}
.dot {{ animation: blink 1.2s steps(2) infinite; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
"""

    body = f'<defs>{defs}</defs><g clip-path="url(#card)">'
    body += f'<rect width="{W}" height="{H}" fill="{BG}"/>'
    # header
    body += text(f.serif_cjk, "吴白雪", 30, 56, 58, INK, tracking=4)
    nx = 56 + f.serif_cjk.width("吴白雪", 30, 4) + 16
    body += text(f.italic, "Baixue Wu", 32, nx, 58, "#c9c3ba")
    body += text(f.mono, "DATA SCIENCE BSc  /  FILM & DRAMA MA  /  HCI @ UCL", 11.5, W - 56, 54, MUTED,
                 "end", 1.2)
    # film strip
    body += f'<rect x="0" y="86" width="{W}" height="{size + 50}" fill="#050506"/>'
    body += reel("edgeSeq")
    body += f'<g clip-path="url(#dataSide)">{reel("dataSeq")}</g>'
    body += f'<g clip-path="url(#filmSide)">{reel("filmSeq")}</g>'
    # scanner
    body += (f'<g class="beam"><rect x="{scan - 18}" y="80" width="36" height="{size + 62}" '
             f'fill="url(#beam)" filter="url(#glow)" opacity=".55"/>'
             f'<rect x="{scan - 1}" y="70" width="2" height="{H - 110}" fill="#fff" opacity=".9"/></g>')
    body += text(f.mono, "MEASURED", 10.5, scan - 14, 340, CYAN, "end", 2)
    body += text(f.mono, "WATCHED", 10.5, scan + 14, 340, AMBER, "start", 2)
    # slogan, two columns split by the scanner
    for cx, small, big, color, en, cls in (
        (300, "以算法与数据", "测量内容", CYAN, "ALGORITHMS & DATA  >  CONTENT", "a"),
        (900, "以视听与审美", "理解用户", AMBER, "SOUND, IMAGE & TASTE  >  PEOPLE", "b"),
    ):
        body += text(f.serif_cjk, small, 30, cx, 408, "#c9c3ba", "middle", 6)
        bw = f.serif_cjk.width(big, 66, 10)
        clip = f"word{cls}"
        body += (f'<clipPath id="{clip}"><path d="{f.serif_cjk.path(big, 66, cx, 486, "middle", 10)}"/></clipPath>'
                 f'<g clip-path="url(#{clip})"><rect x="{cx - bw / 2 - 10}" y="420" width="{bw + 20}" height="80" fill="{color}"/>'
                 f'<rect class="shine {cls}" x="{cx - 40}" y="420" width="80" height="80" fill="#fff" opacity=".55" '
                 f'transform="skewX(-20)"/></g>')
        body += text(f.mono, en, 11, cx, 548, MUTED, "middle", 1.5)
    # underline motifs: a film barcode on the data side, a sound wave on the film side
    bar = m.data["barcodes"]["jimo"]
    bx, bwid = 300 - 150, 300
    stripes = "".join(f'<rect x="{bx + i * bwid / len(bar):.2f}" y="510" width="{bwid / len(bar) + 0.3:.2f}" '
                      f'height="10" fill="{c}"/>' for i, c in enumerate(bar))
    body += f'<g class="measure" style="transform-origin:{bx}px 0">{stripes}</g>'
    rng = np.random.default_rng(7)
    wave = "".join(
        f'<rect class="fb" x="{750 + i * 6}" y="505" width="3" height="20" rx="1.5" fill="{AMBER}" '
        f'style="animation-delay:-{rng.uniform(0, 1.4):.2f}s;opacity:{0.45 + 0.55 * math.sin(math.pi * i / 49):.2f}"/>'
        for i in range(50))
    body += f'<g class="wave">{wave}</g>'
    # footer row: blinking lamp and a running seconds counter
    body += f'<circle class="dot" cx="62" cy="600" r="4" fill="#e5484d"/>'
    body += text(f.mono, "PROJECTING", 10.5, 74, 604, MUTED, tracking=2)
    body += text(f.mono, "TC 00:00:", 11, W - 80, 604, MUTED, "end", 1)
    digits = "".join(text(f.mono, str(d % 10), 11, 0, 16 * (d + 1), INK) for d in range(11))
    tens = "".join(text(f.mono, str(d % 6), 11, 0, 16 * (d + 1), INK) for d in range(7))
    body += (f'<clipPath id="tc"><rect x="{W - 80}" y="592" width="20" height="16"/></clipPath>'
             f'<g clip-path="url(#tc)"><g transform="translate({W - 79},592) translate(0,-4)">'
             f'<g class="digits tens">{tens}</g></g>'
             f'<g transform="translate({W - 71},592) translate(0,-4)"><g class="digits">{digits}</g></g></g>')
    body += text(f.mono, "REEL 01 / 2026", 10.5, W / 2, 604, DIM, "middle", 2)
    body += f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>' + grain(W, H, 18)
    body += "</g>"
    return doc(W, H, "Baixue Wu: measure content with algorithms and data, understand people through sound, image and taste", css, body)


# ------------------------------------------------------------------ section headers

def section(index: str, zh: str, en: str, color: str, motif: str, m: Media, f: Fonts) -> str:
    W, H = 1200, 150
    css = """
.mv { animation: drift 30s linear infinite; }
@keyframes drift { to { transform: translateX(-600px); } }
.wv rect { animation: wave 1.6s ease-in-out infinite alternate; }
@keyframes wave { from { transform: scaleY(.1); } to { transform: scaleY(1); } }
"""
    body = f'<rect width="{W}" height="{H}" rx="16" fill="{BG}"/>'
    body += text(f.italic, index, 96, 30, 112, color, extra='opacity=".9"')
    body += text(f.serif_cjk, zh, 40, 150, 86, INK, tracking=6)
    body += text(f.mono, en, 11.5, 152, 116, MUTED, tracking=2)
    body += f'<clipPath id="m"><rect x="640" y="40" width="530" height="70" rx="6"/></clipPath>'
    if motif == "barcode":
        bar = m.data["barcodes"]["jimo"]
        unit = 600 / len(bar)
        stripes = "".join(f'<rect x="{640 + i * unit:.2f}" y="40" width="{unit + 0.3:.2f}" height="70" fill="{c}"/>'
                          for i, c in enumerate(bar + bar))
        body += (f'<g clip-path="url(#m)"><g class="mv">{stripes}</g>'
                 f'<rect x="640" y="40" width="530" height="70" fill="{BG}" opacity=".25"/></g>')
        body += text(f.sans_cjk, "《寂寞花芳》全片", 10, 1170, 128, DIM, "end")
        body += text(f.mono, "FULL-FILM BARCODE", 9.5, 1170 - f.sans_cjk.width("《寂寞花芳》全片", 10) - 10,
                     128, DIM, "end", 1.5)
    else:
        rng = np.random.default_rng(3)
        bars = "".join(
            f'<rect class="fb" x="{646 + i * 9}" y="45" width="4" height="60" rx="2" fill="{color}" '
            f'style="animation-delay:-{rng.uniform(0, 1.6):.2f}s;opacity:{0.35 + 0.65 * math.sin(math.pi * i / 58):.2f}"/>'
            for i in range(59))
        body += f'<g class="wv">{bars}</g>'
        body += text(f.mono, "VOICE, IMAGE, TASTE", 9.5, 1170, 128, DIM, "end", 1.5)
    return doc(W, H, f"{index} {zh}", css, body)


# ------------------------------------------------------------------ measure cards

def card_color(m: Media, f: Fonts) -> str:
    W, H = 600, 440
    back, front = card_frame(W, H, CYAN, "MEASURE / 01  COLOUR", "赛博朋克动画色彩研究",
                             ["中日美三国作品的明度、饱和度与色相比较", "第一作者 · 《电影评介》（中文核心）"],
                             "MOVIE BARCODE  /  K-MEANS  /  HSV", f)
    key = "cyber-wide"
    pal = m.frame(key)["palette"]
    css = """
.grow { animation: grow 6s cubic-bezier(.6,0,.2,1) infinite; transform-origin: 30px 0; }
@keyframes grow { 0% { transform: scaleX(0); } 40%,85% { transform: scaleX(1); } 100% { transform: scaleX(1); opacity: 0; } }
.orbit { animation: spin 60s linear infinite; transform-origin: 470px 140px; }
@keyframes spin { to { transform: rotate(360deg); } }
.p { animation: pulse 2.4s ease-in-out infinite; }
@keyframes pulse { 50% { transform: scale(1.5); } }
"""
    body = back
    body += (f'<clipPath id="ph"><rect x="30" y="48" width="320" height="180" rx="6"/></clipPath>'
             f'<image x="30" y="48" width="320" height="180" clip-path="url(#ph)" xlink:href="{m.uri(key)}" preserveAspectRatio="xMidYMid slice"/>')
    x = 30.0
    stripes = ""
    for c in sorted(pal, key=lambda c: luminance(c["hex"])):
        w = c["share"] * 320
        stripes += f'<rect x="{x:.1f}" y="240" width="{w + 0.3:.1f}" height="34" fill="{c["hex"]}"/>'
        x += w
    body += f'<g class="grow">{stripes}</g>'
    # hue histogram of every pixel (weighted by saturation and value) around a ring,
    # with the k-means palette placed inside by hue (angle) and saturation (radius)
    cx, cy, r = 470, 140, 62
    hsv_px = np.asarray(Image.open(m.folder / m.frame(key)["file"]).convert("HSV"), dtype=np.float64).reshape(-1, 3)
    weight = (hsv_px[:, 1] / 255) * (hsv_px[:, 2] / 255)
    hist = np.bincount((hsv_px[:, 0] * 72 / 256).astype(int), weights=weight, minlength=72)
    hist = hist / hist.max()
    ring = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}"/>'
    for i, v in enumerate(hist):
        a = math.radians(i * 5 - 90)
        r2 = r + 4 + v * 34
        ring += (f'<line x1="{cx + (r + 3) * math.cos(a):.1f}" y1="{cy + (r + 3) * math.sin(a):.1f}" '
                 f'x2="{cx + r2 * math.cos(a):.1f}" y2="{cy + r2 * math.sin(a):.1f}" '
                 f'stroke="hsl({i * 5:.0f},75%,62%)" stroke-width="3.2" stroke-linecap="round"/>')
    dots = ""
    for i, c in enumerate(pal):
        h_, s_, v_ = hsv(c["hex"])
        a = math.radians(h_ - 90)
        rr = 8 + s_ * (r - 14)
        dots += (f'<circle class="p fb" cx="{cx + rr * math.cos(a):.1f}" cy="{cy + rr * math.sin(a):.1f}" '
                 f'r="{4 + c["share"] * 18:.1f}" fill="{c["hex"]}" stroke="{INK}" stroke-width="1" '
                 f'style="animation-delay:{i * .4}s"/>')
    body += f'<g class="orbit">{ring}</g>{dots}'
    body += f'<circle cx="{cx}" cy="{cy}" r="2" fill="{INK}"/>'
    dom = pal[0]["hex"]
    h_, s_, v_ = hsv(dom)
    body += text(f.mono, f"{dom.upper()}  H{h_:.0f} S{s_ * 100:.0f} V{v_ * 100:.0f}", 10, 470, 258, CYAN, "middle", 1)
    body += text(f.sans_cjk, "示例画面：她的 AI 短片《高空馄饨摊》", 10.5, 470, 276, DIM, "middle")
    body += front
    return doc(W, H, "Colour research on cyberpunk animation", css, body)


def card_boxoffice(m: Media, f: Fonts) -> str:
    W, H = 600, 440
    back, front = card_frame(W, H, CYAN, "MEASURE / 02  BOX OFFICE", "喜剧电影票房影响因素研究",
                             ["931 部喜剧电影：导演产出与类型融合显著预测票房", "独立作者 · 《喜剧世界》"],
                             "TF-IDF  /  PEARSON  /  MULTIPLE REGRESSION", f)
    rng = np.random.default_rng(931)
    n = 931
    xs = rng.beta(2, 3, n)
    ys = np.clip(0.15 + 0.6 * xs + rng.normal(0, 0.13, n), 0.02, 0.98)
    groups = [""] * 8
    for i in range(n):
        groups[i % 8] += f'<circle cx="{40 + xs[i] * 520:.1f}" cy="{270 - ys[i] * 220:.1f}" r="1.9"/>'
    css = """
.g { animation: fade 8s ease-in-out infinite; }
@keyframes fade { 0% { opacity: 0; } 25%,85% { opacity: .8; } 100% { opacity: 0; } }
.fit { stroke-dasharray: 560; animation: draw 8s cubic-bezier(.6,0,.2,1) infinite; }
@keyframes draw { 0%,30% { stroke-dashoffset: 560; } 60%,85% { stroke-dashoffset: 0; } 100% { stroke-dashoffset: 0; opacity: 0; } }
"""
    body = back
    body += f'<path d="M40 270 H570 M40 270 V44" stroke="{LINE}" fill="none"/>'
    for i, g in enumerate(groups):
        body += f'<g class="g" fill="{CYAN}" style="animation-delay:{i * .18:.2f}s">{g}</g>'
    body += (f'<path class="fit" d="M40 {270 - 0.15 * 220} L560 {270 - 0.75 * 220}" stroke="{AMBER}" '
             f'stroke-width="2.5" fill="none"/>')
    body += text(f.mono, "n = 931", 10, 560, 60, MUTED, "end", 1)
    body += front
    return doc(W, H, "Box office study of 931 comedy films", css, body)


def card_jia(m: Media, f: Fonts) -> str:
    W, H = 600, 440
    back, front = card_frame(W, H, CYAN, "MEASURE / 03  SUBTITLES", "贾樟柯地缘电影的文化研究",
                             ["6 部电影字幕的主题与情绪变化 · 数字人文视角", "第二届“地缘杯”中国电影青年学者优秀论文奖 三等奖"],
                             "JIEBA  /  SNOWNLP  /  LDA", f)
    rng = np.random.default_rng(6)
    pts = []
    for i in range(121):
        t = i / 120
        v = 0.5 + 0.22 * math.sin(t * 13) + 0.12 * math.sin(t * 31 + 1) + rng.normal(0, 0.03)
        pts.append((40 + t * 520, 250 - v * 190))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = d + " L560,250 L40,250 Z"
    css = """
.curve { stroke-dasharray: 900; animation: draw 9s ease-in-out infinite; }
@keyframes draw { 0% { stroke-dashoffset: 900; } 55%,85% { stroke-dashoffset: 0; } 100% { stroke-dashoffset: 0; opacity: 0; } }
.sweep { animation: sweep 9s ease-in-out infinite; }
@keyframes sweep { 0% { transform: translateX(0); } 55%,100% { transform: translateX(520px); } }
.t { animation: bob 5s ease-in-out infinite alternate; }
@keyframes bob { to { transform: translateY(-6px); } }
"""
    body = back
    body += ('<linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{CYAN}" stop-opacity=".25"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>')
    for i in range(6):
        x = 40 + i * 520 / 6
        body += f'<rect x="{x:.1f}" y="52" width="{520 / 6 - 4:.1f}" height="198" fill="#ffffff" opacity="{0.018 + 0.012 * (i % 2)}"/>'
        body += text(f.mono, f"FILM {i + 1:02d}", 9, x + 6, 66, DIM, tracking=1)
    body += f'<path d="{area}" fill="url(#fill)"/>'
    body += f'<path class="curve" d="{d}" stroke="{CYAN}" stroke-width="2" fill="none"/>'
    body += f'<g class="sweep"><rect x="40" y="52" width="1" height="198" fill="{AMBER}" opacity=".7"/></g>'
    body += front
    return doc(W, H, "Subtitle sentiment and topics in Jia Zhangke films", css, body)


def card_nexthook(m: Media, f: Fonts) -> str:
    W, H = 600, 440
    back, front = card_frame(W, H, CYAN, "MEASURE / 04  PRODUCT", "NextHook",
                             ["帮创作者从过去的内容数据里，找到下一条该试什么", "基于 Microsoft Data Formulator 改造的产品原型"],
                             "CREATOR ANALYTICS  /  SERIES COMPARISON  /  AI AGENT", f)
    rng = np.random.default_rng(12)
    series = [("影评", 0.62), ("盘点", 0.44), ("幕后", 0.30), ("解说", 0.52), ("短评", 0.38)]
    css = """
.bar { animation: rise 7s cubic-bezier(.6,0,.2,1) infinite; transform-origin: 0 250px; }
@keyframes rise { 0% { transform: scaleY(0); } 35%,85% { transform: scaleY(1); } 100% { transform: scaleY(1); opacity: 0; } }
.pt { animation: pop 7s ease-out infinite; }
@keyframes pop { 0%,30% { opacity: 0; } 45%,85% { opacity: .9; } 100% { opacity: 0; } }
.hot { animation: ring 1.8s ease-out infinite; }
@keyframes ring { from { transform: scale(.6); opacity: 1; } to { transform: scale(2.6); opacity: 0; } }
"""
    body = back
    body += f'<path d="M40 250 H560" stroke="{LINE}"/>'
    bw = 520 / len(series)
    for i, (name, med) in enumerate(series):
        x = 40 + i * bw + 18
        h = med * 190
        body += (f'<rect class="bar" x="{x:.1f}" y="{250 - h:.1f}" width="{bw - 36:.1f}" height="{h:.1f}" '
                 f'fill="{CYAN}" opacity=".18" style="animation-delay:{i * .12:.2f}s"/>')
        body += f'<rect x="{x:.1f}" y="{250 - h:.1f}" width="{bw - 36:.1f}" height="2" fill="{CYAN}"/>'
        for j in range(9):
            v = np.clip(med + rng.normal(0, 0.12), 0.05, 0.95)
            body += (f'<circle class="pt" cx="{x + 8 + rng.uniform(0, bw - 52):.1f}" cy="{250 - v * 190:.1f}" r="3" '
                     f'fill="{INK}" style="animation-delay:{i * .12 + j * .03:.2f}s"/>')
        body += text(f.sans_cjk, name, 12, x + (bw - 36) / 2, 270, MUTED, "middle")
    ox, oy = 40 + bw + 18 + 30, 250 - 0.97 * 190
    body += f'<circle class="hot fb" cx="{ox}" cy="{oy}" r="6" fill="none" stroke="{AMBER}" stroke-width="2"/>'
    body += f'<circle cx="{ox}" cy="{oy}" r="4" fill="{AMBER}"/>'
    body += text(f.mono, "OUTLIER", 9, ox + 12, oy + 3, AMBER, tracking=1)
    body += text(f.mono, "MEDIAN VIEWS PER SERIES  (SAMPLE DATA)", 9, 560, 60, DIM, "end", 1)
    body += front
    return doc(W, H, "NextHook creator analytics", css, body)


# ------------------------------------------------------------------ understand cards

def card_mococo(m: Media, f: Fonts) -> str:
    W, H = 600, 440
    back, front = card_frame(W, H, AMBER, "UNDERSTAND / 01  CO-CREATION", "MoCoCo",
                             ["人机共创电影解说：写下解说稿，系统找出匹配的镜头", "UCL 人机交互研究项目 · 提出四条设计准则 · 可在线试用"],
                             "SCRIPT  >  SHOT RETRIEVAL  >  ROUGH CUT  >  VOICE", f)
    lines = ["别人看电影，他直接钻进银幕！", "想找出真相，谁知一路跟到火车旁。", "他的位置没动，布景却不停换。"]
    keys = ["mococo-a", "mococo-b", "mococo-c"]
    css = """
.ln { animation: hl 9s infinite; opacity: .25; }
@keyframes hl { 0%,30% { opacity: 1; } 34%,100% { opacity: .25; } }
.wire { stroke-dasharray: 220; animation: wire 9s infinite; }
@keyframes wire { 0% { stroke-dashoffset: 220; opacity: 1; } 12%,30% { stroke-dashoffset: 0; opacity: 1; } 34%,100% { stroke-dashoffset: 0; opacity: 0; } }
.fr { animation: fr 9s infinite; opacity: 0; }
@keyframes fr { 0%,8% { opacity: 0; } 14%,30% { opacity: 1; } 34%,100% { opacity: 0; } }
"""
    body = back
    for i, (ln, key) in enumerate(zip(lines, keys)):
        y = 60 + i * 82
        delay = f"animation-delay:{i * 3}s"
        body += f'<g class="ln" style="{delay}">'
        body += text(f.mono, f"{i + 1:02d}", 10, 30, y + 34, AMBER, tracking=1)
        body += text(f.sans_cjk, ln, 14.5, 58, y + 34, INK)
        body += "</g>"
        fx, fy = 452, y + 2
        body += (f'<image x="{fx}" y="{fy}" width="100" height="75" xlink:href="{m.uri(key)}" '
                 f'preserveAspectRatio="xMidYMid slice" opacity=".85"/>')
        body += f'<rect class="fr" x="{fx - 2}" y="{fy - 2}" width="104" height="79" fill="none" stroke="{AMBER}" stroke-width="2" style="{delay}"/>'
        sx = 58 + f.sans_cjk.width(ln, 14.5) + 10
        body += (f'<path class="wire" d="M{sx:.0f},{y + 29} C{(sx + fx) / 2:.0f},{y + 29} {(sx + fx) / 2:.0f},{fy + 37} {fx - 6},{fy + 37}" '
                 f'stroke="{AMBER}" stroke-width="1.5" fill="none" style="{delay}"/>')
    body += front
    return doc(W, H, "MoCoCo movie commentary co-creation", css, body)


def land_path(geojson: Path, x0: float, y0: float, scale: float, lat_top: float, lat_bottom: float) -> str:
    g = json.loads(geojson.read_text())
    parts = []
    for feat in g["features"]:
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            ring = poly[0]
            pts, last = [], None
            for lon, lat in ring:
                if lat < lat_bottom:
                    lat = lat_bottom
                p = (round(x0 + (lon + 180) * scale), round(y0 + (lat_top - lat) * scale))
                if p != last:
                    pts.append(p)
                    last = p
            if len(pts) >= 4:
                parts.append("M" + " ".join(f"{x},{y}" for x, y in pts) + "Z")
    return "".join(parts)


def card_cineatlas(m: Media, f: Fonts, geojson: Path, destinations: Path) -> str:
    W, H = 600, 440
    dests = json.loads(destinations.read_text())
    back, front = card_frame(W, H, LIME, "UNDERSTAND / 02  CULTURE", "映游 CineAtlas",
                             ["跟着电影，走进一个地方：给旅行者的电影文化地图",
                              f"{len(dests)} 个目的地 · 按地点与年代探索电影里的日常与文化"],
                             "MAP  /  TIMELINE  /  CULTURE THROUGH CINEMA", f)
    scale, lat_top, lat_bottom = 1.5, 80, -58
    x0, y0 = 30, 52
    css = """
.ping { animation: ping 3s ease-out infinite; }
@keyframes ping { from { transform: scale(.4); opacity: .9; } to { transform: scale(3); opacity: 0; } }
.route { stroke-dasharray: 4 6; animation: march 1.2s linear infinite; }
@keyframes march { to { stroke-dashoffset: -10; } }
"""
    body = back
    body += f'<path d="{land_path(geojson, x0, y0, scale, lat_top, lat_bottom)}" fill="#1d2622" stroke="#2c3a33" stroke-width=".6"/>'
    pts = [(x0 + (d["longitude"] + 180) * scale, y0 + (lat_top - d["latitude"]) * scale) for d in dests]
    order = sorted(range(len(pts)), key=lambda i: pts[i][0])
    route = "M" + " ".join(f"{pts[i][0]:.1f},{pts[i][1]:.1f}" for i in order)
    body += f'<path class="route" d="{route}" stroke="{LIME}" stroke-width="1" fill="none" opacity=".45"/>'
    for i, (x, y) in enumerate(pts):
        body += (f'<circle class="ping fb" cx="{x:.1f}" cy="{y:.1f}" r="6" fill="none" stroke="{LIME}" '
                 f'stroke-width="1.5" style="animation-delay:{i * .37:.2f}s"/>')
        body += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{LIME}"/>'
    for d, (x, y) in zip(dests, pts):
        if d["id"] in ("paris", "tokyo", "dakar", "mexico-city", "mumbai"):
            body += text(f.sans_cjk, d["name"], 10.5, x + 7, y - 6, "#b9c28f")
    body += front
    return doc(W, H, "CineAtlas film culture map", css, body)


def card_inkmuse(m: Media, f: Fonts) -> str:
    W, H = 600, 440
    back, front = card_frame(W, H, AMBER, "UNDERSTAND / 03  WRITING", "InkMuse",
                             ["写好的文字，自动排成好看的图文卡片", "按内容决定配色、版式与配图 · 网页与微信小程序"],
                             "CONTENT-AWARE LAYOUT  /  IMAGE SEARCH  /  MINI PROGRAM", f)
    still = m.frame("inkmuse-card")
    cw, ch = still["size"]
    k = 228 / ch
    cw, ch = cw * k, ch * k
    css = """
.type { animation: type 8s steps(40) infinite; transform-origin: 30px 0; }
@keyframes type { 0% { transform: scaleX(0); } 40%,90% { transform: scaleX(1); } 100% { transform: scaleX(1); opacity: 0; } }
.fan1 { animation: fan1 8s cubic-bezier(.6,0,.2,1) infinite; }
.fan2 { animation: fan2 8s cubic-bezier(.6,0,.2,1) infinite; }
.top { animation: drop 8s cubic-bezier(.6,0,.2,1) infinite; }
@keyframes fan1 { 0%,35% { transform: rotate(0); } 55%,92% { transform: rotate(-9deg) translateX(-18px); } 100% { transform: rotate(0); } }
@keyframes fan2 { 0%,35% { transform: rotate(0); } 55%,92% { transform: rotate(7deg) translateX(16px); } 100% { transform: rotate(0); } }
@keyframes drop { 0%,35%,100% { transform: translateY(0); } 55%,90% { transform: translateY(-6px); } }
.arrow { animation: nudge 1.6s ease-in-out infinite alternate; }
@keyframes nudge { to { transform: translateX(6px); } }
"""
    body = back
    para = ["把周末，还给自己", "我们总想把休息日过得很充实：", "约朋友、赶展览、补上工作日", "没做完的事。可有时候，真正", "需要的不是更多安排，", "而是一点空白。"]
    body += f'<rect x="30" y="56" width="236" height="208" rx="8" fill="#f6f2ea" opacity=".06"/>'
    lines = ""
    for i, ln in enumerate(para):
        lines += text(f.kai, ln, 17 if i == 0 else 13.5, 46, 92 + i * 28 + (6 if i else 0), INK if i == 0 else "#b8b1a6")
    body += (f'<clipPath id="tp"><rect x="30" y="56" width="236" height="208"/></clipPath>'
             f'<g clip-path="url(#tp)">{lines}<rect class="type" x="30" y="56" width="236" height="208" fill="{PANEL}" '
             f'style="transform-origin:266px 0"/></g>')
    body += f'<g class="arrow">{text(f.mono, "->", 18, 288, 166, AMBER)}</g>'
    px, py = 400, 46
    cx_, cy_ = px + cw / 2, py + ch
    for cls, fill in (("fan1", "#cfc8b8"), ("fan2", "#a9b59a")):
        body += (f'<rect class="{cls}" x="{px}" y="{py}" width="{cw:.0f}" height="{ch:.0f}" rx="3" fill="{fill}" '
                 f'style="transform-origin:{cx_:.0f}px {cy_:.0f}px"/>')
    body += (f'<image class="top" x="{px}" y="{py}" width="{cw:.0f}" height="{ch:.0f}" xlink:href="{m.uri("inkmuse-card")}"/>')
    body += front
    return doc(W, H, "InkMuse visual story studio", css, body)


def card_aiworks(m: Media, f: Fonts) -> str:
    W, H = 600, 440
    back, front = card_frame(W, H, AMBER, "UNDERSTAND / 04  AI VIDEO", "AI 视听作品",
                             ["3D 盲盒动画、秋日穿搭短片、赛博朋克一镜到底", "即梦 / ChatGPT 生图 · 从分镜、提示词到成片全程记录"],
                             "STORYBOARD  /  PROMPT  /  AI VIDEO", f)
    css = """
.kb { animation: kb 12s ease-in-out infinite alternate; }
@keyframes kb { from { transform: scale(1); } to { transform: scale(1.12); } }
.cap { animation: cap 12s infinite; }
"""
    body = back
    names = [("ai-dog", "晒被子吃西瓜"), ("ai-ootd", "秋日穿搭"), ("ai-cyber", "高空馄饨摊")]
    for i, (key, name) in enumerate(names):
        x, y, w, h = 30 + i * 184, 46, 172, 222
        body += (f'<clipPath id="c{i}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/></clipPath>'
                 f'<g clip-path="url(#c{i})"><image class="kb" x="{x}" y="{y}" width="{w}" height="{h}" '
                 f'preserveAspectRatio="xMidYMid slice" xlink:href="{m.uri(key)}" '
                 f'style="transform-origin:{x + w / 2}px {y + h / 2}px;animation-delay:-{i * 4}s"/>'
                 f'<rect x="{x}" y="{y + h - 34}" width="{w}" height="34" fill="#000" opacity=".45"/></g>')
        body += text(f.sans_cjk, name, 12, x + 10, y + h - 12, INK)
    body += front
    return doc(W, H, "AI video works", css, body)


def card_jimo(m: Media, f: Fonts) -> str:
    W, H = 1200, 330
    still = m.frame("jimo-scroll")
    sw, sh = still["size"]
    view_w = 1140
    bar = m.data["barcodes"]["jimo"]
    css = f"""
.pan {{ animation: pan 70s ease-in-out infinite alternate; }}
@keyframes pan {{ to {{ transform: translateX(-{sw - view_w}px); }} }}
.head {{ animation: head 70s ease-in-out infinite alternate; }}
@keyframes head {{ to {{ transform: translateX({view_w}px); }} }}
"""
    body = (f'<rect width="{W}" height="{H}" rx="16" fill="{PANEL}"/>'
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="none" stroke="{LINE}"/>')
    body += text(f.mono, "UNDERSTAND / 05  CODE-PAINTED FILM", 11, 30, 30, AMBER, tracking=1.5)
    body += (f'<clipPath id="win"><rect x="30" y="46" width="{view_w}" height="{sh}" rx="6"/></clipPath>'
             f'<g clip-path="url(#win)"><image class="pan" x="30" y="46" width="{sw}" height="{sh}" '
             f'xlink:href="{m.uri("jimo-scroll")}"/></g>')
    by = 46 + sh + 14
    unit = view_w / len(bar)
    body += "".join(f'<rect x="{30 + i * unit:.2f}" y="{by}" width="{unit + 0.3:.2f}" height="26" fill="{c}"/>'
                    for i, c in enumerate(bar))
    body += f'<g class="head"><rect x="29" y="{by - 4}" width="2" height="34" fill="#fff"/></g>'
    body += text(f.mono, f"FULL-FILM BARCODE  /  {len(bar)} SLICES  /  3:42", 9.5, 30 + view_w, by + 44, DIM, "end", 1.5)
    ty = by + 84
    body += text(f.kai, "寂寞花芳", 34, 30, ty, INK, tracking=6)
    tx = 30 + f.kai.width("寂寞花芳", 34, 6) + 24
    body += text(f.sans_cjk, "改编自《周原纪》中班婕妤的故事。画面里每一座山、每一件衣裳都由代码绘制，配音与配乐合成为 3 分 42 秒短片。",
                 14.5, tx, ty - 6, "#c9c3ba")
    body += text(f.mono, "PROCEDURAL ART  /  NARRATION  /  FFMPEG", 10.5, tx, ty + 18, DIM, tracking=1.2)
    return doc(W, H, "Lonely Flower Fragrance, a code-painted short film", css, body)


def footer(m: Media, f: Fonts) -> str:
    W, H = 1200, 120
    pals = [m.frame(k)["palette"] for k in m.data["frames"]]
    css = """
.sh { animation: sh 5s ease-in-out infinite; }
@keyframes sh { 0% { transform: translateX(-200px); } 100% { transform: translateX(1300px); } }
"""
    body = f'<rect width="{W}" height="{H}" rx="16" fill="{BG}"/>'
    unit = 1140 / len(pals)
    x0 = 30
    for i, pal in enumerate(pals):
        y = 30.0
        for c in sorted(pal, key=lambda c: luminance(c["hex"])):
            h = c["share"] * 44
            body += f'<rect x="{x0 + i * unit:.1f}" y="{y:.1f}" width="{unit + 0.3:.1f}" height="{h + 0.3:.1f}" fill="{c["hex"]}"/>'
            y += h
    body += (f'<clipPath id="ft"><rect x="30" y="30" width="1140" height="44"/></clipPath>'
             '<linearGradient id="sg" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
             f'<g clip-path="url(#ft)"><rect class="sh" x="0" y="30" width="160" height="44" fill="url(#sg)"/></g>')
    body += text(f.mono, f"THIS PAGE, MEASURED  /  {len(pals)} FRAMES FROM HER WORK  /  K = 5", 10, 600, 100, DIM, "middle", 2)
    return doc(W, H, "Colour palettes of every frame on this page", css, body)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--media", type=Path, default=Path("media"), help="folder with media.json (default: media)")
    ap.add_argument("--fonts", type=Path, default=Path("fonts"), help="font folder (default: fonts)")
    ap.add_argument("--out", type=Path, default=Path("assets"), help="output folder (default: assets)")
    ap.add_argument("--land", type=Path, required=True, help="land GeoJSON for the CineAtlas map")
    ap.add_argument("--destinations", type=Path, required=True, help="CineAtlas destinations.json")
    args = ap.parse_args()

    m, f = Media(args.media), Fonts(args.fonts)
    args.out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "hero.svg": hero(m, f),
        "measure.svg": section("01", "测量内容", "MEASURE CONTENT  /  WITH ALGORITHMS & DATA", CYAN, "barcode", m, f),
        "understand.svg": section("02", "理解用户", "UNDERSTAND PEOPLE  /  THROUGH SOUND, IMAGE & TASTE", AMBER, "wave", m, f),
        "color.svg": card_color(m, f),
        "boxoffice.svg": card_boxoffice(m, f),
        "jia.svg": card_jia(m, f),
        "nexthook.svg": card_nexthook(m, f),
        "mococo.svg": card_mococo(m, f),
        "cineatlas.svg": card_cineatlas(m, f, args.land, args.destinations),
        "inkmuse.svg": card_inkmuse(m, f),
        "aiworks.svg": card_aiworks(m, f),
        "jimo.svg": card_jimo(m, f),
        "footer.svg": footer(m, f),
    }
    for name, svg in outputs.items():
        (args.out / name).write_text(svg)
        print(f"{name:16s} {len(svg) / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
