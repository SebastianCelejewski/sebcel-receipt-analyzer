import os
import csv
from receipt_processor.parsing import normalize_document_type, normalize_category, format_total

def init_csv(path, csv_headers):
    print(f"Initializing file: {path}")
    exists = os.path.exists(path)
    file = open(path, "a", newline="", encoding="utf-8-sig")
    writer = csv.writer(file, delimiter=";")

    if not exists:
        writer.writerow(csv_headers)

    return file, writer

def write_csv_row(writer, data):
    writer.writerow([
        data.get("datetime"),
        data.get("store"),
        normalize_document_type(data.get("document_type")),
        format_total(data.get("total")),
        normalize_category(data.get("category"))
    ])

def append_items_to_csv(writer, data, items):
    for item in items:
        writer.writerow([
            data.get("datetime"),
            data.get("store"),
            data.get("document_type"),
            data.get("category"),
            item.get("subcategory"),
            item.get("original_name"),
            item.get("normalized_name"),
            item.get("unit"),
            format_number_pl(item.get("unit_price")),
            format_number_pl(item.get("amount")),
            format_number_pl(item.get("price")),
        ])

def format_number_pl(value):
    try:
        return str(value).replace(".", ",")
    except:
        return value 