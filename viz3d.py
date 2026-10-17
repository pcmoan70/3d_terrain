#!/usr/bin/env python3
"""A 3-D terrain view round a point, from Kartverket's 1 m terrain model. The viewer (viewer/viewer3d_template.html)
does all the processing and drawing in the browser from a "folder": 1 m DTM GeoTIFF tiles + .geojson/.kml/.kmz
overlays + an optional scene.json. A folder can be picked from the disk, or — when the viewer is served from
GitHub Pages / any web server — from the site itself: a folder there needs an index.json listing its files (a web
server cannot list a directory), and scenes/index.json is the catalog the picker shows.

    python3 viz3d.py LAT LON [--name NAME] [--radius 1000] [--points FILE.geojson] [--site DIR] [--out DIR]
      → site/                               ← servable as is (GitHub Pages)
          index.html                         the viewer (offline-capable: libraries inlined)
          scenes/index.json                  catalog: [{name, title, path}]
          scenes/<name>/index.json           {"files": [...]}
          scenes/<name>/dtm_1m.tif           Kartverket NHM DTM 1 m as is (cm, EPSG:25833); the viewer smooths it (optional)
          scenes/<name>/basemap_kv_topo.jpg  Kartverket topo draped on the view's grid (so the standalone file works offline)
          scenes/<name>/habitat.geojson      nesting-habitat areas (lib/habitat.py rules, coloured by facing)
          scenes/<name>/points.geojson       the steepest point on a nesting cliff + the --points within the radius
          scenes/<name>/scene.json           title, centre, radius, sigma (the suggested smoothing, m), layers, basemap
      → <out>/<name>_3dterrain.html          the same viewer with that folder built in (one file, opens offline)

--points FILE.geojson: a FeatureCollection of points (properties name, desc, role, color); a top-level "layer"
member {title, legend, group} names its layer in the viewer. Only the points within the radius are packaged.
Data stores (tile caches, optional N250) come from config.toml — see config.example.toml."""
import argparse, base64, json, math, os, sys
import numpy as np
import rasterio
from rasterio.merge import merge
from scipy import ndimage
from pyproj import Transformer
from affine import Affine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import dtm, habitat
from lib.config import CFG

D = os.path.dirname(os.path.abspath(__file__))
LIBS = {"/*THREE*/": "three.min.js", "/*ORBIT*/": "OrbitControls.js", "/*GEOTIFF*/": "geotiff.js"}
ap = argparse.ArgumentParser(description=__doc__.splitlines()[0]); ap.add_argument("lat", type=float); ap.add_argument("lon", type=float)
ap.add_argument("--name", default="site"); ap.add_argument("--radius", type=float, default=1000.0)
ap.add_argument("--points", default=None, help="GeoJSON points to show (those within the radius)")
ap.add_argument("--site", default=os.path.join(D, "site"), help="the servable site directory (viewer + scenes/)")
ap.add_argument("--out", default=".", help="where <name>_3dterrain.html goes")
ap.add_argument("--title", default=None)
a = ap.parse_args(); R = a.radius; SITE = a.site
to_u = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True); to_g = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
X, Y = to_u.transform(a.lon, a.lat)


def page(embed=""):
    p = open(os.path.join(D, "viewer", "viewer3d_template.html")).read()
    for k, f in LIBS.items(): p = p.replace(k, open(os.path.join(D, "vendor", f)).read())
    return p.replace("/*EMBED*/", embed)


# ---- terrain: the ±R square from the 1 km tiles (missing ones fetched), smoothed as the habitat rules use it
srcs = [rasterio.open(f) for f in dtm.fetch_tiles(X, Y, R) if os.path.exists(f)]
h, tf = merge(srcs, bounds=(X - R, Y - R, X + R, Y + R), nodata=-32767)
h = h[0].astype(np.float32); bad = h < -1000; h[bad] = np.nan
hs = ndimage.gaussian_filter(np.where(bad, np.nanmean(h), h), habitat.SMOOTH_M)
gy, gx = np.gradient(hs, 1.0)
slope = np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32); slope[ndimage.binary_dilation(bad, iterations=3)] = np.nan
aspect = (np.degrees(np.arctan2(-gx, gy)) + 360) % 360
T = (h, slope, tf, aspect, bad)
habitat.NEAR_R = R                                        # habitat over the whole view, not only 500 m
best, areas = habitat.near(T, X, Y, H=habitat.habitat(T))

