# Changes

## 2026-10-20 · a closed section's triangle turns blue when a toggle is set inside

Owner: "the blue triangles should be implemented in the 3d viewer as well" (after BirdsWhere v2141). `markSecs()` gives a section's summary `.set` when any checkbox under it is away from its default (`defaultChecked`) — a layer switched on, contours or markers off, a NIBIO layer in a nested group — on every change in the panel and in `repaint` / `applyVis` (choices applied from a link or a file); the CSS paints the `::marker` of a closed `.set` summary blue (#64b5f6). The nested NIBIO / DTM-derived groups get it too. The scene's own smoothing (`csmooth` from the scene's sigma) sets `defaultChecked` as well, so a 10 m view does not start with a blue Map section. Help (Moving around) and README updated.
## 2026-10-20 · the title line without the "Terrain 3D — pick a place on the map" text

Owner: "Remove the text 'Terrain 3D — pick a place on the map...' from the top of the left pane". The panel's title now carries only the scene name and coordinates once a terrain is loaded, and the 📍 (which opens the map picker); before a view it is just the 📍. The page title and the share title still say Terrain 3D.

## 2026-10-20 · Height × and Smooth terrain in the Map section

Owner: "move Height x and smooth terrain into the collapsible Map sub pane". The two rows moved from the panel head to the Map section, under the base-map rows; the head keeps the view buttons. Help ("Moving around") and README name the section.

## 2026-10-20 · Sun average: a high-pass handle on the legend; the flat map carries the layers only

Owner: "for the average direct radiation give a slider (high pass) along the spectrum at the bottom, cutting away overlay values below this level (default 1kwH/m^2 per day). Also: remove text (clear sky, direct)" — the legend gradient is now the track of a slider (`#sunCut`, `sunCut` in kWh/m² per day, 1 to begin with); `paintBase` leaves cells below it unpainted, the cut part of the bar is dimmed, the text reads "lo – hi kWh/m² per day · below x hidden"; a view link carries it as `scut:`. The phrase "(clear sky, direct)" is gone from the legend and the hover text (the Help still explains the model). Owner: "when switching 3d <-> 2d only transfer the overlays, not the base-map as an overlay" and "do not transfer contours" — `paint2d` uses `overlayRGBA` on every map and `paintBase` takes a `noCont` flag: the 2-D image is the layers alone, the map supplies base and contours; *Plain* is a bare light background (`#map2d` tint); `hillshade()` and the sun-slider repaint hook are removed. Help "Sun" and "2-D map", README.

## 2026-10-20 · A 2-D map view carrying the terrain's layers

Owner: "a feature switching between 2d and 3d views. The main point being transferring the overlay computed and visualised in 3d using dtm tiles to the 2d map. Also the user should be allowed to choose between various background maps including plain (but not any requiring api keys)." A *2D* button in the control column opens a full-screen Leaflet map (the library already loaded for the picker) centred and zoomed like the 3-D view. The picture is the terrain's own `paintBase` output: `overlayRGBA()` paints a grid on a white and a black base and recovers alpha per pixel (every blend is affine in the base), `hillshade()` makes the *Plain* base from the gradients and the light in use, `warpMerc()` projects the UTM square onto Web Mercator (a lattice every 8 px through `UTM.fwd`, bilinear between, nearest cell; the fine square cut out of the surround) into a canvas-fed `L.ImageOverlay`. The *Map* dropdown serves both views — all key-free: Plain, Kartverket topo/greyscale, OpenTopoMap, CyclOSM, Esri streets/aerial, Wayback, NASA GIBS — as `L.tileLayer` under the layers. Hover (`tipXY`, split out of `hoverAt`), the pinned tap, the long press / right-click popup (`pointMenu` with x, y from `UTM.fwd`), areas and points as Leaflet vectors; *Ground view* from the map switches back first; *3D* moves the orbit centre to the map's centre. `repaint()`, `build()`, `applyVis()` and `updateSun()` (Plain, debounced) refresh the map; view links carry `v2:zoom/lat/lon`. Help section "2-D map", README.

## 2026-10-20 · Viewshed from 1 m above the ground

Owner: "The viewshed should be calculated from 1m above ground at the given point." `VS_H = 1` replaces the 1.75 m eye height in `viewshed()` (Ground view keeps its 1.75 m). The feature note, the popup button's tooltip, the help and the README say 1 m.

## 2026-10-20 · Point popup: long press or right-click; coordinates copy on a tap; Ground view beside Viewshed

Owner: "In the 3d viewer point popup let user copy lon/lat by clicking text. Move ground view on same line as viewshed." The lat, lon text is a tap target (dotted underline) that writes "lat, lon" to the clipboard and reads "copied ✓" for a second. The buttons are rearranged into two lines: the model dropdown (narrowed) with *Fetch+* and *Fetch*, then *Ground view* and *Viewshed* (the latter used to wrap alone in a narrow popup).

Owner: "The point popup menu should show when long click on touch screen or right-click on mouse." The terrain's popup now opens on a 500 ms press with one finger (cancelled by movement over 6 px or a second finger) or a right-click without a drag (`contextmenu`, which OrbitControls' right-drag pan also ends with); a plain tap closes the popup, still opens a pin's and still places measuring points. Android's own long-press `contextmenu` is ignored for a second after the press fires. Help and README updated.

