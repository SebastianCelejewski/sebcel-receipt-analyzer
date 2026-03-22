from openai import OpenAI

client = OpenAI()

def build_prompt():
    return """Odczytaj z obrazu:
- datę i godzinę
- nazwę sklepu
- typ dokumentu (np. paragon, potwierdzenie płatności kartą)
- sumę końcową

Dodatkowo przypisz kategorię wydatku na podstawie nazwy sklepu.

Zasady kategoryzacji:
- piekarnia, cukiernia, warzywniak, mięsny → wydatki codzienne
- Auchan → wydatki tygodniowe
- lekarze, apteki → lekarze i leczenie
- C&A, H&M i inne sklepy odzieżowe → ubrania
- Zarząd dróg i zieleni, Gdańsk Transport Company → przejazdy
- stacje benzynowe → paliwo
- inne → inne

Zwróć WYŁĄCZNIE JSON:
{
  "datetime": "YYYY-MM-DD HH:MM",
  "store": "NAZWA",
  "document_type": "TYP",
  "total": "KWOTA",
  "category": "KATEGORIA"
}
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