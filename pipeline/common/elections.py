"""Shared reading of the Knesset election CSVs + per-dataset vote math.

Used by build_geo (for the per-city size weight) and by every election-derived
dataset (haredi-vote, right-left-vote, ...) for its values. The raw results are
one shared source feeding many visualizations; the per-derivation math (Haredi
share, right/left margin) also lives here so the reductions sit next to the
reader. The CSVs are per-locality, one column per party ballot-letter; files mix
UTF-8 and Windows-1255 encodings and vary their headers slightly across elections.
"""

import csv
import os

from normalize import normalize

# The shared election-results source package. All consumers read the raw CSVs
# from here — the results belong to no single dataset.
SOURCES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "elections", "sources"))

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


# Per-election party table: ballot letter -> (Hebrew party name, bloc). This is
# the single source of truth for both the right/left margin (the bloc field) and
# the per-city "how they voted" breakdown (the name field). It MUST be keyed by
# election: letters are reused across elections by completely different parties —
# e.g. כן = Kadima in 2006 but National Unity in 2021-22; ב = Jewish Home in 2009
# but Yamina in 2021; ט = National Union in 2009 but Religious Zionism in 2021. A
# single global letter->party map would be silently wrong.
#
# Bloc rule (documented in datasets/right-left-vote/SOURCE.md):
#   - Ideological placement. Religious-right, settler/national, and secular
#     nationalist (Yisrael Beiteinu) parties -> "R".
#   - Genuine-center parties (Kadima, Yesh Atid, Kahol Lavan / National Unity,
#     Kulanu, Pensioners) and the Zionist/Arab/communist left -> "L". This applies
#     the "center -> left, Arab -> left" two-bloc choice for this dataset.
#   - New Hope (Sa'ar) is an explicitly right-wing breakaway -> "R".
# bloc=None means "named but unclassified" (won't move the margin). Letters absent
# entirely (tiny/unidentified lists) show in a breakdown under their raw letter.
PARTIES = {
    17: {  # 2006
        "מחל": ("הליכוד", "R"), "ל": ("ישראל ביתנו", "R"), "שס": ('ש"ס', "R"),
        "ג": ("יהדות התורה", "R"), "טב": ('האיחוד הלאומי-מפד"ל', "R"),
        "כן": ("קדימה", "L"), "אמת": ("העבודה", "L"), "זך": ("גיל הגמלאים", "L"),
        "מרצ": ("מרצ", "L"), "עם": ('רע"מ-תע"ל', "L"), "ו": ('חד"ש', "L"), "ד": ('בל"ד', "L"),
    },
    18: {  # 2009
        "מחל": ("הליכוד", "R"), "ל": ("ישראל ביתנו", "R"), "שס": ('ש"ס', "R"),
        "ג": ("יהדות התורה", "R"), "ט": ("האיחוד הלאומי", "R"), "ב": ("הבית היהודי", "R"),
        "כן": ("קדימה", "L"), "אמת": ("העבודה", "L"), "מרצ": ("מרצ", "L"),
        "עם": ('רע"מ-תע"ל', "L"), "ו": ('חד"ש', "L"), "ד": ('בל"ד', "L"),
    },
    19: {  # Jan 2013
        "מחל": ("הליכוד ביתנו", "R"), "שס": ('ש"ס', "R"), "טב": ("הבית היהודי", "R"),
        "ג": ("יהדות התורה", "R"), "נץ": ("עוצמה לישראל", "R"),
        "פה": ("יש עתיד", "L"), "אמת": ("העבודה", "L"), "צפ": ("התנועה", "L"),
        "מרץ": ("מרצ", "L"), "כן": ("קדימה", "L"),
        "עם": ('רע"מ-תע"ל', "L"), "ו": ('חד"ש', "L"), "ד": ('בל"ד', "L"),
    },
    20: {  # Mar 2015
        "מחל": ("הליכוד", "R"), "טב": ("הבית היהודי", "R"), "שס": ('ש"ס', "R"),
        "ל": ("ישראל ביתנו", "R"), "ג": ("יהדות התורה", "R"), "קץ": ("יחד", "R"),
        "אמת": ("המחנה הציוני", "L"), "פה": ("יש עתיד", "L"), "כ": ("כולנו", "L"),
        "מרצ": ("מרצ", "L"), "ודעם": ("הרשימה המשותפת", "L"),
    },
    21: {  # Apr 2019
        "מחל": ("הליכוד", "R"), "שס": ('ש"ס', "R"), "ג": ("יהדות התורה", "R"),
        "ל": ("ישראל ביתנו", "R"), "טב": ("איחוד מפלגות הימין", "R"),
        "נ": ("הימין החדש", "R"), "ז": ("זהות", "R"),
        "פה": ("כחול לבן", "L"), "אמת": ("העבודה", "L"), "מרצ": ("מרצ", "L"),
        "כ": ("כולנו", "L"), "נר": ("גשר", "L"),
        "ום": ('חד"ש-תע"ל', "L"), "דעם": ('רע"מ-בל"ד', "L"),
    },
    22: {  # Sep 2019
        "מחל": ("הליכוד", "R"), "שס": ('ש"ס', "R"), "ל": ("ישראל ביתנו", "R"),
        "ג": ("יהדות התורה", "R"), "טב": ("ימינה", "R"), "כף": ("עוצמה יהודית", "R"),
        "פה": ("כחול לבן", "L"), "אמת": ("העבודה-גשר", "L"),
        "מרצ": ("המחנה הדמוקרטי", "L"), "ודעם": ("הרשימה המשותפת", "L"),
    },
    23: {  # Mar 2020
        "מחל": ("הליכוד", "R"), "שס": ('ש"ס', "R"), "ג": ("יהדות התורה", "R"),
        "ל": ("ישראל ביתנו", "R"), "טב": ("ימינה", "R"),
        "פה": ("כחול לבן", "L"), "אמת": ("העבודה-גשר-מרצ", "L"),
        "ודעם": ("הרשימה המשותפת", "L"),
    },
    24: {  # Mar 2021
        "מחל": ("הליכוד", "R"), "שס": ('ש"ס', "R"), "ג": ("יהדות התורה", "R"),
        "ב": ("ימינה", "R"), "ל": ("ישראל ביתנו", "R"), "ט": ("הציונות הדתית", "R"),
        "ת": ("תקווה חדשה", "R"),
        "פה": ("יש עתיד", "L"), "כן": ("כחול לבן", "L"), "אמת": ("העבודה", "L"),
        "מרצ": ("מרצ", "L"), "ודעם": ("הרשימה המשותפת", "L"), "עם": ('רע"מ', "L"),
    },
    25: {  # Nov 2022
        "מחל": ("הליכוד", "R"), "ט": ("הציונות הדתית", "R"), "שס": ('ש"ס', "R"),
        "ג": ("יהדות התורה", "R"), "ל": ("ישראל ביתנו", "R"), "ב": ("הבית היהודי", "R"),
        "פה": ("יש עתיד", "L"), "כן": ("המחנה הממלכתי", "L"), "אמת": ("העבודה", "L"),
        "מרצ": ("מרצ", "L"), "עם": ('רע"מ', "L"), "ום": ('חד"ש-תע"ל', "L"), "ד": ('בל"ד', "L"),
    },
}

