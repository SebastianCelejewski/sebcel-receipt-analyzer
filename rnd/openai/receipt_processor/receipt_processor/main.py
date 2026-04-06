import os
import sys
import argparse

from receipt_processor.parsing import extract_items
from receipt_processor.csv_utils import append_items_to_csv
from receipt_processor.parsing import extract_items
from receipt_processor.csv_utils import append_items_to_csv
from receipt_processor.openai_client import call_openai
from receipt_processor.parsing import parse_response
from receipt_processor.csv_utils import init_csv, write_csv_row
from receipt_processor.file_utils import (
    list_input_files,
    encode_image,
    build_filename,
    safe_rename,
    generate_csv_filenames
)
from receipt_processor.config import SUMMARY_CSV_HEADERS, DETAILS_CSV_HEADERS

def parse_args():
    parser = argparse.ArgumentParser(
        description="Process receipts, invoices, emails and extract structured data."
    )

    parser.add_argument(
        "input",
        help="Path to input folder (will be scanned recursively)"
    )

    return parser.parse_args()

def process_file(path, summary_writer, details_writer):
    dir_path = os.path.dirname(path)
    filename = os.path.basename(path)
    file_extension = os.path.splitext(path)[1].lower()
    print(f"Processing {filename}")

    response = call_openai(path)

    data = parse_response(response)
    if not data:
        return

    write_csv_row(summary_writer, data)

    items = extract_items(data) or []
    append_items_to_csv(details_writer, data, items)

    new_name = build_filename(data, file_extension)
    new_path = os.path.join(dir_path, new_name)

    final_path = safe_rename(path, new_path)
    print("->", final_path)

def main():
    sys.stdout.reconfigure(encoding='utf-8')

    args = parse_args()
    input_folder = args.input
    if not os.path.isdir(input_folder):
        print(f"Error: '{input_folder}' is not a valid directory")
        sys.exit(1)

    summary_csv_path, details_csv_path = generate_csv_filenames()
    
    summary_csv_file, summary_writer = init_csv(summary_csv_path, SUMMARY_CSV_HEADERS)
    details_csv_file, details_writer = init_csv(details_csv_path, DETAILS_CSV_HEADERS)

    try:
        for path in list_input_files(input_folder):
            process_file(path, summary_writer, details_writer)
    finally:
        summary_csv_file.close()
        details_csv_file.close()

if __name__ == "__main__":
    main()