"""Turn text into SVG path data, so the SVGs look the same on every machine.

GitHub shows README images through <img>, where web fonts never load. Every
visible string is therefore drawn from a font file into outlines.
"""

from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer


@lru_cache(maxsize=None)
def load(path: str, weight: int | None = None) -> TTFont:
    font = TTFont(path)
    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": weight or 400})
    return font


class Face:
    """One font file at one weight."""

    def __init__(self, path: Path, weight: int | None = None):
        if not path.exists():
            raise FileNotFoundError(f"font not found: {path} (see fonts/README.md for downloads)")
        self.font = load(str(path), weight)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        total = 0.0
        for ch in text:
            name = self.cmap.get(ord(ch))
            if name is None:
                raise KeyError(f"glyph {ch!r} missing from {self.font.reader.file.name}")
            total += self.glyphs[name].width * size / self.upm + tracking
        return total - tracking if text else 0.0

    def path(self, text: str, size: float, x: float, y: float,
             anchor: str = "start", tracking: float = 0) -> str:
        """Path data for text whose baseline starts at (x, y)."""
        w = self.width(text, size, tracking)
        x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
        scale = size / self.upm
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        for ch in text:
            name = self.cmap[ord(ch)]
            self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
            x += self.glyphs[name].width * scale + tracking
        return pen.getCommands()


class Fonts:
    """The faces the profile uses, loaded from one folder."""

    def __init__(self, folder: Path):
        self.serif_cjk = Face(folder / "NotoSerifCJKsc-Bold.otf")
        self.sans_cjk = Face(folder / "NotoSansSC-Regular.otf")
        self.kai = Face(folder / "LXGWWenKaiLite-Regular.ttf")
        self.serif = Face(folder / "InstrumentSerif-Regular.ttf")
        self.italic = Face(folder / "InstrumentSerif-Italic.ttf")
        self.mono = Face(folder / "JetBrainsMono.ttf", 400)
        self.mono_bold = Face(folder / "JetBrainsMono.ttf", 700)