out = os.path.join(SITE, "scenes", a.name); os.makedirs(out, exist_ok=True)
# A view wider than 3 km is packaged on a coarser grid: the cell is ⌈2R / 3000⌉ m, each cell the mean of the 1 m
# model under it — the habitat areas above stay 1 m.
CELL = max(1, math.ceil(2 * R / 3000))
hw = np.where(bad, np.nan, h)
if CELL > 1:
    k = hw.shape[0] // CELL
    hw = np.nanmean(hw[:k * CELL, :k * CELL].reshape(k, CELL, k, CELL), axis=(1, 3))
tfw = tf * Affine.scale(CELL)
badw = ~np.isfinite(hw)
prof = dict(driver="GTiff", width=hw.shape[1], height=hw.shape[0], count=1, dtype="float32", crs="EPSG:25833", transform=tfw,
            nodata=-32767, compress="deflate", zlevel=9, predictor=3, tiled=True, blockxsize=256, blockysize=256)
# the RAW 1 m model — the viewer smooths it (σ 1.5 m by default, as the habitat rules do) or shows it as is
for f in ("dtm_smoothed_1m.tif",):
    if os.path.exists(os.path.join(out, f)): os.remove(os.path.join(out, f))
with rasterio.open(os.path.join(out, "dtm_1m.tif"), "w", **prof) as dst:
    dst.write(np.where(badw, -32767, np.round(np.nan_to_num(hw, nan=-32767) * 100) / 100).astype(np.float32), 1)

