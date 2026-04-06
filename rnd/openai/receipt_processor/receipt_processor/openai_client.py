from openai import OpenAI
from receipt_processor.prompt import build_prompt
from receipt_processor.input_handlers import build_content_for_file

client = OpenAI()


def call_openai(file_path):
    prompt = build_prompt()
    content_for_file = build_content_for_file(file_path)

    content = [
        {"type": "input_text", "text": prompt}
    ]

    content.extend(content_for_file)

    response = client.responses.create(
        model="gpt-4.1",
        input=[{
            "role": "user",
            "content": content
        }]
    )

    return response.output_text.strip()