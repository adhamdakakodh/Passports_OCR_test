"""
Passport OCR: process-passport HTTP trigger runs the full pipeline (Document Intelligence,
MRZ parse/checksum, OpenAI normalize, validation, score, country). Result is returned as JSON
and enqueued to passport-data-to-save; queue trigger saves to dbo.passport_ocr_results.
"""
import os
import json
import logging
import requests  # type: ignore[import-untyped]
import azure.functions as func  # type: ignore[import-untyped]

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

try:
    SQL_CONNECT_STR = os.environ["SqlConnectionString"]
except KeyError as e:
    raise Exception(f"ERROR: Missing Application Setting {e}") from e


@app.route(route="process-passport", methods=["POST"])
@app.queue_output(arg_name="msg", queue_name="passport-data-to-save", connection="AzureWebJobsStorage")
def process_passport(req: func.HttpRequest, msg: func.Out[str]) -> func.HttpResponse:
    """
    Global Passport OCR pipeline: image_url -> Document Intelligence -> MRZ parse/checksum
    -> OpenAI normalize -> cross-validate -> confidence score -> country XLSX -> DB -> JSON response.
    Body: { "image_url": "<url>", "request_id": "optional" }. Or raw image bytes in body.
    """
    import time
    start = time.time()
    logging.info("process-passport: request received")
    try:
        # Get image bytes: from JSON image_url or raw body
        image_bytes = None
        request_id = None
        image_url = None
        body_bytes = req.get_body()
        if body_bytes:
            try:
                body_str = body_bytes.decode("utf-8")
                body_json = json.loads(body_str)
                image_url = body_json.get("image_url")
                request_id = body_json.get("request_id")
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        if image_url:
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            image_bytes = resp.content
            logging.info("process-passport: downloaded image from URL, size=%s", len(image_bytes))
        else:
            image_bytes = body_bytes
        if not image_bytes:
            return func.HttpResponse(
                body=json.dumps({"error": "Provide image_url in JSON body or raw image bytes"}),
                status_code=400,
                mimetype="application/json",
            )

        from services.document_intelligence_service import extract as di_extract
        from mrz.mrz_parser import parse_mrz_lines
        from mrz.mrz_checksum_validator import validate_td3_line2
        from services.openai_normalizer import normalize as openai_normalize
        from validation.field_validation import cross_validate
        from validation.score_calculator import calculate_confidence
        from validation.country_validator import validate_country
        from models.passport_result_model import PassportResultResponse, passport_result_to_db_row

        di_result = di_extract(image_bytes)
        visual_fields = di_result.get("visual_fields") or {}
        mrz_lines = di_result.get("mrz_lines") or []
        logging.info("process-passport: DI done, mrz_lines=%s", len(mrz_lines))

        mrz_fields = None
        mrz_valid = False
        mrz_line_1 = mrz_lines[0] if len(mrz_lines) >= 1 else None
        mrz_line_2 = mrz_lines[1] if len(mrz_lines) >= 2 else None
        validation_errors: list[str] = []

        if len(mrz_lines) >= 2:
            mrz_fields = parse_mrz_lines(mrz_lines)
            if mrz_fields:
                line2 = mrz_lines[-1].replace(" ", "").upper()
                mrz_valid, checksum_errors = validate_td3_line2(line2)
                validation_errors.extend(checksum_errors)
            logging.info("process-passport: MRZ parsed, mrz_valid=%s", mrz_valid)
        else:
            validation_errors.append("mrz_parse_failed")

        normalized = openai_normalize(visual_fields, mrz_fields)
        logging.info("process-passport: OpenAI normalize done")

        passport_number_match = dob_match = expiry_match = name_match = True
        name_similarity = 1.0
        if mrz_fields:
            passport_number_match, dob_match, expiry_match, name_match, name_similarity, cross_errors = cross_validate(
                mrz_fields, normalized
            )
            validation_errors.extend(cross_errors)

        mrz_code = (mrz_fields or {}).get("nationality") or (mrz_fields or {}).get("country_code") if mrz_fields else None
        country_valid, country_name, country_errors = validate_country(
            normalized.get("nationality") or (mrz_fields or {}).get("nationality"),
            mrz_country_code=mrz_code,
        )
        validation_errors.extend(country_errors)
        if not country_name:
            country_name = (normalized.get("nationality") or "")[:3]

        nationality_code = (normalized.get("nationality") or (mrz_fields or {}).get("nationality") or "").strip().upper()[:3]
        national_id = ""
        if nationality_code == "EGY":
            from validation.egypt_national_id import extract_egypt_national_id
            extracted_id, nid_errors = extract_egypt_national_id(di_result.get("ocr_lines") or [])
            national_id = extracted_id or ""
            validation_errors.extend(nid_errors)
            logging.info("process-passport: EGY national_id extracted=%s", bool(national_id))

        if len(validation_errors) >= 2:
            logging.info("process-passport: multiple validation errors, skipping save")
            return func.HttpResponse(
                body=json.dumps({
                    "error": "Multiple validation errors; result not saved.",
                    "validation_errors": validation_errors,
                }, indent=2),
                status_code=422,
                mimetype="application/json",
            )

        score, band = calculate_confidence(
            mrz_valid, passport_number_match, dob_match, expiry_match, name_match, name_similarity
        )
        logging.info("process-passport: confidence_score=%s band=%s", score, band)

        surname = normalized.get("last_name") or (mrz_fields or {}).get("surname") or ""
        given_names = normalized.get("first_name") or (mrz_fields or {}).get("given_names") or ""
        result = PassportResultResponse(
            passport_number=normalized.get("passport_number") or (mrz_fields or {}).get("passport_number") or "",
            name=f"{given_names} {surname}".strip(),
            surname=surname,
            given_names=given_names,
            nationality=(normalized.get("nationality") or (mrz_fields or {}).get("nationality") or "").strip()[:3],
            country=country_name or "",
            date_of_birth=normalized.get("date_of_birth") or (mrz_fields or {}).get("birth_date") or "",
            expiry_date=normalized.get("expiry_date") or (mrz_fields or {}).get("expiry_date") or "",
            sex=normalized.get("sex") or (mrz_fields or {}).get("sex") or "",
            national_id=national_id,
            mrz_valid=mrz_valid,
            confidence_score=score,
            validation_errors=validation_errors,
        )

        db_row = passport_result_to_db_row(
            result=result,
            request_id=request_id,
            mrz_line_1=mrz_line_1,
            mrz_line_2=mrz_line_2,
            name_match=name_match,
            passport_number_match=passport_number_match,
            dob_match=dob_match,
            expiry_match=expiry_match,
            raw_visual_fields_json=json.dumps(visual_fields, default=str),
            raw_mrz_fields_json=json.dumps(mrz_fields, default=str) if mrz_fields else "{}",
            image_url=image_url,
            processing_time_ms=int((time.time() - start) * 1000) if start else None,
            document_model_version="prebuilt-idDocument",
        )
        msg.set(json.dumps(db_row, default=str))
        logging.info("process-passport: enqueued for DB save")

        response_body = result.model_dump()
        return func.HttpResponse(
            body=json.dumps(response_body, indent=2, default=str),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logging.error("process-passport error: %s", e, exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


@app.queue_trigger(arg_name="msg", queue_name="passport-data-to-save", connection="AzureWebJobsStorage")
def save_passport_from_queue(msg: func.QueueMessage) -> None:
    """Save queued passport_ocr_results row to dbo.passport_ocr_results."""
    logging.info("Queue trigger save_passport_from_queue started.")
    try:
        from services.database_service import insert_passport_result
        body = msg.get_body().decode("utf-8")
        row = json.loads(body)
        logging.info("Saving passport_ocr_result for passport_number=%s", row.get("passport_number"))
        insert_passport_result(SQL_CONNECT_STR, row)
        logging.info("Successfully saved passport from queue.")
    except Exception as e:
        logging.error("Error processing queue message: %s", e, exc_info=True)
        raise
