# Baixue-Wu profile

The GitHub profile README of Baixue Wu (the special `Baixue-Wu/Baixue-Wu` repo). The page targets recruiters for AI product / AI content operations roles. Positioning: 以算法与数据测量内容，以视听与审美理解用户. Data and film carry equal weight; film is her background and taste, not the job she is applying for.

## Structure

- `README.md`: the page. Text that is not yet confirmed is marked 【待补】 or 【待确认】.
- `assets/`: generated animated SVGs. Do not edit by hand; rebuild them.
- `media/sources.json`: which frames and stills come from which of her works. `media/frames/` and `media/media.json` are extracted from it and committed, so rebuilding assets does not need the source videos.
- `tools/profile_assets/`: `extract` (videos to frames, k-means palettes, film barcodes) and `render` (media + fonts to SVGs). Both take `--help`.
- `fonts/`: not committed; download list in `fonts/README.md`.

## Commands

    uv sync
    uv run profile-extract media/sources.json --root ..      # needs her source videos next to this repo
    uv run profile-render --land ../CineAtlas/public/land.geojson --destinations ../CineAtlas/src/data/destinations.json

## Rules

- GitHub shows SVGs through <img>: no scripts, no web fonts, no links inside. Text is drawn as outlines, motion is CSS keyframes, and `prefers-reduced-motion` stops it. Each SVG paints its own dark background so it reads on both GitHub themes.
- Visuals show real data from her works (palettes, barcodes, hue histograms). Where a card illustrates a method without her data (box office scatter, sentiment curve, NextHook bars), it stays free of numbers that could read as results.
- Author and commit as Baixue Wu <baixuewu0@gmail.com> through the `github-baixue` SSH alias. No assistant attribution.
- Comments and docstrings do not use em dashes.

Design decisions: `design-decisions.md`.
