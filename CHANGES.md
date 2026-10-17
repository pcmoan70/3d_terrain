# Changes

## 2026-10-17 — pick a place on a flat map, the terrain fetched from Kartverket

Owner: "Add the dtm builder to the web app, user is given a flat map and selects a point where upon to build and view the 3d view." The viewer opens on a flat map (Leaflet 1.9.4 from cdnjs, loaded on demand; Kartverket topo); a tap sets the centre, the circle shows the radius, the bar gives the download size; **Build 3-D view** fetches the tiles from the Geonorge WCS (1 km at 1 m or 10 km at 10 m; coarser cells for a wide 1 m view) with exponential backoff, keeps them in the Cache API (120 tiles), and renders. `?lat=&lon=&r=&res=` opens a view by link; Share… makes that link; 🗺 in the Data section reopens the map. WCS tiles are sparse GeoTIFFs (sea blocks left out), which geotiff.js cannot read — the missing blocks are pointed at one zero block (the model's sea is 0 m). The 10 m model allows a 15 km radius (3000² grid); its contours are 20 m / 100 m. Checked in Chrome: Preikestolen at 1 m (9 tiles, 36 MB, ~8 s) and Jotunheimen at 10 m, 8 km.

## 2026-10-17 — own repository

The 3-D terrain viewer, its two scripts and the demo site moved here from the BirdsWhere workspace (where the viewer was served as `thebirding.site/terrain3d/`, versions v2081–v2119 of its CHANGES) and from a private owl-project folder. No change in what they do:

- `viewer/viewer3d_template.html` — the viewer as deployed on 2026-10-16; `vendor/` holds the three libraries it inlines (three.js r128, OrbitControls r128, geotiff.js 2.1.3), recovered byte-for-byte from the deployed page.
- `viz3d.py`, `rewrap.py` — the hard-coded paths (tile stores, N250, a scratch directory for the libraries) are read from `config.toml` (`lib/config.py`); the private point source became `--points FILE.geojson` (with the layer's title and legend inside the file); the standalone file goes to `--out` (default the current directory); `--public` is gone (there is no private data without `--points`).
- `lib/dtm.py` (WCS tiles with backoff), `lib/habitat.py` (the nesting-habitat rules) — the modules the scripts used from two other places. N250 is optional now: without it, distances to buildings and roads are "unknown", no quarries are told apart, every small island counts.
- `site/` — the viewer and the Preikestolen demo, published by GitHub Actions to https://pcmoan70.github.io/3d_terrain/.

Checked: Vinstradalen (3 km) and Preikestolen rebuilt by the new scripts give the same `dtm_1m.tif`, base map, `habitat.geojson` and `points.geojson` as the old ones; the regenerated empty viewer is identical to the page deployed at thebirding.site/terrain3d/; a build from an empty cache without N250 works.
