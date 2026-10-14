"""Cross-validate MRZ vs normalized visual fields."""

from utils.text_normalization import (
    normalize_document_number,
    normalize_name_for_compare,
    name_similarity,
    tokenize_mrz_name,
    tokenize_visual_name,
)


def cross_validate(
    mrz_fields: dict | None,
    normalized_visual: dict,
) -> tuple[bool, bool, bool, bool, list[str]]:
    """
    Compare MRZ vs normalized visual.
    Returns (passport_number_match, dob_match, expiry_match, name_match, name_similarity, validation_errors).
    """
    errors: list[str] = []
    passport_number_match = True
    dob_match = True
    expiry_match = True
    name_match = True
    name_sim = 0.0

    if not mrz_fields:
        return False, False, False, False, 0.0, ["mrz_parse_failed"]

    mrz_doc = normalize_document_number(mrz_fields.get("passport_number"))
    vis_doc = normalize_document_number(normalized_visual.get("passport_number"))
    if mrz_doc != vis_doc:
        passport_number_match = False
        errors.append("passport_number_mismatch")

    mrz_dob = (mrz_fields.get("birth_date") or "").strip()
    vis_dob = (normalized_visual.get("date_of_birth") or "").strip()
    if mrz_dob != vis_dob:
        dob_match = False
        errors.append("dob_mismatch")

    mrz_exp = (mrz_fields.get("expiry_date") or "").strip()
    vis_exp = (normalized_visual.get("expiry_date") or "").strip()
    if mrz_exp != vis_exp:
        expiry_match = False
        errors.append("expiry_mismatch")

    mrz_surname = mrz_fields.get("surname") or ""
    mrz_given = mrz_fields.get("given_names") or ""
    vis_last = normalized_visual.get("last_name") or ""
    vis_first = normalized_visual.get("first_name") or ""
    mrz_full = f"{mrz_surname} {mrz_given}".strip()
    vis_full = f"{vis_last} {vis_first}".strip()
    name_sim = name_similarity(mrz_full, vis_full)
    if name_sim < 0.5:
        name_match = False
        errors.append("name_mismatch")

    return passport_number_match, dob_match, expiry_match, name_match, name_sim, errors
