import json
import boto3
import urllib.parse
import os

s3 = boto3.client("s3")

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]

def handler(event, context):

    print("Event received")
    print(json.dumps(event))

    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

    print(f"Reading Textract JSON: s3://{bucket}/{key}")

    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    textract_data = json.loads(response["Body"].read())

    items = []

    for doc in textract_data.get("ExpenseDocuments", []):
        for group in doc.get("LineItemGroups", []):
            for item in group.get("LineItems", []):
                record = {}
                for field in item.get("LineItemExpenseFields", []):
                    field_type = field.get("Type", {}).get("Text")
                    value = field.get("ValueDetection", {}).get("Text")
                    record[field_type] = value
                items.append(record)

    print("Extracted items:")
    print(json.dumps(items, indent=2))

    output_key = key.replace("textract/", "normalized/")

    print(f"Saving normalized data: {output_key}")

    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=output_key,
        Body=json.dumps(items),
        ContentType="application/json"
    )

    return {
        "items_extracted": len(items),
        "output_key": output_key
    }