"""Extract and validate the Egyptian national ID (الرقم القومي) from passport OCR lines.

Egyptian national ID: 14 digits, read left to right, always starts with 2 or 3.
It appears in the visual zone (right side, under the issuing office) next to the
Arabic label الرقم القومي.
"""

import re

NATIONAL_ID_LABEL = "الرقم القومي"
# 14 digits, first digit 2 or 3, not adjacent to other digits.
NATIONAL_ID_PATTERN = re.compile(r"(?<!\d)([23]\d{13})(?!\d)")

# Arabic-Indic and Extended Arabic-Indic digit maps to ASCII 0-9.
_ARABIC_DIGITS = {
    "\u0660": "0", "\u0661": "1", "\u0662": "2", "\u0663": "3", "\u0664": "4",
    "\u0665": "5", "\u0666": "6", "\u0667": "7", "\u0668": "8", "\u0669": "9",
    "\u06f0": "0", "\u06f1": "1", "\u06f2": "2", "\u06f3": "3", "\u06f4": "4",
    "\u06f5": "5", "\u06f6": "6", "\u06f7": "7", "\u06f8": "8", "\u06f9": "9",
}


def _normalize_digits(text: str) -> str:
    """Convert Arabic-Indic digits to ASCII digits."""
    return "".join(_ARABIC_DIGITS.get(ch, ch) for ch in text)


def _find_id_in_text(text: str) -> str | None:
    """Return the first valid 14-digit national ID in text (digits already normalized)."""
    match = NATIONAL_ID_PATTERN.search(text)
    return match.group(1) if match else None


def extract_egypt_national_id(ocr_lines: list[str]) -> tuple[str | None, list[str]]:
    """
    Extract the Egyptian national ID from OCR lines.

    Strategy: prefer the ID closest to the الرقم القومي label (same line, then the
    following few lines). Fall back to any valid 14-digit sequence in the document.
    Returns (national_id, validation_errors).
    """
    errors: list[str] = []
    if not ocr_lines:
        return None, ["national_id_missing"]

    normalized_lines = [_normalize_digits(line) for line in ocr_lines]

    # 1) Search near the Arabic label first.
    label_indices = [i for i, line in enumerate(ocr_lines) if NATIONAL_ID_LABEL in line]
    for idx in label_indices:
        for offset in range(0, 3):
            j = idx + offset
            if j < len(normalized_lines):
                found = _find_id_in_text(normalized_lines[j])
                if found:
                    return found, errors
        # also check the line immediately above the label
        if idx - 1 >= 0:
            found = _find_id_in_text(normalized_lines[idx - 1])
            if found:
                return found, errors

    # 2) Fall back to any valid 14-digit sequence anywhere in the document.
    for line in normalized_lines:
        found = _find_id_in_text(line)
        if found:
            return found, errors

    # 3) Last resort: a 14-digit run present but not starting with 2/3 -> invalid.
    for line in normalized_lines:
        m = re.search(r"(?<!\d)(\d{14})(?!\d)", line)
        if m:
            return None, ["national_id_invalid"]

    return None, ["national_id_missing"]


def is_valid_national_id(national_id: str | None) -> bool:
    """True if 14 digits and starts with 2 or 3."""
    if not national_id:
        return False
    nid = _normalize_digits(str(national_id).strip())
    return len(nid) == 14 and nid.isdigit() and nid[0] in ("2", "3")
