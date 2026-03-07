import json
import boto3
import urllib.parse
import os

textract = boto3.client("textract")
s3 = boto3.client("s3")

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET")

def handler(event, context):

    print("Event received:")
    print(json.dumps(event))

    try:
        record = event["Records"][0]

        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        print(f"Processing file: s3://{bucket}/{key}")

        response = textract.analyze_expense(
            Document={
                "S3Object": {
                    "Bucket": bucket,
                    "Name": key
                }
            }
        )

        filename = os.path.basename(key)
        name, _ = os.path.splitext(filename)
        output_key = f"textract/{name}.json"

        s3.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=output_key,
            Body=json.dumps(response),
            ContentType="application/json"
        )

        print(f"Saved Textract result to s3://{PROCESSED_BUCKET}/{output_key}")

        return {
            "statusCode": 200,
            "body": "Textract analysis completed"
        }

    except Exception as e:
        print("Error during processing")
        print(str(e))

        raise
