import json
import boto3
import urllib.parse
import os
import uuid
from datetime import datetime
from openai import OpenAI
from prompt import build_prompt
from input_handlers import build_content_for_file
from file_utils import build_base_filename

s3client = boto3.client("s3")
ssmClient = boto3.client("ssm")
openAiClient = None

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET")
OPENAI_API_KEY_PARAMETER_NAME = os.environ.get("OPENAI_API_KEY_PARAMETER_NAME")

def handler(event, context):
    try:
        sns_record = event["Records"][0]
        sns_message = json.loads(sns_record["Sns"]["Message"])
        s3_record = sns_message["Records"][0]

        input_bucket = s3_record["s3"]["bucket"]["name"]
        input_key = urllib.parse.unquote_plus(s3_record["s3"]["object"]["key"])
        input_file_name = os.path.basename(input_key)
        # Path relative to the "uploads/" prefix (e.g. "2026-06-07/user_..._uuid.jpg"),
        # used downstream to locate the original image in the raw bucket.
        image_relative_path = input_key[len("uploads/"):] if input_key.startswith("uploads/") else input_file_name
        print(f"Processing file: s3://{input_bucket}/{input_key}")

        get_object_response = s3client.get_object(Bucket=input_bucket, Key=input_key)
        input_file = get_object_response["Body"].read()
        input_file_content_type = get_object_response['ContentType']

        chatgpt_response = call_openai(input_file_name, input_file_content_type, input_file)

        # Reuse the date folder from the uploaded file's path (e.g. "2026-06-07/foo.jpg"
        # -> "2026-06-07"), so the output mirrors the raw bucket structure. Fall back to
        # today's date if the input wasn't uploaded into a date-based folder.
        path_parts = image_relative_path.split("/")
        date_folder = path_parts[0] if len(path_parts) > 1 else datetime.now().strftime("%Y-%m-%d")

        output_file_name = os.path.basename(input_key)
        output_name, file_extension = os.path.splitext(output_file_name)

        # Try to rename the source file (and the JSON output) to reflect the
        # transaction date/time and store, e.g. "2026-06-07_12.30_Biedronka.jpg".
        # Mirrors the behaviour of the local rnd/openai/receipt_processor tool.
        new_base_name = rename_source_file(input_bucket, input_key, date_folder, file_extension, chatgpt_response)
        if new_base_name:
            output_name = new_base_name
            image_relative_path = f"{date_folder}/{new_base_name}{file_extension}"

        response = {
            "image_filename": image_relative_path,
            "chatgpt": chatgpt_response
        }

        output_key = f"chatgpt/{date_folder}/{output_name}.json"

        s3client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=output_key,
            Body=json.dumps(response),
            ContentType="application/json"
        )

        print(f"Saved ChatGPT result to s3://{PROCESSED_BUCKET}/{output_key}")

        return {
            "statusCode": 200,
            "body": "ChatGPT analysis completed"
        }

    except Exception as e:
        print("Error during processing")
        print(str(e))

        raise

def rename_source_file(bucket, source_key, date_folder, file_extension, chatgpt_response):
    """
    Renames (copies + deletes) the source receipt file in S3 so its name
    reflects the transaction date/time and store, e.g.
    "uploads/2026-06-07/2026-06-07_12.30_Biedronka.jpg".

    Returns the new base filename (without extension) on success, or None
    if the rename could not be performed (e.g. response wasn't valid JSON),
    in which case the caller should keep using the original filename.
    """
    try:
        data = json.loads(extract_json(chatgpt_response))
    except Exception as e:
        print(f"Could not parse ChatGPT response as JSON, keeping original filename: {e}")
        return None

    if not data:
        return None

    base_name = build_base_filename(data)
    new_key = f"uploads/{date_folder}/{base_name}{file_extension}"

    if new_key == source_key:
        return base_name

    if object_exists(bucket, new_key):
        base_name = f"{base_name}_{uuid.uuid4().hex[:8]}"
        new_key = f"uploads/{date_folder}/{base_name}{file_extension}"

    print(f"Renaming s3://{bucket}/{source_key} -> s3://{bucket}/{new_key}")

    s3client.copy_object(
        Bucket=bucket,
        CopySource={"Bucket": bucket, "Key": source_key},
        Key=new_key
    )
    s3client.delete_object(Bucket=bucket, Key=source_key)

    return base_name

def object_exists(bucket, key):
    try:
        s3client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False

def extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end + 1]
    return text

def call_openai(file_name, file_content_type, file):
    openAiClient = get_openai_client()

    prompt = build_prompt()
    content_for_file = build_content_for_file(file_name, file_content_type, file)

    content = [
        {"type": "input_text", "text": prompt}
    ]

    content.extend(content_for_file)

    print("Sending request to OpenAI")
    response = openAiClient.responses.create(
        model="gpt-4.1",
        input=[{
            "role": "user",
            "content": content
        }]
    )

    print("Received response from OpenAI")
    return response.output_text.strip()

def get_openai_client():
    global openAiClient
    if openAiClient is None:
        print("Creating new OpenAI client")
        openAiClient = OpenAI(api_key=get_openai_api_key())
    else:
        print("Getting current OpenAI client")
    return openAiClient

def get_openai_api_key():
    response = ssmClient.get_parameter(Name=OPENAI_API_KEY_PARAMETER_NAME, WithDecryption=True)
    return response["Parameter"]["Value"]
