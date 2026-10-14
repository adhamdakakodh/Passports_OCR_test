"""Call Document Intelligence (prebuilt-id-document) and return visual fields + MRZ lines."""

import os
import logging
from azure.core.credentials import AzureKeyCredential  # type: ignore[import-untyped]
from azure.ai.formrecognizer import DocumentAnalysisClient  # type: ignore[import-untyped]

MODEL_ID = "prebuilt-idDocument"
MRZ_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")
MRZ_LINE_LEN = 44


def _get_client() -> DocumentAnalysisClient:
    endpoint = os.environ.get("AZURE_DOC_INTEL_ENDPOINT")
    key = os.environ.get("AZURE_DOC_INTEL_KEY")
    if not endpoint or not key:
        raise ValueError("AZURE_DOC_INTEL_ENDPOINT and AZURE_DOC_INTEL_KEY must be set")
    return DocumentAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )


def _field_value(field) -> str | None:
    """Extract string value from a DocumentField."""
    if field is None:
        return None
    if hasattr(field, "value") and field.value is not None:
        return str(field.value).strip()
    return None


def _find_mrz_lines_from_pages(pages) -> list[str]:
    """Scan page lines for MRZ-like lines (44 chars, allowed set)."""
    mrz_lines = []
    for page in pages:
        for line in page.lines:
            content = line.content.replace(" ", "").upper()
            if len(content) == MRZ_LINE_LEN and all(c in MRZ_CHARS for c in content):
                mrz_lines.append(content)
    return mrz_lines


def _all_ocr_lines(pages) -> list[str]:
    """Return all OCR text lines (original content, not MRZ-normalized)."""
    lines: list[str] = []
    for page in pages:
        for line in page.lines:
            content = (line.content or "").strip()
            if content:
                lines.append(content)
    return lines


def extract(image_bytes: bytes) -> dict:
    """
    Analyze passport image with Document Intelligence.
    Returns { "visual_fields": {...}, "mrz_lines": [...], "ocr_lines": [...] }.
    """
    client = _get_client()
    poller = client.begin_analyze_document(MODEL_ID, document=image_bytes)
    result = poller.result()
    visual_fields: dict[str, str | None] = {}
    mrz_lines: list[str] = []
    ocr_lines: list[str] = []

    if result.documents:
        doc = result.documents[0]
        fields = getattr(doc, "fields", None) or {}
        # Map common ID document field names to our canonical names
        visual_fields["first_name"] = _field_value(fields.get("FirstName"))
        visual_fields["last_name"] = _field_value(fields.get("LastName"))
        visual_fields["passport_number"] = _field_value(fields.get("DocumentNumber"))
        visual_fields["nationality"] = _field_value(fields.get("CountryRegion"))
        visual_fields["date_of_birth"] = _field_value(fields.get("DateOfBirth"))
        visual_fields["expiration_date"] = _field_value(fields.get("ExpirationDate"))
        visual_fields["sex"] = _field_value(fields.get("Sex"))

    if result.pages:
        mrz_lines = _find_mrz_lines_from_pages(result.pages)
        ocr_lines = _all_ocr_lines(result.pages)

    logging.info(
        "Document Intelligence extraction done: %d visual fields, %d MRZ lines, %d OCR lines",
        len(visual_fields), len(mrz_lines), len(ocr_lines),
    )
    return {"visual_fields": visual_fields, "mrz_lines": mrz_lines, "ocr_lines": ocr_lines}