# The Kartverket topo map draped onto this view's grid (the standalone file carries this one so it works offline —
# Kartverket's tiles are open data, CC BY 4.0). Web-Mercator XYZ tiles at the zoom whose pixel is ~ one grid cell,
# cached under <map_tiles>/, sampled at each grid cell's exact lat/lon.
def drape_kv(layer="topo"):
    from PIL import Image
    n = hw.shape[0]; c = CELL
    ii, jj = np.meshgrid(np.arange(n), np.arange(n))
    E = X - R + (ii + 0.5) * c; N = Y + R - (jj + 0.5) * c
    lon, lat = to_g.transform(E, N)
    z = int(min(18, max(1, math.ceil(math.log2(156543.03 * math.cos(math.radians(a.lat)) / (c * 1.25))))))
    while True:
        mx = (lon + 180) / 360 * 2 ** z * 256
        my = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * 2 ** z * 256
        tx0, tx1, ty0, ty1 = int(mx.min() // 256), int(mx.max() // 256), int(my.min() // 256), int(my.max() // 256)
        if (tx1 - tx0 + 1) * (ty1 - ty0 + 1) <= 400 or z <= 1: break
        z -= 1
    mos = np.full(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 3), 216, np.uint8)
    cache = os.path.join(CFG["map_tiles"], "kv_" + layer, str(z)); os.makedirs(cache, exist_ok=True)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            fn = os.path.join(cache, "%d_%d.png" % (tx, ty))
            if not os.path.exists(fn):
                url = "https://cache.kartverket.no/v1/wmts/1.0.0/%s/default/webmercator/%d/%d/%d.png" % (layer, z, ty, tx)
                d = dtm.fetch_backoff(url, ok=lambda b: b[:8] == b"\x89PNG\r\n\x1a\n" or b[:2] == b"\xff\xd8", timeout=60, label="map tile %d/%d/%d" % (z, tx, ty))
                if d is None: print("  tile failed", z, tx, ty); continue
                open(fn, "wb").write(d)
            try: mos[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = np.asarray(Image.open(fn).convert("RGB"))
            except Exception: pass
    u = np.clip((mx - tx0 * 256).astype(int), 0, mos.shape[1] - 1); v = np.clip((my - ty0 * 256).astype(int), 0, mos.shape[0] - 1)
    img = Image.fromarray(mos[v, u])
    img.save(os.path.join(out, "basemap_kv_%s.jpg" % layer), "JPEG", quality=85)
    print("  Kartverket %s draped: zoom %d, %d tiles, %d×%d" % (layer, z, (tx1 - tx0 + 1) * (ty1 - ty0 + 1), n, n))
drape_kv("topo")

ll = lambda x, y: [round(v, 7) for v in to_g.transform(x, y)]
feats = []
for pg, pr in areas:
    col = habitat.COLOURS.get(pr["kind"]) if pr["kind"] != "cliff" else habitat.FACE_COLOURS.get(pr.get("aspect"), habitat.COLOURS[max(1, min(pr["score"], 3))])
    nm, desc, _ = habitat.describe(pr)
    for g in getattr(pg, "geoms", [pg]):
        feats.append({"type": "Feature", "properties": {"name": nm, "desc": desc, "color": col, "kind": pr["kind"]},
                      "geometry": {"type": "Polygon", "coordinates": [[ll(x, y) for x, y in g.exterior.coords]]}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(out, "habitat.geojson"), "w"))

pts = []
if best:
    pts.append({"type": "Feature", "properties": {"name": "steepest point on a nesting cliff, %.0f°" % best[2], "role": "steepest", "color": "#dc1414"},
                "geometry": {"type": "Point", "coordinates": ll(best[0], best[1])}})
layers = {"habitat.geojson": {"title": habitat.TITLE, "group": "birds", "legend": habitat.LEGEND}}
if a.points:
    P = json.load(open(a.points))
    for f in P["features"]:
        if f["geometry"]["type"] != "Point": continue
        x, y = to_u.transform(*f["geometry"]["coordinates"][:2])
        if math.hypot(x - X, y - Y) <= R: pts.append(f)
    if P.get("layer"): layers["points.geojson"] = P["layer"]
json.dump({"type": "FeatureCollection", "features": pts}, open(os.path.join(out, "points.geojson"), "w"))
title = a.title or a.name.replace("_", ", ")
json.dump({"title": title, "lat": a.lat, "lon": a.lon, "radius": R, "sigma": habitat.SMOOTH_M if CELL == 1 else 0, "cell": CELL,
           "basemap": {"id": "kv_topo", "file": "basemap_kv_topo.jpg"},
           # the viewer is generic: this folder names its own layers and explains their colours
           "layers": layers, "source": "Kartverket NHM DTM 1 m (CC BY 4.0)"}, open(os.path.join(out, "scene.json"), "w"))
names = sorted(f for f in os.listdir(out) if f != "index.json")
json.dump({"files": names}, open(os.path.join(out, "index.json"), "w"))
cat_p = os.path.join(SITE, "scenes", "index.json")
cat = [c for c in (json.load(open(cat_p)) if os.path.exists(cat_p) else []) if c["name"] != a.name]
cat = sorted(cat + [{"name": a.name, "title": title, "path": "scenes/%s/" % a.name}], key=lambda c: c["name"])
json.dump(cat, open(cat_p, "w"), indent=1)
open(os.path.join(SITE, "index.html"), "w").write(page())
print("terrain %d×%d m, %.0f–%.0f m a.s.l.; %d habitat areas; %d points; steepest %s"
      % (h.shape[1], h.shape[0], np.nanmin(h), np.nanmax(h), len(feats), len(pts), best and "%.0f°" % best[2]))

files = {f: base64.b64encode(open(os.path.join(out, f), "rb").read()).decode() for f in names}
os.makedirs(a.out, exist_ok=True)
html = os.path.join(a.out, "%s_3dterrain.html" % a.name)
open(html, "w").write(page(json.dumps({"files": files})))
print("-> %s %.1f MB; folder %s (catalog: %d scenes)" % (html, os.path.getsize(html) / 1e6, out, len(cat)))
