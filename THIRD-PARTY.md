# Third-party code and data

## Bundled libraries (`vendor/`, inlined into the viewer)

| Library | Version | Licence |
|---|---|---|
| [three.js](https://threejs.org/) `three.min.js` | r128 | MIT, © 2010-2021 Three.js Authors |
| three.js `examples/js/controls/OrbitControls.js` | r128 | MIT, © 2010-2021 Three.js Authors |
| [geotiff.js](https://github.com/geotiffjs/geotiff.js) `dist-browser/geotiff.js` | 2.1.3 | MIT, © 2015 EOX IT Services GmbH |

## Data the scripts fetch and the viewer draws

- **Kartverket NHM DTM 1 m** (the terrain, via the Geonorge WCS) — open data, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), © Kartverket.
- **Kartverket topographic map tiles** (`cache.kartverket.no`, draped base map; the one packaged into standalone files) — CC BY 4.0, © Kartverket.
- **Kartverket N250 map data** (optional, local: buildings, roads, quarries for the habitat rules) — CC BY 4.0, © Kartverket.
- **CORINE Land Cover 2018** for Norway, from NIBIO's WMS (`wms.nibio.no`; Norwegian licence for open public data, NLOD) — the European dataset is Copernicus Land Monitoring Service, © EEA, free and open. Fetched live when the layer is on; not redistributed.
- Base maps the viewer can fetch live: OpenTopoMap (CC BY-SA, data © OpenStreetMap contributors, ODbL), CyclOSM (data © OpenStreetMap contributors), Esri World Street Map / World Imagery / Wayback (© Esri and its data providers, under Esri's terms of use). Attribution is shown along the bottom of the viewer.
- The 🛰 control opens norgeskart.no (Kartverket); the 🐦 control opens thebirding.site.
