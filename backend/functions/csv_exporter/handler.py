import json
import boto3
import csv
import io
import urllib.parse
import os

s3 = boto3.client("s3")

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
CSV_KEY = "exports/expenses.csv"


def handler(event, context):

    print("Event received")
    print(json.dumps(event))

    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

    print(f"Reading normalized JSON: s3://{bucket}/{key}")

    response = s3.get_object(Bucket=bucket, Key=key)

    receipt = json.loads(response["Body"].read())

    rows = []

    for item in receipt.get("items", []):
        rows.append([
            receipt.get("receipt_id"),
            receipt.get("date"),
            receipt.get("store"),
            item.get("product"),
            item.get("quantity"),
            item.get("unit_price"),
            item.get("total")
        ])

    csv_buffer = io.StringIO()

    writer = csv.writer(csv_buffer)

    writer.writerow([
        "receipt_id",
        "date",
        "store",
        "product",
        "quantity",
        "unit_price",
        "total"
    ])

    writer.writerows(rows)

    print(f"Writing CSV: {CSV_KEY}")

    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=CSV_KEY,
        Body=csv_buffer.getvalue(),
        ContentType="text/csv"
    )

    return {
        "rows_written": len(rows)
    }