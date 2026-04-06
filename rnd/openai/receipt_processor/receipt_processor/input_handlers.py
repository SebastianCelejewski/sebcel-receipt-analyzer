import os
import base64
import email

def encode_file_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
    
def handle_image(path):
    print(f"- handling image {path}")
    image_base64 = encode_file_to_base64(path)
    print(f"- image data size: {len(image_base64)}")

    return [{
        "type": "input_image",
        "image_url": f"data:image/jpeg;base64,{image_base64}"
    }]

def handle_pdf(path):
    print(f"- handling pdf {path}")
    from pdf2image import convert_from_path
    import io

    images = convert_from_path(path, first_page=1, last_page=1)

    if not images:
        return []

    buffer = io.BytesIO()
    images[0].save(buffer, format="JPEG")

    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    print(f"- image data size: {len(image_base64)}")

    return [{
        "type": "input_image",
        "image_url": f"data:image/jpeg;base64,{image_base64}"
    }]

def handle_eml(path):
    print(f"- handling e-mail {path}")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        msg = email.message_from_file(f)

    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body += part.get_payload(decode=True).decode(errors="ignore")
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    print(f"- image data size: {len(body)}")
    return [{
        "type": "input_text",
        "text": body[:8000]
    }]

def build_content_for_file(path):
    print(f"- path: {path}")
    ext = os.path.splitext(path)[1].lower()
    print(f"- ext: {ext}")

    if ext in [".jpg", ".jpeg", ".png"]:
        return handle_image(path)

    if ext == ".pdf":
        return handle_pdf(path)

    if ext == ".eml":
        return handle_eml(path)

    raise ValueError(f"Unsupported file type: {ext}")    