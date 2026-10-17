/* habitat.js - the nesting-habitat rules (cliff-nesters) on a square terrain grid, in the browser: a copy of
   lib/habitat.py plus the preprocessing viz3d.py does before it (smoothing, slope, facing). Plain ES2018, no
   imports, no build step. The constants below are a verbatim copy of rules.json; tests/parity.py checks that
   and compares the results with the Python on public data.

   window.Habitat = { rules, compute(h, n, c, opts) }
     h     Float32Array n*n heights (m), rows north -> south, NaN = no data
     n     grid side (cells)
     c     cell size (m). The rules are written for 1 m; with c > 1 the pixel thresholds scale (EDGE_M / c,
           MIN_AREA / c^2, filter windows ~ metres / c, at least 1)
     opts  { X, Y   the grid centre in EPSG:25833 metres (needed only with people),
             R      NEAR_R: areas + steepest point within this of the centre (default rules.NEAR_R),
             people optional { buildings: [[x, y], ...], roads: [[x, y], ...] (points every ~25 m),
                               quarries: [[[x, y], ...], ...] (outer rings) } in EPSG:25833 metres }
   -> { best:  { x, y, slope, dist } | null      the steepest pixel on a nesting cliff (anywhere, if none)
        areas: [{ ring: [[x, y], ...], kind: "cliff" | "quarry" | "islet", name, desc, color, props }] }
   x, y (best and the rings) are metres from the grid centre, x east, y north. Without `people` the distances
   are Infinity ("unknown (no N250)"), there are no quarries and every small island counts - as the Python
   without N250. Rings are the outer rings only (the area in props is the exact pixel area, holes included). */
