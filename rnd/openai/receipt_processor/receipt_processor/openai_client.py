import sys
import time
from openai import OpenAI, RateLimitError
from receipt_processor.prompt import build_prompt
from receipt_processor.input_handlers import build_content_for_file

client = OpenAI()

_RETRY_DELAYS = [10, 30, 60]  # seconds between retries

def call_openai(file_path):
    print("- building prompt")
    prompt = build_prompt()

    print("- preparing file")
    content_for_file = build_content_for_file(file_path)

    content = [{"type": "input_text", "text": prompt}]
    content.extend(content_for_file)

    for attempt, delay in enumerate([0] + _RETRY_DELAYS):
        if delay:
            print(f"- rate limit hit, waiting {delay}s before retry (attempt {attempt}/{len(_RETRY_DELAYS)})...")
            time.sleep(delay)

        try:
            print("- sending request to OpenAI")
            response = client.responses.create(
                model="gpt-4.1",
                input=[{"role": "user", "content": content}]
            )
            print("- received response from OpenAI")
            return response.output_text.strip()

        except RateLimitError as e:
            if "insufficient_quota" in str(e):
                print("\nERROR: Your OpenAI credit balance is exhausted.")
                print("Top up at: https://platform.openai.com/settings/billing")
                sys.exit(1)
            if attempt == len(_RETRY_DELAYS):
                raise
            continue