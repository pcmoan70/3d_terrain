"""Nesting-habitat rules on the 1 m terrain: the steep areas (≥ STEEP_DEG) as polygons, which of them are
nesting CLIFFS, the steepest point near the centre.

A steep area counts as a nesting cliff only when its face is ≥ CLIFF_MIN_H high (nests sit 10–30 m up the
face; road cuts and banks drop out) and it looks E … S … W (FACING: more sun, less snow in the breeding
season). Each cliff gets its facing, its height, and — with Kartverket's N250 configured (config.toml
`n250`) — its distance to the nearest building and road (disturbance); steep areas inside an N250 quarry
are kept as "quarry" (artificial cliffs are used). Small islands (< ISLET_MAX_HA, no N250 building on
them) are "islet" areas: on the outer coast cliff-nesters nest on the ground there. Without N250 the
distances are unknown, no quarries are told apart, and every small island counts.
Nothing within EDGE_M of the data's edge (the view's border, a missing tile) is detected: the slope there
is made of the border's padding, not the ground."""
import json, math, os
import numpy as np
from rasterio import features
from scipy import ndimage
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from .config import CFG

# every tunable constant lives in rules.json (shared with viewer/habitat.js; tests/parity.py keeps the two in step)
_R = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules.json")))
STEEP_DEG = _R["STEEP_DEG"]; SMOOTH_M = _R["SMOOTH_M"]; MIN_AREA = _R["MIN_AREA"]
NEAR_R = _R["NEAR_R"]                       # viz3d sets it to the view's radius at run time
CLIFF_MIN_H = _R["CLIFF_MIN_H"]; HIGH_FACE_M = _R["HIGH_FACE_M"]
FACING = tuple(_R["FACING"]); PREF_FACING = tuple(_R["PREF_FACING"]); VERTICAL_DEG = _R["VERTICAL_DEG"]
FACE_PAD = int(_R["FACE_PAD_M"]); DROP_HALF = int(_R["DROP_HALF_M"])
ISLET_MAX_HA = _R["ISLET_MAX_HA"]; ISLET_MIN_M2 = _R["ISLET_MIN_M2"]; SEA_LEVEL_M = _R["SEA_LEVEL_M"]
NEAR_BUILDING, NEAR_ROAD = _R["NEAR_BUILDING"], _R["NEAR_ROAD"]
EDGE_M = _R["EDGE_M"]; SIMPLIFY_CLIFF_M = _R["SIMPLIFY_CLIFF_M"]; SIMPLIFY_ISLET_M = _R["SIMPLIFY_ISLET_M"]
COLOURS = {int(k) if k.isdigit() else k: v for k, v in _R["COLOURS"].items()}
FACE_COLOURS = _R["FACE_COLOURS"]; LEGEND = _R["LEGEND"]; TITLE = _R["TITLE"]

_n250 = None


