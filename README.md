# 3d_terrain — a 3-D terrain viewer for Kartverket's 1 m model

Updated 2026-10-17 (evening).

A web page that draws a 1 m terrain model (DTM) of any place in Norway in 3-D, with the sun and its shadows for any date and time, and two Python scripts that package a place — its terrain, a draped map, nesting-habitat areas and your own points — as a folder the page reads or as one self-contained HTML file that opens offline.

**Live viewer:** https://pcmoan70.github.io/3d_terrain/ — it opens on a flat map of Norway: **tap a place, choose the model (1 m, radius ≤ 5 km, or 10 m, radius ≤ 15 km) and the radius, Build 3-D view**. The terrain is fetched straight from Kartverket's model (the Geonorge WCS) and shown; `?lat=&lon=&r=&res=` opens the same view by link, and **Share…** makes that link. The demo folder is Preikestolen.

Everything happens in the browser: the page reads GeoTIFF tiles, mosaics and smooths them, builds the mesh, drapes the map, marches the sun. There is no server and no build step.

## The viewer (`viewer/viewer3d_template.html` → `site/index.html`)

Draws a terrain model from a **folder** (radius up to 5 km: beyond 1.5 km the grid coarsens to ⌈2R / 3000⌉ m so it stays ≤ 3000 × 3000 — a 3 km view is a 2 m grid): 1 m DTM GeoTIFF tiles (one UTM zone, EPSG 258xx / 326xx, Float32 or integer) plus any `.geojson` / `.kml` / `.kmz` overlays (polygons draped on the terrain, points as needles; a point with `role` = `steepest` is the red ring; without one the viewer takes the steepest cell within 500 m, never within 25 m of the data's edge) and an optional `scene.json` (`title`, `lat`, `lon`, `radius`, `sigma` — the suggested smoothing in m, 0 = off).

- **Pick a place on the map** (the start screen, and 🗺 in the Data section): a Leaflet map with Kartverket's topo (loaded on demand); a tap sets the centre, the circle shows the radius, the bar says how many tiles and MB the build fetches. The tiles come from the Geonorge WCS — 1 km tiles at 1 m, or 10 km tiles at 10 m, and coarser cells for a wide 1 m view (a 3 km view asks 2 m tiles, a quarter of the bytes) — one after another with exponential backoff (1 … 60 s), kept in the browser's Cache API (the last 120 tiles) so the next build of the same place is instant. Norway only. A position-loaded view has terrain, contours, slope, facing and the sun, but no habitat areas (those come with packaged folders). On a 10 m grid the contours are 20 m (bold every 100 m) instead of 5 / 25 m.
- **Open** a folder or files from the device, a folder on the same site from the picker (`scenes/index.json` = `[{name, title, path}]`), or any folder URL (`?folder=<url>` too). A web server cannot list a directory, so a folder served over HTTP needs an `index.json` = `{"files": ["dtm.tif", "habitat.geojson", …]}` (or a plain array).
- **Google Drive:** paste a shared Drive folder (or file) link → **Sign in & open** (or open the viewer with `?drive=<link>`). Signs in with Google (read-only Drive access; token in memory only), lists the folder through the Drive API (sub-folders two levels down; no `index.json` needed) and reads the files with the token — so the data stays private to the accounts it is shared with. Needs the page opened from its web address (not a downloaded copy).
- **Sharing a terrain between two users:** **Share…** makes a link (`?drive=<folder link>` or `?folder=<url>`, plus the date and time). For a Drive folder, share the folder in Drive with the other person's Google account (Viewer); they open the link and sign in with their own account.
- **Base map** (selector): *Slope tint*, *Kartverket topo*, *Kartverket greyscale*, *OpenStreetMap* (drawn by OpenTopoMap), *Paths & cycling* (CyclOSM), *Streets (Esri)*, *Aerial (Esri)* or *Aerial, earlier photos (Esri Wayback)* — the newest photo at once, then a *Photo* choice of every distinct earlier photo of the spot — XYZ tiles for the view's box at the zoom whose pixel is about one grid cell, resampled onto the UTM grid so roads, streams and the map's own contours sit on the terrain; attribution along the bottom. A packaged folder can carry a map already draped for its view (`basemap_<id>.jpg`, `scene.json` `basemap`: {id, file}) — the standalone files carry Kartverket topo, so they work offline; the others need the network.
- **Shape:** a block with side walls (the whole square, four walls down to a base below the lowest point, closed underneath), lit by the sun.
- **Map** section: *Contours* (5 m, labelled every 25 m), the overlay files outside the Birds group, *Centre, circles & steepest point*, *Bold markers*. **Birds** section (everything in it starts switched off): *Slope* in NVE's steepness classes (27–30 · 30–35 · 35–40 · 40–45 · ≥ 45°); *Facing* — the way slopes ≥ 15° face, eight directions, one colour each; *Sun: average direct radiation* — clear-sky direct sun on the ground in kWh/m² per day, averaged hourly over two days of each month (NOAA sun position, beam × cos incidence on the slope, 0 below the cell's own horizon — 32 directions marched over the terrain in view), for a **month range** set with a two-handle slider; one layer **per loaded overlay file** (`scene.json` `layers`: {file: {title, legend: [[colour, label] …], group: "birds"}} names and explains it — `group: "birds"` puts it in the Birds group). The compass (true north) is always shown. Hovering shows the height, slope, facing and — with the sun layer — that point's average. **Tapping the terrain** opens a popup with the point's coordinates and height. The **🐦** control opens BirdsWhere (thebirding.site) centred on the view; the **🛰** control opens norgeskart.no there with Kartverket's orthophoto.
- **Missing DTM** (tiles that do not exist): filled with the smoothest surface that meets the known ground (least squares, solved coarse to fine), **greyed and hatched**; the panel gives its share and hovering says "No DTM data here".
- **Shown:** contours, slope tint, the overlays, a centre pin with 500 m / radius circles, the steepest point, a compass, a height slider (×1–3), map-style controls (drag moves the map; rotate by twisting two fingers, right-drag / Shift+drag, the ✋ → ⟳ drag-mode button, or the ⟲ ⟳ ▲ ▼ buttons, N = north up; wheel / pinch / +− zoom, arrow keys pan), top view; a **📏 measuring tool** (tap two points: horizontal distance, height difference, distance along the line, slope in ° and %, true bearing); **optional smoothing** (☑ Smooth terrain, σ m — on at 1.5 m by default; off shows the raw 1 m model). It opens looking down at the area, in daylight (at night: today's solar noon).
- **Sun:** date and time sliders (Norway time CET/CEST or UTC), the NOAA solar-position equations → directional light with cast terrain shadows; sun elevation / azimuth, sunrise / solar noon / sunset; hovering shows the clear-sky direct irradiance on the surface (W/m², incidence on the 1 m slope, terrain shadow) and the day's direct total (kWh/m²). "▶ Day" animates the day.
- **Panels:** one column down the left side — height, smoothing and the view buttons on top, then the collapsible sections **Map**, **Birds**, **Sun** and **Data** (open folder / files / URL / Drive, centre and radius, Render, Share); **‹** tucks the column away. The map controls on the right are one column too. The info panel minimises.
- **Pins:** hovering a point's or an area's pin shows its name and description; tapping it opens the popup with that text, the coordinates and the height. **Bold markers** makes the pins twice the size, draws them over the terrain, and outlines the areas in white.

## The scripts

```bash
pip install -r requirements.txt          # numpy scipy rasterio pyproj shapely affine Pillow (pyogrio only with N250)
cp config.example.toml config.toml       # optional: where the tile caches (and N250) live

python3 viz3d.py 58.98634 6.19051 --name preikestolen --radius 1000 --title "Preikestolen (demo)"
python3 viz3d.py LAT LON --name NAME --radius R [--points FILE.geojson] [--site DIR] [--out DIR]
python3 rewrap.py FILE_3dterrain.html … [--points FILE.geojson] [--viewer DIR]
```

**`viz3d.py LAT LON`** packages the ±R square round a point:

1. fetches the 1 km tiles of Kartverket's 1 m model it does not have yet (Geonorge WCS, one at a time, exponential backoff 1 … 60 s) into the tile cache, and mosaics them;
2. runs the habitat rules (`lib/habitat.py`): steep ground ≥ 50° on the σ 1.5 m-smoothed model, kept as a nesting **cliff** when its face is ≥ 10 m high and looks E … S … W, each with its height, facing, shape, and (with N250) distance to the nearest building and road; steep ground inside an N250 quarry as **quarry**; small islands (< 20 ha, no building) as **islet**; nothing within 25 m of the data's edge. Coloured by facing (S strongest);
3. drapes Kartverket's topo map onto the view's grid (tiles cached) so the standalone file works offline;
4. writes `site/scenes/<name>/` — `dtm_1m.tif` (the raw model, cm precision, EPSG:25833; on a ⌈2R / 3000⌉ m grid beyond 1.5 km), `basemap_kv_topo.jpg`, `habitat.geojson`, `points.geojson` (the steepest point on a nesting cliff + your `--points` within the radius), `scene.json`, `index.json` — and adds it to `site/scenes/index.json`, regenerates `site/index.html`;
5. writes `<out>/<name>_3dterrain.html`: the viewer with that folder built in (base64) — one file, opens from the disk, offline.

`--points FILE.geojson` is a FeatureCollection of points (properties `name`, `desc`, `role`, `color`); a top-level `"layer"` member `{title, legend: [[colour, label] …], group}` names its layer in the viewer. Private points stay in your own files: the repo holds none.

**`rewrap.py`** puts the current viewer round already-built standalone files, keeping each file's embedded folder (no recomputation) — after a viewer change. `--points` swaps the points in each file for those of the file within its view; `--viewer DIR` also rewrites the empty viewer `DIR/index.html`.

**`config.toml`** (`lib/config.py`; `$TERRAIN3D_CONFIG`, `./config.toml`, `~/.config/terrain3d/config.toml`): `dtm1_tiles` and `map_tiles` — the caches (default under `~/.cache/terrain3d/`); `n250` — Kartverket's N250 file geodatabase, optional.

## Layout

```
viewer/viewer3d_template.html   the viewer; /*THREE*/ /*ORBIT*/ /*GEOTIFF*/ take the libraries, /*EMBED*/ a built-in folder
vendor/                         three.min.js r128 · OrbitControls.js r128 · geotiff.js 2.1.3 (THIRD-PARTY.md)
viz3d.py · rewrap.py            the scripts
lib/config.py · dtm.py · habitat.py
site/                           what GitHub Pages serves: index.html + scenes/ (.github/workflows/pages.yml)
config.example.toml · requirements.txt · CHANGES.md · LICENSE (MIT) · THIRD-PARTY.md
```

## Data and licences

Terrain: Kartverket NHM DTM 1 m, CC BY 4.0. Maps: Kartverket (CC BY 4.0), OpenTopoMap / CyclOSM (© OpenStreetMap contributors), Esri. Code: MIT. See `THIRD-PARTY.md`.