Owner: "Short clicks should show point overlay values (hover), with the hover window sticky." The pointermove handler's body is `hoverAt(cx, cy)`; a short tap on the terrain calls it and pins the tip (`tipPinned`, a thin border): pointermove and pointerleave leave it alone until the next tap, long press or right-click. A tap on the sky unpins it.

Owner: "let the drop down menu for tile size be 1m, 10m, 1+10m and make dropdown more narrow, as well as the popup window." The model options read `1m`, `10m`, `1+10m` (the long form in the dropdown's tooltip); the dropdown is 70 px (was 120), the popup at most 250 px (was 320) — measured 245 px with the two button lines intact.

## 2026-10-20 · Cliff drops under one toggle

Owner: "The various cliff drop intervals should be hidden toggled with one "cliff drops" and when toggled on show each of the ranges 5-10, 10-15,15-25,25-50, 50+ toggleable individually. When "cliff drops" is toggled off the options ranges should hide." A *Cliff drops* row (`ft_cliffs`, a five-colour swatch) now stands where the five rows were; switching it on shows the five class rows indented under it, all ticked, each still its own toggle; switching it off unticks and hides them. View links carry the group like any checkbox; an older link naming only the classes still opens them. The five help entries are folded into one. Then "do not repeat cliff drops inside the ranges": the class rows read 5–10 m, 10–15 m … 50 m and more; the pointer and the tap popup keep the full names.

## 2026-10-19 · Openness within 500 m, edge distance coloured to 250 m

Owner: "Topographic openness: let that be 500m, Distance to ridge : 250m." The openness rays run to 500 m (sampled every cell out to 50 m, then every 10 m, so a near wall still counts without a five-fold cost) and the edge-distance colours run 0–250 m.

## 2026-10-19 · Terrain features: streams, mires, alpine plateaus, viewshed; openness, edge distance, ruggedness

Owner: "implement the terrain feature: streams and mires (flow accumulation), alpine plateaus, viewsheds (area seen /total area in 3d view)", then "and Topographic Openness", "and Distance to Ridge / Cliff Edges", "and Ruggedness (TRI/VRM)". Four new masks (`stream`, `mire`, `plateau`, `viewshed`) on the usual machinery — `flowAcc()` (priority flood + ε with a binary heap, D8, accumulation in the flood's order), a TWI rule for mires, a latitude-only tree line for plateaus, `viewshed()` (a ray to every edge cell from 1.75 m over the centre or a tapped point: the point popup gets a *Viewshed* button, the row writes the share of the view seen, the point travels in the view link as `vs:x/y`) — and a small graded-layer mechanism (`GRADED`, `gradedOn()`): a Float32 field per grid, colours over the fine grid's 1st–99th percentiles or a fixed range, a legend bar, the value under the pointer. Fields: `openness()` (Yokoyama, 100 m, on a ≤ 400² grid), `edgeDist()` (Felzenszwalb EDT to ridge crests and cliff brinks, 0–200 m), `triOf()`, `vrmOf()`. Eight help entries; README and the subpane's note updated (only coastal wave exposure is still "not yet").

## 2026-10-19 · Height ×1 by default

Owner: "default height should be 1x." The height slider starts at ×1 (was ×1.5). View links record the slider only when it is moved off this default, so links carrying `ex:1.5` still open at ×1.5.

## 2026-10-19 · The steepest-point pin removed

Owner: "remove red pin for steepest point." The red needle and ring are gone, with the search for the steepest cell within 500 m (and the edge-band helper it used); a `role` = `steepest` overlay point is no longer drawn. The compass is placed 250 m south of the centre instead. The Map toggle reads "Centre & circles".

## 2026-10-19 · Sun: Norway time only

Owner: "make norway time the only time option, and remove dropdown." The time-zone selector (Norway time / UTC) is gone; the sliders, the readout, Now and the first-view noon are all Norway time (CET/CEST by the EU rule). Old view links carrying a `tz` value are ignored.

## 2026-10-19 · Cliff drops painted solid

Owner: "the coloring of cliff faces should not be transparent." The five cliff classes now replace the base colour outright and are painted after the contour lines, which on a vertical face fall in nearly every cell and were darkening the colour; the other masks keep their 70 % blend under the contours.

## 2026-10-19 · Cliff drops: coloured on the face, the brink and the foot

Owner: "the vertical coloring should be on the side of the face and the first non-cliff 1m tile on top of cliff and bottom of cliff." The 2 m band around marked cells is gone: a passing face colours its own cells and, for each run, the highest neighbour of its top cell and the lowest neighbour of its bottom cell — one tile each. The bigger class wins where runs meet.

## 2026-10-19 · Cliff drops: two cells of smear allowed, the band widened

Owner: "I still do not see cliff faces detected and colored." Measured at Preikestolen (1 m, r = 800 m): 388 000 face cells drop ≥ 5 m, but after the one-cell allowance only 2.6 % measured 85°, the angles peaking at 75–80° — the 1 m DTM smears a vertical wall over two to three cells. Now two cells are taken off the run on 1 m grids (one on coarser), 12 % pass, and the marked cells are widened by 2 m so a face shows as a band rather than a one-cell hairline. Help and README say so.

## 2026-10-19 · Cliff drops in five height classes

Owner: "add the following terrain features: vertical cliff drops, 5-10m,10-15m, 15-25m,25-50m, 50m+ (85 -90 degrees)". Five DTM-derived masks (`cliff5` … `cliff50`), one toggle and colour each, from a shared class map (`cliffClasses`): from every cell whose steepest step to a neighbour is ≥ 60° (unsmoothed heights), the face is followed up and down its steepest line while the steps stay that steep; drop H over run L less one cell (the DTM smears a vertical wall over a cell) must be ≥ tan 85°; the class is H. Help per class, named under the pointer.

## 2026-10-19 · A place-name search in the map picker

Owner: "in the 2d map point picker, add a good location name search." A search box above the picker's map: Kartverket's stedsnavn API for Norway (fuzzy prefix search; each hit with its kind and municipality), Photon (OpenStreetMap) for what Kartverket does not know; searched as you type, an exact name first; a hit moves the map to it at zoom 13 or closer and places the point, Enter takes the first hit.

## 2026-10-19 · The view link carries only departures from the defaults

Owner: "the sharing link should only represent overrides from defaults, keep link as short as possible." The `v=` parameter is now a short text: `1=` boxes switched on, `0=` boxes switched off (relative to the defaults), `s=` settings that differ (plus the wind, snow and month choices of layers that are on), `h=` hidden legend classes of layers that are on, `c=` the camera only when it has left the home position; the separators stay unencoded. A view with nothing changed adds nothing. The first day's JSON links still open.

## 2026-10-19 · A pin in the title

Owner: "on top line, next to coordinates show a pin icon, for selecting new pont. if on mobile do not show lon,lat". A 📍 after the coordinates opens the map picker (the coordinates still do too); on screens up to 640 px wide the coordinates are hidden once a terrain is loaded and the pin stands alone.

## 2026-10-19 · ⧉ copies a link to the exact view

Owner: "on top line of the left pane add a copy icon, allowing user to share a link (must respect active selections, location, view etc)". A ⧉ button in the title row copies the terrain's link (as Share… builds it) with a `v=` parameter carrying every checkbox in the panel (on and off), the selects and sliders (wind, snow day and year, sun months, light mode, time zone, date, time, base map, height exaggeration, smoothing σ), the hidden slope / facing / NIBIO legend classes and the camera (position and target). On load the choices are applied before the terrain is built so the normal switch-on paths run, and the camera is put back once the terrain stands. The button shows ✓ for a moment; where the clipboard is not allowed the link is shown in the Data section to copy by hand.

## 2026-10-19 · "DTM derived" subpane

Owner: "the DTM derived features should be under a collapsible subpan \"DTM derived\"." Slope, Facing, Wind exposure and the masks worked out from the model (ridges … sheltered ground) now sit in a collapsible *DTM derived* subpane at the top of Terrain features, open by default; CORINE, the NIBIO groups and the snow layers follow it.

## 2026-10-19 · No "nothing in view" entries

Owner: "I dont want \"Nothing in view\" in legend, those entries should not show!" A layer with nothing in the view gets no legend entry at all; a group whose layers all have nothing shows no legend row.

## 2026-10-19 · Forestry plans group removed

Owner: "remove the subpane \"Forestry plans\"." The skogbruksplan group (development class, age of the oldest forest) is gone from the viewer; four NIBIO groups remain.

## 2026-10-19 · MIS habitats visible on 1 m views

Owner: "The MIS NBIO habitat overlays do not show in the 3d view when turned on." NIBIO draws the MIS features as outlines and symbols a few pixels wide at any scale; a 1 m view asked for 3000 px, so a key biotope came back as a 1 m hairline (0.09 % of the box against 0.84 % at 10 m per pixel). The MIS layers are now fetched at 10 m per pixel and scaled up onto the grid, so they look as they do on NIBIO's map; a MIS legend entry says "nothing in view" when its layer has no feature in the view.

## 2026-10-19 · NIBIO legends list only the classes in view, and toggle them

Owner, same request: "user should be able to turn specific overlays on/off by clicking legend." A click on a class in a NIBIO legend hides or shows that class (dimmed and struck through while hidden, as the slope and facing legends do; the pointer still names it, marked hidden); a click on a MIS entry switches that layer off. Each overlay image gets a per-pixel class map once (`nbClsMap`, memoised by colour), which the legend shares, the pointer and the paint all read.

Owner: "Only show legend for types in the selectd area (eg vegetation types have very many, keep it to those present in image)." `nbShares` counts the classes over both grids (every 5th pixel, as the CORINE legend does) and the legend lists those with at least 0.3 % of the painted area, largest first, with the share; "nothing in view" when none.

## 2026-10-19 · NIBIO classes in English

Owner: "in the hover text, and legend for NBIO overlays only show english names." `NB_EN` translates every class name the style sheets return (AR5, forestry plans, the 54 vegetation types and 13 main types) and the tap readouts' values; the legend and the pointer show the English only, a name without a translation is shown as served. SR16 species are spruce / pine / broadleaf.

## 2026-10-19 · NIBIO classes under the pointer

Owner: "the NBIO legends need to be showing in hover text. need some ocr and color detection for this maybe?" No OCR: the vector layers (AR5, forestry plans, vegetation types) answer WMS GetStyles with each class's name and fill colour, fetched once per layer; the SR16 rasters have no style sheet, so their eleven class tables were transcribed from NIBIO's legend images (`SR16_CL`, colours read by script, labels by eye; heights dm → m, LAI ÷ 100). The pointer samples the overlay's own pixel and names the nearest class (`nbAt`); the MIS layers, being symbols, are named by which of them have a pixel under the pointer. The legends are now built from the same tables (swatch + label), so legend and pointer always agree; a layer without a table (MIS) keeps the service's legend image.

## 2026-10-19 · The MIT licence named in the viewer

Owner: "Make sure all apps exposed on pages make it clear that they carry a mit licence." The attribution line under the view ends with "Viewer: MIT licence, github.com/pcmoan70/3d_terrain", and the help's last section says the same with the link.

## 2026-10-19 · NIBIO overlays: SR16, AR5, forestry plans, vegetation types, MIS habitats

Owner: "add nibo sr16 overlays, where user is allowed to toggle each type on and off" and "Any other nibio overlays that might be of interest, relevant to breeding and forage behaviours should be added as overlay options too." Five collapsible groups under Terrain features, one checkbox per layer (33 in all), served by NIBIO's WMS like CORINE (EPSG:25833, CORS open, one GetMap per grid, up to 3000 px because AR5 draws nothing coarser than 1:50 000): **SR16** (11 rasters), **AR5** (4), **Forestry plans** (2), **Vegetation types** (2), **MIS forest habitats** (14). The map-filling layers paint the whole ground, so one of them is on at a time (switching one on switches the others off); the MIS features stack. Legends are the services' own legend images; the help translates the Norwegian labels and says what each group means for nesting and foraging. A tap asks each service with a layer on for its values at the point: SR16's HTML answer carries every layer's cell value (heights dm → m, LAI ÷ 100), the others answer GML (AR5's four classes; the stand's class, age, site index and species; each MIS feature with its note). Attribution lists the groups on. One `blendImg` loop now serves CORINE, snow and these. Plan: `tasks/terrain3d-sr16_20261019.md` in the workspace.

## 2026-10-19 · Sun average: Jan – Apr to begin with, the range remembered

Owner: "The 'Sun: average direct radiations' should be default 'Jan-Apr', but remember state when user changes it." The two-handle month slider starts at Jan – Apr instead of the whole year; every move of a handle (and *Whole year*) stores the range in localStorage (`terrain3d-sunMonths`, device-wide, not per view), and the viewer restores it on load. Help, README updated.

## 2026-10-19 · Ground view

Later the same day (owner: "the buttons in the point popup should be Fetch+,Fetch,Ground view on one line under the 1m,10m ... dropdown"): the tap popup shows the model dropdown on its own line and one row of buttons under it — **Fetch+** (was *Fetch more*), **Fetch**, **Ground view** (was *Ground view here*); without a fetch context the row holds Ground view alone.

Owner: "in the 3d view, there should be a mode where view is from 175m above ground viewing the horizon supporting all overlays etc. 'Ground view'". A **Ground view** button beside Reset view / Top view (`groundView`): the camera is put 1.75 m (in the model's vertical scale, so it matches the exaggeration) above the ground at the point the view turns about and looks level in the current heading; the orbit target sits 60 m ahead and 1 m down, so ⟲ ⟳ and a rotate-drag turn the head, ▲ ▼ tilt, a drag walks, and the near-horizontal polar limit still holds. The tap popup gets **Ground view here** for the tapped point. First built at 175 m from the request's "175m"; the owner meant eye height ("I ment 1.75m"). Overlays are the terrain's paint, so all show.

## 2026-10-19 · Help: a ? behind every terrain feature, a sectioned help in the title

Owner: "Make a descriptive help text for each of the Terrain features (question marks behind toggle description) also the assumptions made. Also the windexposure seems to be written in degrees, this needs explanation. Other general functions need explanation in a sectioned helptext." A **?** button in the title opens one help panel (`#help`, centred, scrolls inside, × top-right) in sections — getting a terrain, moving around, map, terrain features, sun, pointing / tapping / measuring, data / saving / sharing — built from `HELP`; each terrain feature row (slope, facing, wind, CORINE, snow depth, snow days and the nine masks) gets a **?** that opens the panel at its entry (`FEAT_HELP`: what it shows, then *Assumptions*). The wind entry explains the degrees (the elevation angle of the steepest line to ground within 300 m upwind; +30° a wall, 0° level, −20° the ground falling away); the legend now says "the angle up to the highest ground within 300 m upwind, below level when the ground falls away" and the hover reads "upwind ground rises at 22° — sheltered" / "falls away at 16° — exposed". Checked in Chrome: 15 ? buttons, seven sections, the wind ? scrolls its heading to the panel's top, the panel fits the window.

## 2026-10-19 · Wind exposure; slope and facing classes toggle from their legends

Owner: "in the 3d viewer I would like a wind-exposure overlay, it should also have an option based on the dominating wind-direction." Terrain features gets **Wind exposure** with a wind choice: Winstral's shelter index Sx (`windSx`) on the sun model's coarse cells (`coarseH`, shared with `sunMonthly` now) — in 32 directions the steepest line of sight to the terrain upwind within 300 m — Winstral's range; 1 km was tried first and reached the far fjord wall at Preikestolen, so nearly everything read as sheltered — (through the coarse surround from the fine grid), each direction with its two neighbours (a 34° sector), as an angle: positive = higher ground upwind (sheltered), negative = the ground falls away (exposed). The overlay is a weighted mean over the directions (`windOn`): *all directions*, one compass point (grid convergence applied), or *the winds here* — the view centre's wind rose from Open-Meteo's ERA5 archive (`windRose`: daily dominant direction × peak speed over the last three years, CORS open, ~25 kB; the three main directions and their shares under the legend, "Winds: Open-Meteo (ERA5)" in the attribution; if it does not answer the overlay falls back to all directions and says so). Painted at 68 % on a red – pale – blue ramp with red at the view's 1st percentile, pale at its median and blue at its 99th (one range for both grids; a fixed ±20° made a mountain view all blue, pale pinned at 0 left the red end unused when every direction counts — the sector maximum is rarely negative away from summits — and a plain linear spread left most of the view reddish under the long sheltered tail) (`ramp` generalised from `sunRamp`, `atCoarse` from `sunAt`); the value and its reading under the pointer; recomputed for a new view when on.

Owner: "for the slope legend 27-30, 30-35,35-40 etc should be toggleable by color: user clicks on color/square to toggle overlay on/off for that particular slope. same for the facing legend." Each entry of the Slope and Facing legends is a toggle (`clsOff`): a click hides that class alone (dimmed, struck through), another shows it; where a hidden slope class sat, the facing colour shows through.

## 2026-10-18 · Snow depth, snow days and recent satellite imagery

Owner: "go for snow depth and recent satelite imagery" + "make sure to include the daygt50sdyr". Terrain features gets **Snow depth (seNorge, NVE)** with a day (any since 1957, nine days of forecast) and **Snow days > 5 cm (seNorge, NVE)** with a year: NVE's 1 km grids from gridwms.nve.no (CORS open; `sd` with `time=YYYY-MM-DD`, `daygt50sdyr` with `time=YYYY`), one GetMap per grid, kept per day, blended at 55 % like CORINE (`SNOWL`, `snowImage`, `snowAt`); the legend is seNorge's palette read off its legend graphic, the class under the pointer and in the tap popup comes from the colour; an all-transparent answer says "seNorge has nothing for … here"; the attribution line credits seNorge © NVE; a new view refetches the layers that are on. Map gets **Satellite, recent (NASA)**: NASA GIBS WMTS (CORS open) — the *Photo* list is the days of the last 30 with an HLS pass (Sentinel-2 S30 / Landsat L30, 30 m) over the view's centre, found by fetching one z12 tile per day and layer in parallel (an empty tile is a few hundred bytes), newest first, then the last three days of MODIS Terra true colour (250 m); the chosen day is draped like any tile map (`SAT`, `satStart`, `satUI`). NVE's own Sentinel-2 image services (gis4.nve.no NVE_Copernicus) were tried first and dropped: `time`, a `where` and LockRaster are all ignored and the default mosaic is cloud; NVE's pre-rendered S2 RGB service stops at November 2025. Tested in Chrome at Preikestolen (10 m, 1.5 km): snow depth 2026-03-01 → classes 25–50 / under 25 / bare ground, centre "bare ground"; snow days 2025 → 100–200 / 50–100 / 25–50, centre "10 – 25 days"; hover tip carries both lines; 2031-01-01 → the "nothing" message; the photo list found 14 HLS days (newest 2026-10-11) + 3 MODIS days, the Sentinel-2 and MODIS drapes both real imagery (0.2 % grey fill).

## 2026-10-18 · 1 m centre up to 5 km; a too-big 1 m square flips to the mixed model

Owner: "When user makes download square larger than 1m induced limit app automatically flips to 1m center and 10m surrounding, frames should indicate that. Also when user fetches more areas center 5k should be fetched at 1m even if 10m tiles exist." The 1 m centre of a mixed view may now reach the 1 m model's limit (5 km radius; it coarsens beyond 1.5 km like a 1 m view) instead of 1.5 km — picker, Data section, `buildAt` and the Fetch more union alike. In the picker, a 1 m radius dragged, wheeled or typed past 5 km sets the model to *1 m centre + 10 m around* with the centre at 5 km; the inner frame appears, and both corner handles carry a permanent label (*1 m* / *10 m*, or the single model's). A `?r=` link beyond 5 km at 1 m flips the same way. For a view built at 1 m or 10 m the 1 m radius used by the popup's mixed fetch is min(R, 5 km), so Fetch more at the mixed model fetches the centre 5 km at 1 m even where 10 m tiles are in hand (a mixed build keeps its own 1 m radius). Tested in Chrome: 7 km at 1 m → model n, centre 5 km, 4-corner inner frame, labels 10 m / 1 m; links 7 km/1 m → n + 5 km, 15 km/10 m → R1 5 km, 2 km/1 m → R1 2 km, 6 km/n/0.8 km kept; a 10 m 500 m build + Fetch more at n 500 m north → 4 new 1 m tiles, nested view R 750 / R1 750, "4 tiles new this time, 1 reused".

## 2026-10-18 — progress for the slow steps

Owner: "when 'Reading the terrain…' et things go slow, also show progress". The busy overlay has a progress bar (`busy(text, fraction)`); every long step feeds it: fetching tiles (k / n), reading files, **reading the terrain** (tile k / n, and inside a big tile every 400 rows — "Reading the surround…" / "…the centre…" on a nested view), **filling missing DTM** (`fillHoles` is async now, a yield every few relaxation sweeps, the fraction weighted by cells × sweeps so the finest level dominates), the map tiles, the sun's horizons and months, and the features (k / n). Short synchronous steps are named without a bar (Smoothing, Slopes, Shading, Painting). Tested in Chrome with a MutationObserver on the overlay: 140 distinct states on a 1 m 1.5 km build, the reading bar 0 → 100 % over 16 tiles, the filler's progress monotone to 1 on a synthetic grid.

## 2026-10-18 — Fetch more: nothing in hand is asked for again, and the status says so

Owner: "when fetching more tiles in a direction make sure the previously fetched tiles are not refetched." Already the rule (`wcsGather` skips every tile name in hand or known to have no data; the Cache API is the second guard) — now visible: the status line after a second fetch reads "… in N fetches (k tiles new this time, m reused)". Two things fixed on the way: a wide 1 m view asks 2 m tiles (`E…_2m.tif`), which `wcsShow` took for coarse ones (wrong model in scene.json, mixed-view detection off) — the cell is now read from the name (`tileCell`, fine = < 5 m); and a WCS tile is decoded (`sparseFix`) once and kept on its item, so a Fetch more re-renders without re-reading every tile.

## 2026-10-18 — CORINE under Terrain features

Owner: "Move the corrine option to 'Terrain features' subpane". The *CORINE land cover 2018 (NIBIO)* row and its legend sit at the end of the Terrain features section's fixed rows (after Facing, before the feature masks); nothing else changes — same ids, same behaviour. README.

## 2026-10-18 — Fetch more / Fetch from the tap popup

Owner: "user can add tiles at edges of the scene by clicking on a locations on the map getting a popup with 'fetch more': when clicked app fetches more tiles centered on that point (not re-fetching those existing) and expanding scene as the union of all fetches done, rerendering the scene at completion. User can then save the whole scene. There should also be a 'fetch' option that only re-renders the tiles around the last point." + "the fetching should have an option for 10m or 1m dtm tiles." A map-built view keeps its state in `WCSV`: every tile in hand, the no-data tiles (never asked again), and every square asked for `{X, Y, res}`. `wcsGather` fetches only the plan's tiles not in hand; `wcsShow` builds scene.json (+ the link's points) and renders; `wcsAt(lat, lon, res, more)` is **Fetch** (that square alone, the build's radius, the chosen model) or **Fetch more** (the bounding square of the union of all squares: centre = the bbox centre, R = half the longer side rounded to 50 m, capped at the model's largest radius — a note when capped). Mixed 1 m + 10 m tiles take the nested renderer with `radius_1m` = the 1 m squares' reach from the union centre (≤ 1.5 km). The popup (`pointMenu`, terrain taps on a map-built view only) carries the model `<select>` (default: the last fetch's) and the two buttons; a folder, file or Drive load clears `WCSV`. `buildAt` is now `WCSV` + one `wcsAt`. Save is unchanged — `SRC.items` holds every tile shown. Tested locally: 10 m build → Fetch more 1.6 km east (R 1800, centre moved, "in 2 fetches", no refetch) → Fetch at 1 m there (9 tiles, 1 m view, 1000 m) → Fetch more at 10 m at the start (mixed: `res n`, R 1800, 1 m centre 1500 m, 10 tiles, "in 4 fetches"). README.