def _people():
    """N250 buildings (points), roads (points every 25 m along the centre lines) as KD-trees, and the
    quarry polygons (STRtree) — loaded once; (None, None, None, []) without N250."""
    global _n250
    if _n250 is None:
        if not CFG["n250"]:
            _n250 = (None, None, None, [])
        else:
            import pyogrio
            from scipy.spatial import cKDTree
            from shapely.strtree import STRtree
            b = pyogrio.read_dataframe(CFG["n250"], layer="N250_BygningerOgAnlegg_posisjon", where="objtype = 'Bygning'")
            bx = np.array([(g.x, g.y) for g in b.geometry])
            r = pyogrio.read_dataframe(CFG["n250"], layer="N250_Samferdsel_senterlinje", where="objtype = 'Veglenke'")
            rp = []
            for g in r.geometry:
                for ln in getattr(g, "geoms", [g]):
                    L = ln.length; n = max(2, int(L // 25) + 1)
                    rp.extend((pt.x, pt.y) for pt in (ln.interpolate(t) for t in np.linspace(0, L, n)))
            q = pyogrio.read_dataframe(CFG["n250"], layer="N250_Arealdekke_omrade", where="objtype = 'Steinbrudd'")
            qg = list(q.geometry)
            _n250 = (cKDTree(bx), cKDTree(np.array(rp)), STRtree(qg), qg)
    return _n250


def _aspect_name(deg):
    return ("N", "NE", "E", "SE", "S", "SW", "W", "NW")[int(((deg + 22.5) % 360) // 45)]


_band = (None, None)
def edge_band(T):
    """True within EDGE_M of the read window's border or of no-data (a missing tile, the model's own
    edge): the slope there is made up of the border's padding, not the ground — nothing is detected in it."""
    global _band
    h, slope, tf, aspect, bad = T
    if _band[0] is slope: return _band[1]
    px = max(1, int(math.ceil(EDGE_M / abs(tf.a))))
    edge = np.pad(bad, 1, constant_values=True)
    band = (ndimage.distance_transform_edt(~edge) <= px)[1:-1, 1:-1]
    _band = (slope, band)
    return band


def habitat(T):
    """Label the read square's nesting habitat. Returns (cliff_lab, cliffs, islet_mask): cliffs =
    {label: dict(height, aspect, pref, quarry)} for steep areas whose face is ≥ CLIFF_MIN_H high.
    Nothing within EDGE_M of the data's edge counts (edge_band)."""
    h, slope, tf, aspect, bad = T
    band = edge_band(T)
    steep = ndimage.binary_closing(np.nan_to_num(slope) >= STEEP_DEG, iterations=1) & ~band
    lab, n = ndimage.label(steep)
    cliffs = {}
    if n:
        big = ndimage.grey_dilation(lab, size=(2 * FACE_PAD + 1,) * 2)                   # the face + 3 m round it: its foot and its top
        hf = np.where(np.isnan(h), np.nanmean(h), h)
        drop10 = ndimage.maximum_filter(hf, 2 * DROP_HALF + 1) - ndimage.minimum_filter(hf, 2 * DROP_HALF + 1)   # height difference within ±DROP_HALF m
        d10 = ndimage.maximum(drop10, lab, range(1, n + 1))
        vert = ndimage.mean((np.nan_to_num(slope) >= VERTICAL_DEG).astype(np.float32), lab, range(1, n + 1))
        hmax = ndimage.maximum(np.nan_to_num(h, nan=-1e4), big, range(1, n + 1))
        hmin = ndimage.minimum(np.nan_to_num(h, nan=1e4), big, range(1, n + 1))
        a_s = ndimage.sum(np.sin(np.radians(aspect)), lab, range(1, n + 1)); a_c = ndimage.sum(np.cos(np.radians(aspect)), lab, range(1, n + 1))
        _, _, qtree, qg = _people()
        com = ndimage.center_of_mass(steep, lab, range(1, n + 1))
        for i in range(n):
            ht = float(hmax[i] - hmin[i])
            r_, c_ = com[i]; cx = tf.c + (c_ + .5) * tf.a; cy = tf.f + (r_ + .5) * tf.e
            quarry = qtree is not None and any(qg[j].contains(Point(cx, cy)) for j in qtree.query(Point(cx, cy)))
            if ht < CLIFF_MIN_H and not quarry: continue
            asp = float((np.degrees(np.arctan2(a_s[i], a_c[i])) + 360) % 360)
            if not (FACING[0] <= asp <= FACING[1]): continue                # N / NE / NW faces are not nesting cliffs here
            cliffs[i + 1] = dict(height=ht, aspect=asp, pref=PREF_FACING[0] <= asp <= PREF_FACING[1], quarry=quarry, cx=cx, cy=cy,
                                 top=float(hmax[i]), foot=float(hmin[i]), drop10=float(d10[i]), vertical=float(vert[i]))
    # islets: land patches not touching the square's edge. The 1 m model fills the SEA with ~0 m (it
    # is not "no data"); lakes lie at their own surface height, so sea = ground at or below SEA_LEVEL_M.
    sea = bad | (np.nan_to_num(h, nan=0.0) <= SEA_LEVEL_M)
    sea = ndimage.binary_opening(sea, iterations=2)                    # a low rock or a jetty is not the sea
    land = ~sea; il, ni = ndimage.label(land)
    edge = set(np.unique(np.concatenate([il[0], il[-1], il[:, 0], il[:, -1]]))) - {0}
    edge |= set(np.unique(il[band & land])) - {0}               # nor an islet within EDGE_M of the data's edge
    area = ndimage.sum(land, il, range(1, ni + 1)) if ni else []
    btree = _people()[0]
    islet = np.zeros(land.shape, bool)
    for i in range(ni):
        if (i + 1) in edge or area[i] > ISLET_MAX_HA * 1e4 or area[i] < ISLET_MIN_M2: continue
        m = il == (i + 1); rr, cc = np.nonzero(m)
        xs = tf.c + (cc + .5) * tf.a; ys = tf.f + (rr + .5) * tf.e
        if btree is not None and btree.query_ball_point([float(xs.mean()), float(ys.mean())], r=math.sqrt(area[i] / math.pi) + 20): continue   # a building on it
        islet |= m
    return lab, cliffs, islet


def shape_of(p):
    """Length / width of the area (its minimum rotated rectangle), the bearing its long side runs,
    solidity (area ÷ convex hull) and a plain shape word: a long BAND (a wall), a compact OUTCROP,
    or BROKEN ground (scattered pieces)."""
    r = p.minimum_rotated_rectangle
    xy = list(r.exterior.coords)[:4]
    e1 = math.hypot(xy[1][0] - xy[0][0], xy[1][1] - xy[0][1]); e2 = math.hypot(xy[2][0] - xy[1][0], xy[2][1] - xy[1][1])
    if e1 >= e2: L, W, (ax, ay) = e1, e2, (xy[1][0] - xy[0][0], xy[1][1] - xy[0][1])
    else: L, W, (ax, ay) = e2, e1, (xy[2][0] - xy[1][0], xy[2][1] - xy[1][1])
    bearing = (math.degrees(math.atan2(ax, ay)) + 180) % 180         # the long side's direction, 0–180° from north
    solid = p.area / max(p.convex_hull.area, 1e-9)
    word = "band" if L >= 3 * max(W, 1) and solid >= .5 else ("broken" if solid < .5 else "outcrop")
    run = ("N–S", "NE–SW", "E–W", "SE–NW")[int(((bearing + 22.5) % 180) // 45)]
    return dict(length=L, width=W, runs=run, solidity=solid, shape=word)


def _m(v):
    return "%.0f m" % v if math.isfinite(v) else "unknown (no N250)"


def describe(pr):
    """(name, description, ExtendedData fields) of one habitat area, in plain words."""
    if pr["kind"] == "islet":
        return ("islet %.1f ha (ground nests)" % (pr["area"] / 1e4),
                "Small island, %.1f ha, no building on it: cliff-nesters nest on the ground on such islets." % (pr["area"] / 1e4), [])
    fit = {3: "good", 2: "fair"}.get(min(pr["score"], 3), "poor")
    shape_w = {"band": "a cliff band (wall)", "outcrop": "a compact rock outcrop", "broken": "broken, scattered steep ground"}[pr["shape"]]
    name = "%s %.0f m drop, %s %.0f m long, faces %s (%s)" % (pr["kind"], pr["height"], pr["shape"], pr["length"], pr["aspect"], fit)
    desc = ("%s: %s, %.0f × %.0f m, runs %s, faces %s. Drop %.0f m — top %.0f m, foot %.0f m above sea level; "
            "the sharpest step is %.0f m within %.0f m, %.0f %% of the face is near-vertical (≥ %.0f°), steepest %.0f°. "
            "Nearest building %s, road %s. Fit: %s (%s, %s, %s)."
            % (pr["kind"].capitalize(), shape_w, pr["length"], pr["width"], pr["runs"], pr["aspect"], pr["height"], pr["top"], pr["foot"],
               pr["drop10"], 2 * DROP_HALF, 100 * pr["vertical"], VERTICAL_DEG, pr["max_deg"], _m(pr["d_building"]), _m(pr["d_road"]), fit,
               "faces the sun" if pr["pref"] else "not S-facing", "high face" if pr["height"] >= HIGH_FACE_M else "low face",
               "close to people" if (pr["d_building"] < NEAR_BUILDING or pr["d_road"] < NEAR_ROAD) else "away from people"))
    ed = [("shape", pr["shape"]), ("length_m", "%.0f" % pr["length"]), ("width_m", "%.0f" % pr["width"]), ("runs", pr["runs"]),
          ("faces", pr["aspect"]), ("drop_m", "%.0f" % pr["height"]), ("top_m", "%.0f" % pr["top"]), ("foot_m", "%.0f" % pr["foot"]),
          ("drop_10m", "%.0f" % pr["drop10"]), ("vertical_pct", "%.0f" % (100 * pr["vertical"])), ("max_slope_deg", "%.0f" % pr["max_deg"]),
          ("building_m", "%.0f" % pr["d_building"]), ("road_m", "%.0f" % pr["d_road"]), ("fit", fit)]
    return name, desc, ed


def near(T, X, Y, H=None):
    """Within NEAR_R of (X, Y): the steepest pixel ON A NESTING CLIFF (X, Y, slope°, distance m; the
    steepest pixel anywhere when there is no cliff) and the habitat areas [(shapely polygon in
    EPSG:25833, props)] — cliffs with height, facing, distances to people and a suitability class, and
    islets."""
    h, slope, tf, aspect = T[:4]
    lab, cliffs, islet = H if H is not None else habitat(T)
    rr, cc = np.mgrid[0:slope.shape[0], 0:slope.shape[1]]
    xs = tf.c + (cc + .5) * tf.a; ys = tf.f + (rr + .5) * tf.e
    inR = (np.hypot(xs - X, ys - Y) <= NEAR_R) & ~edge_band(T)   # never the steepest pixel at the data's edge
    oncliff = np.isin(lab, list(cliffs)) & inR
    best = None
    for m in (oncliff, inR):
        sl = np.where(m, slope, np.nan)
        if not np.all(np.isnan(sl)):
            k = np.unravel_index(np.nanargmax(sl), sl.shape)
            best = (float(xs[k]), float(ys[k]), float(sl[k]), float(math.hypot(xs[k] - X, ys[k] - Y))); break
    btree, rtree, _, _ = _people()
    out = []
    # Each area is described by ITS OWN pixels inside the circle (a mountainside of connected steep
    # ground was reported as one "cliff" with a 1 000 m drop when the whole component was measured).
    sel = np.where(oncliff, lab, 0).astype(np.int32)
    objs = ndimage.find_objects(sel)
    for v, sl_ in enumerate(objs, start=1):
        if sl_ is None: continue
        r0, r1 = max(0, sl_[0].start - 4), min(sel.shape[0], sl_[0].stop + 4); c0, c1 = max(0, sl_[1].start - 4), min(sel.shape[1], sl_[1].stop + 4)
        m = sel[r0:r1, c0:c1] == v
        if m.sum() < MIN_AREA: continue
        c = cliffs[v]
        hh = h[r0:r1, c0:c1]; dil = ndimage.binary_dilation(m, iterations=FACE_PAD)
        top = float(np.nanmax(np.where(dil, hh, np.nan))); foot = float(np.nanmin(np.where(dil, hh, np.nan)))
        if top - foot < CLIFF_MIN_H and not c["quarry"]: continue          # this part of the face is too low
        hf = np.where(np.isnan(hh), np.nanmean(hh), hh)
        drop10 = float((ndimage.maximum_filter(hf, 2 * DROP_HALF + 1) - ndimage.minimum_filter(hf, 2 * DROP_HALF + 1))[m].max())
        ssub = slope[r0:r1, c0:c1]; asub = aspect[r0:r1, c0:c1]
        asp = float((np.degrees(np.arctan2(np.sin(np.radians(asub[m])).sum(), np.cos(np.radians(asub[m])).sum())) + 360) % 360)
        if not (FACING[0] <= asp <= FACING[1]): continue                # this part of the face looks N / NE / NW
        pref = PREF_FACING[0] <= asp <= PREF_FACING[1]
        rr_, cc_ = np.nonzero(m); cx = tf.c + (c0 + cc_.mean() + .5) * tf.a; cy = tf.f + (r0 + rr_.mean() + .5) * tf.e
        db = float(btree.query([cx, cy])[0]) if btree is not None else math.inf; dr = float(rtree.query([cx, cy])[0]) if rtree is not None else math.inf
        geoms = [shape(g) for g, val in features.shapes(m.astype(np.uint8), mask=m, transform=tf * tf.translation(c0, r0)) if val == 1]
        p = max(geoms, key=lambda g: g.area) if len(geoms) == 1 else unary_union(geoms)
        if p.area < MIN_AREA: continue
        height = top - foot
        disturbed = db < NEAR_BUILDING or dr < NEAR_ROAD
        score = 1 + (1 if pref else 0) + (1 if height >= HIGH_FACE_M else 0) - (1 if disturbed else 0)
        for part in getattr(p, "geoms", [p]):
            if part.area < MIN_AREA: continue
            out.append((part.simplify(SIMPLIFY_CLIFF_M), dict(kind="quarry" if c["quarry"] else "cliff", area=float(part.area), max_deg=float(np.nanmax(np.where(m, ssub, np.nan))),
                        height=height, aspect=_aspect_name(asp), pref=pref, d_building=db, d_road=dr, score=score,
                        top=top, foot=foot, drop10=drop10, vertical=float(np.mean(np.nan_to_num(ssub[m]) >= VERTICAL_DEG)), **shape_of(part))))
    isl = (islet & inR).astype(np.uint8)
    for g, v in features.shapes(isl, mask=isl > 0, transform=tf):
        p = shape(g)
        if p.area < ISLET_MIN_M2: continue
        out.append((p.simplify(SIMPLIFY_ISLET_M), dict(kind="islet", area=float(p.area), score=2)))
    return best, out
