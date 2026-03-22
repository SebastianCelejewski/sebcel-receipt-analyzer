import os
from receipt_processor.openai_client import call_openai
from receipt_processor.parsing import parse_response
from receipt_processor.csv_utils import init_csv, write_csv_row
from receipt_processor.file_utils import (
    list_jpg_files,
    encode_image,
    is_already_processed,
    build_filename,
    safe_rename,
    generate_csv_filename
)

def process_file(folder, filename, writer):
    path = os.path.join(folder, filename)
    print(f"Processing {filename}")

    image = encode_image(path)
    response = call_openai(image)

    data = parse_response(response)
    if not data:
        return

    write_csv_row(writer, data)

    new_name = build_filename(data)
    new_path = os.path.join(folder, new_name)

    final_path = safe_rename(path, new_path)
    print("->", final_path)

def main():
    folder = "."
    csv_path = generate_csv_filename()

    csv_file, writer = init_csv(csv_path)

    try:
        for file in list_jpg_files(folder):
            process_file(folder, file, writer)
    finally:
        csv_file.close()

if __name__ == "__main__":
    main()