# Derived letter -> bloc map per election (only the classified letters).
BLOC = {e: {ltr: bloc for ltr, (_, bloc) in parties.items() if bloc}
        for e, parties in PARTIES.items()}


def right_left_margin(votes, election):
    """Signed right-vs-left margin in [-1, +1] for one locality in `election`:
    (R - L) / (R + L) over the votes whose ballot letter is classified in
    BLOC[election]. +1 = entirely right bloc, -1 = entirely left bloc, 0 = even.
    Returns None if no classified votes (so the city shows as no-data, never a
    misleading 0). Unclassified letters are ignored — they belong to neither bloc.
    """
    blocs = BLOC[election]
    r = sum(c for letter, c in votes.items() if blocs.get(letter) == "R")
    l = sum(c for letter, c in votes.items() if blocs.get(letter) == "L")
    if r + l == 0:
        return None
    return (r - l) / (r + l)


def classified_share(votes, valid, election):
    """Fraction of valid votes that fell into a classified (R or L) bloc — a
    coverage stat for the right/left builder. 0 if no valid votes."""
    if not valid:
        return 0.0
    blocs = BLOC[election]
    return sum(c for letter, c in votes.items() if letter in blocs) / valid


def top_parties(votes, valid, election, n=6):
    """The per-city "how they voted" breakdown: the top `n` parties by votes, each
    as {labelHe, value (share of valid votes), tag?}, plus an aggregated "אחר"
    (other) row so the parts sum to ~1. `tag` is "R"/"L" when the party is in a
    bloc, omitted otherwise. Named from PARTIES[election]; unknown letters fall
    back to the raw letter. Returns [] if there are no valid votes."""
    if not valid:
        return []
    names = PARTIES.get(election, {})
    ranked = sorted(votes.items(), key=lambda kv: -kv[1])
    parts = []
    shown = 0
    for letter, c in ranked[:n]:
        if c <= 0:
            break
        name, bloc = names.get(letter, (letter, None))
        part = {"labelHe": name, "value": round(c / valid, 4)}
        if bloc:
            part["tag"] = bloc
        parts.append(part)
        shown += c
    other = valid - shown
    if other > 0:
        parts.append({"labelHe": "אחר", "value": round(other / valid, 4)})
    return parts


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
