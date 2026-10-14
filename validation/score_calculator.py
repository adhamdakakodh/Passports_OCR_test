"""Confidence score: MRZ checksum +40, passport +20, DOB +15, expiry +15, name +10."""

def calculate_confidence(
    mrz_valid: bool,
    passport_number_match: bool,
    dob_match: bool,
    expiry_match: bool,
    name_match: bool,
    name_similarity: float = 1.0,
) -> tuple[int, str]:
    """
    Returns (score 0-100, band: "high" | "medium" | "manual_review").
    Weights: MRZ checksum +40, passport +20, DOB +15, expiry +15, name +10.
    """
    score = 0
    if mrz_valid:
        score += 40
    if passport_number_match:
        score += 20
    if dob_match:
        score += 15
    if expiry_match:
        score += 15
    # Name: up to 10 points by similarity
    if name_match:
        score += int(10 * name_similarity) if name_similarity <= 1.0 else 10
    else:
        score += int(10 * name_similarity) if 0 <= name_similarity <= 1.0 else 0

    if score >= 90:
        band = "high"
    elif score >= 70:
        band = "medium"
    else:
        band = "manual_review"
    return min(100, score), band
