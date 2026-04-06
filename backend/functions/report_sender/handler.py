import boto3
import os
import base64
import smtplib
import json
from email.message import EmailMessage
from decimal import Decimal, InvalidOperation

s3 = boto3.client("s3")
ses = boto3.client("ses")
ssm = boto3.client("ssm")

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
RAW_BUCKET = os.environ["RAW_BUCKET"]
SES_SENDER = os.environ["SES_SENDER"]
SMTP_USERNAME_PARAM = os.environ["SMTP_USERNAME_PARAM"]
SMTP_PASSWORD_PARAM = os.environ["SMTP_PASSWORD_PARAM"]
RECIPIENTS = os.environ.get("RECIPIENTS", "").split(",")

def handler(event, context):
    print(json.dumps(event))
    record = event["Records"][0]
    
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    print(f"Loading JSON file from s3://{bucket}/{key}")
    data = download_json(bucket, key)
    print(json.dumps(data))

    if (data == None or len(data) == 0):
        print("Error: No data in json")
        error_html = build_html_with_error("Brak danych w pliku JSON")
        print("Email built, sending")
        send_email(error_html, "error")
        print("Email sent")
        return

    image_filename = data["image_filename"]
    chatgpt_response = data["chatgpt"]

    chatgpt_data = json.loads(chatgpt_response)

    store = chatgpt_data["store"]
    date = chatgpt_data["datetime"]
    document_type = chatgpt_data["document_type"]
    total = chatgpt_data["total"]
    category = chatgpt_data["category"]
    items = chatgpt_data["items"]

    image_key = f"uploads/{image_filename}"

    print(f"Loading receipt image from s3://{RAW_BUCKET}/{image_key}")

    image_base64 = download_image_base64(RAW_BUCKET, image_key)

    print("Image downloaded")

    html = build_html(
        store,
        date,
        document_type,
        category,
        total,
        items,
        image_base64
    )

    print("Email created, sending")

    send_email(html, image_filename)

    print("Email sent")

    return {"status": "ok"}

def load_smtp_credentials():
    response = ssm.get_parameters(
        Names=[SMTP_USERNAME_PARAM, SMTP_PASSWORD_PARAM],
        WithDecryption=True
    )

    params = {p["Name"]: p["Value"] for p in response["Parameters"]}

    return (
        params[SMTP_USERNAME_PARAM],
        params[SMTP_PASSWORD_PARAM]
    )
    
def download_json(bucket, key):
    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )
    body = response["Body"].read()

    return json.loads(body)

def download_image_base64(bucket, key):

    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    image_bytes = response["Body"].read()
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return encoded

def build_html(store, date, document_type, category, total, items, image_base64):
    rows_html = ""

    for item in items:

        rows_html += f"""
        <tr>
            <td>{item['normalized_name']}</td>
            <td>{item['unit']}</td>
            <td>{format_pln_decimal(item['unit_price'])} zł</td>
            <td>{item['amount']}</td>
            <td>{format_pln_decimal(item['price'])} zł</td>
        </tr>
        """

    html = f"""
    <html>
    <body>

    <h1>Skaner paragonów, wersja 2 (ChatGPT)</h1>
    <h2>Paragon przetworzony</h2>

    <p><b>Sklep:</b> {store}</p>
    <p><b>Data:</b> {date.replace("T", " ")}</p>
    <p><b>Typ dokumentu:</b> {document_type}</p>
    <p><b>Kategoria:</b> {category}</p>
    <p><b>Kwota:</b> {format_pln_decimal(total)} zł</p>
    
    <h3>Pozycje</h3>

    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Produkt/usługa</th>
            <th>Jednostka</th>
            <th>Cena jednostkowa</th>
            <th>Ilość/liczba</th>
            <th>Cena</th>
        </tr>

        {rows_html}

    </table>

    <h3>Skan paragonu</h3>

    <img src="data:image/jpeg;base64,{image_base64}" width="400">

    </body>
    </html>
    """

    return html

def build_html_with_error(error_message):

    html = f"""
    <html>
    <body>

    <h2>Błąd przetwarzania paragonu</h2>

    <p><b>Błąd:</b> {error_message}</p>

    </body>
    </html>
    """

    return html

def send_email(html, document_id):
    return send_email_via_smtp(html, document_id)

def send_email_via_smtp(html, document_id, attachment_bytes=None, filename=None):

    smtp_username, smtp_password = load_smtp_credentials();

    msg = EmailMessage()

    msg["Subject"] = f"[Paragony, v.2] Dokument przetworzony ({document_id})"
    msg["From"] = smtp_username
    msg["To"] = ", ".join(RECIPIENTS)

    msg.set_content("Twój klient poczty nie obsługuje HTML.")

    msg.add_alternative(html, subtype="html")

    if attachment_bytes and filename:

        msg.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="octet-stream",
            filename=filename
        )

    with smtplib.SMTP("smtp.wp.pl", 587) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(msg)

def send_email_via_sns(html, document_id):
    ses.send_email(
        Source=SES_SENDER,
        Destination={
            "ToAddresses": RECIPIENTS
        },
        Message={
            "Subject": {
                "Data": f"[ChatGPT] Dokument przetworzony ({document_id})"
            },
            "Body": {
                "Html": {
                    "Data": html
                }
            }
        }
    )

def format_pln_decimal(value) -> str:
    if value is None:
        return ""

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return ""

    formatted = f"{number:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", " ")    