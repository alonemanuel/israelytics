import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
from elections import (haredi_share, merge_shares, read_localities, build_name_to_cbs,
                       ELECTIONS, SOURCES_DIR, BLOC, PARTIES, right_left_margin,
                       classified_share, top_parties)
from normalize import normalize

# The shared election-results source package (raw CSVs live here now).
SRC = SOURCES_DIR


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


def test_elections_include_17_and_18():
    nums = [n for n, _ in ELECTIONS]
    assert 17 in nums and 18 in nums


def test_read_18_aggregates_ballot_boxes_to_localities_with_cbs():
    locs = list(read_localities(SRC, 18))
    assert len(locs) > 800                      # ~1100 localities in 2009
    assert all(l["cbs_code"] for l in locs)     # 18th carries CBS codes
    codes = [l["cbs_code"] for l in locs]
    assert len(codes) == len(set(codes))        # one aggregated row per locality


def test_read_17_backfills_most_cbs_codes_from_names():
    locs = list(read_localities(SRC, 17))
    assert len(locs) > 800
    resolved = [l for l in locs if l["cbs_code"]]
    assert len(resolved) > 0.8 * len(locs)      # most 2006 names resolve to a code


def test_name_to_cbs_resolves_jerusalem():
    m = build_name_to_cbs(SRC)
    assert m.get(normalize("ירושלים"))


# --- right vs left margin ---------------------------------------------------

def test_margin_all_right_is_plus_one():
    # מחל=Likud (R), שס=Shas (R) in election 25
    assert right_left_margin({"מחל": 60, "שס": 40}, 25) == 1.0


def test_margin_all_left_is_minus_one():
    # פה=Yesh Atid (L), אמת=Labor (L) in election 25
    assert right_left_margin({"פה": 70, "אמת": 30}, 25) == -1.0


def test_margin_even_split_is_zero():
    assert right_left_margin({"מחל": 50, "פה": 50}, 25) == 0.0


def test_margin_ignores_unclassified_letters():
    # 'זzz' is not a real letter -> not in BLOC[25] -> excluded from both blocs,
    # so it must not move the margin (R vs L only).
    assert right_left_margin({"מחל": 50, "פה": 50, "zz": 999}, 25) == 0.0


def test_margin_none_when_no_classified_votes():
    assert right_left_margin({"zz": 100}, 25) is None


def test_margin_is_election_specific_for_reused_letters():
    # כן = Kadima (L/center) in 2006 but National Unity (L) in 2022 — both Left
    # here, but the table is keyed per election so the lookup must use the year.
    assert "כן" in BLOC[17] and "כן" in BLOC[25]
    # ב = Jewish Home (R) in 2009, Yamina (R) in 2021 — present, right, both years
    assert BLOC[18]["ב"] == "R" and BLOC[24]["ב"] == "R"


def test_arab_and_center_parties_count_as_left():
    # documented two-bloc rule: Arab (עם/ודעם) and center (פה) -> Left
    assert BLOC[25]["עם"] == "L"
    assert BLOC[24]["ודעם"] == "L"
    assert BLOC[25]["פה"] == "L"


def test_yisrael_beiteinu_is_right_every_election_it_ran_alone():
    # ל = Yisrael Beiteinu in every election from 2009 on (ran joint as מחל in 2013)
    for n in (18, 20, 21, 22, 23, 24, 25):
        assert BLOC[n]["ל"] == "R"


def test_classified_share_is_classified_over_valid():
    # 80 classified (50 R + 30 L) out of 100 valid -> 0.8
    assert classified_share({"מחל": 50, "פה": 30, "zz": 20}, 100, 25) == 0.8


def test_classified_share_zero_without_valid():
    assert classified_share({"מחל": 10}, 0, 25) == 0.0


def test_bloc_is_derived_from_parties_classified_letters_only():
    # BLOC should be exactly the PARTIES letters that carry a non-None bloc.
    for e, parties in PARTIES.items():
        expected = {ltr for ltr, (_, bloc) in parties.items() if bloc}
        assert set(BLOC[e]) == expected


# --- per-city "how they voted" breakdown ------------------------------------

def test_top_parties_names_and_shares():
    parts = top_parties({"מחל": 50, "פה": 30}, 100, 25)
    by_label = {p["labelHe"]: p for p in parts}
    assert by_label["הליכוד"]["value"] == 0.5
    assert by_label["הליכוד"]["tag"] == "R"
    assert by_label["יש עתיד"]["value"] == 0.3
    assert by_label["יש עתיד"]["tag"] == "L"


def test_top_parties_adds_other_row_for_remainder():
    # 80 named out of 100 valid -> an "אחר" row of 0.2
    parts = top_parties({"מחל": 50, "פה": 30}, 100, 25)
    other = [p for p in parts if p["labelHe"] == "אחר"]
    assert other and other[0]["value"] == 0.2
    assert "tag" not in other[0]


def test_top_parties_limits_to_n_plus_other():
    votes = {l: 10 for l in ("מחל", "פה", "שס", "אמת", "ג", "מרצ", "ל", "כן")}
    parts = top_parties(votes, 100, 25, n=6)
    # at most 6 named parties + 1 "אחר"
    assert len(parts) == 7
    assert parts[-1]["labelHe"] == "אחר"


def test_top_parties_unknown_letter_falls_back_to_letter_and_no_tag():
    parts = top_parties({"zz": 100}, 100, 25)
    assert parts[0]["labelHe"] == "zz"
    assert "tag" not in parts[0]


def test_top_parties_empty_without_valid():
    assert top_parties({"מחל": 10}, 0, 25) == []
