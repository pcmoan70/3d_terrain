# Changes

## 2026-10-17 — own repository

The 3-D terrain viewer, its two scripts and the demo site moved here from the BirdsWhere workspace (where the viewer was served as `thebirding.site/terrain3d/`, versions v2081–v2119 of its CHANGES) and from a private owl-project folder. No change in what they do:

- `viewer/viewer3d_template.html` — the viewer as deployed on 2026-10-16; `vendor/` holds the three libraries it inlines (three.js r128, OrbitControls r128, geotiff.js 2.1.3), recovered byte-for-byte from the deployed page.
- `viz3d.py`, `rewrap.py` — the hard-coded paths (tile stores, N250, a scratch directory for the libraries) are read from `config.toml` (`lib/config.py`); the private point source became `--points FILE.geojson` (with the layer's title and legend inside the file); the standalone file goes to `--out` (default the current directory); `--public` is gone (there is no private data without `--points`).
- `lib/dtm.py` (WCS tiles with backoff), `lib/habitat.py` (the nesting-habitat rules) — the modules the scripts used from two other places. N250 is optional now: without it, distances to buildings and roads are "unknown", no quarries are told apart, every small island counts.
- `site/` — the viewer and the Preikestolen demo, published by GitHub Actions to https://pcmoan70.github.io/3d_terrain/.

Checked: Vinstradalen (3 km) and Preikestolen rebuilt by the new scripts give the same `dtm_1m.tif`, base map, `habitat.geojson` and `points.geojson` as the old ones; the regenerated empty viewer is identical to the page deployed at thebirding.site/terrain3d/; a build from an empty cache without N250 works.
