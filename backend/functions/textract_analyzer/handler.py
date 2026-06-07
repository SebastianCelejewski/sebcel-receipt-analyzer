import json
import boto3
import urllib.parse
import os

textract = boto3.client("textract")
s3 = boto3.client("s3")

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET")

def handler(event, context):

    try:
        sns_record = event["Records"][0]
        sns_message = json.loads(sns_record["Sns"]["Message"])
        s3_record = sns_message["Records"][0]

        bucket = s3_record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(s3_record["s3"]["object"]["key"])

        print(f"Processing file: s3://{bucket}/{key}")

        textract_response = textract.analyze_expense(
            Document={
                "S3Object": {
                    "Bucket": bucket,
                    "Name": key
                }
            }
        )

        # Path relative to the "uploads/" prefix (e.g. "2026-06-07/user_..._uuid.jpg"),
        # used downstream to locate the original image in the raw bucket.
        image_filename = key[len("uploads/"):] if key.startswith("uploads/") else os.path.basename(key)

        response = {
            "image_filename": image_filename,
            "textract": textract_response
        }

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
