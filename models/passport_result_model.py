"""Pydantic/dataclass models for passport OCR result and DB row."""

from typing import Any

from pydantic import BaseModel, Field


class PassportResultResponse(BaseModel):
    """Final JSON response for process-passport endpoint."""

    passport_number: str = ""
    name: str = Field(default="", description="Surname + given names combined")
    surname: str = ""
    given_names: str = ""
    nationality: str = ""
    country: str = Field(default="", description="Country name from XLSX")
    date_of_birth: str = ""
    expiry_date: str = ""
    sex: str = ""
    national_id: str = Field(default="", description="Egyptian national ID (EGY only)")
    mrz_valid: bool = False
    confidence_score: int = 0
    validation_errors: list[str] = Field(default_factory=list)


def passport_result_to_db_row(
    result: PassportResultResponse,
    request_id: str | None,
    mrz_line_1: str | None,
    mrz_line_2: str | None,
    name_match: bool,
    passport_number_match: bool,
    dob_match: bool,
    expiry_match: bool,
    raw_visual_fields_json: str,
    raw_mrz_fields_json: str,
    image_url: str | None = None,
    processing_time_ms: int | None = None,
    document_model_version: str | None = None,
) -> dict[str, Any]:
    """Build a flat dict suitable for INSERT into passport_ocr_results."""
    import json

    return {
        "request_id": request_id,
        "passport_number": result.passport_number,
        "surname": result.surname,
        "given_names": result.given_names,
        "nationality": result.nationality,
        "country_name": result.country,
        "date_of_birth": result.date_of_birth,
        "expiry_date": result.expiry_date,
        "sex": result.sex,
        "national_id": result.national_id,
        "mrz_line_1": mrz_line_1,
        "mrz_line_2": mrz_line_2,
        "mrz_valid": result.mrz_valid,
        "name_match": name_match,
        "passport_number_match": passport_number_match,
        "dob_match": dob_match,
        "expiry_match": expiry_match,
        "confidence_score": result.confidence_score,
        "validation_errors": json.dumps(result.validation_errors) if result.validation_errors else None,
        "raw_visual_fields_json": raw_visual_fields_json,
        "raw_mrz_fields_json": raw_mrz_fields_json,
        "image_url": image_url,
        "processing_time": processing_time_ms,
        "document_model_version": document_model_version,
    }
