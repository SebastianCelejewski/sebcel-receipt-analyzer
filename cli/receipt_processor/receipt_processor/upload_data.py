import os
import sys
import uuid
import argparse
from datetime import datetime

import boto3

PROJECT = "sebcel-receipt-analyzer"

# Identifies the uploader in the generated filename, mirroring the convention
# used by the upload_url_generator Lambda (derived from the user's e-mail:
# "sebastian.celejewski@wp.pl" -> "sebastian_celejewski").
DEFAULT_USER = "sebastian_celejewski"

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "eml": "message/rfc822",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload receipt/invoice files (e.g. PDFs received by e-mail) "
                    "directly to the cloud raw bucket, the same way the PWA uploads "
                    "photos, so they get picked up by the cloud processing pipeline."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Path(s) to file(s) to upload (e.g. invoice1.pdf invoice2.pdf)"
    )
    parser.add_argument(
        "-e", "--env",
        default="prod",
        help="Environment to upload to (default: prod)"
    )
    parser.add_argument(
        "-u", "--user",
        default=DEFAULT_USER,
        help=f"User identifier embedded in the generated filename (default: {DEFAULT_USER})"
    )
    return parser.parse_args()


def build_key(path, user):
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "bin"

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    date_folder = now.strftime("%Y-%m-%d")

    return f"uploads/{date_folder}/{user}_{timestamp}_{uuid.uuid4().hex}.{ext}", ext


def upload_file(s3, bucket, path, user):
    if not os.path.isfile(path):
        print(f"Skipping '{path}': file not found")
        return False

    key, ext = build_key(path, user)
    content_type = CONTENT_TYPES.get(ext, "application/octet-stream")

    print(f"Uploading {path} -> s3://{bucket}/{key}")

    s3.upload_file(
        Filename=path,
        Bucket=bucket,
        Key=key,
        ExtraArgs={
            "ContentType": content_type,
            "Metadata": {
                "user": user,
                "source": "cli"
            }
        }
    )
    return True


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    bucket = f"{PROJECT}-raw-bucket-{args.env}"

    print(f"Target bucket: s3://{bucket}\n")

    s3 = boto3.client("s3")

    uploaded = 0
    for path in args.files:
        if upload_file(s3, bucket, path, args.user):
            uploaded += 1

    print(f"\nDone. Uploaded {uploaded}/{len(args.files)} file(s).")


if __name__ == "__main__":
    main()
