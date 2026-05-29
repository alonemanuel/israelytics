"""Shared reading of the Knesset election CSVs and the Haredi-share math.

Used by build_geo (for the per-city size weight) and build_haredi (for values).
The CSVs are per-locality, one column per party ballot-letter; files mix UTF-8
and Windows-1255 encodings and vary their headers slightly across elections.
"""

import csv
import os

# (election number, human label). Elections 19-25, 2013-2022.
ELECTIONS = [
    (19, "Jan 2013"), (20, "Mar 2015"), (21, "Apr 2019"), (22, "Sep 2019"),
    (23, "Mar 2020"), (24, "Mar 2021"), (25, "Nov 2022"),
]

# Non-party columns present in the CSVs.
FIXED = {"סמל ועדה", "שם ישוב", "סמל ישוב", "בזב", "מצביעים", "פסולים", "כשרים"}

# Pseudo-localities aggregating non-geographic votes (absentee / "double
# envelope") — never a real place.
EXCLUDE_SUBSTR = ("מעטפות",)

# Haredi (ultra-orthodox) party ballot letters — stable across elections 19-25.
# שס = Shas (Sephardi Haredi), ג = Yahadut HaTorah / UTJ (Ashkenazi Haredi).
HAREDI_LETTERS = {"שס", "ג"}


def is_aggregate(name):
    return any(sub in name for sub in EXCLUDE_SUBSTR)


def haredi_share(votes, valid):
    """Haredi votes (Shas + UTJ) as a fraction of all valid votes, or None if
    there are no valid votes. `votes` maps party-letter -> count."""
    if not valid:
        return None
    haredi = sum(votes.get(l, 0) for l in HAREDI_LETTERS)
    return haredi / valid


def merge_shares(share_lists):
    """Combine per-timestep value lists from spelling variants of one place.
    Per timestep, average the non-None values (usually exactly one)."""
    n = len(share_lists[0])
    out = []
    for i in range(n):
        vals = [sl[i] for sl in share_lists if sl[i] is not None]
        out.append(sum(vals) / len(vals) if vals else None)
    return out




def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _col(rowkeys, *contains):
    """Find the raw header key whose normalized text contains all fragments."""
    for k in rowkeys:
        kn = k.replace("﻿", "").strip()
        if all(frag in kn for frag in contains):
            return k
    return None


def _read_rows(sources_dir, election):
    path = os.path.join(sources_dir, f"{election}.csv")
    for enc in ("utf-8-sig", "cp1255"):
        try:
            with open(path, encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"could not decode {path}")


def read_localities(sources_dir, election):
    """Yield {'raw', 'votes', 'valid', 'voters', 'eligible'} per real locality
    in one election file (skips aggregate/empty rows)."""
    rows = _read_rows(sources_dir, election)
    keys = list(rows[0].keys())
    name_key = _col(keys, "שם", "ישוב")
    code_key = _col(keys, "סמל", "ישוב")
    voters_key = _col(keys, "מצביעים")
    valid_key = _col(keys, "כשרים")
    eligible_key = _col(keys, "בזב")
    party_keys = [k for k in keys if k.replace("﻿", "").strip() not in FIXED
                  and k.replace("﻿", "").strip()]

    for r in rows:
        raw = (r[name_key] or "").strip()
        if not raw or is_aggregate(raw):
            continue
        votes = {}
        for pk in party_keys:
            letter = pk.replace("﻿", "").strip()
            c = _to_int(r[pk])
            if c:
                votes[letter] = c
        valid = _to_int(r[valid_key]) if valid_key else sum(votes.values())
        yield {
            "raw": raw,
            "cbs_code": (r[code_key] or "").strip() if code_key else "",
            "votes": votes,
            "valid": valid,
            "voters": _to_int(r[voters_key]) if voters_key else 0,
            "eligible": _to_int(r[eligible_key]) if eligible_key else 0,
        }
