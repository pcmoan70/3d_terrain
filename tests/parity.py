#!/usr/bin/env python3
"""Parity of viewer/habitat.js with lib/habitat.py, on public data only.

    python3 tests/parity.py [--sync-rules]

Two scenes: the Preikestolen demo (site/scenes/preikestolen/dtm_1m.tif, 2 km square, 1 m; no N250, as on a fresh
clone) and a small synthetic one (an escarpment, a quarry, two islands, a building, a road, a missing corner) that
exercises the islet, quarry and distance paths with the same "people" given to both sides. Each is run exactly as
viz3d.py runs the rules, written to tests/fixtures/<name>.json (n, c, X, Y, R, people, h -> a raw float32 file
next to it, regenerated every run and not committed, py: the Python's steepest point and areas), run through the
JS with node (tests/run_js.js) and compared: cliff count (+-1), >= 95 % overlap (IoU) of the union of the cliff
areas, the steepest point within 2 m, the same islet count; and the rules block in habitat.js must equal
rules.json (--sync-rules rewrites it from rules.json). Prints PASS / FAIL."""
import json, math, os, subprocess, sys, tempfile
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, D)
# the Python rules read config.toml at import: point them at an empty one, so there is no N250 (as on a fresh clone)
_empty = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False); _empty.close()
os.environ["TERRAIN3D_CONFIG"] = _empty.name
import numpy as np
import rasterio
from affine import Affine
from scipy import ndimage
from scipy.spatial import cKDTree
from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
from lib import habitat

SCENE = os.path.join(D, "site", "scenes", "preikestolen")
FIX = os.path.join(D, "tests", "fixtures"); os.makedirs(FIX, exist_ok=True)
JS = os.path.join(D, "viewer", "habitat.js")
R_START, R_END = "var RULES = /* rules.json */ ", "; /* end rules.json */"


def js_rules_block():
    s = open(JS).read(); a = s.index(R_START) + len(R_START); b = s.index(R_END)
    return s, a, b


def sync_rules():
    s, a, b = js_rules_block()
    block = json.dumps(json.load(open(os.path.join(D, "rules.json"))), indent=2).replace("\n", "\n  ")
    open(JS, "w").write(s[:a] + block + s[b:]); print("habitat.js: rules block rewritten from rules.json")


def run_python(h, tf, X, Y, R, people=None):
    """The rules exactly as viz3d.py runs them. people = (buildings, road points, quarry polygons) stands in for
    N250 (None = without). Returns the JS-shaped result: coordinates relative to the centre."""
    bad = ~np.isfinite(h)
    hs = ndimage.gaussian_filter(np.where(bad, np.nanmean(h), h), habitat.SMOOTH_M)
    gy, gx = np.gradient(hs, 1.0)
    slope = np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32); slope[ndimage.binary_dilation(bad, iterations=3)] = np.nan
    aspect = (np.degrees(np.arctan2(-gx, gy)) + 360) % 360
    T = (h, slope, tf, aspect, bad)
    habitat.NEAR_R = R
    habitat._n250 = (cKDTree(np.array(people[0])), cKDTree(np.array(people[1])), STRtree(people[2]), people[2]) if people else (None, None, None, [])
    try: best, areas = habitat.near(T, X, Y, H=habitat.habitat(T))
    finally: habitat._n250 = None
    rel = lambda g: [[x - X, y - Y] for x, y in g.exterior.coords]
    return {"best": best and {"x": best[0] - X, "y": best[1] - Y, "slope": best[2], "dist": best[3]},
            "areas": [{"kind": pr["kind"], "ring": rel(g), "name": habitat.describe(pr)[0], "desc": habitat.describe(pr)[1]}
                      for pg, pr in areas for g in getattr(pg, "geoms", [pg])]}


def scene_preikestolen():
    scene = json.load(open(os.path.join(SCENE, "scene.json"))); R = float(scene["radius"])
    X, Y = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True).transform(scene["lon"], scene["lat"])
    with rasterio.open(os.path.join(SCENE, "dtm_1m.tif")) as src:
        h = src.read(1).astype(np.float32); tf = src.transform; nod = src.nodata
    h[(h < -1000) | (h == nod)] = np.nan
    n = h.shape[0]; assert h.shape == (n, n) and abs(tf.a) == abs(tf.e)
    assert abs(tf.c + n * tf.a / 2 - X) < 0.01 and abs(tf.f + n * tf.e / 2 - Y) < 0.01, "the TIFF is not centred on scene.json's lat/lon"
    return {"n": n, "c": float(tf.a), "X": X, "Y": Y, "R": R, "people": None, "py": run_python(h, tf, X, Y, R)}, h


