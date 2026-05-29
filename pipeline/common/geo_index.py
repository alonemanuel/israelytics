"""Single source of truth for the join key.

Loads the polygon and coordinate geometry sources and resolves any Israeli
locality name to a canonical key + geometry. Every dataset builder resolves
names through here, so dataset city keys always line up with geo.json keys.

A polygon city's canonical key is the normalized MUN_HEB name; a point city's
canonical key is its tight_key (which collapses spelling variants). Aliases
(an editable CSV) rewrite known renames/spellings before matching.
"""

import csv
import json
import os

from normalize import normalize, tight_key

# Israel + West Bank + Golan bounding box. The coordinate source mis-geocodes
# some names that collide with foreign places (Hebron -> USA, Uman -> Ukraine);
# anything outside this box is rejected so it never lands on the map.
IL_BBOX = (34.0, 36.0, 29.3, 33.45)   # lon_min, lon_max, lat_min, lat_max


def _in_israel(lat, lon):
    lo1, lo2, la1, la2 = IL_BBOX
    return lo1 <= lon <= lo2 and la1 <= lat <= la2


class GeoIndex:
    def __init__(self, sources_dir):
        self._load_aliases(sources_dir)
        self._load_polygons(sources_dir)
        self._load_coords(sources_dir)

    def _load_aliases(self, sources_dir):
        path = os.path.join(sources_dir, "aliases.csv")
        self.aliases = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.aliases[tight_key(r["from"])] = tight_key(r["to"])

    def _load_polygons(self, sources_dir):
        path = os.path.join(sources_dir, "municipalities.geojson")
        with open(path, encoding="utf-8") as f:
            fc = json.load(f)
        self.poly_exact = {}     # normalized name -> canonical poly key
        self.poly_tight = {}     # tight key       -> canonical poly key
        self.poly_feature = {}   # canonical poly key -> GeoJSON feature
        self.poly_name = {}      # canonical poly key -> MUN_HEB display name
        for feat in fc["features"]:
            heb = feat["properties"].get("MUN_HEB", "")
            key = normalize(heb)
            if not key:
                continue
            self.poly_exact.setdefault(key, key)
            self.poly_tight.setdefault(tight_key(heb), key)
            self.poly_feature.setdefault(key, feat)
            self.poly_name.setdefault(key, heb)

    def _load_coords(self, sources_dir):
        path = os.path.join(sources_dir, "coords.csv")
        self.coord_exact = {}    # normalized name -> (lat, lon)
        self.coord_tight = {}    # tight key       -> (lat, lon)
        self.coord_name = {}     # tight key       -> City display name
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                key = normalize(r["City"])
                if not key:
                    continue
                lat, lon = float(r["Latitude"]), float(r["Longitude"])
                if not _in_israel(lat, lon):
                    continue
                self.coord_exact.setdefault(key, (lat, lon))
                tk = tight_key(r["City"])
                self.coord_tight.setdefault(tk, (lat, lon))
                self.coord_name.setdefault(tk, r["City"])

    def resolve(self, name):
        """Return (canonical_key, kind) where kind is 'polygon' or 'point', or
        (None, None) if the name matches no geometry."""
        key = normalize(name)
        tkey = self.aliases.get(tight_key(name), tight_key(name))
        poly_key = self.poly_exact.get(key) or self.poly_tight.get(tkey)
        if poly_key:
            return poly_key, "polygon"
        if key in self.coord_exact:
            return tight_key(name), "point"
        if tkey in self.coord_tight:
            return tkey, "point"
        return None, None

    def name_for(self, canonical_key, kind):
        if kind == "polygon":
            return self.poly_name.get(canonical_key, canonical_key)
        return self.coord_name.get(canonical_key, canonical_key)

    def geometry_for(self, canonical_key, kind):
        """For polygons returns the GeoJSON geometry; for points returns
        {'lat':, 'lon':}."""
        if kind == "polygon":
            return self.poly_feature[canonical_key]["geometry"]
        lat, lon = self.coord_tight[canonical_key]
        return {"lat": lat, "lon": lon}