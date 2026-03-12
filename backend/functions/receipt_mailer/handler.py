import boto3
import csv
import os
import base64
import json
import smtplib
import json
from email.message import EmailMessage

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
    record = event["Records"][0]
    
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    print(f"Loading CSV file from s3://{bucket}/{key}")
    csv_data = download_csv(bucket, key)

    if (csv_data == None or len(csv_data) == 0):
        error_html = build_html_with_error("Brak danych w pliku CSV")
        send_email(error_html, "error")
        return

    receipt_id = csv_data[0]["receipt_id"]
    image_filename = csv_data[0]["image_filename"]
    store = csv_data[0]["store"]
    date = csv_data[0]["date"]
    total = csv_data[0]["total"]

    image_key = f"uploads/{image_filename}"

    print(f"Loading receipt image from s3://{RAW_BUCKET}/{image_key}")

    image_base64 = download_image_base64(RAW_BUCKET, image_key)

    print("Image downloaded")

    html = build_html(
        receipt_id,
        store,
        date,
        total,
        csv_data,
        image_base64
    )

    print("Email created, sending")

    # response = send_email(html, receipt_id)
    send_email_via_smtp(html, receipt_id)

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
    
def download_csv(bucket, key):
    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    content = response["Body"].read().decode("utf-8-sig")
    reader = csv.DictReader(content.splitlines())
    rows = list(reader)
    return rows

def download_image_base64(bucket, key):

    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    image_bytes = response["Body"].read()
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return encoded

def build_html(receipt_id, store, date, total, items, image_base64):
    rows_html = ""

    for item in items:

        rows_html += f"""
        <tr>
            <td>{item['product']}</td>
            <td>{item['quantity']}</td>
            <td>{item['unit_price']}</td>
            <td>{item['total']}</td>
        </tr>
        """

    html = f"""
    <html>
    <body>

    <h2>Paragon przetworzony</h2>

    <p><b>Sklep:</b> {store}</p>
    <p><b>Data:</b> {date}</p>
    <p><b>Kwota:</b> {total}</p>
    <p><b>ID:</b> {receipt_id}</p>

    <h3>Pozycje</h3>

    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Produkt</th>
            <th>Ilość</th>
            <th>Cena</th>
            <th>Razem</th>
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

def send_email_via_smtp(html, receipt_id, attachment_bytes=None, filename=None):

    smtp_username, smtp_password = load_smtp_credentials();

    msg = EmailMessage()

    msg["Subject"] = f"Paragon przetworzony ({receipt_id})"
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

def send_email_via_sns(html, receipt_id):
    ses.send_email(
        Source=SES_SENDER,
        Destination={
            "ToAddresses": RECIPIENTS
        },
        Message={
            "Subject": {
                "Data": f"Paragon przetworzony ({receipt_id})"
            },
            "Body": {
                "Html": {
                    "Data": html
                }
            }
        }
    )