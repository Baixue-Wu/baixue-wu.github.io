# baixue-wu.github.io

Personal website of Baixue Wu, served by GitHub Pages at https://baixue-wu.github.io.

Plain static files: `index.html`, `css/`, `js/`, `assets/` and `media/`. No build step is needed to serve it.

Rebuilding the generated parts (needs Python with uv, her source videos next to this repo, and the fonts in `fonts/README.md`):

    uv sync
    uv run site-extract media/sources.json --root ..        # frames, palettes, barcodes, web videos -> media/
    uv run site-render --land ../CineAtlas/public/land.geojson --destinations ../CineAtlas/src/data/destinations.json
    uv run site-fonts index.html                             # rerun after editing page text

Preview locally: `python3 -m http.server 8000`, then open http://127.0.0.1:8000.

## Project demos

`InkMuse/`, `CineAtlas/` and `NextHook/` hold static project builds. Rebuild in the source repositories, then copy each with `python3 tools/site-demos.py --name NAME --source BUILD_DIR --repository GITHUB_URL --revision SOURCE_COMMIT`. Each directory includes `demo-manifest.json` with its source revision and file hashes. Only static assets belong here.

Verification: all three builds passed desktop sample flows and mobile overflow checks in Chromium. InkMuse editing/drafts/ZIP export and NextHook metric selection/chart exploration/plan export/refresh/back navigation passed. No backend API requests, missing assets or browser exceptions were observed. NextHook creator tests (18), type checking, and InkMuse core/HTTP tests also passed.
