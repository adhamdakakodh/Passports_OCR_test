"""Parse TD3 (passport) MRZ lines into structured fields."""

from utils.date_utils import parse_yymmdd

MRZ_LINE_LENGTH = 44


def parse_td3(line1: str, line2: str) -> dict | None:
    """
    Parse TD3 (passport) MRZ: 2 lines of 44 chars.
    Returns dict with: document_type, country_code, surname, given_names, passport_number,
    nationality, birth_date, sex, expiry_date, issuing_country.
    """
    if len(line1) != MRZ_LINE_LENGTH or len(line2) != MRZ_LINE_LENGTH:
        return None
    try:
        # Line 1: P<country(3)<<surname<<given_names
        document_type = line1[0:2].replace("<", "")
        issuing_country = line1[2:5].replace("<", "")
        name_part = line1[5:44].replace("<", " ").strip()
        parts = [p.strip() for p in name_part.split("  ") if p.strip()]
        surname = (parts[0] if parts else "").replace("  ", " ")
        given_names = (parts[1] if len(parts) > 1 else "").replace("  ", " ")

        # Line 2: doc_number(9), check(1), nationality(3), birth(6), check(1), sex(1), expiry(6), check(1)...
        passport_number = line2[0:9].replace("<", "").strip()
        nationality = line2[10:13].replace("<", "")
        birth_raw = line2[13:19]
        sex = line2[20] if line2[20] in "MF" else ""
        expiry_raw = line2[21:27]

        return {
            "document_type": document_type,
            "country_code": issuing_country,
            "issuing_country": issuing_country,
            "surname": surname,
            "given_names": given_names,
            "passport_number": passport_number,
            "nationality": nationality,
            "birth_date": parse_yymmdd(birth_raw),
            "birth_date_raw": birth_raw,
            "sex": sex,
            "expiry_date": parse_yymmdd(expiry_raw),
            "expiry_date_raw": expiry_raw,
        }
    except Exception:
        return None


def parse_mrz_lines(mrz_lines: list[str]) -> dict | None:
    """Parse MRZ lines (TD3: last 2 lines of 44 chars). Returns parsed dict or None."""
    if not mrz_lines or len(mrz_lines) < 2:
        return None
    line1 = mrz_lines[-2].replace(" ", "").upper()
    line2 = mrz_lines[-1].replace(" ", "").upper()
    if len(line1) != MRZ_LINE_LENGTH or len(line2) != MRZ_LINE_LENGTH:
        return None
    return parse_td3(line1, line2)