## 2026-10-18 — points in the link

Owner: "The 3d viewer must support rich params allowing in addition to lat, lon to specify dots with descriptive text from BirdsWhere app to be drawn in 3d view". `#pts=<URL-encoded JSON>` — `[[lat, lon, name, text, colour] …]` — on a `?lat=&lon=&r=` link is read at build time (`linkPoints`) and fed into the folder as `points.geojson` with a `scene.layers` title, so it takes the ordinary overlay path: a pin per point, the file row *Points from the link* under Map, name and text in the tap popup. Points outside the block and malformed entries are dropped; colour is any CSS colour (BirdsWhere sends `hsl(…)` species colours). The hash is used because the server never sees it and the viewer's `history.replaceState` keeps it; **Share…** copies it along for a map-built view. README.

## 2026-10-17 — no cliff layer in the viewer

Owner: "remove 'Cliffs, quarries and islets' and the whole Birds sub section". The viewer no longer runs the cliff rules on a map-built view (the browser copy of the rules, `viewer/habitat.js`, its Overpass lookup of buildings, roads and quarries, and `tests/parity.py` are gone), and the Preikestolen demo lost its `habitat.geojson`. A map-built view is terrain, sun and the Terrain features only. The packager `viz3d.py` still writes a `habitat.geojson` (`lib/habitat.py`, `rules.json`), which the viewer shows as an ordinary overlay file under Map, starting switched off. README.

