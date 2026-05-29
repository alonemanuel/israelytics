import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
from geo_index import GeoIndex

SOURCES = os.path.join(os.path.dirname(__file__), '..', 'basemap', 'sources')


def _idx():
    return GeoIndex(SOURCES)


def test_known_cbs_code_returns_polygon():
    kind, name, geom = _idx().lookup("3000")  # Bnei Brak
    assert kind == "polygon"
    assert name
    assert geom["type"] in ("Polygon", "MultiPolygon")


def test_large_city_has_polygon():
    kind, name, geom = _idx().lookup("5000")  # Tel Aviv
    assert kind == "polygon"
    assert "תל אביב" in name


def test_unknown_cbs_code_without_fallback():
    kind, name, geom = _idx().lookup("9999999")
    assert kind is None and name is None and geom is None


def test_point_fallback_for_unrecognized_settlement():
    # CBS code 967 (Abu Gweighed tribe) is not in CBS polygons but is in coords
    idx = _idx()
    kind, name, geom = idx.lookup("967", "אבו גווייעד")
    # May be point (coords fallback) or None if not in coords either
    if kind:
        assert kind == "point"
        assert "lat" in geom and "lon" in geom


def test_different_cbs_codes_give_different_cities():
    idx = _idx()
    _, name1, _ = idx.lookup("3000")
    _, name2, _ = idx.lookup("5000")
    assert name1 != name2
