"""Reusable text normalizers for passport/document comparison."""


def normalize_document_number(s: str | None) -> str:
    """Alphanumeric only, uppercase. So 'AB 1234567', 'AB-1234567' -> 'AB1234567'."""
    if s is None:
        return ""
    return "".join(c for c in str(s).upper().strip() if c.isalnum())


def normalize_name_for_compare(s: str | None) -> str:
    """Uppercase, collapse spaces, for fuzzy name comparison."""
    if s is None:
        return ""
    return " ".join(str(s).upper().split())


def tokenize_mrz_name(mrz_name: str) -> set[str]:
    """Tokenize MRZ name (e.g. 'SMITH<<JOHN' -> {'SMITH', 'JOHN'})."""
    if not mrz_name:
        return set()
    t = mrz_name.replace("<", " ").upper().split()
    return set(p for p in t if p)


def tokenize_visual_name(visual_name: str) -> set[str]:
    """Tokenize visual name (spaces, hyphens)."""
    if not visual_name:
        return set()
    t = str(visual_name).upper().replace("-", " ").split()
    return set(p for p in t if p)


def name_similarity(s1: str | None, s2: str | None) -> float:
    """Jaccard-like token similarity between two name strings. Returns 0.0 to 1.0."""
    tokens1 = tokenize_visual_name(s1 or "") or tokenize_mrz_name(s1 or "")
    tokens2 = tokenize_visual_name(s2 or "") or tokenize_mrz_name(s2 or "")
    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0
    inter = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return inter / union if union else 0.0
