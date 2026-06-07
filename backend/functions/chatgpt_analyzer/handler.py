import json
import boto3
import urllib.parse
import os
from datetime import datetime
from openai import OpenAI
from prompt import build_prompt
from input_handlers import build_content_for_file

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

        response = {
            "image_filename": image_relative_path,
            "chatgpt": chatgpt_response
        }

        output_file_name = os.path.basename(input_key)
        output_name, _ = os.path.splitext(output_file_name)

        # Reuse the date folder from the uploaded file's path (e.g. "2026-06-07/foo.jpg"
        # -> "2026-06-07"), so the output mirrors the raw bucket structure. Fall back to
        # today's date if the input wasn't uploaded into a date-based folder.
        path_parts = image_relative_path.split("/")
        date_folder = path_parts[0] if len(path_parts) > 1 else datetime.now().strftime("%Y-%m-%d")

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
