"""Shared reading of the Knesset election CSVs and the Haredi-share math.

Used by build_geo (for the per-city size weight) and build_haredi (for values).
The CSVs are per-locality, one column per party ballot-letter; files mix UTF-8
and Windows-1255 encodings and vary their headers slightly across elections.
"""

import csv
import os

from normalize import normalize

# (election number, human label). Elections 17-25, 2006-2022.
ELECTIONS = [
    (17, "2006"), (18, "2009"), (19, "Jan 2013"), (20, "Mar 2015"),
    (21, "Apr 2019"), (22, "Sep 2019"), (23, "Mar 2020"), (24, "Mar 2021"),
    (25, "Nov 2022"),
]

# Per-election source file + format. Elections 19-25 are per-locality CSVs;
# 17 and 18 are per-ballot-box files (17 = legacy .xls with city names only,
# 18 = CSV that already carries the CBS code) that get aggregated up to locality.
_SPEC = {
    17: ("17-kalpiot.xls", "bb_xls"),
    18: ("18-kalpiot.csv", "bb_csv"),
    **{n: (f"{n}.csv", "loc_csv") for n in range(19, 26)},
}

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


def _read_csv_rows(path):
    for enc in ("utf-8-sig", "cp1255"):
        try:
            with open(path, encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"could not decode {path}")


def read_localities(sources_dir, election):
    """Yield per-locality {'raw','cbs_code','votes','valid','voters','eligible'}
    for one election, dispatching on its source format. Ballot-box sources are
    aggregated up to the locality. Skips aggregate/empty rows."""
    fname, fmt = _SPEC[election]
    path = os.path.join(sources_dir, fname)
    if fmt == "loc_csv":
        yield from _read_loc_csv(path)
    elif fmt == "bb_csv":
        yield from _read_bb_csv(path)
    elif fmt == "bb_xls":
        yield from _read_bb_xls(path, sources_dir)
    else:
        raise ValueError(f"unknown format {fmt}")


def _read_loc_csv(path):
    """Per-locality CSV (elections 19-25): one row per locality, has CBS code."""
    rows = _read_csv_rows(path)
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
            c = _to_int(r[pk])
            if c:
                votes[pk.replace("﻿", "").strip()] = c
        valid = _to_int(r[valid_key]) if valid_key else sum(votes.values())
        yield {
            "raw": raw,
            "cbs_code": (r[code_key] or "").strip() if code_key else "",
            "votes": votes,
            "valid": valid,
            "voters": _to_int(r[voters_key]) if voters_key else 0,
            "eligible": _to_int(r[eligible_key]) if eligible_key else 0,
        }


def _aggregate_ballot_boxes(rows, *, name_key, valid_key, voters_key,
                            eligible_key, meta_keys, group_key):
    """Sum ballot-box `rows` into per-group locality records. `group_key(row)`
    returns the grouping id (CBS code or normalized name); rows with a falsy
    group id, or aggregate/envelope names, are skipped. Party columns are every
    column not in `meta_keys`."""
    party_keys = [k for k in rows[0].keys()
                  if k and k.replace("﻿", "").strip()
                  and k not in meta_keys]
    agg = {}
    for r in rows:
        raw = (r.get(name_key) or "").strip()
        if not raw or is_aggregate(raw):
            continue
        gid = group_key(r)
        if not gid:
            continue
        rec = agg.get(gid)
        if rec is None:
            rec = agg[gid] = {"raw": raw, "gid": gid, "votes": {},
                              "valid": 0, "voters": 0, "eligible": 0}
        rec["valid"] += _to_int(r.get(valid_key)) if valid_key else 0
        rec["voters"] += _to_int(r.get(voters_key)) if voters_key else 0
        rec["eligible"] += _to_int(r.get(eligible_key)) if eligible_key else 0
        for pk in party_keys:
            c = _to_int(r.get(pk))
            if c:
                rec["votes"][pk.replace("﻿", "").strip()] = \
                    rec["votes"].get(pk.replace("﻿", "").strip(), 0) + c
    return agg


def _read_bb_csv(path):
    """Per-ballot-box CSV that carries the CBS code (election 18): aggregate by
    CBS code."""
    rows = _read_csv_rows(path)
    keys = list(rows[0].keys())
    name_key = _col(keys, "שם", "ישוב")
    code_key = _col(keys, "סמל", "ישוב")
    valid_key = _col(keys, "כשרים")
    voters_key = _col(keys, "מצביעים")
    eligible_key = _col(keys, "בז")          # "בז''ב" with gershayim
    meta = {k for k in (name_key, code_key, valid_key, voters_key, eligible_key,
                        _col(keys, "סמל", "קלפי"), _col(keys, "פסולים"),
                        _col(keys, "עדכון")) if k}
    agg = _aggregate_ballot_boxes(
        rows, name_key=name_key, valid_key=valid_key, voters_key=voters_key,
        eligible_key=eligible_key, meta_keys=meta,
        group_key=lambda r: (r.get(code_key) or "").strip())
    for cbs, rec in agg.items():
        yield {"raw": rec["raw"], "cbs_code": cbs, "votes": rec["votes"],
               "valid": rec["valid"], "voters": rec["voters"],
               "eligible": rec["eligible"]}


def _read_bb_xls(path, sources_dir):
    """Per-ballot-box legacy .xls with city names but no CBS code (election 17):
    aggregate by normalized name, then resolve the name to a CBS code using the
    name<->code pairs from the per-locality files."""
    import xlrd
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    keys = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
    rows = [{keys[c]: sh.cell_value(r, c) for c in range(sh.ncols)}
            for r in range(1, sh.nrows)]
    name_key = _col(keys, "שם", "ישוב")
    valid_key = _col(keys, "כשרים")
    voters_key = _col(keys, "מצביעים")
    meta = {k for k in (name_key, valid_key, voters_key,
                        _col(keys, "קלפי"), _col(keys, "כתובת")) if k}
    name_to_cbs = build_name_to_cbs(sources_dir)
    agg = _aggregate_ballot_boxes(
        rows, name_key=name_key, valid_key=valid_key, voters_key=voters_key,
        eligible_key=None, meta_keys=meta,
        group_key=lambda r: normalize(r.get(name_key) or ""))
    for _, rec in agg.items():
        yield {"raw": rec["raw"], "cbs_code": name_to_cbs.get(rec["gid"], ""),
               "votes": rec["votes"], "valid": rec["valid"],
               "voters": rec["voters"], "eligible": 0}


_name_to_cbs_cache = {}


def build_name_to_cbs(sources_dir):
    """Map normalized locality name -> CBS code, learned from the per-locality
    files (which carry both). Used to backfill CBS codes for older sources that
    only have names. Cached per sources_dir."""
    if sources_dir in _name_to_cbs_cache:
        return _name_to_cbs_cache[sources_dir]
    mapping = {}
    for n, (fname, fmt) in _SPEC.items():
        if fmt != "loc_csv":
            continue
        for loc in _read_loc_csv(os.path.join(sources_dir, fname)):
            if loc["cbs_code"]:
                mapping.setdefault(normalize(loc["raw"]), loc["cbs_code"])
    _name_to_cbs_cache[sources_dir] = mapping
    return mapping
