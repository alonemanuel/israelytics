import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))
from normalize import normalize, tight_key


def test_plain_name_unchanged():
    assert normalize("אבו גוש") == "אבו גוש"


def test_strips_bom_and_whitespace():
    assert normalize("﻿  אבו גוש  ") == "אבו גוש"


def test_removes_balanced_parenthetical_suffix():
    assert normalize("אבו עבדון (שבט)") == "אבו עבדון"


def test_removes_unbalanced_open_parenthesis():
    assert normalize("אבו קרינאת (יישוב") == "אבו קרינאת"


def test_removes_trailing_shevet_word_without_parens():
    assert normalize("אבו גווייעד שבט") == normalize("אבו גווייעד (שבט")


def test_hyphen_becomes_space():
    assert normalize("אום אל-פחם") == "אום אל פחם"


def test_collapses_multiple_spaces():
    assert normalize("תל  אביב   יפו") == "תל אביב יפו"


def test_apostrophe_glyph_variants_match():
    assert normalize("ג'ת") == normalize("ג׳ת") == normalize("ג'ת")


def test_parenthetical_with_extra_content_removed():
    assert normalize("אבן יצחק (גלעד)") == "אבן יצחק"


def test_tight_key_matches_hyphen_vs_concatenated():
    assert tight_key("מודיעין-מכבים-רעות") == tight_key("מודיעיןמכביםרעות")


def test_tight_key_matches_spacing_variant():
    assert tight_key("אום אל-פחם") == tight_key("אום אלפחם")


def test_tight_key_ignores_geresh():
    assert tight_key("סח'נין") == tight_key("סחנין")


def test_tight_key_keeps_distinct_names_distinct():
    assert tight_key("תל אביב") != tight_key("חיפה")


def test_tight_key_ignores_gershayim():
    assert tight_key('בני עי"ש') == tight_key("בני עיש")
    assert tight_key('כפר חב"ד') == tight_key("כפר חבד")
