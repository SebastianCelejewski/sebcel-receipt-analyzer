import re
import unicodedata


def sanitize_filename_part(text):
    if not text:
        return "unknown"

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.replace(" ", "_")
    text = re.sub(r'[^A-Za-z0-9._-]', '', text)
    text = re.sub(r'_+', '_', text)
    return text[:100] if text else "unknown"


def build_base_filename(data):
    """
    Builds a filename (without extension) reflecting the transaction
    date/time and store, e.g. "2026-06-07_12.30_Biedronka".

    Mirrors the naming scheme used by the local rnd/openai/receipt_processor
    tool, so files processed by either tool follow the same convention.
    """
    dt = str(data.get("datetime") or "unknown").replace(":", ".").replace("T", " ").replace(" ", "_")
    store = sanitize_filename_part(data.get("store", "unknown"))
    return f"{dt}_{store}"
