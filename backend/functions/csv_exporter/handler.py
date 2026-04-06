import json
import boto3
import csv
import io
import urllib.parse
import os

s3 = boto3.client("s3")

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]

CSV_COLUMNS = [
    "receipt_id",
    "image_filename",
    "date",
    "store",
    "product",
    "quantity",
    "unit_price",
    "total"
]

def handler(event, context):
    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
    filename = os.path.basename(key)
    name, _ = os.path.splitext(filename)
    output_key = f"exports/receipts/{name}.csv"

    print(f"Reading normalized JSON: s3://{bucket}/{key}")

    response = s3.get_object(Bucket=bucket, Key=key)
    get_object_obj = s3.get_object(Bucket=bucket, Key=key)
    binary = obj["Body"].read()
    base64_data = base64.b64encode(binary).decode("utf-8")

data_url = f"data:{obj['ContentType']};base64,{base64_data}"
    receipt = json.loads(response["Body"].read())

    rows = []

    for item in receipt.get("items", []):
        rows.append([
            receipt.get("receipt_id"),
            receipt.get("image_filename"),
            receipt.get("date"),
            receipt.get("store"),
            item.get("product"),
            item.get("quantity"),
            item.get("unit_price"),
            item.get("total")
        ])

    csv_buffer = io.StringIO()

    writer = csv.writer(csv_buffer)

    writer.writerow(CSV_COLUMNS)
    writer.writerows(rows)

    print(f"Writing CSV: s3://{PROCESSED_BUCKET}/{output_key}")

    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=output_key,
        Body=csv_buffer.getvalue().encode("utf-8-sig"),
        ContentType="text/csv"
    )

    return {
        "rows_written": len(rows)
    }