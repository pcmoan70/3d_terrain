# Changes

## 2026-10-17 — Save as one file or as a folder

Owner: "user should be given option to save full, standalone html file (like now), or a folder containing dtm tiles and point-lists etc that should annotate the 3d view." "Save as" chooses: one offline file (as before) or a folder `<name>/` with the DTM tiles, habitat.geojson, points.geojson, scene.json and index.json — written into a folder the user picks (File System Access in Chrome / Edge), elsewhere downloaded as a stored zip (a tiny zip writer in the page). Load with an empty path opens the folder again; more .geojson / .kml / .kmz files dropped into it annotate the view.

## 2026-10-17 — the map opens from the coordinates in the title

Owner: "The pick place on map, should be removed and be executed when user clicks on coordinates in title on top of pane." The 🗺 button is gone; the panel's title reads "Terrain 3D — <scene title ·> 58.98634, 6.19051" and tapping the coordinates opens the map picker (before any view: "pick a place on the map").

## 2026-10-17 — the picker by touch

Owner: "Make sure mobile phone touch makes for good natural navigation too". The centre is a draggable red dot; the view's square has an orange handle on its south-east corner and the 1 m detail square a white one on its north-east corner — drag them (finger or mouse) to set the radii, which snap to 100 m (50 m under 1 km); one-finger drag pans, pinch zooms, a tap places the centre (a tap that ends a drag does not). On touch screens the bar's controls are finger-sized (38 px) and the number fields open the decimal keypad.

## 2026-10-17 — the picker: the wheel sets the radius, the square is drawn; radii as text in the Data section

Owner: "In the map picture user gives center and radius. Radius in km, in settings pane the given radius and dtm resolution is show as text. When user selects in map he rolling mouse wheel changes radius. Also a indicative square is shown." On the map, once a point is tapped, the mouse wheel changes the view radius (100 m to 1 km steps by size; + / − and pinch still zoom the map) and the view's square — the block exactly, in the UTM grid — is drawn in yellow, the 1 m detail square dashed white in the nested model, instead of the circle. The Data section shows "Terrain model: … · view radius … · 1 m detail within …" as text; the inputs behind it feed Render.

## 2026-10-17 — the picker's radii in km

Owner: "In map selection, write radius in km not m". The map picker's "View radius" and "1 m detail within" are typed in km (0.1 km steps; 5 / 15 and 1.5 km limits); the Data section still shows metres.

## 2026-10-17 — the nesting-habitat rules run in the browser on map-built views

`viewer/habitat.js` (a JavaScript copy of `lib/habitat.py`, both reading `rules.json`; `tests/parity.py` holds them together: 99.8 % area overlap, identical names and texts on the Preikestolen demo) is inlined into the viewer like the libraries. After a map-built 1 m view renders, the rules run on its fine grid (1–2 m cells); OpenStreetMap buildings, roads (a point every 25 m) and quarries from Overpass (three mirrors, 20 s each) stand in for N250; the areas, the steepest point and the layer's legend are added to the view and its files, so Save keeps them. The Birds group starts switched off as before.

## 2026-10-17 — one path box: Load and Save

Owner: "the opening of premade files and saving of built files should be simplified. Make the functionality dependent on path user writes into a single textbox and single buttons save/load." The Data section's Open folder / Open files / Folder on this site / URL / Google Drive rows are one **Path** box with **Load** and **Save**. Load reads a web folder, the URL of a built `…_3dterrain.html` (new: its embedded folder is read), a Drive link, a scene name on this site (suggested as you type), or with an empty box a folder from the device (a built `.html` among the files is read too). Save writes the current view — also one built from the map — as one offline `<name>_3dterrain.html`: the page keeps its own source as served and swaps the embed slot; the name comes from the box, else the title; Chrome / Edge ask where (File System Access), others download. The picker's and the Data section's radius fields now say what they are: "View radius … m from the point" and "1 m detail within … m" (owner: "The 1000 is unclear in the map functionality, spell out what it is").

## 2026-10-17 — 10 m model, and a 1 m centre inside a 10 m surround, shaded as one terrain