(function () {
  'use strict';
  var RULES = /* rules.json */ {
    "_doc": {
      "": "Nesting-habitat rules (cliff-nesters) shared by lib/habitat.py and viewer/habitat.js; tests/parity.py keeps the JS copy in step. Metres on the 1 m grid, degrees with 0 = north clockwise.",
      "STEEP_DEG": "a 1 m pixel this steep (degrees) counts as cliff",
      "SMOOTH_M": "the DTM is smoothed by this sigma (m) before slopes: one odd pixel (a road edge) cannot win",
      "MIN_AREA": "m2: smaller steep specks are not drawn",
      "NEAR_R": "m: polygons + steepest point within this of the centre (viz3d sets it to the view's radius)",
      "CLIFF_MIN_H": "m: a nesting cliff's face is at least this high",
      "HIGH_FACE_M": "m: a face at least this high is a 'high face' (one point of fit)",
      "FACING": "degrees [from, to]: only faces looking E ... S ... W count - more sun, less snow in the breeding season",
      "PREF_FACING": "degrees [from, to]: the preferred, sun-facing band SE ... S ... SW (one point of fit)",
      "VERTICAL_DEG": "degrees: a pixel at least this steep is near-vertical (the face's vertical share)",
      "FACE_PAD_M": "m: the face plus this much round it gives its top and foot (grey dilation 2*pad+1, binary dilation pad)",
      "DROP_HALF_M": "m: the sharpest step = height range within +-this (max - min filter of size 2*half+1)",
      "ISLET_MAX_HA": "ha: islands this small (inside the read square) are ground-nest islets",
      "ISLET_MIN_M2": "m2: smaller islands (and islet polygons) are left out",
      "SEA_LEVEL_M": "m: the 1 m model fills the sea with ~0 m; ground at or below this is sea",
      "NEAR_BUILDING": "m: a cliff closer than this to a building is less suitable",
      "NEAR_ROAD": "m: a cliff closer than this to a road is less suitable",
      "EDGE_M": "m: nothing is detected this close to the data's edge (the view's border, a missing tile)",
      "SIMPLIFY_CLIFF_M": "m: Douglas-Peucker tolerance of the cliff polygons",
      "SIMPLIFY_ISLET_M": "m: Douglas-Peucker tolerance of the islet polygons",
      "COLOURS": "fill by kind (quarry, islet) and, as a fallback, by fit score 1..3",
      "FACE_COLOURS": "cliff fill by facing: S strongest, SE / SW orange, E / W pale",
      "LEGEND": "[[colour, label], ...] of the habitat layer",
      "TITLE": "the habitat layer's title"
    },
    "STEEP_DEG": 50.0,
    "SMOOTH_M": 1.5,
    "MIN_AREA": 25.0,
    "NEAR_R": 500.0,
    "CLIFF_MIN_H": 10.0,
    "HIGH_FACE_M": 20.0,
    "FACING": [
      67.5,
      292.5
    ],
    "PREF_FACING": [
      112.5,
      247.5
    ],
    "VERTICAL_DEG": 70.0,
    "FACE_PAD_M": 3,
    "DROP_HALF_M": 5,
    "ISLET_MAX_HA": 20.0,
    "ISLET_MIN_M2": 200.0,
    "SEA_LEVEL_M": 0.6,
    "NEAR_BUILDING": 100.0,
    "NEAR_ROAD": 50.0,
    "EDGE_M": 25.0,
    "SIMPLIFY_CLIFF_M": 0.7,
    "SIMPLIFY_ISLET_M": 1.0,
    "COLOURS": {
      "quarry": "#7b1fa2",
      "islet": "#1e88e5",
      "3": "#bf360c",
      "2": "#f57c00",
      "1": "#ffb74d"
    },
    "FACE_COLOURS": {
      "S": "#bf360c",
      "SE": "#f57c00",
      "SW": "#f57c00",
      "E": "#ffcc80",
      "W": "#ffcc80"
    },
    "LEGEND": [
      [
        "#bf360c",
        "cliff faces S"
      ],
      [
        "#f57c00",
        "SE / SW"
      ],
      [
        "#ffcc80",
        "E / W"
      ],
      [
        "#7b1fa2",
        "quarry"
      ],
      [
        "#1e88e5",
        "islet"
      ]
    ],
    "TITLE": "Nesting habitat (cliffs, quarries, islets)"
  }; /* end rules.json */

  var fr = Math.fround, DEG32 = 57.2957763671875;          // float32(180 / pi), as numpy's degrees on float32

  // ---- scipy.ndimage on a w x h grid (row-major, row 0 = north) --------------------------------------------

  // gaussian_filter(sigma): separable, truncate 4 sigma, mode 'reflect'; one float32 rounding per pass as scipy
  function gaussianFilter(src, n, sigma) {
    var lw = Math.floor(4 * sigma + 0.5), w = new Float64Array(lw + 1), q = -0.5 / (sigma * sigma), s = 0, j;
    for (j = 0; j <= lw; j++) { w[j] = Math.exp(q * (j * j)); s += (j ? 2 : 1) * w[j]; }
    for (j = 0; j <= lw; j++) w[j] /= s;
    var line = new Float64Array(n + 2 * lw), tmp = new Float32Array(n * n), out = new Float32Array(n * n);
    function pass(a, b, step, base) {                       // one line: a[base + i*step], i = 0..n-1
      var i, t;
      for (i = 0; i < n; i++) line[lw + i] = a[base + i * step];
      for (j = 1; j <= lw; j++) { line[lw - j] = line[lw + j - 1]; line[lw + n - 1 + j] = line[lw + n - j]; }
      for (i = 0; i < n; i++) {
        t = line[lw + i] * w[0];
        for (j = lw; j >= 1; j--) t += (line[lw + i - j] + line[lw + i + j]) * w[j];
        b[base + i * step] = t;
      }
    }
    var k;
    for (k = 0; k < n; k++) pass(src, tmp, n, k);           // axis 0 (down the columns)
    for (k = 0; k < n; k++) pass(tmp, out, 1, k * n);       // axis 1 (along the rows)
    return out;
  }

  // np.gradient(f, d) on float32: gy = d/d(row) (southward), gx = d/d(col) (eastward); one-sided at the edges
  function gradient(f, n, d) {
    var gy = new Float32Array(n * n), gx = new Float32Array(n * n), d1 = fr(d), d2 = fr(2 * d), i, j, k;
    for (i = 0; i < n; i++) for (j = 0; j < n; j++) {
      k = i * n + j;
      gy[k] = i === 0 ? fr(f[k + n] - f[k]) / d1 : i === n - 1 ? fr(f[k] - f[k - n]) / d1 : fr(f[k + n] - f[k - n]) / d2;
      gx[k] = j === 0 ? fr(f[k + 1] - f[k]) / d1 : j === n - 1 ? fr(f[k] - f[k - 1]) / d1 : fr(f[k + 1] - f[k - 1]) / d2;
    }
    return { gy: gy, gx: gx };
  }

  // binary_dilation / binary_erosion with the default cross element, border_value 0, `it` iterations
  function dilate(m, w, h, it) {
    var a = m, b, x, y, k, t;
    for (t = 0; t < it; t++) {
      b = new Uint8Array(w * h);
      for (y = 0; y < h; y++) for (x = 0; x < w; x++) {
        k = y * w + x;
        b[k] = (a[k] || (x > 0 && a[k - 1]) || (x < w - 1 && a[k + 1]) || (y > 0 && a[k - w]) || (y < h - 1 && a[k + w])) ? 1 : 0;
      }
      a = b;
    }
    return a === m ? new Uint8Array(m) : a;
  }
  function erode(m, w, h, it) {
    var a = m, b, x, y, k, t;
    for (t = 0; t < it; t++) {
      b = new Uint8Array(w * h);
      for (y = 1; y < h - 1; y++) for (x = 1; x < w - 1; x++) {
        k = y * w + x;
        b[k] = (a[k] && a[k - 1] && a[k + 1] && a[k - w] && a[k + w]) ? 1 : 0;
      }
      a = b;
    }
    return a === m ? new Uint8Array(m) : a;
  }
  function closing(m, w, h, it) { return erode(dilate(m, w, h, it), w, h, it); }   // binary_closing
  function opening(m, w, h, it) { return dilate(erode(m, w, h, it), w, h, it); }   // binary_opening

  // ndimage.label, 4-connectivity; labels 1.. in order of first appearance (row-major)
  function label4(m, w, h) {
    var N = w * h, lab = new Int32Array(N), parent = new Int32Array((N >> 1) + 2), cur = 0, x, y, k, up, left, ru, rl;
    function find(a) { while (parent[a] !== a) { parent[a] = parent[parent[a]]; a = parent[a]; } return a; }
    for (y = 0; y < h; y++) for (x = 0; x < w; x++) {
      k = y * w + x;
      if (!m[k]) continue;
      up = y ? lab[k - w] : 0; left = x ? lab[k - 1] : 0;
      if (!up && !left) { lab[k] = ++cur; parent[cur] = cur; }
      else if (up && left) {
        ru = find(up); rl = find(left);
        if (ru < rl) { parent[rl] = ru; lab[k] = ru; } else { parent[ru] = rl; lab[k] = rl; }
      } else lab[k] = up || left;
    }
    var map = new Int32Array(cur + 1), count = 0, r;
    for (k = 0; k < N; k++) if (lab[k]) { r = find(lab[k]); if (!map[r]) map[r] = ++count; lab[k] = map[r]; }
    return { lab: lab, count: count };
  }

  // maximum_filter / minimum_filter of size 2*half+1 (mode 'reflect' == the window clipped at the border)
  function extremeFilter(src, w, h, half, isMax) {
    var tmp = new Float64Array(w * h), out = new Float64Array(w * h), x, y, k, j, a, b, v, e;
    for (y = 0; y < h; y++) for (x = 0; x < w; x++) {             // along the rows
      a = Math.max(0, x - half); b = Math.min(w - 1, x + half); e = src[y * w + a];
      for (j = a + 1; j <= b; j++) { v = src[y * w + j]; if (isMax ? v > e : v < e) e = v; }
      tmp[y * w + x] = e;
    }
    for (y = 0; y < h; y++) for (x = 0; x < w; x++) {             // down the columns
      a = Math.max(0, y - half); b = Math.min(h - 1, y + half); e = tmp[a * w + x];
      for (j = a + 1; j <= b; j++) { v = tmp[j * w + x]; if (isMax ? v > e : v < e) e = v; }
      out[y * w + x] = e;
    }
    return out;
  }
  function maxFilter(s, w, h, half) { return extremeFilter(s, w, h, half, true); }
  function minFilter(s, w, h, half) { return extremeFilter(s, w, h, half, false); }

  // distance_transform_edt: squared Euclidean distance of every pixel to the nearest pixel with src[k] != 0
  // (Felzenszwalb-Huttenlocher, exact)
  function edtSq(src, w, h) {
    var INF = Infinity, g = new Float64Array(w * h), out = new Float64Array(w * h), x, y, k, d;
    for (x = 0; x < w; x++) {                                     // 1-D along each column: |dy|, then squared
      d = INF;
      for (y = 0; y < h; y++) { k = y * w + x; d = src[k] ? 0 : d + 1; g[k] = d; }
      d = INF;
      for (y = h - 1; y >= 0; y--) { k = y * w + x; d = src[k] ? 0 : d + 1; if (d < g[k]) g[k] = d; g[k] *= g[k]; }
    }
    var v = new Int32Array(w), z = new Float64Array(w + 1), f = new Float64Array(w), q, s, t;
    for (y = 0; y < h; y++) {                                     // lower envelope of parabolas along each row
      for (x = 0; x < w; x++) f[x] = g[y * w + x];
      for (q = 0; q < w && f[q] === INF; q++) {}
      if (q === w) { for (x = 0; x < w; x++) out[y * w + x] = INF; continue; }
      t = 0; v[0] = q; z[0] = -INF; z[1] = INF;
      for (q++; q < w; q++) {
        if (f[q] === INF) continue;
        for (;;) {
          s = ((f[q] + q * q) - (f[v[t]] + v[t] * v[t])) / (2 * q - 2 * v[t]);
          if (s <= z[t]) t--; else break;
        }
        t++; v[t] = q; z[t] = s; z[t + 1] = INF;
      }
      t = 0;
      for (x = 0; x < w; x++) { while (z[t + 1] < x) t++; out[y * w + x] = (x - v[t]) * (x - v[t]) + f[v[t]]; }
    }
    return out;
  }

  // rasterio.features.shapes with 4-connectivity: one outer ring per 4-connected component (pixel-corner
  // coordinates col/row, clockwise on screen, from the top-left corner of the component's first pixel) + its
  // pixel count. Where a component touches itself diagonally the ring stays outside (the bay becomes a hole,
  // as GDAL's polygonize does); a diagonal pixel of ANOTHER component is not connected.
  function outline(m, w, h) {
    var L = label4(m, w, h), lab = L.lab, cnt = new Int32Array(L.count + 1), start = new Int32Array(L.count + 1), k, cur;
    for (k = 0; k < w * h; k++) if (lab[k]) { if (!cnt[lab[k]]) start[lab[k]] = k; cnt[lab[k]]++; }
    function inside(x, y) { return x >= 0 && y >= 0 && x < w && y < h && lab[y * w + x] === cur; }
    var DX = [1, 0, -1, 0], DY = [0, 1, 0, -1];                  // E S W N, y down; the inside is on the right
    function ar(vx, vy, d) { return d === 0 ? inside(vx, vy) : d === 1 ? inside(vx - 1, vy) : d === 2 ? inside(vx - 1, vy - 1) : inside(vx, vy - 1); }
    function al(vx, vy, d) { return d === 0 ? inside(vx, vy - 1) : d === 1 ? inside(vx, vy) : d === 2 ? inside(vx - 1, vy) : inside(vx - 1, vy - 1); }
    var out = [], sx, sy, vx, vy, d, nd, ring, guard;
    for (cur = 1; cur <= L.count; cur++) {
      k = start[cur]; sx = k % w; sy = (k - sx) / w; vx = sx; vy = sy; d = 0; ring = [[sx, sy]]; guard = 4 * w * h + 8;
      for (;;) {
        vx += DX[d]; vy += DY[d];
        // ahead-left inside: turn left; else ahead-right inside: straight; else turn right
        nd = al(vx, vy, d) ? (d + 3) & 3 : (ar(vx, vy, d) ? d : (d + 1) & 3);
        if (vx === sx && vy === sy && nd === 0) break;
        if (nd !== d) ring.push([vx, vy]);
        d = nd;
        if (--guard < 0) throw new Error('outline: open ring');
      }
      ring.push([sx, sy]);
      out.push({ ring: ring, count: cnt[cur] });
    }
    return out;
  }

  // ---- shapely bits ---------------------------------------------------------------------------------------

  function cross(o, a, b) { return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); }
  function convexHull(pts) {                                      // monotone chain, counter-clockwise, open
    var p = pts.slice().sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; }), lo = [], up = [], i;
    for (i = 0; i < p.length; i++) { while (lo.length >= 2 && cross(lo[lo.length - 2], lo[lo.length - 1], p[i]) <= 0) lo.pop(); lo.push(p[i]); }
    for (i = p.length - 1; i >= 0; i--) { while (up.length >= 2 && cross(up[up.length - 2], up[up.length - 1], p[i]) <= 0) up.pop(); up.push(p[i]); }
    lo.pop(); up.pop();
    return lo.concat(up);
  }
  function ringArea(r) {                                          // shoelace, unsigned; r open or closed
    var a = 0, i, j, m = r.length;
    for (i = 0; i < m; i++) { j = (i + 1) % m; a += r[i][0] * r[j][1] - r[j][0] * r[i][1]; }
    return Math.abs(a) / 2;
  }
  // minimum_rotated_rectangle (rotating calipers on the hull): long side L, short side W, long side's direction
  function minRotRect(hull) {
    var best = null, m = hull.length, i, j, ux, uy, len, lo1, hi1, lo2, hi2, p1, p2, area;
    if (m < 3) {
      ux = m === 2 ? hull[1][0] - hull[0][0] : 0; uy = m === 2 ? hull[1][1] - hull[0][1] : 0;
      return { L: Math.hypot(ux, uy), W: 0, ax: ux, ay: uy };
    }
    for (i = 0; i < m; i++) {
      j = (i + 1) % m; ux = hull[j][0] - hull[i][0]; uy = hull[j][1] - hull[i][1]; len = Math.hypot(ux, uy);
      if (!len) continue;
      ux /= len; uy /= len; lo1 = lo2 = Infinity; hi1 = hi2 = -Infinity;
      for (var k = 0; k < m; k++) {
        p1 = hull[k][0] * ux + hull[k][1] * uy; p2 = -hull[k][0] * uy + hull[k][1] * ux;
        if (p1 < lo1) lo1 = p1; if (p1 > hi1) hi1 = p1; if (p2 < lo2) lo2 = p2; if (p2 > hi2) hi2 = p2;
      }
      area = (hi1 - lo1) * (hi2 - lo2);
      if (!best || area < best.area) best = { area: area, e1: hi1 - lo1, e2: hi2 - lo2, ux: ux, uy: uy };
    }
    return best.e1 >= best.e2 ? { L: best.e1, W: best.e2, ax: best.ux, ay: best.uy } : { L: best.e2, W: best.e1, ax: -best.uy, ay: best.ux };
  }
  // simplify(tolerance): Douglas-Peucker on a closed ring, the start vertex kept
  function simplify(ring, tol) {
    var keep = new Uint8Array(ring.length), stack = [[0, ring.length - 1]], seg, a, b, i, dmax, imax, d;
    keep[0] = keep[ring.length - 1] = 1;
    while (stack.length) {
      seg = stack.pop(); a = seg[0]; b = seg[1]; dmax = -1; imax = -1;
      for (i = a + 1; i < b; i++) { d = segDist(ring[i], ring[a], ring[b]); if (d > dmax) { dmax = d; imax = i; } }
      if (dmax > tol) { keep[imax] = 1; stack.push([a, imax]); stack.push([imax, b]); }
    }
    var out = [];
    for (i = 0; i < ring.length; i++) if (keep[i]) out.push(ring[i]);
    return out;
  }
  function segDist(p, a, b) {
    var dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy, t = L2 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)) : 0;
    return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
  }
  function pointInRing(x, y, r) {                                 // even-odd rule
    var inside = false, i, j, m = r.length;
    for (i = 0, j = m - 1; i < m; j = i++)
      if ((r[i][1] > y) !== (r[j][1] > y) && x < (r[j][0] - r[i][0]) * (y - r[i][1]) / (r[j][1] - r[i][1]) + r[i][0]) inside = !inside;
    return inside;
  }
  function nearest(pts, x, y) {                                   // cKDTree.query: the distance to the nearest point
    var best = Infinity, i, d;
    if (!pts) return best;
    for (i = 0; i < pts.length; i++) { d = Math.hypot(pts[i][0] - x, pts[i][1] - y); if (d < best) best = d; }
    return best;
  }

  // ---- text, as Python's "%.0f" / "%.1f" (ties to even on exact halves) ------------------------------------

  function pyFixed(v, dec) {
    var s = Math.pow(10, dec), t = v * s, r = Math.round(t);
    if (Math.abs(t % 1) === 0.5) r = 2 * Math.round(t / 2);
    if (r === 0 && (v < 0 || (v === 0 && 1 / v < 0))) return (dec ? '-0.' + '0'.repeat(dec) : '-0');
    return (r / s).toFixed(dec);
  }
  function f0(v) { return pyFixed(v, 0); }
  function metres(v) { return isFinite(v) ? f0(v) + ' m' : 'unknown (no N250)'; }   // _m
  function aspectName(deg) { return ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.floor(((deg + 22.5) % 360) / 45)]; }
  function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

  // shape_of: length / width (minimum rotated rectangle), the long side's bearing, solidity, a shape word
  function shapeOf(ring, area) {
    var hull = convexHull(ring), rr = minRotRect(hull), L = rr.L, W = rr.W;
    var bearing = ((Math.atan2(rr.ax, rr.ay) * 180 / Math.PI) + 180) % 180;
    var solid = area / Math.max(ringArea(hull), 1e-9);
    var word = (L >= 3 * Math.max(W, 1) && solid >= 0.5) ? 'band' : (solid < 0.5 ? 'broken' : 'outcrop');
    var run = ['N\u2013S', 'NE\u2013SW', 'E\u2013W', 'SE\u2013NW'][Math.floor(((bearing + 22.5) % 180) / 45)];
    return { length: L, width: W, runs: run, solidity: solid, shape: word };
  }

  // describe: (name, description) of one habitat area, in plain words - the same text as the Python
  function describe(pr, R) {
    if (pr.kind === 'islet') {
      var ha = pyFixed(pr.area / 1e4, 1);
      return { name: 'islet ' + ha + ' ha (ground nests)',
               desc: 'Small island, ' + ha + ' ha, no building on it: cliff-nesters nest on the ground on such islets.' };
    }
    var fit = pr.score >= 3 ? 'good' : pr.score === 2 ? 'fair' : 'poor';
    var shapeW = { band: 'a cliff band (wall)', outcrop: 'a compact rock outcrop', broken: 'broken, scattered steep ground' }[pr.shape];
    var name = pr.kind + ' ' + f0(pr.height) + ' m drop, ' + pr.shape + ' ' + f0(pr.length) + ' m long, faces ' + pr.aspect + ' (' + fit + ')';
    var desc = capitalize(pr.kind) + ': ' + shapeW + ', ' + f0(pr.length) + ' \u00d7 ' + f0(pr.width) + ' m, runs ' + pr.runs + ', faces ' + pr.aspect +
      '. Drop ' + f0(pr.height) + ' m \u2014 top ' + f0(pr.top) + ' m, foot ' + f0(pr.foot) + ' m above sea level; ' +
      'the sharpest step is ' + f0(pr.drop10) + ' m within ' + f0(2 * R.DROP_HALF_M) + ' m, ' + f0(100 * pr.vertical) +
      ' % of the face is near-vertical (\u2265 ' + f0(R.VERTICAL_DEG) + '\u00b0), steepest ' + f0(pr.max_deg) + '\u00b0. ' +
      'Nearest building ' + metres(pr.d_building) + ', road ' + metres(pr.d_road) + '. Fit: ' + fit + ' (' +
      (pr.pref ? 'faces the sun' : 'not S-facing') + ', ' + (pr.height >= R.HIGH_FACE_M ? 'high face' : 'low face') + ', ' +
      ((pr.d_building < R.NEAR_BUILDING || pr.d_road < R.NEAR_ROAD) ? 'close to people' : 'away from people') + ').';
    return { name: name, desc: desc };
  }
  function colourOf(pr, R) {                                      // as viz3d.py: facing for cliffs, kind otherwise
    if (pr.kind !== 'cliff') return R.COLOURS[pr.kind];
    return R.FACE_COLOURS[pr.aspect] || R.COLOURS[String(Math.max(1, Math.min(pr.score, 3)))];
  }

  // ---- the rules ------------------------------------------------------------------------------------------

  function compute(h, n, c, opts) {
    var R = Habitat.rules, N = n * n, half = n * c / 2, i, j, k, v;
    opts = opts || {}; c = c || 1;
    var NEAR_R = opts.R || R.NEAR_R, X = opts.X || 0, Y = opts.Y || 0, people = opts.people || null;
    function rel(pts) { return pts ? pts.map(function (p) { return [p[0] - X, p[1] - Y]; }) : null; }
    var buildings = people && people.buildings && people.buildings.length ? rel(people.buildings) : null;
    var roads = people && people.roads && people.roads.length ? rel(people.roads) : null;
    var quarries = people && people.quarries ? people.quarries.map(rel) : [];
    var px = function (m) { return Math.max(1, Math.round(m / c)); };   // metres -> pixels (filter sizes)
    var xOf = function (col) { return (col + 0.5) * c - half; }, yOf = function (row) { return half - (row + 0.5) * c; };

    // -- viz3d.py: smoothed model, slope (float32, NaN near no-data), facing
    var bad = new Uint8Array(N), sum = 0, cnt = 0;
    for (k = 0; k < N; k++) { if (h[k] !== h[k]) bad[k] = 1; else { sum += h[k]; cnt++; } }
    var mean = fr(cnt ? sum / cnt : 0), filled = new Float32Array(N);
    for (k = 0; k < N; k++) filled[k] = bad[k] ? mean : h[k];
    var hs = gaussianFilter(filled, n, R.SMOOTH_M / c), g = gradient(hs, n, c), gy = g.gy, gx = g.gx;
    var slope = new Float32Array(N), aspect = new Float64Array(N), nearBad = dilate(bad, n, n, px(3));
    for (k = 0; k < N; k++) {
      slope[k] = nearBad[k] ? NaN : fr(fr(Math.atan(fr(Math.hypot(gx[k], gy[k])))) * DEG32);
      aspect[k] = (Math.atan2(-gx[k], gy[k]) * 180 / Math.PI + 360) % 360;
    }
    hs = gy = gx = null;

    // -- edge_band: within EDGE_M of the square's border or of no-data
    var W2 = n + 2, pad = new Uint8Array(W2 * W2), epx = Math.ceil(R.EDGE_M / c);
    for (k = 0; k < W2 * W2; k++) pad[k] = 1;
    for (i = 0; i < n; i++) for (j = 0; j < n; j++) pad[(i + 1) * W2 + j + 1] = bad[i * n + j];
    var dist = edtSq(pad, W2, W2), band = new Uint8Array(N);
    for (i = 0; i < n; i++) for (j = 0; j < n; j++) band[i * n + j] = dist[(i + 1) * W2 + j + 1] <= epx * epx ? 1 : 0;
    pad = dist = null;

    // -- habitat(): steep areas, which are nesting cliffs
    var steep = new Uint8Array(N);
    for (k = 0; k < N; k++) steep[k] = slope[k] >= R.STEEP_DEG ? 1 : 0;                // nan_to_num: NaN -> 0
    steep = closing(steep, n, n, 1);
    for (k = 0; k < N; k++) if (band[k]) steep[k] = 0;
    var LB = label4(steep, n, n), lab = LB.lab, nl = LB.count;
    var isCliff = new Uint8Array(nl + 1), isQuarry = new Uint8Array(nl + 1);
    if (nl) {
      var labF = new Float64Array(lab), big = maxFilter(labF, n, n, px(R.FACE_PAD_M));   // grey_dilation: the face + its foot and top
      var dropAll = maxFilter(filled, n, n, px(R.DROP_HALF_M)), dropMin = minFilter(filled, n, n, px(R.DROP_HALF_M));
      var hmax = new Float64Array(nl + 1).fill(-1e4), hmin = new Float64Array(nl + 1).fill(1e4);
      var aS = new Float64Array(nl + 1), aC = new Float64Array(nl + 1), rSum = new Float64Array(nl + 1), cSum = new Float64Array(nl + 1), cN = new Float64Array(nl + 1);
      for (k = 0; k < N; k++) {
        v = big[k];
        if (v) {                                                                        // nan_to_num(h, -1e4 / 1e4) over the dilated face
          if ((bad[k] ? -1e4 : h[k]) > hmax[v]) hmax[v] = bad[k] ? -1e4 : h[k];
          if ((bad[k] ? 1e4 : h[k]) < hmin[v]) hmin[v] = bad[k] ? 1e4 : h[k];
        }
        v = lab[k];
        if (v) {
          var a = aspect[k] * Math.PI / 180;
          aS[v] += Math.sin(a); aC[v] += Math.cos(a); rSum[v] += (k - k % n) / n; cSum[v] += k % n; cN[v]++;
        }
      }
      labF = big = dropAll = dropMin = null;
      for (v = 1; v <= nl; v++) {
        var ht = hmax[v] - hmin[v], cx = xOf(cSum[v] / cN[v]), cy = yOf(rSum[v] / cN[v]);      // center_of_mass
        var quarry = false;
        for (i = 0; i < quarries.length && !quarry; i++) quarry = pointInRing(cx, cy, quarries[i]);
        if (ht < R.CLIFF_MIN_H && !quarry) continue;
        var asp = (Math.atan2(aS[v], aC[v]) * 180 / Math.PI + 360) % 360;
        if (!(R.FACING[0] <= asp && asp <= R.FACING[1])) continue;                  // N / NE / NW faces are not nesting cliffs here
        isCliff[v] = 1; isQuarry[v] = quarry ? 1 : 0;
      }
    }

    // -- islets: land patches not touching the square's edge. The model fills the SEA with ~0 m; lakes lie
    //    at their own height, so sea = ground at or below SEA_LEVEL_M
    var sea = new Uint8Array(N);
    for (k = 0; k < N; k++) sea[k] = (bad[k] || h[k] <= R.SEA_LEVEL_M) ? 1 : 0;
    sea = opening(sea, n, n, 2);                                   // a low rock or a jetty is not the sea
    var land = new Uint8Array(N);
    for (k = 0; k < N; k++) land[k] = sea[k] ? 0 : 1;
    var IL = label4(land, n, n), il = IL.lab, ni = IL.count;
    var onEdge = new Uint8Array(ni + 1), areaPx = new Float64Array(ni + 1), xS = new Float64Array(ni + 1), yS = new Float64Array(ni + 1);
    for (k = 0; k < N; k++) {
      v = il[k];
      if (!v) continue;
      i = (k - k % n) / n; j = k % n;
      areaPx[v]++; xS[v] += xOf(j); yS[v] += yOf(i);
      if (i === 0 || j === 0 || i === n - 1 || j === n - 1 || band[k]) onEdge[v] = 1;
    }
    var isIslet = new Uint8Array(ni + 1), islet = new Uint8Array(N);
    for (v = 1; v <= ni; v++) {
      var am2 = areaPx[v] * c * c;
      if (onEdge[v] || am2 > R.ISLET_MAX_HA * 1e4 || am2 < R.ISLET_MIN_M2) continue;
      if (buildings && nearest(buildings, xS[v] / areaPx[v], yS[v] / areaPx[v]) <= Math.sqrt(am2 / Math.PI) + 20) continue;   // a building on it
      isIslet[v] = 1;
    }
    for (k = 0; k < N; k++) if (isIslet[il[k]]) islet[k] = 1;
    sea = land = il = null;

    // -- near(): within NEAR_R of the centre - the steepest pixel on a nesting cliff, the areas
    var inR = new Uint8Array(N), oncliff = new Uint8Array(N), bestK = -1, bestS = -Infinity, anyK = -1, anyS = -Infinity, xr, yr;
    for (i = 0; i < n; i++) for (j = 0; j < n; j++) {
      k = i * n + j; xr = xOf(j); yr = yOf(i);
      if (Math.hypot(xr, yr) > NEAR_R || band[k]) continue;       // never the steepest pixel at the data's edge
      inR[k] = 1;
      if (isCliff[lab[k]]) { oncliff[k] = 1; if (slope[k] > bestS) { bestS = slope[k]; bestK = k; } }
      if (slope[k] > anyS) { anyS = slope[k]; anyK = k; }
    }
    if (bestK < 0) { bestK = anyK; bestS = anyS; }
    var best = null;
    if (bestK >= 0) {
      xr = xOf(bestK % n); yr = yOf((bestK - bestK % n) / n);
      best = { x: xr, y: yr, slope: bestS, dist: Math.hypot(xr, yr) };
    }
    var areas = [], minPix = R.MIN_AREA / (c * c);
    // bounding boxes of each cliff's pixels inside the circle (find_objects)
    var r0 = new Int32Array(nl + 1).fill(n), r1 = new Int32Array(nl + 1).fill(-1), c0 = new Int32Array(nl + 1).fill(n), c1 = new Int32Array(nl + 1).fill(-1);
    for (k = 0; k < N; k++) if (oncliff[k]) {
      v = lab[k]; i = (k - k % n) / n; j = k % n;
      if (i < r0[v]) r0[v] = i; if (i > r1[v]) r1[v] = i; if (j < c0[v]) c0[v] = j; if (j > c1[v]) c1[v] = j;
    }
    // Each area is described by ITS OWN pixels inside the circle (a mountainside of connected steep ground
    // would otherwise be one "cliff" with a 1 000 m drop)
    for (v = 1; v <= nl; v++) {
      if (r1[v] < 0) continue;
      var R0 = Math.max(0, r0[v] - 4), R1 = Math.min(n, r1[v] + 1 + 4), C0 = Math.max(0, c0[v] - 4), C1 = Math.min(n, c1[v] + 1 + 4);
      var w = C1 - C0, hh = R1 - R0, m = new Uint8Array(w * hh), mc = 0, hsub = new Float64Array(w * hh), ssum = 0, scnt = 0;
      for (i = 0; i < hh; i++) for (j = 0; j < w; j++) {
        k = (R0 + i) * n + C0 + j;
        if (oncliff[k] && lab[k] === v) { m[i * w + j] = 1; mc++; }
        hsub[i * w + j] = bad[k] ? NaN : h[k];
        if (!bad[k]) { ssum += h[k]; scnt++; }
      }
      if (mc < minPix) continue;
      var dil = dilate(m, w, hh, px(R.FACE_PAD_M)), top = -Infinity, foot = Infinity;
      for (k = 0; k < w * hh; k++) if (dil[k] && hsub[k] === hsub[k]) { if (hsub[k] > top) top = hsub[k]; if (hsub[k] < foot) foot = hsub[k]; }
      if (top - foot < R.CLIFF_MIN_H && !isQuarry[v]) continue;    // this part of the face is too low
      var hf = new Float64Array(w * hh), smean = scnt ? ssum / scnt : 0;
      for (k = 0; k < w * hh; k++) hf[k] = hsub[k] === hsub[k] ? hsub[k] : smean;
      var mx = maxFilter(hf, w, hh, px(R.DROP_HALF_M)), mn = minFilter(hf, w, hh, px(R.DROP_HALF_M));
      var drop10 = -Infinity, sS = 0, sC = 0, maxDeg = -Infinity, nVert = 0, rS = 0, cS = 0;
      for (i = 0; i < hh; i++) for (j = 0; j < w; j++) {
        k = i * w + j;
        if (!m[k]) continue;
        if (mx[k] - mn[k] > drop10) drop10 = mx[k] - mn[k];
        var kk = (R0 + i) * n + C0 + j, a2 = aspect[kk] * Math.PI / 180, sl = slope[kk];
        sS += Math.sin(a2); sC += Math.cos(a2);
        if (sl > maxDeg) maxDeg = sl;
        if (sl >= R.VERTICAL_DEG) nVert++;
        rS += i; cS += j;
      }
      var asp2 = (Math.atan2(sS, sC) * 180 / Math.PI + 360) % 360;
      if (!(R.FACING[0] <= asp2 && asp2 <= R.FACING[1])) continue;  // this part of the face looks N / NE / NW
      var pref = R.PREF_FACING[0] <= asp2 && asp2 <= R.PREF_FACING[1];
      var ccx = xOf(C0 + cS / mc), ccy = yOf(R0 + rS / mc);
      var db = nearest(buildings, ccx, ccy), dr = nearest(roads, ccx, ccy);
      var height = top - foot, disturbed = db < R.NEAR_BUILDING || dr < R.NEAR_ROAD;
      var score = 1 + (pref ? 1 : 0) + (height >= R.HIGH_FACE_M ? 1 : 0) - (disturbed ? 1 : 0);
      var parts = outline(m, w, hh), p;
      for (p = 0; p < parts.length; p++) {
        var area = parts[p].count * c * c;
        if (area < R.MIN_AREA) continue;
        var ring = parts[p].ring.map(function (q) { return [(C0 + q[0]) * c - half, half - (R0 + q[1]) * c]; });
        var pr = { kind: isQuarry[v] ? 'quarry' : 'cliff', area: area, max_deg: maxDeg, height: height, aspect: aspectName(asp2), pref: pref,
                   d_building: db, d_road: dr, score: score, top: top, foot: foot, drop10: drop10, vertical: nVert / mc };
        Object.assign(pr, shapeOf(ring, area));
        var t = describe(pr, R);
        areas.push({ ring: simplify(ring, R.SIMPLIFY_CLIFF_M), kind: pr.kind, name: t.name, desc: t.desc, color: colourOf(pr, R), props: pr });
      }
    }
    var isl = new Uint8Array(N);
    for (k = 0; k < N; k++) isl[k] = islet[k] && inR[k] ? 1 : 0;
    var iparts = outline(isl, n, n);
    for (i = 0; i < iparts.length; i++) {
      var ia = iparts[i].count * c * c;
      if (ia < R.ISLET_MIN_M2) continue;
      var iring = iparts[i].ring.map(function (q) { return [q[0] * c - half, half - q[1] * c]; });
      var ipr = { kind: 'islet', area: ia, score: 2 }, it = describe(ipr, R);
      areas.push({ ring: simplify(iring, R.SIMPLIFY_ISLET_M), kind: 'islet', name: it.name, desc: it.desc, color: colourOf(ipr, R), props: ipr });
    }
    return { best: best, areas: areas };
  }

  var Habitat = { rules: RULES, compute: compute };
  window.Habitat = Habitat;
})();
