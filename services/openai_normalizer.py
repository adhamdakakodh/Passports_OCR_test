"""Use OpenAI to normalize passport fields: names uppercase, dates YYYY-MM-DD, trim passport number."""

import os
import json
import logging
from openai import AzureOpenAI


def _get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_key=os.environ.get("AZURE_OPENAI_KEY"),
        api_version="2024-02-01",
    )


def normalize(
    visual_fields: dict,
    mrz_fields: dict | None = None,
) -> dict:
    """
    Normalize fields: names uppercase, dates YYYY-MM-DD, passport number alphanumeric only.
    Returns dict with keys: first_name, last_name, passport_number, nationality, date_of_birth, expiry_date, sex.
    """
    combined = {"visual": visual_fields, "mrz": mrz_fields or {}}
    prompt = f"""
Normalize these passport fields into a single JSON object. Use ONLY these keys:
first_name, last_name, passport_number, nationality, date_of_birth, expiry_date, sex.

RULES:
1. Names: uppercase, trim spaces.
2. Dates: format as YYYY-MM-DD.
3. Passport number: alphanumeric only, no spaces or special characters.
4. Nationality: use 3-letter ISO code if possible (e.g. EGY, USA).
5. Sex: M or F.
6. If a value is missing, use null.
7. Prefer MRZ values when visual is missing or ambiguous; otherwise use visual.
8. Output ONLY the JSON object, no other text.

Input data:
{json.dumps(combined, default=str)}
"""
    try:
        client = _get_client()
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You normalize passport data. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        out = json.loads(response.choices[0].message.content)
        return out
    except Exception as e:
        logging.error("OpenAI normalizer failed: %s", e, exc_info=True)
        # Fallback: return visual with simple normalizations
        return {
            "first_name": (visual_fields.get("first_name") or "").strip().upper(),
            "last_name": (visual_fields.get("last_name") or "").strip().upper(),
            "passport_number": "".join(c for c in str(visual_fields.get("passport_number") or "").upper() if c.isalnum()),
            "nationality": (visual_fields.get("nationality") or "").strip().upper()[:3],
            "date_of_birth": visual_fields.get("date_of_birth") or None,
            "expiry_date": visual_fields.get("expiration_date") or visual_fields.get("expiry_date") or None,
            "sex": (visual_fields.get("sex") or "").strip().upper()[:1] or None,
        }
