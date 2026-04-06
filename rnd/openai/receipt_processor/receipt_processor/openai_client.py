from openai import OpenAI
from receipt_processor.prompt import build_prompt
from receipt_processor.input_handlers import build_content_for_file

client = OpenAI()

def call_openai(file_path):
    print("- building prompt")
    prompt = build_prompt()

    print("- preparing file")
    content_for_file = build_content_for_file(file_path)

    content = [
        {"type": "input_text", "text": prompt}
    ]

    content.extend(content_for_file)

    print("- sending request to OpenAI")
    response = client.responses.create(
        model="gpt-4.1",
        input=[{
            "role": "user",
            "content": content
        }]
    )

    print("- received response from OpenAI")
    return response.output_text.strip()