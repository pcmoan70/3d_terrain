#!/usr/bin/env python3
"""Put the current viewer (viewer/viewer3d_template.html + the inlined libraries) round already-built terrain
files, keeping each file's embedded folder — no recomputation.

    rewrap.py FILE.html … [--points FILE.geojson] [--viewer DIR]

--points: replace each file's points with those of FILE.geojson within the view (the steepest point is kept; a
top-level "layer" member names the layer). --viewer DIR: also rewrite DIR/index.html (the empty viewer)."""
import base64, json, math, os, re, sys
D = os.path.dirname(os.path.abspath(__file__))
LIBS = {"/*THREE*/": "three.min.js", "/*ORBIT*/": "OrbitControls.js", "/*GEOTIFF*/": "geotiff.js"}


def page(embed=""):
    p = open(os.path.join(D, "viewer", "viewer3d_template.html")).read()
    for k, f in LIBS.items(): p = p.replace(k, open(os.path.join(D, "vendor", f)).read())
    return p.replace("/*EMBED*/", embed)


args = sys.argv[1:]; P = None
if "--points" in args:
    i = args.index("--points"); P = json.load(open(args[i + 1])); del args[i:i + 2]
if "--viewer" in args:
    i = args.index("--viewer"); d = args[i + 1]; del args[i:i + 2]
    open(os.path.join(d, "index.html"), "w").write(page()); print("viewer ->", d)
for f in args:
    m = re.search(r'<script id="embed" type="application/json">(.*?)</script>', open(f).read(), re.S)
    if not m or not m.group(1).startswith("{"): print("skip (no embedded folder):", f); continue
    E = json.loads(m.group(1)); fs = E["files"]
    if P is not None and "scene.json" in fs and "points.geojson" in fs:
        from pyproj import Transformer
        sc = json.loads(base64.b64decode(fs["scene.json"])); to_u = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)
        X0, Y0 = to_u.transform(sc["lon"], sc["lat"]); R = float(sc["radius"])
        old = json.loads(base64.b64decode(fs["points.geojson"]))
        keep = [f_ for f_ in old["features"] if f_["properties"].get("role") == "steepest"]
        new = [f_ for f_ in P["features"] if f_["geometry"]["type"] == "Point"
               and math.hypot(*(v - w for v, w in zip(to_u.transform(*f_["geometry"]["coordinates"][:2]), (X0, Y0)))) <= R]
        fs["points.geojson"] = base64.b64encode(json.dumps({"type": "FeatureCollection", "features": keep + new}).encode()).decode()
        if P.get("layer"): sc.setdefault("layers", {})["points.geojson"] = P["layer"]
        fs["scene.json"] = base64.b64encode(json.dumps(sc).encode()).decode()
        print("  points:", len(new))
    open(f, "w").write(page(json.dumps(E))); print("rewrapped", os.path.basename(f))
