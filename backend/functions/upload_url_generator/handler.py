import json
import boto3
import os
import uuid
import urllib.request
from datetime import datetime

s3 = boto3.client("s3")
BUCKET = os.environ["RAW_BUCKET"]


def handler(event, context):
    email = fetch_email(event)

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

    print("Upload URL:", url)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "upload_url": url,
            "key": key,
            "user": email
        })
    }


def fetch_email(event):
    auth_header = event["headers"]["authorization"]
    token = auth_header.split(" ")[1]

    req = urllib.request.Request(
        "https://sebcel-receipt-analyzer-dev.auth.eu-central-1.amazoncognito.com/oauth2/userInfo",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())

    return data.get("email", "unknown@example.com")