def scene_synthetic():
    """600 m square, 1 m: land at ~40 m in the north with an escarpment down to the sea (faces S), a 6 m step
    inside a quarry (counts only as quarry), a 1 ha island, a smaller island with a building, a road, a
    missing-data corner."""
    n = 600; X, Y = 300000.0, 6600000.0; R = 280.0
    tf = Affine(1.0, 0.0, X - n / 2, 0.0, -1.0, Y + n / 2)
    i, j = np.mgrid[0:n, 0:n].astype(np.float64)
    h = np.where(i <= 200, 40.0, np.where(i < 215, 40.0 - (i - 200) * 2.7, 0.0))
    floor = 34.0 + 6.0 * np.clip((np.abs(j - 450) - 10) / 10, 0, 1)                                 # a pit: steep only on its N wall
    pit = (j >= 430) & (j < 470)
    h = np.where(pit & (i >= 95) & (i < 97), 40.0 - (40.0 - floor) * (i - 94) / 3, h)
    h = np.where(pit & (i >= 97) & (i < 100), floor, h)
    h = np.where(pit & (i >= 100) & (i < 130), floor + (40.0 - floor) * (i - 100) / 30, h)
    for ci, cj, rad, top in ((450, 300, 60, 12.0), (450, 100, 40, 8.0)):                            # two domed islands
        r = np.hypot(i - ci, j - cj); h = np.where(r < rad, np.maximum(h, top * (1 - (r / rad) ** 2)), h)
    h += 0.3 * np.sin(i * 0.37) * np.cos(j * 0.23)
    h[-40:, -40:] = np.nan                                                                          # a missing corner
    h = h.astype(np.float32)
    xy = lambda row, col: [tf.c + (col + .5) * tf.a, tf.f + (row + .5) * tf.e]
    buildings = [xy(450, 100), xy(150, 100)]
    roads = [xy(r, 500) for r in range(0, n, 25)]
    q = [xy(85, 420), xy(85, 480), xy(110, 480), xy(110, 420)]
    people = {"buildings": buildings, "roads": roads, "quarries": [q]}
    return {"n": n, "c": 1.0, "X": X, "Y": Y, "R": R, "people": people, "py": run_python(h, tf, X, Y, R, (buildings, roads, [Polygon(q)]))}, h


def poly(ring):
    p = Polygon(ring)
    return p if p.is_valid else make_valid(p)


def iou(a, b):
    u = a.union(b).area
    return a.intersection(b).area / u if u else 1.0


def compare(py, js, check):
    pc = [x for x in py["areas"] if x["kind"] != "islet"]; jc = [x for x in js["areas"] if x["kind"] != "islet"]
    pi = [x for x in py["areas"] if x["kind"] == "islet"]; ji = [x for x in js["areas"] if x["kind"] == "islet"]
    check("cliff count (+-1)", abs(len(pc) - len(jc)) <= 1, "Python %d, JS %d" % (len(pc), len(jc)))
    P = unary_union([poly(x["ring"]) for x in pc]); J = unary_union([poly(x["ring"]) for x in jc])
    check("cliff area overlap >= 95 %", iou(P, J) >= 0.95, "IoU %.2f %% (Python %.0f m2, JS %.0f m2, common %.0f m2)" % (100 * iou(P, J), P.area, J.area, P.intersection(J).area))
    bp, bj = py["best"], js["best"]
    if bp and bj:
        d = math.hypot(bp["x"] - bj["x"], bp["y"] - bj["y"])
        check("steepest point within 2 m", d <= 2, "%.2f m apart (Python %.2f deg, JS %.2f deg)" % (d, bp["slope"], bj["slope"]))
    else:
        check("steepest point", bp is None and bj is None, "Python %s, JS %s" % (bp, bj))
    check("islet count", len(pi) == len(ji), "Python %d, JS %d%s" % (len(pi), len(ji), "".join("; " + x["name"] for x in ji)))
    # informational: each area's best match and the text
    matched = same_name = same_desc = 0; unmatched = []
    pg = [poly(x["ring"]) for x in pc]; jg = [poly(x["ring"]) for x in jc]
    for x, g in zip(jc, jg):
        k, best = max(((k, iou(g, gy)) for k, gy in enumerate(pg)), key=lambda t: t[1], default=(None, 0))
        if best >= 0.5:
            matched += 1; same_name += pc[k]["name"] == x["name"]; same_desc += pc[k]["desc"] == x["desc"]
            if pc[k]["desc"] != x["desc"]: unmatched.append("text differs:\n          py %s\n          js %s" % (pc[k]["desc"], x["desc"]))
        else: unmatched.append("JS only: %s (%.0f m2, best IoU %.0f %%)" % (x["name"], g.area, 100 * best))
    for y, gy in zip(pc, pg):
        if not any(iou(gy, g) >= 0.5 for g in jg): unmatched.append("Python only: %s (%.0f m2)" % (y["name"], gy.area))
    print("  info  %d of %d JS cliff/quarry areas match a Python one (IoU >= 50 %%); %d with the identical name, %d the identical description"
          % (matched, len(jc), same_name, same_desc))
    for u in unmatched[:10]: print("        " + u)


def main():
    if "--sync-rules" in sys.argv: sync_rules()
    fails = []
    def check(name, cond, detail):
        if not cond: fails.append(name)
        print("  %s  %s: %s" % ("ok  " if cond else "FAIL", name, detail))

    s, a, b = js_rules_block()
    same = json.loads(s[a:b]) == json.load(open(os.path.join(D, "rules.json")))
    print("rules.json vs the block in viewer/habitat.js")
    check("rules in step", same, "identical" if same else "differ - run python3 tests/parity.py --sync-rules")
    for name, build in (("preikestolen", scene_preikestolen), ("synthetic", scene_synthetic)):
        fx, h = build(); fx["h"] = name + ".h.f32"
        np.ascontiguousarray(h, dtype="<f4").tofile(os.path.join(FIX, fx["h"]))
        json.dump(fx, open(os.path.join(FIX, name + ".json"), "w"))
        print("%s: %d x %d, c = %g m, R = %g m, %s; Python: %d areas"
              % (name, fx["n"], fx["n"], fx["c"], fx["R"], "with people" if fx["people"] else "no people", len(fx["py"]["areas"])))
        r = subprocess.run(["node", os.path.join(D, "tests", "run_js.js"), os.path.join(FIX, name + ".json")], capture_output=True, text=True)
        if r.returncode: print(r.stderr); sys.exit("node failed")
        js = json.loads(r.stdout)
        print("  JS: %d areas in %d ms" % (len(js["areas"]), js["ms"]))
        compare(fx["py"], js, check)
    print("PASS" if not fails else "FAIL: " + ", ".join(fails))
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
