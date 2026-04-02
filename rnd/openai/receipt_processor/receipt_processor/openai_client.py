from openai import OpenAI

client = OpenAI()

def build_prompt():
    return """You are a system that extracts structured data from Polish retail receipts (paragony).

The input is an image of a receipt written in Polish.

--------------------------------
TASK
--------------------------------

Extract from the image:

1. Date and time
2. Store name
3. Document type (e.g. receipt, card payment confirmation, etc.)
4. Final total amount
5. Expense category (based on store name)
6. List of purchased items

--------------------------------
CATEGORY RULES (VERY IMPORTANT)
--------------------------------

Assign category based on store name:

- piekarnia, cukiernia, warzywniak, mięsny → wydatki codzienne
- Auchan → wydatki tygodniowe
- lekarze, apteki → lekarze i leczenie
- C&A, H&M and other clothing stores → ubrania
- Zarząd Dróg i Zieleni, Gdańsk Transport Company → przejazdy
- gas stations (e.g. Orlen, Shell, BP) → paliwo
- otherwise → inne

--------------------------------
POLISH CONTEXT
--------------------------------

The receipt is in Polish. Common words:

- "szt" = pieces
- "kg" = kilograms
- "g" = grams
- "l" = liters
- "RAZEM", "SUMA" = total
- "GOTÓWKA" = cash
- "KARTA" = card payment

Prices usually use comma as decimal separator (e.g. 12,99), however dot is also sometimes used.

--------------------------------
OUTPUT FORMAT (STRICT JSON ONLY)
--------------------------------

{
  "datetime": "YYYY-MM-DDTHH:MM",
  "store": "string",
  "document_type": "string",
  "total": number,
  "category": "string",
  "items": [
    {
      "name": "string",
      "unit": "kg | g | l | szt | op | null",
      "unit_price": number,
      "amount": number,
      "price": number
    }
  ]
}

--------------------------------
FIELD RULES
--------------------------------

datetime:
- Extract date and time
- Format: YYYY-MM-DD HH:MM

store:
- Normalize store name if possible
  e.g. BIEDRONKA → Biedronka

document_type:
- Examples: "receipt", "card_payment", etc.

total:
- Final total amount (ignore intermediate totals)
- Convert to number (use dot instead of comma)

--------------------------------
ITEM RULES
--------------------------------

Each item must include:

name:
- Clean product name
- Remove unnecessary codes

unit:
- Use:
  "kg" for weighted products
  "g" if explicitly shown
  "l" for liquids
  "szt" for pieces
  "op" for packages
- If unknown → null

unit_price:
- Price per unit
- Convert to number

amount:
- Quantity purchased
- Weighted goods → decimal (e.g. 0.75)
- Pieces → integer

price:
- Total price for this item

--------------------------------
IMPORTANT RULES
--------------------------------

- Convert ALL numbers:
  12,99 → 12.99

- If unit price is missing:
  unit_price = price / amount

- If amount is missing:
  assume amount = 1

- Ignore:
  VAT breakdown
  payment method lines
  duplicate totals

- If any value is missing → use null

--------------------------------
CRITICAL
--------------------------------

- Return ONLY valid JSON
- No explanations
- No comments
- No extra text
"""

def call_openai(image_base64):
    response = client.responses.create(
        model="gpt-4.1",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": build_prompt()},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{image_base64}"
                }
            ]
        }]
    )
    return response.output_text.strip()