import json
import boto3
import os
import uuid

s3 = boto3.client("s3")
BUCKET = os.environ["RAW_BUCKET"]

def handler(event, context):

    key = f"uploads/{uuid.uuid4()}.jpg"

    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": BUCKET,
            "Key": key,
            "ContentType": "image/jpeg"
        },
        ExpiresIn=300
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "upload_url": url,
            "key": key
        })
    }