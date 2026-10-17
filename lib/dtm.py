"""Kartverket's 1 m terrain model (NHM DTM, open data, CC BY 4.0) as 1 km tiles from the Geonorge WCS — only
the tiles a view needs, fetched once into <dtm1_tiles>/tiles/E<km>_N<km>.tif (EPSG:25833, deflate, nodata
−32767) and reused from there. One request at a time, with exponential backoff, to stay gentle on the free
service. Tiles Kartverket does not have (sea, abroad) stay missing; the viewer fills them and greys them out."""
import os, time, urllib.request, urllib.error
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from .config import CFG

WCS = ("https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=WCS&version=1.0.0&request=GetCoverage"
       "&coverage=NHM_DTM_25833&CRS=EPSG:25833&RESPONSE_CRS=EPSG:25833&FORMAT=GeoTIFF&BBOX={x0},{y0},{x1},{y1}&WIDTH=1000&HEIGHT=1000")
UA = "terrain3d (https://github.com/pcmoan70/3d_terrain)"


def tiles_for(X, Y, R):
    """Every 1 km tile (E km, N km) of the whole ±R SQUARE round (X, Y) — the block shows its corners, so a
    missing corner tile would leave a jump."""
    return [(e, n) for e in range(int((X - R) // 1000), int((X + R - 1e-6) // 1000) + 1)
            for n in range(int((Y - R) // 1000), int((Y + R - 1e-6) // 1000) + 1)]


def fetch_backoff(url, ok=lambda d: True, headers=None, timeout=60, cap=60, label=""):
    """GET url with exponential backoff: waits 1, 2, 4 … s between tries, the last wait `cap` s (~2 min in all).
    Retried: network errors, timeouts, HTTP 5xx and 429, and a reply `ok` rejects that is not a definite "no such
    data". Not retried (returns None at once): HTTP 4xx other than 429, and an OGC exception report (XML) — the
    service saying it has no data there (a sea tile), which no retry changes."""
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    waits = [w for w in (1, 2, 4, 8, 16, 32) if w < cap] + [cap]
    for k in range(len(waits) + 1):
        why = None
        try:
            d = urllib.request.urlopen(req, timeout=timeout).read()
            if ok(d): return d
            if d.lstrip()[:5] in (b"<?xml", b"<Serv", b"<ows:", b"<Exce"): return None   # the service: no data here
            why = "unexpected reply (%d bytes)" % len(d)
        except urllib.error.HTTPError as ex:
            if ex.code != 429 and 400 <= ex.code < 500: return None
            why = "HTTP %d" % ex.code
        except Exception as ex:
            why = str(ex)[:80]
        if k == len(waits): print("  gave up", label or url, "—", why, flush=True); return None
        print("  retry in %d s" % waits[k], label or url, "—", why, flush=True)
        time.sleep(waits[k])


def fetch_tiles(X, Y, R):
    """The tile files of the ±R square round (X, Y) (EPSG:25833), missing ones fetched; the ones that exist."""
    td = os.path.join(CFG["dtm1_tiles"], "tiles"); os.makedirs(td, exist_ok=True); got = []
    for e, n in tiles_for(X, Y, R):
        fn = os.path.join(td, f"E{e}_N{n}.tif"); got.append(fn)
        if os.path.exists(fn): continue
        data = fetch_backoff(WCS.format(x0=e * 1000, y0=n * 1000, x1=(e + 1) * 1000, y1=(n + 1) * 1000),
                             ok=lambda d: d[:2] in (b"II", b"MM"), timeout=120, label=f"E{e}_N{n}")
        if data is None:   # no data there (sea, abroad) or the service keeps failing: the tile stays missing
            print("  NO TILE", f"E{e}_N{n}"); got.pop(); continue
        with MemoryFile(data) as mf, mf.open() as src:
            arr = src.read(1); prof = src.profile
        ok = np.isfinite(arr) & (arr > -1000)
        prof.update(driver="GTiff", compress="deflate", predictor=3, tiled=True, blockxsize=256, blockysize=256, nodata=-32767)
        with rasterio.open(fn, "w", **prof) as d_: d_.write(np.where(ok, arr, -32767).astype(np.float32), 1)
        print("  fetched", os.path.basename(fn))
    return got
