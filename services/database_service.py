"""Insert passport OCR result into passport_ocr_results table."""

import logging
import pyodbc  # type: ignore[import-untyped]


def insert_passport_result(conn_str: str, row: dict) -> None:
    """Insert one row into dbo.passport_ocr_results."""
    sql = """
        INSERT INTO dbo.passport_ocr_results (
            request_id, passport_number, surname, given_names, nationality, country_name,
            date_of_birth, expiry_date, sex, national_id,
            mrz_line_1, mrz_line_2,
            mrz_valid, name_match, passport_number_match, dob_match, expiry_match,
            confidence_score, validation_errors,
            raw_visual_fields_json, raw_mrz_fields_json,
            image_url, processing_time, document_model_version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    values = (
        row.get("request_id"),
        row.get("passport_number"),
        row.get("surname"),
        row.get("given_names"),
        row.get("nationality"),
        row.get("country_name"),
        row.get("date_of_birth"),
        row.get("expiry_date"),
        row.get("sex"),
        row.get("national_id"),
        row.get("mrz_line_1"),
        row.get("mrz_line_2"),
        row.get("mrz_valid"),
        row.get("name_match"),
        row.get("passport_number_match"),
        row.get("dob_match"),
        row.get("expiry_match"),
        row.get("confidence_score"),
        row.get("validation_errors"),
        row.get("raw_visual_fields_json"),
        row.get("raw_mrz_fields_json"),
        row.get("image_url"),
        row.get("processing_time"),
        row.get("document_model_version"),
    )
    try:
        with pyodbc.connect(conn_str) as cnxn:
            with cnxn.cursor() as cursor:
                cursor.execute(sql, values)
                cnxn.commit()
        logging.info("Inserted passport_ocr_result for passport_number=%s", row.get("passport_number"))
    except pyodbc.Error as e:
        logging.error("Database insert failed: %s", e, exc_info=True)
        raise
