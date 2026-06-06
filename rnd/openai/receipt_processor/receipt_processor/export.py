import os
import sys
import argparse

from receipt_processor.parsing import extract_items
from receipt_processor.csv_utils import init_csv, write_csv_row, append_items_to_csv
from receipt_processor.file_utils import list_sidecars, load_sidecar, generate_csv_filenames
from receipt_processor.config import SUMMARY_CSV_HEADERS, DETAILS_CSV_HEADERS


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export already-processed receipts from JSON sidecars to CSV."
    )
    parser.add_argument(
        "input",
        help="Path to input folder (will be scanned recursively for .json sidecar files)"
    )
    return parser.parse_args()


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    input_folder = args.input
    if not os.path.isdir(input_folder):
        print(f"Error: '{input_folder}' is not a valid directory")
        sys.exit(1)

    sidecars = list_sidecars(input_folder)
    if not sidecars:
        print("No processed files found (no .json sidecar files in the input folder).")
        sys.exit(0)

    summary_csv_path, details_csv_path = generate_csv_filenames()
    summary_csv_file, summary_writer = init_csv(summary_csv_path, SUMMARY_CSV_HEADERS)
    details_csv_file, details_writer = init_csv(details_csv_path, DETAILS_CSV_HEADERS)

    try:
        for sidecar in sorted(sidecars):
            print(f"Exporting {os.path.basename(sidecar)}")
            data = load_sidecar(sidecar)
            write_csv_row(summary_writer, data)
            items = extract_items(data) or []
            append_items_to_csv(details_writer, data, items)
    finally:
        summary_csv_file.close()
        details_csv_file.close()

    print(f"\nDone. Written:")
    print(f"  {summary_csv_path}")
    print(f"  {details_csv_path}")


if __name__ == "__main__":
    main()
