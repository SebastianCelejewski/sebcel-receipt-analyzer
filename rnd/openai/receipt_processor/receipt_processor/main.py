import os
import sys
from receipt_processor.parsing import extract_items
from receipt_processor.csv_utils import append_items_to_csv
from receipt_processor.parsing import extract_items
from receipt_processor.csv_utils import append_items_to_csv
from receipt_processor.openai_client import call_openai
from receipt_processor.parsing import parse_response
from receipt_processor.csv_utils import init_csv, write_csv_row
from receipt_processor.file_utils import (
    list_jpg_files,
    encode_image,
    is_already_processed,
    build_filename,
    safe_rename,
    generate_csv_filenames
)
from receipt_processor.config import SUMMARY_CSV_HEADERS, DETAILS_CSV_HEADERS

def process_file(folder, filename, summary_writer, details_writer):
    path = os.path.join(folder, filename)
    print(f"Processing {filename}")

    print("[image]", end="", flush=True)
    image = encode_image(path)

    print("[openai]", end="", flush=True)
    response = call_openai(image)

    print("[parsing]", end="", flush=True)
    data = parse_response(response)
    if not data:
        return

    print("[csv_s]", end="", flush=True)
    write_csv_row(summary_writer, data)

    print("[csv_d]", end="", flush=True)
    items = extract_items(data) or []
    append_items_to_csv(details_writer, data, items)

    print("[rename]", end="\n")
    new_name = build_filename(data)
    new_path = os.path.join(folder, new_name)

    final_path = safe_rename(path, new_path)
    print("->", final_path)

def main():
    sys.stdout.reconfigure(encoding='utf-8')

    folder = "."
    summary_csv_path, details_csv_path = generate_csv_filenames()
    
    summary_csv_file, summary_writer = init_csv(summary_csv_path, SUMMARY_CSV_HEADERS)
    details_csv_file, details_writer = init_csv(details_csv_path, DETAILS_CSV_HEADERS)

    try:
        for file in list_jpg_files(folder):
            process_file(folder, file, summary_writer, details_writer)
    finally:
        summary_csv_file.close()
        details_csv_file.close()

if __name__ == "__main__":
    main()