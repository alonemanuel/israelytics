"""Single source of truth for the join key: the CBS locality code (סמל יישוב).

Loads per-locality polygon boundaries from the CBS statistical areas GeoJSON
(dissolved by SEMEL_YISHUV), keyed by CBS code. Falls back to coords.csv
point data for the ~30 unrecognized Bedouin settlements missing from the CBS
source.

The CBS source (localities.geojson) is derived from the CBS "Statistical Areas
with Demographic Data" geodatabase, dissolved by locality code and reprojected
to WGS84.
"""

import csv
import json
import os

from normalize import normalize

IL_BBOX = (34.0, 36.0, 29.3, 33.45)   # lon_min, lon_max, lat_min, lat_max


def _in_israel(lat, lon):
    lo1, lo2, la1, la2 = IL_BBOX
    return lo1 <= lon <= lo2 and la1 <= lat <= la2


class GeoIndex:
    def __init__(self, sources_dir):
        self._load_localities(sources_dir)
        self._load_coords(sources_dir)

    def _load_localities(self, sources_dir):
        path = os.path.join(sources_dir, "localities.geojson")
        with open(path, encoding="utf-8") as f:
            fc = json.load(f)
        self._poly = {}
        for feat in fc["features"]:
            code = feat["properties"]["cbs_code"]
            self._poly[code] = {
                "geometry": feat["geometry"],
                "name_he": feat["properties"]["name_he"],
            }

    def _load_coords(self, sources_dir):
        path = os.path.join(sources_dir, "coords.csv")
        self._coords = {}
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                name = r["City"].strip()
                if not name:
                    continue
                lat, lon = float(r["Latitude"]), float(r["Longitude"])
                if not _in_israel(lat, lon):
                    continue
                key = normalize(name)
                self._coords.setdefault(key, {"lat": lat, "lon": lon, "name": name})

    def lookup(self, cbs_code, raw_name=None):
        """Look up geometry for a CBS code. Returns (kind, name_he, geometry).

        Falls back to coords.csv point data if the CBS code isn't in the
        polygon source and raw_name is provided. Returns (None, None, None)
        if no geometry found at all."""
        code = str(cbs_code)
        if code in self._poly:
            p = self._poly[code]
            return "polygon", p["name_he"], p["geometry"]
        if raw_name:
            key = normalize(raw_name)
            if key in self._coords:
                c = self._coords[key]
                return "point", c["name"], {"lat": c["lat"], "lon": c["lon"]}
        return None, None, None
