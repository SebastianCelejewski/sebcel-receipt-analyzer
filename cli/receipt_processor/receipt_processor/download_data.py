import os
import re
import sys
import argparse

import boto3

PROJECT = "sebcel-receipt-analyzer"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# (bucket name suffix, key prefix template)
SOURCES = [
    ("raw-bucket", "uploads/{date}/"),
    ("processed-bucket", "chatgpt/{date}/"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download receipt source files and their JSON analysis results "
                    "for a given date from S3, so they can be processed locally "
                    "without calling OpenAI again."
    )
    parser.add_argument(
        "date",
        help="Date to fetch, in YYYY-MM-DD format (e.g. 2026-06-07)"
    )
    parser.add_argument(
        "-e", "--env",
        default="prod",
        help="Environment to fetch from (default: prod)"
    )
    parser.add_argument(
        "-o", "--output",
        default=".",
        help="Local folder to download files into (default: current folder)"
    )
    return parser.parse_args()


def download_prefix(s3, bucket, prefix, output_folder):
    paginator = s3.get_paginator("list_objects_v2")
    found_any = False

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue

            found_any = True
            filename = os.path.basename(key)
            local_path = os.path.join(output_folder, filename)

            print(f"Downloading s3://{bucket}/{key} -> {local_path}")
            s3.download_file(bucket, key, local_path)

    if not found_any:
        print(f"No files found at s3://{bucket}/{prefix}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    if not DATE_RE.match(args.date):
        print(f"Error: '{args.date}' is not a valid date in YYYY-MM-DD format")
        sys.exit(1)

    output_folder = args.output
    os.makedirs(output_folder, exist_ok=True)

    s3 = boto3.client("s3")

    for bucket_suffix, prefix_template in SOURCES:
        bucket = f"{PROJECT}-{bucket_suffix}-{args.env}"
        prefix = prefix_template.format(date=args.date)
        print(f"\nFetching from s3://{bucket}/{prefix}")
        download_prefix(s3, bucket, prefix, output_folder)

    print(f"\nDone. Files saved to: {os.path.abspath(output_folder)}")


if __name__ == "__main__":
    main()