## 2026-10-17 — the Birds section is gone

Owner: "remove the 'Birds' dropdown subpane in 3d viewer". Every overlay file now lists under Map, after CORINE. `group: "birds"` in scene.json keeps one meaning: that layer starts switched off (the cliff layer of a built view too). Sections: Map, Terrain features, Sun, Data. README.

## 2026-10-17 — Slope and Facing under Terrain features

Owner: "move options inside subpane birds (slope, facing) into subpane 'terrain features'". The *Slope* (NVE steepness classes) and *Facing* rows, with their legends, now open the Terrain features section, above the feature masks. The Birds section holds only the bird overlay files (`group: "birds"` in scene.json, and the cliff rules of a map-built view) and is left out when a view has none. README.

## 2026-10-17 — terrain-feature layers; Shift + wheel for the radius; the square's turn explained

Owner: "why is the select square not aligned w edge of map. also square size should be controlled by shift-wheel. Add the various features listed as a possible selections in the menu." (1) The picker's square is the 3-D block, cut along the UTM zone 33 grid, which is turned by the grid convergence (about 8° at Preikestolen) against the north-up map; the status line now says the turn. (2) Shift + wheel changes the radius; the plain wheel zooms the map again. (3) A **Terrain features** section with nine layers: ridges and crests, gullies and ravines (terrain position index over 25 m, cliff faces excluded), ledges on cliffs, scree and boulder fields (1 m grids), lakes and ponds (level patches ≥ 400 m²), updraft slopes, and — from the sun model's monthly maps and horizons, computed on first use — sun-warmed slopes in spring, shade hollows (late snow), sheltered ground (low sky view). Masks are cached per grid, painted at 70 %, listed under the pointer. On the Preikestolen demo the six terrain-only layers compute in about 2 s. Not yet: streams and mires (flow accumulation), alpine plateaus, viewsheds, coastal wave exposure.

