import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
from geo_index import GeoIndex

SOURCES = os.path.join(os.path.dirname(__file__), '..', 'sources')


def _idx():
    return GeoIndex(SOURCES)


def test_major_city_resolves_to_polygon():
    key, kind = _idx().resolve("בני ברק")
    assert kind == "polygon"
    assert key


def test_spelling_variants_resolve_to_same_key():
    idx = _idx()
    a, _ = idx.resolve("אום אל-פחם")
    b, _ = idx.resolve("אום אלפחם")
    assert a == b


def test_alias_resolves_renamed_city():
    # נוף הגליל (renamed 2019) -> נצרת עילית in the geo source, via aliases.csv
    key, kind = _idx().resolve("נוף הגליל")
    assert key is not None


def test_unknown_place_resolves_to_nothing():
    key, kind = _idx().resolve("עיר שלא קיימת בכלל")
    assert key is None and kind is None


def test_geometry_available_for_resolved_polygon():
    idx = _idx()
    key, kind = idx.resolve("ירושלים")
    geom = idx.geometry_for(key, kind)
    assert geom["type"] in ("Polygon", "MultiPolygon")
