import os
import base64
import uuid
import re
import unicodedata
from datetime import datetime

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png",
    ".pdf",
    ".eml"
}

def list_input_files(folder):
    result = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()

            if ext in SUPPORTED_EXTENSIONS:
                result.append(os.path.join(root, file))
            else:
                print(f"File {file} is not supported - ignoring!")

    return result

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def sanitize_filename_part(text):
    if not text:
        return "unknown"

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.replace(" ", "_")
    text = re.sub(r'[^A-Za-z0-9._-]', '', text)
    text = re.sub(r'_+', '_', text)
    return text[:100] if text else "unknown"

def build_filename(data, file_extension):
    dt = data.get("datetime", "unknown").replace(":", ".").replace(" ", "_")
    store = sanitize_filename_part(data.get("store", "unknown"))
    return f"{dt}_{store}.{file_extension}"

def safe_rename(src, dst):
    if not os.path.exists(dst):
        os.rename(src, dst)
        return dst

    base, ext = os.path.splitext(dst)
    new_path = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
    os.rename(src, new_path)
    return new_path

def generate_csv_filenames():
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H.%M")
    return f"{timestamp}_summary.csv", f"{timestamp}_details.csv"
