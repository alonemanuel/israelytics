import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
from elections import haredi_share, merge_shares


def test_haredi_share_basic():
    assert haredi_share({"שס": 30, "ג": 20, "מחל": 50}, 100) == 0.5


def test_haredi_share_zero_when_no_haredi_parties():
    assert haredi_share({"מחל": 100, "פה": 50}, 150) == 0.0


def test_haredi_share_none_when_no_valid_votes():
    assert haredi_share({"שס": 10}, 0) is None


def test_haredi_share_only_counts_haredi_letters():
    # 'ל' (Yisrael Beiteinu) is right but NOT haredi
    assert haredi_share({"שס": 25, "ל": 75}, 100) == 0.25


def test_merge_fills_gaps_from_variants():
    assert merge_shares([[0.3, 0.4, None, None], [None, None, 0.5, 0.6]]) == [0.3, 0.4, 0.5, 0.6]


def test_merge_single_list_unchanged():
    assert merge_shares([[0.1, None, 0.2]]) == [0.1, None, 0.2]


def test_merge_keeps_none_where_no_variant_has_data():
    assert merge_shares([[None, 0.5], [None, None]]) == [None, 0.5]


def test_merge_averages_genuine_overlap():
    assert merge_shares([[0.4], [0.6]]) == [0.5]
