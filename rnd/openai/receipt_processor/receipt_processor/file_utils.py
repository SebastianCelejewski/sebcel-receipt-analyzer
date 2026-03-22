import os
import base64
import uuid
import re
import unicodedata
from datetime import datetime

def list_jpg_files(folder):
    return [f for f in os.listdir(folder) if f.lower().endswith(".jpg")]

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def is_already_processed(filename):
    pattern = r"^\d{4}-\d{2}-\d{2}_\d{2}\.\d{2}_.+\.jpg$"
    return re.match(pattern, filename) is not None

def sanitize_filename_part(text):
    if not text:
        return "unknown"

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.replace(" ", "_")
    text = re.sub(r'[^A-Za-z0-9._-]', '', text)
    text = re.sub(r'_+', '_', text)
    return text[:100] if text else "unknown"

def build_filename(data):
    dt = data.get("datetime", "unknown").replace(":", ".").replace(" ", "_")
    store = sanitize_filename_part(data.get("store", "unknown"))
    return f"{dt}_{store}.jpg"

def safe_rename(src, dst):
    if not os.path.exists(dst):
        os.rename(src, dst)
        return dst

    base, ext = os.path.splitext(dst)
    new_path = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
    os.rename(src, new_path)
    return new_path

def generate_csv_filename():
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H.%M")
    return f"{timestamp}_receipts.csv"    