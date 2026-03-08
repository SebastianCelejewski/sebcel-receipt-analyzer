import json
import boto3
import os
import uuid
from datetime import datetime

s3 = boto3.client("s3")
BUCKET = os.environ["RAW_BUCKET"]

def handler(event, context):

    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    email = claims.get("email", "unknown")
    user = email.split("@")[0].replace(".", "_")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    key = f"uploads/{user}_{timestamp}_{uuid.uuid4().hex}.jpg"

    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": BUCKET,
            "Key": key,
            "ContentType": "image/jpeg",
            "Metadata": {
                "user": email,
                "source": "pwa"
            }
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
            "key": key,
            "user": user
        })
    }