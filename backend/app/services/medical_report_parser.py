import json
import os
import re
from pathlib import Path
from typing import Dict
import zipfile
import xml.etree.ElementTree as ET

from google.cloud import documentai
import google.generativeai as genai
from pydantic import BaseModel

from ..config import get_settings


settings = get_settings()

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

if settings.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

gemini_model = genai.GenerativeModel("gemini-2.5-pro") if settings.GEMINI_API_KEY else None


class MedicalSchema(BaseModel):
    age: float | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    bmi: float | None = None
    gender: str | None = None
    physical_activity_level: str | None = None
    primary_goal: str | None = None
    steps_per_day: float | None = None
    sleep_hours: float | None = None
    diabetes_duration_years: float | None = None
    hba1c_percent: float | None = None
    fasting_glucose_mg_dl: float | None = None
    postprandial_glucose_mg_dl: float | None = None
    triglycerides_mg_dl: float | None = None
    ldl_cholesterol_mg_dl: float | None = None
    hdl_cholesterol_mg_dl: float | None = None
    systolic_bp_mmHg: float | None = None
    diastolic_bp_mmHg: float | None = None
    creatinine_mg_dl: float | None = None
    egfr_ml_min_1_73m2: float | None = None
    smoking_status: int | None = 0
    alcohol_use: int | None = 0


OCR_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/gif",
    "application/msword",
}


def _infer_mime_type(file_path: str, content_type: str | None = None) -> str:
    if content_type:
        return content_type.lower()

    suffix = Path(file_path).suffix.lower()
    mapping = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".gif": "image/gif",
    }
    return mapping.get(suffix, "application/octet-stream")


def extract_text_with_ocr(file_path: str, mime_type: str) -> str:
    client = documentai.DocumentProcessorServiceClient()

    processor_name = client.processor_path(
        settings.GCP_PROJECT_ID,
        settings.GCP_LOCATION,
        settings.GCP_PROCESSOR_ID,
    )

    with open(file_path, "rb") as f:
        file_content = f.read()

    raw_document = documentai.RawDocument(
        content=file_content,
        mime_type=mime_type,
    )

    request = documentai.ProcessRequest(
        name=processor_name,
        raw_document=raw_document,
    )

    result = client.process_document(request=request)
    return result.document.text


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text_from_docx(file_path: str) -> str:
    with zipfile.ZipFile(file_path) as zf:
        with zf.open("word/document.xml") as doc_xml:
            xml_bytes = doc_xml.read()

    root = ET.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = [node.text for node in root.findall(".//w:t", namespace) if node.text]
    return "\n".join(texts)


def extract_with_gemini(text: str) -> Dict:
    if not gemini_model:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    schema_template = MedicalSchema().model_dump()

    prompt = f"""
You are a strict medical data extraction system.

Rules:
- Extract ONLY explicitly mentioned values.
- Do NOT calculate.
- Do NOT assume.
- Missing values must be null.
- Return ONLY valid JSON.
- No explanation text.

Schema:
{json.dumps(schema_template, indent=2)}

Medical Report:
{text}
"""

    response = gemini_model.generate_content(
        prompt,
        generation_config={
            "temperature": 0,
            "response_mime_type": "application/json",
        },
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise RuntimeError("Gemini returned invalid JSON for medical extraction.")


def normalize_output(data: Dict) -> Dict:
    for key, value in list(data.items()):
        if isinstance(value, str):
            clean = (
                value.replace("%", "")
                .replace("mg/dL", "")
                .replace("mmHg", "")
                .strip()
            )

            bp_match = re.match(r"(\d+)\s*/\s*(\d+)", clean)
            if bp_match:
                data["systolic_bp_mmHg"] = float(bp_match.group(1))
                data["diastolic_bp_mmHg"] = float(bp_match.group(2))
                continue

            try:
                data[key] = float(clean)
            except Exception:
                data[key] = clean

    return data


def parse_medical_report(file_path: str, content_type: str | None = None) -> Dict:
    """
    Full pipeline:
    - OCR via Google Document AI
    - Structured extraction via Gemini
    - Normalization
    - Validation against MedicalSchema
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError("Medical report file not found.")

    mime_type = _infer_mime_type(file_path, content_type)

    if mime_type == "text/plain":
        raw_text = extract_text_from_txt(file_path)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        raw_text = extract_text_from_docx(file_path)
    elif mime_type in OCR_MIME_TYPES or mime_type.startswith("image/"):
        raw_text = extract_text_with_ocr(file_path, mime_type)
    else:
        raise ValueError(
            "Unsupported report format. Use PDF, image, TXT, DOC, or DOCX."
        )

    if not raw_text.strip():
        raise RuntimeError("No readable text found in the uploaded report.")

    structured = extract_with_gemini(raw_text)
    normalized = normalize_output(structured)
    validated = MedicalSchema(**normalized)
    return validated.model_dump()

