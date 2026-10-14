"""ICAO MRZ checksum validation. Weights [7,3,1]; 0-9->0-9, A-Z->10-35, <->0."""

# Character value for checksum: 0-9 -> 0-9, A-Z -> 10-35, < -> 0
_WEIGHTS = [7, 3, 1]


def _char_value(c: str) -> int:
    if c == "<":
        return 0
    if c.isdigit():
        return int(c)
    if "A" <= c <= "Z":
        return ord(c) - ord("A") + 10
    return 0


def compute_checksum(s: str) -> int:
    """Compute ICAO checksum: sum(value * weight) % 10 for positions 0..len(s)-1."""
    total = 0
    for i, c in enumerate(s):
        total += _char_value(c) * _WEIGHTS[i % 3]
    return total % 10


def validate_field(value_with_check: str, check_pos: int) -> bool:
    """
    value_with_check: string that includes the check digit at index check_pos.
    So for passport number (9 chars + 1 check), value_with_check is 10 chars, check_pos=9.
    """
    if not value_with_check or check_pos >= len(value_with_check):
        return False
    segment = value_with_check[:check_pos]
    expected_check = int(value_with_check[check_pos]) if value_with_check[check_pos].isdigit() else -1
    computed = compute_checksum(segment)
    return computed == expected_check


def validate_td3_line2(line2: str) -> tuple[bool, list[str]]:
    """
    Validate checksums in TD3 line 2 (44 chars).
    Positions: passport_number 0-8, check 9; birth 13-18, check 19; expiry 21-26, check 27.
    Returns (all_valid, list of error codes).
    """
    errors: list[str] = []
    if len(line2) < 28:
        return False, ["mrz_checksum_failed"]

    doc_ok = validate_field(line2[0:10], 9)
    if not doc_ok:
        errors.append("mrz_checksum_failed")

    birth_ok = validate_field(line2[13:20], 6)
    if not birth_ok:
        errors.append("mrz_checksum_failed")

    expiry_ok = validate_field(line2[21:28], 6)
    if not expiry_ok:
        errors.append("mrz_checksum_failed")

    return (doc_ok and birth_ok and expiry_ok), errors
