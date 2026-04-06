import os
import base64
import email
import fitz
import io

def build_content_for_file(file_name, file_content_type, file):
    print(f"Building content for file: {file_name}")
    ext = os.path.splitext(file_name)[1].lower()
    print(f"Ext: {ext}")

    if ext in [".jpg", ".jpeg", ".png"]:
        return handle_image(file, file_content_type)

    if ext == ".pdf":
        return handle_pdf(file)

    if ext == ".eml":
        return handle_eml(file)

    raise ValueError(f"Unsupported file type: {ext}")    

def handle_image(file, file_content_type):
    print("This is image")
    image_base64 = encode_file_to_base64(file)

    return [{
        "type": "input_image",
        "image_url": f"data:{file_content_type};base64,{image_base64}"
    }]

def handle_pdf(file):
    print("This is pdf")
    images = []

    images = pdf_to_images(file)

    if not images:
        return []

    buffer = io.BytesIO()
    images[0].save(buffer, format="JPEG")

    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return [{
        "type": "input_image",
        "image_url": f"data:image/jpeg;base64,{image_base64}"
    }]

def handle_eml(file):
    print("This is email")
    msg = email.message_from_file(file)
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body += part.get_payload(decode=True).decode(errors="ignore")
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    return [{
        "type": "input_text",
        "text": body[:8000]
    }]

def encode_file_to_base64(file):
    print("Converting file to base63")
    return base64.b64encode(file).decode("utf-8")
    
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    images = []

    for page in doc:
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        images.append(img_bytes)

    return images