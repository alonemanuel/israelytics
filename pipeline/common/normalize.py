"""Canonicalize Israeli locality names so election, polygon, and coordinate
datasets join on the same key. This is the riskiest glue in the pipeline."""

import re

_APOSTROPHES = "'׳’‘`\"״"      # geresh + gershayim glyph variants
_PARENS = "()﴾﴿"                      # ( ) and ornate variants
_DASHES = "-־–—−"           # - ־ – — −


def normalize(name: str) -> str:
    if name is None:
        return ""
    s = name.replace("﻿", "")              # strip BOM

    # canonicalize geresh/apostrophe glyphs to a single form
    for ch in _APOSTROPHES:
        s = s.replace(ch, "'")

    # cut everything from the first parenthesis onward (handles "(שבט)",
    # truncated "(יישוב", and trailing qualifiers like "(גלעד)")
    cut = min((s.find(p) for p in _PARENS if p in s), default=-1)
    if cut != -1:
        s = s[:cut]

    # dashes act as separators
    for ch in _DASHES:
        s = s.replace(ch, " ")

    # drop the standalone "שבט" (tribe) qualifier used inconsistently
    s = re.sub(r"(?:^|\s)שבט(?=\s|$)", " ", s)

    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tight_key(name: str) -> str:
    """Stricter fallback key: normalize, then drop all spaces and geresh so
    CSV spellings ('אום אלפחם', 'מודיעיןמכביםרעות') match the hyphenated
    geo-dataset spellings ('אום אל-פחם', 'מודיעין-מכבים-רעות')."""
    s = normalize(name)
    return s.replace(" ", "").replace("'", "")
