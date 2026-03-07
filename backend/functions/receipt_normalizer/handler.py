import json
import boto3
import urllib.parse
import os
import re

s3 = boto3.client("s3")

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]

IGNORE_WORDS = [
    "SPRZEDAZ",
    "SUMA",
    "PTU"
]

KNOWN_STORES = ["AUCHAN", "LIDL", "BIEDRONKA"]

def handler(event, context):

    print("Event received")
    print(json.dumps(event))

    event_record = event["Records"][0]

    bucket = event_record["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event_record["s3"]["object"]["key"])

    filename = os.path.basename(key)
    name, _ = os.path.splitext(filename)
    output_key = f"normalized/{name}.json"

    print(f"Reading Textract JSON: s3://{bucket}/{key}")

    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    textract_data = json.loads(response["Body"].read())
    
    docs = textract_data.get("ExpenseDocuments") or []
    blocks = textract_data.get("Blocks") or []
    
    receipt_id = build_receipt_id(docs, blocks, name)
    store = normalize_store(extract_store(docs))

    items = []

    for doc in docs:
        for group in doc.get("LineItemGroups", []):
            for item in group.get("LineItems", []):
                line = {
                    field.get("Type", {}).get("Text"):
                    field.get("ValueDetection", {}).get("Text")
                    for field in item.get("LineItemExpenseFields", [])
                }

                if not is_product(line):
                    continue

                unit_price = normalize_unit_price(line.get("UNIT_PRICE"))
                total = normalize_price(line.get("PRICE"))

                quantity = normalize_quantity(
                    line.get("QUANTITY"),
                    unit_price,
                    total
                )

                normalized = {
                    "receipt_id": receipt_id,
                    "source_file": filename,
                    "store": store,
                    "product": line.get("ITEM"),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total": total
                }

                items.append(normalized)

    print("Extracted items:")
    print(json.dumps(items, indent=2))

    total = extract_total(docs)
    date = extract_date(docs) or extract_date_from_text(blocks)

    # fallback dla paragonów bez pozycji (np. autostrada)
    if len(items) == 0:
        if total:
            items.append({
                "receipt_id": receipt_id,
                "source_file": filename,
                "store": store,
                "product": "nieokreślony produkt lub usługa",
                "quantity": 1,
                "unit_price": total,
                "total": total
            })

    result = {
        "receipt_id": receipt_id,
        "source_file": filename,
        "store": store,
        "date": date,
        "total": total,
        "items": items
    }

    print(f"Saving normalized data: {output_key}")

    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=output_key,
        Body=json.dumps(result, ensure_ascii=False),
        ContentType="application/json"
    )

    return {
        "items_extracted": len(items),
        "output_key": output_key
    }


def is_product(item):

    name = item.get("ITEM", "")

    if not name:
        return False

    for word in IGNORE_WORDS:
        if word in name:
            return False

    return True


def normalize_price(value):

    if not value:
        return None

    value = value.replace(",", ".")
    value = value.replace("C", "")
    value = value.strip()

    try:
        return float(value)
    except:
        return None


def normalize_unit_price(value):

    if not value:
        return None

    value = value.replace("x", "")
    value = value.replace(",", ".")
    value = value.replace("C", "")

    try:
        return float(value)
    except:
        return None

def normalize_quantity(q, unit_price, total):

    if not q:
        return 1

    q = q.replace(",", ".")
    
    try:
        val = float(q)
    except:
        return 1

    if unit_price is None or total is None:
        return val

    # sprawdzenie czy pasuje bez korekty
    if abs(val * unit_price - total) < 0.2:
        return val

    # sprawdzenie czy to były gramy
    corrected = val / 1000

    if abs(corrected * unit_price - total) < 0.2:
        return corrected

    return val

def extract_store(docs):

    store = None

    for doc in docs:
        for field in doc.get("SummaryFields", []):

            field_type = field.get("Type", {}).get("Text")
            value = field.get("ValueDetection", {}).get("Text")

            if field_type == "VENDOR_NAME":
                store = value

    return store

def normalize_store(name):

    if not name:
        return None

    name = name.upper()

    for store in KNOWN_STORES:
        if store in name:
            return store

    return name

def build_receipt_id(docs, blocks, name):

    date = None
    time = None
    number = None

    for doc in docs:
        for field in doc.get("SummaryFields", []):

            t = field.get("Type", {}).get("Text")
            v = field.get("ValueDetection", {}).get("Text")

            if t == "INVOICE_RECEIPT_DATE":
                date = v

            elif t == "TIME":
                time = v

            elif t == "INVOICE_RECEIPT_ID":
                number = v

    # fallback – spróbuj znaleźć numer w tekście
    if not number:
        number = extract_receipt_number_from_text(blocks)

    return f"{date}_{time}_{number}__{name}"

def extract_receipt_number_from_text(blocks):

    patterns = [
        r"\bnr\.?\s*[:#]?\s*(\d+)",
        r"\bparagon\s*nr\.?\s*(\d+)",
    ]

    for block in blocks:

        if block.get("BlockType") != "LINE":
            continue

        text = block.get("Text", "").lower()

        # próba regexów
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return m.group(1)

        # fallback: linia z samymi cyframi
        if re.fullmatch(r"\d{4,}", text.strip()):
            return text.strip()

    return None

def extract_total(docs):

    for doc in docs:
        for field in doc.get("SummaryFields", []):

            field_type = field.get("Type", {}).get("Text")
            value = field.get("ValueDetection", {}).get("Text")

            if field_type == "TOTAL":
                return normalize_price(value)

    return None

def extract_date(docs):

    for doc in docs:
        for field in doc.get("SummaryFields", []):

            field_type = field.get("Type", {}).get("Text")
            value = field.get("ValueDetection", {}).get("Text")

            if field_type == "INVOICE_RECEIPT_DATE":
                return value

    return None

def extract_date_from_text(blocks):

    for block in blocks:
        if block.get("BlockType") != "LINE":
            continue

        text = block.get("Text", "")

        m = re.search(r"\b(20\d\d[-./]\d\d[-./]\d\d)\b", text)
        if m:
            return m.group(1)

    return None    