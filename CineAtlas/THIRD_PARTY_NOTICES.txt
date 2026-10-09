# Third-party materials

## Adapted application code

CineAtlas adapts the React Leaflet map/marker components and hash routing pattern of [The Chronicle of Light](https://github.com/rafsunsheikh/The-Chronicle-of-Light), by MD Rafsun Sheikh, under MIT. The full upstream notice is preserved in [docs/LICENSE-upstream](docs/LICENSE-upstream); the exact snapshot and adapted file paths are in [docs/upstream.json](docs/upstream.json).

The application shell, cultural film catalog, guide text, filtering, chronological view, interface styling and tests were developed for CineAtlas. The original Islamic history dataset, media, accounts, contributions and 3D relationship graph are not copied. The upstream dataset's CC BY-SA license does not grant rights to arbitrary movie images, and it is not the license of CineAtlas's independently written catalog.

## Destination photography

The images are contemporary destination photographs, not movie stills. They are downloaded locally and displayed using CSS crops. Source records are maintained in [src/data/image-credits.json](src/data/image-credits.json).

| Place | Photographer | Source |
| --- | --- | --- |
| Tokyo | Derch | [Shinjuku at night](https://unsplash.com/photos/vehicles-on-roadway-between-lighted-buildings-at-night-4CMq1GxDSPA) |
| Paris | Léonard Cotte | [Pont Alexandre III](https://unsplash.com/photos/pont-alexandre-iii-bridge-in-paris-R5scocnOOdM) |
| Hong Kong | Airam Dato-on | [Yau Ma Tei street](https://unsplash.com/photos/vehicle-in-road-during-nighttime-OnAB7tWXxpA) |

All three source pages identify the free [Unsplash License](https://unsplash.com/license). Credits are also available inside the application.

## Map geometry

`public/land.geojson` is Natural Earth's 1:110m land geometry, downloaded from the [Natural Earth vector repository](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson). [Natural Earth data are public domain](https://www.naturalearthdata.com/about/terms-of-use/). The app uses coastline geometry, not political boundaries, and does not provide navigation or historical boundary reconstruction.

## Fonts and film sources

Optional DM Sans and Noto Sans SC fonts are requested from Google Fonts; system fonts are used if unavailable. No font files are redistributed in this repository. Each film links to the film institution, distributor or archive used to check its background. Guide text is an original editorial interpretation; linking a source does not imply affiliation or endorsement. Film posters, trailers and streaming services are not embedded.