## 2026-10-17 — CORINE land cover overlay

Owner: "add support for the CORINE land cover as a map overlay in the 3d terrain view". Map section → *CORINE land cover 2018 (NIBIO)*: NIBIO's CLC WMS (`wms.nibio.no/cgi-bin/clc`, EPSG:25833, CORS open) is asked for the view's square per grid (≤ 1500 px) and blended at 55 % over the base map; the legend lists the classes in view by share (nearest standard CLC colour per pixel), hovering shows the class under the pointer, a tap adds the exact class from GetFeatureInfo (English + Norwegian, code) to the popup; the attribution line credits NIBIO / Copernicus. The EEA's own tile service was tried first but answers 404 for tiles. Checked at Preikestolen: colour lookup and the WMS agree (333 Sparsely vegetated areas); legend 57 % sparsely vegetated, 31 % sea, 12 % broad-leaved forest.

## 2026-10-17 — no "nesting habitat" wording

Owner: "Terrain 3d should not mention nesting habitat anywhere." The layer is "Cliffs, quarries and islets" (rules.json TITLE, the demo scene too), the point is "steepest point on a cliff", islets read "islet 1.1 ha — Small island, 1.1 ha, no building on it.", the status texts say "cliff rules" / "cliff areas". Python and JS texts changed alike (the parity test compares them).

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
