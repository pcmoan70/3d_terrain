"""Where terrain3d keeps and finds its data — config.toml, every key optional (see config.example.toml):
the first of $TERRAIN3D_CONFIG, ./config.toml next to the scripts, ~/.config/terrain3d/config.toml."""
import os, tomllib

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULTS = {"dtm1_tiles": "~/.cache/terrain3d/dtm1",   # the 1 km DTM tiles, fetched once: <dtm1_tiles>/tiles/E<km>_N<km>.tif
            "map_tiles": "~/.cache/terrain3d/maps",    # the base-map tiles draped onto a view
            "n250": ""}                                # Kartverket N250 (FGDB): buildings, roads, quarries for the habitat rules; "" = without


def load():
    for p in (os.environ.get("TERRAIN3D_CONFIG"), os.path.join(D, "config.toml"), os.path.expanduser("~/.config/terrain3d/config.toml")):
        if p and os.path.exists(p):
            c = dict(DEFAULTS); c.update(tomllib.load(open(p, "rb"))); c["file"] = p; break
    else:
        c = dict(DEFAULTS, file=None)
    return {k: os.path.expanduser(v) if isinstance(v, str) and v else v for k, v in c.items()}


CFG = load()
