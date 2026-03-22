import json
from receipt_processor.config import ALLOWED_CATEGORIES

def extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

def parse_response(text):
    try:
        return json.loads(extract_json(text))
    except Exception:
        print("JSON parse error:", text)
        return None

def normalize_document_type(value):
    return str(value).strip().lower() if value else ""

def normalize_category(value):
    if not value:
        return "inne"
    value = value.strip().lower()
    return value if value in ALLOWED_CATEGORIES else "inne"

def format_total(value):
    if not value:
        return ""
    value = str(value).replace(",", ".")
    try:
        return f"{float(value):.2f}".replace(".", ",")
    except:
        return value