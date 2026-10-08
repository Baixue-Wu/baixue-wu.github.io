# baixue-wu.github.io

Personal website of Baixue Wu, served by GitHub Pages at https://baixue-wu.github.io.

Plain static files: `index.html`, `css/`, `js/`, `assets/` and `media/`. No build step is needed to serve it.

Rebuilding the generated parts (needs Python with uv, her source videos next to this repo, and the fonts in `fonts/README.md`):

    uv sync
    uv run site-extract media/sources.json --root ..        # frames, palettes, barcodes, web videos -> media/
    uv run site-render --land ../CineAtlas/public/land.geojson --destinations ../CineAtlas/src/data/destinations.json
    uv run site-fonts index.html                             # rerun after editing page text

Preview locally: `python3 -m http.server 8000`, then open http://127.0.0.1:8000.
