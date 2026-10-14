"""Date parsing and formatting for passport fields."""

import re


def parse_yymmdd(yymmdd: str) -> str | None:
    """Parse YYMMDD to YYYY-MM-DD. Century: YY < 50 -> 20xx, else 19xx."""
    if not yymmdd or len(yymmdd) != 6 or not yymmdd.isdigit():
        return None
    try:
        yy, mm, dd = yymmdd[0:2], yymmdd[2:4], yymmdd[4:6]
        y = "20" + yy if int(yy) < 50 else "19" + yy
        if not (1 <= int(mm) <= 12 and 1 <= int(dd) <= 31):
            return None
        return f"{y}-{mm}-{dd}"
    except (ValueError, IndexError):
        return None


def normalize_date_to_iso(s: str | None) -> str | None:
    """Best-effort normalize a date string to YYYY-MM-DD. Returns None if unparseable."""
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    # Already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    # DD/MM/YYYY or similar
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$", s)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    m = re.match(r"^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})$", s)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    return None
