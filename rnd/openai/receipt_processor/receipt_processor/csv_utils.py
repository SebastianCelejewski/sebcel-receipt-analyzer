import os
import csv
from receipt_processor.config import CSV_HEADERS
from receipt_processor.parsing import normalize_document_type, normalize_category, format_total

def init_csv(path):
    exists = os.path.exists(path)
    file = open(path, "a", newline="", encoding="utf-8-sig")
    writer = csv.writer(file, delimiter=";")

    if not exists:
        writer.writerow(CSV_HEADERS)

    return file, writer

def write_csv_row(writer, data):
    writer.writerow([
        data.get("datetime"),
        data.get("store"),
        normalize_document_type(data.get("document_type")),
        format_total(data.get("total")),
        normalize_category(data.get("category"))
    ])