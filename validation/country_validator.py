"""Validate nationality code against XLSX-loaded country codes."""

from data.country_codes_loader import get_country_name, is_valid_country_code, load_country_codes


def _normalize_code_for_compare(code: str | None) -> str:
    """Normalize to 3-letter for comparison; German 'D' -> 'DEU'."""
    if not code or not str(code).strip():
        return ""
    c = str(code).strip().upper()
    c = c[:3] if len(c) >= 3 else c
    return "DEU" if c == "D" else (c if len(c) <= 3 else c[:3])


def validate_country(
    nationality_code: str | None,
    mrz_country_code: str | None = None,
) -> tuple[bool, str | None, list[str]]:
    """
    Check nationality code. If visual (nationality_code) and MRZ (mrz_country_code)
    both match each other, do not add invalid_country_code even if not in XLSX.
    Returns (valid, country_name, validation_errors).
    """
    errors: list[str] = []
    if not nationality_code or not str(nationality_code).strip():
        return False, None, ["invalid_country_code"]
    code = str(nationality_code).strip().upper()
    code = code[:3] if len(code) >= 3 else ("DEU" if code == "D" else code)
    mrz_norm = _normalize_code_for_compare(mrz_country_code) if mrz_country_code else ""
    if mrz_norm and code == mrz_norm:
        # Visual and MRZ match: do not add invalid_country_code even if not in XLSX
        name = get_country_name(code)
        return True, name or code, errors
    if not is_valid_country_code(code):
        errors.append("invalid_country_code")
        return False, None, errors
    name = get_country_name(code)
    return True, name or code, errors
