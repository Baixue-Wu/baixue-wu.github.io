"""Subset the site's fonts to the characters its pages actually use.

The site must load fast in mainland China, where Google Fonts is blocked, so
every face is self-hosted as a small WOFF2 file. Rerun after editing page text.
"""

import argparse
import re
from html import unescape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

# output name, source file, weight for variable fonts, character set
FACES = [
    ("serif-sc.woff2", "NotoSerifCJKsc-Bold.otf", None, "page"),
    ("kai.woff2", "LXGWWenKaiLite-Regular.ttf", None, "page"),
    ("display.woff2", "InstrumentSerif-Italic.ttf", None, "latin"),
    ("mono.woff2", "JetBrainsMono.ttf", 400, "latin"),
]
LATIN = "".join(chr(c) for c in range(0x20, 0x7F)) + "·–—“”‘’…•→←↗"


def page_text(pages: list[Path]) -> str:
    chars = set(LATIN)
    for p in pages:
        raw = p.read_text()
        raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S)
        chars |= set(unescape(re.sub(r"<[^>]+>", " ", raw)))
    return "".join(sorted(chars))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", type=Path, nargs="+", help="HTML pages whose text the fonts must cover")
    ap.add_argument("--fonts", type=Path, default=Path("fonts"), help="source font folder (default: fonts)")
    ap.add_argument("--out", type=Path, default=Path("assets/fonts"), help="output folder (default: assets/fonts)")
    ap.add_argument("--extra", default="", help="extra characters to keep, e.g. text drawn by scripts")
    args = ap.parse_args()

    text = page_text(args.pages) + args.extra + LATIN
    args.out.mkdir(parents=True, exist_ok=True)
    for name, source, weight, charset in FACES:
        path = args.fonts / source
        if not path.exists():
            raise FileNotFoundError(f"font not found: {path} (see fonts/README.md for downloads)")
        font = TTFont(path)
        if weight and "fvar" in font:
            font = instancer.instantiateVariableFont(font, {"wght": weight})
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "palt", "vpal"]
        sub = subset.Subsetter(opts)
        sub.populate(text=text if charset == "page" else LATIN)
        sub.subset(font)
        font.flavor = "woff2"
        font.save(args.out / name)
        print(f"{name:16s} {(args.out / name).stat().st_size / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
