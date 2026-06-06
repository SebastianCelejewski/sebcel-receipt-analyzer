import os
import json
import base64
import uuid
import re
import unicodedata
from datetime import datetime

SUPPORTED_EXTENSIONS = {
    "jpg", "jpeg", "png",
    "pdf",
    "eml"
}

def list_input_files(folder):
    result = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext.startswith("."):
                ext = ext[1:]

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

def sidecar_path(file_path):
    return file_path + ".json"

def has_sidecar(file_path):
    return os.path.exists(sidecar_path(file_path))

def save_sidecar(file_path, data):
    with open(sidecar_path(file_path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_sidecar(file_path):
    with open(sidecar_path(file_path), "r", encoding="utf-8") as f:
        return json.load(f)

def rename_sidecar(old_file_path, new_file_path):
    old_sc = sidecar_path(old_file_path)
    new_sc = sidecar_path(new_file_path)
    if os.path.exists(old_sc) and not os.path.exists(new_sc):
        os.rename(old_sc, new_sc)

def list_sidecars(folder):
    result = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".json"):
                result.append(os.path.join(root, file))
    return result

def generate_csv_filenames():
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H.%M")
    return f"{timestamp}_summary.csv", f"{timestamp}_details.csv"