Owner (plan of 2026-10-16): "support both 1m and 10m dtm as well as 1m dtm in a smaller central area and 10m dtm around in a larger area … The 1m in middle + 10m surrounding should affect the shading algo." The viewer renders two grids when fine and coarse tiles are opened together (or the picker's "1 m centre + 10 m around"): a fine grid over ±R1 (≤ 1.5 km, ≤ 3000² cells) and a coarse grid over ±R (≤ 15 km, ≤ 1500² cells). The surround's mesh has the centre cut out, its vertices there snapped to the fine surface and its material pushed back in depth; the centre carries a skirt. Two render passes on three.js layers (the surround, its walls and its light; then the centre, its light and every marker, sharing the depth buffer; the colour background is dropped for the second pass, which three.js would otherwise clear). Two shadow maps: 2048² over the block, 4096² over the centre, each fed by an uncut shadow-only copy of the surround so the far ridges shade the centre. The sun-average horizons of the centre's cells are marched through the fine grid and on through the coarse grid to the block's edge; every march (and the popup's "Sun now") takes the Earth's curvature less refraction off distant heights; both grids share one colour range. `sample()` prefers the fine grid everywhere. `viz3d.py --res 10` packages `dtm_10m.tif` (the WCS's 10 km tiles, cached in `tiles10/`, or a local DTM10 via `config.toml` `dtm10`); `--radius-1m R1` adds the 1 m model and habitat over ±R1 and `scene.json` `radius_1m`. Checked in Chrome at Preikestolen (1 km centre in 6 km): no crack or light step at the seam, the surround's shadow falls across the centre, the sun layer is continuous across the seam.

## 2026-10-17 — pick a place on a flat map, the terrain fetched from Kartverket

Owner: "Add the dtm builder to the web app, user is given a flat map and selects a point where upon to build and view the 3d view." The viewer opens on a flat map (Leaflet 1.9.4 from cdnjs, loaded on demand; Kartverket topo); a tap sets the centre, the circle shows the radius, the bar gives the download size; **Build 3-D view** fetches the tiles from the Geonorge WCS (1 km at 1 m or 10 km at 10 m; coarser cells for a wide 1 m view) with exponential backoff, keeps them in the Cache API (120 tiles), and renders. `?lat=&lon=&r=&res=` opens a view by link; Share… makes that link; 🗺 in the Data section reopens the map. WCS tiles are sparse GeoTIFFs (sea blocks left out), which geotiff.js cannot read — the missing blocks are pointed at one zero block (the model's sea is 0 m). The 10 m model allows a 15 km radius (3000² grid); its contours are 20 m / 100 m. Checked in Chrome: Preikestolen at 1 m (9 tiles, 36 MB, ~8 s) and Jotunheimen at 10 m, 8 km.

## 2026-10-17 — own repository

The 3-D terrain viewer, its two scripts and the demo site moved here from the BirdsWhere workspace (where the viewer was served as `thebirding.site/terrain3d/`, versions v2081–v2119 of its CHANGES) and from a private owl-project folder. No change in what they do:

- `viewer/viewer3d_template.html` — the viewer as deployed on 2026-10-16; `vendor/` holds the three libraries it inlines (three.js r128, OrbitControls r128, geotiff.js 2.1.3), recovered byte-for-byte from the deployed page.
- `viz3d.py`, `rewrap.py` — the hard-coded paths (tile stores, N250, a scratch directory for the libraries) are read from `config.toml` (`lib/config.py`); the private point source became `--points FILE.geojson` (with the layer's title and legend inside the file); the standalone file goes to `--out` (default the current directory); `--public` is gone (there is no private data without `--points`).
- `lib/dtm.py` (WCS tiles with backoff), `lib/habitat.py` (the nesting-habitat rules) — the modules the scripts used from two other places. N250 is optional now: without it, distances to buildings and roads are "unknown", no quarries are told apart, every small island counts.
- `site/` — the viewer and the Preikestolen demo, published by GitHub Actions to https://pcmoan70.github.io/3d_terrain/.

Checked: Vinstradalen (3 km) and Preikestolen rebuilt by the new scripts give the same `dtm_1m.tif`, base map, `habitat.geojson` and `points.geojson` as the old ones; the regenerated empty viewer is identical to the page deployed at thebirding.site/terrain3d/; a build from an empty cache without N250 works.
